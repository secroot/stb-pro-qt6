"""
Aufnahme (Live) und Download (VOD/Archiv) von Streams für STB Pro Qt6.
- HTTP/TS/MKV/MP4: direkter Stream-Download via requests (VOD mit Resume per Range).
- HLS (.m3u8): ffmpeg -c copy.
- Automatische Erkennung von HLS-Playlists, HTML/JSON-Fehlermeldungen und Reconnect-Schutz.
"""
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import requests

CHUNK = 256 * 1024
MAX_DOWNTIME = 180
MIN_VOD_BYTES = 100 * 1024


class _HLSDetected(Exception):
    def __init__(self, url: str):
        super().__init__("HLS Playlist erkannt")
        self.url = url


def safe_name(name: str, maxlen: int = 80) -> str:
    s = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", name or "stream").strip(" ._")
    return (s or "stream")[:maxlen]


def find_ffmpeg() -> Optional[str]:
    ff = shutil.which("ffmpeg")
    if ff:
        return ff
    candidates = []
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        candidates.append(os.path.join(local_app, "Microsoft", "WinGet", "Links", "ffmpeg.exe"))
    prog_files = os.environ.get("ProgramFiles")
    if prog_files:
        candidates.append(os.path.join(prog_files, "ffmpeg", "bin", "ffmpeg.exe"))
    candidates.extend([
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ])
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


@dataclass
class Job:
    id: int
    kind: str                # "rec" | "dl"
    name: str
    url: str
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    state: str = "queued"    # queued|running|done|stopped|error
    bytes: int = 0
    total: int = 0
    error: str = ""
    started: float = 0.0
    ended: float = 0.0
    speed: float = 0.0
    stop_ev: threading.Event = field(default_factory=threading.Event)
    proc: Optional[subprocess.Popen] = None
    refresh: Optional[Callable[[], Optional[str]]] = None
    reconnects: int = 0
    note: str = ""
    last_data: float = 0.0
    duration_sec: float = 0.0
    current_sec: float = 0.0

    @property
    def active(self) -> bool:
        return self.state in ("queued", "running")

    @property
    def elapsed(self) -> float:
        return (self.ended or time.time()) - self.started if self.started else 0.0

    @property
    def job_id(self) -> str:
        return str(self.id)

    @property
    def title(self) -> str:
        return self.name

    @property
    def status(self) -> str:
        if self.state == "done":
            return "completed"
        return self.state

    @property
    def bytes_written(self) -> int:
        return self.bytes

    @property
    def total_bytes(self) -> int:
        return self.total

    @property
    def speed_kbps(self) -> float:
        return self.speed / 1024.0

    @property
    def elapsed_str(self) -> str:
        sec = int(max(0, self.elapsed))
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"


class Recorder:
    def __init__(
        self,
        out_dir: str,
        on_change: Optional[Callable[[], None]] = None,
        log: Optional[Callable[[str], None]] = None,
    ):
        self.out_dir = out_dir
        self.on_change = on_change or (lambda: None)
        self.log = log or (lambda m: None)
        self.jobs: List[Job] = []
        self._seq = 0
        self._lock = threading.Lock()

    @property
    def output_dir(self) -> str:
        return self.out_dir

    def set_dir(self, d: str):
        self.out_dir = d

    def start(
        self,
        kind: str,
        name: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        ext: Optional[str] = None,
        refresh: Optional[Callable[[], Optional[str]]] = None,
    ) -> Job:
        os.makedirs(self.out_dir, exist_ok=True)
        is_hls = ".m3u8" in url.lower().split("?")[0]
        if not ext:
            m = re.search(r"\.(mkv|mp4|avi|ts|mov|m4v|flv|webm)(?:$|\?)", url.lower())
            ext = m.group(1) if m else ("ts" if kind == "rec" or is_hls else "mp4")
        if is_hls:
            ext = "ts"
        stamp = time.strftime("%Y%m%d_%H%M%S")
        base = safe_name(name)
        fname = f"{base}_{stamp}.{ext}" if kind == "rec" else f"{base}.{ext}"
        path = os.path.join(self.out_dir, fname)
        with self._lock:
            self._seq += 1
            job = Job(self._seq, kind, name, url, path, dict(headers or {}), refresh=refresh)
            self.jobs.append(job)
        threading.Thread(target=self._run, args=(job, is_hls), daemon=True).start()
        return job

    def stop(self, job: Job):
        job.stop_ev.set()
        if job.proc and job.proc.poll() is None:
            try:
                if job.proc.stdin:
                    job.proc.stdin.write(b"q")
                    job.proc.stdin.flush()
            except Exception:
                pass
            try:
                job.proc.terminate()
            except Exception:
                pass

    def stop_job(self, job_id: str | int):
        target = str(job_id)
        for j in self.jobs:
            if str(j.id) == target and j.active:
                self.stop(j)

    def stop_all(self):
        for j in self.jobs:
            if j.active:
                self.stop(j)

    def active_jobs(self, kind: Optional[str] = None) -> List[Job]:
        return [j for j in self.jobs if j.active and (kind is None or j.kind == kind)]

    def remove_finished(self):
        with self._lock:
            self.jobs = [j for j in self.jobs if j.active]
        self.on_change()

    def clear_finished(self):
        self.remove_finished()

    def _finish(self, job: Job, state: str, err: str = ""):
        job.state, job.error, job.ended = state, err, time.time()
        mbs = job.bytes / 1048576.0
        self.log(
            f"[{'+' if state in ('done', 'stopped') else '-'}] {job.kind.upper()} {state}: "
            f"{os.path.basename(job.path)} ({mbs:.1f} MB){' - ' + err if err else ''}"
        )
        self.on_change()

    def _run(self, job: Job, is_hls: bool):
        job.state, job.started = "running", time.time()
        self.log(f"[*] {job.kind.upper()} gestartet: {os.path.basename(job.path)}")
        self.on_change()
        try:
            if is_hls:
                self._run_ffmpeg(job)
            else:
                try:
                    self._run_http(job)
                except _HLSDetected as hls_err:
                    self.log(f"[*] Stream ist HLS-Playlist. Wechsle zu ffmpeg für: {job.name}")
                    job.url = hls_err.url
                    self._run_ffmpeg(job)
        except Exception as e:
            self._finish(job, "error", str(e))

    def _attempt(self, job: Job, resume_from: int, append: bool) -> str:
        hdrs = dict(job.headers)
        hdrs.setdefault("User-Agent", "VLC/3.0.0")
        if job.kind == "dl" and resume_from > 0:
            hdrs["Range"] = f"bytes={resume_from}-"

        with requests.get(job.url, headers=hdrs, stream=True, timeout=(10, 20), allow_redirects=True) as r:
            if r.status_code == 416:
                job.bytes = job.total = resume_from
                return "complete"
            if r.status_code >= 400:
                raise RuntimeError(f"HTTP {r.status_code} {r.reason}")

            ctype = r.headers.get("Content-Type", "").lower()
            if any(h in ctype for h in ("mpegurl", "m3u8", "x-mpegurl")) or ".m3u8" in r.url.lower().split("?")[0]:
                raise _HLSDetected(r.url)

            ranged = r.status_code == 206
            if job.kind == "dl":
                if resume_from and not ranged:
                    resume_from, append = 0, False
                cl = int(r.headers.get("Content-Length") or 0)
                if cl and not job.total:
                    job.total = resume_from + cl
                job.bytes = resume_from

            last_t, last_b, last_ui = time.time(), job.bytes, 0.0
            got = False
            first_chunk = True

            with open(job.path, "ab" if append else "wb") as f:
                for chunk in r.iter_content(CHUNK):
                    if job.stop_ev.is_set():
                        return "stopped"
                    if not chunk:
                        continue

                    if first_chunk:
                        first_chunk = False
                        sample = chunk[:512].strip()
                        if sample.startswith(b"#EXTM3U") or b"#EXT-X-STREAM-INF" in sample:
                            raise _HLSDetected(r.url)
                        if sample.startswith((b"<!DOCTYPE", b"<html", b"<HTML", b"{\"error\"", b"{\"js\"")):
                            err_txt = sample.decode("utf-8", "ignore")[:150].strip()
                            raise RuntimeError(f"Server-Fehlermeldung (kein Video): {err_txt}")

                    got = True
                    job.last_data = time.time()
                    f.write(chunk)
                    job.bytes += len(chunk)
                    now = job.last_data
                    if now - last_t >= 1.0:
                        job.speed = (job.bytes - last_b) / (now - last_t)
                        last_t, last_b = now, job.bytes
                    if now - last_ui >= 0.5:
                        last_ui = now
                        self.on_change()

        if job.stop_ev.is_set():
            return "stopped"
        if job.total and job.bytes >= job.total:
            return "complete"
        if job.kind == "dl" and not job.total:
            if job.bytes >= MIN_VOD_BYTES:
                return "complete"
            return "dropped"
        return "dropped" if got or job.kind == "rec" else "dropped"

    def _run_http(self, job: Job):
        append = job.kind == "dl" and os.path.exists(job.path) and os.path.getsize(job.path) > 0
        resume = os.path.getsize(job.path) if append else 0
        job.last_data = time.time()
        fails = 0
        down_since = None
        while not job.stop_ev.is_set():
            before = job.bytes
            try:
                res = self._attempt(job, resume, append)
                err = "Verbindung beendet"
            except _HLSDetected:
                raise
            except Exception as e:
                res, err = "dropped", str(e) or e.__class__.__name__

            if res == "stopped":
                break
            if res == "complete":
                if job.kind == "dl" and job.bytes < MIN_VOD_BYTES and not job.stop_ev.is_set():
                    return self._finish(job, "error", f"Unvollständiger Download (nur {job.bytes // 1024} KB empfangen)")
                return self._finish(job, "done")

            if job.bytes > before:
                fails, down_since = 0, None
            fails += 1
            down_since = down_since or time.time()
            if time.time() - down_since > MAX_DOWNTIME:
                return self._finish(job, "error", f"Reconnect aufgegeben nach {MAX_DOWNTIME}s ({err})")
            job.reconnects += 1
            job.speed = 0
            job.note = f"Reconnect #{job.reconnects}: {err}"
            self.log(f"[!] {job.kind.upper()} '{job.name}': {err} - verbinde neu (#{job.reconnects})")
            self.on_change()

            if fails >= 2 and job.refresh:
                try:
                    new = job.refresh()
                    if new:
                        job.url = new
                except Exception as e:
                    self.log(f"[-] Link-Refresh fehlgeschlagen: {e}")

            if job.stop_ev.wait(min(1.0 * fails, 5.0)):
                break
            append, resume = True, (job.bytes if job.kind == "dl" else 0)

        self._finish(job, "stopped")

    def _run_ffmpeg(self, job: Job):
        ff = find_ffmpeg()
        if not ff:
            raise RuntimeError("HLS-Stream: ffmpeg.exe nicht gefunden.")

        hdr_str = "".join(f"{k}: {v}\r\n" for k, v in job.headers.items())
        cmd = [
            ff, "-y", "-stats", "-loglevel", "info",
            "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "10"
        ]
        if hdr_str:
            cmd.extend(["-headers", hdr_str])
        cmd.extend(["-i", job.url, "-c", "copy", job.path])

        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        job.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=flags,
        )

        stderr_lines: List[str] = []

        def _reader():
            if not job.proc or not job.proc.stderr:
                return
            last_t = time.time()
            last_b = 0
            for raw_line in iter(job.proc.stderr.readline, b""):
                line = raw_line.decode("utf-8", "replace").strip()
                if not line:
                    continue
                stderr_lines.append(line)
                if len(stderr_lines) > 20:
                    stderr_lines.pop(0)

                m_dur = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", line)
                if m_dur:
                    h, m, s = float(m_dur.group(1)), float(m_dur.group(2)), float(m_dur.group(3))
                    job.duration_sec = h * 3600 + m * 60 + s

                m_time = re.search(r"time=\s*(\d+):(\d+):(\d+(?:\.\d+)?)", line)
                if m_time:
                    h, m, s = float(m_time.group(1)), float(m_time.group(2)), float(m_time.group(3))
                    job.current_sec = h * 3600 + m * 60 + s

                now = time.time()
                if now - last_t >= 1.0:
                    try:
                        cur_b = os.path.getsize(job.path)
                        job.speed = (cur_b - last_b) / (now - last_t)
                        last_b = cur_b
                    except OSError:
                        pass
                    last_t = now

        t_read = threading.Thread(target=_reader, daemon=True)
        t_read.start()

        while job.proc.poll() is None:
            try:
                job.bytes = os.path.getsize(job.path)
            except OSError:
                pass
            self.on_change()
            time.sleep(0.5)

        t_read.join(timeout=2.0)

        try:
            job.bytes = os.path.getsize(job.path)
        except OSError:
            pass

        if job.stop_ev.is_set():
            return self._finish(job, "stopped")

        if job.proc.returncode != 0:
            err_msg = " ".join(stderr_lines[-5:]) if stderr_lines else f"ffmpeg exit {job.proc.returncode}"
            return self._finish(job, "error", err_msg[-200:])

        if job.kind == "dl" and job.bytes < MIN_VOD_BYTES:
            err_msg = " ".join(stderr_lines[-3:]) if stderr_lines else f"Unvollständiger Download (nur {job.bytes // 1024} KB)"
            return self._finish(job, "error", err_msg[-200:])

        self._finish(job, "done")


RecorderManager = Recorder

