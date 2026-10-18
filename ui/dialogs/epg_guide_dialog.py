"""
Multi-Day EPG Program Guide & Timeshift/Catchup Archive Dialog.
Allows browsing programs by date, searching EPG titles, playing archived programs, and downloading them.
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models import Channel, EPGProgram


class EPGGuideDialog(QDialog):
    archive_play_requested = Signal(object, object)      # (Channel, EPGProgram)
    archive_download_requested = Signal(object, object)  # (Channel, EPGProgram)

    def __init__(
        self,
        channel: Channel,
        programs: Optional[List[EPGProgram]] = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"📅 Programmführer & Catchup-Archiv – {channel.name}")
        self.resize(880, 600)
        self._channel = channel
        self._all_programs: List[EPGProgram] = list(programs) if programs is not None else []
        self._filtered_programs: List[EPGProgram] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header + Filter Bar
        top_row = QHBoxLayout()
        count_tag = f" ({len(self._all_programs)} EPG-Einträge)" if programs is not None else ""
        self.lbl_title = QLabel(f"📺 {channel.name}{count_tag}")
        self.lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #38BDF8;")
        top_row.addWidget(self.lbl_title)

        self.lbl_loading = QLabel("⏳ Lade EPG-Daten vom Portal...")
        self.lbl_loading.setStyleSheet(
            "background-color: #1E293B; color: #38BDF8; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600;"
        )
        self.lbl_loading.setVisible(programs is None)
        top_row.addWidget(self.lbl_loading)

        top_row.addStretch(1)

        top_row.addWidget(QLabel("Tag:"))
        self.combo_day = QComboBox()
        self.combo_day.setMinimumWidth(150)
        top_row.addWidget(self.combo_day)

        self.entry_search = QLineEdit()
        self.entry_search.setPlaceholderText("🔍 Sendung suchen...")
        self.entry_search.setFixedWidth(220)
        self.entry_search.textChanged.connect(self._refresh_table)
        top_row.addWidget(self.entry_search)
        layout.addLayout(top_row)

        # Progress bar for asynchronous initial fetch
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(programs is None)
        layout.addWidget(self.progress_bar)

        # Programs Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Zeitraum", "Status / Archiv", "Sendung", "Dauer (Min.)"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table, 1)

        # Program Description Box
        self.txt_descr = QPlainTextEdit()
        self.txt_descr.setReadOnly(True)
        self.txt_descr.setFixedHeight(85)
        self.txt_descr.setPlaceholderText(
            "⏳ EPG-Daten werden geladen..." if programs is None else "Sendung auswählen, um die Beschreibung zu lesen..."
        )
        layout.addWidget(self.txt_descr)

        # Bottom Actions
        btn_row = QHBoxLayout()
        self.btn_play_archive = QPushButton("⏪ Im Archiv / Catchup abspielen")
        self.btn_play_archive.setObjectName("PrimaryButton")
        self.btn_play_archive.setEnabled(False)
        self.btn_play_archive.clicked.connect(self._on_play_archive)
        btn_row.addWidget(self.btn_play_archive)

        self.btn_dl_archive = QPushButton("⬇ Sendung herunterladen")
        self.btn_dl_archive.setEnabled(False)
        self.btn_dl_archive.clicked.connect(self._on_dl_archive)
        btn_row.addWidget(self.btn_dl_archive)

        btn_row.addStretch(1)
        btn_close = QPushButton("Schließen")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self.combo_day.currentIndexChanged.connect(self._refresh_table)

        if programs is not None:
            self._populate_days_combo()
            self._refresh_table()

    def set_programs(self, programs: List[EPGProgram]):
        self._all_programs = list(programs or [])
        self.progress_bar.setVisible(False)
        self.lbl_loading.setVisible(False)
        self.lbl_title.setText(f"📺 {self._channel.name} ({len(self._all_programs)} EPG-Einträge)")
        self.txt_descr.setPlaceholderText("Sendung auswählen, um die Beschreibung zu lesen...")
        if not self._all_programs:
            self.txt_descr.setPlainText("Keine EPG-Einträge für diesen Sender auf dem Portal verfügbar.")
        self._populate_days_combo()
        self._refresh_table()

    def _populate_days_combo(self):
        self.combo_day.blockSignals(True)
        self.combo_day.clear()
        days_set: Dict[str, str] = {"*": "Alle Tage"}
        for p in self._all_programs:
            day_str = (p.time_str or "")[:10]
            if not day_str and p.start_timestamp:
                day_str = datetime.fromtimestamp(p.start_timestamp).strftime("%Y-%m-%d")
            if day_str:
                days_set[day_str] = day_str
        for k, v in days_set.items():
            self.combo_day.addItem(v, k)
        today_str = datetime.now().strftime("%Y-%m-%d")
        idx_today = self.combo_day.findData(today_str)
        if idx_today >= 0:
            self.combo_day.setCurrentIndex(idx_today)
        self.combo_day.blockSignals(False)

    def _refresh_table(self):
        day_filter = self.combo_day.currentData() or "*"
        query = (self.entry_search.text() or "").strip().lower()
        now_ts = int(time.time())

        self._filtered_programs = []
        for p in self._all_programs:
            p_day = (p.time_str or "")[:10]
            if not p_day and p.start_timestamp:
                p_day = datetime.fromtimestamp(p.start_timestamp).strftime("%Y-%m-%d")
            if day_filter != "*" and p_day != day_filter:
                continue
            if query and query not in p.name.lower() and query not in (p.descr or "").lower():
                continue
            self._filtered_programs.append(p)

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self._filtered_programs))
        for row, p in enumerate(self._filtered_programs):
            t1 = p.time_str or (datetime.fromtimestamp(p.start_timestamp).strftime("%Y-%m-%d %H:%M") if p.start_timestamp else "")
            t2 = (p.time_to_str or "").split(" ")[-1][:5]
            span = f"{t1[:16]} – {t2}" if t2 else t1[:16]

            is_live = p.start_timestamp <= now_ts <= p.stop_timestamp if (p.start_timestamp and p.stop_timestamp) else False
            is_past = p.stop_timestamp < now_ts if p.stop_timestamp else False

            if is_live:
                status = "🟢 LIVE"
                color = QColor("#10B981")
            elif p.mark_archive or (is_past and self._channel.enable_tv_archive):
                status = "⏪ Archiv verfügbar"
                color = QColor("#38BDF8")
            elif is_past:
                status = "Vergangen"
                color = QColor("#64748B")
            else:
                status = "Geplant"
                color = QColor("#CBD5E1")

            dur_min = max(0, (p.stop_timestamp - p.start_timestamp) // 60) if (p.start_timestamp and p.stop_timestamp) else (p.duration // 60)

            it_time = QTableWidgetItem(span)
            it_time.setData(Qt.ItemDataRole.UserRole, p)
            it_stat = QTableWidgetItem(status)
            it_stat.setForeground(color)
            it_name = QTableWidgetItem(p.name)

            it_dur = QTableWidgetItem()
            it_dur.setData(Qt.ItemDataRole.DisplayRole, dur_min)
            it_dur.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, it_time)
            self.table.setItem(row, 1, it_stat)
            self.table.setItem(row, 2, it_name)
            self.table.setItem(row, 3, it_dur)

        self.table.setSortingEnabled(True)

    def _selected_program(self) -> EPGProgram | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        it = self.table.item(row, 0)
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def _on_selection_changed(self):
        prog = self._selected_program()
        if not prog:
            self.txt_descr.clear()
            self.btn_play_archive.setEnabled(False)
            self.btn_dl_archive.setEnabled(False)
            return
        self.txt_descr.setPlainText(f"{prog.name}\n\n{prog.descr or 'Keine Beschreibung vorhanden.'}")
        can_archive = bool(prog.mark_archive or self._channel.enable_tv_archive or prog.start_timestamp > 0)
        self.btn_play_archive.setEnabled(can_archive)
        self.btn_dl_archive.setEnabled(can_archive)

    def _on_play_archive(self):
        prog = self._selected_program()
        if prog and self.btn_play_archive.isEnabled():
            self.archive_play_requested.emit(self._channel, prog)
            self.accept()

    def _on_dl_archive(self):
        prog = self._selected_program()
        if prog:
            self.archive_download_requested.emit(self._channel, prog)
