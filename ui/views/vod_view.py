"""
VOD (Movies) & Series Browser View.
Uses virtualized QTableView + VODTableModel + VODFilterProxyModel for zero-lag browsing,
coupled with a rich Movie/Series Detail & Poster Card.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ui.models.vod_model import (
    VODFilterProxyModel,
    VODRoles,
    VODTableModel,
    extract_vod_quality,
    extract_vod_rating,
    extract_vod_title,
    extract_vod_year,
)


class VODView(QWidget):
    mode_changed = Signal(str)                         # "vod" or "series"
    category_selected = Signal(str, str)               # (mode, category_id)
    portal_search_requested = Signal(str, str)         # (mode, search_query)
    play_vod_requested = Signal(dict)                  # (item_dict)
    download_vod_requested = Signal(dict)              # (item_dict)
    copy_vod_url_requested = Signal(dict)              # (item_dict)
    open_series_requested = Signal(dict)               # (series_item_dict)
    favorite_toggled = Signal(str, dict)               # (item_id, item_dict)
    raw_json_requested = Signal(str, dict)             # (title, item_dict)

    def __init__(self, logo_cache=None, parent: QWidget | None = None):
        super().__init__(parent)
        self._logo_cache = logo_cache
        self._current_mode: str = "vod"  # "vod" | "series"
        self._categories: List[Dict[str, Any]] = []
        self._selected_item: Optional[Dict[str, Any]] = None
        self._favorites: Set[str] = set()

        if self._logo_cache:
            self._logo_cache.logo_ready.connect(self._on_poster_ready)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # ── Top Filter & Mode Bar ──
        top_bar = QFrame()
        top_bar.setObjectName("CardFrame")
        top_lay = QHBoxLayout(top_bar)
        top_lay.setContentsMargins(12, 8, 12, 8)
        top_lay.setSpacing(8)

        # Mode Pills: Movies vs Series
        self.btn_mode_vod = QPushButton("🎬 Filme (VOD)")
        self.btn_mode_vod.setObjectName("NavPill")
        self.btn_mode_vod.setProperty("active", "true")
        self.btn_mode_vod.clicked.connect(lambda: self._switch_mode("vod"))
        top_lay.addWidget(self.btn_mode_vod)

        self.btn_mode_series = QPushButton("📺 Serien")
        self.btn_mode_series.setObjectName("NavPill")
        self.btn_mode_series.setProperty("active", "false")
        self.btn_mode_series.clicked.connect(lambda: self._switch_mode("series"))
        top_lay.addWidget(self.btn_mode_series)

        top_lay.addSpacing(4)
        top_lay.addWidget(QLabel("Kategorie:"))
        self.combo_category = QComboBox()
        self.combo_category.setMinimumWidth(140)
        self.combo_category.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.combo_category.setMinimumContentsLength(14)
        self.combo_category.currentIndexChanged.connect(self._on_category_changed)
        top_lay.addWidget(self.combo_category)

        # Local Instant Filter + Portal Global Search
        self.entry_search = QLineEdit()
        self.entry_search.setPlaceholderText("🔍 Lokal filtern oder Suchbegriff für Portal-Suche...")
        self.entry_search.setMinimumWidth(140)
        self.entry_search.textChanged.connect(self._on_local_search_changed)
        self.entry_search.returnPressed.connect(self._on_portal_search)
        top_lay.addWidget(self.entry_search, 1)

        self.btn_portal_search = QPushButton("🌐 Portal-Suche")
        self.btn_portal_search.setToolTip("Durchsucht alle Kategorien auf dem Server")
        self.btn_portal_search.clicked.connect(self._on_portal_search)
        top_lay.addWidget(self.btn_portal_search)

        top_lay.addWidget(QLabel("Sortierung:"))
        self.combo_sort = QComboBox()
        self.combo_sort.addItems(["Standard", "Name A-Z", "Bewertung ↓", "Jahr ↓"])
        self.combo_sort.currentTextChanged.connect(self._on_sort_changed)
        top_lay.addWidget(self.combo_sort)

        self.chk_hd = QCheckBox("✨ HD/4K")
        self.chk_hd.toggled.connect(self._on_filter_toggled)
        top_lay.addWidget(self.chk_hd)

        self.chk_fav = QCheckBox("★ Favoriten")
        self.chk_fav.toggled.connect(self._on_filter_toggled)
        top_lay.addWidget(self.chk_fav)

        layout.addWidget(top_bar)

        # ── Main Splitter: Virtualized Table (Left) + Detail Card (Right) ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left Table Container
        left_box = QFrame()
        left_box.setObjectName("CardFrame")
        left_lay = QVBoxLayout(left_box)
        left_lay.setContentsMargins(8, 8, 8, 8)
        left_lay.setSpacing(6)

        hdr_row = QHBoxLayout()
        self.lbl_status = QLabel("0 Einträge geladen")
        self.lbl_status.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600;")
        hdr_row.addWidget(self.lbl_status)
        hdr_row.addStretch(1)
        left_lay.addLayout(hdr_row)

        self.model = VODTableModel(self)
        self.proxy = VODFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)

        thdr = self.table.horizontalHeader()
        thdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 38)
        thdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        thdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 70)
        thdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 95)
        thdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 80)

        self.table.selectionModel().currentRowChanged.connect(self._on_row_selected)
        self.table.doubleClicked.connect(self._on_double_clicked)
        left_lay.addWidget(self.table, 1)

        splitter.addWidget(left_box)

        # Right Detail Card
        detail_card = QFrame()
        detail_card.setObjectName("CardFrame")
        detail_card.setMinimumWidth(280)
        detail_card.setMaximumWidth(520)
        det_lay = QVBoxLayout(detail_card)
        det_lay.setContentsMargins(14, 14, 14, 14)
        det_lay.setSpacing(10)

        # Poster + Header Row
        poster_row = QHBoxLayout()
        poster_row.setSpacing(12)

        self.lbl_poster = QLabel("🎬\nKein Cover")
        self.lbl_poster.setFixedSize(115, 165)
        self.lbl_poster.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_poster.setStyleSheet(
            "background-color: #080C14; color: #64748B; border: 1px solid #1E293B; border-radius: 8px;"
        )
        poster_row.addWidget(self.lbl_poster)

        meta_col = QVBoxLayout()
        meta_col.setSpacing(5)

        self.lbl_title = QLabel("Wähle einen Titel aus")
        self.lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet("color: #F8FAFC;")
        meta_col.addWidget(self.lbl_title)

        self.lbl_badges = QLabel("Jahr: —  |  ⭐ —  |  Qualität: —")
        self.lbl_badges.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 600;")
        meta_col.addWidget(self.lbl_badges)

        self.lbl_genre = QLabel("Genre: —")
        self.lbl_genre.setWordWrap(True)
        self.lbl_genre.setStyleSheet("color: #94A3B8; font-size: 11px;")
        meta_col.addWidget(self.lbl_genre)

        self.lbl_director = QLabel("Regie: —")
        self.lbl_director.setWordWrap(True)
        self.lbl_director.setStyleSheet("color: #94A3B8; font-size: 11px;")
        meta_col.addWidget(self.lbl_director)

        self.lbl_actors = QLabel("Cast: —")
        self.lbl_actors.setWordWrap(True)
        self.lbl_actors.setStyleSheet("color: #64748B; font-size: 11px;")
        meta_col.addWidget(self.lbl_actors)

        meta_col.addStretch(1)
        poster_row.addLayout(meta_col, 1)
        det_lay.addLayout(poster_row)

        # Plot / Description
        lbl_plot_hdr = QLabel("📖 HANDLUNG & DETAILS")
        lbl_plot_hdr.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_plot_hdr.setStyleSheet("color: #818CF8;")
        det_lay.addWidget(lbl_plot_hdr)

        self.txt_plot = QPlainTextEdit()
        self.txt_plot.setReadOnly(True)
        self.txt_plot.setPlaceholderText("Keine Beschreibung verfügbar.")
        det_lay.addWidget(self.txt_plot, 1)

        # Action Buttons
        self.btn_primary_action = QPushButton("▶ Film im Player starten")
        self.btn_primary_action.setObjectName("PrimaryButton")
        self.btn_primary_action.setFixedHeight(36)
        self.btn_primary_action.setEnabled(False)
        self.btn_primary_action.clicked.connect(self._on_primary_action)
        det_lay.addWidget(self.btn_primary_action)

        act_row1 = QHBoxLayout()
        self.btn_download = QPushButton("⬇ Download")
        self.btn_download.setEnabled(False)
        self.btn_download.clicked.connect(self._on_download)
        act_row1.addWidget(self.btn_download)

        self.btn_copy_url = QPushButton("📋 Stream-URL")
        self.btn_copy_url.setEnabled(False)
        self.btn_copy_url.clicked.connect(self._on_copy_url)
        act_row1.addWidget(self.btn_copy_url)
        det_lay.addLayout(act_row1)

        act_row2 = QHBoxLayout()
        self.btn_fav = QPushButton("☆ Favorit")
        self.btn_fav.setEnabled(False)
        self.btn_fav.clicked.connect(self._on_toggle_fav)
        act_row2.addWidget(self.btn_fav)

        self.btn_json = QPushButton("{ } JSON Info")
        self.btn_json.setEnabled(False)
        self.btn_json.clicked.connect(self._on_show_json)
        act_row2.addWidget(self.btn_json)
        det_lay.addLayout(act_row2)

        splitter.addWidget(detail_card)
        splitter.setSizes([760, 380])
        layout.addWidget(splitter, 1)

    @property
    def current_mode(self) -> str:
        return self._current_mode

    def _switch_mode(self, mode: str):
        if mode == self._current_mode:
            return
        self._current_mode = mode
        for m, btn in (("vod", self.btn_mode_vod), ("series", self.btn_mode_series)):
            btn.setProperty("active", "true" if m == mode else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if mode == "series":
            self.btn_primary_action.setText("📂 Staffeln & Episoden öffnen")
            self.btn_download.setVisible(False)
        else:
            self.btn_primary_action.setText("▶ Film im Player starten")
            self.btn_download.setVisible(True)

        self.mode_changed.emit(mode)

    def set_categories(self, categories: List[Dict[str, Any]]):
        self._categories = list(categories)
        self.combo_category.blockSignals(True)
        self.combo_category.clear()
        self.combo_category.addItem("Alle Kategorien", "*")
        for cat in self._categories:
            cid = str(cat.get("id") or cat.get("category_id") or "*")
            cname = str(cat.get("title") or cat.get("category_name") or cat.get("name") or cid)
            if cid != "*":
                self.combo_category.addItem(cname, cid)
        self.combo_category.blockSignals(False)

    def set_items(self, items: List[Dict[str, Any]], favorites: Optional[Set[str]] = None):
        if favorites is not None:
            self._favorites = set(favorites)
        self.model.set_items(items, self._favorites)
        self._update_status_label()

    def update_favorites(self, favorites: Set[str]):
        self._favorites = set(favorites)
        self.model.set_favorites(self._favorites)
        if self._selected_item:
            item_id = self._get_item_id(self._selected_item)
            self.btn_fav.setText("★ Favorit" if item_id in self._favorites else "☆ Favorit")

    def set_loading(self, text: str):
        self.lbl_status.setText(f"⏳ {text}")

    def _update_status_label(self):
        vis = self.proxy.rowCount()
        tot = self.model.rowCount()
        label = "Serien" if self._current_mode == "series" else "Filme"
        self.lbl_status.setText(f"{vis} / {tot} {label}")

    def _on_category_changed(self, idx: int):
        if idx < 0:
            return
        cat_id = str(self.combo_category.itemData(idx) or "*")
        self.category_selected.emit(self._current_mode, cat_id)

    def _on_local_search_changed(self, text: str):
        self.proxy.set_search(text)
        self._update_status_label()

    def _on_portal_search(self):
        q = (self.entry_search.text() or "").strip()
        if q:
            self.portal_search_requested.emit(self._current_mode, q)

    def _on_sort_changed(self, mode: str):
        self.proxy.set_sort_mode(mode)

    def _on_filter_toggled(self):
        self.proxy.set_hd_only(self.chk_hd.isChecked())
        self.proxy.set_fav_only(self.chk_fav.isChecked())
        self._update_status_label()

    @staticmethod
    def _get_item_id(item: Dict[str, Any]) -> str:
        return str(item.get("id") or item.get("stream_id") or item.get("series_id") or "")

    def _on_row_selected(self, current: QModelIndex, _previous: QModelIndex):
        if not current.isValid():
            return
        item = self.proxy.data(current, VODRoles.ItemDictRole)
        if not isinstance(item, dict):
            return
        self._selected_item = item
        self._populate_detail(item)

    def _populate_detail(self, item: Dict[str, Any]):
        title = extract_vod_title(item)
        year = extract_vod_year(item) or "—"
        rating = extract_vod_rating(item)
        quality = extract_vod_quality(item)
        r_str = f"⭐ {rating:.1f}" if rating > 0 else "⭐ —"

        self.lbl_title.setText(title)
        self.lbl_badges.setText(f"Jahr: {year}  |  {r_str}  |  {quality}")
        self.lbl_genre.setText(f"Genre: {item.get('genres_str') or item.get('genre') or item.get('category_name') or '—'}")
        self.lbl_director.setText(f"Regie: {item.get('director') or '—'}")
        actors = str(item.get("actors") or item.get("cast") or "—")
        self.lbl_actors.setText(f"Cast: {actors[:110] + '…' if len(actors) > 110 else actors}")

        descr = str(item.get("description") or item.get("plot") or item.get("o_name") or "Keine Beschreibung vorhanden.")
        self.txt_plot.setPlainText(descr)

        item_id = self._get_item_id(item)
        is_fav = item_id in self._favorites
        self.btn_fav.setText("★ Favorit" if is_fav else "☆ Favorit")

        self.btn_primary_action.setEnabled(True)
        self.btn_download.setEnabled(self._current_mode == "vod")
        self.btn_copy_url.setEnabled(self._current_mode == "vod")
        self.btn_fav.setEnabled(True)
        self.btn_json.setEnabled(True)

        # Poster
        poster_url = str(
            item.get("screenshot_uri")
            or item.get("stream_icon")
            or item.get("cover")
            or item.get("cover_big")
            or item.get("pic")
            or ""
        )
        if poster_url and self._logo_cache:
            pix = self._logo_cache.get_or_fetch(poster_url, width=115, height=165)
            if pix and not pix.isNull():
                self.lbl_poster.setPixmap(pix)
                return
        self.lbl_poster.clear()
        self.lbl_poster.setText("🎬\nKein Cover")

    def _on_poster_ready(self, url: str):
        if not self._selected_item:
            return
        poster_url = str(
            self._selected_item.get("screenshot_uri")
            or self._selected_item.get("stream_icon")
            or self._selected_item.get("cover")
            or self._selected_item.get("cover_big")
            or self._selected_item.get("pic")
            or ""
        )
        if url == poster_url and self._logo_cache:
            pix = self._logo_cache.get_or_fetch(poster_url, width=115, height=165)
            if pix and not pix.isNull():
                self.lbl_poster.setPixmap(pix)

    def _on_double_clicked(self, index: QModelIndex):
        if not index.isValid():
            return
        self._on_primary_action()

    def _on_primary_action(self):
        if not self._selected_item:
            return
        if self._current_mode == "series":
            self.open_series_requested.emit(self._selected_item)
        else:
            self.play_vod_requested.emit(self._selected_item)

    def _on_download(self):
        if self._selected_item and self._current_mode == "vod":
            self.download_vod_requested.emit(self._selected_item)

    def _on_copy_url(self):
        if self._selected_item and self._current_mode == "vod":
            self.copy_vod_url_requested.emit(self._selected_item)

    def _on_toggle_fav(self):
        if not self._selected_item:
            return
        item_id = self._get_item_id(self._selected_item)
        if item_id:
            self.favorite_toggled.emit(item_id, self._selected_item)

    def _on_show_json(self):
        if self._selected_item:
            self.raw_json_requested.emit(extract_vod_title(self._selected_item), self._selected_item)
