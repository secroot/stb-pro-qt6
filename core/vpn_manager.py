"""
NordVPN Manager für STB Pro Qt6.
Erkennt eine aktive NordVPN-Installation, überwacht den Verbindungsstatus und
führt bei Erkennung von IP-/ISP-Sperren (IP_BAN / ISP_LOCK) vollautomatische
Server- und Länder-Rotationen via NordVPN-CLI durch.
"""
import os
import re
import shutil
import subprocess
import threading
import time
from typing import Optional, Callable, Tuple, List
import requests

from core.signals import event_bus


class NordVpnManager:
    """
    Verwaltet die Integration mit NordVPN unter Windows.
    Unterstützt Quick-Connect, länderspezifische Server-Rotation und
    reaktive Auto-Umschaltung bei Stream-Blockaden.
    """

    NORD_PATHS = [
        r"C:\Program Files\NordVPN\NordVPN.exe",
        r"C:\Program Files (x86)\NordVPN\NordVPN.exe",
        r"C:\Program Files\NordVPN\nordvpn.exe",
    ]

    def __init__(self):
        self._cli_path: Optional[str] = None
        self._lock = threading.Lock()
        self._last_switch_time: float = 0.0
        self._is_switching: bool = False
        self._auto_switch_enabled: bool = True
        self._last_known_ip: str = ""
        self._last_known_country: str = ""
        self._detect_cli()

    def _detect_cli(self) -> Optional[str]:
        if self._cli_path and os.path.exists(self._cli_path):
            return self._cli_path

        # 1. Bekannte Standard-Pfade
        for path in self.NORD_PATHS:
            if os.path.exists(path):
                self._cli_path = path
                return path

        # 2. PATH-Umgebung
        which_p = shutil.which("nordvpn") or shutil.which("NordVPN")
        if which_p and os.path.exists(which_p):
            self._cli_path = which_p
            return which_p

        return None

    def is_installed(self) -> bool:
        """Prüft, ob NordVPN auf dem System installiert ist."""
        return self._detect_cli() is not None

    def is_running(self) -> bool:
        """Prüft, ob der NordVPN-Dienst oder die App im Hintergrund aktiv ist."""
        if not self.is_installed():
            return False
        try:
            # Schneller Tasklist-Check nach NordVPN-Prozessen
            res = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq nordvpn*"],
                capture_output=True,
                text=True,
                timeout=2,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            out = res.stdout.lower()
            return "nordvpn" in out or "nordvpn-service" in out
        except Exception:
            return True  # Fallback falls tasklist blockiert ist

    def is_connected(self) -> bool:
        """Prüft über Netzwerkschnittstellen, ob der NordLynx-Adapter aktiv verbunden ist."""
        try:
            res = subprocess.run(
                ["netsh", "interface", "show", "interface"],
                capture_output=True,
                text=True,
                timeout=2,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            for line in res.stdout.splitlines():
                if "nordlynx" in line.lower() or "openvpn data channel" in line.lower():
                    if "verbunden" in line.lower() or "connected" in line.lower():
                        return True
        except Exception:
            pass
        return False

    def get_public_ip(self, timeout: float = 3.0) -> str:
        """Ermittelt die aktuelle öffentliche IP-Adresse."""
        endpoints = [
            "https://api.ipify.org?format=json",
            "https://ipinfo.io/json",
            "https://api.myip.com",
        ]
        for ep in endpoints:
            try:
                r = requests.get(ep, timeout=timeout)
                if r.status_code == 200:
                    data = r.json()
                    ip = str(data.get("ip") or "").strip()
                    if ip:
                        self._last_known_ip = ip
                        return ip
            except Exception:
                continue
        return self._last_known_ip or "Unbekannt"

    @staticmethod
    def guess_country_for_profile(profile_name: str = "", portal_url: str = "") -> str:
        """
        Leitet aus dem Profilnamen oder der Portal-Domain das optimale Zielland ab.
        Beispiel: 'DE | HD paplive.me' -> 'Germany', '.tr' -> 'Turkey'
        """
        combined = f"{profile_name} {portal_url}".lower()

        # Länder-Heuristik
        if re.search(r"\b(de|deutsch|germany|ger|ard|zdf)\b", combined) or ".de" in combined:
            return "Germany"
        if re.search(r"\b(tr|turk|türk|turkey)\b", combined) or ".tr" in combined:
            return "Turkey"
        if re.search(r"\b(at|austria|österreich)\b", combined) or ".at" in combined:
            return "Austria"
        if re.search(r"\b(ch|swiss|schweiz)\b", combined) or ".ch" in combined:
            return "Switzerland"
        if re.search(r"\b(nl|netherlands|holland)\b", combined) or ".nl" in combined:
            return "Netherlands"
        if re.search(r"\b(uk|gb|england|britain)\b", combined) or ".co.uk" in combined:
            return "United Kingdom"
        if re.search(r"\b(us|usa|united states)\b", combined) or ".us" in combined:
            return "United States"
        if re.search(r"\b(fr|france|frankreich)\b", combined) or ".fr" in combined:
            return "France"
        if re.search(r"\b(it|italy|italien)\b", combined) or ".it" in combined:
            return "Italy"
        if re.search(r"\b(es|spain|spanien)\b", combined) or ".es" in combined:
            return "Spain"

        # Standard-Fallback für europäische IPTV-Dienste: Germany
        return "Germany"

    def switch_server(
        self,
        target_country: Optional[str] = None,
        callback: Optional[Callable[[bool, str], None]] = None,
    ) -> bool:
        """
        Wechselt asynchron zu einem neuen NordVPN-Server (optional mit Länderangabe).
        Benachrichtigt die UI über den Event-Bus und ruft den Callback nach Abschluss auf.
        """
        cli = self._detect_cli()
        if not cli:
            if callback:
                callback(False, "NordVPN ist nicht installiert.")
            return False

        now = time.time()
        with self._lock:
            # 8 Sekunden Cooldown zwischen Server-Wechseln zum Schutz des Daemons
            if self._is_switching or (now - self._last_switch_time < 8.0):
                if callback:
                    callback(False, "Server-Wechsel läuft bereits oder Cooldown aktiv.")
                return False
            self._is_switching = True
            self._last_switch_time = now

        country = (target_country or "").strip()
        msg_target = f"zu {country}" if country else "neuer Server (Quick Connect)"
        event_bus.log_message.emit(f"[🛡️ VPN] Wechsle NordVPN Server {msg_target}...")
        event_bus.vpn_status_changed.emit("switching", f"Wechsle Server {msg_target}...")

        def _worker():
            success = False
            new_ip = ""
            try:
                cmd = [cli, "-c"]
                if country:
                    cmd.extend(["-g", country])

                # Starte NordVPN CLI
                subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=8,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )

                # Warte bis Schnittstelle wieder online ist und IP wechselt (max. 12s)
                t_start = time.time()
                while time.time() - t_start < 12.0:
                    time.sleep(1.2)
                    ip = self.get_public_ip(timeout=2.0)
                    if ip and ip != "Unbekannt":
                        new_ip = ip
                        success = True
                        break

            except Exception as e:
                new_ip = str(e)
            finally:
                with self._lock:
                    self._is_switching = False

                if success:
                    info = f"NordVPN verbunden ({country or 'Quick'}): {new_ip}"
                    event_bus.log_message.emit(f"[🛡️ VPN] {info}")
                    event_bus.vpn_status_changed.emit("connected", info)
                else:
                    err_info = f"NordVPN Wechsel fehlgeschlagen ({new_ip})"
                    event_bus.log_message.emit(f"[⚠️ VPN] {err_info}")
                    event_bus.vpn_status_changed.emit("error", err_info)

                if callback:
                    try:
                        callback(success, new_ip)
                    except Exception:
                        pass

        th = threading.Thread(target=_worker, daemon=True, name="NordVpnSwitcher")
        th.start()
        return True

    def handle_ip_ban(
        self,
        url: str,
        err_msg: str,
        profile_name: str = "",
        on_success: Optional[Callable[[], None]] = None,
    ) -> bool:
        """
        Reagiert auf eine detektierte IP_BAN / ISP_LOCK Sperre.
        Ermittelt das optimale Zielland und leitet den Serverwechsel mit anschließendem Retry ein.
        """
        if not self._auto_switch_enabled or not self.is_installed():
            return False

        country = self.guess_country_for_profile(profile_name, url)
        event_bus.log_message.emit(
            f"[🛡️ VPN] 🚫 IP-/ISP-Sperre erkannt! Rotiere NordVPN automatisch nach '{country}'..."
        )

        def _on_switched(ok: bool, new_ip: str):
            if ok and on_success:
                time.sleep(0.5)
                on_success()

        return self.switch_server(target_country=country, callback=_on_switched)


# Globaler Singleton
vpn_manager = NordVpnManager()
