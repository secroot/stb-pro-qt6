"""
Interactive System & Pentest Log Console View.
Features real-time log streaming via Qt Signals, level filtering, keyword search, clipboard export, and file export.
"""
from __future__ import annotations

import time
from typing import List, Tuple
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ConsoleView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._entries: List[Tuple[str, str, str]] = []  # (timestamp, level, text)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Top Toolbar Card
        bar = QFrame()
        bar.setObjectName("CardFrame")
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(12, 8, 12, 8)
        bar_lay.setSpacing(10)

        lbl_title = QLabel("🖥 SYSTEM- & PENTEST-KONSOLE")
        lbl_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #38BDF8;")
        bar_lay.addWidget(lbl_title)

        self.lbl_count = QLabel("0 Einträge")
        self.lbl_count.setStyleSheet("color: #64748B; font-size: 11px;")
        bar_lay.addWidget(self.lbl_count)

        bar_lay.addStretch(1)

        bar_lay.addWidget(QLabel("Level:"))
        self.combo_level = QComboBox()
        self.combo_level.addItems(["Alle", "Info", "Warnung / WAF", "Fehler"])
        self.combo_level.currentTextChanged.connect(self._rebuild_view)
        bar_lay.addWidget(self.combo_level)

        self.entry_search = QLineEdit()
        self.entry_search.setPlaceholderText("🔍 Logs durchsuchen...")
        self.entry_search.setFixedWidth(220)
        self.entry_search.textChanged.connect(self._rebuild_view)
        bar_lay.addWidget(self.entry_search)

        self.chk_autoscroll = QCheckBox("Auto-Scroll")
        self.chk_autoscroll.setChecked(True)
        bar_lay.addWidget(self.chk_autoscroll)

        btn_copy = QPushButton("📋 Kopieren")
        btn_copy.clicked.connect(self._copy_all)
        bar_lay.addWidget(btn_copy)

        btn_save = QPushButton("💾 Speichern")
        btn_save.clicked.connect(self._save_to_file)
        bar_lay.addWidget(btn_save)

        btn_clear = QPushButton("🗑 Leeren")
        btn_clear.setObjectName("DangerButton")
        btn_clear.clicked.connect(self.clear_logs)
        bar_lay.addWidget(btn_clear)

        layout.addWidget(bar)

        # Log Output Box
        self.txt_console = QPlainTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setMaximumBlockCount(5000)
        self.txt_console.setFont(QFont("Consolas", 10))
        self.txt_console.setStyleSheet(
            "background-color: #060911; color: #E2E8F0; border: 1px solid #1E293B; "
            "border-radius: 8px; padding: 10px;"
        )
        layout.addWidget(self.txt_console, 1)

    @staticmethod
    def _detect_level(msg: str) -> str:
        low = msg.lower()
        if any(k in low for k in ("fehler", "error", "exception", "failed", "❌", "abgelehnt")):
            return "Fehler"
        if any(k in low for k in ("warn", "429", "rate-limit", "cooldown", "waf", "⚠", "timeout")):
            return "Warnung / WAF"
        return "Info"

    def append_log(self, message: str):
        ts = time.strftime("%H:%M:%S")
        lvl = self._detect_level(message)
        self._entries.append((ts, lvl, message))
        if len(self._entries) > 5000:
            self._entries = self._entries[-4000:]

        self.lbl_count.setText(f"{len(self._entries)} Einträge")

        if self._matches_filter(lvl, message):
            self.txt_console.appendPlainText(f"[{ts}] {message}")
            if self.chk_autoscroll.isChecked():
                sb = self.txt_console.verticalScrollBar()
                sb.setValue(sb.maximum())

    def _matches_filter(self, lvl: str, msg: str) -> bool:
        sel_lvl = self.combo_level.currentText()
        if sel_lvl != "Alle" and lvl != sel_lvl:
            return False
        q = (self.entry_search.text() or "").strip().lower()
        if q and q not in msg.lower():
            return False
        return True

    def _rebuild_view(self):
        lines = [
            f"[{ts}] {msg}"
            for ts, lvl, msg in self._entries
            if self._matches_filter(lvl, msg)
        ]
        self.txt_console.setPlainText("\n".join(lines))
        if self.chk_autoscroll.isChecked():
            sb = self.txt_console.verticalScrollBar()
            sb.setValue(sb.maximum())

    def clear_logs(self):
        self._entries.clear()
        self.txt_console.clear()
        self.lbl_count.setText("0 Einträge")

    def _copy_all(self):
        QGuiApplication.clipboard().setText(self.txt_console.toPlainText())

    def _save_to_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Konsole speichern", "stb_pro_console.log", "Log-Dateien (*.log *.txt)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.txt_console.toPlainText())
            except Exception:
                pass
