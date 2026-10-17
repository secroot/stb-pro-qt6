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
        cb.assert_called_with(False, "Server-Wechsel läuft bereits oder Cooldown aktiv (15s).")

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

    def test_is_ip_or_stream_ban(self):
        from core.stream_probe import is_ip_or_stream_ban
        for code in (511, 456, 401, 403, 407, 458):
            self.assertTrue(is_ip_or_stream_ban(code), f"Expected {code} to be recognized as ban")
        for code in (200, 206, 404, 500, 502):
            self.assertFalse(is_ip_or_stream_ban(code), f"Expected {code} not to be recognized as ban")

        self.assertTrue(is_ip_or_stream_ban(0, "HTTP 511 (Device-Auth / Geo-Lock)"))
        self.assertTrue(is_ip_or_stream_ban(0, "Cloudflare Access Denied"))
        self.assertTrue(is_ip_or_stream_ban(0, "IP-Sperre: IP_BAN"))
        self.assertTrue(is_ip_or_stream_ban(0, "ISP-Sperre: ISP_LOCK"))
        self.assertFalse(is_ip_or_stream_ban(0, "Upstream beendet"))

    def test_probe_stream_triggers_ip_ban_on_511(self):
        from core.stream_probe import probe_stream
        from core.signals import event_bus

        mock_resp = MagicMock()
        mock_resp.status_code = 511
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False

        emitted_signals = []
        def _on_ban(url, reason):
            emitted_signals.append((url, reason))

        event_bus.stream_ip_ban_detected.connect(_on_ban)
        try:
            with patch("requests.get", return_value=mock_resp):
                # 1. Default (trigger_vpn=False, z.B. Vorschaubilder-Abruf): darf KEIN System-VPN-Switch auslösen
                res_passive = probe_stream("http://pro.8k-strong.tv/play/live.php?mac=00:1A:79:00:13:BE", trigger_vpn=False)
                self.assertFalse(res_passive.is_alive)
                self.assertEqual(len(emitted_signals), 0)

                # 2. Explizit trigger_vpn=True (z.B. aktives Playback): muss Event emittieren
                res_active = probe_stream("http://pro.8k-strong.tv/play/live.php?mac=00:1A:79:00:13:BE", trigger_vpn=True)
                self.assertFalse(res_active.is_alive)
                self.assertEqual(res_active.status_code, 511)
                self.assertIn("511", res_active.error_msg)
                self.assertEqual(len(emitted_signals), 1)
                self.assertIn("pro.8k-strong.tv", emitted_signals[0][0])
                self.assertIn("511", emitted_signals[0][1])
        finally:
            event_bus.stream_ip_ban_detected.disconnect(_on_ban)

    def test_vpn_manager_clean_disconnect_and_sequence(self):
        vm = NordVpnManager()
        vm._cli_path = r"C:\fake\NordVPN.exe"

        called_cmds = []
        def _fake_run(cmd, *args, **kwargs):
            called_cmds.append(list(cmd))
            m = MagicMock()
            m.returncode = 0
            return m

        with patch("subprocess.run", side_effect=_fake_run):
            # Test expliziter Disconnect
            ok = vm.disconnect()
            self.assertTrue(ok)
            import time
            for _ in range(20):
                if any("-d" in cmd for cmd in called_cmds):
                    break
                time.sleep(0.05)
            self.assertTrue(any("-d" in cmd for cmd in called_cmds))

            # Test Serverwechsel: Muss -d vor -c aufrufen
            called_cmds.clear()
            vm._is_switching = False
            vm._last_switch_time = 0.0
            with patch.object(vm, "get_public_ip", return_value="1.2.3.4"):
                vm.switch_server("Switzerland")
                for _ in range(40):
                    if len(called_cmds) >= 2:
                        break
                    time.sleep(0.05)
                self.assertTrue(len(called_cmds) >= 2)
                self.assertIn("-d", called_cmds[0])
                self.assertIn("-c", called_cmds[1])
                self.assertIn("Switzerland", called_cmds[1])

    def test_stream_buffer_aborts_immediately_on_511(self):
        import time
        from PySide6.QtCore import Qt
        from core.stream_buffer import BufferSettings, _Session
        from core.signals import event_bus

        mock_resp = MagicMock()
        mock_resp.status_code = 511
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False

        emitted_signals = []
        log_messages = []
        def _on_ban(url, reason):
            emitted_signals.append((url, reason))
        def _on_log(msg):
            log_messages.append(msg)

        event_bus.stream_ip_ban_detected.connect(_on_ban, Qt.DirectConnection)
        event_bus.log_message.connect(_on_log, Qt.DirectConnection)
        try:
            st = BufferSettings(reconnect=True, max_retries=10)
            with patch("core.stream_buffer.requests.get", return_value=mock_resp):
                sess = _Session("http://pro.8k-strong.tv/play/live.php?stream=123", {}, st)
                sess.thread.join(timeout=1.0)

                # Reconnect-Versuche müssen 0 sein, da sofort abgebrochen wurde
                self.assertEqual(sess.reconnects, 0)
                self.assertFalse(sess.connected)
                self.assertTrue(sess.eof)
                self.assertIn("511", sess.error)
                self.assertEqual(len(emitted_signals), 1)
                self.assertTrue(any("Stream-Fehler" in m and "511" in m for m in log_messages))
        finally:
            event_bus.stream_ip_ban_detected.disconnect(_on_ban)
            event_bus.log_message.disconnect(_on_log)


if __name__ == "__main__":
    unittest.main()
