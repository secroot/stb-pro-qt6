"""
Dialog zur Visualisierung von MAC-Mustern und Generierung von Permutationen.
Ermöglicht das Erkennen von Hot-Prefixes (z. B. B5-Reihe) und den direkten
Transfer von generierten Permutationen in den Scanner oder als TXT-Export.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.mac_database import MacDatabase
from core.pattern_predictor import MacPatternPredictor, MacClusterPattern


class MacPatternDialog(QDialog):
    """
    Dialog für die Mustererkennung und Permutations-Generierung.
    """
    send_to_scanner_requested = Signal(list)  # List of generated MACs

    def __init__(self, mac_db: MacDatabase, initial_portal: Optional[str] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("🧠 Intelligenter MAC-Muster-Prädiktor & Permutations-Generator")
        self.resize(960, 640)
        self._db = mac_db
        self._initial_portal = initial_portal
        self._patterns: List[MacClusterPattern] = []
        self._generated_macs: List[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header Info Card
        hdr_layout = QVBoxLayout()
        lbl_title = QLabel("🧠 MAC-Muster-Prädiktor & Permutationen")
        lbl_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #38BDF8;")
        hdr_layout.addWidget(lbl_title)

        self.lbl_subtitle = QLabel(
            "Erkennt signifikante Treffer-Häufungen (z. B. '00:1A:79:B5:XX:XX') und dichte "
            "Provisioning-Blöcke in der MAC-Datenbank zur gezielten Permutation."
        )
        self.lbl_subtitle.setStyleSheet("color: #94A3B8; font-size: 11px;")
        hdr_layout.addWidget(self.lbl_subtitle)
        layout.addLayout(hdr_layout)

        # Controls Row
        ctrl_row = QHBoxLayout()
        ctrl_row.addWidget(QLabel("Datenbasis:"))
        self.combo_portal = QComboBox()
        self.combo_portal.setMinimumWidth(220)
        self.combo_portal.currentIndexChanged.connect(self._run_analysis)
        ctrl_row.addWidget(self.combo_portal)

        ctrl_row.addWidget(QLabel("Strategie:"))
        self.combo_strategy = QComboBox()
        self.combo_strategy.addItem("Cluster-Vollbereich (/24 Sub-Blöcke)", "cluster_full")
        self.combo_strategy.addItem("Nahbereich (± 40 um jeden Treffer)", "neighbor_sweep")
        self.combo_strategy.addItem("Reihen-Sampling (Gitter über 4-Byte Präfixe)", "series_sample")
        self.combo_strategy.currentIndexChanged.connect(self._generate_candidates)
        ctrl_row.addWidget(self.combo_strategy)

        ctrl_row.addWidget(QLabel("Max. MACs:"))
        self.spin_count = QSpinBox()
        self.spin_count.setRange(20, 10000)
        self.spin_count.setSingleStep(100)
        self.spin_count.setValue(500)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._generate_candidates)
        self.spin_count.valueChanged.connect(lambda: self._debounce_timer.start(200))
        ctrl_row.addWidget(self.spin_count)

        btn_refresh = QPushButton("🔄 Neu analysieren")
        btn_refresh.clicked.connect(self._run_analysis)
        ctrl_row.addWidget(btn_refresh)
        ctrl_row.addStretch(1)
        layout.addLayout(ctrl_row)

        # Splitter: Oben Muster, Unten generierte Permutationen
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Widget 1: Gefundene Muster
        w_top = QWidget()
        v_top = QVBoxLayout(w_top)
        v_top.setContentsMargins(0, 0, 0, 0)
        self.lbl_patterns_hdr = QLabel("📊 Erkannte Cluster & Hot-Präfixe:")
        self.lbl_patterns_hdr.setStyleSheet("color: #F8FAFC; font-weight: bold;")
        v_top.addWidget(self.lbl_patterns_hdr)

        self.table_patterns = QTableWidget(0, 5)
        self.table_patterns.setHorizontalHeaderLabels([
            "Muster / Präfix", "Typ / Reihe", "Hits in DB", "Dichte", "Beispiel-Treffer"
        ])
        self.table_patterns.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_patterns.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_patterns.verticalHeader().setVisible(False)
        pHdr = self.table_patterns.horizontalHeader()
        pHdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        pHdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        pHdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        pHdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        pHdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table_patterns.setColumnWidth(0, 160)
        self.table_patterns.setColumnWidth(1, 150)
        self.table_patterns.setColumnWidth(2, 90)
        self.table_patterns.setColumnWidth(3, 80)
        self.table_patterns.setSortingEnabled(True)
        v_top.addWidget(self.table_patterns)
        splitter.addWidget(w_top)

        # Widget 2: Generierte Permutationen
        w_bot = QWidget()
        v_bot = QVBoxLayout(w_bot)
        v_bot.setContentsMargins(0, 0, 0, 0)
        self.lbl_candidates_hdr = QLabel("🎯 Berechnete neue Permutationen für den Scanner (noch ungetestet):")
        self.lbl_candidates_hdr.setStyleSheet("color: #10B981; font-weight: bold;")
        v_bot.addWidget(self.lbl_candidates_hdr)

        self.table_candidates = QTableWidget(0, 2)
        self.table_candidates.setHorizontalHeaderLabels(["#", "Generierte MAC-Adresse"])
        self.table_candidates.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_candidates.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_candidates.verticalHeader().setVisible(False)
        cHdr = self.table_candidates.horizontalHeader()
        cHdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        cHdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_candidates.setColumnWidth(0, 65)
        self.table_candidates.setSortingEnabled(True)
        v_bot.addWidget(self.table_candidates)
        splitter.addWidget(w_bot)

        layout.addWidget(splitter, 1)

        # Bottom Actions Row
        bot_row = QHBoxLayout()
        self.btn_send_scan = QPushButton("🚀 In Scanner laden & Scan vorbereiten")
        self.btn_send_scan.setObjectName("SuccessButton")
        self.btn_send_scan.setFixedHeight(34)
        self.btn_send_scan.setStyleSheet("font-weight: bold;")
        self.btn_send_scan.clicked.connect(self._on_send_to_scanner)
        bot_row.addWidget(self.btn_send_scan)

        btn_export = QPushButton("💾 Als .txt exportieren")
        btn_export.setFixedHeight(34)
        btn_export.clicked.connect(self._on_export_txt)
        bot_row.addWidget(btn_export)

        btn_copy = QPushButton("📋 In Zwischenablage")
        btn_copy.setFixedHeight(34)
        btn_copy.clicked.connect(self._on_copy_all)
        bot_row.addWidget(btn_copy)

        bot_row.addStretch(1)
        btn_close = QPushButton("Schließen")
        btn_close.setFixedHeight(34)
        btn_close.clicked.connect(self.accept)
        bot_row.addWidget(btn_close)
        layout.addLayout(bot_row)

        self._populate_portals()
        self._run_analysis()

    def _populate_portals(self):
        self.combo_portal.blockSignals(True)
        self.combo_portal.clear()
        self.combo_portal.addItem("Alle Portale (*)", "*")
        for p in self._db.get_portals():
            self.combo_portal.addItem(p, p)
        if self._initial_portal and self._initial_portal != "*":
            idx = self.combo_portal.findData(self._initial_portal)
            if idx >= 0:
                self.combo_portal.setCurrentIndex(idx)
        self.combo_portal.blockSignals(False)

    def _run_analysis(self):
        portal = self.combo_portal.currentData() or "*"
        records = self._db.get_entries(None if portal == "*" else portal)
        source_macs = [str(r.get("mac", "")) for r in records if r.get("mac")]

        self._patterns = MacPatternPredictor.analyze(source_macs)
        self.table_patterns.setSortingEnabled(False)
        self.table_patterns.setUpdatesEnabled(False)
        self.table_patterns.blockSignals(True)
        try:
            self.table_patterns.setRowCount(len(self._patterns))
            for row, pat in enumerate(self._patterns):
                it_prefix = QTableWidgetItem(pat.prefix)
                it_prefix.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
                if pat.depth == 4:
                    it_prefix.setForeground(QColor("#38BDF8"))
                else:
                    it_prefix.setForeground(QColor("#10B981"))

                it_type = QTableWidgetItem(f"{pat.depth}-Byte Reihe" if pat.depth == 4 else "5-Byte Sub-Cluster")
                it_hits = QTableWidgetItem()
                it_hits.setData(Qt.ItemDataRole.DisplayRole, int(pat.hit_count))
                it_hits.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                d_pct = int(pat.density_score * 100)
                it_density = QTableWidgetItem()
                it_density.setData(Qt.ItemDataRole.DisplayRole, d_pct)
                it_density.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                examples = ", ".join(pat.sample_macs[:2])
                it_ex = QTableWidgetItem(examples)

                self.table_patterns.setItem(row, 0, it_prefix)
                self.table_patterns.setItem(row, 1, it_type)
                self.table_patterns.setItem(row, 2, it_hits)
                self.table_patterns.setItem(row, 3, it_density)
                self.table_patterns.setItem(row, 4, it_ex)
        finally:
            self.table_patterns.blockSignals(False)
            self.table_patterns.setUpdatesEnabled(True)
            self.table_patterns.setSortingEnabled(True)

        self.lbl_patterns_hdr.setText(
            f"📊 Erkannte Cluster & Hot-Präfixe ({len(self._patterns)} Muster aus {len(source_macs)} Hits):"
        )
        self._generate_candidates()

    def _generate_candidates(self):
        portal = self.combo_portal.currentData() or "*"
        records = self._db.get_entries(None if portal == "*" else portal)
        source_macs = [str(r.get("mac", "")) for r in records if r.get("mac")]

        mode = self.combo_strategy.currentData() or "cluster_full"
        limit = self.spin_count.value()

        # Alle bekannten MACs aus DB ausschließen
        known_set = set(self._db.get_known_macs())

        self._generated_macs = MacPatternPredictor.generate_permutations(
            source_macs=source_macs,
            selected_patterns=self._patterns,
            max_total=limit,
            mode=mode,
            existing_macs=known_set,
        )

        self.table_candidates.setSortingEnabled(False)
        self.table_candidates.setUpdatesEnabled(False)
        self.table_candidates.blockSignals(True)
        try:
            self.table_candidates.setRowCount(len(self._generated_macs))
            for row, mac in enumerate(self._generated_macs):
                it_num = QTableWidgetItem()
                it_num.setData(Qt.ItemDataRole.DisplayRole, row + 1)
                it_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_mac = QTableWidgetItem(mac)
                it_mac.setFont(QFont("Consolas", 10))
                it_mac.setForeground(QColor("#38BDF8"))
                self.table_candidates.setItem(row, 0, it_num)
                self.table_candidates.setItem(row, 1, it_mac)
        finally:
            self.table_candidates.blockSignals(False)
            self.table_candidates.setUpdatesEnabled(True)
            self.table_candidates.setSortingEnabled(True)

        self.lbl_candidates_hdr.setText(
            f"🎯 Berechnete neue Permutationen für den Scanner ({len(self._generated_macs)} ungetestete MACs):"
        )
        self.btn_send_scan.setEnabled(len(self._generated_macs) > 0)

    def _on_send_to_scanner(self):
        if not self._generated_macs:
            return
        macs_to_send = list(self._generated_macs)
        self.accept()
        self.send_to_scanner_requested.emit(macs_to_send)

    def _on_export_txt(self):
        if not self._generated_macs:
            return
        path, _ = QFileDialog.getSaveFileName(
            self.window(), "MAC-Permutationen exportieren", "mac_permutations.txt", "Textdateien (*.txt)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self._generated_macs) + "\n")
            QMessageBox.information(self.window(), "Export erfolgreich", f"{len(self._generated_macs)} MACs gespeichert nach:\n{path}")

    def _on_copy_all(self):
        if not self._generated_macs:
            return
        QApplication.clipboard().setText("\n".join(self._generated_macs))
        QMessageBox.information(self.window(), "Kopiert", f"{len(self._generated_macs)} MACs in die Zwischenablage kopiert.")
