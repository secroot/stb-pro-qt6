"""
Interactive Protocol & HTTP Exchange Inspector View.
Replaces the static text dump of the legacy Tkinter version with a live, searchable HTTP traffic table,
JSON pretty-printer, header inspector, 1-click cURL generator, and on-demand Handshake / Endpoint tester.
"""
from __future__ import annotations

import json
from typing import List
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models import HttpLogEntry


class InspectorView(QWidget):
    handshake_test_requested = Signal()
    profile_dump_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._entries: List[HttpLogEntry] = []
        self._filtered_entries: List[HttpLogEntry] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # ── Top Control Bar ──
        top_bar = QFrame()
        top_bar.setObjectName("CardFrame")
        top_lay = QHBoxLayout(top_bar)
        top_lay.setContentsMargins(12, 8, 12, 8)
        top_lay.setSpacing(10)

        lbl_title = QLabel("🔬 PROTOKOLL- & HTTP-INSPECTOR")
        lbl_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #818CF8;")
        top_lay.addWidget(lbl_title)

        self.lbl_counter = QLabel("0 Requests")
        self.lbl_counter.setStyleSheet("color: #94A3B8; font-size: 11px;")
        top_lay.addWidget(self.lbl_counter)

        top_lay.addStretch(1)

        self.entry_filter = QLineEdit()
        self.entry_filter.setPlaceholderText("🔍 URL, Action oder Statuscode filtern...")
        self.entry_filter.setFixedWidth(250)
        self.entry_filter.textChanged.connect(self._refresh_table)
        top_lay.addWidget(self.entry_filter)

        self.chk_pause = QCheckBox("Aufzeichnung pausieren")
        top_lay.addWidget(self.chk_pause)

        btn_test_hs = QPushButton("⚡ Handshake & Account prüfen")
        btn_test_hs.setObjectName("PrimaryButton")
        btn_test_hs.clicked.connect(self.handshake_test_requested.emit)
        top_lay.addWidget(btn_test_hs)

        btn_dump = QPushButton("📄 Client-Status Dump")
        btn_dump.clicked.connect(self.profile_dump_requested.emit)
        top_lay.addWidget(btn_dump)

        btn_clear = QPushButton("🗑 Leeren")
        btn_clear.setObjectName("DangerButton")
        btn_clear.clicked.connect(self.clear_entries)
        top_lay.addWidget(btn_clear)

        layout.addWidget(top_bar)

        # ── Main Vertical Splitter: Request Table (Top) + Detail Tabs (Bottom) ──
        splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Zeit", "Methode", "Status", "Dauer (ms)", "URL / Endpoint"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        splitter.addWidget(self.table)

        # Detail Inspection Tabs
        self.tabs = QTabWidget()

        # Tab 1: Formatted Response / JSON
        tab_resp = QWidget()
        resp_lay = QVBoxLayout(tab_resp)
        resp_lay.setContentsMargins(8, 8, 8, 8)
        self.txt_response = QPlainTextEdit()
        self.txt_response.setReadOnly(True)
        self.txt_response.setFont(QFont("Consolas", 10))
        self.txt_response.setPlaceholderText("Wähle oben einen HTTP-Request aus, um die Server-Antwort zu inspizieren...")
        resp_lay.addWidget(self.txt_response)
        self.tabs.addTab(tab_resp, "📦 Response Body / JSON")

        # Tab 2: Request Headers & Params
        tab_hdr = QWidget()
        hdr_lay = QVBoxLayout(tab_hdr)
        hdr_lay.setContentsMargins(8, 8, 8, 8)
        self.txt_headers = QPlainTextEdit()
        self.txt_headers.setReadOnly(True)
        self.txt_headers.setFont(QFont("Consolas", 10))
        hdr_lay.addWidget(self.txt_headers)
        self.tabs.addTab(tab_hdr, "🔑 Request Header & Cookies")

        # Tab 3: cURL Replay Generator
        tab_curl = QWidget()
        curl_lay = QVBoxLayout(tab_curl)
        curl_lay.setContentsMargins(8, 8, 8, 8)
        curl_top = QHBoxLayout()
        curl_top.addWidget(QLabel("Reproduzierbares cURL-Kommando (inkl. Cookies, Token & User-Agent):"))
        curl_top.addStretch(1)
        btn_copy_curl = QPushButton("📋 cURL in Zwischenablage kopieren")
        btn_copy_curl.setObjectName("PrimaryButton")
        btn_copy_curl.clicked.connect(self._copy_curl)
        curl_top.addWidget(btn_copy_curl)
        curl_lay.addLayout(curl_top)

        self.txt_curl = QPlainTextEdit()
        self.txt_curl.setReadOnly(True)
        self.txt_curl.setFont(QFont("Consolas", 10))
        curl_lay.addWidget(self.txt_curl)
        self.tabs.addTab(tab_curl, "🐚 cURL Export")

        # Tab 4: Client / Handshake Summary Dump
        tab_summary = QWidget()
        sum_lay = QVBoxLayout(tab_summary)
        sum_lay.setContentsMargins(8, 8, 8, 8)
        self.txt_summary = QPlainTextEdit()
        self.txt_summary.setReadOnly(True)
        self.txt_summary.setFont(QFont("Consolas", 10))
        self.txt_summary.setPlaceholderText("Klicke auf 'Handshake & Account prüfen' oder 'Client-Status Dump'...")
        sum_lay.addWidget(self.txt_summary)
        self.tabs.addTab(tab_summary, "🛡 Account & Handshake Bericht")

        splitter.addWidget(self.tabs)
        splitter.setSizes([280, 360])
        layout.addWidget(splitter, 1)

    def add_http_entry(self, entry: HttpLogEntry):
        if self.chk_pause.isChecked():
            return
        self._entries.append(entry)
        if len(self._entries) > 600:
            self._entries = self._entries[-500:]
        self.lbl_counter.setText(f"{len(self._entries)} Requests")

        if self._matches(entry):
            self._filtered_entries.append(entry)
            self._append_row(entry)

    def _matches(self, entry: HttpLogEntry) -> bool:
        q = (self.entry_filter.text() or "").strip().lower()
        if not q:
            return True
        return (
            q in entry.url.lower()
            or q in entry.method.lower()
            or q in str(entry.status_code)
            or q in (entry.response_preview or "").lower()
        )

    def _refresh_table(self):
        self._filtered_entries = [e for e in self._entries if self._matches(e)]
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for e in self._filtered_entries:
            self._append_row(e)
        self.table.setSortingEnabled(True)

    def _append_row(self, entry: HttpLogEntry):
        row = self.table.rowCount()
        self.table.insertRow(row)

        it_time = QTableWidgetItem(entry.timestamp)
        it_time.setData(Qt.ItemDataRole.UserRole, entry)
        it_method = QTableWidgetItem(entry.method)

        it_status = QTableWidgetItem()
        it_status.setData(Qt.ItemDataRole.DisplayRole, int(entry.status_code))
        it_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        it_dur = QTableWidgetItem()
        it_dur.setData(Qt.ItemDataRole.DisplayRole, int(entry.elapsed_ms))
        it_dur.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        it_url = QTableWidgetItem(entry.url)

        if 200 <= entry.status_code < 300:
            it_status.setForeground(QColor("#10B981"))
        elif entry.status_code in (401, 403, 429):
            it_status.setForeground(QColor("#F59E0B"))
        elif entry.status_code >= 400 or entry.status_code == 0:
            it_status.setForeground(QColor("#EF4444"))

        self.table.setItem(row, 0, it_time)
        self.table.setItem(row, 1, it_method)
        self.table.setItem(row, 2, it_status)
        self.table.setItem(row, 3, it_dur)
        self.table.setItem(row, 4, it_url)

    def _on_row_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        it_time = self.table.item(row, 0)
        entry = it_time.data(Qt.ItemDataRole.UserRole) if it_time else None
        if not entry or not isinstance(entry, HttpLogEntry):
            return

        # Format Response Body (Pretty JSON if applicable)
        raw_body = (entry.response_preview or "").strip()
        formatted_body = raw_body
        if raw_body.startswith("{") or raw_body.startswith("["):
            try:
                parsed = json.loads(raw_body)
                formatted_body = json.dumps(parsed, indent=2, ensure_ascii=False)
            except Exception:
                pass
        self.txt_response.setPlainText(formatted_body or "(Leerer oder binärer Response-Body)")

        # Headers
        hdr_lines = [f"{entry.method} {entry.url}", f"HTTP Status: {entry.status_code} ({entry.elapsed_ms} ms)", ""]
        hdr_lines.append("── Request Headers ──")
        for k, v in entry.request_headers.items():
            hdr_lines.append(f"{k}: {v}")
        if entry.request_params:
            hdr_lines.append("\n── Request Payload ──")
            hdr_lines.append(entry.request_params)
        self.txt_headers.setPlainText("\n".join(hdr_lines))

        # cURL
        self.txt_curl.setPlainText(entry.to_curl())

    def set_summary_report(self, text: str, switch_tab: bool = True):
        self.txt_summary.setPlainText(text)
        if switch_tab:
            self.tabs.setCurrentIndex(3)

    def _copy_curl(self):
        QGuiApplication.clipboard().setText(self.txt_curl.toPlainText())

    def clear_entries(self):
        self._entries.clear()
        self._filtered_entries.clear()
        self.table.setRowCount(0)
        self.txt_response.clear()
        self.txt_headers.clear()
        self.txt_curl.clear()
        self.lbl_counter.setText("0 Requests")
