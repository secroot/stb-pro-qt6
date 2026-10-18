"""
Unit-Tests für die Validierung von Ablaufdaten (Expiration Dates) und
die Verhinderung von False-Positive Hot-Hits bei 0000000 / None / Unbekannt / abgelaufenen Accounts.
"""
import datetime
import os
import tempfile
import unittest
from unittest.mock import MagicMock

from core.models import is_valid_expire_date
from core.mac_database import MacDatabase
from core.scan_scheduler import MultiPortalScanScheduler, ScanRotationMode


class TestExpireDateValidation(unittest.TestCase):
    """Tests für is_valid_expire_date Hilfsfunktion."""

    def test_invalid_and_zero_dates(self):
        """Nullwerte, Nullen und Platzhalter müssen als ungültig erkannt werden."""
        invalid_values = [
            None,
            "",
            "   ",
            "0000000",
            "00000000",
            "0",
            "0000-00-00",
            "0000-00-00 00:00:00",
            "0000-00-00 00:00",
            "none",
            "None",
            "NONE",
            "null",
            "nil",
            "undefined",
            "Unbekannt",
            "unknown",
            "UNKNOWN",
            "-",
            "--",
            "n/a",
            "na",
            "N/A",
        ]
        for val in invalid_values:
            with self.subTest(val=val):
                self.assertFalse(
                    is_valid_expire_date(val),
                    f"Wert {val!r} sollte nicht als gültiges Ablaufdatum akzeptiert werden!"
                )

    def test_past_dates(self):
        """Vergangene Ablaufdaten müssen als abgelaufen (False) erkannt werden."""
        past_values = [
            "2020-01-01 00:00:00",
            "2022-05-15 12:30:00",
            "2024-12-31 23:59:59",
            "2025-01-01",
            "01.01.2023",
            "January 1, 2024",
            "March 10, 2025, 5:00 pm",
            1577836800,  # 2020-01-01
            "1577836800",
        ]
        for val in past_values:
            with self.subTest(val=val):
                self.assertFalse(
                    is_valid_expire_date(val),
                    f"Vergangenes Datum {val!r} sollte nicht als gültig akzeptiert werden!"
                )

    def test_future_valid_dates(self):
        """Zukünftige Daten müssen als aktiv und gültig erkannt werden."""
        now = datetime.datetime.now()
        future_dt_1 = now + datetime.timedelta(days=60)
        future_dt_2 = now + datetime.timedelta(days=365)
        future_values = [
            future_dt_1.strftime("%Y-%m-%d %H:%M:%S"),
            future_dt_1.strftime("%Y-%m-%d"),
            future_dt_2.strftime("%d.%m.%Y"),
            future_dt_2.strftime("%B %d, %Y, %I:%M %p"),
            "2028-12-31 23:59:59",
            "2029-06-15",
            int((now + datetime.timedelta(days=100)).timestamp()),
            str(int((now + datetime.timedelta(days=100)).timestamp())),
        ]
        for val in future_values:
            with self.subTest(val=val):
                self.assertTrue(
                    is_valid_expire_date(val),
                    f"Zukünftiges Datum {val!r} sollte als gültig akzeptiert werden!"
                )

    def test_unlimited_and_lifetime_dates(self):
        """Unbegrenzte / Lifetime Kennzeichnungen müssen als gültig akzeptiert werden."""
        unlimited_values = [
            "Unlimited",
            "unlimited",
            "UNLIMITED",
            "Unbegrenzt",
            "unbegrenzt",
            "Lifetime",
            "lifetime",
            "Never",
            "Permanent",
            "dauerhaft",
        ]
        for val in unlimited_values:
            with self.subTest(val=val):
                self.assertTrue(
                    is_valid_expire_date(val, allow_unlimited=True),
                    f"Unbegrenzt-Wert {val!r} sollte als gültig akzeptiert werden!"
                )
                self.assertFalse(
                    is_valid_expire_date(val, allow_unlimited=False),
                    f"Unbegrenzt-Wert {val!r} sollte bei allow_unlimited=False abgewiesen werden!"
                )


class TestMacDatabaseExpireFilter(unittest.TestCase):
    """Tests für MacDatabase Filterung ungültiger Ablaufdaten."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_file = os.path.join(self.tmp_dir.name, "test_mac_db.json")
        self.db = MacDatabase(filepath=self.db_file)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_save_found_mac_rejects_zero_and_none_expire(self):
        """save_found_mac darf Accounts mit 0000000 oder None Expire nicht speichern."""
        portal = "http://stalker.example.com/c/"

        res_zero = {
            "mac": "00:1A:79:AA:BB:CC",
            "channels": 150,
            "expire": "0000-00-00 00:00:00",
            "status": "Aktiv",
        }
        saved = self.db.save_found_mac(portal, res_zero)
        self.assertFalse(saved)
        self.assertEqual(len(self.db.get_known_macs(portal)), 0)

        res_none = {
            "mac": "00:1A:79:AA:BB:DD",
            "channels": 200,
            "expire": "None",
            "status": "Aktiv",
        }
        saved = self.db.save_found_mac(portal, res_none)
        self.assertFalse(saved)
        self.assertEqual(len(self.db.get_known_macs(portal)), 0)

        res_000 = {
            "mac": "00:1A:79:AA:BB:EE",
            "channels": 50,
            "expire": "0000000",
            "status": "Aktiv",
        }
        saved = self.db.save_found_mac(portal, res_000)
        self.assertFalse(saved)
        self.assertEqual(len(self.db.get_known_macs(portal)), 0)

    def test_save_found_mac_accepts_valid_future_expire(self):
        """save_found_mac speichert Accounts mit zukünftigem Datum oder Unlimited."""
        portal = "http://stalker.example.com/c/"
        res_valid = {
            "mac": "00:1A:79:11:22:33",
            "channels": 300,
            "expire": "2028-05-20 20:00:00",
            "status": "Aktiv",
        }
        saved = self.db.save_found_mac(portal, res_valid)
        self.assertTrue(saved)
        self.assertIn("00:1A:79:11:22:33", self.db.get_known_macs(portal))

    def test_clean_duplicates_removes_invalid_expire_records(self):
        """clean_duplicates bereinigt historische Einträge mit 0000000 oder abgelaufenem Datum."""
        portal = "http://stalker.example.com/c/"
        # Direkt in interne Struktur schreiben, wie in alten DBs vorhanden
        self.db._db = {
            "portals": {
                portal: {
                    "00:1A:79:00:00:01": {
                        "mac": "00:1A:79:00:00:01",
                        "portal_url": portal,
                        "channels": 100,
                        "expire": "0000-00-00 00:00:00",
                    },
                    "00:1A:79:00:00:02": {
                        "mac": "00:1A:79:00:00:02",
                        "portal_url": portal,
                        "channels": 200,
                        "expire": "2028-10-10 10:00:00",
                    },
                    "00:1A:79:00:00:03": {
                        "mac": "00:1A:79:00:00:03",
                        "portal_url": portal,
                        "channels": 50,
                        "expire": "None",
                    },
                }
            },
            "global_history": {
                "00:1A:79:00:00:01": {
                    "mac": "00:1A:79:00:00:01",
                    "channels": 100,
                    "expire": "0000-00-00 00:00:00",
                },
                "00:1A:79:00:00:02": {
                    "mac": "00:1A:79:00:00:02",
                    "channels": 200,
                    "expire": "2028-10-10 10:00:00",
                },
                "00:1A:79:00:00:03": {
                    "mac": "00:1A:79:00:00:03",
                    "channels": 50,
                    "expire": "None",
                },
            },
        }
        removed = self.db.clean_duplicates()
        # 2 ungültige in portals + 2 ungültige in global = mind. 4 Bereinigungen
        self.assertGreaterEqual(removed, 4)
        records = self.db.get_all_records(portal)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["mac"], "00:1A:79:00:00:02")


class TestScanSchedulerExpireHandling(unittest.TestCase):
    """Tests für MultiPortalScanScheduler mit 0000000 / ungültigen Ablaufdaten."""

    def test_report_result_with_zero_expire_does_not_trigger_hotspot(self):
        """Ein Account mit 0000000 / None Expire darf keinen Hot-Spot Burst auslösen."""
        portals = ["http://portal-a.com/c/", "http://portal-b.com/c/"]
        macs = ["00:1A:79:00:00:01", "00:1A:79:00:00:02", "00:1A:79:00:00:03"]
        scheduler = MultiPortalScanScheduler(
            portals=portals,
            macs=macs,
            mode=ScanRotationMode.HOT_SPOT,
            hot_spot_burst=5,
        )

        m1, p1 = scheduler.get_next_work_item()
        # Report mit Kanälen > 0, aber tag="valid" und expire="0000-00-00 00:00:00"
        scheduler.report_result(
            p1,
            m1,
            {
                "mac": m1,
                "portal_url": p1,
                "valid": True,
                "channels": 120,
                "expire": "0000-00-00 00:00:00",
                "tag": "valid",
            },
        )

        # Darf NICHT als Hot-Portal oder solved_mac markiert worden sein
        self.assertIsNone(scheduler.active_hot_portal)
        self.assertEqual(scheduler.hot_spot_remaining, 0)
        self.assertNotIn(m1, scheduler.solved_macs)

    def test_report_result_with_valid_expire_triggers_hotspot(self):
        """Ein echter Hot-Hit mit gültigem Ablaufdatum löst wie gewohnt Hot-Spot Burst aus."""
        portals = ["http://portal-a.com/c/", "http://portal-b.com/c/"]
        macs = ["00:1A:79:00:00:01", "00:1A:79:00:00:02", "00:1A:79:00:00:03"]
        scheduler = MultiPortalScanScheduler(
            portals=portals,
            macs=macs,
            mode=ScanRotationMode.HOT_SPOT,
            hot_spot_burst=5,
        )

        m1, p1 = scheduler.get_next_work_item()
        scheduler.report_result(
            p1,
            m1,
            {
                "mac": m1,
                "portal_url": p1,
                "valid": True,
                "channels": 120,
                "expire": "2028-11-15 12:00:00",
                "tag": "hot",
            },
        )

        self.assertEqual(scheduler.active_hot_portal, p1)
        self.assertEqual(scheduler.hot_spot_remaining, 5)
        self.assertIn(m1, scheduler.solved_macs)


if __name__ == "__main__":
    unittest.main()
