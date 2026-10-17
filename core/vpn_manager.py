"""
NordVPN Manager für STB Pro Qt6.
Erkennt eine aktive NordVPN-Installation, überwacht den Verbindungsstatus und
führt bei Erkennung von IP-/ISP-Sperren (IP_BAN / ISP_LOCK) vollautomatische,
mehrstufige Server- und Länder-Rotationen via NordVPN-CLI durch.
Speichert verbrannte IPs pro Host und respektiert Benutzer-Präferenzen zur VPN-Steuerung.
"""
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
from typing import Optional, Callable, Tuple, List, Dict, Set
import requests

from core.signals import event_bus


def _safe_emit(sig, *args):
    """Sicheres Emitten von Qt-Signalen aus Hintergrund-Threads."""
    try:
        sig.emit(*args)
    except (RuntimeError, Exception):
        pass


class NordVpnManager:
    """
    Verwaltet die Integration mit NordVPN unter Windows.
    Unterstützt Quick-Connect, länderspezifische Server-Rotation,
    persistentes Tracking verbrannter IPs pro Host und reaktive Auto-Umschaltung.
    """

    NORD_PATHS = [
        r"C:\Program Files\NordVPN\NordVPN.exe",
        r"C:\Program Files (x86)\NordVPN\NordVPN.exe",
        r"C:\Program Files\NordVPN\nordvpn.exe",
    ]

    ROTATION_POOLS: Dict[str, List[str]] = {
        "Germany": ["Switzerland", "Austria", "Netherlands", "Berlin", "Germany", "France", "United Kingdom"],
        "Turkey": ["Turkey", "Germany", "Netherlands", "Bulgaria", "Greece"],
        "Austria": ["Austria", "Switzerland", "Germany", "Netherlands"],
        "Switzerland": ["Switzerland", "Austria", "Germany", "Netherlands"],
        "Netherlands": ["Netherlands", "Germany", "Belgium", "France", "Switzerland"],
        "United Kingdom": ["United Kingdom", "Ireland", "Netherlands", "Germany"],
        "United States": ["United States", "Canada", "United Kingdom"],
    }

    def __init__(self):
        self._cli_path: Optional[str] = None
        self._lock = threading.Lock()
        self._last_switch_time: float = 0.0
        self._is_switching: bool = False
        self._auto_switch_enabled: bool = True
        self._last_known_ip: str = ""
        self._last_known_country: str = ""
        self._burned_ips: Dict[str, Set[str]] = {}
        self._host_rotation_index: Dict[str, int] = {}
        self._global_rotation_idx: int = -1
        self._consecutive_hops: Dict[str, int] = {}
        self._config_mgr = None
        self._detect_cli()

    def set_config_manager(self, mgr):
        """Bindet den Konfigurations-Manager ein und synchronisiert gespeicherte Einstellungen."""
        self._config_mgr = mgr
        if mgr:
            self._auto_switch_enabled = bool(mgr.get("vpn_auto_switch", True))
            raw_burned = mgr.get("burned_ips", {})
            if isinstance(raw_burned, dict):
                for host, ips in raw_burned.items():
                    if isinstance(ips, list):
                        self._burned_ips[self._normalize_host(host)] = set(str(x) for x in ips)

    @property
    def auto_switch_enabled(self) -> bool:
        if self._config_mgr:
            return bool(self._config_mgr.get("vpn_auto_switch", True))
        return self._auto_switch_enabled

    @auto_switch_enabled.setter
    def auto_switch_enabled(self, val: bool):
        self._auto_switch_enabled = bool(val)
        if self._config_mgr:
            self._config_mgr.set("vpn_auto_switch", bool(val), auto_save=True)

    def _detect_cli(self) -> Optional[str]:
        if self._config_mgr:
            custom_p = str(self._config_mgr.get("vpn_custom_cli_path", "")).strip()
            if custom_p and os.path.exists(custom_p):
                self._cli_path = custom_p
                return custom_p

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
            return True

    def is_connected(self) -> bool:
        """Prüft über die Routing-Tabelle, ob der NordLynx-Tunnel aktiv Datenverkehr leitet."""
        try:
            res = subprocess.run(
                ["route", "print", "0.0.0.0"],
                capture_output=True,
                text=True,
                timeout=2,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            for line in res.stdout.splitlines():
                if "0.0.0.0" in line and ("100." in line or "nordlynx" in line.lower()):
                    return True
        except Exception:
            pass
        return False

    def get_public_ip(self, timeout: float = 3.0) -> str:
        """Ermittelt die aktuelle öffentliche IP-Adresse und Standortinformationen."""
        endpoints = [
            "https://api.nordvpn.com/v1/helpers/ips/insights",
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
                        c = data.get("country")
                        if c:
                            self._last_known_country = str(c)
                        return ip
            except Exception:
                continue
        return self._last_known_ip or "Unbekannt"

    @staticmethod
    def _normalize_host(host_or_url: str) -> str:
        s = str(host_or_url or "").strip()
        if "://" in s:
            try:
                parsed = urllib.parse.urlparse(s)
                s = parsed.netloc or parsed.path
            except Exception:
                pass
        if ":" in s:
            s = s.split(":")[0]
        return s.strip("/ ").lower()

    # ──────────────────────────────────────────────────────────────────────
    # Verbrannte IPs Tracking
    # ──────────────────────────────────────────────────────────────────────

    def mark_ip_burned(self, host: str, ip: str, reason: str = ""):
        """Markiert eine IP für einen bestimmten Host als gesperrt/verbrannt."""
        clean_host = self._normalize_host(host)
        clean_ip = str(ip or "").strip()
        if not clean_host or not clean_ip or clean_ip in ("Unbekannt", ""):
            return

        with self._lock:
            s = self._burned_ips.setdefault(clean_host, set())
            if clean_ip not in s:
                s.add(clean_ip)
                event_bus.log_message.emit(
                    f"[🔥 Verbrannte IP] Host '{clean_host}': IP {clean_ip} blockiert ({reason or 'IP/ISP-Block'})."
                )
                if self._config_mgr:
                    self._config_mgr.add_burned_ip(clean_host, clean_ip)

    def is_ip_burned(self, host: str, ip: str) -> bool:
        """Prüft, ob eine IP für den angegebenen Host bereits als gesperrt markiert wurde."""
        clean_host = self._normalize_host(host)
        clean_ip = str(ip or "").strip()
        if not clean_host or not clean_ip:
            return False

        with self._lock:
            if clean_host in self._burned_ips and clean_ip in self._burned_ips[clean_host]:
                return True
            if self._config_mgr:
                return clean_ip in self._config_mgr.get_burned_ips(clean_host)
            return False

    def get_burned_ips(self, host: str) -> List[str]:
        """Gibt die Liste aller verbrannten IPs für einen Host zurück."""
        clean_host = self._normalize_host(host)
        with self._lock:
            ips = set(self._burned_ips.get(clean_host, set()))
            if self._config_mgr:
                ips.update(self._config_mgr.get_burned_ips(clean_host))
            return sorted(list(ips))

    def clear_burned_ips(self, host: Optional[str] = None):
        """Setzt verbrannte IPs zurück (für einen Host oder global)."""
        with self._lock:
            if host:
                clean_host = self._normalize_host(host)
                self._burned_ips.pop(clean_host, None)
                if self._config_mgr:
                    self._config_mgr.clear_burned_ips(clean_host)
                event_bus.log_message.emit(f"[🧹 VPN] Verbrannte IPs für '{clean_host}' gelöscht.")
            else:
                self._burned_ips.clear()
                if self._config_mgr:
                    self._config_mgr.clear_burned_ips()
                event_bus.log_message.emit("[🧹 VPN] Alle verbrannten IPs zurückgesetzt.")

    def reset_consecutive_hops(self, host: Optional[str] = None):
        """Setzt den Zähler für konsekutive Hops zurück (z.B. bei stabiler Wiedergabe)."""
        with self._lock:
            if host:
                self._consecutive_hops.pop(self._normalize_host(host), None)
            else:
                self._consecutive_hops.clear()

    # ──────────────────────────────────────────────────────────────────────
    # Länder- & Server-Rotation
    # ──────────────────────────────────────────────────────────────────────

    @classmethod
    def guess_country_for_profile(cls, profile_name: str = "", portal_url: str = "") -> str:
        """
        Leitet aus dem Profilnamen oder der Portal-Domain das optimale Zielland ab.
        Beispiel: 'DE | HD paplive.me' -> 'Germany', '.tr' -> 'Turkey'
        """
        combined = f"{profile_name} {portal_url}".lower()

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

        return "Germany"

    def get_rotation_candidates(self, base_country: str) -> List[str]:
        """Liefert eine geordnete Liste alternativer Länder für die Rotation."""
        if self._config_mgr:
            custom_pool = self._config_mgr.get("vpn_rotation_pool")
            if custom_pool and isinstance(custom_pool, list) and len(custom_pool) > 0:
                clean_pool = [str(x).strip() for x in custom_pool if str(x).strip()]
                if clean_pool:
                    if base_country in clean_pool:
                        return [base_country] + [c for c in clean_pool if c != base_country]
                    return clean_pool

        pool = self.ROTATION_POOLS.get(base_country)
        if pool:
            return list(pool)
        return [base_country, "Germany", "Switzerland", "Austria", "Netherlands"]

    def disconnect(self, callback: Optional[Callable[[bool, str], None]] = None) -> bool:
        """
        Trennt die aktive NordVPN-Verbindung sauber (-d), um das Gerätelimit in der Cloud freizugeben.
        """
        cli = self._detect_cli()
        if not cli:
            if callback:
                callback(False, "NordVPN ist nicht installiert.")
            return False

        event_bus.log_message.emit("[🛡️ VPN] Trenne aktive NordVPN-Verbindung (-d)...")
        event_bus.vpn_status_changed.emit("switching", "Trenne VPN...")

        cli_dir = os.path.dirname(cli) if os.path.dirname(cli) else None

        def _worker():
            try:
                subprocess.run(
                    [cli, "-d"],
                    capture_output=True,
                    text=True,
                    timeout=6,
                    cwd=cli_dir,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                time.sleep(1.2)
                _safe_emit(event_bus.log_message, "[🛡️ VPN] NordVPN sauber getrennt. Verbindungslimit freigegeben.")
                _safe_emit(event_bus.vpn_status_changed, "disconnected", "NordVPN getrennt")
                if callback:
                    callback(True, "NordVPN getrennt")
            except Exception as e:
                _safe_emit(event_bus.log_message, f"[⚠️ VPN] Fehler beim Trennen: {e}")
                _safe_emit(event_bus.vpn_status_changed, "error", str(e))
                if callback:
                    callback(False, str(e))

        th = threading.Thread(target=_worker, daemon=True, name="NordVpnDisconnecter")
        th.start()
        return True

    def switch_server(
        self,
        target_country: Optional[str] = None,
        callback: Optional[Callable[[bool, str], None]] = None,
    ) -> bool:
        """
        Wechselt asynchron zu einem neuen NordVPN-Server (optional mit Länderangabe).
        Verbindet direkt via (-c), um störende Auto-Connect-Bestätigungsdialoge zu vermeiden.
        Rotiert bei leerer Länderangabe dynamisch durch verfügbare Länder statt statisch auf Frankfurt.
        """
        cli = self._detect_cli()
        if not cli:
            if callback:
                callback(False, "NordVPN ist nicht installiert.")
            return False

        now = time.time()
        cooldown = float(self._config_mgr.get("vpn_cooldown_seconds", 15.0)) if self._config_mgr else 15.0
        with self._lock:
            # Konfigurierbarer Cooldown zwischen Server-Wechseln, um NordVPN-Gerätelimits zu schützen
            if self._is_switching or (now - self._last_switch_time < cooldown):
                if callback:
                    callback(False, f"Server-Wechsel läuft bereits oder Cooldown aktiv ({int(cooldown)}s).")
                return False
            self._is_switching = True
            self._last_switch_time = now

            country = (target_country or "").strip()
            if not country:
                fallback_candidates = self.get_rotation_candidates("Germany")
                self._global_rotation_idx = (self._global_rotation_idx + 1) % len(fallback_candidates)
                country = fallback_candidates[self._global_rotation_idx]

        msg_target = f"nach {country}"
        event_bus.log_message.emit(f"[🛡️ VPN] Wechsle NordVPN Server {msg_target}...")
        event_bus.vpn_status_changed.emit("switching", f"Wechsle Server {msg_target}...")

        cli_dir = os.path.dirname(cli) if os.path.dirname(cli) else None

        def _worker():
            success = False
            new_ip = ""
            try:
                cmd = [cli, "-c", "-g", country]

                subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=8,
                    cwd=cli_dir,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )

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
                    info = f"NordVPN verbunden ({country}): {new_ip}"
                    _safe_emit(event_bus.log_message, f"[🛡️ VPN] {info}")
                    _safe_emit(event_bus.vpn_status_changed, "connected", info)
                else:
                    err_info = f"NordVPN Wechsel fehlgeschlagen ({new_ip})"
                    _safe_emit(event_bus.log_message, f"[⚠️ VPN] {err_info}")
                    _safe_emit(event_bus.vpn_status_changed, "error", err_info)

                if callback:
                    try:
                        callback(success, new_ip)
                    except Exception:
                        pass

        th = threading.Thread(target=_worker, daemon=True, name="NordVpnSwitcher")
        th.start()
        return True

    def rotate_server_for_host(
        self,
        host: str,
        profile_name: str = "",
        on_success: Optional[Callable[[], None]] = None,
    ) -> bool:
        """
        Rotiert intelligent und sequenziell zu einem frischen Ziel-Server/Land.
        Verbindet direkt via (-c), um störende Auto-Connect-Bestätigungsdialoge zu vermeiden.
        Zyklischer Durchlauf aller Kandidaten pro Host, damit niemals auf derselben Location verharrt wird.
        """
        if not self.auto_switch_enabled or not self.is_installed():
            return False

        cli = self._detect_cli()
        if not cli:
            return False

        clean_host = self._normalize_host(host)
        base_country = self.guess_country_for_profile(profile_name, clean_host)
        candidates = self.get_rotation_candidates(base_country)
        if not candidates:
            candidates = ["Switzerland", "Austria", "Netherlands", "Berlin", "Germany"]

        now = time.time()
        debounce = float(self._config_mgr.get("vpn_debounce_seconds", 2.0)) if self._config_mgr else 2.0
        cooldown = float(self._config_mgr.get("vpn_cooldown_seconds", 15.0)) if self._config_mgr else 15.0
        max_hops_cfg = int(self._config_mgr.get("vpn_max_consecutive_hops", 5)) if self._config_mgr else 5
        limit_hops = max(1, min(max_hops_cfg, len(candidates)))

        with self._lock:
            # 1. Kein paralleler Umschaltvorgang
            if self._is_switching:
                return False

            # 2. Mindestens Debounce-Zeit abwarten, damit Routing und Interface nach dem letzten Wechsel stabil sind
            if now - self._last_switch_time < debounce:
                event_bus.log_message.emit(
                    f"[🛡️ VPN] Rotation für '{clean_host}' verzögert (Netzwerk-Stabilisierung {debounce:.1f}s)..."
                )
                return False

            # 3. Konsekutive Hops: Wenn ein Standort unmittelbar blockiert wird, sofort zum nächsten springen!
            hops = self._consecutive_hops.get(clean_host, 0)
            if hops >= limit_hops:
                if now - self._last_switch_time < cooldown:
                    event_bus.log_message.emit(
                        f"[🛡️ VPN] Alle {limit_hops} Standorte für '{clean_host}' getestet (Cooldown {int(cooldown)}s aktiv)."
                    )
                    return False
                self._consecutive_hops[clean_host] = 0
                hops = 0

            self._consecutive_hops[clean_host] = hops + 1
            self._is_switching = True
            self._last_switch_time = now

            prev_idx = self._host_rotation_index.get(clean_host, -1)
            next_idx = (prev_idx + 1) % len(candidates)
            self._host_rotation_index[clean_host] = next_idx
            target_country = candidates[next_idx]

        event_bus.log_message.emit(
            f"[🛡️ VPN] Starte Server-Rotation für '{clean_host}' (Hop {hops + 1}/{len(candidates)}) nach {target_country}..."
        )
        event_bus.vpn_status_changed.emit("switching", f"Rotiere nach {target_country}...")

        cli_dir = os.path.dirname(cli) if os.path.dirname(cli) else None

        def _rotation_worker():
            final_ip = ""
            success = False

            try:
                # Verbindung zum Zielland aufbauen (NordVPN wechselt den Server nahtlos ohne Auto-Connect-Modal)
                cmd = [cli, "-c", "-g", target_country]
                subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=8,
                    cwd=cli_dir,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )

                # Warte auf neue IP
                t_start = time.time()
                while time.time() - t_start < 12.0:
                    time.sleep(1.2)
                    ip = self.get_public_ip(timeout=2.0)
                    if ip and ip != "Unbekannt":
                        final_ip = ip
                        success = True
                        break

                if success and final_ip:
                    if self.is_ip_burned(clean_host, final_ip):
                        event_bus.log_message.emit(
                            f"[🔥 VPN] Erhaltene IP {final_ip} ({target_country}) ist für '{clean_host}' bereits verbrannt."
                        )
                    else:
                        event_bus.log_message.emit(
                            f"[🛡️ VPN] Frische, unverbrannte IP {final_ip} ({target_country}) aktiv!"
                        )

            except Exception as e:
                final_ip = str(e)
            finally:
                with self._lock:
                    self._is_switching = False

                if success:
                    info = f"NordVPN verbunden ({target_country}): {final_ip}"
                    _safe_emit(event_bus.log_message, f"[🛡️ VPN] {info}")
                    _safe_emit(event_bus.vpn_status_changed, "connected", info)
                    if on_success:
                        time.sleep(0.5)
                        on_success()
                else:
                    err_info = f"NordVPN Rotation fehlgeschlagen ({final_ip})"
                    _safe_emit(event_bus.log_message, f"[⚠️ VPN] {err_info}")
                    _safe_emit(event_bus.vpn_status_changed, "error", err_info)

        th = threading.Thread(target=_rotation_worker, daemon=True, name="NordVpnRotator")
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
        Markiert die aktuelle IP als verbrannt und startet bei aktiver Option die Rotation.
        """
        clean_host = self._normalize_host(url)
        cur_ip = self.get_public_ip(timeout=1.5) or self._last_known_ip

        # 1. Aktuelle IP als verbrannt für diesen Host markieren
        if cur_ip and cur_ip != "Unbekannt":
            self.mark_ip_burned(clean_host, cur_ip, reason=err_msg)

        # 2. Prüfen, ob Auto-Switch vom Benutzer gewünscht und NordVPN aktiv ist
        if not self.auto_switch_enabled:
            event_bus.log_message.emit(
                f"[🛡️ VPN] IP-Sperre erkannt auf '{clean_host}'. Auto-VPN ist in den Einstellungen deaktiviert."
            )
            return False

        if not self.is_installed() or not self.is_running():
            event_bus.log_message.emit(
                f"[⚠️ VPN] IP-Sperre auf '{clean_host}', aber NordVPN ist nicht gestartet oder nicht erreichbar."
            )
            return False

        # 3. Intelligente Rotation durchführen
        return self.rotate_server_for_host(
            host=clean_host,
            profile_name=profile_name,
            on_success=on_success,
        )


# Globaler Singleton
vpn_manager = NordVpnManager()
