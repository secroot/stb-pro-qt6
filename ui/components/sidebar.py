"""
Collapsible Left Sidebar Widget.
Manages Scan-Profiles & Hosts from 'mac_scans/' (Host selection, MAC login selection, Live Hit details),
Quick Connection override, Player Engine selection, Prebuffer preset, Timeout, UI Scaling,
and Connect/Disconnect action.
"""
from __future__ import annotations

import os
import subprocess
import sys
from typing import Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.models import Profile
from core.scan_repository import ScanRepository, ScanHost, ScanAccount


class SidebarWidget(QFrame):
    host_selected = Signal(str)                         # host_name
    account_selected = Signal(str, str)                 # host_name, mac
    profile_selected = Signal(str)                      # backward compatibility
    reload_scans_requested = Signal()
    connect_requested = Signal()
    disconnect_requested = Signal()
    quick_fields_changed = Signal(str, str, str)        # url, mac, proxy
    player_engine_changed = Signal(str)
    prebuffer_preset_changed = Signal(str)
    timeout_changed = Signal(int)
    ui_scale_changed = Signal(str)
    mac_db_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setMinimumWidth(260)
        self.setMaximumWidth(450)
        self._is_connected = False
        self._updating = False
        self._scan_repo: Optional[ScanRepository] = None
        self._current_host: Optional[ScanHost] = None
        self._current_account: Optional[ScanAccount] = None

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scrollable upper settings area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(3)

        # ── 1. SCAN-PROFILE & HOSTS CARD ──
        prof_card = QFrame()
        prof_card.setObjectName("CardFrame")
        prof_lay = QVBoxLayout(prof_card)
        prof_lay.setContentsMargins(6, 4, 6, 4)
        prof_lay.setSpacing(2)

        lbl_prof = QLabel("🌐 PORTALE & SCAN-PROFILE")
        lbl_prof.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_prof.setStyleSheet("color: #818CF8;")
        prof_lay.addWidget(lbl_prof)

        # 1. Host / Scan-Datei Dropdown
        self.combo_hosts = QComboBox()
        self.combo_hosts.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo_hosts.setMinimumContentsLength(14)
        self.combo_hosts.currentIndexChanged.connect(self._on_host_index_changed)
        prof_lay.addWidget(self.combo_hosts)

        # Buttons unter Host-Auswahl: Neu laden & Ordner öffnen
        btn_host_row = QHBoxLayout()
        btn_host_row.setSpacing(4)

        self.btn_reload_scans = QPushButton("🔄 Neu laden")
        self.btn_reload_scans.setProperty("compact", "true")
        self.btn_reload_scans.setFixedHeight(22)
        self.btn_reload_scans.setToolTip("Ordner mac_scans/ neu durchsuchen und Host-Dateien einlesen")
        self.btn_reload_scans.clicked.connect(self.reload_scans_requested.emit)
        btn_host_row.addWidget(self.btn_reload_scans, 1)

        self.btn_open_scans = QPushButton("📂 Ordner")
        self.btn_open_scans.setProperty("compact", "true")
        self.btn_open_scans.setFixedHeight(22)
        self.btn_open_scans.setToolTip("Ordner 'mac_scans' im Explorer öffnen")
        self.btn_open_scans.clicked.connect(self._open_scans_folder)
        btn_host_row.addWidget(self.btn_open_scans, 0)

        prof_lay.addLayout(btn_host_row)

        # 2. Login / MAC Dropdown
        self.combo_logins = QComboBox()
        self.combo_logins.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo_logins.setMinimumContentsLength(16)
        self.combo_logins.currentIndexChanged.connect(self._on_login_index_changed)
        prof_lay.addWidget(self.combo_logins)

        # 3. Account-Details Info-Karte
        self.info_card = QFrame()
        self.info_card.setStyleSheet(
            "background-color: #0B1120; border: 1px solid #1E293B; border-radius: 6px;"
        )
        info_lay = QVBoxLayout(self.info_card)
        info_lay.setContentsMargins(6, 4, 6, 4)
        info_lay.setSpacing(2)

        row_a = QHBoxLayout()
        row_a.setContentsMargins(0, 0, 0, 0)
        self.lbl_acc_status = QLabel("🟢 Aktiv")
        self.lbl_acc_status.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")
        self.lbl_acc_channels = QLabel("0 Kanäle")
        self.lbl_acc_channels.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 11px;")
        row_a.addWidget(self.lbl_acc_status)
        row_a.addStretch(1)
        row_a.addWidget(self.lbl_acc_channels)
        info_lay.addLayout(row_a)

        self.lbl_acc_expire = QLabel("Ablauf: -")
        self.lbl_acc_expire.setStyleSheet("color: #CBD5E1; font-size: 10px;")
        info_lay.addWidget(self.lbl_acc_expire)

        self.lbl_acc_scandate = QLabel("Scan: -")
        self.lbl_acc_scandate.setStyleSheet("color: #64748B; font-size: 10px;")
        info_lay.addWidget(self.lbl_acc_scandate)

        prof_lay.addWidget(self.info_card)

        # Abwärtskompatibles verstecktes/Fallback profile combo für bestehende Tests/Slots
        self.combo_profiles = self.combo_hosts

        layout.addWidget(prof_card)

        # ── 2. QUICK CONNECTION CARD ──
        conn_card = QFrame()
        conn_card.setObjectName("CardFrame")
        conn_lay = QVBoxLayout(conn_card)
        conn_lay.setContentsMargins(6, 4, 6, 4)
        conn_lay.setSpacing(2)

        lbl_conn = QLabel("⚡ SCHNELLVERBINDUNG")
        lbl_conn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_conn.setStyleSheet("color: #38BDF8;")
        conn_lay.addWidget(lbl_conn)

        conn_lay.addWidget(QLabel("Portal / Server URL:"))
        self.entry_url = QLineEdit()
        self.entry_url.setPlaceholderText("http://portal.example.com/c/")
        self.entry_url.editingFinished.connect(self._emit_quick_fields)
        conn_lay.addWidget(self.entry_url)

        self.lbl_mac_or_user = QLabel("MAC-Adresse:")
        conn_lay.addWidget(self.lbl_mac_or_user)
        self.entry_mac = QLineEdit()
        self.entry_mac.setPlaceholderText("00:1A:79:XX:XX:XX")
        self.entry_mac.editingFinished.connect(self._emit_quick_fields)
        conn_lay.addWidget(self.entry_mac)

        conn_lay.addWidget(QLabel("HTTP / SOCKS5 Proxy (optional):"))
        self.entry_proxy = QLineEdit()
        self.entry_proxy.setPlaceholderText("socks5://127.0.0.1:9050")
        self.entry_proxy.editingFinished.connect(self._emit_quick_fields)
        conn_lay.addWidget(self.entry_proxy)

        self.btn_mac_db = QPushButton("🗄 MAC Hit-Datenbank öffnen")
        self.btn_mac_db.setFixedHeight(24)
        self.btn_mac_db.setProperty("compact", "true")
        self.btn_mac_db.clicked.connect(self.mac_db_requested.emit)
        conn_lay.addWidget(self.btn_mac_db)

        layout.addWidget(conn_card)

        # ── 3. PLAYBACK & ENGINE SETTINGS CARD ──
        eng_card = QFrame()
        eng_card.setObjectName("CardFrame")
        eng_lay = QVBoxLayout(eng_card)
        eng_lay.setContentsMargins(6, 4, 6, 4)
        eng_lay.setSpacing(2)

        lbl_eng = QLabel("🎛 ENGINE & SYSTEM")
        lbl_eng.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_eng.setStyleSheet("color: #10B981;")
        eng_lay.addWidget(lbl_eng)

        eng_lay.addWidget(QLabel("Video-Player Engine:"))
        self.combo_player = QComboBox()
        self.combo_player.addItems([
            "Integrierter Player",
            "Externer VLC",
            "Externer MPV",
            "Externer FFplay",
        ])
        self.combo_player.currentTextChanged.connect(self.player_engine_changed.emit)
        eng_lay.addWidget(self.combo_player)

        eng_lay.addWidget(QLabel("Stream-Prebuffer Profil:"))
        self.combo_prebuffer = QComboBox()
        self.combo_prebuffer.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo_prebuffer.setMinimumContentsLength(14)
        self.combo_prebuffer.addItems([
            "Aus (Direct VLC)",
            "Zapping (0.5 MB / 0.8s)",
            "Ausgewogen (1.5 MB / 1.5s)",
            "Stabil (4 MB / 2.5s)",
            "Maximal / Anti-Freeze (8 MB / 4s)",
        ])
        self.combo_prebuffer.currentTextChanged.connect(self.prebuffer_preset_changed.emit)
        eng_lay.addWidget(self.combo_prebuffer)

        row_bottom = QHBoxLayout()
        row_bottom.setSpacing(8)
        col_t = QVBoxLayout()
        col_t.setSpacing(3)
        col_t.addWidget(QLabel("Timeout:"))
        self.combo_timeout = QComboBox()
        self.combo_timeout.addItems(["5s", "8s", "10s", "15s", "25s", "30s"])
        self.combo_timeout.setCurrentText("10s")
        self.combo_timeout.setMinimumHeight(26)
        self.combo_timeout.currentTextChanged.connect(self._on_timeout_combo)
        col_t.addWidget(self.combo_timeout)
        row_bottom.addLayout(col_t, 1)

        col_s = QVBoxLayout()
        col_s.setSpacing(3)
        col_s.addWidget(QLabel("UI Zoom:"))
        self.combo_scale = QComboBox()
        self.combo_scale.addItems(["Auto", "90%", "100%", "110%", "120%", "130%"])
        self.combo_scale.setCurrentText("100%")
        self.combo_scale.setMinimumHeight(26)
        self.combo_scale.currentTextChanged.connect(self.ui_scale_changed.emit)
        col_s.addWidget(self.combo_scale)
        row_bottom.addLayout(col_s, 1)

        eng_lay.addLayout(row_bottom)
        layout.addWidget(eng_card)
        layout.addStretch(1)

        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)

        # ── 4. FIXED BOTTOM ACTION BAR ──
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet(
            "background-color: #090D16; border-top: 1px solid #1E293B;"
        )
        bottom_lay = QVBoxLayout(bottom_bar)
        bottom_lay.setContentsMargins(10, 8, 10, 8)
        bottom_lay.setSpacing(4)

        self.btn_connect = QPushButton("🚀 Portal Verbinden")
        self.btn_connect.setObjectName("PrimaryButton")
        self.btn_connect.setMinimumHeight(36)
        self.btn_connect.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_connect.clicked.connect(self._on_connect_btn_clicked)
        bottom_lay.addWidget(self.btn_connect)

        root_layout.addWidget(bottom_bar)

    # ══════════════════════════════════════════════════════════════════════
    # Scan-Repository & Dynamic Selection
    # ══════════════════════════════════════════════════════════════════════

    def load_scan_repository(
        self,
        repo: ScanRepository,
        default_host: str = "",
        default_mac: str = "",
    ):
        """Lädt alle Hosts und Logins aus dem Scan-Repository in die Comboboxen."""
        self._updating = True
        self._scan_repo = repo
        self.combo_hosts.clear()
        self.combo_logins.clear()

        hosts = repo.get_hosts()
        if not hosts:
            self.combo_hosts.addItem("Keine Scan-Dateien gefunden")
            self.combo_logins.addItem("Keine Logins verfügbar")
            self._updating = False
            return

        target_host_idx = 0
        for idx, h in enumerate(hosts):
            self.combo_hosts.addItem(h.display_label(), userData=h.host_name)
            if default_host and (h.host_name.lower() == default_host.lower() or default_host.lower() in h.file_name.lower()):
                target_host_idx = idx

        self.combo_hosts.setCurrentIndex(target_host_idx)
        self._updating = False

        # Befülle Logins für den gewählten Host
        self._populate_logins_for_host(hosts[target_host_idx], target_mac=default_mac)

    def _on_host_index_changed(self, index: int):
        if self._updating or index < 0 or not self._scan_repo:
            return
        host_name = self.combo_hosts.itemData(index)
        host = self._scan_repo.get_host(host_name)
        if host:
            self._current_host = host
            self._populate_logins_for_host(host)
            self.host_selected.emit(host.host_name)

    def _populate_logins_for_host(self, host: ScanHost, target_mac: str = ""):
        self._updating = True
        self._current_host = host
        self.combo_logins.clear()

        target_login_idx = 0
        for idx, acc in enumerate(host.accounts):
            self.combo_logins.addItem(acc.display_text(), userData=acc.mac)
            if target_mac and acc.mac.strip().upper() == target_mac.strip().upper():
                target_login_idx = idx

        if host.accounts:
            self.combo_logins.setCurrentIndex(target_login_idx)
            selected_acc = host.accounts[target_login_idx]
            self._apply_account_details(selected_acc, host)
        else:
            self.combo_logins.addItem("Keine Logins im Scan")
            self._clear_account_details()

        self._updating = False

        if host.accounts:
            acc = host.accounts[target_login_idx]
            self.account_selected.emit(host.host_name, acc.mac)
            self.profile_selected.emit(f"{host.host_name} ({acc.mac})")

    def _on_login_index_changed(self, index: int):
        if self._updating or index < 0 or not self._current_host:
            return
        mac = self.combo_logins.itemData(index)
        if not mac:
            return
        acc = self._current_host.accounts[index] if index < len(self._current_host.accounts) else None
        if acc:
            self._apply_account_details(acc, self._current_host)
            self.account_selected.emit(self._current_host.host_name, acc.mac)
            self.profile_selected.emit(f"{self._current_host.host_name} ({acc.mac})")

    def _apply_account_details(self, acc: ScanAccount, host: ScanHost):
        self._current_account = acc
        self.lbl_acc_status.setText(f"🟢 {acc.status or 'Aktiv'}")
        ch_formatted = f"{acc.channels:,} Kanäle".replace(",", ".") if acc.channels > 0 else "0 Kanäle"
        self.lbl_acc_channels.setText(ch_formatted)
        self.lbl_acc_expire.setText(f"Ablauf: {acc.expire or '-'}")
        self.lbl_acc_scandate.setText(f"Scan: {acc.scandate or '-'}")

        # Schnellverbindungs-Eingaben automatisch synchronisieren
        self._updating = True
        self.entry_url.setText(acc.portal_url or host.portal_url)
        self.entry_mac.setText(acc.mac)
        self._updating = False

    def _clear_account_details(self):
        self._current_account = None
        self.lbl_acc_status.setText("⚪ Keine Daten")
        self.lbl_acc_channels.setText("0 Kanäle")
        self.lbl_acc_expire.setText("Ablauf: -")
        self.lbl_acc_scandate.setText("Scan: -")

    def get_selected_account(self) -> Optional[ScanAccount]:
        return self._current_account

    def get_selected_host(self) -> Optional[ScanHost]:
        return self._current_host

    def _open_scans_folder(self):
        folder = self._scan_repo.get_scans_dir() if self._scan_repo else ""
        if not folder or not os.path.exists(folder):
            return
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════
    # Legacy Profile & Display Fallback
    # ══════════════════════════════════════════════════════════════════════

    def load_profiles(self, profiles: Dict[str, Profile], active_name: str):
        """Fallback für Abwärtskompatibilität."""
        pass

    def display_profile(self, profile: Profile):
        self._updating = True
        self.entry_url.setText(profile.url)
        self.entry_mac.setText(profile.mac or profile.username)
        self.entry_proxy.setText(profile.proxy)
        self._updating = False

    def set_connected_state(self, connected: bool, busy: bool = False):
        self._is_connected = connected
        self.btn_connect.setEnabled(not busy)
        if busy:
            self.btn_connect.setText("⏳ Verbinde...")
            self.btn_connect.setObjectName("WarningButton")
        elif connected:
            self.btn_connect.setText("🔌 Verbindung trennen")
            self.btn_connect.setObjectName("DangerButton")
        else:
            self.btn_connect.setText("🚀 Portal Verbinden")
            self.btn_connect.setObjectName("PrimaryButton")
        self.btn_connect.style().unpolish(self.btn_connect)
        self.btn_connect.style().polish(self.btn_connect)

    def _emit_quick_fields(self):
        if not self._updating:
            self.quick_fields_changed.emit(
                self.entry_url.text().strip(),
                self.entry_mac.text().strip(),
                self.entry_proxy.text().strip(),
            )

    def _on_timeout_combo(self, text: str):
        try:
            sec = int(text.replace("s", "").strip())
            self.timeout_changed.emit(sec)
        except Exception:
            pass

    def _on_connect_btn_clicked(self):
        self._emit_quick_fields()
        if self._is_connected:
            self.disconnect_requested.emit()
        else:
            self.connect_requested.emit()
