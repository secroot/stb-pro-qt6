"""
Stalker / Ministra STB Client für STB Pro Qt6.
Erweitert den bewährten StbClient um Live-HTTP-Telemetrie für den interaktiven Protokoll-Inspector
(inklusive Request-Historie, Header-Capturing und cURL-Export).
"""
import os
import sys
from typing import Optional, Dict, Any

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
        for att in range(2):
            try:
                res_ord = client._request(
                    "get_ordered_list",
                    req_type="itv",
                    extra_params={"genre": genre_param, "sortby": sortby_param, "p": "1"},
                    timeout_override=ch_timeout,
                )
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

    except PermissionError as pe:
        res["status"] = "Ungültig / Nicht autorisiert"
        res["error"] = str(pe)
    except RateLimitError as re_err:
        res["status"] = "Rate Limited (429/WAF)"
        res["error"] = str(re_err)
        res["rate_limited"] = True
    except ConnectionError as ce:
        res["status"] = "Verbindungsfehler"
        res["error"] = str(ce)
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
