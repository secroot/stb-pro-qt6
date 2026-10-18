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
    extract_portal_urls_from_folder,
    extract_portal_urls_from_text,
    get_portal_candidate_endpoints,
    is_stalker_response,
    load_portal_list,
    normalize_portal_url,
    save_reachable_portals_file,
)
from clients.stb_client import emit_scanner_connection_error_log
from core.models import HttpLogEntry


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

            with patch("ui.main_window.check_mac_account", side_effect=mock_check), \
                 patch.object(win.mac_db, "save_found_mac", return_value=True):
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

    def test_08_check_single_portal_rejects_generic_web_server(self):
        """Verifiziert, dass generische Webserver (z. B. Apache/Nginx Default Page 200) als ungültig verworfen werden."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Server": "nginx", "Content-Type": "text/html"}
        mock_resp.text = "<html><head><title>Welcome to nginx!</title></head><body><p>If you see this page, the nginx web server is successfully installed.</p></body></html>"
        mock_resp.cookies = []

        with patch("requests.Session.get", return_value=mock_resp):
            res = check_single_portal("http://not-a-portal.com/c", timeout=1.0)
            self.assertFalse(res.is_online)
            self.assertFalse(res.stalker_detected)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Kein Stalker", res.display_status())
            self.assertIn("Kein Stalker", res.error)

    def test_09_check_single_portal_detects_stalker_via_handshake_probe(self):
        """Testet, dass Stalker-Portale erkannt werden, wenn erst die Sondierung von server/load.php erfolgreich antwortet."""
        resp_main = MagicMock()
        resp_main.status_code = 404
        resp_main.headers = {"Content-Type": "text/html"}
        resp_main.text = "404 Not Found"
        resp_main.cookies = []

        resp_probe = MagicMock()
        resp_probe.status_code = 200
        resp_probe.headers = {"Content-Type": "application/json"}
        resp_probe.text = '/*-secure-{"js":{"token":"abc1234567890123","random":"rnd123"}}*/'
        resp_probe.cookies = []

        def side_effect(url, *args, **kwargs):
            if "server/load.php" in url or "portal.php" in url:
                return resp_probe
            return resp_main

        with patch("requests.Session.get", side_effect=side_effect):
            res = check_single_portal("http://myiptv.org/c", timeout=1.5)
            self.assertTrue(res.is_online)
            self.assertTrue(res.stalker_detected)
            self.assertIn("🟢", res.display_status())
            self.assertTrue(res.endpoint.endswith("load.php") or res.endpoint.endswith("portal.php"))

    def test_10_extract_portal_urls_from_text_and_folder(self):
        """Testet das regex-basierte Parsen von Portal-URLs aus Text und Ordnern."""
        sample_text = (
            "# Dies ist eine Test-Liste\n"
            "http://portal1.me:8080/c/\n"
            "https://stream.server.com:2095/c\n"
            "http://portal1.me:8080/c\n"  # Duplicate
            "Portal: http://mag.tv:8888/stalker_portal/c/\n"
            "// Kommentar\n"
            "keine-url-hier\n"
        )
        extracted = extract_portal_urls_from_text(sample_text)
        self.assertEqual(len(extracted), 3)
        self.assertIn("http://portal1.me:8080/c", extracted)
        self.assertIn("https://stream.server.com:2095/c", extracted)
        self.assertIn("http://mag.tv:8888/stalker_portal/c", extracted)

        # Teste Ordner-Scan
        with tempfile.TemporaryDirectory() as tmp_dir:
            f1 = os.path.join(tmp_dir, "sub1", "list1.txt")
            os.makedirs(os.path.dirname(f1), exist_ok=True)
            with open(f1, "w", encoding="utf-8") as tf1:
                tf1.write("http://folder-portal-1.com:8080/c\n")

            f2 = os.path.join(tmp_dir, "sub2", "list2.txt")
            os.makedirs(os.path.dirname(f2), exist_ok=True)
            with open(f2, "w", encoding="utf-8") as tf2:
                tf2.write("http://folder-portal-2.com:8080/c\nhttp://folder-portal-1.com:8080/c\n")

            urls, count = extract_portal_urls_from_folder(tmp_dir)
            self.assertEqual(count, 2)
            self.assertEqual(len(urls), 2)
            self.assertIn("http://folder-portal-1.com:8080/c", urls)
            self.assertIn("http://folder-portal-2.com:8080/c", urls)

    def test_11_scanner_view_smoothed_cps_and_eta(self):
        """Testet die geglättete Telemetrie- und ETA-Berechnung in ScannerView."""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])

        from ui.views.scanner_view import ScannerView
        sv = ScannerView()
        try:
            # 1. Start-Reset
            sv.update_scan_progress(0, 100)
            self.assertIn("0 / 100", sv.lbl_telemetry.text())
            self.assertIn("ETA: —", sv.lbl_telemetry.text())

            # 2. Simuliere Fortschritt
            sv._scan_start_perf = time.perf_counter() - 2.0
            sv._scan_samples.append((time.perf_counter() - 1.0, 5))
            sv.update_scan_progress(10, 100)

            # CPS muss positiv und geglättet sein, ETA formatiert als MM:SS
            self.assertNotIn("ETA: —", sv.lbl_telemetry.text())
            self.assertIn("CPS", sv.lbl_telemetry.text())
            self.assertGreater(sv._smoothed_cps, 0.0)

            # 3. Fertiggestellt (100/100) -> ETA 00:00
            sv.update_scan_progress(100, 100)
            self.assertIn("ETA: 00:00", sv.lbl_telemetry.text())
        finally:
            sv.close()

    def test_12_sporadic_error_logging_inspector(self):
        """Testet das sporadische Logging von Scan-Verbindungsfehlern in den HTTP-Inspector."""
        from core.signals import event_bus
        logged_entries = []
        event_bus.http_Exchange_logged.connect(logged_entries.append)
        try:
            emit_scanner_connection_error_log(
                portal_url="http://fail-portal.org/c",
                mac="00:1A:79:88:99:00",
                error_msg="Connection timed out after 3.0s",
                status_code=504,
                sample_interval=0.0,
                sample_frequency=1,
            )
            self.assertGreaterEqual(len(logged_entries), 1)
            entry = logged_entries[-1]
            self.assertIsInstance(entry, HttpLogEntry)
            self.assertEqual(entry.status_code, 504)
            self.assertIn("00:1A:79:88:99:00", entry.response_preview)
            self.assertIn("Connection timed out", entry.response_preview)
            self.assertIn("Cookie", entry.request_headers)
        finally:
            try:
                event_bus.http_Exchange_logged.disconnect(logged_entries.append)
            except Exception:
                pass

    def test_13_scanner_view_import_portals_from_folder(self):
        """Testet den Ordner-Import von Portal-URLs im ScannerView."""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])

        from ui.views.scanner_view import ScannerView
        sv = ScannerView()
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                f_path = os.path.join(tmp_dir, "portals.txt")
                with open(f_path, "w", encoding="utf-8") as f:
                    f.write("http://portal-folder-test-a.com/c\nhttp://portal-folder-test-b.com/c\n")

                with patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory", return_value=tmp_dir):
                    sv._import_portals_from_folder()

                self.assertIn("http://portal-folder-test-a.com/c", sv._loaded_portals)
                self.assertIn("http://portal-folder-test-b.com/c", sv._loaded_portals)
                self.assertIn("Portal-Checker", sv.btn_toggle_checker.text())
        finally:
            sv.close()

    def test_14_rejects_php_page_with_images_and_phpsessid(self):
        """Verifiziert, dass generische PHP-Seiten mit PHPSESSID und Bildern/Wörtern wie 'image' nicht als Stalker erkannt werden."""
        mock_cookie = MagicMock()
        mock_cookie.name = "PHPSESSID"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.text = "<html><body><h1>Mein Foto-Blog</h1><p><img src='/images/magenta_sunset.jpg'>Schöne Bilder</p></body></html>"
        mock_resp.cookies = [mock_cookie]

        self.assertFalse(is_stalker_response(mock_resp))

        with patch("requests.Session.get", return_value=mock_resp):
            res = check_single_portal("http://mein-php-blog.de/c", timeout=1.0)
            self.assertFalse(res.is_online)
            self.assertFalse(res.stalker_detected)
            self.assertIn("Kein Stalker", res.display_status())

    def test_15_rejects_generic_json_apis_with_tokens_or_unauthorized(self):
        """Verifiziert, dass generische REST-APIs (z. B. OAuth Tokens oder 401 Unauthorized) nicht als Stalker fehlklassifiziert werden."""
        # Generic OAuth Token response
        mock_oauth = MagicMock()
        mock_oauth.status_code = 200
        mock_oauth.headers = {"Content-Type": "application/json"}
        mock_oauth.text = '{"token": "eyJhbGciOi...", "expires_in": 3600, "user": "alice"}'
        mock_oauth.cookies = []
        self.assertFalse(is_stalker_response(mock_oauth))

        # Generic 401 Unauthorized response
        mock_unauth = MagicMock()
        mock_unauth.status_code = 401
        mock_unauth.headers = {"Content-Type": "application/json"}
        mock_unauth.text = '{"error": "unauthorized", "message": "Invalid API key"}'
        mock_unauth.cookies = []
        self.assertFalse(is_stalker_response(mock_unauth))

        # Echtes Stalker JsHttpRequest Handshake dagegen MUSS erkannt werden
        mock_stalker = MagicMock()
        mock_stalker.status_code = 200
        mock_stalker.headers = {"Content-Type": "text/html"}
        mock_stalker.text = '/*-secure-{"js":{"token":"ABC123XYZ","random":"RND456"}}*/'
        mock_stalker.cookies = []
        self.assertTrue(is_stalker_response(mock_stalker))

    def test_16_extract_portal_urls_without_port_or_scheme_and_exclude_files(self):
        """Testet, dass Stalker-URLs ohne Scheme und Port korrekt geparst und Dateinamen ignoriert werden."""
        sample = (
            "portal.provider.com/c\n"
            "http://other-portal.org:8080/c\n"
            "192.168.1.50/c\n"
            "readme.txt\n"
            "config.json\n"
            "tool.py\n"
            "script.bat\n"
            "vip.streamtv.to/c/portal.php\n"
        )
        urls = extract_portal_urls_from_text(sample)
        self.assertEqual(len(urls), 4)
        self.assertIn("http://portal.provider.com/c", urls)
        self.assertIn("http://other-portal.org:8080/c", urls)
        self.assertIn("http://192.168.1.50/c", urls)
        self.assertIn("http://vip.streamtv.to/c/portal.php", urls)
        # Keine Dateinamen
        for u in urls:
            self.assertNotIn("readme.txt", u)
            self.assertNotIn("config.json", u)

    def test_17_to_curl_includes_get_query_parameters(self):
        """Testet, dass to_curl() für GET-Requests die Query-Parameter an die URL anhängt."""
        entry = HttpLogEntry.create(
            method="GET",
            url="http://stalker-server.me:8080/c/server/load.php",
            status_code=200,
            elapsed_ms=150,
            headers={"User-Agent": "MAG200", "Cookie": "mac=00:1A:79:AA:BB:CC"},
            params="type=stb&action=handshake&token=&JsHttpRequest=1-xml",
        )
        curl_cmd = entry.to_curl()
        self.assertIn("type=stb&action=handshake", curl_cmd)
        self.assertIn("http://stalker-server.me:8080/c/server/load.php?", curl_cmd)

    def test_18_cps_and_eta_stall_decay(self):
        """Testet, dass bei einem Stillstand des Scanners der CPS-Wert abfällt und nicht auf Lifetime-Average verharrt."""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])

        from ui.views.scanner_view import ScannerView
        sv = ScannerView()
        try:
            sv._scan_start_perf = time.perf_counter() - 10.0
            sv._smoothed_cps = 5.0
            sv._scan_samples.clear()
            sv._scan_samples.append((time.perf_counter() - 3.0, 50))
            # Keine neuen Treffer seit 3 Sekunden -> dn = 0 bei dt >= 0.4
            sv.update_scan_progress(50, 100)

            # smoothed CPS muss kleiner sein als die anfänglichen 5.0, da dn == 0
            self.assertLess(sv._smoothed_cps, 5.0)
        finally:
            sv.close()

    def test_19_check_mac_account_handles_timeout_as_connection_error(self):
        """Testet, dass Timeouts in check_mac_account als Verbindungsfehler behandelt werden."""
        import requests
        from clients.stb_client import check_mac_account

        with patch("clients.stb_client.StbClient.handshake", side_effect=requests.exceptions.ConnectTimeout("Connect timed out")):
            res = check_mac_account("http://timeout-portal.com/c", "00:1A:79:00:11:22", timeout=1.0)
            self.assertEqual(res["status"], "Verbindungsfehler")
            self.assertIn("timed out", res["error"].lower())

    def test_20_extract_portal_urls_rejects_combos_and_fake_hosts(self):
        """
        Verifiziert, dass extract_portal_urls_from_text User:Pass/Email:Pass Combos,
        Namen (lucas.pr, jester.bermejo, babi.morosoli) und Dateinamen strikt verwirft,
        während echte Stalker-Portale sauber extrahiert werden.
        """
        sample_dump = (
            "lucas.pr@yahoo.com:password123\n"
            "jester.bermejo@hotmail.com:secret\n"
            "babi.morosoli:mypassword\n"
            "ian.meiser:12345\n"
            "philippe.zanasi:qwerty\n"
            "http://vip.bmbtv.me:15000/c\n"
            "https://c44k.net/c\n"
            "http://185.246.209.95/c\n"
            "pars01.com:8080/c\n"
            "mag.rs6ott.com:8000\n"
            "185.125.230.128:8080\n"
            "portal = mag.clubxc.com:8080/c\n"
            "Host: iptv.darktv.eu:25461\n"
            "readme.txt\n"
            "config.json\n"
            "https://github.com/secroot/stb-pro-qt6\n"
            "http://google.com\n"
        )
        extracted = extract_portal_urls_from_text(sample_dump)

        # Verifiziere: KEINE der Fake-Hosts / Combos vorhanden
        for fake in ["lucas.pr", "jester.bermejo", "babi.morosoli", "ian.meiser", "philippe.zanasi", "yahoo.com", "google.com", "readme.txt"]:
            self.assertFalse(any(fake in u for u in extracted), f"Fake entry '{fake}' was erroneously extracted!")

        # Verifiziere: Alle echten Portale wurden extrahiert
        expected_portals = [
            "http://vip.bmbtv.me:15000/c",
            "https://c44k.net/c",
            "http://185.246.209.95/c",
            "http://pars01.com:8080/c",
            "http://mag.rs6ott.com:8000/c",
            "http://185.125.230.128:8080/c",
            "http://mag.clubxc.com:8080/c",
            "http://iptv.darktv.eu:25461/c",
        ]
        self.assertEqual(len(extracted), len(expected_portals))
        for exp in expected_portals:
            self.assertIn(exp, extracted)

    def test_19_scanner_all_sorting_disabled_and_autoscroll(self):
        """Verifiziert, dass der ALL-Filter im Scanner keine Sortierung hat und neueste Treffer unten anfügt."""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        from ui.views.scanner_view import ScannerView

        sv = ScannerView()
        try:
            # 1. Standard ALL-Modus muss Sorting deaktiviert haben
            self.assertEqual(sv._filter_mode, "ALL")
            self.assertFalse(sv.table.isSortingEnabled())
            self.assertTrue(sv.chk_autoscroll.isChecked())

            # 2. Ergebnisse hinzufügen
            sv.add_scan_result({"mac": "00:1A:79:00:00:01", "portal_url": "http://p1.com", "tag": "invalid", "channels": 0})
            sv.add_scan_result({"mac": "00:1A:79:00:00:02", "portal_url": "http://p1.com", "tag": "hot", "channels": 150, "expire": "2027-01-01"})
            sv.add_scan_result({"mac": "00:1A:79:00:00:03", "portal_url": "http://p1.com", "tag": "invalid", "channels": 0})

            # Reihenfolge in ALL: Letzter Eintrag ist unten
            self.assertEqual(sv.table.rowCount(), 3)
            self.assertFalse(sv.table.isSortingEnabled())
            last_it = sv.table.item(2, 0)
            self.assertIsNotNone(last_it)
            self.assertEqual(last_it.text(), "00:1A:79:00:00:03")

            # HOT Zähler muss 1 sein
            self.assertEqual(sv._hot_results_count, 1)
            self.assertIn("HOT (1)", sv._filter_btns["HOT"].text())

            # 3. Wechsel auf HOT aktiviert Sortierung
            sv._set_result_filter("HOT")
            self.assertEqual(sv.table.rowCount(), 1)
            self.assertTrue(sv.table.isSortingEnabled())

            # 4. Wechsel zurück auf ALL deaktiviert Sortierung wieder
            sv._set_result_filter("ALL")
            self.assertEqual(sv.table.rowCount(), 3)
            self.assertFalse(sv.table.isSortingEnabled())
        finally:
            sv.close()

    def test_20_inspector_trimming_and_scanner_http_log(self):
        """Verifiziert das Logging von Scan-Traffic in den Inspector und das Tabellen-Trimming."""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        from ui.views.inspector_view import InspectorView
        from clients.stb_client import emit_scanner_http_log
        from core.signals import event_bus

        insp = InspectorView()
        event_bus.http_Exchange_logged.connect(insp.add_http_entry)
        try:
            self.assertFalse(insp.table.isSortingEnabled())
            self.assertTrue(insp.chk_autoscroll.isChecked())

            # HOT Hits werden immer direkt geloggt
            emit_scanner_http_log(
                portal_url="http://test-portal.org",
                mac="00:1A:79:11:22:33",
                res={"tag": "hot", "valid": True, "channels": 42, "expire": "2028-01-01", "token": "tok123"},
                force=True,
            )
            self.assertGreaterEqual(len(insp._entries), 1)
            self.assertEqual(insp.table.rowCount(), len(insp._filtered_entries))
            last_entry = insp._entries[-1]
            self.assertEqual(last_entry.status_code, 200)
            self.assertIn("HOT HIT", last_entry.response_preview)

            # Trimming-Test: Über 500 Einträge dürfen die Tabelle und _entries nicht sprengen
            for i in range(520):
                insp.add_http_entry(last_entry)

            self.assertLessEqual(len(insp._entries), 500)
            self.assertLessEqual(insp.table.rowCount(), 500)
        finally:
            insp.close()


if __name__ == "__main__":
    unittest.main()
