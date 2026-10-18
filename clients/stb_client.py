"""
Stalker / Ministra STB Client für STB Pro Qt6.
Erweitert den bewährten StbClient um Live-HTTP-Telemetrie für den interaktiven Protokoll-Inspector
(inklusive Request-Historie, Header-Capturing und cURL-Export).
"""
import os
import sys
import threading
from typing import Optional, Dict, Any, List

# Cache für Portal-Kategorien / Genres während MAC-Scans (Portal-URL -> Liste von Genres)
_SCAN_GENRES_CACHE: Dict[str, List[Any]] = {}
_SCAN_GENRES_LOCK = threading.Lock()

# Füge Parent-Verzeichnis für den Basis-StbClient hinzu, sodass jegliche Protokoll-Updates sofort greifen
_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PARENT_DIR = os.path.dirname(_APP_DIR)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.append(_PARENT_DIR)

from stb_client import (  # noqa: E402
    StbClient as _BaseStbClient,
    STB_PRESETS,
    RateLimitError,
)
from core.models import HttpLogEntry  # noqa: E402
from core.signals import event_bus  # noqa: E402


def _attach_inspector_hook(session, enable: bool = True):
    if not enable:
        return

    def _on_response(resp, *args, **kwargs):
        try:
            req = resp.request
            elapsed_ms = int(resp.elapsed.total_seconds() * 1000) if resp.elapsed else 0
            headers = {str(k): str(v) for k, v in (req.headers or {}).items()}
            body_preview = ""
            content_type = resp.headers.get("Content-Type", "").lower()
            # Keine Video-Binärdaten in den Text-Inspector loggen
            if not any(m in content_type for m in ("video/", "audio/", "octet-stream", "mp2t")):
                try:
                    body_preview = resp.text[:6000]
                except Exception:
                    body_preview = ""
            params_str = str(req.body or "") if req.method == "POST" else ""
            entry = HttpLogEntry.create(
                method=req.method or "GET",
                url=req.url or "",
                status_code=resp.status_code,
                elapsed_ms=elapsed_ms,
                headers=headers,
                params=params_str,
                body=body_preview,
            )
            event_bus.http_Exchange_logged.emit(entry)
        except Exception:
            pass

    session.hooks.setdefault("response", []).append(_on_response)


import datetime as _dt
import re
import threading
import time

_last_inspector_sample_ts = 0.0
_inspector_sample_counter = 0
_inspector_sample_lock = threading.Lock()


def emit_scanner_connection_error_log(
    portal_url: str,
    mac: str,
    error_msg: str,
    endpoint: Optional[str] = None,
    status_code: int = 0,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[str] = None,
    elapsed_ms: int = 0,
    sample_interval: float = 1.0,
    sample_frequency: int = 5,
):
    """
    Sporadisches / gesampeltes Logging von Verbindungs- und Timeout-Fehlern während des MAC-Scannens
    in den interaktiven HTTP-Inspector.
    Verhindert Inspector-Überlastung bei Massen-Scans und zeigt Request-Header, Parameter und Response/Fehler an.
    """
    global _last_inspector_sample_ts, _inspector_sample_counter
    now = time.time()
    with _inspector_sample_lock:
        _inspector_sample_counter += 1
        cnt = _inspector_sample_counter
        time_elapsed = now - _last_inspector_sample_ts
        if time_elapsed < 0.25:
            return
        if (cnt % sample_frequency != 0) and (time_elapsed < sample_interval):
            return
        _last_inspector_sample_ts = now

    target_url = endpoint or f"{portal_url.rstrip('/')}/c/server/load.php"
    req_headers = dict(headers or {
        "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Cookie": f"mac={mac}; stb_lang=en; timezone=Europe/Berlin",
    })
    req_params = params or f"type=stb&action=handshake&mac={mac}&token=&JsHttpRequest=1-xml"

    code = status_code
    if not code:
        code_match = re.search(r"\b(50[0-4]|429|403|404|401)\b", error_msg)
        if code_match:
            try:
                code = int(code_match.group(1))
            except Exception:
                code = 0

    response_preview = (
        f"--- [MAC SCANNER VERBINDUNGSFEHLER] ---\n"
        f"Zeitstempel: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Portal: {portal_url}\n"
        f"MAC-Adresse: {mac}\n"
        f"Ziel-Endpoint: {target_url}\n"
        f"Status: {code if code else '0 (Timeout / Verbindungsfehler)'}\n"
        f"Fehler-Details:\n{error_msg}\n"
        f"----------------------------------------"
    )

    entry = HttpLogEntry.create(
        method="GET",
        url=target_url,
        status_code=code,
        elapsed_ms=elapsed_ms or 2500,
        headers=req_headers,
        params=req_params,
        body=response_preview,
    )
    try:
        event_bus.http_Exchange_logged.emit(entry)
    except Exception:
        pass


_last_scanner_http_ts = 0.0
_scanner_http_counter = 0
_scanner_http_lock = threading.Lock()


def emit_scanner_http_log(
    portal_url: str,
    mac: str,
    res: Dict[str, Any],
    endpoint: Optional[str] = None,
    elapsed_ms: int = 0,
    force: bool = False,
):
    """
    Kontinuierliches & gesampeltes Logging von MAC-Scanner Requests/Responses in den Inspector.
    - HOT Hits werden IMMER sofort und ungedrosselt geloggt.
    - Fehler & Timeouts werden mit ca. 2 Samples/s geloggt.
    - Normale Scan-Prüfungen werden gleichmäßig (~1 Sample alle 1.2s) geloggt,
      damit der Inspector während des gesamten Scans aktiv bleibt und nicht abbricht.
    """
    global _last_scanner_http_ts, _scanner_http_counter
    tag = res.get("tag", "")
    ch_cnt = int(res.get("channels") or 0)
    is_hot = (tag == "hot" or (res.get("valid") and ch_cnt > 0))
    is_err = (
        not res.get("valid")
        and not is_hot
        and any(k in str(res.get("status") or "") for k in ("Fehler", "Timeout", "503", "502", "429"))
    )

    now = time.time()
    if not is_hot and not force:
        with _scanner_http_lock:
            _scanner_http_counter += 1
            time_since = now - _last_scanner_http_ts
            min_interval = 0.5 if is_err else 1.2
            if time_since < min_interval:
                return
            _last_scanner_http_ts = now

    target_url = endpoint or res.get("load_url") or f"{portal_url.rstrip('/')}/c/server/load.php"
    req_headers = {
        "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Cookie": f"mac={mac}; stb_lang=en; timezone=Europe/Berlin",
    }
    req_params = f"type=stb&action=handshake&mac={mac}&token=&JsHttpRequest=1-xml"

    if is_hot or res.get("valid"):
        code = 200
    elif is_err:
        code = 504 if "timeout" in str(res.get("status") or "").lower() else 503
    elif "401" in str(res.get("status") or "") or "Nicht autorisiert" in str(res.get("status") or ""):
        code = 401
    else:
        code = 200

    now_str = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if is_hot:
        preview = (
            f"--- [🔥 HOT HIT] ---\n"
            f"Zeitstempel: {now_str}\n"
            f"Portal: {portal_url}\n"
            f"MAC-Adresse: {mac}\n"
            f"Status: {res.get('status', 'Aktiv')}\n"
            f"Ablaufdatum: {res.get('expire', '-')}\n"
            f"Kanäle: {ch_cnt}\n"
            f"Token: {res.get('token', '-')}\n"
            f"Endpoint: {target_url}\n"
        )
    elif is_err:
        preview = (
            f"--- [⚠ SCAN FEHLER / TIMEOUT] ---\n"
            f"Zeitstempel: {now_str}\n"
            f"Portal: {portal_url}\n"
            f"MAC-Adresse: {mac}\n"
            f"Status: {res.get('status', 'Verbindungsfehler')}\n"
            f"Endpoint: {target_url}\n"
        )
    else:
        preview = (
            f"--- [SCAN PROBE] ---\n"
            f"Zeitstempel: {now_str}\n"
            f"Portal: {portal_url}\n"
            f"MAC-Adresse: {mac}\n"
            f"Status: {res.get('status', 'Ungültig')}\n"
            f"Ablaufdatum: {res.get('expire', '-')}\n"
            f"Kanäle: {ch_cnt}\n"
            f"Endpoint: {target_url}\n"
        )

    entry = HttpLogEntry.create(
        method="GET",
        url=target_url,
        status_code=code,
        elapsed_ms=elapsed_ms or 120,
        headers=req_headers,
        params=req_params,
        body=preview,
    )
    try:
        event_bus.http_Exchange_logged.emit(entry)
    except Exception:
        pass


try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass


class StbClient(_BaseStbClient):
    """
    Erweiterter Stalker/Ministra Client mit automatischem Inspector-Logging
    und konfigurierbarer SSL-Zertifikatsprüfung.
    """
    def __init__(
        self,
        portal_url: str,
        mac: str,
        model: str = "MAG 250",
        serial_number: Optional[str] = None,
        device_id: Optional[str] = None,
        device_id2: Optional[str] = None,
        signature: Optional[str] = None,
        user_agent: Optional[str] = None,
        timeout: int = 8,
        normalized_load_url: Optional[str] = None,
        enable_inspector: bool = True,
        verify_ssl: bool = False,
        session: Optional[Any] = None,
        connect_timeout: Optional[float] = None,
        read_timeout: Optional[float] = None,
        device_id_mode: Optional[str] = None,
    ):
        if device_id_mode == "random" and not any((device_id, device_id2, signature, serial_number)):
            rand_ids = _BaseStbClient.generate_random_device_ids()
            serial_number = rand_ids["sn"]
            device_id = rand_ids["device_id"]
            device_id2 = rand_ids["device_id2"]
            signature = rand_ids["signature"]

        super().__init__(
            portal_url=portal_url,
            mac=mac,
            model=model,
            serial_number=serial_number,
            device_id=device_id,
            device_id2=device_id2,
            signature=signature,
            user_agent=user_agent,
            timeout=timeout,
            normalized_load_url=normalized_load_url,
            session=session,
        )
        self.device_id_mode = device_id_mode or "deterministic"
        self.session.verify = verify_ssl
        if connect_timeout is not None and read_timeout is not None:
            self.req_timeout = (float(connect_timeout), float(read_timeout))
        elif connect_timeout is not None:
            self.req_timeout = (float(connect_timeout), self.req_timeout[1])
        elif read_timeout is not None:
            self.req_timeout = (self.req_timeout[0], float(read_timeout))
        _attach_inspector_hook(self.session, enable=enable_inspector)


def check_mac_account(
    portal_url: str,
    mac: str,
    model: str = "MAG 250",
    device_id: Optional[str] = None,
    device_id2: Optional[str] = None,
    serial_number: Optional[str] = None,
    signature: Optional[str] = None,
    timeout: float = 8.0,
    normalized_load_url: Optional[str] = None,
    session: Optional[Any] = None,
    verify_ssl: bool = False,
    genre_param: str = "*",
    sortby_param: str = "number",
    fallback_get_all: bool = True,
    device_id_mode: Optional[str] = None,
    enable_error_log: bool = False,
    portal_genres_cache: Optional[Dict[str, List[Any]]] = None,
    fetch_genres: bool = True,
) -> Dict[str, Any]:
    """Prüft einen einzelnen MAC-Account schnell im Hintergrund mit voller Boost-Konfigurierbarkeit."""
    import time
    import datetime as _dt
    import socket
    import requests

    res = {
        "mac": StbClient.format_mac(mac),
        "status": "Fehlgeschlagen",
        "valid": False,
        "token": None,
        "blocked": None,
        "expire": None,
        "channels": 0,
        "tags": [],
        "error": None,
        "load_url": normalized_load_url,
    }
    if session is not None:
        try:
            session.cookies.clear()
            session.verify = verify_ssl
        except Exception:
            pass

    client = None
    try:
        client = StbClient(
            portal_url=portal_url,
            mac=mac,
            model=model,
            device_id=device_id,
            device_id2=device_id2,
            serial_number=serial_number,
            signature=signature,
            timeout=int(timeout),
            normalized_load_url=normalized_load_url,
            session=session,
            verify_ssl=verify_ssl,
            enable_inspector=False,
            device_id_mode=device_id_mode,
        )

        client.handshake()
        res["token"] = client.token
        res["load_url"] = client.normalized_load_url
        profile = client.get_profile()
        res["blocked"] = profile.get("blocked", "0")
        res["expire"] = profile.get("expire_billing_date", "Unbekannt")
        res["max_streams"] = profile.get("playback_limit")
        res["tariff"] = profile.get("tariff_plan_id")

        if str(res["blocked"]) == "0":
            res["status"] = "Aktiv"
            res["valid"] = True
        else:
            res["status"] = "Blockiert"
            res["valid"] = False

        # Viele Portale liefern das echte Ablaufdatum nur in account_info/get_main_info
        try:
            ai = client.get_account_info()
            if ai.get("expire") and str(ai.get("expire")).strip() not in ("", "Unbekannt", "-", "0000-00-00 00:00:00"):
                res["expire"] = ai["expire"]
        except Exception:
            pass

        # Schnelle Kanalanzahl-Ermittlung via paginiertem Endpoint get_ordered_list
        ch_timeout = (min(3.0, float(timeout)), min(6.0, float(timeout)))
        last_channel_response = None
        for att in range(2):
            try:
                res_ord = client._request(
                    "get_ordered_list",
                    req_type="itv",
                    extra_params={"genre": genre_param, "sortby": sortby_param, "p": "1"},
                    timeout_override=ch_timeout,
                )
                last_channel_response = res_ord
                if isinstance(res_ord, dict) and res_ord.get("total_items") is not None:
                    res["channels"] = int(res_ord["total_items"])
                elif isinstance(res_ord, dict) and "data" in res_ord and isinstance(res_ord["data"], (list, dict)):
                    res["channels"] = int(res_ord.get("total_items") or len(res_ord["data"]))
                elif isinstance(res_ord, list):
                    res["channels"] = len(res_ord)

                if res.get("channels", 0) > 0:
                    break

                # Fallback: get_all_channels nur falls get_ordered_list 0 liefert und Fallback aktiv ist
                if fallback_get_all:
                    res_ch = client._request("get_all_channels", req_type="itv", timeout_override=ch_timeout)
                    last_channel_response = res_ch
                    if isinstance(res_ch, dict) and res_ch.get("total_items") is not None:
                        res["channels"] = int(res_ch["total_items"])
                    elif isinstance(res_ch, dict) and "data" in res_ch:
                        res["channels"] = len(res_ch["data"])
                    elif isinstance(res_ch, list):
                        res["channels"] = len(res_ch)

                if res.get("channels", 0) > 0:
                    break
            except (ConnectionError, requests.exceptions.RequestException, socket.error) as ce:
                if att == 0:
                    time.sleep(0.15)
                    continue
                res["channel_error"] = str(ce)
                if enable_error_log:
                    emit_scanner_connection_error_log(
                        portal_url=portal_url,
                        mac=mac,
                        error_msg=f"Kanalabfrage fehlgeschlagen: {ce}",
                        endpoint=res.get("load_url"),
                    )
            except Exception:
                pass

        # Timestamp Normalization für Unix-Epochen
        raw_exp = str(res.get("expire") or "").strip()
        if raw_exp.isdigit() and len(raw_exp) in (10, 13):
            try:
                ts = int(raw_exp[:10])
                res["expire"] = _dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

        # Bouquet / Kategorie Tag-Erkennung (nur einmalig pro Portal abfragen & cachen)
        if fetch_genres and res.get("valid") and res.get("channels", 0) > 0:
            target_cache = portal_genres_cache if portal_genres_cache is not None else _SCAN_GENRES_CACHE
            norm_p_key = portal_url.strip().rstrip("/")
            with _SCAN_GENRES_LOCK:
                cached_genres = target_cache.get(norm_p_key)
            if cached_genres is None:
                with _SCAN_GENRES_LOCK:
                    cached_genres = target_cache.get(norm_p_key)
                    if cached_genres is None:
                        # Reserviere Key, um doppelte Abfragen durch parallele Worker zu verhindern
                        target_cache[norm_p_key] = []
                        need_query = True
                    else:
                        need_query = False
                if need_query:
                    try:
                        fetched = client.get_genres()
                        if not fetched:
                            # Fallback: Genre- und Sendernamen aus den ersten Kanälen extrahieren
                            curr_ord = last_channel_response
                            if isinstance(curr_ord, dict) and "data" in curr_ord and isinstance(curr_ord["data"], list):
                                fetched = []
                                for ch in curr_ord["data"][:50]:
                                    if isinstance(ch, dict):
                                        for field in ("group_title", "category_name", "genre_name", "name", "alias"):
                                            v = ch.get(field)
                                            if v and isinstance(v, str):
                                                fetched.append(v)
                                        if ch.get("censored") in (1, "1", True):
                                            fetched.append({"censored": 1})
                        with _SCAN_GENRES_LOCK:
                            target_cache[norm_p_key] = fetched or []
                    except Exception:
                        with _SCAN_GENRES_LOCK:
                            target_cache[norm_p_key] = []

            with _SCAN_GENRES_LOCK:
                genres_for_tags = list(target_cache.get(norm_p_key, []))

            from core.category_parser import detect_category_tags
            res["tags"] = detect_category_tags(genres_for_tags)

    except PermissionError as pe:
        res["status"] = "Ungültig / Nicht autorisiert"
        res["error"] = str(pe)
    except RateLimitError as re_err:
        res["status"] = "Rate Limited (429/WAF)"
        res["error"] = str(re_err)
        res["rate_limited"] = True
    except (ConnectionError, requests.exceptions.RequestException, socket.error) as ce:
        res["status"] = "Verbindungsfehler"
        res["error"] = str(ce)
        if enable_error_log:
            emit_scanner_connection_error_log(
                portal_url=portal_url,
                mac=mac,
                error_msg=str(ce),
                endpoint=res.get("load_url"),
                status_code=504 if ("timeout" in str(ce).lower() or "timed out" in str(ce).lower()) else 0,
            )
    except Exception as e:
        res["status"] = "Fehlgeschlagen"
        res["error"] = str(e)
    finally:
        if session is None and client and getattr(client, "session", None):
            try:
                client.session.close()
            except Exception:
                pass

    return res
