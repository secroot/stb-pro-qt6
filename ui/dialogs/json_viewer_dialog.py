"""
Interactive JSON & Account Details Viewer Dialog.
Provides both a collapsible QTreeWidget view and formatted JSON text view with search & copy.
"""
from __future__ import annotations

import json
from typing import Any
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class JsonViewerDialog(QDialog):
    def __init__(self, title: str, data: Any, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(780, 560)
        self._data = data

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Top Search + Copy Row
        top_row = QHBoxLayout()
        lbl = QLabel(f"📄 {title}")
        lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        top_row.addWidget(lbl)
        top_row.addStretch(1)

        self.entry_search = QLineEdit()
        self.entry_search.setPlaceholderText("🔍 Schlüssel oder Wert suchen...")
        self.entry_search.setFixedWidth(240)
        self.entry_search.textChanged.connect(self._on_filter_tree)
        top_row.addWidget(self.entry_search)

        btn_copy = QPushButton("📋 JSON kopieren")
        btn_copy.clicked.connect(self._copy_json)
        top_row.addWidget(btn_copy)
        layout.addLayout(top_row)

        # Tabs: Strukturierter Baum & Raw JSON
        self.tabs = QTabWidget()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Schlüssel / Index", "Wert", "Typ"])
        self.tree.setColumnWidth(0, 260)
        self.tree.setColumnWidth(1, 360)
        self._populate_tree(self.tree.invisibleRootItem(), data)
        self.tree.expandToDepth(1)
        self.tabs.addTab(self.tree, "🌳 Struktur-Baum")

        self.txt_raw = QPlainTextEdit()
        self.txt_raw.setReadOnly(True)
        self.txt_raw.setFont(QFont("Consolas", 10))
        try:
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            formatted = str(data)
        self.txt_raw.setPlainText(formatted)
        self.tabs.addTab(self.txt_raw, "📝 Formatiertes JSON")

        layout.addWidget(self.tabs, 1)

        btn_close = QPushButton("Schließen")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignRight)

    def _populate_tree(self, parent_item: QTreeWidgetItem, value: Any, key_name: str = ""):
        if isinstance(value, dict):
            node = parent_item if not key_name else QTreeWidgetItem(parent_item, [str(key_name), f"{{ {len(value)} Felder }}", "Object"])
            for k, v in value.items():
                self._populate_tree(node, v, str(k))
        elif isinstance(value, list):
            node = parent_item if not key_name else QTreeWidgetItem(parent_item, [str(key_name), f"[ {len(value)} Einträge ]", "Array"])
            for idx, v in enumerate(value[:500]):
                self._populate_tree(node, v, f"[{idx}]")
        else:
            tname = type(value).__name__
            QTreeWidgetItem(parent_item, [str(key_name), str(value), tname])

    def _on_filter_tree(self, query: str):
        q = (query or "").strip().lower()

        def filter_item(item: QTreeWidgetItem) -> bool:
            match = (
                q in item.text(0).lower()
                or q in item.text(1).lower()
            ) if q else True
            child_match = False
            for i in range(item.childCount()):
                if filter_item(item.child(i)):
                    child_match = True
            visible = match or child_match
            item.setHidden(not visible)
            if child_match and q:
                item.setExpanded(True)
            return visible

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            filter_item(root.child(i))

    def _copy_json(self):
        QApplication.clipboard().setText(self.txt_raw.toPlainText())
