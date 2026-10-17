# STB Pro Qt6 — Entwicklungs-Checkpoints & Audit

## 📋 Audit der bisherigen CustomTkinter-Version (`app.py`)
Vor der Überführung nach Python + Qt6 (PySide6/QML) wurden alle Module der bestehenden Version analysiert und folgende Schwachstellen, Bugs und fehlende QoL-Features identifiziert:

### Gefundene Bugs & Architektur-Probleme in der alten Version
1. **UI-Ruckeln & Frame-Drops beim Scrollen**: `ChannelListView` verschob `CTkFrame`-Widgets in einem `tk.Canvas`, während `VODView` tausende Zeilen synchron in ein `ttk.Treeview` einfügte.
2. **Passwort-Verlust im `ProfileDialog` (Bug)**: In `ui/components/profile_dialog.py` (`load_profile`) wurde `p.password` beim Öffnen des Dialogs **nicht** in `entry_xc_pass` geladen. Jedes Speichern eines Xtream-Profils überschrieb das Passwort mit einem leeren String.
3. **Verlust der VOD-Favoriten & "Zuletzt gespielt"-Liste**: `_vod_favs` in `app.py` und `recently_played_ids` in `channel_list.py` lagen nur im flüchtigen RAM und gingen bei jedem Neustart verloren.
4. **Sequenzielle Kategorie-Validierung**: `_on_validate_category` prüfte jeden Kanal einzeln nacheinander im selben Thread, was bei 500 Sendern über 15 Minuten dauerte.
5. **Ungenutzter M3U-Export**: `M3UClient.build_m3u()` existierte im Code, war aber nirgendwo in der Benutzeroberfläche aufrufbar.
6. **Statischer Inspector**: `InspectorView` zeigte nur den allerletzten Request als unformatierten Textblock an; vorherige Handshake-Schritte wurden sofort überschrieben.
7. **25ms Polling-Loop**: Permanente CPU-Last durch `self.after(25, self._poll_ui_queue)`.

---

## ✅ Entwicklungs-Checkpoints

### [x] Checkpoint 1: Projekt-Setup, Architektur & Core-Engine
- [x] Neuer Ordner `stb_pro_qt6/` mit dedizierter Python 3.12 `.venv` und `PySide6` eingerichtet.
- [x] `ARCHITECTURE.md` und `CHECKPOINTS.md` angelegt.
- [x] `core/models.py`: Erweiterte Dataclasses (`Channel`, `EPGProgram`, `Profile`, `StreamProbeResult`, `ScanResult`, `HttpLogEntry`).
- [x] `core/signals.py`: Reaktiver `AppEventBus` (`QObject` mit `Signal`) und `AsyncWorkerPool` (`QThreadPool`) als Ersatz für `after()`-Polling.
- [x] `core/config_manager.py`: Persistenz für Profile, Live-Favoriten, **VOD-Favoriten** und **Recently Played History** erweitert.
- [x] `core/mac_database.py`, `core/stream_buffer.py`, `core/stream_probe.py`, `core/preview_grabber.py`, `core/recorder.py`, `core/logo_cache.py` und `core/m3u_exporter.py` sauber modularisiert.

### [x] Checkpoint 2: Protokoll-Clients & Request-Telemetrie
- [x] `clients/stb_client.py`: Stalker/Ministra MAG Client mit automatischer Endpunkt-Erkennung, 14 STB-Hardware-Presets und Request-Telemetrie-Hook für den Inspector.
- [x] `clients/xtream_client.py`: Xtream Codes API Client inkl. Live, VOD, Serien & EPG.
- [x] `clients/m3u_client.py`: M3U/M3U8 Parser inkl. `#EXTVLCOPT` Header-Extraktion.
- [x] `clients/throttle.py`: Adaptiver `ScanThrottleController` gegen HTTP 429 / Cloudflare / WAF-Bans.

### [x] Checkpoint 3: Video-Engine & Fullscreen-OSD
- [x] `player/vlc_controller.py`: Hardware-beschleunigte LibVLC-Einbettung in natives Qt-Video-Surface + Ringpuffer-Proxy + Audio-/Untertitel-/Speed-Steuerung.
- [x] `player/external_player.py`: Nahtloser Start von externem VLC, MPV oder FFplay.
- [x] `player/osd_overlay.py`: Transparentes Fullscreen-HUD mit Auto-Hide bei Maus-Inaktivität, Echtzeit-Uhr, EPG-Fortschritt und einblendbarem Quick-Channel-Drawer (`[C]`).

### [x] Checkpoint 4: Qt6 Model/View, QML-Komponenten & Hauptansichten
- [x] `ui/theme.py`: Modernes "Obsidian Cyber-Cinema" Theme (QSS + Farb-Tokens).
- [x] `ui/qml/`: Hardware-beschleunigte QML-Komponenten (`TelemetryHeader.qml`, `ScannerDashboard.qml`).
- [x] `ui/models/channel_model.py`: Virtualisiertes `QAbstractListModel` + `QSortFilterProxyModel` + Custom `ChannelCardDelegate` für 100.000+ Sender mit 120 FPS.
- [x] `ui/models/vod_model.py`: Performantes `QAbstractTableModel` für Filme & Serien.
- [x] `ui/views/live_tv_view.py`: Split-View mit Schnellfiltern (Alle, Favoriten, Zuletzt, HD/4K), Multi-Thread Kategorie-Validator, M3U-Export, Video-Viewport, VOD-Seekbar & EPG.
- [x] `ui/views/vod_view.py`: VOD- & Serien-Kino mit Poster-Vorschau, IMDb-Sortierung, persistenten VOD-Favoriten & Direkt-Download.
- [x] `ui/views/scanner_view.py`: Multi-MAC Batch Scanner mit CPS-Anzeige (Checks/s), Restzeit (ETA), Masken-/OUI-Generator, Auto-DB-Save & Live-Filter-Tabs.
- [x] `ui/views/inspector_view.py`: Interaktiver Protokoll-Inspector mit Request-Historie, JSON-Tree, Handshake-Tester & **1-Click cURL-Generator**.
- [x] `ui/views/console_view.py`: Farbige Echtzeit-Konsole mit Suchfilter, Level-Filter & Log-Export.

### [x] Checkpoint 5: Dialoge, QoL-Upgrades & Verifikation
- [x] Alle 7 Dialoge (`profile_dialog.py`, `buffer_dialog.py`, `epg_guide_dialog.py`, `series_dialog.py`, `jobs_dialog.py`, `mac_db_dialog.py`, `json_viewer_dialog.py`) als eigene Module umgesetzt.
- [x] **Neu (QoL)**: Picture-in-Picture (PiP) / Always-on-Top Mini-Player Modus (`[P]`).
- [x] **Neu (QoL)**: Paralleler Kategorie-Stream-Validator (8 Worker gleichzeitig statt 1) + Option, tote Sender auszublenden oder wiederherzustellen.
- [x] **Neu (QoL)**: 1-Click M3U-Playlist-Export für aktuelle Auswahl/Kategorie/Favoriten.
- [x] **Neu (QoL)**: Passwort-Sichtbarkeits-Toggle & Profil-Klonen/Umbenennen im `ProfileDialog`.
- [x] Automatisierter Smoke- & Integrations-Test aller Module.

### [x] Checkpoint 6: Top-Bar 2-Tier Redesign, Codec-Detection & EPG/Video Polishing
- [x] **Top-Bar Entzerrung & 2-Tier Layout**: `Qt6 GPU` Badge entfernt; utility buttons (`Jobs`, `Puffer`, `PiP`, `Kino`, `Vollbild`) in die 2. Reihe unter die Reiter platziert.
- [x] **REC-Kapsel**: Feste Mindestbreite (125px) und Padding, damit Timer `REC 00:xx` niemals abgeschnitten wird.
- [x] **Video- & Audio-Codec Erkennung**: Echte MPEG-TS PAT & PMT Parsing-Engine in `core/stream_buffer.py` integriert; FourCC-Decoding in `player/vlc_controller.py` mit 32-bit Unsigned-Fix und Heuristik für 4K HEVC / H.264 / AAC / AC3 / E-AC3 erweitert.
- [x] **Sofortiges Öffnen des Programmführers**: `EPGGuideDialog` öffnet sich ohne Netzwerk-Latenz mit Ladeindikator/Progress-Bar; Duplikat-Schutz verhindert mehrfaches Öffnen bei Mehrfachklicks.
- [x] **Keine Video-Artefakte beim Stoppen**: `VideoSurfaceWidget.paintEvent` repainted den Win32/HWND-Surface solid schwarz (`#000000`), wodurch Direct3D Swapchain Freeze-Frames und Tab-Bleed-Through beseitigt sind.
- [x] **Puffer- & Telemetrie-Aktualisierung**: Anzeige für Aussetzer, Nachpuffern und Rebuffer-Zähler synchronisiert; Status-Label verwendet verlässlich den aktiven Wiedergabe-Sender.

### [x] Checkpoint 7: Beseitigung von Puffer-Ballooning, Bild-Freeze & Stream-Korruption
- [x] **Künstliche PCR-Drossel entfernt**: In `core/stream_buffer.py::_Session.serve` wurde die künstliche `cond.wait(min(wait, 0.2))` Drosselung komplett entfernt. Lokales TCP-Loopback zu LibVLC flow-controlled sich nativ nach Player-Bedarf ohne 1.28 Mbps Flaschenhals.
- [x] **Zero-Drop Chunk-Eviction**: Chunks werden im Ringpuffer nur noch freigegeben, wenn LibVLC sie bereits vollständig gelesen hat (`cpos >= base + len(c)`). Kein vorzeitiges Wegwerfen ungesehener MPEG-TS Pakete mehr -> Beseitigung von NAL-Verlust, Bildabrissen und Macroblocking.
- [x] **Robuste Bitraten-basierte Puffer-Berechnung**: `_level_s` nutzt primär die physische Bitrate (`unconsumed / bytes_per_sec`) mit Plausibilitätsfilter für PCR-Jumps/Diskontinuitäten. Puffer füllt sich nicht mehr unkontrolliert bis 128 MB (180s) auf.
- [x] **Aktualisierung von "Überbrücke Aussetzer" & "Nachpuffern"**: Veraltete `is_actively_rendering` Bedingung entfernt, sodass Rebuffer- und Vorab-Puffer-Zustände sofort und unverzögert in OSD und Top-Pills gerendert werden.
- [x] **Test-Suite erweitert**: `test_06_high_bitrate_puffer_no_bloat_and_rebuffer_overlay` hinzugefügt und alle 6 Tests erfolgreich bestanden.

### [x] Checkpoint 8: Flow-Control Pacing, Rolling PCR Mux Bitrate & Single-Writer Protection
- [x] **Upstream Flow-Control Pacing**: In `_Session._produce()` wurde aktives Pacing integriert: Sobald der Puffer das konfigurierte Ziel (`target_s`, z. B. 15 s) erreicht hat, pausiert das Upstream-Lesen via `cond.wait(0.04)`. Dies verhindert unkontrolliertes Vorsaugen in die Live-Kante des Providers, Anti-Scrape-Server-Trennungen nach ~20 Sekunden und unbegrenzten Puffer-Aufbau.
- [x] **Rolling PCR Mux-Bitrate & Jitter-Eliminierung**: Fragile PCR-Diskontinuitätsberechnungen durch ein rollendes PCR-Delta-Fenster ersetzt (`_record_pcr`). Die Bitrate wird direkt aus dem MPEG-TS Mux errechnet und bleibt glatt und kontinuierlich. Das Springen zwischen 30+ und 120+ Sekunden ist vollständig beseitigt.
- [x] **Single-Writer Sequence Guard**: In `_Session.serve()` verhindert ein atomarer Writer-Sequenzzähler (`_writer_seq`), dass parallele Socket-Anfragen von LibVLC (z. B. HEAD/Probe oder Reconnect) denselben Stream korrumpieren oder Pakete aufteilen.
- [x] **HTTP/1.1 & HEAD Support im Proxy**: `_Handler` antwortet nun sauber auf `HEAD`-Anfragen und liefert normgerechte HTTP/1.1 Live-Streaming-Header (`no-cache, no-store`).
- [x] **VLC Network Caching**: Erhöhung der LibVLC-Netzwerkpufferung auf 800–2000 ms (`max(800, min(st.vlc_caching_ms, 2000))`), um 4K UHD Decoder-Starvation bei Frame-Jitter zu verhindern.

### [x] Checkpoint 9: High-Speed Multi-MAC Scanning, Resilient Stalker Probing & Stream-Link Auto-Resolution
- [x] **Uncapped Multi-Thread Scanning & CPS Optimierung**:
  - Künstliche Begrenzung auf maximal 20 Threads aufgehoben (`spin_threads` bis 250 Threads regelbar).
  - Zusätzliche Micro-Delay Presets (`0 ms`, `20 ms`, `50 ms`) im Scanner für maximale Durchsatzraten.
  - 1-Time Preflight Endpoint Discovery: Ermittelt und cacht den korrekten Stalker-Endpunkt (`load_url` / `portal.php`) einmalig vor dem Multi-Thread-Start, wodurch spekulative 6-URL-Fallback-Probes für jede MAC entfallen.
  - Worker-Session HTTP Keep-Alive: Jeder Worker-Thread behält eine langlebige `requests.Session` zur Vermeidung von TCP/TLS-Handshake-Overhead (~100–300 ms Ersparnis je Check).
- [x] **Session-Cookie-Isolation**:
  - Zwingendes `session.cookies.clear()` vor jedem einzelnen MAC-Handshake implementiert. Verhindert die Verschleppung von `PHPSESSID`- und Session-Cookies zwischen verschiedenen Accounts innerhalb desselben Worker-Threads.
- [x] **Lightweight Channel Probing & 0-Kanal Bugfix**:
  - Vollkatalog-Download via `get_all_channels` (5–8 MB JSON) durch paginiertes `get_ordered_list(genre='*', p='1')` ersetzt. Extrahiert direkt das `total_items`-Feld aus dem JSON-Header (~2 KB Payload, ~100 ms Abfragezeit).
  - Resilientes Auto-Requeue: Bei aktiven Accounts mit Zukunftslaufzeit (z. B. 2027), deren Kanalabfrage unter Scan-Last einen transienten Timeout oder 503 erleidet, wird der Account nicht mehr voreilig mit 0 Kanälen abgeschlossen, sondern automatisch hinten angestellt (`[⏳ Requeue] ... (Kanal-Timeout)`).
  - Saubere Fehlerklassifizierung: Nicht-autorisierte oder abgewiesene MACs werden einheitlich als `Ungültig / Nicht autorisiert` angezeigt statt roher HTML-404-Fehler. Echte 0-Kanal-Testaccounts zeigen sauber `0`, ungültige `—`.
- [x] **Dynamische Scan-Steuerung bei Pause & Resume**:
  - Einstellungen für Threads und Delay können bei pausiertem Scan beliebig geändert werden.
  - Beim Fortsetzen (`▶ FORTSETZEN`) oder live während des Scans skaliert die Engine den Thread-Pool dynamisch (spawnt neue Worker bei Erhöhung, überzählige Worker beenden sich sauber bei Reduzierung). Der Throttle-Controller übernimmt das neue Delay ohne Neustart.
  - QoL-Buttons: Scan pausieren/fortsetzen, Liste leeren, sowie rekursiver MAC-Import aus Ordnern mit automatischer Bereinigung von Duplikaten.
- [x] **Kompakte UI-Filter & Strukturierter Hit-Export**:
  - Filter-Pills über der Treffertabelle auf `ALL`, `HOT (N)` (als einziger Reiter mit Live-Zähler für aktive Accounts mit >0 Sendern), `OK` und `ERR` verkürzt.
  - Exportfilter: Es werden ausschließlich verifizierte `HOT`-Treffer (`tag == 'hot'` und `channels > 0`) exportiert.
  - Dynamischer Standard-Dateiname: `<hostname>_<hits>hits_<YYYY-MM-DD>.txt` (z. B. `iptvgarden.streamtv.to_3hits_2026-10-17.txt`).
  - Strukturierte ASCII-Block-Formatierung (`Portal`, `Status`, `Mac`, `Scandate`, `Expire`, `Channels`).
- [x] **Stalker Stream-Link Resolution & Auto-Patching**:
  - Behebung des `id: null, stream=&` Fehlers bei Portalen mit vorformatierten Kanal-CMDs: Extraktion der Stream-ID und primäre Abfrage über native MAG-Kandidaten (`ffmpeg http://localhost/ch/{ch_id}_`).
  - Auto-Patching für leere `stream=&` und automatische Anreicherung von leeren `&sn2=` Parametern mit `device_id2`, um HTTP 511 (Network Authentication Required) Fehler auf Streaming-Servern zuverlässig zu verhindern.
- [x] **UI & Layout Polishing**:
  - Shortcut-Infos nach rechts neben den Jobs-Button verlegt.
  - Sidebar-Toggle in die zweite Reihe linksbündig, Logo ("STB-EMU PRO") linksbündig in die erste Reihe platziert.
  - Fenstertitel auf `"STB-Emulator Pro by InfoHazard & H7CFoX"` gesetzt und App-Icon integriert.
  - Double-Click Playback-Fix im virtuellen Senderlisten-Modell.
  - Automatisches EPG- & Preview-Grabben beim ersten Auswählen einer Sendergruppe mit Session-Cache.

---

### [x] Checkpoint 10: Dynamisches Scan-Repository & Host-/Login-Profilverwaltung (`mac_scans`)
- [x] **Scan-Repository Engine (`core/scan_repository.py`)**:
  - Automatisches Scannen und Einlesen aller strukturierten Treffer-Dateien (`*.txt`) aus dem Ordner `mac_scans/`.
  - Blockweiser Parser für das ASCII-Trefferformat (`Portal`, `Status`, `Mac`, `Scandate`, `Expire`, `Channels`).
  - Gruppierung nach Hostnames (`ScanHost`) und Normalisierung der Portale.
  - Automatische Sortierung der Accounts (`ScanAccount`) nach Kanalanzahl absteigend (Top-Accounts mit maximaler Sendervielfalt sofort an erster Stelle).
- [x] **Sidebar-Redesign: Host- und Login-Auswahl (`ui/components/sidebar.py`)**:
  - Alte statische Dummy-Profile aus der Hauptauswahl entfernt und durch ein 2-stufiges System ersetzt:
    1. **Host / Scan-Portal Dropdown (`combo_hosts`)**: Listet alle gescannten Hosts auf (inklusive Gesamt-Treffer und Max-Kanal-Badge).
    2. **Login / MAC Dropdown (`combo_logins`)**: Listet alle Accounts des gewählten Hosts auf (`MAC • Kanäle • Ablauf`).
  - **Live Account Info-Card**: Kompakte 2-Zeilen-Übersicht für Status (`🟢 Aktiv`), Kanäle (`13.180 Kanäle`), Ablaufdatum und Scandatum.
  - **Schnellverbindungs-Synchronisation**: Automatische Übernahme von Portal-URL und MAC in die Eingabefelder bei Auswahl eines Logins.
  - **QoL-Steuerung**: Schnellbuttons `🔄 Neu laden` (rescannt den Ordner zur Laufzeit) und `📂 Ordner` (öffnet `mac_scans/` direkt im Explorer).
- [x] **Scanner-Export Integration & Auto-Reload**:
  - Standard-Speicherpfad für Hit-Exporte im Scanner direkt auf den Ordner `mac_scans/` gesetzt.
  - Automatischer Trigger von `scan_repo.reload()` nach jedem Export, sodass neue Scans sofort ohne Neustart in der Profilauswahl erscheinen.
- [x] **Test-Abdeckung**:
  - Neuer dedizierter Test `tests/test_scan_profiles.py` verifiziert das Einlesen, Sortieren und die Profilerzeugung.
  - Sämtliche 9 UI- und Engine-Tests in `tests/test_ui_and_engine.py` erfolgreich (100% OK).

---

### [x] Checkpoint 11: Multi-Host Probing, Telegram-Reverse-Engineering & ISP/Geo-Status-Diagnostik
- [x] **Reverse-Engineering Analyse (`C:\Users\basti\Desktop\Telegram\`)**:
  - Analyse von `Zenith_Nexus_v6.0_Premium_English.py`, `API_MAC_SCANNER_FINAL.py`, `MacScan.py`, `RobHartz4Edition.py`, `Original Pro_StbMac_Pandora_v5.py`.
  - Extraktion des De-Facto-Standards für MAC-Hashing:
    - `sn = MD5(mac).upper()[:13]`
    - `dev1 = SHA256(mac).upper()`
    - `dev2 = SHA256(sn + '+' + mac).upper()`
    - `sig = dev2`
  - Integration von Standard-Headers (`X-User-Agent: Model: MAG254; Link: Ethernet,WiFi`, `Accept: application/json, text/javascript, */*`, `Accept-Encoding: gzip, deflate`) und Bypass-Parametern (`force_ch_link_check=0`, `download=0`, `series=`, `forced_storage=0`, `disable_ad=0`).
  - Stream-Request Header (`hea3`): `Icy-MetaData: 1`, `Range: bytes=0-`, `Accept-Encoding: identity`, `User-Agent: Lavf/58.29.100` / `VLC` Fallback.
- [x] **IPTV Status-Code Diagnostik (`diagnose_iptv_status`)**:
  - Mapping von Streaming-Fehlercodes in `core/stream_probe.py` und `core/stream_buffer.py`:
    - `HTTP 456`: Geo-Lock / ISP-Datacenter-ASN-Sperre oder Multi-Connection Limit erreicht.
    - `HTTP 407`: Proxy erforderlich / Provider-seitige Länderbeschränkung.
    - `HTTP 459`: Stream-Leitung belegt (Concurrent Connection Limit).
    - `HTTP 511`: Cloudflare WAF Challenge / Device-Auth mit `sn2` erforderlich.
    - `HTTP 401`: Token abgelaufen oder ungültig.
    - `HTTP 403`: Account gesperrt / deaktiviert.
    - `HTTP 429`: Server-Rate-Limit (Pause 5s).
  - Feedback in der UI: Bernsteinfarbene Warn-Badges in `HeroCard` und Statusanzeigen (`⚠️ Server-Rückmeldung: <error>`), kein schwarzer Freeze-Screen mehr.
- [x] **Multi-Host Live Probing Benchmark**:
  - Live-Tests über 8 Portale hinweg (`clubxc.com`, `t-rex4k.top`, `paplive.me`, `iptv.darktv.eu`, `pro.8k-strong.tv`, `hottest.vip`, `iptvgarden.streamtv.to`, `web2021.biz`).
  - Validierung von Geo-IP-Effekten: Umschalten auf US-VPN schaltete `clubxc.com` direkt von `HTTP 407` auf `🟢 1080p FHD @ 4.6 Mbps (HTTP 200)` frei.
  - Erkennung von `HTTP 456 Geo Blocked` auf `iptv.darktv.eu` (reine DE-Kanalliste blockiert US-Datacenter ASNs) und `HTTP 511` auf `pro.8k-strong.tv` (Cloudflare Edge Protection).
  - Enforced Account-Filter: Accounts mit `Expire: 0000-00-00` (inaktive Dummies seit 2022) werden im Test- und Scan-Workflow strikt ignoriert.

---

### [x] Checkpoint 12: Live TV Progress-Bar Redesign & Zwei-Phasen Auto-Thumbnail-Engine
- [x] **Progress-Bar Redesign & Beseitigung von Text-Clipping**:
  - `self.val_progress` Höhe von 6px auf **18px** angehoben (`min-height: 18px`, `max-height: 18px`).
  - Vertikales Abschneiden der Prozentanzeige (`64%` zur Hälfte abgeschnitten) vollständig beseitigt.
  - Neues Theme-Styling `#ValidationProgressBar`: Dunkelblauer Hintergrund (`#0F172A`), kontrastreiche zentrierte weiße Schrift (`#F8FAFC`, 10px bold), abgerundete Ecken (5px) und Indigo-Cyan-Emerald Farbverlauf im Chunk.
  - Dynamische Textformatierung:
    - Phase 1: `🩺 Prüfe Sender: {done} / {total} ({pct}%)`
    - Phase 2: `📸 Lade Vorschaubilder: {done} / {total} ({pct}%)`
- [x] **Zwei-Phasen Kategorie-Validierung**:
  - **Phase 1 (Paralleler Health-Check)**: Blitzschnelle Überprüfung von Ping/Latenz, Stream-Erreichbarkeit und echten Qualitäts-Badges (`FHD`, `HD`, `UHD`) mit 8 Worker-Threads. Blockiert nicht mehr auf trägen FFmpeg-Frames.
  - **Phase 2 (Automatischer Thumbnail-Grabber)**: Startet nach Abschluss von Phase 1 vollautomatisch für alle Online-Sender der Gruppe, die noch kein Bild im Disk-Cache haben.
  - Schonender **2-Worker-Pool** mit **4,5s FFmpeg-Timeout** und kooperativem Abbruch via `_val_stop_ev`, um Server-Trennungen (HTTP 459) und CPU-Spikes zu verhindern.
  - Live-Aktualisierung: Sobald ein Thumbnail eintrifft, wird die Senderkarte per `delegate.set_thumbnail()` im Viewport live aktualisiert und dauerhaft in `.cache/thumbs/{profile}:{ch_id}.jpg` abgelegt.
  - Der `⏹ Stopp`-Button bricht sowohl die Prüfung als auch das Thumbnail-Ziehen sofort ab.
- [x] **Manuelle On-Demand Thumbnail-Abfrage**:
  - Neuer Kontextmenü-Eintrag in der Senderliste: `📸 Vorschaubilder für sichtbare Sender laden` (`fetch_group_thumbnails_requested` -> `start_group_thumbnail_fetch`).
- [x] **Kamera-Platzhalter Glyph-Korrektur**:
  - Schriftart für den Standbild-Platzhalter (`📷`) in `ChannelCardDelegate.paint()` auf `Segoe UI Symbol` umgestellt, sodass vor dem Eintreffen des Bildes kein schwarzer Block mehr gezeichnet wird.
- [x] **Automatisierte Verifikation**:
  - Alle 9 Testsuiten in `tests/test_ui_and_engine.py` erfolgreich (100% OK).
  - Fortschrittsbalken-Formatierung, Höhenprüfung und Sichtbarkeitszustände automatisiert verifiziert.

---

### [x] Checkpoint 13: High-Speed In-Memory Thumbnail Engine & Viewport Auto-Loader
- [x] **Ursachenanalyse der fehlenden Thumbnails (Behebung des 4.5s Timeout-Bottlenecks)**:
  - FFmpeg benötigte über HTTP-Streams mit standardmäßigem `probesize=1500000` und `analyzeduration=1500000` zwischen 5,5 und 7,2 Sekunden, um den ersten Video-Frame über das Netzwerk zu puffern.
  - Das bisherige harte 4,5s Timeout brach fast alle Netzwerk-Grabs vorzeitig ab (`thumb_sz=0`), wodurch nur 1-2 besonders flinke Sender ein Bild erhielten.
  - Beim Starten einer Wiedergabe brach `play_channel` die Hintergrund-Extraktion mit `_val_stop_ev.set()` für alle verbleibenden Sender ab.
- [x] **Single-Pass In-Memory Frame Extraktion (`extract_thumbnail_from_ts`)**:
  - In `probe_stream`: Der ohnehin für die Bitraten- und Codec-Analyse heruntergeladene TS-Stream-Chunk (768KB - 1MB) wird direkt im Speicher belassen.
  - FFmpeg decodiert den Keyframe via `stdin` Memory-Pipe (`pipe:0`) in **unter 0,12 Sekunden**!
  - Phase 1 der Kategorie-Validierung liefert dadurch Latenz, Auflösung **UND** fertiges Thumbnail in einem einzigen Durchgang für alle 8 Threads gleichzeitig.
  - Reduziert die Gesamtzeit einer 15-Sender-Gruppe von über 45 Sekunden auf **unter 2 Sekunden**!
- [x] **Schwarze Dummy-Frames Filterung & Disk-Cache Bereinigung**:
  - Kategorietrenn-Kanäle (`####### HULU RAW #######`) und Stream-Starts mit schwarzen Initial-Frames erzeugten 581-Byte JPEGs (`#000000` Pixel).
  - Neue Validierung `is_blank_or_black_jpeg(data)` filtert korrupte oder rein schwarze Dummy-Bilder vor dem Speichern heraus und löscht bestehende Fehl-Dateien aus `.cache/thumbs/`.
  - Vermeidet unschöne schwarze Kacheln in der Senderliste.
- [x] **Automatischer Viewport-Thumbnail-Lader**:
  - `LiveTVView` überwacht per entprelltem `_visible_thumbs_timer` (350ms) das Scrollen der Senderliste.
  - Sichtbare Sender ohne Thumbnail werden beim Verweilen vollautomatisch im Hintergrund angefordert, ohne dass der Nutzer manuell "Gruppe prüfen" klicken muss.
- [x] **Live-Wiedergabe Snapshot-Engine**:
  - Sobald ein Sender aktiv abgespielt wird, nimmt LibVLC nach 1,8 Sekunden einen direkten Snapshot aus dem gerenderten Video-Surface (`vlc_ctrl.snapshot()`).
  - Der abgespielte Sender erhält sofort ein frisches Live-Thumbnail samt grünem `LIVE`-Badge.
- [x] **120 FPS Delegate-Optimierung**:
  - Senderkarten-Thumbnails werden in `set_thumbnail()` einmalig mit Smooth-Transformation auf 56x32 vor-skaliert.
  - Kein dynamisches Bild-Skalieren im `paint()`-Event mehr; Cache-Misses werden gespeichert, um wiederholte Disk-I/O während der GPU-Darstellung zu eliminieren.

---

### [x] Checkpoint 14: Code Index Register, Agent-Regel & GitHub Release Repository Setup
- [x] **Automatisierter Code-Index & Symbol-Register (`CODE_INDEX.md`)**:
  - Generator `tools/generate_code_index.py` via Python `ast` (Abstract Syntax Tree) implementiert.
  - Erfasst alle Module, Klassen, Methoden, Funktionen, Signals, Konstanten und Unittests mit exakten Start- und Endzeilennummern sowie Docstrings.
  - Universell tragfähige, relative Markdown-Links (`[file.py](file.py#L10-L50)`) für direkte Navigation auf GitHub, in IDEs und für AI-Agents.
  - Integrierter CLI-Prüfmodus `python tools/generate_code_index.py --check` für CI/CD-Pipelines.
- [x] **Dauerhafte Agent-Richtlinie (`.agents/rules/code_index_maintenance.md`)**:
  - Obligatorische Konsultation von `CODE_INDEX.md` vor allen Breitband-Recherchen und Dateidurchsuchungen zum Schutz von Kontext- und Token-Budget.
  - Verbindliche Vorgabe zur automatischen Ausführung des Index-Generators nach Code-Änderungen.
- [x] **Ordner-Bereinigung & Release-Standardisierung**:
  - Lose Ad-hoc-Skripte und manuelle Testläufe sauber nach `tests/manual/` überführt.
  - Werkzeuge zur Codegenerierung nach `tools/` modularisiert.
  - Bild-Assets bereinigt (temporäre Multi-Resolution Build-PNGs entfernt, `assets/app_icon.png` in `README.md` verknüpft).
- [x] **Release-Dateien & GitHub Setup**:
  - `.gitignore`: Ausschluss von virtuellen Umgebungen (`.venv/`), Runtime-Caches (` record/`, `thumbs/`, `logos/`), persönlichen MAC-Hitlisten (`ALL MACS.txt`, `mac_scans/`), lokalen Datenbanken (`mac_database.json`) und Passwörtern (`config.json`).
  - `LICENSE`: Vollständige MIT-Lizenz (Copyright 2026 InfoHazard & H7CFoX).
  - `pyproject.toml`: Modernes PEP 517/621 Build- & Metadaten-Manifest inklusive CLI-Entrypoint `stb-pro-qt6 = "main:main"`.
  - `config.example.json`: Bereinigte Vorlage ohne sensible Zugangsdaten für Open-Source-Distribution.
  - `.github/workflows/ci.yml`: GitHub Actions Matrix-CI (Windows/Ubuntu, Python 3.11/3.12) mit Code-Index-Validierung und headless Qt-Unittests.
  - Initialer Release-Commit (`feat: initial release of STB-Emulator Pro Qt6 (v1.0.0)`) mit 76 Dateien und 18.178 Zeilen im Master-Branch erstellt.
