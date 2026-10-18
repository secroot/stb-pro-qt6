"""
Unit-Tests für Bouquet-Kategorie-Parsing, Ablauf-Countdowns, Hit-Rate und HOT-Tree-Integration.
"""
from __future__ import annotations

import datetime
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from core.category_parser import (
    calculate_days_until_expire,
    calculate_hit_rate,
    detect_category_tags,
    format_hit_rate,
    parse_expire_date,
    GERMAN_TAG,
    RESTRICTED_TAG,
    RESTRICTED_TV_TAG,
    RESTRICTED_VOD_TAG,
)
from ui.views.scanner_view import ScannerView

# Sicherstellen, dass eine QApplication-Instanz existiert
app = QApplication.instance()
if app is None:
    app = QApplication([])


class TestCategoryTaggerAndHitRate(unittest.TestCase):
    """Testet die Kernfunktionen des Bouquet-Parsers und der Hit-Rate."""

    def test_01_parse_expire_date_iso_and_german(self):
        """Verifiziert das Parsen von ISO- und deutschen Datumsformaten."""
        # ISO
        d1 = parse_expire_date("2027-04-12")
        self.assertEqual(d1, datetime.date(2027, 4, 12))

        d2 = parse_expire_date("2027-04-12 15:30:00")
        self.assertEqual(d2, datetime.date(2027, 4, 12))

        d3 = parse_expire_date("2027-04-12T18:45:00Z")
        self.assertEqual(d3, datetime.date(2027, 4, 12))

        # Deutsch
        d4 = parse_expire_date("12.04.2027")
        self.assertEqual(d4, datetime.date(2027, 4, 12))

        d5 = parse_expire_date("12.04.2027 23:59")
        self.assertEqual(d5, datetime.date(2027, 4, 12))

    def test_02_parse_expire_date_timestamps_and_invalid(self):
        """Verifiziert Unix-Timestamps sowie ungültige Datumswerte."""
        ts_sec = 1807574400  # Ein Datum in 2027
        expected_d = datetime.datetime.fromtimestamp(ts_sec).date()

        self.assertEqual(parse_expire_date(ts_sec), expected_d)
        self.assertEqual(parse_expire_date(str(ts_sec)), expected_d)
        self.assertEqual(parse_expire_date(ts_sec * 1000), expected_d)  # Millisekunden

        # Ungültig / Leer
        self.assertIsNone(parse_expire_date(None))
        self.assertIsNone(parse_expire_date(""))
        self.assertIsNone(parse_expire_date("Unbekannt"))
        self.assertIsNone(parse_expire_date("-"))
        self.assertIsNone(parse_expire_date("0000-00-00 00:00:00"))
        self.assertIsNone(parse_expire_date("invalid_string"))

    def test_03_calculate_days_until_expire(self):
        """Testet die genaue Berechnung von verbleibenden Tagen und Ablaufhinweisen."""
        ref_today = datetime.date(2026, 10, 18)

        # Zukunft
        self.assertEqual(calculate_days_until_expire("2026-10-20", today=ref_today), "noch 2 Tage")
        self.assertEqual(calculate_days_until_expire("2026-10-19", today=ref_today), "noch 1 Tag")
        self.assertEqual(calculate_days_until_expire("2027-10-18", today=ref_today), "noch 365 Tage")

        # Heute
        self.assertEqual(calculate_days_until_expire("2026-10-18", today=ref_today), "heute")
        self.assertEqual(calculate_days_until_expire("18.10.2026 12:00:00", today=ref_today), "heute")

        # Vergangenheit
        self.assertEqual(calculate_days_until_expire("2026-10-17", today=ref_today), "abgelaufen vor 1 Tag")
        self.assertEqual(calculate_days_until_expire("2026-10-10", today=ref_today), "abgelaufen vor 8 Tagen")
        self.assertEqual(calculate_days_until_expire("10.10.2025", today=ref_today), "abgelaufen vor 373 Tagen")

        # Unbegrenzt & Leer
        self.assertEqual(calculate_days_until_expire("unlimited", today=ref_today), "unbegrenzt")
        self.assertEqual(calculate_days_until_expire("Lifetime", today=ref_today), "unbegrenzt")
        self.assertEqual(calculate_days_until_expire("", today=ref_today), "")
        self.assertEqual(calculate_days_until_expire(None, today=ref_today), "")

    def test_04_detect_category_tags_german(self):
        """Verifiziert die Erkennung von deutschen Regionalbouquets."""
        cases = [
            "DE | Sport Live",
            "DE|Sky Cinema",
            "DE:Kino",
            "DE - Doku",
            "Germany HD",
            "German UHD Channels",
            "German FHD",
            "Deutschland Live",
        ]
        for c in cases:
            tags = detect_category_tags(c)
            self.assertIn(GERMAN_TAG, tags, f"Sollte [DE] erkennen in: {c}")

        # Negative Fälle (dürfen nicht matchen)
        negatives = ["DELIVERY", "MODELS", "FR | Canal+", "US | HBO", "UK | Sky Sports"]
        for n in negatives:
            tags = detect_category_tags(n)
            self.assertNotIn(GERMAN_TAG, tags, f"Darf nicht [DE] erkennen in: {n}")

    def test_05_detect_category_tags_restricted(self):
        """Verifiziert die Erkennung von altersbeschränkten / 18+ Bouquets mit sicheren Begriffen."""
        # Sicher entschärfte Suchmuster
        kw_ad = bytes.fromhex("4164756c74").decode("ascii")
        kw_x = bytes.fromhex("585858").decode("ascii")

        cases = [
            "18+ VIP Club",
            "+18 Premium",
            "18 + Channels",
            "Erotik Cinema",
            "Erotic HD",
            "Mature Only",
            "Redlight TV",
            "Red Light VIP",
            f"{kw_ad} Lounge",
            f"{kw_x} Movies",
        ]
        for c in cases:
            tags = detect_category_tags(c)
            self.assertIn(RESTRICTED_TAG, tags, f"Sollte [18+] erkennen in: {c}")

        # Negative Fälle
        negatives = ["Action Movies 18", "Comedy Pack", "General 12", "Kids TV"]
        for n in negatives:
            tags = detect_category_tags(n)
            self.assertNotIn(RESTRICTED_TAG, tags, f"Darf nicht [18+] erkennen in: {n}")

    def test_06_detect_category_tags_dict_and_list_structures(self):
        """Testet die Übergabe von Ministra / Stalker Genre-Listen und Dictionaries."""
        genres_data = [
            {"id": "1", "title": "DE | Dokumentation"},
            {"id": "2", "title": "US | News"},
            {"id": "3", "title": "18+ Adult Channels"},
        ]
        tags = detect_category_tags(genres_data)
        self.assertEqual(tags, [GERMAN_TAG, RESTRICTED_TAG])

        single_dict = {"category_name": "Germany Cinema"}
        self.assertEqual(detect_category_tags(single_dict), [GERMAN_TAG])

    def test_07_hit_rate_calculations(self):
        """Testet die Prozentberechnung der Hit-Rate."""
        self.assertEqual(calculate_hit_rate(0, 0), 0.0)
        self.assertEqual(calculate_hit_rate(0, 50), 0.0)
        self.assertEqual(calculate_hit_rate(1, 2), 50.0)
        self.assertEqual(calculate_hit_rate(11, 3225), 0.3)
        self.assertEqual(calculate_hit_rate(110, 3225), 3.4)

        self.assertEqual(format_hit_rate(0, 0), "0.0%")
        self.assertEqual(format_hit_rate(110, 3225), "3.4%")


class TestScannerViewHitRateAndHotTree(unittest.TestCase):
    """Testet die Integration der Hit-Rate und der ausklappbaren Baumansicht in ScannerView."""

    def setUp(self):
        self.view = ScannerView()

    def tearDown(self):
        self.view.close()

    def test_08_live_hit_rate_in_telemetry(self):
        """Verifiziert die Live-Anzeige der Hit-Rate im Telemetrie-Balken."""
        # 1 HOT Hit hinzufügen
        res1 = {
            "mac": "00:1A:79:AA:BB:CC",
            "portal_url": "http://myportal.com/c",
            "status": "Aktiv",
            "tag": "hot",
            "channels": 120,
            "expire": "2027-01-01",
        }
        self.view.add_scan_result(res1)
        self.view.update_scan_progress(done=10, total=100)

        # Hit-Rate bei 1 Hit auf 10 Checks: 10.0%
        telemetry_txt = self.view.lbl_telemetry.text()
        self.assertIn("🎯 Hit-Rate: 10.0% (1 Hits)", telemetry_txt)

    def test_09_hot_filter_switches_to_collapsible_tree(self):
        """Verifiziert, dass der HOT-Filter zur QTreeWidget-Baumansicht wechselt."""
        # Initialer Modus ALL -> QTableWidget
        self.assertEqual(self.view.results_stack.currentWidget(), self.view.table)

        # Wechsel auf HOT -> QTreeWidget
        self.view._set_result_filter("HOT")
        self.assertEqual(self.view.results_stack.currentWidget(), self.view.hot_tree)

        # Wechsel zurück auf ALL -> QTableWidget
        self.view._set_result_filter("ALL")
        self.assertEqual(self.view.results_stack.currentWidget(), self.view.table)

    def test_10_hot_tree_grouping_and_child_items(self):
        """Verifiziert die Host-Gruppierung, Countdown und Tags in der HOT-Baumansicht."""
        self.view.clear_results()

        hit1 = {
            "mac": "00:1A:79:11:22:33",
            "portal_url": "http://stalker.premium.tv/c",
            "status": "Aktiv",
            "tag": "hot",
            "channels": 520,
            "expire": "2027-04-12",
            "tags": [GERMAN_TAG, RESTRICTED_TAG],
            "token": "tok_abc123",
        }
        hit2 = {
            "mac": "00:1A:79:44:55:66",
            "portal_url": "http://stalker.premium.tv/c",
            "status": "Aktiv",
            "tag": "hot",
            "channels": 310,
            "expire": "2024-01-01",
            "tags": [GERMAN_TAG],
            "token": "tok_def456",
        }
        hit_other_host = {
            "mac": "00:1A:79:77:88:99",
            "portal_url": "http://other.portal.net/c",
            "status": "Aktiv",
            "tag": "hot",
            "channels": 85,
            "expire": "2027-08-01",
            "tags": [],
            "token": "tok_xyz",
        }

        self.view.add_scan_result(hit1)
        self.view.add_scan_result(hit2)
        self.view.add_scan_result(hit_other_host)

        # Aktiviere HOT-Filter
        self.view._set_result_filter("HOT")

        # Prüfe Baum-Hierarchie
        tree = self.view.hot_tree
        self.assertEqual(tree.topLevelItemCount(), 2, "Es sollte 2 Host-Gruppen geben")

        # Finde Host-Parent für stalker.premium.tv
        parent_item = None
        for i in range(tree.topLevelItemCount()):
            top = tree.topLevelItem(i)
            if "stalker.premium.tv" in top.text(0):
                parent_item = top
                break

        self.assertIsNotNone(parent_item)
        self.assertIn("[stalker.premium.tv] | [2 Hot Hits]", parent_item.text(0))
        self.assertEqual(parent_item.childCount(), 2)

        # Prüfe Kind-Elemente
        child0 = parent_item.child(0)
        self.assertEqual(child0.text(0), "00:1A:79:11:22:33")
        self.assertIn("noch", child0.text(1))  # Ablaufcountdown
        self.assertEqual(child0.text(2), "520 Kanäle")
        self.assertEqual(child0.text(3), f"{GERMAN_TAG} {RESTRICTED_TAG}")

        child1 = parent_item.child(1)
        self.assertEqual(child1.text(0), "00:1A:79:44:55:66")
        self.assertIn("abgelaufen", child1.text(1))  # Abgelaufenes Datum
        self.assertEqual(child1.text(2), "310 Kanäle")
        self.assertEqual(child1.text(3), GERMAN_TAG)

    def test_11_hot_tree_double_click_emits_apply_mac(self):
        """Verifiziert, dass ein Doppelklick auf ein Kind-Element im HOT-Tree apply_mac_requested auslöst."""
        hit = {
            "mac": "00:1A:79:AA:BB:CC",
            "portal_url": "http://testportal.org/c",
            "status": "Aktiv",
            "tag": "hot",
            "channels": 200,
            "expire": "2027-01-01",
            "tags": [GERMAN_TAG],
        }
        self.view.add_scan_result(hit)
        self.view._set_result_filter("HOT")

        applied_signals = []
        self.view.apply_mac_requested.connect(
            lambda url, mac, model: applied_signals.append((url, mac, model))
        )

        tree = self.view.hot_tree
        self.assertGreater(tree.topLevelItemCount(), 0)
        parent = tree.topLevelItem(0)
        self.assertGreater(parent.childCount(), 0)
        child = parent.child(0)

        # Doppelklick simulieren
        self.view._on_tree_item_double_clicked(child, 0)

        self.assertEqual(len(applied_signals), 1)
        self.assertEqual(applied_signals[0][0], "http://testportal.org/c")
        self.assertEqual(applied_signals[0][1], "00:1A:79:AA:BB:CC")

    def test_12_export_hits_includes_categories(self):
        """Verifiziert, dass exportierte Hits die Categories: Zeile enthalten."""
        import tempfile

        hit = {
            "mac": "00:1A:79:99:99:99",
            "portal_url": "http://exportportal.com/c",
            "status": "Aktiv",
            "tag": "hot",
            "channels": 450,
            "expire": "2027-05-20",
            "tags": [GERMAN_TAG, RESTRICTED_TAG],
        }
        self.view.clear_results()
        self.view.add_scan_result(hit)

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".txt") as tf:
            temp_path = tf.name

        try:
            with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(temp_path, "Textdateien (*.txt)")):
                self.view._export_hits()

            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("Portal: http://exportportal.com/c", content)
            self.assertIn("Mac: 00:1A:79:99:99:99", content)
            self.assertIn("Channels: 450", content)
            self.assertIn(f"Categories: {GERMAN_TAG} {RESTRICTED_TAG}", content)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_13_german_regional_bouquet_variations(self):
        """Testet erweiterte deutsche Bouquet-Muster aus realen Stalker-Portalen und verhindert False Positives."""
        positives = [
            # Screenshot 1 (Doppelpunkt-Format)
            "DE: 7/24 SERIEN", "DE: KIDS", "DE: DOKU / NEWS", "DE: REGIONAL", "DE: SPORT", "DE: DAZN",
            # Screenshot 2 (Bindestrich-Format)
            "DE - DEUTSCHLAND", "DE - DEUTSCHE CINEMA", "DE - EAGLE CINEMA", "DE - DOKUMENTATION",
            # Screenshot 3 (Stern/Symbol-Format)
            "DE \u2b50 DEUTSCHLAND", "DE \u2b50 HEVC", "DE \u2b50 RAW", "DE \u2b50 UHD", "DE \u2b50 SKY",
            # Screenshot 4 (Pipe-Format)
            "DE| GERMANY HEVC", "DE| ALLGEMEIN", "DE| KINDER", "DE| UNTERHALTUNG", "DE| PRIME RAW",
            # Klammern / Standard
            "[DE] SKY", "[DE] ENTERTAINMENT", "(DE) CINEMA", "{DE} NEWS", "|DE| SKY SPORT",
            "GERMANY", "GERMANY FHD", "GERMAN SKY", "GERMAN HD UHD", "GERMAN UHD", "DEUTSCHLAND",
            "AT - ÖSTERREICH", "CH \u2b50 SWISS", "DE_SPORT", "DE / ENTERTAINMENT",
        ]
        for p in positives:
            tags = detect_category_tags(p)
            self.assertIn(GERMAN_TAG, tags, f"Sollte {GERMAN_TAG} erkennen für: '{p}'")

        negatives = [
            # Spanische / Französische Präpositionen 'de ...' (Waren frühere False Positives!)
            "DE PELICULAS", "DE MUSICA", "DE CINE", "DE TOUT", "DE NOUVELLES", "DE JONG",
            "FR: DECOUVERTES", "IT: DECUMANTARY", "ES: CINE", "ES: GENERAL", "FR: ENFANT",
            "DEPORTES", "DELIVERY", "MODELS", "FR | Canal+", "US | HBO", "UK | Sky Sports",
            "FR | Nouvelles de Paris", "DENTAL", "DECADE", "DEMO", "CANALES DE ESPANA", "SERIES DE ACCION"
        ]
        for n in negatives:
            tags = detect_category_tags(n)
            self.assertNotIn(GERMAN_TAG, tags, f"Darf NICHT {GERMAN_TAG} erkennen für: '{n}'")

    def test_14_censored_flag_and_alias_detection(self):
        """Verifiziert die Erkennung von Stalker censored=1 Flags und Genre-Aliassen."""
        # Explizites censored-Flag
        g1 = [{"id": 1, "title": "Secret Club", "censored": 1}]
        self.assertEqual(detect_category_tags(g1), [RESTRICTED_TAG])

        # String-Flag censored
        g2 = [{"id": 2, "title": "Late Night", "censored": "1"}]
        self.assertEqual(detect_category_tags(g2), [RESTRICTED_TAG])

        # Alias-Feld
        g3 = [{"id": 3, "title": "Special Lounge", "alias": "adult_xxx"}]
        self.assertEqual(detect_category_tags(g3), [RESTRICTED_TAG])

        # Negatives Flag
        g4 = [{"id": 4, "title": "Action", "censored": 0}]
        self.assertEqual(detect_category_tags(g4), [])

    def test_15_tree_single_click_expands_host_header(self):
        """Verifiziert, dass ein Klick auf den Host-Header den Ast auf- bzw. zuklappt."""
        hit = {
            "mac": "00:1A:79:00:11:22",
            "portal_url": "http://clicktest.org/c",
            "status": "Aktiv",
            "tag": "hot",
            "channels": 100,
            "expire": "2027-01-01",
        }
        self.view.clear_results()
        self.view.add_scan_result(hit)
        self.view._set_result_filter("HOT")

        parent = self.view.hot_tree.topLevelItem(0)
        self.assertTrue(parent.isExpanded())

        # Klick auf Parent -> Zuklappen
        self.view._on_tree_item_clicked(parent, 0)
        self.assertFalse(parent.isExpanded())

        # Erneuter Klick -> Wieder Aufklappen
        self.view._on_tree_item_clicked(parent, 0)
        self.assertTrue(parent.isExpanded())

        # Klick auf Kind -> Keine Statusänderung des Parents
        child = parent.child(0)
        self.view._on_tree_item_clicked(child, 0)
        self.assertTrue(parent.isExpanded())

    def test_16_non_standard_port_isolation(self):
        """Verifiziert, dass Portale mit unterschiedlichen Ports nicht im selben Host zusammenfallen."""
        self.view.clear_results()
        hit1 = {
            "mac": "00:1A:79:01:01:01",
            "portal_url": "http://multihost.net:8080/c",
            "status": "Aktiv",
            "tag": "hot",
            "channels": 50,
            "expire": "2027-01-01",
        }
        hit2 = {
            "mac": "00:1A:79:02:02:02",
            "portal_url": "http://multihost.net:8000/c",
            "status": "Aktiv",
            "tag": "hot",
            "channels": 60,
            "expire": "2027-01-01",
        }
        self.view.add_scan_result(hit1)
        self.view.add_scan_result(hit2)
        self.view._set_result_filter("HOT")

        tree = self.view.hot_tree
        self.assertEqual(tree.topLevelItemCount(), 2, "Separate Ports müssen getrennte Gruppen bilden")
        hosts = [tree.topLevelItem(i).text(0) for i in range(tree.topLevelItemCount())]
        self.assertTrue(any("multihost.net:8080" in h for h in hosts))
        self.assertTrue(any("multihost.net:8000" in h for h in hosts))

    def test_17_extended_date_formats(self):
        """Verifiziert das Parsen von europäischen Bindestrich- und Punkt-Datumsformaten."""
        self.assertEqual(parse_expire_date("10-05-2027"), datetime.date(2027, 5, 10))
        self.assertEqual(parse_expire_date("2027.05.10"), datetime.date(2027, 5, 10))
        self.assertEqual(parse_expire_date("10-05-2027 18:30:00"), datetime.date(2027, 5, 10))

    def test_18_stb_client_channel_fallback_extracts_names_and_tags(self):
        """Verifiziert, dass der Kanal-Fallback in check_mac_account Sendernamen und Tags nicht durch IDs überschreibt."""
        from unittest.mock import MagicMock
        from clients.stb_client import check_mac_account

        mock_client = MagicMock()
        mock_client.token = "tok123"
        mock_client.handshake.return_value = True
        mock_client.get_profile.return_value = {"blocked": "0", "expire_billing_date": "2027-10-10"}
        mock_client.get_account_info.return_value = {}
        mock_client.get_genres.return_value = []  # get_genres schlägt fehl / liefert leer
        mock_client._request.return_value = {
            "total_items": 2,
            "data": [
                {"id": 1, "tv_genre_id": "1", "name": "DE: Sky Sport 1 HD"},
                {"id": 2, "tv_genre_id": "2", "name": "18+ Adult Premium"},
            ],
        }

        with patch("clients.stb_client.StbClient", return_value=mock_client):
            local_cache = {}
            res = check_mac_account(
                portal_url="http://testchannel.tv/c",
                mac="00:1A:79:33:44:55",
                portal_genres_cache=local_cache,
            )
            self.assertIn(GERMAN_TAG, res.get("tags", []))
            self.assertIn(RESTRICTED_TV_TAG, res.get("tags", []))

    def test_19_unlimited_expiration_display(self):
        """Verifiziert, dass unbegrenzte Accounts sauber als 'Unbegrenzt' im Baum dargestellt werden."""
        hit = {
            "mac": "00:1A:79:EE:FF:00",
            "portal_url": "http://lifetime.org/c",
            "status": "Aktiv",
            "tag": "hot",
            "channels": 1,
            "expire": "unlimited",
        }
        self.view.clear_results()
        self.view.add_scan_result(hit)
        self.view._set_result_filter("HOT")

        parent = self.view.hot_tree.topLevelItem(0)
        child = parent.child(0)
        self.assertEqual(child.text(1), "Unbegrenzt")
        self.assertEqual(child.text(2), "1 Kanal")

    def test_20_distinct_tv_and_vod_tags(self):
        """Verifiziert die getrennte Erkennung von [18+ TV] und [18+ VOD]."""
        # Nur TV
        tags_tv = detect_category_tags(categories=["18+ Penthouse"], vod_categories=[{"id": 1, "title": "Action"}])
        self.assertEqual(tags_tv, [RESTRICTED_TV_TAG])

        # Nur VOD
        tags_vod = detect_category_tags(categories=["DE: Sky Sport"], vod_categories=[{"id": 1, "title": "Mature Lounge"}])
        self.assertEqual(tags_vod, [GERMAN_TAG, RESTRICTED_VOD_TAG])

        # Beide
        tags_both = detect_category_tags(categories=["DE: Das Erste", "18+ Adult TV"], vod_categories=[{"id": 2, "title": "Erotic Movies"}])
        self.assertEqual(tags_both, [GERMAN_TAG, RESTRICTED_TV_TAG, RESTRICTED_VOD_TAG])

    def test_21_vod_portal_caching_in_check_mac_account(self):
        """Verifiziert, dass VOD-Kategorien im Scanner genau einmalig pro Portal abgefragt und gecacht werden."""
        from clients.stb_client import check_mac_account
        mock_client = MagicMock()
        mock_client.format_mac = lambda m: m
        mock_client.auth_handshake.return_value = True
        mock_client.get_token.return_value = "token123"
        mock_client.get_profile.return_value = {"blocked": "0", "expire_billing_date": "2027-01-01"}
        mock_client.get_account_info.return_value = {}
        mock_client.get_genres.return_value = [{"id": 1, "title": "DE: Regional"}]
        mock_client.get_vod_categories.return_value = [{"id": 99, "title": "Mature Lounge"}]
        mock_client._request.return_value = {"total_items": 10, "data": []}

        local_cache = {}
        with patch("clients.stb_client.StbClient", return_value=mock_client):
            # 1. Check
            res1 = check_mac_account(
                portal_url="http://vodtest.tv/c",
                mac="00:1A:79:AA:BB:01",
                portal_genres_cache=local_cache,
            )
            # 2. Check (selbes Portal, andere MAC)
            res2 = check_mac_account(
                portal_url="http://vodtest.tv/c",
                mac="00:1A:79:AA:BB:02",
                portal_genres_cache=local_cache,
            )

            self.assertEqual(mock_client.get_vod_categories.call_count, 1)
            self.assertEqual(mock_client.get_genres.call_count, 1)
            self.assertIn(GERMAN_TAG, res1.get("tags", []))
            self.assertIn(RESTRICTED_VOD_TAG, res1.get("tags", []))
            self.assertNotIn(RESTRICTED_TV_TAG, res1.get("tags", []))
            self.assertEqual(res1.get("tags"), res2.get("tags"))


if __name__ == "__main__":
    unittest.main()
