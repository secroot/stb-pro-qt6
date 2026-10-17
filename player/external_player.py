"""
Externer Player-Runner für STB Pro Qt6.
Unterstützt VLC, MPV und FFplay inklusive Übergabe von User-Agent und Referer.
"""
import os
import sys
import subprocess
from typing import Optional


class ExternalPlayerRunner:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None

    def is_running(self) -> bool:
        return bool(self.process and self.process.poll() is None)

    def stop(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                pass
            self.process = None

    def toggle_fullscreen(self) -> bool:
        if not self.is_running():
            return False
        if sys.platform.startswith("win"):
            try:
                import ctypes
                user32 = ctypes.windll.user32
                pid = self.process.pid
                found_hwnd = []

                WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

                def enum_windows_cb(hwnd, _lparam):
                    lp_pid = ctypes.c_ulong()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lp_pid))
                    if lp_pid.value == pid and user32.IsWindowVisible(hwnd):
                        found_hwnd.append(hwnd)
                    return True

                cb = WNDENUMPROC(enum_windows_cb)
                user32.EnumWindows(cb, 0)
                if found_hwnd:
                    for h in found_hwnd:
                        user32.PostMessageW(h, 0x0100, 0x46, 0)  # VK_F
                        user32.PostMessageW(h, 0x0101, 0x46, 0)
                    return True
            except Exception:
                pass
        return False

    def play(
        self,
        player_type: str,
        player_path: str,
        stream_url: str,
        title: str = "IPTV Stream",
        user_agent: str = "",
        referrer: str = "",
        fullscreen: bool = False,
        caching_ms: Optional[int] = None,
        hw_decode: bool = True,
    ) -> bool:
        self.stop()
        if not player_path or not os.path.exists(player_path):
            return False

        try:
            cmd = [player_path]
            low = player_path.lower()
            if "vlc" in low or player_type == "vlc":
                caching = int(caching_ms) if caching_ms is not None else 1500
                cmd.extend([
                    "--meta-title", title,
                    f"--network-caching={caching}",
                ])
                if hw_decode:
                    cmd.append("--avcodec-hw=any")
                if fullscreen:
                    cmd.append("--fullscreen")
                if user_agent:
                    cmd.append(f"--http-user-agent={user_agent}")
                if referrer:
                    cmd.append(f"--http-referrer={referrer}")
                cmd.append(stream_url)
            elif "mpv" in low or player_type == "mpv":
                cmd.append(f"--title={title}")
                if hw_decode:
                    cmd.append("--hwdec=auto")
                if caching_ms is not None:
                    cmd.append(f"--demuxer-readahead-secs={max(0.5, caching_ms / 1000.0):.1f}")
                if fullscreen:
                    cmd.append("--fs")
                if user_agent:
                    cmd.append(f"--user-agent={user_agent}")
                if referrer:
                    cmd.append(f"--referrer={referrer}")
                cmd.append(stream_url)
            elif "ffplay" in low or player_type == "ffplay":
                cmd.extend([
                    "-window_title", title,
                    "-fflags", "nobuffer",
                    "-flags", "low_delay",
                ])
                if fullscreen:
                    cmd.append("-fs")
                if user_agent:
                    cmd.extend(["-user_agent", user_agent])
                if referrer:
                    cmd.extend(["-headers", f"Referer: {referrer}\r\n"])
                cmd.append(stream_url)
            else:
                if fullscreen:
                    cmd.append("--fullscreen")
                cmd.append(stream_url)

            self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False
