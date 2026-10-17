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


if __name__ == "__main__":
    unittest.main()
