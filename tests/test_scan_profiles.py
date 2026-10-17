import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scan_repository import ScanRepository, ScanHost, ScanAccount


class TestScanProfiles(unittest.TestCase):
    def setUp(self):
        self.repo = ScanRepository()

    def test_01_repo_loads_known_hosts(self):
        hosts = self.repo.get_hosts()
        self.assertGreater(len(hosts), 0, "ScanRepository sollte mindestens 1 Host finden")

        # Prüfe ob clubxc.com oder t-rex4k.top gefunden wird
        host_names = [h.host_name.lower() for h in hosts]
        self.assertTrue(any("clubxc.com" in n for n in host_names), f"clubxc.com erwartet in {host_names}")

    def test_02_host_accounts_parsed_and_sorted_by_channels(self):
        host = self.repo.get_host("clubxc.com")
        self.assertIsNotNone(host)
        self.assertGreater(len(host.accounts), 10, "clubxc.com sollte viele Accounts haben")

        # Prüfe, dass die Accounts nach Channels absteigend sortiert sind
        first_acc = host.accounts[0]
        second_acc = host.accounts[1]
        self.assertGreaterEqual(first_acc.channels, second_acc.channels)
        self.assertGreater(first_acc.channels, 0)
        self.assertTrue(first_acc.mac.startswith("00:") or ":" in first_acc.mac)
        self.assertTrue(first_acc.portal_url.startswith("http"))

    def test_03_create_profile_from_scan(self):
        host = self.repo.get_hosts()[0]
        acc = host.accounts[0]
        prof = self.repo.create_profile(host.host_name, acc.mac)
        self.assertIsNotNone(prof)
        self.assertEqual(prof.mac, acc.mac)
        self.assertEqual(prof.portal_url, acc.portal_url)
        self.assertEqual(prof.provider_type, "Stalker MAC")


if __name__ == "__main__":
    unittest.main()
