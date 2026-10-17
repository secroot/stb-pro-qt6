"""
Top Navigation & Status Bar Component.
Includes View Tabs, Provider Status Pill, REC Indicator, Jobs Badge, Buffer Config,
Sidebar Toggle, Cinema Mode Toggle, PiP Floating Player Toggle, and Fullscreen Toggle.
"""
from __future__ import annotations

from typing import Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QFontMetrics, QResizeEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class TopNavigationBar(QFrame):
    view_changed = Signal(str)           # "live", "vod", "scanner", "inspector", "console"
    sidebar_toggled = Signal()
    cinema_toggled = Signal()
    pip_toggled = Signal()
    fullscreen_requested = Signal()
    buffer_dialog_requested = Signal()
    jobs_dialog_requested = Signal()
    account_info_requested = Signal()
    record_stop_requested = Signal()
    vpn_switch_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setMinimumHeight(62)
        self._provider_connected = False
        self._provider_summary = "Nicht verbunden"

        root_vbox = QVBoxLayout(self)
        root_vbox.setContentsMargins(8, 4, 8, 4)
        root_vbox.setSpacing(3)

        # ─── TIER 1: Brand, Navigation Pills, REC Pill & Provider Status ───
        # ─── TIER 1: Primary Navigation Bar (Schön linksbündig: Brand Logo, Tabs, Status) ───
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(8)

        # App Brand Badge (schön linksbündig über dem Seitenleisten-Button)
        self.lbl_brand = QLabel("⚡ STB-EMU PRO")
        self.lbl_brand.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_brand.setStyleSheet("color: #F8FAFC; padding: 0 4px;")
        row1.addWidget(self.lbl_brand)

        row1.addSpacing(6)

        # Navigation Pills
        self._nav_buttons: Dict[str, QPushButton] = {}
        nav_items = [
            ("live", "📺 Live TV"),
            ("vod", "🎬 VOD & Serien"),
            ("scanner", "🎯 MAC Scanner"),
            ("inspector", "🔬 Inspector"),
            ("console", "🖥 Konsole"),
        ]
        for key, label in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("NavPill")
            btn.setProperty("active", "true" if key == "live" else "false")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked=False, k=key: self.set_active_view(k))
            row1.addWidget(btn)
            self._nav_buttons[key] = btn

        row1.addStretch(1)

        # Blinking REC Indicator button (expanded minimum width, generous padding so it never clips)
        self.btn_rec_indicator = QPushButton("🔴 REC 00:00")
        self.btn_rec_indicator.setObjectName("DangerButton")
        self.btn_rec_indicator.setMinimumWidth(125)
        self.btn_rec_indicator.setFixedHeight(28)
        self.btn_rec_indicator.setStyleSheet(
            "background-color: #991B1B; color: #FEE2E2; border: 1px solid #EF4444; "
            "border-radius: 6px; padding: 2px 10px; font-weight: bold; font-size: 11px;"
        )
        self.btn_rec_indicator.setToolTip("Aufnahme läuft – Klicken zum Beenden")
        self.btn_rec_indicator.setVisible(False)
        self.btn_rec_indicator.clicked.connect(self.record_stop_requested.emit)
        row1.addWidget(self.btn_rec_indicator)

        # Provider / Account Status Chip (clickable for Account JSON / Details)
        self.btn_provider_status = QPushButton("⚪ Nicht verbunden")
        self.btn_provider_status.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.btn_provider_status.setMinimumWidth(140)
        self.btn_provider_status.setMaximumWidth(420)
        self.btn_provider_status.setFixedHeight(28)
        self.btn_provider_status.setToolTip("Klicken für Account-/Handshake-Details")
        self.btn_provider_status.setStyleSheet(
            "background-color: #0F172A; color: #94A3B8; border: 1px solid #1E293B; "
            "border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: 600;"
        )
        self.btn_provider_status.clicked.connect(self.account_info_requested.emit)
        row1.addWidget(self.btn_provider_status)

        # NordVPN Status & Switcher Chip
        self.btn_vpn = QPushButton("🛡️ VPN: Bereit")
        self.btn_vpn.setObjectName("NavPill")
        self.btn_vpn.setFixedHeight(28)
        self.btn_vpn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_vpn.setStyleSheet(
            "background-color: #0F172A; color: #38BDF8; border: 1px solid #1E293B; "
            "border-radius: 6px; padding: 3px 8px; font-size: 11px; font-weight: 600;"
        )
        self.btn_vpn.setToolTip("NordVPN Status – Klicken zum Rotieren des VPN-Servers")
        self.btn_vpn.clicked.connect(self.vpn_switch_requested.emit)
        row1.addWidget(self.btn_vpn)

        root_vbox.addLayout(row1)

        # ─── TIER 2: Secondary Utility Sub-Bar (Left: Sidebar Toggle, Right: Shortcuts + Utility Buttons) ───
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(6)

        # Seitenleisten-Button: In die zweite Reihe linksbündig (direkt unter dem Logo)
        self.btn_sidebar = QPushButton("☰")
        self.btn_sidebar.setObjectName("IconButton")
        self.btn_sidebar.setFixedSize(32, 24)
        self.btn_sidebar.setToolTip("Seitenleiste ein-/ausblenden [B]")
        self.btn_sidebar.clicked.connect(self.sidebar_toggled.emit)
        row2.addWidget(self.btn_sidebar)

        row2.addStretch(1)

        # Shortcut Infos: Rechts neben / links vor den Jobs-Button geschoben
        self.lbl_hotkeys_hint = QLabel("⌨ Shortcuts: Leertaste: Play/Pause  •  F11: Vollbild  •  F2: Favorit  •  M: Stumm  •  A: Format  •  T: Kino  •  P: PiP")
        self.lbl_hotkeys_hint.setStyleSheet("color: #64748B; font-size: 10px; font-weight: 500; padding-right: 6px;")
        row2.addWidget(self.lbl_hotkeys_hint)

        # Right-aligned utility buttons
        self.btn_jobs = QPushButton("📥 Jobs (0)")
        self.btn_jobs.setProperty("compact", "true")
        self.btn_jobs.setFixedHeight(24)
        self.btn_jobs.setToolTip("Aufnahmen & Downloads verwalten")
        self.btn_jobs.clicked.connect(self.jobs_dialog_requested.emit)
        row2.addWidget(self.btn_jobs)

        self.btn_buffer = QPushButton("🛡 Puffer")
        self.btn_buffer.setProperty("compact", "true")
        self.btn_buffer.setFixedHeight(24)
        self.btn_buffer.setToolTip("Lokaler PCR-Ringpuffer & VLC-Netzwerk-Caching")
        self.btn_buffer.clicked.connect(self.buffer_dialog_requested.emit)
        row2.addWidget(self.btn_buffer)

        self.btn_pip = QPushButton("🗗 PiP")
        self.btn_pip.setProperty("compact", "true")
        self.btn_pip.setFixedHeight(24)
        self.btn_pip.setToolTip("Schwebender Mini-Player (Picture-in-Picture, Always-on-Top)")
        self.btn_pip.clicked.connect(self.pip_toggled.emit)
        row2.addWidget(self.btn_pip)

        self.btn_cinema = QPushButton("🍿 Kino")
        self.btn_cinema.setProperty("compact", "true")
        self.btn_cinema.setFixedHeight(24)
        self.btn_cinema.setToolTip("Kinomodus umschalten [T]")
        self.btn_cinema.clicked.connect(self.cinema_toggled.emit)
        row2.addWidget(self.btn_cinema)

        self.btn_fullscreen = QPushButton("⛶ Vollbild")
        self.btn_fullscreen.setObjectName("PrimaryButton")
        self.btn_fullscreen.setProperty("compact", "true")
        self.btn_fullscreen.setFixedHeight(24)
        self.btn_fullscreen.setToolTip("Echtes Vollbild mit HUD-Overlay [F11 / F]")
        self.btn_fullscreen.clicked.connect(self.fullscreen_requested.emit)
        row2.addWidget(self.btn_fullscreen)

        root_vbox.addLayout(row2)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        w = self.width()
        self.lbl_hotkeys_hint.setVisible(w >= 1180)
        self._update_provider_elide()

    def _update_provider_elide(self):
        prefix = "🟢 " if self._provider_connected else "⚪ "
        full_txt = f"{prefix}{self._provider_summary}"
        avail_w = max(140, min(420, self.width() - 640))
        self.btn_provider_status.setMaximumWidth(avail_w)
        fm = QFontMetrics(self.btn_provider_status.font())
        elided = fm.elidedText(full_txt, Qt.TextElideMode.ElideRight, avail_w - 24)
        self.btn_provider_status.setText(elided)
        self.btn_provider_status.setToolTip(f"{full_txt} — Klicken für Account-/Handshake-Details")

    def set_active_view(self, view_key: str):
        for k, btn in self._nav_buttons.items():
            btn.setProperty("active", "true" if k == view_key else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.view_changed.emit(view_key)

    def set_provider_status(self, connected: bool, summary: str):
        self._provider_connected = bool(connected)
        self._provider_summary = summary or ("Verbunden" if connected else "Nicht verbunden")
        if connected:
            self.btn_provider_status.setStyleSheet(
                "background-color: #064E3B; color: #A7F3D0; border: 1px solid #059669; "
                "border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 700;"
            )
        else:
            self.btn_provider_status.setStyleSheet(
                "background-color: #0F172A; color: #94A3B8; border: 1px solid #1E293B; "
                "border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 600;"
            )
        self._update_provider_elide()

    def update_jobs_badge(self, active_count: int, total_count: int):
        if active_count > 0:
            self.btn_jobs.setText(f"📥 Jobs ({active_count} aktiv)")
            self.btn_jobs.setStyleSheet(
                "background-color: #1E3A8A; color: #93C5FD; border: 1px solid #3B82F6; font-weight: 700;"
            )
        else:
            self.btn_jobs.setText(f"📥 Jobs ({total_count})")
            self.btn_jobs.setStyleSheet("")

    def update_rec_indicator(self, is_recording: bool, label_text: str = "🔴 REC"):
        self.btn_rec_indicator.setVisible(is_recording)
        if is_recording:
            self.btn_rec_indicator.setText(label_text)

    def update_vpn_badge(self, text: str, status: str = "connected"):
        self.btn_vpn.setText(text)
        if status == "connected":
            self.btn_vpn.setStyleSheet(
                "background-color: #064E3B; color: #6EE7B7; border: 1px solid #059669; "
                "border-radius: 6px; padding: 3px 8px; font-size: 11px; font-weight: 700;"
            )
        elif status == "switching":
            self.btn_vpn.setStyleSheet(
                "background-color: #78350F; color: #FDE68A; border: 1px solid #D97706; "
                "border-radius: 6px; padding: 3px 8px; font-size: 11px; font-weight: 700;"
            )
        elif status == "error":
            self.btn_vpn.setStyleSheet(
                "background-color: #7F1D1D; color: #FCA5A5; border: 1px solid #DC2626; "
                "border-radius: 6px; padding: 3px 8px; font-size: 11px; font-weight: 700;"
            )
        else:
            self.btn_vpn.setStyleSheet(
                "background-color: #0F172A; color: #94A3B8; border: 1px solid #1E293B; "
                "border-radius: 6px; padding: 3px 8px; font-size: 11px; font-weight: 600;"
            )
