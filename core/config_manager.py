"""
Konfigurations-Manager für STB Pro Qt6.
Unterstützt nahtlose Übernahme der bestehenden config.json aus dem Hauptverzeichnis,
damit alle gespeicherten Profile, Favoriten und Einstellungen erhalten bleiben.
Zusätzlich neu: Persistente VOD-Favoriten und Recently-Played-Historie!
"""
import os
import json
import shutil
from typing import Dict, List, Optional, Any
from core.models import Profile

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(APP_DIR)
LOCAL_CONFIG_FILE = os.path.join(APP_DIR, "config.json")
PARENT_CONFIG_FILE = os.path.join(PARENT_DIR, "config.json")


def detect_vlc_path() -> str:
    which = shutil.which("vlc")
    if which:
        return which
    win_paths = [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ]
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        win_paths.append(os.path.join(local_app, "Microsoft", "WinGet", "Links", "vlc.exe"))
    for p in win_paths:
        if os.path.exists(p):
            return p
    return ""


def detect_mpv_path() -> str:
    which = shutil.which("mpv")
    if which:
        return which
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        p = os.path.join(local_app, "Microsoft", "WinGet", "Links", "mpv.exe")
        if os.path.exists(p):
            return p
    return ""


def detect_ffplay_path() -> str:
    which = shutil.which("ffplay")
    if which:
        return which
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        wg_path = os.path.join(local_app, "Microsoft", "WinGet", "Links", "ffplay.exe")
        if os.path.exists(wg_path):
            return wg_path
    return ""


class ConfigManager:
    """Verwaltet Profile, Live-/VOD-Favoriten, Verlauf, Player-Pfade und UI-Einstellungen."""

    def __init__(self, filepath: Optional[str] = None):
        if filepath is None:
            # Nutze bestehende config.json im Hauptordner falls vorhanden, sonst lokal
            if os.path.exists(PARENT_CONFIG_FILE) and not os.path.exists(LOCAL_CONFIG_FILE):
                try:
                    shutil.copy2(PARENT_CONFIG_FILE, LOCAL_CONFIG_FILE)
                except Exception:
                    pass
            filepath = LOCAL_CONFIG_FILE
        self.filepath = filepath
        self.config: Dict[str, Any] = self._load()

    def _default_config(self) -> Dict[str, Any]:
        return {
            "profiles": [
                {
                    "name": "Standard Test",
                    "provider_type": "Stalker MAC",
                    "portal_url": "http://example.com:8080/c/",
                    "mac": "00:1A:79:00:11:22",
                    "model": "MAG 250",
                    "device_id": "",
                    "device_id2": "",
                    "signature": "",
                    "serial_number": "",
                    "user_agent": "",
                    "xc_url": "",
                    "username": "",
                    "password": "",
                    "xc_format": "ts",
                    "m3u_source": "",
                }
            ],
            "last_profile": "Standard Test",
            "vlc_path": detect_vlc_path(),
            "mpv_path": detect_mpv_path(),
            "ffplay_path": detect_ffplay_path(),
            "selected_player": "Integrierter Player",
            "player_volume": 100,
            "connection_timeout_label": "8s Standard",
            "favorites": {},
            "vod_favorites": {},
            "recently_played": {},
            "cached_endpoints": {},
            "ui_scale": "100%",
            "start_maximized": True,
            "hide_dead_channels": True,
            "validation_workers": 8,
            "validation_probe_timeout": 3.0,
            "validation_auto_start": True,

            # --- Connection & Handshake Defaults ---
            "ssl_verify": False,
            "handshake_connect_timeout": 4.5,
            "handshake_read_timeout": 8.0,
            "token_refresh_interval_s": 75,
            "default_stb_model": "MAG 250",
            "device_id_mode": "deterministic",
            "custom_user_agent_default": "",

            # --- Scanning & Probing Settings ---
            "scan_threads": 8,
            "scan_delay_s": 0.0,
            "scan_probe_timeout": 5.0,
            "scan_auto_requeue": True,
            "scan_max_requeue_retries": 2,
            "scan_genre_param": "*",
            "scan_sortby_param": "number",
            "scan_fallback_get_all": True,

            # --- Playback & Stream Buffering ---
            "buffer_settings": {
                "mode": "proxy",
                "vlc_caching_ms": 1200,
                "start_seconds": 0.8,
                "buffer_seconds": 15.0,
                "max_mb": 128,
                "fallback_kbps": 6000,
                "reconnect": True,
                "max_retries": 10,
                "timeout_connect": 5.0,
                "timeout_read": 10.0,
                "hw_decode": True,
                "preview_enabled": True,
                "preview_max_age_min": 15,
                "proxy": "",
            },
            "pcr_smoothing_enabled": True,

            # --- VPN Configuration ---
            "vpn_auto_switch": True,
            "vpn_cooldown_seconds": 15.0,
            "vpn_debounce_seconds": 2.0,
            "vpn_max_consecutive_hops": 5,
            "vpn_fallback_country": "Germany",
            "vpn_custom_cli_path": "",
            "vpn_rotation_pool": [
                "Switzerland",
                "Austria",
                "Netherlands",
                "Berlin",
                "Germany",
                "France",
                "United Kingdom",
            ],
            "burned_ips": {},
        }

    def _load(self) -> Dict[str, Any]:
        defaults = self._default_config()
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    for k, v in defaults.items():
                        if k not in cfg:
                            cfg[k] = v
                        elif isinstance(v, dict) and isinstance(cfg.get(k), dict):
                            for sub_k, sub_v in v.items():
                                if sub_k not in cfg[k]:
                                    cfg[k][sub_k] = sub_v
                    return cfg
            except Exception:
                pass
        return defaults

    def save(self) -> bool:
        try:
            tmp_path = self.filepath + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            if os.path.exists(self.filepath):
                os.replace(tmp_path, self.filepath)
            else:
                os.rename(tmp_path, self.filepath)
            # Synchronisiere auch zurück in die Parent config.json falls vorhanden
            if os.path.exists(PARENT_CONFIG_FILE) and os.path.abspath(self.filepath) != os.path.abspath(PARENT_CONFIG_FILE):
                try:
                    shutil.copy2(self.filepath, PARENT_CONFIG_FILE)
                except Exception:
                    pass
            return True
        except Exception:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True):
        self.config[key] = value
        if auto_save:
            self.save()

    def get_profiles(self) -> List[Profile]:
        raw_profiles = self.config.get("profiles", [])
        out = [Profile.from_dict(p) for p in raw_profiles if isinstance(p, dict)]
        return out if out else [Profile.from_dict(self._default_config()["profiles"][0])]

    def get_profile(self, name: str) -> Optional[Profile]:
        for p in self.get_profiles():
            if p.name == name:
                return p
        return None

    def save_profile(self, profile: Profile, old_name: Optional[str] = None):
        profiles = self.get_profiles()
        target_name = old_name or profile.name
        idx = next((i for i, p in enumerate(profiles) if p.name == target_name), None)
        if idx is not None:
            profiles[idx] = profile
        else:
            profiles.append(profile)
        self.config["profiles"] = [p.to_dict() for p in profiles]
        self.config["last_profile"] = profile.name
        self.save()

    def delete_profile(self, name: str) -> bool:
        profiles = self.get_profiles()
        if len(profiles) <= 1:
            return False
        new_profiles = [p for p in profiles if p.name != name]
        if len(new_profiles) == len(profiles):
            return False
        self.config["profiles"] = [p.to_dict() for p in new_profiles]
        self.config["last_profile"] = new_profiles[0].name
        self.save()
        return True

    def get_favorites(self, profile_name: str) -> List[str]:
        fav_dict = self.config.get("favorites", {})
        return [str(x) for x in fav_dict.get(profile_name, [])]

    def save_favorites(self, profile_name: str, favorites: List[str]):
        if "favorites" not in self.config or not isinstance(self.config["favorites"], dict):
            self.config["favorites"] = {}
        self.config["favorites"][profile_name] = [str(x) for x in favorites]
        self.save()

    def get_vod_favorites(self, profile_name: str) -> List[str]:
        fav_dict = self.config.get("vod_favorites", {})
        return [str(x) for x in fav_dict.get(profile_name, [])]

    def save_vod_favorites(self, profile_name: str, favorites: List[str]):
        if "vod_favorites" not in self.config or not isinstance(self.config["vod_favorites"], dict):
            self.config["vod_favorites"] = {}
        self.config["vod_favorites"][profile_name] = [str(x) for x in favorites]
        self.save()

    def get_recently_played(self, profile_name: str) -> List[str]:
        rec_dict = self.config.get("recently_played", {})
        return [str(x) for x in rec_dict.get(profile_name, [])]

    def save_recently_played(self, profile_name: str, channel_ids: List[str]):
        if "recently_played" not in self.config or not isinstance(self.config["recently_played"], dict):
            self.config["recently_played"] = {}
        self.config["recently_played"][profile_name] = [str(x) for x in channel_ids[:50]]
        self.save()

    def get_timeout_seconds(self) -> int:
        import re
        val = str(self.config.get("connection_timeout_label", "10s"))
        m = re.search(r"(\d+)", val)
        if m:
            return max(1, int(m.group(1)))
        return 10

    def get_burned_ips(self, host: str) -> List[str]:
        b = self.config.get("burned_ips", {})
        if not isinstance(b, dict):
            return []
        return [str(x) for x in b.get(host, [])]

    def add_burned_ip(self, host: str, ip: str):
        if not host or not ip or ip == "Unbekannt":
            return
        if "burned_ips" not in self.config or not isinstance(self.config["burned_ips"], dict):
            self.config["burned_ips"] = {}
        ips = list(self.config["burned_ips"].get(host, []))
        if ip not in ips:
            ips.append(ip)
            self.config["burned_ips"][host] = ips
            self.save()

    def clear_burned_ips(self, host: Optional[str] = None):
        if "burned_ips" not in self.config or not isinstance(self.config["burned_ips"], dict):
            self.config["burned_ips"] = {}
        if host:
            self.config["burned_ips"].pop(host, None)
        else:
            self.config["burned_ips"] = {}
        self.save()

