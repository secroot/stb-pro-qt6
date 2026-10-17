"""
Settings & Boost Configuration View for STB Pro Qt6.
Provides comprehensive controls for Portal Handshake, Scanner & Probing,
Stream Ringbuffer & Playback, External Player Engines, NordVPN Ban-Recovery,
and UI / System preferences with live persistence to config.json.
"""
from __future__ import annotations

import os
import shutil
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from clients.stb_client import STB_PRESETS
from core.config_manager import (
    ConfigManager,
    detect_ffplay_path,
    detect_mpv_path,
    detect_vlc_path,
)
from core.logo_cache import logo_cache
from core.stream_buffer import BufferSettings


class SettingsView(QWidget):
    settings_saved = Signal(dict)
    buffer_settings_changed = Signal(object)
    vpn_settings_changed = Signal(dict)
    ui_scale_changed = Signal(str)
    cache_cleared = Signal()

    def __init__(
        self,
        config_mgr: ConfigManager,
        vpn_mgr: Optional[Any] = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.vpn_mgr = vpn_mgr

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # ── Header Bar ──
        hdr_frame = QFrame()
        hdr_frame.setObjectName("CardFrame")
        hdr_lay = QHBoxLayout(hdr_frame)
        hdr_lay.setContentsMargins(14, 10, 14, 10)
        hdr_lay.setSpacing(10)

        lbl_title = QLabel("⚙️ SYSTEM- & LEISTUNGS-EINSTELLUNGEN (/BOOST)")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #38BDF8;")
        hdr_lay.addWidget(lbl_title)

        hdr_lay.addStretch(1)

        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")
        hdr_lay.addWidget(self.lbl_feedback)

        btn_reset = QPushButton("↺ Standardwerte")
        btn_reset.setProperty("compact", "true")
        btn_reset.setToolTip("Alle Einstellungen auf optimale System-Standardwerte zurücksetzen")
        btn_reset.clicked.connect(self.reset_to_defaults)
        hdr_lay.addWidget(btn_reset)

        self.btn_save = QPushButton("💾 Einstellungen speichern")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setToolTip("Speichert alle Einstellungen in config.json und wendet sie live an")
        self.btn_save.clicked.connect(self.save_to_config)
        hdr_lay.addWidget(self.btn_save)

        layout.addWidget(hdr_frame)

        # ── Tabbed Configuration Sections ──
        self.tabs = QTabWidget()
        self.tabs.setObjectName("SettingsTabs")

        self._build_handshake_tab()
        self._build_scanner_tab()
        self._build_buffering_tab()
        self._build_player_tab()
        self._build_vpn_tab()
        self._build_gui_tab()

        layout.addWidget(self.tabs, 1)

        # Load values into widgets
        self.load_from_config()

    # ══════════════════════════════════════════════════════════════════════
    # Tab 1: Portal & Handshake
    # ══════════════════════════════════════════════════════════════════════
    def _build_handshake_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        card = QFrame()
        card.setObjectName("CardFrame")
        form = QGridLayout(card)
        form.setContentsMargins(16, 14, 16, 14)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)

        r = 0
        lbl_sec1 = QLabel("🔒 SSL-Zertifikate & Sicherheit")
        lbl_sec1.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec1.setStyleSheet("color: #818CF8;")
        form.addWidget(lbl_sec1, r, 0, 1, 2)

        r += 1
        self.chk_ssl_verify = QCheckBox(
            "SSL-Zertifikatsprüfung für HTTPS-Portale erzwingen (Deaktivieren für selbstsignierte Provider-Certs)"
        )
        self.chk_ssl_verify.setToolTip(
            "Bei Deaktivierung können HTTPS-Portale mit ungültigen oder selbstsignierten Zertifikaten problemlos geladen werden."
        )
        form.addWidget(self.chk_ssl_verify, r, 0, 1, 2)

        r += 1
        lbl_sec2 = QLabel("⏱ Timeouts & Keepalive")
        lbl_sec2.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec2.setStyleSheet("color: #818CF8;")
        form.addWidget(lbl_sec2, r, 0, 1, 2)

        r += 1
        form.addWidget(QLabel("Connect-Timeout Handshake (Sek.):"), r, 0)
        self.spin_hs_connect = QDoubleSpinBox()
        self.spin_hs_connect.setRange(1.0, 30.0)
        self.spin_hs_connect.setSingleStep(0.5)
        self.spin_hs_connect.setDecimals(1)
        self.spin_hs_connect.setSuffix(" s")
        form.addWidget(self.spin_hs_connect, r, 1)

        r += 1
        form.addWidget(QLabel("Read-Timeout Handshake (Sek.):"), r, 0)
        self.spin_hs_read = QDoubleSpinBox()
        self.spin_hs_read.setRange(2.0, 60.0)
        self.spin_hs_read.setSingleStep(1.0)
        self.spin_hs_read.setDecimals(1)
        self.spin_hs_read.setSuffix(" s")
        form.addWidget(self.spin_hs_read, r, 1)

        r += 1
        form.addWidget(QLabel("Token-Keepalive Intervall (Sek.):"), r, 0)
        self.spin_token_refresh = QSpinBox()
        self.spin_token_refresh.setRange(15, 3600)
        self.spin_token_refresh.setSingleStep(15)
        self.spin_token_refresh.setSuffix(" s")
        self.spin_token_refresh.setToolTip(
            "Intervall für Hintergrund-Keepalive Pings an das Stalker Portal, um Session-Tokens aktiv zu halten."
        )
        form.addWidget(self.spin_token_refresh, r, 1)

        r += 1
        lbl_sec3 = QLabel("📟 STB-Emulation Standardwerte")
        lbl_sec3.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec3.setStyleSheet("color: #818CF8;")
        form.addWidget(lbl_sec3, r, 0, 1, 2)

        r += 1
        form.addWidget(QLabel("Standard STB-Modell:"), r, 0)
        self.combo_default_model = QComboBox()
        self.combo_default_model.addItems(list(STB_PRESETS.keys()))
        form.addWidget(self.combo_default_model, r, 1)

        r += 1
        form.addWidget(QLabel("Device-ID Generierung:"), r, 0)
        self.combo_devid_mode = QComboBox()
        self.combo_devid_mode.addItem("Deterministisch (Standard StbEmu / SHA256)", "deterministic")
        self.combo_devid_mode.addItem("Zufallsbasiert (64-Zeichen Hex)", "random")
        form.addWidget(self.combo_devid_mode, r, 1)

        r += 1
        form.addWidget(QLabel("Standard User-Agent Fallback:"), r, 0)
        self.entry_default_ua = QLineEdit()
        self.entry_default_ua.setPlaceholderText("Leer lassen für modellabhängigen Standard-User-Agent")
        form.addWidget(self.entry_default_ua, r, 1)

        lay.addWidget(card)
        lay.addStretch(1)
        self.tabs.addTab(tab, "🌐 Handshake & Verbindung")

    # ══════════════════════════════════════════════════════════════════════
    # Tab 2: Scanner & Probing
    # ══════════════════════════════════════════════════════════════════════
    def _build_scanner_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        card = QFrame()
        card.setObjectName("CardFrame")
        form = QGridLayout(card)
        form.setContentsMargins(16, 14, 16, 14)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)

        r = 0
        lbl_sec1 = QLabel("⚡ Scan-Performance & Concurrency")
        lbl_sec1.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec1.setStyleSheet("color: #818CF8;")
        form.addWidget(lbl_sec1, r, 0, 1, 2)

        r += 1
        form.addWidget(QLabel("Standard-Threads (Scanner Concurrency):"), r, 0)
        self.spin_scan_threads = QSpinBox()
        self.spin_scan_threads.setRange(1, 64)
        self.spin_scan_threads.setValue(8)
        form.addWidget(self.spin_scan_threads, r, 1)

        r += 1
        form.addWidget(QLabel("Standard-Verzögerung zwischen Requests (Sek.):"), r, 0)
        self.spin_scan_delay = QDoubleSpinBox()
        self.spin_scan_delay.setRange(0.0, 5.0)
        self.spin_scan_delay.setSingleStep(0.05)
        self.spin_scan_delay.setDecimals(2)
        self.spin_scan_delay.setSuffix(" s")
        form.addWidget(self.spin_scan_delay, r, 1)

        r += 1
        form.addWidget(QLabel("Probe-Timeout pro MAC (Sek.):"), r, 0)
        self.spin_scan_probe_timeout = QDoubleSpinBox()
        self.spin_scan_probe_timeout.setRange(1.0, 20.0)
        self.spin_scan_probe_timeout.setSingleStep(0.5)
        self.spin_scan_probe_timeout.setDecimals(1)
        self.spin_scan_probe_timeout.setSuffix(" s")
        form.addWidget(self.spin_scan_probe_timeout, r, 1)

        r += 1
        lbl_sec2 = QLabel("🛡 Resilienz & Auto-Requeue (Stalker-Richtlinien)")
        lbl_sec2.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec2.setStyleSheet("color: #818CF8;")
        form.addWidget(lbl_sec2, r, 0, 1, 2)

        r += 1
        self.chk_scan_requeue = QCheckBox(
            "Auto-Requeue bei transienten Fehlern (502/503/429/Timeout/Kanalfehler)"
        )
        self.chk_scan_requeue.setToolTip(
            "Stellt Accounts mit aktivem Ablaufdatum und vorübergehendem Server-Drop automatisch hinten an."
        )
        form.addWidget(self.chk_scan_requeue, r, 0, 1, 2)

        r += 1
        form.addWidget(QLabel("Max. Requeue-Wiederholungen pro MAC:"), r, 0)
        self.spin_scan_max_retries = QSpinBox()
        self.spin_scan_max_retries.setRange(1, 10)
        self.spin_scan_max_retries.setValue(2)
        form.addWidget(self.spin_scan_max_retries, r, 1)

        r += 1
        lbl_sec3 = QLabel("🔍 Stalker API & Kategorie-Validierung")
        lbl_sec3.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec3.setStyleSheet("color: #818CF8;")
        form.addWidget(lbl_sec3, r, 0, 1, 2)

        r += 1
        form.addWidget(QLabel("Ordered-List Genre-Filter:"), r, 0)
        self.entry_scan_genre = QLineEdit("*")
        self.entry_scan_genre.setToolTip("Standard ist '*' für alle Genres (~2 KB Payload)")
        form.addWidget(self.entry_scan_genre, r, 1)

        r += 1
        form.addWidget(QLabel("Ordered-List Sortierung:"), r, 0)
        self.combo_scan_sortby = QComboBox()
        self.combo_scan_sortby.addItems(["number", "name", "id"])
        form.addWidget(self.combo_scan_sortby, r, 1)

        r += 1
        self.chk_scan_fallback_all = QCheckBox(
            "Fallback auf get_all_channels falls get_ordered_list 0 Kanäle meldet"
        )
        form.addWidget(self.chk_scan_fallback_all, r, 0, 1, 2)

        r += 1
        form.addWidget(QLabel("Parallele Sender-Validierungs-Threads:"), r, 0)
        self.spin_val_workers = QSpinBox()
        self.spin_val_workers.setRange(1, 32)
        self.spin_val_workers.setValue(8)
        form.addWidget(self.spin_val_workers, r, 1)

        r += 1
        form.addWidget(QLabel("Validierungs-Timeout pro Sender (Sek.):"), r, 0)
        self.spin_val_timeout = QDoubleSpinBox()
        self.spin_val_timeout.setRange(1.0, 15.0)
        self.spin_val_timeout.setSingleStep(0.5)
        self.spin_val_timeout.setDecimals(1)
        self.spin_val_timeout.setSuffix(" s")
        form.addWidget(self.spin_val_timeout, r, 1)

        r += 1
        self.chk_val_auto = QCheckBox(
            "Kategorie bei erster Auswahl in der Sitzung automatisch im Hintergrund prüfen"
        )
        form.addWidget(self.chk_val_auto, r, 0, 1, 2)

        lay.addWidget(card)
        lay.addStretch(1)
        self.tabs.addTab(tab, "🎯 Scanner & Probing")

    # ══════════════════════════════════════════════════════════════════════
    # Tab 3: Puffer & Wiedergabe
    # ══════════════════════════════════════════════════════════════════════
    def _build_buffering_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        card = QFrame()
        card.setObjectName("CardFrame")
        form = QGridLayout(card)
        form.setContentsMargins(16, 14, 16, 14)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)

        r = 0
        lbl_sec1 = QLabel("🛡 Lokaler PCR-Ringpuffer-Proxy (127.0.0.1)")
        lbl_sec1.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec1.setStyleSheet("color: #38BDF8;")
        form.addWidget(lbl_sec1, r, 0, 1, 2)

        r += 1
        form.addWidget(QLabel("Puffer-Betriebsmodus:"), r, 0)
        self.combo_buf_mode = QComboBox()
        self.combo_buf_mode.addItem("Proxy (Lokaler PCR-Ringpuffer, Empfohlen)", "proxy")
        self.combo_buf_mode.addItem("VLC Direct (Direktes LibVLC Caching)", "vlc")
        form.addWidget(self.combo_buf_mode, r, 1)

        r += 1
        form.addWidget(QLabel("Startpuffer (Wiedergabe ab X Sek.):"), r, 0)
        self.spin_buf_start_s = QDoubleSpinBox()
        self.spin_buf_start_s.setRange(0.2, 10.0)
        self.spin_buf_start_s.setSingleStep(0.2)
        self.spin_buf_start_s.setDecimals(1)
        self.spin_buf_start_s.setSuffix(" s")
        self.spin_buf_start_s.setToolTip("Geringer Wert = extrem schnelles Zapping; Höherer Wert = maximale Stabilität.")
        form.addWidget(self.spin_buf_start_s, r, 1)

        r += 1
        form.addWidget(QLabel("Ziel-Ringpufferlänge im RAM (Sek.):"), r, 0)
        self.spin_buf_target_s = QDoubleSpinBox()
        self.spin_buf_target_s.setRange(2.0, 180.0)
        self.spin_buf_target_s.setSingleStep(2.0)
        self.spin_buf_target_s.setDecimals(1)
        self.spin_buf_target_s.setSuffix(" s")
        form.addWidget(self.spin_buf_target_s, r, 1)

        r += 1
        form.addWidget(QLabel("Maximaler RAM-Ringpuffer (MB):"), r, 0)
        self.spin_buf_max_mb = QSpinBox()
        self.spin_buf_max_mb.setRange(8, 1024)
        self.spin_buf_max_mb.setSingleStep(16)
        self.spin_buf_max_mb.setSuffix(" MB")
        form.addWidget(self.spin_buf_max_mb, r, 1)

        r += 1
        form.addWidget(QLabel("VLC Network/Live-Caching (ms):"), r, 0)
        self.spin_vlc_cache_ms = QSpinBox()
        self.spin_vlc_cache_ms.setRange(200, 15000)
        self.spin_vlc_cache_ms.setSingleStep(100)
        self.spin_vlc_cache_ms.setSuffix(" ms")
        form.addWidget(self.spin_vlc_cache_ms, r, 1)

        r += 1
        lbl_sec2 = QLabel("⚡ PCR-Glättung & Reconnect-Schutz")
        lbl_sec2.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec2.setStyleSheet("color: #818CF8;")
        form.addWidget(lbl_sec2, r, 0, 1, 2)

        r += 1
        self.chk_pcr_smoothing = QCheckBox("PCR-Rate-Smoothing aktivieren (Präzise TS-Taktung)")
        self.chk_pcr_smoothing.setToolTip(
            "Glättet unregelmäßige Server-Ausgaberaten anhand der MPEG-TS PCR Zeitstempel."
        )
        form.addWidget(self.chk_pcr_smoothing, r, 0, 1, 2)

        r += 1
        form.addWidget(QLabel("Fallback Bitrate bei fehlendem PCR (kbps):"), r, 0)
        self.spin_fallback_kbps = QSpinBox()
        self.spin_fallback_kbps.setRange(500, 50000)
        self.spin_fallback_kbps.setSingleStep(500)
        self.spin_fallback_kbps.setSuffix(" kbps")
        form.addWidget(self.spin_fallback_kbps, r, 1)

        r += 1
        self.chk_buf_reconnect = QCheckBox("Automatischer Upstream-Reconnect bei Verbindungsabbruch")
        form.addWidget(self.chk_buf_reconnect, r, 0, 1, 2)

        r += 1
        form.addWidget(QLabel("Maximale Reconnect-Versuche:"), r, 0)
        self.spin_buf_max_retries = QSpinBox()
        self.spin_buf_max_retries.setRange(1, 50)
        self.spin_buf_max_retries.setValue(10)
        form.addWidget(self.spin_buf_max_retries, r, 1)

        r += 1
        self.chk_hw_decode = QCheckBox("Hardware-Dekodierung (Direct3D11 / DXVA2) aktivieren")
        form.addWidget(self.chk_hw_decode, r, 0, 1, 2)

        r += 1
        self.chk_preview_enabled = QCheckBox("Live-Standbild-Vorschau bei Senderauswahl aktivieren")
        form.addWidget(self.chk_preview_enabled, r, 0, 1, 2)

        r += 1
        form.addWidget(QLabel("Maximales Vorschau-Cache-Alter (Min.):"), r, 0)
        self.spin_preview_age = QSpinBox()
        self.spin_preview_age.setRange(0, 180)
        self.spin_preview_age.setSuffix(" Min.")
        form.addWidget(self.spin_preview_age, r, 1)

        lay.addWidget(card)
        lay.addStretch(1)
        self.tabs.addTab(tab, "🛡️ Puffer & Wiedergabe")

    # ══════════════════════════════════════════════════════════════════════
    # Tab 4: Externe Player
    # ══════════════════════════════════════════════════════════════════════
    def _build_player_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        card = QFrame()
        card.setObjectName("CardFrame")
        form = QGridLayout(card)
        form.setContentsMargins(16, 14, 16, 14)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)

        r = 0
        lbl_sec = QLabel("🎮 Player-Engines & Pfade")
        lbl_sec.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec.setStyleSheet("color: #818CF8;")
        form.addWidget(lbl_sec, r, 0, 1, 3)

        r += 1
        form.addWidget(QLabel("Standard Player-Engine:"), r, 0)
        self.combo_player = QComboBox()
        self.combo_player.addItems([
            "Integrierter Player",
            "VLC Media Player",
            "mpv",
            "ffplay",
        ])
        form.addWidget(self.combo_player, r, 1, 1, 2)

        r += 1
        form.addWidget(QLabel("Standardlautstärke (%):"), r, 0)
        self.spin_volume = QSpinBox()
        self.spin_volume.setRange(0, 100)
        self.spin_volume.setValue(100)
        self.spin_volume.setSuffix(" %")
        form.addWidget(self.spin_volume, r, 1, 1, 2)

        # VLC Pfad
        r += 1
        form.addWidget(QLabel("VLC Executable Pfad:"), r, 0)
        self.entry_vlc_path = QLineEdit()
        self.entry_vlc_path.setPlaceholderText("z.B. C:\\Program Files\\VideoLAN\\VLC\\vlc.exe")
        form.addWidget(self.entry_vlc_path, r, 1)
        btn_vlc_browse = QPushButton("📁 Durchsuchen...")
        btn_vlc_browse.clicked.connect(lambda: self._browse_file(self.entry_vlc_path, "VLC Executable (*.exe)"))
        form.addWidget(btn_vlc_browse, r, 2)

        # mpv Pfad
        r += 1
        form.addWidget(QLabel("mpv Executable Pfad:"), r, 0)
        self.entry_mpv_path = QLineEdit()
        self.entry_mpv_path.setPlaceholderText("z.B. C:\\Tools\\mpv\\mpv.exe")
        form.addWidget(self.entry_mpv_path, r, 1)
        btn_mpv_browse = QPushButton("📁 Durchsuchen...")
        btn_mpv_browse.clicked.connect(lambda: self._browse_file(self.entry_mpv_path, "mpv Executable (*.exe)"))
        form.addWidget(btn_mpv_browse, r, 2)

        # ffplay Pfad
        r += 1
        form.addWidget(QLabel("ffplay Executable Pfad:"), r, 0)
        self.entry_ffplay_path = QLineEdit()
        self.entry_ffplay_path.setPlaceholderText("z.B. C:\\ffmpeg\\bin\\ffplay.exe")
        form.addWidget(self.entry_ffplay_path, r, 1)
        btn_ffplay_browse = QPushButton("📁 Durchsuchen...")
        btn_ffplay_browse.clicked.connect(lambda: self._browse_file(self.entry_ffplay_path, "ffplay Executable (*.exe)"))
        form.addWidget(btn_ffplay_browse, r, 2)

        r += 1
        btn_auto_detect_players = QPushButton("🔍 Player automatisch im System suchen")
        btn_auto_detect_players.clicked.connect(self._auto_detect_players)
        form.addWidget(btn_auto_detect_players, r, 0, 1, 3)

        lay.addWidget(card)
        lay.addStretch(1)
        self.tabs.addTab(tab, "🎮 Externe Player")

    # ══════════════════════════════════════════════════════════════════════
    # Tab 5: NordVPN Ban-Recovery
    # ══════════════════════════════════════════════════════════════════════
    def _build_vpn_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        card = QFrame()
        card.setObjectName("CardFrame")
        form = QGridLayout(card)
        form.setContentsMargins(16, 14, 16, 14)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)

        r = 0
        lbl_sec1 = QLabel("🛡️ NordVPN Status & CLI-Steuerung")
        lbl_sec1.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec1.setStyleSheet("color: #38BDF8;")
        form.addWidget(lbl_sec1, r, 0, 1, 3)

        r += 1
        form.addWidget(QLabel("Erkannter NordVPN Status:"), r, 0)
        self.lbl_vpn_status = QLabel("Wird geprüft...")
        self.lbl_vpn_status.setStyleSheet("font-weight: bold; color: #94A3B8;")
        form.addWidget(self.lbl_vpn_status, r, 1, 1, 2)

        r += 1
        form.addWidget(QLabel("Benutzerdefinierter CLI-Pfad:"), r, 0)
        self.entry_vpn_cli = QLineEdit()
        self.entry_vpn_cli.setPlaceholderText("Leer lassen für automatische Erkennung")
        form.addWidget(self.entry_vpn_cli, r, 1)
        btn_vpn_browse = QPushButton("📁 Durchsuchen...")
        btn_vpn_browse.clicked.connect(lambda: self._browse_file(self.entry_vpn_cli, "NordVPN CLI (*.exe)"))
        form.addWidget(btn_vpn_browse, r, 2)

        r += 1
        lbl_sec2 = QLabel("🔄 Auto-Rotation & Ban-Recovery")
        lbl_sec2.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec2.setStyleSheet("color: #818CF8;")
        form.addWidget(lbl_sec2, r, 0, 1, 3)

        r += 1
        self.chk_vpn_auto = QCheckBox(
            "Automatische Server-Rotation bei Stream-IP-Sperren (HTTP 511/456/401/403/458) aktivieren"
        )
        form.addWidget(self.chk_vpn_auto, r, 0, 1, 3)

        r += 1
        form.addWidget(QLabel("Cooldown zwischen Server-Wechseln (Sek.):"), r, 0)
        self.spin_vpn_cooldown = QDoubleSpinBox()
        self.spin_vpn_cooldown.setRange(5.0, 120.0)
        self.spin_vpn_cooldown.setSingleStep(5.0)
        self.spin_vpn_cooldown.setDecimals(1)
        self.spin_vpn_cooldown.setSuffix(" s")
        self.spin_vpn_cooldown.setToolTip("Verhindert Erschöpfung des NordVPN Cloud-Gerätelimits.")
        form.addWidget(self.spin_vpn_cooldown, r, 1, 1, 2)

        r += 1
        form.addWidget(QLabel("Debounce / Interface-Stabilisierung (Sek.):"), r, 0)
        self.spin_vpn_debounce = QDoubleSpinBox()
        self.spin_vpn_debounce.setRange(0.5, 15.0)
        self.spin_vpn_debounce.setSingleStep(0.5)
        self.spin_vpn_debounce.setDecimals(1)
        self.spin_vpn_debounce.setSuffix(" s")
        form.addWidget(self.spin_vpn_debounce, r, 1, 1, 2)

        r += 1
        form.addWidget(QLabel("Max. konsekutive Hops vor Cooldown:"), r, 0)
        self.spin_vpn_hops = QSpinBox()
        self.spin_vpn_hops.setRange(1, 20)
        self.spin_vpn_hops.setValue(5)
        form.addWidget(self.spin_vpn_hops, r, 1, 1, 2)

        r += 1
        form.addWidget(QLabel("Standard Fallback-Zielland:"), r, 0)
        self.combo_vpn_fallback = QComboBox()
        self.combo_vpn_fallback.addItems([
            "Germany",
            "Switzerland",
            "Austria",
            "Netherlands",
            "United Kingdom",
            "United States",
            "France",
            "Turkey",
        ])
        form.addWidget(self.combo_vpn_fallback, r, 1, 1, 2)

        r += 1
        form.addWidget(QLabel("Rotations-Pool (Komma-separiert):"), r, 0)
        self.entry_vpn_pool = QLineEdit()
        self.entry_vpn_pool.setPlaceholderText("z.B. Switzerland, Austria, Netherlands, Germany, France")
        form.addWidget(self.entry_vpn_pool, r, 1, 1, 2)

        r += 1
        lbl_sec3 = QLabel("🔥 Tracking verbrannter IPs")
        lbl_sec3.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec3.setStyleSheet("color: #818CF8;")
        form.addWidget(lbl_sec3, r, 0, 1, 3)

        r += 1
        btn_clear_burned = QPushButton("🧹 Alle verbrannten IPs zurücksetzen")
        btn_clear_burned.clicked.connect(self._clear_all_burned_ips)
        form.addWidget(btn_clear_burned, r, 0, 1, 3)

        lay.addWidget(card)
        lay.addStretch(1)
        self.tabs.addTab(tab, "🛡️ NordVPN Ban-Recovery")

    # ══════════════════════════════════════════════════════════════════════
    # Tab 6: GUI & System
    # ══════════════════════════════════════════════════════════════════════
    def _build_gui_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        card = QFrame()
        card.setObjectName("CardFrame")
        form = QGridLayout(card)
        form.setContentsMargins(16, 14, 16, 14)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)

        r = 0
        lbl_sec = QLabel("🖥️ Erscheinungsbild & Verhalten")
        lbl_sec.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec.setStyleSheet("color: #818CF8;")
        form.addWidget(lbl_sec, r, 0, 1, 2)

        r += 1
        form.addWidget(QLabel("UI-Skalierung:"), r, 0)
        self.combo_ui_scale = QComboBox()
        self.combo_ui_scale.addItems(["90%", "100%", "120%", "Auto"])
        form.addWidget(self.combo_ui_scale, r, 1)

        r += 1
        self.chk_start_max = QCheckBox("Beim Programmstart maximiert öffnen")
        form.addWidget(self.chk_start_max, r, 0, 1, 2)

        r += 1
        self.chk_hide_dead = QCheckBox("Inaktive / Tote Sender in der Senderliste ausblenden")
        form.addWidget(self.chk_hide_dead, r, 0, 1, 2)

        r += 1
        lbl_sec2 = QLabel("🗑️ Cache & Speicherverwaltung")
        lbl_sec2.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sec2.setStyleSheet("color: #818CF8;")
        form.addWidget(lbl_sec2, r, 0, 1, 2)

        r += 1
        btn_clear_cache = QPushButton("🗑️ Sender-Logo- und Thumbnail-Cache leeren")
        btn_clear_cache.clicked.connect(self._clear_caches)
        form.addWidget(btn_clear_cache, r, 0, 1, 2)

        lay.addWidget(card)
        lay.addStretch(1)
        self.tabs.addTab(tab, "🖥️ GUI & System")

    # ══════════════════════════════════════════════════════════════════════
    # Logic: Load & Save
    # ══════════════════════════════════════════════════════════════════════
    def load_from_config(self):
        cfg = self.config_mgr.config

        # 1. Handshake
        self.chk_ssl_verify.setChecked(bool(cfg.get("ssl_verify", False)))
        self.spin_hs_connect.setValue(float(cfg.get("handshake_connect_timeout", 4.5)))
        self.spin_hs_read.setValue(float(cfg.get("handshake_read_timeout", 8.0)))
        self.spin_token_refresh.setValue(int(cfg.get("token_refresh_interval_s", 75)))

        model = str(cfg.get("default_stb_model", "MAG 250"))
        idx = self.combo_default_model.findText(model)
        if idx >= 0:
            self.combo_default_model.setCurrentIndex(idx)

        dmode = str(cfg.get("device_id_mode", "deterministic"))
        didx = self.combo_devid_mode.findData(dmode)
        if didx >= 0:
            self.combo_devid_mode.setCurrentIndex(didx)

        self.entry_default_ua.setText(str(cfg.get("custom_user_agent_default", "")))

        # 2. Scanner
        self.spin_scan_threads.setValue(int(cfg.get("scan_threads", 8)))
        self.spin_scan_delay.setValue(float(cfg.get("scan_delay_s", 0.0)))
        self.spin_scan_probe_timeout.setValue(float(cfg.get("scan_probe_timeout", 5.0)))
        self.chk_scan_requeue.setChecked(bool(cfg.get("scan_auto_requeue", True)))
        self.spin_scan_max_retries.setValue(int(cfg.get("scan_max_requeue_retries", 2)))
        self.entry_scan_genre.setText(str(cfg.get("scan_genre_param", "*")))
        sortby = str(cfg.get("scan_sortby_param", "number"))
        sidx = self.combo_scan_sortby.findText(sortby)
        if sidx >= 0:
            self.combo_scan_sortby.setCurrentIndex(sidx)
        self.chk_scan_fallback_all.setChecked(bool(cfg.get("scan_fallback_get_all", True)))
        self.spin_val_workers.setValue(int(cfg.get("validation_workers", 8)))
        self.spin_val_timeout.setValue(float(cfg.get("validation_probe_timeout", 3.0)))
        self.chk_val_auto.setChecked(bool(cfg.get("validation_auto_start", True)))

        # 3. Puffer & Wiedergabe
        raw_buf = cfg.get("buffer_settings") or {}
        st = BufferSettings.from_dict(raw_buf)
        bidx = self.combo_buf_mode.findData(st.mode)
        if bidx >= 0:
            self.combo_buf_mode.setCurrentIndex(bidx)
        self.spin_buf_start_s.setValue(float(st.start_seconds))
        self.spin_buf_target_s.setValue(float(st.buffer_seconds))
        self.spin_buf_max_mb.setValue(int(st.max_mb))
        self.spin_vlc_cache_ms.setValue(int(st.vlc_caching_ms))
        self.chk_pcr_smoothing.setChecked(bool(cfg.get("pcr_smoothing_enabled", True)))
        self.spin_fallback_kbps.setValue(int(st.fallback_kbps))
        self.chk_buf_reconnect.setChecked(bool(st.reconnect))
        self.spin_buf_max_retries.setValue(int(st.max_retries))
        self.chk_hw_decode.setChecked(bool(st.hw_decode))
        self.chk_preview_enabled.setChecked(bool(st.preview_enabled))
        self.spin_preview_age.setValue(int(st.preview_max_age_min))

        # 4. Player
        cur_player = str(cfg.get("selected_player", "Integrierter Player"))
        pidx = self.combo_player.findText(cur_player)
        if pidx >= 0:
            self.combo_player.setCurrentIndex(pidx)
        self.spin_volume.setValue(int(cfg.get("player_volume", 100)))
        self.entry_vlc_path.setText(str(cfg.get("vlc_path", "")))
        self.entry_mpv_path.setText(str(cfg.get("mpv_path", "")))
        self.entry_ffplay_path.setText(str(cfg.get("ffplay_path", "")))

        # 5. VPN
        self.chk_vpn_auto.setChecked(bool(cfg.get("vpn_auto_switch", True)))
        self.spin_vpn_cooldown.setValue(float(cfg.get("vpn_cooldown_seconds", 15.0)))
        self.spin_vpn_debounce.setValue(float(cfg.get("vpn_debounce_seconds", 2.0)))
        self.spin_vpn_hops.setValue(int(cfg.get("vpn_max_consecutive_hops", 5)))
        fb_country = str(cfg.get("vpn_fallback_country", "Germany"))
        fidx = self.combo_vpn_fallback.findText(fb_country)
        if fidx >= 0:
            self.combo_vpn_fallback.setCurrentIndex(fidx)
        self.entry_vpn_cli.setText(str(cfg.get("vpn_custom_cli_path", "")))
        raw_pool = cfg.get("vpn_rotation_pool") or []
        self.entry_vpn_pool.setText(", ".join(str(x) for x in raw_pool))

        # Update VPN status label
        self._update_vpn_badge()

        # 6. GUI
        scale = str(cfg.get("ui_scale", "100%"))
        scidx = self.combo_ui_scale.findText(scale)
        if scidx >= 0:
            self.combo_ui_scale.setCurrentIndex(scidx)
        self.chk_start_max.setChecked(bool(cfg.get("start_maximized", True)))
        self.chk_hide_dead.setChecked(bool(cfg.get("hide_dead_channels", False)))

    def save_to_config(self):
        # 1. Handshake
        self.config_mgr.set("ssl_verify", self.chk_ssl_verify.isChecked(), auto_save=False)
        self.config_mgr.set("handshake_connect_timeout", self.spin_hs_connect.value(), auto_save=False)
        self.config_mgr.set("handshake_read_timeout", self.spin_hs_read.value(), auto_save=False)
        self.config_mgr.set("token_refresh_interval_s", self.spin_token_refresh.value(), auto_save=False)
        self.config_mgr.set("default_stb_model", self.combo_default_model.currentText(), auto_save=False)
        self.config_mgr.set("device_id_mode", self.combo_devid_mode.currentData(), auto_save=False)
        self.config_mgr.set("custom_user_agent_default", self.entry_default_ua.text().strip(), auto_save=False)

        # 2. Scanner
        self.config_mgr.set("scan_threads", self.spin_scan_threads.value(), auto_save=False)
        self.config_mgr.set("scan_delay_s", self.spin_scan_delay.value(), auto_save=False)
        self.config_mgr.set("scan_probe_timeout", self.spin_scan_probe_timeout.value(), auto_save=False)
        self.config_mgr.set("scan_auto_requeue", self.chk_scan_requeue.isChecked(), auto_save=False)
        self.config_mgr.set("scan_max_requeue_retries", self.spin_scan_max_retries.value(), auto_save=False)
        self.config_mgr.set("scan_genre_param", self.entry_scan_genre.text().strip() or "*", auto_save=False)
        self.config_mgr.set("scan_sortby_param", self.combo_scan_sortby.currentText(), auto_save=False)
        self.config_mgr.set("scan_fallback_get_all", self.chk_scan_fallback_all.isChecked(), auto_save=False)
        self.config_mgr.set("validation_workers", self.spin_val_workers.value(), auto_save=False)
        self.config_mgr.set("validation_probe_timeout", self.spin_val_timeout.value(), auto_save=False)
        self.config_mgr.set("validation_auto_start", self.chk_val_auto.isChecked(), auto_save=False)

        # 3. Buffer Settings
        buf_st = BufferSettings(
            mode=self.combo_buf_mode.currentData(),
            vlc_caching_ms=self.spin_vlc_cache_ms.value(),
            start_seconds=self.spin_buf_start_s.value(),
            buffer_seconds=self.spin_buf_target_s.value(),
            max_mb=self.spin_buf_max_mb.value(),
            fallback_kbps=self.spin_fallback_kbps.value(),
            reconnect=self.chk_buf_reconnect.isChecked(),
            max_retries=self.spin_buf_max_retries.value(),
            timeout_connect=self.spin_hs_connect.value(),
            timeout_read=self.spin_hs_read.value(),
            hw_decode=self.chk_hw_decode.isChecked(),
            preview_enabled=self.chk_preview_enabled.isChecked(),
            preview_max_age_min=self.spin_preview_age.value(),
            pcr_smoothing_enabled=self.chk_pcr_smoothing.isChecked(),
        ).clamp()
        self.config_mgr.set("buffer_settings", buf_st.to_dict(), auto_save=False)
        self.config_mgr.set("pcr_smoothing_enabled", self.chk_pcr_smoothing.isChecked(), auto_save=False)

        # 4. Player
        self.config_mgr.set("selected_player", self.combo_player.currentText(), auto_save=False)
        self.config_mgr.set("player_volume", self.spin_volume.value(), auto_save=False)
        self.config_mgr.set("vlc_path", self.entry_vlc_path.text().strip(), auto_save=False)
        self.config_mgr.set("mpv_path", self.entry_mpv_path.text().strip(), auto_save=False)
        self.config_mgr.set("ffplay_path", self.entry_ffplay_path.text().strip(), auto_save=False)

        # 5. VPN
        self.config_mgr.set("vpn_auto_switch", self.chk_vpn_auto.isChecked(), auto_save=False)
        self.config_mgr.set("vpn_cooldown_seconds", self.spin_vpn_cooldown.value(), auto_save=False)
        self.config_mgr.set("vpn_debounce_seconds", self.spin_vpn_debounce.value(), auto_save=False)
        self.config_mgr.set("vpn_max_consecutive_hops", self.spin_vpn_hops.value(), auto_save=False)
        self.config_mgr.set("vpn_fallback_country", self.combo_vpn_fallback.currentText(), auto_save=False)
        self.config_mgr.set("vpn_custom_cli_path", self.entry_vpn_cli.text().strip(), auto_save=False)
        pool_raw = [x.strip() for x in self.entry_vpn_pool.text().split(",") if x.strip()]
        self.config_mgr.set("vpn_rotation_pool", pool_raw, auto_save=False)

        # 6. GUI
        old_scale = self.config_mgr.get("ui_scale", "100%")
        new_scale = self.combo_ui_scale.currentText()
        self.config_mgr.set("ui_scale", new_scale, auto_save=False)
        self.config_mgr.set("start_maximized", self.chk_start_max.isChecked(), auto_save=False)
        self.config_mgr.set("hide_dead_channels", self.chk_hide_dead.isChecked(), auto_save=False)

        # Save to disk
        self.config_mgr.save()

        # Dynamically reload VPN manager state & update status badge
        if self.vpn_mgr:
            self.vpn_mgr.reload_config()
            self._update_vpn_badge()

        # Emit change signals
        self.buffer_settings_changed.emit(buf_st)
        self.vpn_settings_changed.emit(self.config_mgr.config)
        if old_scale != new_scale:
            self.ui_scale_changed.emit(new_scale)
        self.settings_saved.emit(self.config_mgr.config)

        # Show feedback toast
        self.lbl_feedback.setText("✅ Einstellungen erfolgreich gespeichert & live angewendet!")
        QTimer.singleShot(3500, lambda: self.lbl_feedback.setText(""))

    def reset_to_defaults(self):
        ret = QMessageBox.question(
            self,
            "Standardwerte wiederherstellen",
            "Möchten Sie wirklich alle erweiterten Einstellungen auf die Standardwerte zurücksetzen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            defaults = self.config_mgr._default_config()
            for k, v in defaults.items():
                if k not in ("profiles", "last_profile", "favorites", "vod_favorites", "recently_played", "burned_ips"):
                    self.config_mgr.set(k, v, auto_save=False)
            self.config_mgr.save()
            self.load_from_config()
            self.save_to_config()
            self.lbl_feedback.setText("↺ Standardwerte wiederhergestellt!")
            QTimer.singleShot(3500, lambda: self.lbl_feedback.setText(""))

    def _browse_file(self, line_edit: QLineEdit, filter_str: str):
        path, _ = QFileDialog.getOpenFileName(self, "Programmdatei auswählen", "", filter_str)
        if path:
            line_edit.setText(path)

    def _auto_detect_players(self):
        vlc = detect_vlc_path()
        mpv = detect_mpv_path()
        ffp = detect_ffplay_path()
        found = []
        if vlc:
            self.entry_vlc_path.setText(vlc)
            found.append("VLC")
        if mpv:
            self.entry_mpv_path.setText(mpv)
            found.append("mpv")
        if ffp:
            self.entry_ffplay_path.setText(ffp)
            found.append("ffplay")

        if found:
            QMessageBox.information(
                self,
                "Player erkannt",
                f"Folgende Player wurden erfolgreich im System lokalisiert:\n• " + "\n• ".join(found),
            )
        else:
            QMessageBox.warning(
                self,
                "Keine Player gefunden",
                "Es konnten keine bekannten Standard-Installationen von VLC, mpv oder ffplay gefunden werden.",
            )

    def _update_vpn_badge(self):
        if not self.vpn_mgr:
            self.lbl_vpn_status.setText("VPN Manager nicht initialisiert")
            return
        installed = self.vpn_mgr.is_installed()
        running = self.vpn_mgr.is_running()
        connected = self.vpn_mgr.is_connected()
        if connected:
            self.lbl_vpn_status.setText("🟢 Verbunden (NordLynx aktiv)")
            self.lbl_vpn_status.setStyleSheet("color: #10B981; font-weight: bold;")
        elif running:
            self.lbl_vpn_status.setText("🟡 Installiert & Aktiv (Getrennt)")
            self.lbl_vpn_status.setStyleSheet("color: #F59E0B; font-weight: bold;")
        elif installed:
            self.lbl_vpn_status.setText("⚪ Installiert (App geschlossen)")
            self.lbl_vpn_status.setStyleSheet("color: #94A3B8; font-weight: bold;")
        else:
            self.lbl_vpn_status.setText("🔴 Nicht gefunden / Nicht installiert")
            self.lbl_vpn_status.setStyleSheet("color: #EF4444; font-weight: bold;")

    def _clear_all_burned_ips(self):
        if self.vpn_mgr:
            self.vpn_mgr.clear_burned_ips()
        else:
            self.config_mgr.clear_burned_ips()
        QMessageBox.information(
            self,
            "Verbrannte IPs zurückgesetzt",
            "Alle verzeichneten verbrannten IP-Adressen wurden erfolgreich gelöscht.",
        )

    def _clear_caches(self):
        logo_cache.clear()
        self.cache_cleared.emit()
        QMessageBox.information(
            self,
            "Cache geleert",
            "Der Sender-Logo- und Thumbnail-Cache wurde erfolgreich geleert.",
        )
