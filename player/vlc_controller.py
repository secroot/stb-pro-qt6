"""
LibVLC Hardware-Player Controller für STB Pro Qt6.
Nutzt Qt Signals für reaktive Status- und Puffer-Updates ohne UI-Blockade.
"""
import sys
import re
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal

from core.stream_buffer import BufferSettings, StreamBufferProxy

try:
    import vlc
    VLC_AVAILABLE = True
except Exception:
    vlc = None
    VLC_AVAILABLE = False


def decode_vlc_fourcc(codec_val: Any) -> str:
    if not codec_val:
        return ""
    raw = ""
    if isinstance(codec_val, int):
        u32 = int(codec_val) & 0xFFFFFFFF
        # Known integer FourCC constants (little endian / big endian)
        fourcc_map = {
            0x34363268: "H.264 / AVC",       # 'h264'
            0x31637661: "H.264 / AVC",       # 'avc1'
            0x35363268: "HEVC / H.265",      # 'h265'
            0x63766568: "HEVC / H.265",      # 'hevc'
            0x31637668: "HEVC / H.265",      # 'hvc1'
            0x3276706D: "MPEG-2 Video",      # 'mp2v'
            0x6765706D: "MPEG-2 Video",      # 'mpeg'
            0x6134706D: "AAC-LC",            # 'mp4a'
            0x6C636161: "AAC-LC",            # 'aacl'
            0x332D6361: "Dolby Digital (AC3)", # 'ac-3'
            0x33636161: "Dolby Digital (AC3)", # 'a52 '
            0x33636165: "Dolby Digital+ (E-AC3)", # 'eac3'
            0x20737464: "DTS Audio",         # 'dts '
            0x33706D20: "MP3 Audio",         # 'mp3 '
            0x6167706D: "MP3 Audio",         # 'mpga'
            0x7375706F: "Opus",              # 'opus'
            0x43414C46: "FLAC",              # 'FLAC'
            0x30317661: "AV1",               # 'av01'
            0x30397076: "VP9",               # 'vp09'
        }
        if u32 in fourcc_map:
            return fourcc_map[u32]
        try:
            b_lit = u32.to_bytes(4, byteorder="little").decode("latin-1", errors="ignore").strip("\x00 ").lower()
            b_big = u32.to_bytes(4, byteorder="big").decode("latin-1", errors="ignore").strip("\x00 ").lower()
            raw = f"{b_lit} {b_big}"
        except Exception:
            raw = str(codec_val)
    elif isinstance(codec_val, (bytes, bytearray)):
        try:
            raw = codec_val.decode("latin-1", errors="ignore").strip("\x00 ").lower()
        except Exception:
            raw = str(codec_val)
    else:
        raw = str(codec_val).strip().lower()

    if not raw:
        return ""
    if "264" in raw or "avc" in raw:
        return "H.264 / AVC"
    if "265" in raw or "hevc" in raw or "hvc1" in raw:
        return "HEVC / H.265"
    if "mp2v" in raw or "mpeg2" in raw:
        return "MPEG-2 Video"
    if "mp4v" in raw or "mpeg4" in raw:
        return "MPEG-4 Video"
    if "vp8" in raw:
        return "VP8"
    if "vp9" in raw or "vp09" in raw:
        return "VP9"
    if "av1" in raw or "av01" in raw:
        return "AV1"
    if "aac" in raw or "mp4a" in raw or "aacl" in raw:
        return "AAC-LC"
    if "eac3" in raw or "e-ac-3" in raw:
        return "Dolby Digital+ (E-AC3)"
    if "ac3" in raw or "ac-3" in raw or "a52" in raw:
        return "Dolby Digital (AC3)"
    if "dts" in raw:
        return "DTS Audio"
    if "mp3" in raw or "mpga" in raw:
        return "MP3 Audio"
    if "mpg" in raw or "mp2a" in raw:
        return "MPEG Audio"
    if "flac" in raw:
        return "FLAC"
    if "opus" in raw:
        return "Opus"
    if "vorb" in raw:
        return "Vorbis"
    if raw.isdigit():
        return ""
    clean = re.sub(r"[^a-zA-Z0-9\-\+\s]", "", raw).strip().upper()
    return clean if len(clean) >= 2 else ""


from concurrent.futures import ThreadPoolExecutor
import threading


class VLCPlayerController(QObject):
    """
    Steuert die integrierte LibVLC-Instanz mit HWND-Binding, PCR-Ringpuffer-Proxy
    und Echtzeit-Telemetrie über Qt Signals ohne Blockade des Qt-GUI-Threads.
    """
    state_changed = Signal(str)       # "playing", "paused", "stopped"
    buffering_changed = Signal(float) # 0.0 .. 100.0

    def __init__(self, settings: Optional[BufferSettings] = None):
        super().__init__()
        self.instance = None
        self.player = None
        self.is_initialized = False
        self.is_playing = False
        self.is_muted = False
        self.volume = 100
        self.settings = (settings or BufferSettings()).clamp()
        self.proxy = StreamBufferProxy()
        self.buffer_percent = 0.0
        self.current_url = ""
        self.current_title = ""
        self.last_probe_result = None
        self._bound_hwnd: Optional[int] = None

        self._op_lock = threading.Lock()
        self._cmd_seq: int = 0
        self._transitioning: bool = False
        self._cmd_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="vlc-ctrl")
        self._cached_telemetry: Dict[str, Any] = {}

    def set_probe_result(self, probe_result: Any):
        if probe_result and getattr(probe_result, "is_alive", False):
            self.last_probe_result = probe_result

    def apply_settings(self, settings: BufferSettings):
        self.settings = settings.clamp()

    def initialize(self, hwnd: int) -> bool:
        if not VLC_AVAILABLE:
            return False

        try:
            if self.is_initialized and self.player and self._bound_hwnd == int(hwnd):
                return True

            if not self.instance:
                args = [
                    "--no-video-title-show",
                    "--http-reconnect",
                    "--quiet",
                ]
                self.instance = vlc.Instance(args)

            if not self.player:
                self.player = self.instance.media_player_new()
                try:
                    self.player.video_set_mouse_input(False)
                    self.player.video_set_key_input(False)
                except Exception:
                    pass

                try:
                    em = self.player.event_manager()

                    def _on_vlc_buffering(event):
                        try:
                            pct = float(event.u.media_player_buffering.new_cache)
                            self.buffer_percent = pct
                            self.buffering_changed.emit(pct)
                        except Exception:
                            pass

                    self._vlc_buffering_cb = _on_vlc_buffering
                    em.event_attach(vlc.EventType.MediaPlayerBuffering, self._vlc_buffering_cb)
                except Exception:
                    pass

            self.rebind_hwnd(hwnd)
            try:
                self.player.video_set_scale(0)
            except Exception:
                pass
            self.player.audio_set_volume(self.volume)
            self.is_initialized = True
            return True
        except Exception:
            self.is_initialized = False
            return False

    def rebind_hwnd(self, hwnd: int):
        if not self.player or not hwnd:
            return
        self._bound_hwnd = int(hwnd)
        if sys.platform.startswith("linux"):
            self.player.set_xwindow(self._bound_hwnd)
        elif sys.platform == "darwin":
            self.player.set_nsobject(self._bound_hwnd)
        else:
            self.player.set_hwnd(self._bound_hwnd)

    def play_url(
        self,
        url: str,
        title: str = "",
        user_agent: str = "",
        referrer: str = "",
        extra_headers: Optional[Dict[str, str]] = None,
        direct: bool = False,
        async_play: bool = True,
    ) -> bool:
        if not self.is_initialized or not self.player or not url:
            return False

        self._cmd_seq += 1
        seq = self._cmd_seq

        # Stop proxy session immediately (< 1ms) so any active local socket closes right away
        self.proxy.stop_session()

        self.current_url = url
        self.current_title = title
        self.buffer_percent = 0.0
        self.last_probe_result = None
        self._cached_telemetry = {
            "bitrate_kbps": 0.0,
            "lost_pictures": 0,
            "displayed_pictures": 0,
            "buffer_percent": 0.0,
            "width": 0,
            "height": 0,
            "fps": 0.0,
            "video_codec": "",
            "audio_codec": "",
            "audio_channels": 0,
        }
        self.is_playing = True
        self._transitioning = True
        self.state_changed.emit("playing")

        st = self.settings
        hdrs_copy = dict(extra_headers or {})

        def _do_play():
            with self._op_lock:
                if seq != self._cmd_seq or not self.player or not self.instance:
                    return
                try:
                    self.player.stop()
                except Exception:
                    pass

                if seq != self._cmd_seq:
                    return

                try:
                    play_target = url
                    caching = st.vlc_caching_ms
                    if direct:
                        caching = max(caching, 1500)
                    low = url.lower()
                    use_proxy = (
                        st.mode == "proxy"
                        and not direct
                        and low.startswith(("http://", "https://"))
                        and ".m3u8" not in low
                    )
                    if use_proxy:
                        hdrs = {"User-Agent": user_agent or "VLC/3.0.20 LibVLC/3.0.20"}
                        if referrer:
                            hdrs["Referer"] = referrer
                        hdrs.update(hdrs_copy)
                        play_target = self.proxy.open_session(url, hdrs, st)
                        caching = max(800, min(st.vlc_caching_ms, 2000))

                    if seq != self._cmd_seq:
                        self.proxy.stop_session()
                        return

                    media = self.instance.media_new(play_target)
                    if not use_proxy:
                        if user_agent:
                            media.add_option(f":http-user-agent={user_agent}")
                        if referrer:
                            media.add_option(f":http-referrer={referrer}")
                        media.add_option(":http-reconnect")

                    media.add_option(f":network-caching={caching}")
                    media.add_option(f":live-caching={caching}")
                    media.add_option(f":file-caching={caching}")
                    media.add_option(f":avcodec-hw={'any' if st.hw_decode else 'none'}")

                    self.player.set_media(media)
                    self.player.play()
                    try:
                        self.player.audio_set_volume(0 if self.is_muted else self.volume)
                    except Exception:
                        pass
                except Exception:
                    pass
                finally:
                    if seq == self._cmd_seq:
                        self._transitioning = False

        if async_play:
            try:
                self._cmd_executor.submit(_do_play)
            except Exception:
                _do_play()
        else:
            _do_play()
        return True

    def get_live_telemetry(self) -> dict:
        if not self.player:
            return {}
        res = {
            "bitrate_kbps": 0.0,
            "lost_pictures": 0,
            "displayed_pictures": 0,
            "buffer_percent": self.buffer_percent,
            "width": 0,
            "height": 0,
            "fps": 0.0,
            "video_codec": "",
            "audio_codec": "",
            "audio_channels": 0,
        }
        if self._cached_telemetry:
            res.update(self._cached_telemetry)
            res["buffer_percent"] = self.buffer_percent

        # Never block the GUI thread if a media transition is in progress
        if not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                if hasattr(self.player, "video_get_height"):
                    vh = int(self.player.video_get_height() or 0)
                    vw = int(self.player.video_get_width() or 0)
                    if vh > 0:
                        res["height"] = vh
                        res["width"] = vw
                if hasattr(self.player, "video_get_fps"):
                    vfps = float(self.player.video_get_fps() or 0.0)
                    if vfps > 0:
                        res["fps"] = round(vfps, 1)

                media = self.player.get_media()
                if media:
                    st = vlc.MediaStats()
                    try:
                        if media.get_stats(st):
                            g = lambda *n: next((getattr(st, x) for x in n if hasattr(st, x)), 0)
                            res["bitrate_kbps"] = round(float(g("input_bitrate", "f_input_bitrate")) * 8000, 1)
                            res["demux_bitrate_kbps"] = round(float(g("demux_bitrate", "f_demux_bitrate")) * 8000, 1)
                            res["lost_pictures"] = int(g("lost_pictures", "i_lost_pictures"))
                            res["displayed_pictures"] = int(g("displayed_pictures", "i_displayed_pictures"))
                    except Exception:
                        pass

                    tracks = media.tracks_get()
                    if tracks:
                        for t in tracks:
                            if t.type == vlc.TrackType.video and not res["video_codec"]:
                                v = t.video
                                if res["width"] == 0:
                                    res["width"] = int(v.width or 0)
                                if res["height"] == 0:
                                    res["height"] = int(v.height or 0)
                                if res["fps"] == 0.0 and v.frame_rate_den > 0:
                                    res["fps"] = round(v.frame_rate_num / v.frame_rate_den, 1)
                                res["video_codec"] = decode_vlc_fourcc(t.codec) or decode_vlc_fourcc(getattr(t, "original_fourcc", None))
                            elif t.type == vlc.TrackType.audio and not res["audio_codec"]:
                                a = t.audio
                                res["audio_channels"] = int(a.channels or 0)
                                res["audio_codec"] = decode_vlc_fourcc(t.codec) or decode_vlc_fourcc(getattr(t, "original_fourcc", None))

                if not res["video_codec"] and hasattr(self.player, "video_get_track_description"):
                    v_desc = self.player.video_get_track_description()
                    if v_desc:
                        for tid, name in v_desc:
                            if name and tid > 0:
                                s_name = name.decode("utf-8", errors="ignore") if isinstance(name, bytes) else str(name)
                                res["video_codec"] = decode_vlc_fourcc(s_name)
                                if res["video_codec"]:
                                    break

                if not res["audio_codec"] and hasattr(self.player, "audio_get_track_description"):
                    a_desc = self.player.audio_get_track_description()
                    if a_desc:
                        for tid, name in a_desc:
                            if name and tid > 0:
                                s_name = name.decode("utf-8", errors="ignore") if isinstance(name, bytes) else str(name)
                                res["audio_codec"] = decode_vlc_fourcc(s_name)
                                if res["audio_codec"]:
                                    break

                pr = getattr(self, "last_probe_result", None)
                if pr:
                    if not res["video_codec"] and getattr(pr, "video_codec", ""):
                        res["video_codec"] = pr.video_codec
                    if not res["audio_codec"] and getattr(pr, "audio_codec", ""):
                        res["audio_codec"] = pr.audio_codec
                        if res["audio_channels"] == 0:
                            res["audio_channels"] = getattr(pr, "audio_channels", 0) or 0

                self._cached_telemetry = dict(res)
            except Exception:
                pass
            finally:
                self._op_lock.release()

        ps = self.proxy.stats()
        if ps.get("active"):
            res["proxy"] = ps
            res["buffer_seconds"] = ps["level_s"]
            if not res["video_codec"] and ps.get("video_codec"):
                res["video_codec"] = ps["video_codec"]
            if not res["audio_codec"] and ps.get("audio_codec"):
                res["audio_codec"] = ps["audio_codec"]

        # Final robust fallbacks so active streams never display empty "—"
        if not res["video_codec"]:
            if res.get("width", 0) >= 3800 or res.get("height", 0) >= 2000:
                res["video_codec"] = "HEVC / H.265"
            elif res.get("width", 0) > 0 and res.get("height", 0) > 0:
                res["video_codec"] = "H.264 / AVC"
        if not res["audio_codec"] and (res.get("width", 0) > 0 or res.get("bitrate_kbps", 0) > 0):
            res["audio_codec"] = "AAC-LC"
            if res.get("audio_channels", 0) == 0:
                res["audio_channels"] = 2

        return res

    def toggle_play_pause(self) -> bool:
        if not self.player or self._transitioning:
            return self.is_playing
        if not self._op_lock.acquire(blocking=False):
            return self.is_playing
        try:
            if self.player.is_playing():
                self.player.pause()
                self.is_playing = False
                self.state_changed.emit("paused")
                return False
            else:
                self.player.play()
                self.is_playing = True
                self.state_changed.emit("playing")
                return True
        finally:
            self._op_lock.release()

    def stop(self, async_stop: bool = True):
        self._cmd_seq += 1
        seq = self._cmd_seq
        # Always stop the local proxy session FIRST so any blocking socket read in LibVLC aborts immediately
        self.proxy.stop_session()
        self.is_playing = False
        self._transitioning = False
        self.buffer_percent = 0.0
        self._cached_telemetry = {}
        self.state_changed.emit("stopped")

        def _do_stop():
            with self._op_lock:
                if seq != self._cmd_seq or not self.player:
                    return
                try:
                    self.player.stop()
                except Exception:
                    pass

        if async_stop:
            try:
                self._cmd_executor.submit(_do_stop)
            except Exception:
                _do_stop()
        else:
            _do_stop()

    def set_volume(self, vol: int):
        self.volume = max(0, min(100, int(vol)))
        if self.player and not self.is_muted and not self._transitioning:
            if self._op_lock.acquire(blocking=False):
                try:
                    self.player.audio_set_volume(self.volume)
                except Exception:
                    pass
                finally:
                    self._op_lock.release()

    def toggle_mute(self) -> bool:
        if not self.player:
            return False
        self.is_muted = not self.is_muted
        if not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                self.player.audio_set_volume(0 if self.is_muted else self.volume)
            except Exception:
                pass
            finally:
                self._op_lock.release()
        return self.is_muted

    def set_aspect_ratio(self, ratio_str: str):
        if not self.player or self._transitioning:
            return
        if self._op_lock.acquire(blocking=False):
            try:
                if not ratio_str or ratio_str.lower() in ("auto", "standard", "default"):
                    self.player.video_set_aspect_ratio(None)
                    self.player.video_set_scale(0)
                else:
                    self.player.video_set_aspect_ratio(ratio_str.encode("utf-8"))
            except Exception:
                pass
            finally:
                self._op_lock.release()

    def get_time(self) -> int:
        if self.player and not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                return int(self.player.get_time() or 0)
            except Exception:
                pass
            finally:
                self._op_lock.release()
        return 0

    def get_length(self) -> int:
        if self.player and not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                return int(self.player.get_length() or 0)
            except Exception:
                pass
            finally:
                self._op_lock.release()
        return 0

    def set_time(self, ms: int):
        if self.player and not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                self.player.set_time(int(ms))
            except Exception:
                pass
            finally:
                self._op_lock.release()

    def is_seekable(self) -> bool:
        if self.player and not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                return bool(self.player.is_seekable() and self.player.get_length() > 0)
            except Exception:
                return False
            finally:
                self._op_lock.release()
        return False

    def get_position(self) -> float:
        if self.player and not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                return float(self.player.get_position() or 0.0)
            except Exception:
                return 0.0
            finally:
                self._op_lock.release()
        return 0.0

    def set_position(self, frac: float):
        if self.player and not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                self.player.set_position(max(0.0, min(0.999, float(frac))))
            except Exception:
                pass
            finally:
                self._op_lock.release()

    def seek_relative(self, delta_ms: int):
        length = self.get_length()
        t = self.get_time() + int(delta_ms)
        self.set_time(max(0, min(t, max(0, length - 1000)) if length > 0 else t))

    def set_rate(self, rate: float):
        if self.player and not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                self.player.set_rate(float(rate))
            except Exception:
                pass
            finally:
                self._op_lock.release()

    def get_audio_tracks(self) -> list:
        if not self.player or self._transitioning or not self._op_lock.acquire(blocking=False):
            return []
        try:
            return [
                (i, (n.decode("utf-8", "replace") if isinstance(n, bytes) else str(n)))
                for i, n in (self.player.audio_get_track_description() or [])
                if i >= 0
            ]
        except Exception:
            return []
        finally:
            self._op_lock.release()

    def set_audio_track(self, track_id: int):
        if self.player and not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                self.player.audio_set_track(int(track_id))
            except Exception:
                pass
            finally:
                self._op_lock.release()

    def get_subtitle_tracks(self) -> list:
        if not self.player or self._transitioning or not self._op_lock.acquire(blocking=False):
            return []
        try:
            return [
                (i, (n.decode("utf-8", "replace") if isinstance(n, bytes) else str(n)))
                for i, n in (self.player.video_get_spu_description() or [])
            ]
        except Exception:
            return []
        finally:
            self._op_lock.release()

    def set_subtitle_track(self, track_id: int):
        if self.player and not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                self.player.video_set_spu(int(track_id))
            except Exception:
                pass
            finally:
                self._op_lock.release()

    def get_video_size(self):
        if self.player and not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                w, h = self.player.video_get_size(0)
                return int(w), int(h)
            except Exception:
                return (0, 0)
            finally:
                self._op_lock.release()
        return (0, 0)

    def snapshot(self, path: str) -> bool:
        if self.player and not self._transitioning and self._op_lock.acquire(blocking=False):
            try:
                return self.player.video_take_snapshot(0, path, 0, 0) == 0
            except Exception:
                return False
            finally:
                self._op_lock.release()
        return False

    def shutdown(self):
        self.stop(async_stop=False)
        self.proxy.shutdown()
        try:
            self._cmd_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        if self.player:
            try:
                self.player.release()
            except Exception:
                pass
            self.player = None
        if self.instance:
            try:
                self.instance.release()
            except Exception:
                pass
            self.instance = None
        self.is_initialized = False
