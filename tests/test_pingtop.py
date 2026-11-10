"""Regression checks for PINGTOP. Run with python3 -m unittest discover -s tests."""

import curses
import errno
import fcntl
import os
import pty
import runpy
import select
import shutil
import signal
import struct
import subprocess
import termios
import time
import unittest
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import Mock, patch


PROGRAM = Path(__file__).resolve().parents[1] / "pingtop"
APP = runpy.run_path(str(PROGRAM))
STAMP = "12:00:00"


class TargetsTest(unittest.TestCase):
    def test_cidr_uses_usable_ipv4_hosts(self):
        self.assertEqual(APP["expand_target"]("192.0.2.2/30"), ["192.0.2.1", "192.0.2.2"])
        self.assertEqual(APP["expand_target"]("192.0.2.0/31"), ["192.0.2.0", "192.0.2.1"])
        self.assertEqual(APP["expand_target"]("192.0.2.1/32"), ["192.0.2.1"])
        self.assertEqual(len(APP["expand_target"]("192.0.0.0/22")), 1022)

    def test_ranges_include_both_ends(self):
        self.assertEqual(
            APP["expand_target"]("192.0.2.254-192.0.3.1"),
            ["192.0.2.254", "192.0.2.255", "192.0.3.0", "192.0.3.1"],
        )

    def test_invalid_inputs_fail_before_starting_curses(self):
        for target in ("192.0.2.0/8", "192.0.2.1/33", "192.0.2.9-192.0.2.1",
                       "192.0.0.1-192.0.4.1", "example.com;echo", "fe80::1/64"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                APP["expand_target"](target)
        result = subprocess.run([PROGRAM, "-i", "0.1"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("intervalo", result.stderr)


class ProbesTest(unittest.TestCase):
    def test_iputils_reply(self):
        stdout = (
            "PING example.test (192.0.2.1) 56(84) bytes of data.\n"
            "64 bytes from 192.0.2.1: icmp_seq=1 ttl=56 time=12.34 ms\n"
        )
        response = subprocess.CompletedProcess([], 0, stdout, "")
        with patch("subprocess.run", return_value=response) as run:
            status, rtt, address, stamp, details = APP["probe"]("example.test")
        self.assertEqual((status, rtt, address, details), ("OK", 12.34, "192.0.2.1", (64, 56)))
        self.assertRegex(stamp, r"^\d{2}:\d{2}:\d{2}$")
        self.assertEqual(run.call_args.args[0][-2:], ["--", "example.test"])

    def test_ping_failures_distinguish_timeout_from_error(self):
        for code, state in ((1, "TIMEOUT"), (2, "ERRO")):
            with self.subTest(code=code), patch(
                "subprocess.run", return_value=subprocess.CompletedProcess([], code, "", "")
            ):
                result = APP["probe"]("example.test")
                self.assertEqual(result[:2], (state, None))
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ping", 3)):
            self.assertEqual(APP["probe"]("example.test")[:2], ("TIMEOUT", None))
        with patch("subprocess.run", side_effect=FileNotFoundError):
            self.assertEqual(APP["probe"]("example.test")[:2], ("ERRO", None))

    def test_mixed_route_probes_stay_in_order(self):
        output = (
            "traceroute to example.test (192.0.2.2)\n"
            " 1 gateway (192.0.2.1) 1.2 ms 1.4 ms *\n"
            " 2 * * *\n"
            " 3 * example.test (192.0.2.2) 3.4 ms alternate (192.0.2.3) 3.6 ms !H\n"
        )
        hops = APP["parse_route"](output, STAMP)
        self.assertEqual([hop[0] for hop in hops], [1, 2, 3])
        self.assertEqual(hops[0][1], (("gateway", "192.0.2.1", 1.2),
                                     ("gateway", "192.0.2.1", 1.4), (None, None, None)))
        self.assertEqual(hops[1][1], ((None, None, None),) * 3)
        self.assertEqual(hops[2][1], ((None, None, None), ("example.test", "192.0.2.2", 3.4),
                                     ("alternate", "192.0.2.3", 3.6)))

    def test_route_numeric_responders_and_ipv6(self):
        output = (
            " 1  192.0.2.1 1.20 ms 1.30 ms 192.0.2.2 1.40 ms\n"
            " 2  * 2001:db8::1 2.00 ms *\n"
        )
        hops = APP["parse_route"](output, STAMP)
        self.assertEqual([probe[1] for probe in hops[0][1]], ["192.0.2.1", "192.0.2.1", "192.0.2.2"])
        self.assertEqual([probe[1] for probe in hops[1][1]], [None, "2001:db8::1", None])

    def test_ipv6_ping_hop_limit(self):
        stdout = (
            "PING example.test(example.test (2001:db8::1)) 56 data bytes\n"
            "64 bytes from 2001:db8::1: icmp_seq=1 hlim=63 time=1.25 ms\n"
        )
        with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout, "")):
            state, rtt, address, _, details = APP["probe"]("example.test")
        self.assertEqual((state, rtt, address, details), ("OK", 1.25, "2001:db8::1", (64, 63)))

    def test_missing_traceroute_reports_dependency(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            hops, message = APP["trace"]("example.test")
        self.assertFalse(hops)
        self.assertIn("traceroute", message)

    def test_pausing_collects_inflight_result_without_scheduling(self):
        pool = Mock()
        future = Future()
        pool.submit.return_value = future
        monitor = APP["Monitor"]("example.test")
        monitor.update(pool, True)
        self.assertEqual(pool.submit.call_count, 1)
        monitor.update(pool, False)
        self.assertEqual(pool.submit.call_count, 1)
        future.set_result(("OK", 1.2, "192.0.2.1", STAMP))
        monitor.update(pool, False)
        self.assertIsNone(monitor.pending)
        self.assertEqual(list(monitor.history), [1.2])
        monitor.update(pool, True)
        self.assertEqual(pool.submit.call_count, 2)

    def test_loss_and_logs_distinguish_missing_replies_from_errors(self):
        monitor = APP["Monitor"]("example.test")
        monitor.record("OK", 1.2, "192.0.2.1", STAMP)
        monitor.record("TIMEOUT", None, None, STAMP)
        monitor.record("ERRO", None, None, STAMP)
        self.assertEqual((monitor.sent, monitor.lost, monitor.address), (2, 1, "192.0.2.1"))
        self.assertEqual(list(monitor.history), [1.2, None, None])


class GraphTest(unittest.TestCase):
    def render(self, width, height, values, graph_mode="Quadrantes"):
        monitor = APP["Monitor"]("127.0.0.1")
        for sequence, value in enumerate(values, 1):
            status = "TIMEOUT" if value is None else "OK"
            monitor.record(status, value, monitor.host, f"12:00:{sequence:02d}", (64, 64))

        pixels = {}

        def put(y, x, value, style=0):
            self.assertLessEqual(0, y)
            self.assertLess(y, height)
            self.assertLessEqual(0, x)
            self.assertLessEqual(x + len(value), width)
            for index, cell in enumerate(value, x):
                pixels[y, index] = cell, style

        with patch.object(curses, "color_pair", return_value=0):
            APP["draw_graph"](put, 0, width, height, monitor, 0, 0, 0, graph_mode)
        return pixels

    def test_quadrant_plot_mirrors_across_horizontal_axis(self):
        blocks = APP["QUADRANTS"]
        for width, height in ((47, 6), (64, 11), (110, 22), (120, 25)):
            with self.subTest(width=width, height=height):
                pixels = self.render(width, height, [40.0, 40.1, 40.7, None, None, None, 41.1, 45.0, 42.5])
                points = {(y, x): blocks.index(glyph)
                          for (y, x), (glyph, _) in pixels.items()
                          if glyph in blocks[1:] and (width < 100 or x < width - 20)}
                self.assertTrue(points)
                mirror_y = min(y for y, _ in points) + max(y for y, _ in points)
                for (y, x), mask in points.items():
                    mirrored = (mask >> 2) | ((mask & 3) << 2)
                    self.assertEqual(points.get((mirror_y - y, x)), mirrored)
                self.assertTrue(any(glyph == "×" for glyph, _ in pixels.values()))

    def test_micro_plot_mirrors_all_four_subpixel_levels(self):
        pixels = self.render(110, 22, [40.0, 40.1, 40.7, 42.1, 45.0, 42.5], "Micro")
        bits = (1, 8, 2, 16, 4, 32, 64, 128)
        points = {(y, x): ord(glyph) - 0x2800
                  for (y, x), (glyph, _) in pixels.items()
                  if 0x2800 < ord(glyph) <= 0x28ff}
        self.assertTrue(points)
        mirror_y = min(y for y, _ in points) + max(y for y, _ in points)
        for (y, x), mask in points.items():
            mirrored = sum(bits[(3 - bit // 2) * 2 + bit % 2]
                           for bit in range(8) if mask & bits[bit])
            self.assertEqual(points.get((mirror_y - y, x)), mirrored)

    def test_live_meter_changes_with_latest_reading(self):
        def meter(latest):
            pixels = self.render(112, 18, [40.0, 50.0, latest])
            return sum(glyph == "■" for (_, column), (glyph, _) in pixels.items()
                       if column > 94)

        self.assertGreater(meter(50.0), meter(40.0))
        self.assertGreater(meter(40.0), meter(None))
        self.assertEqual(meter(None), 0)

    def test_history_fades_metadata_but_preserves_failure_color(self):
        monitor = APP["Monitor"]("127.0.0.1")
        for index in range(8):
            monitor.record("TIMEOUT" if index == 0 else "OK",
                           None if index == 0 else 42.0, monitor.host, "12:00:00")
        calls = []
        with patch.object(curses, "color_pair", side_effect=lambda n: n << 8):
            APP["draw_history"](lambda *args: calls.append(args), 0, 26, 13, monitor, 4 << 8, 0, True)
        rows = [call for call in calls if call[2].startswith("12:")]
        self.assertEqual(len(rows), 8)
        self.assertTrue(rows[0][3] & curses.A_BOLD)
        self.assertLess(rows[0][3] & curses.A_COLOR, rows[-1][3] & curses.A_COLOR)
        self.assertTrue(any(call[2:] == ("×", 4 << 8) for call in calls))

    def test_history_shows_newest_reply_first(self):
        pixels = self.render(112, 16, [40.0, 41.1, 42.5])
        stamps = {}
        for row in range(16):
            prefix = "".join(pixels.get((row, col), (" ", 0))[0] for col in range(2, 10))
            if prefix.startswith("12:00:"):
                stamps[row] = prefix
        self.assertEqual(list(stamps.values()), ["12:00:03", "12:00:02", "12:00:01"])


class TargetViewTest(unittest.TestCase):
    def test_loss_meter_distinguishes_none_partial_and_total(self):
        meter = APP["loss_meter"]
        self.assertEqual([meter(lost, 100, 8) for lost in (0, 1, 50, 99, 100)], [0, 1, 4, 7, 8])
        self.assertEqual(meter(0, 0, 8), 0)

    def test_status_query_and_reverse_are_combined(self):
        monitors = [APP["Monitor"](name) for name in ("Router", "router-backup", "other", "router-pending")]
        for monitor, status, address in zip(
            monitors, ("OK", "TIMEOUT", "OK", "AGUARDE"),
            ("192.168.0.1", "192.168.0.2", "192.168.0.3", None),
        ):
            monitor.status, monitor.address = status, address
        visible = APP["visible_targets"]
        self.assertEqual(visible(monitors, "ROUTER", 0, True), [3, 1, 0])
        self.assertEqual(visible(monitors, "192.168.0.", 1, True), [2, 0])
        self.assertEqual(visible(monitors, "router", 2, False), [1])
        self.assertEqual(visible(monitors, "sem correspondência", 0, False), [])


class TerminalSession:
    def __init__(self, rows, columns, *targets):
        self.master, slave = pty.openpty()
        try:
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, columns, 0, 0))
            self.process = subprocess.Popen(
                [PROGRAM, *targets], stdin=slave, stdout=slave, stderr=slave,
                env={**os.environ, "TERM": "xterm-256color", "LC_ALL": "C.UTF-8"},
            )
        finally:
            os.close(slave)
        self.pending = b""

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait()
        os.close(self.master)

    def expect(self, marker, timeout=7):
        marker = marker.encode()
        deadline = time.monotonic() + timeout
        while marker not in self.pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.master], [], [], remaining)[0]:
                raise AssertionError(f"{marker!r} ausente em {self.pending[-1200:]!r}")
            try:
                chunk = os.read(self.master, 65536)
            except OSError as error:
                if error.errno != errno.EIO:
                    raise
                chunk = b""
            if not chunk:
                raise AssertionError(f"terminal fechou antes de {marker!r}: {self.pending[-1600:]!r}")
            self.pending += chunk
        _, self.pending = self.pending.split(marker, 1)

    def send(self, keys):
        os.write(self.master, keys)

    def resize(self, rows, columns):
        fcntl.ioctl(self.master, termios.TIOCSWINSZ, struct.pack("HHHH", rows, columns, 0, 0))
        self.process.send_signal(signal.SIGWINCH)

    def finish(self):
        self.send(b"q")
        return self.process.wait(timeout=8)


@unittest.skipUnless(shutil.which("ping"), "iputils-ping indisponível")
class TerminalTest(unittest.TestCase):
    def test_pause_resume_and_menu_in_terminal(self):
        with TerminalSession(30, 150, "127.0.0.1") as terminal:
            terminal.expect("PINGTOP")
            terminal.expect("Alvos monitorados")
            terminal.send(b"p")
            terminal.expect("pausado")
            terminal.send(b"p")
            terminal.expect("ativo")
            terminal.send(b"m")
            terminal.expect("Limpar lista")
            self.assertEqual(terminal.finish(), 0)

    def test_switch_graph_mode_in_options(self):
        with TerminalSession(30, 150, "127.0.0.1") as terminal:
            terminal.expect("Alvos monitorados")
            terminal.send(b"m")
            terminal.expect("Opções")
            terminal.send(b"\n")
            terminal.expect("Micro")
            terminal.send(b"\x1bOB\x1bOB\x1bOC")
            terminal.expect("Quadrantes")
            terminal.send(b"\x1bOD")
            terminal.expect("Micro")
            self.assertEqual(terminal.finish(), 0)

    def test_live_filter_cancel_and_status_switch(self):
        with TerminalSession(30, 150, "127.0.0.1", "127.0.0.2") as terminal:
            terminal.expect("Alvos monitorados")
            terminal.send(b"fxyz")
            terminal.expect("Nenhum alvo neste filtro.")
            terminal.send(b"\x1b")
            terminal.expect("127.0.0.1")
            terminal.send(b"/127.0.0.2\n")
            terminal.expect("Filtro:")
            terminal.send(b"\x1b[3~rs")
            terminal.expect("Com resposta")
            terminal.send(b"s")
            terminal.expect("Nenhum alvo neste filtro.")
            self.assertEqual(terminal.finish(), 0)

    def test_toggle_theme_background(self):
        with TerminalSession(30, 150, "127.0.0.1") as terminal:
            terminal.expect("Alvos monitorados")
            terminal.send(b"m\n")
            terminal.expect("Sim")
            terminal.send(b"\x1bOA\x1bOC")
            terminal.expect("Não")
            terminal.send(b"\x1bOC")
            terminal.expect("Sim")
            self.assertEqual(terminal.finish(), 0)

    def test_resize_and_return_to_dashboard(self):
        with TerminalSession(30, 150, "127.0.0.1") as terminal:
            terminal.expect("Alvos monitorados")
            terminal.resize(10, 38)
            terminal.expect("Amplie o terminal")
            terminal.resize(20, 60)
            terminal.expect("Alvos monitorados")
            self.assertEqual(terminal.finish(), 0)

    def test_range_addition_deduplicates_and_clear_list_requires_confirmation(self):
        with TerminalSession(30, 150, "127.0.0.1") as terminal:
            terminal.expect("Alvos monitorados")
            terminal.send(b"a")
            terminal.expect("Alvo:")
            terminal.send(b"127.0.0.1-127.0.0.2\n")
            terminal.expect("adicionado")
            terminal.send(b"m")
            terminal.expect("Limpar lista")
            terminal.send(b"\x1bOB\x1bOB\n")
            terminal.expect("Cancelar")
            terminal.send(b"\n")
            terminal.expect("Opções")
            terminal.send(b"\x1bOB\x1bOB\n")
            terminal.expect("Limpar tudo")
            terminal.send(b"\x1bOB\n")
            terminal.expect("Lista limpa.")
            self.assertEqual(terminal.finish(), 0)

    @unittest.skipUnless(shutil.which("traceroute"), "traceroute indisponível")
    def test_loopback_route_preserves_three_probes(self):
        hops, error = APP["trace"]("127.0.0.1")
        if error:
            self.skipTest(f"ICMP traceroute indisponível neste ambiente: {error}")
        self.assertTrue(hops)
        self.assertEqual(hops[0][0], 1)
        self.assertEqual(len(hops[0][1]), 3)
        self.assertTrue(all(probe[1] == "127.0.0.1" for probe in hops[0][1]))
        with TerminalSession(35, 160, "127.0.0.1") as terminal:
            terminal.expect("Tracert")
            terminal.send(b"t")
            terminal.expect("salto 1")
            terminal.send(b"\t")
            terminal.expect("alvo")
            self.assertEqual(terminal.finish(), 0)



if __name__ == "__main__":
    unittest.main()
