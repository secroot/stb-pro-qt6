"""
Asynchroner Qt6 Logo- & Poster-Cache (QPixmap / QImage).
Nutzt Memory-Cache + Disk-Cache (teilt sich .cache/logos mit dem Hauptprojekt für sofortige Anzeige).
"""
import os
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable, Dict, Tuple
import requests
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QImage, QPixmap

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(APP_DIR)
# Teile den bestehenden Logo-Cache, falls vorhanden
PARENT_CACHE_DIR = os.path.join(PARENT_DIR, ".cache", "logos")
CACHE_DIR = PARENT_CACHE_DIR if os.path.exists(PARENT_CACHE_DIR) else os.path.join(APP_DIR, ".cache", "logos")
os.makedirs(CACHE_DIR, exist_ok=True)


class LogoCache(QObject):
    """
    Lädt Kanal-Logos und VOD-Poster im Hintergrund als QImage (Thread-sicher!)
    und wandelt sie im UI-Thread in skalierte QPixmaps um.
    """
    _image_decoded = Signal(str, int, int, QImage)
    logo_ready = Signal(str)  # (url) emitted after QPixmap is stored in mem_cache

    def __init__(self, max_threads: int = 6):
        super().__init__()
        self.executor = ThreadPoolExecutor(max_workers=max_threads)
        self.mem_cache: Dict[Tuple[str, int, int], QPixmap] = {}
        self.callbacks: Dict[Tuple[str, int, int], list] = {}
        self.pending = set()
        self.lock = threading.Lock()
        self._image_decoded.connect(self._on_image_ready)

    @staticmethod
    def _url_to_path(url: str) -> str:
        h = hashlib.md5(url.encode("utf-8", errors="ignore")).hexdigest()
        ext = ".png"
        low = url.lower().split("?")[0]
        if low.endswith((".jpg", ".jpeg")):
            ext = ".jpg"
        elif low.endswith(".webp"):
            ext = ".webp"
        return os.path.join(CACHE_DIR, f"{h}{ext}")

    def get_cached_pixmap(self, url: str, size: Tuple[int, int] = (40, 40)) -> Optional[QPixmap]:
        if not url:
            return None
        key = (url, size[0], size[1])
        return self.mem_cache.get(key)

    def get_pixmap(self, url: str, width: int = 40, height: int = 40) -> Optional[QPixmap]:
        return self.request_pixmap(url, size=(width, height))

    def get_or_fetch(self, url: str, width: int = 40, height: int = 40) -> Optional[QPixmap]:
        return self.request_pixmap(url, size=(width, height))

    def request_pixmap(
        self,
        url: str,
        size: Tuple[int, int] = (40, 40),
        on_loaded: Optional[Callable[[QPixmap], None]] = None,
    ) -> Optional[QPixmap]:
        """
        Gibt QPixmap sofort zurück falls im RAM-Cache; andernfalls startet asynchroner Abruf.
        """
        if not url or not url.startswith(("http://", "https://")):
            return None

        key = (url, size[0], size[1])
        if key in self.mem_cache:
            pm = self.mem_cache[key]
            if on_loaded:
                on_loaded(pm)
            return pm

        with self.lock:
            if on_loaded:
                self.callbacks.setdefault(key, []).append(on_loaded)
            if key in self.pending:
                return None
            self.pending.add(key)

        def _worker():
            try:
                disk_path = self._url_to_path(url)
                raw_bytes = None

                if os.path.exists(disk_path) and os.path.getsize(disk_path) > 100:
                    try:
                        with open(disk_path, "rb") as f:
                            raw_bytes = f.read()
                    except Exception:
                        raw_bytes = None

                if raw_bytes is None:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
                        "Accept": "image/*,*/*",
                    }
                    resp = requests.get(url, headers=headers, timeout=4.0)
                    if resp.status_code == 200 and len(resp.content) > 100:
                        raw_bytes = resp.content
                        try:
                            with open(disk_path, "wb") as f:
                                f.write(raw_bytes)
                        except Exception:
                            pass

                if raw_bytes:
                    qimg = QImage()
                    if qimg.loadFromData(raw_bytes):
                        scaled = qimg.scaled(
                            size[0],
                            size[1],
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        self._image_decoded.emit(url, size[0], size[1], scaled)
            except Exception:
                pass
            finally:
                with self.lock:
                    self.pending.discard(key)

        self.executor.submit(_worker)
        return None

    def _on_image_ready(self, url: str, w: int, h: int, qimg: QImage):
        key = (url, w, h)
        pm = QPixmap.fromImage(qimg)
        if len(self.mem_cache) > 2500:
            # Einfache LRU-Bereinigung bei extrem großen Playlisten
            for k in list(self.mem_cache.keys())[:500]:
                self.mem_cache.pop(k, None)
        self.mem_cache[key] = pm

        with self.lock:
            cbs = self.callbacks.pop(key, [])

        for cb in cbs:
            try:
                cb(pm)
            except Exception:
                pass

        self.logo_ready.emit(url)


logo_cache = LogoCache()
