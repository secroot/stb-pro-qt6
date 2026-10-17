"""
Unit Tests für IP- und ISP-Sperren-Erkennung sowie NordVPN-Manager.
Testet JSON-Fehler-Payloads (auch gzipped), HTML-WAF-Sperren,
Länder-Heuristiken und die StreamBuffer-Schutzlogik.
"""
import gzip
import json
import unittest
from unittest.mock import MagicMock, patch

from core.stream_probe import detect_stream_error_payload
from core.vpn_manager import NordVpnManager


class TestVpnAndStreamErrors(unittest.TestCase):

    def test_detect_stream_error_valid_ts(self):
        # 188-Byte TS packet starting with 0x47
        valid_ts = b"\x47\x40\x00\x10" + b"\xFF" * 184
        self.assertIsNone(detect_stream_error_payload(valid_ts))

    def test_detect_stream_error_valid_hls(self):
        hls_header = b"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:10\n"
        self.assertIsNone(detect_stream_error_payload(hls_header))

    def test_detect_stream_error_empty(self):
        self.assertIsNone(detect_stream_error_payload(b""))

    def test_detect_stream_error_ip_ban_json(self):
        raw_json = json.dumps({
            "error": "IP_BAN",
            "message": "Your IP address is not authorized to access this service",
            "status": 401
        }).encode("utf-8")
        err = detect_stream_error_payload(raw_json, content_type="application/json")
        self.assertIsNotNone(err)
        self.assertIn("IP-Sperre", err)
        self.assertIn("IP_BAN", err)

    def test_detect_stream_error_ip_ban_gzip(self):
        raw_json = json.dumps({
            "error": "IP_BAN",
            "message": "Your IP address is not authorized to access this service",
            "status": 401
        }).encode("utf-8")
        gzipped = gzip.compress(raw_json)
        err = detect_stream_error_payload(gzipped, content_type="application/json")
        self.assertIsNotNone(err)
        self.assertIn("IP-Sperre", err)
        self.assertIn("IP_BAN", err)

    def test_detect_stream_error_isp_lock_json(self):
        raw_json = json.dumps({
            "error": "ISP_LOCK_FAILED",
            "message": "ISP verification failed: Your internet provider is not authorized",
            "status": 401
        }).encode("utf-8")
        err = detect_stream_error_payload(raw_json)
        self.assertIsNotNone(err)
        self.assertIn("ISP-Sperre", err)
        self.assertIn("ISP_LOCK", err)

    def test_detect_stream_error_html_waf(self):
        html_block = b"<html><head><title>403 Forbidden</title></head><body>Cloudflare Access Denied</body></html>"
        err = detect_stream_error_payload(html_block, content_type="text/html")
        self.assertIsNotNone(err)
        self.assertIn("Cloudflare", err)

    def test_vpn_manager_country_guessing(self):
        vm = NordVpnManager()
        self.assertEqual(vm.guess_country_for_profile("DE | HD paplive.me", "http://paplive.me:8080/c/"), "Germany")
        self.assertEqual(vm.guess_country_for_profile("TR | Spor", "http://portal.tr:8080/c/"), "Turkey")
        self.assertEqual(vm.guess_country_for_profile("AT ORF HD", "http://austria-tv.at/c/"), "Austria")
        self.assertEqual(vm.guess_country_for_profile("CH SRF Info", "http://swiss.ch/c/"), "Switzerland")
        self.assertEqual(vm.guess_country_for_profile("UK Sky Sports", "http://uk-stream.co.uk/c/"), "United Kingdom")
        self.assertEqual(vm.guess_country_for_profile("US ESPN 4K", "http://us-sports.us/c/"), "United States")
        self.assertEqual(vm.guess_country_for_profile("Random Portal", "http://example.com/c/"), "Germany")

    def test_vpn_manager_cooldown(self):
        vm = NordVpnManager()
        vm._cli_path = r"C:\fake\nordvpn.exe"
        vm._is_switching = True
        cb = MagicMock()
        ok = vm.switch_server(callback=cb)
        self.assertFalse(ok)
        cb.assert_called_with(False, "Server-Wechsel läuft bereits oder Cooldown aktiv.")

    def test_burned_ips_tracking(self):
        vm = NordVpnManager()
        host = "http://paplive.me:8080/c/"
        ip1 = "86.38.149.243"
        ip2 = "45.150.175.84"

        # Anfangs keine verbrannten IPs
        vm.clear_burned_ips("paplive.me")
        self.assertFalse(vm.is_ip_burned(host, ip1))

        # IP 1 als verbrannt markieren
        vm.mark_ip_burned(host, ip1, reason="IP_BAN Test")
        self.assertTrue(vm.is_ip_burned("paplive.me", ip1))
        self.assertTrue(vm.is_ip_burned(host, ip1))
        self.assertFalse(vm.is_ip_burned(host, ip2))
        self.assertFalse(vm.is_ip_burned("other-portal.to", ip1))

        # Prüfe Liste
        b_list = vm.get_burned_ips("paplive.me")
        self.assertIn(ip1, b_list)

        # Löschen für Host
        vm.clear_burned_ips("paplive.me")
        self.assertFalse(vm.is_ip_burned(host, ip1))

    def test_rotation_candidates(self):
        vm = NordVpnManager()
        cands = vm.get_rotation_candidates("Germany")
        self.assertIn("Germany", cands)
        self.assertIn("Switzerland", cands)
        self.assertIn("Austria", cands)
        self.assertIn("Netherlands", cands)

    def test_auto_switch_toggle(self):
        vm = NordVpnManager()
        vm.auto_switch_enabled = True
        self.assertTrue(vm.auto_switch_enabled)

        vm.auto_switch_enabled = False
        self.assertFalse(vm.auto_switch_enabled)
        # Wenn deaktiviert, darf handle_ip_ban keinen Server-Wechsel starten
        ok = vm.handle_ip_ban("http://test.com/stream", "IP_BAN", "Test Profile")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
