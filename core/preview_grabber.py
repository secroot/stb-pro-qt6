"""
Sender-Vorschau für STB Pro Qt6: Standbild (ein Frame via FFmpeg, gecacht auf Disk).
Optimiert mit High-Speed In-Memory TS-Extraktion und Black-Frame-Filterung.
"""
import hashlib
import os
import shutil
import subprocess
import threading
import time
from typing import Dict, Optional
import requests


def find_ffmpeg() -> str:
    which = shutil.which("ffmpeg")
    if which:
        return which
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        candidate = os.path.join(local_app, "Microsoft", "WinGet", "Links", "ffmpeg.exe")
        if os.path.exists(candidate):
            return candidate
    for pf in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if pf:
            candidate = os.path.join(pf, "ffmpeg", "bin", "ffmpeg.exe")
            if os.path.exists(candidate):
                return candidate
    return ""


FFMPEG_BIN = find_ffmpeg()
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(APP_DIR)
PARENT_THUMB_DIR = os.path.join(PARENT_DIR, ".cache", "thumbs")
THUMB_DIR = PARENT_THUMB_DIR if os.path.exists(PARENT_THUMB_DIR) else os.path.join(APP_DIR, ".cache", "thumbs")
_NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def is_blank_or_black_jpeg(data: bytes) -> bool:
    """Erkennt korrupte, leere oder rein schwarze Dummy-Frames zuverlässig."""
    if not data or len(data) < 1000:
        return True
    if data[:2] != b"\xff\xd8" or data[-2:] != b"\xff\xd9":
        return True
    try:
        from PySide6.QtGui import QImage
        img = QImage()
        if not img.loadFromData(data):
            return True
        w, h = img.width(), img.height()
        if w <= 0 or h <= 0:
            return True
        for sx in (0.2, 0.4, 0.6, 0.8):
            for sy in (0.2, 0.4, 0.6, 0.8):
                c = img.pixelColor(int(w * sx), int(h * sy))
                if c.red() > 16 or c.green() > 16 or c.blue() > 16:
                    return False
        return True
    except Exception:
        return False


def extract_thumbnail_from_ts(data: bytes, width: int = 320) -> Optional[bytes]:
    """
    Extrahiert blitzschnell (0.1s) genau ein Frame aus bereits heruntergeladenen MPEG-TS Bytes via stdin.
    Vermeidet doppelten Netzwerkverkehr und Timeouts.
    """
    if not FFMPEG_BIN or not data or len(data) < 188 * 10:
        return None
    cmd = [
        FFMPEG_BIN, "-hide_banner", "-loglevel", "error", "-nostdin",
        "-fflags", "+genpts+discardcorrupt",
        "-f", "mpegts",
        "-i", "pipe:0",
        "-an", "-sn", "-dn",
        "-frames:v", "1",
        "-vf", f"scale={width}:-2",
        "-q:v", "4",
        "-f", "image2pipe", "-vcodec", "mjpeg", "-"
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            creationflags=_NOWIN,
        )
        out, _ = proc.communicate(input=data, timeout=3.0)
        if out and out[:2] == b"\xff\xd8" and out[-2:] == b"\xff\xd9":
            if not is_blank_or_black_jpeg(out):
                return out
    except Exception:
        pass
    return None


def _cmd(url: str, headers: Dict[str, str], width: int, tail: list) -> list:
    cmd = [
        FFMPEG_BIN or "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
    ]
    if headers:
        hdr = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
        if hdr:
            cmd.extend(["-headers", hdr])
    cmd.extend([
        "-timeout", "5000000",  # 5s socket timeout
        "-fflags", "nobuffer", "-flags", "low_delay",
        "-analyzeduration", "1000000", "-probesize", "1000000",
        "-i", url, "-an", "-sn", "-dn",
    ])
    return cmd + tail


def thumb_path(key: str) -> str:
    return os.path.join(THUMB_DIR, hashlib.md5(key.encode("utf-8", "ignore")).hexdigest() + ".jpg")


def load_cached_thumb(key: str) -> Optional[bytes]:
    p = thumb_path(key)
    try:
        with open(p, "rb") as f:
            data = f.read()
        if is_blank_or_black_jpeg(data):
            try:
                os.remove(p)
            except OSError:
                pass
            return None
        return data
    except OSError:
        return None


def save_thumb(key: str, data: bytes):
    if not data or is_blank_or_black_jpeg(data):
        return
    try:
        os.makedirs(THUMB_DIR, exist_ok=True)
        with open(thumb_path(key), "wb") as f:
            f.write(data)
    except OSError:
        pass


def thumb_age_s(key: str) -> Optional[float]:
    try:
        return time.time() - os.path.getmtime(thumb_path(key))
    except OSError:
        return None


class ThumbGrabber:
    """Holt genau ein Standbild; cancel() beendet ffmpeg sofort."""

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    def grab(self, url: str, headers: Dict[str, str], width: int = 640, timeout: float = 8.0) -> Optional[bytes]:
        # Versuche zuerst schnellen In-Memory Stream-Abruf
        try:
            with requests.get(url, headers=headers or {}, stream=True, timeout=min(timeout, 4.0)) as r:
                if r.status_code == 200:
                    sample = bytearray()
                    for chunk in r.iter_content(32768):
                        sample.extend(chunk)
                        if len(sample) >= 1024 * 1024:
                            break
                    res = extract_thumbnail_from_ts(bytes(sample), width=width)
                    if res:
                        return res
        except Exception:
            pass

        tail = ["-frames:v", "1", "-vf", f"scale={width}:-2", "-q:v", "4", "-f", "image2pipe", "-vcodec", "mjpeg", "-"]
        self.cancel()
        try:
            proc = subprocess.Popen(
                _cmd(url, headers, width, tail),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                creationflags=_NOWIN,
            )
        except Exception:
            return None
        with self._lock:
            self._proc = proc
        try:
            data, _ = proc.communicate(timeout=timeout)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
            return None
        finally:
            with self._lock:
                if self._proc is proc:
                    self._proc = None
        if data and data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9":
            return data if not is_blank_or_black_jpeg(data) else None
        return None

    def cancel(self):
        with self._lock:
            proc, self._proc = self._proc, None
        if proc:
            try:
                proc.kill()
            except Exception:
                pass


def grab_thumbnail(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    width: int = 320,
    timeout: float = 6.0,
    cancel_ev: Optional[threading.Event] = None,
) -> Optional[bytes]:
    """
    High-Performance Standalone Thumbnail Grabber.
    1. Zieht einen ~768KB TS-Chunk via requests.
    2. Dekodiert den Frame in 0.1s via FFmpeg Memory-Pipe.
    3. Fallback auf direkten FFmpeg URL-Aufruf.
    """
    if cancel_ev and cancel_ev.is_set():
        return None
    if not FFMPEG_BIN or not url:
        return None

    # Schneller In-Memory Stream Download + Extraktion
    try:
        t_req = min(max(2.5, timeout - 1.0), 4.5)
        with requests.get(url, headers=headers or {}, stream=True, timeout=t_req) as r:
            if cancel_ev and cancel_ev.is_set():
                return None
            if r.status_code == 200:
                sample = bytearray()
                for chunk in r.iter_content(32768):
                    if cancel_ev and cancel_ev.is_set():
                        return None
                    sample.extend(chunk)
                    if len(sample) >= 800 * 1024:
                        break
                res = extract_thumbnail_from_ts(bytes(sample), width=width)
                if res:
                    return res
    except Exception:
        pass

    if cancel_ev and cancel_ev.is_set():
        return None

    # Fallback: Direktes FFmpeg
    tail = ["-frames:v", "1", "-vf", f"scale={width}:-2", "-q:v", "4", "-f", "image2pipe", "-vcodec", "mjpeg", "-"]
    try:
        proc = subprocess.Popen(
            _cmd(url, headers or {}, width, tail),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            creationflags=_NOWIN,
        )
    except Exception:
        return None

    try:
        data, _ = proc.communicate(timeout=timeout)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
        return None

    if data and data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9":
        return data if not is_blank_or_black_jpeg(data) else None
    return None
