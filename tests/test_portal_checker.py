import os
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.portal_checker import (
    PortalCheckResult,
    StalkerPortalChecker,
    check_single_portal,
    load_portal_list,
    normalize_portal_url,
    save_reachable_portals_file,
)


class TestPortalChecker(unittest.TestCase):
    def test_01_normalize_portal_url(self):
        self.assertEqual(normalize_portal_url("vip.bmbtv.me:15000/c"), "http://vip.bmbtv.me:15000/c")
        self.assertEqual(normalize_portal_url("https://c44k.net/c/"), "https://c44k.net/c")
        self.assertEqual(normalize_portal_url("http://example.com"), "http://example.com/c")
        self.assertEqual(normalize_portal_url("http://portal.com:8080/portal.php"), "http://portal.com:8080/portal.php")
        self.assertEqual(normalize_portal_url(""), "")

    def test_02_load_and_save_portal_list(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tf:
            tf.write("# Stalker Portals Test\n")
            tf.write("http://portal1.com/c\n")
            tf.write("\n")
            tf.write("portal2.com/c\n")
            tf.write("http://portal1.com/c/\n")  # duplicate
            temp_path = tf.name

        try:
            portals = load_portal_list(temp_path)
            self.assertEqual(len(portals), 2)
            self.assertIn("http://portal1.com/c", portals)
            self.assertIn("http://portal2.com/c", portals)

            # Test save
            save_path = temp_path + ".saved.txt"
            ok = save_reachable_portals_file(save_path, portals)
            self.assertTrue(ok)
            loaded_saved = load_portal_list(save_path)
            self.assertEqual(loaded_saved, portals)
            if os.path.exists(save_path):
                os.remove(save_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_03_check_single_portal_online_and_stalker(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Server": "nginx/1.18.0", "Content-Type": "text/html"}
        mock_resp.text = "<html><title>Ministra Infomir Portal</title></html>"
        mock_resp.cookies = []

        with patch("requests.Session.get", return_value=mock_resp):
            res = check_single_portal("http://vip.testportal.com/c", timeout=2.0)
            self.assertTrue(res.is_online)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.server, "nginx/1.18.0")
            self.assertTrue(res.stalker_detected)
            self.assertIn("🟢", res.display_status())

    def test_04_check_single_portal_timeout_and_error(self):
        import requests
        with patch("requests.Session.get", side_effect=requests.exceptions.ConnectTimeout("Connection timed out")):
            res = check_single_portal("http://deadportal.com/c", timeout=1.0)
            self.assertFalse(res.is_online)
            self.assertIn("Timeout", res.error)
            self.assertIn("⏳", res.display_status())

    def test_05_stalker_portal_checker_engine_multithreaded(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Server": "Apache"}
        mock_resp.text = "Stalker STB Web"
        mock_resp.cookies = []

        results = []
        progress_calls = []
        finished_results = []
        finished_reachables = []

        checker = StalkerPortalChecker()
        checker.on_portal_result = results.append
        checker.on_progress = lambda d, t, on, off, cps: progress_calls.append((d, t, on, off))
        checker.on_finished = lambda res, reach: (finished_results.extend(res), finished_reachables.extend(reach))

        urls = [f"http://test-portal-{i}.com/c" for i in range(5)]

        with patch("requests.Session.get", return_value=mock_resp):
            checker.start_check(urls, threads=3, timeout=1.0)

            # Warte bis Fertigstellung
            deadline = time.time() + 5.0
            while checker.is_running and time.time() < deadline:
                time.sleep(0.05)

        self.assertFalse(checker.is_running)
        self.assertEqual(len(results), 5)
        self.assertEqual(len(finished_reachables), 5)
        self.assertTrue(all(r.is_online for r in results))
        self.assertGreater(len(progress_calls), 0)

    def test_06_scanner_view_portal_rotation_ui(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])

        from ui.views.scanner_view import ScannerView
        sv = ScannerView()
        try:
            # 1. Test: Setze erreichbare Portale
            portals = ["http://portal-alpha.com/c", "http://portal-beta.com/c"]
            sv.set_reachable_portals(portals)
            self.assertEqual(len(sv.get_reachable_portals()), 2)
            self.assertIn("2", sv.combo_portal_selector.itemText(1))

            # 2. Test: Rotation aktivieren
            sv.chk_portal_rotation.setChecked(True)
            self.assertEqual(sv.combo_portal_selector.currentIndex(), 1)
            self.assertFalse(sv.entry_portal.isEnabled())

            # 3. Test: Start Scan mit Rotation emittiert Signal mit Portalliste
            sig_received = []
            sv.start_scan_requested.connect(
                lambda u, m, mod, th, d, rot, mode: sig_received.append((u, m, mod, th, d, rot, mode))
            )
            sv.txt_macs.setPlainText("00:1A:79:AA:BB:CC\n00:1A:79:DD:EE:FF")
            sv.combo_rotation_mode.setCurrentText("Round-Robin (Verteilt)")
            sv._on_start_clicked()

            self.assertEqual(len(sig_received), 1)
            sig_u, sig_macs, sig_mod, sig_th, sig_d, sig_rot, sig_mode = sig_received[0]
            self.assertEqual(len(sig_macs), 2)
            self.assertEqual(len(sig_rot), 2)
            self.assertEqual(sig_mode, "round_robin")
            self.assertEqual(sig_u, "http://portal-alpha.com/c")

            # 4. Test: Doppelklick auf Portal in Tabelle
            res_item = PortalCheckResult(
                url="http://portal-gamma.com/c",
                host="portal-gamma.com",
                port=80,
                is_online=True,
                status_code=200,
            )
            sv._append_portal_row(res_item)
            last_row = sv.table_portals.rowCount() - 1
            sv._on_portal_row_double_clicked(last_row, 1)
            self.assertEqual(sv.entry_portal.text(), "http://portal-gamma.com/c")
            self.assertFalse(sv.chk_portal_rotation.isChecked())
        finally:
            sv.close()

    def test_07_main_window_start_mac_scan_multi_portal_rotation(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])

        from ui.main_window import MainWindow
        from core.signals import event_bus

        win = MainWindow()
        try:
            portal_calls = []

            def mock_check(portal_url, mac, **kwargs):
                portal_calls.append((portal_url, mac))
                return {
                    "mac": mac,
                    "portal_url": portal_url,
                    "valid": True,
                    "status": "Aktiv",
                    "channels": 50,
                    "expire": "2027-01-01",
                }

            with patch("ui.main_window.check_mac_account", side_effect=mock_check):
                results_received = []
                event_bus.scan_result_received.connect(results_received.append)

                rotation_portals = ["http://rot1.com/c", "http://rot2.com/c"]
                macs = ["00:1A:79:11:11:11", "00:1A:79:22:22:22"]

                # 1. Test Round-Robin: 2 MACs auf 2 Portale verteilt
                win.start_mac_scan(
                    portal_url=rotation_portals[0],
                    mac_list=macs,
                    model="MAG 250",
                    threads=2,
                    delay_s=0.0,
                    portal_rotation_list=rotation_portals,
                    rotation_mode="round_robin",
                )

                deadline = time.time() + 5.0
                while time.time() < deadline and len(results_received) < 2:
                    time.sleep(0.05)
                    app.processEvents()

                win.stop_mac_scan()
                self.assertEqual(len(results_received), 2)
                called_ports = {c[0] for c in portal_calls}
                self.assertIn("http://rot1.com/c", called_ports)
                self.assertIn("http://rot2.com/c", called_ports)
        finally:
            win.stop_mac_scan()
            win.close()


if __name__ == "__main__":
    unittest.main()
