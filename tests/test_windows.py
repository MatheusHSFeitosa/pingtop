import runpy
import unittest
from pathlib import Path

APP = runpy.run_path(str(Path(__file__).resolve().parents[1] / "pingtop"))


class WindowsParsersTest(unittest.TestCase):
    def test_localized_ping(self):
        parse = APP["parse_windows_ping"]
        for message in (
            "Reply from 127.0.0.1: bytes=32 time<1ms TTL=128",
            "Resposta de 127.0.0.1: bytes=32 tempo<1ms TTL=128",
        ):
            self.assertEqual(parse(message, "localhost", "12:00:00"),
                             ("OK", 1.0, "127.0.0.1", "12:00:00", (32, 128)))

    def test_ipv6_ping_without_ttl(self):
        self.assertEqual(APP["parse_windows_ping"]("Reply from ::1: time=2ms", "::1", "12:00:00"),
                         ("OK", 2.0, "::1", "12:00:00", (None, None)))

    def test_route_three_probes(self):
        rows = """  1     <1 ms     2 ms     *     gateway [192.0.2.1]
  2      *        *        *     Esgotado o tempo limite.
  3      4 ms     5 ms     6 ms  2001:db8::1
"""
        hops = APP["parse_windows_route"](rows, "12:00:00")
        self.assertEqual([hop[0] for hop in hops], [1, 2, 3])
        self.assertEqual(hops[0][1], (("gateway", "192.0.2.1", 1.0),
                                     ("gateway", "192.0.2.1", 2.0),
                                     (None, None, None)))
        self.assertEqual(hops[1][1], ((None, None, None),) * 3)
        self.assertEqual(hops[2][1][2], ("2001:db8::1", "2001:db8::1", 6.0))

    def test_nslookup_passes_selected_server_to_native_command(self):
        from subprocess import CompletedProcess
        from unittest.mock import Mock, patch

        lookup = APP["dns_lookup"]
        native = Mock(return_value=CompletedProcess([], 0, "Server: 192.0.2.53\n", ""))
        with patch.dict(lookup.__globals__, {"WINDOWS": True, "windows_command": native}):
            self.assertEqual(lookup("example.test", "192.0.2.53"), ["Server: 192.0.2.53"])
        native.assert_called_once_with("nslookup.exe", "-timeout=2", "-retry=1",
                                       "example.test", "192.0.2.53", timeout=7)
