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


class StbClient(_BaseStbClient):
    """
    Erweiterter Stalker/Ministra Client mit automatischem Inspector-Logging.
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
    ):
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
        )
        _attach_inspector_hook(self.session, enable=enable_inspector)


def check_mac_account(
    portal_url: str,
    mac: str,
    model: str = "MAG 250",
    device_id: Optional[str] = None,
    device_id2: Optional[str] = None,
    serial_number: Optional[str] = None,
    signature: Optional[str] = None,
    timeout: int = 8,
    normalized_load_url: Optional[str] = None,
    session: Optional[Any] = None,
) -> Dict[str, Any]:
    """Prüft einen einzelnen MAC-Account schnell im Hintergrund (ohne Inspector-Spam)."""
    from stb_client import check_mac_account as _base_check
    return _base_check(
        portal_url=portal_url,
        mac=mac,
        model=model,
        device_id=device_id,
        device_id2=device_id2,
        serial_number=serial_number,
        signature=signature,
        timeout=timeout,
        normalized_load_url=normalized_load_url,
        session=session,
    )
