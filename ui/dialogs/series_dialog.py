"""
Series Season & Episode Browser Dialog.
Supports both Xtream Codes (`get_series_info`) and Stalker (`get_ordered_list` seasons/episodes),
with episode search, 1-click playback, direct episode download, and link copy.
"""
from __future__ import annotations

from typing import Any, Dict, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class SeriesBrowserDialog(QDialog):
    episode_play_requested = Signal(dict)      # episode dict
    episode_download_requested = Signal(dict)  # episode dict
    episode_copy_requested = Signal(dict)      # episode dict

    def __init__(
        self,
        series_title: str,
        seasons_data: Dict[str, List[Dict[str, Any]]],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"📺 Serien-Episoden – {series_title}")
        self.resize(820, 540)
        self._series_title = series_title
        self._seasons = dict(seasons_data)
        self._visible_episodes: List[Dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header Row
        top_row = QHBoxLayout()
        lbl = QLabel(f"🎬 {series_title}")
        lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #818CF8;")
        top_row.addWidget(lbl)
        top_row.addStretch(1)

        top_row.addWidget(QLabel("Staffel:"))
        self.combo_season = QComboBox()
        self.combo_season.setMinimumWidth(140)
        for s_key in self._seasons.keys():
            self.combo_season.addItem(f"Staffel {s_key}", s_key)
        self.combo_season.currentIndexChanged.connect(self._refresh_episodes)
        top_row.addWidget(self.combo_season)

        self.entry_search = QLineEdit()
        self.entry_search.setPlaceholderText("🔍 Episode filtern...")
        self.entry_search.setFixedWidth(200)
        self.entry_search.textChanged.connect(self._refresh_episodes)
        top_row.addWidget(self.entry_search)

        layout.addLayout(top_row)

        # Episodes Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Ep. #", "Titel", "Container / Format", "Dauer / Info"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.doubleClicked.connect(lambda _: self._on_play())
        layout.addWidget(self.table, 1)

        # Bottom Action Row
        btn_row = QHBoxLayout()
        btn_play = QPushButton("▶ Episode abspielen")
        btn_play.setObjectName("PrimaryButton")
        btn_play.clicked.connect(self._on_play)
        btn_row.addWidget(btn_play)

        btn_dl = QPushButton("⬇ Episode herunterladen")
        btn_dl.clicked.connect(self._on_download)
        btn_row.addWidget(btn_dl)

        btn_copy = QPushButton("📋 Stream-Link kopieren")
        btn_copy.clicked.connect(self._on_copy)
        btn_row.addWidget(btn_copy)

        btn_row.addStretch(1)
        btn_close = QPushButton("Schließen")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self._refresh_episodes()

    def _refresh_episodes(self):
        s_key = self.combo_season.currentData()
        raw_eps = self._seasons.get(str(s_key), []) if s_key is not None else []
        query = (self.entry_search.text() or "").strip().lower()

        self._visible_episodes = []
        for idx, ep in enumerate(raw_eps, start=1):
            title = str(ep.get("title") or ep.get("name") or f"Episode {idx}")
            if query and query not in title.lower():
                continue
            self._visible_episodes.append(ep)

        self.table.setRowCount(len(self._visible_episodes))
        for row, ep in enumerate(self._visible_episodes):
            ep_num = str(
                ep.get("episode_num")
                or ep.get("episode_number")
                or ep.get("series_number")
                or (row + 1)
            )
            title = str(ep.get("title") or ep.get("name") or f"Episode {ep_num}")
            ext = str(ep.get("container_extension") or "mp4").upper()
            info = ep.get("info") if isinstance(ep.get("info"), dict) else {}
            dur = str(info.get("duration") or ep.get("time") or "—")

            self.table.setItem(row, 0, QTableWidgetItem(f"E{ep_num.zfill(2)}"))
            self.table.setItem(row, 1, QTableWidgetItem(title))
            self.table.setItem(row, 2, QTableWidgetItem(ext))
            self.table.setItem(row, 3, QTableWidgetItem(dur))

        if self._visible_episodes:
            self.table.selectRow(0)

    def _selected_episode(self) -> Dict[str, Any] | None:
        row = self.table.currentRow()
        if 0 <= row < len(self._visible_episodes):
            return self._visible_episodes[row]
        return None

    def _on_play(self):
        ep = self._selected_episode()
        if ep:
            self.episode_play_requested.emit(ep)
            self.accept()

    def _on_download(self):
        ep = self._selected_episode()
        if ep:
            self.episode_download_requested.emit(ep)

    def _on_copy(self):
        ep = self._selected_episode()
        if ep:
            self.episode_copy_requested.emit(ep)
