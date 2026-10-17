"""
Main Application Window (Orchestrator) for STB Pro v6.0 Qt6 Edition.
Coordinates Sidebar, TopNavigationBar, LiveTVView, VODView, ScannerView, InspectorView, ConsoleView,
LibVLC Hardware Player, External Player Runner, Fullscreen HUD Overlay, PiP Mini-Player,
Multi-Thread MAC Scanner, Parallel Category Validator, and all 7 Dialogs.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import collections
import datetime
import os
import queue
import threading
import time
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QRect, Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import requests
from requests.adapters import HTTPAdapter

from clients.m3u_client import M3UClient
from clients.stb_client import STB_PRESETS, RateLimitError, StbClient, check_mac_account
from clients.throttle import ScanThrottleController
from clients.xtream_client import XtreamClient
from core.config_manager import APP_DIR, ConfigManager
from core.logo_cache import logo_cache
from core.m3u_exporter import build_m3u_playlist
from core.mac_database import MacDatabase
from core.models import AppState, Channel, EPGProgram, Profile, StreamProbeResult, quality_from_dimensions
from core.preview_grabber import ThumbGrabber, grab_thumbnail, load_cached_thumb, save_thumb, thumb_age_s
from core.recorder import Recorder
from core.scan_repository import ScanRepository, ScanHost, ScanAccount
from core.signals import event_bus, worker_pool
from core.stream_buffer import BufferSettings
from core.stream_probe import probe_stream
from player.external_player import ExternalPlayerRunner
from player.osd_overlay import FullscreenOSDOverlay
from player.vlc_controller import VLCPlayerController
from ui.components.sidebar import SidebarWidget
from ui.components.top_bar import TopNavigationBar
from ui.dialogs import (
    BufferConfigDialog,
    EPGGuideDialog,
    JobsDialog,
    JsonViewerDialog,
    MacDatabaseDialog,
    ProfileEditorDialog,
    SeriesBrowserDialog,
)
from ui.theme import apply_obsidian_theme
from ui.views import (
    ConsoleView,
    InspectorView,
    LiveTVView,
    ScannerView,
    VODView,
)


class MainWindow(QMainWindow):
    # Internal cross-thread marshaling signals
    _val_progress_sig = Signal(str, bool, int, str, int, int, object)  # (ch_id, alive, latency_ms, quality_tag, done, total, thumb_bytes)
    _val_finished_sig = Signal(int, int)                  # (alive_count, dead_count)
    _val_thumb_progress_sig = Signal(str, object, int, int)  # (ch_id, thumb_bytes, done, total)
    _val_thumb_finished_sig = Signal(int)                     # (total_count)
    _epg_loaded_sig = Signal(str, list)                   # (ch_id, List[EPGProgram])
    _probe_done_sig = Signal(str, object)                 # (ch_id, StreamProbeResult)
    _preview_ready_sig = Signal(str, bytes, str)          # (ch_id, jpeg_bytes, badge_text)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("STB-Emulator Pro by InfoHazard & H7CFoX")
        self.resize(1540, 920)
        self.setMinimumSize(960, 580)

        # Set App Icon
        icon_ico = os.path.join(APP_DIR, "assets", "app_icon.ico")
        icon_png = os.path.join(APP_DIR, "assets", "app_icon.png")
        if os.path.exists(icon_ico):
            self.setWindowIcon(QIcon(icon_ico))
        elif os.path.exists(icon_png):
            self.setWindowIcon(QIcon(icon_png))

        # Core Managers & State
        self.config_mgr = ConfigManager()
        self.mac_db = MacDatabase()
        self.scan_repo = ScanRepository()
        self.state = AppState()
        self.logo_cache = logo_cache
        self.thumb_grabber = ThumbGrabber()

        rec_dir = os.path.join(APP_DIR, "recordings")
        os.makedirs(rec_dir, exist_ok=True)
        self.recorder = Recorder(
            out_dir=rec_dir,
            on_change=lambda: event_bus.recorder_changed.emit(),
            log=lambda msg: event_bus.log_message.emit(msg),
        )

        raw_buf = self.config_mgr.get("buffer_settings") or {}
        buf_settings = BufferSettings.from_dict(raw_buf)
        # Sanitize legacy extreme caching values (e.g., 7800ms VLC caching or 6s prebuffer)
        if buf_settings.vlc_caching_ms > 3500:
            buf_settings.vlc_caching_ms = 1500
        if buf_settings.start_seconds > 4.5:
            buf_settings.start_seconds = 1.5
        self.vlc_ctrl = VLCPlayerController(settings=buf_settings)
        self.ext_player = ExternalPlayerRunner()

        self.active_client: Optional[Any] = None
        self.genre_map: Dict[str, str] = {"*": "Alle Kategorien"}
        self.is_fullscreen: bool = False
        self.is_cinema_mode: bool = False
        self.is_pip_mode: bool = False
        self._normal_geometry: Optional[QRect] = None
        self._was_maximized: bool = False
        self._pending_preview_channel: Optional[Channel] = None
        self._settled_channel: Optional[Channel] = None
        self._sel_seq: int = 0
        self._play_seq: int = 0
        self.resolved_stream_cache: Dict[str, tuple[str, float]] = {}
        self._last_track_signature: tuple = ()

        # Background cancellation flags
        self._scan_stop_ev = threading.Event()
        self._scan_pause_ev = threading.Event()
        self._scan_pause_ev.set()
        self._val_stop_ev = threading.Event()
        self._probe_cancel_ev = threading.Event()

        # Debounce timer for channel selection (EPG + pre-resolve + Standbild preview)
        self._selection_timer = QTimer(self)
        self._selection_timer.setSingleShot(True)
        self._selection_timer.setInterval(320)
        self._selection_timer.timeout.connect(self._on_selection_settled)

        # Debounce timer for live Standbild preview grabbing
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(260)
        self._preview_timer.timeout.connect(self._trigger_channel_preview)

        # Automatic live snapshot timer for active playback (1.8s post-start)
        self._live_snapshot_timer = QTimer(self)
        self._live_snapshot_timer.setSingleShot(True)
        self._live_snapshot_timer.setInterval(1800)
        self._live_snapshot_timer.timeout.connect(self._snapshot_playing_channel)

        # Build UI Layout
        self._build_ui()
        self._bind_signals()
        self._setup_shortcuts()
        self._load_initial_config()

        # Periodic telemetry & seekbar timer (600ms)
        self._telemetry_timer = QTimer(self)
        self._telemetry_timer.setInterval(600)
        self._telemetry_timer.timeout.connect(self._tick_telemetry)
        self._telemetry_timer.start()

        event_bus.log_message.emit(
            "⚡ STB Pro v6.0 (Qt6 / PySide6 Edition) bereit. Alle Profile & Datenbanken geladen."
        )

    # ══════════════════════════════════════════════════════════════════════
    # 1. UI Construction & Signal Wiring
    # ══════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root_lay = QVBoxLayout(central)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # Top Bar
        self.top_bar = TopNavigationBar(self)
        root_lay.addWidget(self.top_bar)

        # Body Area: Resizable & Collapsible Left Sidebar + Stacked Main Workspace
        self.body_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.body_splitter.setChildrenCollapsible(False)

        self.sidebar = SidebarWidget(self)
        self.body_splitter.addWidget(self.sidebar)

        self.stack = QStackedWidget(self)
        self.live_view = LiveTVView(logo_cache=self.logo_cache, parent=self)
        self.vod_view = VODView(logo_cache=self.logo_cache, parent=self)
        self.scanner_view = ScannerView(parent=self)
        self.inspector_view = InspectorView(parent=self)
        self.console_view = ConsoleView(parent=self)

        self._views_map: Dict[str, QWidget] = {
            "live": self.live_view,
            "vod": self.vod_view,
            "scanner": self.scanner_view,
            "inspector": self.inspector_view,
            "console": self.console_view,
        }
        for w in self._views_map.values():
            self.stack.addWidget(w)

        self.body_splitter.addWidget(self.stack)
        self.body_splitter.setStretchFactor(0, 0)
        self.body_splitter.setStretchFactor(1, 1)
        self.body_splitter.setSizes([285, 1255])
        root_lay.addWidget(self.body_splitter, 1)

        # Fullscreen HUD Overlay
        self.osd = FullscreenOSDOverlay(
            main_window=self,
            on_play_pause=self._on_play_pause,
            on_stop=self._on_stop_playback,
            on_prev=self._on_prev_channel,
            on_next=self._on_next_channel,
            on_volume=self._on_volume_changed,
            on_toggle_mute=self._on_mute_toggled,
            on_aspect_ratio=self.vlc_ctrl.set_aspect_ratio,
            on_exit_fullscreen=self.exit_fullscreen,
            on_channel_select=self._on_osd_channel_selected,
        )

    def _bind_signals(self):
        # Global Event Bus
        event_bus.log_message.connect(self.console_view.append_log)
        event_bus.http_Exchange_logged.connect(self.inspector_view.add_http_entry)
        event_bus.recorder_changed.connect(self._on_recorder_changed)
        event_bus.scan_result_received.connect(self.scanner_view.add_scan_result)
        event_bus.scan_progress_updated.connect(self.scanner_view.update_scan_progress)
        event_bus.scan_state_changed.connect(self.scanner_view.set_scan_running)

        # Internal Worker Signals
        self._val_progress_sig.connect(self._on_val_progress_ui)
        self._val_finished_sig.connect(self._on_val_finished_ui)
        self._val_thumb_progress_sig.connect(self._on_val_thumb_progress_ui)
        self._val_thumb_finished_sig.connect(self._on_val_thumb_finished_ui)
        self._epg_loaded_sig.connect(self._on_epg_loaded_ui)
        self._probe_done_sig.connect(self._on_probe_done_ui)
        self._preview_ready_sig.connect(self._on_preview_ready_ui)

        # VLC Signals
        self.vlc_ctrl.state_changed.connect(self.live_view.update_player_state)
        self.vlc_ctrl.state_changed.connect(self._on_vlc_state_changed)
        self.vlc_ctrl.buffering_changed.connect(self._on_vlc_buffering)

        # Top Bar Signals
        self.top_bar.view_changed.connect(self.switch_view)
        self.top_bar.sidebar_toggled.connect(self.toggle_sidebar)
        self.top_bar.cinema_toggled.connect(self.toggle_cinema_mode)
        self.top_bar.pip_toggled.connect(self.toggle_pip_mode)
        self.top_bar.fullscreen_requested.connect(self.toggle_fullscreen)
        self.top_bar.buffer_dialog_requested.connect(self.open_buffer_dialog)
        self.top_bar.jobs_dialog_requested.connect(self.open_jobs_dialog)
        self.top_bar.account_info_requested.connect(self.show_account_details)
        self.top_bar.record_stop_requested.connect(self._stop_active_recordings)

        # Sidebar Signals
        self.sidebar.host_selected.connect(self._on_scan_host_selected)
        self.sidebar.account_selected.connect(self._on_scan_account_selected)
        self.sidebar.reload_scans_requested.connect(self._on_reload_scans)
        self.sidebar.connect_requested.connect(self.connect_active_profile)
        self.sidebar.disconnect_requested.connect(self.disconnect_portal)
        self.sidebar.quick_fields_changed.connect(self._on_quick_fields_changed)
        self.sidebar.player_engine_changed.connect(self._on_player_engine_changed)
        self.sidebar.prebuffer_preset_changed.connect(self._on_prebuffer_preset_changed)
        self.sidebar.timeout_changed.connect(self._on_timeout_changed)
        self.sidebar.ui_scale_changed.connect(self._on_ui_scale_changed)
        self.sidebar.mac_db_requested.connect(self.open_mac_db_dialog)

        # Live TV View Signals
        self.live_view.channel_selected.connect(self._on_channel_selected)
        self.live_view.channel_play_requested.connect(self.play_channel)
        self.live_view.favorite_toggled.connect(self.toggle_channel_favorite)
        self.live_view.probe_channel_requested.connect(self.probe_channel_stream)
        self.live_view.copy_url_requested.connect(self.copy_channel_url)
        self.live_view.record_channel_requested.connect(self.record_channel)
        self.live_view.export_m3u_requested.connect(self.export_channels_m3u)
        self.live_view.raw_json_requested.connect(self.open_json_viewer)
        self.live_view.epg_guide_requested.connect(self.open_epg_guide_dialog)
        self.live_view.validate_category_requested.connect(self.start_category_validation)
        self.live_view.fetch_group_thumbnails_requested.connect(self.start_group_thumbnail_fetch)
        self.live_view.stop_validation_requested.connect(self.stop_category_validation)
        self.live_view.chk_hide_dead.toggled.connect(
            lambda checked: self.config_mgr.set("hide_dead_channels", bool(checked))
        )

        self.live_view.prev_channel_requested.connect(self._on_prev_channel)
        self.live_view.next_channel_requested.connect(self._on_next_channel)
        self.live_view.play_pause_requested.connect(self._on_play_pause)
        self.live_view.stop_requested.connect(self._on_stop_playback)
        self.live_view.mute_toggled.connect(self._on_mute_toggled)
        self.live_view.volume_changed.connect(self._on_volume_changed)
        self.live_view.aspect_ratio_changed.connect(self.vlc_ctrl.set_aspect_ratio)
        self.live_view.playback_speed_changed.connect(self.vlc_ctrl.set_rate)
        self.live_view.audio_track_selected.connect(self.vlc_ctrl.set_audio_track)
        self.live_view.subtitle_track_selected.connect(self.vlc_ctrl.set_subtitle_track)
        self.live_view.seek_position_requested.connect(self.vlc_ctrl.set_position)
        self.live_view.seek_relative_requested.connect(self.vlc_ctrl.seek_relative)
        self.live_view.snapshot_requested.connect(self.take_video_snapshot)
        self.live_view.external_player_requested.connect(self._play_current_in_external)
        self.live_view.cinema_mode_requested.connect(self.toggle_cinema_mode)
        self.live_view.pip_mode_requested.connect(self.toggle_pip_mode)
        self.live_view.fullscreen_requested.connect(self.toggle_fullscreen)
        self.live_view.video_mouse_moved.connect(lambda: self.osd.show() if self.is_fullscreen else None)

        # VOD & Series View Signals
        self.vod_view.mode_changed.connect(self._on_vod_mode_changed)
        self.vod_view.category_selected.connect(self._on_vod_category_selected)
        self.vod_view.portal_search_requested.connect(self._on_vod_portal_search)
        self.vod_view.play_vod_requested.connect(self.play_vod_item)
        self.vod_view.download_vod_requested.connect(self.download_vod_item)
        self.vod_view.copy_vod_url_requested.connect(self.copy_vod_url)
        self.vod_view.open_series_requested.connect(self.open_series_dialog)
        self.vod_view.favorite_toggled.connect(self.toggle_vod_favorite)
        self.vod_view.raw_json_requested.connect(self.open_json_viewer)

        # MAC Scanner Signals
        self.scanner_view.start_scan_requested.connect(self.start_mac_scan)
        self.scanner_view.stop_scan_requested.connect(self.stop_mac_scan)
        self.scanner_view.pause_scan_requested.connect(self.pause_mac_scan)
        self.scanner_view.resume_scan_requested.connect(self.resume_mac_scan)
        self.scanner_view.scan_settings_updated.connect(self.update_scan_settings)
        self.scanner_view.apply_mac_requested.connect(self.apply_mac_from_scanner_or_db)
        self.scanner_view.prepend_db_macs_requested.connect(self._prepend_known_macs_to_scanner)
        self.scanner_view.scan_exported.connect(lambda p: self._on_reload_scans())

        # Inspector Signals
        self.inspector_view.handshake_test_requested.connect(self._run_inspector_handshake_test)
        self.inspector_view.profile_dump_requested.connect(self._dump_active_client_state)

    def _is_text_input_focused(self) -> bool:
        fw = QApplication.focusWidget()
        return isinstance(fw, (QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox))

    def _bind_guarded_shortcut(self, key_seq: str, callback):
        def _handler():
            if not self._is_text_input_focused():
                callback()

        sc = QShortcut(QKeySequence(key_seq), self)
        sc.activated.connect(_handler)
        return sc

    def _cycle_aspect_ratio(self):
        combo = self.live_view.combo_aspect
        nxt = (combo.currentIndex() + 1) % max(1, combo.count())
        combo.setCurrentIndex(nxt)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("F11"), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self, activated=self._on_escape_pressed)
        QShortcut(QKeySequence("F2"), self, activated=self._fav_active_channel)
        QShortcut(QKeySequence("PgUp"), self, activated=self._on_prev_channel)
        QShortcut(QKeySequence("PgDown"), self, activated=self._on_next_channel)
        QShortcut(
            QKeySequence("Ctrl+F"),
            self,
            activated=lambda: self.live_view.entry_search.setFocus(),
        )

        # Single-key shortcuts guarded so they don't steal characters when typing in search/URL inputs
        self._bind_guarded_shortcut("Space", self._on_play_pause)
        self._bind_guarded_shortcut("M", self._on_mute_toggled)
        self._bind_guarded_shortcut("T", self.toggle_cinema_mode)
        self._bind_guarded_shortcut("P", self.toggle_pip_mode)
        self._bind_guarded_shortcut("C", self.osd.toggle_drawer)
        self._bind_guarded_shortcut("R", self._record_active_channel)
        self._bind_guarded_shortcut("F", self.toggle_fullscreen)
        self._bind_guarded_shortcut("S", self._on_stop_playback)
        self._bind_guarded_shortcut("A", self._cycle_aspect_ratio)

    def _load_initial_config(self):
        last_host = str(self.config_mgr.get("last_scan_host", ""))
        last_mac = str(self.config_mgr.get("last_scan_mac", ""))
        self.sidebar.load_scan_repository(self.scan_repo, default_host=last_host, default_mac=last_mac)

        sel_acc = self.sidebar.get_selected_account()
        sel_host = self.sidebar.get_selected_host()
        if sel_acc and sel_host:
            active_url = sel_acc.portal_url or sel_host.portal_url
            self.scanner_view.set_portal_url(active_url)
            self.state.current_profile_name = f"{sel_host.host_name} ({sel_acc.mac})"

        vol = int(self.config_mgr.get("player_volume", 100))
        self.live_view.slider_volume.setValue(vol)
        self.vlc_ctrl.set_volume(vol)

        sel_player = str(self.config_mgr.get("selected_player", "Integrierter Player"))
        self.sidebar.combo_player.blockSignals(True)
        self.sidebar.combo_player.setCurrentText(sel_player)
        self.sidebar.combo_player.blockSignals(False)

        timeout_lbl = str(self.config_mgr.get("connection_timeout_label", "8s"))
        self.sidebar.combo_timeout.blockSignals(True)
        if self.sidebar.combo_timeout.findText(timeout_lbl) >= 0:
            self.sidebar.combo_timeout.setCurrentText(timeout_lbl)
        self.sidebar.combo_timeout.blockSignals(False)

        ui_scale = str(self.config_mgr.get("ui_scale", "100%"))
        self.sidebar.combo_scale.blockSignals(True)
        if self.sidebar.combo_scale.findText(ui_scale) >= 0:
            self.sidebar.combo_scale.setCurrentText(ui_scale)
        self.sidebar.combo_scale.blockSignals(False)
        if ui_scale != "100%":
            self._on_ui_scale_changed(ui_scale)

        hide_dead = bool(self.config_mgr.get("hide_dead_channels", True))
        self.live_view.chk_hide_dead.blockSignals(True)
        self.live_view.chk_hide_dead.setChecked(hide_dead)
        self.live_view.proxy_model.set_hide_dead(hide_dead)
        self.live_view.chk_hide_dead.blockSignals(False)

        st = self.vlc_ctrl.settings
        self.sidebar.combo_prebuffer.blockSignals(True)
        if st.mode != "proxy":
            self.sidebar.combo_prebuffer.setCurrentIndex(0)
        elif st.start_seconds <= 2.0:
            self.sidebar.combo_prebuffer.setCurrentIndex(1)
        elif st.start_seconds <= 4.5:
            self.sidebar.combo_prebuffer.setCurrentIndex(2)
        elif st.start_seconds <= 7.5:
            self.sidebar.combo_prebuffer.setCurrentIndex(3)
        else:
            self.sidebar.combo_prebuffer.setCurrentIndex(4)
        self.sidebar.combo_prebuffer.blockSignals(False)

    # ══════════════════════════════════════════════════════════════════════
    # 2. View Navigation, Cinema Mode, PiP Mode & Fullscreen
    # ══════════════════════════════════════════════════════════════════════

    def switch_view(self, view_key: str):
        target = self._views_map.get(view_key)
        if not target:
            return
        self.stack.setCurrentWidget(target)
        if view_key == "vod" and self.state.is_connected and self.vod_view.model.rowCount() == 0:
            self._load_vod_or_series_categories(self.vod_view.current_mode)

    def toggle_sidebar(self):
        vis = not self.sidebar.isVisible()
        self.sidebar.setVisible(vis)
        self.state.sidebar_visible = vis

    def toggle_cinema_mode(self):
        if self.is_fullscreen or self.is_pip_mode:
            return
        self.is_cinema_mode = not self.is_cinema_mode
        self.sidebar.setVisible(not self.is_cinema_mode)
        self.live_view.set_cinema_layout(self.is_cinema_mode, pip_mode=False)

    def toggle_pip_mode(self):
        """Switches into a floating Always-on-Top Picture-in-Picture mini-player window."""
        if self.is_fullscreen:
            self.exit_fullscreen()

        self.is_pip_mode = not self.is_pip_mode
        self.state.is_pip_mode = self.is_pip_mode

        if self.is_pip_mode:
            self._was_maximized = self.isMaximized()
            self._normal_geometry = self.normalGeometry() if self._was_maximized else self.geometry()
            self.top_bar.set_active_view("live")
            self.stack.setCurrentWidget(self.live_view)
            self.top_bar.setVisible(False)
            self.sidebar.setVisible(False)
            self.live_view.set_cinema_layout(True, pip_mode=True)
            if self._was_maximized:
                self.showNormal()
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
            self.setMinimumSize(360, 220)
            scr = self.screen() or QGuiApplication.primaryScreen()
            avail = scr.availableGeometry()
            w, h = 480, 270
            self.setGeometry(avail.right() - w - 24, avail.bottom() - h - 48, w, h)
            self.show()
            event_bus.log_message.emit("🗗 PiP Mini-Player aktiviert (Drücke [P] oder [Esc] zum Zurückkehren).")
        else:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            self.setMinimumSize(960, 580)
            self.top_bar.setVisible(True)
            self.sidebar.setVisible(not self.is_cinema_mode)
            self.live_view.set_cinema_layout(self.is_cinema_mode, pip_mode=False)
            if self._normal_geometry:
                self.setGeometry(self._normal_geometry)
            if self._was_maximized:
                self.showMaximized()
            else:
                self.showNormal()

        if self.vlc_ctrl.is_initialized:
            self.vlc_ctrl.rebind_hwnd(self.live_view.get_video_hwnd())

    def toggle_fullscreen(self):
        if self.ext_player.is_running():
            if self.ext_player.toggle_fullscreen():
                return
        if self.is_fullscreen:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    def enter_fullscreen(self):
        if self.is_fullscreen:
            return
        if self.is_pip_mode:
            self.toggle_pip_mode()

        self._was_maximized = self.isMaximized()
        self._normal_geometry = self.normalGeometry() if self._was_maximized else self.geometry()
        self.is_fullscreen = True
        self.state.is_fullscreen = True
        self.top_bar.set_active_view("live")
        self.stack.setCurrentWidget(self.live_view)
        self.top_bar.setVisible(False)
        self.sidebar.setVisible(False)
        self.live_view.set_cinema_layout(True, pip_mode=False)
        self.live_view.controls_card.setVisible(False)
        self.showFullScreen()
        self.osd.show()

    def exit_fullscreen(self):
        if not self.is_fullscreen:
            return
        self.is_fullscreen = False
        self.state.is_fullscreen = False
        self.osd.hide_all()
        if self._was_maximized:
            self.showMaximized()
        else:
            self.showNormal()
            if self._normal_geometry:
                self.setGeometry(self._normal_geometry)
        self.top_bar.setVisible(True)
        self.sidebar.setVisible(not self.is_cinema_mode)
        self.live_view.controls_card.setVisible(True)
        self.live_view.set_cinema_layout(self.is_cinema_mode, pip_mode=False)

    def _on_escape_pressed(self):
        if self.is_fullscreen:
            self.exit_fullscreen()
        elif self.is_pip_mode:
            self.toggle_pip_mode()
        elif self.is_cinema_mode:
            self.toggle_cinema_mode()

    # ══════════════════════════════════════════════════════════════════════
    # 3. Profile Management & Async Portal Connection
    # ══════════════════════════════════════════════════════════════════════

    def _get_current_profile(self) -> Profile:
        acc = self.sidebar.get_selected_account()
        host = self.sidebar.get_selected_host()
        url = self.sidebar.entry_url.text().strip()
        mac = self.sidebar.entry_mac.text().strip()
        proxy = self.sidebar.entry_proxy.text().strip()

        if host and acc:
            portal_url = url or acc.portal_url or host.portal_url
            mac_val = mac or acc.mac
            name = f"{host.host_name} ({mac_val})"
            prof = Profile(
                name=name,
                provider_type="Stalker MAC",
                portal_url=portal_url,
                mac=mac_val,
                model="MAG 250",
                proxy=proxy,
            )
            ids = StbClient.generate_device_ids(mac_val)
            prof.serial_number = ids["sn"]
            prof.device_id = ids["device_id"]
            prof.device_id2 = ids["device_id2"]
            prof.signature = ids["signature"]
            self.state.current_profile_name = name
            return prof

        # Fallback falls manuell eingegeben
        if url or mac:
            name = "Manuelle Schnellverbindung"
            prof = Profile(
                name=name,
                provider_type="Stalker MAC",
                portal_url=url,
                mac=mac,
                model="MAG 250",
                proxy=proxy,
            )
            if mac:
                ids = StbClient.generate_device_ids(mac)
                prof.serial_number = ids["sn"]
                prof.device_id = ids["device_id"]
                prof.device_id2 = ids["device_id2"]
                prof.signature = ids["signature"]
            return prof

        profs = self.config_mgr.get_profiles()
        return profs[0] if profs else Profile("Standard", portal_url="http://", mac="00:1A:79:00:00:00")

    def _on_scan_host_selected(self, host_name: str):
        self.config_mgr.set("last_scan_host", host_name)
        event_bus.log_message.emit(f"🌐 Host / Portal gewählt: {host_name}")

    def _on_scan_account_selected(self, host_name: str, mac: str):
        self.config_mgr.set("last_scan_host", host_name)
        self.config_mgr.set("last_scan_mac", mac)
        self.state.current_profile_name = f"{host_name} ({mac})"
        acc = self.scan_repo.get_account(host_name, mac)
        if acc:
            self.scanner_view.set_portal_url(acc.portal_url)
            event_bus.log_message.emit(f"🔑 Account gewählt: {mac} (Host: {host_name}, {acc.channels:,} Kanäle)")

    def _on_reload_scans(self):
        total = self.scan_repo.reload()
        last_host = str(self.config_mgr.get("last_scan_host", ""))
        last_mac = str(self.config_mgr.get("last_scan_mac", ""))
        self.sidebar.load_scan_repository(self.scan_repo, default_host=last_host, default_mac=last_mac)
        event_bus.log_message.emit(
            f"🔄 Scan-Ordner 'mac_scans/' aktualisiert: {len(self.scan_repo.get_hosts())} Hosts mit {total} Logins bereit."
        )

    def _refresh_sidebar_profiles(self, select_name: Optional[str] = None):
        pass

    def _on_profile_selected(self, name: str):
        pass

    def _on_profile_new(self):
        pass

    def _on_profile_edit(self, name: str):
        pass

    def _on_profile_clone(self, name: str):
        pass

    def _on_profile_delete(self, name: str):
        pass

    def _on_quick_fields_changed(self, url: str, mac_or_user: str, proxy: str):
        prof = self._get_current_profile()
        if url:
            prof.url = url
        if mac_or_user:
            if prof.portal_type == "xtream":
                prof.username = mac_or_user
            elif prof.portal_type == "stalker":
                new_mac = StbClient.format_mac(mac_or_user)
                if new_mac != prof.mac:
                    prof.mac = new_mac
                    ids = StbClient.generate_device_ids(new_mac)
                    prof.serial_number = ids["sn"]
                    prof.device_id = ids["device_id"]
                    prof.device_id2 = ids["device_id2"]
                    prof.signature = ids["signature"]
        prof.proxy = proxy
        self.config_mgr.save_profile(prof)

    def connect_active_profile(self):
        prof = self._get_current_profile()
        if not prof.url:
            QMessageBox.warning(self, "Verbindungsfehler", "Bitte eine gültige Portal-/Server-URL eingeben.")
            return

        self.sidebar.set_connected_state(False, busy=True)
        self.top_bar.set_provider_status(False, "Verbinde...")
        timeout_s = self.config_mgr.get_timeout_seconds()
        cached_eps = self.config_mgr.get("cached_endpoints", {}) or {}

        event_bus.log_message.emit(
            f"[*] Verbinde mit '{prof.name}' ({prof.provider_type}) -> {prof.url} ..."
        )

        def _task():
            ptype = prof.portal_type
            if ptype == "stalker":
                norm_ep = cached_eps.get(prof.url.strip().rstrip("/"))
                client = StbClient(
                    portal_url=prof.url,
                    mac=prof.mac,
                    model=prof.model,
                    serial_number=prof.serial_number or None,
                    device_id=prof.device_id or None,
                    device_id2=prof.device_id2 or None,
                    signature=prof.signature or None,
                    user_agent=prof.user_agent or None,
                    timeout=timeout_s,
                    normalized_load_url=norm_ep,
                )
                if prof.proxy:
                    client.session.proxies.update({"http": prof.proxy, "https": prof.proxy})
                client.handshake()
                profile_info = client.get_profile()
                exp_str = str(profile_info.get("expire_billing_date") or "")
                try:
                    acc = client.get_account_info()
                    if acc.get("expire"):
                        exp_str = str(acc["expire"])
                except Exception:
                    pass
                genres_raw = client.get_genres()
                channels_raw = client.get_all_channels()
                client.start_keepalive(interval_seconds=75)
                summary = f"Stalker: {prof.mac} ({len(channels_raw)} Sender)"
                if exp_str and exp_str not in ("0000-00-00 00:00:00", "Unbekannt"):
                    summary += f" | Exp: {exp_str[:10]}"
                return {
                    "client": client,
                    "genres": genres_raw,
                    "channels": channels_raw,
                    "summary": summary,
                    "expire": exp_str or "Aktiv",
                }

            elif ptype == "xtream":
                client = XtreamClient(
                    server_url=prof.server_url or prof.url,
                    username=prof.username,
                    password=prof.password,
                    output_format=prof.xc_format or "ts",
                    timeout=timeout_s,
                    user_agent=prof.user_agent or None,
                )
                if prof.proxy:
                    client.session.proxies.update({"http": prof.proxy, "https": prof.proxy})
                client.authenticate()
                p_sum = client.get_profile_summary()
                genres_raw = client.get_live_categories()
                channels_raw = client.get_all_channels()
                summary = f"XC: {prof.username} ({len(channels_raw)} Sender | Exp: {p_sum.get('expire_date', '—')})"
                return {
                    "client": client,
                    "genres": genres_raw,
                    "channels": channels_raw,
                    "summary": summary,
                    "expire": p_sum.get("expire_date", "Aktiv"),
                }

            else:
                client = M3UClient(source=prof.m3u_url or prof.url, timeout=timeout_s)
                channels_raw = client.load_playlist()
                genres_raw = client.genres
                summary = f"M3U ({len(channels_raw)} Sender)"
                return {
                    "client": client,
                    "genres": genres_raw,
                    "channels": channels_raw,
                    "summary": summary,
                    "expire": "Playlist",
                }

        worker_pool.run_async(
            _task,
            on_success=lambda res: self._on_connect_success(prof, res),
            on_error=self._on_connect_error,
        )

    def _on_connect_success(self, prof: Profile, res: Dict[str, Any]):
        if self.active_client and hasattr(self.active_client, "close"):
            try:
                self.active_client.close()
            except Exception:
                pass

        self.active_client = res["client"]
        self.state.is_connected = True
        self.state.connection_status_text = res["summary"]

        # Cache discovered Stalker load_url & save working MAC into MacDatabase
        if prof.portal_type == "stalker" and isinstance(self.active_client, StbClient):
            if self.active_client.normalized_load_url:
                eps = self.config_mgr.get("cached_endpoints", {}) or {}
                eps[prof.url.strip().rstrip("/")] = self.active_client.normalized_load_url
                self.config_mgr.set("cached_endpoints", eps)
            if len(res["channels"]) > 0:
                self.mac_db.save_found_mac(
                    prof.url,
                    {
                        "mac": prof.mac,
                        "model": prof.model,
                        "channels": len(res["channels"]),
                        "expire": res.get("expire", "Aktiv"),
                        "status": "Aktiv",
                        "token": self.active_client.token or "",
                    },
                )

        # Build Genre Map & Channel Objects
        self.genre_map = {"*": "Alle Kategorien"}
        for g in res.get("genres") or []:
            gid = str(g.get("id") or g.get("category_id") or "")
            gtitle = str(g.get("title") or g.get("category_name") or g.get("name") or gid)
            if gid:
                self.genre_map[gid] = gtitle

        fav_set = set(self.config_mgr.get_favorites(prof.name))
        vod_fav_set = set(self.config_mgr.get_vod_favorites(prof.name))
        recent_list = self.config_mgr.get_recently_played(prof.name)

        self.state.favorites = fav_set
        self.state.vod_favorites = vod_fav_set
        self.state.recently_played = recent_list

        channels: List[Channel] = []
        for idx, raw in enumerate(res.get("channels") or [], start=1):
            ch = Channel.from_raw(raw, self.genre_map)
            if not ch.number:
                ch.number = str(idx)
            if str(ch.id) in fav_set:
                ch.is_fav = True
            channels.append(ch)

        self.state.channels = channels
        self.state.channels_by_id = {str(c.id): c for c in channels}

        self.live_view.set_channels(channels, self.genre_map, fav_set, recent_list)
        self.live_view.delegate.set_profile_name(prof.name)
        self.vod_view.update_favorites(vod_fav_set)
        self.osd.populate_drawer_channels(channels)

        self.sidebar.set_connected_state(True, busy=False)
        self.top_bar.set_provider_status(True, res["summary"])
        event_bus.log_message.emit(
            f"[+] Verbunden: {res['summary']} ({len( self.genre_map) - 1} Kategorien)."
        )

        # Auto-collapse sidebar upon successful connection to maximize workspace
        if self.sidebar.isVisible():
            self.sidebar.setVisible(False)
            self.state.sidebar_visible = False

    def _on_connect_error(self, exc: Exception):
        self.state.is_connected = False
        self.sidebar.set_connected_state(False, busy=False)
        self.top_bar.set_provider_status(False, "Verbindung fehlgeschlagen")
        event_bus.log_message.emit(f"[-] Verbindungsfehler: {exc}")
        QMessageBox.warning(self, "Verbindungsfehler", str(exc))

    def disconnect_portal(self):
        self._selection_timer.stop()
        self._preview_timer.stop()
        self.thumb_grabber.cancel()
        self._on_stop_playback()
        self.live_view.clear_preview()
        self.resolved_stream_cache.clear()
        if self.active_client and hasattr(self.active_client, "close"):
            try:
                self.active_client.close()
            except Exception:
                pass
        self.active_client = None
        self.state.is_connected = False
        self.sidebar.set_connected_state(False, busy=False)
        self.top_bar.set_provider_status(False, "Nicht verbunden")
        event_bus.log_message.emit("[*] Verbindung zum Portal getrennt.")

    # ══════════════════════════════════════════════════════════════════════
    # 4. Channel Selection, EPG Fetching, Standbild Preview & Playback
    # ══════════════════════════════════════════════════════════════════════

    def _stream_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Icy-MetaData": "1",
            "Range": "bytes=0-",
            "Accept": "*/*",
            "Accept-Encoding": "identity",
        }
        client = self.active_client
        if client:
            cookies = {}
            if hasattr(client, "session"):
                try:
                    cookies.update(dict(client.session.cookies))
                except Exception:
                    pass
            if hasattr(client, "mac") and getattr(client, "mac", ""):
                cookies.setdefault("mac", str(client.mac))
                cookies.setdefault("stb_lang", "en")
                cookies.setdefault("timezone", "Europe/Berlin")
            if hasattr(client, "token") and getattr(client, "token", ""):
                cookies.setdefault("token", str(client.token))
                headers["Authorization"] = f"Bearer {client.token}"
            if cookies:
                headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
            if hasattr(client, "model") and getattr(client, "model", ""):
                m_str = str(client.model).replace(" ", "")
                headers["X-User-Agent"] = f"Model: {m_str}; Link: Ethernet,WiFi"
        return headers

    def _on_channel_selected(self, channel: Channel):
        if not channel:
            return

        self._pending_selected_channel = channel
        self._sel_seq += 1
        self.thumb_grabber.cancel()

        cid = str(channel.id)
        prof_name = self.state.current_profile_name
        cache_key = f"{prof_name}:{cid}"

        # Immediate cached Standbild lookup (purely local disk/memory, fast)
        if (
            not self.vlc_ctrl.is_playing
            and not self.vlc_ctrl._transitioning
            and self.vlc_ctrl.settings.preview_enabled
        ):
            age = thumb_age_s(cache_key)
            cached_jpeg = load_cached_thumb(cache_key)
            if cached_jpeg:
                age_txt = (
                    f"vor {int(age or 0)}s"
                    if (age is not None and age < 120)
                    else f"vor {int((age or 0) // 60)}m"
                )
                self.live_view.set_preview_jpeg(cached_jpeg, f"Vorschau: {channel.name} ({age_txt})")
                self.live_view.delegate.set_thumbnail(channel.id, cached_jpeg)
                self.live_view.list_view.viewport().update()

        # Debounce network EPG & live preview requests while scrolling (450ms)
        self._selection_timer.start(450)

    def _on_selection_settled(self):
        channel = self._pending_selected_channel
        if not channel:
            return

        seq = self._sel_seq
        cid = str(channel.id)
        prof_name = self.state.current_profile_name
        cache_key = f"{prof_name}:{cid}"

        # 1. Standbild Preview Overlay when player is completely idle
        if (
            not self.vlc_ctrl.is_playing
            and not self.vlc_ctrl._transitioning
            and self.vlc_ctrl.settings.preview_enabled
        ):
            max_age_s = max(60.0, float(self.vlc_ctrl.settings.preview_max_age_min) * 60.0)
            age = thumb_age_s(cache_key)
            if self.active_client and (age is None or age > max_age_s):
                self._pending_preview_channel = channel
                self._preview_timer.start(350)

        if not self.active_client:
            return

        # 2. Fetch short EPG in background (skips if user already moved on)
        client = self.active_client

        def _fetch_epg():
            if self._sel_seq != seq:
                return None
            if hasattr(client, "get_short_epg"):
                raw_epg = client.get_short_epg(cid, size=8)
                if self._sel_seq != seq:
                    return None
                return [EPGProgram.from_raw(e) for e in (raw_epg or []) if isinstance(e, dict)]
            return []

        worker_pool.run_async(
            _fetch_epg,
            on_success=lambda progs: (
                self._epg_loaded_sig.emit(cid, progs) if progs is not None else None
            ),
        )

    def _trigger_channel_preview(self):
        ch = self._pending_preview_channel
        if (
            not ch
            or self.vlc_ctrl.is_playing
            or self.vlc_ctrl._transitioning
            or not self.vlc_ctrl.settings.preview_enabled
            or not self.active_client
        ):
            return
        if not self.live_view._selected_channel or str(self.live_view._selected_channel.id) != str(ch.id):
            return

        cid = str(ch.id)
        ch_name = ch.name
        prof_name = self.state.current_profile_name
        cache_key = f"{prof_name}:{cid}"
        ua = getattr(self.active_client, "user_agent", "") or "VLC/3.0.20 LibVLC/3.0.20"
        headers: Dict[str, str] = {"User-Agent": ua}
        headers.update(self._stream_headers())
        if hasattr(self.active_client, "portal_url") and self.active_client.portal_url:
            headers["Referer"] = f"{self.active_client.portal_url}/"

        self.live_view.lbl_preview_badge.setText("📸 Lade Vorschau...")

        def _grab_preview_task() -> Optional[bytes]:
            if self.vlc_ctrl.is_playing or self.vlc_ctrl._transitioning:
                return None
            url = self._resolve_channel_url(ch)
            if not url or self.vlc_ctrl.is_playing or self.vlc_ctrl._transitioning:
                return None
            jpeg = self.thumb_grabber.grab(url, headers=headers, width=640, timeout=4.5)
            if jpeg:
                save_thumb(cache_key, jpeg)
            return jpeg

        def _on_grabbed(jpeg_bytes: Optional[bytes]):
            if jpeg_bytes:
                self._preview_ready_sig.emit(cid, jpeg_bytes, f"Live-Vorschau: {ch_name}")
            elif not self.vlc_ctrl.is_playing:
                self.live_view.lbl_preview_badge.setText("")

        worker_pool.run_async(_grab_preview_task, on_success=_on_grabbed)

    def _on_preview_ready_ui(self, ch_id: str, jpeg_bytes: bytes, badge_text: str):
        if self.vlc_ctrl.is_playing or self.vlc_ctrl._transitioning:
            return
        sel = self.live_view._selected_channel
        if sel and str(sel.id) == str(ch_id):
            self.live_view.set_preview_jpeg(jpeg_bytes, badge_text)
        self.live_view.delegate.set_thumbnail(ch_id, jpeg_bytes)
        self.live_view.list_view.viewport().update()

    def _on_epg_loaded_ui(self, ch_id: str, programs: list):
        self.live_view.update_epg(ch_id, programs)
        if self.state.playing_channel and str(self.state.playing_channel.id) == str(ch_id) and programs:
            self.osd.update_info(
                number=self.state.playing_channel.number,
                title=self.state.playing_channel.name,
                category=self.state.playing_channel.category,
                epg_now=programs[0].name,
                is_playing=self.vlc_ctrl.is_playing,
            )

    def _resolve_channel_url(self, channel: Channel) -> str:
        if not self.active_client:
            return channel.cmd
        if hasattr(self.active_client, "create_link"):
            if isinstance(self.active_client, XtreamClient):
                return self.active_client.create_link(str(channel.id), media_type="live")
            try:
                return self.active_client.create_link(channel.cmd, media_type="itv", ch_id=str(channel.id))
            except TypeError:
                return self.active_client.create_link(channel.cmd, media_type="itv")
        return channel.cmd

    def play_channel(self, channel: Channel):
        if not channel:
            return
        self._selection_timer.stop()
        self._preview_timer.stop()
        self._pending_preview_channel = None
        self._pending_selected_channel = None
        self.thumb_grabber.cancel()
        self._probe_cancel_ev.set()
        self.live_view.clear_preview()
        self._live_snapshot_timer.start(1800)

        self._play_seq += 1
        play_seq = self._play_seq
        self._sel_seq += 1
        epg_seq = self._sel_seq
        self._last_track_signature = None

        self.state.playing_channel = channel
        self.live_view.set_playing_channel(channel)
        self.live_view.set_video_status_text(f"⏳ Lade Stream: {channel.name} ...", "Verbinde...")

        # Record in Recently Played (persistent!)
        cid = str(channel.id)
        if cid in self.state.recently_played:
            self.state.recently_played.remove(cid)
        self.state.recently_played.insert(0, cid)
        self.state.recently_played = self.state.recently_played[:50]
        self.config_mgr.save_recently_played(self.state.current_profile_name, self.state.recently_played)
        self.live_view.update_recent(self.state.recently_played)

        client = self.active_client

        def _resolve():
            if self._play_seq != play_seq:
                return ""
            return self._resolve_channel_url(channel)

        def _on_resolved(url: str):
            if self._play_seq != play_seq:
                return
            self._start_stream_url(
                url, title=channel.name, channel=channel, is_vod=False, play_seq=play_seq
            )
            # Fetch EPG AFTER create_link completes so it never blocks StbClient._io_lock during zapping
            if client and hasattr(client, "get_short_epg"):
                def _fetch_epg_after():
                    if self._play_seq != play_seq:
                        return None
                    raw_epg = client.get_short_epg(cid, size=8)
                    return [EPGProgram.from_raw(e) for e in (raw_epg or []) if isinstance(e, dict)]

                worker_pool.run_async(
                    _fetch_epg_after,
                    on_success=lambda progs: (
                        self._epg_loaded_sig.emit(cid, progs)
                        if (progs is not None and self._sel_seq == epg_seq)
                        else None
                    ),
                )

        worker_pool.run_async(
            _resolve,
            on_success=_on_resolved,
            on_error=lambda exc: (
                self._on_play_error(channel.name, exc) if self._play_seq == play_seq else None
            ),
        )

    def _start_stream_url(
        self,
        stream_url: str,
        title: str,
        channel: Optional[Channel] = None,
        is_vod: bool = False,
        play_seq: Optional[int] = None,
    ):
        if play_seq is not None and play_seq != self._play_seq:
            return
        if not stream_url:
            self.live_view.set_video_status_text(f"❌ Keine gültige Stream-URL für '{title}'", "Fehler")
            return

        self.live_view.clear_preview()
        ua = getattr(self.active_client, "user_agent", "") or ""
        ref = (
            f"{getattr(self.active_client, 'portal_url', '')}/"
            if hasattr(self.active_client, "portal_url") and getattr(self.active_client, "portal_url", "")
            else ""
        )
        extra_headers = self._stream_headers()

        engine = self.sidebar.combo_player.currentText()
        if engine != "Integrierter Player":
            self._launch_external_player(engine, stream_url, title, ua, ref)
            return

        hwnd = self.live_view.get_video_hwnd()
        if not self.vlc_ctrl.initialize(hwnd):
            event_bus.log_message.emit(
                "[!] LibVLC nicht initialisiert – versuche externen Player als Fallback."
            )
            self._launch_external_player("Externer VLC", stream_url, title, ua, ref)
            return

        prof = self.config_mgr.get_profile(self.state.current_profile_name)
        if prof and getattr(prof, "proxy", ""):
            self.vlc_ctrl.settings.proxy = str(prof.proxy or "").strip()

        ok = self.vlc_ctrl.play_url(
            stream_url,
            title=title,
            user_agent=ua,
            referrer=ref,
            extra_headers=extra_headers,
            direct=is_vod,
        )
        if ok:
            if not is_vod and self.vlc_ctrl.settings.mode == "proxy":
                self.live_view.set_video_status_text(
                    f"⏳ Verbinde & puffere: {title} ...", "Puffere..."
                )
            else:
                self.live_view.set_video_status_text(
                    f"🟢 Wiedergabe: {title}", "LIVE" if not is_vod else "VOD"
                )
            event_bus.log_message.emit(f"[▶] Wiedergabe gestartet: {title} -> {stream_url}")
            if channel:
                self.osd.update_info(
                    number=channel.number,
                    title=channel.name,
                    category=channel.category,
                    is_playing=True,
                )
        else:
            self.live_view.set_video_status_text(f"❌ Wiedergabefehler bei '{title}'", "Fehler")

    def _launch_external_player(self, engine_label: str, url: str, title: str, ua: str, ref: str):
        if "MPV" in engine_label:
            p_type, p_path = "mpv", str(self.config_mgr.get("mpv_path") or "")
        elif "FFplay" in engine_label:
            p_type, p_path = "ffplay", str(self.config_mgr.get("ffplay_path") or "")
        else:
            p_type, p_path = "vlc", str(self.config_mgr.get("vlc_path") or "")

        if self.ext_player.play(p_type, p_path, url, title=title, user_agent=ua, referrer=ref):
            self.live_view.set_video_status_text(f"↗ Externer Player ({p_type.upper()}): {title}", "Extern")
            event_bus.log_message.emit(f"[↗] Externer Player ({p_type.upper()}) gestartet für: {title}")
        else:
            QMessageBox.warning(
                self,
                "Externer Player nicht gefunden",
                f"Der Player '{engine_label}' konnte unter '{p_path or 'PATH'}' nicht gestartet werden.",
            )

    def _on_play_error(self, title: str, exc: Exception):
        self.live_view.set_video_status_text(f"❌ Stream-Fehler ({title}): {exc}", "Fehler")
        event_bus.log_message.emit(f"[-] Fehler beim Auflösen von '{title}': {exc}")

    def _on_play_pause(self):
        playing = self.vlc_ctrl.toggle_play_pause()
        if self.state.playing_channel:
            self.osd.update_info(
                number=self.state.playing_channel.number,
                title=self.state.playing_channel.name,
                category=self.state.playing_channel.category,
                is_playing=playing,
            )

    def _on_stop_playback(self):
        self._play_seq += 1
        self._last_track_signature = None
        self.vlc_ctrl.stop()
        self.ext_player.stop()
        self.live_view.video_surface.clear_surface()
        self.live_view.set_video_status_text("⏹ Wiedergabe gestoppt", "")

    def _on_prev_channel(self):
        ch = self.live_view.select_adjacent_channel(-1)
        if ch:
            self.play_channel(ch)

    def _on_next_channel(self):
        ch = self.live_view.select_adjacent_channel(1)
        if ch:
            self.play_channel(ch)

    def _on_osd_channel_selected(self, ch_id: str):
        ch = self.state.channels_by_id.get(str(ch_id))
        if ch:
            self.play_channel(ch)

    def _on_mute_toggled(self):
        muted = self.vlc_ctrl.toggle_mute()
        self.live_view.btn_mute.setText("🔇" if muted else "🔊")
        self.osd.update_volume_ui(self.vlc_ctrl.volume, muted)

    def _on_volume_changed(self, vol: int):
        self.vlc_ctrl.set_volume(vol)
        self.config_mgr.set("player_volume", vol)
        self.osd.update_volume_ui(vol, self.vlc_ctrl.is_muted)

    def _on_vlc_buffering(self, pct: float):
        title = self.vlc_ctrl.current_title or (
            self.state.playing_channel.name if self.state.playing_channel else "Stream"
        )
        if pct < 100.0:
            self.live_view.set_video_status_text(
                f"⏳ Pufferung ({pct:.0f}%): {title}", f"Puffer {pct:.0f}%"
            )
        else:
            self.live_view.set_video_status_text(
                f"🟢 Wiedergabe: {title}", "LIVE"
            )

    def _play_current_in_external(self):
        url = self.vlc_ctrl.current_url
        title = self.vlc_ctrl.current_title or "Stream"
        ua = getattr(self.active_client, "user_agent", "") or ""
        ref = f"{getattr(self.active_client, 'portal_url', '')}/" if hasattr(self.active_client, "portal_url") else ""

        if url:
            self.vlc_ctrl.stop()
            self._launch_external_player("Externer VLC", url, title, ua, ref)
            return

        target_ch = self.state.playing_channel or self.live_view._selected_channel
        if not target_ch:
            return
        ch_title = target_ch.name

        def _resolve():
            return self._resolve_channel_url(target_ch)

        def _done(resolved_url: str):
            if resolved_url:
                self.vlc_ctrl.stop()
                self._launch_external_player("Externer VLC", resolved_url, ch_title, ua, ref)

        worker_pool.run_async(_resolve, on_success=_done)

    def take_video_snapshot(self):
        snap_dir = os.path.join(APP_DIR, "recordings")
        os.makedirs(snap_dir, exist_ok=True)
        path = os.path.join(snap_dir, f"snapshot_{time.strftime('%Y%m%d_%H%M%S')}.png")
        if self.vlc_ctrl.snapshot(path):
            event_bus.log_message.emit(f"[📸] Screenshot gespeichert: {path}")
            self.live_view.set_video_status_text(f"📸 Screenshot gespeichert: {os.path.basename(path)}", "Snapshot")

    # ══════════════════════════════════════════════════════════════════════
    # 5. Favorites, Probe, Copy URL, Record & M3U8 Export
    # ══════════════════════════════════════════════════════════════════════

    def toggle_channel_favorite(self, ch_id: str):
        cid = str(ch_id)
        if cid in self.state.favorites:
            self.state.favorites.remove(cid)
        else:
            self.state.favorites.add(cid)

        ch = self.state.channels_by_id.get(cid)
        if ch:
            ch.is_fav = cid in self.state.favorites

        self.config_mgr.save_favorites(self.state.current_profile_name, list(self.state.favorites))
        self.live_view.update_favorites(self.state.favorites)

    def _fav_active_channel(self):
        ch = self.live_view._selected_channel or self.state.playing_channel
        if ch:
            self.toggle_channel_favorite(str(ch.id))

    def probe_channel_stream(
        self,
        channel: Channel,
        resolved_url: Optional[str] = None,
        quiet: bool = False,
    ):
        # Never open parallel probe connections when a stream is actively playing in quiet mode
        if quiet and self.vlc_ctrl.is_playing:
            return
        self._probe_cancel_ev.set()
        cancel_ev = threading.Event()
        self._probe_cancel_ev = cancel_ev
        cid = str(channel.id)
        ua = getattr(self.active_client, "user_agent", "") or ""
        cookies = (
            dict(self.active_client.session.cookies)
            if hasattr(self.active_client, "session")
            else None
        )

        proxy_url = getattr(self.active_client, "proxy", "") or ""
        if not proxy_url and self.state.current_profile_name:
            cur_p = self.config_mgr.get_profile(self.state.current_profile_name)
            if cur_p and getattr(cur_p, "proxy", ""):
                proxy_url = cur_p.proxy

        if not quiet:
            event_bus.log_message.emit(f"[🔍] Starte Stream-Probe für '{channel.name}' ...")

        def _task():
            url = resolved_url or self._resolve_channel_url(channel)
            return probe_stream(
                url, user_agent=ua, cookies=cookies, cancel=cancel_ev, proxy=proxy_url
            )

        worker_pool.run_async(
            _task,
            on_success=lambda res: self._probe_done_sig.emit(cid, res),
        )

    def _on_probe_done_ui(self, ch_id: str, res: StreamProbeResult):
        self.vlc_ctrl.set_probe_result(res)
        is_blocked = not res.is_alive and res.status_code in (456, 407, 459, 511)
        self.live_view.channel_model.update_channel_health(
            ch_id, is_alive=(res.is_alive or is_blocked), latency_ms=(res.latency_ms if res.is_alive else 0)
        )
        if res.width > 0 and res.height > 0:
            q = quality_from_dimensions(res.width, res.height)
            if q:
                self.live_view.channel_model.update_channel_quality(ch_id, q)
        if self.live_view._selected_channel and str(self.live_view._selected_channel.id) == str(ch_id):
            self.live_view.update_probe_telemetry(res)
        if not res.is_alive and res.error_msg:
            event_bus.log_message.emit(f"[⚠️] Stream-Probe ({ch_id}): {res.error_msg}")

    def copy_channel_url(self, channel: Channel):
        def _task():
            return self._resolve_channel_url(channel)

        def _done(url: str):
            if url:
                QApplication.clipboard().setText(url)
                event_bus.log_message.emit(f"[📋] Stream-URL kopiert ({channel.name}): {url}")

        worker_pool.run_async(_task, on_success=_done)

    def record_channel(self, channel: Channel):
        ua = getattr(self.active_client, "user_agent", "") or "VLC/3.0"

        def _task():
            return self._resolve_channel_url(channel)

        def _start_rec(url: str):
            if not url:
                return
            self.recorder.start(
                kind="rec",
                name=channel.name,
                url=url,
                headers={"User-Agent": ua},
                refresh=lambda: self._resolve_channel_url(channel),
            )
            self._on_recorder_changed()

        worker_pool.run_async(_task, on_success=_start_rec)

    def _record_active_channel(self):
        ch = self.state.playing_channel or self.live_view._selected_channel
        if ch:
            self.record_channel(ch)

    def _stop_active_recordings(self):
        for job in self.recorder.active_jobs(kind="rec"):
            self.recorder.stop(job)
        self._on_recorder_changed()

    def _on_recorder_changed(self):
        active = self.recorder.active_jobs()
        rec_jobs = self.recorder.active_jobs(kind="rec")
        self.top_bar.update_jobs_badge(len(active), len(self.recorder.jobs))
        if rec_jobs:
            j = rec_jobs[0]
            self.top_bar.update_rec_indicator(True, f"🔴 REC {j.elapsed_str}")
        else:
            self.top_bar.update_rec_indicator(False)

    def export_channels_m3u(self, channels: List[Channel]):
        if not channels:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Senderliste als .M3U8 exportieren",
            f"playlist_{self.state.current_profile_name}.m3u8",
            "M3U8 Playlist (*.m3u8 *.m3u)",
        )
        if not path:
            return
        ua = getattr(self.active_client, "user_agent", "") or ""
        content = build_m3u_playlist(channels, user_agent=ua)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            event_bus.log_message.emit(f"[💾] {len(channels)} Sender erfolgreich nach '{path}' exportiert.")
        except Exception as e:
            QMessageBox.warning(self, "Export-Fehler", str(e))

    # ══════════════════════════════════════════════════════════════════════
    # 6. Parallel 8-Thread Category Validator (QoL Upgrade)
    # ══════════════════════════════════════════════════════════════════════

    def start_category_validation(self, channels: List[Channel]):
        if not channels:
            return
        # Stop current stream to respect single-connection limits and minimize latency
        if self.vlc_ctrl.is_playing or getattr(self.vlc_ctrl, "_transitioning", False):
            self._on_stop_playback()

        self._val_stop_ev.set()
        self._val_stop_ev = threading.Event()
        total = len(channels)
        self.live_view.set_validation_running(True, 0, total)
        ua = getattr(self.active_client, "user_agent", "") or ""
        cookies = (
            dict(self.active_client.session.cookies)
            if hasattr(self.active_client, "session")
            else None
        )
        is_stalker = isinstance(self.active_client, StbClient)
        workers = int(self.config_mgr.get("validation_workers", 8) or 8)
        prof_name = self.state.current_profile_name
        stream_hdrs = self._stream_headers()
        portal_ref = (
            f"{self.active_client.portal_url}/"
            if (hasattr(self.active_client, "portal_url") and self.active_client.portal_url)
            else ""
        )
        proxy_url = getattr(self.active_client, "proxy", "") or ""
        if not proxy_url and self.state.current_profile_name:
            cur_p = self.config_mgr.get_profile(self.state.current_profile_name)
            if cur_p and getattr(cur_p, "proxy", ""):
                proxy_url = cur_p.proxy

        event_bus.log_message.emit(
            f"[🩺] Starte parallele Kategorie-Validierung & Vorschaubild-Abruf ({total} Sender, {workers} Threads) ..."
        )

        def _Coordinator():
            done = 0
            alive_cnt = 0
            dead_cnt = 0
            alive_ids = set()
            lock = threading.Lock()
            # Throttle concurrent Stalker create_link calls to avoid HTTP 429 bans
            link_sem = threading.Semaphore(2 if is_stalker else workers)

            def _resolve_with_retry(ch: Channel) -> str:
                with link_sem:
                    try:
                        return self._resolve_channel_url(ch)
                    except RateLimitError as rle:
                        wait_s = min(8.0, float(rle.retry_after or 2.5))
                        self._val_stop_ev.wait(wait_s)
                        if self._val_stop_ev.is_set():
                            return ""
                        return self._resolve_channel_url(ch)
                    except Exception:
                        return ""

            def _check_one(ch: Channel):
                nonlocal done, alive_cnt, dead_cnt
                if self._val_stop_ev.is_set():
                    return
                is_ok = False
                is_blocked = False
                lat = -1
                q = ""
                thumb_bytes: Optional[bytes] = None
                cid = str(ch.id)
                cache_key = f"{prof_name}:{cid}"

                # 1. Sofort Disk-Cache prüfen
                cached_thumb = load_cached_thumb(cache_key) or (load_cached_thumb(cid) if prof_name else None)
                if cached_thumb:
                    thumb_bytes = cached_thumb

                need_extract = (thumb_bytes is None)
                try:
                    url = _resolve_with_retry(ch)
                    if url and not self._val_stop_ev.is_set():
                        res = probe_stream(
                            url,
                            user_agent=ua,
                            cookies=cookies,
                            timeout=3.0,
                            sample_duration=0.5,
                            cancel=self._val_stop_ev,
                            skip_ffprobe=False,
                            proxy=proxy_url,
                            extract_thumbnail=need_extract,
                        )
                        is_blocked = not res.is_alive and res.status_code in (456, 407, 459, 511)
                        is_ok = bool(res.is_alive and res.latency_ms <= 3000)
                        lat = res.latency_ms if is_ok else -1
                        if is_ok and res.width > 0 and res.height > 0:
                            q = quality_from_dimensions(res.width, res.height)
                        if res.thumb_bytes and not thumb_bytes:
                            thumb_bytes = res.thumb_bytes
                            save_thumb(cache_key, thumb_bytes)
                except Exception:
                    is_ok = False
                    is_blocked = False
                    lat = -1
                    q = ""

                with lock:
                    done += 1
                    if is_ok or is_blocked:
                        alive_cnt += 1
                        alive_ids.add(cid)
                    else:
                        dead_cnt += 1
                    cur_done = done

                is_alive_flag = is_ok or is_blocked
                self._val_progress_sig.emit(str(ch.id), is_alive_flag, lat, q, cur_done, total, thumb_bytes)

            with ThreadPoolExecutor(max_workers=workers) as pool:
                list(pool.map(_check_one, channels))

            # Phase 2: Automatisch Vorschaubilder für alle Online-Sender der Gruppe holen, die noch keines haben
            if not self._val_stop_ev.is_set():
                need_thumbs = [
                    ch for ch in channels
                    if str(ch.id) in alive_ids and not (load_cached_thumb(f"{prof_name}:{ch.id}") or (prof_name and load_cached_thumb(str(ch.id))))
                ]
                if need_thumbs:
                    t_total = len(need_thumbs)
                    t_done = 0
                    event_bus.log_message.emit(
                        f"[📸] Ziehe automatisch Vorschaubilder für {t_total} Online-Sender der Gruppe..."
                    )
                    def _grab_one_val(ch: Channel):
                        nonlocal t_done
                        if self._val_stop_ev.is_set():
                            return
                        cid = str(ch.id)
                        k = f"{prof_name}:{cid}" if prof_name else cid
                        t_bytes = None
                        try:
                            u = _resolve_with_retry(ch)
                            if u and not self._val_stop_ev.is_set():
                                hdrs = {"User-Agent": ua}
                                hdrs.update(stream_hdrs)
                                if portal_ref:
                                    hdrs["Referer"] = portal_ref
                                t_bytes = grab_thumbnail(
                                    u,
                                    headers=hdrs,
                                    width=320,
                                    timeout=6.0,
                                    cancel_ev=self._val_stop_ev,
                                )
                                if t_bytes:
                                    save_thumb(k, t_bytes)
                        except Exception:
                            pass
                        with lock:
                            t_done += 1
                            cur_tdone = t_done
                        self._val_thumb_progress_sig.emit(cid, t_bytes, cur_tdone, t_total)

                    with ThreadPoolExecutor(max_workers=3) as thumb_pool:
                        list(thumb_pool.map(_grab_one_val, need_thumbs))

            self._val_finished_sig.emit(alive_cnt, dead_cnt)

        threading.Thread(target=_Coordinator, daemon=True).start()

    def start_group_thumbnail_fetch(self, channels: List[Channel]):
        if not channels:
            return

        self._val_stop_ev.set()
        self._val_stop_ev = threading.Event()

        prof_name = self.state.current_profile_name
        need_thumbs = [
            ch for ch in channels
            if not ch.is_dead and not (load_cached_thumb(f"{prof_name}:{ch.id}") or (prof_name and load_cached_thumb(str(ch.id))))
        ]
        if not need_thumbs:
            event_bus.log_message.emit("[📸] Alle sichtbaren Sender besitzen bereits ein gespeichertes Vorschaubild.")
            return

        total = len(need_thumbs)
        self.live_view.set_thumbnail_progress(True, 0, total)
        ua = getattr(self.active_client, "user_agent", "") or ""
        stream_hdrs = self._stream_headers()
        portal_ref = (
            f"{self.active_client.portal_url}/"
            if (hasattr(self.active_client, "portal_url") and self.active_client.portal_url)
            else ""
        )
        is_stalker = isinstance(self.active_client, StbClient)
        link_sem = threading.Semaphore(2 if is_stalker else 4)

        event_bus.log_message.emit(f"[📸] Starte Vorschaubild-Abruf für {total} Sender...")

        def _Coordinator():
            done = 0
            lock = threading.Lock()

            def _resolve_with_retry(ch: Channel) -> str:
                with link_sem:
                    try:
                        return self._resolve_channel_url(ch)
                    except RateLimitError as rle:
                        wait_s = min(8.0, float(rle.retry_after or 2.5))
                        self._val_stop_ev.wait(wait_s)
                        if self._val_stop_ev.is_set():
                            return ""
                        return self._resolve_channel_url(ch)
                    except Exception:
                        return ""

            def _grab_one(ch: Channel):
                nonlocal done
                if self._val_stop_ev.is_set():
                    return
                cid = str(ch.id)
                k = f"{prof_name}:{cid}" if prof_name else cid
                t_bytes = None
                try:
                    u = _resolve_with_retry(ch)
                    if u and not self._val_stop_ev.is_set():
                        hdrs = {"User-Agent": ua}
                        hdrs.update(stream_hdrs)
                        if portal_ref:
                            hdrs["Referer"] = portal_ref
                        t_bytes = grab_thumbnail(
                            u,
                            headers=hdrs,
                            width=320,
                            timeout=6.0,
                            cancel_ev=self._val_stop_ev,
                        )
                        if t_bytes:
                            save_thumb(k, t_bytes)
                except Exception:
                    pass
                with lock:
                    done += 1
                    cur_done = done
                self._val_thumb_progress_sig.emit(cid, t_bytes, cur_done, total)

            with ThreadPoolExecutor(max_workers=3) as pool:
                list(pool.map(_grab_one, need_thumbs))

            self._val_thumb_finished_sig.emit(total)

        threading.Thread(target=_Coordinator, daemon=True).start()

    def stop_category_validation(self):
        self._val_stop_ev.set()

    def _on_val_progress_ui(
        self,
        ch_id: str,
        is_alive: bool,
        latency_ms: int,
        quality_tag: str,
        done: int,
        total: int,
        thumb_bytes: Optional[bytes] = None,
    ):
        self.live_view.channel_model.update_channel_health(ch_id, is_alive, latency_ms)
        if quality_tag:
            self.live_view.channel_model.update_channel_quality(ch_id, quality_tag)
        if thumb_bytes:
            self.live_view.delegate.set_thumbnail(ch_id, thumb_bytes)
            sel = self.live_view._selected_channel
            if sel and str(sel.id) == str(ch_id) and not self.vlc_ctrl.is_playing:
                self.live_view.set_preview_jpeg(thumb_bytes, f"Live-Vorschau: {sel.name}")
            self.live_view.list_view.viewport().update()
        self.live_view.set_validation_running(True, done, total)

    def _on_val_finished_ui(self, alive_cnt: int, dead_cnt: int):
        self.live_view.set_validation_running(False)
        self.live_view.proxy_model.invalidate()
        self.live_view._update_count_label()
        event_bus.log_message.emit(
            f"[+] Kategorie-Validierung abgeschlossen: {alive_cnt} Online, {dead_cnt} Offline."
        )

    def _on_val_thumb_progress_ui(
        self,
        ch_id: str,
        thumb_bytes: Optional[bytes],
        done: int,
        total: int,
    ):
        if thumb_bytes:
            self.live_view.delegate.set_thumbnail(ch_id, thumb_bytes)
            sel = self.live_view._selected_channel
            if sel and str(sel.id) == str(ch_id) and not self.vlc_ctrl.is_playing:
                self.live_view.set_preview_jpeg(thumb_bytes, f"Live-Vorschau: {sel.name}")
            self.live_view.list_view.viewport().update()
        self.live_view.set_thumbnail_progress(True, done, total)

    def _on_val_thumb_finished_ui(self, count: int):
        self.live_view.set_thumbnail_progress(False)
        self.live_view.list_view.viewport().update()
        event_bus.log_message.emit(
            f"[+] 📸 Vorschaubilder-Abruf abgeschlossen ({count} Sender verarbeitet)."
        )

    def _on_vlc_state_changed(self, state: str):
        if state == "playing":
            self._live_snapshot_timer.start(1800)
        else:
            self._live_snapshot_timer.stop()

    def _snapshot_playing_channel(self):
        ch = self.state.playing_channel
        if not ch or not self.vlc_ctrl.is_playing:
            return
        cid = str(ch.id)
        prof_name = self.state.current_profile_name
        cache_key = f"{prof_name}:{cid}" if prof_name else cid
        tmp_snap = os.path.join(THUMB_DIR, f"live_{cid}.jpg")
        try:
            if self.vlc_ctrl.snapshot(tmp_snap):
                time.sleep(0.06)
                if os.path.exists(tmp_snap):
                    with open(tmp_snap, "rb") as f:
                        snap_data = f.read()
                    from core.preview_grabber import is_blank_or_black_jpeg
                    if not is_blank_or_black_jpeg(snap_data):
                        save_thumb(cache_key, snap_data)
                        self.live_view.delegate.set_thumbnail(cid, snap_data)
                        self.live_view.list_view.viewport().update()
                    try:
                        os.remove(tmp_snap)
                    except OSError:
                        pass
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════
    # 7. VOD & Series Loading, Playback & Downloads
    # ══════════════════════════════════════════════════════════════════════

    def _on_vod_mode_changed(self, mode: str):
        if self.state.is_connected:
            self._load_vod_or_series_categories(mode)

    def _load_vod_or_series_categories(self, mode: str):
        if not self.active_client:
            return
        self.vod_view.set_loading("Lade Kategorien...")
        client = self.active_client

        def _task():
            if mode == "series" and hasattr(client, "get_series_categories"):
                return client.get_series_categories()
            if hasattr(client, "get_vod_categories"):
                return client.get_vod_categories()
            return []

        def _done(cats: list):
            self.vod_view.set_categories(cats or [])
            self._on_vod_category_selected(mode, "*")

        worker_pool.run_async(_task, on_success=_done)

    def _on_vod_category_selected(self, mode: str, category_id: str):
        if not self.active_client:
            return
        self.vod_view.set_loading("Lade Einträge...")
        client = self.active_client

        def _task():
            # Xtream returns all items in page 1; Stalker paginates 14 items per page
            if isinstance(client, StbClient):
                combined: List[Dict[str, Any]] = []
                seen_ids = set()
                for page in range(1, 6):
                    if mode == "series":
                        batch = client.get_series(category_id=category_id, page=page)
                    else:
                        batch = client.get_vod_movies(category_id=category_id, page=page)
                    if not batch:
                        break
                    new_in_page = 0
                    for item in batch:
                        if not isinstance(item, dict):
                            continue
                        iid = str(item.get("id") or item.get("stream_id") or item.get("series_id") or "")
                        if iid and iid in seen_ids:
                            continue
                        if iid:
                            seen_ids.add(iid)
                        combined.append(item)
                        new_in_page += 1
                    if len(batch) < 14 or new_in_page == 0:
                        break
                return combined

            if mode == "series" and hasattr(client, "get_series"):
                return client.get_series(category_id=category_id, page=1)
            if hasattr(client, "get_vod_movies"):
                return client.get_vod_movies(category_id=category_id, page=1)
            return []

        worker_pool.run_async(
            _task,
            on_success=lambda items: self.vod_view.set_items(items or [], self.state.vod_favorites),
        )

    def _on_vod_portal_search(self, mode: str, query: str):
        q = (query or "").strip()
        if not q:
            return
        if not self.active_client:
            self.vod_view.entry_search.setText(q)
            self.vod_view._on_local_search_changed(q)
            return

        self.vod_view.set_loading(f"🌐 Suche im Portal nach '{q}' ...")
        client = self.active_client

        def _task():
            if isinstance(client, StbClient):
                mtype = "series" if mode == "series" else "vod"
                results: List[Dict[str, Any]] = []
                seen = set()
                for page in range(1, 4):
                    batch = client.get_ordered_list(
                        media_type=mtype, category_id="*", page=page, search=q
                    )
                    if not batch:
                        break
                    for item in batch:
                        if isinstance(item, dict):
                            iid = str(item.get("id") or "")
                            if iid not in seen:
                                seen.add(iid)
                                results.append(item)
                    if len(batch) < 14:
                        break
                return results

            # Xtream Codes or M3U: fetch full catalog and filter server-side results by query
            ql = q.lower()
            if mode == "series" and hasattr(client, "get_series"):
                all_items = client.get_series(category_id="*", page=1) or []
            elif hasattr(client, "get_vod_movies"):
                all_items = client.get_vod_movies(category_id="*", page=1) or []
            else:
                all_items = []
            return [
                it
                for it in all_items
                if isinstance(it, dict)
                and ql in str(it.get("name") or it.get("title") or "").lower()
            ]

        def _done(items: list):
            self.vod_view.entry_search.blockSignals(True)
            self.vod_view.entry_search.clear()
            self.vod_view.entry_search.blockSignals(False)
            self.vod_view.set_items(items or [], self.state.vod_favorites)
            event_bus.log_message.emit(f"[🌐] Portal-Suche nach '{q}': {len(items or [])} Treffer.")

        worker_pool.run_async(_task, on_success=_done)

    def _resolve_vod_url(self, item: Dict[str, Any], media_type: str = "vod") -> str:
        cmd = str(item.get("cmd") or item.get("url") or "")
        if cmd.startswith(("http://", "https://")) and "localhost" not in cmd:
            return cmd
        if not self.active_client:
            return cmd
        if isinstance(self.active_client, XtreamClient):
            sid = str(item.get("stream_id") or item.get("id") or "")
            ext = str(item.get("container_extension") or "mp4")
            return self.active_client.create_link(sid, media_type=media_type, extension=ext)
        if hasattr(self.active_client, "create_link"):
            return self.active_client.create_link(cmd or str(item.get("id") or ""), media_type="vod")
        return cmd

    def play_vod_item(self, item: Dict[str, Any]):
        title = str(item.get("name") or item.get("title") or "Film")
        self.top_bar.set_active_view("live")

        def _task():
            return self._resolve_vod_url(item, media_type="vod")

        worker_pool.run_async(
            _task,
            on_success=lambda url: self._start_stream_url(url, title=title, is_vod=True),
            on_error=lambda exc: self._on_play_error(title, exc),
        )

    def download_vod_item(self, item: Dict[str, Any]):
        title = str(item.get("name") or item.get("title") or "VOD_Download")
        ua = getattr(self.active_client, "user_agent", "") or "VLC/3.0"

        def _task():
            return self._resolve_vod_url(item, media_type="vod")

        def _start_dl(url: str):
            if not url:
                return
            self.recorder.start(kind="dl", name=title, url=url, headers={"User-Agent": ua})
            self._on_recorder_changed()
            event_bus.log_message.emit(f"[⬇] VOD-Download gestartet: {title}")

        worker_pool.run_async(_task, on_success=_start_dl)

    def copy_vod_url(self, item: Dict[str, Any]):
        worker_pool.run_async(
            lambda: self._resolve_vod_url(item, media_type="vod"),
            on_success=lambda url: QApplication.clipboard().setText(url or ""),
        )

    def toggle_vod_favorite(self, item_id: str, _item: Dict[str, Any]):
        iid = str(item_id)
        if iid in self.state.vod_favorites:
            self.state.vod_favorites.remove(iid)
        else:
            self.state.vod_favorites.add(iid)
        self.config_mgr.save_vod_favorites(
            self.state.current_profile_name, list(self.state.vod_favorites)
        )
        self.vod_view.update_favorites(self.state.vod_favorites)

    def open_series_dialog(self, series_item: Dict[str, Any]):
        if not self.active_client or not hasattr(self.active_client, "get_series_info"):
            return
        sid = str(series_item.get("series_id") or series_item.get("id") or "")
        title = str(series_item.get("name") or series_item.get("title") or "Serie")
        client = self.active_client

        def _task():
            raw = client.get_series_info(sid)
            if isinstance(raw, dict):
                return raw
            if isinstance(raw, list):
                out: Dict[str, List[Dict[str, Any]]] = {}
                for s in raw:
                    if isinstance(s, dict):
                        s_num = str(s.get("season_number") or "1")
                        out[s_num] = s.get("episodes") or []
                return out
            return {}

        def _show(seasons_dict: Dict[str, List[Dict[str, Any]]]):
            dlg = SeriesBrowserDialog(title, seasons_dict, parent=self)
            dlg.episode_play_requested.connect(self.play_vod_item)
            dlg.episode_download_requested.connect(self.download_vod_item)
            dlg.episode_copy_requested.connect(self.copy_vod_url)
            dlg.exec()

        worker_pool.run_async(_task, on_success=_show)

    # ══════════════════════════════════════════════════════════════════════
    # 8. Multi-MAC Batch Scanner Engine
    # ══════════════════════════════════════════════════════════════════════

    def start_mac_scan(
        self,
        portal_url: str,
        mac_list: List[str],
        model: str,
        threads: int,
        delay_s: float,
    ):
        self._scan_stop_ev.clear()
        self._scan_pause_ev.set()
        event_bus.scan_state_changed.emit(True)

        # Normalisiere und dedupliziere Ausgangsliste unter Beibehaltung der Reihenfolge
        unique_macs: List[str] = []
        seen_set = set()
        for m in mac_list:
            mu = StbClient.format_mac(m).upper()
            if mu and mu not in seen_set:
                seen_set.add(mu)
                unique_macs.append(mu)

        total = len(unique_macs)
        timeout_s = self.config_mgr.get_timeout_seconds()
        cached_eps = self.config_mgr.get("cached_endpoints", {}) or {}
        norm_portal = portal_url.strip().rstrip("/")
        shared_ep = [cached_eps.get(norm_portal)]

        self._current_scan_threads = max(1, threads)
        self._current_scan_delay = max(0.0, delay_s)
        throttle = ScanThrottleController(
            base_delay=self._current_scan_delay,
            on_throttle_notify=lambda msg: event_bus.log_message.emit(msg),
        )
        self._scan_throttle = throttle

        event_bus.log_message.emit(
            f"[🎯] Starte Multi-MAC Scan auf {portal_url} ({total} MACs, {threads} Threads, Modell {model}) ..."
        )

        work_q: queue.Queue[str] = queue.Queue()
        for m in unique_macs:
            work_q.put(m)

        # ⚡ PREFLIGHT ENDPOINT ERMITTLUNG:
        # Falls der Stalker load_url Endpoint noch unbekannt ist, ermitteln wir ihn einmalig vorab.
        # Dadurch entfallen für alle weiteren 10.000 MACs zeitraubende Fallback-Probes auf 6 verschiedene URLs!
        if not shared_ep[0] and unique_macs:
            try:
                probe_cl = StbClient(portal_url=portal_url, mac=unique_macs[0], model=model, timeout=timeout_s)
                for ep in probe_cl._get_candidate_endpoints()[:5]:
                    try:
                        probe_cl._execute_request(
                            ep,
                            {"type": "stb", "action": "handshake", "token": "", "JsHttpRequest": "1-xml"},
                            timeout_override=(2.0, 2.5),
                        )
                        shared_ep[0] = ep
                        break
                    except PermissionError:
                        # Server hat geantwortet und die MAC abgewiesen -> exakter Stalker Endpoint gefunden!
                        shared_ep[0] = ep
                        break
                    except Exception:
                        continue
                if shared_ep[0]:
                    cached_eps[norm_portal] = shared_ep[0]
                    self.config_mgr.set("cached_endpoints", cached_eps)
                    event_bus.log_message.emit(f"[⚡] Stalker-Endpoint erkannt: {shared_ep[0]} (Turbo-Modus aktiv)")
            except Exception:
                pass

        def _coordinator():
            done = 0
            in_flight = 0
            active_workers = 0
            conclusive_macs = set()
            retry_counts = collections.defaultdict(int)
            lock = threading.Lock()

            def _worker():
                nonlocal done, in_flight, active_workers
                with lock:
                    active_workers += 1

                # ⚡ KEEPALIVE HTTP SESSION PRO WORKER:
                # Verhindert ständiges Öffnen/Schließen von TCP/TLS Sockets pro MAC.
                # Spart 100-300ms Overhead pro einzelner Abfrage!
                worker_session = requests.Session()
                worker_adapter = HTTPAdapter(
                    pool_connections=4,
                    pool_maxsize=4,
                    max_retries=0,
                )
                worker_session.mount("http://", worker_adapter)
                worker_session.mount("https://", worker_adapter)
                ua_str = STB_PRESETS.get(model, STB_PRESETS.get("MAG 250", {})).get(
                    "user_agent", "Mozilla/5.0 (QtEmbedded; U; Linux; C)"
                )
                worker_session.headers.update({
                    "User-Agent": ua_str,
                    "Accept": "*/*",
                    "Connection": "keep-alive",
                })

                try:
                    while not self._scan_stop_ev.is_set():
                        # 1. Behandle Scan-Pausierung
                        while not self._scan_pause_ev.is_set():
                            if self._scan_stop_ev.is_set():
                                return
                            time.sleep(0.15)

                        # Wenn die gewünschte Thread-Anzahl reduziert wurde: überzählige Worker sauber beenden
                        with lock:
                            if active_workers > self._current_scan_threads:
                                active_workers -= 1
                                return

                        # 2. Prüfe ob Warteschlange komplett leer und keine Worker mehr aktiv sind
                        with lock:
                            if work_q.empty() and in_flight == 0:
                                break
                        try:
                            mac = work_q.get(timeout=0.15)
                        except queue.Empty:
                            continue

                        with lock:
                            in_flight += 1

                        try:
                            if delay_s > 0:
                                throttle.wait_turn(
                                    stop_check=lambda: not self._scan_stop_ev.is_set() and self._scan_pause_ev.is_set()
                                )
                            if self._scan_stop_ev.is_set():
                                continue

                            res = check_mac_account(
                                portal_url=portal_url,
                                mac=mac,
                                model=model,
                                timeout=min(5, timeout_s),
                                normalized_load_url=shared_ep[0],
                                session=worker_session,
                            )
                            res["portal_url"] = portal_url

                            if res.get("load_url") and not shared_ep[0]:
                                shared_ep[0] = res["load_url"]
                                cached_eps[norm_portal] = res["load_url"]
                                self.config_mgr.set("cached_endpoints", cached_eps)

                            err_str = str(res.get("error") or "")
                            stat_str = str(res.get("status") or "")

                            # Prüfe auf Rate-Limit oder temporäre Server-/Verbindungsfehler
                            is_rate_limit = bool(
                                res.get("rate_limited")
                                or "429" in stat_str
                                or "429" in err_str
                                or "WAF" in stat_str
                                or "WAF" in err_str
                            )
                            is_transient = bool(
                                is_rate_limit
                                or "503" in stat_str
                                or "503" in err_str
                                or "502" in stat_str
                                or "502" in err_str
                                or "504" in stat_str
                                or "504" in err_str
                                or "Timeout" in stat_str
                                or "timeout" in err_str
                                or "ConnectionError" in err_str
                                or "RemoteDisconnected" in err_str
                            )

                            ch_cnt = int(res.get("channels") or 0)
                            retries = retry_counts.get(mac, 0)
                            has_ch_error = bool(res.get("valid") and res.get("channel_error"))
                            active_date_missing_channels = bool(
                                res.get("valid")
                                and ch_cnt == 0
                                and any(y in str(res.get("expire") or "") for y in ("2025", "2026", "2027", "2028", "2029", "2030"))
                                and retries < 2
                            )
                            is_transient = bool(
                                is_transient
                                or has_ch_error
                                or active_date_missing_channels
                            )

                            # WENN TRANSIENT (Timeout/503/429/Kanalfehler): MAC hinten anstellen und erneut probieren!
                            # Scanner pausiert NICHT global, sondern prüft direkt nächste MACs mit voller Geschwindigkeit.
                            if is_transient and not self._scan_stop_ev.is_set():
                                retries += 1
                                retry_counts[mac] = retries
                                work_q.put(mac)
                                rem_q = work_q.qsize()
                                reason_txt = "Kanal-Timeout" if (has_ch_error or active_date_missing_channels) else (stat_str or "Timeout/503/429")
                                event_bus.log_message.emit(
                                    f"[⏳ Requeue] {mac} ({reason_txt}) -> hinten angestellt (Retry #{retries}, Warteschlange: {rem_q})."
                                )
                                continue

                            # Endgültiges Ergebnis ermitteln
                            if res.get("valid") and ch_cnt > 0:
                                res["tag"] = "hot"
                                self.mac_db.save_found_mac(portal_url, res)
                                event_bus.log_message.emit(
                                    f"[🔥 HIT] {res['mac']} | {ch_cnt} Kanäle | Exp: {res.get('expire')} ({portal_url})"
                                )
                            elif res.get("valid"):
                                res["tag"] = "valid"
                            else:
                                res["tag"] = "invalid"

                            with lock:
                                if mac not in conclusive_macs:
                                    conclusive_macs.add(mac)
                                    done += 1
                                cur_done = done

                            event_bus.scan_result_received.emit(res)
                            event_bus.scan_progress_updated.emit(cur_done, total)

                        finally:
                            with lock:
                                in_flight -= 1
                            work_q.task_done()
                finally:
                    with lock:
                        active_workers = max(0, active_workers - 1)
                    try:
                        worker_session.close()
                    except Exception:
                        pass

            def _spawn_workers(target_count: int):
                with lock:
                    needed = target_count - active_workers
                if needed > 0 and not self._scan_stop_ev.is_set():
                    for _ in range(needed):
                        t = threading.Thread(target=_worker, daemon=True)
                        t.start()

            self._spawn_workers_cb = _spawn_workers
            _spawn_workers(self._current_scan_threads)

            while not self._scan_stop_ev.is_set():
                with lock:
                    if work_q.empty() and in_flight == 0 and active_workers == 0:
                        break
                time.sleep(0.15)

            event_bus.scan_state_changed.emit(False)
            event_bus.log_message.emit(f"[+] MAC-Scan beendet ({done}/{total} MACs abgeschlossen).")

        threading.Thread(target=_coordinator, daemon=True).start()

    def update_scan_settings(self, threads: int, delay_s: float):
        self._current_scan_threads = max(1, threads)
        self._current_scan_delay = max(0.0, delay_s)
        if hasattr(self, "_scan_throttle") and self._scan_throttle:
            self._scan_throttle.base_delay = self._current_scan_delay
        if not self._scan_stop_ev.is_set() and hasattr(self, "_spawn_workers_cb") and self._spawn_workers_cb:
            self._spawn_workers_cb(self._current_scan_threads)

    def pause_mac_scan(self):
        self._scan_pause_ev.clear()
        event_bus.log_message.emit("[⏸] Multi-MAC Scan pausiert. Einstellungen (Threads, Delay) können jetzt angepasst werden.")

    def resume_mac_scan(self, threads: Optional[int] = None, delay_s: Optional[float] = None):
        if threads is not None and delay_s is not None:
            self.update_scan_settings(threads, delay_s)
            event_bus.log_message.emit(
                f"[▶] Multi-MAC Scan fortgesetzt ({self._current_scan_threads} Threads, {int(self._current_scan_delay * 1000)} ms Delay)."
            )
        else:
            event_bus.log_message.emit("[▶] Multi-MAC Scan fortgesetzt.")
        self._scan_pause_ev.set()

    def stop_mac_scan(self):
        self._scan_stop_ev.set()
        self._scan_pause_ev.set()
        event_bus.scan_state_changed.emit(False)

    def _prepend_known_macs_to_scanner(self):
        url = self.scanner_view.entry_portal.text().strip()
        macs = self.mac_db.get_known_macs(url or None)
        if macs:
            self.scanner_view.prepend_macs(macs)
            event_bus.log_message.emit(f"[⭐] {len(macs)} bekannte MACs aus der Datenbank geladen.")

    def apply_mac_from_scanner_or_db(self, portal_url: str, mac: str, model: str):
        prof = self._get_current_profile()
        prof.portal_type = "stalker"
        prof.provider_type = "Stalker MAC"
        prof.url = portal_url
        new_mac = StbClient.format_mac(mac)
        if new_mac != prof.mac:
            prof.mac = new_mac
            ids = StbClient.generate_device_ids(new_mac)
            prof.serial_number = ids["sn"]
            prof.device_id = ids["device_id"]
            prof.device_id2 = ids["device_id2"]
            prof.signature = ids["signature"]
        if model:
            prof.model = model
        self.config_mgr.save_profile(prof)
        self.sidebar.display_profile(prof)
        self.top_bar.set_active_view("live")
        self.connect_active_profile()

    # ══════════════════════════════════════════════════════════════════════
    # 9. Inspector & Dialogs
    # ══════════════════════════════════════════════════════════════════════

    def _run_inspector_handshake_test(self):
        prof = self._get_current_profile()
        self._dump_active_client_state()
        if not self.state.is_connected:
            self.connect_active_profile()

    def _dump_active_client_state(self):
        prof = self._get_current_profile()
        lines = [
            f"═══ STB PRO v6.0 CLIENT & HANDSHAKE BERICHT ═══",
            f"Aktives Profil : {prof.name} ({prof.provider_type})",
            f"Portal / URL   : {prof.url}",
            f"MAC / User     : {prof.mac if prof.portal_type == 'stalker' else prof.username}",
            f"STB Modell     : {prof.model}",
            f"Verbunden      : {'JA' if self.state.is_connected else 'NEIN'}",
            f"Geladene Kanäle: {len(self.state.channels)}",
        ]
        if isinstance(self.active_client, StbClient):
            lines.extend([
                f"Session Token  : {self.active_client.token}",
                f"Load Endpoint  : {self.active_client.normalized_load_url}",
                f"Serial (SN)    : {self.active_client.serial_number}",
                f"Device ID 1    : {self.active_client.device_id}",
                f"Device ID 2    : {self.active_client.device_id2}",
                f"User-Agent     : {self.active_client.user_agent}",
            ])
        self.inspector_view.set_summary_report("\n".join(lines), switch_tab=True)

    def open_buffer_dialog(self):
        st = self.vlc_ctrl.settings
        cfg = st.to_dict()
        cfg.update({
            "enabled": st.mode == "proxy",
            "ring_size_mb": st.max_mb,
            "vlc_network_caching_ms": st.vlc_caching_ms,
            "auto_reconnect": st.reconnect,
        })
        dlg = BufferConfigDialog(cfg, parent=self)
        if dlg.exec():
            res = dlg.get_config()
            st.mode = str(res.get("mode") or ("proxy" if res.get("enabled", True) else "vlc"))
            st.start_seconds = float(res.get("start_seconds", st.start_seconds))
            st.buffer_seconds = float(res.get("buffer_seconds", st.buffer_seconds))
            st.max_mb = int(res.get("max_mb", res.get("ring_size_mb", st.max_mb)))
            st.vlc_caching_ms = int(res.get("vlc_caching_ms", res.get("vlc_network_caching_ms", st.vlc_caching_ms)))
            st.reconnect = bool(res.get("reconnect", res.get("auto_reconnect", True)))
            st.hw_decode = bool(res.get("hw_decode", True))
            st.preview_enabled = bool(res.get("preview_enabled", True))
            st.preview_max_age_min = int(res.get("preview_max_age_min", 10))
            st.clamp()
            self.vlc_ctrl.apply_settings(st)
            self.config_mgr.set("buffer_settings", st.to_dict())

    def open_jobs_dialog(self):
        dlg = JobsDialog(self.recorder, parent=self)
        dlg.exec()

    def open_mac_db_dialog(self):
        dlg = MacDatabaseDialog(self.mac_db, parent=self)
        dlg.apply_mac_requested.connect(self.apply_mac_from_scanner_or_db)
        dlg.send_to_scanner_requested.connect(self._on_db_macs_to_scanner)
        dlg.exec()

    def _on_db_macs_to_scanner(self, macs: list):
        self.scanner_view.prepend_macs(macs)
        self.top_bar.set_active_view("scanner")

    def open_epg_guide_dialog(self, channel: Channel):
        if not self.active_client:
            return

        # Guard: If dialog is already open, simply bring it to front to prevent multi-click duplicates
        if getattr(self, "_active_epg_dialog", None) is not None and self._active_epg_dialog.isVisible():
            self._active_epg_dialog.raise_()
            self._active_epg_dialog.activateWindow()
            return

        client = self.active_client
        cid = str(channel.id)
        today = datetime.date.today().isoformat()

        dlg = EPGGuideDialog(channel, programs=None, parent=self)
        self._active_epg_dialog = dlg
        dlg.archive_play_requested.connect(self._play_archive_program)
        dlg.archive_download_requested.connect(self._download_archive_program)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

        def _task():
            raw = []
            if hasattr(client, "get_epg_day"):
                raw = client.get_epg_day(cid, today)
            if not raw and hasattr(client, "get_short_epg"):
                raw = client.get_short_epg(cid, size=50)
            return [EPGProgram.from_raw(e) for e in (raw or []) if isinstance(e, dict)]

        def _done(programs: List[EPGProgram]):
            if getattr(self, "_active_epg_dialog", None) is dlg and dlg.isVisible():
                dlg.set_programs(programs)

        worker_pool.run_async(_task, on_success=_done)

    def _play_archive_program(self, channel: Channel, prog: EPGProgram):
        if not self.active_client or not hasattr(self.active_client, "get_archive_url"):
            return
        client = self.active_client
        dur_m = max(5, prog.duration // 60) if prog.duration else 60
        self.top_bar.set_active_view("live")

        def _task():
            return client.get_archive_url(str(channel.id), prog.start_timestamp, dur_m)

        def _done(url: str):
            if url:
                self._start_stream_url(url, title=f"[Archiv] {prog.name}", channel=channel, is_vod=True)

        worker_pool.run_async(_task, on_success=_done, on_error=lambda e: self._on_play_error(prog.name, e))

    def _download_archive_program(self, channel: Channel, prog: EPGProgram):
        if not self.active_client or not hasattr(self.active_client, "get_archive_url"):
            return
        client = self.active_client
        dur_m = max(5, prog.duration // 60) if prog.duration else 60
        ua = getattr(self.active_client, "user_agent", "") or "VLC/3.0"

        def _task():
            return client.get_archive_url(str(channel.id), prog.start_timestamp, dur_m)

        def _done(url: str):
            if url:
                self.recorder.start(kind="dl", name=f"{channel.name}_{prog.name}", url=url, headers={"User-Agent": ua})
                self._on_recorder_changed()

        worker_pool.run_async(_task, on_success=_done)

    def show_account_details(self):
        if not self.active_client:
            prof = self._get_current_profile()
            self.open_json_viewer(f"Profil – {prof.name}", prof.to_dict())
            return
        data = getattr(self.active_client, "profile", None) or getattr(self.active_client, "user_info", None) or {}
        self.open_json_viewer("Account- & Handshake-Details", data)

    def open_json_viewer(self, title: str, data: Any):
        dlg = JsonViewerDialog(title, data, parent=self)
        dlg.exec()

    # ══════════════════════════════════════════════════════════════════════
    # 10. Sidebar Engine Callbacks, Telemetry Loop & Clean Shutdown
    # ══════════════════════════════════════════════════════════════════════

    def _on_player_engine_changed(self, text: str):
        self.config_mgr.set("selected_player", text)

    def _on_prebuffer_preset_changed(self, preset: str):
        st = self.vlc_ctrl.settings
        if "Aus" in preset:
            st.mode = "vlc"
            st.vlc_caching_ms = 1200
        else:
            st.mode = "proxy"
            if "0.8s" in preset or "0.5" in preset:
                st.start_seconds = 0.8
                st.buffer_seconds = 12.0
                st.max_mb = 64
                st.vlc_caching_ms = 1000
            elif "1.5s" in preset or "1.5" in preset:
                st.start_seconds = 1.2
                st.buffer_seconds = 15.0
                st.max_mb = 128
                st.vlc_caching_ms = 1200
            elif "2.5s" in preset or "4 MB" in preset:
                st.start_seconds = 2.0
                st.buffer_seconds = 25.0
                st.max_mb = 256
                st.vlc_caching_ms = 1800
            else:
                st.start_seconds = 3.5
                st.buffer_seconds = 35.0
                st.max_mb = 384
                st.vlc_caching_ms = 2200
        st.clamp()
        self.vlc_ctrl.apply_settings(st)
        self.config_mgr.set("prebuffer_preset", preset)
        self.config_mgr.set("buffer_settings", st.to_dict())

    def _on_timeout_changed(self, sec: int):
        self.config_mgr.set("connection_timeout_label", f"{sec}s")
        if self.active_client and hasattr(self.active_client, "timeout"):
            self.active_client.timeout = max(3, int(sec))

    def _on_ui_scale_changed(self, scale_str: str):
        self.config_mgr.set("ui_scale", scale_str)
        try:
            app = QApplication.instance()
            if not isinstance(app, QApplication):
                return
            if scale_str.strip().lower() == "auto":
                screen = app.primaryScreen()
                dpi = screen.logicalDotsPerInch() if screen else 96.0
                factor = max(0.85, min(1.35, dpi / 96.0))
            else:
                factor = float(scale_str.replace("%", "").strip()) / 100.0
            apply_obsidian_theme(app, scale_factor=factor)
        except Exception:
            pass

    def _tick_telemetry(self):
        if self.vlc_ctrl.is_playing or self.vlc_ctrl._transitioning:
            tel = self.vlc_ctrl.get_live_telemetry()
            if tel:
                self.live_view.update_live_telemetry(tel)
            if self.vlc_ctrl.is_playing:
                is_seek = self.vlc_ctrl.is_seekable()
                self.live_view.update_seek_ui(
                    is_seek, self.vlc_ctrl.get_time(), self.vlc_ctrl.get_length()
                )
                a_tracks = self.vlc_ctrl.get_audio_tracks()
                s_tracks = self.vlc_ctrl.get_subtitle_tracks()
                sig = (tuple(a_tracks), tuple(s_tracks))
                if sig != self._last_track_signature and (a_tracks or s_tracks):
                    self._last_track_signature = sig
                    self.live_view.update_tracks_ui(a_tracks, s_tracks)

        if self.recorder.active_jobs():
            self._on_recorder_changed()

    def closeEvent(self, event):
        self._selection_timer.stop()
        self._preview_timer.stop()
        self._scan_stop_ev.set()
        self._scan_pause_ev.set()
        self._val_stop_ev.set()
        self._probe_cancel_ev.set()
        self.thumb_grabber.cancel()
        self.osd.shutdown()
        self.ext_player.stop()
        self.vlc_ctrl.shutdown()
        self.recorder.stop_all()
        if self.active_client and hasattr(self.active_client, "close"):
            try:
                self.active_client.close()
            except Exception:
                pass
        worker_pool.shutdown()
        super().closeEvent(event)


