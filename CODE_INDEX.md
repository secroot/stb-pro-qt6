# 📑 STB Pro Qt6 — Vollständiges Code-Register & Symbol-Index

> **Wichtig für Entwickler & AI-Agents**: Dieses Register wird automatisiert durch `tools/generate_code_index.py` gepflegt. Bevor Dateien im Repository blind durchsucht werden, immer zuerst diesen Index konsultieren, um Funktionssignaturen, Zeilennummern und Architektur-Zuständigkeiten direkt anzusteuern.

---

## 🧭 Inhaltsverzeichnis
1. [Alphabetisches Master-Symbolverzeichnis](#alphabetisches-master-symbolverzeichnis)
- [Clients (Protokolle & APIs)](#clients-protokolle--apis)
- [Core (Business Logic, Cache & DB)](#core-business-logic,-cache--db)
- [Player & Engine (VLC, Proxy & OSD)](#player--engine-vlc,-proxy--osd)
- [UI - Hauptfenster & Theme](#ui---hauptfenster--theme)
- [UI - Views & Workspaces](#ui---views--workspaces)
- [UI - Komponenten & Controls](#ui---komponenten--controls)
- [UI - Dialoge & Overlays](#ui---dialoge--overlays)
- [UI - Virtuelle Models & Delegates](#ui---virtuelle-models--delegates)
- [Automatisierte Test-Suiten](#automatisierte-test-suiten)
- [Einstiegspunkt](#einstiegspunkt)

---

## 🔍 Alphabetisches Master-Symbolverzeichnis

| Symbol | Typ | Datei | Zeilen | Kurzbeschreibung |
| :--- | :---: | :--- | :---: | :--- |
| `_AsyncTask` | **Class / Widget** | [core/signals.py](core/signals.py#L35-L63) | `L35-L63` | Kapselt eine beliebige Funktion für den globalen QThreadPool. |
| `_attach_inspector_hook` | **Function** | [clients/stb_client.py](clients/stb_client.py#L27-L58) | `L27-L58` | def _attach_inspector_hook(session, enable) |
| `_BottomHudBar` | **Class / Widget** | [player/osd_overlay.py](player/osd_overlay.py#L84-L194) | `L84-L194` | Basis: QWidget |
| `_ChannelDrawerOverlay` | **Class / Widget** | [player/osd_overlay.py](player/osd_overlay.py#L197-L275) | `L197-L275` | Basis: QWidget |
| `_cmd` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L99-L113) | `L99-L113` | def _cmd(url, headers, width, tail) |
| `_Handler` | **Class / Widget** | [core/stream_buffer.py](core/stream_buffer.py#L551-L582) | `L551-L582` | Basis: BaseHTTPRequestHandler |
| `_HLSDetected` | **Class / Widget** | [core/recorder.py](core/recorder.py#L23-L26) | `L23-L26` | Basis: Exception |
| `_make_ts_packet` | **Function** | [tests/test_ui_and_engine.py](tests/test_ui_and_engine.py#L34-L51) | `L34-L51` | Build a valid 188-byte MPEG-TS packet with optional PCR. |
| `_MockTSHandler` | **Class / Widget** | [tests/test_ui_and_engine.py](tests/test_ui_and_engine.py#L54-L87) | `L54-L87` | Basis: BaseHTTPRequestHandler |
| `_normalize_stb_model` | **Function** | [ui/dialogs/profile_dialog.py](ui/dialogs/profile_dialog.py#L34-L41) | `L34-L41` | def _normalize_stb_model(model_str) |
| `_on_response` | **Function** | [clients/stb_client.py](clients/stb_client.py#L31-L56) | `L31-L56` | def _on_response(resp) |
| `_parse_json` | **Function** | [core/stream_probe.py](core/stream_probe.py#L549-L570) | `L549-L570` | def _parse_json(parsed) |
| `_Session` | **Class / Widget** | [core/stream_buffer.py](core/stream_buffer.py#L68-L548) | `L68-L548` | Basis:  |
| `_TopHudBar` | **Class / Widget** | [player/osd_overlay.py](player/osd_overlay.py#L16-L81) | `L16-L81` | Basis: QWidget |
| `_WorkerSignals` | **Class / Widget** | [core/signals.py](core/signals.py#L30-L32) | `L30-L32` | Basis: QObject |
| `AppEventBus` | **Class / Widget** | [core/signals.py](core/signals.py#L10-L27) | `L10-L27` | Zentraler Signal-Bus für die gesamte Applikation. |
| `apply_obsidian_theme` | **Function** | [ui/theme.py](ui/theme.py#L465-L499) | `L465-L499` | Apply dark QPalette and Obsidian Cyber-Cinema QSS stylesheet with dynamic UI scaling. |
| `AppState` | **Class / Widget** | [core/models.py](core/models.py#L536-L558) | `L536-L558` | Zentraler Laufzeit-Zustand der Anwendung. |
| `AsyncWorkerPool` | **Class / Widget** | [core/signals.py](core/signals.py#L66-L111) | `L66-L111` | Hochperformanter Thread-Pool auf Basis von Qt QThreadPool. |
| `BufferConfigDialog` | **Class / Widget** | [ui/dialogs/buffer_dialog.py](ui/dialogs/buffer_dialog.py#L23-L169) | `L23-L169` | Basis: QDialog |
| `BufferSettings` | **Class / Widget** | [core/stream_buffer.py](core/stream_buffer.py#L22-L65) | `L22-L65` | Basis:  |
| `build_m3u_playlist` | **Function** | [core/m3u_exporter.py](core/m3u_exporter.py#L10-L44) | `L10-L44` | def build_m3u_playlist(channels, user_agent, resolve_url_fn) |
| `Channel` | **Class / Widget** | [core/models.py](core/models.py#L62-L167) | `L62-L167` | Basis:  |
| `ChannelCardDelegate` | **Class / Widget** | [ui/models/channel_model.py](ui/models/channel_model.py#L284-L580) | `L284-L580` | Custom QPainter delegate rendering sleek, GPU-accelerated channel cards: |
| `ChannelFilterProxyModel` | **Class / Widget** | [ui/models/channel_model.py](ui/models/channel_model.py#L213-L281) | `L213-L281` | Zero-allocation filter proxy supporting Category, Search, Favorites, Recent, HD/4K, and De... |
| `ChannelListModel` | **Class / Widget** | [ui/models/channel_model.py](ui/models/channel_model.py#L51-L210) | `L51-L210` | High-performance backing model for 50,000+ Live TV channels. |
| `ChannelRoles` | **Class / Widget** | [ui/models/channel_model.py](ui/models/channel_model.py#L33-L48) | `L33-L48` | Basis:  |
| `check_mac_account` | **Function** | [clients/stb_client.py](clients/stb_client.py#L94-L119) | `L94-L119` | Prüft einen einzelnen MAC-Account schnell im Hintergrund (ohne Inspector-Spam). |
| `ConfigManager` | **Class / Widget** | [core/config_manager.py](core/config_manager.py#L60-L253) | `L60-L253` | Verwaltet Profile, Live-/VOD-Favoriten, Verlauf, Player-Pfade und UI-Einstellungen. |
| `ConsoleView` | **Class / Widget** | [ui/views/console_view.py](ui/views/console_view.py#L26-L156) | `L26-L156` | Basis: QWidget |
| `decode_vlc_fourcc` | **Function** | [player/vlc_controller.py](player/vlc_controller.py#L20-L101) | `L20-L101` | def decode_vlc_fourcc(codec_val) |
| `detect_ffplay_path` | **Function** | [core/config_manager.py](core/config_manager.py#L48-L57) | `L48-L57` | def detect_ffplay_path() |
| `detect_mpv_path` | **Function** | [core/config_manager.py](core/config_manager.py#L36-L45) | `L36-L45` | def detect_mpv_path() |
| `detect_quality_tag` | **Function** | [core/models.py](core/models.py#L31-L58) | `L31-L58` | Erkennt den Qualitäts-Tag AUSSCHLIESSLICH anhand von echten Dimensionsdaten in den Metadat... |
| `detect_stream_error_payload` | **Function** | [core/stream_probe.py](core/stream_probe.py#L332-L399) | `L332-L399` | Erkennt versteckte Fehler-Payloads (z. B. IP_BAN, ISP_LOCK_FAILED, Geo-Blocks), |
| `detect_vlc_path` | **Function** | [core/config_manager.py](core/config_manager.py#L19-L33) | `L19-L33` | def detect_vlc_path() |
| `diagnose_iptv_status` | **Function** | [core/stream_probe.py](core/stream_probe.py#L311-L329) | `L311-L329` | Diagnostiziert proprietäre/spezifische HTTP-Statuscodes von IPTV- und Streaming-Clustern. |
| `EPGGuideDialog` | **Class / Widget** | [ui/dialogs/epg_guide_dialog.py](ui/dialogs/epg_guide_dialog.py#L31-L245) | `L31-L245` | Basis: QDialog |
| `EPGPanel` | **Class / Widget** | [ui/components/epg_panel.py](ui/components/epg_panel.py#L26-L192) | `L26-L192` | Basis: QFrame |
| `EPGProgram` | **Class / Widget** | [core/models.py](core/models.py#L171-L329) | `L171-L329` | Basis:  |
| `ExternalPlayerRunner` | **Class / Widget** | [player/external_player.py](player/external_player.py#L11-L115) | `L11-L115` | Basis:  |
| `extract_resolution_from_hls_text` | **Function** | [core/stream_probe.py](core/stream_probe.py#L274-L289) | `L274-L289` | Extrahiert RESOLUTION=WxH direkt aus HLS-Playlists. |
| `extract_thumbnail_from_ts` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L64-L96) | `L64-L96` | Extrahiert blitzschnell (0.1s) genau ein Frame aus bereits heruntergeladenen MPEG-TS Bytes... |
| `extract_video_info_from_ts` | **Function** | [core/stream_probe.py](core/stream_probe.py#L211-L271) | `L211-L271` | Scannt MPEG-TS Pakete nach H.264/H.265 SPS in Millisekunden. |
| `extract_vod_quality` | **Function** | [ui/models/vod_model.py](ui/models/vod_model.py#L47-L55) | `L47-L55` | def extract_vod_quality(item) |
| `extract_vod_rating` | **Function** | [ui/models/vod_model.py](ui/models/vod_model.py#L36-L44) | `L36-L44` | def extract_vod_rating(item) |
| `extract_vod_title` | **Function** | [ui/models/vod_model.py](ui/models/vod_model.py#L27-L28) | `L27-L28` | def extract_vod_title(item) |
| `extract_vod_year` | **Function** | [ui/models/vod_model.py](ui/models/vod_model.py#L31-L33) | `L31-L33` | def extract_vod_year(item) |
| `find_ffmpeg` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L15-L29) | `L15-L29` | def find_ffmpeg() |
| `find_ffmpeg` | **Function** | [core/recorder.py](core/recorder.py#L34-L52) | `L34-L52` | def find_ffmpeg() |
| `find_ffprobe` | **Function** | [core/stream_probe.py](core/stream_probe.py#L17-L31) | `L17-L31` | def find_ffprobe() |
| `format_codec_name` | **Function** | [core/stream_probe.py](core/stream_probe.py#L69-L85) | `L69-L85` | def format_codec_name(codec) |
| `format_mac_str` | **Function** | [core/mac_database.py](core/mac_database.py#L19-L23) | `L19-L23` | def format_mac_str(mac) |
| `format_resolution` | **Function** | [core/stream_probe.py](core/stream_probe.py#L88-L104) | `L88-L104` | def format_resolution(width, height, fps) |
| `FullscreenOSDOverlay` | **Class / Widget** | [player/osd_overlay.py](player/osd_overlay.py#L278-L396) | `L278-L396` | Koordiniert Top-HUD, Bottom-HUD, Uhrzeit-Timer, Auto-Hide und den Quick-Channel-Drawer. |
| `grab_thumbnail` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L216-L280) | `L216-L280` | High-Performance Standalone Thumbnail Grabber. |
| `HeroCard` | **Class / Widget** | [ui/components/hero_card.py](ui/components/hero_card.py#L25-L283) | `L25-L283` | Basis: QFrame |
| `HttpLogEntry` | **Class / Widget** | [core/models.py](core/models.py#L492-L533) | `L492-L533` | Basis:  |
| `InspectorView` | **Class / Widget** | [ui/views/inspector_view.py](ui/views/inspector_view.py#L32-L262) | `L32-L262` | Basis: QWidget |
| `is_blank_or_black_jpeg` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L40-L61) | `L40-L61` | Erkennt korrupte, leere oder rein schwarze Dummy-Frames zuverlässig. |
| `is_ip_or_stream_ban` | **Function** | [core/stream_probe.py](core/stream_probe.py#L295-L308) | `L295-L308` | Ermittelt zuverlässig, ob ein HTTP-Statuscode oder Fehlertext auf |
| `Job` | **Class / Widget** | [core/recorder.py](core/recorder.py#L56-L118) | `L56-L118` | Basis:  |
| `JobsDialog` | **Class / Widget** | [ui/dialogs/jobs_dialog.py](ui/dialogs/jobs_dialog.py#L25-L135) | `L25-L135` | Basis: QDialog |
| `JsonViewerDialog` | **Class / Widget** | [ui/dialogs/json_viewer_dialog.py](ui/dialogs/json_viewer_dialog.py#L27-L119) | `L27-L119` | Basis: QDialog |
| `LiveTVView` | **Class / Widget** | [ui/views/live_tv_view.py](ui/views/live_tv_view.py#L155-L1199) | `L155-L1199` | Basis: QWidget |
| `load_cached_thumb` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L120-L133) | `L120-L133` | def load_cached_thumb(key) |
| `LogoCache` | **Class / Widget** | [core/logo_cache.py](core/logo_cache.py#L22-L151) | `L22-L151` | Lädt Kanal-Logos und VOD-Poster im Hintergrund als QImage (Thread-sicher!) |
| `MacDatabase` | **Class / Widget** | [core/mac_database.py](core/mac_database.py#L26-L238) | `L26-L238` | Persistente, threadsichere Datenbank für gefundene MAC-Adressen mit Sendern. |
| `MacDatabaseDialog` | **Class / Widget** | [ui/dialogs/mac_db_dialog.py](ui/dialogs/mac_db_dialog.py#L31-L211) | `L31-L211` | Basis: QDialog |
| `main` | **Function** | [main.py](main.py#L22-L54) | `L22-L54` | def main() |
| `MainWindow` | **Class / Widget** | [ui/main_window.py](ui/main_window.py#L87-L2789) | `L87-L2789` | Basis: QMainWindow |
| `NordVpnManager` | **Class / Widget** | [core/vpn_manager.py](core/vpn_manager.py#L21-L519) | `L21-L519` | Verwaltet die Integration mit NordVPN unter Windows. |
| `parse_sps_from_h264` | **Function** | [core/stream_probe.py](core/stream_probe.py#L107-L208) | `L107-L208` | Decodiert H.264 Sequence Parameter Set (SPS) direkt in (width, height) ohne externe Tools. |
| `pcr_bitrate_kbps` | **Function** | [core/stream_probe.py](core/stream_probe.py#L38-L66) | `L38-L66` | Echte Mux-Bitrate aus MPEG-TS-PCR. |
| `PreviewOverlayWidget` | **Class / Widget** | [ui/views/live_tv_view.py](ui/views/live_tv_view.py#L86-L152) | `L86-L152` | Standbild-Preview Thumbnail Overlay displayed inside the video viewport when |
| `probe_stream` | **Function** | [core/stream_probe.py](core/stream_probe.py#L402-L614) | `L402-L614` | def probe_stream(url, user_agent, cookies, timeout, sample_duration, cancel, skip_ffprobe,... |
| `Profile` | **Class / Widget** | [core/models.py](core/models.py#L333-L452) | `L333-L452` | Basis:  |
| `ProfileEditorDialog` | **Class / Widget** | [ui/dialogs/profile_dialog.py](ui/dialogs/profile_dialog.py#L44-L308) | `L44-L308` | Basis: QDialog |
| `quality_from_dimensions` | **Function** | [core/models.py](core/models.py#L13-L28) | `L13-L28` | Ermittelt den Qualitäts-Tag (UHD/FHD/HD/SD) exakt anhand von Pixel-Dimensionen. |
| `read_bit` | **Function** | [core/stream_probe.py](core/stream_probe.py#L124-L133) | `L124-L133` | def read_bit() |
| `read_bits` | **Function** | [core/stream_probe.py](core/stream_probe.py#L135-L139) | `L135-L139` | def read_bits(count) |
| `read_se` | **Function** | [core/stream_probe.py](core/stream_probe.py#L149-L151) | `L149-L151` | def read_se() |
| `read_ue` | **Function** | [core/stream_probe.py](core/stream_probe.py#L141-L147) | `L141-L147` | def read_ue() |
| `Recorder` | **Class / Widget** | [core/recorder.py](core/recorder.py#L121-L435) | `L121-L435` | Basis:  |
| `safe_name` | **Function** | [core/recorder.py](core/recorder.py#L29-L31) | `L29-L31` | def safe_name(name, maxlen) |
| `save_thumb` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L136-L144) | `L136-L144` | def save_thumb(key, data) |
| `ScanAccount` | **Class / Widget** | [core/scan_repository.py](core/scan_repository.py#L24-L58) | `L24-L58` | Repräsentiert einen einzelnen gescannten MAC-Account eines Portals. |
| `ScanHost` | **Class / Widget** | [core/scan_repository.py](core/scan_repository.py#L62-L85) | `L62-L85` | Repräsentiert einen Host / ein Portal mit allen zugehörigen Logins. |
| `ScannerView` | **Class / Widget** | [ui/views/scanner_view.py](ui/views/scanner_view.py#L66-L711) | `L66-L711` | Basis: QWidget |
| `ScanRepository` | **Class / Widget** | [core/scan_repository.py](core/scan_repository.py#L88-L264) | `L88-L264` | Verwaltet das Einlesen, Filtern und Cachen aller Scan-Dateien aus 'mac_scans/'. |
| `ScanResult` | **Class / Widget** | [core/models.py](core/models.py#L478-L488) | `L478-L488` | Basis:  |
| `ScanThrottleController` | **Class / Widget** | [clients/throttle.py](clients/throttle.py#L11-L69) | `L11-L69` | Basis:  |
| `SeriesBrowserDialog` | **Class / Widget** | [ui/dialogs/series_dialog.py](ui/dialogs/series_dialog.py#L26-L163) | `L26-L163` | Basis: QDialog |
| `SidebarWidget` | **Class / Widget** | [ui/components/sidebar.py](ui/components/sidebar.py#L32-L453) | `L32-L453` | Basis: QFrame |
| `StbClient` | **Class / Widget** | [clients/stb_client.py](clients/stb_client.py#L61-L91) | `L61-L91` | Erweiterter Stalker/Ministra Client mit automatischem Inspector-Logging. |
| `StreamBufferProxy` | **Class / Widget** | [core/stream_buffer.py](core/stream_buffer.py#L585-L629) | `L585-L629` | Basis:  |
| `StreamProbeResult` | **Class / Widget** | [core/models.py](core/models.py#L456-L474) | `L456-L474` | Basis:  |
| `TestScanProfiles` | **Class / Widget** | [tests/test_scan_profiles.py](tests/test_scan_profiles.py#L10-L42) | `L10-L42` | Basis: unittest.TestCase |
| `TestUIAndEngine` | **Class / Widget** | [tests/test_ui_and_engine.py](tests/test_ui_and_engine.py#L90-L840) | `L90-L840` | Basis: unittest.TestCase |
| `TestVpnAndStreamErrors` | **Class / Widget** | [tests/test_vpn_and_stream_errors.py](tests/test_vpn_and_stream_errors.py#L15-L257) | `L15-L257` | Basis: unittest.TestCase |
| `ThemeColors` | **Class / Widget** | [ui/theme.py](ui/theme.py#L11-L43) | `L11-L43` | Design tokens matching and refining the Obsidian Cyber-Cinema palette. |
| `thumb_age_s` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L147-L151) | `L147-L151` | def thumb_age_s(key) |
| `thumb_path` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L116-L117) | `L116-L117` | def thumb_path(key) |
| `ThumbGrabber` | **Class / Widget** | [core/preview_grabber.py](core/preview_grabber.py#L154-L213) | `L154-L213` | Holt genau ein Standbild; cancel() beendet ffmpeg sofort. |
| `TopNavigationBar` | **Class / Widget** | [ui/components/top_bar.py](ui/components/top_bar.py#L22-L256) | `L22-L256` | Basis: QFrame |
| `VideoSurfaceWidget` | **Class / Widget** | [ui/views/live_tv_view.py](ui/views/live_tv_view.py#L52-L83) | `L52-L83` | Dedicated native HWND container for LibVLC Direct3D11/OpenGL rendering. |
| `VLCPlayerController` | **Class / Widget** | [player/vlc_controller.py](player/vlc_controller.py#L108-L683) | `L108-L683` | Steuert die integrierte LibVLC-Instanz mit HWND-Binding, PCR-Ringpuffer-Proxy |
| `VODFilterProxyModel` | **Class / Widget** | [ui/models/vod_model.py](ui/models/vod_model.py#L165-L236) | `L165-L236` | Supports local instant search, HD filter, Favorites filter, and custom sorting. |
| `VODRoles` | **Class / Widget** | [ui/models/vod_model.py](ui/models/vod_model.py#L17-L24) | `L17-L24` | Basis:  |
| `VODTableModel` | **Class / Widget** | [ui/models/vod_model.py](ui/models/vod_model.py#L58-L162) | `L58-L162` | Virtualized table model for Movies (VOD) and Series. |
| `VODView` | **Class / Widget** | [ui/views/vod_view.py](ui/views/vod_view.py#L38-L453) | `L38-L453` | Basis: QWidget |
| `XtreamClient` | **Class / Widget** | [clients/xtream_client.py](clients/xtream_client.py#L20-L119) | `L20-L119` | Basis: _BaseXtreamClient |

---

## 📦 Clients (Protokolle & APIs)

### 📄 [`clients/__init__.py`](clients/__init__.py) (17 Zeilen)
> Protokoll-Clients für STB Pro Qt6 (Stalker/Ministra, Xtream Codes, M3U).

---

### 📄 [`clients/m3u_client.py`](clients/m3u_client.py) (16 Zeilen)
> M3U / M3U8 Playlist Client für STB Pro Qt6.

#### Wichtige Konstanten / Konfigurationen
- `_APP_DIR` (L7), `_PARENT_DIR` (L8)

---

### 📄 [`clients/stb_client.py`](clients/stb_client.py) (119 Zeilen)
> Stalker / Ministra STB Client für STB Pro Qt6.
Erweitert den bewährten StbClient um Live-HTTP-Telemetrie für den interaktiven Protokoll-Inspector
(inklusive Request-Historie, Header-Capturing und cURL-Export).

#### Klassen & Komponenten
- **[`StbClient`](clients/stb_client.py#L61-L91)** : *_BaseStbClient* — `L61-L91`
  - *Erweiterter Stalker/Ministra Client mit automatischem Inspector-Logging.*
  - **Wichtige Methoden:**
    - [`__init__(portal_url, mac, model, serial_number, device_id, device_id2, signature, user_agent, timeout, normalized_load_url, enable_inspector)`](clients/stb_client.py#L65) — `L65`

#### Modul-Funktionen
- **[`_attach_inspector_hook(session, enable)`](clients/stb_client.py#L27-L58)** — `L27`
- **[`_on_response(resp)`](clients/stb_client.py#L31-L56)** — `L31`
- **[`check_mac_account(portal_url, mac, model, device_id, device_id2, serial_number, signature, timeout, normalized_load_url, session)`](clients/stb_client.py#L94-L119)** — `L94` — *Prüft einen einzelnen MAC-Account schnell im Hintergrund (ohne Inspector-Spam).*

#### Wichtige Konstanten / Konfigurationen
- `_APP_DIR` (L11), `_PARENT_DIR` (L12)

---

### 📄 [`clients/throttle.py`](clients/throttle.py) (69 Zeilen)
> Thread-sicherer Rate-Limit & Backoff-Controller für den Multi-MAC-Scanner.
Verhindert Paketfluten bei HTTP 429 / Cloudflare / WAF-Sperren durch automatische
Cooldown-Phasen, Worker-Pausierung und adaptives Pacing.

#### Klassen & Komponenten
- **[`ScanThrottleController`](clients/throttle.py#L11-L69)** — `L11-L69`
  - **Wichtige Methoden:**
    - [`__init__(base_delay, on_throttle_notify)`](clients/throttle.py#L12) — `L12`
    - [`wait_turn(stop_check)`](clients/throttle.py#L24) — `L24` *(Wird vor jedem HTTP-Request aufgerufen und pausiert bei Cooldown/Pacing.)*
    - [`handle_rate_limit(retry_after)`](clients/throttle.py#L42) — `L42` *(Wird bei HTTP 429 oder Cloudflare/WAF-Blocks aufgerufen und bremst alle Threads.)*
    - [`handle_success()`](clients/throttle.py#L64) — `L64`

---

### 📄 [`clients/xtream_client.py`](clients/xtream_client.py) (119 Zeilen)
> Xtream Codes API Client für STB Pro Qt6.
Mit automatischer HTTP-Telemetrie für den Protokoll-Inspector sowie Serien-API-Unterstützung.

#### Klassen & Komponenten
- **[`XtreamClient`](clients/xtream_client.py#L20-L119)** : *_BaseXtreamClient* — `L20-L119`
  - **Wichtige Methoden:**
    - [`__init__(server_url, username, password, output_format, timeout, user_agent, enable_inspector)`](clients/xtream_client.py#L21) — `L21`
    - [`get_series_categories()`](clients/xtream_client.py#L42) — `L42`
    - [`get_series(category_id, page)`](clients/xtream_client.py#L58) — `L58`
    - [`get_series_info(series_id)`](clients/xtream_client.py#L84) — `L84`

#### Wichtige Konstanten / Konfigurationen
- `_APP_DIR` (L9), `_PARENT_DIR` (L10)

---

## 📦 Core (Business Logic, Cache & DB)

### 📄 [`core/__init__.py`](core/__init__.py) (33 Zeilen)
> Core-Paket für STB Pro Qt6.
Enthält Datenmodelle, Event-Bus, Persistenz, Stream-Puffer, Probing und Recording.

---

### 📄 [`core/config_manager.py`](core/config_manager.py) (254 Zeilen)
> Konfigurations-Manager für STB Pro Qt6.
Unterstützt nahtlose Übernahme der bestehenden config.json aus dem Hauptverzeichnis,
damit alle gespeicherten Profile, Favoriten und Einstellungen erhalten bleiben.
Zusätzlich neu: Persistente VOD-Favoriten und Recently-Played-Historie!

#### Klassen & Komponenten
- **[`ConfigManager`](core/config_manager.py#L60-L253)** — `L60-L253`
  - *Verwaltet Profile, Live-/VOD-Favoriten, Verlauf, Player-Pfade und UI-Einstellungen.*
  - **Wichtige Methoden:**
    - [`__init__(filepath)`](core/config_manager.py#L63) — `L63`
    - [`_default_config()`](core/config_manager.py#L75) — `L75`
    - [`_load()`](core/config_manager.py#L115) — `L115`
    - [`save()`](core/config_manager.py#L129) — `L129`
    - [`get(key, default)`](core/config_manager.py#L148) — `L148`
    - [`set(key, value, auto_save)`](core/config_manager.py#L151) — `L151`
    - [`get_profiles()`](core/config_manager.py#L156) — `L156`
    - [`get_profile(name)`](core/config_manager.py#L161) — `L161`
    - [`save_profile(profile, old_name)`](core/config_manager.py#L167) — `L167`
    - [`delete_profile(name)`](core/config_manager.py#L179) — `L179`
    - [`get_favorites(profile_name)`](core/config_manager.py#L191) — `L191`
    - [`save_favorites(profile_name, favorites)`](core/config_manager.py#L195) — `L195`
    - [`get_vod_favorites(profile_name)`](core/config_manager.py#L201) — `L201`
    - [`save_vod_favorites(profile_name, favorites)`](core/config_manager.py#L205) — `L205`
    - [`get_recently_played(profile_name)`](core/config_manager.py#L211) — `L211`
    - *... und 5 weitere Hilfsmethoden.*

#### Modul-Funktionen
- **[`detect_vlc_path()`](core/config_manager.py#L19-L33)** — `L19`
- **[`detect_mpv_path()`](core/config_manager.py#L36-L45)** — `L36`
- **[`detect_ffplay_path()`](core/config_manager.py#L48-L57)** — `L48`

#### Wichtige Konstanten / Konfigurationen
- `APP_DIR` (L13), `PARENT_DIR` (L14), `LOCAL_CONFIG_FILE` (L15), `PARENT_CONFIG_FILE` (L16)

---

### 📄 [`core/logo_cache.py`](core/logo_cache.py) (154 Zeilen)
> Asynchroner Qt6 Logo- & Poster-Cache (QPixmap / QImage).
Nutzt Memory-Cache + Disk-Cache (teilt sich .cache/logos mit dem Hauptprojekt für sofortige Anzeige).

#### Klassen & Komponenten
- **[`LogoCache`](core/logo_cache.py#L22-L151)** : *QObject* — `L22-L151`
  - *Lädt Kanal-Logos und VOD-Poster im Hintergrund als QImage (Thread-sicher!)*
  - **Signals**: `_image_decoded`, `logo_ready`
  - **Wichtige Methoden:**
    - [`__init__(max_threads)`](core/logo_cache.py#L30) — `L30`
    - [`_url_to_path(url)`](core/logo_cache.py#L40) — `L40`
    - [`get_cached_pixmap(url, size)`](core/logo_cache.py#L50) — `L50`
    - [`get_pixmap(url, width, height)`](core/logo_cache.py#L56) — `L56`
    - [`get_or_fetch(url, width, height)`](core/logo_cache.py#L59) — `L59`
    - [`request_pixmap(url, size, on_loaded)`](core/logo_cache.py#L62) — `L62` *(Gibt QPixmap sofort zurück falls im RAM-Cache; andernfalls startet asynchroner Abruf.)*
    - [`_on_image_ready(url, w, h, qimg)`](core/logo_cache.py#L133) — `L133`

#### Wichtige Konstanten / Konfigurationen
- `APP_DIR` (L14), `PARENT_DIR` (L15), `PARENT_CACHE_DIR` (L17), `CACHE_DIR` (L18)

---

### 📄 [`core/m3u_exporter.py`](core/m3u_exporter.py) (44 Zeilen)
> M3U / M3U8 Playlist Exporter für STB Pro Qt6 (QoL Feature).
Exportiert beliebige Kanallisten (aktueller Filter, Kategorie, Favoriten oder Gesamtliste)
als standardkonforme .m3u8 Datei für VLC, Kodi, TiviMate oder externe Tools.

#### Modul-Funktionen
- **[`build_m3u_playlist(channels, user_agent, resolve_url_fn)`](core/m3u_exporter.py#L10-L44)** — `L10`

---

### 📄 [`core/mac_database.py`](core/mac_database.py) (239 Zeilen)
> Persistente, threadsichere MAC-Hit-Datenbank für STB Pro Qt6.
Synchronisiert sich automatisch mit einer vorhandenen mac_database.json im Hauptordner.

#### Klassen & Komponenten
- **[`MacDatabase`](core/mac_database.py#L26-L238)** — `L26-L238`
  - *Persistente, threadsichere Datenbank für gefundene MAC-Adressen mit Sendern.*
  - **Wichtige Methoden:**
    - [`__init__(filepath)`](core/mac_database.py#L32) — `L32`
    - [`_load()`](core/mac_database.py#L44) — `L44`
    - [`_save()`](core/mac_database.py#L57) — `L57`
    - [`save_found_mac(portal_url, res)`](core/mac_database.py#L74) — `L74`
    - [`get_known_macs(portal_url)`](core/mac_database.py#L127) — `L127`
    - [`get_all_records(portal_url)`](core/mac_database.py#L150) — `L150`
    - [`get_portals()`](core/mac_database.py#L159) — `L159`
    - [`delete_entry(mac, portal_url)`](core/mac_database.py#L163) — `L163`
    - [`clean_duplicates()`](core/mac_database.py#L186) — `L186`
    - [`get_count()`](core/mac_database.py#L216) — `L216`
    - [`total_count()`](core/mac_database.py#L220) — `L220`
    - [`get_entries(portal_url)`](core/mac_database.py#L223) — `L223`
    - [`deduplicate()`](core/mac_database.py#L234) — `L234`
    - [`remove_entry(portal_url, mac)`](core/mac_database.py#L237) — `L237`

#### Modul-Funktionen
- **[`format_mac_str(mac)`](core/mac_database.py#L19-L23)** — `L19`

#### Wichtige Konstanten / Konfigurationen
- `APP_DIR` (L13), `PARENT_DIR` (L14), `LOCAL_DB_FILE` (L15), `PARENT_DB_FILE` (L16)

---

### 📄 [`core/models.py`](core/models.py) (558 Zeilen)
> Datenmodelle (Dataclasses) für STB Pro Qt6.
Strikt typisiert und unabhängig von UI-Komponenten.

#### Klassen & Komponenten
- **[`Channel`](core/models.py#L62-L167)** — `L62-L167`
  - **Wichtige Methoden:**
    - [`__post_init__()`](core/models.py#L79) — `L79`
    - [`__hash__()`](core/models.py#L83) — `L83`
    - [`__eq__(other)`](core/models.py#L86) — `L86`
    - [`tv_genre_id()`](core/models.py#L92) — `L92`
    - [`tv_genre_id(val)`](core/models.py#L96) — `L96`
    - [`fav()`](core/models.py#L100) — `L100`
    - [`fav(val)`](core/models.py#L104) — `L104`
    - [`is_hls()`](core/models.py#L108) — `L108`
    - [`has_archive()`](core/models.py#L112) — `L112`
    - [`enable_tv_archive()`](core/models.py#L121) — `L121`
    - [`flags_summary()`](core/models.py#L125) — `L125`
    - [`from_raw(cls, raw, genre_map)`](core/models.py#L147) — `L147`
- **[`EPGProgram`](core/models.py#L171-L329)** — `L171-L329`
  - **Wichtige Methoden:**
    - [`name()`](core/models.py#L186) — `L186`
    - [`descr()`](core/models.py#L190) — `L190`
    - [`time_str()`](core/models.py#L194) — `L194`
    - [`time_to_str()`](core/models.py#L198) — `L198`
    - [`progress_percent()`](core/models.py#L202) — `L202`
    - [`progress()`](core/models.py#L231) — `L231`
    - [`remaining_minutes()`](core/models.py#L235) — `L235`
    - [`from_raw(cls, raw)`](core/models.py#L248) — `L248`
- **[`Profile`](core/models.py#L333-L452)** — `L333-L452`
  - **Wichtige Methoden:**
    - [`from_dict(cls, data)`](core/models.py#L352) — `L352`
    - [`to_dict()`](core/models.py#L372) — `L372`
    - [`portal_type()`](core/models.py#L393) — `L393`
    - [`portal_type(val)`](core/models.py#L402) — `L402`
    - [`url()`](core/models.py#L412) — `L412`
    - [`url(val)`](core/models.py#L421) — `L421`
    - [`server_url()`](core/models.py#L430) — `L430`
    - [`server_url(val)`](core/models.py#L434) — `L434`
    - [`m3u_url()`](core/models.py#L440) — `L440`
    - [`m3u_url(val)`](core/models.py#L444) — `L444`
    - [`clone(new_name)`](core/models.py#L449) — `L449`
- **[`StreamProbeResult`](core/models.py#L456-L474)** — `L456-L474`
- **[`ScanResult`](core/models.py#L478-L488)** — `L478-L488`
- **[`HttpLogEntry`](core/models.py#L492-L533)** — `L492-L533`
  - **Wichtige Methoden:**
    - [`create(cls, method, url, status_code, elapsed_ms, headers, params, body)`](core/models.py#L503) — `L503`
    - [`to_curl()`](core/models.py#L524) — `L524`
- **[`AppState`](core/models.py#L536-L558)** — `L536-L558`
  - *Zentraler Laufzeit-Zustand der Anwendung.*
  - **Wichtige Methoden:**
    - [`__init__()`](core/models.py#L538) — `L538`

#### Modul-Funktionen
- **[`quality_from_dimensions(width, height)`](core/models.py#L13-L28)** — `L13` — *Ermittelt den Qualitäts-Tag (UHD/FHD/HD/SD) exakt anhand von Pixel-Dimensionen.*
- **[`detect_quality_tag(name, raw)`](core/models.py#L31-L58)** — `L31` — *Erkennt den Qualitäts-Tag AUSSCHLIESSLICH anhand von echten Dimensionsdaten in den Metadaten.*

---

### 📄 [`core/preview_grabber.py`](core/preview_grabber.py) (280 Zeilen)
> Sender-Vorschau für STB Pro Qt6: Standbild (ein Frame via FFmpeg, gecacht auf Disk).
Optimiert mit High-Speed In-Memory TS-Extraktion und Black-Frame-Filterung.

#### Klassen & Komponenten
- **[`ThumbGrabber`](core/preview_grabber.py#L154-L213)** — `L154-L213`
  - *Holt genau ein Standbild; cancel() beendet ffmpeg sofort.*
  - **Wichtige Methoden:**
    - [`__init__()`](core/preview_grabber.py#L157) — `L157`
    - [`grab(url, headers, width, timeout)`](core/preview_grabber.py#L161) — `L161`
    - [`cancel()`](core/preview_grabber.py#L206) — `L206`

#### Modul-Funktionen
- **[`find_ffmpeg()`](core/preview_grabber.py#L15-L29)** — `L15`
- **[`is_blank_or_black_jpeg(data)`](core/preview_grabber.py#L40-L61)** — `L40` — *Erkennt korrupte, leere oder rein schwarze Dummy-Frames zuverlässig.*
- **[`extract_thumbnail_from_ts(data, width)`](core/preview_grabber.py#L64-L96)** — `L64` — *Extrahiert blitzschnell (0.1s) genau ein Frame aus bereits heruntergeladenen MPEG-TS Bytes via stdin.*
- **[`_cmd(url, headers, width, tail)`](core/preview_grabber.py#L99-L113)** — `L99`
- **[`thumb_path(key)`](core/preview_grabber.py#L116-L117)** — `L116`
- **[`load_cached_thumb(key)`](core/preview_grabber.py#L120-L133)** — `L120`
- **[`save_thumb(key, data)`](core/preview_grabber.py#L136-L144)** — `L136`
- **[`thumb_age_s(key)`](core/preview_grabber.py#L147-L151)** — `L147`
- **[`grab_thumbnail(url, headers, width, timeout, cancel_ev)`](core/preview_grabber.py#L216-L280)** — `L216` — *High-Performance Standalone Thumbnail Grabber.*

#### Wichtige Konstanten / Konfigurationen
- `FFMPEG_BIN` (L32), `APP_DIR` (L33), `PARENT_DIR` (L34), `PARENT_THUMB_DIR` (L35), `THUMB_DIR` (L36), `_NOWIN` (L37)

---

### 📄 [`core/recorder.py`](core/recorder.py) (439 Zeilen)
> Aufnahme (Live) und Download (VOD/Archiv) von Streams für STB Pro Qt6.
- HTTP/TS/MKV/MP4: direkter Stream-Download via requests (VOD mit Resume per Range).
- HLS (.m3u8): ffmpeg -c copy.
- Automatische Erkennung von HLS-Playlists, HTML/JSON-Fehlermeldungen und Reconnect-Schutz.

#### Klassen & Komponenten
- **[`_HLSDetected`](core/recorder.py#L23-L26)** : *Exception* — `L23-L26`
  - **Wichtige Methoden:**
    - [`__init__(url)`](core/recorder.py#L24) — `L24`
- **[`Job`](core/recorder.py#L56-L118)** — `L56-L118`
  - **Wichtige Methoden:**
    - [`active()`](core/recorder.py#L80) — `L80`
    - [`elapsed()`](core/recorder.py#L84) — `L84`
    - [`job_id()`](core/recorder.py#L88) — `L88`
    - [`title()`](core/recorder.py#L92) — `L92`
    - [`status()`](core/recorder.py#L96) — `L96`
    - [`bytes_written()`](core/recorder.py#L102) — `L102`
    - [`total_bytes()`](core/recorder.py#L106) — `L106`
    - [`speed_kbps()`](core/recorder.py#L110) — `L110`
    - [`elapsed_str()`](core/recorder.py#L114) — `L114`
- **[`Recorder`](core/recorder.py#L121-L435)** — `L121-L435`
  - **Wichtige Methoden:**
    - [`__init__(out_dir, on_change, log)`](core/recorder.py#L122) — `L122`
    - [`output_dir()`](core/recorder.py#L136) — `L136`
    - [`set_dir(d)`](core/recorder.py#L139) — `L139`
    - [`start(kind, name, url, headers, ext, refresh)`](core/recorder.py#L142) — `L142`
    - [`stop(job)`](core/recorder.py#L169) — `L169`
    - [`stop_job(job_id)`](core/recorder.py#L183) — `L183`
    - [`stop_all()`](core/recorder.py#L189) — `L189`
    - [`active_jobs(kind)`](core/recorder.py#L194) — `L194`
    - [`remove_finished()`](core/recorder.py#L197) — `L197`
    - [`clear_finished()`](core/recorder.py#L202) — `L202`
    - [`_finish(job, state, err)`](core/recorder.py#L205) — `L205`
    - [`_run(job, is_hls)`](core/recorder.py#L214) — `L214`
    - [`_attempt(job, resume_from, append)`](core/recorder.py#L231) — `L231`
    - [`_run_http(job)`](core/recorder.py#L299) — `L299`
    - [`_run_ffmpeg(job)`](core/recorder.py#L348) — `L348`

#### Modul-Funktionen
- **[`safe_name(name, maxlen)`](core/recorder.py#L29-L31)** — `L29`
- **[`find_ffmpeg()`](core/recorder.py#L34-L52)** — `L34`

#### Wichtige Konstanten / Konfigurationen
- `CHUNK` (L18), `MAX_DOWNTIME` (L19), `MIN_VOD_BYTES` (L20)

---

### 📄 [`core/scan_repository.py`](core/scan_repository.py) (264 Zeilen)
> Scan-Repository & Profil-Manager für STB Pro.
Liest strukturierte Scan-Dateien (*.txt) aus dem Ordner 'mac_scans/' ein
und generiert dynamisch Host- und Login-Auswahlen für Stalker-Portale.

#### Klassen & Komponenten
- **[`ScanAccount`](core/scan_repository.py#L24-L58)** — `L24-L58`
  - *Repräsentiert einen einzelnen gescannten MAC-Account eines Portals.*
  - **Wichtige Methoden:**
    - [`display_text()`](core/scan_repository.py#L34) — `L34` *(Kompakte, übersichtliche Darstellung für Dropdowns.)*
    - [`to_profile(host_label)`](core/scan_repository.py#L42) — `L42` *(Erzeugt ein einsatzbereites Profile-Objekt für STB Pro.)*
- **[`ScanHost`](core/scan_repository.py#L62-L85)** — `L62-L85`
  - *Repräsentiert einen Host / ein Portal mit allen zugehörigen Logins.*
  - **Wichtige Methoden:**
    - [`total_hits()`](core/scan_repository.py#L71) — `L71`
    - [`max_channels()`](core/scan_repository.py#L75) — `L75`
    - [`display_label()`](core/scan_repository.py#L78) — `L78` *(Formatierte Anzeige für die Host-Combobox.)*
- **[`ScanRepository`](core/scan_repository.py#L88-L264)** — `L88-L264`
  - *Verwaltet das Einlesen, Filtern und Cachen aller Scan-Dateien aus 'mac_scans/'.*
  - **Wichtige Methoden:**
    - [`__init__(directory)`](core/scan_repository.py#L93) — `L93`
    - [`get_scans_dir()`](core/scan_repository.py#L109) — `L109`
    - [`reload()`](core/scan_repository.py#L114) — `L114` *(Liest alle *.txt Dateien im Scans-Ordner ein und aktualisiert den Host-Katalog.)*
    - [`_parse_file(file_path)`](core/scan_repository.py#L139) — `L139`
    - [`get_hosts()`](core/scan_repository.py#L234) — `L234` *(Gibt alle verfügbaren Hosts alphabetisch sortiert zurück.)*
    - [`get_host(host_name)`](core/scan_repository.py#L238) — `L238`
    - [`get_account(host_name, mac)`](core/scan_repository.py#L250) — `L250`
    - [`create_profile(host_name, mac)`](core/scan_repository.py#L260) — `L260`

#### Wichtige Konstanten / Konfigurationen
- `APP_DIR` (L17), `PARENT_DIR` (L18), `LOCAL_SCANS_DIR` (L19), `PARENT_SCANS_DIR` (L20)

---

### 📄 [`core/signals.py`](core/signals.py) (116 Zeilen)
> Reaktiver Qt6 Event-Bus & Asynchroner QThreadPool-Worker.
Ersetzt das langsame Tkinter after()-Polling durch echte Qt Signals & Slots.

#### Klassen & Komponenten
- **[`AppEventBus`](core/signals.py#L10-L27)** : *QObject* — `L10-L27`
  - *Zentraler Signal-Bus für die gesamte Applikation.*
  - **Signals**: `log_message`, `http_Exchange_logged`, `connection_state_changed`, `profile_updated`, `channels_loaded`, `vod_categories_loaded`, `channel_selected`, `channel_play_requested`, `favorites_changed`, `recorder_changed`, `telemetry_updated`, `scan_result_received`, `scan_progress_updated`, `scan_state_changed`, `vpn_status_changed`, `stream_ip_ban_detected`
- **[`_WorkerSignals`](core/signals.py#L30-L32)** : *QObject* — `L30-L32`
  - **Signals**: `finished`, `error`
- **[`_AsyncTask`](core/signals.py#L35-L63)** : *QRunnable* — `L35-L63`
  - *Kapselt eine beliebige Funktion für den globalen QThreadPool.*
  - **Wichtige Methoden:**
    - [`__init__(fn)`](core/signals.py#L37) — `L37`
    - [`run()`](core/signals.py#L57) — `L57`
- **[`AsyncWorkerPool`](core/signals.py#L66-L111)** : *QObject* — `L66-L111`
  - *Hochperformanter Thread-Pool auf Basis von Qt QThreadPool.*
  - **Signals**: `ui_dispatch_signal`
  - **Wichtige Methoden:**
    - [`__init__(max_workers)`](core/signals.py#L73) — `L73`
    - [`_execute_on_ui(fn, args, kwargs)`](core/signals.py#L81) — `L81`
    - [`run_async(task_fn)`](core/signals.py#L87) — `L87`
    - [`submit(fn)`](core/signals.py#L103) — `L103`
    - [`dispatch_to_ui(fn)`](core/signals.py#L106) — `L106`
    - [`shutdown()`](core/signals.py#L109) — `L109`

---

### 📄 [`core/stream_buffer.py`](core/stream_buffer.py) (629 Zeilen)
> Lokaler Stream-Puffer-Proxy (127.0.0.1) für STB Pro Qt6.
Liest den Upstream-Stream unabhängig vom Player in einen Ringpuffer (Sekunden/MB),
liefert ihn PCR-getaktet an LibVLC und überbrückt kurze Aussetzer durch Auto-Reconnect.

#### Klassen & Komponenten
- **[`BufferSettings`](core/stream_buffer.py#L22-L65)** — `L22-L65`
  - **Wichtige Methoden:**
    - [`clamp()`](core/stream_buffer.py#L38) — `L38`
    - [`to_dict()`](core/stream_buffer.py#L52) — `L52`
    - [`from_dict(cls, d)`](core/stream_buffer.py#L56) — `L56`
- **[`_Session`](core/stream_buffer.py#L68-L548)** — `L68-L548`
  - **Wichtige Methoden:**
    - [`__init__(url, headers, st)`](core/stream_buffer.py#L69) — `L69`
    - [`_url_host()`](core/stream_buffer.py#L109) — `L109`
    - [`_rate_est()`](core/stream_buffer.py#L117) — `L117`
    - [`_record_pcr(abs_offset, pcr_time)`](core/stream_buffer.py#L123) — `L123`
    - [`_level_s(pos)`](core/stream_buffer.py#L145) — `L145`
    - [`_scan(chunk)`](core/stream_buffer.py#L153) — `L153`
    - [`_parse_ts_psi(p, o, pid, has_pusi, afc)`](core/stream_buffer.py#L218) — `L218`
    - [`_produce()`](core/stream_buffer.py#L289) — `L289`
    - [`_tick_rate(n)`](core/stream_buffer.py#L436) — `L436`
    - [`_take(pos, n)`](core/stream_buffer.py#L444) — `L444`
    - [`serve(wfile)`](core/stream_buffer.py#L454) — `L454`
    - [`stop()`](core/stream_buffer.py#L509) — `L509`
    - [`stats()`](core/stream_buffer.py#L523) — `L523`
- **[`_Handler`](core/stream_buffer.py#L551-L582)** : *BaseHTTPRequestHandler* — `L551-L582`
  - **Wichtige Methoden:**
    - [`log_message()`](core/stream_buffer.py#L554) — `L554`
    - [`do_HEAD()`](core/stream_buffer.py#L557) — `L557`
    - [`do_GET()`](core/stream_buffer.py#L568) — `L568`
- **[`StreamBufferProxy`](core/stream_buffer.py#L585-L629)** — `L585-L629`
  - **Wichtige Methoden:**
    - [`__init__()`](core/stream_buffer.py#L586) — `L586`
    - [`_ensure_server()`](core/stream_buffer.py#L591) — `L591`
    - [`open_session(url, headers, settings)`](core/stream_buffer.py#L599) — `L599`
    - [`get_session(path)`](core/stream_buffer.py#L607) — `L607`
    - [`stop_session()`](core/stream_buffer.py#L611) — `L611`
    - [`stats()`](core/stream_buffer.py#L617) — `L617`
    - [`shutdown()`](core/stream_buffer.py#L621) — `L621`

#### Wichtige Konstanten / Konfigurationen
- `TS_PACKET` (L17), `_LEAD_S` (L18)

---

### 📄 [`core/stream_probe.py`](core/stream_probe.py) (614 Zeilen)
> Stream-Probe Engine für STB Pro Qt6.
Ermittelt HTTP-Latenz, MPEG-TS PCR-Mux-Bitrate sowie Video-/Audio-Codecs und Auflösung via FFprobe.

#### Modul-Funktionen
- **[`find_ffprobe()`](core/stream_probe.py#L17-L31)** — `L17`
- **[`pcr_bitrate_kbps(data)`](core/stream_probe.py#L38-L66)** — `L38` — *Echte Mux-Bitrate aus MPEG-TS-PCR.*
- **[`format_codec_name(codec)`](core/stream_probe.py#L69-L85)** — `L69`
- **[`format_resolution(width, height, fps)`](core/stream_probe.py#L88-L104)** — `L88`
- **[`parse_sps_from_h264(sps_bytes)`](core/stream_probe.py#L107-L208)** — `L107` — *Decodiert H.264 Sequence Parameter Set (SPS) direkt in (width, height) ohne externe Tools.*
- **[`read_bit()`](core/stream_probe.py#L124-L133)** — `L124`
- **[`read_bits(count)`](core/stream_probe.py#L135-L139)** — `L135`
- **[`read_ue()`](core/stream_probe.py#L141-L147)** — `L141`
- **[`read_se()`](core/stream_probe.py#L149-L151)** — `L149`
- **[`extract_video_info_from_ts(data)`](core/stream_probe.py#L211-L271)** — `L211` — *Scannt MPEG-TS Pakete nach H.264/H.265 SPS in Millisekunden.*
- **[`extract_resolution_from_hls_text(text)`](core/stream_probe.py#L274-L289)** — `L274` — *Extrahiert RESOLUTION=WxH direkt aus HLS-Playlists.*
- **[`is_ip_or_stream_ban(status_code, error_text)`](core/stream_probe.py#L295-L308)** — `L295` — *Ermittelt zuverlässig, ob ein HTTP-Statuscode oder Fehlertext auf*
- **[`diagnose_iptv_status(status_code)`](core/stream_probe.py#L311-L329)** — `L311` — *Diagnostiziert proprietäre/spezifische HTTP-Statuscodes von IPTV- und Streaming-Clustern.*
- **[`detect_stream_error_payload(data, content_type)`](core/stream_probe.py#L332-L399)** — `L332` — *Erkennt versteckte Fehler-Payloads (z. B. IP_BAN, ISP_LOCK_FAILED, Geo-Blocks),*
- **[`probe_stream(url, user_agent, cookies, timeout, sample_duration, cancel, skip_ffprobe, proxy, extract_thumbnail, trigger_vpn)`](core/stream_probe.py#L402-L614)** — `L402`
- **[`_parse_json(parsed)`](core/stream_probe.py#L549-L570)** — `L549`

#### Wichtige Konstanten / Konfigurationen
- `FFPROBE_BIN` (L34), `_NOWIN` (L35), `BAN_STATUS_CODES` (L292)

---

### 📄 [`core/vpn_manager.py`](core/vpn_manager.py) (523 Zeilen)
> NordVPN Manager für STB Pro Qt6.
Erkennt eine aktive NordVPN-Installation, überwacht den Verbindungsstatus und
führt bei Erkennung von IP-/ISP-Sperren (IP_BAN / ISP_LOCK) vollautomatische,
mehrstufige Server- und Länder-Rotationen via NordVPN-CLI durch.
Speichert verbrannte IPs pro Host und respektiert Benutzer-Präferenzen zur VPN-Steuerung.

#### Klassen & Komponenten
- **[`NordVpnManager`](core/vpn_manager.py#L21-L519)** — `L21-L519`
  - *Verwaltet die Integration mit NordVPN unter Windows.*
  - **Wichtige Methoden:**
    - [`__init__()`](core/vpn_manager.py#L44) — `L44`
    - [`set_config_manager(mgr)`](core/vpn_manager.py#L56) — `L56` *(Bindet den Konfigurations-Manager ein und synchronisiert gespeicherte Einstellungen.)*
    - [`auto_switch_enabled()`](core/vpn_manager.py#L68) — `L68`
    - [`auto_switch_enabled(val)`](core/vpn_manager.py#L74) — `L74`
    - [`_detect_cli()`](core/vpn_manager.py#L79) — `L79`
    - [`is_installed()`](core/vpn_manager.py#L97) — `L97` *(Prüft, ob NordVPN auf dem System installiert ist.)*
    - [`is_running()`](core/vpn_manager.py#L101) — `L101` *(Prüft, ob der NordVPN-Dienst oder die App im Hintergrund aktiv ist.)*
    - [`is_connected()`](core/vpn_manager.py#L118) — `L118` *(Prüft über die Routing-Tabelle, ob der NordLynx-Tunnel aktiv Datenverkehr leitet.)*
    - [`get_public_ip(timeout)`](core/vpn_manager.py#L135) — `L135` *(Ermittelt die aktuelle öffentliche IP-Adresse.)*
    - [`_normalize_host(host_or_url)`](core/vpn_manager.py#L156) — `L156`
    - [`mark_ip_burned(host, ip, reason)`](core/vpn_manager.py#L172) — `L172` *(Markiert eine IP für einen bestimmten Host als gesperrt/verbrannt.)*
    - [`is_ip_burned(host, ip)`](core/vpn_manager.py#L189) — `L189` *(Prüft, ob eine IP für den angegebenen Host bereits als gesperrt markiert wurde.)*
    - [`get_burned_ips(host)`](core/vpn_manager.py#L203) — `L203` *(Gibt die Liste aller verbrannten IPs für einen Host zurück.)*
    - [`clear_burned_ips(host)`](core/vpn_manager.py#L212) — `L212` *(Setzt verbrannte IPs zurück (für einen Host oder global).)*
    - [`guess_country_for_profile(cls, profile_name, portal_url)`](core/vpn_manager.py#L232) — `L232` *(Leitet aus dem Profilnamen oder der Portal-Domain das optimale Zielland ab.)*
    - *... und 5 weitere Hilfsmethoden.*

---

## 📦 Player & Engine (VLC, Proxy & OSD)

### 📄 [`player/__init__.py`](player/__init__.py) (14 Zeilen)
> Player-Paket für STB Pro Qt6.
Enthält LibVLC-Controller, externen Player-Runner und das transparente Fullscreen-OSD.

---

### 📄 [`player/external_player.py`](player/external_player.py) (115 Zeilen)
> Externer Player-Runner für STB Pro Qt6.
Unterstützt VLC, MPV und FFplay inklusive Übergabe von User-Agent und Referer.

#### Klassen & Komponenten
- **[`ExternalPlayerRunner`](player/external_player.py#L11-L115)** — `L11-L115`
  - **Wichtige Methoden:**
    - [`__init__()`](player/external_player.py#L12) — `L12`
    - [`is_running()`](player/external_player.py#L15) — `L15`
    - [`stop()`](player/external_player.py#L18) — `L18`
    - [`toggle_fullscreen()`](player/external_player.py#L26) — `L26`
    - [`play(player_type, player_path, stream_url, title, user_agent, referrer, fullscreen)`](player/external_player.py#L56) — `L56`

---

### 📄 [`player/osd_overlay.py`](player/osd_overlay.py) (396 Zeilen)
> Transparentes Qt6 Fullscreen-OSD (HUD) & Quick-Channel-Drawer.
Verwendet eigene rahmenlose Tool-Overlays, die niemals vom Direct3D11/LibVLC-Video-Surface
übermalt werden und flimmerfrei über dem Vollbild-Video schweben.

#### Klassen & Komponenten
- **[`_TopHudBar`](player/osd_overlay.py#L16-L81)** : *QWidget* — `L16-L81`
  - **Wichtige Methoden:**
    - [`__init__(parent_window, on_exit_fs)`](player/osd_overlay.py#L17) — `L17`
- **[`_BottomHudBar`](player/osd_overlay.py#L84-L194)** : *QWidget* — `L84-L194`
  - **Wichtige Methoden:**
    - [`__init__(parent_window, on_prev, on_play_pause, on_stop, on_next, on_mute, on_volume, on_aspect, on_toggle_drawer)`](player/osd_overlay.py#L85) — `L85`
- **[`_ChannelDrawerOverlay`](player/osd_overlay.py#L197-L275)** : *QWidget* — `L197-L275`
  - **Wichtige Methoden:**
    - [`__init__(parent_window, on_select_channel)`](player/osd_overlay.py#L198) — `L198`
    - [`set_channels(channels)`](player/osd_overlay.py#L252) — `L252`
    - [`_filter()`](player/osd_overlay.py#L256) — `L256`
    - [`_on_item_activated(item)`](player/osd_overlay.py#L272) — `L272`
- **[`FullscreenOSDOverlay`](player/osd_overlay.py#L278-L396)** : *QObject* — `L278-L396`
  - *Koordiniert Top-HUD, Bottom-HUD, Uhrzeit-Timer, Auto-Hide und den Quick-Channel-Drawer.*
  - **Wichtige Methoden:**
    - [`__init__(main_window, on_play_pause, on_stop, on_prev, on_next, on_volume, on_toggle_mute, on_aspect_ratio, on_exit_fullscreen, on_channel_select)`](player/osd_overlay.py#L280) — `L280`
    - [`populate_drawer_channels(channels)`](player/osd_overlay.py#L318) — `L318`
    - [`update_info(number, title, category, epg_now, is_playing)`](player/osd_overlay.py#L321) — `L321`
    - [`update_volume_ui(vol, is_muted)`](player/osd_overlay.py#L335) — `L335`
    - [`_reposition()`](player/osd_overlay.py#L342) — `L342`
    - [`show(auto_hide_ms)`](player/osd_overlay.py#L353) — `L353`
    - [`hide_bars()`](player/osd_overlay.py#L365) — `L365`
    - [`hide_all()`](player/osd_overlay.py#L373) — `L373`
    - [`toggle_drawer()`](player/osd_overlay.py#L381) — `L381`
    - [`_tick_clock()`](player/osd_overlay.py#L392) — `L392`
    - [`shutdown()`](player/osd_overlay.py#L395) — `L395`

---

### 📄 [`player/vlc_controller.py`](player/vlc_controller.py) (683 Zeilen)
> LibVLC Hardware-Player Controller für STB Pro Qt6.
Nutzt Qt Signals für reaktive Status- und Puffer-Updates ohne UI-Blockade.

#### Klassen & Komponenten
- **[`VLCPlayerController`](player/vlc_controller.py#L108-L683)** : *QObject* — `L108-L683`
  - *Steuert die integrierte LibVLC-Instanz mit HWND-Binding, PCR-Ringpuffer-Proxy*
  - **Signals**: `state_changed`, `buffering_changed`
  - **Wichtige Methoden:**
    - [`__init__(settings)`](player/vlc_controller.py#L116) — `L116`
    - [`set_probe_result(probe_result)`](player/vlc_controller.py#L138) — `L138`
    - [`apply_settings(settings)`](player/vlc_controller.py#L142) — `L142`
    - [`initialize(hwnd)`](player/vlc_controller.py#L145) — `L145`
    - [`rebind_hwnd(hwnd)`](player/vlc_controller.py#L197) — `L197`
    - [`play_url(url, title, user_agent, referrer, extra_headers, direct, async_play)`](player/vlc_controller.py#L208) — `L208`
    - [`get_live_telemetry()`](player/vlc_controller.py#L320) — `L320`
    - [`toggle_play_pause()`](player/vlc_controller.py#L440) — `L440`
    - [`stop(async_stop)`](player/vlc_controller.py#L459) — `L459`
    - [`set_volume(vol)`](player/vlc_controller.py#L487) — `L487`
    - [`toggle_mute()`](player/vlc_controller.py#L498) — `L498`
    - [`set_aspect_ratio(ratio_str)`](player/vlc_controller.py#L511) — `L511`
    - [`get_time()`](player/vlc_controller.py#L526) — `L526`
    - [`get_length()`](player/vlc_controller.py#L536) — `L536`
    - [`set_time(ms)`](player/vlc_controller.py#L546) — `L546`
    - *... und 12 weitere Hilfsmethoden.*

#### Modul-Funktionen
- **[`decode_vlc_fourcc(codec_val)`](player/vlc_controller.py#L20-L101)** — `L20`

#### Wichtige Konstanten / Konfigurationen
- `VLC_AVAILABLE` (L14), `VLC_AVAILABLE` (L17)

---

## 📦 UI - Hauptfenster & Theme

### 📄 [`ui/__init__.py`](ui/__init__.py) (3 Zeilen)
> UI Layer Package for STB Pro v6.0 Qt6 Edition.

---

### 📄 [`ui/main_window.py`](ui/main_window.py) (2791 Zeilen)
> Main Application Window (Orchestrator) for STB Pro v6.0 Qt6 Edition.
Coordinates Sidebar, TopNavigationBar, LiveTVView, VODView, ScannerView, InspectorView, ConsoleView,
LibVLC Hardware Player, External Player Runner, Fullscreen HUD Overlay, PiP Mini-Player,
Multi-Thread MAC Scanner, Parallel Category Validator, and all 7 Dialogs.

#### Klassen & Komponenten
- **[`MainWindow`](ui/main_window.py#L87-L2789)** : *QMainWindow* — `L87-L2789`
  - **Signals**: `_val_progress_sig`, `_val_finished_sig`, `_val_thumb_progress_sig`, `_val_thumb_finished_sig`, `_epg_loaded_sig`, `_probe_done_sig`, `_preview_ready_sig`
  - **Wichtige Methoden:**
    - [`__init__()`](ui/main_window.py#L97) — `L97`
    - [`_build_ui()`](ui/main_window.py#L196) — `L196`
    - [`_bind_signals()`](ui/main_window.py#L251) — `L251`
    - [`_is_text_input_focused()`](ui/main_window.py#L362) — `L362`
    - [`_bind_guarded_shortcut(key_seq, callback)`](ui/main_window.py#L366) — `L366`
    - [`_cycle_aspect_ratio()`](ui/main_window.py#L375) — `L375`
    - [`_setup_shortcuts()`](ui/main_window.py#L380) — `L380`
    - [`_load_initial_config()`](ui/main_window.py#L403) — `L403`
    - [`switch_view(view_key)`](ui/main_window.py#L476) — `L476`
    - [`toggle_sidebar()`](ui/main_window.py#L484) — `L484`
    - [`toggle_cinema_mode()`](ui/main_window.py#L489) — `L489`
    - [`toggle_pip_mode()`](ui/main_window.py#L496) — `L496` *(Switches into a floating Always-on-Top Picture-in-Picture mini-player window.)*
    - [`toggle_fullscreen()`](ui/main_window.py#L538) — `L538`
    - [`enter_fullscreen()`](ui/main_window.py#L547) — `L547`
    - [`exit_fullscreen()`](ui/main_window.py#L566) — `L566`
    - *... und 93 weitere Hilfsmethoden.*

---

### 📄 [`ui/theme.py`](ui/theme.py) (499 Zeilen)
> Obsidian Cyber-Cinema Design System & Qt6 Stylesheet (QSS).
Provides color tokens, font families, and global dark stylesheet for PySide6.

#### Klassen & Komponenten
- **[`ThemeColors`](ui/theme.py#L11-L43)** — `L11-L43`
  - *Design tokens matching and refining the Obsidian Cyber-Cinema palette.*

#### Modul-Funktionen
- **[`apply_obsidian_theme(app, scale_factor)`](ui/theme.py#L465-L499)** — `L465` — *Apply dark QPalette and Obsidian Cyber-Cinema QSS stylesheet with dynamic UI scaling.*

#### Wichtige Konstanten / Konfigurationen
- `GLOBAL_QSS` (L46)

---

## 📦 UI - Views & Workspaces

### 📄 [`ui/views/__init__.py`](ui/views/__init__.py) (16 Zeilen)
> Main Workspace Views for STB Pro Qt6.

---

### 📄 [`ui/views/console_view.py`](ui/views/console_view.py) (156 Zeilen)
> Interactive System & Pentest Log Console View.
Features real-time log streaming via Qt Signals, level filtering, keyword search, clipboard export, and file export.

#### Klassen & Komponenten
- **[`ConsoleView`](ui/views/console_view.py#L26-L156)** : *QWidget* — `L26-L156`
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/views/console_view.py#L27) — `L27`
    - [`_detect_level(msg)`](ui/views/console_view.py#L96) — `L96`
    - [`append_log(message)`](ui/views/console_view.py#L104) — `L104`
    - [`_matches_filter(lvl, msg)`](ui/views/console_view.py#L119) — `L119`
    - [`_rebuild_view()`](ui/views/console_view.py#L128) — `L128`
    - [`clear_logs()`](ui/views/console_view.py#L139) — `L139`
    - [`_copy_all()`](ui/views/console_view.py#L144) — `L144`
    - [`_save_to_file()`](ui/views/console_view.py#L147) — `L147`

---

### 📄 [`ui/views/inspector_view.py`](ui/views/inspector_view.py) (262 Zeilen)
> Interactive Protocol & HTTP Exchange Inspector View.
Replaces the static text dump of the legacy Tkinter version with a live, searchable HTTP traffic table,
JSON pretty-printer, header inspector, 1-click cURL generator, and on-demand Handshake / Endpoint tester.

#### Klassen & Komponenten
- **[`InspectorView`](ui/views/inspector_view.py#L32-L262)** : *QWidget* — `L32-L262`
  - **Signals**: `handshake_test_requested`, `profile_dump_requested`
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/views/inspector_view.py#L36) — `L36`
    - [`add_http_entry(entry)`](ui/views/inspector_view.py#L165) — `L165`
    - [`_matches(entry)`](ui/views/inspector_view.py#L177) — `L177`
    - [`_refresh_table()`](ui/views/inspector_view.py#L188) — `L188`
    - [`_append_row(entry)`](ui/views/inspector_view.py#L194) — `L194`
    - [`_on_row_selected()`](ui/views/inspector_view.py#L217) — `L217`
    - [`set_summary_report(text, switch_tab)`](ui/views/inspector_view.py#L247) — `L247`
    - [`_copy_curl()`](ui/views/inspector_view.py#L252) — `L252`
    - [`clear_entries()`](ui/views/inspector_view.py#L255) — `L255`

---

### 📄 [`ui/views/live_tv_view.py`](ui/views/live_tv_view.py) (1200 Zeilen)
> Live TV Split-Workspace View for STB Pro Qt6.
Combines the GPU-virtualized Channel List (QListView + ChannelListModel + ChannelFilterProxyModel + ChannelCardDelegate)
with the Hero Banner, Native Video Surface (LibVLC HWND + FFmpeg Standbild-Preview),
VOD/Catchup Seekbar, Audio/Subtitle/Aspect/Speed Controls, Multi-Thread Category Validator, and Live EPG Panel.

#### Klassen & Komponenten
- **[`VideoSurfaceWidget`](ui/views/live_tv_view.py#L52-L83)** : *QFrame* — `L52-L83`
  - *Dedicated native HWND container for LibVLC Direct3D11/OpenGL rendering.*
  - **Signals**: `double_clicked`, `mouse_moved`
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/views/live_tv_view.py#L61) — `L61`
    - [`paintEvent(event)`](ui/views/live_tv_view.py#L68) — `L68`
    - [`clear_surface()`](ui/views/live_tv_view.py#L72) — `L72`
    - [`mouseDoubleClickEvent(event)`](ui/views/live_tv_view.py#L76) — `L76`
    - [`mouseMoveEvent(event)`](ui/views/live_tv_view.py#L81) — `L81`
- **[`PreviewOverlayWidget`](ui/views/live_tv_view.py#L86-L152)** : *QFrame* — `L86-L152`
  - *Standbild-Preview Thumbnail Overlay displayed inside the video viewport when*
  - **Signals**: `play_requested`
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/views/live_tv_view.py#L94) — `L94`
    - [`set_pixmap(pixmap, badge_text)`](ui/views/live_tv_view.py#L121) — `L121`
    - [`clear_pixmap()`](ui/views/live_tv_view.py#L128) — `L128`
    - [`_rescale()`](ui/views/live_tv_view.py#L132) — `L132`
    - [`resizeEvent(event)`](ui/views/live_tv_view.py#L145) — `L145`
    - [`mouseDoubleClickEvent(event)`](ui/views/live_tv_view.py#L149) — `L149`
- **[`LiveTVView`](ui/views/live_tv_view.py#L155-L1199)** : *QWidget* — `L155-L1199`
  - **Signals**: `channel_selected`, `channel_play_requested`, `favorite_toggled`, `probe_channel_requested`, `copy_url_requested`, `record_channel_requested`, `export_m3u_requested`, `raw_json_requested`, `epg_guide_requested`, `validate_category_requested`, `fetch_group_thumbnails_requested`, `stop_validation_requested`, `prev_channel_requested`, `next_channel_requested`, `play_pause_requested`, `stop_requested`, `mute_toggled`, `volume_changed`, `aspect_ratio_changed`, `playback_speed_changed`, `audio_track_selected`, `subtitle_track_selected`, `seek_position_requested`, `seek_relative_requested`, `snapshot_requested`, `external_player_requested`, `cinema_mode_requested`, `pip_mode_requested`, `fullscreen_requested`, `video_mouse_moved`
  - **Wichtige Methoden:**
    - [`__init__(logo_cache, parent)`](ui/views/live_tv_view.py#L192) — `L192`
    - [`get_video_hwnd()`](ui/views/live_tv_view.py#L634) — `L634`
    - [`set_channels(channels, genre_map, favorites, recent_ids)`](ui/views/live_tv_view.py#L637) — `L637`
    - [`set_playing_channel(channel)`](ui/views/live_tv_view.py#L659) — `L659`
    - [`update_favorites(favorites)`](ui/views/live_tv_view.py#L670) — `L670`
    - [`update_recent(recent_ids)`](ui/views/live_tv_view.py#L676) — `L676`
    - [`update_epg(ch_id, programs)`](ui/views/live_tv_view.py#L680) — `L680`
    - [`update_probe_telemetry(probe)`](ui/views/live_tv_view.py#L686) — `L686`
    - [`update_live_telemetry(telemetry)`](ui/views/live_tv_view.py#L698) — `L698`
    - [`update_player_state(state)`](ui/views/live_tv_view.py#L778) — `L778`
    - [`set_preview_pixmap(pixmap, badge_text)`](ui/views/live_tv_view.py#L788) — `L788` *(Displays a Standbild preview thumbnail overlay when no live stream is actively playing.)*
    - [`set_preview_jpeg(jpeg_bytes, badge_text)`](ui/views/live_tv_view.py#L798) — `L798` *(Loads JPEG bytes into a QPixmap and displays the preview overlay.)*
    - [`clear_preview()`](ui/views/live_tv_view.py#L808) — `L808` *(Hides the preview thumbnail overlay and restores the native video surface.)*
    - [`update_seek_ui(is_seekable, current_ms, total_ms)`](ui/views/live_tv_view.py#L815) — `L815`
    - [`update_tracks_ui(audio_tracks, sub_tracks)`](ui/views/live_tv_view.py#L833) — `L833`
    - *... und 35 weitere Hilfsmethoden.*

---

### 📄 [`ui/views/scanner_view.py`](ui/views/scanner_view.py) (711 Zeilen)
> Multi-MAC Scanner & Pentest Generator View.
Features 22 OUI Vendor Presets, custom wildcard masks (XX:XX:XX), sequential & random generation,
adaptive WAF/429 Throttle Controller integration, live CPS (Checks/sec) & ETA telemetry,
filterable hit table, and 1-click profile adoption.

#### Klassen & Komponenten
- **[`ScannerView`](ui/views/scanner_view.py#L66-L711)** : *QWidget* — `L66-L711`
  - **Signals**: `start_scan_requested`, `stop_scan_requested`, `pause_scan_requested`, `resume_scan_requested`, `scan_settings_updated`, `apply_mac_requested`, `prepend_db_macs_requested`, `scan_exported`
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/views/scanner_view.py#L76) — `L76`
    - [`set_portal_url(url)`](ui/views/scanner_view.py#L326) — `L326`
    - [`_on_oui_selected(text)`](ui/views/scanner_view.py#L330) — `L330`
    - [`generate_macs()`](ui/views/scanner_view.py#L337) — `L337`
    - [`prepend_macs(macs)`](ui/views/scanner_view.py#L376) — `L376`
    - [`get_candidate_macs()`](ui/views/scanner_view.py#L387) — `L387`
    - [`clear_candidates()`](ui/views/scanner_view.py#L392) — `L392`
    - [`_update_queue_count()`](ui/views/scanner_view.py#L396) — `L396`
    - [`_import_from_file()`](ui/views/scanner_view.py#L400) — `L400`
    - [`_import_from_folder()`](ui/views/scanner_view.py#L414) — `L414`
    - [`_import_from_clipboard()`](ui/views/scanner_view.py#L461) — `L461`
    - [`_deduplicate_list()`](ui/views/scanner_view.py#L467) — `L467`
    - [`_on_start_clicked()`](ui/views/scanner_view.py#L477) — `L477`
    - [`get_scan_threads()`](ui/views/scanner_view.py#L497) — `L497`
    - [`get_scan_delay()`](ui/views/scanner_view.py#L500) — `L500`
    - *... und 13 weitere Hilfsmethoden.*

#### Wichtige Konstanten / Konfigurationen
- `OUI_VENDOR_PRESETS` (L38), `MAC_REGEX` (L63)

---

### 📄 [`ui/views/vod_view.py`](ui/views/vod_view.py) (453 Zeilen)
> VOD (Movies) & Series Browser View.
Uses virtualized QTableView + VODTableModel + VODFilterProxyModel for zero-lag browsing,
coupled with a rich Movie/Series Detail & Poster Card.

#### Klassen & Komponenten
- **[`VODView`](ui/views/vod_view.py#L38-L453)** : *QWidget* — `L38-L453`
  - **Signals**: `mode_changed`, `category_selected`, `portal_search_requested`, `play_vod_requested`, `download_vod_requested`, `copy_vod_url_requested`, `open_series_requested`, `favorite_toggled`, `raw_json_requested`
  - **Wichtige Methoden:**
    - [`__init__(logo_cache, parent)`](ui/views/vod_view.py#L49) — `L49`
    - [`current_mode()`](ui/views/vod_view.py#L272) — `L272`
    - [`_switch_mode(mode)`](ui/views/vod_view.py#L275) — `L275`
    - [`set_categories(categories)`](ui/views/vod_view.py#L293) — `L293`
    - [`set_items(items, favorites)`](ui/views/vod_view.py#L305) — `L305`
    - [`update_favorites(favorites)`](ui/views/vod_view.py#L311) — `L311`
    - [`set_loading(text)`](ui/views/vod_view.py#L318) — `L318`
    - [`_update_status_label()`](ui/views/vod_view.py#L321) — `L321`
    - [`_on_category_changed(idx)`](ui/views/vod_view.py#L327) — `L327`
    - [`_on_local_search_changed(text)`](ui/views/vod_view.py#L333) — `L333`
    - [`_on_portal_search()`](ui/views/vod_view.py#L337) — `L337`
    - [`_on_sort_changed(mode)`](ui/views/vod_view.py#L342) — `L342`
    - [`_on_filter_toggled()`](ui/views/vod_view.py#L345) — `L345`
    - [`_get_item_id(item)`](ui/views/vod_view.py#L351) — `L351`
    - [`_on_row_selected(current, _previous)`](ui/views/vod_view.py#L354) — `L354`
    - *... und 8 weitere Hilfsmethoden.*

---

## 📦 UI - Komponenten & Controls

### 📄 [`ui/components/__init__.py`](ui/components/__init__.py) (14 Zeilen)
> Reusable UI Components for STB Pro v6.0 Qt6 Edition.

---

### 📄 [`ui/components/epg_panel.py`](ui/components/epg_panel.py) (192 Zeilen)
> EPG Now & Next Card Panel Component.
Displays the currently running program with a live progress bar, the upcoming program,
and a button to open the Multi-Day EPG & Catchup Archive Dialog.

#### Klassen & Komponenten
- **[`EPGPanel`](ui/components/epg_panel.py#L26-L192)** : *QFrame* — `L26-L192`
  - **Signals**: `epg_guide_requested`
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/components/epg_panel.py#L29) — `L29`
    - [`resizeEvent(event)`](ui/components/epg_panel.py#L117) — `L117`
    - [`_apply_elided_texts()`](ui/components/epg_panel.py#L121) — `L121`
    - [`update_programs(programs)`](ui/components/epg_panel.py#L139) — `L139`

---

### 📄 [`ui/components/hero_card.py`](ui/components/hero_card.py) (283 Zeilen)
> Hero Channel Banner Card Component.
Displays the currently active/selected channel with Logo, Title, Category,
Live Telemetry Badges (Resolution, Codec, Bitrate, Audio, Buffer Health),
and Quick Action Buttons (Favorite, Probe Stream, Copy URL, Export M3U, Fullscreen).

#### Klassen & Komponenten
- **[`HeroCard`](ui/components/hero_card.py#L25-L283)** : *QFrame* — `L25-L283`
  - **Signals**: `favorite_toggled`, `probe_requested`, `copy_url_requested`, `export_m3u_requested`, `fullscreen_requested`
  - **Wichtige Methoden:**
    - [`__init__(logo_cache, parent)`](ui/components/hero_card.py#L32) — `L32`
    - [`_make_pill(text, bg, fg)`](ui/components/hero_card.py#L133) — `L133`
    - [`resizeEvent(event)`](ui/components/hero_card.py#L144) — `L144`
    - [`_elide_header_labels()`](ui/components/hero_card.py#L148) — `L148`
    - [`set_channel(channel, genre_name, is_fav)`](ui/components/hero_card.py#L159) — `L159`
    - [`set_favorite_state(is_fav)`](ui/components/hero_card.py#L196) — `L196`
    - [`update_probe_telemetry(probe)`](ui/components/hero_card.py#L204) — `L204`
    - [`update_live_telemetry(width, height, bitrate_kbps, buffer_text, fps, video_codec, audio_codec, audio_channels)`](ui/components/hero_card.py#L251) — `L251`

---

### 📄 [`ui/components/sidebar.py`](ui/components/sidebar.py) (453 Zeilen)
> Collapsible Left Sidebar Widget.
Manages Scan-Profiles & Hosts from 'mac_scans/' (Host selection, MAC login selection, Live Hit details),
Quick Connection override, Player Engine selection, Prebuffer preset, Timeout, UI Scaling,
and Connect/Disconnect action.

#### Klassen & Komponenten
- **[`SidebarWidget`](ui/components/sidebar.py#L32-L453)** : *QFrame* — `L32-L453`
  - **Signals**: `host_selected`, `account_selected`, `profile_selected`, `reload_scans_requested`, `connect_requested`, `disconnect_requested`, `quick_fields_changed`, `player_engine_changed`, `prebuffer_preset_changed`, `timeout_changed`, `ui_scale_changed`, `mac_db_requested`
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/components/sidebar.py#L46) — `L46`
    - [`load_scan_repository(repo, default_host, default_mac)`](ui/components/sidebar.py#L285) — `L285` *(Lädt alle Hosts und Logins aus dem Scan-Repository in die Comboboxen.)*
    - [`_on_host_index_changed(index)`](ui/components/sidebar.py#L316) — `L316`
    - [`_populate_logins_for_host(host, target_mac)`](ui/components/sidebar.py#L326) — `L326`
    - [`_on_login_index_changed(index)`](ui/components/sidebar.py#L352) — `L352`
    - [`_apply_account_details(acc, host)`](ui/components/sidebar.py#L364) — `L364`
    - [`_clear_account_details()`](ui/components/sidebar.py#L378) — `L378`
    - [`get_selected_account()`](ui/components/sidebar.py#L385) — `L385`
    - [`get_selected_host()`](ui/components/sidebar.py#L388) — `L388`
    - [`_open_scans_folder()`](ui/components/sidebar.py#L391) — `L391`
    - [`load_profiles(profiles, active_name)`](ui/components/sidebar.py#L407) — `L407` *(Fallback für Abwärtskompatibilität.)*
    - [`display_profile(profile)`](ui/components/sidebar.py#L411) — `L411`
    - [`set_connected_state(connected, busy)`](ui/components/sidebar.py#L418) — `L418`
    - [`_emit_quick_fields()`](ui/components/sidebar.py#L433) — `L433`
    - [`_on_timeout_combo(text)`](ui/components/sidebar.py#L441) — `L441`
    - *... und 1 weitere Hilfsmethoden.*

---

### 📄 [`ui/components/top_bar.py`](ui/components/top_bar.py) (256 Zeilen)
> Top Navigation & Status Bar Component.
Includes View Tabs, Provider Status Pill, REC Indicator, Jobs Badge, Buffer Config,
Sidebar Toggle, Cinema Mode Toggle, PiP Floating Player Toggle, and Fullscreen Toggle.

#### Klassen & Komponenten
- **[`TopNavigationBar`](ui/components/top_bar.py#L22-L256)** : *QFrame* — `L22-L256`
  - **Signals**: `view_changed`, `sidebar_toggled`, `cinema_toggled`, `pip_toggled`, `fullscreen_requested`, `buffer_dialog_requested`, `jobs_dialog_requested`, `account_info_requested`, `record_stop_requested`, `vpn_switch_requested`
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/components/top_bar.py#L34) — `L34`
    - [`resizeEvent(event)`](ui/components/top_bar.py#L182) — `L182`
    - [`_update_provider_elide()`](ui/components/top_bar.py#L188) — `L188`
    - [`set_active_view(view_key)`](ui/components/top_bar.py#L198) — `L198`
    - [`set_provider_status(connected, summary)`](ui/components/top_bar.py#L205) — `L205`
    - [`update_jobs_badge(active_count, total_count)`](ui/components/top_bar.py#L220) — `L220`
    - [`update_rec_indicator(is_recording, label_text)`](ui/components/top_bar.py#L230) — `L230`
    - [`update_vpn_badge(text, status)`](ui/components/top_bar.py#L235) — `L235`

---

## 📦 UI - Dialoge & Overlays

### 📄 [`ui/dialogs/__init__.py`](ui/dialogs/__init__.py) (20 Zeilen)
> Modal & Non-Modal Dialogs for STB Pro v6.0 Qt6 Edition.

---

### 📄 [`ui/dialogs/buffer_dialog.py`](ui/dialogs/buffer_dialog.py) (170 Zeilen)
> Stream Ringbuffer & VLC Network Caching Configuration Dialog.

#### Klassen & Komponenten
- **[`BufferConfigDialog`](ui/dialogs/buffer_dialog.py#L23-L169)** : *QDialog* — `L23-L169`
  - **Wichtige Methoden:**
    - [`__init__(current_cfg, parent)`](ui/dialogs/buffer_dialog.py#L24) — `L24`
    - [`_on_reset_defaults()`](ui/dialogs/buffer_dialog.py#L138) — `L138`
    - [`_on_save()`](ui/dialogs/buffer_dialog.py#L149) — `L149`
    - [`get_config()`](ui/dialogs/buffer_dialog.py#L168) — `L168`

---

### 📄 [`ui/dialogs/epg_guide_dialog.py`](ui/dialogs/epg_guide_dialog.py) (245 Zeilen)
> Multi-Day EPG Program Guide & Timeshift/Catchup Archive Dialog.
Allows browsing programs by date, searching EPG titles, playing archived programs, and downloading them.

#### Klassen & Komponenten
- **[`EPGGuideDialog`](ui/dialogs/epg_guide_dialog.py#L31-L245)** : *QDialog* — `L31-L245`
  - **Signals**: `archive_play_requested`, `archive_download_requested`
  - **Wichtige Methoden:**
    - [`__init__(channel, programs, parent)`](ui/dialogs/epg_guide_dialog.py#L35) — `L35`
    - [`set_programs(programs)`](ui/dialogs/epg_guide_dialog.py#L138) — `L138`
    - [`_populate_days_combo()`](ui/dialogs/epg_guide_dialog.py#L149) — `L149`
    - [`_refresh_table()`](ui/dialogs/epg_guide_dialog.py#L167) — `L167`
    - [`_selected_program()`](ui/dialogs/epg_guide_dialog.py#L218) — `L218`
    - [`_on_selection_changed()`](ui/dialogs/epg_guide_dialog.py#L224) — `L224`
    - [`_on_play_archive()`](ui/dialogs/epg_guide_dialog.py#L236) — `L236`
    - [`_on_dl_archive()`](ui/dialogs/epg_guide_dialog.py#L242) — `L242`

---

### 📄 [`ui/dialogs/jobs_dialog.py`](ui/dialogs/jobs_dialog.py) (135 Zeilen)
> Recordings & Downloads Job Manager Dialog.
Displays live progress, speed, MB downloaded, status, stop action, and 1-click folder opener.

#### Klassen & Komponenten
- **[`JobsDialog`](ui/dialogs/jobs_dialog.py#L25-L135)** : *QDialog* — `L25-L135`
  - **Wichtige Methoden:**
    - [`__init__(recorder_mgr, parent)`](ui/dialogs/jobs_dialog.py#L26) — `L26`
    - [`refresh_jobs()`](ui/dialogs/jobs_dialog.py#L85) — `L85`
    - [`_stop_selected()`](ui/dialogs/jobs_dialog.py#L117) — `L117`
    - [`_clear_finished()`](ui/dialogs/jobs_dialog.py#L125) — `L125`
    - [`_open_output_dir()`](ui/dialogs/jobs_dialog.py#L129) — `L129`

---

### 📄 [`ui/dialogs/json_viewer_dialog.py`](ui/dialogs/json_viewer_dialog.py) (119 Zeilen)
> Interactive JSON & Account Details Viewer Dialog.
Provides both a collapsible QTreeWidget view and formatted JSON text view with search & copy.

#### Klassen & Komponenten
- **[`JsonViewerDialog`](ui/dialogs/json_viewer_dialog.py#L27-L119)** : *QDialog* — `L27-L119`
  - **Wichtige Methoden:**
    - [`__init__(title, data, parent)`](ui/dialogs/json_viewer_dialog.py#L28) — `L28`
    - [`_populate_tree(parent_item, value, key_name)`](ui/dialogs/json_viewer_dialog.py#L83) — `L83`
    - [`_on_filter_tree(query)`](ui/dialogs/json_viewer_dialog.py#L96) — `L96`
    - [`_copy_json()`](ui/dialogs/json_viewer_dialog.py#L118) — `L118`

---

### 📄 [`ui/dialogs/mac_db_dialog.py`](ui/dialogs/mac_db_dialog.py) (211 Zeilen)
> MAC Hit Database Explorer Dialog.
Browses `mac_database.json`, filters by Portal URL or search text, removes duplicates,
exports hits, applies a MAC directly to the active profile, or sends portal MACs to the scanner.

#### Klassen & Komponenten
- **[`MacDatabaseDialog`](ui/dialogs/mac_db_dialog.py#L31-L211)** : *QDialog* — `L31-L211`
  - **Signals**: `apply_mac_requested`, `send_to_scanner_requested`
  - **Wichtige Methoden:**
    - [`__init__(mac_db, parent)`](ui/dialogs/mac_db_dialog.py#L35) — `L35`
    - [`_reload_portals()`](ui/dialogs/mac_db_dialog.py#L121) — `L121`
    - [`refresh_view()`](ui/dialogs/mac_db_dialog.py#L129) — `L129`
    - [`_selected_entry()`](ui/dialogs/mac_db_dialog.py#L160) — `L160`
    - [`_on_apply_selected()`](ui/dialogs/mac_db_dialog.py#L166) — `L166`
    - [`_on_send_to_scanner()`](ui/dialogs/mac_db_dialog.py#L177) — `L177`
    - [`_on_copy_mac()`](ui/dialogs/mac_db_dialog.py#L183) — `L183`
    - [`_on_dedup()`](ui/dialogs/mac_db_dialog.py#L188) — `L188`
    - [`_on_delete_selected()`](ui/dialogs/mac_db_dialog.py#L193) — `L193`
    - [`_on_export()`](ui/dialogs/mac_db_dialog.py#L199) — `L199`

---

### 📄 [`ui/dialogs/profile_dialog.py`](ui/dialogs/profile_dialog.py) (309 Zeilen)
> Profile Editor Dialog (Stalker MAC, Xtream Codes, M3U Playlist).
Fixes the Xtream password bug from the old CustomTkinter version, adds a password eye toggle,
supports renaming profiles, random serial number generation, and MAC-based SHA256 DeviceID calculation.

#### Klassen & Komponenten
- **[`ProfileEditorDialog`](ui/dialogs/profile_dialog.py#L44-L308)** : *QDialog* — `L44-L308`
  - **Wichtige Methoden:**
    - [`__init__(profile_name, profile, is_new, parent)`](ui/dialogs/profile_dialog.py#L45) — `L45`
    - [`_toggle_password_echo()`](ui/dialogs/profile_dialog.py#L227) — `L227`
    - [`_generate_random_sn()`](ui/dialogs/profile_dialog.py#L233) — `L233`
    - [`_calculate_device_ids_from_mac()`](ui/dialogs/profile_dialog.py#L238) — `L238`
    - [`_browse_m3u_file()`](ui/dialogs/profile_dialog.py#L261) — `L261`
    - [`_on_save()`](ui/dialogs/profile_dialog.py#L271) — `L271`
    - [`get_result()`](ui/dialogs/profile_dialog.py#L307) — `L307`

#### Modul-Funktionen
- **[`_normalize_stb_model(model_str)`](ui/dialogs/profile_dialog.py#L34-L41)** — `L34`

---

### 📄 [`ui/dialogs/series_dialog.py`](ui/dialogs/series_dialog.py) (163 Zeilen)
> Series Season & Episode Browser Dialog.
Supports both Xtream Codes (`get_series_info`) and Stalker (`get_ordered_list` seasons/episodes),
with episode search, 1-click playback, direct episode download, and link copy.

#### Klassen & Komponenten
- **[`SeriesBrowserDialog`](ui/dialogs/series_dialog.py#L26-L163)** : *QDialog* — `L26-L163`
  - **Signals**: `episode_play_requested`, `episode_download_requested`, `episode_copy_requested`
  - **Wichtige Methoden:**
    - [`__init__(series_title, seasons_data, parent)`](ui/dialogs/series_dialog.py#L31) — `L31`
    - [`_refresh_episodes()`](ui/dialogs/series_dialog.py#L110) — `L110`
    - [`_selected_episode()`](ui/dialogs/series_dialog.py#L143) — `L143`
    - [`_on_play()`](ui/dialogs/series_dialog.py#L149) — `L149`
    - [`_on_download()`](ui/dialogs/series_dialog.py#L155) — `L155`
    - [`_on_copy()`](ui/dialogs/series_dialog.py#L160) — `L160`

---

## 📦 UI - Virtuelle Models & Delegates

### 📄 [`ui/models/__init__.py`](ui/models/__init__.py) (14 Zeilen)
> Qt6 Virtualized Item Models & Custom Delegates.

---

### 📄 [`ui/models/channel_model.py`](ui/models/channel_model.py) (580 Zeilen)
> Virtualized Channel List Model, Filter Proxy Model, and 120-FPS Custom QPainter Delegate.
Eliminates CustomTkinter's 120-widget creation bottleneck by rendering only visible rows on the GPU.

#### Klassen & Komponenten
- **[`ChannelRoles`](ui/models/channel_model.py#L33-L48)** — `L33-L48`
- **[`ChannelListModel`](ui/models/channel_model.py#L51-L210)** : *QAbstractListModel* — `L51-L210`
  - *High-performance backing model for 50,000+ Live TV channels.*
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/models/channel_model.py#L54) — `L54`
    - [`set_channels(channels, genre_map, favorites, recent_ids)`](ui/models/channel_model.py#L64) — `L64`
    - [`rowCount(parent)`](ui/models/channel_model.py#L79) — `L79`
    - [`channel_at(row)`](ui/models/channel_model.py#L84) — `L84`
    - [`find_channel_by_id(ch_id)`](ui/models/channel_model.py#L89) — `L89`
    - [`set_playing_channel(ch_id)`](ui/models/channel_model.py#L95) — `L95`
    - [`update_favorites(favorites)`](ui/models/channel_model.py#L104) — `L104`
    - [`update_recent(recent_ids)`](ui/models/channel_model.py#L113) — `L113`
    - [`update_channel_health(ch_id, is_alive, latency_ms)`](ui/models/channel_model.py#L122) — `L122`
    - [`update_channel_quality(ch_id, quality_tag)`](ui/models/channel_model.py#L133) — `L133` *(Aktualisiert die tatsächliche Videoauflösung (UHD/FHD/HD/SD) dynamisch im Channel-Objekt und UI.)*
    - [`clear_dead_flags()`](ui/models/channel_model.py#L147) — `L147`
    - [`set_epg_now(ch_id, program_title)`](ui/models/channel_model.py#L158) — `L158`
    - [`notify_logo_updated(logo_url)`](ui/models/channel_model.py#L165) — `L165`
    - [`data(index, role)`](ui/models/channel_model.py#L173) — `L173`
- **[`ChannelFilterProxyModel`](ui/models/channel_model.py#L213-L281)** : *QSortFilterProxyModel* — `L213-L281`
  - *Zero-allocation filter proxy supporting Category, Search, Favorites, Recent, HD/4K, and Dead hiding.*
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/models/channel_model.py#L216) — `L216`
    - [`set_category_id(category_id)`](ui/models/channel_model.py#L224) — `L224`
    - [`set_search_query(query)`](ui/models/channel_model.py#L228) — `L228`
    - [`set_mode_filter(mode)`](ui/models/channel_model.py#L232) — `L232`
    - [`set_hide_dead(hide_dead)`](ui/models/channel_model.py#L236) — `L236`
    - [`filterAcceptsRow(source_row, source_parent)`](ui/models/channel_model.py#L240) — `L240`
- **[`ChannelCardDelegate`](ui/models/channel_model.py#L284-L580)** : *QStyledItemDelegate* — `L284-L580`
  - *Custom QPainter delegate rendering sleek, GPU-accelerated channel cards:*
  - **Signals**: `favorite_clicked`
  - **Wichtige Methoden:**
    - [`__init__(logo_cache, parent)`](ui/models/channel_model.py#L295) — `L295`
    - [`set_profile_name(name)`](ui/models/channel_model.py#L301) — `L301`
    - [`set_thumbnail(ch_id, pixmap_or_bytes)`](ui/models/channel_model.py#L304) — `L304`
    - [`sizeHint(option, index)`](ui/models/channel_model.py#L327) — `L327`
    - [`editorEvent(event, model, option, index)`](ui/models/channel_model.py#L330) — `L330`
    - [`paint(painter, option, index)`](ui/models/channel_model.py#L345) — `L345`

---

### 📄 [`ui/models/vod_model.py`](ui/models/vod_model.py) (236 Zeilen)
> Virtualized VOD & Series Table Model and Sort/Filter Proxy Model.
Handles thousands of Movies and Series items effortlessly without blocking the UI thread.

#### Klassen & Komponenten
- **[`VODRoles`](ui/models/vod_model.py#L17-L24)** — `L17-L24`
- **[`VODTableModel`](ui/models/vod_model.py#L58-L162)** : *QAbstractTableModel* — `L58-L162`
  - *Virtualized table model for Movies (VOD) and Series.*
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/models/vod_model.py#L63) — `L63`
    - [`set_items(items, favorites)`](ui/models/vod_model.py#L68) — `L68`
    - [`set_favorites(favorites)`](ui/models/vod_model.py#L75) — `L75`
    - [`item_at(row)`](ui/models/vod_model.py#L84) — `L84`
    - [`rowCount(parent)`](ui/models/vod_model.py#L89) — `L89`
    - [`columnCount(parent)`](ui/models/vod_model.py#L94) — `L94`
    - [`headerData(section, orientation, role)`](ui/models/vod_model.py#L99) — `L99`
    - [`data(index, role)`](ui/models/vod_model.py#L105) — `L105`
- **[`VODFilterProxyModel`](ui/models/vod_model.py#L165-L236)** : *QSortFilterProxyModel* — `L165-L236`
  - *Supports local instant search, HD filter, Favorites filter, and custom sorting.*
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/models/vod_model.py#L168) — `L168`
    - [`set_search(query)`](ui/models/vod_model.py#L176) — `L176`
    - [`set_hd_only(hd_only)`](ui/models/vod_model.py#L180) — `L180`
    - [`set_fav_only(fav_only)`](ui/models/vod_model.py#L184) — `L184`
    - [`set_sort_mode(mode)`](ui/models/vod_model.py#L188) — `L188`
    - [`filterAcceptsRow(source_row, source_parent)`](ui/models/vod_model.py#L199) — `L199`
    - [`lessThan(left, right)`](ui/models/vod_model.py#L221) — `L221`

#### Modul-Funktionen
- **[`extract_vod_title(item)`](ui/models/vod_model.py#L27-L28)** — `L27`
- **[`extract_vod_year(item)`](ui/models/vod_model.py#L31-L33)** — `L31`
- **[`extract_vod_rating(item)`](ui/models/vod_model.py#L36-L44)** — `L36`
- **[`extract_vod_quality(item)`](ui/models/vod_model.py#L47-L55)** — `L47`

---

## 📦 Automatisierte Test-Suiten

### 📄 [`tests/probe_multi_hosts.py`](tests/probe_multi_hosts.py) (134 Zeilen)
---

### 📄 [`tests/test_scan_profiles.py`](tests/test_scan_profiles.py) (46 Zeilen)
#### Klassen & Komponenten
- **[`TestScanProfiles`](tests/test_scan_profiles.py#L10-L42)** : *unittest.TestCase* — `L10-L42`
  - **Wichtige Methoden:**
    - [`setUp()`](tests/test_scan_profiles.py#L11) — `L11`
    - [`test_01_repo_loads_known_hosts()`](tests/test_scan_profiles.py#L14) — `L14`
    - [`test_02_host_accounts_parsed_and_sorted_by_channels()`](tests/test_scan_profiles.py#L22) — `L22`
    - [`test_03_create_profile_from_scan()`](tests/test_scan_profiles.py#L35) — `L35`

---

### 📄 [`tests/test_ui_and_engine.py`](tests/test_ui_and_engine.py) (844 Zeilen)
> Automated Verification Suite for STB Pro v6.0 Qt6:
1. Responsive UI Layout, Dynamic Scaling & Zero-Overlap / Zero-Truncation Geometry Checks
2. StreamBufferProxy (Ringbuffer, PCR Pacing, Corrupt TS Guard, Wall-Clock Fallback, 0ms Stop)
3. VLCPlayerController (Non-Blocking Async Zapping, Sequence Cancellation, Lock-Free Telemetry)
4. MainWindow Channel Selection Debouncing & Buffering Status Restoration

#### Klassen & Komponenten
- **[`_MockTSHandler`](tests/test_ui_and_engine.py#L54-L87)** : *BaseHTTPRequestHandler* — `L54-L87`
  - **Wichtige Methoden:**
    - [`log_message(format)`](tests/test_ui_and_engine.py#L57) — `L57`
    - [`do_GET()`](tests/test_ui_and_engine.py#L60) — `L60`
- **[`TestUIAndEngine`](tests/test_ui_and_engine.py#L90-L840)** : *unittest.TestCase* — `L90-L840`
  - **Wichtige Methoden:**
    - [`setUpClass(cls)`](tests/test_ui_and_engine.py#L92) — `L92`
    - [`tearDownClass(cls)`](tests/test_ui_and_engine.py#L102) — `L102`
    - [`_assert_no_sibling_overlap(container, label)`](tests/test_ui_and_engine.py#L106) — `L106`
    - [`test_01_ui_scaling_and_non_overlapping_geometries()`](tests/test_ui_and_engine.py#L124) — `L124` *(Verify UI layout across multiple resolutions and UI scales has 0 overlaps and 0 truncated pills.)*
    - [`test_02_stream_buffer_pcr_corrupt_packet_and_fast_stop()`](tests/test_ui_and_engine.py#L261) — `L261` *(Verify StreamBufferProxy ignores TEI corrupt PCR packets, prefills cleanly, and stops in <50ms.)*
    - [`test_03_non_pcr_wall_clock_fallback()`](tests/test_ui_and_engine.py#L306) — `L306` *(Verify non-PCR streams unlock prefill via wall-clock fallback without hanging.)*
    - [`test_04_async_zapping_and_debounce()`](tests/test_ui_and_engine.py#L333) — `L333` *(Verify rapid channel switching never blocks the GUI thread and debounces EPG calls.)*
    - [`test_05_top_bar_tier2_codec_epg_and_blackout()`](tests/test_ui_and_engine.py#L376) — `L376` *(Verify:)*
    - [`test_06_high_bitrate_puffer_no_bloat_and_rebuffer_overlay()`](tests/test_ui_and_engine.py#L461) — `L461` *(Verify 4K/high-bitrate proxy does not choke or bloat to 128MB, and rebuffer overlay updates.)*
    - [`test_07_quality_tag_detection_and_dynamic_resolution_sync()`](tests/test_ui_and_engine.py#L541) — `L541` *(Verify quality_from_dimensions, detect_quality_tag and dynamic UI badge updates from decoded stream.)*
    - [`test_08_group_auto_validation_and_preview_thumbnails()`](tests/test_ui_and_engine.py#L644) — `L644` *(Verify category selection auto-validates on first selection in session and loads thumbnails.)*
    - [`test_scanner_queue_retry_pause_and_folder_extract()`](tests/test_ui_and_engine.py#L700) — `L700` *(Testet die neuen Scanner-Optimierungen: Requeue bei 503/429/Timeout, Pause/Resume, Liste leeren und Ordner-Extraktion.)*
    - [`test_15_snapshot_playing_channel_no_name_error()`](tests/test_ui_and_engine.py#L827) — `L827` *(Verifies _snapshot_playing_channel executes without NameError for THUMB_DIR.)*

#### Modul-Funktionen
- **[`_make_ts_packet(pid, pcr_seconds, tei)`](tests/test_ui_and_engine.py#L34-L51)** — `L34` — *Build a valid 188-byte MPEG-TS packet with optional PCR.*

#### Wichtige Konstanten / Konfigurationen
- `APP_DIR` (L19)

---

### 📄 [`tests/test_vpn_and_stream_errors.py`](tests/test_vpn_and_stream_errors.py) (261 Zeilen)
> Unit Tests für IP- und ISP-Sperren-Erkennung sowie NordVPN-Manager.
Testet JSON-Fehler-Payloads (auch gzipped), HTML-WAF-Sperren,
Länder-Heuristiken und die StreamBuffer-Schutzlogik.

#### Klassen & Komponenten
- **[`TestVpnAndStreamErrors`](tests/test_vpn_and_stream_errors.py#L15-L257)** : *unittest.TestCase* — `L15-L257`
  - **Wichtige Methoden:**
    - [`test_detect_stream_error_valid_ts()`](tests/test_vpn_and_stream_errors.py#L17) — `L17`
    - [`test_detect_stream_error_valid_hls()`](tests/test_vpn_and_stream_errors.py#L22) — `L22`
    - [`test_detect_stream_error_empty()`](tests/test_vpn_and_stream_errors.py#L26) — `L26`
    - [`test_detect_stream_error_ip_ban_json()`](tests/test_vpn_and_stream_errors.py#L29) — `L29`
    - [`test_detect_stream_error_ip_ban_gzip()`](tests/test_vpn_and_stream_errors.py#L40) — `L40`
    - [`test_detect_stream_error_isp_lock_json()`](tests/test_vpn_and_stream_errors.py#L52) — `L52`
    - [`test_detect_stream_error_html_waf()`](tests/test_vpn_and_stream_errors.py#L63) — `L63`
    - [`test_vpn_manager_country_guessing()`](tests/test_vpn_and_stream_errors.py#L69) — `L69`
    - [`test_vpn_manager_cooldown()`](tests/test_vpn_and_stream_errors.py#L79) — `L79`
    - [`test_burned_ips_tracking()`](tests/test_vpn_and_stream_errors.py#L88) — `L88`
    - [`test_rotation_candidates()`](tests/test_vpn_and_stream_errors.py#L113) — `L113`
    - [`test_is_ip_or_stream_ban()`](tests/test_vpn_and_stream_errors.py#L121) — `L121`
    - [`test_probe_stream_triggers_ip_ban_on_511()`](tests/test_vpn_and_stream_errors.py#L134) — `L134`
    - [`test_vpn_manager_clean_disconnect_and_sequence()`](tests/test_vpn_and_stream_errors.py#L167) — `L167`
    - [`test_stream_buffer_aborts_immediately_on_511()`](tests/test_vpn_and_stream_errors.py#L221) — `L221`

---

### 📄 [`tests/manual/test_combinations.py`](tests/manual/test_combinations.py) (56 Zeilen)
---

### 📄 [`tests/manual/test_compare_ids.py`](tests/manual/test_compare_ids.py) (20 Zeilen)
---

### 📄 [`tests/manual/test_darktv.py`](tests/manual/test_darktv.py) (23 Zeilen)
---

### 📄 [`tests/manual/test_darktv_accounts.py`](tests/manual/test_darktv_accounts.py) (28 Zeilen)
---

### 📄 [`tests/manual/test_epg.py`](tests/manual/test_epg.py) (18 Zeilen)
---

### 📄 [`tests/manual/test_multi_streams.py`](tests/manual/test_multi_streams.py) (18 Zeilen)
---

### 📄 [`tests/manual/test_other_portals.py`](tests/manual/test_other_portals.py) (41 Zeilen)
---

### 📄 [`tests/manual/test_probe_headers.py`](tests/manual/test_probe_headers.py) (34 Zeilen)
---

### 📄 [`tests/manual/test_scan_darktv_live.py`](tests/manual/test_scan_darktv_live.py) (35 Zeilen)
---

## 📦 Einstiegspunkt

### 📄 [`main.py`](main.py) (58 Zeilen)
> STB Pro v6.0 — Qt6 / PySide6 Edition Entry Point.
Initializes High-DPI scaling, applies the Obsidian Cyber-Cinema dark theme,
and launches the main application window.

#### Modul-Funktionen
- **[`main()`](main.py#L22-L54)** — `L22`

#### Wichtige Konstanten / Konfigurationen
- `APP_DIR` (L10)

---
