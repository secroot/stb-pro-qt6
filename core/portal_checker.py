"""
Stalker Portal Erreichbarkeits-Checker & Rotations-Pool.
Prüft Stalker-Portale aus Listen (z. B. stalker_portals.txt) multi-threaded
auf Erreichbarkeit, Latenz (Ping), HTTP-Status und Stalker-Signaturen.
Ermöglicht das Speichern erreichbarer Portale und deren direkte Bereitstellung
zur automatischen Rotation im MAC-Scanner.
"""
from __future__ import annotations

import collections
import datetime
import os
import queue
import re
import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
import urllib3

# Deaktiviere unsichere HTTPS-Warnungen für Self-Signed Stalker-Zertifikate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_PORTAL_TIMEOUT = 3.0
DEFAULT_CHECKER_THREADS = 25


@dataclass
class PortalCheckResult:
    """Repräsentiert das Prüfergebnis eines einzelnen Stalker-Portals."""
    url: str
    host: str
    port: int
    is_online: bool
    status_code: Optional[int] = None
    latency_ms: float = 0.0
    server: str = ""
    stalker_detected: bool = False
    endpoint: str = ""
    error: Optional[str] = None
    checked_at: str = field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "host": self.host,
            "port": self.port,
            "is_online": self.is_online,
            "status_code": self.status_code,
            "latency_ms": self.latency_ms,
            "server": self.server,
            "stalker_detected": self.stalker_detected,
            "endpoint": self.endpoint,
            "error": self.error,
            "checked_at": self.checked_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PortalCheckResult:
        return cls(
            url=data.get("url", ""),
            host=data.get("host", ""),
            port=int(data.get("port", 80)),
            is_online=bool(data.get("is_online", False)),
            status_code=data.get("status_code"),
            latency_ms=float(data.get("latency_ms", 0.0)),
            server=data.get("server", ""),
            stalker_detected=bool(data.get("stalker_detected", False)),
            endpoint=data.get("endpoint", ""),
            error=data.get("error"),
            checked_at=data.get("checked_at", ""),
        )

    def display_status(self) -> str:
        if self.is_online and self.stalker_detected:
            return f"🟢 Stalker OK ({self.status_code})"
        if self.is_online:
            return f"🟢 Stalker OK ({self.status_code})"
        if self.status_code is not None and not self.stalker_detected:
            return f"🔴 Kein Stalker ({self.status_code})"
        if self.error:
            if "Timeout" in self.error or "timed out" in self.error.lower():
                return "⏳ Timeout"
            if "DNS" in self.error or "gaierror" in self.error.lower():
                return "🔴 DNS-Fehler"
            if "Connection refused" in self.error or "Verbindung abgelehnt" in self.error:
                return "🔴 Refused"
        return "🔴 Offline"


# Vollständige Liste an gültigen IANA TLDs (ccTLDs + gTLDs) zur Vermeidung von False-Positives aus Combo-Listen
VALID_TLDS = {
    # 2-stellige ccTLDs (Länder-Domains)
    "ac", "ad", "ae", "af", "ag", "ai", "al", "am", "ao", "aq", "ar", "as", "at", "au", "aw", "ax", "az",
    "ba", "bb", "bd", "be", "bf", "bg", "bh", "bi", "bj", "bm", "bn", "bo", "br", "bs", "bt", "bw", "by", "bz",
    "ca", "cc", "cd", "cf", "cg", "ch", "ci", "ck", "cl", "cm", "cn", "co", "cr", "cu", "cv", "cw", "cx", "cy", "cz",
    "de", "dj", "dk", "dm", "do", "dz", "ec", "ee", "eg", "er", "es", "et", "eu", "fi", "fj", "fk", "fm", "fo", "fr",
    "ga", "gb", "gd", "ge", "gf", "gg", "gh", "gi", "gl", "gm", "gn", "gp", "gq", "gr", "gs", "gt", "gu", "gw", "gy",
    "hk", "hm", "hn", "hr", "ht", "hu", "id", "ie", "il", "im", "in", "io", "iq", "ir", "is", "it",
    "je", "jm", "jo", "jp", "ke", "kg", "kh", "ki", "km", "kn", "kp", "kr", "kw", "ky", "kz",
    "la", "lb", "lc", "li", "lk", "lr", "ls", "lt", "lu", "lv", "ly",
    "ma", "mc", "md", "me", "mf", "mg", "mh", "mk", "ml", "mm", "mn", "mo", "mp", "mq", "mr", "ms", "mt", "mu", "mv", "mw", "mx", "my", "mz",
    "na", "nc", "ne", "nf", "ng", "ni", "nl", "no", "np", "nr", "nu", "nz",
    "om", "pa", "pe", "pf", "pg", "ph", "pk", "pl", "pm", "pn", "pr", "ps", "pt", "pw", "py",
    "qa", "re", "ro", "rs", "ru", "rw", "sa", "sb", "sc", "sd", "se", "sg", "sh", "si", "sk", "sl", "sm", "sn", "so", "sr", "ss", "st", "su", "sv", "sx", "sy", "sz",
    "tc", "td", "tf", "tg", "th", "tj", "tk", "tl", "tm", "tn", "to", "tr", "tt", "tv", "tw", "tz",
    "ua", "ug", "uk", "us", "uy", "uz", "va", "vc", "ve", "vg", "vi", "vn", "vu", "wf", "ws", "ye", "yt", "za", "zm", "zw",
    # gTLDs (Generische und neue Domains, insbesondere für IPTV & Webserver)
    "com", "net", "org", "info", "biz", "pro", "name", "xyz", "club", "top", "online", "site",
    "live", "vip", "shop", "one", "cloud", "best", "link", "tech", "space", "store", "fun",
    "host", "website", "today", "run", "rocks", "casa", "uno", "actor", "homes", "cfd", "guru",
    "life", "work", "stream", "solutions", "services", "network", "zone", "world", "mobi", "asia",
    "tel", "cat", "jobs", "travel", "media", "center", "agency", "digital", "expert", "group",
    "support", "systems", "team", "plus", "video", "click", "app", "dev", "page", "wiki", "news",
    "gold", "fit", "tube", "pub", "bar", "direct", "icu", "cyou", "sbs", "lol", "monster",
    "rest", "band", "show", "watch", "global", "express", "company", "city", "community", "cool",
    "events", "exchange", "guide", "international", "land", "limited", "management", "marketing",
    "partners", "photography", "photos", "productions", "properties", "rentals", "repair", "report",
    "reviews", "social", "software", "supplies", "supply", "technology", "tips", "tools", "town",
    "toys", "training", "university", "vacations", "ventures", "viajes", "villas", "vision", "voyage",
    "wales", "dance", "fyi", "bio", "cam", "rip", "soy", "arpa"
}

PORTAL_URL_PATTERN = re.compile(
    r"(?:https?://[^\s<>\"'{}|\\^`]+|"
    r"(?:[a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s<>\"'{}|\\^`]*)?|"
    r"(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/[^\s<>\"'{}|\\^`]*)?)",
    re.IGNORECASE,
)

# Regexes zur zielgerichteten Erkennung echter Portal-Kandidaten
_URL_WITH_SCHEME = re.compile(r"https?://[^\s<>\"'{}|\\^`]+", re.IGNORECASE)
_LABEL_PREFIXED_URL = re.compile(r"(?i)(?:portal|host|url|server)\s*[:=]\s*([^\s<>\"'{}|\\^`]+)")
_BARE_HOST_WITH_PORT = re.compile(r"\b((?:[a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}|(?:\d{1,3}\.){3}\d{1,3}):(\d{1,5})(?:/[^\s<>\"'{}|\\^`]*)?")
_BARE_HOST_WITH_PATH = re.compile(r"\b((?:[a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}|(?:\d{1,3}\.){3}\d{1,3})(/(?:c|stalker_portal|portal\.php|server/load\.php|load\.php)[^\s<>\"'{}|\\^`]*)")
_PORTAL_PREFIXED_HOST = re.compile(r"\b((?:mag|stb|portal|iptv|ott|stream|panel)\.[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)*(?::\d{1,5})?(?:/[^\s<>\"'{}|\\^`]*)?)", re.IGNORECASE)

EXCLUDED_HOST_SUFFIXES = (
    "w3.org", "schema.org", "github.com", "gitlab.com", "google.com", "google.de",
    "microsoft.com", "apple.com", "cloudflare.com", "example.com", "localhost",
    "yahoo.com", "hotmail.com", "outlook.com", "live.com", "gmail.com", "mail.ru",
    "yandex.ru", "yandex.com", "web.de", "gmx.de", "gmx.net", "t-online.de",
    "facebook.com", "twitter.com", "x.com", "instagram.com", "youtube.com",
    "wikipedia.org", "reddit.com", "amazon.com", "netflix.com", "pastebin.com",
    "t.me", "telegram.org", "discord.com", "discord.gg", "mega.nz", "anonfiles.com"
)

EXCLUDED_EXTENSIONS = {
    ".txt", ".json", ".log", ".py", ".md", ".exe", ".dll", ".bak",
    ".csv", ".bat", ".sh", ".zip", ".tar", ".gz", ".png", ".jpg",
    ".jpeg", ".gif", ".pdf", ".doc", ".docx", ".xml", ".yml", ".yaml",
    ".ini", ".cfg", ".conf", ".htm", ".html", ".css", ".js", ".ts",
    ".m3u", ".m3u8", ".mp4", ".mkv", ".avi", ".mp3"
}


def is_valid_portal_hostname(host: Optional[str]) -> bool:
    """
    Validiert streng, ob ein Hostname eine reale Internet-Domain oder IPv4-Adresse darstellt.
    Verwirft Usernamen aus Combos (z. B. 'lucas.pr', 'jester.bermejo'), Dateinamen und Plattformen.
    """
    if not host:
        return False
    h = host.strip().lower().rstrip(".")
    if not h or len(h) > 253:
        return False

    # Ungültige Steuer- oder Trennzeichen
    if any(c in h for c in ("@", " ", "/", "\\", ":", "<", ">", "{", "}", "|", "^", "`", "*", "?", "!", "$", "%")):
        return False

    # Ausschluss bekannter Nicht-Portal-Plattformen / Mailprovider
    for ex in EXCLUDED_HOST_SUFFIXES:
        if h == ex or h.endswith("." + ex):
            return False

    # Prüfe IPv4-Adresse
    parts = h.split(".")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        try:
            nums = [int(p) for p in parts]
            if all(0 <= n <= 255 for n in nums):
                if nums[0] == 0 or nums[0] == 127:
                    return False
                return True
            return False
        except ValueError:
            return False

    # Prüfe Domain-Struktur
    if len(parts) < 2:
        return False

    for p in parts:
        if not p or len(p) > 63 or not re.match(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$", p):
            return False

    # TLD-Validierung gegen offizielle TLDs
    tld = parts[-1]
    if tld not in VALID_TLDS:
        return False

    if "." + tld in EXCLUDED_EXTENSIONS:
        return False

    return True


def extract_portal_urls_from_text(content: str) -> List[str]:
    """
    Extrahiert Stalker-Portal-URLs aus einem Textstring (z. B. aus TXT-Listen, Logs, M3U).
    Filtert Combo-Listen (Email:Pass, User:Pass) und Dateinamen zuverlässig heraus.
    Erkennt http(s)-URLs sowie Host:Port-Angaben, Host/Path-Angaben und IPs,
    validiert Hostnames über is_valid_portal_hostname und normalisiert
    die URLs dedupliziert über normalize_portal_url.
    """
    if not content:
        return []

    found: List[str] = []
    seen = set()

    for line in content.splitlines():
        line_s = line.strip()
        if not line_s or line_s.startswith(("#", "//", "/*")):
            continue

        # 1. Ignoriere Email-Zeilen und Email-Combos ohne explizites HTTP-Schema (z. B. user@domain.com:pass)
        if "@" in line_s and not line_s.startswith(("http://", "https://")):
            continue

        # 2. Ignoriere reine User:Pass-Combos (z. B. 'jester.bermejo:secret', 'babi.morosoli:1234')
        if ":" in line_s and not line_s.startswith(("http://", "https://")):
            parts = line_s.split(":", 1)
            # Wenn nach dem Doppelpunkt kein numerischer Port folgt und kein Portal-Label vorliegt -> Combo!
            if not re.match(r"^\d{1,5}(?:/.*)?$", parts[1].strip()) and not parts[0].lower().startswith(("portal", "host", "url", "server")):
                continue

        candidates: List[str] = []
        working_line = line_s

        # A. Vollständige HTTP(S)-URLs
        for m in _URL_WITH_SCHEME.findall(working_line):
            candidates.append(m)
            working_line = working_line.replace(m, " ")

        # B. Über Labels eingeleitete URLs (z. B. 'Host: iptv.server.com:25461')
        for m in _LABEL_PREFIXED_URL.findall(working_line):
            candidates.append(m)
            working_line = working_line.replace(m, " ")

        # C. Reiner Host mit Port (z. B. 'pars01.com:8080')
        for m in _BARE_HOST_WITH_PORT.finditer(working_line):
            candidates.append(m.group(0))

        # D. Reiner Host mit Stalker-Pfad (z. B. 'portal.server.com/c')
        for m in _BARE_HOST_WITH_PATH.finditer(working_line):
            candidates.append(m.group(0))

        # E. Typischer Portal-Subdomain-Präfix (z. B. 'mag.clubxc.com')
        for m in _PORTAL_PREFIXED_HOST.findall(working_line):
            candidates.append(m)

        for raw_u in candidates:
            clean_u = raw_u.strip().rstrip(".,;:)'\"<>`|")
            if not clean_u:
                continue

            norm = normalize_portal_url(clean_u)
            parsed = urlparse(norm)
            if not is_valid_portal_hostname(parsed.hostname):
                continue
            if parsed.port and not (1 <= parsed.port <= 65535):
                continue

            if norm.lower() not in seen:
                seen.add(norm.lower())
                found.append(norm)

    return found


def extract_portal_urls_from_folder(
    folder_path: str,
    max_file_size: int = 50 * 1024 * 1024,
) -> Tuple[List[str], int]:
    """
    Durchsucht alle .txt-Dateien eines Ordners rekursiv nach Stalker Portal-URLs.
    Gibt (deduplizierte Liste normalisierter URLs, Anzahl durchsuchter .txt-Dateien) zurück.
    """
    if not os.path.exists(folder_path):
        return [], 0

    found_portals: List[str] = []
    seen = set()
    txt_files_count = 0

    for root, _dirs, files in os.walk(folder_path):
        for fname in files:
            if fname.lower().endswith(".txt"):
                txt_files_count += 1
                fpath = os.path.join(root, fname)
                try:
                    if os.path.getsize(fpath) > max_file_size:
                        continue
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    urls = extract_portal_urls_from_text(content)
                    for u in urls:
                        if u.lower() not in seen:
                            seen.add(u.lower())
                            found_portals.append(u)
                except Exception:
                    continue

    return found_portals, txt_files_count


def normalize_portal_url(raw: str) -> str:
    """Normalisiert eine Portal-URL sauber (Protokoll, Leerzeichen, Format)."""
    u = raw.strip()
    if not u:
        return ""
    if not u.startswith(("http://", "https://")):
        u = f"http://{u}"
    parsed = urlparse(u)
    scheme = parsed.scheme.lower() or "http"
    netloc = parsed.netloc.strip()
    path = parsed.path.rstrip("/")
    
    # Wenn Stream-URL (z. B. MPEG-TS oder HLS Stream), auf Basispfad /c zuruecksetzen
    if any(path.lower().endswith(ext) for ext in (".ts", ".m3u8", ".mp4", ".mkv", ".avi")) or "/live/" in path or "/movie/" in path:
        path = "/c"
    elif not path or path == "/":
        path = "/c"
    elif not path.endswith("/c") and not path.endswith(".php"):
        path = f"{path}/c"
    
    # Query oder Fragmente bei reinen Portal-Listen meist nicht erwünscht
    return f"{scheme}://{netloc}{path}"


def load_portal_list(file_path: str) -> List[str]:
    """
    Liest eine Stalker-Portal-Datei (.txt) ein, bereinigt Kommentare und
    gibt eine deduplizierte Liste normalisierter Portal-URLs zurück.
    """
    if not os.path.exists(file_path):
        return []

    portals: List[str] = []
    seen = set()
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("//"):
                    continue
                # Unterstütze URLs oder Hostnames
                norm = normalize_portal_url(line)
                parsed = urlparse(norm)
                if not is_valid_portal_hostname(parsed.hostname):
                    continue
                if parsed.port and not (1 <= parsed.port <= 65535):
                    continue
                if norm and norm.lower() not in seen:
                    seen.add(norm.lower())
                    portals.append(norm)
    except Exception:
        pass
    return portals


def save_reachable_portals_file(file_path: str, urls: List[str]) -> bool:
    """Speichert eine Liste erreichbarer Portal-URLs zeilenweise in eine .txt-Datei."""
    try:
        dir_path = os.path.dirname(os.path.abspath(file_path))
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            for u in urls:
                u_clean = u.strip()
                if u_clean:
                    f.write(f"{u_clean}\n")
        return True
    except Exception:
        return False


def is_stalker_response(r: Optional[requests.Response]) -> bool:
    """
    Prüft eine HTTP-Response rigoros auf definitive Stalker / Ministra Signaturen.
    Verwirft generische Webseiten, PHP-Blogs und fremde REST-APIs (False-Positive Schutz).
    """
    if r is None:
        return False
    text = (r.text[:8192] if r.text else "").lower()
    content_type = r.headers.get("Content-Type", "").lower()
    cookies_names = {c.name.lower() for c in r.cookies}

    # 1. Spezifische JsHttpRequest & Stalker API Container Signaturen
    # JsHttpRequest liefert immer JSON mit Top-Level Key "js" oder /*-secure- Wrapper
    if "/*-secure-" in text or "jshttprequest" in text:
        return True
    if '"js":' in text or '"js" :' in text:
        return True

    # 2. Spezifische Stalker / Ministra JavaScript- und Middleware-Pfade
    if any(k in text for k in (
        "stbapp", "ministra", "stalker portal", "layer_loader",
        "/c/default/", "/c/version", "embed.js", "stb.js",
        "player engine version", "infomir", "stalker stb",
        "tariff_plan_id"
    )):
        return True

    # 3. HTML-Titel spezifisch für STB-Portale (mit beliebigen Leerzeichen im Tag)
    if re.search(r"<title>[^<]*(ministra|stalker|mag\s*25\d|mag\s*32\d)", text, re.IGNORECASE):
        return True

    # 4. Spezifische STB-Cookies
    if any(c in cookies_names for c in ("mac", "stb_lang", "stb_mac", "stb_version")):
        return True

    # 5. Handshake-Parameter / Fehlermeldungen von Stalker (z.B. bei fehlendem/ungültigem MAC)
    # Stalker gibt bei Handshake typischerweise {"token":..., "random":...} oder "authorization failed" zurück
    if ('"token":' in text and '"random":' in text) or "authorization failed" in text or "unhandled request" in text:
        return True

    # 6. PHPSESSID in Kombination mit expliziten Stalker-Identifikatoren
    if "phpsessid" in cookies_names and any(k in text for k in (
        "ministra", "stalker", "/c/default/", "/c/portal", "infomir", "stbapp"
    )):
        return True

    return False


def get_portal_candidate_endpoints(url: str) -> List[str]:
    """Generiert typische Stalker/Ministra-Endpunkte für Handshake-Probes."""
    norm = normalize_portal_url(url)
    parsed = urlparse(norm)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc
    base = f"{scheme}://{netloc}"
    path = parsed.path.rstrip("/")

    candidates: List[str] = []

    if path.endswith(".php"):
        candidates.append(f"{base}{path}")

    clean_sub = re.sub(r"/c$", "", path)
    if clean_sub and clean_sub != "/":
        candidates.append(f"{base}{clean_sub}/c/server/load.php")
        candidates.append(f"{base}{clean_sub}/server/load.php")
        candidates.append(f"{base}{clean_sub}/c/portal.php")
        candidates.append(f"{base}{clean_sub}/portal.php")
        candidates.append(f"{base}{clean_sub}/load.php")

    candidates.append(f"{base}/c/server/load.php")
    candidates.append(f"{base}/server/load.php")
    candidates.append(f"{base}/c/portal.php")
    candidates.append(f"{base}/portal.php")
    candidates.append(f"{base}/load.php")
    candidates.append(f"{base}/stalker_portal/server/load.php")

    seen = set()
    res = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            res.append(c)
    return res[:6]


def check_single_portal(
    url: str,
    timeout: float = DEFAULT_PORTAL_TIMEOUT,
    verify_ssl: bool = False,
    session: Optional[requests.Session] = None,
) -> PortalCheckResult:
    """
    Prüft einen einzelnen Portal-Host rigoros auf echte Stalker/Ministra-Erreichbarkeit,
    Latenz und Endpunkte. Verwirft generische Webseiten und Parking-Seiten (False-Positive Schutz).
    """
    norm_url = normalize_portal_url(url)
    parsed = urlparse(norm_url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    res = PortalCheckResult(
        url=norm_url,
        host=host,
        port=port,
        is_online=False,
    )

    if not host:
        res.error = "Ungültige URL / Kein Host"
        return res

    owns_session = False
    if session is None:
        owns_session = True
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.verify = verify_ssl
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp",
            "Accept": "*/*",
            "Connection": "close",
        })
    else:
        # Session Cookie Isolation zwischen verschiedenen Portalen (STB Guideline Rule 1)
        try:
            session.cookies.clear()
        except Exception:
            pass

    t0 = time.perf_counter()
    connect_timeout = min(2.5, timeout)
    read_timeout = max(1.5, timeout)

    try:
        # 1. Hauptabfrage auf Ziel-URL
        r = session.get(
            norm_url,
            timeout=(connect_timeout, read_timeout),
            allow_redirects=True,
            verify=verify_ssl,
        )
        latency = (time.perf_counter() - t0) * 1000.0
        res.latency_ms = round(latency, 1)
        res.status_code = r.status_code
        res.server = r.headers.get("Server", "").strip()

        is_stalker = is_stalker_response(r)
        detected_ep = norm_url

        # 2. Falls Hauptabfrage nicht eindeutig Stalker ist: Endpunkte mit Handshake-Payload sondieren
        if not is_stalker:
            cand_eps = get_portal_candidate_endpoints(norm_url)
            for cand in cand_eps:
                try:
                    probe_r = session.get(
                        cand,
                        params={"type": "stb", "action": "handshake", "token": "", "JsHttpRequest": "1-xml"},
                        timeout=(1.5, 2.0),
                        verify=verify_ssl,
                        allow_redirects=True,
                    )
                    if is_stalker_response(probe_r):
                        is_stalker = True
                        detected_ep = cand
                        res.status_code = probe_r.status_code
                        break
                    probe_txt = (probe_r.text[:2048] if probe_r.text else "").lower()
                    if any(k in probe_txt for k in ('"js":', '"token":', '"random":', "authorization failed", "/*-secure-")):
                        is_stalker = True
                        detected_ep = cand
                        res.status_code = probe_r.status_code
                        break
                except Exception:
                    pass

        res.stalker_detected = is_stalker
        res.endpoint = detected_ep

        # Strikte Einstufung: Nur verifizierte Stalker-Portale sind online & erreichbar!
        if is_stalker:
            res.is_online = True
            res.error = None
        else:
            res.is_online = False
            res.error = f"Kein Stalker/Ministra Portal (HTTP {res.status_code})"

    except requests.exceptions.ConnectTimeout:
        res.latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        res.is_online = False
        res.stalker_detected = False
        res.error = f"Verbindungs-Timeout (>{connect_timeout}s)"
    except requests.exceptions.ReadTimeout:
        res.latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        res.is_online = False
        res.stalker_detected = False
        res.error = f"Lese-Timeout (>{read_timeout}s)"
    except requests.exceptions.SSLError as ssl_err:
        res.latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        res.is_online = False
        res.stalker_detected = False
        res.status_code = 495  # SSL Certificate Error marker
        res.error = "SSL-Zertifikatsfehler (verify_ssl=False empfohlen)"
    except (socket.gaierror, requests.exceptions.ConnectionError) as ce:
        res.latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        res.is_online = False
        res.stalker_detected = False
        err_msg = str(ce)
        if "getaddrinfo failed" in err_msg or "gaierror" in err_msg:
            res.error = "DNS-Auflösungsfehler (Host nicht gefunden)"
        elif "Connection refused" in err_msg:
            res.error = "Verbindung abgelehnt (Port geschlossen)"
        elif "No route to host" in err_msg:
            res.error = "Keine Route zum Host"
        else:
            res.error = "Verbindungsfehler"
    except Exception as e:
        res.latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        res.is_online = False
        res.stalker_detected = False
        res.error = f"Fehler: {type(e).__name__}"
    finally:
        if owns_session and session:
            try:
                session.close()
            except Exception:
                pass

    return res


class StalkerPortalChecker:
    """
    Multi-threaded Stalker Portal Prüf-Engine.
    Unterstützt Worker-Concurrency, Echtzeit-Fortschritt, Pausieren und Stoppen.
    """

    def __init__(self):
        self._stop_ev = threading.Event()
        self._pause_ev = threading.Event()
        self._pause_ev.set()
        self._is_running = False

        self._lock = threading.Lock()
        self._results: List[PortalCheckResult] = []
        self._reachable_urls: List[str] = []
        self._total = 0
        self._done = 0
        self._online_count = 0
        self._offline_count = 0
        self._start_ts = 0.0
        self._start_perf = 0.0
        self._progress_samples: collections.deque[Tuple[float, int]] = collections.deque(maxlen=50)
        self._smoothed_cps: float = 0.0

        # Callbacks
        self.on_portal_result: Optional[Callable[[PortalCheckResult], None]] = None
        self.on_progress: Optional[Callable[[int, int, int, int, float], None]] = None
        self.on_finished: Optional[Callable[[List[PortalCheckResult], List[str]], None]] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_results(self) -> List[PortalCheckResult]:
        with self._lock:
            return list(self._results)

    def get_reachable_urls(self) -> List[str]:
        with self._lock:
            return list(self._reachable_urls)

    def stop(self):
        """Stoppt die laufende Prüfung sofort."""
        self._stop_ev.set()
        self._pause_ev.set()
        self._is_running = False

    def pause(self):
        """Pausiert die Prüfung."""
        self._pause_ev.clear()

    def resume(self):
        """Setzt die Prüfung fort."""
        self._pause_ev.set()

    def start_check(
        self,
        urls: List[str],
        threads: int = DEFAULT_CHECKER_THREADS,
        timeout: float = DEFAULT_PORTAL_TIMEOUT,
        verify_ssl: bool = False,
        delay_s: float = 0.0,
    ):
        """Startet die asynchrone Multi-Threaded Portalprüfung im Hintergrund."""
        if self._is_running:
            self.stop()
            time.sleep(0.1)

        self._stop_ev.clear()
        self._pause_ev.set()
        self._is_running = True

        with self._lock:
            self._results.clear()
            self._reachable_urls.clear()
            self._total = len(urls)
            self._done = 0
            self._online_count = 0
            self._offline_count = 0
            self._start_ts = time.time()
            self._start_perf = time.perf_counter()
            self._progress_samples.clear()
            self._smoothed_cps = 0.0

        work_queue: queue.Queue[str] = queue.Queue()
        for u in urls:
            work_queue.put(u)

        num_workers = max(1, min(threads, len(urls) or 1))

        def _coordinator():
            def _worker():
                # Eigene Keep-Alive Session pro Thread spart TLS/Socket Re-Handshakes
                s = requests.Session()
                adapter = HTTPAdapter(pool_connections=2, pool_maxsize=2, max_retries=0)
                s.mount("http://", adapter)
                s.mount("https://", adapter)
                s.verify = verify_ssl
                s.headers.update({
                    "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp",
                    "Accept": "*/*",
                    "Connection": "keep-alive",
                })

                try:
                    while not self._stop_ev.is_set():
                        # Pausen-Unterstützung
                        while not self._pause_ev.is_set():
                            if self._stop_ev.is_set():
                                return
                            time.sleep(0.1)

                        try:
                            portal_url = work_queue.get(timeout=0.2)
                        except queue.Empty:
                            break

                        try:
                            if self._stop_ev.is_set():
                                break

                            if delay_s > 0:
                                time.sleep(delay_s)

                            res = check_single_portal(
                                portal_url,
                                timeout=timeout,
                                verify_ssl=verify_ssl,
                                session=s,
                            )

                            with self._lock:
                                self._results.append(res)
                                self._done += 1
                                if res.is_online and res.stalker_detected:
                                    self._online_count += 1
                                    if res.url not in self._reachable_urls:
                                        self._reachable_urls.append(res.url)
                                else:
                                    self._offline_count += 1

                                cur_done = self._done
                                cur_online = self._online_count
                                cur_offline = self._offline_count

                                # Windowed & EMA smoothed CPS
                                now_perf = time.perf_counter()
                                self._progress_samples.append((now_perf, cur_done))
                                cutoff = now_perf - 4.0
                                while len(self._progress_samples) > 2 and self._progress_samples[0][0] < cutoff:
                                    self._progress_samples.popleft()

                                oldest_t, oldest_d = self._progress_samples[0]
                                dt = now_perf - oldest_t
                                dn = cur_done - oldest_d
                                if dt >= 0.5:
                                    instant_cps = max(0.0, dn / dt)
                                elif cur_done > 0:
                                    instant_cps = cur_done / max(0.001, now_perf - (self._start_perf or now_perf))
                                else:
                                    instant_cps = 0.0

                                if self._smoothed_cps <= 0.0:
                                    self._smoothed_cps = instant_cps
                                else:
                                    self._smoothed_cps = 0.25 * instant_cps + 0.75 * self._smoothed_cps
                                cps = round(max(0.0, self._smoothed_cps), 1)

                            if self.on_portal_result:
                                try:
                                    self.on_portal_result(res)
                                except Exception:
                                    pass

                            if self.on_progress:
                                try:
                                    self.on_progress(cur_done, self._total, cur_online, cur_offline, cps)
                                except Exception:
                                    pass

                        finally:
                            work_queue.task_done()
                finally:
                    try:
                        s.close()
                    except Exception:
                        pass

            worker_threads: List[threading.Thread] = []
            for _ in range(num_workers):
                t = threading.Thread(target=_worker, daemon=True)
                t.start()
                worker_threads.append(t)

            for t in worker_threads:
                t.join()

            self._is_running = False

            with self._lock:
                final_results = list(self._results)
                final_reachables = list(self._reachable_urls)

            if self.on_finished and not self._stop_ev.is_set():
                try:
                    self.on_finished(final_results, final_reachables)
                except Exception:
                    pass

        t_coord = threading.Thread(target=_coordinator, daemon=True)
        t_coord.start()
