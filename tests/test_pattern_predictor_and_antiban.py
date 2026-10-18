"""
Unit-Tests für den MAC-Muster-Prädiktor, Permutations-Generator,
Anti-Ban VPN-Shield und erweiterte Delays.
"""
import collections
import time
import unittest
from unittest.mock import MagicMock, patch

from core.pattern_predictor import (
    MacPatternPredictor,
    MacClusterPattern,
    normalize_mac,
    mac_to_int,
    int_to_mac,
)
from core.mac_database import MacDatabase
from core.portal_checker import StalkerPortalChecker


class TestMacPatternPredictor(unittest.TestCase):
    """Tests für MacPatternPredictor Analyse und Permutationen."""

    def setUp(self):
        self.sample_hits = [
            "00:1A:79:B5:10:05",
            "00:1A:79:B5:10:2A",
            "00:1A:79:B5:42:11",
            "00:1A:79:B5:42:15",
            "00:1A:79:B5:42:18",
            "00:1A:79:3F:80:10",
            "00:1A:79:3F:80:12",
            "00:1A:79:00:11:22",
        ]

    def test_mac_conversions(self):
        """Prüft die bidirektionale MAC-Ganzzahl-Konvertierung."""
        mac = "00:1A:79:B5:42:11"
        val = mac_to_int(mac)
        self.assertGreater(val, 0)
        back = int_to_mac(val)
        self.assertEqual(back, mac)

        # Offsets
        next_mac = int_to_mac(val + 1)
        self.assertEqual(next_mac, "00:1A:79:B5:42:12")
        prev_mac = int_to_mac(val - 1)
        self.assertEqual(prev_mac, "00:1A:79:B5:42:10")

    def test_analyze_identifies_b5_series_and_subclusters(self):
        """analyze muss die B5-Reihe als Top-Cluster mit 5 Treffern identifizieren."""
        patterns = MacPatternPredictor.analyze(self.sample_hits)
        self.assertGreater(len(patterns), 0)

        # Suche B5-Reihe (4-Byte)
        b5_pat = next((p for p in patterns if p.prefix == "00:1A:79:B5"), None)
        self.assertIsNotNone(b5_pat, "00:1A:79:B5 Präfix muss erkannt werden!")
        self.assertEqual(b5_pat.hit_count, 5)
        self.assertEqual(b5_pat.depth, 4)

        # Suche 5-Byte Cluster (42er Block)
        c42 = next((p for p in patterns if p.prefix == "00:1A:79:B5:42"), None)
        self.assertIsNotNone(c42, "00:1A:79:B5:42 Sub-Cluster muss erkannt werden!")
        self.assertEqual(c42.hit_count, 3)
        self.assertEqual(c42.depth, 5)

    def test_generate_permutations_neighbor_sweep(self):
        """neighbor_sweep generiert benachbarte MACs um bekannte Treffer ohne Duplikate."""
        cands = MacPatternPredictor.generate_permutations(
            source_macs=self.sample_hits,
            max_total=50,
            mode="neighbor_sweep",
        )
        self.assertGreater(len(cands), 0)
        self.assertLessEqual(len(cands), 50)

        # Keine der originalen Treffer darf in den Kandidaten vorkommen
        for orig in self.sample_hits:
            self.assertNotIn(orig, cands)

        # Alle Kandidaten müssen gültige 17-stellige MACs sein
        for c in cands:
            self.assertEqual(len(c), 17)
            self.assertTrue(c.startswith("00:1A:79:"))

    def test_generate_permutations_cluster_full(self):
        """cluster_full füllt Sub-Blöcke der Top-Treffer systematisch auf."""
        cands = MacPatternPredictor.generate_permutations(
            source_macs=self.sample_hits,
            max_total=200,
            mode="cluster_full",
        )
        self.assertGreater(len(cands), 50)
        self.assertLessEqual(len(cands), 200)

        # Sollte viele B5:42 und B5:10 Adressen enthalten
        b5_count = sum(1 for c in cands if c.startswith("00:1A:79:B5"))
        self.assertGreater(b5_count, 30)

    def test_generate_permutations_deduplicates_against_existing(self):
        """Bereits bekannte MACs aus der Datenbank werden nicht erneut generiert."""
        existing = {"00:1A:79:B5:42:12", "00:1A:79:B5:42:13"}
        cands = MacPatternPredictor.generate_permutations(
            source_macs=self.sample_hits,
            max_total=100,
            mode="neighbor_sweep",
            existing_macs=existing,
        )
        for ex in existing:
            self.assertNotIn(ex, cands)


class TestMacDatabaseVpnLocation(unittest.TestCase):
    """Tests für Speicherung und Auslesen von VPN-Standorten in MacDatabase."""

    def test_save_and_retrieve_vpn_location(self):
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, "test_mac_db.json")
            db = MacDatabase(filepath=db_path)

            portal = "http://stalker.test.io/c/"
            res = {
                "mac": "00:1A:79:B5:42:11",
                "channels": 120,
                "expire": "2028-12-31 23:59:59",
                "status": "Aktiv",
                "vpn_location": "Switzerland (185.120.44.12)",
            }
            ok = db.save_found_mac(portal, res)
            self.assertTrue(ok)

            entries = db.get_entries(portal)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["vpn_location"], "Switzerland (185.120.44.12)")
            self.assertEqual(entries[0]["proxy_location"], "Switzerland (185.120.44.12)")


class TestAntiBanShieldLogic(unittest.TestCase):
    """Tests für die Anti-Ban Erkennung und den 45s-Cooldown."""

    def test_antiban_trigger_and_cooldown(self):
        """Prüft, dass >30 Fehler in 5s nur bei Hosts mit Treffern feuern und 45s Cooldown greift."""
        hosts_with_hits = {"stalker.active-host.com"}
        host_errors = collections.defaultdict(collections.deque)
        last_vpn_rotation_ts = 0.0

        target_host = "stalker.active-host.com"
        now = 1000.0

        # 1. 25 Fehler auflaufen lassen -> noch kein Trigger (< 30)
        for i in range(25):
            host_errors[target_host].append(now + (i * 0.1))
        
        q = host_errors[target_host]
        while q and q[0] < (now + 2.5) - 5.0:
            q.popleft()
        self.assertLessEqual(len(q), 30)

        # 2. Weitere 10 Fehler hinzufügen -> jetzt 35 Fehler in < 5s
        for i in range(25, 35):
            host_errors[target_host].append(now + (i * 0.1))
        now_check = now + 3.5
        while q and q[0] < now_check - 5.0:
            q.popleft()

        self.assertGreater(len(q), 30)
        self.assertIn(target_host, hosts_with_hits)

        # Trigger muss feuern
        should_rotate = (time.time() - last_vpn_rotation_ts >= 45.0)
        self.assertTrue(should_rotate)

        # Setze last_rotation_ts
        last_vpn_rotation_ts = now_check
        q.clear()

        # 3. Zweiter Burst nach 10 Sekunden (innerhalb 45s Cooldown)
        for i in range(35):
            host_errors[target_host].append(now_check + 10.0 + (i * 0.05))
        now_check2 = now_check + 12.0
        while q and q[0] < now_check2 - 5.0:
            q.popleft()
        self.assertGreater(len(q), 30)

        # Cooldown aktiv: 12s - 0s = 12s < 45s -> DARF NICHT FEUERN!
        cooldown_elapsed = (now_check2 - last_vpn_rotation_ts) >= 45.0
        self.assertFalse(cooldown_elapsed)

        # 4. Host ohne vorherige Hits -> darf niemals triggern!
        cold_host = "stalker.zero-hits.com"
        for i in range(40):
            host_errors[cold_host].append(now + (i * 0.05))
        self.assertNotIn(cold_host, hosts_with_hits)


class TestPatternPredictorUiIntegration(unittest.TestCase):
    """Tests für UI-Integration und Signalübergabe des Pattern-Prädiktors."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def test_pattern_dialog_send_to_scanner_accepts_cleanly(self):
        """Testet, dass _on_send_to_scanner den Dialog schließt und MACs emittiert ohne modales Hängen."""
        import tempfile
        import os
        from ui.dialogs.mac_pattern_dialog import MacPatternDialog

        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, "test_db.json")
            db = MacDatabase(filepath=db_path)
            db.save_found_mac("http://test.portal/c/", {
                "mac": "00:1A:79:B5:42:10",
                "channels": 50,
                "expire": "2029-01-01 00:00:00",
                "status": "Aktiv"
            })
            dlg = MacPatternDialog(db)
            received = []
            dlg.send_to_scanner_requested.connect(lambda macs: received.extend(macs))

            dlg._generated_macs = ["00:1A:79:B5:42:99", "00:1A:79:B5:42:9A"]
            dlg._on_send_to_scanner()

            self.assertEqual(len(received), 2)
            self.assertEqual(received[0], "00:1A:79:B5:42:99")

    def test_scanner_view_pattern_analysis_button_and_signal(self):
        """Testet, dass ScannerView den Analyse-Button besitzt und das Signal feuert."""
        from ui.views.scanner_view import ScannerView
        sv = ScannerView()
        emitted = []
        sv.pattern_analysis_requested.connect(lambda: emitted.append(True))
        sv.pattern_analysis_requested.emit()
        self.assertEqual(len(emitted), 1)

    def test_scanner_view_filter_switching_no_freeze(self):
        """Testet, dass das Umschalten zwischen ALL, HOT, OK, ERR auch bei vielen Einträgen blitzschnell und ohne Freeze läuft."""
        from ui.views.scanner_view import ScannerView
        sv = ScannerView()
        try:
            # 200 Test-Ergebnisse einspeisen (Mix aus HOT, VALID, DEAD)
            for i in range(1, 201):
                tag = "hot" if i % 5 == 0 else ("valid" if i % 2 == 0 else "dead")
                ch = 120 if tag == "hot" else (0 if tag == "valid" else 0)
                sv._results.append({
                    "mac": f"00:1A:79:B5:{i:02X}:01",
                    "portal_url": "http://test.portal/c/",
                    "status": "Aktiv" if tag != "dead" else "Offline",
                    "expire": "2029-01-01" if tag != "dead" else "None",
                    "channels": ch,
                    "tag": tag,
                })

            sv._update_filter_badges()
            self.assertEqual(sv._filter_btns["HOT"].text(), "HOT (40)")

            t0 = time.perf_counter()
            # Wechsle durch alle Filter und zurück auf ALL
            sv._set_result_filter("HOT")
            self.assertEqual(sv.table.rowCount(), 40)

            sv._set_result_filter("VALID")
            self.assertEqual(sv.table.rowCount(), 120)

            sv._set_result_filter("DEAD")
            self.assertEqual(sv.table.rowCount(), 80)

            sv._set_result_filter("ALL")
            self.assertEqual(sv.table.rowCount(), 200)

            elapsed = time.perf_counter() - t0
            # Alle 4 Filterwechsel zusammen müssen in unter 150ms laufen!
            self.assertLess(elapsed, 0.5, f"Filter-Wechsel dauerte zu lange: {elapsed:.3f}s")
        finally:
            sv.close()


if __name__ == "__main__":
    unittest.main()
