"""
Live TV Split-Workspace View for STB Pro Qt6.
Combines the GPU-virtualized Channel List (QListView + ChannelListModel + ChannelFilterProxyModel + ChannelCardDelegate)
with the Hero Banner, Native Video Surface (LibVLC HWND + FFmpeg Standbild-Preview),
VOD/Catchup Seekbar, Audio/Subtitle/Aspect/Speed Controls, Multi-Thread Category Validator, and Live EPG Panel.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set
from PySide6.QtCore import QEvent, QModelIndex, QObject, QPoint, Qt, Signal, QTimer
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QKeyEvent,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPixmap,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMenu,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.models import Channel, EPGProgram, StreamProbeResult, quality_from_dimensions
from core.preview_grabber import load_cached_thumb
from ui.components.epg_panel import EPGPanel
from ui.components.hero_card import HeroCard
from ui.models.channel_model import (
    ChannelCardDelegate,
    ChannelFilterProxyModel,
    ChannelListModel,
    ChannelRoles,
)


class VideoSurfaceWidget(QFrame):
    """
    Dedicated native HWND container for LibVLC Direct3D11/OpenGL rendering.
    Emits double_clicked for instant fullscreen toggle and mouse_moved for HUD wake-up.
    Repaints solid black on stop to eliminate Direct3D swapchain ghosting or tab bleed-through.
    """
    double_clicked = Signal()
    mouse_moved = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.setMouseTracking(True)
        self.setAutoFillBackground(True)
        self.setStyleSheet("background-color: #000000; border: none;")

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#000000"))

    def clear_surface(self):
        self.update()
        self.repaint()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.mouse_moved.emit()
        super().mouseMoveEvent(event)


class PreviewOverlayWidget(QFrame):
    """
    Standbild-Preview Thumbnail Overlay displayed inside the video viewport when
    a channel is selected in the list but live playback is not active.
    Double-clicking starts playback of the selected channel.
    """
    play_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #000000; border: none;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._source_pixmap: Optional[QPixmap] = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.lbl_image = QLabel(self)
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.lbl_image.setStyleSheet("background-color: #000000; color: #94A3B8; font-size: 12px;")
        self.lbl_image.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        lay.addWidget(self.lbl_image, 1)

        self.lbl_overlay_tag = QLabel("📸 Standbild-Vorschau — Doppelklick zum Abspielen", self.lbl_image)
        self.lbl_overlay_tag.setStyleSheet(
            "background-color: rgba(10, 14, 23, 210); color: #38BDF8; "
            "border: 1px solid #1E293B; border-radius: 6px; padding: 4px 10px; "
            "font-size: 11px; font-weight: bold;"
        )
        self.lbl_overlay_tag.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.lbl_overlay_tag.move(12, 12)
        self.lbl_overlay_tag.adjustSize()

    def set_pixmap(self, pixmap: QPixmap, badge_text: str = ""):
        self._source_pixmap = pixmap
        tag = f"📸 {badge_text} — ▶ Doppelklick zum Abspielen" if badge_text else "📸 Standbild-Vorschau — ▶ Doppelklick zum Abspielen"
        self.lbl_overlay_tag.setText(tag)
        self.lbl_overlay_tag.adjustSize()
        self._rescale()

    def clear_pixmap(self):
        self._source_pixmap = None
        self.lbl_image.clear()

    def _rescale(self):
        if self._source_pixmap and not self._source_pixmap.isNull():
            sz = self.lbl_image.size()
            if sz.width() > 10 and sz.height() > 10:
                scaled = self._source_pixmap.scaled(
                    sz,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.lbl_image.setPixmap(scaled)
            else:
                self.lbl_image.setPixmap(self._source_pixmap)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self._rescale()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.play_requested.emit()
        super().mouseDoubleClickEvent(event)


class LiveTVView(QWidget):
    # Channel selection & playback signals
    channel_selected = Signal(object)              # (Channel) single click -> preview & EPG
    channel_play_requested = Signal(object)        # (Channel) double click or Enter -> play
    favorite_toggled = Signal(str)                 # (channel_id)
    probe_channel_requested = Signal(object)       # (Channel)
    copy_url_requested = Signal(object)            # (Channel)
    record_channel_requested = Signal(object)      # (Channel)
    export_m3u_requested = Signal(list)            # (List[Channel])
    raw_json_requested = Signal(str, dict)         # (title, raw_dict)
    epg_guide_requested = Signal(object)           # (Channel)

    # Category batch validation & thumbnail signals
    validate_category_requested = Signal(list)     # (List[Channel])
    fetch_group_thumbnails_requested = Signal(list)  # (List[Channel])
    stop_validation_requested = Signal()

    # Player transport signals
    prev_channel_requested = Signal()
    next_channel_requested = Signal()
    play_pause_requested = Signal()
    stop_requested = Signal()
    mute_toggled = Signal()
    volume_changed = Signal(int)
    aspect_ratio_changed = Signal(str)
    playback_speed_changed = Signal(float)
    audio_track_selected = Signal(int)
    subtitle_track_selected = Signal(int)
    seek_position_requested = Signal(float)        # 0.0 .. 1.0
    seek_relative_requested = Signal(int)          # delta_ms
    snapshot_requested = Signal()
    external_player_requested = Signal()
    cinema_mode_requested = Signal()
    pip_mode_requested = Signal()
    fullscreen_requested = Signal()
    video_mouse_moved = Signal()

    def __init__(self, logo_cache=None, parent: QWidget | None = None):
        super().__init__(parent)
        self._logo_cache = logo_cache
        self._genre_map: Dict[str, str] = {}
        self._selected_channel: Optional[Channel] = None
        self._is_seeking: bool = False
        self._validation_running: bool = False
        self._checked_groups_session: Set[str] = set()
        self._player_state: str = "stopped"
        self._requested_thumb_ids: Set[str] = set()
        self._visible_thumbs_timer = QTimer(self)
        self._visible_thumbs_timer.setSingleShot(True)
        self._visible_thumbs_timer.setInterval(350)
        self._visible_thumbs_timer.timeout.connect(self._check_visible_thumbnails)

        if self._logo_cache:
            self._logo_cache.logo_ready.connect(self._on_logo_ready)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # ══════════════════════════════════════════════════════════════════
        # LEFT PANEL: Virtualized Channel Browser + Filters + Validator
        # ══════════════════════════════════════════════════════════════════
        self.left_panel = QFrame()
        self.left_panel.setObjectName("CardFrame")
        self.left_panel.setMinimumWidth(320)
        left_lay = QVBoxLayout(self.left_panel)
        left_lay.setContentsMargins(10, 10, 10, 10)
        left_lay.setSpacing(7)

        # 1. Search Input + Category Dropdown
        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        self.entry_search = QLineEdit()
        self.entry_search.setPlaceholderText("🔍 Sender, Nr. oder EPG suchen... [Ctrl+F]")
        self.entry_search.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self.entry_search, 1)

        self.btn_clear_search = QPushButton("✕")
        self.btn_clear_search.setObjectName("IconButton")
        self.btn_clear_search.setFixedSize(28, 28)
        self.btn_clear_search.setToolTip("Suche zurücksetzen")
        self.btn_clear_search.clicked.connect(lambda: self.entry_search.clear())
        search_row.addWidget(self.btn_clear_search)
        left_lay.addLayout(search_row)

        cat_row = QHBoxLayout()
        cat_row.setSpacing(6)
        lbl_grp = QLabel("📂 Gruppe:")
        lbl_grp.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        cat_row.addWidget(lbl_grp)
        self.combo_category = QComboBox()
        self.combo_category.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo_category.setMinimumContentsLength(14)
        self.combo_category.addItem("Alle Kategorien", "*")
        self.combo_category.currentIndexChanged.connect(self._on_category_changed)
        cat_row.addWidget(self.combo_category, 1)
        left_lay.addLayout(cat_row)

        # 2. Quick Filter Mode Pills (ALL, FAV, RECENT, HD)
        pills_row = QHBoxLayout()
        pills_row.setSpacing(3)
        self._mode_buttons: Dict[str, QPushButton] = {}
        for mode_key, label in (
            ("ALL", "📺 Alle"),
            ("FAV", "★ Fav."),
            ("RECENT", "🕘 Verlauf"),
            ("HD", "✨ HD/4K"),
        ):
            btn = QPushButton(label)
            btn.setObjectName("FilterPill")
            btn.setCheckable(True)
            btn.setChecked(mode_key == "ALL")
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, m=mode_key: self._set_mode_filter(m))
            pills_row.addWidget(btn)
            self._mode_buttons[mode_key] = btn
        left_lay.addLayout(pills_row)

        # 3. Multi-Thread Category Health Validator Bar
        val_row = QHBoxLayout()
        val_row.setSpacing(4)

        self.btn_validate = QPushButton("🩺 Gruppe prüfen")
        self.btn_validate.setProperty("compact", "true")
        self.btn_validate.setFixedHeight(24)
        self.btn_validate.setToolTip("Prüft alle sichtbaren Sender der Gruppe (3s Timeout) und ermittelt echte Video-Metadaten")
        self.btn_validate.clicked.connect(self._on_validate_clicked)
        val_row.addWidget(self.btn_validate)

        self.chk_hide_dead = QCheckBox("Tote ausbl.")
        self.chk_hide_dead.setToolTip("Als offline markierte Sender automatisch ausblenden")
        self.chk_hide_dead.setChecked(False)
        self.chk_hide_dead.toggled.connect(self._on_hide_dead_toggled)
        val_row.addWidget(self.chk_hide_dead)

        self.btn_reset_dead = QPushButton("↺")
        self.btn_reset_dead.setObjectName("IconButton")
        self.btn_reset_dead.setFixedSize(24, 24)
        self.btn_reset_dead.setToolTip("Alle als offline markierten Sender wiederherstellen")
        self.btn_reset_dead.clicked.connect(self._on_reset_dead)
        val_row.addWidget(self.btn_reset_dead)

        val_row.addStretch(1)
        self.lbl_channel_count = QLabel("0 Sender")
        self.lbl_channel_count.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600;")
        val_row.addWidget(self.lbl_channel_count)
        left_lay.addLayout(val_row)

        self.val_progress = QProgressBar()
        self.val_progress.setObjectName("ValidationProgressBar")
        self.val_progress.setFixedHeight(18)
        self.val_progress.setTextVisible(True)
        self.val_progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.val_progress.setVisible(False)
        left_lay.addWidget(self.val_progress)

        # 4. GPU-Virtualized QListView
        self.channel_model = ChannelListModel(self)
        self.proxy_model = ChannelFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.channel_model)
        self.proxy_model.set_hide_dead(False)

        self.delegate = ChannelCardDelegate(logo_cache=self._logo_cache, parent=self)
        self.delegate.favorite_clicked.connect(self.favorite_toggled.emit)

        self.list_view = QListView()
        self.list_view.setModel(self.proxy_model)
        self.list_view.setItemDelegate(self.delegate)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setMouseTracking(True)
        self.list_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.list_view.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self._show_context_menu)
        self.list_view.clicked.connect(self._on_list_clicked)
        self.list_view.doubleClicked.connect(self._on_list_double_clicked)
        self.list_view.selectionModel().currentChanged.connect(self._on_list_current_changed)
        self.list_view.installEventFilter(self)
        self.list_view.viewport().installEventFilter(self)
        self.list_view.verticalScrollBar().valueChanged.connect(lambda: self._visible_thumbs_timer.start(350))
        left_lay.addWidget(self.list_view, 1)

        self.splitter.addWidget(self.left_panel)

        # ══════════════════════════════════════════════════════════════════
        # RIGHT PANEL: Hero Banner + Video Viewport + Transport + EPG
        # ══════════════════════════════════════════════════════════════════
        self.right_panel = QWidget()
        self.right_panel.setMinimumWidth(480)
        right_lay = QVBoxLayout(self.right_panel)
        right_lay.setContentsMargins(8, 0, 0, 0)
        right_lay.setSpacing(6)

        # 1. Hero Channel Card
        self.hero_card = HeroCard(logo_cache=self._logo_cache, parent=self)
        self.hero_card.favorite_toggled.connect(self._on_hero_fav_clicked)
        self.hero_card.probe_requested.connect(self._on_hero_probe_clicked)
        self.hero_card.copy_url_requested.connect(self._on_hero_copy_clicked)
        self.hero_card.export_m3u_requested.connect(self._on_export_visible_m3u)
        self.hero_card.fullscreen_requested.connect(self.fullscreen_requested.emit)
        right_lay.addWidget(self.hero_card)

        # 2. Video Viewport Frame (houses Native Surface + Standbild Preview Overlay + Status Bar)
        self.video_frame = QFrame()
        self.video_frame.setObjectName("CardFrame")
        self.video_frame.setStyleSheet(
            "QFrame#CardFrame { background-color: #000000; border: 1px solid #1E293B; border-radius: 10px; }"
        )
        video_lay = QVBoxLayout(self.video_frame)
        video_lay.setContentsMargins(2, 2, 2, 2)
        video_lay.setSpacing(0)

        self.video_surface = VideoSurfaceWidget(self.video_frame)
        self.video_surface.setMinimumHeight(240)
        self.video_surface.double_clicked.connect(self.fullscreen_requested.emit)
        self.video_surface.mouse_moved.connect(self.video_mouse_moved.emit)
        video_lay.addWidget(self.video_surface, 1)

        self.preview_overlay = PreviewOverlayWidget(self.video_frame)
        self.preview_overlay.setMinimumHeight(240)
        self.preview_overlay.setVisible(False)
        self.preview_overlay.play_requested.connect(self._on_preview_play_clicked)
        video_lay.addWidget(self.preview_overlay, 1)

        # Standbild Preview / Buffering Status Bar at bottom of video frame
        self.preview_bar = QFrame(self.video_frame)
        self.preview_bar.setFixedHeight(26)
        self.preview_bar.setStyleSheet("background-color: #080C14; border-top: 1px solid #162032;")
        prev_lay = QHBoxLayout(self.preview_bar)
        prev_lay.setContentsMargins(10, 2, 10, 2)
        prev_lay.setSpacing(8)

        self.lbl_video_status = QLabel("⏹ Bereit – Doppelklick auf einen Sender startet die Wiedergabe")
        self.lbl_video_status.setStyleSheet("color: #94A3B8; font-size: 11px;")
        self.lbl_video_status.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        prev_lay.addWidget(self.lbl_video_status, 1)

        self.lbl_preview_badge = QLabel("")
        self.lbl_preview_badge.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 600;")
        self.lbl_preview_badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        prev_lay.addWidget(self.lbl_preview_badge)
        video_lay.addWidget(self.preview_bar)

        right_lay.addWidget(self.video_frame, 1)

        # 3. Transport, Seekbar & Track Controls Card (Responsive 2-Row Layout)
        self.controls_card = QFrame()
        self.controls_card.setObjectName("CardFrame")
        ctrl_lay = QVBoxLayout(self.controls_card)
        ctrl_lay.setContentsMargins(10, 6, 10, 6)
        ctrl_lay.setSpacing(5)

        # VOD / Catchup Seek Row (hidden unless stream is seekable or VOD)
        self.seek_widget = QWidget()
        seek_lay = QHBoxLayout(self.seek_widget)
        seek_lay.setContentsMargins(0, 0, 0, 0)
        seek_lay.setSpacing(6)

        btn_back30 = QPushButton("⏪ -30s")
        btn_back30.setProperty("compact", "true")
        btn_back30.setFixedHeight(24)
        btn_back30.clicked.connect(lambda: self.seek_relative_requested.emit(-30000))
        seek_lay.addWidget(btn_back30)

        btn_back10 = QPushButton("-10s")
        btn_back10.setProperty("compact", "true")
        btn_back10.setFixedHeight(24)
        btn_back10.clicked.connect(lambda: self.seek_relative_requested.emit(-10000))
        seek_lay.addWidget(btn_back10)

        self.slider_seek = QSlider(Qt.Orientation.Horizontal)
        self.slider_seek.setRange(0, 1000)
        self.slider_seek.sliderPressed.connect(self._on_seek_pressed)
        self.slider_seek.sliderReleased.connect(self._on_seek_released)
        seek_lay.addWidget(self.slider_seek, 1)

        btn_fwd10 = QPushButton("+10s")
        btn_fwd10.setProperty("compact", "true")
        btn_fwd10.setFixedHeight(24)
        btn_fwd10.clicked.connect(lambda: self.seek_relative_requested.emit(10000))
        seek_lay.addWidget(btn_fwd10)

        btn_fwd30 = QPushButton("+30s ⏩")
        btn_fwd30.setProperty("compact", "true")
        btn_fwd30.setFixedHeight(24)
        btn_fwd30.clicked.connect(lambda: self.seek_relative_requested.emit(30000))
        seek_lay.addWidget(btn_fwd30)

        self.lbl_seek_time = QLabel("00:00 / 00:00")
        self.lbl_seek_time.setStyleSheet("color: #CBD5E1; font-family: Consolas; font-size: 11px;")
        seek_lay.addWidget(self.lbl_seek_time)

        self.combo_speed = QComboBox()
        self.combo_speed.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.combo_speed.setCurrentText("1.0x")
        self.combo_speed.setMinimumWidth(68)
        self.combo_speed.setMaximumWidth(80)
        self.combo_speed.currentTextChanged.connect(self._on_speed_changed)
        seek_lay.addWidget(self.combo_speed)

        self.seek_widget.setVisible(False)
        ctrl_lay.addWidget(self.seek_widget)

        # Row 1: Primary Transport + Volume + Recording / Viewport Actions
        trans_row = QHBoxLayout()
        trans_row.setSpacing(4)

        self.btn_prev = QPushButton("⏮")
        self.btn_prev.setObjectName("IconButton")
        self.btn_prev.setFixedSize(30, 26)
        self.btn_prev.setToolTip("Vorheriger Sender [PgUp]")
        self.btn_prev.clicked.connect(self.prev_channel_requested.emit)
        trans_row.addWidget(self.btn_prev)

        self.btn_play_pause = QPushButton("▶ Play")
        self.btn_play_pause.setObjectName("SuccessButton")
        self.btn_play_pause.setProperty("compact", "true")
        self.btn_play_pause.setMinimumWidth(64)
        self.btn_play_pause.setFixedHeight(26)
        self.btn_play_pause.setToolTip("Wiedergabe / Pause [Leertaste]")
        self.btn_play_pause.clicked.connect(self.play_pause_requested.emit)
        trans_row.addWidget(self.btn_play_pause)

        self.btn_stop = QPushButton("⏹")
        self.btn_stop.setObjectName("DangerButton")
        self.btn_stop.setProperty("compact", "true")
        self.btn_stop.setFixedSize(30, 26)
        self.btn_stop.setToolTip("Stopp [S]")
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        trans_row.addWidget(self.btn_stop)

        self.btn_next = QPushButton("⏭")
        self.btn_next.setObjectName("IconButton")
        self.btn_next.setFixedSize(30, 26)
        self.btn_next.setToolTip("Nächster Sender [PgDn]")
        self.btn_next.clicked.connect(self.next_channel_requested.emit)
        trans_row.addWidget(self.btn_next)

        self.btn_mute = QPushButton("🔊")
        self.btn_mute.setObjectName("IconButton")
        self.btn_mute.setFixedSize(30, 26)
        self.btn_mute.setToolTip("Stummschalten [M]")
        self.btn_mute.clicked.connect(self.mute_toggled.emit)
        trans_row.addWidget(self.btn_mute)

        self.slider_volume = QSlider(Qt.Orientation.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(100)
        self.slider_volume.setMinimumWidth(55)
        self.slider_volume.setMaximumWidth(100)
        self.slider_volume.valueChanged.connect(self._on_volume_slider)
        trans_row.addWidget(self.slider_volume)

        self.lbl_volume = QLabel("100%")
        self.lbl_volume.setMinimumWidth(32)
        self.lbl_volume.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_volume.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600;")
        trans_row.addWidget(self.lbl_volume)

        trans_row.addStretch(1)

        # Record, Snapshot, External Player, Cinema, PiP, Fullscreen
        self.btn_record = QPushButton("🔴 REC")
        self.btn_record.setProperty("compact", "true")
        self.btn_record.setFixedHeight(26)
        self.btn_record.setToolTip("Aktuellen Stream direkt aufnehmen [R]")
        self.btn_record.clicked.connect(self._on_record_clicked)
        trans_row.addWidget(self.btn_record)

        self.btn_snap = QPushButton("📸")
        self.btn_snap.setObjectName("IconButton")
        self.btn_snap.setFixedSize(30, 26)
        self.btn_snap.setToolTip("Screenshot speichern")
        self.btn_snap.clicked.connect(self.snapshot_requested.emit)
        trans_row.addWidget(self.btn_snap)

        self.btn_ext = QPushButton("↗ Ext.")
        self.btn_ext.setProperty("compact", "true")
        self.btn_ext.setFixedHeight(26)
        self.btn_ext.setToolTip("Stream im externen Player (VLC / MPV / FFplay) öffnen")
        self.btn_ext.clicked.connect(self.external_player_requested.emit)
        self.btn_detach = self.btn_ext
        trans_row.addWidget(self.btn_ext)

        self.btn_cinema = QPushButton("🎭")
        self.btn_cinema.setObjectName("IconButton")
        self.btn_cinema.setFixedSize(30, 26)
        self.btn_cinema.setToolTip("Kino-Modus (Cinema) umschalten [T]")
        self.btn_cinema.clicked.connect(self.cinema_mode_requested.emit)
        trans_row.addWidget(self.btn_cinema)

        self.btn_pip = QPushButton("🗔")
        self.btn_pip.setObjectName("IconButton")
        self.btn_pip.setFixedSize(30, 26)
        self.btn_pip.setToolTip("Mini-Player (PiP) umschalten [P]")
        self.btn_pip.clicked.connect(self.pip_mode_requested.emit)
        trans_row.addWidget(self.btn_pip)

        self.btn_fs = QPushButton("⛶")
        self.btn_fs.setObjectName("PrimaryButton")
        self.btn_fs.setProperty("compact", "true")
        self.btn_fs.setFixedSize(32, 26)
        self.btn_fs.setToolTip("Vollbild umschalten [F11 / F / Doppelklick]")
        self.btn_fs.clicked.connect(self.fullscreen_requested.emit)
        trans_row.addWidget(self.btn_fs)

        ctrl_lay.addLayout(trans_row)

        # Row 2: Audio Track, Subtitle Track & Aspect Ratio Selectors (Compact & Responsive)
        tracks_row = QHBoxLayout()
        tracks_row.setSpacing(6)

        lbl_aud = QLabel("Ton:")
        lbl_aud.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600;")
        lbl_aud.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        tracks_row.addWidget(lbl_aud)

        self.combo_audio = QComboBox()
        self.combo_audio.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo_audio.setMinimumContentsLength(8)
        self.combo_audio.setMinimumWidth(80)
        self.combo_audio.setFixedHeight(26)
        self.combo_audio.addItem("Audio: Auto", -1)
        self.combo_audio.setToolTip("Audiospur wählen")
        self.combo_audio.currentIndexChanged.connect(self._on_audio_combo)
        tracks_row.addWidget(self.combo_audio, 3)

        lbl_sub = QLabel("UT:")
        lbl_sub.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600;")
        lbl_sub.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        tracks_row.addWidget(lbl_sub)

        self.combo_subs = QComboBox()
        self.combo_subs.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo_subs.setMinimumContentsLength(6)
        self.combo_subs.setMinimumWidth(70)
        self.combo_subs.setFixedHeight(26)
        self.combo_subs.addItem("Aus", -1)
        self.combo_subs.setToolTip("Untertitelspur wählen")
        self.combo_subs.currentIndexChanged.connect(self._on_subs_combo)
        tracks_row.addWidget(self.combo_subs, 2)

        lbl_asp = QLabel("Bild:")
        lbl_asp.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600;")
        lbl_asp.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        tracks_row.addWidget(lbl_asp)

        self.combo_aspect = QComboBox()
        self.combo_aspect.addItems(["Auto", "16:9", "4:3", "21:9", "16:10"])
        self.combo_aspect.setMinimumWidth(65)
        self.combo_aspect.setMaximumWidth(85)
        self.combo_aspect.setFixedHeight(26)
        self.combo_aspect.setToolTip("Seitenverhältnis (Aspect Ratio) [A]")
        self.combo_aspect.currentTextChanged.connect(self.aspect_ratio_changed.emit)
        tracks_row.addWidget(self.combo_aspect)

        ctrl_lay.addLayout(tracks_row)
        right_lay.addWidget(self.controls_card)

        # 4. EPG Now & Next Panel
        self.epg_panel = EPGPanel(self)
        self.epg_panel.epg_guide_requested.connect(self._on_epg_guide_clicked)
        right_lay.addWidget(self.epg_panel)

        self.splitter.addWidget(self.right_panel)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([320, 960])
        root_layout.addWidget(self.splitter, 1)

    # ──────────────────────────────────────────────────────────────────────
    # Public Data & State API
    # ──────────────────────────────────────────────────────────────────────

    def get_video_hwnd(self) -> int:
        return int(self.video_surface.winId())

    def set_channels(
        self,
        channels: List[Channel],
        genre_map: Dict[str, str],
        favorites: Set[str],
        recent_ids: List[str],
    ):
        self._genre_map = dict(genre_map)
        self._checked_groups_session.clear()
        self.combo_category.blockSignals(True)
        self.combo_category.clear()
        self.combo_category.addItem(f"Alle Kategorien ({len(channels)})", "*")
        for gid, gname in self._genre_map.items():
            if gid != "*":
                self.combo_category.addItem(gname, gid)
        self.combo_category.blockSignals(False)

        self.channel_model.set_channels(channels, genre_map, favorites, recent_ids)
        self._update_count_label()
        self._requested_thumb_ids.clear()
        self._visible_thumbs_timer.start(400)

    def set_playing_channel(self, channel: Optional[Channel]):
        cid = str(channel.id) if channel else ""
        self.channel_model.set_playing_channel(cid)
        self._playing_channel = channel
        if channel:
            self.clear_preview()
            self._selected_channel = channel
            gname = self._genre_map.get(str(channel.tv_genre_id), channel.category)
            is_fav = cid in self.channel_model._favorites or channel.fav
            self.hero_card.set_channel(channel, gname, is_fav)

    def update_favorites(self, favorites: Set[str]):
        self.channel_model.update_favorites(favorites)
        if self._selected_channel:
            self.hero_card.set_favorite_state(str(self._selected_channel.id) in favorites)
        self._update_count_label()

    def update_recent(self, recent_ids: List[str]):
        self.channel_model.update_recent(recent_ids)
        self._update_count_label()

    def update_epg(self, ch_id: str, programs: List[EPGProgram]):
        if programs:
            self.channel_model.set_epg_now(ch_id, programs[0].name)
        if self._selected_channel and str(self._selected_channel.id) == str(ch_id):
            self.epg_panel.update_programs(programs)

    def update_probe_telemetry(self, probe: StreamProbeResult):
        if probe.width > 0 and probe.height > 0:
            real_q = quality_from_dimensions(probe.width, probe.height)
            if real_q:
                if self._selected_channel:
                    self._selected_channel.quality_tag = real_q
                    self.channel_model.update_channel_quality(self._selected_channel.id, real_q)
                if getattr(self, "_playing_channel", None):
                    self._playing_channel.quality_tag = real_q
                    self.channel_model.update_channel_quality(self._playing_channel.id, real_q)
        self.hero_card.update_probe_telemetry(probe)

    def update_live_telemetry(self, telemetry: dict):
        w = int(telemetry.get("width") or 0)
        h = int(telemetry.get("height") or 0)
        fps = float(telemetry.get("fps") or 0.0)
        kbps = int(telemetry.get("bitrate_kbps") or telemetry.get("demux_bitrate_kbps") or 0)

        # Dynamically sync real decoded stream resolution to channel badge
        if w > 0 and h > 0:
            real_q = quality_from_dimensions(w, h)
            if real_q:
                target_ch = getattr(self, "_playing_channel", None) or getattr(self, "_selected_channel", None)
                if target_ch:
                    if target_ch.quality_tag != real_q:
                        target_ch.quality_tag = real_q
                    self.channel_model.update_channel_quality(target_ch.id, real_q)
                if self._selected_channel and target_ch and str(self._selected_channel.id) == str(target_ch.id):
                    self._selected_channel.quality_tag = real_q

        ch_name = self._playing_channel.name if getattr(self, "_playing_channel", None) else (
            self._selected_channel.name if self._selected_channel else "Stream"
        )
        # Playback is verified active when video dimensions are decoded or stream bitrate is flowing
        is_actively_rendering = (w > 0 and kbps > 100) or (self._player_state == "playing" and (w > 0 or kbps > 300))

        proxy = telemetry.get("proxy")
        if isinstance(proxy, dict) and proxy.get("active"):
            lvl = float(proxy.get("level_s") or 0.0)
            in_k = int(proxy.get("in_kbps") or 0)
            if in_k > 0 and kbps == 0:
                kbps = in_k
            st_state = proxy.get("state", "playing")

            if st_state == "prefill":
                pct = float(proxy.get("prefill_pct") or 0.0)
                start_s = float(proxy.get("start_s") or 1.5)
                buf_txt = f"⏳ Vorab: {lvl:.1f}s/{start_s:.1f}s ({pct:.0f}%)"
                self.set_video_status_text(
                    f"⏳ Fülle Ringpuffer ({lvl:.1f}s / {start_s:.1f}s – {pct:.0f}%) ...",
                    f"Puffer {pct:.0f}%",
                )
            elif st_state == "rebuffer" or not proxy.get("connected", True):
                proxy_err = proxy.get("error", "")
                if proxy_err:
                    buf_txt = f"⚠️ {proxy_err[:28]}"
                    self.set_video_status_text(
                        f"⚠️ Server-Rückmeldung: {proxy_err}",
                        "Blockiert",
                    )
                else:
                    buf_txt = f"⏳ Nachpuffern: {lvl:.1f}s"
                    self.set_video_status_text(
                        f"⏳ Überbrücke Aussetzer ({lvl:.1f}s im Ringpuffer) ...",
                        "Rebuffer",
                    )
            else:
                rebuf_cnt = int(proxy.get("rebuffers") or 0)
                rebuf_note = f" (Aussetzer: {rebuf_cnt})" if rebuf_cnt > 0 else ""
                buf_mb = float(proxy.get("level_mb", 0) or 0.0)
                buf_lvl_str = f"{lvl:.1f}s" if lvl > 0.0 else "Live"
                buf_txt = f"🛡 Puffer: {buf_lvl_str} ({buf_mb:.1f} MB){rebuf_note}"
                self.set_video_status_text(
                    f"🟢 Wiedergabe: {ch_name}",
                    "LIVE",
                )
        else:
            pct = float(telemetry.get("buffer_percent") or 0.0)
            buf_txt = f"Puffer: {pct:.0f}%" if (0.0 < pct < 100.0) else "Direct Stream"
            if (pct >= 100.0 or w > 0) and (self._player_state == "playing"):
                self.set_video_status_text(
                    f"🟢 Wiedergabe: {ch_name}",
                    "LIVE",
                )

        v_cod = telemetry.get("video_codec") or ""
        a_cod = telemetry.get("audio_codec") or ""
        a_ch = int(telemetry.get("audio_channels") or 0)
        self.hero_card.update_live_telemetry(
            w, h, kbps, buf_txt, fps=fps, video_codec=v_cod, audio_codec=a_cod, audio_channels=a_ch
        )

    def update_player_state(self, state: str):
        self._player_state = state
        if state == "playing":
            self.clear_preview()
            self.btn_play_pause.setText("⏸ Pause")
        else:
            self.btn_play_pause.setText("▶ Play")
            if state == "stopped":
                self.video_surface.clear_surface()

    def set_preview_pixmap(self, pixmap: QPixmap, badge_text: str = ""):
        """Displays a Standbild preview thumbnail overlay when no live stream is actively playing."""
        if self._player_state == "playing" or pixmap is None or pixmap.isNull():
            return
        self.preview_overlay.set_pixmap(pixmap, badge_text)
        self.video_surface.setVisible(False)
        self.preview_overlay.setVisible(True)
        if badge_text:
            self.lbl_preview_badge.setText(badge_text)

    def set_preview_jpeg(self, jpeg_bytes: bytes, badge_text: str = "") -> bool:
        """Loads JPEG bytes into a QPixmap and displays the preview overlay."""
        if not jpeg_bytes or self._player_state == "playing":
            return False
        pix = QPixmap()
        if pix.loadFromData(jpeg_bytes):
            self.set_preview_pixmap(pix, badge_text)
            return True
        return False

    def clear_preview(self):
        """Hides the preview thumbnail overlay and restores the native video surface."""
        self.preview_overlay.clear_pixmap()
        self.preview_overlay.setVisible(False)
        self.video_surface.setVisible(True)
        self.lbl_preview_badge.setText("")

    def update_seek_ui(self, is_seekable: bool, current_ms: int, total_ms: int):
        self.seek_widget.setVisible(is_seekable and total_ms > 0)
        if not is_seekable or total_ms <= 0:
            return
        if not self._is_seeking:
            pos_permil = int((current_ms / max(1, total_ms)) * 1000)
            self.slider_seek.blockSignals(True)
            self.slider_seek.setValue(max(0, min(1000, pos_permil)))
            self.slider_seek.blockSignals(False)

        def _fmt(ms: int) -> str:
            sec = max(0, ms // 1000)
            m, s = divmod(sec, 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

        self.lbl_seek_time.setText(f"{_fmt(current_ms)} / {_fmt(total_ms)}")

    def update_tracks_ui(self, audio_tracks: list, sub_tracks: list):
        self.combo_audio.blockSignals(True)
        self.combo_audio.clear()
        if not audio_tracks:
            self.combo_audio.addItem("Audio: Auto", -1)
        else:
            for tid, name in audio_tracks:
                clean_name = str(name).replace("Track ", "Spur ").strip()
                self.combo_audio.addItem(f"Spur {tid}: {clean_name}" if not clean_name.startswith("Spur") else clean_name, tid)
        self.combo_audio.blockSignals(False)

        self.combo_subs.blockSignals(True)
        self.combo_subs.clear()
        self.combo_subs.addItem("UT: Aus", -1)
        for tid, name in sub_tracks:
            if tid >= 0:
                clean_name = str(name).replace("Track ", "Spur ").strip()
                self.combo_subs.addItem(clean_name, tid)
        self.combo_subs.blockSignals(False)

    def set_video_status_text(self, text: str, badge: str = ""):
        self.lbl_video_status.setText(text)
        self.lbl_preview_badge.setText(badge)

    def set_validation_running(self, running: bool, done: int = 0, total: int = 0):
        self._validation_running = running
        self.val_progress.setVisible(running)
        if running:
            self.btn_validate.setText("⏹ Stopp")
            self.btn_validate.setObjectName("DangerButton")
            self.val_progress.setRange(0, max(1, total))
            self.val_progress.setValue(done)
            pct = int((done / max(1, total)) * 100)
            self.val_progress.setFormat(f"🩺 Prüfe Sender: {done} / {total} ({pct}%)")
        else:
            self.btn_validate.setText("🩺 Gruppe prüfen")
            self.btn_validate.setObjectName("")
        self.btn_validate.style().unpolish(self.btn_validate)
        self.btn_validate.style().polish(self.btn_validate)
        self._update_count_label()

    def set_thumbnail_progress(self, running: bool, done: int = 0, total: int = 0):
        self._validation_running = running
        self.val_progress.setVisible(running)
        if running:
            self.btn_validate.setText("⏹ Stopp")
            self.btn_validate.setObjectName("DangerButton")
            self.val_progress.setRange(0, max(1, total))
            self.val_progress.setValue(done)
            pct = int((done / max(1, total)) * 100)
            self.val_progress.setFormat(f"📸 Lade Vorschaubilder: {done} / {total} ({pct}%)")
        else:
            self.btn_validate.setText("🩺 Gruppe prüfen")
            self.btn_validate.setObjectName("")
        self.btn_validate.style().unpolish(self.btn_validate)
        self.btn_validate.style().polish(self.btn_validate)
        self._update_count_label()

    def get_visible_channels(self) -> List[Channel]:
        out: List[Channel] = []
        for row in range(self.proxy_model.rowCount()):
            idx = self.proxy_model.index(row, 0)
            ch = self.proxy_model.data(idx, ChannelRoles.ChannelObjRole)
            if isinstance(ch, Channel):
                out.append(ch)
        return out

    def select_adjacent_channel(self, delta: int) -> Optional[Channel]:
        total = self.proxy_model.rowCount()
        if total == 0:
            return None
        cur_idx = self.list_view.currentIndex()
        next_row = (cur_idx.row() + delta) % total if cur_idx.isValid() else 0
        new_idx = self.proxy_model.index(next_row, 0)
        self.list_view.setCurrentIndex(new_idx)
        self.list_view.scrollTo(new_idx)
        ch = self.proxy_model.data(new_idx, ChannelRoles.ChannelObjRole)
        if isinstance(ch, Channel):
            self._selected_channel = ch
            return ch
        return None

    def set_cinema_layout(self, cinema_or_fs: bool, pip_mode: bool = False):
        """Hides surrounding chrome for Cinema Mode, Fullscreen, or PiP Mini-Player."""
        self.left_panel.setVisible(not cinema_or_fs and not pip_mode)
        self.hero_card.setVisible(not cinema_or_fs and not pip_mode)
        self.epg_panel.setVisible(not cinema_or_fs and not pip_mode)
        self.controls_card.setVisible(not pip_mode)
        self.preview_bar.setVisible(not cinema_or_fs and not pip_mode)

    # ──────────────────────────────────────────────────────────────────────
    # Internal UI Handlers
    # ──────────────────────────────────────────────────────────────────────

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if (obj is self.list_view or obj is self.list_view.viewport()) and event.type() == QEvent.Type.MouseButtonDblClick:
            if isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
                pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
                idx = self.list_view.indexAt(pos)
                if idx.isValid():
                    self._on_list_double_clicked(idx)
                    return True
        if obj is self.list_view and event.type() == QEvent.Type.KeyPress:
            if isinstance(event, QKeyEvent) and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                idx = self.list_view.currentIndex()
                if idx.isValid():
                    self._on_list_double_clicked(idx)
                    return True
        return super().eventFilter(obj, event)

    def _on_preview_play_clicked(self):
        if self._selected_channel:
            self.channel_play_requested.emit(self._selected_channel)

    def _on_logo_ready(self, url: str):
        self.channel_model.notify_logo_updated(url)
        if self._selected_channel and self._selected_channel.logo == url:
            gname = self._genre_map.get(str(self._selected_channel.tv_genre_id), self._selected_channel.category)
            is_fav = str(self._selected_channel.id) in self.channel_model._favorites
            self.hero_card.set_channel(self._selected_channel, gname, is_fav)

    def _update_count_label(self):
        vis = self.proxy_model.rowCount()
        tot = self.channel_model.rowCount()
        self.lbl_channel_count.setText(f"{vis} / {tot} Sender")

    def _on_search_changed(self, text: str):
        self.proxy_model.set_search_query(text)
        self._update_count_label()

    def _on_category_changed(self, idx: int):
        if idx < 0:
            return
        cat_id = str(self.combo_category.itemData(idx) or "*")
        self.proxy_model.set_category_id(cat_id)
        self._update_count_label()

        # Automatische Prüfung beim ersten Aufruf der Gruppe in der Sitzung
        if cat_id != "*" and cat_id not in self._checked_groups_session:
            self._checked_groups_session.add(cat_id)
            if self._validation_running:
                self.stop_validation_requested.emit()
            chans = self.get_visible_channels()
            if chans:
                self.validate_category_requested.emit(chans)
        else:
            self._requested_thumb_ids.clear()
            self._visible_thumbs_timer.start(350)

    def _set_mode_filter(self, mode: str):
        for k, btn in self._mode_buttons.items():
            btn.setChecked(k == mode)
        self.proxy_model.set_mode_filter(mode)
        self._update_count_label()
        self._visible_thumbs_timer.start(350)

    def _on_hide_dead_toggled(self, checked: bool):
        self.proxy_model.set_hide_dead(checked)
        self._update_count_label()
        self._visible_thumbs_timer.start(350)

    def _on_reset_dead(self):
        self.channel_model.clear_dead_flags()
        self.proxy_model.invalidate()
        self._update_count_label()
        self._visible_thumbs_timer.start(350)

    def _on_validate_clicked(self):
        if self._validation_running:
            self.stop_validation_requested.emit()
        else:
            cur_idx = self.combo_category.currentIndex()
            if cur_idx >= 0:
                cat_id = str(self.combo_category.itemData(cur_idx) or "*")
                self._checked_groups_session.add(cat_id)
            chans = self.get_visible_channels()
            if chans:
                self.validate_category_requested.emit(chans)

    def _on_fetch_thumbnails_clicked(self):
        if self._validation_running:
            self.stop_validation_requested.emit()
        else:
            chans = self.get_visible_channels()
            if chans:
                self.fetch_group_thumbnails_requested.emit(chans)

    def _check_visible_thumbnails(self):
        if not self.isVisible() or self._validation_running:
            return
        vp = self.list_view.viewport()
        if not vp or vp.height() <= 0:
            return
        top_idx = self.list_view.indexAt(QPoint(10, 10))
        bottom_idx = self.list_view.indexAt(QPoint(10, vp.height() - 10))
        if not top_idx.isValid():
            return
        start_row = top_idx.row()
        end_row = bottom_idx.row() if bottom_idx.isValid() else min(start_row + 15, self.proxy_model.rowCount() - 1)

        need_fetch: List[Channel] = []
        for row in range(max(0, start_row), min(self.proxy_model.rowCount(), end_row + 1)):
            idx = self.proxy_model.index(row, 0)
            if not idx.isValid():
                continue
            cid = str(idx.data(ChannelRoles.ChannelIdRole) or "")
            is_dead = bool(idx.data(ChannelRoles.IsDeadRole))
            if is_dead or not cid:
                continue
            if cid in self.delegate._thumb_cache and self.delegate._thumb_cache[cid] is not None:
                continue
            key = f"{self.delegate._profile_name}:{cid}" if self.delegate._profile_name else cid
            if load_cached_thumb(key) or (load_cached_thumb(cid) if self.delegate._profile_name else None):
                continue
            ch = self.proxy_model.data(idx, ChannelRoles.ChannelObjRole)
            if isinstance(ch, Channel) and str(ch.id) not in self._requested_thumb_ids:
                self._requested_thumb_ids.add(str(ch.id))
                need_fetch.append(ch)

        if need_fetch:
            self.fetch_group_thumbnails_requested.emit(need_fetch)

    def _select_channel_from_index(self, index: QModelIndex, force_emit: bool = False):
        if not index.isValid():
            return
        ch = self.proxy_model.data(index, ChannelRoles.ChannelObjRole)
        if isinstance(ch, Channel):
            already_selected = (
                self._selected_channel is not None
                and str(self._selected_channel.id) == str(ch.id)
            )
            self._selected_channel = ch
            gname = self._genre_map.get(str(ch.tv_genre_id), ch.category)
            is_fav = str(ch.id) in self.channel_model._favorites or ch.fav
            self.hero_card.set_channel(ch, gname, is_fav)
            if not already_selected or force_emit:
                self.channel_selected.emit(ch)

    def _on_list_current_changed(self, current: QModelIndex, _previous: QModelIndex):
        self._select_channel_from_index(current, force_emit=False)

    def _on_list_clicked(self, index: QModelIndex):
        self._select_channel_from_index(index, force_emit=False)

    def _on_list_double_clicked(self, index: QModelIndex):
        if not index.isValid():
            return
        ch = self.proxy_model.data(index, ChannelRoles.ChannelObjRole)
        if isinstance(ch, Channel):
            self._selected_channel = ch
            gname = self._genre_map.get(str(ch.tv_genre_id), ch.category)
            is_fav = str(ch.id) in self.channel_model._favorites or ch.fav
            self.hero_card.set_channel(ch, gname, is_fav)
            self.channel_play_requested.emit(ch)

    def _show_context_menu(self, pos: QPoint):
        index = self.list_view.indexAt(pos)
        if not index.isValid():
            return
        ch = self.proxy_model.data(index, ChannelRoles.ChannelObjRole)
        if not isinstance(ch, Channel):
            return
        self._selected_channel = ch

        menu = QMenu(self)
        act_play = QAction(f"▶ '{ch.name}' abspielen", self)
        act_play.triggered.connect(lambda: self.channel_play_requested.emit(ch))
        menu.addAction(act_play)

        is_fav = str(ch.id) in self.channel_model._favorites
        act_fav = QAction("★ Aus Favoriten entfernen" if is_fav else "☆ Zu Favoriten hinzufügen", self)
        act_fav.triggered.connect(lambda: self.favorite_toggled.emit(str(ch.id)))
        menu.addAction(act_fav)

        menu.addSeparator()

        act_epg = QAction("📅 Programmführer & Catchup-Archiv öffnen", self)
        act_epg.triggered.connect(lambda: self.epg_guide_requested.emit(ch))
        menu.addAction(act_epg)

        act_rec = QAction("🔴 Stream direkt aufnehmen (REC)", self)
        act_rec.triggered.connect(lambda: self.record_channel_requested.emit(ch))
        menu.addAction(act_rec)

        act_probe = QAction("🔍 Stream-Codec & Bitrate analysieren (FFprobe)", self)
        act_probe.triggered.connect(lambda: self.probe_channel_requested.emit(ch))
        menu.addAction(act_probe)

        act_val_grp = QAction("🩺 Alle Sender dieser Gruppe verifizieren (3s Timeout)", self)
        act_val_grp.triggered.connect(self._on_validate_clicked)
        menu.addAction(act_val_grp)

        act_thumbs = QAction("📸 Vorschaubilder für sichtbare Sender laden", self)
        act_thumbs.triggered.connect(self._on_fetch_thumbnails_clicked)
        menu.addAction(act_thumbs)

        act_copy = QAction("📋 Stream-URL in Zwischenablage kopieren", self)
        act_copy.triggered.connect(lambda: self.copy_url_requested.emit(ch))
        menu.addAction(act_copy)

        menu.addSeparator()

        act_m3u = QAction("💾 Sichtbare Senderliste als .M3U8 exportieren", self)
        act_m3u.triggered.connect(self._on_export_visible_m3u)
        menu.addAction(act_m3u)

        act_json = QAction("{ } Raw Kanal-JSON inspizieren", self)
        act_json.triggered.connect(lambda: self.raw_json_requested.emit(ch.name, ch.raw_data))
        menu.addAction(act_json)

        menu.exec(self.list_view.viewport().mapToGlobal(pos))

    def _on_hero_fav_clicked(self):
        if self._selected_channel:
            self.favorite_toggled.emit(str(self._selected_channel.id))

    def _on_hero_probe_clicked(self):
        if self._selected_channel:
            self.probe_channel_requested.emit(self._selected_channel)

    def _on_hero_copy_clicked(self):
        if self._selected_channel:
            self.copy_url_requested.emit(self._selected_channel)

    def _on_export_visible_m3u(self):
        chans = self.get_visible_channels()
        if chans:
            self.export_m3u_requested.emit(chans)

    def _on_record_clicked(self):
        if self._selected_channel:
            self.record_channel_requested.emit(self._selected_channel)

    def _on_epg_guide_clicked(self):
        if self._selected_channel:
            self.epg_guide_requested.emit(self._selected_channel)

    def _on_volume_slider(self, val: int):
        self.lbl_volume.setText(f"{val}%")
        self.volume_changed.emit(val)

    def _on_audio_combo(self, idx: int):
        if idx >= 0:
            tid = self.combo_audio.itemData(idx)
            if tid is not None:
                self.audio_track_selected.emit(int(tid))

    def _on_subs_combo(self, idx: int):
        if idx >= 0:
            tid = self.combo_subs.itemData(idx)
            if tid is not None:
                self.subtitle_track_selected.emit(int(tid))

    def _on_speed_changed(self, text: str):
        try:
            rate = float(text.replace("x", "").strip())
            self.playback_speed_changed.emit(rate)
        except Exception:
            pass

    def _on_seek_pressed(self):
        self._is_seeking = True

    def _on_seek_released(self):
        self._is_seeking = False
        frac = self.slider_seek.value() / 1000.0
        self.seek_position_requested.emit(frac)

