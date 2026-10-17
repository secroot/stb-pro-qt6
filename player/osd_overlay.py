"""
Transparentes Qt6 Fullscreen-OSD (HUD) & Quick-Channel-Drawer.
Verwendet eigene rahmenlose Tool-Overlays, die niemals vom Direct3D11/LibVLC-Video-Surface
übermalt werden und flimmerfrei über dem Vollbild-Video schweben.
"""
import datetime
from typing import List, Callable, Optional
from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QLineEdit, QListWidget, QListWidgetItem, QFrame
)
from core.models import Channel


class _TopHudBar(QWidget):
    def __init__(self, parent_window: QWidget, on_exit_fs: Callable[[], None]):
        super().__init__(
            parent_window,
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 14, 23, 230);
                border-bottom: 1px solid #1E293B;
            }
            QLabel { background: transparent; border: none; }
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(12)

        self.lbl_badge = QLabel("🔴 LIVE")
        self.lbl_badge.setStyleSheet(
            "background-color: #DC2626; color: #FFFFFF; font-weight: bold; "
            "font-size: 11px; padding: 3px 8px; border-radius: 5px;"
        )
        layout.addWidget(self.lbl_badge)

        self.lbl_num = QLabel("#01")
        self.lbl_num.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.lbl_num)

        self.lbl_title = QLabel("Kein Sender aktiv")
        self.lbl_title.setStyleSheet("color: #F8FAFC; font-weight: bold; font-size: 15px;")
        layout.addWidget(self.lbl_title)

        self.lbl_cat = QLabel("")
        self.lbl_cat.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(self.lbl_cat)

        self.lbl_epg = QLabel("")
        self.lbl_epg.setStyleSheet("color: #34D399; font-size: 12px; font-weight: 600; margin-left: 12px;")
        layout.addWidget(self.lbl_epg)

        layout.addStretch(1)

        self.lbl_clock = QLabel("--:--:--")
        self.lbl_clock.setStyleSheet("color: #E2E8F0; font-family: Consolas; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.lbl_clock)

        btn_exit = QPushButton("✕ Vollbild verlassen [Esc]")
        btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exit.setStyleSheet("""
            QPushButton {
                background-color: #1E293B; color: #F8FAFC; border: 1px solid #334155;
                border-radius: 6px; padding: 5px 12px; font-weight: bold; font-size: 11px;
            }
            QPushButton:hover { background-color: #334155; }
        """)
        btn_exit.clicked.connect(on_exit_fs)
        layout.addWidget(btn_exit)

        outer.addWidget(frame)


class _BottomHudBar(QWidget):
    def __init__(
        self,
        parent_window: QWidget,
        on_prev: Callable[[], None],
        on_play_pause: Callable[[], None],
        on_stop: Callable[[], None],
        on_next: Callable[[], None],
        on_mute: Callable[[], None],
        on_volume: Callable[[int], None],
        on_aspect: Callable[[str], None],
        on_toggle_drawer: Callable[[], None],
    ):
        super().__init__(
            parent_window,
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 14, 23, 230);
                border-top: 1px solid #1E293B;
            }
            QLabel { background: transparent; border: none; color: #94A3B8; }
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(8)

        btn_style = """
            QPushButton {
                background-color: #182236; color: #F8FAFC; border: 1px solid #283A54;
                border-radius: 6px; padding: 5px 12px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #253554; }
        """

        btn_prev = QPushButton("⏮")
        btn_prev.setStyleSheet(btn_style)
        btn_prev.clicked.connect(on_prev)
        layout.addWidget(btn_prev)

        self.btn_play = QPushButton("⏸")
        self.btn_play.setStyleSheet("""
            QPushButton {
                background-color: #10B981; color: #FFFFFF; border: none;
                border-radius: 6px; padding: 5px 16px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_play.clicked.connect(on_play_pause)
        layout.addWidget(self.btn_play)

        btn_stop = QPushButton("⏹")
        btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #991B1B; color: #FFFFFF; border: none;
                border-radius: 6px; padding: 5px 12px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #7F1D1D; }
        """)
        btn_stop.clicked.connect(on_stop)
        layout.addWidget(btn_stop)

        btn_next = QPushButton("⏭")
        btn_next.setStyleSheet(btn_style)
        btn_next.clicked.connect(on_next)
        layout.addWidget(btn_next)

        self.btn_mute = QPushButton("🔊")
        self.btn_mute.setStyleSheet(btn_style)
        self.btn_mute.clicked.connect(on_mute)
        layout.addWidget(self.btn_mute)

        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        self.slider_vol.setFixedWidth(120)
        self.slider_vol.valueChanged.connect(on_volume)
        layout.addWidget(self.slider_vol)

        self.lbl_vol = QLabel("100%")
        self.lbl_vol.setFixedWidth(40)
        layout.addWidget(self.lbl_vol)

        layout.addStretch(1)

        self.combo_aspect = QComboBox()
        self.combo_aspect.addItems(["16:9", "4:3", "21:9", "Auto"])
        self.combo_aspect.setFixedWidth(85)
        self.combo_aspect.currentTextChanged.connect(on_aspect)
        layout.addWidget(self.combo_aspect)

        btn_drawer = QPushButton("📋 Senderliste [C]")
        btn_drawer.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; color: #FFFFFF; border: none;
                border-radius: 6px; padding: 6px 14px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        btn_drawer.clicked.connect(on_toggle_drawer)
        layout.addWidget(btn_drawer)

        outer.addWidget(frame)


class _ChannelDrawerOverlay(QWidget):
    def __init__(self, parent_window: QWidget, on_select_channel: Callable[[str], None]):
        super().__init__(
            parent_window,
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.on_select_channel = on_select_channel
        self._channels: List[Channel] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(13, 19, 31, 242);
                border-left: 1px solid #1E293B;
            }
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        hdr = QHBoxLayout()
        lbl = QLabel("📺 Schnell-Senderwahl")
        lbl.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 13px; border: none;")
        hdr.addWidget(lbl)
        hdr.addStretch(1)
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(26, 26)
        btn_close.clicked.connect(self.hide)
        hdr.addWidget(btn_close)
        lay.addLayout(hdr)

        self.entry_search = QLineEdit()
        self.entry_search.setPlaceholderText("🔍 Sender filtern...")
        self.entry_search.textChanged.connect(self._filter)
        lay.addWidget(self.entry_search)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #080C14; border: 1px solid #1E293B;
                border-radius: 6px; color: #F1F5F9; font-size: 12px;
            }
            QListWidget::item { padding: 7px 8px; border-bottom: 1px solid #111827; }
            QListWidget::item:selected { background-color: #1E3A8A; color: #FFFFFF; }
            QListWidget::item:hover { background-color: #162032; }
        """)
        self.list_widget.itemDoubleClicked.connect(self._on_item_activated)
        lay.addWidget(self.list_widget, 1)

        outer.addWidget(frame)

    def set_channels(self, channels: List[Channel]):
        self._channels = list(channels)
        self._filter()

    def _filter(self):
        q = self.entry_search.text().strip().lower()
        self.list_widget.clear()
        count = 0
        for ch in self._channels:
            if ch.is_dead:
                continue
            if q and q not in ch.name.lower() and q not in str(ch.number).lower() and q not in ch.category.lower():
                continue
            item = QListWidgetItem(f"{ch.number}. {ch.name}  [{ch.category}]")
            item.setData(Qt.ItemDataRole.UserRole, ch.id)
            self.list_widget.addItem(item)
            count += 1
            if count >= 400:
                break

    def _on_item_activated(self, item: QListWidgetItem):
        cid = item.data(Qt.ItemDataRole.UserRole)
        if cid:
            self.on_select_channel(str(cid))


class FullscreenOSDOverlay(QObject):
    """Koordiniert Top-HUD, Bottom-HUD, Uhrzeit-Timer, Auto-Hide und den Quick-Channel-Drawer."""
    def __init__(
        self,
        main_window: QWidget,
        on_play_pause: Callable[[], None],
        on_stop: Callable[[], None],
        on_prev: Callable[[], None],
        on_next: Callable[[], None],
        on_volume: Callable[[int], None],
        on_toggle_mute: Callable[[], None],
        on_aspect_ratio: Callable[[str], None],
        on_exit_fullscreen: Callable[[], None],
        on_channel_select: Callable[[str], None],
    ):
        super().__init__(main_window)
        self.main_window = main_window
        self.is_visible = False

        self.top_bar = _TopHudBar(main_window, on_exit_fullscreen)
        self.bottom_bar = _BottomHudBar(
            main_window,
            on_prev=on_prev,
            on_play_pause=on_play_pause,
            on_stop=on_stop,
            on_next=on_next,
            on_mute=on_toggle_mute,
            on_volume=on_volume,
            on_aspect=on_aspect_ratio,
            on_toggle_drawer=self.toggle_drawer,
        )
        self.drawer = _ChannelDrawerOverlay(main_window, on_channel_select)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_bars)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._tick_clock)

    def populate_drawer_channels(self, channels: List[Channel]):
        self.drawer.set_channels(channels)

    def update_info(
        self,
        number: str = "",
        title: str = "",
        category: str = "",
        epg_now: str = "",
        is_playing: bool = True,
    ):
        self.top_bar.lbl_num.setText(f"#{number}" if number else "")
        self.top_bar.lbl_title.setText(title or "Kein Sender aktiv")
        self.top_bar.lbl_cat.setText(f"• {category}" if category else "")
        self.top_bar.lbl_epg.setText(f"🕒 {epg_now}" if epg_now else "")
        self.bottom_bar.btn_play.setText("⏸" if is_playing else "▶")

    def update_volume_ui(self, vol: int, is_muted: bool):
        self.bottom_bar.slider_vol.blockSignals(True)
        self.bottom_bar.slider_vol.setValue(vol)
        self.bottom_bar.slider_vol.blockSignals(False)
        self.bottom_bar.lbl_vol.setText("MUTE" if is_muted else f"{vol}%")
        self.bottom_bar.btn_mute.setText("🔇" if is_muted else "🔊")

    def _reposition(self):
        screen = self.main_window.screen()
        if getattr(self.main_window, "is_fullscreen", False) and screen is not None:
            geo = screen.geometry()
        else:
            geo = self.main_window.geometry()
        x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
        self.top_bar.setGeometry(x, y, w, 54)
        self.bottom_bar.setGeometry(x, y + h - 58, w, 58)
        self.drawer.setGeometry(x + w - 350, y + 54, 350, max(200, h - 112))

    def show(self, auto_hide_ms: int = 3800):
        if not getattr(self.main_window, "is_fullscreen", False):
            return
        self._reposition()
        self._tick_clock()
        if not self.clock_timer.isActive():
            self.clock_timer.start(1000)
        self.top_bar.show()
        self.bottom_bar.show()
        self.is_visible = True
        self.hide_timer.start(auto_hide_ms)

    def hide_bars(self):
        if self.drawer.isVisible():
            self.hide_timer.start(3500)
            return
        self.top_bar.hide()
        self.bottom_bar.hide()
        self.is_visible = False

    def hide_all(self):
        self.hide_timer.stop()
        self.clock_timer.stop()
        self.top_bar.hide()
        self.bottom_bar.hide()
        self.drawer.hide()
        self.is_visible = False

    def toggle_drawer(self):
        if not getattr(self.main_window, "is_fullscreen", False):
            return
        self._reposition()
        if self.drawer.isVisible():
            self.drawer.hide()
        else:
            self.show(auto_hide_ms=8000)
            self.drawer.show()
            self.drawer.entry_search.setFocus()

    def _tick_clock(self):
        self.top_bar.lbl_clock.setText(datetime.datetime.now().strftime("%H:%M:%S"))

    def shutdown(self):
        self.hide_all()
