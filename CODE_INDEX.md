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
| `_AsyncTask` | **Class / Widget** | [core/signals.py](core/signals.py#L36-L64) | `L36-L64` | Kapselt eine beliebige Funktion für den globalen QThreadPool. |
| `_attach_inspector_hook` | **Function** | [clients/stb_client.py](clients/stb_client.py#L27-L58) | `L27-L58` | def _attach_inspector_hook(session, enable) |
| `_BottomHudBar` | **Class / Widget** | [player/osd_overlay.py](player/osd_overlay.py#L84-L194) | `L84-L194` | Basis: QWidget |
| `_ChannelDrawerOverlay` | **Class / Widget** | [player/osd_overlay.py](player/osd_overlay.py#L197-L275) | `L197-L275` | Basis: QWidget |
| `_cmd` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L99-L113) | `L99-L113` | def _cmd(url, headers, width, tail) |
| `_Handler` | **Class / Widget** | [core/stream_buffer.py](core/stream_buffer.py#L556-L587) | `L556-L587` | Basis: BaseHTTPRequestHandler |
| `_HLSDetected` | **Class / Widget** | [core/recorder.py](core/recorder.py#L23-L26) | `L23-L26` | Basis: Exception |
| `_make_ts_packet` | **Function** | [tests/test_ui_and_engine.py](tests/test_ui_and_engine.py#L35-L52) | `L35-L52` | Build a valid 188-byte MPEG-TS packet with optional PCR. |
| `_MockTSHandler` | **Class / Widget** | [tests/test_ui_and_engine.py](tests/test_ui_and_engine.py#L55-L90) | `L55-L90` | Basis: BaseHTTPRequestHandler |
| `_normalize_stb_model` | **Function** | [ui/dialogs/profile_dialog.py](ui/dialogs/profile_dialog.py#L34-L41) | `L34-L41` | def _normalize_stb_model(model_str) |
| `_on_response` | **Function** | [clients/stb_client.py](clients/stb_client.py#L31-L56) | `L31-L56` | def _on_response(resp) |
| `_parse_json` | **Function** | [core/stream_probe.py](core/stream_probe.py#L549-L570) | `L549-L570` | def _parse_json(parsed) |
| `_PortalCheckerSignals` | **Class / Widget** | [ui/views/scanner_view.py](ui/views/scanner_view.py#L80-L84) | `L80-L84` | Thread-sichere Qt-Signals für Hintergrund-Prüfungen der Stalker-Portale. |
| `_safe_emit` | **Function** | [core/vpn_manager.py](core/vpn_manager.py#L21-L26) | `L21-L26` | Sicheres Emitten von Qt-Signalen aus Hintergrund-Threads. |
| `_Session` | **Class / Widget** | [core/stream_buffer.py](core/stream_buffer.py#L70-L553) | `L70-L553` | Basis:  |
| `_TopHudBar` | **Class / Widget** | [player/osd_overlay.py](player/osd_overlay.py#L16-L81) | `L16-L81` | Basis: QWidget |
| `_WorkerSignals` | **Class / Widget** | [core/signals.py](core/signals.py#L31-L33) | `L31-L33` | Basis: QObject |
| `AppEventBus` | **Class / Widget** | [core/signals.py](core/signals.py#L10-L28) | `L10-L28` | Zentraler Signal-Bus für die gesamte Applikation. |
| `apply_obsidian_theme` | **Function** | [ui/theme.py](ui/theme.py#L492-L526) | `L492-L526` | Apply dark QPalette and Obsidian Cyber-Cinema QSS stylesheet with dynamic UI scaling. |
| `AppState` | **Class / Widget** | [core/models.py](core/models.py#L663-L685) | `L663-L685` | Zentraler Laufzeit-Zustand der Anwendung. |
| `AsyncWorkerPool` | **Class / Widget** | [core/signals.py](core/signals.py#L67-L112) | `L67-L112` | Hochperformanter Thread-Pool auf Basis von Qt QThreadPool. |
| `BufferConfigDialog` | **Class / Widget** | [ui/dialogs/buffer_dialog.py](ui/dialogs/buffer_dialog.py#L23-L169) | `L23-L169` | Basis: QDialog |
| `BufferSettings` | **Class / Widget** | [core/stream_buffer.py](core/stream_buffer.py#L22-L67) | `L22-L67` | Basis:  |
| `build_m3u_playlist` | **Function** | [core/m3u_exporter.py](core/m3u_exporter.py#L10-L44) | `L10-L44` | def build_m3u_playlist(channels, user_agent, resolve_url_fn) |
| `Channel` | **Class / Widget** | [core/models.py](core/models.py#L184-L289) | `L184-L289` | Basis:  |
| `ChannelCardDelegate` | **Class / Widget** | [ui/models/channel_model.py](ui/models/channel_model.py#L284-L580) | `L284-L580` | Custom QPainter delegate rendering sleek, GPU-accelerated channel cards: |
| `ChannelFilterProxyModel` | **Class / Widget** | [ui/models/channel_model.py](ui/models/channel_model.py#L213-L281) | `L213-L281` | Zero-allocation filter proxy supporting Category, Search, Favorites, Recent, HD/4K, and De... |
| `ChannelListModel` | **Class / Widget** | [ui/models/channel_model.py](ui/models/channel_model.py#L51-L210) | `L51-L210` | High-performance backing model for 50,000+ Live TV channels. |
| `ChannelRoles` | **Class / Widget** | [ui/models/channel_model.py](ui/models/channel_model.py#L33-L48) | `L33-L48` | Basis:  |
| `check_mac_account` | **Function** | [clients/stb_client.py](clients/stb_client.py#L206-L374) | `L206-L374` | Prüft einen einzelnen MAC-Account schnell im Hintergrund mit voller Boost-Konfigurierbarke... |
| `check_single_portal` | **Function** | [core/portal_checker.py](core/portal_checker.py#L482-L626) | `L482-L626` | Prüft einen einzelnen Portal-Host rigoros auf echte Stalker/Ministra-Erreichbarkeit, |
| `ConfigManager` | **Class / Widget** | [core/config_manager.py](core/config_manager.py#L60-L334) | `L60-L334` | Verwaltet Profile, Live-/VOD-Favoriten, Verlauf, Player-Pfade und UI-Einstellungen. |
| `ConsoleView` | **Class / Widget** | [ui/views/console_view.py](ui/views/console_view.py#L26-L156) | `L26-L156` | Basis: QWidget |
| `decode_vlc_fourcc` | **Function** | [player/vlc_controller.py](player/vlc_controller.py#L20-L101) | `L20-L101` | def decode_vlc_fourcc(codec_val) |
| `detect_ffplay_path` | **Function** | [core/config_manager.py](core/config_manager.py#L48-L57) | `L48-L57` | def detect_ffplay_path() |
| `detect_mpv_path` | **Function** | [core/config_manager.py](core/config_manager.py#L36-L45) | `L36-L45` | def detect_mpv_path() |
| `detect_quality_tag` | **Function** | [core/models.py](core/models.py#L153-L180) | `L153-L180` | Erkennt den Qualitäts-Tag AUSSCHLIESSLICH anhand von echten Dimensionsdaten in den Metadat... |
| `detect_stream_error_payload` | **Function** | [core/stream_probe.py](core/stream_probe.py#L332-L399) | `L332-L399` | Erkennt versteckte Fehler-Payloads (z. B. IP_BAN, ISP_LOCK_FAILED, Geo-Blocks), |
| `detect_vlc_path` | **Function** | [core/config_manager.py](core/config_manager.py#L19-L33) | `L19-L33` | def detect_vlc_path() |
| `diagnose_iptv_status` | **Function** | [core/stream_probe.py](core/stream_probe.py#L311-L329) | `L311-L329` | Diagnostiziert proprietäre/spezifische HTTP-Statuscodes von IPTV- und Streaming-Clustern. |
| `emit_scanner_connection_error_log` | **Function** | [clients/stb_client.py](clients/stb_client.py#L71-L141) | `L71-L141` | Sporadisches / gesampeltes Logging von Verbindungs- und Timeout-Fehlern während des MAC-Sc... |
| `EPGGuideDialog` | **Class / Widget** | [ui/dialogs/epg_guide_dialog.py](ui/dialogs/epg_guide_dialog.py#L31-L254) | `L31-L254` | Basis: QDialog |
| `EPGPanel` | **Class / Widget** | [ui/components/epg_panel.py](ui/components/epg_panel.py#L26-L192) | `L26-L192` | Basis: QFrame |
| `EPGProgram` | **Class / Widget** | [core/models.py](core/models.py#L293-L451) | `L293-L451` | Basis:  |
| `ExternalPlayerRunner` | **Class / Widget** | [player/external_player.py](player/external_player.py#L11-L124) | `L11-L124` | Basis:  |
| `extract_portal_urls_from_folder` | **Function** | [core/portal_checker.py](core/portal_checker.py#L288-L321) | `L288-L321` | Durchsucht alle .txt-Dateien eines Ordners rekursiv nach Stalker Portal-URLs. |
| `extract_portal_urls_from_text` | **Function** | [core/portal_checker.py](core/portal_checker.py#L214-L285) | `L214-L285` | Extrahiert Stalker-Portal-URLs aus einem Textstring (z. B. aus TXT-Listen, Logs, M3U). |
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
| `format_mac_str` | **Function** | [core/mac_database.py](core/mac_database.py#L21-L25) | `L21-L25` | def format_mac_str(mac) |
| `format_resolution` | **Function** | [core/stream_probe.py](core/stream_probe.py#L88-L104) | `L88-L104` | def format_resolution(width, height, fps) |
| `FullscreenOSDOverlay` | **Class / Widget** | [player/osd_overlay.py](player/osd_overlay.py#L278-L396) | `L278-L396` | Koordiniert Top-HUD, Bottom-HUD, Uhrzeit-Timer, Auto-Hide und den Quick-Channel-Drawer. |
| `get_portal_candidate_endpoints` | **Function** | [core/portal_checker.py](core/portal_checker.py#L444-L479) | `L444-L479` | Generiert typische Stalker/Ministra-Endpunkte für Handshake-Probes. |
| `grab_thumbnail` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L216-L280) | `L216-L280` | High-Performance Standalone Thumbnail Grabber. |
| `HeroCard` | **Class / Widget** | [ui/components/hero_card.py](ui/components/hero_card.py#L25-L283) | `L25-L283` | Basis: QFrame |
| `HttpLogEntry` | **Class / Widget** | [core/models.py](core/models.py#L614-L660) | `L614-L660` | Basis:  |
| `InspectorView` | **Class / Widget** | [ui/views/inspector_view.py](ui/views/inspector_view.py#L32-L275) | `L32-L275` | Basis: QWidget |
| `int_to_mac` | **Function** | [core/pattern_predictor.py](core/pattern_predictor.py#L42-L45) | `L42-L45` | Konvertiert eine 48-Bit-Ganzzahl in eine formatierte MAC-Adresse. |
| `is_blank_or_black_jpeg` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L40-L61) | `L40-L61` | Erkennt korrupte, leere oder rein schwarze Dummy-Frames zuverlässig. |
| `is_ip_or_stream_ban` | **Function** | [core/stream_probe.py](core/stream_probe.py#L295-L308) | `L295-L308` | Ermittelt zuverlässig, ob ein HTTP-Statuscode oder Fehlertext auf |
| `is_stalker_response` | **Function** | [core/portal_checker.py](core/portal_checker.py#L395-L441) | `L395-L441` | Prüft eine HTTP-Response rigoros auf definitive Stalker / Ministra Signaturen. |
| `is_valid_expire_date` | **Function** | [core/models.py](core/models.py#L29-L131) | `L29-L131` | Prüft, ob ein Ablaufdatum-Wert gültig und aktiv (in der Zukunft oder unbegrenzt) ist. |
| `is_valid_portal_hostname` | **Function** | [core/portal_checker.py](core/portal_checker.py#L162-L211) | `L162-L211` | Validiert streng, ob ein Hostname eine reale Internet-Domain oder IPv4-Adresse darstellt. |
| `Job` | **Class / Widget** | [core/recorder.py](core/recorder.py#L56-L118) | `L56-L118` | Basis:  |
| `JobsDialog` | **Class / Widget** | [ui/dialogs/jobs_dialog.py](ui/dialogs/jobs_dialog.py#L25-L138) | `L25-L138` | Basis: QDialog |
| `JsonViewerDialog` | **Class / Widget** | [ui/dialogs/json_viewer_dialog.py](ui/dialogs/json_viewer_dialog.py#L27-L119) | `L27-L119` | Basis: QDialog |
| `LiveTVView` | **Class / Widget** | [ui/views/live_tv_view.py](ui/views/live_tv_view.py#L155-L1199) | `L155-L1199` | Basis: QWidget |
| `load_cached_thumb` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L120-L133) | `L120-L133` | def load_cached_thumb(key) |
| `load_portal_list` | **Function** | [core/portal_checker.py](core/portal_checker.py#L348-L376) | `L348-L376` | Liest eine Stalker-Portal-Datei (.txt) ein, bereinigt Kommentare und |
| `LogoCache` | **Class / Widget** | [core/logo_cache.py](core/logo_cache.py#L22-L151) | `L22-L151` | Lädt Kanal-Logos und VOD-Poster im Hintergrund als QImage (Thread-sicher!) |
| `mac_to_int` | **Function** | [core/pattern_predictor.py](core/pattern_predictor.py#L34-L39) | `L34-L39` | Konvertiert eine MAC-Adresse in eine 48-Bit-Ganzzahl. |
| `MacClusterPattern` | **Class / Widget** | [core/pattern_predictor.py](core/pattern_predictor.py#L15-L23) | `L15-L23` | Repräsentiert ein identifiziertes MAC-Muster oder Cluster. |
| `MacDatabase` | **Class / Widget** | [core/mac_database.py](core/mac_database.py#L28-L262) | `L28-L262` | Persistente, threadsichere Datenbank für gefundene MAC-Adressen mit Sendern. |
| `MacDatabaseDialog` | **Class / Widget** | [ui/dialogs/mac_db_dialog.py](ui/dialogs/mac_db_dialog.py#L32-L265) | `L32-L265` | Basis: QDialog |
| `MacPatternDialog` | **Class / Widget** | [ui/dialogs/mac_pattern_dialog.py](ui/dialogs/mac_pattern_dialog.py#L33-L308) | `L33-L308` | Dialog für die Mustererkennung und Permutations-Generierung. |
| `MacPatternPredictor` | **Class / Widget** | [core/pattern_predictor.py](core/pattern_predictor.py#L48-L197) | `L48-L197` | Analysiert MAC-Treffer auf wiederkehrende Muster und generiert |
| `main` | **Function** | [main.py](main.py#L22-L54) | `L22-L54` | def main() |
| `MainWindow` | **Class / Widget** | [ui/main_window.py](ui/main_window.py#L106-L3121) | `L106-L3121` | Basis: QMainWindow |
| `MultiPortalScanScheduler` | **Class / Widget** | [core/scan_scheduler.py](core/scan_scheduler.py#L58-L596) | `L58-L596` | Thread-sicherer Work-Scheduler für Multi-Portal MAC-Scans mit intelligenter |
| `NordVpnManager` | **Class / Widget** | [core/vpn_manager.py](core/vpn_manager.py#L29-L653) | `L29-L653` | Verwaltet die Integration mit NordVPN unter Windows. |
| `normalize_mac` | **Function** | [core/pattern_predictor.py](core/pattern_predictor.py#L26-L31) | `L26-L31` | Bereinigt und formatiert eine MAC-Adresse nach XX:XX:XX:XX:XX:XX. |
| `normalize_portal_url` | **Function** | [core/portal_checker.py](core/portal_checker.py#L324-L345) | `L324-L345` | Normalisiert eine Portal-URL sauber (Protokoll, Leerzeichen, Format). |
| `parse_sps_from_h264` | **Function** | [core/stream_probe.py](core/stream_probe.py#L107-L208) | `L107-L208` | Decodiert H.264 Sequence Parameter Set (SPS) direkt in (width, height) ohne externe Tools. |
| `pcr_bitrate_kbps` | **Function** | [core/stream_probe.py](core/stream_probe.py#L38-L66) | `L38-L66` | Echte Mux-Bitrate aus MPEG-TS-PCR. |
| `PortalCheckResult` | **Class / Widget** | [core/portal_checker.py](core/portal_checker.py#L34-L93) | `L34-L93` | Repräsentiert das Prüfergebnis eines einzelnen Stalker-Portals. |
| `PreviewOverlayWidget` | **Class / Widget** | [ui/views/live_tv_view.py](ui/views/live_tv_view.py#L86-L152) | `L86-L152` | Standbild-Preview Thumbnail Overlay displayed inside the video viewport when |
| `probe_stream` | **Function** | [core/stream_probe.py](core/stream_probe.py#L402-L614) | `L402-L614` | def probe_stream(url, user_agent, cookies, timeout, sample_duration, cancel, skip_ffprobe,... |
| `Profile` | **Class / Widget** | [core/models.py](core/models.py#L455-L574) | `L455-L574` | Basis:  |
| `ProfileEditorDialog` | **Class / Widget** | [ui/dialogs/profile_dialog.py](ui/dialogs/profile_dialog.py#L44-L308) | `L44-L308` | Basis: QDialog |
| `quality_from_dimensions` | **Function** | [core/models.py](core/models.py#L135-L150) | `L135-L150` | Ermittelt den Qualitäts-Tag (UHD/FHD/HD/SD) exakt anhand von Pixel-Dimensionen. |
| `read_bit` | **Function** | [core/stream_probe.py](core/stream_probe.py#L124-L133) | `L124-L133` | def read_bit() |
| `read_bits` | **Function** | [core/stream_probe.py](core/stream_probe.py#L135-L139) | `L135-L139` | def read_bits(count) |
| `read_se` | **Function** | [core/stream_probe.py](core/stream_probe.py#L149-L151) | `L149-L151` | def read_se() |
| `read_ue` | **Function** | [core/stream_probe.py](core/stream_probe.py#L141-L147) | `L141-L147` | def read_ue() |
| `Recorder` | **Class / Widget** | [core/recorder.py](core/recorder.py#L121-L435) | `L121-L435` | Basis:  |
| `safe_name` | **Function** | [core/recorder.py](core/recorder.py#L29-L31) | `L29-L31` | def safe_name(name, maxlen) |
| `save_reachable_portals_file` | **Function** | [core/portal_checker.py](core/portal_checker.py#L379-L392) | `L379-L392` | Speichert eine Liste erreichbarer Portal-URLs zeilenweise in eine .txt-Datei. |
| `save_thumb` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L136-L144) | `L136-L144` | def save_thumb(key, data) |
| `ScanAccount` | **Class / Widget** | [core/scan_repository.py](core/scan_repository.py#L24-L58) | `L24-L58` | Repräsentiert einen einzelnen gescannten MAC-Account eines Portals. |
| `ScanHost` | **Class / Widget** | [core/scan_repository.py](core/scan_repository.py#L62-L85) | `L62-L85` | Repräsentiert einen Host / ein Portal mit allen zugehörigen Logins. |
| `ScannerView` | **Class / Widget** | [ui/views/scanner_view.py](ui/views/scanner_view.py#L87-L1466) | `L87-L1466` | Basis: QWidget |
| `ScanRepository` | **Class / Widget** | [core/scan_repository.py](core/scan_repository.py#L88-L264) | `L88-L264` | Verwaltet das Einlesen, Filtern und Cachen aller Scan-Dateien aus 'mac_scans/'. |
| `ScanResult` | **Class / Widget** | [core/models.py](core/models.py#L600-L610) | `L600-L610` | Basis:  |
| `ScanRotationMode` | **Class / Widget** | [core/scan_scheduler.py](core/scan_scheduler.py#L21-L55) | `L21-L55` | Konstanten für Multi-Portal Rotations- und Scan-Modi. |
| `ScanThrottleController` | **Class / Widget** | [clients/throttle.py](clients/throttle.py#L11-L69) | `L11-L69` | Basis:  |
| `SeriesBrowserDialog` | **Class / Widget** | [ui/dialogs/series_dialog.py](ui/dialogs/series_dialog.py#L26-L170) | `L26-L170` | Basis: QDialog |
| `SettingsView` | **Class / Widget** | [ui/views/settings_view.py](ui/views/settings_view.py#L45-L968) | `L45-L968` | Basis: QWidget |
| `SidebarWidget` | **Class / Widget** | [ui/components/sidebar.py](ui/components/sidebar.py#L32-L453) | `L32-L453` | Basis: QFrame |
| `StalkerPortalChecker` | **Class / Widget** | [core/portal_checker.py](core/portal_checker.py#L629-L839) | `L629-L839` | Multi-threaded Stalker Portal Prüf-Engine. |
| `StbClient` | **Class / Widget** | [clients/stb_client.py](clients/stb_client.py#L151-L203) | `L151-L203` | Erweiterter Stalker/Ministra Client mit automatischem Inspector-Logging |
| `StreamBufferProxy` | **Class / Widget** | [core/stream_buffer.py](core/stream_buffer.py#L590-L634) | `L590-L634` | Basis:  |
| `StreamProbeResult` | **Class / Widget** | [core/models.py](core/models.py#L578-L596) | `L578-L596` | Basis:  |
| `TestAntiBanShieldLogic` | **Class / Widget** | [tests/test_pattern_predictor_and_antiban.py](tests/test_pattern_predictor_and_antiban.py#L141-L196) | `L141-L196` | Tests für die Anti-Ban Erkennung und den 45s-Cooldown. |
| `TestExpireDateValidation` | **Class / Widget** | [tests/test_expire_validation.py](tests/test_expire_validation.py#L16-L118) | `L16-L118` | Tests für is_valid_expire_date Hilfsfunktion. |
| `TestMacDatabaseExpireFilter` | **Class / Widget** | [tests/test_expire_validation.py](tests/test_expire_validation.py#L121-L229) | `L121-L229` | Tests für MacDatabase Filterung ungültiger Ablaufdaten. |
| `TestMacDatabaseVpnLocation` | **Class / Widget** | [tests/test_pattern_predictor_and_antiban.py](tests/test_pattern_predictor_and_antiban.py#L113-L138) | `L113-L138` | Tests für Speicherung und Auslesen von VPN-Standorten in MacDatabase. |
| `TestMacPatternPredictor` | **Class / Widget** | [tests/test_pattern_predictor_and_antiban.py](tests/test_pattern_predictor_and_antiban.py#L21-L110) | `L21-L110` | Tests für MacPatternPredictor Analyse und Permutationen. |
| `TestPatternPredictorUiIntegration` | **Class / Widget** | [tests/test_pattern_predictor_and_antiban.py](tests/test_pattern_predictor_and_antiban.py#L199-L281) | `L199-L281` | Tests für UI-Integration und Signalübergabe des Pattern-Prädiktors. |
| `TestPortalChecker` | **Class / Widget** | [tests/test_portal_checker.py](tests/test_portal_checker.py#L26-L532) | `L26-L532` | Basis: unittest.TestCase |
| `TestScanProfiles` | **Class / Widget** | [tests/test_scan_profiles.py](tests/test_scan_profiles.py#L10-L42) | `L10-L42` | Basis: unittest.TestCase |
| `TestScanScheduler` | **Class / Widget** | [tests/test_scan_scheduler.py](tests/test_scan_scheduler.py#L13-L474) | `L13-L474` | Basis: unittest.TestCase |
| `TestScanSchedulerExpireHandling` | **Class / Widget** | [tests/test_expire_validation.py](tests/test_expire_validation.py#L232-L293) | `L232-L293` | Tests für MultiPortalScanScheduler mit 0000000 / ungültigen Ablaufdaten. |
| `TestSettingsAndSidebar` | **Class / Widget** | [tests/test_settings_and_sidebar.py](tests/test_settings_and_sidebar.py#L25-L301) | `L25-L301` | Basis: unittest.TestCase |
| `TestUIAndEngine` | **Class / Widget** | [tests/test_ui_and_engine.py](tests/test_ui_and_engine.py#L93-L843) | `L93-L843` | Basis: unittest.TestCase |
| `TestVpnAndStreamErrors` | **Class / Widget** | [tests/test_vpn_and_stream_errors.py](tests/test_vpn_and_stream_errors.py#L15-L330) | `L15-L330` | Basis: unittest.TestCase |
| `ThemeColors` | **Class / Widget** | [ui/theme.py](ui/theme.py#L11-L43) | `L11-L43` | Design tokens matching and refining the Obsidian Cyber-Cinema palette. |
| `thumb_age_s` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L147-L151) | `L147-L151` | def thumb_age_s(key) |
| `thumb_path` | **Function** | [core/preview_grabber.py](core/preview_grabber.py#L116-L117) | `L116-L117` | def thumb_path(key) |
| `ThumbGrabber` | **Class / Widget** | [core/preview_grabber.py](core/preview_grabber.py#L154-L213) | `L154-L213` | Holt genau ein Standbild; cancel() beendet ffmpeg sofort. |
| `TopNavigationBar` | **Class / Widget** | [ui/components/top_bar.py](ui/components/top_bar.py#L22-L266) | `L22-L266` | Basis: QFrame |
| `VideoSurfaceWidget` | **Class / Widget** | [ui/views/live_tv_view.py](ui/views/live_tv_view.py#L52-L83) | `L52-L83` | Dedicated native HWND container for LibVLC Direct3D11/OpenGL rendering. |
| `VLCPlayerController` | **Class / Widget** | [player/vlc_controller.py](player/vlc_controller.py#L108-L683) | `L108-L683` | Steuert die integrierte LibVLC-Instanz mit HWND-Binding, PCR-Ringpuffer-Proxy |
| `VODFilterProxyModel` | **Class / Widget** | [ui/models/vod_model.py](ui/models/vod_model.py#L165-L244) | `L165-L244` | Supports local instant search, HD filter, Favorites filter, and custom sorting. |
| `VODRoles` | **Class / Widget** | [ui/models/vod_model.py](ui/models/vod_model.py#L17-L24) | `L17-L24` | Basis:  |
| `VODTableModel` | **Class / Widget** | [ui/models/vod_model.py](ui/models/vod_model.py#L58-L162) | `L58-L162` | Virtualized table model for Movies (VOD) and Series. |
| `VODView` | **Class / Widget** | [ui/views/vod_view.py](ui/views/vod_view.py#L38-L454) | `L38-L454` | Basis: QWidget |
| `XtreamClient` | **Class / Widget** | [clients/xtream_client.py](clients/xtream_client.py#L20-L129) | `L20-L129` | Basis: _BaseXtreamClient |

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

### 📄 [`clients/stb_client.py`](clients/stb_client.py) (374 Zeilen)
> Stalker / Ministra STB Client für STB Pro Qt6.
Erweitert den bewährten StbClient um Live-HTTP-Telemetrie für den interaktiven Protokoll-Inspector
(inklusive Request-Historie, Header-Capturing und cURL-Export).

#### Klassen & Komponenten
- **[`StbClient`](clients/stb_client.py#L151-L203)** : *_BaseStbClient* — `L151-L203`
  - *Erweiterter Stalker/Ministra Client mit automatischem Inspector-Logging*
  - **Wichtige Methoden:**
    - [`__init__(portal_url, mac, model, serial_number, device_id, device_id2, signature, user_agent, timeout, normalized_load_url, enable_inspector, verify_ssl, session, connect_timeout, read_timeout, device_id_mode)`](clients/stb_client.py#L156) — `L156`

#### Modul-Funktionen
- **[`_attach_inspector_hook(session, enable)`](clients/stb_client.py#L27-L58)** — `L27`
- **[`_on_response(resp)`](clients/stb_client.py#L31-L56)** — `L31`
- **[`emit_scanner_connection_error_log(portal_url, mac, error_msg, endpoint, status_code, headers, params, elapsed_ms, sample_interval, sample_frequency)`](clients/stb_client.py#L71-L141)** — `L71` — *Sporadisches / gesampeltes Logging von Verbindungs- und Timeout-Fehlern während des MAC-Scannens*
- **[`check_mac_account(portal_url, mac, model, device_id, device_id2, serial_number, signature, timeout, normalized_load_url, session, verify_ssl, genre_param, sortby_param, fallback_get_all, device_id_mode, enable_error_log)`](clients/stb_client.py#L206-L374)** — `L206` — *Prüft einen einzelnen MAC-Account schnell im Hintergrund mit voller Boost-Konfigurierbarkeit.*

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

### 📄 [`clients/xtream_client.py`](clients/xtream_client.py) (129 Zeilen)
> Xtream Codes API Client für STB Pro Qt6.
Mit automatischer HTTP-Telemetrie für den Protokoll-Inspector sowie Serien-API-Unterstützung.

#### Klassen & Komponenten
- **[`XtreamClient`](clients/xtream_client.py#L20-L129)** : *_BaseXtreamClient* — `L20-L129`
  - **Wichtige Methoden:**
    - [`__init__(server_url, username, password, output_format, timeout, user_agent, enable_inspector, verify_ssl, connect_timeout, read_timeout)`](clients/xtream_client.py#L21) — `L21`
    - [`get_series_categories()`](clients/xtream_client.py#L52) — `L52`
    - [`get_series(category_id, page)`](clients/xtream_client.py#L68) — `L68`
    - [`get_series_info(series_id)`](clients/xtream_client.py#L94) — `L94`

#### Wichtige Konstanten / Konfigurationen
- `_APP_DIR` (L9), `_PARENT_DIR` (L10)

---

## 📦 Core (Business Logic, Cache & DB)

### 📄 [`core/__init__.py`](core/__init__.py) (41 Zeilen)
> Core-Paket für STB Pro Qt6.
Enthält Datenmodelle, Event-Bus, Persistenz, Stream-Puffer, Probing und Recording.

---

### 📄 [`core/config_manager.py`](core/config_manager.py) (335 Zeilen)
> Konfigurations-Manager für STB Pro Qt6.
Unterstützt nahtlose Übernahme der bestehenden config.json aus dem Hauptverzeichnis,
damit alle gespeicherten Profile, Favoriten und Einstellungen erhalten bleiben.
Zusätzlich neu: Persistente VOD-Favoriten und Recently-Played-Historie!

#### Klassen & Komponenten
- **[`ConfigManager`](core/config_manager.py#L60-L334)** — `L60-L334`
  - *Verwaltet Profile, Live-/VOD-Favoriten, Verlauf, Player-Pfade und UI-Einstellungen.*
  - **Wichtige Methoden:**
    - [`__init__(filepath)`](core/config_manager.py#L63) — `L63`
    - [`_default_config()`](core/config_manager.py#L75) — `L75`
    - [`_load()`](core/config_manager.py#L173) — `L173`
    - [`save()`](core/config_manager.py#L191) — `L191`
    - [`get(key, default)`](core/config_manager.py#L210) — `L210`
    - [`set(key, value, auto_save)`](core/config_manager.py#L213) — `L213`
    - [`get_profiles()`](core/config_manager.py#L218) — `L218`
    - [`get_profile(name)`](core/config_manager.py#L223) — `L223`
    - [`save_profile(profile, old_name)`](core/config_manager.py#L229) — `L229`
    - [`delete_profile(name)`](core/config_manager.py#L241) — `L241`
    - [`get_favorites(profile_name)`](core/config_manager.py#L253) — `L253`
    - [`save_favorites(profile_name, favorites)`](core/config_manager.py#L257) — `L257`
    - [`get_vod_favorites(profile_name)`](core/config_manager.py#L263) — `L263`
    - [`save_vod_favorites(profile_name, favorites)`](core/config_manager.py#L267) — `L267`
    - [`get_recently_played(profile_name)`](core/config_manager.py#L273) — `L273`
    - *... und 7 weitere Hilfsmethoden.*

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

### 📄 [`core/mac_database.py`](core/mac_database.py) (263 Zeilen)
> Persistente, threadsichere MAC-Hit-Datenbank für STB Pro Qt6.
Synchronisiert sich automatisch mit einer vorhandenen mac_database.json im Hauptordner.

#### Klassen & Komponenten
- **[`MacDatabase`](core/mac_database.py#L28-L262)** — `L28-L262`
  - *Persistente, threadsichere Datenbank für gefundene MAC-Adressen mit Sendern.*
  - **Wichtige Methoden:**
    - [`__init__(filepath)`](core/mac_database.py#L34) — `L34`
    - [`_load()`](core/mac_database.py#L46) — `L46`
    - [`_save()`](core/mac_database.py#L59) — `L59`
    - [`save_found_mac(portal_url, res)`](core/mac_database.py#L76) — `L76`
    - [`get_known_macs(portal_url)`](core/mac_database.py#L135) — `L135`
    - [`get_all_records(portal_url)`](core/mac_database.py#L158) — `L158`
    - [`get_portals()`](core/mac_database.py#L167) — `L167`
    - [`delete_entry(mac, portal_url)`](core/mac_database.py#L171) — `L171`
    - [`clean_duplicates()`](core/mac_database.py#L194) — `L194`
    - [`get_count()`](core/mac_database.py#L230) — `L230`
    - [`total_count()`](core/mac_database.py#L234) — `L234`
    - [`has_portal_entries(portal_url)`](core/mac_database.py#L237) — `L237`
    - [`get_entries(portal_url)`](core/mac_database.py#L245) — `L245`
    - [`deduplicate()`](core/mac_database.py#L258) — `L258`
    - [`remove_entry(portal_url, mac)`](core/mac_database.py#L261) — `L261`

#### Modul-Funktionen
- **[`format_mac_str(mac)`](core/mac_database.py#L21-L25)** — `L21`

#### Wichtige Konstanten / Konfigurationen
- `APP_DIR` (L15), `PARENT_DIR` (L16), `LOCAL_DB_FILE` (L17), `PARENT_DB_FILE` (L18)

---

### 📄 [`core/models.py`](core/models.py) (685 Zeilen)
> Datenmodelle (Dataclasses) für STB Pro Qt6.
Strikt typisiert und unabhängig von UI-Komponenten.

#### Klassen & Komponenten
- **[`Channel`](core/models.py#L184-L289)** — `L184-L289`
  - **Wichtige Methoden:**
    - [`__post_init__()`](core/models.py#L201) — `L201`
    - [`__hash__()`](core/models.py#L205) — `L205`
    - [`__eq__(other)`](core/models.py#L208) — `L208`
    - [`tv_genre_id()`](core/models.py#L214) — `L214`
    - [`tv_genre_id(val)`](core/models.py#L218) — `L218`
    - [`fav()`](core/models.py#L222) — `L222`
    - [`fav(val)`](core/models.py#L226) — `L226`
    - [`is_hls()`](core/models.py#L230) — `L230`
    - [`has_archive()`](core/models.py#L234) — `L234`
    - [`enable_tv_archive()`](core/models.py#L243) — `L243`
    - [`flags_summary()`](core/models.py#L247) — `L247`
    - [`from_raw(cls, raw, genre_map)`](core/models.py#L269) — `L269`
- **[`EPGProgram`](core/models.py#L293-L451)** — `L293-L451`
  - **Wichtige Methoden:**
    - [`name()`](core/models.py#L308) — `L308`
    - [`descr()`](core/models.py#L312) — `L312`
    - [`time_str()`](core/models.py#L316) — `L316`
    - [`time_to_str()`](core/models.py#L320) — `L320`
    - [`progress_percent()`](core/models.py#L324) — `L324`
    - [`progress()`](core/models.py#L353) — `L353`
    - [`remaining_minutes()`](core/models.py#L357) — `L357`
    - [`from_raw(cls, raw)`](core/models.py#L370) — `L370`
- **[`Profile`](core/models.py#L455-L574)** — `L455-L574`
  - **Wichtige Methoden:**
    - [`from_dict(cls, data)`](core/models.py#L474) — `L474`
    - [`to_dict()`](core/models.py#L494) — `L494`
    - [`portal_type()`](core/models.py#L515) — `L515`
    - [`portal_type(val)`](core/models.py#L524) — `L524`
    - [`url()`](core/models.py#L534) — `L534`
    - [`url(val)`](core/models.py#L543) — `L543`
    - [`server_url()`](core/models.py#L552) — `L552`
    - [`server_url(val)`](core/models.py#L556) — `L556`
    - [`m3u_url()`](core/models.py#L562) — `L562`
    - [`m3u_url(val)`](core/models.py#L566) — `L566`
    - [`clone(new_name)`](core/models.py#L571) — `L571`
- **[`StreamProbeResult`](core/models.py#L578-L596)** — `L578-L596`
- **[`ScanResult`](core/models.py#L600-L610)** — `L600-L610`
- **[`HttpLogEntry`](core/models.py#L614-L660)** — `L614-L660`
  - **Wichtige Methoden:**
    - [`create(cls, method, url, status_code, elapsed_ms, headers, params, body)`](core/models.py#L625) — `L625`
    - [`to_curl()`](core/models.py#L646) — `L646`
- **[`AppState`](core/models.py#L663-L685)** — `L663-L685`
  - *Zentraler Laufzeit-Zustand der Anwendung.*
  - **Wichtige Methoden:**
    - [`__init__()`](core/models.py#L665) — `L665`

#### Modul-Funktionen
- **[`is_valid_expire_date(expire_val, allow_unlimited)`](core/models.py#L29-L131)** — `L29` — *Prüft, ob ein Ablaufdatum-Wert gültig und aktiv (in der Zukunft oder unbegrenzt) ist.*
- **[`quality_from_dimensions(width, height)`](core/models.py#L135-L150)** — `L135` — *Ermittelt den Qualitäts-Tag (UHD/FHD/HD/SD) exakt anhand von Pixel-Dimensionen.*
- **[`detect_quality_tag(name, raw)`](core/models.py#L153-L180)** — `L153` — *Erkennt den Qualitäts-Tag AUSSCHLIESSLICH anhand von echten Dimensionsdaten in den Metadaten.*

#### Wichtige Konstanten / Konfigurationen
- `_MONTHS` (L13)

---

### 📄 [`core/pattern_predictor.py`](core/pattern_predictor.py) (197 Zeilen)
> Intelligenter MAC-Muster-Prädiktor und Permutations-Generator für STB Pro Qt6.
Analysiert bekannte Treffer aus der MAC-Datenbank auf Präfix-Häufungen (z. B. B5-Reihe '00:1A:79:B5:XX:XX'),
erkennt dichte Adress-Cluster und generiert gezielte Permutationen für weitere Scans.

#### Klassen & Komponenten
- **[`MacClusterPattern`](core/pattern_predictor.py#L15-L23)** — `L15-L23`
  - *Repräsentiert ein identifiziertes MAC-Muster oder Cluster.*
- **[`MacPatternPredictor`](core/pattern_predictor.py#L48-L197)** — `L48-L197`
  - *Analysiert MAC-Treffer auf wiederkehrende Muster und generiert*
  - **Wichtige Methoden:**
    - [`analyze(mac_list)`](core/pattern_predictor.py#L55) — `L55` *(Analysiert eine Liste von MAC-Adressen und ermittelt die heißesten Muster)*
    - [`generate_permutations(cls, source_macs, selected_patterns, max_total, mode, existing_macs)`](core/pattern_predictor.py#L126) — `L126` *(Generiert neue, noch nicht bekannte MAC-Kandidaten aus Mustern und Cluster-Nachbarschaften.)*

#### Modul-Funktionen
- **[`normalize_mac(mac)`](core/pattern_predictor.py#L26-L31)** — `L26` — *Bereinigt und formatiert eine MAC-Adresse nach XX:XX:XX:XX:XX:XX.*
- **[`mac_to_int(mac)`](core/pattern_predictor.py#L34-L39)** — `L34` — *Konvertiert eine MAC-Adresse in eine 48-Bit-Ganzzahl.*
- **[`int_to_mac(val)`](core/pattern_predictor.py#L42-L45)** — `L42` — *Konvertiert eine 48-Bit-Ganzzahl in eine formatierte MAC-Adresse.*

---

### 📄 [`core/portal_checker.py`](core/portal_checker.py) (839 Zeilen)
> Stalker Portal Erreichbarkeits-Checker & Rotations-Pool.
Prüft Stalker-Portale aus Listen (z. B. stalker_portals.txt) multi-threaded
auf Erreichbarkeit, Latenz (Ping), HTTP-Status und Stalker-Signaturen.
Ermöglicht das Speichern erreichbarer Portale und deren direkte Bereitstellung
zur automatischen Rotation im MAC-Scanner.

#### Klassen & Komponenten
- **[`PortalCheckResult`](core/portal_checker.py#L34-L93)** — `L34-L93`
  - *Repräsentiert das Prüfergebnis eines einzelnen Stalker-Portals.*
  - **Wichtige Methoden:**
    - [`to_dict()`](core/portal_checker.py#L48) — `L48`
    - [`from_dict(cls, data)`](core/portal_checker.py#L64) — `L64`
    - [`display_status()`](core/portal_checker.py#L79) — `L79`
- **[`StalkerPortalChecker`](core/portal_checker.py#L629-L839)** — `L629-L839`
  - *Multi-threaded Stalker Portal Prüf-Engine.*
  - **Wichtige Methoden:**
    - [`__init__()`](core/portal_checker.py#L635) — `L635`
    - [`is_running()`](core/portal_checker.py#L659) — `L659`
    - [`get_results()`](core/portal_checker.py#L662) — `L662`
    - [`get_reachable_urls()`](core/portal_checker.py#L666) — `L666`
    - [`stop()`](core/portal_checker.py#L670) — `L670` *(Stoppt die laufende Prüfung sofort.)*
    - [`pause()`](core/portal_checker.py#L676) — `L676` *(Pausiert die Prüfung.)*
    - [`resume()`](core/portal_checker.py#L680) — `L680` *(Setzt die Prüfung fort.)*
    - [`start_check(urls, threads, timeout, verify_ssl, delay_s)`](core/portal_checker.py#L684) — `L684` *(Startet die asynchrone Multi-Threaded Portalprüfung im Hintergrund.)*

#### Modul-Funktionen
- **[`is_valid_portal_hostname(host)`](core/portal_checker.py#L162-L211)** — `L162` — *Validiert streng, ob ein Hostname eine reale Internet-Domain oder IPv4-Adresse darstellt.*
- **[`extract_portal_urls_from_text(content)`](core/portal_checker.py#L214-L285)** — `L214` — *Extrahiert Stalker-Portal-URLs aus einem Textstring (z. B. aus TXT-Listen, Logs, M3U).*
- **[`extract_portal_urls_from_folder(folder_path, max_file_size)`](core/portal_checker.py#L288-L321)** — `L288` — *Durchsucht alle .txt-Dateien eines Ordners rekursiv nach Stalker Portal-URLs.*
- **[`normalize_portal_url(raw)`](core/portal_checker.py#L324-L345)** — `L324` — *Normalisiert eine Portal-URL sauber (Protokoll, Leerzeichen, Format).*
- **[`load_portal_list(file_path)`](core/portal_checker.py#L348-L376)** — `L348` — *Liest eine Stalker-Portal-Datei (.txt) ein, bereinigt Kommentare und*
- **[`save_reachable_portals_file(file_path, urls)`](core/portal_checker.py#L379-L392)** — `L379` — *Speichert eine Liste erreichbarer Portal-URLs zeilenweise in eine .txt-Datei.*
- **[`is_stalker_response(r)`](core/portal_checker.py#L395-L441)** — `L395` — *Prüft eine HTTP-Response rigoros auf definitive Stalker / Ministra Signaturen.*
- **[`get_portal_candidate_endpoints(url)`](core/portal_checker.py#L444-L479)** — `L444` — *Generiert typische Stalker/Ministra-Endpunkte für Handshake-Probes.*
- **[`check_single_portal(url, timeout, verify_ssl, session)`](core/portal_checker.py#L482-L626)** — `L482` — *Prüft einen einzelnen Portal-Host rigoros auf echte Stalker/Ministra-Erreichbarkeit,*

#### Wichtige Konstanten / Konfigurationen
- `DEFAULT_PORTAL_TIMEOUT` (L29), `DEFAULT_CHECKER_THREADS` (L30), `VALID_TLDS` (L97), `PORTAL_URL_PATTERN` (L129), `_URL_WITH_SCHEME` (L137), `_LABEL_PREFIXED_URL` (L138), `_BARE_HOST_WITH_PORT` (L139), `_BARE_HOST_WITH_PATH` (L140), `_PORTAL_PREFIXED_HOST` (L141), `EXCLUDED_HOST_SUFFIXES` (L143), `EXCLUDED_EXTENSIONS` (L153)

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

### 📄 [`core/scan_scheduler.py`](core/scan_scheduler.py) (596 Zeilen)
> Multi-Portal Scan Scheduler für STB Pro Qt6.
Bietet intelligente Verteilungsmodi für Multi-Portal MAC-Scans:
- HOT_SPOT: Hot-Spot Affinity mit Backfill (bei einem Treffer werden auch zuvor auf anderen Portalen abgewiesene MACs auf dem Hot-Portal nachgetestet)
- ROUND_ROBIN: Klassische zyklische Verteilung aller MACs über alle erreichbaren Portale
- ADAPTIVE: Dynamische Hit-Rate-Gewichtung mit Backfill (Multi-Armed Bandit / epsilon-greedy)
- FAILOVER: Primäres Portal aktiv; automatischer Wechsel zum nächsten Portal bei 3 aufeinanderfolgenden Fehlern
- SWEEP: Jede MAC gegen alle Portale prüfen (vollständige Matrix)
- SWEEP_EARLY_EXIT: Sweep mit Abbruch sobald eine MAC auf einem Portal erfolgreich verifiziert wurde

#### Klassen & Komponenten
- **[`ScanRotationMode`](core/scan_scheduler.py#L21-L55)** — `L21-L55`
  - *Konstanten für Multi-Portal Rotations- und Scan-Modi.*
  - **Wichtige Methoden:**
    - [`describe(cls, mode)`](core/scan_scheduler.py#L31) — `L31`
    - [`from_ui_label(cls, label)`](core/scan_scheduler.py#L43) — `L43`
- **[`MultiPortalScanScheduler`](core/scan_scheduler.py#L58-L596)** — `L58-L596`
  - *Thread-sicherer Work-Scheduler für Multi-Portal MAC-Scans mit intelligenter*
  - **Wichtige Methoden:**
    - [`__init__(portals, macs, mode, hot_spot_burst, failover_threshold, on_log)`](core/scan_scheduler.py#L64) — `L64`
    - [`_log(msg)`](core/scan_scheduler.py#L155) — `L155`
    - [`get_next_work_item()`](core/scan_scheduler.py#L162) — `L162` *(Gibt das nächste (MAC, Portal)-Tupel thread-sicher zurück.)*
    - [`_get_hot_spot_item()`](core/scan_scheduler.py#L203) — `L203`
    - [`_get_adaptive_item()`](core/scan_scheduler.py#L272) — `L272`
    - [`_get_failover_item()`](core/scan_scheduler.py#L318) — `L318`
    - [`_get_round_robin_item()`](core/scan_scheduler.py#L342) — `L342`
    - [`_weighted_portal_choice()`](core/scan_scheduler.py#L355) — `L355`
    - [`_activate_hot_spot(portal, ch_cnt)`](core/scan_scheduler.py#L368) — `L368` *(Aktiviert Hot-Spot Modus und sammelt alle bisher auf anderen Portalen abgewiesenen MACs.)*
    - [`report_result(portal_url, mac, result)`](core/scan_scheduler.py#L398) — `L398` *(Aktualisiert Metriken, Treffer, Burst-Quotas und Failover-Zustände thread-sicher.)*
    - [`requeue_item(portal_url, mac, reason)`](core/scan_scheduler.py#L543) — `L543` *(Stellt ein Work-Item bei transientem Fehler thread-sicher erneut an.)*
    - [`release_in_flight()`](core/scan_scheduler.py#L560) — `L560` *(Reduziert in_flight falls ein Worker unerwartet abbricht.)*
    - [`is_exhausted()`](core/scan_scheduler.py#L565) — `L565` *(Prüft, ob alle Items verarbeitet wurden und keine mehr in Bearbeitung sind.)*
    - [`get_progress()`](core/scan_scheduler.py#L575) — `L575` *(Gibt (effektive_fertige_checks, gesamt_checks) zurück.)*
    - [`get_queue_size()`](core/scan_scheduler.py#L581) — `L581` *(Gibt die Anzahl der noch wartenden Items zurück.)*
    - *... und 1 weitere Hilfsmethoden.*

---

### 📄 [`core/signals.py`](core/signals.py) (117 Zeilen)
> Reaktiver Qt6 Event-Bus & Asynchroner QThreadPool-Worker.
Ersetzt das langsame Tkinter after()-Polling durch echte Qt Signals & Slots.

#### Klassen & Komponenten
- **[`AppEventBus`](core/signals.py#L10-L28)** : *QObject* — `L10-L28`
  - *Zentraler Signal-Bus für die gesamte Applikation.*
  - **Signals**: `log_message`, `http_Exchange_logged`, `connection_state_changed`, `profile_updated`, `channels_loaded`, `vod_categories_loaded`, `channel_selected`, `channel_play_requested`, `favorites_changed`, `recorder_changed`, `telemetry_updated`, `scan_result_received`, `scan_progress_updated`, `scan_state_changed`, `vpn_status_changed`, `stream_ip_ban_detected`
- **[`_WorkerSignals`](core/signals.py#L31-L33)** : *QObject* — `L31-L33`
  - **Signals**: `finished`, `error`
- **[`_AsyncTask`](core/signals.py#L36-L64)** : *QRunnable* — `L36-L64`
  - *Kapselt eine beliebige Funktion für den globalen QThreadPool.*
  - **Wichtige Methoden:**
    - [`__init__(fn)`](core/signals.py#L38) — `L38`
    - [`run()`](core/signals.py#L58) — `L58`
- **[`AsyncWorkerPool`](core/signals.py#L67-L112)** : *QObject* — `L67-L112`
  - *Hochperformanter Thread-Pool auf Basis von Qt QThreadPool.*
  - **Signals**: `ui_dispatch_signal`
  - **Wichtige Methoden:**
    - [`__init__(max_workers)`](core/signals.py#L74) — `L74`
    - [`_execute_on_ui(fn, args, kwargs)`](core/signals.py#L82) — `L82`
    - [`run_async(task_fn)`](core/signals.py#L88) — `L88`
    - [`submit(fn)`](core/signals.py#L104) — `L104`
    - [`dispatch_to_ui(fn)`](core/signals.py#L107) — `L107`
    - [`shutdown(msecs)`](core/signals.py#L110) — `L110`

---

### 📄 [`core/stream_buffer.py`](core/stream_buffer.py) (634 Zeilen)
> Lokaler Stream-Puffer-Proxy (127.0.0.1) für STB Pro Qt6.
Liest den Upstream-Stream unabhängig vom Player in einen Ringpuffer (Sekunden/MB),
liefert ihn PCR-getaktet an LibVLC und überbrückt kurze Aussetzer durch Auto-Reconnect.

#### Klassen & Komponenten
- **[`BufferSettings`](core/stream_buffer.py#L22-L67)** — `L22-L67`
  - **Wichtige Methoden:**
    - [`clamp()`](core/stream_buffer.py#L39) — `L39`
    - [`to_dict()`](core/stream_buffer.py#L54) — `L54`
    - [`from_dict(cls, d)`](core/stream_buffer.py#L58) — `L58`
- **[`_Session`](core/stream_buffer.py#L70-L553)** — `L70-L553`
  - **Wichtige Methoden:**
    - [`__init__(url, headers, st)`](core/stream_buffer.py#L71) — `L71`
    - [`_url_host()`](core/stream_buffer.py#L111) — `L111`
    - [`_rate_est()`](core/stream_buffer.py#L119) — `L119`
    - [`_record_pcr(abs_offset, pcr_time)`](core/stream_buffer.py#L125) — `L125`
    - [`_level_s(pos)`](core/stream_buffer.py#L150) — `L150`
    - [`_scan(chunk)`](core/stream_buffer.py#L158) — `L158`
    - [`_parse_ts_psi(p, o, pid, has_pusi, afc)`](core/stream_buffer.py#L223) — `L223`
    - [`_produce()`](core/stream_buffer.py#L294) — `L294`
    - [`_tick_rate(n)`](core/stream_buffer.py#L441) — `L441`
    - [`_take(pos, n)`](core/stream_buffer.py#L449) — `L449`
    - [`serve(wfile)`](core/stream_buffer.py#L459) — `L459`
    - [`stop()`](core/stream_buffer.py#L514) — `L514`
    - [`stats()`](core/stream_buffer.py#L528) — `L528`
- **[`_Handler`](core/stream_buffer.py#L556-L587)** : *BaseHTTPRequestHandler* — `L556-L587`
  - **Wichtige Methoden:**
    - [`log_message()`](core/stream_buffer.py#L559) — `L559`
    - [`do_HEAD()`](core/stream_buffer.py#L562) — `L562`
    - [`do_GET()`](core/stream_buffer.py#L573) — `L573`
- **[`StreamBufferProxy`](core/stream_buffer.py#L590-L634)** — `L590-L634`
  - **Wichtige Methoden:**
    - [`__init__()`](core/stream_buffer.py#L591) — `L591`
    - [`_ensure_server()`](core/stream_buffer.py#L596) — `L596`
    - [`open_session(url, headers, settings)`](core/stream_buffer.py#L604) — `L604`
    - [`get_session(path)`](core/stream_buffer.py#L612) — `L612`
    - [`stop_session()`](core/stream_buffer.py#L616) — `L616`
    - [`stats()`](core/stream_buffer.py#L622) — `L622`
    - [`shutdown()`](core/stream_buffer.py#L626) — `L626`

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

### 📄 [`core/vpn_manager.py`](core/vpn_manager.py) (657 Zeilen)
> NordVPN Manager für STB Pro Qt6.
Erkennt eine aktive NordVPN-Installation, überwacht den Verbindungsstatus und
führt bei Erkennung von IP-/ISP-Sperren (IP_BAN / ISP_LOCK) vollautomatische,
mehrstufige Server- und Länder-Rotationen via NordVPN-CLI durch.
Speichert verbrannte IPs pro Host und respektiert Benutzer-Präferenzen zur VPN-Steuerung.

#### Klassen & Komponenten
- **[`NordVpnManager`](core/vpn_manager.py#L29-L653)** — `L29-L653`
  - *Verwaltet die Integration mit NordVPN unter Windows.*
  - **Wichtige Methoden:**
    - [`__init__()`](core/vpn_manager.py#L52) — `L52`
    - [`set_config_manager(mgr)`](core/vpn_manager.py#L67) — `L67` *(Bindet den Konfigurations-Manager ein und synchronisiert gespeicherte Einstellungen.)*
    - [`auto_switch_enabled()`](core/vpn_manager.py#L79) — `L79`
    - [`auto_switch_enabled(val)`](core/vpn_manager.py#L85) — `L85`
    - [`reload_config()`](core/vpn_manager.py#L90) — `L90` *(Lädt die Konfiguration dynamisch neu und aktualisiert Pfade und Caches.)*
    - [`_detect_cli(force_refresh)`](core/vpn_manager.py#L101) — `L101`
    - [`is_installed()`](core/vpn_manager.py#L131) — `L131` *(Prüft, ob NordVPN auf dem System installiert ist.)*
    - [`is_running()`](core/vpn_manager.py#L135) — `L135` *(Prüft, ob der NordVPN-Dienst oder die App im Hintergrund aktiv ist.)*
    - [`is_connected()`](core/vpn_manager.py#L152) — `L152` *(Prüft über die Routing-Tabelle, ob der NordLynx-Tunnel aktiv Datenverkehr leitet.)*
    - [`get_public_ip(timeout)`](core/vpn_manager.py#L169) — `L169` *(Ermittelt die aktuelle öffentliche IP-Adresse und Standortinformationen.)*
    - [`_normalize_host(host_or_url)`](core/vpn_manager.py#L194) — `L194`
    - [`mark_ip_burned(host, ip, reason)`](core/vpn_manager.py#L210) — `L210` *(Markiert eine IP für einen bestimmten Host als gesperrt/verbrannt.)*
    - [`is_ip_burned(host, ip)`](core/vpn_manager.py#L227) — `L227` *(Prüft, ob eine IP für den angegebenen Host bereits als gesperrt markiert wurde.)*
    - [`get_burned_ips(host)`](core/vpn_manager.py#L241) — `L241` *(Gibt die Liste aller verbrannten IPs für einen Host zurück.)*
    - [`clear_burned_ips(host)`](core/vpn_manager.py#L250) — `L250` *(Setzt verbrannte IPs zurück (für einen Host oder global).)*
    - *... und 7 weitere Hilfsmethoden.*

#### Modul-Funktionen
- **[`_safe_emit(sig)`](core/vpn_manager.py#L21-L26)** — `L21` — *Sicheres Emitten von Qt-Signalen aus Hintergrund-Threads.*

---

## 📦 Player & Engine (VLC, Proxy & OSD)

### 📄 [`player/__init__.py`](player/__init__.py) (14 Zeilen)
> Player-Paket für STB Pro Qt6.
Enthält LibVLC-Controller, externen Player-Runner und das transparente Fullscreen-OSD.

---

### 📄 [`player/external_player.py`](player/external_player.py) (124 Zeilen)
> Externer Player-Runner für STB Pro Qt6.
Unterstützt VLC, MPV und FFplay inklusive Übergabe von User-Agent und Referer.

#### Klassen & Komponenten
- **[`ExternalPlayerRunner`](player/external_player.py#L11-L124)** — `L11-L124`
  - **Wichtige Methoden:**
    - [`__init__()`](player/external_player.py#L12) — `L12`
    - [`is_running()`](player/external_player.py#L15) — `L15`
    - [`stop()`](player/external_player.py#L18) — `L18`
    - [`toggle_fullscreen()`](player/external_player.py#L26) — `L26`
    - [`play(player_type, player_path, stream_url, title, user_agent, referrer, fullscreen, caching_ms, hw_decode)`](player/external_player.py#L56) — `L56`

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

### 📄 [`ui/main_window.py`](ui/main_window.py) (3123 Zeilen)
> Main Application Window (Orchestrator) for STB Pro v6.0 Qt6 Edition.
Coordinates Sidebar, TopNavigationBar, LiveTVView, VODView, ScannerView, InspectorView, ConsoleView,
LibVLC Hardware Player, External Player Runner, Fullscreen HUD Overlay, PiP Mini-Player,
Multi-Thread MAC Scanner, Parallel Category Validator, and all 7 Dialogs.

#### Klassen & Komponenten
- **[`MainWindow`](ui/main_window.py#L106-L3121)** : *QMainWindow* — `L106-L3121`
  - **Signals**: `_val_progress_sig`, `_val_finished_sig`, `_val_thumb_progress_sig`, `_val_thumb_finished_sig`, `_epg_loaded_sig`, `_probe_done_sig`, `_preview_ready_sig`
  - **Wichtige Methoden:**
    - [`__init__()`](ui/main_window.py#L116) — `L116`
    - [`_build_ui()`](ui/main_window.py#L215) — `L215`
    - [`_bind_signals()`](ui/main_window.py#L276) — `L276`
    - [`_on_buffer_settings_from_view(st)`](ui/main_window.py#L400) — `L400`
    - [`_on_settings_applied(cfg)`](ui/main_window.py#L405) — `L405`
    - [`_is_text_input_focused()`](ui/main_window.py#L425) — `L425`
    - [`_bind_guarded_shortcut(key_seq, callback)`](ui/main_window.py#L429) — `L429`
    - [`_cycle_aspect_ratio()`](ui/main_window.py#L438) — `L438`
    - [`_setup_shortcuts()`](ui/main_window.py#L443) — `L443`
    - [`_load_initial_config()`](ui/main_window.py#L466) — `L466`
    - [`switch_view(view_key)`](ui/main_window.py#L554) — `L554`
    - [`toggle_sidebar()`](ui/main_window.py#L562) — `L562`
    - [`toggle_cinema_mode()`](ui/main_window.py#L568) — `L568`
    - [`toggle_pip_mode()`](ui/main_window.py#L576) — `L576` *(Switches into a floating Always-on-Top Picture-in-Picture mini-player window.)*
    - [`toggle_fullscreen()`](ui/main_window.py#L618) — `L618`
    - *... und 96 weitere Hilfsmethoden.*

---

### 📄 [`ui/theme.py`](ui/theme.py) (526 Zeilen)
> Obsidian Cyber-Cinema Design System & Qt6 Stylesheet (QSS).
Provides color tokens, font families, and global dark stylesheet for PySide6.

#### Klassen & Komponenten
- **[`ThemeColors`](ui/theme.py#L11-L43)** — `L11-L43`
  - *Design tokens matching and refining the Obsidian Cyber-Cinema palette.*

#### Modul-Funktionen
- **[`apply_obsidian_theme(app, scale_factor)`](ui/theme.py#L492-L526)** — `L492` — *Apply dark QPalette and Obsidian Cyber-Cinema QSS stylesheet with dynamic UI scaling.*

#### Wichtige Konstanten / Konfigurationen
- `GLOBAL_QSS` (L46)

---

## 📦 UI - Views & Workspaces

### 📄 [`ui/views/__init__.py`](ui/views/__init__.py) (18 Zeilen)
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

### 📄 [`ui/views/inspector_view.py`](ui/views/inspector_view.py) (275 Zeilen)
> Interactive Protocol & HTTP Exchange Inspector View.
Replaces the static text dump of the legacy Tkinter version with a live, searchable HTTP traffic table,
JSON pretty-printer, header inspector, 1-click cURL generator, and on-demand Handshake / Endpoint tester.

#### Klassen & Komponenten
- **[`InspectorView`](ui/views/inspector_view.py#L32-L275)** : *QWidget* — `L32-L275`
  - **Signals**: `handshake_test_requested`, `profile_dump_requested`
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/views/inspector_view.py#L36) — `L36`
    - [`add_http_entry(entry)`](ui/views/inspector_view.py#L165) — `L165`
    - [`_matches(entry)`](ui/views/inspector_view.py#L177) — `L177`
    - [`_refresh_table()`](ui/views/inspector_view.py#L188) — `L188`
    - [`_append_row(entry)`](ui/views/inspector_view.py#L196) — `L196`
    - [`_on_row_selected()`](ui/views/inspector_view.py#L227) — `L227`
    - [`set_summary_report(text, switch_tab)`](ui/views/inspector_view.py#L260) — `L260`
    - [`_copy_curl()`](ui/views/inspector_view.py#L265) — `L265`
    - [`clear_entries()`](ui/views/inspector_view.py#L268) — `L268`

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

### 📄 [`ui/views/scanner_view.py`](ui/views/scanner_view.py) (1466 Zeilen)
> Multi-MAC Scanner & Pentest Generator View.
Features 22 OUI Vendor Presets, custom wildcard masks (XX:XX:XX), sequential & random generation,
adaptive WAF/429 Throttle Controller integration, live CPS (Checks/sec) & ETA telemetry,
filterable hit table, and 1-click profile adoption.

#### Klassen & Komponenten
- **[`_PortalCheckerSignals`](ui/views/scanner_view.py#L80-L84)** : *QObject* — `L80-L84`
  - *Thread-sichere Qt-Signals für Hintergrund-Prüfungen der Stalker-Portale.*
  - **Signals**: `result_received`, `progress_updated`, `finished`
- **[`ScannerView`](ui/views/scanner_view.py#L87-L1466)** : *QWidget* — `L87-L1466`
  - **Signals**: `start_scan_requested`, `stop_scan_requested`, `pause_scan_requested`, `resume_scan_requested`, `scan_settings_updated`, `apply_mac_requested`, `prepend_db_macs_requested`, `pattern_analysis_requested`, `scan_exported`
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/views/scanner_view.py#L98) — `L98`
    - [`set_portal_url(url)`](ui/views/scanner_view.py#L586) — `L586`
    - [`_on_oui_selected(text)`](ui/views/scanner_view.py#L590) — `L590`
    - [`generate_macs()`](ui/views/scanner_view.py#L597) — `L597`
    - [`prepend_macs(macs)`](ui/views/scanner_view.py#L636) — `L636`
    - [`get_candidate_macs()`](ui/views/scanner_view.py#L647) — `L647`
    - [`clear_candidates()`](ui/views/scanner_view.py#L652) — `L652`
    - [`_update_queue_count()`](ui/views/scanner_view.py#L656) — `L656`
    - [`_import_from_file()`](ui/views/scanner_view.py#L660) — `L660`
    - [`_import_from_folder()`](ui/views/scanner_view.py#L674) — `L674`
    - [`_import_from_clipboard()`](ui/views/scanner_view.py#L721) — `L721`
    - [`_deduplicate_list()`](ui/views/scanner_view.py#L727) — `L727`
    - [`_on_start_clicked()`](ui/views/scanner_view.py#L737) — `L737`
    - [`get_scan_threads()`](ui/views/scanner_view.py#L779) — `L779`
    - [`get_scan_delay()`](ui/views/scanner_view.py#L782) — `L782`
    - *... und 39 weitere Hilfsmethoden.*

#### Wichtige Konstanten / Konfigurationen
- `OUI_VENDOR_PRESETS` (L52), `MAC_REGEX` (L77)

---

### 📄 [`ui/views/settings_view.py`](ui/views/settings_view.py) (968 Zeilen)
> Settings & Boost Configuration View for STB Pro Qt6.
Provides comprehensive controls for Portal Handshake, Scanner & Probing,
Stream Ringbuffer & Playback, External Player Engines, NordVPN Ban-Recovery,
and UI / System preferences with live persistence to config.json.

#### Klassen & Komponenten
- **[`SettingsView`](ui/views/settings_view.py#L45-L968)** : *QWidget* — `L45-L968`
  - **Signals**: `settings_saved`, `buffer_settings_changed`, `vpn_settings_changed`, `ui_scale_changed`, `cache_cleared`
  - **Wichtige Methoden:**
    - [`__init__(config_mgr, vpn_mgr, parent)`](ui/views/settings_view.py#L52) — `L52`
    - [`_build_handshake_tab()`](ui/views/settings_view.py#L118) — `L118`
    - [`_build_scanner_tab()`](ui/views/settings_view.py#L213) — `L213`
    - [`_build_buffering_tab()`](ui/views/settings_view.py#L332) — `L332`
    - [`_build_player_tab()`](ui/views/settings_view.py#L447) — `L447`
    - [`_build_vpn_tab()`](ui/views/settings_view.py#L527) — `L527`
    - [`_build_gui_tab()`](ui/views/settings_view.py#L651) — `L651`
    - [`load_from_config()`](ui/views/settings_view.py#L702) — `L702`
    - [`save_to_config()`](ui/views/settings_view.py#L792) — `L792`
    - [`reset_to_defaults()`](ui/views/settings_view.py#L879) — `L879`
    - [`_browse_file(line_edit, filter_str)`](ui/views/settings_view.py#L897) — `L897`
    - [`_auto_detect_players()`](ui/views/settings_view.py#L902) — `L902`
    - [`_update_vpn_badge()`](ui/views/settings_view.py#L930) — `L930`
    - [`_clear_all_burned_ips()`](ui/views/settings_view.py#L950) — `L950`
    - [`_clear_caches()`](ui/views/settings_view.py#L961) — `L961`

---

### 📄 [`ui/views/vod_view.py`](ui/views/vod_view.py) (454 Zeilen)
> VOD (Movies) & Series Browser View.
Uses virtualized QTableView + VODTableModel + VODFilterProxyModel for zero-lag browsing,
coupled with a rich Movie/Series Detail & Poster Card.

#### Klassen & Komponenten
- **[`VODView`](ui/views/vod_view.py#L38-L454)** : *QWidget* — `L38-L454`
  - **Signals**: `mode_changed`, `category_selected`, `portal_search_requested`, `play_vod_requested`, `download_vod_requested`, `copy_vod_url_requested`, `open_series_requested`, `favorite_toggled`, `raw_json_requested`
  - **Wichtige Methoden:**
    - [`__init__(logo_cache, parent)`](ui/views/vod_view.py#L49) — `L49`
    - [`current_mode()`](ui/views/vod_view.py#L273) — `L273`
    - [`_switch_mode(mode)`](ui/views/vod_view.py#L276) — `L276`
    - [`set_categories(categories)`](ui/views/vod_view.py#L294) — `L294`
    - [`set_items(items, favorites)`](ui/views/vod_view.py#L306) — `L306`
    - [`update_favorites(favorites)`](ui/views/vod_view.py#L312) — `L312`
    - [`set_loading(text)`](ui/views/vod_view.py#L319) — `L319`
    - [`_update_status_label()`](ui/views/vod_view.py#L322) — `L322`
    - [`_on_category_changed(idx)`](ui/views/vod_view.py#L328) — `L328`
    - [`_on_local_search_changed(text)`](ui/views/vod_view.py#L334) — `L334`
    - [`_on_portal_search()`](ui/views/vod_view.py#L338) — `L338`
    - [`_on_sort_changed(mode)`](ui/views/vod_view.py#L343) — `L343`
    - [`_on_filter_toggled()`](ui/views/vod_view.py#L346) — `L346`
    - [`_get_item_id(item)`](ui/views/vod_view.py#L352) — `L352`
    - [`_on_row_selected(current, _previous)`](ui/views/vod_view.py#L355) — `L355`
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

### 📄 [`ui/components/top_bar.py`](ui/components/top_bar.py) (266 Zeilen)
> Top Navigation & Status Bar Component.
Includes View Tabs, Provider Status Pill, REC Indicator, Jobs Badge, Buffer Config,
Sidebar Toggle, Cinema Mode Toggle, PiP Floating Player Toggle, and Fullscreen Toggle.

#### Klassen & Komponenten
- **[`TopNavigationBar`](ui/components/top_bar.py#L22-L266)** : *QFrame* — `L22-L266`
  - **Signals**: `view_changed`, `sidebar_toggled`, `cinema_toggled`, `pip_toggled`, `fullscreen_requested`, `buffer_dialog_requested`, `jobs_dialog_requested`, `account_info_requested`, `record_stop_requested`, `vpn_switch_requested`
  - **Wichtige Methoden:**
    - [`__init__(parent)`](ui/components/top_bar.py#L34) — `L34`
    - [`resizeEvent(event)`](ui/components/top_bar.py#L185) — `L185`
    - [`_update_provider_elide()`](ui/components/top_bar.py#L191) — `L191`
    - [`set_active_view(view_key)`](ui/components/top_bar.py#L203) — `L203`
    - [`set_sidebar_active(active)`](ui/components/top_bar.py#L210) — `L210`
    - [`set_provider_status(connected, summary)`](ui/components/top_bar.py#L215) — `L215`
    - [`update_jobs_badge(active_count, total_count)`](ui/components/top_bar.py#L230) — `L230`
    - [`update_rec_indicator(is_recording, label_text)`](ui/components/top_bar.py#L240) — `L240`
    - [`update_vpn_badge(text, status)`](ui/components/top_bar.py#L245) — `L245`

---

## 📦 UI - Dialoge & Overlays

### 📄 [`ui/dialogs/__init__.py`](ui/dialogs/__init__.py) (22 Zeilen)
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

### 📄 [`ui/dialogs/epg_guide_dialog.py`](ui/dialogs/epg_guide_dialog.py) (254 Zeilen)
> Multi-Day EPG Program Guide & Timeshift/Catchup Archive Dialog.
Allows browsing programs by date, searching EPG titles, playing archived programs, and downloading them.

#### Klassen & Komponenten
- **[`EPGGuideDialog`](ui/dialogs/epg_guide_dialog.py#L31-L254)** : *QDialog* — `L31-L254`
  - **Signals**: `archive_play_requested`, `archive_download_requested`
  - **Wichtige Methoden:**
    - [`__init__(channel, programs, parent)`](ui/dialogs/epg_guide_dialog.py#L35) — `L35`
    - [`set_programs(programs)`](ui/dialogs/epg_guide_dialog.py#L139) — `L139`
    - [`_populate_days_combo()`](ui/dialogs/epg_guide_dialog.py#L150) — `L150`
    - [`_refresh_table()`](ui/dialogs/epg_guide_dialog.py#L168) — `L168`
    - [`_selected_program()`](ui/dialogs/epg_guide_dialog.py#L226) — `L226`
    - [`_on_selection_changed()`](ui/dialogs/epg_guide_dialog.py#L233) — `L233`
    - [`_on_play_archive()`](ui/dialogs/epg_guide_dialog.py#L245) — `L245`
    - [`_on_dl_archive()`](ui/dialogs/epg_guide_dialog.py#L251) — `L251`

---

### 📄 [`ui/dialogs/jobs_dialog.py`](ui/dialogs/jobs_dialog.py) (138 Zeilen)
> Recordings & Downloads Job Manager Dialog.
Displays live progress, speed, MB downloaded, status, stop action, and 1-click folder opener.

#### Klassen & Komponenten
- **[`JobsDialog`](ui/dialogs/jobs_dialog.py#L25-L138)** : *QDialog* — `L25-L138`
  - **Wichtige Methoden:**
    - [`__init__(recorder_mgr, parent)`](ui/dialogs/jobs_dialog.py#L26) — `L26`
    - [`refresh_jobs()`](ui/dialogs/jobs_dialog.py#L86) — `L86`
    - [`_stop_selected()`](ui/dialogs/jobs_dialog.py#L120) — `L120`
    - [`_clear_finished()`](ui/dialogs/jobs_dialog.py#L128) — `L128`
    - [`_open_output_dir()`](ui/dialogs/jobs_dialog.py#L132) — `L132`

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

### 📄 [`ui/dialogs/mac_db_dialog.py`](ui/dialogs/mac_db_dialog.py) (265 Zeilen)
> MAC Hit Database Explorer Dialog.
Browses `mac_database.json`, filters by Portal URL or search text, removes duplicates,
exports hits, applies a MAC directly to the active profile, or sends portal MACs to the scanner.

#### Klassen & Komponenten
- **[`MacDatabaseDialog`](ui/dialogs/mac_db_dialog.py#L32-L265)** : *QDialog* — `L32-L265`
  - **Signals**: `apply_mac_requested`, `send_to_scanner_requested`
  - **Wichtige Methoden:**
    - [`__init__(mac_db, parent)`](ui/dialogs/mac_db_dialog.py#L36) — `L36`
    - [`_reload_portals()`](ui/dialogs/mac_db_dialog.py#L128) — `L128`
    - [`refresh_view()`](ui/dialogs/mac_db_dialog.py#L136) — `L136`
    - [`_selected_entry()`](ui/dialogs/mac_db_dialog.py#L195) — `L195`
    - [`_on_pattern_search()`](ui/dialogs/mac_db_dialog.py#L203) — `L203`
    - [`_on_pattern_to_scanner(macs)`](ui/dialogs/mac_db_dialog.py#L209) — `L209`
    - [`_on_apply_selected()`](ui/dialogs/mac_db_dialog.py#L214) — `L214`
    - [`_on_send_to_scanner()`](ui/dialogs/mac_db_dialog.py#L225) — `L225`
    - [`_on_copy_mac()`](ui/dialogs/mac_db_dialog.py#L235) — `L235`
    - [`_on_dedup()`](ui/dialogs/mac_db_dialog.py#L240) — `L240`
    - [`_on_delete_selected()`](ui/dialogs/mac_db_dialog.py#L245) — `L245`
    - [`_on_export()`](ui/dialogs/mac_db_dialog.py#L251) — `L251`

---

### 📄 [`ui/dialogs/mac_pattern_dialog.py`](ui/dialogs/mac_pattern_dialog.py) (308 Zeilen)
> Dialog zur Visualisierung von MAC-Mustern und Generierung von Permutationen.
Ermöglicht das Erkennen von Hot-Prefixes (z. B. B5-Reihe) und den direkten
Transfer von generierten Permutationen in den Scanner oder als TXT-Export.

#### Klassen & Komponenten
- **[`MacPatternDialog`](ui/dialogs/mac_pattern_dialog.py#L33-L308)** : *QDialog* — `L33-L308`
  - *Dialog für die Mustererkennung und Permutations-Generierung.*
  - **Signals**: `send_to_scanner_requested`
  - **Wichtige Methoden:**
    - [`__init__(mac_db, initial_portal, parent)`](ui/dialogs/mac_pattern_dialog.py#L39) — `L39`
    - [`_populate_portals()`](ui/dialogs/mac_pattern_dialog.py#L184) — `L184`
    - [`_run_analysis()`](ui/dialogs/mac_pattern_dialog.py#L196) — `L196`
    - [`_generate_candidates()`](ui/dialogs/mac_pattern_dialog.py#L243) — `L243`
    - [`_on_send_to_scanner()`](ui/dialogs/mac_pattern_dialog.py#L286) — `L286`
    - [`_on_export_txt()`](ui/dialogs/mac_pattern_dialog.py#L293) — `L293`
    - [`_on_copy_all()`](ui/dialogs/mac_pattern_dialog.py#L304) — `L304`

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

### 📄 [`ui/dialogs/series_dialog.py`](ui/dialogs/series_dialog.py) (170 Zeilen)
> Series Season & Episode Browser Dialog.
Supports both Xtream Codes (`get_series_info`) and Stalker (`get_ordered_list` seasons/episodes),
with episode search, 1-click playback, direct episode download, and link copy.

#### Klassen & Komponenten
- **[`SeriesBrowserDialog`](ui/dialogs/series_dialog.py#L26-L170)** : *QDialog* — `L26-L170`
  - **Signals**: `episode_play_requested`, `episode_download_requested`, `episode_copy_requested`
  - **Wichtige Methoden:**
    - [`__init__(series_title, seasons_data, parent)`](ui/dialogs/series_dialog.py#L31) — `L31`
    - [`_refresh_episodes()`](ui/dialogs/series_dialog.py#L111) — `L111`
    - [`_selected_episode()`](ui/dialogs/series_dialog.py#L149) — `L149`
    - [`_on_play()`](ui/dialogs/series_dialog.py#L156) — `L156`
    - [`_on_download()`](ui/dialogs/series_dialog.py#L162) — `L162`
    - [`_on_copy()`](ui/dialogs/series_dialog.py#L167) — `L167`

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

### 📄 [`ui/models/vod_model.py`](ui/models/vod_model.py) (244 Zeilen)
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
- **[`VODFilterProxyModel`](ui/models/vod_model.py#L165-L244)** : *QSortFilterProxyModel* — `L165-L244`
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

### 📄 [`tests/test_expire_validation.py`](tests/test_expire_validation.py) (297 Zeilen)
> Unit-Tests für die Validierung von Ablaufdaten (Expiration Dates) und
die Verhinderung von False-Positive Hot-Hits bei 0000000 / None / Unbekannt / abgelaufenen Accounts.

#### Klassen & Komponenten
- **[`TestExpireDateValidation`](tests/test_expire_validation.py#L16-L118)** : *unittest.TestCase* — `L16-L118`
  - *Tests für is_valid_expire_date Hilfsfunktion.*
  - **Wichtige Methoden:**
    - [`test_invalid_and_zero_dates()`](tests/test_expire_validation.py#L19) — `L19` *(Nullwerte, Nullen und Platzhalter müssen als ungültig erkannt werden.)*
    - [`test_past_dates()`](tests/test_expire_validation.py#L53) — `L53` *(Vergangene Ablaufdaten müssen als abgelaufen (False) erkannt werden.)*
    - [`test_future_valid_dates()`](tests/test_expire_validation.py#L73) — `L73` *(Zukünftige Daten müssen als aktiv und gültig erkannt werden.)*
    - [`test_unlimited_and_lifetime_dates()`](tests/test_expire_validation.py#L95) — `L95` *(Unbegrenzte / Lifetime Kennzeichnungen müssen als gültig akzeptiert werden.)*
- **[`TestMacDatabaseExpireFilter`](tests/test_expire_validation.py#L121-L229)** : *unittest.TestCase* — `L121-L229`
  - *Tests für MacDatabase Filterung ungültiger Ablaufdaten.*
  - **Wichtige Methoden:**
    - [`setUp()`](tests/test_expire_validation.py#L124) — `L124`
    - [`tearDown()`](tests/test_expire_validation.py#L129) — `L129`
    - [`test_save_found_mac_rejects_zero_and_none_expire()`](tests/test_expire_validation.py#L132) — `L132` *(save_found_mac darf Accounts mit 0000000 oder None Expire nicht speichern.)*
    - [`test_save_found_mac_accepts_valid_future_expire()`](tests/test_expire_validation.py#L166) — `L166` *(save_found_mac speichert Accounts mit zukünftigem Datum oder Unlimited.)*
    - [`test_clean_duplicates_removes_invalid_expire_records()`](tests/test_expire_validation.py#L179) — `L179` *(clean_duplicates bereinigt historische Einträge mit 0000000 oder abgelaufenem Datum.)*
- **[`TestScanSchedulerExpireHandling`](tests/test_expire_validation.py#L232-L293)** : *unittest.TestCase* — `L232-L293`
  - *Tests für MultiPortalScanScheduler mit 0000000 / ungültigen Ablaufdaten.*
  - **Wichtige Methoden:**
    - [`test_report_result_with_zero_expire_does_not_trigger_hotspot()`](tests/test_expire_validation.py#L235) — `L235` *(Ein Account mit 0000000 / None Expire darf keinen Hot-Spot Burst auslösen.)*
    - [`test_report_result_with_valid_expire_triggers_hotspot()`](tests/test_expire_validation.py#L266) — `L266` *(Ein echter Hot-Hit mit gültigem Ablaufdatum löst wie gewohnt Hot-Spot Burst aus.)*

---

### 📄 [`tests/test_pattern_predictor_and_antiban.py`](tests/test_pattern_predictor_and_antiban.py) (285 Zeilen)
> Unit-Tests für den MAC-Muster-Prädiktor, Permutations-Generator,
Anti-Ban VPN-Shield und erweiterte Delays.

#### Klassen & Komponenten
- **[`TestMacPatternPredictor`](tests/test_pattern_predictor_and_antiban.py#L21-L110)** : *unittest.TestCase* — `L21-L110`
  - *Tests für MacPatternPredictor Analyse und Permutationen.*
  - **Wichtige Methoden:**
    - [`setUp()`](tests/test_pattern_predictor_and_antiban.py#L24) — `L24`
    - [`test_mac_conversions()`](tests/test_pattern_predictor_and_antiban.py#L36) — `L36` *(Prüft die bidirektionale MAC-Ganzzahl-Konvertierung.)*
    - [`test_analyze_identifies_b5_series_and_subclusters()`](tests/test_pattern_predictor_and_antiban.py#L50) — `L50` *(analyze muss die B5-Reihe als Top-Cluster mit 5 Treffern identifizieren.)*
    - [`test_generate_permutations_neighbor_sweep()`](tests/test_pattern_predictor_and_antiban.py#L67) — `L67` *(neighbor_sweep generiert benachbarte MACs um bekannte Treffer ohne Duplikate.)*
    - [`test_generate_permutations_cluster_full()`](tests/test_pattern_predictor_and_antiban.py#L86) — `L86` *(cluster_full füllt Sub-Blöcke der Top-Treffer systematisch auf.)*
    - [`test_generate_permutations_deduplicates_against_existing()`](tests/test_pattern_predictor_and_antiban.py#L100) — `L100` *(Bereits bekannte MACs aus der Datenbank werden nicht erneut generiert.)*
- **[`TestMacDatabaseVpnLocation`](tests/test_pattern_predictor_and_antiban.py#L113-L138)** : *unittest.TestCase* — `L113-L138`
  - *Tests für Speicherung und Auslesen von VPN-Standorten in MacDatabase.*
  - **Wichtige Methoden:**
    - [`test_save_and_retrieve_vpn_location()`](tests/test_pattern_predictor_and_antiban.py#L116) — `L116`
- **[`TestAntiBanShieldLogic`](tests/test_pattern_predictor_and_antiban.py#L141-L196)** : *unittest.TestCase* — `L141-L196`
  - *Tests für die Anti-Ban Erkennung und den 45s-Cooldown.*
  - **Wichtige Methoden:**
    - [`test_antiban_trigger_and_cooldown()`](tests/test_pattern_predictor_and_antiban.py#L144) — `L144` *(Prüft, dass >30 Fehler in 5s nur bei Hosts mit Treffern feuern und 45s Cooldown greift.)*
- **[`TestPatternPredictorUiIntegration`](tests/test_pattern_predictor_and_antiban.py#L199-L281)** : *unittest.TestCase* — `L199-L281`
  - *Tests für UI-Integration und Signalübergabe des Pattern-Prädiktors.*
  - **Wichtige Methoden:**
    - [`setUpClass(cls)`](tests/test_pattern_predictor_and_antiban.py#L203) — `L203`
    - [`test_pattern_dialog_send_to_scanner_accepts_cleanly()`](tests/test_pattern_predictor_and_antiban.py#L208) — `L208` *(Testet, dass _on_send_to_scanner den Dialog schließt und MACs emittiert ohne modales Hängen.)*
    - [`test_scanner_view_pattern_analysis_button_and_signal()`](tests/test_pattern_predictor_and_antiban.py#L233) — `L233` *(Testet, dass ScannerView den Analyse-Button besitzt und das Signal feuert.)*
    - [`test_scanner_view_filter_switching_no_freeze()`](tests/test_pattern_predictor_and_antiban.py#L242) — `L242` *(Testet, dass das Umschalten zwischen ALL, HOT, OK, ERR auch bei vielen Einträgen blitzschnell und ohne Freeze läuft.)*

---

### 📄 [`tests/test_portal_checker.py`](tests/test_portal_checker.py) (536 Zeilen)
#### Klassen & Komponenten
- **[`TestPortalChecker`](tests/test_portal_checker.py#L26-L532)** : *unittest.TestCase* — `L26-L532`
  - **Wichtige Methoden:**
    - [`test_01_normalize_portal_url()`](tests/test_portal_checker.py#L27) — `L27`
    - [`test_02_load_and_save_portal_list()`](tests/test_portal_checker.py#L34) — `L34`
    - [`test_03_check_single_portal_online_and_stalker()`](tests/test_portal_checker.py#L61) — `L61`
    - [`test_04_check_single_portal_timeout_and_error()`](tests/test_portal_checker.py#L76) — `L76`
    - [`test_05_stalker_portal_checker_engine_multithreaded()`](tests/test_portal_checker.py#L84) — `L84`
    - [`test_06_scanner_view_portal_rotation_ui()`](tests/test_portal_checker.py#L117) — `L117`
    - [`test_07_main_window_start_mac_scan_multi_portal_rotation()`](tests/test_portal_checker.py#L167) — `L167`
    - [`test_08_check_single_portal_rejects_generic_web_server()`](tests/test_portal_checker.py#L222) — `L222` *(Verifiziert, dass generische Webserver (z. B. Apache/Nginx Default Page 200) als ungültig verworfen werden.)*
    - [`test_09_check_single_portal_detects_stalker_via_handshake_probe()`](tests/test_portal_checker.py#L238) — `L238` *(Testet, dass Stalker-Portale erkannt werden, wenn erst die Sondierung von server/load.php erfolgreich antwortet.)*
    - [`test_10_extract_portal_urls_from_text_and_folder()`](tests/test_portal_checker.py#L264) — `L264` *(Testet das regex-basierte Parsen von Portal-URLs aus Text und Ordnern.)*
    - [`test_11_scanner_view_smoothed_cps_and_eta()`](tests/test_portal_checker.py#L299) — `L299` *(Testet die geglättete Telemetrie- und ETA-Berechnung in ScannerView.)*
    - [`test_12_sporadic_error_logging_inspector()`](tests/test_portal_checker.py#L328) — `L328` *(Testet das sporadische Logging von Scan-Verbindungsfehlern in den HTTP-Inspector.)*
    - [`test_13_scanner_view_import_portals_from_folder()`](tests/test_portal_checker.py#L355) — `L355` *(Testet den Ordner-Import von Portal-URLs im ScannerView.)*
    - [`test_14_rejects_php_page_with_images_and_phpsessid()`](tests/test_portal_checker.py#L377) — `L377` *(Verifiziert, dass generische PHP-Seiten mit PHPSESSID und Bildern/Wörtern wie 'image' nicht als Stalker erkannt werden.)*
    - [`test_15_rejects_generic_json_apis_with_tokens_or_unauthorized()`](tests/test_portal_checker.py#L395) — `L395` *(Verifiziert, dass generische REST-APIs (z. B. OAuth Tokens oder 401 Unauthorized) nicht als Stalker fehlklassifiziert werden.)*
    - *... und 5 weitere Hilfsmethoden.*

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

### 📄 [`tests/test_scan_scheduler.py`](tests/test_scan_scheduler.py) (478 Zeilen)
#### Klassen & Komponenten
- **[`TestScanScheduler`](tests/test_scan_scheduler.py#L13-L474)** : *unittest.TestCase* — `L13-L474`
  - **Wichtige Methoden:**
    - [`setUp()`](tests/test_scan_scheduler.py#L14) — `L14`
    - [`test_01_mode_labels_and_descriptions()`](tests/test_scan_scheduler.py#L22) — `L22`
    - [`test_02_round_robin_distribution()`](tests/test_scan_scheduler.py#L34) — `L34`
    - [`test_03_hot_spot_affinity_focus_and_recovery()`](tests/test_scan_scheduler.py#L63) — `L63`
    - [`test_04_hot_spot_burst_extension_and_error_abort()`](tests/test_scan_scheduler.py#L110) — `L110`
    - [`test_05_adaptive_scoring_and_weights()`](tests/test_scan_scheduler.py#L141) — `L141`
    - [`test_06_failover_automatic_switch()`](tests/test_scan_scheduler.py#L162) — `L162`
    - [`test_07_sweep_exhaustive_matrix()`](tests/test_scan_scheduler.py#L196) — `L196`
    - [`test_08_sweep_early_exit_on_first_hit()`](tests/test_scan_scheduler.py#L217) — `L217`
    - [`test_09_multithreaded_concurrency()`](tests/test_scan_scheduler.py#L262) — `L262` *(Testet threadsichere Abarbeitung mit 8 parallelen Worker-Threads.)*
    - [`test_10_main_window_start_mac_scan_hot_spot_integration()`](tests/test_scan_scheduler.py#L311) — `L311`
    - [`test_11_hot_spot_backfills_previously_failed_macs()`](tests/test_scan_scheduler.py#L369) — `L369` *(Verifiziert, dass beim Entdecken eines Hot-Portals zuvor auf anderen Portalen abgewiesene MACs nachgetestet werden.)*
    - [`test_12_hot_spot_consecutive_misses_does_not_abort_scan_prematurely()`](tests/test_scan_scheduler.py#L428) — `L428` *(Simuliert den realen Fall: 50 MACs über 2 Portale.)*

---

### 📄 [`tests/test_settings_and_sidebar.py`](tests/test_settings_and_sidebar.py) (305 Zeilen)
> Unit tests for Sidebar Toggle Button ('Verbindung..'), SettingsView,
ConfigManager extended options, and live setting applications.

#### Klassen & Komponenten
- **[`TestSettingsAndSidebar`](tests/test_settings_and_sidebar.py#L25-L301)** : *unittest.TestCase* — `L25-L301`
  - **Wichtige Methoden:**
    - [`setUpClass(cls)`](tests/test_settings_and_sidebar.py#L27) — `L27`
    - [`test_01_sidebar_button_label_and_toggle()`](tests/test_settings_and_sidebar.py#L30) — `L30` *(Verify the top bar sidebar toggle button displays 'Verbindung..' and emits sidebar_toggled.)*
    - [`test_02_top_bar_settings_nav_pill()`](tests/test_settings_and_sidebar.py#L46) — `L46` *(Verify TopNavigationBar includes the Settings tab and emits view_changed.)*
    - [`test_03_config_manager_boost_options()`](tests/test_settings_and_sidebar.py#L63) — `L63` *(Verify ConfigManager defines and loads all handshake, scan, buffer, and vpn settings.)*
    - [`test_04_settings_view_load_modify_save()`](tests/test_settings_and_sidebar.py#L103) — `L103` *(Verify SettingsView loads config, modifies fields, and emits save signals.)*
    - [`test_05_main_window_settings_live_application()`](tests/test_settings_and_sidebar.py#L147) — `L147` *(Verify MainWindow integrates SettingsView, switches to it, and applies live updates.)*
    - [`test_06_device_id_mode_random_vs_deterministic()`](tests/test_settings_and_sidebar.py#L181) — `L181` *(Verify StbClient respects device_id_mode='random' vs 'deterministic'.)*
    - [`test_07_pcr_rate_smoothing()`](tests/test_settings_and_sidebar.py#L204) — `L204` *(Verify BufferSettings and _Session apply PCR rate smoothing when enabled.)*
    - [`test_08_check_mac_account_boost_options()`](tests/test_settings_and_sidebar.py#L230) — `L230` *(Verify check_mac_account accepts and uses genre_param, sortby_param, and fallback_get_all.)*
    - [`test_09_vpn_fallback_country_and_reload()`](tests/test_settings_and_sidebar.py#L263) — `L263` *(Verify NordVpnManager respects configured vpn_fallback_country and reload_config.)*
    - [`test_10_external_player_caching_and_hwdec()`](tests/test_settings_and_sidebar.py#L280) — `L280` *(Verify ExternalPlayerRunner passes caching_ms and hw_decode flags without crashing.)*

#### Wichtige Konstanten / Konfigurationen
- `APP_DIR` (L11)

---

### 📄 [`tests/test_ui_and_engine.py`](tests/test_ui_and_engine.py) (847 Zeilen)
> Automated Verification Suite for STB Pro v6.0 Qt6:
1. Responsive UI Layout, Dynamic Scaling & Zero-Overlap / Zero-Truncation Geometry Checks
2. StreamBufferProxy (Ringbuffer, PCR Pacing, Corrupt TS Guard, Wall-Clock Fallback, 0ms Stop)
3. VLCPlayerController (Non-Blocking Async Zapping, Sequence Cancellation, Lock-Free Telemetry)
4. MainWindow Channel Selection Debouncing & Buffering Status Restoration

#### Klassen & Komponenten
- **[`_MockTSHandler`](tests/test_ui_and_engine.py#L55-L90)** : *BaseHTTPRequestHandler* — `L55-L90`
  - **Wichtige Methoden:**
    - [`log_message(format)`](tests/test_ui_and_engine.py#L58) — `L58`
    - [`do_GET()`](tests/test_ui_and_engine.py#L61) — `L61`
- **[`TestUIAndEngine`](tests/test_ui_and_engine.py#L93-L843)** : *unittest.TestCase* — `L93-L843`
  - **Wichtige Methoden:**
    - [`setUpClass(cls)`](tests/test_ui_and_engine.py#L95) — `L95`
    - [`tearDownClass(cls)`](tests/test_ui_and_engine.py#L105) — `L105`
    - [`_assert_no_sibling_overlap(container, label)`](tests/test_ui_and_engine.py#L109) — `L109`
    - [`test_01_ui_scaling_and_non_overlapping_geometries()`](tests/test_ui_and_engine.py#L127) — `L127` *(Verify UI layout across multiple resolutions and UI scales has 0 overlaps and 0 truncated pills.)*
    - [`test_02_stream_buffer_pcr_corrupt_packet_and_fast_stop()`](tests/test_ui_and_engine.py#L264) — `L264` *(Verify StreamBufferProxy ignores TEI corrupt PCR packets, prefills cleanly, and stops in <50ms.)*
    - [`test_03_non_pcr_wall_clock_fallback()`](tests/test_ui_and_engine.py#L309) — `L309` *(Verify non-PCR streams unlock prefill via wall-clock fallback without hanging.)*
    - [`test_04_async_zapping_and_debounce()`](tests/test_ui_and_engine.py#L336) — `L336` *(Verify rapid channel switching never blocks the GUI thread and debounces EPG calls.)*
    - [`test_05_top_bar_tier2_codec_epg_and_blackout()`](tests/test_ui_and_engine.py#L379) — `L379` *(Verify:)*
    - [`test_06_high_bitrate_puffer_no_bloat_and_rebuffer_overlay()`](tests/test_ui_and_engine.py#L463) — `L463` *(Verify 4K/high-bitrate proxy does not choke or bloat to 128MB, and rebuffer overlay updates.)*
    - [`test_07_quality_tag_detection_and_dynamic_resolution_sync()`](tests/test_ui_and_engine.py#L543) — `L543` *(Verify quality_from_dimensions, detect_quality_tag and dynamic UI badge updates from decoded stream.)*
    - [`test_08_group_auto_validation_and_preview_thumbnails(mock_val)`](tests/test_ui_and_engine.py#L647) — `L647` *(Verify category selection auto-validates on first selection in session and loads thumbnails.)*
    - [`test_scanner_queue_retry_pause_and_folder_extract()`](tests/test_ui_and_engine.py#L703) — `L703` *(Testet die neuen Scanner-Optimierungen: Requeue bei 503/429/Timeout, Pause/Resume, Liste leeren und Ordner-Extraktion.)*
    - [`test_15_snapshot_playing_channel_no_name_error()`](tests/test_ui_and_engine.py#L831) — `L831` *(Verifies _snapshot_playing_channel executes without NameError for THUMB_DIR.)*

#### Modul-Funktionen
- **[`_make_ts_packet(pid, pcr_seconds, tei)`](tests/test_ui_and_engine.py#L35-L52)** — `L35` — *Build a valid 188-byte MPEG-TS packet with optional PCR.*

#### Wichtige Konstanten / Konfigurationen
- `APP_DIR` (L20)

---

### 📄 [`tests/test_vpn_and_stream_errors.py`](tests/test_vpn_and_stream_errors.py) (334 Zeilen)
> Unit Tests für IP- und ISP-Sperren-Erkennung sowie NordVPN-Manager.
Testet JSON-Fehler-Payloads (auch gzipped), HTML-WAF-Sperren,
Länder-Heuristiken und die StreamBuffer-Schutzlogik.

#### Klassen & Komponenten
- **[`TestVpnAndStreamErrors`](tests/test_vpn_and_stream_errors.py#L15-L330)** : *unittest.TestCase* — `L15-L330`
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
    - [`test_vpn_manager_rate_limit_pacing()`](tests/test_vpn_and_stream_errors.py#L269) — `L269`
    - *... und 1 weitere Hilfsmethoden.*

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
