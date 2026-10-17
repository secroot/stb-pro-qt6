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
from typing import Any, Callable, Dict, List, Optional
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
        if self.is_online:
            if self.stalker_detected:
                return f"🟢 Stalker OK ({self.status_code})"
            return f"🟢 Online ({self.status_code})"
        if self.error:
            if "Timeout" in self.error or "timed out" in self.error.lower():
                return "⏳ Timeout"
            if "DNS" in self.error or "gaierror" in self.error.lower():
                return "🔴 DNS-Fehler"
            if "Connection refused" in self.error or "Verbindung abgelehnt" in self.error:
                return "🔴 Refused"
        return "🔴 Offline"


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
    if not path or path == "/":
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


def check_single_portal(
    url: str,
    timeout: float = DEFAULT_PORTAL_TIMEOUT,
    verify_ssl: bool = False,
    session: Optional[requests.Session] = None,
) -> PortalCheckResult:
    """
    Prüft einen einzelnen Portal-Host schnell auf TCP/HTTP-Erreichbarkeit,
    Latenz und Stalker/Ministra-Endpunkte.
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

        # HTTP Status-Codes im Bereich 200..599 bedeuten: Host antwortet auf TCP/HTTP -> ONLINE
        # (Selbst 401/403/500 bedeuten, dass der Stalker-Server aktiv läuft und erreichbar ist)
        res.is_online = True

        # Stalker / Ministra Prüfung
        text_snippet = (r.text[:2048] if r.text else "").lower()
        content_type = r.headers.get("Content-Type", "").lower()
        cookies_names = [c.name.lower() for c in r.cookies]

        is_stalker = False
        detected_ep = norm_url

        if any(k in text_snippet for k in ("ministra", "stalker", "infomir", "mag", "jshttprequest", "stb")):
            is_stalker = True
        elif any(c in cookies_names for c in ("phpsessid", "mac", "stb_lang")):
            is_stalker = True
        elif "json" in content_type and ("token" in text_snippet or "js" in text_snippet):
            is_stalker = True

        # Schneller Handshake-Check, falls 200/401/403
        if not is_stalker and r.status_code in (200, 301, 302, 401, 403):
            # Prüfe ob Basis-Endpoint server/load.php oder portal.php antwortet
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            cand_eps = [
                f"{norm_url.rstrip('/')}/../server/load.php",
                f"{base_url}/server/load.php",
                f"{base_url}/portal.php",
            ]
            for cand in cand_eps:
                try:
                    probe_r = session.get(
                        cand,
                        params={"type": "stb", "action": "handshake", "token": "", "JsHttpRequest": "1-xml"},
                        timeout=(1.5, 2.0),
                        verify=verify_ssl,
                    )
                    probe_txt = (probe_r.text[:1024] if probe_r.text else "").lower()
                    if "js" in probe_txt or "token" in probe_txt or probe_r.status_code in (200, 401, 403):
                        is_stalker = True
                        detected_ep = cand
                        break
                except Exception:
                    pass

        res.stalker_detected = is_stalker
        res.endpoint = detected_ep

    except requests.exceptions.ConnectTimeout:
        res.latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        res.error = f"Verbindungs-Timeout (>{connect_timeout}s)"
    except requests.exceptions.ReadTimeout:
        res.latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        res.error = f"Lese-Timeout (>{read_timeout}s)"
    except requests.exceptions.SSLError as ssl_err:
        # SSL-Zertifikatsfehler bedeutet: Host existiert und ist erreichbar!
        res.latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        res.is_online = True
        res.status_code = 495  # SSL Certificate Error marker
        res.error = "SSL-Zertifikatsfehler (verify_ssl=False empfohlen)"
    except (socket.gaierror, requests.exceptions.ConnectionError) as ce:
        res.latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
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

                            res = check_single_portal(
                                portal_url,
                                timeout=timeout,
                                verify_ssl=verify_ssl,
                                session=s,
                            )

                            with self._lock:
                                self._results.append(res)
                                self._done += 1
                                if res.is_online:
                                    self._online_count += 1
                                    if res.url not in self._reachable_urls:
                                        self._reachable_urls.append(res.url)
                                else:
                                    self._offline_count += 1

                                cur_done = self._done
                                cur_online = self._online_count
                                cur_offline = self._offline_count

                            # Berechne CPS (Checks/sec)
                            elapsed = max(0.001, time.time() - self._start_ts)
                            cps = cur_done / elapsed

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
