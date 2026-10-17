"""
Stream Ringbuffer & VLC Network Caching Configuration Dialog.
"""
from __future__ import annotations

from typing import Any, Dict
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class BufferConfigDialog(QDialog):
    def __init__(self, current_cfg: Dict[str, Any], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("🛡 Stream-Ringpuffer & VLC-Caching Konfiguration")
        self.resize(540, 480)
        self._cfg = dict(current_cfg or {})

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hdr = QLabel("🛡 Lokaler PCR-Paced Stream-Proxy & VLC-Puffer")
        hdr.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        hdr.setStyleSheet("color: #38BDF8;")
        layout.addWidget(hdr)

        desc = QLabel(
            "Der lokale Ringpuffer schützt vor Mikrorucklern, Server-Drops und PCR-Jitter, "
            "indem er den Upstream-Stream im RAM puffert und automatisch neu verbindet."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(desc)

        card = QFrame()
        card.setObjectName("CardFrame")
        form = QFormLayout(card)
        form.setContentsMargins(14, 14, 14, 14)
        form.setSpacing(10)

        is_proxy = (
            self._cfg.get("mode", "proxy") == "proxy"
            if "mode" in self._cfg
            else bool(self._cfg.get("enabled", True))
        )
        self.chk_enabled = QCheckBox("Lokalen HTTP-Ringpuffer-Proxy aktivieren (127.0.0.1)")
        self.chk_enabled.setChecked(is_proxy)
        form.addRow("", self.chk_enabled)

        start_s = float(
            self._cfg.get(
                "start_seconds",
                float(self._cfg.get("prebuffer_mb", 1.5)),
            )
        )
        self.spin_start_s = QDoubleSpinBox()
        self.spin_start_s.setRange(0.2, 30.0)
        self.spin_start_s.setSingleStep(0.5)
        self.spin_start_s.setDecimals(1)
        self.spin_start_s.setSuffix(" Sek.")
        self.spin_start_s.setValue(start_s)
        form.addRow("Startpuffer (Wiedergabe ab X Sek.):", self.spin_start_s)

        buf_s = float(self._cfg.get("buffer_seconds", 20.0))
        self.spin_buffer_s = QDoubleSpinBox()
        self.spin_buffer_s.setRange(2.0, 180.0)
        self.spin_buffer_s.setSingleStep(2.0)
        self.spin_buffer_s.setDecimals(1)
        self.spin_buffer_s.setSuffix(" Sek.")
        self.spin_buffer_s.setValue(buf_s)
        form.addRow("Ziel-Ringpufferlänge im RAM:", self.spin_buffer_s)

        max_mb = int(self._cfg.get("max_mb", self._cfg.get("ring_size_mb", 128)))
        self.spin_ring_mb = QSpinBox()
        self.spin_ring_mb.setRange(8, 1024)
        self.spin_ring_mb.setSingleStep(16)
        self.spin_ring_mb.setSuffix(" MB")
        self.spin_ring_mb.setValue(max_mb)
        form.addRow("Maximaler RAM-Ringpuffer:", self.spin_ring_mb)

        vlc_ms = int(self._cfg.get("vlc_caching_ms", self._cfg.get("vlc_network_caching_ms", 1500)))
        self.spin_vlc_net_ms = QSpinBox()
        self.spin_vlc_net_ms.setRange(200, 15000)
        self.spin_vlc_net_ms.setSingleStep(200)
        self.spin_vlc_net_ms.setSuffix(" ms")
        self.spin_vlc_net_ms.setValue(vlc_ms)
        form.addRow("VLC Network/Live-Caching (Direct Mode):", self.spin_vlc_net_ms)

        reconn = bool(self._cfg.get("reconnect", self._cfg.get("auto_reconnect", True)))
        self.chk_reconnect = QCheckBox("Automatischer Upstream-Reconnect bei Verbindungsabbruch")
        self.chk_reconnect.setChecked(reconn)
        form.addRow("", self.chk_reconnect)

        self.chk_hw_decode = QCheckBox("Hardware-Beschleunigung (Direct3D11 / DXVA2) aktivieren")
        self.chk_hw_decode.setChecked(bool(self._cfg.get("hw_decode", True)))
        form.addRow("", self.chk_hw_decode)

        self.chk_preview = QCheckBox("Live-Standbild-Vorschau bei Senderauswahl aktivieren")
        self.chk_preview.setChecked(bool(self._cfg.get("preview_enabled", True)))
        form.addRow("", self.chk_preview)

        self.spin_preview_age = QSpinBox()
        self.spin_preview_age.setRange(0, 120)
        self.spin_preview_age.setSuffix(" Min.")
        self.spin_preview_age.setValue(int(self._cfg.get("preview_max_age_min", 15)))
        form.addRow("Max. Alter für Vorschau-Cache:", self.spin_preview_age)

        layout.addWidget(card, 1)

        btn_row = QHBoxLayout()
        btn_reset = QPushButton("↺ Standardwerte")
        btn_reset.setToolTip("Auf optimale Zapping- & Ringpuffer-Standardwerte zurücksetzen")
        btn_reset.clicked.connect(self._on_reset_defaults)
        btn_row.addWidget(btn_reset)

        btn_row.addStretch(1)
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾 Übernehmen")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _on_reset_defaults(self):
        self.chk_enabled.setChecked(True)
        self.spin_start_s.setValue(1.5)
        self.spin_buffer_s.setValue(20.0)
        self.spin_ring_mb.setValue(128)
        self.spin_vlc_net_ms.setValue(1500)
        self.chk_reconnect.setChecked(True)
        self.chk_hw_decode.setChecked(True)
        self.chk_preview.setChecked(True)
        self.spin_preview_age.setValue(15)

    def _on_save(self):
        enabled = self.chk_enabled.isChecked()
        self._cfg["mode"] = "proxy" if enabled else "vlc"
        self._cfg["enabled"] = enabled
        self._cfg["start_seconds"] = self.spin_start_s.value()
        self._cfg["buffer_seconds"] = max(self.spin_start_s.value() + 1.0, self.spin_buffer_s.value())
        self._cfg["max_mb"] = self.spin_ring_mb.value()
        self._cfg["ring_size_mb"] = self.spin_ring_mb.value()
        self._cfg["prebuffer_mb"] = self.spin_start_s.value()
        self._cfg["vlc_caching_ms"] = self.spin_vlc_net_ms.value()
        self._cfg["vlc_network_caching_ms"] = self.spin_vlc_net_ms.value()
        self._cfg["vlc_live_caching_ms"] = self.spin_vlc_net_ms.value()
        self._cfg["reconnect"] = self.chk_reconnect.isChecked()
        self._cfg["auto_reconnect"] = self.chk_reconnect.isChecked()
        self._cfg["hw_decode"] = self.chk_hw_decode.isChecked()
        self._cfg["preview_enabled"] = self.chk_preview.isChecked()
        self._cfg["preview_max_age_min"] = self.spin_preview_age.value()
        self.accept()

    def get_config(self) -> Dict[str, Any]:
        return self._cfg

