"""
Unit tests for Sidebar Toggle Button ('Verbindung..'), SettingsView,
ConfigManager extended options, and live setting applications.
"""
from __future__ import annotations

import os
import sys
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from PySide6.QtWidgets import QApplication

from core.config_manager import ConfigManager
from core.stream_buffer import BufferSettings
from core.vpn_manager import NordVpnManager
from ui.components.top_bar import TopNavigationBar
from ui.main_window import MainWindow
from ui.views.settings_view import SettingsView


class TestSettingsAndSidebar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_01_sidebar_button_label_and_toggle(self):
        """Verify the top bar sidebar toggle button displays 'Verbindung..' and emits sidebar_toggled."""
        top_bar = TopNavigationBar()
        self.assertIn("Verbindung..", top_bar.btn_sidebar.text())
        self.assertEqual(top_bar.btn_sidebar.objectName(), "SidebarToggle")

        toggled = False

        def _on_toggled():
            nonlocal toggled
            toggled = True

        top_bar.sidebar_toggled.connect(_on_toggled)
        top_bar.btn_sidebar.click()
        self.assertTrue(toggled)

    def test_02_top_bar_settings_nav_pill(self):
        """Verify TopNavigationBar includes the Settings tab and emits view_changed."""
        top_bar = TopNavigationBar()
        self.assertIn("settings", top_bar._nav_buttons)
        btn_settings = top_bar._nav_buttons["settings"]
        self.assertIn("Einstellungen", btn_settings.text())

        changed_to = ""

        def _on_view_changed(v):
            nonlocal changed_to
            changed_to = v

        top_bar.view_changed.connect(_on_view_changed)
        btn_settings.click()
        self.assertEqual(changed_to, "settings")

    def test_03_config_manager_boost_options(self):
        """Verify ConfigManager defines and loads all handshake, scan, buffer, and vpn settings."""
        cfg_mgr = ConfigManager()

        # Handshake options
        self.assertIn("ssl_verify", cfg_mgr.config)
        self.assertIn("handshake_connect_timeout", cfg_mgr.config)
        self.assertIn("handshake_read_timeout", cfg_mgr.config)
        self.assertIn("token_refresh_interval_s", cfg_mgr.config)
        self.assertIn("default_stb_model", cfg_mgr.config)
        self.assertIn("device_id_mode", cfg_mgr.config)

        # Scan options
        self.assertIn("scan_threads", cfg_mgr.config)
        self.assertIn("scan_delay_s", cfg_mgr.config)
        self.assertIn("scan_probe_timeout", cfg_mgr.config)
        self.assertIn("scan_auto_requeue", cfg_mgr.config)
        self.assertIn("scan_max_requeue_retries", cfg_mgr.config)
        self.assertIn("validation_workers", cfg_mgr.config)
        self.assertIn("validation_probe_timeout", cfg_mgr.config)

        # Buffer options
        raw_buf = cfg_mgr.get("buffer_settings")
        self.assertIsInstance(raw_buf, dict)
        self.assertIn("mode", raw_buf)
        self.assertIn("start_seconds", raw_buf)
        self.assertIn("buffer_seconds", raw_buf)
        self.assertIn("vlc_caching_ms", raw_buf)
        self.assertIn("fallback_kbps", raw_buf)
        self.assertIn("max_retries", raw_buf)

        # VPN options
        self.assertIn("vpn_auto_switch", cfg_mgr.config)
        self.assertIn("vpn_cooldown_seconds", cfg_mgr.config)
        self.assertIn("vpn_debounce_seconds", cfg_mgr.config)
        self.assertIn("vpn_max_consecutive_hops", cfg_mgr.config)
        self.assertIn("vpn_fallback_country", cfg_mgr.config)
        self.assertIn("vpn_rotation_pool", cfg_mgr.config)

    def test_04_settings_view_load_modify_save(self):
        """Verify SettingsView loads config, modifies fields, and emits save signals."""
        cfg_mgr = ConfigManager()
        vpn = NordVpnManager()
        vpn.set_config_manager(cfg_mgr)
        view = SettingsView(config_mgr=cfg_mgr, vpn_mgr=vpn)

        # Check tab count (6 tabs)
        self.assertEqual(view.tabs.count(), 6)

        # Modify values
        view.chk_ssl_verify.setChecked(True)
        view.spin_hs_connect.setValue(6.5)
        view.spin_scan_threads.setValue(12)
        view.spin_buf_start_s.setValue(2.2)
        view.spin_vpn_cooldown.setValue(25.0)

        saved_cfg = None

        def _on_saved(c):
            nonlocal saved_cfg
            saved_cfg = c

        view.settings_saved.connect(_on_saved)
        view.save_to_config()

        self.assertIsNotNone(saved_cfg)
        self.assertTrue(cfg_mgr.get("ssl_verify"))
        self.assertEqual(cfg_mgr.get("handshake_connect_timeout"), 6.5)
        self.assertEqual(cfg_mgr.get("scan_threads"), 12)
        self.assertEqual(cfg_mgr.get("buffer_settings")["start_seconds"], 2.2)
        self.assertEqual(cfg_mgr.get("vpn_cooldown_seconds"), 25.0)

        # Reset back to defaults
        view.chk_ssl_verify.setChecked(False)
        view.spin_hs_connect.setValue(4.5)
        view.spin_scan_threads.setValue(8)
        view.spin_buf_start_s.setValue(0.8)
        view.spin_vpn_cooldown.setValue(15.0)
        view.save_to_config()

    def test_05_main_window_settings_live_application(self):
        """Verify MainWindow integrates SettingsView, switches to it, and applies live updates."""
        win = MainWindow()
        try:
            self.assertIn("settings", win._views_map)
            self.assertEqual(win._views_map["settings"], win.settings_view)

            # Switch view to settings
            win.switch_view("settings")
            self.assertEqual(win.stack.currentWidget(), win.settings_view)

            # Test live application of buffer settings
            new_buf = BufferSettings(
                mode="proxy",
                start_seconds=1.2,
                buffer_seconds=18.0,
                max_mb=96,
                vlc_caching_ms=1000,
            )
            win._on_buffer_settings_from_view(new_buf)
            self.assertEqual(win.vlc_ctrl.settings.start_seconds, 1.2)
            self.assertEqual(win.vlc_ctrl.settings.buffer_seconds, 18.0)
            self.assertEqual(win.vlc_ctrl.settings.max_mb, 96)

            # Test live application of scanner threads
            test_cfg = dict(win.config_mgr.config)
            test_cfg["scan_threads"] = 16
            test_cfg["scan_delay_s"] = 0.25
            win._on_settings_applied(test_cfg)
            self.assertEqual(win.scanner_view.spin_threads.value(), 16)
            self.assertEqual(win.scanner_view.combo_delay.currentText(), "250 ms")
        finally:
            win.close()

    def test_06_device_id_mode_random_vs_deterministic(self):
        """Verify StbClient respects device_id_mode='random' vs 'deterministic'."""
        from clients.stb_client import StbClient

        cl_det = StbClient(
            portal_url="http://example.com/c/",
            mac="00:1A:79:AA:BB:CC",
            device_id_mode="deterministic",
            enable_inspector=False,
        )
        cl_rand = StbClient(
            portal_url="http://example.com/c/",
            mac="00:1A:79:AA:BB:CC",
            device_id_mode="random",
            enable_inspector=False,
        )

        self.assertEqual(cl_det.device_id_mode, "deterministic")
        self.assertEqual(cl_rand.device_id_mode, "random")
        self.assertEqual(len(cl_rand.device_id), 64)
        # Random IDs must differ from deterministic SHA-256 hash
        self.assertNotEqual(cl_det.device_id, cl_rand.device_id)

    def test_07_pcr_rate_smoothing(self):
        """Verify BufferSettings and _Session apply PCR rate smoothing when enabled."""
        from core.stream_buffer import BufferSettings, _Session

        st_smooth = BufferSettings(pcr_smoothing_enabled=True)
        session_smooth = _Session("http://test.ts", {}, st_smooth)
        session_smooth._record_pcr(0, 0.0)
        session_smooth._record_pcr(500_000, 1.0)
        initial_bps = session_smooth.mux_bps
        self.assertGreater(initial_bps, 0)

        # Feed a sharp jump with smoothing active: should be weighted 0.75 / 0.25
        # dt = 2.0 - 0.0 = 2.0s, db = 1_500_000 bytes -> calc_bps = 6.0 Mbps
        calc_bps = (1_500_000 * 8.0) / 2.0
        session_smooth._record_pcr(1_500_000, 2.0)
        expected_smoothed = 0.75 * initial_bps + 0.25 * calc_bps
        self.assertAlmostEqual(session_smooth.mux_bps, expected_smoothed, delta=100.0)

        # Now test with smoothing disabled: directly assigned without EMA
        st_raw = BufferSettings(pcr_smoothing_enabled=False)
        session_raw = _Session("http://test.ts", {}, st_raw)
        session_raw._record_pcr(0, 0.0)
        session_raw._record_pcr(500_000, 1.0)
        session_raw._record_pcr(1_500_000, 2.0)
        self.assertAlmostEqual(session_raw.mux_bps, calc_bps, delta=100.0)

    def test_08_check_mac_account_boost_options(self):
        """Verify check_mac_account accepts and uses genre_param, sortby_param, and fallback_get_all."""
        from unittest.mock import MagicMock, patch
        from clients.stb_client import check_mac_account

        with patch("clients.stb_client.StbClient") as mock_stb_cls:
            mock_client = MagicMock()
            mock_client.token = "test_token"
            mock_client.normalized_load_url = "http://example.com/c/load.php"
            mock_client.get_profile.return_value = {"blocked": "0", "expire_billing_date": "2027-10-10"}
            mock_client.get_account_info.return_value = {"expire": "2027-10-10"}
            mock_client._request.return_value = {"total_items": 42}
            mock_stb_cls.return_value = mock_client
            mock_stb_cls.format_mac = lambda m: m.upper()

            res = check_mac_account(
                portal_url="http://example.com/c/",
                mac="00:1A:79:00:11:22",
                genre_param="15",
                sortby_param="name",
                fallback_get_all=False,
                verify_ssl=True,
                device_id_mode="random",
            )

            self.assertTrue(res["valid"])
            self.assertEqual(res["channels"], 42)
            mock_client._request.assert_called_once()
            call_args = mock_client._request.call_args
            self.assertEqual(call_args[0][0], "get_ordered_list")
            self.assertEqual(call_args[1]["extra_params"]["genre"], "15")
            self.assertEqual(call_args[1]["extra_params"]["sortby"], "name")

    def test_09_vpn_fallback_country_and_reload(self):
        """Verify NordVpnManager respects configured vpn_fallback_country and reload_config."""
        cfg_mgr = ConfigManager()
        cfg_mgr.set("vpn_fallback_country", "Switzerland", auto_save=False)
        vpn = NordVpnManager()
        vpn.set_config_manager(cfg_mgr)

        self.assertEqual(vpn.guess_country_for_profile("Unknown Profile", "unknown-host.net"), "Switzerland")
        candidates = vpn.get_rotation_candidates("Switzerland")
        self.assertIn("Switzerland", candidates)

        # Test reload_config resets internal CLI cache
        vpn._cli_path = "C:\\fake\\nordvpn.exe"
        cfg_mgr.set("vpn_custom_cli_path", "", auto_save=False)
        vpn.reload_config()
        self.assertNotEqual(vpn._cli_path, "C:\\fake\\nordvpn.exe")

    def test_10_external_player_caching_and_hwdec(self):
        """Verify ExternalPlayerRunner passes caching_ms and hw_decode flags without crashing."""
        from unittest.mock import MagicMock, patch
        from player.external_player import ExternalPlayerRunner

        runner = ExternalPlayerRunner()
        with patch("os.path.exists", return_value=True), patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_popen.return_value = mock_proc

            # VLC with custom caching
            runner.play("vlc", "C:\\vlc\\vlc.exe", "http://stream.ts", caching_ms=3500, hw_decode=True)
            vlc_cmd = mock_popen.call_args[0][0]
            self.assertIn("--network-caching=3500", vlc_cmd)
            self.assertIn("--avcodec-hw=any", vlc_cmd)

            # MPV with custom caching and hwdec
            runner.play("mpv", "C:\\mpv\\mpv.exe", "http://stream.ts", caching_ms=2000, hw_decode=True)
            mpv_cmd = mock_popen.call_args[0][0]
            self.assertIn("--hwdec=auto", mpv_cmd)
            self.assertIn("--demuxer-readahead-secs=2.0", mpv_cmd)


if __name__ == "__main__":
    unittest.main()
