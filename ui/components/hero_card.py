"""
Hero Channel Banner Card Component.
Displays the currently active/selected channel with Logo, Title, Category,
Live Telemetry Badges (Resolution, Codec, Bitrate, Audio, Buffer Health),
and Quick Action Buttons (Favorite, Probe Stream, Copy URL, Export M3U, Fullscreen).
"""
from __future__ import annotations

from typing import Optional
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

from core.models import Channel, StreamProbeResult


class HeroCard(QFrame):
    favorite_toggled = Signal()
    probe_requested = Signal()
    copy_url_requested = Signal()
    export_m3u_requested = Signal()
    fullscreen_requested = Signal()

    def __init__(self, logo_cache=None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("HeroCard")
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._logo_cache = logo_cache
        self._current_channel: Optional[Channel] = None
        self._full_title_text = "Kein Sender ausgewählt"
        self._full_cat_text = "Portal verbinden oder Sender wählen"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Logo Box
        self.lbl_logo = QLabel("TV")
        self.lbl_logo.setFixedSize(52, 52)
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_logo.setStyleSheet(
            "background-color: #0B101B; color: #818CF8; border: 1px solid #263554; border-radius: 10px;"
        )
        layout.addWidget(self.lbl_logo)

        # Right Column: Top Row (Title + Category + Quick Actions), Bottom Row (Full-Width Telemetry Pills)
        info_col = QVBoxLayout()
        info_col.setContentsMargins(0, 0, 0, 0)
        info_col.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.lbl_title = QLabel(self._full_title_text)
        self.lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #F8FAFC;")
        self.lbl_title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        top_row.addWidget(self.lbl_title)

        self.lbl_category = QLabel(self._full_cat_text)
        self.lbl_category.setStyleSheet(
            "background-color: #1E293B; color: #94A3B8; border-radius: 4px; "
            "padding: 2px 7px; font-size: 11px; font-weight: 600;"
        )
        self.lbl_category.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        top_row.addWidget(self.lbl_category)
        top_row.addStretch(1)

        # Quick Actions in top-right so telemetry pills below get 100% width
        actions_row = QHBoxLayout()
        actions_row.setSpacing(5)

        self.btn_fav = QPushButton("☆")
        self.btn_fav.setObjectName("IconButton")
        self.btn_fav.setFixedSize(30, 28)
        self.btn_fav.setToolTip("Als Favorit markieren [F2]")
        self.btn_fav.clicked.connect(self.favorite_toggled.emit)
        actions_row.addWidget(self.btn_fav)

        self.btn_probe = QPushButton("🔍 Probe")
        self.btn_probe.setProperty("compact", "true")
        self.btn_probe.setFixedHeight(28)
        self.btn_probe.setToolTip("Stream-Codec, PCR-Bitrate & Header analysieren")
        self.btn_probe.clicked.connect(self.probe_requested.emit)
        actions_row.addWidget(self.btn_probe)

        self.btn_copy_url = QPushButton("📋 URL")
        self.btn_copy_url.setProperty("compact", "true")
        self.btn_copy_url.setFixedHeight(28)
        self.btn_copy_url.setToolTip("Aufgelöste Stream-URL in Zwischenablage kopieren")
        self.btn_copy_url.clicked.connect(self.copy_url_requested.emit)
        actions_row.addWidget(self.btn_copy_url)

        self.btn_export_m3u = QPushButton("💾 .M3U8")
        self.btn_export_m3u.setProperty("compact", "true")
        self.btn_export_m3u.setFixedHeight(28)
        self.btn_export_m3u.setToolTip("Aktuelle Senderliste / Kategorie als .m3u8 exportieren")
        self.btn_export_m3u.clicked.connect(self.export_m3u_requested.emit)
        actions_row.addWidget(self.btn_export_m3u)

        top_row.addLayout(actions_row)
        info_col.addLayout(top_row)

        # Full-Width Telemetry Pills Row with Responsive Sizing
        pills_row = QHBoxLayout()
        pills_row.setContentsMargins(0, 0, 0, 0)
        pills_row.setSpacing(5)

        self.pill_res = self._make_pill("Auflösung: —", "#1E1B4B", "#A5B4FC")
        self.pill_codec = self._make_pill("Video: —", "#083344", "#67E8F9")
        self.pill_bitrate = self._make_pill("Bitrate: —", "#064E3B", "#6EE7B7")
        self.pill_audio = self._make_pill("Audio: —", "#1E293B", "#CBD5E1")
        self.pill_buffer = self._make_pill("Bereit", "#312E81", "#C7D2FE")

        for p in (self.pill_res, self.pill_codec, self.pill_bitrate, self.pill_audio, self.pill_buffer):
            pills_row.addWidget(p)
        pills_row.addStretch(1)
        info_col.addLayout(pills_row)

        layout.addLayout(info_col, 1)

    @staticmethod
    def _make_pill(text: str, bg: str, fg: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        lbl.setMinimumHeight(20)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border-radius: 4px; "
            f"padding: 1px 6px; font-family: 'Consolas', 'Segoe UI', monospace; font-size: 10px; font-weight: bold;"
        )
        return lbl

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self._elide_header_labels()

    def _elide_header_labels(self):
        avail = max(140, self.width() - 360)
        title_max = max(100, int(avail * 0.62))
        cat_max = max(80, int(avail * 0.38))
        fm_t = QFontMetrics(self.lbl_title.font())
        fm_c = QFontMetrics(self.lbl_category.font())
        self.lbl_title.setText(fm_t.elidedText(self._full_title_text, Qt.TextElideMode.ElideRight, title_max))
        self.lbl_title.setToolTip(self._full_title_text)
        self.lbl_category.setText(fm_c.elidedText(self._full_cat_text, Qt.TextElideMode.ElideRight, cat_max))
        self.lbl_category.setToolTip(self._full_cat_text)

    def set_channel(self, channel: Optional[Channel], genre_name: str = "Live TV", is_fav: bool = False):
        self._current_channel = channel
        if not channel:
            self._full_title_text = "Kein Sender ausgewählt"
            self._full_cat_text = "Bereit"
            self._elide_header_labels()
            self.lbl_logo.setPixmap(QLabel().pixmap())
            self.lbl_logo.setText("TV")
            self.btn_fav.setText("☆")
            return

        num_prefix = f"#{channel.number}  " if channel.number else ""
        self._full_title_text = f"{num_prefix}{channel.name}"
        self._full_cat_text = f"{genre_name}  {channel.flags_summary}".strip()
        self._elide_header_labels()
        self.set_favorite_state(is_fav)

        if channel.quality_tag:
            self.pill_res.setText(f"Tag: {channel.quality_tag}")
        else:
            self.pill_res.setText("Auflösung: —")
        self.pill_codec.setText("Video: —")
        self.pill_bitrate.setText("Bitrate: —")
        self.pill_audio.setText("Audio: —")

        # Load cached logo or monogram
        pixmap = None
        if self._logo_cache and channel.logo:
            pixmap = self._logo_cache.get_pixmap(channel.logo, 46, 46)
        if pixmap and not pixmap.isNull():
            self.lbl_logo.setText("")
            self.lbl_logo.setPixmap(pixmap)
        else:
            self.lbl_logo.clear()
            monogram = "".join([w[0] for w in channel.name.split()[:2] if w]).upper() or "TV"
            self.lbl_logo.setText(monogram[:3])

    def set_favorite_state(self, is_fav: bool):
        self.btn_fav.setText("★" if is_fav else "☆")
        self.btn_fav.setStyleSheet(
            "color: #F59E0B; font-size: 15px; padding: 0px;"
            if is_fav
            else "color: #94A3B8; font-size: 15px; padding: 0px;"
        )

    def update_probe_telemetry(self, probe: StreamProbeResult):
        if not probe.is_alive:
            code_txt = f"HTTP {probe.status_code}" if probe.status_code else "Timeout"
            self.pill_res.setText(code_txt)
            self.pill_res.setStyleSheet(
                "background-color: #78350F; color: #FCD34D; border-radius: 4px; padding: 1px 6px; font-weight: bold;"
                if probe.status_code in (456, 407, 459, 511)
                else "background-color: #7F1D1D; color: #FCA5A5; border-radius: 4px; padding: 1px 6px; font-weight: bold;"
            )
            diag_short = (
                "Geo-Lock / ISP" if probe.status_code == 456
                else "Proxy nötig (407)" if probe.status_code == 407
                else "Line belegt (459)" if probe.status_code == 459
                else "Deaktiviert (458)" if probe.status_code == 458
                else "Auth Fehler (511)" if probe.status_code == 511
                else probe.error_msg[:24]
            )
            self.pill_codec.setText(f"Diagnose: {diag_short}")
            self.pill_bitrate.setText("Bitrate: —")
            self.pill_audio.setText("Audio: —")
            self.pill_buffer.setText(f"Status: {code_txt}")
            self.pill_buffer.setStyleSheet(
                "background-color: #78350F; color: #FCD34D; border-radius: 4px; padding: 1px 6px; font-weight: bold;"
                if probe.status_code in (456, 407, 459, 511)
                else "background-color: #7F1D1D; color: #FCA5A5; border-radius: 4px; padding: 1px 6px; font-weight: bold;"
            )
            return

        self.pill_res.setStyleSheet(
            "background-color: #1E293B; color: #F8FAFC; border-radius: 4px; "
            "padding: 1px 6px; font-family: 'Consolas', 'Segoe UI', monospace; font-size: 10px; font-weight: bold;"
        )
        if probe.width and probe.height:
            fps = f" @{probe.fps:.0f}fps" if probe.fps > 0 else ""
            self.pill_res.setText(f"{probe.width}x{probe.height}{fps}")
        if probe.video_codec:
            self.pill_codec.setText(f"Video: {probe.video_codec.upper()}")
        elif probe.content_type:
            self.pill_codec.setText(probe.content_type.split(";")[0][:22])
        if probe.bitrate_kbps > 0:
            mbps = probe.bitrate_kbps / 1000.0
            self.pill_bitrate.setText(f"{mbps:.2f} Mbps")
        if probe.audio_codec:
            ch_str = f" ({probe.audio_channels}ch)" if probe.audio_channels else ""
            self.pill_audio.setText(f"Audio: {probe.audio_codec.upper()}{ch_str}")
        self.pill_buffer.setText(f"Puffer: {probe.buffer_health}")

    def update_live_telemetry(
        self,
        width: int,
        height: int,
        bitrate_kbps: int,
        buffer_text: str = "",
        fps: float = 0.0,
        video_codec: str = "",
        audio_codec: str = "",
        audio_channels: int = 0,
    ):
        if width > 0 and height > 0:
            fps_s = f" @{fps:.0f}fps" if fps > 0 else ""
            self.pill_res.setText(f"{width}x{height}{fps_s}")
        if bitrate_kbps > 0:
            self.pill_bitrate.setText(f"{bitrate_kbps / 1000.0:.2f} Mbps")
        if buffer_text:
            self.pill_buffer.setText(buffer_text)
            if "⏳" in buffer_text:
                self.pill_buffer.setStyleSheet(
                    "background-color: #312E81; color: #C7D2FE; border-radius: 4px; "
                    "padding: 1px 6px; font-family: 'Consolas', 'Segoe UI', monospace; font-size: 10px; font-weight: bold;"
                )
            else:
                self.pill_buffer.setStyleSheet(
                    "background-color: #064E3B; color: #6EE7B7; border-radius: 4px; "
                    "padding: 1px 6px; font-family: 'Consolas', 'Segoe UI', monospace; font-size: 10px; font-weight: bold;"
                )
        if video_codec:
            self.pill_codec.setText(f"Video: {video_codec}")
        if audio_codec:
            ch_s = f" ({audio_channels}ch)" if audio_channels else ""
            self.pill_audio.setText(f"Audio: {audio_codec}{ch_s}")
