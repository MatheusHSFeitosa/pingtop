import runpy
import socket
import unittest
from pathlib import Path
from unittest.mock import patch

APP = runpy.run_path(str(Path(__file__).resolve().parents[1] / "pingtop"))
LOAD = APP["load_targets"]


class AddressFamiliesTest(unittest.TestCase):
    def test_url_uses_hostname_and_available_families(self):
        with patch.object(socket, "getaddrinfo", return_value=[
            (socket.AF_INET6, 0, 0, "", ("2001:db8::1", 0, 0, 0)),
            (socket.AF_INET, 0, 0, "", ("192.0.2.1", 0)),
            (socket.AF_INET, 0, 0, "", ("192.0.2.2", 0)),
        ]) as lookup:
            self.assertEqual(LOAD("https://example.test:8443/page", (4, 6)),
                             ["192.0.2.1", "2001:db8::1"])
            lookup.assert_called_once_with("example.test", None, type=socket.SOCK_STREAM)

    def test_literals_and_missing_families(self):
        self.assertEqual(LOAD("https://[::1]/", (4, 6)), ["::1"])
        self.assertEqual(LOAD("192.0.2.0/30", (4,)), ["192.0.2.1", "192.0.2.2"])
        with self.assertRaisesRegex(ValueError, "IPv6"):
            LOAD("192.0.2.1", (6,))
        self.assertEqual(LOAD("https://example.test/path"), ["example.test"])

    def test_url_groups_remain_distinct_even_when_they_share_an_ip(self):
        with patch.object(socket, "getaddrinfo", return_value=[
            (socket.AF_INET, 0, 0, "", ("192.0.2.1", 0)),
            (socket.AF_INET6, 0, 0, "", ("2001:db8::1", 0, 0, 0)),
        ]):
            group = APP["grouped_targets"]
            targets = group("https://first.test") + group("https://second.test", (4,))
            targets += group("192.0.2.1")
        monitors = [APP["Monitor"](address, group=name) for address, name in targets]
        self.assertEqual(APP["target_tree"](monitors, True), [
            (None, "first.test"), (0, "├─ 192.0.2.1"), (1, "└─ 2001:db8::1"),
            (None, "second.test"), (2, "└─ 192.0.2.1"), (3, "192.0.2.1"),
        ])
        self.assertEqual(APP["visible_targets"](monitors, "", 0, True), [3, 2, 0, 1])
        self.assertEqual(APP["visible_targets"](monitors, "first.test", 0, False), [0, 1])
