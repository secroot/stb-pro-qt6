"""
Persistente, threadsichere MAC-Hit-Datenbank für STB Pro Qt6.
Synchronisiert sich automatisch mit einer vorhandenen mac_database.json im Hauptordner.
"""
import os
import re
import json
import time
import shutil
import threading
from typing import Dict, List, Optional, Any

from core.models import is_valid_expire_date

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(APP_DIR)
LOCAL_DB_FILE = os.path.join(APP_DIR, "mac_database.json")
PARENT_DB_FILE = os.path.join(PARENT_DIR, "mac_database.json")


def format_mac_str(mac: str) -> str:
    cleaned = re.sub(r'[^0-9A-Fa-f]', '', mac or "").upper()
    if len(cleaned) == 12:
        return ":".join(cleaned[i:i+2] for i in range(0, 12, 2))
    return (mac or "").strip().upper()


class MacDatabase:
    """
    Persistente, threadsichere Datenbank für gefundene MAC-Adressen mit Sendern.
    Speichert verifizierte Accounts getrennt nach Portal-URL und global mit Dubletten-Check.
    """

    def __init__(self, filepath: Optional[str] = None):
        if filepath is None:
            if os.path.exists(PARENT_DB_FILE) and not os.path.exists(LOCAL_DB_FILE):
                try:
                    shutil.copy2(PARENT_DB_FILE, LOCAL_DB_FILE)
                except Exception:
                    pass
            filepath = LOCAL_DB_FILE
        self.filepath = filepath
        self._lock = threading.RLock()
        self._db: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        data.setdefault("portals", {})
                        data.setdefault("global_history", {})
                        return data
            except Exception:
                pass
        return {"portals": {}, "global_history": {}}

    def _save(self):
        try:
            tmp_path = self.filepath + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._db, f, indent=2, ensure_ascii=False)
            if os.path.exists(self.filepath):
                os.replace(tmp_path, self.filepath)
            else:
                os.rename(tmp_path, self.filepath)
            if os.path.exists(PARENT_DB_FILE) and os.path.abspath(self.filepath) != os.path.abspath(PARENT_DB_FILE):
                try:
                    shutil.copy2(self.filepath, PARENT_DB_FILE)
                except Exception:
                    pass
        except Exception:
            pass

    def save_found_mac(self, portal_url: str, res: Dict[str, Any]) -> bool:
        mac = format_mac_str(str(res.get("mac", "")))
        if not mac:
            return False

        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        norm_portal = (portal_url or "").strip().rstrip("/")

        try:
            ch_cnt = int(res.get("channels", 0) or 0)
        except Exception:
            ch_cnt = 0

        new_expire = str(res.get("expire", "Unbekannt"))

        with self._lock:
            self._db.setdefault("portals", {})
            self._db["portals"].setdefault(norm_portal, {})

            existing = self._db["portals"][norm_portal].get(mac)
            first_seen = now_str
            if existing:
                first_seen = existing.get("first_seen", now_str)
                prev_ch = int(existing.get("channels", 0) or 0)
                if prev_ch > ch_cnt:
                    ch_cnt = prev_ch
                prev_exp = existing.get("expire", "")
                if is_valid_expire_date(prev_exp) and not is_valid_expire_date(new_expire):
                    new_expire = prev_exp

            # Nur echte Treffer mit gültigem Ablaufdatum und Kanälen > 0 aufnehmen
            if ch_cnt <= 0 or not is_valid_expire_date(new_expire):
                return False

            vpn_loc = str(res.get("vpn_location") or res.get("proxy_location") or (existing or {}).get("vpn_location") or "")
            record = {
                "mac": mac,
                "portal_url": norm_portal,
                "channels": ch_cnt,
                "expire": new_expire,
                "status": str(res.get("status", "Aktiv")),
                "token": str(res.get("token", "")),
                "model": str(res.get("model") or (existing or {}).get("model") or "MAG 250"),
                "vpn_location": vpn_loc,
                "first_seen": first_seen,
                "last_seen": now_str,
            }

            self._db["portals"][norm_portal][mac] = record

            self._db.setdefault("global_history", {})
            g_existing = self._db["global_history"].get(mac)
            if g_existing:
                record["first_seen"] = g_existing.get("first_seen", first_seen)
            self._db["global_history"][mac] = record

            self._save()
        return True

    def get_known_macs(self, portal_url: Optional[str] = None) -> List[str]:
        with self._lock:
            portal_macs = []
            if portal_url:
                norm_portal = portal_url.strip().rstrip("/")
                p_dict = self._db.get("portals", {}).get(norm_portal, {})
                sorted_p = sorted(
                    p_dict.values(),
                    key=lambda x: (int(str(x.get("channels", 0)).strip() or 0), str(x.get("last_seen", ""))),
                    reverse=True,
                )
                portal_macs = [format_mac_str(item["mac"]) for item in sorted_p if "mac" in item]

            global_dict = self._db.get("global_history", {})
            sorted_g = sorted(
                global_dict.values(),
                key=lambda x: (int(str(x.get("channels", 0)).strip() or 0), str(x.get("last_seen", ""))),
                reverse=True,
            )
            global_macs = [format_mac_str(item["mac"]) for item in sorted_g if "mac" in item]

            return list(dict.fromkeys(portal_macs + global_macs))

    def get_all_records(self, portal_url: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if portal_url and portal_url not in ("all", "Alle Portale"):
                norm_portal = portal_url.strip().rstrip("/")
                p_dict = self._db.get("portals", {}).get(norm_portal, {})
                return list(p_dict.values())
            global_dict = self._db.get("global_history", {})
            return list(global_dict.values())

    def get_portals(self) -> List[str]:
        with self._lock:
            return [k for k in self._db.get("portals", {}).keys() if k]

    def delete_entry(self, mac: str, portal_url: Optional[str] = None) -> bool:
        norm_mac = format_mac_str(mac)
        with self._lock:
            modified = False
            if portal_url and portal_url not in ("all", "Alle Portale"):
                norm_portal = portal_url.strip().rstrip("/")
                if norm_portal in self._db.get("portals", {}) and norm_mac in self._db["portals"][norm_portal]:
                    del self._db["portals"][norm_portal][norm_mac]
                    modified = True
            else:
                for p_key in list(self._db.get("portals", {}).keys()):
                    if norm_mac in self._db["portals"][p_key]:
                        del self._db["portals"][p_key][norm_mac]
                        modified = True

            if norm_mac in self._db.get("global_history", {}):
                del self._db["global_history"][norm_mac]
                modified = True

            if modified:
                self._save()
            return modified

    def clean_duplicates(self) -> int:
        with self._lock:
            removed = 0
            new_portals = {}
            for p_url, mac_map in self._db.get("portals", {}).items():
                clean_p = p_url.strip().rstrip("/")
                new_portals.setdefault(clean_p, {})
                for m_key, val in mac_map.items():
                    norm_m = format_mac_str(m_key)
                    if not is_valid_expire_date(val.get("expire")) or int(val.get("channels", 0) or 0) <= 0:
                        removed += 1
                        continue
                    if norm_m in new_portals[clean_p]:
                        removed += 1
                    else:
                        val["mac"] = norm_m
                        val["portal_url"] = clean_p
                        new_portals[clean_p][norm_m] = val

            new_global = {}
            for m_key, val in self._db.get("global_history", {}).items():
                norm_m = format_mac_str(m_key)
                if not is_valid_expire_date(val.get("expire")) or int(val.get("channels", 0) or 0) <= 0:
                    removed += 1
                    continue
                if norm_m in new_global:
                    removed += 1
                else:
                    val["mac"] = norm_m
                    new_global[norm_m] = val

            self._db["portals"] = new_portals
            self._db["global_history"] = new_global
            self._save()
            return removed

    def get_count(self) -> int:
        with self._lock:
            return len(self._db.get("global_history", {}))

    def total_count(self) -> int:
        return self.get_count()

    def has_portal_entries(self, portal_url: Optional[str] = None) -> bool:
        if not portal_url:
            return self.get_count() > 0
        norm = portal_url.strip().rstrip("/")
        with self._lock:
            p_dict = self._db.get("portals", {}).get(norm, {})
            return len(p_dict) > 0

    def get_entries(self, portal_url: Optional[str] = None) -> List[Dict[str, Any]]:
        raw = self.get_all_records(portal_url)
        out = []
        for r in raw:
            item = dict(r)
            item.setdefault("portal", item.get("portal_url", ""))
            item.setdefault("expiry", item.get("expire", "—"))
            item.setdefault("model", item.get("model", "MAG 250"))
            item.setdefault("vpn_location", item.get("vpn_location", "—"))
            item.setdefault("proxy_location", item.get("proxy_location", item.get("vpn_location", "—")))
            out.append(item)
        return out

    def deduplicate(self) -> int:
        return self.clean_duplicates()

    def remove_entry(self, portal_url: str, mac: str) -> bool:
        return self.delete_entry(mac=mac, portal_url=portal_url)

