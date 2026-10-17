"""
Virtualized VOD & Series Table Model and Sort/Filter Proxy Model.
Handles thousands of Movies and Series items effortlessly without blocking the UI thread.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtGui import QColor


class VODRoles:
    ItemDictRole = Qt.ItemDataRole.UserRole + 1
    ItemIdRole = Qt.ItemDataRole.UserRole + 2
    TitleRole = Qt.ItemDataRole.UserRole + 3
    YearRole = Qt.ItemDataRole.UserRole + 4
    RatingRole = Qt.ItemDataRole.UserRole + 5
    QualityRole = Qt.ItemDataRole.UserRole + 6
    IsFavRole = Qt.ItemDataRole.UserRole + 7


def extract_vod_title(item: Dict[str, Any]) -> str:
    return str(item.get("name") or item.get("o_name") or item.get("title") or "Unbekannt")


def extract_vod_year(item: Dict[str, Any]) -> str:
    y = str(item.get("year") or item.get("releaseDate") or item.get("added") or "")
    return y[:4] if len(y) >= 4 else y


def extract_vod_rating(item: Dict[str, Any]) -> float:
    for k in ("rating_imdb", "rating_kinopoisk", "rating", "rating_5based"):
        val = item.get(k)
        if val not in (None, "", "0", 0):
            try:
                return float(str(val).replace(",", "."))
            except Exception:
                pass
    return 0.0


def extract_vod_quality(item: Dict[str, Any]) -> str:
    title = extract_vod_title(item).upper()
    if bool(item.get("hd")) or "4K" in title or "UHD" in title:
        if "4K" in title or "UHD" in title:
            return "4K UHD"
        return "HD"
    if "1080" in title or "FHD" in title:
        return "FHD"
    return "SD"


class VODTableModel(QAbstractTableModel):
    """Virtualized table model for Movies (VOD) and Series."""

    COLUMNS = ("★", "Titel", "Jahr", "Bewertung", "Qualität")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[Dict[str, Any]] = []
        self._favorites: Set[str] = set()

    def set_items(self, items: List[Dict[str, Any]], favorites: Optional[Set[str]] = None):
        self.beginResetModel()
        self._items = list(items)
        if favorites is not None:
            self._favorites = set(favorites)
        self.endResetModel()

    def set_favorites(self, favorites: Set[str]):
        self._favorites = set(favorites)
        if self._items:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._items) - 1, 0),
                [Qt.ItemDataRole.DisplayRole, VODRoles.IsFavRole],
            )

    def item_at(self, row: int) -> Optional[Dict[str, Any]]:
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._items)):
            return None

        item = self._items[index.row()]
        item_id = str(item.get("id") or item.get("stream_id") or item.get("series_id") or index.row())
        is_fav = item_id in self._favorites
        col = index.column()

        if role == VODRoles.ItemDictRole:
            return item
        if role == VODRoles.ItemIdRole:
            return item_id
        if role == VODRoles.TitleRole:
            return extract_vod_title(item)
        if role == VODRoles.YearRole:
            return extract_vod_year(item)
        if role == VODRoles.RatingRole:
            return extract_vod_rating(item)
        if role == VODRoles.QualityRole:
            return extract_vod_quality(item)
        if role == VODRoles.IsFavRole:
            return is_fav

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return "★" if is_fav else "☆"
            if col == 1:
                return extract_vod_title(item)
            if col == 2:
                return extract_vod_year(item) or "—"
            if col == 3:
                r = extract_vod_rating(item)
                return f"⭐ {r:.1f}" if r > 0 else "—"
            if col == 4:
                return extract_vod_quality(item)

        if role == Qt.ItemDataRole.ForegroundRole:
            if col == 0:
                return QColor("#F59E0B" if is_fav else "#475569")
            if col == 3:
                r = extract_vod_rating(item)
                if r >= 7.5:
                    return QColor("#10B981")
                if r >= 5.5:
                    return QColor("#F59E0B")
            if col == 4:
                q = extract_vod_quality(item)
                if "4K" in q:
                    return QColor("#C4B5FD")
                if "HD" in q:
                    return QColor("#67E8F9")

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (0, 2, 3, 4):
                return int(Qt.AlignmentFlag.AlignCenter)

        return None


class VODFilterProxyModel(QSortFilterProxyModel):
    """Supports local instant search, HD filter, Favorites filter, and custom sorting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search: str = ""
        self._hd_only: bool = False
        self._fav_only: bool = False
        self._sort_mode: str = "Standard"
        self.setDynamicSortFilter(True)

    def set_search(self, query: str):
        self._search = (query or "").strip().lower()
        self.invalidateFilter()

    def set_hd_only(self, hd_only: bool):
        self._hd_only = bool(hd_only)
        self.invalidateFilter()

    def set_fav_only(self, fav_only: bool):
        self._fav_only = bool(fav_only)
        self.invalidateFilter()

    def set_sort_mode(self, mode: str):
        self._sort_mode = mode
        if mode == "Name A-Z":
            self.sort(1, Qt.SortOrder.AscendingOrder)
        elif mode == "Bewertung ↓":
            self.sort(3, Qt.SortOrder.DescendingOrder)
        elif mode == "Jahr ↓":
            self.sort(2, Qt.SortOrder.DescendingOrder)
        else:
            self.sort(-1)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        if not model:
            return True
        idx = model.index(source_row, 0, source_parent)

        if self._fav_only and not model.data(idx, VODRoles.IsFavRole):
            return False

        if self._hd_only:
            q = model.data(idx, VODRoles.QualityRole) or ""
            if "HD" not in q and "4K" not in q:
                return False

        if self._search:
            title = (model.data(idx, VODRoles.TitleRole) or "").lower()
            year = (model.data(idx, VODRoles.YearRole) or "").lower()
            if self._search not in title and self._search not in year:
                return False

        return True

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        col = left.column()
        model = self.sourceModel()
        if not model:
            return False
        if col == 3:
            r_left = model.data(left, VODRoles.RatingRole) or 0.0
            r_right = model.data(right, VODRoles.RatingRole) or 0.0
            return float(r_left) < float(r_right)
        if col == 2:
            y_left = model.data(left, VODRoles.YearRole) or ""
            y_right = model.data(right, VODRoles.YearRole) or ""
            return str(y_left) < str(y_right)
        t_left = (model.data(left, VODRoles.TitleRole) or "").lower()
        t_right = (model.data(right, VODRoles.TitleRole) or "").lower()
        return t_left < t_right
