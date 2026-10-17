"""
Recordings & Downloads Job Manager Dialog.
Displays live progress, speed, MB downloaded, status, stop action, and 1-click folder opener.
"""
from __future__ import annotations

import os
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.recorder import RecorderManager


class JobsDialog(QDialog):
    def __init__(self, recorder_mgr: RecorderManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("📥 Aufnahmen & Downloads (Job-Manager)")
        self.resize(840, 480)
        self._recorder = recorder_mgr

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        lbl = QLabel("📥 Aktive & abgeschlossene Stream-Aufnahmen / VOD-Downloads")
        lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #38BDF8;")
        top_row.addWidget(lbl)
        top_row.addStretch(1)

        btn_open_dir = QPushButton("📂 Aufnahmeordner öffnen")
        btn_open_dir.clicked.connect(self._open_output_dir)
        top_row.addWidget(btn_open_dir)
        layout.addLayout(top_row)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Typ", "Titel", "Status", "Größe / Fortschritt", "Speed / Dauer"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        self.btn_stop_selected = QPushButton("⏹ Ausgewählten Job stoppen")
        self.btn_stop_selected.setObjectName("DangerButton")
        self.btn_stop_selected.clicked.connect(self._stop_selected)
        btn_row.addWidget(self.btn_stop_selected)

        btn_clear_done = QPushButton("🧹 Abgeschlossene ausblenden")
        btn_clear_done.clicked.connect(self._clear_finished)
        btn_row.addWidget(btn_clear_done)

        btn_row.addStretch(1)
        btn_close = QPushButton("Schließen")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self._timer = QTimer(self)
        self._timer.setInterval(750)
        self._timer.timeout.connect(self.refresh_jobs)
        self._timer.start()
        self.refresh_jobs()

    def refresh_jobs(self):
        jobs = self._recorder.jobs
        self.table.setRowCount(len(jobs))
        for row, job in enumerate(jobs):
            mb = job.bytes_written / (1024 * 1024)
            if job.total_bytes > 0:
                total_mb = job.total_bytes / (1024 * 1024)
                pct = (job.bytes_written / job.total_bytes) * 100.0
                size_str = f"{mb:.1f} / {total_mb:.1f} MB ({pct:.0f}%)"
            else:
                size_str = f"{mb:.1f} MB"

            spd_mb = job.speed_kbps / 1024.0
            spd_str = f"{spd_mb:.2f} MB/s ({job.elapsed_str})"

            it_status = QTableWidgetItem(job.status.upper())
            if job.status == "running":
                it_status.setForeground(QColor("#10B981"))
            elif job.status == "completed":
                it_status.setForeground(QColor("#38BDF8"))
            elif job.status == "error":
                it_status.setForeground(QColor("#EF4444"))
            else:
                it_status.setForeground(QColor("#F59E0B"))

            self.table.setItem(row, 0, QTableWidgetItem(job.job_id))
            self.table.setItem(row, 1, QTableWidgetItem(job.kind.upper()))
            self.table.setItem(row, 2, QTableWidgetItem(job.title))
            self.table.setItem(row, 3, it_status)
            self.table.setItem(row, 4, QTableWidgetItem(size_str))
            self.table.setItem(row, 5, QTableWidgetItem(spd_str))

    def _stop_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                self._recorder.stop_job(item.text())
                self.refresh_jobs()

    def _clear_finished(self):
        self._recorder.clear_finished()
        self.refresh_jobs()

    def _open_output_dir(self):
        out_dir = self._recorder.output_dir
        os.makedirs(out_dir, exist_ok=True)
        try:
            os.startfile(out_dir)
        except Exception:
            pass
