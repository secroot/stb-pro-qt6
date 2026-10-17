"""
Profile Editor Dialog (Stalker MAC, Xtream Codes, M3U Playlist).
Fixes the Xtream password bug from the old CustomTkinter version, adds a password eye toggle,
supports renaming profiles, random serial number generation, and MAC-based SHA256 DeviceID calculation.
"""
from __future__ import annotations

import hashlib
import random
import string
from typing import Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from clients.stb_client import STB_PRESETS, StbClient
from core.models import Profile


def _normalize_stb_model(model_str: str) -> str:
    m = (model_str or "").strip()
    if m in STB_PRESETS:
        return m
    for k in STB_PRESETS.keys():
        if k.replace(" ", "").upper() == m.replace(" ", "").upper():
            return k
    return "MAG 250"


class ProfileEditorDialog(QDialog):
    def __init__(
        self,
        profile_name: str,
        profile: Profile,
        is_new: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Neues Profil anlegen" if is_new else f"Profil bearbeiten – {profile_name}")
        self.resize(560, 590)
        self._original_name = profile_name
        self._profile = profile.clone()
        self._result_data: Optional[Tuple[str, Profile]] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hdr = QLabel("⚙ Portal-Profil & Emulations-Konfiguration")
        hdr.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        hdr.setStyleSheet("color: #818CF8;")
        layout.addWidget(hdr)

        # Common Header Fields (Profile Name + Portal Type + Proxy + User-Agent)
        top_card = QFrame()
        top_card.setObjectName("CardFrame")
        top_form = QFormLayout(top_card)
        top_form.setContentsMargins(12, 12, 12, 12)
        top_form.setSpacing(8)

        self.entry_name = QLineEdit(profile_name)
        self.entry_name.setPlaceholderText("Mein IPTV Portal")
        top_form.addRow("Profilname:", self.entry_name)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["Stalker / Ministra MAC", "Xtream Codes API", "M3U / M3U8 Playlist"])
        top_form.addRow("Portal-Typ:", self.combo_type)

        self.entry_proxy = QLineEdit(self._profile.proxy)
        self.entry_proxy.setPlaceholderText("Optional: http://127.0.0.1:8080 oder socks5://127.0.0.1:9050")
        top_form.addRow("Proxy Server:", self.entry_proxy)

        self.entry_user_agent = QLineEdit(self._profile.user_agent)
        self.entry_user_agent.setPlaceholderText("Leer = Standard-User-Agent des gewählten STB-Modells")
        top_form.addRow("User-Agent:", self.entry_user_agent)

        layout.addWidget(top_card)

        # Stacked Type-Specific Pages
        self.stack = QStackedWidget()

        # ── Page 0: Stalker MAC ──
        page_stalker = QFrame()
        page_stalker.setObjectName("CardFrame")
        st_form = QFormLayout(page_stalker)
        st_form.setContentsMargins(12, 12, 12, 12)
        st_form.setSpacing(8)

        self.entry_st_url = QLineEdit(self._profile.url)
        self.entry_st_url.setPlaceholderText("http://portal.example.com/c/")
        st_form.addRow("Portal URL:", self.entry_st_url)

        self.entry_st_mac = QLineEdit(self._profile.mac)
        self.entry_st_mac.setPlaceholderText("00:1A:79:XX:XX:XX")
        st_form.addRow("MAC-Adresse:", self.entry_st_mac)

        self.combo_st_model = QComboBox()
        self.combo_st_model.addItems(list(STB_PRESETS.keys()))
        self.combo_st_model.setCurrentText(_normalize_stb_model(self._profile.model))
        st_form.addRow("STB Modell:", self.combo_st_model)

        sn_row = QHBoxLayout()
        self.entry_st_sn = QLineEdit(self._profile.serial_number)
        self.entry_st_sn.setPlaceholderText("Leer = automatisch aus MAC berechnen")
        btn_gen_sn = QPushButton("🎲 Zufall")
        btn_gen_sn.clicked.connect(self._generate_random_sn)
        sn_row.addWidget(self.entry_st_sn, 1)
        sn_row.addWidget(btn_gen_sn)
        st_form.addRow("Serial Number (SN):", sn_row)

        dev_row = QHBoxLayout()
        self.entry_st_dev1 = QLineEdit(self._profile.device_id)
        self.entry_st_dev1.setPlaceholderText("SHA256 Device ID 1 (optional)")
        btn_calc_dev = QPushButton("🔐 Aus MAC berechnen")
        btn_calc_dev.clicked.connect(self._calculate_device_ids_from_mac)
        dev_row.addWidget(self.entry_st_dev1, 1)
        dev_row.addWidget(btn_calc_dev)
        st_form.addRow("Device ID 1:", dev_row)

        self.entry_st_dev2 = QLineEdit(self._profile.device_id2)
        self.entry_st_dev2.setPlaceholderText("SHA256 Device ID 2 (optional)")
        st_form.addRow("Device ID 2:", self.entry_st_dev2)

        self.entry_st_sig = QLineEdit(self._profile.signature)
        self.entry_st_sig.setPlaceholderText("SHA256 Signature (optional)")
        st_form.addRow("Signature:", self.entry_st_sig)

        self.stack.addWidget(page_stalker)

        # ── Page 1: Xtream Codes (FIXED PASSWORD BUG + EYE TOGGLE) ──
        page_xtream = QFrame()
        page_xtream.setObjectName("CardFrame")
        xc_form = QFormLayout(page_xtream)
        xc_form.setContentsMargins(12, 12, 12, 12)
        xc_form.setSpacing(10)

        self.entry_xc_server = QLineEdit(self._profile.server_url or self._profile.url)
        self.entry_xc_server.setPlaceholderText("http://line.example.com:8080")
        xc_form.addRow("Server URL:", self.entry_xc_server)

        self.entry_xc_user = QLineEdit(self._profile.username)
        self.entry_xc_user.setPlaceholderText("Benutzername")
        xc_form.addRow("Benutzername:", self.entry_xc_user)

        pass_row = QHBoxLayout()
        # Bug Fix: Explicitly prefill self._profile.password so edits never wipe it!
        self.entry_xc_pass = QLineEdit(self._profile.password)
        self.entry_xc_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.entry_xc_pass.setPlaceholderText("Passwort")
        self.btn_toggle_pass = QPushButton("👁")
        self.btn_toggle_pass.setFixedWidth(36)
        self.btn_toggle_pass.setToolTip("Passwort ein-/ausblenden")
        self.btn_toggle_pass.clicked.connect(self._toggle_password_echo)
        pass_row.addWidget(self.entry_xc_pass, 1)
        pass_row.addWidget(self.btn_toggle_pass)
        xc_form.addRow("Passwort:", pass_row)

        self.combo_xc_format = QComboBox()
        self.combo_xc_format.addItems(["ts", "m3u8"])
        self.combo_xc_format.setCurrentText(
            "m3u8" if (self._profile.xc_format or "ts").lower() == "m3u8" else "ts"
        )
        xc_form.addRow("Stream-Format:", self.combo_xc_format)

        self.stack.addWidget(page_xtream)

        # ── Page 2: M3U / M3U8 Playlist ──
        page_m3u = QFrame()
        page_m3u.setObjectName("CardFrame")
        m3u_form = QFormLayout(page_m3u)
        m3u_form.setContentsMargins(12, 12, 12, 12)
        m3u_form.setSpacing(10)

        m3u_row = QHBoxLayout()
        self.entry_m3u_url = QLineEdit(self._profile.m3u_url or self._profile.url)
        self.entry_m3u_url.setPlaceholderText("https://example.com/playlist.m3u8 oder lokaler Dateipfad")
        btn_browse_m3u = QPushButton("📂 Datei...")
        btn_browse_m3u.clicked.connect(self._browse_m3u_file)
        m3u_row.addWidget(self.entry_m3u_url, 1)
        m3u_row.addWidget(btn_browse_m3u)
        m3u_form.addRow("M3U URL / Pfad:", m3u_row)

        self.stack.addWidget(page_m3u)

        layout.addWidget(self.stack, 1)

        # Set active page from profile
        ptype = (self._profile.portal_type or "stalker").lower()
        if ptype == "xtream":
            self.combo_type.setCurrentIndex(1)
            self.stack.setCurrentIndex(1)
        elif ptype == "m3u":
            self.combo_type.setCurrentIndex(2)
            self.stack.setCurrentIndex(2)
        else:
            self.combo_type.setCurrentIndex(0)
            self.stack.setCurrentIndex(0)

        self.combo_type.currentIndexChanged.connect(self.stack.setCurrentIndex)

        # Bottom Dialog Buttons
        btn_bar = QHBoxLayout()
        btn_bar.addStretch(1)
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾 Profil speichern")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self._on_save)
        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(btn_save)
        layout.addLayout(btn_bar)

    def _toggle_password_echo(self):
        if self.entry_xc_pass.echoMode() == QLineEdit.EchoMode.Password:
            self.entry_xc_pass.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.entry_xc_pass.setEchoMode(QLineEdit.EchoMode.Password)

    def _generate_random_sn(self):
        prefix = random.choice(["0920", "1020", "1120", "0520", "1220"])
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=9))
        self.entry_st_sn.setText(prefix + suffix)

    def _calculate_device_ids_from_mac(self):
        raw_mac = self.entry_st_mac.text().strip()
        if not raw_mac:
            return
        clean_mac = StbClient.format_mac(raw_mac)
        self.entry_st_mac.setText(clean_mac)
        ids = StbClient.generate_device_ids(clean_mac)
        custom_sn = self.entry_st_sn.text().strip()
        if custom_sn and custom_sn != ids["sn"]:
            sn = custom_sn
            dev1 = hashlib.sha256(sn.encode()).hexdigest().upper()
            dev2 = hashlib.sha256(clean_mac.encode()).hexdigest().upper()
            sig = hashlib.sha256((sn + clean_mac).encode()).hexdigest().upper()
        else:
            sn = ids["sn"]
            dev1 = ids["device_id"]
            dev2 = ids["device_id2"]
            sig = ids["signature"]
        self.entry_st_sn.setText(sn)
        self.entry_st_dev1.setText(dev1)
        self.entry_st_dev2.setText(dev2)
        self.entry_st_sig.setText(sig)

    def _browse_m3u_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "M3U / M3U8 Playlist auswählen",
            "",
            "M3U Playlists (*.m3u *.m3u8);;Alle Dateien (*.*)",
        )
        if path:
            self.entry_m3u_url.setText(path)

    def _on_save(self):
        new_name = self.entry_name.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Fehler", "Bitte einen Profilnamen eingeben.")
            return

        idx = self.combo_type.currentIndex()
        self._profile.proxy = self.entry_proxy.text().strip()
        self._profile.user_agent = self.entry_user_agent.text().strip()

        if idx == 0:
            self._profile.portal_type = "stalker"
            self._profile.url = self.entry_st_url.text().strip()
            self._profile.mac = StbClient.format_mac(self.entry_st_mac.text().strip())
            self._profile.model = self.combo_st_model.currentText()
            self._profile.serial_number = self.entry_st_sn.text().strip()
            self._profile.device_id = self.entry_st_dev1.text().strip()
            self._profile.device_id2 = self.entry_st_dev2.text().strip()
            self._profile.signature = self.entry_st_sig.text().strip()
        elif idx == 1:
            self._profile.portal_type = "xtream"
            srv = self.entry_xc_server.text().strip()
            self._profile.server_url = srv
            self._profile.url = srv
            self._profile.username = self.entry_xc_user.text().strip()
            self._profile.password = self.entry_xc_pass.text()
            self._profile.xc_format = self.combo_xc_format.currentText()
        else:
            self._profile.portal_type = "m3u"
            murl = self.entry_m3u_url.text().strip()
            self._profile.m3u_url = murl
            self._profile.url = murl

        self._result_data = (new_name, self._profile)
        self.accept()

    def get_result(self) -> Optional[Tuple[str, Profile]]:
        return self._result_data

