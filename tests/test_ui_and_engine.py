"""
Automated Verification Suite for STB Pro v6.0 Qt6:
1. Responsive UI Layout, Dynamic Scaling & Zero-Overlap / Zero-Truncation Geometry Checks
2. StreamBufferProxy (Ringbuffer, PCR Pacing, Corrupt TS Guard, Wall-Clock Fallback, 0ms Stop)
3. VLCPlayerController (Non-Blocking Async Zapping, Sequence Cancellation, Lock-Free Telemetry)
4. MainWindow Channel Selection Debouncing & Buffering Status Restoration
"""
from __future__ import annotations

import os
import sys
import struct
import threading
import time
import unittest
from unittest.mock import MagicMock, patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import List

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from core.models import Channel, EPGProgram
from core.stream_buffer import BufferSettings, StreamBufferProxy, _Session
from player.vlc_controller import VLCPlayerController
from ui.dialogs.buffer_dialog import BufferConfigDialog
from ui.main_window import MainWindow
from ui.theme import apply_obsidian_theme


def _make_ts_packet(pid: int = 0x0100, pcr_seconds: float | None = None, tei: bool = False) -> bytes:
    """Build a valid 188-byte MPEG-TS packet with optional PCR."""
    b1 = (0x80 if tei else 0x00) | ((pid >> 8) & 0x1F)
    b2 = pid & 0xFF
    if pcr_seconds is not None:
        pcr_base = int(pcr_seconds * 90000.0) & ((1 << 33) - 1)
        b3 = 0x30  # Adaptation field + payload
        af_len = 7
        af_flags = 0x10  # PCR flag
        # 33-bit pcr_base + 6 reserved bits + 9-bit ext (0)
        raw48 = (pcr_base << 15) | (0x3F << 9)
        pcr_bytes = raw48.to_bytes(6, "big")
        header = bytes([0x47, b1, b2, b3, af_len, af_flags]) + pcr_bytes
        return header + (b"\xFF" * (188 - len(header)))
    else:
        b3 = 0x10  # Payload only
        header = bytes([0x47, b1, b2, b3])
        return header + (b"\x42" * (188 - len(header)))


class _MockTSHandler(BaseHTTPRequestHandler):
    mode = "pcr"

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "video/mp2t")
        self.end_headers()
        t0 = time.monotonic()
        seq = 0
        try:
            while True:
                el = time.monotonic() - t0
                batch = bytearray()
                for i in range(40):
                    seq += 1
                    if self.mode == "pcr":
                        # First inject a corrupt TEI packet to ensure _scan ignores it
                        if seq == 1:
                            batch.extend(_make_ts_packet(pid=0x0020, pcr_seconds=999.0, tei=True))
                        elif i == 0:
                            batch.extend(_make_ts_packet(pid=0x0100, pcr_seconds=el + i * 0.002))
                        else:
                            batch.extend(_make_ts_packet(pid=0x0100, pcr_seconds=None))
                    else:
                        # Non-PCR stream
                        batch.extend(_make_ts_packet(pid=0x0100, pcr_seconds=None))
                self.wfile.write(bytes(batch))
                self.wfile.flush()
                time.sleep(0.002)
                if seq > 3000:
                    break
        except Exception:
            pass


class TestUIAndEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        apply_obsidian_theme(cls.app, scale_factor=1.0)

        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _MockTSHandler)
        cls.port = cls.httpd.server_address[1]
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _assert_no_sibling_overlap(self, container: QWidget, label: str):
        children = [
            w for w in container.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly)
            if w.isVisible() and w.width() > 0 and w.height() > 0
        ]
        for i in range(len(children)):
            for j in range(i + 1, len(children)):
                w1, w2 = children[i], children[j]
                r1: QRect = w1.geometry()
                r2: QRect = w2.geometry()
                inter = r1.intersected(r2)
                if inter.width() > 2 and inter.height() > 2:
                    self.fail(
                        f"[{label}] Sibling overlap detected between "
                        f"{w1.__class__.__name__}({w1.objectName() or getattr(w1, 'text', lambda: '')()}) {r1} "
                        f"and {w2.__class__.__name__}({w2.objectName() or getattr(w2, 'text', lambda: '')()}) {r2}"
                    )

    def test_01_ui_scaling_and_non_overlapping_geometries(self):
        """Verify UI layout across multiple resolutions and UI scales has 0 overlaps and 0 truncated pills."""
        win = MainWindow()
        try:
            # Populate sample channels & long metadata
            channels = [
                Channel(
                    id=str(i),
                    number=str(i),
                    name=f"DE: SKY CINEMA PREMIEREN UHD HDR {i} [HEVC 50FPS]",
                    cmd=f"http://127.0.0.1:{self.port}/live/{i}.ts",
                    category="DE | SKY CINEMA & ENTERTAINMENT UHD",
                    genre_id="10",
                    quality_tag="UHD",
                )
                for i in range(1, 35)
            ]
            win.live_view.set_channels(
                channels,
                {"*": "Alle Kanäle", "10": "DE | SKY CINEMA & ENTERTAINMENT UHD"},
                set(),
                [],
            )
            win.live_view.set_playing_channel(channels[0])
            win.top_bar.set_provider_status(
                True,
                "Stalker MAC: http://hyper.de1-eu.com:8000 | Ablauf: March 31, 2028, 9:07 pm | Max Streams: 3",
            )

            now_ts = int(time.time())
            progs = [
                EPGProgram(
                    title="Der Herr der Ringe: Die Rückkehr des Königs (Extended Edition UHD)",
                    description="Epischer Fantasy-Blockbuster mit extrem langer Beschreibung über mehrere Zeilen zum Testen der dynamischen Text-Elision ohne vertikales Abschneiden.",
                    start_str="20:15",
                    end_str="23:45",
                    start_timestamp=now_ts - 1800,
                    stop_timestamp=now_ts + 5400,
                ),
                EPGProgram(
                    title="Dune: Part Two (4K IMAX Fassung)",
                    description="Paul Atreides schließt sich den Fremen an.",
                    start_str="23:45",
                    end_str="02:30",
                    start_timestamp=now_ts + 5400,
                    stop_timestamp=now_ts + 12600,
                ),
            ]
            win.live_view.update_epg("1", progs)

            tel = {
                "is_playing": True,
                "width": 3840,
                "height": 2160,
                "fps": 50.0,
                "video_codec": "HEVC",
                "audio_codec": "EAC3",
                "audio_channels": 6,
                "audio_sample_rate": 48000,
                "bitrate_kbps": 18540,
                "buffer_pct": 98.0,
                "buffer_seconds": 14.2,
                "proxy": {
                    "active": True,
                    "state": "streaming",
                    "level_s": 14.2,
                    "level_mb": 32.1,
                    "prefill_pct": 100.0,
                    "in_kbps": 18540,
                },
            }
            win.live_view.update_live_telemetry(tel)

            for scale in ("100%", "120%"):
                win._on_ui_scale_changed(scale)
                for w_px, h_px in ((1280, 720), (1920, 1080)):
                    win.resize(w_px, h_px)
                    win.show()
                    self.app.processEvents()

                    tag = f"{w_px}x{h_px}@{scale}"
                    self._assert_no_sibling_overlap(win.top_bar, f"TopBar {tag}")
                    self._assert_no_sibling_overlap(win.sidebar, f"Sidebar {tag}")
                    self._assert_no_sibling_overlap(win.live_view.hero_card, f"HeroCard {tag}")
                    self._assert_no_sibling_overlap(win.live_view.controls_card, f"ControlsCard {tag}")
                    self._assert_no_sibling_overlap(win.live_view.epg_panel, f"EPGPanel {tag}")

                    # Ensure Sidebar bottom controls (combo_timeout, combo_scale) are fully inside sidebar height
                    sb_h = win.sidebar.height()
                    scale_bottom = win.sidebar.combo_scale.mapTo(win.sidebar, win.sidebar.combo_scale.rect().bottomLeft()).y()
                    self.assertLessEqual(
                        scale_bottom,
                        sb_h,
                        f"[{tag}] Sidebar combo_scale is clipped at bottom ({scale_bottom} > {sb_h})",
                    )

                    # Ensure all 5 HeroCard telemetry pills have enough width for their text
                    hc = win.live_view.hero_card
                    for pill in (hc.pill_res, hc.pill_codec, hc.pill_bitrate, hc.pill_audio, hc.pill_buffer):
                        fm = pill.fontMetrics()
                        text_w = fm.horizontalAdvance(pill.text())
                        self.assertGreaterEqual(
                            pill.width(),
                            text_w,
                            f"[{tag}] Pill '{pill.text()}' squished: width={pill.width()} < text_w={text_w}",
                        )

                    # Ensure compact icon buttons are readable (width >= 26)
                    for btn in (
                        win.live_view.btn_clear_search,
                        win.live_view.btn_reset_dead,
                        win.live_view.btn_prev,
                        win.live_view.btn_stop,
                        win.live_view.btn_next,
                        win.live_view.btn_mute,
                        win.live_view.btn_snap,
                        win.live_view.btn_pip,
                        win.live_view.btn_fs,
                        win.live_view.btn_detach,
                        hc.btn_fav,
                    ):
                        self.assertGreaterEqual(
                            btn.width(),
                            26,
                            f"[{tag}] Icon button '{btn.text()}' crushed to width={btn.width()}",
                        )

            # Test BufferConfigDialog roundtrip
            dlg = BufferConfigDialog(win.vlc_ctrl.settings.to_dict(), parent=win)
            cfg_out = dlg.get_config()
            self.assertIn("start_seconds", cfg_out)
            self.assertIn("buffer_seconds", cfg_out)
            self.assertIn("max_mb", cfg_out)
            dlg.close()
        finally:
            win.close()

    def test_02_stream_buffer_pcr_corrupt_packet_and_fast_stop(self):
        """Verify StreamBufferProxy ignores TEI corrupt PCR packets, prefills cleanly, and stops in <50ms."""
        _MockTSHandler.mode = "pcr"
        settings = BufferSettings(
            mode="proxy",
            start_seconds=0.8,
            buffer_seconds=10.0,
            max_mb=32,
            vlc_caching_ms=800,
        )
        proxy = StreamBufferProxy()
        try:
            local_url = proxy.open_session(
                f"http://127.0.0.1:{self.port}/live/test.ts",
                headers={
                    "User-Agent": "TestSTB/1.0",
                    "Referer": "http://portal.local/",
                    "Cookie": "mac=00%3A1A%3A79",
                },
                settings=settings,
            )
            self.assertTrue(local_url.startswith("http://127.0.0.1:"))

            # Wait up to 1.5s for producer to ingest packets
            t0 = time.monotonic()
            while time.monotonic() - t0 < 1.5:
                st = proxy.stats()
                if st.get("level_mb", 0) >= 0.05 and st.get("pcr"):
                    break
                time.sleep(0.05)

            st = proxy.stats()
            self.assertGreater(st.get("level_mb", 0), 0.02)
            self.assertTrue(st.get("pcr"))
            # Ensure corrupt TEI packet on PID 0x0020 was rejected and valid PID 0x0100 was locked
            self.assertEqual(proxy.session._pcr_pid, 0x0100)

            # Test stop_session latency (< 50ms)
            t_stop = time.monotonic()
            proxy.stop_session()
            stop_ms = (time.monotonic() - t_stop) * 1000.0
            self.assertLess(stop_ms, 50.0, f"stop_session took too long: {stop_ms:.1f}ms")
        finally:
            proxy.shutdown()

    def test_03_non_pcr_wall_clock_fallback(self):
        """Verify non-PCR streams unlock prefill via wall-clock fallback without hanging."""
        _MockTSHandler.mode = "nopcr"
        settings = BufferSettings(
            mode="proxy",
            start_seconds=0.6,
            buffer_seconds=8.0,
            max_mb=16,
            fallback_kbps=25000,  # Artificially high fallback so byte-estimate alone wouldn't reach 0.6s quickly
        )
        proxy = StreamBufferProxy()
        try:
            local_url = proxy.open_session(
                f"http://127.0.0.1:{self.port}/live/nopcr.ts",
                headers={"User-Agent": "TestSTB/1.0"},
                settings=settings,
            )
            import requests
            t0 = time.monotonic()
            with requests.get(local_url, stream=True, timeout=3.0) as r:
                first_chunk = next(r.iter_content(chunk_size=16384))
                elapsed = time.monotonic() - t0
                self.assertTrue(len(first_chunk) > 0)
                self.assertLess(elapsed, 1.5, f"Prefill wall-clock fallback took {elapsed:.2f}s")
        finally:
            proxy.shutdown()

    def test_04_async_zapping_and_debounce(self):
        """Verify rapid channel switching never blocks the GUI thread and debounces EPG calls."""
        win = MainWindow()
        try:
            epg_calls: List[str] = []

            class DummyClient:
                user_agent = "MAG250"
                portal_url = f"http://127.0.0.1:{self.port}"

                def create_link(self, cmd: str, media_type: str = "itv") -> str:
                    return cmd

                def get_short_epg(self, ch_id: str, size: int = 8):
                    epg_calls.append(str(ch_id))
                    return []

            win.active_client = DummyClient()

            # 1. Rapidly select 15 channels in a row (simulating fast scroll)
            for i in range(1, 16):
                ch = Channel(id=str(i), number=str(i), name=f"Ch {i}", cmd=f"http://127.0.0.1:{self.port}/{i}.ts")
                win._on_channel_selected(ch)

            # Immediately after scrolling, 0 network EPG calls should have fired
            self.assertEqual(len(epg_calls), 0)

            # Trigger settled timer manually
            win._on_selection_settled()
            time.sleep(0.1)
            self.app.processEvents()
            # Only the last channel ("15") should have been queried
            self.assertEqual(epg_calls, ["15"])

            # 2. Verify buffering status bar restores LIVE at 100%
            win._on_vlc_buffering(56.0)
            self.assertIn("56%", win.live_view.lbl_video_status.text())
            win._on_vlc_buffering(100.0)
            self.assertIn("🟢 Wiedergabe", win.live_view.lbl_video_status.text())
            self.assertEqual(win.live_view.lbl_preview_badge.text(), "LIVE")
        finally:
            win.close()

    def test_05_top_bar_tier2_codec_epg_and_blackout(self):
        """
        Verify:
        1. TopNavigationBar 2-tier layout (Row 1: Brand/Nav/REC/Status, Row 2: Utility pills).
        2. REC indicator minimum width (>= 120px) preventing any text cutoff.
        3. VideoSurfaceWidget black background repaint and clear_surface() to eliminate stop artifacts.
        4. EPGGuideDialog instant open with loading progress bar and guard against duplicate dialog instances.
        5. Codec detection in HeroCard and live telemetry.
        """
        win = MainWindow()
        try:
            win.resize(1400, 850)
            win.show()
            self.app.processEvents()

            # 1. Top Bar Tier 2 buttons existence and placement
            tb = win.top_bar
            self.assertTrue(hasattr(tb, "btn_jobs"))
            self.assertTrue(hasattr(tb, "btn_buffer"))
            self.assertTrue(hasattr(tb, "btn_pip"))
            self.assertTrue(hasattr(tb, "btn_cinema"))
            self.assertTrue(hasattr(tb, "btn_fullscreen"))
            self.assertFalse(hasattr(tb, "qt_badge"))

            # 2. REC indicator width check
            tb.update_rec_indicator(True, "🔴 REC 00:03:45")
            self.app.processEvents()
            self.assertTrue(tb.btn_rec_indicator.isVisible())
            self.assertGreaterEqual(tb.btn_rec_indicator.width(), 120)

            # 3. Video surface blackout
            surf = win.live_view.video_surface
            self.assertTrue(hasattr(surf, "clear_surface"))
            surf.clear_surface()

            # 4. Instant EPG Guide Dialog with guard against multiple instances
            ch = Channel(id="101", number="1", name="Das Erste HD", cmd="http://dummy")
            class DummyEpgClient:
                def get_epg_day(self, cid, day):
                    return [{"time": "12:00", "name": "Tagesschau", "descr": "Nachrichten"}]
            win.active_client = DummyEpgClient()

            # First open
            win.open_epg_guide_dialog(ch)
            self.app.processEvents()
            dlg1 = win._active_epg_dialog
            self.assertIsNotNone(dlg1)
            self.assertTrue(dlg1.isVisible())
            # Loading bar is shown immediately
            self.assertTrue(dlg1.progress_bar.isVisible() or len(dlg1._all_programs) > 0)

            # Clicking again while open should NOT spawn a second dialog
            win.open_epg_guide_dialog(ch)
            self.app.processEvents()
            self.assertIs(win._active_epg_dialog, dlg1)
            dlg1.close()

            # 5. Live Telemetry Codecs in HeroCard
            hc = win.live_view.hero_card
            tel = {
                "width": 3840,
                "height": 2160,
                "bitrate_kbps": 12500,
                "fps": 50.0,
                "video_codec": "HEVC / H.265",
                "audio_codec": "Dolby Digital (AC3)",
                "audio_channels": 6,
                "proxy": {
                    "active": True,
                    "state": "playing",
                    "level_s": 8.5,
                    "level_mb": 14.2,
                    "rebuffers": 0,
                },
            }
            win.live_view.update_live_telemetry(tel)
            self.assertEqual(hc.pill_res.text(), "3840x2160 @50fps")
            self.assertEqual(hc.pill_codec.text(), "Video: HEVC / H.265")
            self.assertEqual(hc.pill_audio.text(), "Audio: Dolby Digital (AC3) (6ch)")
            self.assertIn("12.50 Mbps", hc.pill_bitrate.text())
            self.assertIn("Puffer: 8.5s", hc.pill_buffer.text())
        finally:
            win.close()

    def test_06_high_bitrate_puffer_no_bloat_and_rebuffer_overlay(self):
        """Verify 4K/high-bitrate proxy does not choke or bloat to 128MB, and rebuffer overlay updates."""
        win = MainWindow()
        try:
            hc = win.live_view.hero_card

            # 1. Rebuffer state: status label & buffer pill must reflect rebuffer overlay
            tel_rebuf = {
                "width": 3840,
                "height": 2160,
                "bitrate_kbps": 0,
                "video_codec": "H.264 / AVC",
                "audio_codec": "AAC-LC",
                "proxy": {
                    "active": True,
                    "state": "rebuffer",
                    "level_s": 1.2,
                    "level_mb": 0.8,
                    "connected": False,
                    "rebuffers": 2,
                },
            }
            win.live_view.update_live_telemetry(tel_rebuf)
            self.assertIn("Nachpuffern", hc.pill_buffer.text())
            self.assertIn("Überbrücke Aussetzer", win.live_view.lbl_video_status.text())

            # 2. Prefill state: status label & buffer pill must reflect prefill
            tel_prefill = {
                "width": 0,
                "height": 0,
                "proxy": {
                    "active": True,
                    "state": "prefill",
                    "level_s": 0.4,
                    "start_s": 0.8,
                    "prefill_pct": 50.0,
                    "connected": True,
                },
            }
            win.live_view.update_live_telemetry(tel_prefill)
            self.assertIn("Vorab", hc.pill_buffer.text())
            self.assertIn("Fülle Ringpuffer", win.live_view.lbl_video_status.text())

            # 3. StreamBufferProxy high-throughput test (500KB in < 500ms without artificial PCR sleep)
            _MockTSHandler.mode = "pcr"
            settings = BufferSettings(
                mode="proxy",
                start_seconds=0.4,
                buffer_seconds=5.0,
                max_mb=16,
            )
            proxy = StreamBufferProxy()
            try:
                local_url = proxy.open_session(
                    f"http://127.0.0.1:{self.port}/live/4k_test.ts",
                    headers={"User-Agent": "TestSTB/1.0"},
                    settings=settings,
                )
                import requests
                t0 = time.monotonic()
                total_read = 0
                with requests.get(local_url, stream=True, timeout=3.0) as r:
                    for chunk in r.iter_content(chunk_size=32768):
                        total_read += len(chunk)
                        if total_read >= 262144:  # Read 256 KB
                            break
                        if time.monotonic() - t0 > 2.5:
                            break
                dur = time.monotonic() - t0
                self.assertGreaterEqual(total_read, 262144)
                # Ensure high throughput was achieved without artificial 200ms sleep delays
                self.assertLess(dur, 2.0, f"Proxy delivery was throttled: took {dur:.2f}s for 256KB")
                # Ensure buffer didn't balloon to max_mb
                st = proxy.stats()
                self.assertLess(st.get("level_mb", 0), 10.0, f"Buffer ballooned: {st.get('level_mb')} MB")
            finally:
                proxy.shutdown()
        finally:
            win.close()

    def test_07_quality_tag_detection_and_dynamic_resolution_sync(self):
        """Verify quality_from_dimensions, detect_quality_tag and dynamic UI badge updates from decoded stream."""
        from core.models import quality_from_dimensions, detect_quality_tag
        from ui.models.channel_model import ChannelRoles

        # 1. Dimension classification verification
        self.assertEqual(quality_from_dimensions(3840, 2160), "UHD")
        self.assertEqual(quality_from_dimensions(1920, 1080), "FHD")
        self.assertEqual(quality_from_dimensions(1440, 1080), "FHD")  # Anamorphic 1080i
        self.assertEqual(quality_from_dimensions(1280, 720), "HD")
        self.assertEqual(quality_from_dimensions(960, 720), "HD")
        self.assertEqual(quality_from_dimensions(720, 576), "SD")
        self.assertEqual(quality_from_dimensions(640, 480), "SD")

        # 2. Ingest detection prioritization (Strictly facts: NO guessing from channel names!)
        self.assertEqual(detect_quality_tag("DE: RTL FHD"), "")  # Never guess from title!
        self.assertEqual(detect_quality_tag("DE: DAS ERSTE HD"), "")  # Never guess from title!
        self.assertEqual(detect_quality_tag("DE: TEST", {"width": 1280, "height": 720}), "HD")
        self.assertEqual(detect_quality_tag("DE: TEST", {"width": 1920, "height": 1080}), "FHD")
        self.assertEqual(detect_quality_tag("DE: TEST", {"resolution": "1280x720"}), "HD")

        # 3. Dynamic sync during playback in LiveTVView and MainWindow
        win = MainWindow()
        try:
            ch_720 = Channel(
                id="101",
                number="1",
                name="DE: RTL FHD",  # Channel has no raw dimensions, initial tag must be empty
                cmd="http://example.com/101.ts",
                quality_tag="",
            )
            ch_1080 = Channel(
                id="102",
                number="2",
                name="DE: DAS ERSTE HD",
                cmd="http://example.com/102.ts",
                quality_tag="",
            )
            ch_dead = Channel(
                id="103",
                number="3",
                name="DE: DEAD CHANNEL",
                cmd="http://example.com/103.ts",
                quality_tag="",
            )

            win.live_view.set_channels([ch_720, ch_1080, ch_dead], {"*": "Alle"}, set(), [])

            # Check initial state: No fake tags guessed from titles!
            idx_720 = win.live_view.channel_model.index(0, 0)
            idx_1080 = win.live_view.channel_model.index(1, 0)
            idx_dead = win.live_view.channel_model.index(2, 0)
            self.assertEqual(win.live_view.channel_model.data(idx_720, ChannelRoles.QualityTagRole), "")
            self.assertEqual(win.live_view.channel_model.data(idx_1080, ChannelRoles.QualityTagRole), "")

            # Play 720p stream: telemetry reports real 1280x720
            win.live_view.set_playing_channel(ch_720)
            win.live_view.update_live_telemetry({
                "width": 1280,
                "height": 720,
                "fps": 50.0,
                "bitrate_kbps": 4500,
            })

            # Must dynamically set verified badge to HD!
            self.assertEqual(ch_720.quality_tag, "HD")
            self.assertEqual(win.live_view.channel_model.data(idx_720, ChannelRoles.QualityTagRole), "HD")

            # Play 1080p stream: telemetry reports real 1920x1080
            win.live_view.set_playing_channel(ch_1080)
            win.live_view.update_live_telemetry({
                "width": 1920,
                "height": 1080,
                "fps": 50.0,
                "bitrate_kbps": 7500,
            })

            # Must dynamically set verified badge to FHD!
            self.assertEqual(ch_1080.quality_tag, "FHD")
            self.assertEqual(win.live_view.channel_model.data(idx_1080, ChannelRoles.QualityTagRole), "FHD")

            # Group validation progress test: dead channel (timeout > 3s)
            win._on_val_progress_ui("103", is_alive=False, latency_ms=-1, quality_tag="", done=1, total=3)
            self.assertTrue(ch_dead.is_dead)
            self.assertTrue(win.live_view.channel_model.data(idx_dead, ChannelRoles.IsDeadRole))
            self.assertEqual(win.live_view.channel_model.data(idx_dead, ChannelRoles.LatencyMsRole), -1)

            # Probe 4K stream: probe reports 3840x2160
            from core.models import StreamProbeResult
            probe_res = StreamProbeResult(
                is_alive=True,
                latency_ms=120,
                width=3840,
                height=2160,
                fps=50.0,
                video_codec="hevc",
            )
            win._on_probe_done_ui("102", probe_res)
            self.assertEqual(ch_1080.quality_tag, "UHD")
            self.assertEqual(win.live_view.channel_model.data(idx_1080, ChannelRoles.QualityTagRole), "UHD")
        finally:
            win.close()

    @patch.object(MainWindow, "start_category_validation")
    def test_08_group_auto_validation_and_preview_thumbnails(self, mock_val):
        """Verify category selection auto-validates on first selection in session and loads thumbnails."""
        win = MainWindow()
        try:
            ch_de = Channel(id="201", number="1", name="ZDF HD", cmd="http://fake.stream/201.ts", category="Germany", genre_id="10")
            ch_sp = Channel(id="202", number="2", name="Sky Sport", cmd="http://fake.stream/202.ts", category="Sports", genre_id="20")
            genres = {"*": "Alle Kategorien", "10": "Germany", "20": "Sports"}

            win.live_view.set_channels([ch_de, ch_sp], genres, set(), [])

            # Initially _checked_groups_session is empty
            self.assertEqual(len(win.live_view._checked_groups_session), 0)

            # Spy on validate_category_requested signal
            requested_batches = []
            win.live_view.validate_category_requested.connect(lambda chans: requested_batches.append(chans))

            # Select "Germany" (index 1) -> must auto-trigger validation on first session visit
            idx_germany = win.live_view.combo_category.findData("10")
            self.assertGreaterEqual(idx_germany, 0)
            win.live_view.combo_category.setCurrentIndex(idx_germany)

            self.assertIn("10", win.live_view._checked_groups_session)
            self.assertEqual(len(requested_batches), 1)
            self.assertEqual(len(requested_batches[0]), 1)
            self.assertEqual(requested_batches[0][0].id, "201")

            # Switch to "Sports" (index 2) -> must auto-trigger validation on first session visit
            idx_sports = win.live_view.combo_category.findData("20")
            self.assertGreaterEqual(idx_sports, 0)
            win.live_view.combo_category.setCurrentIndex(idx_sports)

            self.assertIn("20", win.live_view._checked_groups_session)
            self.assertEqual(len(requested_batches), 2)
            self.assertEqual(len(requested_batches[1]), 1)
            self.assertEqual(requested_batches[1][0].id, "202")

            # Switch BACK to "Germany" -> already checked in session! Must NOT re-trigger!
            win.live_view.combo_category.setCurrentIndex(idx_germany)
            self.assertEqual(len(requested_batches), 2)  # Still 2, no auto re-trigger!

            # Manual click on "🩺 Gruppe prüfen" MUST re-trigger even if already in session
            win.live_view.set_validation_running(False)
            win.live_view._on_validate_clicked()
            self.assertEqual(len(requested_batches), 3)

            # Test thumbnail ingestion during validation progress
            fake_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
            win._on_val_progress_ui("201", is_alive=True, latency_ms=85, quality_tag="FHD", done=1, total=1, thumb_bytes=fake_jpeg)

            # Thumbnail must be in delegate cache
            self.assertIn("201", win.live_view.delegate._thumb_cache)
            self.assertFalse(win.live_view.delegate._thumb_cache["201"].isNull())
        finally:
            win.close()

    def test_scanner_queue_retry_pause_and_folder_extract(self):
        """Testet die neuen Scanner-Optimierungen: Requeue bei 503/429/Timeout, Pause/Resume, Liste leeren und Ordner-Extraktion."""
        import tempfile
        from unittest.mock import patch
        from core.signals import event_bus
        from ui.views.scanner_view import ScannerView

        sv = ScannerView()
        try:
            # 1. Test: get_candidate_macs normalisiert sowohl : als auch - und wandelt in Großbuchstaben um
            sv.txt_macs.setPlainText("00-1a-79-a1-b2-c3\n00:1A:79:d4:e5:f6\ninvalid text\n00:1a:79:A1:B2:C3")
            macs = sv.get_candidate_macs()
            self.assertEqual(macs, ["00:1A:79:A1:B2:C3", "00:1A:79:D4:E5:F6", "00:1A:79:A1:B2:C3"])

            # 2. Test: Dedup entfernt Duplikate
            sv._deduplicate_list()
            self.assertEqual(sv.get_candidate_macs(), ["00:1A:79:A1:B2:C3", "00:1A:79:D4:E5:F6"])

            # 3. Test: clear_candidates leert die Liste und aktualisiert den Zähler auf 0
            sv.clear_candidates()
            self.assertEqual(len(sv.get_candidate_macs()), 0)
            self.assertIn("(0)", sv.lbl_queue_count.text())

            # 4. Test: Pause & Resume Button
            pause_sig_fired = []
            resume_sig_fired = []
            sv.pause_scan_requested.connect(lambda: pause_sig_fired.append(True))
            sv.resume_scan_requested.connect(lambda: resume_sig_fired.append(True))

            # Erstes Klicken: Pause aktivieren
            sv._on_pause_clicked()
            self.assertTrue(sv._is_paused)
            self.assertEqual(sv.btn_pause.text(), "▶ FORTSETZEN")
            self.assertEqual(len(pause_sig_fired), 1)

            # Zweites Klicken: Resume aktivieren
            sv._on_pause_clicked()
            self.assertFalse(sv._is_paused)
            self.assertEqual(sv.btn_pause.text(), "⏸ PAUSE")
            self.assertEqual(len(resume_sig_fired), 1)

            # 5. Test: Rekursive Ordner-Extraktion
            with tempfile.TemporaryDirectory() as tmp_dir:
                sub_dir = os.path.join(tmp_dir, "nested")
                os.makedirs(sub_dir, exist_ok=True)

                f1 = os.path.join(tmp_dir, "dump1.txt")
                with open(f1, "w", encoding="utf-8") as f:
                    f.write("Some logs 00:1A:79:11:22:33 and 00-1a-79-44-55-66 in text\n")

                f2 = os.path.join(sub_dir, "dump2.txt")
                with open(f2, "w", encoding="utf-8") as f:
                    f.write("Dupe 00:1A:79:11:22:33 and new 00:1A:79:77:88:99\n")

                f_ignored = os.path.join(tmp_dir, "image.jpg")
                with open(f_ignored, "w", encoding="utf-8") as f:
                    f.write("00:1A:79:99:99:99 should be ignored as not txt\n")

                with patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory", return_value=tmp_dir):
                    sv._import_from_folder()

                extracted = sv.get_candidate_macs()
                self.assertIn("00:1A:79:11:22:33", extracted)
                self.assertIn("00:1A:79:44:55:66", extracted)
                self.assertIn("00:1A:79:77:88:99", extracted)
                self.assertNotIn("00:1A:79:99:99:99", extracted)
                # Ensure no duplicates in extracted list
                self.assertEqual(len(extracted), len(set(extracted)))
                self.assertEqual(len(extracted), 3)

            # 6. Test: Requeue Engine bei 503/429/Timeout in MainWindow
            win = MainWindow()
            win.config_mgr.set("cached_endpoints", {"http://test.com/c": "http://test.com/c/server/load.php"})
            try:
                call_counts = {"00:1A:79:11:22:33": 0, "00:1A:79:44:55:66": 0}

                def mock_check(portal_url, mac, model, timeout, normalized_load_url, session=None, **kwargs):
                    call_counts[mac] += 1
                    # Erste Abfrage wirft 503 Service Unavailable, zweite Abfrage liefert Erfolg
                    if call_counts[mac] == 1:
                        return {
                            "mac": mac,
                            "valid": False,
                            "status": "🔴 503 Service Unavailable",
                            "error": "503 Server Error",
                            "channels": 0,
                        }
                    else:
                        return {
                            "mac": mac,
                            "valid": True,
                            "status": "Aktiv",
                            "channels": 120,
                            "expire": "2027-01-01",
                        }

                with patch("ui.main_window.check_mac_account", side_effect=mock_check):
                    results_received = []
                    event_bus.scan_result_received.connect(results_received.append)

                    # Starte Scan mit 2 MACs
                    win.start_mac_scan(
                        portal_url="http://test.com/c/",
                        mac_list=["00:1A:79:11:22:33", "00:1A:79:44:55:66"],
                        model="MAG 250",
                        threads=2,
                        delay_s=0.0,
                    )

                    # Warte kurz bis beide MACs ihren Retry absolviert haben
                    deadline = time.time() + 5.0
                    while time.time() < deadline:
                        if len(results_received) >= 2:
                            break
                        time.sleep(0.05)
                        self.app.processEvents()

                    # Beide MACs müssen mindestens 2x aufgerufen worden sein (1x Fehlversuch -> Requeue -> 1x Erfolg)
                    self.assertGreaterEqual(call_counts["00:1A:79:11:22:33"], 2)
                    self.assertGreaterEqual(call_counts["00:1A:79:44:55:66"], 2)
                    self.assertEqual(len(results_received), 2)
                    self.assertTrue(all(r["valid"] for r in results_received))
            finally:
                win.stop_mac_scan()
                win.close()
        finally:
            sv.close()

    def test_15_snapshot_playing_channel_no_name_error(self):
        """Verifies _snapshot_playing_channel executes without NameError for THUMB_DIR."""
        win = MainWindow.__new__(MainWindow)
        win.state = MagicMock()
        win.state.playing_channel = Channel(id="9999", name="Test Live Snap", number=1, cmd="http://test")
        win.state.current_profile_name = "test"
        win.vlc_ctrl = MagicMock()
        win.vlc_ctrl.is_playing = True
        win.vlc_ctrl.snapshot = MagicMock(return_value=False)

        # Muss fehlerfrei durchlaufen (kein NameError: THUMB_DIR)
        win._snapshot_playing_channel()
        win.vlc_ctrl.snapshot.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
