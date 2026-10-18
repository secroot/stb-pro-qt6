"""
MAC Hit Database Explorer Dialog.
Browses `mac_database.json`, filters by Portal URL or search text, removes duplicates,
exports hits, applies a MAC directly to the active profile, or sends portal MACs to the scanner.
"""
from __future__ import annotations

from typing import Any, Dict, List
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.mac_database import MacDatabase
from .mac_pattern_dialog import MacPatternDialog


class MacDatabaseDialog(QDialog):
    apply_mac_requested = Signal(str, str, str)  # (portal_url, mac, model)
    send_to_scanner_requested = Signal(list)     # list of MAC strings

    def __init__(self, mac_db: MacDatabase, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("🗄 Persistente MAC Hit-Datenbank")
        self.resize(1020, 580)
        self._db = mac_db
        self._visible_rows: List[Dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header + Filter Row
        top_row = QHBoxLayout()
        self.lbl_summary = QLabel("🗄 MAC Hit-Datenbank")
        self.lbl_summary.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_summary.setStyleSheet("color: #10B981;")
        top_row.addWidget(self.lbl_summary)
        top_row.addStretch(1)

        top_row.addWidget(QLabel("Portal:"))
        self.combo_portal = QComboBox()
        self.combo_portal.setMinimumWidth(240)
        self.combo_portal.currentIndexChanged.connect(self.refresh_view)
        top_row.addWidget(self.combo_portal)

        self.entry_search = QLineEdit()
        self.entry_search.setPlaceholderText("🔍 MAC, Tarif oder Ablaufdatum filtern...")
        self.entry_search.setFixedWidth(230)
        self.entry_search.textChanged.connect(self.refresh_view)
        top_row.addWidget(self.entry_search)
        layout.addLayout(top_row)

        # Table (8 Spalten inkl. Proxy/VPN Standort)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Portal URL", "MAC-Adresse", "Status", "Ablaufdatum", "Kanäle", "Modell", "Proxy / VPN", "Zuletzt geprüft"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 8):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.doubleClicked.connect(lambda _: self._on_apply_selected())
        layout.addWidget(self.table, 1)

        # Bottom Actions
        btn_row = QHBoxLayout()

        btn_pattern = QPushButton("🧠 Nach MAC-Mustern suchen")
        btn_pattern.setStyleSheet("font-weight: bold; color: #38BDF8;")
        btn_pattern.clicked.connect(self._on_pattern_search)
        btn_row.addWidget(btn_pattern)

        btn_apply = QPushButton("🚀 Im aktiven Profil verbinden")
        btn_apply.setObjectName("PrimaryButton")
        btn_apply.clicked.connect(self._on_apply_selected)
        btn_row.addWidget(btn_apply)

        btn_send_scan = QPushButton("🎯 Sichtbare MACs an Scanner")
        btn_send_scan.clicked.connect(self._on_send_to_scanner)
        btn_row.addWidget(btn_send_scan)

        btn_copy = QPushButton("📋 Kopieren")
        btn_copy.clicked.connect(self._on_copy_mac)
        btn_row.addWidget(btn_copy)

        btn_dedup = QPushButton("🧹 Bereinigen")
        btn_dedup.clicked.connect(self._on_dedup)
        btn_row.addWidget(btn_dedup)

        btn_export = QPushButton("💾 Export (.txt)")
        btn_export.clicked.connect(self._on_export)
        btn_row.addWidget(btn_export)

        btn_del = QPushButton("🗑 Löschen")
        btn_del.setObjectName("DangerButton")
        btn_del.clicked.connect(self._on_delete_selected)
        btn_row.addWidget(btn_del)

        btn_row.addStretch(1)
        btn_close = QPushButton("Schließen")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self._reload_portals()
        self.refresh_view()

    def _reload_portals(self):
        self.combo_portal.blockSignals(True)
        self.combo_portal.clear()
        self.combo_portal.addItem("Alle Portale", "*")
        for p in self._db.get_portals():
            self.combo_portal.addItem(p, p)
        self.combo_portal.blockSignals(False)

    def refresh_view(self):
        portal_filter = self.combo_portal.currentData() or "*"
        query = (self.entry_search.text() or "").strip().lower()

        raw_entries = self._db.get_entries(None if portal_filter == "*" else portal_filter)
        self._visible_rows = []
        for e in raw_entries:
            if query:
                hay = f"{e.get('portal', '')} {e.get('mac', '')} {e.get('status', '')} {e.get('expiry', '')}".lower()
                if query not in hay:
                    continue
            self._visible_rows.append(e)

        self.lbl_summary.setText(f"🗄 MAC Hit-Datenbank ({len(self._visible_rows)} / {self._db.total_count()} Treffer)")
        self.table.setRowCount(len(self._visible_rows))
        for row, e in enumerate(self._visible_rows):
            status = str(e.get("status", "OK"))
            it_status = QTableWidgetItem(status)
            if "HOT" in status.upper() or "AKTIV" in status.upper():
                it_status.setForeground(QColor("#10B981"))
            else:
                it_status.setForeground(QColor("#F59E0B"))

            loc = str(e.get("vpn_location") or e.get("proxy_location") or "—")
            it_loc = QTableWidgetItem(loc)
            if loc != "—":
                it_loc.setForeground(QColor("#38BDF8"))
            else:
                it_loc.setForeground(QColor("#94A3B8"))

            self.table.setItem(row, 0, QTableWidgetItem(str(e.get("portal", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(e.get("mac", ""))))
            self.table.setItem(row, 2, it_status)
            self.table.setItem(row, 3, QTableWidgetItem(str(e.get("expiry", "—"))))
            self.table.setItem(row, 4, QTableWidgetItem(str(e.get("channels", 0))))
            self.table.setItem(row, 5, QTableWidgetItem(str(e.get("model", "MAG 250"))))
            self.table.setItem(row, 6, it_loc)
            self.table.setItem(row, 7, QTableWidgetItem(str(e.get("last_seen", "—"))))

    def _selected_entry(self) -> Dict[str, Any] | None:
        row = self.table.currentRow()
        if 0 <= row < len(self._visible_rows):
            return self._visible_rows[row]
        return None

    def _on_pattern_search(self):
        portal_filter = self.combo_portal.currentData() or "*"
        dlg = MacPatternDialog(self._db, initial_portal=portal_filter, parent=self)
        dlg.send_to_scanner_requested.connect(self._on_pattern_to_scanner)
        dlg.exec()

    def _on_pattern_to_scanner(self, macs: list):
        if macs:
            self.send_to_scanner_requested.emit(macs)
            self.accept()

    def _on_apply_selected(self):
        e = self._selected_entry()
        if not e:
            return
        self.apply_mac_requested.emit(
            str(e.get("portal", "")),
            str(e.get("mac", "")),
            str(e.get("model", "MAG 250")),
        )
        self.accept()

    def _on_send_to_scanner(self):
        macs = [str(e.get("mac", "")) for e in self._visible_rows if e.get("mac")]
        if macs:
            self.send_to_scanner_requested.emit(macs)
            self.accept()

    def _on_copy_mac(self):
        e = self._selected_entry()
        if e and e.get("mac"):
            QApplication.clipboard().setText(str(e["mac"]))

    def _on_dedup(self):
        removed = self._db.deduplicate()
        self.refresh_view()
        QMessageBox.information(self, "Bereinigung", f"{removed} doppelte MAC-Einträge entfernt.")

    def _on_delete_selected(self):
        e = self._selected_entry()
        if e:
            self._db.remove_entry(str(e.get("portal", "")), str(e.get("mac", "")))
            self.refresh_view()

    def _on_export(self):
        if not self._visible_rows:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "MAC Hits exportieren", "mac_hits_export.txt", "Textdateien (*.txt)"
        )
        if path:
            lines = [
                f"{e.get('mac')} | {e.get('portal')} | Exp: {e.get('expiry')} | Ch: {e.get('channels')}"
                for e in self._visible_rows
            ]
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
