"""
EPG Now & Next Card Panel Component.
Displays the currently running program with a live progress bar, the upcoming program,
and a button to open the Multi-Day EPG & Catchup Archive Dialog.
"""
from __future__ import annotations

import time
from typing import List
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QFontMetrics, QResizeEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.models import EPGProgram


class EPGPanel(QFrame):
    epg_guide_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("CardFrame")
        self.setMinimumHeight(114)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self._now_title_raw = "JETZT: Keine EPG-Daten verfügbar"
        self._now_desc_raw = "Wähle einen Sender für Programminformationen."
        self._next_title_raw = "DANACH: —"
        self._next_desc_raw = "Keine nachfolgende Sendung geladen."

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # Header Row
        hdr = QHBoxLayout()
        hdr.setSpacing(8)
        lbl_hdr = QLabel("📅 LIVE EPG – JETZT & DANACH")
        lbl_hdr.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_hdr.setStyleSheet("color: #38BDF8;")
        hdr.addWidget(lbl_hdr)

        hdr.addStretch(1)

        self.btn_open_guide = QPushButton("📅 Programmführer & Archiv öffnen")
        self.btn_open_guide.setProperty("compact", "true")
        self.btn_open_guide.setFixedHeight(24)
        self.btn_open_guide.setStyleSheet(
            "font-size: 11px; padding: 2px 10px; background-color: #1E293B; color: #E2E8F0;"
        )
        self.btn_open_guide.clicked.connect(self.epg_guide_requested.emit)
        hdr.addWidget(self.btn_open_guide)
        layout.addLayout(hdr)

        # Two-column Now / Next cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        # NOW Card
        self.now_box = QFrame()
        self.now_box.setObjectName("SubtlePanel")
        now_lay = QVBoxLayout(self.now_box)
        now_lay.setContentsMargins(10, 6, 10, 6)
        now_lay.setSpacing(4)

        self.lbl_now_title = QLabel(self._now_title_raw)
        self.lbl_now_title.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.lbl_now_title.setStyleSheet("color: #F8FAFC;")
        self.lbl_now_title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        now_lay.addWidget(self.lbl_now_title)

        self.progress_now = QProgressBar()
        self.progress_now.setFixedHeight(6)
        self.progress_now.setRange(0, 100)
        self.progress_now.setValue(0)
        self.progress_now.setTextVisible(False)
        now_lay.addWidget(self.progress_now)

        self.lbl_now_desc = QLabel(self._now_desc_raw)
        self.lbl_now_desc.setStyleSheet("color: #94A3B8; font-size: 11px;")
        self.lbl_now_desc.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        now_lay.addWidget(self.lbl_now_desc)

        cards_row.addWidget(self.now_box, 3)

        # NEXT Card
        self.next_box = QFrame()
        self.next_box.setObjectName("SubtlePanel")
        next_lay = QVBoxLayout(self.next_box)
        next_lay.setContentsMargins(10, 6, 10, 6)
        next_lay.setSpacing(4)

        self.lbl_next_title = QLabel(self._next_title_raw)
        self.lbl_next_title.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.lbl_next_title.setStyleSheet("color: #CBD5E1;")
        self.lbl_next_title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        next_lay.addWidget(self.lbl_next_title)

        self.lbl_next_desc = QLabel(self._next_desc_raw)
        self.lbl_next_desc.setStyleSheet("color: #64748B; font-size: 11px;")
        self.lbl_next_desc.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        next_lay.addWidget(self.lbl_next_desc)
        next_lay.addStretch(1)

        cards_row.addWidget(self.next_box, 2)
        layout.addLayout(cards_row, 1)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self._apply_elided_texts()

    def _apply_elided_texts(self):
        now_w = max(140, self.now_box.width() - 24)
        next_w = max(110, self.next_box.width() - 24)

        fm_nt = QFontMetrics(self.lbl_now_title.font())
        fm_nd = QFontMetrics(self.lbl_now_desc.font())
        self.lbl_now_title.setText(fm_nt.elidedText(self._now_title_raw, Qt.TextElideMode.ElideRight, now_w))
        self.lbl_now_title.setToolTip(self._now_title_raw)
        self.lbl_now_desc.setText(fm_nd.elidedText(self._now_desc_raw, Qt.TextElideMode.ElideRight, now_w))
        self.lbl_now_desc.setToolTip(self._now_desc_raw)

        fm_xt = QFontMetrics(self.lbl_next_title.font())
        fm_xd = QFontMetrics(self.lbl_next_desc.font())
        self.lbl_next_title.setText(fm_xt.elidedText(self._next_title_raw, Qt.TextElideMode.ElideRight, next_w))
        self.lbl_next_title.setToolTip(self._next_title_raw)
        self.lbl_next_desc.setText(fm_xd.elidedText(self._next_desc_raw, Qt.TextElideMode.ElideRight, next_w))
        self.lbl_next_desc.setToolTip(self._next_desc_raw)

    def update_programs(self, programs: List[EPGProgram]):
        if not programs:
            self._now_title_raw = "JETZT: Keine EPG-Programmdaten vom Portal gemeldet"
            self.progress_now.setValue(0)
            self._now_desc_raw = "Tipp: Manche Sender liefern EPG erst im Programmführer."
            self._next_title_raw = "DANACH: —"
            self._next_desc_raw = "—"
            self._apply_elided_texts()
            return

        now_ts = int(time.time())
        current_prog = None
        next_prog = None

        for idx, p in enumerate(programs):
            if p.start_timestamp and p.stop_timestamp:
                if p.start_timestamp <= now_ts <= p.stop_timestamp:
                    current_prog = p
                    if idx + 1 < len(programs):
                        next_prog = programs[idx + 1]
                    break
                elif p.start_timestamp > now_ts and current_prog is None:
                    current_prog = programs[max(0, idx - 1)]
                    next_prog = p
                    break

        if current_prog is None:
            current_prog = programs[0]
            if len(programs) > 1:
                next_prog = programs[1]

        time_span = ""
        if current_prog.time_str and current_prog.time_to_str:
            t1 = current_prog.time_str.split(" ")[-1][:5]
            t2 = current_prog.time_to_str.split(" ")[-1][:5]
            time_span = f"[{t1} - {t2}] "

        self._now_title_raw = f"🟢 {time_span}{current_prog.name}"
        pct = int(round(current_prog.progress * 100))
        self.progress_now.setValue(max(0, min(100, pct)))
        desc = (current_prog.descr or "Keine Beschreibung vorhanden.").replace("\n", " ").strip()
        self._now_desc_raw = desc

        if next_prog:
            nt1 = next_prog.time_str.split(" ")[-1][:5] if next_prog.time_str else ""
            nprefix = f"[{nt1}] " if nt1 else ""
            self._next_title_raw = f"⏭ DANACH: {nprefix}{next_prog.name}"
            ndesc = (next_prog.descr or "Keine Beschreibung.").replace("\n", " ").strip()
            self._next_desc_raw = ndesc
        else:
            self._next_title_raw = "⏭ DANACH: —"
            self._next_desc_raw = "Keine weiteren EPG-Einträge."

        self._apply_elided_texts()
