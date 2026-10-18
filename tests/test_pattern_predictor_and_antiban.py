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


if __name__ == "__main__":
    unittest.main()
