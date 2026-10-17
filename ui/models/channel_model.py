"""
Virtualized Channel List Model, Filter Proxy Model, and 120-FPS Custom QPainter Delegate.
Eliminates CustomTkinter's 120-widget creation bottleneck by rendering only visible rows on the GPU.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set
from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QRect,
    QRectF,
    QSize,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from core.models import Channel, EPGProgram
from core.preview_grabber import load_cached_thumb


class ChannelRoles:
    ChannelObjRole = Qt.ItemDataRole.UserRole + 1
    ChannelIdRole = Qt.ItemDataRole.UserRole + 2
    NameRole = Qt.ItemDataRole.UserRole + 3
    NumberRole = Qt.ItemDataRole.UserRole + 4
    GenreNameRole = Qt.ItemDataRole.UserRole + 5
    GenreIdRole = Qt.ItemDataRole.UserRole + 6
    QualityTagRole = Qt.ItemDataRole.UserRole + 7
    IsFavoriteRole = Qt.ItemDataRole.UserRole + 8
    IsPlayingRole = Qt.ItemDataRole.UserRole + 9
    IsRecentRole = Qt.ItemDataRole.UserRole + 10
    IsDeadRole = Qt.ItemDataRole.UserRole + 11
    LatencyMsRole = Qt.ItemDataRole.UserRole + 12
    EpgNowTitleRole = Qt.ItemDataRole.UserRole + 13
    LogoUrlRole = Qt.ItemDataRole.UserRole + 14
    FlagsSummaryRole = Qt.ItemDataRole.UserRole + 15


class ChannelListModel(QAbstractListModel):
    """High-performance backing model for 50,000+ Live TV channels."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._channels: List[Channel] = []
        self._id_to_row: Dict[str, int] = {}
        self._genre_map: Dict[str, str] = {}
        self._favorites: Set[str] = set()
        self._recent_ids: List[str] = []
        self._epg_now: Dict[str, str] = {}
        self._playing_id: str = ""

    def set_channels(
        self,
        channels: List[Channel],
        genre_map: Dict[str, str],
        favorites: Set[str],
        recent_ids: List[str],
    ):
        self.beginResetModel()
        self._channels = list(channels)
        self._id_to_row = {str(ch.id): idx for idx, ch in enumerate(self._channels)}
        self._genre_map = dict(genre_map)
        self._favorites = set(favorites)
        self._recent_ids = list(recent_ids)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._channels)

    def channel_at(self, row: int) -> Optional[Channel]:
        if 0 <= row < len(self._channels):
            return self._channels[row]
        return None

    def find_channel_by_id(self, ch_id: str) -> Optional[Channel]:
        row = self._id_to_row.get(str(ch_id))
        if row is not None and 0 <= row < len(self._channels):
            return self._channels[row]
        return None

    def set_playing_channel(self, ch_id: str):
        old_id = self._playing_id
        self._playing_id = str(ch_id)
        for cid in (old_id, self._playing_id):
            row = self._id_to_row.get(cid)
            if row is not None:
                idx = self.index(row, 0)
                self.dataChanged.emit(idx, idx, [ChannelRoles.IsPlayingRole])

    def update_favorites(self, favorites: Set[str]):
        self._favorites = set(favorites)
        if self._channels:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._channels) - 1, 0),
                [ChannelRoles.IsFavoriteRole],
            )

    def update_recent(self, recent_ids: List[str]):
        self._recent_ids = list(recent_ids)
        if self._channels:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._channels) - 1, 0),
                [ChannelRoles.IsRecentRole],
            )

    def update_channel_health(self, ch_id: str, is_alive: bool, latency_ms: int = -1):
        row = self._id_to_row.get(str(ch_id))
        if row is not None:
            ch = self._channels[row]
            ch.is_dead = not is_alive
            ch.latency_ms = latency_ms
            idx = self.index(row, 0)
            self.dataChanged.emit(
                idx, idx, [ChannelRoles.IsDeadRole, ChannelRoles.LatencyMsRole]
            )

    def update_channel_quality(self, ch_id: str, quality_tag: str):
        """Aktualisiert die tatsächliche Videoauflösung (UHD/FHD/HD/SD) dynamisch im Channel-Objekt und UI."""
        if not quality_tag:
            return
        row = self._id_to_row.get(str(ch_id))
        if row is not None and 0 <= row < len(self._channels):
            ch = self._channels[row]
            if ch.quality_tag != quality_tag:
                ch.quality_tag = quality_tag
                idx = self.index(row, 0)
                self.dataChanged.emit(
                    idx, idx, [ChannelRoles.QualityTagRole, ChannelRoles.FlagsSummaryRole]
                )

    def clear_dead_flags(self):
        for ch in self._channels:
            ch.is_dead = False
            ch.latency_ms = -1
        if self._channels:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._channels) - 1, 0),
                [ChannelRoles.IsDeadRole, ChannelRoles.LatencyMsRole],
            )

    def set_epg_now(self, ch_id: str, program_title: str):
        self._epg_now[str(ch_id)] = program_title
        row = self._id_to_row.get(str(ch_id))
        if row is not None:
            idx = self.index(row, 0)
            self.dataChanged.emit(idx, idx, [ChannelRoles.EpgNowTitleRole])

    def notify_logo_updated(self, logo_url: str):
        if not self._channels:
            return
        for row, ch in enumerate(self._channels):
            if ch.logo == logo_url:
                idx = self.index(row, 0)
                self.dataChanged.emit(idx, idx)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._channels)):
            return None

        ch = self._channels[index.row()]
        cid = str(ch.id)

        if role in (Qt.ItemDataRole.DisplayRole, ChannelRoles.NameRole):
            return ch.name
        if role == ChannelRoles.ChannelObjRole:
            return ch
        if role == ChannelRoles.ChannelIdRole:
            return cid
        if role == ChannelRoles.NumberRole:
            return ch.number
        if role == ChannelRoles.GenreIdRole:
            return str(ch.tv_genre_id)
        if role == ChannelRoles.GenreNameRole:
            return self._genre_map.get(str(ch.tv_genre_id), "Alle Kanäle")
        if role == ChannelRoles.QualityTagRole:
            return ch.quality_tag
        if role == ChannelRoles.IsFavoriteRole:
            return cid in self._favorites or ch.fav
        if role == ChannelRoles.IsPlayingRole:
            return cid == self._playing_id
        if role == ChannelRoles.IsRecentRole:
            return cid in self._recent_ids
        if role == ChannelRoles.IsDeadRole:
            return ch.is_dead
        if role == ChannelRoles.LatencyMsRole:
            return ch.latency_ms
        if role == ChannelRoles.EpgNowTitleRole:
            return self._epg_now.get(cid, "")
        if role == ChannelRoles.LogoUrlRole:
            return ch.logo
        if role == ChannelRoles.FlagsSummaryRole:
            return ch.flags_summary
        return None


class ChannelFilterProxyModel(QSortFilterProxyModel):
    """Zero-allocation filter proxy supporting Category, Search, Favorites, Recent, HD/4K, and Dead hiding."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._category_id: str = "*"
        self._search_query: str = ""
        self._mode_filter: str = "ALL"  # ALL, FAV, RECENT, HD
        self._hide_dead: bool = False
        self.setDynamicSortFilter(True)

    def set_category_id(self, category_id: str):
        self._category_id = str(category_id or "*")
        self.invalidate()

    def set_search_query(self, query: str):
        self._search_query = (query or "").strip().lower()
        self.invalidate()

    def set_mode_filter(self, mode: str):
        self._mode_filter = (mode or "ALL").upper()
        self.invalidate()

    def set_hide_dead(self, hide_dead: bool):
        self._hide_dead = bool(hide_dead)
        self.invalidate()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        if not model:
            return True
        idx = model.index(source_row, 0, source_parent)

        if self._hide_dead and model.data(idx, ChannelRoles.IsDeadRole):
            return False

        # Mode filter (ALL, FAV, RECENT, HD)
        if self._mode_filter == "FAV":
            if not model.data(idx, ChannelRoles.IsFavoriteRole):
                return False
        elif self._mode_filter == "RECENT":
            if not model.data(idx, ChannelRoles.IsRecentRole):
                return False
        elif self._mode_filter == "HD":
            qtag = model.data(idx, ChannelRoles.QualityTagRole)
            if qtag not in ("UHD", "FHD", "HD"):
                return False

        # Category filter
        if self._category_id not in ("*", "", "ALL"):
            gid = model.data(idx, ChannelRoles.GenreIdRole)
            if gid != self._category_id:
                return False

        # Text search filter (matches name, number, genre, or current EPG program)
        if self._search_query:
            name = (model.data(idx, ChannelRoles.NameRole) or "").lower()
            num = str(model.data(idx, ChannelRoles.NumberRole) or "")
            genre = (model.data(idx, ChannelRoles.GenreNameRole) or "").lower()
            epg = (model.data(idx, ChannelRoles.EpgNowTitleRole) or "").lower()
            if (
                self._search_query not in name
                and self._search_query not in num
                and self._search_query not in genre
                and self._search_query not in epg
            ):
                return False

        return True


class ChannelCardDelegate(QStyledItemDelegate):
    """
    Custom QPainter delegate rendering sleek, GPU-accelerated channel cards:
    - Left active indicator bar when playing
    - Number badge + Async Channel Logo / Monogram
    - Bold Title + Quality Pill (UHD/FHD/HD) + Latency/Dead badge
    - Subtitle with Genre + Live EPG Now Playing + Archive/Catchup icon
    - Interactive Star toggle on the right
    """
    favorite_clicked = Signal(str)  # Emits channel_id when star is clicked

    def __init__(self, logo_cache=None, parent=None):
        super().__init__(parent)
        self._logo_cache = logo_cache
        self._thumb_cache: Dict[str, QPixmap] = {}
        self._profile_name: str = ""

    def set_profile_name(self, name: str):
        self._profile_name = str(name or "")

    def set_thumbnail(self, ch_id: str, pixmap_or_bytes: Any):
        cid = str(ch_id)
        if not pixmap_or_bytes:
            self._thumb_cache[cid] = None
            return
        pix = None
        if isinstance(pixmap_or_bytes, bytes):
            p = QPixmap()
            if p.loadFromData(pixmap_or_bytes) and not p.isNull():
                pix = p
        elif isinstance(pixmap_or_bytes, QPixmap) and not pixmap_or_bytes.isNull():
            pix = pixmap_or_bytes

        if pix:
            scaled = pix.scaled(
                106, 60,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._thumb_cache[cid] = scaled
        else:
            self._thumb_cache[cid] = None

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), 80)

    def editorEvent(self, event, model, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Type.MouseButtonDblClick:
            return False
        if event.type() == QEvent.Type.MouseButtonRelease:
            rect = option.rect.adjusted(4, 3, -4, -3)
            star_rect = QRect(rect.right() - 36, rect.top(), 36, rect.height())
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            if star_rect.contains(pos):
                cid = str(index.data(ChannelRoles.ChannelIdRole) or "")
                if cid:
                    self.favorite_clicked.emit(cid)
                    return True
        return super().editorEvent(event, model, option, index)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = option.rect.adjusted(4, 3, -4, -3)
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        is_playing = bool(index.data(ChannelRoles.IsPlayingRole))
        is_fav = bool(index.data(ChannelRoles.IsFavoriteRole))
        is_dead = bool(index.data(ChannelRoles.IsDeadRole))
        latency_ms = index.data(ChannelRoles.LatencyMsRole) or -1

        # Gray out dead / non-responsive channels
        if is_dead:
            painter.setOpacity(0.55)

        # Background card
        bg_path = QPainterPath()
        bg_path.addRoundedRect(QRectF(rect), 8.0, 8.0)

        if is_playing:
            bg_color = QColor("#14223E")
            border_color = QColor("#10B981")
        elif is_selected:
            bg_color = QColor("#161E30" if is_dead else "#1E2B48")
            border_color = QColor("#4B5563" if is_dead else "#6366F1")
        elif is_hovered:
            bg_color = QColor("#111726" if is_dead else "#162035")
            border_color = QColor("#1E2A3E" if is_dead else "#263554")
        else:
            bg_color = QColor("#0B0E17" if is_dead else "#101726")
            border_color = QColor("#151C2B" if is_dead else "#1A2438")

        painter.fillPath(bg_path, bg_color)
        painter.setPen(QPen(border_color, 1.4 if is_playing else (1.2 if is_selected else 1.0)))
        painter.drawPath(bg_path)

        # Left accent bar if playing or selected
        if is_playing or is_selected:
            bar_rect = QRectF(rect.left() + 2, rect.top() + 8, 4, rect.height() - 16)
            bar_path = QPainterPath()
            bar_path.addRoundedRect(bar_rect, 2, 2)
            painter.fillPath(bar_path, QColor("#10B981" if is_playing else ("#475569" if is_dead else "#6366F1")))

        # Avatar / Logo Box (42x42)
        logo_rect = QRect(rect.left() + 10, rect.top() + (rect.height() - 42) // 2, 42, 42)
        logo_url = index.data(ChannelRoles.LogoUrlRole) or ""
        pixmap: Optional[QPixmap] = None
        if self._logo_cache and logo_url:
            pixmap = self._logo_cache.get_pixmap(logo_url, 38, 38)

        avatar_path = QPainterPath()
        avatar_path.addRoundedRect(QRectF(logo_rect), 8.0, 8.0)
        painter.fillPath(avatar_path, QColor("#090D15" if is_dead else "#0B101B"))
        painter.setPen(QPen(QColor("#1A2335" if is_dead else "#23304A"), 1))
        painter.drawPath(avatar_path)

        name = str(index.data(ChannelRoles.NameRole) or "Unbekannt")
        if pixmap and not pixmap.isNull():
            px = logo_rect.left() + (logo_rect.width() - pixmap.width()) // 2
            py = logo_rect.top() + (logo_rect.height() - pixmap.height()) // 2
            painter.drawPixmap(px, py, pixmap)
        else:
            # Monogram fallback
            monogram = "".join([w[0] for w in name.split()[:2] if w]).upper() or "TV"
            font_mono = QFont("Segoe UI", 10, QFont.Weight.Bold)
            painter.setFont(font_mono)
            painter.setPen(QColor("#475569" if is_dead else "#818CF8"))
            painter.drawText(logo_rect, Qt.AlignmentFlag.AlignCenter, monogram[:3])

        # Favorite star hitbox on right
        star_rect = QRect(rect.right() - 28, rect.top() + (rect.height() - 26) // 2, 26, 26)
        font_star = QFont("Segoe UI Symbol", 13)
        painter.setFont(font_star)
        painter.setPen(QColor("#334155" if is_dead else ("#F59E0B" if is_fav else "#475569")))
        painter.drawText(star_rect, Qt.AlignmentFlag.AlignCenter, "★" if is_fav else "☆")

        # ─── Large 16:9 Preview Thumbnail (106x60) on right of channel row ───
        thumb_w = 106
        thumb_h = 60
        thumb_rect = QRectF(star_rect.left() - 8 - thumb_w, rect.top() + (rect.height() - thumb_h) / 2, thumb_w, thumb_h)

        cid = str(index.data(ChannelRoles.ChannelIdRole) or "")
        thumb_pix = None
        if cid:
            if cid in self._thumb_cache:
                thumb_pix = self._thumb_cache[cid]
            else:
                key = f"{self._profile_name}:{cid}" if self._profile_name else cid
                cached_b = load_cached_thumb(key) or (load_cached_thumb(cid) if self._profile_name else None)
                if cached_b:
                    self.set_thumbnail(cid, cached_b)
                    thumb_pix = self._thumb_cache.get(cid)
                else:
                    self._thumb_cache[cid] = None

        thumb_path = QPainterPath()
        thumb_path.addRoundedRect(thumb_rect, 6.0, 6.0)

        if thumb_pix and not thumb_pix.isNull():
            painter.fillPath(thumb_path, QColor("#090D15"))
            painter.setPen(QPen(QColor("#10B981" if is_playing else "#2A3854"), 1.2 if is_playing else 1.0))
            painter.drawPath(thumb_path)

            painter.save()
            painter.setClipPath(thumb_path)
            painter.drawPixmap(int(thumb_rect.left()), int(thumb_rect.top()), thumb_pix)
            if is_playing:
                badge_r = QRectF(thumb_rect.left() + 4, thumb_rect.top() + 4, 30, 13)
                badge_p = QPainterPath()
                badge_p.addRoundedRect(badge_r, 3.0, 3.0)
                painter.fillPath(badge_p, QColor("#10B981"))
                painter.setFont(QFont("Segoe UI", 6, QFont.Weight.Bold))
                painter.setPen(QColor("#FFFFFF"))
                painter.drawText(badge_r, Qt.AlignmentFlag.AlignCenter, "LIVE")
            painter.restore()
        else:
            # Elegant preview placeholder frame
            painter.fillPath(thumb_path, QColor("#090D15"))
            painter.setPen(QPen(QColor("#10B981" if is_playing else "#1A2438"), 1.2 if is_playing else 1.0))
            painter.drawPath(thumb_path)
            if is_playing and not is_dead:
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                painter.setPen(QColor("#10B981"))
                painter.drawText(thumb_rect, Qt.AlignmentFlag.AlignCenter, "▶ LIVE")
            else:
                painter.setFont(QFont("Segoe UI Symbol", 13))
                painter.setPen(QColor("#25334D"))
                painter.drawText(thumb_rect, Qt.AlignmentFlag.AlignCenter, "📷")

        # ─── Center Multi-Tier Content: Title / EPG / Badges ───
        text_left = logo_rect.right() + 10
        text_right = int(thumb_rect.left()) - 8
        avail_w = max(40, text_right - text_left)

        # Row 1: Number + Channel Name
        num = index.data(ChannelRoles.NumberRole) or 0
        prefix = f"▶ " if is_playing else (f"{num}. " if num else "")
        title_str = f"{prefix}{name}"

        font_title = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
        painter.setFont(font_title)
        painter.setPen(QColor("#6EE7B7" if is_playing else ("#64748B" if is_dead else "#F8FAFC")))
        fm_title = QFontMetrics(font_title)
        elided_title = fm_title.elidedText(title_str, Qt.TextElideMode.ElideRight, avail_w)
        painter.drawText(
            QRect(text_left, rect.top() + 7, avail_w, 20),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            elided_title,
        )

        # Row 2: Subtitle: Live EPG Program or Genre
        epg_now = index.data(ChannelRoles.EpgNowTitleRole) or ""
        genre_name = index.data(ChannelRoles.GenreNameRole) or "Live TV"
        if is_dead:
            sub_str = "Offline / Nicht erreichbar (> 3s Timeout)"
            sub_color = QColor("#EF4444")
        elif epg_now:
            sub_str = f"📺 {epg_now}"
            sub_color = QColor("#38BDF8")
        else:
            sub_str = f"{genre_name}"
            sub_color = QColor("#64748B")

        font_sub = QFont("Segoe UI", 9)
        painter.setFont(font_sub)
        painter.setPen(sub_color)
        fm_sub = QFontMetrics(font_sub)
        elided_sub = fm_sub.elidedText(sub_str, Qt.TextElideMode.ElideRight, avail_w)
        painter.drawText(
            QRect(text_left, rect.top() + 29, avail_w, 18),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            elided_sub,
        )

        # Row 3: Quality & Latency Badges (clean horizontal layout)
        badge_x = float(text_left)
        badge_y = float(rect.top() + 49)
        badge_h = 16.0

        quality = index.data(ChannelRoles.QualityTagRole) or ""
        if quality and not is_dead:
            q_colors = {
                "UHD": ("#4C1D95", "#C4B5FD"),
                "FHD": ("#064E3B", "#6EE7B7"),
                "HD": ("#0E7490", "#67E8F9"),
                "SD": ("#334155", "#CBD5E1"),
                "HEVC": ("#312E81", "#A5B4FC"),
            }
            bg_c, fg_c = q_colors.get(quality, ("#1E293B", "#94A3B8"))
            pill_w = 34.0
            pill_rect = QRectF(badge_x, badge_y, pill_w, badge_h)
            pill_path = QPainterPath()
            pill_path.addRoundedRect(pill_rect, 3.5, 3.5)
            painter.fillPath(pill_path, QColor(bg_c))
            painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            painter.setPen(QColor(fg_c))
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, quality)
            badge_x += pill_w + 5.0

        if is_dead:
            dead_w = 52.0
            dead_rect = QRectF(badge_x, badge_y, dead_w, badge_h)
            dead_path = QPainterPath()
            dead_path.addRoundedRect(dead_rect, 3.5, 3.5)
            painter.fillPath(dead_path, QColor("#7F1D1D"))
            painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            painter.setPen(QColor("#FCA5A5"))
            painter.drawText(dead_rect, Qt.AlignmentFlag.AlignCenter, "OFFLINE")
            badge_x += dead_w + 5.0
        elif latency_ms > 0:
            lat_text = f"{latency_ms}ms"
            lat_w = 44.0
            lat_rect = QRectF(badge_x, badge_y, lat_w, badge_h)
            lat_path = QPainterPath()
            lat_path.addRoundedRect(lat_rect, 3.5, 3.5)
            painter.fillPath(lat_path, QColor("#064E3B" if latency_ms < 600 else "#78350F"))
            painter.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
            painter.setPen(QColor("#6EE7B7" if latency_ms < 600 else "#FCD34D"))
            painter.drawText(lat_rect, Qt.AlignmentFlag.AlignCenter, lat_text)
            badge_x += lat_w + 5.0

        flags = index.data(ChannelRoles.FlagsSummaryRole) or ""
        if flags and ("Archiv" in flags or "PVR" in flags) and not is_dead:
            flag_txt = "PVR" if "PVR" in flags else "Archiv"
            flag_w = 36.0
            if badge_x + flag_w <= text_right:
                flag_rect = QRectF(badge_x, badge_y, flag_w, badge_h)
                flag_path = QPainterPath()
                flag_path.addRoundedRect(flag_rect, 3.5, 3.5)
                painter.fillPath(flag_path, QColor("#1E293B"))
                painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                painter.setPen(QColor("#94A3B8"))
                painter.drawText(flag_rect, Qt.AlignmentFlag.AlignCenter, flag_txt)

        painter.restore()
