"""
Xtream Codes API Client für STB Pro Qt6.
Mit automatischer HTTP-Telemetrie für den Protokoll-Inspector sowie Serien-API-Unterstützung.
"""
import os
import sys
from typing import Any, Dict, List, Optional

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PARENT_DIR = os.path.dirname(_APP_DIR)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.append(_PARENT_DIR)

from xtream_client import XtreamClient as _BaseXtreamClient  # noqa: E402
from clients.stb_client import _attach_inspector_hook  # noqa: E402


class XtreamClient(_BaseXtreamClient):
    def __init__(
        self,
        server_url: str,
        username: str,
        password: str,
        output_format: str = "ts",
        timeout: int = 8,
        user_agent: Optional[str] = None,
        enable_inspector: bool = True,
        verify_ssl: bool = False,
    ):
        super().__init__(
            server_url=server_url,
            username=username,
            password=password,
            output_format=output_format,
            timeout=timeout,
            user_agent=user_agent,
        )
        self.session.verify = verify_ssl
        self.series_categories: List[Dict[str, Any]] = []
        _attach_inspector_hook(self.session, enable=enable_inspector)

    def get_series_categories(self) -> List[Dict[str, Any]]:
        url = self._api_url("get_series_categories")
        try:
            resp = self.session.get(url, timeout=self.req_timeout)
            data = resp.json()
            if isinstance(data, list):
                self.series_categories = [
                    {"id": str(c.get("category_id")), "title": c.get("category_name")}
                    for c in data
                ]
                return self.series_categories
        except Exception:
            pass
        self.series_categories = []
        return self.series_categories

    def get_series(self, category_id: str = "*", page: int = 1) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if category_id and category_id != "*":
            params["category_id"] = category_id
        url = self._api_url("get_series", extra_params=params)
        try:
            resp = self.session.get(url, timeout=self.req_timeout)
            data = resp.json()
            if isinstance(data, list):
                out = []
                for s in data:
                    item = dict(s)
                    sid = str(s.get("series_id") or s.get("id") or "")
                    item["id"] = sid
                    item["series_id"] = sid
                    item["name"] = s.get("name") or s.get("title") or "Serie"
                    item["year"] = str(s.get("releaseDate") or s.get("year") or "")[:4]
                    item["rating_imdb"] = str(s.get("rating") or s.get("rating_5based") or "")
                    item["cover"] = s.get("cover") or ""
                    item["description"] = s.get("plot") or ""
                    out.append(item)
                return out
        except Exception:
            pass
        return []

    def get_series_info(self, series_id: str) -> Dict[str, List[Dict[str, Any]]]:
        url = self._api_url("get_series_info", extra_params={"series_id": str(series_id)})
        try:
            resp = self.session.get(url, timeout=self.req_timeout)
            data = resp.json()
            if isinstance(data, dict):
                raw_eps = data.get("episodes", {})
                seasons: Dict[str, List[Dict[str, Any]]] = {}
                if isinstance(raw_eps, dict):
                    for s_key, ep_list in raw_eps.items():
                        if isinstance(ep_list, list):
                            norm_list = []
                            for ep in ep_list:
                                if isinstance(ep, dict):
                                    ep_copy = dict(ep)
                                    ep_id = str(ep.get("id") or "")
                                    ext = str(ep.get("container_extension") or "mp4")
                                    ep_copy["cmd"] = self.create_link(ep_id, media_type="series", extension=ext)
                                    norm_list.append(ep_copy)
                            seasons[str(s_key)] = norm_list
                elif isinstance(raw_eps, list):
                    for idx, ep_list in enumerate(raw_eps, start=1):
                        if isinstance(ep_list, list):
                            norm_list = []
                            for ep in ep_list:
                                if isinstance(ep, dict):
                                    ep_copy = dict(ep)
                                    ep_id = str(ep.get("id") or "")
                                    ext = str(ep.get("container_extension") or "mp4")
                                    ep_copy["cmd"] = self.create_link(ep_id, media_type="series", extension=ext)
                                    norm_list.append(ep_copy)
                            seasons[str(idx)] = norm_list
                return seasons
        except Exception:
            pass
        return {}
