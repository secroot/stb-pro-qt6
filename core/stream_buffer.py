"""
Lokaler Stream-Puffer-Proxy (127.0.0.1) für STB Pro Qt6.
Liest den Upstream-Stream unabhängig vom Player in einen Ringpuffer (Sekunden/MB),
liefert ihn PCR-getaktet an LibVLC und überbrückt kurze Aussetzer durch Auto-Reconnect.
"""
import bisect
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, asdict, fields
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

import requests

TS_PACKET = 188
_LEAD_S = 2.2


@dataclass
class BufferSettings:
    mode: str = "proxy"          # "proxy" (Ringpuffer) | "vlc" (nur LibVLC-Caching)
    vlc_caching_ms: int = 1200   # network/live-caching im VLC-Modus
    start_seconds: float = 0.8   # Startpuffer: Wiedergabe startet ab X s Material (Schnellzapping)
    buffer_seconds: float = 15.0 # Ziel-/Maximal-Puffer-Länge
    max_mb: int = 128            # Harte RAM-Obergrenze des Ringpuffers
    fallback_kbps: int = 6000    # Bitraten-Annahme falls kein PCR/TS erkannt wird
    reconnect: bool = True       # Upstream bei Abbruch automatisch neu verbinden
    max_retries: int = 10        # Maximale Anzahl an Reconnect-Versuchen
    timeout_connect: float = 5.0 # Verbindungs-Timeout
    timeout_read: float = 10.0   # Lese-Timeout
    hw_decode: bool = True       # Hardware-Dekodierung (D3D11/DXVA)
    preview_enabled: bool = True # Standbild bei Senderauswahl
    preview_max_age_min: int = 15
    proxy: str = ""              # HTTP/SOCKS5 Proxy (z.B. http://127.0.0.1:1080)

    def clamp(self) -> "BufferSettings":
        self.mode = self.mode if self.mode in ("proxy", "vlc") else "proxy"
        self.vlc_caching_ms = max(200, min(15000, int(self.vlc_caching_ms)))
        self.buffer_seconds = max(2.0, min(180.0, float(self.buffer_seconds)))
        self.start_seconds = max(0.2, min(self.buffer_seconds, float(self.start_seconds)))
        self.max_mb = max(8, min(1024, int(self.max_mb)))
        self.fallback_kbps = max(200, int(self.fallback_kbps))
        self.max_retries = max(1, int(self.max_retries))
        self.timeout_connect = max(1.0, float(self.timeout_connect))
        self.timeout_read = max(1.0, float(self.timeout_read))
        self.preview_max_age_min = max(0, int(self.preview_max_age_min))
        self.proxy = str(self.proxy or "").strip()
        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "BufferSettings":
        s = cls()
        for f in fields(cls):
            if d and f.name in d:
                try:
                    cur = getattr(s, f.name)
                    setattr(s, f.name, type(cur)(d[f.name]))
                except Exception:
                    pass
        return s.clamp()


class _Session:
    def __init__(self, url: str, headers: Dict[str, str], st: BufferSettings):
        self.url, self.headers, self.st = url, dict(headers or {}), st
        self.cond = threading.Condition()
        self.chunks: deque = deque()
        self.base = 0
        self.stored = 0
        self.produced = 0
        self.cpos = 0
        self.stopped = False
        self.eof = False
        self.connected = False
        self.error = ""
        self.state = "prefill"
        self.reconnects = 0
        self.rebuffers = 0
        self.id = uuid.uuid4().hex[:10]
        self._resp = None
        self.in_bps = 0.0
        self.mux_bps = 0.0
        self._win_t = time.time()
        self._win_b = 0
        self._t_first = 0.0
        self._bytes_active = 0
        self.ts_ok = True
        self.pcr_seen = False
        self._pcr_pid: Optional[int] = None
        self._pcr_rate_start: Optional[tuple] = None
        self._pcr_rate_last: Optional[tuple] = None
        self._writer_seq: int = 0
        self._pend = bytearray()
        self._pend_abs = 0
        self._need_sync = True
        self._sync_fail = 0
        self.video_codec: str = ""
        self.audio_codec: str = ""
        self._pmt_pid: Optional[int] = None
        self._last_rx: float = time.time()
        self.thread = threading.Thread(target=self._produce, daemon=True)
        self.thread.start()

    def _rate_est(self) -> float:
        el = time.time() - self._t_first if self._t_first else 0
        if el >= 2.0 and self._bytes_active > 0:
            return max(1.0, self._bytes_active / el)
        return max(1.0, self.st.fallback_kbps * 125.0)

    def _record_pcr(self, abs_offset: int, pcr_time: float):
        if self._pcr_rate_start is None:
            self._pcr_rate_start = (abs_offset, pcr_time)
            self._pcr_rate_last = (abs_offset, pcr_time)
            return

        dt = pcr_time - self._pcr_rate_start[1]
        db = abs_offset - self._pcr_rate_start[0]

        if dt < -0.5 or dt > 10.0 or db < 0:
            self._pcr_rate_start = (abs_offset, pcr_time)
            self._pcr_rate_last = (abs_offset, pcr_time)
            return

        if dt >= 0.8 and db > 0:
            calc_bps = (db * 8.0) / dt
            if 100_000 <= calc_bps <= 150_000_000:
                self.mux_bps = calc_bps
            if dt >= 2.5:
                self._pcr_rate_start = self._pcr_rate_last
        self._pcr_rate_last = (abs_offset, pcr_time)

    def _level_s(self, pos: int) -> float:
        unconsumed = max(0, self.produced - pos)
        bps = self.mux_bps if self.mux_bps >= 50000.0 else (
            self.in_bps if self.in_bps >= 50000.0 else (self._rate_est() * 8.0)
        )
        bytes_per_sec = max(10000.0, bps / 8.0)
        return unconsumed / bytes_per_sec

    def _scan(self, chunk: bytes):
        p = self._pend
        p.extend(chunk)
        while True:
            if self._need_sync:
                if len(p) < TS_PACKET * 3 + 1:
                    return
                idx = -1
                for i in range(0, len(p) - 2 * TS_PACKET):
                    if p[i] == 0x47 and p[i + TS_PACKET] == 0x47 and p[i + 2 * TS_PACKET] == 0x47:
                        idx = i
                        break
                    if i >= TS_PACKET:
                        break
                if idx < 0:
                    self._sync_fail += 1
                    if self._sync_fail >= 20 and not self.pcr_seen:
                        self.ts_ok = False
                        self._pend.clear()
                        return
                    del p[:TS_PACKET]
                    self._pend_abs += TS_PACKET
                    continue
                del p[:idx]
                self._pend_abs += idx
                self._need_sync = False
            n = len(p) // TS_PACKET
            if n == 0:
                return
            done = 0
            for k in range(n):
                o = k * TS_PACKET
                if p[o] != 0x47:
                    self._need_sync = True
                    break
                done = k + 1
                # Ignore packets with Transport Error Indicator (TEI, bit 7 of byte 1)
                if (p[o + 1] & 0x80) != 0:
                    continue
                pid = ((p[o + 1] & 0x1F) << 8) | p[o + 2]
                has_pusi = bool(p[o + 1] & 0x40)
                afc = (p[o + 3] & 0x30) >> 4

                if not (self.video_codec and self.audio_codec):
                    self._parse_ts_psi(p, o, pid, has_pusi, afc)

                if (p[o + 3] & 0x20) and (7 <= p[o + 4] <= 183) and (p[o + 5] & 0x10):
                    if pid < 0x0010 or pid >= 0x1FFF:
                        continue
                    if self._pcr_pid is None:
                        self._pcr_pid = pid
                    if pid != self._pcr_pid:
                        continue
                    base = (p[o + 6] << 25) | (p[o + 7] << 17) | (p[o + 8] << 9) | (p[o + 9] << 1) | (p[o + 10] >> 7)
                    ext = ((p[o + 10] & 1) << 8) | p[o + 11]
                    t = (base * 300 + ext) / 27_000_000.0
                    self.pcr_seen = True
                    self._record_pcr(self._pend_abs + o, t)
            consumed = done * TS_PACKET
            del p[:consumed]
            self._pend_abs += consumed
            if self._need_sync:
                continue
            return

    def _parse_ts_psi(self, p: bytearray, o: int, pid: int, has_pusi: bool, afc: int):
        try:
            pay_off = o + 4
            if afc == 0x03:
                pay_off = o + 5 + p[o + 4]
            elif afc == 0x02:
                return
            if pay_off >= o + TS_PACKET:
                return

            # 1. PAT (PID 0) -> discover PMT PID
            if pid == 0 and not self._pmt_pid:
                tbl_off = pay_off + (1 + p[pay_off] if has_pusi else 0)
                if tbl_off + 8 < o + TS_PACKET and p[tbl_off] == 0x00:
                    sec_len = ((p[tbl_off + 1] & 0x0F) << 8) | p[tbl_off + 2]
                    end_sec = min(o + TS_PACKET - 4, tbl_off + 3 + sec_len - 4)
                    for prg_i in range(tbl_off + 8, end_sec, 4):
                        prg_num = (p[prg_i] << 8) | p[prg_i + 1]
                        if prg_num != 0:
                            self._pmt_pid = ((p[prg_i + 2] & 0x1F) << 8) | p[prg_i + 3]
                            break

            # 2. PMT -> extract elementary stream codecs
            elif self._pmt_pid and pid == self._pmt_pid:
                tbl_off = pay_off + (1 + p[pay_off] if has_pusi else 0)
                if tbl_off + 12 < o + TS_PACKET and p[tbl_off] == 0x02:
                    sec_len = ((p[tbl_off + 1] & 0x0F) << 8) | p[tbl_off + 2]
                    prog_info_len = ((p[tbl_off + 10] & 0x0F) << 8) | p[tbl_off + 11]
                    es_start = tbl_off + 12 + prog_info_len
                    end_sec = min(o + TS_PACKET - 4, tbl_off + 3 + sec_len - 4)
                    idx = es_start
                    while idx + 5 <= end_sec:
                        stype = p[idx]
                        es_info_len = ((p[idx + 3] & 0x0F) << 8) | p[idx + 4]
                        if not self.video_codec:
                            if stype == 0x1B:
                                self.video_codec = "H.264 / AVC"
                            elif stype == 0x24:
                                self.video_codec = "HEVC / H.265"
                            elif stype == 0x02:
                                self.video_codec = "MPEG-2 Video"
                            elif stype in (0x01, 0x10):
                                self.video_codec = "MPEG-4 Video"

                        if not self.audio_codec:
                            desc_bytes = p[idx + 5 : min(end_sec, idx + 5 + es_info_len)]
                            if stype == 0x0F:
                                self.audio_codec = "AAC-LC"
                            elif stype == 0x11:
                                self.audio_codec = "AAC (LATM)"
                            elif stype in (0x03, 0x04):
                                self.audio_codec = "MP3 Audio"
                            elif stype == 0x81:
                                self.audio_codec = "Dolby Digital (AC3)"
                            elif stype == 0x87:
                                self.audio_codec = "Dolby Digital+ (E-AC3)"
                            elif stype in (0x82, 0x86):
                                self.audio_codec = "DTS Audio"
                            elif stype == 0x06:
                                if 0x6A in desc_bytes:
                                    self.audio_codec = "Dolby Digital (AC3)"
                                elif 0x7A in desc_bytes:
                                    self.audio_codec = "Dolby Digital+ (E-AC3)"
                                elif 0x7B in desc_bytes:
                                    self.audio_codec = "DTS Audio"
                                else:
                                    self.audio_codec = "Dolby Audio"
                        idx += 5 + es_info_len
        except Exception:
            pass

    def _produce(self):
        max_b = self.st.max_mb * 1048576
        attempts = 0
        proxies = {"http": self.st.proxy, "https": self.st.proxy} if getattr(self.st, "proxy", "") else None
        while not self.stopped:
            try:
                target_s = max(self.st.buffer_seconds, self.st.start_seconds + 2.0)
                with requests.get(
                    self.url,
                    headers=self.headers,
                    stream=True,
                    timeout=(self.st.timeout_connect, self.st.timeout_read),
                    proxies=proxies,
                ) as r:
                    self._resp = r
                    if r.status_code not in (200, 206):
                        from core.stream_probe import diagnose_iptv_status
                        raise IOError(diagnose_iptv_status(r.status_code))
                    self.connected = True
                    self.error = ""
                    attempts = 0
                    self._pend.clear()
                    self._pend_abs = self.produced
                    self._need_sync = True
                    if not self._t_first:
                        self._t_first = time.time()

                    first_chunk = True
                    for chunk in r.iter_content(65536):
                        if self.stopped:
                            return
                        if not chunk:
                            continue
                        if first_chunk:
                            first_chunk = False
                            from core.stream_probe import detect_stream_error_payload
                            err_payload = detect_stream_error_payload(chunk, r.headers.get("Content-Type", ""))
                            if err_payload:
                                self.connected = False
                                self.error = err_payload
                                try:
                                    from core.signals import event_bus
                                    event_bus.stream_ip_ban_detected.emit(self.url, err_payload)
                                except Exception:
                                    pass
                                raise IOError(err_payload)

                        self._last_rx = time.time()
                        if self.ts_ok:
                            self._scan(chunk)

                        with self.cond:
                            self.chunks.append(chunk)
                            self.produced += len(chunk)
                            self.stored += len(chunk)
                            self._bytes_active += len(chunk)
                            self.cond.notify_all()

                        self._tick_rate(len(chunk))

                        # Flow-control pacing:
                        # Keep buffer filled to target_s (e.g. 15s).
                        # Pauses upstream ingest when buffer cushion is full,
                        # avoiding runaway buffer bloat and preventing running into live broadcast edge.
                        with self.cond:
                            while not self.stopped and self.state == "playing":
                                lvl = self._level_s(self.cpos)
                                if lvl >= target_s:
                                    self.cond.wait(0.04)
                                else:
                                    break

                            # Emergency cap: only if stored exceeds hard max_b (e.g. player paused)
                            while self.stored > max_b and len(self.chunks) > 1:
                                c = self.chunks.popleft()
                                self.base += len(c)
                                self.stored -= len(c)

                raise IOError("Upstream beendet")
            except Exception as e:
                self.connected = False
                self.error = str(e)[:140]
                if self.stopped:
                    return
                # Bei definitiver IP- oder ISP-Sperre keine sinnlosen Reconnects erzwingen
                if any(k in self.error for k in ("IP-Sperre", "ISP-Sperre", "IP_BAN", "ISP_LOCK")):
                    break
                if not self.st.reconnect or attempts >= self.st.max_retries:
                    break
                attempts += 1
                self.reconnects += 1
                with self.cond:
                    if not self.stopped:
                        self.cond.wait(min(2.0, 0.3 * attempts))
        with self.cond:
            self.eof = True
            self.cond.notify_all()

    def _tick_rate(self, n: int):
        now = time.time()
        self._win_b += n
        dt = now - self._win_t
        if dt >= 1.0:
            self.in_bps = self._win_b * 8 / dt
            self._win_t, self._win_b = now, 0

    def _take(self, pos: int, n: int):
        while self.chunks and self.base + len(self.chunks[0]) <= pos:
            c = self.chunks.popleft()
            self.base += len(c)
            self.stored -= len(c)
        c = self.chunks[0]
        i = pos - self.base
        data = c[i:i + n]
        return data, pos + len(data)

    def serve(self, wfile):
        with self.cond:
            self._writer_seq += 1
            writer_id = self._writer_seq
            pos = self.cpos if self.cpos >= self.base else self.base

        while True:
            with self.cond:
                while True:
                    if self.stopped or writer_id != self._writer_seq:
                        return
                    pos = max(pos, self.base)
                    self.cpos = pos
                    level_b = self.produced - pos
                    lvl = self._level_s(pos)

                    if self.state != "playing":
                        need = self.st.start_seconds if self.state == "prefill" else max(0.2, self.st.start_seconds * 0.3)
                        wall_el = (time.time() - self._t_first) if self._t_first else 0.0
                        # Start immediately if we have either enough seconds, EOF, or at least 48KB after 0.25s
                        if level_b > 0 and (lvl >= need or self.eof or (wall_el >= 0.25 and level_b >= 49152)):
                            self.state = "playing"
                            self.cond.notify_all()
                        elif self.eof and level_b <= 0:
                            return
                        else:
                            self.cond.wait(0.04)
                            continue

                    if level_b <= 0:
                        if self.eof:
                            return
                        now = time.time()
                        # Only enter rebuffer if upstream has genuinely stopped delivering bytes (> 1.8s) or disconnected
                        if (not self.connected) or (self._last_rx > 0 and (now - self._last_rx) > 1.8):
                            if self.state != "rebuffer":
                                self.state = "rebuffer"
                                self.rebuffers += 1
                        self.cond.wait(0.04)
                        continue

                    break

                data, new_pos = self._take(pos, 32768)
                self.cpos = new_pos
                self.cond.notify_all()

            try:
                wfile.write(data)
                wfile.flush()
            except (BrokenPipeError, ConnectionResetError, IOError, OSError):
                return

            pos = new_pos

    def stop(self):
        self.stopped = True
        with self.cond:
            self.cond.notify_all()
        resp = self._resp
        self._resp = None
        if resp is not None:
            def _close_resp():
                try:
                    resp.close()
                except Exception:
                    pass
            threading.Thread(target=_close_resp, daemon=True).start()

    def stats(self) -> Dict[str, Any]:
        with self.cond:
            pos = max(self.cpos, self.base)
            lvl = self._level_s(pos)
            need = max(0.01, self.st.start_seconds)
            bps = self.mux_bps if self.mux_bps >= 50000.0 else (
                self.in_bps if self.in_bps >= 50000.0 else (self._rate_est() * 8.0)
            )
            return {
                "active": True,
                "state": self.state,
                "level_s": round(lvl, 1),
                "buffer_s": self.st.buffer_seconds,
                "start_s": self.st.start_seconds,
                "prefill_pct": min(100.0, lvl / need * 100.0) if self.state == "prefill" else 100.0,
                "level_mb": round(max(0, self.produced - pos) / 1048576, 2),
                "max_mb": self.st.max_mb,
                "in_kbps": round(bps / 1000.0, 0),
                "reconnects": self.reconnects,
                "rebuffers": self.rebuffers,
                "connected": self.connected,
                "pcr": self.pcr_seen,
                "video_codec": self.video_codec,
                "audio_codec": self.audio_codec,
                "error": self.error,
            }


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_HEAD(self):
        sess = self.server.proxy.get_session(self.path)
        if not sess:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "video/mp2t")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Connection", "close")
        self.end_headers()

    def do_GET(self):
        sess = self.server.proxy.get_session(self.path)
        if not sess:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "video/mp2t")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Pragma", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            sess.serve(self.wfile)
        except (OSError, ValueError):
            pass


class StreamBufferProxy:
    def __init__(self):
        self.server: Optional[ThreadingHTTPServer] = None
        self.session: Optional[_Session] = None
        self._lock = threading.Lock()

    def _ensure_server(self):
        if self.server:
            return
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.server.daemon_threads = True
        self.server.proxy = self
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def open_session(self, url: str, headers: Dict[str, str], settings: BufferSettings) -> str:
        with self._lock:
            self._ensure_server()
            if self.session:
                self.session.stop()
            self.session = _Session(url, headers, settings)
            return f"http://127.0.0.1:{self.server.server_address[1]}/s/{self.session.id}"

    def get_session(self, path: str) -> Optional[_Session]:
        s = self.session
        return s if s and path.rstrip("/").endswith(s.id) else None

    def stop_session(self):
        with self._lock:
            if self.session:
                self.session.stop()
                self.session = None

    def stats(self) -> Dict[str, Any]:
        s = self.session
        return s.stats() if s else {"active": False}

    def shutdown(self):
        self.stop_session()
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass
            self.server = None
