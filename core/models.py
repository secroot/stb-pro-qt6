"""
Datenmodelle (Dataclasses) für STB Pro Qt6.
Strikt typisiert und unabhängig von UI-Komponenten.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Set, Any
import datetime
import time


def quality_from_dimensions(width: int, height: int) -> str:
    """Ermittelt den Qualitäts-Tag (UHD/FHD/HD/SD) exakt anhand von Pixel-Dimensionen."""
    try:
        w = int(width or 0)
        h = int(height or 0)
    except (ValueError, TypeError):
        return ""
    if w >= 3800 or h >= 2100:
        return "UHD"
    if h >= 1000 or w >= 1800:
        return "FHD"
    if h >= 650 or w >= 1200:
        return "HD"
    if w > 0 or h > 0:
        return "SD"
    return ""


def detect_quality_tag(name: str, raw: Optional[Dict[str, Any]] = None) -> str:
    """Erkennt den Qualitäts-Tag AUSSCHLIESSLICH anhand von echten Dimensionsdaten in den Metadaten.
    Kein Raten oder Auslesen aus dem Sendernamen!
    """
    if raw and isinstance(raw, dict):
        try:
            rw = int(raw.get("width") or raw.get("video_width") or 0)
            rh = int(raw.get("height") or raw.get("video_height") or 0)
            if rw > 0 or rh > 0:
                q = quality_from_dimensions(rw, rh)
                if q:
                    return q
        except (ValueError, TypeError):
            pass

        res_str = str(raw.get("resolution") or raw.get("res") or "").strip()
        if "X" in res_str.upper():
            parts = res_str.upper().split("X")
            if len(parts) == 2:
                try:
                    rw, rh = int(parts[0].strip()), int(parts[1].strip())
                    q = quality_from_dimensions(rw, rh)
                    if q:
                        return q
                except (ValueError, TypeError):
                    pass

    return ""


@dataclass
class Channel:
    id: str
    number: str
    name: str
    cmd: str
    category: str = "Allgemein"
    genre_id: str = "*"
    logo: str = ""
    is_fav: bool = False
    is_playing: bool = False
    is_dead: bool = False
    quality_tag: str = ""          # z.B. "UHD", "FHD", "HD", "SD"
    latency_ms: int = -1
    bitrate_kbps: float = 0.0
    epg_now_title: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.quality_tag:
            self.quality_tag = detect_quality_tag(self.name, self.raw_data)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Channel):
            return str(self.id) == str(other.id)
        return False

    @property
    def tv_genre_id(self) -> str:
        return str(self.genre_id or self.raw_data.get("tv_genre_id") or self.raw_data.get("category_id") or "*")

    @tv_genre_id.setter
    def tv_genre_id(self, val: str):
        self.genre_id = str(val)

    @property
    def fav(self) -> bool:
        return bool(self.is_fav or str(self.raw_data.get("fav", "0")) == "1")

    @fav.setter
    def fav(self, val: bool):
        self.is_fav = bool(val)

    @property
    def is_hls(self) -> bool:
        return ".m3u8" in str(self.cmd or "").lower()

    @property
    def has_archive(self) -> bool:
        r = self.raw_data or {}
        return (
            str(r.get("archive", "0")) == "1"
            or str(r.get("enable_tv_archive", "0")) == "1"
            or str(r.get("tv_archive", "0")) == "1"
        )

    @property
    def enable_tv_archive(self) -> bool:
        return self.has_archive

    @property
    def flags_summary(self) -> str:
        r = self.raw_data or {}
        flags = []
        if self.quality_tag:
            flags.append(self.quality_tag)
        elif str(r.get("hd")) == "1":
            flags.append("HD")
        if self.has_archive:
            days = r.get("tv_archive_duration")
            flags.append(f"Archiv {days}d" if days else "Archiv")
        if str(r.get("pvr")) == "1" or str(r.get("allow_pvr")) == "1":
            flags.append("PVR")
        if str(r.get("lock")) == "1" or str(r.get("locked")) == "1" or str(r.get("censored")) == "1":
            flags.append("🔒")
        n_cmds = len(r.get("cmds") or [])
        if n_cmds > 1:
            flags.append(f"{n_cmds} Quellen")
        if r.get("xmltv_id"):
            flags.append(f"EPG:{r['xmltv_id']}")
        return " · ".join(flags)

    @classmethod
    def from_raw(cls, raw: Dict[str, Any], genre_map: Optional[Dict[str, str]] = None) -> "Channel":
        ch_id = str(raw.get("id") or raw.get("stream_id") or raw.get("ch_id") or "")
        number = str(raw.get("number") or raw.get("num") or "")
        name = str(raw.get("name") or raw.get("title") or "Unbekannter Kanal")
        cmd = str(raw.get("cmd") or raw.get("url") or "")
        gid = str(raw.get("tv_genre_id") or raw.get("category_id") or raw.get("genre_id") or "*")
        cat = (genre_map or {}).get(gid) or str(raw.get("category_name") or raw.get("group") or "Allgemein")
        logo = str(raw.get("logo") or raw.get("stream_icon") or raw.get("tvg_logo") or "")
        fav = str(raw.get("fav", "0")) == "1"
        return cls(
            id=ch_id,
            number=number,
            name=name,
            cmd=cmd,
            category=cat,
            genre_id=gid,
            logo=logo,
            is_fav=fav,
            quality_tag=detect_quality_tag(name, raw),
            raw_data=dict(raw),
        )


@dataclass
class EPGProgram:
    title: str
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    start_str: str = ""
    end_str: str = ""
    description: str = ""
    category: str = ""
    start_timestamp: int = 0
    stop_timestamp: int = 0
    duration: int = 0
    mark_archive: bool = False
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.title

    @property
    def descr(self) -> str:
        return self.description

    @property
    def time_str(self) -> str:
        return self.start_str

    @property
    def time_to_str(self) -> str:
        return self.end_str

    @property
    def progress_percent(self) -> float:
        now_ts = int(time.time())
        if self.start_timestamp > 0 and self.stop_timestamp > self.start_timestamp:
            if now_ts <= self.start_timestamp:
                return 0.0
            if now_ts >= self.stop_timestamp:
                return 100.0
            return min(
                100.0,
                max(0.0, ((now_ts - self.start_timestamp) / (self.stop_timestamp - self.start_timestamp)) * 100.0),
            )
        if not self.start_time or not self.end_time:
            return 0.0
        now = datetime.datetime.now()
        if self.start_time.tzinfo is not None and now.tzinfo is None:
            now = datetime.datetime.now(self.start_time.tzinfo)
        elif self.start_time.tzinfo is None and now.tzinfo is not None:
            now = datetime.datetime.now()
        if now <= self.start_time:
            return 0.0
        if now >= self.end_time:
            return 100.0
        total = (self.end_time - self.start_time).total_seconds()
        if total <= 0:
            return 0.0
        elapsed = (now - self.start_time).total_seconds()
        return min(100.0, max(0.0, (elapsed / total) * 100.0))

    @property
    def progress(self) -> float:
        return self.progress_percent / 100.0

    @property
    def remaining_minutes(self) -> int:
        now_ts = int(time.time())
        if self.stop_timestamp > 0:
            return max(0, (self.stop_timestamp - now_ts) // 60)
        if not self.end_time:
            return 0
        now = datetime.datetime.now()
        if self.end_time.tzinfo is not None and now.tzinfo is None:
            now = datetime.datetime.now(self.end_time.tzinfo)
        rem = (self.end_time - now).total_seconds()
        return max(0, int(rem // 60))

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]) -> "EPGProgram":
        title = str(raw.get("name") or raw.get("title") or "Sendung")
        descr = str(raw.get("descr") or raw.get("description") or "")
        t_start_str = str(raw.get("time") or raw.get("start") or raw.get("t_time") or "")
        t_stop_str = str(raw.get("time_to") or raw.get("end") or raw.get("stop") or raw.get("t_time_to") or "")

        start_ts = 0
        stop_ts = 0
        for k in ("start_timestamp", "time_ts", "start_ts"):
            val = raw.get(k)
            if val:
                try:
                    start_ts = int(float(val))
                    break
                except Exception:
                    pass
        for k in ("stop_timestamp", "time_to_ts", "stop_ts", "end_timestamp"):
            val = raw.get(k)
            if val:
                try:
                    stop_ts = int(float(val))
                    break
                except Exception:
                    pass

        dt_start = None
        dt_stop = None
        if start_ts > 0:
            try:
                dt_start = datetime.datetime.fromtimestamp(start_ts)
                if not t_start_str:
                    t_start_str = dt_start.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
        elif t_start_str:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    dt_start = datetime.datetime.strptime(t_start_str[:19], fmt)
                    start_ts = int(dt_start.timestamp())
                    break
                except Exception:
                    pass

        if stop_ts > 0:
            try:
                dt_stop = datetime.datetime.fromtimestamp(stop_ts)
                if not t_stop_str:
                    t_stop_str = dt_stop.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
        elif t_stop_str:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    dt_stop = datetime.datetime.strptime(t_stop_str[:19], fmt)
                    stop_ts = int(dt_stop.timestamp())
                    break
                except Exception:
                    pass

        dur = 0
        try:
            dur = int(raw.get("duration") or 0)
        except Exception:
            dur = 0
        if dur <= 0 and start_ts > 0 and stop_ts > start_ts:
            dur = stop_ts - start_ts

        mark_arch = str(raw.get("mark_archive", "0")) == "1" or bool(raw.get("has_archive"))
        return cls(
            title=title,
            start_time=dt_start,
            end_time=dt_stop,
            start_str=t_start_str,
            end_str=t_stop_str,
            description=descr,
            category=str(raw.get("category") or ""),
            start_timestamp=start_ts,
            stop_timestamp=stop_ts,
            duration=dur,
            mark_archive=mark_arch,
            raw_data=dict(raw),
        )


@dataclass
class Profile:
    name: str
    provider_type: str = "Stalker MAC"  # "Stalker MAC", "Xtream Codes", "M3U Playlist"
    portal_url: str = ""
    mac: str = ""
    model: str = "MAG 250"
    serial_number: str = ""
    device_id: str = ""
    device_id2: str = ""
    signature: str = ""
    user_agent: str = ""
    xc_url: str = ""
    username: str = ""
    password: str = ""
    xc_format: str = "ts"
    m3u_source: str = ""
    proxy: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        return cls(
            name=str(data.get("name", "Neues Profil")),
            provider_type=str(data.get("provider_type", "Stalker MAC")),
            portal_url=str(data.get("portal_url", "")),
            mac=str(data.get("mac", "")),
            model=str(data.get("model", "MAG 250")),
            serial_number=str(data.get("serial_number", "")),
            device_id=str(data.get("device_id", "")),
            device_id2=str(data.get("device_id2", "")),
            signature=str(data.get("signature", "")),
            user_agent=str(data.get("user_agent", "")),
            xc_url=str(data.get("xc_url", "")),
            username=str(data.get("username", "")),
            password=str(data.get("password", "")),
            xc_format=str(data.get("xc_format", "ts")),
            m3u_source=str(data.get("m3u_source", "")),
            proxy=str(data.get("proxy", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "portal_url": self.portal_url,
            "mac": self.mac,
            "model": self.model,
            "serial_number": self.serial_number,
            "device_id": self.device_id,
            "device_id2": self.device_id2,
            "signature": self.signature,
            "user_agent": self.user_agent,
            "xc_url": self.xc_url,
            "username": self.username,
            "password": self.password,
            "xc_format": self.xc_format,
            "m3u_source": self.m3u_source,
            "proxy": self.proxy,
        }

    @property
    def portal_type(self) -> str:
        pt = (self.provider_type or "").lower()
        if "xtream" in pt or pt == "xc":
            return "xtream"
        if "m3u" in pt:
            return "m3u"
        return "stalker"

    @portal_type.setter
    def portal_type(self, val: str):
        v = (val or "").lower()
        if "xtream" in v or v == "xc":
            self.provider_type = "Xtream Codes"
        elif "m3u" in v:
            self.provider_type = "M3U Playlist"
        else:
            self.provider_type = "Stalker MAC"

    @property
    def url(self) -> str:
        pt = self.portal_type
        if pt == "xtream":
            return self.xc_url or self.portal_url
        if pt == "m3u":
            return self.m3u_source or self.portal_url
        return self.portal_url

    @url.setter
    def url(self, val: str):
        v = str(val or "").strip()
        self.portal_url = v
        if self.portal_type == "xtream":
            self.xc_url = v
        elif self.portal_type == "m3u":
            self.m3u_source = v

    @property
    def server_url(self) -> str:
        return self.xc_url or self.portal_url

    @server_url.setter
    def server_url(self, val: str):
        self.xc_url = str(val or "").strip()
        if not self.portal_url:
            self.portal_url = self.xc_url

    @property
    def m3u_url(self) -> str:
        return self.m3u_source or self.portal_url

    @m3u_url.setter
    def m3u_url(self, val: str):
        self.m3u_source = str(val or "").strip()
        if not self.portal_url:
            self.portal_url = self.m3u_source

    def clone(self, new_name: Optional[str] = None) -> "Profile":
        d = self.to_dict()
        d["name"] = new_name if new_name is not None else self.name
        return Profile.from_dict(d)


@dataclass
class StreamProbeResult:
    is_alive: bool
    status_code: int = 0
    latency_ms: int = 0
    content_type: str = ""
    error_msg: str = ""
    video_codec: str = ""
    resolution: str = ""
    width: int = 0
    height: int = 0
    fps: float = 0.0
    bitrate_kbps: float = 0.0
    audio_codec: str = ""
    audio_channels: int = 0
    audio_rate: int = 0
    audio_bitrate_kbps: float = 0.0
    packet_loss_percent: float = 0.0
    buffer_health: str = "Optimal"
    thumb_bytes: Optional[bytes] = None


@dataclass
class ScanResult:
    mac: str
    status: str = "Fehler"
    expire: str = "-"
    channels: int = 0
    token: str = ""
    valid: bool = False
    rate_limited: bool = False
    load_url: str = ""
    portal_url: str = ""
    tag: str = "invalid"  # "hot" | "valid" | "expired" | "invalid"


@dataclass
class HttpLogEntry:
    timestamp: str
    method: str
    url: str
    status_code: int
    elapsed_ms: int
    request_headers: Dict[str, str] = field(default_factory=dict)
    request_params: str = ""
    response_preview: str = ""

    @classmethod
    def create(
        cls,
        method: str,
        url: str,
        status_code: int,
        elapsed_ms: int,
        headers: Optional[Dict[str, str]] = None,
        params: str = "",
        body: str = "",
    ) -> "HttpLogEntry":
        return cls(
            timestamp=time.strftime("%H:%M:%S"),
            method=method.upper(),
            url=url,
            status_code=status_code,
            elapsed_ms=elapsed_ms,
            request_headers=dict(headers or {}),
            request_params=params,
            response_preview=body[:8000] if body else "",
        )

    def to_curl(self) -> str:
        parts = [f"curl -i -X {self.method}"]
        for k, v in self.request_headers.items():
            safe_v = str(v).replace('"', '\\"')
            parts.append(f'-H "{k}: {safe_v}"')
        if self.request_params and self.method == "POST":
            safe_p = self.request_params.replace('"', '\\"')
            parts.append(f'--data "{safe_p}"')
        parts.append(f'"{self.url}"')
        return " \\\n  ".join(parts)


class AppState:
    """Zentraler Laufzeit-Zustand der Anwendung."""
    def __init__(self):
        self.provider_mode: str = "Stalker MAC"
        self.current_profile_name: str = "Standard Test"
        self.is_connected: bool = False
        self.connection_status_text: str = "Nicht verbunden"

        self.channels: List[Channel] = []
        self.channels_by_id: Dict[str, Channel] = {}
        self.categories: List[str] = ["Alle Kategorien"]
        self.favorites: Set[str] = set()
        self.vod_favorites: Set[str] = set()
        self.recently_played: List[str] = []

        self.playing_channel: Optional[Channel] = None
        self.current_epg_now: Optional[EPGProgram] = None
        self.current_epg_next: Optional[EPGProgram] = None

        self.sidebar_visible: bool = True
        self.channel_list_visible: bool = True
        self.is_fullscreen: bool = False
        self.is_pip_mode: bool = False
