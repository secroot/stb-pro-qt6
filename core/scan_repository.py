"""
Scan-Repository & Profil-Manager für STB Pro.
Liest strukturierte Scan-Dateien (*.txt) aus dem Ordner 'mac_scans/' ein
und generiert dynamisch Host- und Login-Auswahlen für Stalker-Portale.
"""
from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from core.models import Profile

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(APP_DIR)
LOCAL_SCANS_DIR = os.path.join(APP_DIR, "mac_scans")
PARENT_SCANS_DIR = os.path.join(PARENT_DIR, "mac_scans")


@dataclass
class ScanAccount:
    """Repräsentiert einen einzelnen gescannten MAC-Account eines Portals."""
    portal_url: str
    mac: str
    status: str = "Aktiv"
    scandate: str = ""
    expire: str = ""
    channels: int = 0
    raw_lines: Dict[str, str] = field(default_factory=dict)

    def display_text(self) -> str:
        """Kompakte, übersichtliche Darstellung für Dropdowns."""
        ch_str = f"{self.channels:,} Ch".replace(",", ".") if self.channels > 0 else "0 Ch"
        exp_clean = self.expire.strip() if self.expire else "Kein Ablauf"
        if len(exp_clean) > 24:
            exp_clean = exp_clean[:22] + "…"
        return f"{self.mac}  •  {ch_str}  •  {exp_clean}"

    def to_profile(self, host_label: str = "") -> Profile:
        """Erzeugt ein einsatzbereites Profile-Objekt für STB Pro."""
        name = f"{host_label} ({self.mac})" if host_label else self.mac
        p = Profile(
            name=name,
            provider_type="Stalker MAC",
            portal_url=self.portal_url,
            mac=self.mac,
            model="MAG 250",
            serial_number="",
            device_id="",
            device_id2="",
            signature="",
            user_agent="",
            proxy="",
        )
        return p


@dataclass
class ScanHost:
    """Repräsentiert einen Host / ein Portal mit allen zugehörigen Logins."""
    host_name: str
    file_path: str
    file_name: str
    portal_url: str
    accounts: List[ScanAccount] = field(default_factory=list)

    @property
    def total_hits(self) -> int:
        return len(self.accounts)

    @property
    def max_channels(self) -> int:
        return max((a.channels for a in self.accounts), default=0)

    def display_label(self) -> str:
        """Formatierte Anzeige für die Host-Combobox."""
        max_ch = self.max_channels
        if max_ch > 0:
            ch_str = f" | Max: {max_ch:,} Ch".replace(",", ".")
        else:
            ch_str = ""
        return f"{self.host_name}  ({self.total_hits} Logins{ch_str})"


class ScanRepository:
    """
    Verwaltet das Einlesen, Filtern und Cachen aller Scan-Dateien aus 'mac_scans/'.
    """

    def __init__(self, directory: Optional[str] = None):
        if directory:
            self.scans_dir = directory
        else:
            # Bevorzuge lokales Verzeichnis stb_pro_qt6/mac_scans
            if os.path.exists(LOCAL_SCANS_DIR):
                self.scans_dir = LOCAL_SCANS_DIR
            elif os.path.exists(PARENT_SCANS_DIR):
                self.scans_dir = PARENT_SCANS_DIR
            else:
                os.makedirs(LOCAL_SCANS_DIR, exist_ok=True)
                self.scans_dir = LOCAL_SCANS_DIR

        self.hosts: Dict[str, ScanHost] = {}
        self.reload()

    def get_scans_dir(self) -> str:
        if not os.path.exists(self.scans_dir):
            os.makedirs(self.scans_dir, exist_ok=True)
        return self.scans_dir

    def reload(self) -> int:
        """
        Liest alle *.txt Dateien im Scans-Ordner ein und aktualisiert den Host-Katalog.
        Gibt die Gesamtzahl gefundener Accounts zurück.
        """
        self.hosts.clear()
        target_dir = self.get_scans_dir()
        file_pattern = os.path.join(target_dir, "*.txt")
        files = glob.glob(file_pattern)

        # Falls im übergeordneten Verzeichnis zusätzliche Dateien liegen, ebenfalls prüfen
        if os.path.exists(PARENT_SCANS_DIR) and PARENT_SCANS_DIR != target_dir:
            for pf in glob.glob(os.path.join(PARENT_SCANS_DIR, "*.txt")):
                if os.path.basename(pf) not in [os.path.basename(f) for f in files]:
                    files.append(pf)

        total_accounts = 0
        for fpath in files:
            host_obj = self._parse_file(fpath)
            if host_obj and host_obj.accounts:
                self.hosts[host_obj.host_name] = host_obj
                total_accounts += len(host_obj.accounts)

        return total_accounts

    def _parse_file(self, file_path: str) -> Optional[ScanHost]:
        fname = os.path.basename(file_path)
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return None

        # Aufteilung in Blöcke anhand von Begrenzer-Linien (mindestens 10 Bindestriche)
        raw_blocks = re.split(r"-{10,}", content)
        accounts: List[ScanAccount] = []
        file_portal_url = ""

        for b in raw_blocks:
            lines = [l.strip() for l in b.strip().splitlines() if l.strip()]
            if not lines:
                continue

            data: Dict[str, str] = {}
            for line in lines:
                if ":" in line:
                    k, v = line.split(":", 1)
                    k_clean = k.strip().lower()
                    v_clean = v.strip()
                    data[k_clean] = v_clean

            # Gültiger Treffer benötigt mindestens eine MAC
            mac_val = data.get("mac", "")
            if not mac_val:
                continue

            portal_val = data.get("portal", "") or data.get("portal_url", "")
            if portal_val and not file_portal_url:
                file_portal_url = portal_val

            status_val = data.get("status", "Aktiv")
            scandate_val = data.get("scandate", "")
            expire_val = data.get("expire", "-")

            # Kanäle robust als Integer parsen
            ch_raw = data.get("channels", "0")
            ch_digits = re.sub(r"[^0-9]", "", ch_raw)
            try:
                channels_val = int(ch_digits) if ch_digits else 0
            except Exception:
                channels_val = 0

            acc = ScanAccount(
                portal_url=portal_val or file_portal_url,
                mac=mac_val,
                status=status_val,
                scandate=scandate_val,
                expire=expire_val,
                channels=channels_val,
                raw_lines=data,
            )
            accounts.append(acc)

        if not accounts:
            return None

        # Primäre Host-Identifikation ermitteln
        # 1. Aus der im Scan gefundenen Portal-URL (Hostname)
        detected_host = ""
        if file_portal_url:
            try:
                p_url = file_portal_url if "://" in file_portal_url else f"http://{file_portal_url}"
                detected_host = urlparse(p_url).hostname or ""
            except Exception:
                pass

        # 2. Fallback: Aus dem Dateinamen (z.B. clubxc.com_150hits_2026-10-17.txt -> clubxc.com)
        if not detected_host:
            match = re.match(r"^([a-zA-Z0-9_\.-]+?)(?:_\d+hits.*|\.txt)$", fname)
            if match:
                detected_host = match.group(1)
            else:
                detected_host = fname.replace(".txt", "")

        # Alle Accounts ohne explizite Portal-URL mit der File-Portal-URL nachziehen
        for acc in accounts:
            if not acc.portal_url:
                acc.portal_url = file_portal_url

        # Sortierung der Accounts: Höchste Kanalzahl zuerst (Top Accounts oben)
        accounts.sort(key=lambda a: a.channels, reverse=True)

        return ScanHost(
            host_name=detected_host,
            file_path=file_path,
            file_name=fname,
            portal_url=file_portal_url,
            accounts=accounts,
        )

    def get_hosts(self) -> List[ScanHost]:
        """Gibt alle verfügbaren Hosts alphabetisch sortiert zurück."""
        return sorted(self.hosts.values(), key=lambda h: h.host_name.lower())

    def get_host(self, host_name: str) -> Optional[ScanHost]:
        if not host_name:
            return None
        # Exakter Match
        if host_name in self.hosts:
            return self.hosts[host_name]
        # Match ohne case
        for k, h in self.hosts.items():
            if k.lower() == host_name.lower():
                return h
        return None

    def get_account(self, host_name: str, mac: str) -> Optional[ScanAccount]:
        h = self.get_host(host_name)
        if not h:
            return None
        mac_clean = mac.strip().upper()
        for a in h.accounts:
            if a.mac.strip().upper() == mac_clean:
                return a
        return None

    def create_profile(self, host_name: str, mac: str) -> Optional[Profile]:
        acc = self.get_account(host_name, mac)
        if not acc:
            return None
        return acc.to_profile(host_label=host_name)
