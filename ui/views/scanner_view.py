"""
Multi-MAC Scanner & Pentest Generator View.
Features 22 OUI Vendor Presets, custom wildcard masks (XX:XX:XX), sequential & random generation,
adaptive WAF/429 Throttle Controller integration, live CPS (Checks/sec) & ETA telemetry,
filterable hit table, and 1-click profile adoption.
"""
from __future__ import annotations

import collections
import os
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clients.stb_client import STB_PRESETS
from core.category_parser import (
    calculate_days_until_expire,
    calculate_hit_rate,
    format_hit_rate,
)
from core.portal_checker import (
    PortalCheckResult,
    StalkerPortalChecker,
    extract_portal_urls_from_folder,
    extract_portal_urls_from_text,
    load_portal_list,
    normalize_portal_url,
    save_reachable_portals_file,
)
from core.scan_scheduler import ScanRotationMode
from core.signals import event_bus

OUI_VENDOR_PRESETS = [
    "00:1A:79 (Infomir Standard)",
    "00:1A:79:A0 (Infomir Batch A0)",
    "00:1A:79:B0 (Infomir Batch B0)",
    "00:1A:79:C0 (Infomir Batch C0)",
    "00:1A:79:D0 (Infomir Batch D0)",
    "00:1A:79:E0 (Infomir Batch E0)",
    "00:1A:79:F0 (Infomir Batch F0)",
    "00:1A:79:00 (Infomir Early)",
    "00:1A:79:10 (Infomir Series 1)",
    "00:1A:79:20 (Infomir Series 2)",
    "00:1A:79:30 (Infomir Series 3)",
    "00:1A:79:40 (Infomir Series 4)",
    "00:1A:79:50 (Infomir Series 5)",
    "00:1A:79:60 (Infomir Series 6)",
    "00:1A:79:70 (Infomir Series 7)",
    "00:1A:79:80 (Infomir Series 8)",
    "10:27:BE (TVIP STB)",
    "A0:BB:3E (Formuler STB)",
    "00:1E:B8 (Formuler / Z-Series)",
    "D4:CF:F9 (MAG / OEM Clone)",
    "00:22:02 (Amino STB)",
    "C4:4E:AC (SmartLabs STB)",
]

MAC_REGEX = re.compile(r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}")


class _PortalCheckerSignals(QObject):
    """Thread-sichere Qt-Signals für Hintergrund-Prüfungen der Stalker-Portale."""
    result_received = Signal(object)
    progress_updated = Signal(int, int, int, int, float)
    finished = Signal(list, list)


class ScannerView(QWidget):
    start_scan_requested = Signal(str, list, str, int, float, list, str)  # (url, macs, model, threads, delay_s, rotation_portals, rotation_mode)
    stop_scan_requested = Signal()
    pause_scan_requested = Signal()
    resume_scan_requested = Signal(int, float)                 # (threads, delay_s)
    scan_settings_updated = Signal(int, float)                 # (threads, delay_s)
    apply_mac_requested = Signal(str, str, str)                # (portal_url, mac, model)
    prepend_db_macs_requested = Signal()
    pattern_analysis_requested = Signal()
    scan_exported = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._results: List[Dict[str, Any]] = []
        self._hot_results_count: int = 0
        self._filter_mode: str = "ALL"  # ALL, HOT, VALID, DEAD
        self._scan_start_ts: float = 0.0
        self._scan_start_perf: float = 0.0
        self._total_to_scan: int = 0
        self._done_count: int = 0
        self._is_paused: bool = False
        self._scan_samples: collections.deque[Tuple[float, int]] = collections.deque(maxlen=60)
        self._smoothed_cps: float = 0.0
        self._smoothed_eta: Optional[float] = None
        self._smoothed_portal_eta: Optional[float] = None

        # Baumansicht (Host-Gruppierung) für HOT Treffer
        self._tree_host_items: Dict[str, QTreeWidgetItem] = {}
        self._tree_host_hits: Dict[str, List[Dict[str, Any]]] = {}

        # Stalker Portal Checker & Rotations-Pool Attribute
        self._portal_checker = StalkerPortalChecker()
        self._portal_signals = _PortalCheckerSignals()
        self._portal_results: List[PortalCheckResult] = []
        self._reachable_portals: List[str] = []
        self._loaded_portals: List[str] = []
        self._portal_filter_mode: str = "ALL"
        self._portal_filter_btns: Dict[str, QPushButton] = {}

        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._default_portals_file = os.path.join(app_dir, "stalker_portals.txt")
        self._default_reachable_file = os.path.join(app_dir, "reachable_portals.txt")

        # Verbinde Thread-sichere Qt-Signals
        self._portal_signals.result_received.connect(self._on_portal_check_result)
        self._portal_signals.progress_updated.connect(self._on_portal_check_progress)
        self._portal_signals.finished.connect(self._on_portal_check_finished)

        self._portal_checker.on_portal_result = self._portal_signals.result_received.emit
        self._portal_checker.on_progress = self._portal_signals.progress_updated.emit
        self._portal_checker.on_finished = self._portal_signals.finished.emit

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # ── 1. MAC GENERATOR CARD ──
        gen_card = QFrame()
        gen_card.setObjectName("CardFrame")
        gen_lay = QVBoxLayout(gen_card)
        gen_lay.setContentsMargins(12, 10, 12, 10)
        gen_lay.setSpacing(8)

        row1 = QHBoxLayout()
        lbl_gen = QLabel("🎲 Multi-MAC Generator")
        lbl_gen.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_gen.setStyleSheet("color: #818CF8;")
        row1.addWidget(lbl_gen)
        row1.addStretch(1)

        row1.addWidget(QLabel("Vendor:"))
        self.combo_oui = QComboBox()
        self.combo_oui.addItems(OUI_VENDOR_PRESETS)
        self.combo_oui.currentTextChanged.connect(self._on_oui_selected)
        row1.addWidget(self.combo_oui)

        row1.addWidget(QLabel("Maske:"))
        self.entry_mask = QLineEdit("00:1A:79:XX:XX:XX")
        self.entry_mask.setFixedWidth(135)
        self.entry_mask.setToolTip("Nutze X als Hex-Wildcard, z.B. 00:1A:79:A2:XX:XX")
        row1.addWidget(self.entry_mask)

        row1.addWidget(QLabel("Modus:"))
        self.combo_gen_mode = QComboBox()
        self.combo_gen_mode.addItems(["Zufällig (Random)", "Sequentiell (+1)"])
        row1.addWidget(self.combo_gen_mode)

        row1.addWidget(QLabel("Anzahl:"))
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 50000)
        self.spin_count.setValue(100)
        self.spin_count.setSingleStep(50)
        row1.addWidget(self.spin_count)

        btn_gen = QPushButton("⚡ Generieren")
        btn_gen.setObjectName("PrimaryButton")
        btn_gen.clicked.connect(self.generate_macs)
        row1.addWidget(btn_gen)
        gen_lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(6)
        btn_prepend_db = QPushButton("⭐ DB-Vorrat")
        btn_prepend_db.setToolTip("Bekannte MACs aus der Datenbank voranstellen")
        btn_prepend_db.clicked.connect(self.prepend_db_macs_requested.emit)
        row2.addWidget(btn_prepend_db)

        btn_patterns = QPushButton("🧠 Muster-Analyse")
        btn_patterns.setStyleSheet("color: #38BDF8; font-weight: 500;")
        btn_patterns.setToolTip("Analysiert bekannte Treffer auf Muster/Reihen (z.B. B5-Reihe) und generiert Permutationen")
        btn_patterns.clicked.connect(self.pattern_analysis_requested.emit)
        row2.addWidget(btn_patterns)

        btn_import_file = QPushButton("📂 Datei (.txt)")
        btn_import_file.setToolTip("MACs aus Text- oder CSV-Datei importieren")
        btn_import_file.clicked.connect(self._import_from_file)
        row2.addWidget(btn_import_file)

        btn_import_folder = QPushButton("📁 Ordner (.txt)")
        btn_import_folder.setToolTip("Durchsucht alle .txt-Dateien eines Ordners rekursiv nach MACs und fügt sie dedupliziert hinzu")
        btn_import_folder.clicked.connect(self._import_from_folder)
        row2.addWidget(btn_import_folder)

        btn_import_clip = QPushButton("📋 Zwischenablage")
        btn_import_clip.setToolTip("MAC-Adressen aus der Zwischenablage extrahieren")
        btn_import_clip.clicked.connect(self._import_from_clipboard)
        row2.addWidget(btn_import_clip)

        btn_dedup = QPushButton("🧹 Bereinigen")
        btn_dedup.setToolTip("Duplikate entfernen und ungültige Zeilen bereinigen")
        btn_dedup.clicked.connect(self._deduplicate_list)
        row2.addWidget(btn_dedup)

        row2.addStretch(1)
        btn_clear_macs = QPushButton("🗑 Leeren")
        btn_clear_macs.setToolTip("Kandidatenliste leeren")
        btn_clear_macs.clicked.connect(self.clear_candidates)
        row2.addWidget(btn_clear_macs)
        gen_lay.addLayout(row2)

        layout.addWidget(gen_card)

        # ── 1.5 STALKER PORTAL-CHECKER & ROTATIONS-POOL CARD (COLLAPSIBLE) ──
        self.portal_card = QFrame()
        self.portal_card.setObjectName("CardFrame")
        portal_lay = QVBoxLayout(self.portal_card)
        portal_lay.setContentsMargins(12, 10, 12, 10)
        portal_lay.setSpacing(8)

        # Header Bar
        p_head = QHBoxLayout()
        lbl_p_title = QLabel("🌐 Stalker Portal-Checker && Rotations-Pool")
        lbl_p_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_p_title.setStyleSheet("color: #38BDF8;")
        p_head.addWidget(lbl_p_title)

        self.lbl_portals_summary = QLabel("0 / 0 Erreichbar")
        self.lbl_portals_summary.setStyleSheet(
            "background-color: #064E3B; color: #6EE7B7; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: bold;"
        )
        p_head.addWidget(self.lbl_portals_summary)
        p_head.addStretch(1)

        self.btn_toggle_checker = QPushButton("▼ Portal-Checker ausklappen (0 Portale)")
        self.btn_toggle_checker.setStyleSheet("color: #38BDF8; font-weight: bold; padding: 4px 10px;")
        self.btn_toggle_checker.clicked.connect(self._toggle_checker_drawer)
        p_head.addWidget(self.btn_toggle_checker)
        portal_lay.addLayout(p_head)

        # Collapsible Drawer Frame
        self.checker_drawer = QFrame()
        self.checker_drawer.setVisible(False)
        drawer_lay = QVBoxLayout(self.checker_drawer)
        drawer_lay.setContentsMargins(0, 6, 0, 0)
        drawer_lay.setSpacing(8)

        # Drawer Row 1: File, Threads, Timeout, Actions
        drow1 = QHBoxLayout()
        drow1.addWidget(QLabel("Quelldatei:"))
        self.entry_portal_file = QLineEdit("stalker_portals.txt")
        self.entry_portal_file.setPlaceholderText("Pfad zu stalker_portals.txt")
        drow1.addWidget(self.entry_portal_file, 1)

        btn_browse_portal = QPushButton("📂")
        btn_browse_portal.setToolTip("Andere Portal-Liste auswählen (.txt)")
        btn_browse_portal.clicked.connect(self._browse_portal_file)
        drow1.addWidget(btn_browse_portal)

        btn_import_portal_folder = QPushButton("📁 Ordner (.txt)")
        btn_import_portal_folder.setToolTip("Durchsucht alle .txt-Dateien eines Ordners rekursiv nach Portal-URLs und fügt sie dedupliziert hinzu")
        btn_import_portal_folder.clicked.connect(self._import_portals_from_folder)
        drow1.addWidget(btn_import_portal_folder)

        btn_reload_portal = QPushButton("🔄 Neu laden")
        btn_reload_portal.setToolTip("Liest die ausgewählte Portaldatei neu ein")
        btn_reload_portal.clicked.connect(self._reload_portal_file)
        drow1.addWidget(btn_reload_portal)

        drow1.addWidget(QLabel("Threads:"))
        self.spin_checker_threads = QSpinBox()
        self.spin_checker_threads.setRange(1, 100)
        self.spin_checker_threads.setValue(30)
        drow1.addWidget(self.spin_checker_threads)

        drow1.addWidget(QLabel("Timeout:"))
        self.combo_checker_timeout = QComboBox()
        self.combo_checker_timeout.addItems(["1.0 s", "1.5 s", "2.0 s", "2.5 s", "3.0 s", "4.0 s", "5.0 s", "8.0 s", "10.0 s", "15.0 s"])
        self.combo_checker_timeout.setCurrentText("3.0 s")
        drow1.addWidget(self.combo_checker_timeout)

        drow1.addWidget(QLabel("Delay:"))
        self.combo_checker_delay = QComboBox()
        self.combo_checker_delay.addItems(["0 ms", "50 ms", "100 ms", "250 ms", "500 ms", "1000 ms", "2000 ms", "3000 ms", "5000 ms"])
        self.combo_checker_delay.setCurrentIndex(0)
        drow1.addWidget(self.combo_checker_delay)

        self.btn_start_portal_check = QPushButton("🚀 Portale prüfen")
        self.btn_start_portal_check.setObjectName("SuccessButton")
        self.btn_start_portal_check.setFixedHeight(30)
        self.btn_start_portal_check.clicked.connect(self._on_start_portal_check_clicked)
        drow1.addWidget(self.btn_start_portal_check)

        self.btn_stop_portal_check = QPushButton("⏹ Stoppen")
        self.btn_stop_portal_check.setObjectName("DangerButton")
        self.btn_stop_portal_check.setFixedHeight(30)
        self.btn_stop_portal_check.setEnabled(False)
        self.btn_stop_portal_check.clicked.connect(self._on_stop_portal_check_clicked)
        drow1.addWidget(self.btn_stop_portal_check)
        drawer_lay.addLayout(drow1)

        # Drawer Row 2: Actions & Filter Pills
        drow2 = QHBoxLayout()
        self.btn_save_reachable = QPushButton("💾 Erreichbare speichern")
        self.btn_save_reachable.setStyleSheet("font-weight: 500; color: #10B981;")
        self.btn_save_reachable.setToolTip("Speichert alle erreichbaren Portale in reachable_portals.txt")
        self.btn_save_reachable.clicked.connect(self._save_reachable_portals_clicked)
        drow2.addWidget(self.btn_save_reachable)

        self.btn_adopt_rotation = QPushButton("➕ In Rotation übernehmen")
        self.btn_adopt_rotation.setStyleSheet("font-weight: 500; color: #38BDF8;")
        self.btn_adopt_rotation.setToolTip("Übernimmt erreichbare Portale in den aktiven Scanner-Rotationspool")
        self.btn_adopt_rotation.clicked.connect(self._adopt_to_rotation_clicked)
        drow2.addWidget(self.btn_adopt_rotation)

        drow2.addStretch(1)

        for key, title in (("ALL", "ALL (0)"), ("ONLINE", "🟢 ONLINE (0)"), ("OFFLINE", "🔴 OFFLINE (0)")):
            pb = QPushButton(title)
            pb.setObjectName("NavPill")
            pb.setProperty("active", "true" if key == "ALL" else "false")
            pb.clicked.connect(lambda checked=False, k=key: self._set_portal_filter(k))
            drow2.addWidget(pb)
            self._portal_filter_btns[key] = pb

        btn_clear_ptable = QPushButton("🗑 Leeren")
        btn_clear_ptable.setToolTip("Geprüfte Portalliste leeren")
        btn_clear_ptable.clicked.connect(self._clear_portal_results)
        drow2.addWidget(btn_clear_ptable)
        drawer_lay.addLayout(drow2)

        # Drawer Row 3: Progress & Telemetry
        drow3 = QHBoxLayout()
        self.portal_progress = QProgressBar()
        self.portal_progress.setFixedHeight(10)
        self.portal_progress.setRange(0, 100)
        self.portal_progress.setValue(0)
        self.portal_progress.setTextVisible(False)
        drow3.addWidget(self.portal_progress, 1)

        self.lbl_portal_telemetry = QLabel("Bereit zum Prüfen.")
        self.lbl_portal_telemetry.setStyleSheet("color: #94A3B8; font-size: 11px;")
        drow3.addWidget(self.lbl_portal_telemetry)
        drawer_lay.addLayout(drow3)

        # Drawer Row 4: Portals Table
        self.table_portals = QTableWidget(0, 5)
        self.table_portals.setHorizontalHeaderLabels(["Status", "Portal-URL", "HTTP", "Ping", "Server / Stalker Info"])
        self.table_portals.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_portals.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_portals.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_portals.setSortingEnabled(True)
        self.table_portals.verticalHeader().setVisible(False)
        self.table_portals.setFixedHeight(180)
        phdr = self.table_portals.horizontalHeader()
        phdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        phdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        phdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        phdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        phdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_portals.cellDoubleClicked.connect(self._on_portal_row_double_clicked)
        drawer_lay.addWidget(self.table_portals)

        lbl_p_hint = QLabel("💡 Tipp: Doppelklick auf ein Portal übernimmt es direkt als aktives Ziel-Portal für den Scanner.")
        lbl_p_hint.setStyleSheet("color: #64748B; font-size: 10px;")
        drawer_lay.addWidget(lbl_p_hint)

        portal_lay.addWidget(self.checker_drawer)
        layout.addWidget(self.portal_card)

        # ── 2. SCANNER ENGINE & LIVE TELEMETRY CARD ──
        ctrl_card = QFrame()
        ctrl_card.setObjectName("CardFrame")
        ctrl_lay = QVBoxLayout(ctrl_card)
        ctrl_lay.setContentsMargins(12, 10, 12, 10)
        ctrl_lay.setSpacing(8)

        # Rotation & Portal Selector Row
        crow0 = QHBoxLayout()
        crow0.addWidget(QLabel("🎯 Portal / Rotation:"))
        self.combo_portal_selector = QComboBox()
        self.combo_portal_selector.setMinimumWidth(200)
        self.combo_portal_selector.currentIndexChanged.connect(self._on_portal_selector_changed)
        crow0.addWidget(self.combo_portal_selector)

        self.chk_portal_rotation = QCheckBox("🔄 Rotation aktiv")
        self.chk_portal_rotation.setStyleSheet("color: #38BDF8; font-weight: 500;")
        self.chk_portal_rotation.toggled.connect(self._on_rotation_toggled)
        crow0.addWidget(self.chk_portal_rotation)

        crow0.addWidget(QLabel("Modus:"))
        self.combo_rotation_mode = QComboBox()
        self.combo_rotation_mode.addItems([
            "Hot-Spot Affinity",
            "Round-Robin (Verteilt)",
            "Smart Adaptive",
            "Failover Auto-Switch",
            "Sweep (Alle Portale)",
            "Sweep (Stopp bei Hit)",
        ])
        self.combo_rotation_mode.setToolTip(
            "Intelligente Scanning-Modi für Multi-Portal-Tests:\n"
            "• Hot-Spot Affinity: Fokussiert nach einem Treffer (>0 Kanäle) die nächsten MACs auf das erfolgreiche Portal.\n"
            "• Round-Robin: Gleichmäßige zyklische Verteilung aller MACs.\n"
            "• Smart Adaptive: Bewertet Portale dynamisch nach Hit-Rate und priorisiert die besten Hosts.\n"
            "• Failover: Bleibt auf Primär-Portal, wechselt bei 3 Fehlern/Timeouts automatisch zum nächsten.\n"
            "• Sweep (Alle): Jede MAC wird gegen ausnahmslos alle Portale geprüft.\n"
            "• Sweep (Stopp bei Hit): Prüft Portale, bricht für eine gefundene MAC aber sofort ab."
        )
        crow0.addWidget(self.combo_rotation_mode)

        crow0.addStretch(1)

        btn_quick_checker = QPushButton("⚡ Portale prüfen")
        btn_quick_checker.setToolTip("Öffnet den Stalker Portal-Checker zum schnellen Prüfen von stalker_portals.txt")
        btn_quick_checker.clicked.connect(self._toggle_checker_drawer)
        crow0.addWidget(btn_quick_checker)
        ctrl_lay.addLayout(crow0)

        # Scan Controls Row
        crow1 = QHBoxLayout()
        crow1.setSpacing(6)
        crow1.addWidget(QLabel("Manuelle URL:"))
        self.entry_portal = QLineEdit()
        self.entry_portal.setPlaceholderText("http://example-portal.com/c/")
        self.entry_portal.setMinimumWidth(180)
        crow1.addWidget(self.entry_portal, 1)

        crow1.addWidget(QLabel("Gerät:"))
        self.combo_model = QComboBox()
        self.combo_model.addItems(list(STB_PRESETS.keys()))
        crow1.addWidget(self.combo_model)

        crow1.addWidget(QLabel("Threads:"))
        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(1, 250)
        self.spin_threads.setSingleStep(5)
        self.spin_threads.setValue(20)
        crow1.addWidget(self.spin_threads)

        crow1.addWidget(QLabel("Delay:"))
        self.combo_delay = QComboBox()
        self.combo_delay.addItems([
            "0 ms", "20 ms", "50 ms", "100 ms", "250 ms", "500 ms", "750 ms",
            "1000 ms", "1500 ms", "2000 ms", "3000 ms", "5000 ms", "8000 ms", "10000 ms", "15000 ms"
        ])
        self.combo_delay.setCurrentIndex(0)  # Default to 0 ms for full speed
        self.spin_threads.valueChanged.connect(self._on_settings_changed_live)
        self.combo_delay.currentIndexChanged.connect(self._on_settings_changed_live)
        crow1.addWidget(self.combo_delay)

        self.btn_start = QPushButton("🚀 Scan starten")
        self.btn_start.setObjectName("SuccessButton")
        self.btn_start.setFixedHeight(30)
        self.btn_start.clicked.connect(self._on_start_clicked)
        crow1.addWidget(self.btn_start)

        self.btn_pause = QPushButton("⏸ PAUSE")
        self.btn_pause.setFixedHeight(30)
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self._on_pause_clicked)
        crow1.addWidget(self.btn_pause)

        self.btn_stop = QPushButton("⏹ Stopp")
        self.btn_stop.setObjectName("DangerButton")
        self.btn_stop.setFixedHeight(30)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_scan_requested.emit)
        crow1.addWidget(self.btn_stop)
        ctrl_lay.addLayout(crow1)

        # Telemetry Row
        crow2 = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setFixedHeight(12)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        crow2.addWidget(self.progress, 1)

        self.lbl_telemetry = QLabel("Bereit  |  0 / 0 geprüft  |  🎯 Hit-Rate: 0.0% (0 Hits)  |  ⚡ 0.0 CPS  |  ETA: —")
        self.lbl_telemetry.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: bold;")
        crow2.addWidget(self.lbl_telemetry)

        self.lbl_waf_status = QLabel("🛡 WAF: Normal")
        self.lbl_waf_status.setStyleSheet(
            "background-color: #064E3B; color: #6EE7B7; border-radius: 4px; padding: 2px 8px; font-size: 11px;"
        )
        crow2.addWidget(self.lbl_waf_status)
        ctrl_lay.addLayout(crow2)

        layout.addWidget(ctrl_card)

        # ── 3. SPLITTER: MAC QUEUE (LEFT) + RESULTS TABLE (RIGHT) ──
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Queue Box
        q_box = QFrame()
        q_box.setObjectName("CardFrame")
        q_lay = QVBoxLayout(q_box)
        q_lay.setContentsMargins(10, 10, 10, 10)
        
        q_head = QHBoxLayout()
        self.lbl_queue_count = QLabel("📋 MAC-Kandidaten (0)")
        self.lbl_queue_count.setStyleSheet("color: #94A3B8; font-weight: bold;")
        q_head.addWidget(self.lbl_queue_count)
        q_head.addStretch(1)
        btn_clear_q = QPushButton("🗑 Leeren")
        btn_clear_q.setToolTip("Leert die gesamte Kandidatenliste")
        btn_clear_q.clicked.connect(self.clear_candidates)
        q_head.addWidget(btn_clear_q)
        q_lay.addLayout(q_head)

        self.txt_macs = QPlainTextEdit()
        self.txt_macs.setFont(QFont("Consolas", 10))
        self.txt_macs.setPlaceholderText("Eine MAC-Adresse pro Zeile:\n00:1A:79:12:34:56\n00:1A:79:AB:CD:EF")
        self.txt_macs.textChanged.connect(self._update_queue_count)
        q_lay.addWidget(self.txt_macs, 1)
        splitter.addWidget(q_box)

        # Right Results Box
        res_box = QFrame()
        res_box.setObjectName("CardFrame")
        res_lay = QVBoxLayout(res_box)
        res_lay.setContentsMargins(10, 10, 10, 10)
        res_lay.setSpacing(8)

        # Results Filter Bar
        f_row = QHBoxLayout()
        self._filter_btns: Dict[str, QPushButton] = {}
        for key, title in (
            ("ALL", "ALL"),
            ("HOT", "HOT (0)"),
            ("VALID", "OK"),
            ("DEAD", "ERR"),
        ):
            b = QPushButton(title)
            b.setObjectName("NavPill")
            b.setProperty("active", "true" if key == "ALL" else "false")
            b.clicked.connect(lambda checked=False, k=key: self._set_result_filter(k))
            f_row.addWidget(b)
            self._filter_btns[key] = b

        f_row.addStretch(1)
        self.chk_autoscroll = QCheckBox("Auto-Scroll")
        self.chk_autoscroll.setChecked(True)
        f_row.addWidget(self.chk_autoscroll)

        btn_export = QPushButton("💾 Exportieren")
        btn_export.setToolTip("Gefundene HOT-Treffer als .txt exportieren")
        btn_export.clicked.connect(self._export_hits)
        f_row.addWidget(btn_export)

        btn_clear_res = QPushButton("🗑 Leeren")
        btn_clear_res.setToolTip("Ergebnisse leeren")
        btn_clear_res.clicked.connect(self.clear_results)
        f_row.addWidget(btn_clear_res)
        res_lay.addLayout(f_row)

        # Results Stack: QTableWidget für ALL/OK/ERR, QTreeWidget für HOT
        self.results_stack = QStackedWidget()

        # Results Table (ALL, OK, ERR)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["MAC-Adresse", "Portal", "Status", "Ablaufdatum", "Kanäle", "Token / Info"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        self.results_stack.addWidget(self.table)

        # HOT Hits Tree Widget (Host-Gruppierung, ausklappbar)
        self.hot_tree = QTreeWidget()
        self.hot_tree.setColumnCount(5)
        self.hot_tree.setHeaderLabels(["MAC-Adresse / Host", "Ablaufdatum", "Kanäle", "Bouquet / Tags", "Token / Info"])
        self.hot_tree.setAnimated(True)
        self.hot_tree.setIndentation(22)
        self.hot_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.hot_tree.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)
        tree_hdr = self.hot_tree.header()
        tree_hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tree_hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tree_hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        tree_hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        tree_hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.hot_tree.itemClicked.connect(self._on_tree_item_clicked)
        self.hot_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        self.results_stack.addWidget(self.hot_tree)

        res_lay.addWidget(self.results_stack, 1)

        lbl_hint = QLabel("💡 Tipp: Doppelklick auf einen Treffer übernimmt die MAC sofort in das aktive Profil und verbindet.")
        lbl_hint.setStyleSheet("color: #64748B; font-size: 11px;")
        res_lay.addWidget(lbl_hint)

        splitter.addWidget(res_box)
        splitter.setSizes([280, 780])
        layout.addWidget(splitter, 1)

        # Initialisiere Portale von Festplatte
        self._init_portals_from_disk()

    def set_portal_url(self, url: str):
        if url and not self.entry_portal.text().strip():
            self.entry_portal.setText(url)

    def _on_oui_selected(self, text: str):
        prefix = text.split(" ")[0].strip().upper()
        parts = [p for p in prefix.split(":") if p]
        while len(parts) < 6:
            parts.append("XX")
        self.entry_mask.setText(":".join(parts[:6]))

    def generate_macs(self):
        mask = (self.entry_mask.text() or "00:1A:79:XX:XX:XX").strip().upper()
        mask_clean = re.sub(r"[^0-9A-FX]", "", mask)
        if len(mask_clean) < 12:
            mask_clean = (mask_clean + "XXXXXXXXXXXX")[:12]
        else:
            mask_clean = mask_clean[:12]

        count = self.spin_count.value()
        seq_mode = "Sequentiell" in self.combo_gen_mode.currentText()
        generated: List[str] = []

        if seq_mode:
            base_hex = mask_clean.replace("X", "0")
            try:
                base_val = int(base_hex, 16)
            except Exception:
                base_val = 0x001A79000000
            start_offset = random.randint(0, 0xFFF)
            for i in range(count):
                val = (base_val + start_offset + i) & 0xFFFFFFFFFFFF
                h = f"{val:012X}"
                generated.append(":".join(h[j : j + 2] for j in range(0, 12, 2)))
        else:
            seen = set()
            for _ in range(count * 2):
                if len(generated) >= count:
                    break
                chars = [random.choice("0123456789ABCDEF") if c == "X" else c for c in mask_clean]
                h = "".join(chars)
                mac = ":".join(h[j : j + 2] for j in range(0, 12, 2))
                if mac not in seen:
                    seen.add(mac)
                    generated.append(mac)

        existing = self.get_candidate_macs()
        combined = existing + [m for m in generated if m not in set(existing)]
        self.txt_macs.setPlainText("\n".join(combined))

    def prepend_macs(self, macs: List[str]):
        existing = self.get_candidate_macs()
        seen = set()
        merged: List[str] = []
        for m in list(macs) + existing:
            mu = m.strip().upper()
            if mu and mu not in seen:
                seen.add(mu)
                merged.append(mu)
        self.txt_macs.setPlainText("\n".join(merged))

    def get_candidate_macs(self) -> List[str]:
        raw = self.txt_macs.toPlainText()
        matches = MAC_REGEX.findall(raw)
        return [m.replace("-", ":").upper() for m in matches]

    def clear_candidates(self):
        self.txt_macs.clear()
        self._update_queue_count()

    def _update_queue_count(self):
        macs = self.get_candidate_macs()
        self.lbl_queue_count.setText(f"📋 MAC-Kandidaten ({len(macs)})")

    def _import_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window(), "MAC-Liste importieren", "", "Text/CSV Dateien (*.txt *.csv *.log);;Alle Dateien (*.*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                found = [m.replace("-", ":").upper() for m in MAC_REGEX.findall(f.read())]
            if found:
                self.prepend_macs(found)
        except Exception:
            pass

    def _import_from_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self.window(), "Ordner auswählen (durchsucht alle .txt-Dateien rekursiv nach MACs)"
        )
        if not folder:
            return

        import os
        found_macs: List[str] = []
        seen = set()
        txt_files_count = 0

        for root, _dirs, files in os.walk(folder):
            for fname in files:
                if fname.lower().endswith(".txt"):
                    txt_files_count += 1
                    fpath = os.path.join(root, fname)
                    try:
                        if os.path.getsize(fpath) > 50 * 1024 * 1024:
                            continue
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        matches = MAC_REGEX.findall(content)
                        for m in matches:
                            mu = m.replace("-", ":").upper()
                            if mu not in seen:
                                seen.add(mu)
                                found_macs.append(mu)
                    except Exception:
                        continue

        if found_macs:
            existing = self.get_candidate_macs()
            existing_set = set(existing)
            new_only = [m for m in found_macs if m not in existing_set]
            combined = existing + new_only
            self.txt_macs.setPlainText("\n".join(combined))
            self._update_queue_count()
            event_bus.log_message.emit(
                f"[📁] Ordner-Scan abgeschlossen: {txt_files_count} .txt-Dateien durchsucht, "
                f"{len(found_macs)} eindeutige MACs gefunden ({len(new_only)} neu zur Liste hinzugefügt)."
            )
        else:
            event_bus.log_message.emit(
                f"[📁] Ordner-Scan: {txt_files_count} .txt-Dateien durchsucht, keine MAC-Adressen gefunden."
            )

    def _import_from_clipboard(self):
        clip = QGuiApplication.clipboard().text() or ""
        found = [m.replace("-", ":").upper() for m in MAC_REGEX.findall(clip)]
        if found:
            self.prepend_macs(found)

    def _deduplicate_list(self):
        macs = self.get_candidate_macs()
        seen = set()
        unique = []
        for m in macs:
            if m not in seen:
                seen.add(m)
                unique.append(m)
        self.txt_macs.setPlainText("\n".join(unique))

    def _on_start_clicked(self):
        macs = self.get_candidate_macs()
        if not macs:
            event_bus.log_message.emit("[⚠️] Keine MAC-Adressen in der Kandidatenliste. Bitte erst generieren oder importieren.")
            return

        is_rotation = self.chk_portal_rotation.isChecked() or self.combo_portal_selector.currentIndex() == 1
        rotation_portals = list(self._reachable_portals) if is_rotation else []
        rot_mode_raw = self.combo_rotation_mode.currentText()
        rot_mode = ScanRotationMode.from_ui_label(rot_mode_raw)

        if is_rotation:
            if not rotation_portals:
                event_bus.log_message.emit("[⚠️] Portal-Rotation aktiv, aber keine erreichbaren Portale im Pool! Bitte zuerst Portale prüfen.")
                return
            url = rotation_portals[0]
        else:
            url = (self.entry_portal.text() or "").strip()
            if not url:
                event_bus.log_message.emit("[⚠️] Bitte ein Ziel-Portal eingeben oder Portal-Rotation aktivieren.")
                return

        model = self.combo_model.currentText()
        threads = self.spin_threads.value()
        delay_str = self.combo_delay.currentText().replace(" ms", "").strip()
        delay_s = float(delay_str) / 1000.0 if delay_str.isdigit() else 0.0

        self._scan_start_ts = time.time()
        self._scan_start_perf = time.perf_counter()
        self._scan_samples.clear()
        self._scan_samples.append((self._scan_start_perf, 0))
        self._smoothed_cps = 0.0
        self._smoothed_eta = None
        self._total_to_scan = len(macs) if not (is_rotation and rot_mode == "sweep") else len(macs) * len(rotation_portals)
        self._done_count = 0
        self._is_paused = False
        self.btn_pause.setText("⏸ PAUSE")
        self.btn_pause.setStyleSheet("")
        self.progress.setRange(0, max(1, self._total_to_scan))
        self.progress.setValue(0)
        self.start_scan_requested.emit(url, macs, model, threads, delay_s, rotation_portals, rot_mode)

    def get_scan_threads(self) -> int:
        return self.spin_threads.value()

    def get_scan_delay(self) -> float:
        delay_str = self.combo_delay.currentText().replace(" ms", "").strip()
        return float(delay_str) / 1000.0 if delay_str.isdigit() else 0.0

    def _on_settings_changed_live(self):
        threads = self.get_scan_threads()
        delay_s = self.get_scan_delay()
        self.scan_settings_updated.emit(threads, delay_s)

    def _on_pause_clicked(self):
        if self._is_paused:
            self._is_paused = False
            self.btn_pause.setText("⏸ PAUSE")
            self.btn_pause.setStyleSheet("")
            threads = self.get_scan_threads()
            delay_s = self.get_scan_delay()
            self.resume_scan_requested.emit(threads, delay_s)
        else:
            self._is_paused = True
            self.btn_pause.setText("▶ FORTSETZEN")
            self.btn_pause.setStyleSheet("background-color: #D97706; color: #FFFFFF; font-weight: bold;")
            self.pause_scan_requested.emit()
        self.update_scan_progress(self._done_count, self._total_to_scan)

    def set_scan_running(self, running: bool):
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.btn_pause.setEnabled(running)
        if not running:
            self._is_paused = False
            self.btn_pause.setText("⏸ PAUSE")
            self.btn_pause.setStyleSheet("")
            if self._done_count > 0:
                hit_rate = calculate_hit_rate(self._hot_results_count, self._done_count)
                self.lbl_telemetry.setText(
                    f"{self._done_count} / {self._total_to_scan} geprüft  |  🎯 Hit-Rate: {hit_rate:.1f}% ({self._hot_results_count} Hits)  |  ⚡ 0.0 CPS  |  ETA: 00:00"
                )

    def add_scan_result(self, res: Dict[str, Any]):
        is_hot = (res.get("tag") == "hot" and int(res.get("channels") or 0) > 0)
        if is_hot:
            self._hot_results_count += 1
            self._filter_btns["HOT"].setText(f"HOT ({self._hot_results_count})")

        self._results.append(res)

        if is_hot:
            child = self._append_hot_tree_row(res)
            if self._filter_mode == "HOT" and self.chk_autoscroll.isChecked():
                self.hot_tree.scrollToItem(child)

        if self._matches_filter(res):
            self._append_row(res)
            if self._filter_mode != "HOT" and self.chk_autoscroll.isChecked():
                self.table.scrollToBottom()

        if res.get("rate_limited"):
            self.lbl_waf_status.setText("⚠ WAF / 429 Cooldown aktiv")
            self.lbl_waf_status.setStyleSheet(
                "background-color: #78350F; color: #FCD34D; border-radius: 4px; padding: 2px 8px; font-size: 11px;"
            )
        else:
            self.lbl_waf_status.setText("🛡 WAF: Normal")
            self.lbl_waf_status.setStyleSheet(
                "background-color: #064E3B; color: #6EE7B7; border-radius: 4px; padding: 2px 8px; font-size: 11px;"
            )

    def update_scan_progress(self, done: int, total: int):
        self._done_count = done
        self._total_to_scan = max(1, total)
        self.progress.setRange(0, self._total_to_scan)
        self.progress.setValue(done)

        now = time.perf_counter()
        if not self._scan_start_perf:
            self._scan_start_perf = now
        self._scan_samples.append((now, done))

        # Exaktes 3.0-Sekunden gleitendes Zeitfenster zur Eliminierung von Sprüngen
        cutoff = now - 3.0
        while len(self._scan_samples) > 2 and self._scan_samples[0][0] < cutoff:
            self._scan_samples.popleft()

        oldest_t, oldest_d = self._scan_samples[0]
        dt = now - oldest_t
        dn = done - oldest_d

        if dt >= 0.5:
            instant_cps = max(0.0, dn / dt)
        elif done > 0:
            total_elapsed = max(0.001, now - self._scan_start_perf)
            instant_cps = done / total_elapsed
        else:
            instant_cps = 0.0

        # Glättung über Moving Average
        if self._smoothed_cps <= 0.0:
            self._smoothed_cps = instant_cps
        else:
            alpha = 0.35
            self._smoothed_cps = alpha * instant_cps + (1.0 - alpha) * self._smoothed_cps

        cps = max(0.0, self._smoothed_cps)
        rem = max(0, total - done)

        # ETA-Berechnung mit stabiler Glättung
        if rem == 0:
            eta_str = "00:00"
            self._smoothed_eta = 0.0
        elif cps > 0.05:
            raw_eta = rem / cps
            if self._smoothed_eta is None or self._smoothed_eta <= 0:
                self._smoothed_eta = raw_eta
            else:
                alpha_eta = 0.25
                self._smoothed_eta = alpha_eta * raw_eta + (1.0 - alpha_eta) * self._smoothed_eta

            eta_sec = int(round(self._smoothed_eta))
            if eta_sec >= 3600:
                h = eta_sec // 3600
                m = (eta_sec % 3600) // 60
                s = eta_sec % 60
                eta_str = f"{h:02d}:{m:02d}:{s:02d}"
            else:
                m = eta_sec // 60
                s = eta_sec % 60
                eta_str = f"{m:02d}:{s:02d}"
        else:
            eta_str = "—"

        # Visuals gezielt im stabilen Takt (alle 0.3s), bei Statuswechsel (ETA erstmals verfügbar) oder bei Scan-Ende aktualisieren
        last_vis = getattr(self, "_last_telemetry_visual_ts", 0.0)
        had_no_eta = ("—" in self.lbl_telemetry.text() and eta_str != "—")
        if last_vis > 0 and (now - last_vis) < 0.3 and done < total and not had_no_eta:
            return
        self._last_telemetry_visual_ts = now

        hot_cnt = self._hot_results_count
        hit_rate = calculate_hit_rate(hot_cnt, done)
        pause_txt = " [⏸ PAUSIERT]" if self._is_paused else ""
        self.lbl_telemetry.setText(
            f"{done} / {total} geprüft{pause_txt}  |  🎯 Hit-Rate: {hit_rate:.1f}% ({hot_cnt} Hits)  |  ⚡ {cps:.1f} CPS  |  ETA: {eta_str}"
        )

    def _matches_filter(self, res: Dict[str, Any]) -> bool:
        tag = res.get("tag", "invalid")
        if self._filter_mode == "HOT":
            return tag == "hot"
        if self._filter_mode == "VALID":
            return tag in ("hot", "valid")
        if self._filter_mode == "DEAD":
            return tag not in ("hot", "valid")
        return True

    def _set_result_filter(self, mode: str):
        self._filter_mode = mode
        if mode == "ALL":
            self.table.setSortingEnabled(False)
        for k, btn in self._filter_btns.items():
            btn.setProperty("active", "true" if k == mode else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self._rebuild_table()
        if mode == "HOT":
            self.results_stack.setCurrentWidget(self.hot_tree)
            self._rebuild_hot_tree()
        else:
            self.results_stack.setCurrentWidget(self.table)

    def _update_filter_badges(self):
        self._hot_results_count = sum(1 for r in self._results if r.get("tag") == "hot" and int(r.get("channels") or 0) > 0)
        self._filter_btns["ALL"].setText("ALL")
        self._filter_btns["HOT"].setText(f"HOT ({self._hot_results_count})")
        self._filter_btns["VALID"].setText("OK")
        self._filter_btns["DEAD"].setText("ERR")

    def _rebuild_table(self):
        filtered = [r for r in self._results if self._matches_filter(r)]
        enable_sort = (self._filter_mode != "ALL")
        self.table.setSortingEnabled(False)
        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        try:
            self.table.setRowCount(len(filtered))
            for row, r in enumerate(filtered):
                self._populate_row(row, r)
        finally:
            self.table.blockSignals(False)
            self.table.setUpdatesEnabled(True)
            if enable_sort:
                self.table.setSortingEnabled(True)
            else:
                self.table.setSortingEnabled(False)
                if self.chk_autoscroll.isChecked():
                    self.table.scrollToBottom()

    def _append_row(self, res: Dict[str, Any]):
        was_sort = self.table.isSortingEnabled()
        if was_sort:
            self.table.setSortingEnabled(False)
        try:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._populate_row(row, res)
        finally:
            if was_sort and self._filter_mode != "ALL":
                self.table.setSortingEnabled(True)

    def _populate_row(self, row: int, res: Dict[str, Any]):
        mac = str(res.get("mac", ""))
        raw_p_url = str(res.get("portal_url", "")).strip()
        parsed_p = urlparse(raw_p_url if "://" in raw_p_url else f"http://{raw_p_url}")
        portal_disp = parsed_p.netloc or raw_p_url or "—"
        status = str(res.get("status", ""))
        expire = str(res.get("expire", "-"))
        channels = int(res.get("channels") or 0)
        token = str(res.get("token", ""))
        tag = res.get("tag", "invalid")

        it_mac = QTableWidgetItem(mac)
        it_mac.setData(Qt.ItemDataRole.UserRole, res)
        it_portal = QTableWidgetItem(portal_disp)
        it_portal.setToolTip(raw_p_url)
        it_stat = QTableWidgetItem(status)
        it_exp = QTableWidgetItem(expire)

        it_ch = QTableWidgetItem()
        if channels > 0:
            it_ch.setData(Qt.ItemDataRole.DisplayRole, channels)
        elif res.get("valid"):
            it_ch.setData(Qt.ItemDataRole.DisplayRole, 0)
        else:
            it_ch.setText("—")
        it_ch.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        it_tok = QTableWidgetItem(token)

        if tag == "hot":
            color = QColor("#10B981")
        elif tag == "valid":
            color = QColor("#38BDF8")
        elif res.get("rate_limited"):
            color = QColor("#F59E0B")
        else:
            color = QColor("#64748B")

        it_mac.setForeground(color)
        it_portal.setForeground(QColor("#94A3B8"))
        it_stat.setForeground(color)
        it_ch.setForeground(color)

        self.table.setItem(row, 0, it_mac)
        self.table.setItem(row, 1, it_portal)
        self.table.setItem(row, 2, it_stat)
        self.table.setItem(row, 3, it_exp)
        self.table.setItem(row, 4, it_ch)
        self.table.setItem(row, 5, it_tok)

    def _on_row_double_clicked(self, row: int, _col: int):
        it = self.table.item(row, 0)
        if not it:
            return
        res = it.data(Qt.ItemDataRole.UserRole)
        if isinstance(res, dict):
            mac = str(res.get("mac") or "")
            url = str(res.get("portal_url") or self.entry_portal.text() or "").strip()
            model = self.combo_model.currentText()
            if mac and url:
                self.apply_mac_requested.emit(url, mac, model)

    def _extract_res_hostname(self, res: Dict[str, Any]) -> str:
        raw_url = str(res.get("portal_url") or self.entry_portal.text() or "").strip()
        if not raw_url:
            return "Unbekannt"
        parsed = urlparse(raw_url if "://" in raw_url else f"http://{raw_url}")
        if parsed.port and parsed.port not in (80, 443):
            return parsed.netloc or raw_url
        return parsed.hostname or parsed.netloc or raw_url

    def _rebuild_hot_tree(self):
        """Erstellt die Host-gruppierte Baumansicht für alle HOT-Treffer neu."""
        self.hot_tree.clear()
        self._tree_host_items.clear()
        self._tree_host_hits.clear()

        hot_hits = [r for r in self._results if r.get("tag") == "hot" and int(r.get("channels") or 0) > 0]
        for r in hot_hits:
            self._append_hot_tree_row(r)

        if self.chk_autoscroll.isChecked() and self.hot_tree.topLevelItemCount() > 0:
            last_top = self.hot_tree.topLevelItem(self.hot_tree.topLevelItemCount() - 1)
            if last_top.childCount() > 0:
                self.hot_tree.scrollToItem(last_top.child(last_top.childCount() - 1))
            else:
                self.hot_tree.scrollToItem(last_top)

    def _append_hot_tree_row(self, res: Dict[str, Any]) -> QTreeWidgetItem:
        """Fügt einen HOT-Treffer dynamisch in die Host-Kategorie der Baumansicht ein."""
        host = self._extract_res_hostname(res)
        if host not in self._tree_host_items:
            parent = QTreeWidgetItem(self.hot_tree)
            parent.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
            parent.setForeground(0, QColor("#38BDF8"))
            parent.setBackground(0, QColor("#1E293B"))
            for c in range(1, 5):
                parent.setBackground(c, QColor("#1E293B"))
            parent.setExpanded(True)
            self._tree_host_items[host] = parent
            self._tree_host_hits[host] = []
        else:
            parent = self._tree_host_items[host]

        self._tree_host_hits[host].append(res)
        hit_count = len(self._tree_host_hits[host])
        parent.setText(0, f"[{host}] | [{hit_count} Hot Hits]")

        child = QTreeWidgetItem(parent)
        mac = str(res.get("mac", ""))
        child.setText(0, mac)
        child.setData(0, Qt.ItemDataRole.UserRole, res)
        child.setFont(0, QFont("Consolas", 10, QFont.Weight.Bold))
        child.setForeground(0, QColor("#10B981"))

        # Ablaufdatum + Countdown in Tagen
        expire_val = str(res.get("expire") or "-").strip()
        countdown = calculate_days_until_expire(expire_val)
        if countdown:
            if expire_val.lower() in ("unlimited", "unbegrenzt", "lifetime", "never", "dauerhaft", "permanent"):
                child.setText(1, "Unbegrenzt")
                child.setForeground(1, QColor("#10B981"))
            else:
                child.setText(1, f"{expire_val} ({countdown})")
                if countdown.startswith("abgelaufen"):
                    child.setForeground(1, QColor("#EF4444"))
                elif countdown == "heute":
                    child.setForeground(1, QColor("#F59E0B"))
                else:
                    child.setForeground(1, QColor("#38BDF8"))
        else:
            child.setText(1, expire_val if expire_val else "—")
            child.setForeground(1, QColor("#94A3B8"))

        # Senderanzahl
        ch_cnt = int(res.get("channels") or 0)
        ch_txt = f"{ch_cnt} Kanal" if ch_cnt == 1 else f"{ch_cnt} Kanäle"
        child.setText(2, ch_txt)
        child.setForeground(2, QColor("#10B981"))
        child.setFont(2, QFont("Segoe UI", 9, QFont.Weight.Bold))

        # Bouquet / Kategorie Tags
        tags = res.get("tags") or []
        if tags:
            child.setText(3, " ".join(tags))
            child.setForeground(3, QColor("#F59E0B"))
            child.setFont(3, QFont("Segoe UI", 9, QFont.Weight.Bold))
        else:
            child.setText(3, "—")
            child.setForeground(3, QColor("#64748B"))

        # Token / Info / VPN
        tok = str(res.get("token") or "")
        loc = str(res.get("vpn_location") or res.get("proxy_location") or "")
        info_bits = []
        if loc:
            info_bits.append(f"VPN: {loc}")
        if tok:
            info_bits.append(f"Token: {tok[:16]}…")
        child.setText(4, "  |  ".join(info_bits) if info_bits else (tok or "—"))
        child.setForeground(4, QColor("#94A3B8"))

        return child

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, _column: int):
        """Klappt beim einfachen Klick auf einen Host-Header die Kategorie dynamisch auf oder zu."""
        res = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(res, dict):
            item.setExpanded(not item.isExpanded())

    def _on_tree_item_double_clicked(self, item: QTreeWidgetItem, _column: int):
        """Übernimmt den MAC-Account bei Doppelklick im Tree und verbindet sofort."""
        res = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(res, dict):
            mac = str(res.get("mac") or "")
            url = str(res.get("portal_url") or self.entry_portal.text() or "").strip()
            model = self.combo_model.currentText()
            if mac and url:
                self.apply_mac_requested.emit(url, mac, model)
        else:
            item.setExpanded(not item.isExpanded())

    def _export_hits(self):
        hits = [r for r in self._results if r.get("tag") == "hot" and int(r.get("channels") or 0) > 0]
        if not hits:
            return

        import datetime
        import os
        from urllib.parse import urlparse

        raw_url = str(hits[0].get("portal_url") or self.entry_portal.text() or "").strip()
        parsed = urlparse(raw_url if "://" in raw_url else f"http://{raw_url}")
        host = parsed.hostname or "portal"
        safe_host = re.sub(r"[^a-zA-Z0-9_\.-]", "_", host)
        hit_count = len(hits)
        date_file = datetime.datetime.now().strftime("%Y-%m-%d")
        default_filename = f"{safe_host}_{hit_count}hits_{date_file}.txt"

        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        scans_dir = os.path.join(app_dir, "mac_scans")
        os.makedirs(scans_dir, exist_ok=True)
        default_filepath = os.path.join(scans_dir, default_filename)

        path, _ = QFileDialog.getSaveFileName(
            self.window(), "HOT MAC-Treffer exportieren", default_filepath, "Textdateien (*.txt)"
        )
        if path:
            try:
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sep = "-" * 45
                blocks = []
                for r in hits:
                    p_url = str(r.get("portal_url") or raw_url).strip()
                    p_status = str(r.get("status") or "Aktiv").strip()
                    p_mac = str(r.get("mac") or "").strip()
                    p_expire = str(r.get("expire") or "-").strip()
                    p_channels = str(r.get("channels") or "0").strip()
                    p_tags = " ".join(r.get("tags") or [])
                    block_lines = [
                        sep,
                        f"Portal: {p_url}",
                        f"Status: {p_status}",
                        f"Mac: {p_mac}",
                        f"Scandate: {now_str}",
                        f"Expire: {p_expire}",
                        f"Channels: {p_channels}",
                    ]
                    if p_tags:
                        block_lines.append(f"Categories: {p_tags}")
                    block_lines.append(sep)
                    blocks.append("\n".join(block_lines))

                content = "\n\n".join(blocks) + "\n"
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.scan_exported.emit(path)
                event_bus.log_message.emit(
                    f"💾 {len(hits)} HOT Treffer erfolgreich nach '{os.path.basename(path)}' exportiert."
                )
            except Exception:
                pass

    def clear_results(self):
        self._results.clear()
        self._hot_results_count = 0
        self.table.setRowCount(0)
        self.hot_tree.clear()
        self._tree_host_items.clear()
        self._tree_host_hits.clear()
        self._update_filter_badges()
        self.lbl_telemetry.setText("Bereit  |  0 / 0 geprüft  |  🎯 Hit-Rate: 0.0% (0 Hits)  |  ⚡ 0.0 CPS  |  ETA: —")

    # ── STALKER PORTAL-CHECKER & ROTATIONS-POOL METHODEN ──

    def _init_portals_from_disk(self):
        """Lädt stalker_portals.txt und reachable_portals.txt initial von der Festplatte."""
        portals_file = self._default_portals_file
        if os.path.exists(portals_file):
            self._loaded_portals = load_portal_list(portals_file)
            self.entry_portal_file.setText(os.path.basename(portals_file))
            self.btn_toggle_checker.setText(f"▼ Portal-Checker ausklappen ({len(self._loaded_portals)} Portale)")
            self.lbl_portals_summary.setText(f"0 / {len(self._loaded_portals)} Erreichbar in {os.path.basename(portals_file)}")

        if os.path.exists(self._default_reachable_file):
            saved_reachables = load_portal_list(self._default_reachable_file)
            if saved_reachables:
                self.set_reachable_portals(saved_reachables)
                self.lbl_portals_summary.setText(f"🟢 {len(saved_reachables)} Erreichbar (aus Datei geladen)")
        else:
            self._update_portal_selector_dropdown()

    def _toggle_checker_drawer(self):
        is_vis = self.checker_drawer.isVisible()
        self.checker_drawer.setVisible(not is_vis)
        arrow = "▲" if not is_vis else "▼"
        count = len(self._loaded_portals)
        self.btn_toggle_checker.setText(f"{arrow} Portal-Checker {'einklappen' if not is_vis else 'ausklappen'} ({count} Portale)")

    def _browse_portal_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window(), "Stalker-Portal Liste wählen", "", "Textdateien (*.txt);;Alle Dateien (*.*)"
        )
        if path:
            self.entry_portal_file.setText(path)
            self._reload_portal_file()

    def _import_portals_from_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self.window(), "Ordner auswählen (durchsucht alle .txt-Dateien rekursiv nach Portal-URLs)"
        )
        if not folder:
            return

        found_portals, txt_count = extract_portal_urls_from_folder(folder)
        if found_portals:
            existing_set = {p.lower() for p in self._loaded_portals}
            new_portals = [p for p in found_portals if p.lower() not in existing_set]
            self._loaded_portals.extend(new_portals)
            count = len(self._loaded_portals)
            self.btn_toggle_checker.setText(f"▼ Portal-Checker ({count} Portale)")
            self.lbl_portals_summary.setText(f"0 / {count} Erreichbar")
            self.lbl_portal_telemetry.setText(
                f"{count} Portale geladen ({len(found_portals)} im Ordner gefunden, {len(new_portals)} neu hinzugefügt)."
            )
            event_bus.log_message.emit(
                f"[📁] Portal-Ordner-Scan abgeschlossen: {txt_count} .txt-Dateien durchsucht, "
                f"{len(found_portals)} Portal-URLs gefunden ({len(new_portals)} neu zur Prüfliste hinzugefügt)."
            )
        else:
            event_bus.log_message.emit(
                f"[📁] Portal-Ordner-Scan: {txt_count} .txt-Dateien durchsucht, keine gültigen Portal-URLs gefunden."
            )

    def _reload_portal_file(self):
        file_input = self.entry_portal_file.text().strip()
        if not file_input:
            file_path = self._default_portals_file
        elif os.path.isabs(file_input):
            file_path = file_input
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            file_path = os.path.join(app_dir, file_input)

        if not os.path.exists(file_path):
            event_bus.log_message.emit(f"[⚠️] Datei '{file_path}' nicht gefunden.")
            return

        portals = load_portal_list(file_path)
        self._loaded_portals = portals
        fname = os.path.basename(file_path)
        self.btn_toggle_checker.setText(f"▼ Portal-Checker ({len(portals)} Portale in {fname})")
        self.lbl_portals_summary.setText(f"0 / {len(portals)} Erreichbar in {fname}")
        self.lbl_portal_telemetry.setText(f"Bereit. {len(portals)} Portale erfolgreich eingelesen.")
        event_bus.log_message.emit(f"[🌐] {len(portals)} Stalker-Portale aus '{fname}' eingelesen.")

    def _on_start_portal_check_clicked(self):
        if not self._loaded_portals:
            self._reload_portal_file()
        if not self._loaded_portals:
            event_bus.log_message.emit("[⚠️] Keine Portale zum Prüfen geladen. Bitte eine gültige .txt-Datei wählen.")
            return

        threads = self.spin_checker_threads.value()
        tout_str = self.combo_checker_timeout.currentText().replace(" s", "").strip()
        timeout = float(tout_str) if tout_str.replace(".", "").isdigit() else 3.0
        del_str = self.combo_checker_delay.currentText().replace(" ms", "").strip()
        chk_delay = float(del_str) / 1000.0 if del_str.isdigit() else 0.0

        self.btn_start_portal_check.setEnabled(False)
        self.btn_stop_portal_check.setEnabled(True)
        self._clear_portal_results()
        self._smoothed_portal_eta = None

        self.portal_progress.setRange(0, len(self._loaded_portals))
        self.portal_progress.setValue(0)
        self.lbl_portal_telemetry.setText(f"Prüfe {len(self._loaded_portals)} Portale mit {threads} Threads...")

        event_bus.log_message.emit(
            f"[🌐] Starte Erreichbarkeits-Check für {len(self._loaded_portals)} Stalker-Portale "
            f"({threads} Threads, Timeout {timeout}s, Delay {del_str} ms)..."
        )
        self._portal_checker.start_check(self._loaded_portals, threads=threads, timeout=timeout, delay_s=chk_delay)

    def _on_stop_portal_check_clicked(self):
        self._portal_checker.stop()
        self.btn_start_portal_check.setEnabled(True)
        self.btn_stop_portal_check.setEnabled(False)
        self.lbl_portal_telemetry.setText("Prüfung gestoppt.")
        event_bus.log_message.emit("[⏹] Stalker-Portal Erreichbarkeits-Check gestoppt.")

    def _on_portal_check_result(self, res: PortalCheckResult):
        self._portal_results.append(res)
        if res.is_online and res.stalker_detected and res.url not in self._reachable_portals:
            self._reachable_portals.append(res.url)
            self._update_portal_selector_dropdown()

        self._update_portal_filter_badges()
        if self._matches_portal_filter(res):
            self._append_portal_row(res)

    def _on_portal_check_progress(self, done: int, total: int, online: int, offline: int, cps: float):
        self.portal_progress.setRange(0, max(1, total))
        self.portal_progress.setValue(done)
        rem = max(0, total - done)
        if rem == 0:
            eta_str = "00:00"
            self._smoothed_portal_eta = 0.0
        elif cps > 0.05:
            raw_eta = rem / cps
            if self._smoothed_portal_eta is None or self._smoothed_portal_eta <= 0:
                self._smoothed_portal_eta = raw_eta
            else:
                alpha = 0.20
                self._smoothed_portal_eta = alpha * raw_eta + (1.0 - alpha) * self._smoothed_portal_eta
            eta_s = int(round(self._smoothed_portal_eta))
            if eta_s >= 3600:
                eta_str = f"{eta_s // 3600:02d}:{(eta_s % 3600) // 60:02d}:{eta_s % 60:02d}"
            else:
                eta_str = f"{eta_s // 60:02d}:{eta_s % 60:02d}"
        else:
            eta_str = "—"

        self.lbl_portal_telemetry.setText(
            f"{done}/{total} geprüft  |  🟢 {online} Online  |  🔴 {offline} Offline  |  ⚡ {cps:.1f} P/s  |  ETA: {eta_str}"
        )
        self.lbl_portals_summary.setText(f"🟢 {online} / {total} Erreichbar")

    def _on_portal_check_finished(self, results: List[PortalCheckResult], reachables: List[str]):
        self.btn_start_portal_check.setEnabled(True)
        self.btn_stop_portal_check.setEnabled(False)
        self.set_reachable_portals(reachables)

        online_cnt = len(reachables)
        total_cnt = len(results)
        self.lbl_portals_summary.setText(f"🟢 {online_cnt} / {total_cnt} Erreichbar")
        self.lbl_portal_telemetry.setText(f"Prüfung abgeschlossen: {online_cnt} von {total_cnt} Portalen erreichbar.")

        # Automatisches Speichern der erreichbaren Portale in reachable_portals.txt
        save_reachable_portals_file(self._default_reachable_file, reachables)
        event_bus.log_message.emit(
            f"[🌐] Portal-Check beendet: {online_cnt}/{total_cnt} Portale erreichbar. "
            f"Automatisch nach '{os.path.basename(self._default_reachable_file)}' gespeichert & in Rotation bereitgestellt."
        )

    def _matches_portal_filter(self, res: PortalCheckResult) -> bool:
        if self._portal_filter_mode == "ONLINE":
            return bool(res.is_online and res.stalker_detected)
        if self._portal_filter_mode == "OFFLINE":
            return not (res.is_online and res.stalker_detected)
        return True

    def _set_portal_filter(self, mode: str):
        self._portal_filter_mode = mode
        for k, btn in self._portal_filter_btns.items():
            btn.setProperty("active", "true" if k == mode else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._rebuild_portal_table()

    def _update_portal_filter_badges(self):
        online = sum(1 for r in self._portal_results if r.is_online and r.stalker_detected)
        offline = len(self._portal_results) - online
        self._portal_filter_btns["ALL"].setText(f"ALL ({len(self._portal_results)})")
        self._portal_filter_btns["ONLINE"].setText(f"🟢 ONLINE ({online})")
        self._portal_filter_btns["OFFLINE"].setText(f"🔴 OFFLINE ({offline})")

    def _rebuild_portal_table(self):
        filtered = [r for r in self._portal_results if self._matches_portal_filter(r)]
        was_sort = self.table_portals.isSortingEnabled()
        if was_sort:
            self.table_portals.setSortingEnabled(False)
        self.table_portals.setUpdatesEnabled(False)
        self.table_portals.blockSignals(True)
        try:
            self.table_portals.setRowCount(len(filtered))
            for row, r in enumerate(filtered):
                self._populate_portal_row(row, r)
        finally:
            self.table_portals.blockSignals(False)
            self.table_portals.setUpdatesEnabled(True)
            if was_sort:
                self.table_portals.setSortingEnabled(True)

    def _append_portal_row(self, res: PortalCheckResult):
        was_sort = self.table_portals.isSortingEnabled()
        if was_sort:
            self.table_portals.setSortingEnabled(False)
        try:
            row = self.table_portals.rowCount()
            self.table_portals.insertRow(row)
            self._populate_portal_row(row, res)
        finally:
            if was_sort:
                self.table_portals.setSortingEnabled(True)

    def _populate_portal_row(self, row: int, res: PortalCheckResult):
        it_stat = QTableWidgetItem(res.display_status())
        it_url = QTableWidgetItem(res.url)
        it_url.setData(Qt.ItemDataRole.UserRole, res.url)

        it_code = QTableWidgetItem()
        if res.status_code is not None:
            it_code.setData(Qt.ItemDataRole.DisplayRole, int(res.status_code))
        else:
            it_code.setText("—")
        it_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        it_ping = QTableWidgetItem()
        if res.latency_ms > 0:
            it_ping.setData(Qt.ItemDataRole.DisplayRole, int(round(res.latency_ms)))
        else:
            it_ping.setText("—")
        it_ping.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        info_parts = []
        if res.server:
            info_parts.append(res.server)
        if res.stalker_detected:
            info_parts.append("Ministra/Stalker erkannt")
        if res.error:
            info_parts.append(res.error)
        it_info = QTableWidgetItem(" | ".join(info_parts) if info_parts else "—")

        if res.is_online and res.stalker_detected:
            color = QColor("#10B981")
        elif res.status_code is not None and not res.stalker_detected:
            color = QColor("#F59E0B")
        else:
            color = QColor("#EF4444")

        it_stat.setForeground(color)
        it_code.setForeground(color)
        it_ping.setForeground(QColor("#94A3B8"))

        self.table_portals.setItem(row, 0, it_stat)
        self.table_portals.setItem(row, 1, it_url)
        self.table_portals.setItem(row, 2, it_code)
        self.table_portals.setItem(row, 3, it_ping)
        self.table_portals.setItem(row, 4, it_info)

    def _clear_portal_results(self):
        self._portal_results.clear()
        self.table_portals.setRowCount(0)
        self._update_portal_filter_badges()

    def _on_portal_row_double_clicked(self, row: int, _col: int):
        it = self.table_portals.item(row, 1)
        if not it:
            return
        url = str(it.data(Qt.ItemDataRole.UserRole) or it.text() or "").strip()
        if url:
            self.entry_portal.setText(url)
            self.chk_portal_rotation.setChecked(False)
            self.combo_portal_selector.setCurrentIndex(0)
            event_bus.log_message.emit(f"[🎯] Portal '{url}' direkt als Scanner-Ziel übernommen.")

    def _save_reachable_portals_clicked(self):
        if not self._reachable_portals:
            event_bus.log_message.emit("[⚠️] Keine erreichbaren Portale zum Speichern vorhanden.")
            return

        default_file = self._default_reachable_file
        path, _ = QFileDialog.getSaveFileName(
            self.window(), "Erreichbare Stalker-Portale speichern", default_file, "Textdateien (*.txt)"
        )
        if path:
            ok = save_reachable_portals_file(path, self._reachable_portals)
            if ok:
                event_bus.log_message.emit(
                    f"[💾] {len(self._reachable_portals)} erreichbare Portale erfolgreich in '{os.path.basename(path)}' gespeichert."
                )

    def _adopt_to_rotation_clicked(self):
        if not self._reachable_portals:
            event_bus.log_message.emit("[⚠️] Noch keine erreichbaren Portale ermittelt.")
            return

        self.chk_portal_rotation.setChecked(True)
        self.combo_portal_selector.setCurrentIndex(1)
        event_bus.log_message.emit(
            f"[🔄] {len(self._reachable_portals)} erreichbare Portale in die Scanner-Rotation übernommen (Modus: {self.combo_rotation_mode.currentText()})."
        )

    def _update_portal_selector_dropdown(self):
        cur_txt = self.combo_portal_selector.currentText()
        self.combo_portal_selector.blockSignals(True)
        self.combo_portal_selector.clear()
        self.combo_portal_selector.addItem("✏ Manuelles Portal (unten)")
        count = len(self._reachable_portals)
        if count > 0:
            self.combo_portal_selector.addItem(f"🔄 {count} Portale in Rotation")
            for u in self._reachable_portals:
                parsed = urlparse(u)
                label = f"🟢 {parsed.netloc}{parsed.path}"
                self.combo_portal_selector.addItem(label, u)
        else:
            self.combo_portal_selector.addItem("🔄 Keine Portale (bitte prüfen)")
        self.combo_portal_selector.blockSignals(False)

        idx = self.combo_portal_selector.findText(cur_txt)
        if idx >= 0:
            self.combo_portal_selector.setCurrentIndex(idx)

    def _on_portal_selector_changed(self, idx: int):
        if idx == 0:
            self.chk_portal_rotation.setChecked(False)
            self.entry_portal.setEnabled(True)
        elif idx == 1:
            if len(self._reachable_portals) > 0:
                self.chk_portal_rotation.setChecked(True)
                self.entry_portal.setEnabled(False)
            else:
                self.chk_portal_rotation.setChecked(False)
                self.entry_portal.setEnabled(True)
        else:
            target_url = self.combo_portal_selector.itemData(idx)
            if target_url:
                self.entry_portal.setText(target_url)
            self.chk_portal_rotation.setChecked(False)
            self.entry_portal.setEnabled(True)

    def _on_rotation_toggled(self, checked: bool):
        if checked:
            if len(self._reachable_portals) > 0:
                if self.combo_portal_selector.currentIndex() != 1:
                    self.combo_portal_selector.setCurrentIndex(1)
                self.entry_portal.setEnabled(False)
            else:
                self.chk_portal_rotation.setChecked(False)
                event_bus.log_message.emit("[⚠️] Keine erreichbaren Portale vorhanden. Bitte zuerst den Stalker-Portal-Checker starten!")
        else:
            if self.combo_portal_selector.currentIndex() == 1:
                self.combo_portal_selector.setCurrentIndex(0)
            self.entry_portal.setEnabled(True)

    def get_reachable_portals(self) -> List[str]:
        return list(self._reachable_portals)

    def set_reachable_portals(self, portals: List[str]):
        clean = []
        seen = set()
        for p in portals:
            norm = normalize_portal_url(p)
            if norm and norm.lower() not in seen:
                seen.add(norm.lower())
                clean.append(norm)
        self._reachable_portals = clean
        self._update_portal_selector_dropdown()
        self.lbl_portals_summary.setText(f"🟢 {len(clean)} Erreichbar")
        self.btn_toggle_checker.setText(f"▼ Portal-Checker ausklappen ({len(self._loaded_portals)} Portale, {len(clean)} online)")
