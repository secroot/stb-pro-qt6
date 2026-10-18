import os
import sys
import threading
import time
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scan_scheduler import MultiPortalScanScheduler, ScanRotationMode


class TestScanScheduler(unittest.TestCase):
    def setUp(self):
        self.portals = [
            "http://portal-a.com/c",
            "http://portal-b.com/c",
            "http://portal-c.com/c",
        ]
        self.macs = [f"00:1A:79:00:00:{i:02X}" for i in range(1, 21)]

    def test_01_mode_labels_and_descriptions(self):
        self.assertEqual(ScanRotationMode.from_ui_label("Hot-Spot Affinity (Bei Hit fokussieren)"), ScanRotationMode.HOT_SPOT)
        self.assertEqual(ScanRotationMode.from_ui_label("Round-Robin (Verteilt)"), ScanRotationMode.ROUND_ROBIN)
        self.assertEqual(ScanRotationMode.from_ui_label("Smart Adaptive (Hit-Rate gewichtet)"), ScanRotationMode.ADAPTIVE)
        self.assertEqual(ScanRotationMode.from_ui_label("Failover bei Fehler (Auto-Switch)"), ScanRotationMode.FAILOVER)
        self.assertEqual(ScanRotationMode.from_ui_label("Sweep (Alle Portale)"), ScanRotationMode.SWEEP)
        self.assertEqual(ScanRotationMode.from_ui_label("Sweep (Stopp bei erstem Hit)"), ScanRotationMode.SWEEP_EARLY_EXIT)
        self.assertEqual(ScanRotationMode.from_ui_label("Unknown"), ScanRotationMode.ROUND_ROBIN)

        desc = ScanRotationMode.describe(ScanRotationMode.HOT_SPOT)
        self.assertIn("Hot-Spot", desc)

    def test_02_round_robin_distribution(self):
        scheduler = MultiPortalScanScheduler(
            portals=self.portals,
            macs=self.macs[:6],
            mode=ScanRotationMode.ROUND_ROBIN,
        )
        self.assertEqual(scheduler.total_checks, 6)

        assigned = []
        while True:
            item = scheduler.get_next_work_item()
            if not item:
                break
            assigned.append(item)
            scheduler.report_result(item[1], item[0], {"valid": False, "status": "Ungültig"})

        self.assertEqual(len(assigned), 6)
        self.assertEqual(assigned[0][1], self.portals[0])
        self.assertEqual(assigned[1][1], self.portals[1])
        self.assertEqual(assigned[2][1], self.portals[2])
        self.assertEqual(assigned[3][1], self.portals[0])
        self.assertEqual(assigned[4][1], self.portals[1])
        self.assertEqual(assigned[5][1], self.portals[2])

        done, total = scheduler.get_progress()
        self.assertEqual(done, 6)
        self.assertEqual(total, 6)
        self.assertTrue(scheduler.is_exhausted())

    def test_03_hot_spot_affinity_focus_and_recovery(self):
        logs = []
        scheduler = MultiPortalScanScheduler(
            portals=self.portals,
            macs=self.macs[:10],
            mode=ScanRotationMode.HOT_SPOT,
            hot_spot_burst=3,
            on_log=logs.append,
        )

        # 1. Erstes Item holt Portal A
        m1, p1 = scheduler.get_next_work_item()
        self.assertEqual(p1, self.portals[0])
        # Kein Hit auf Portal A
        scheduler.report_result(p1, m1, {"valid": False, "channels": 0, "status": "Ungültig"})

        # 2. Zweites Item holt Portal B
        m2, p2 = scheduler.get_next_work_item()
        self.assertEqual(p2, self.portals[1])
        # HOT HIT auf Portal B!
        scheduler.report_result(p2, m2, {"tag": "hot", "valid": True, "channels": 500, "status": "Aktiv"})

        # Jetzt muss Hot-Spot aktiv sein
        self.assertEqual(scheduler.active_hot_portal, self.portals[1])
        self.assertEqual(scheduler.hot_spot_remaining, 3)

        # 3. Nächste 3 Items MÜSSEN alle auf Portal B gehen (Burst = 3)
        m3, p3 = scheduler.get_next_work_item()
        self.assertEqual(p3, self.portals[1])
        scheduler.report_result(p3, m3, {"valid": False, "channels": 0})

        m4, p4 = scheduler.get_next_work_item()
        self.assertEqual(p4, self.portals[1])
        scheduler.report_result(p4, m4, {"valid": False, "channels": 0})

        m5, p5 = scheduler.get_next_work_item()
        self.assertEqual(p5, self.portals[1])
        scheduler.report_result(p5, m5, {"valid": False, "channels": 0})

        # Nach Ablauf des Bursts ist Hot-Spot beendet
        self.assertIsNone(scheduler.active_hot_portal)

        # 4. Item 6 kehrt zur regulären Rotation zurück (Portal C)
        m6, p6 = scheduler.get_next_work_item()
        self.assertEqual(p6, self.portals[2])
        scheduler.report_result(p6, m6, {"valid": False, "channels": 0})

    def test_04_hot_spot_burst_extension_and_error_abort(self):
        logs = []
        scheduler = MultiPortalScanScheduler(
            portals=self.portals,
            macs=self.macs[:10],
            mode=ScanRotationMode.HOT_SPOT,
            hot_spot_burst=4,
            on_log=logs.append,
        )

        m1, p1 = scheduler.get_next_work_item()
        # Hit erzeugen
        scheduler.report_result(p1, m1, {"tag": "hot", "channels": 100})
        self.assertEqual(scheduler.active_hot_portal, p1)
        self.assertEqual(scheduler.hot_spot_remaining, 4)

        # Weiteres Item auf Portal A
        m2, p2 = scheduler.get_next_work_item()
        self.assertEqual(p2, p1)
        self.assertEqual(scheduler.hot_spot_remaining, 3)

        # Zweiter Hit verlängert Burst (+10)
        scheduler.report_result(p2, m2, {"tag": "hot", "channels": 120})
        self.assertEqual(scheduler.hot_spot_remaining, 13)

        # Wenn nun ein Serverfehler (z. B. 429 Rate Limit) auftritt: sofortiger Abbruch des Hot-Spots
        m3, p3 = scheduler.get_next_work_item()
        scheduler.report_result(p3, m3, {"valid": False, "status": "429 Too Many Requests", "error": "Rate Limited"})
        self.assertIsNone(scheduler.active_hot_portal)
        self.assertEqual(scheduler.hot_spot_remaining, 0)

    def test_05_adaptive_scoring_and_weights(self):
        logs = []
        scheduler = MultiPortalScanScheduler(
            portals=self.portals,
            macs=self.macs[:10],
            mode=ScanRotationMode.ADAPTIVE,
            on_log=logs.append,
        )

        # Initial weights
        for p in self.portals:
            self.assertEqual(scheduler.portal_weights[p], 1.0)

        # Hot hit auf Portal A erhöht Score
        scheduler.report_result(self.portals[0], "00:1A:79:00:00:01", {"tag": "hot", "channels": 300})
        self.assertEqual(scheduler.portal_weights[self.portals[0]], 4.0)

        # Fehler auf Portal B halbiert Score
        scheduler.report_result(self.portals[1], "00:1A:79:00:00:02", {"error": "Timeout 504", "status": "Timeout"})
        self.assertEqual(scheduler.portal_weights[self.portals[1]], 0.5)

    def test_06_failover_automatic_switch(self):
        logs = []
        scheduler = MultiPortalScanScheduler(
            portals=self.portals,
            macs=self.macs[:10],
            mode=ScanRotationMode.FAILOVER,
            failover_threshold=3,
            on_log=logs.append,
        )

        # Primäres Portal ist index 0
        self.assertEqual(scheduler.get_active_portal(), self.portals[0])

        m1, p1 = scheduler.get_next_work_item()
        self.assertEqual(p1, self.portals[0])
        # Fehler 1
        scheduler.report_result(p1, m1, {"error": "ConnectionError", "status": "503 Service Unavailable"})
        self.assertEqual(scheduler.current_primary_index, 0)

        m2, p2 = scheduler.get_next_work_item()
        # Fehler 2
        scheduler.report_result(p2, m2, {"error": "Timeout", "status": "504 Gateway Timeout"})
        self.assertEqual(scheduler.current_primary_index, 0)

        m3, p3 = scheduler.get_next_work_item()
        # Fehler 3 -> Schwellenwert 3 erreicht -> Umschalten auf Portal 1 (Portal B)!
        scheduler.report_result(p3, m3, {"error": "WAF Block", "status": "429 Too Many Requests"})
        self.assertEqual(scheduler.current_primary_index, 1)
        self.assertEqual(scheduler.get_active_portal(), self.portals[1])

        # Nächstes Item MUSS auf Portal B gehen
        m4, p4 = scheduler.get_next_work_item()
        self.assertEqual(p4, self.portals[1])

    def test_07_sweep_exhaustive_matrix(self):
        scheduler = MultiPortalScanScheduler(
            portals=self.portals[:2],
            macs=self.macs[:3],
            mode=ScanRotationMode.SWEEP,
        )
        self.assertEqual(scheduler.total_checks, 6)

        checks = []
        while True:
            item = scheduler.get_next_work_item()
            if not item:
                break
            checks.append(item)
            scheduler.report_result(item[1], item[0], {"valid": False})

        self.assertEqual(len(checks), 6)
        done, total = scheduler.get_progress()
        self.assertEqual(done, 6)
        self.assertEqual(total, 6)

    def test_08_sweep_early_exit_on_first_hit(self):
        logs = []
        scheduler = MultiPortalScanScheduler(
            portals=self.portals,
            macs=["00:1A:79:00:00:01", "00:1A:79:00:00:02"],
            mode=ScanRotationMode.SWEEP_EARLY_EXIT,
            on_log=logs.append,
        )
        # Total initial: 2 MACs * 3 Portale = 6
        self.assertEqual(scheduler.total_checks, 6)

        # 1. MAC 1 auf Portal A -> HIT!
        m1, p1 = scheduler.get_next_work_item()
        self.assertEqual(m1, "00:1A:79:00:00:01")
        self.assertEqual(p1, self.portals[0])
        scheduler.report_result(p1, m1, {"tag": "hot", "channels": 100})

        # Da MAC 1 nun solved ist, müssen die verbleibenden 2 Checks für MAC 1 (Portal B und C) übersprungen werden!
        # Das nächste Item muss direkt MAC 2 sein
        m2, p2 = scheduler.get_next_work_item()
        self.assertEqual(m2, "00:1A:79:00:00:02")
        self.assertEqual(p2, self.portals[0])
        scheduler.report_result(p2, m2, {"valid": False, "channels": 0})

        # MAC 2 auf Portal B
        m3, p3 = scheduler.get_next_work_item()
        self.assertEqual(m3, "00:1A:79:00:00:02")
        self.assertEqual(p3, self.portals[1])
        scheduler.report_result(p3, m3, {"valid": False, "channels": 0})

        # MAC 2 auf Portal C
        m4, p4 = scheduler.get_next_work_item()
        self.assertEqual(m4, "00:1A:79:00:00:02")
        self.assertEqual(p4, self.portals[2])
        scheduler.report_result(p4, m4, {"valid": False, "channels": 0})

        # Nun muss die Queue erschöpft sein
        self.assertIsNone(scheduler.get_next_work_item())
        done, total = scheduler.get_progress()
        # 4 tatsächlich bearbeitete + 2 übersprungene = 6 (100%)
        self.assertEqual(done, 6)
        self.assertEqual(total, 6)
        self.assertEqual(scheduler.skipped_count, 2)
        self.assertTrue(scheduler.is_exhausted())

    def test_09_multithreaded_concurrency(self):
        """Testet threadsichere Abarbeitung mit 8 parallelen Worker-Threads."""
        scheduler = MultiPortalScanScheduler(
            portals=self.portals,
            macs=self.macs,
            mode=ScanRotationMode.HOT_SPOT,
            hot_spot_burst=5,
        )

        completed_items = []
        lock = threading.Lock()

        def worker():
            while True:
                item = scheduler.get_next_work_item()
                if item is None:
                    if scheduler.is_exhausted():
                        break
                    time.sleep(0.01)
                    continue

                mac, portal = item
                with lock:
                    completed_items.append((mac, portal))

                # Simuliere Arbeit
                time.sleep(0.005)
                # Jeder 5. Check liefert einen Hot Hit
                is_hit = (len(completed_items) % 5 == 0)
                res = {
                    "tag": "hot" if is_hit else "invalid",
                    "valid": is_hit,
                    "channels": 50 if is_hit else 0,
                    "status": "Aktiv" if is_hit else "Ungültig",
                }
                scheduler.report_result(portal, mac, res)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        self.assertEqual(len(completed_items), len(self.macs))
        done, total = scheduler.get_progress()
        self.assertEqual(done, len(self.macs))
        self.assertEqual(total, len(self.macs))
        self.assertTrue(scheduler.is_exhausted())

    def test_10_main_window_start_mac_scan_hot_spot_integration(self):
        from PySide6.QtWidgets import QApplication
        from unittest.mock import patch
        app = QApplication.instance() or QApplication([])

        from ui.main_window import MainWindow
        from core.signals import event_bus

        win = MainWindow()
        try:
            portal_calls = []

            def mock_check(portal_url, mac, **kwargs):
                portal_calls.append((portal_url, mac))
                is_hit = (mac == "00:1A:79:00:00:01")
                return {
                    "mac": mac,
                    "portal_url": portal_url,
                    "valid": is_hit,
                    "status": "Aktiv" if is_hit else "Ungültig",
                    "channels": 100 if is_hit else 0,
                    "expire": "2027-01-01",
                }

            with patch("ui.main_window.check_mac_account", side_effect=mock_check), \
                 patch.object(win.mac_db, "save_found_mac", return_value=True):
                results_received = []
                event_bus.scan_result_received.connect(results_received.append)

                rotation_portals = ["http://rot1.com/c", "http://rot2.com/c"]
                test_macs = ["00:1A:79:00:00:01", "00:1A:79:00:00:02", "00:1A:79:00:00:03"]

                win.start_mac_scan(
                    portal_url=rotation_portals[0],
                    mac_list=test_macs,
                    model="MAG 250",
                    threads=1,
                    delay_s=0.0,
                    portal_rotation_list=rotation_portals,
                    rotation_mode="hot_spot",
                )

                deadline = time.time() + 5.0
                while time.time() < deadline and len(results_received) < len(test_macs):
                    time.sleep(0.05)
                    app.processEvents()

                win.stop_mac_scan()
                self.assertEqual(len(results_received), len(test_macs))
                # Weil MAC 1 auf rot1.com einen Hit liefert, müssen die nachfolgenden MACs 2 und 3
                # dank Hot-Spot Affinity ebenfalls auf rot1.com geprüft worden sein!
                self.assertEqual(portal_calls[0][0], "http://rot1.com/c")
                self.assertEqual(portal_calls[1][0], "http://rot1.com/c")
                self.assertEqual(portal_calls[2][0], "http://rot1.com/c")
        finally:
            win.stop_mac_scan()
            win.close()


if __name__ == "__main__":
    unittest.main()
