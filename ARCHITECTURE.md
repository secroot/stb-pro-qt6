# STB Pro Qt6 — Architektur- & Modul-Dokumentation

## 1. Zielsetzung & Warum Qt6 (PySide6 + QML/QtQuick)
Die ursprüngliche CustomTkinter-Version (`app.py`) litt unter den inhärenten Limitierungen von Tkinter:
- **Single-Threaded CPU-Rendering**: Jedes Widget-Update, jedes Scrollen und jedes Nachladen von Kanal-Logos blockierte den GUI-Mainthread.
- **Kein natives Model/View-Virtual-Scrolling**: Das manuelle Verschieben von Frame-Widgets auf einem `tk.Canvas` führte bei großen Senderlisten (10.000+ Kanäle) zu spürbarem Ruckeln.
- **UI-Polling statt Event-Driven Reactivity**: Ein 25ms-Polling-Loop (`_poll_ui_queue`) musste permanent prüfen, ob Hintergrund-Threads Ergebnisse geliefert haben.
- **HWND-Konflikte im Vollbild**: Das Umhängen des Video-Canvas über `place(in_=self)` verursachte Flackern und Skalierungsfehler.

Die **STB Pro Qt6 Edition** löst diese Probleme fundamental durch:
1. **Echte Event-Reaktivität (`QtCore.Signal` & `Slot`)**: Hintergrund-Threads (`QThreadPool` / `QRunnable` / Worker) kommunizieren über typsichere Qt-Signale direkt und verzögerungsfrei mit der UI – ohne Polling-Loops.
2. **Hardware-beschleunigtes Virtual Scrolling (`QAbstractListModel` + `QStyledItemDelegate` & QML)**: Egal ob 500 oder 100.000 Kanäle – es werden exakt nur die im Viewport sichtbaren Zeilen mit 60/120 FPS über `QPainter` / GPU gezeichnet.
3. **QML / QtQuick Telemetrie-Komponenten**: Moderne, flüssig animierte Status- und Telemetrie-Widgets (`ui/qml/`).
4. **Saubere Schichten-Architektur (Separation of Concerns)**: Keine Datei überschreitet eine übersichtliche Größe; Datenmodelle, Protokoll-Clients, Video-Engine, Views und Dialoge sind strikt voneinander getrennt.

---

## 2. Verzeichnis- & Modulstruktur

```text
stb_pro_qt6/
├── ARCHITECTURE.md                  # Diese Architektur-Dokumentation
├── CHECKPOINTS.md                   # Entwicklungs-Checkpoints, Audit & behobene Bugs
├── README.md                        # Bedienungsanleitung, Features & Hotkeys
├── requirements.txt                 # Python-Abhängigkeiten (PySide6, python-vlc, requests, Pillow)
├── start_qt6.bat                    # Windows-Starter (automatisches Python 3.12 .venv Setup)
├── main.py                          # Application Bootstrapper & High-DPI Initialisierung
│
├── core/                            # Kernlogik, Zustand & Persistenz (keine UI-Abhängigkeiten)
│   ├── models.py                    # Dataclasses (Channel, EPGProgram, Profile, StreamProbeResult, HttpLogEntry)
│   ├── signals.py                   # Zentraler AppEventBus (Qt Signals für globale App-Events)
│   ├── config_manager.py            # Atomare JSON-Persistenz (Profile, Live/VOD-Favoriten, Verlauf, Settings)
│   ├── mac_database.py              # Thread-sichere MAC-Hit-Datenbank (Portal-Index + Global History)
│   ├── logo_cache.py                # Asynchroner QPixmap/QImage Downloader mit RAM- & Disk-Cache
│   ├── stream_buffer.py             # Lokaler PCR-getakteter MPEG-TS Ringpuffer-Proxy (127.0.0.1)
│   ├── stream_probe.py              # Stream-Health, PCR-Bitraten-Berechnung & FFprobe-Analyse
│   ├── preview_grabber.py           # FFmpeg Standbild-Vorschau-Generator mit Alters-Cache
│   ├── recorder.py                  # Live-Aufnahme & VOD/Archiv-Download (HTTP Range Resume + FFmpeg HLS)
│   └── m3u_exporter.py              # M3U8-Generator zum Exportieren von Kanallisten, Kategorien & Favoriten
│
├── clients/                         # IPTV-Protokoll-Clients & Pentest-Scanner
│   ├── stb_client.py                # Stalker/Ministra MAG Emulator + Endpunkt-Discovery + Request-Hooks
│   ├── xtream_client.py             # Xtream Codes API Client (Live, VOD, Serien, EPG)
│   ├── m3u_client.py                # M3U/M3U8 Parser (inkl. #EXTVLCOPT User-Agent/Referer)
│   └── throttle.py                  # ScanThrottleController (HTTP 429 / WAF Cooldown & adaptives Pacing)
│
├── player/                          # Video-Wiedergabe & Fullscreen-HUD
│   ├── vlc_controller.py            # LibVLC Hardware-Player + Proxy-Anbindung + Spur-/Tempo-Steuerung
│   ├── external_player.py           # Prozess-Steuerung für externe Player (VLC, MPV, FFplay)
│   └── osd_overlay.py               # Rahmenloses Fullscreen-OSD mit Auto-Hide, Uhr & Quick-Channel-Drawer
│
└── ui/                              # Modulare Qt6 Benutzeroberfläche
    ├── theme.py                     # Obsidian Cyber-Cinema Design-Tokens & QSS Stylesheet
    ├── main_window.py               # Hauptfenster, Layout-Orchestrierung, PiP-Modus & globale Hotkeys
    ├── qml/                         # Deklarative QtQuick / QML Komponenten
    │   ├── TelemetryHeader.qml      # Reaktives QML Stream-Telemetrie-Banner
    │   └── ScannerDashboard.qml     # Reaktives QML MAC-Scanner Live-Dashboard
    ├── models/                      # Hochperformante Qt Datenmodelle
    │   ├── channel_model.py         # QAbstractListModel + QSortFilterProxyModel + Custom Card Renderer
    │   └── vod_model.py             # QAbstractTableModel + Multi-Column Sort/Filter Proxy
    ├── components/                  # Wiederverwendbare Hauptkomponenten
    │   ├── top_bar.py               # Navigationsleiste, Provider-Status, REC/Jobs-Badges, Kino/PiP-Buttons
    │   ├── sidebar.py               # Ein-/ausklappbare Profil- & Engine-Steuerleiste
    │   ├── hero_card.py             # Kanal-Info-Header mit Qualitäts-Pills, Puffer-Füllstand & Aktionen
    │   └── epg_panel.py             # Now/Next EPG-Anzeige mit Fortschrittsbalken & Guide-Button
    ├── views/                       # Haupt-Tabs
    │   ├── live_tv_view.py          # Live-TV Arbeitsbereich (Senderliste, Video-Player, Seekbar, EPG)
    │   ├── vod_view.py              # VOD & Serien-Kino mit Poster-Panel, Filtern & Favoriten
    │   ├── scanner_view.py          # Multi-MAC Batch Scanner, Generator, CPS/ETA & Ergebnis-Filter
    │   ├── inspector_view.py        # Request-Historie, Header/JSON-Inspector, Handshake-Test & cURL-Export
    │   └── console_view.py          # Echtzeit-Log-Konsole mit Level-Farben, Textfilter & Datei-Export
    └── dialogs/                     # Eigenständige Dialogfenster
        ├── profile_dialog.py        # Verbindungs- & Profil-Editor (Stalker, Xtream, M3U)
        ├── buffer_dialog.py         # Detaillierte Ringpuffer- & VLC-Einstellungen
        ├── epg_guide_dialog.py      # Mehr-Tages-EPG mit Timeshift/Archiv-Wiedergabe & Download
        ├── series_dialog.py         # Staffel- & Episoden-Auswahl für Serien
        ├── jobs_dialog.py           # Live-Manager für Aufnahmen & Downloads
        ├── mac_db_dialog.py         # Hit-Datenbank-Explorer & Dubletten-Bereinigung
        └── json_viewer_dialog.py    # Interaktiver Baum-/JSON-Inspektor für Rohdaten
```

---

## 3. Datenfluss & Threading-Modell
- **UI-Thread**: Führt ausschließlich das Event-Handling, die `QAbstractItemModel`-Updates und das Zeichnen aus.
- **Worker-Pool (`core/signals.py` & `QThreadPool`)**: Alle Netzwerk-Operationen (Portal-Handshake, Kanallisten-Abruf, Stream-Probing, EPG-Abruf, Kategorie-Validierung, MAC-Scanning) laufen in Hintergrund-Threads und emittieren nach Abschluss typsichere `QtCore.Signal`-Events.
- **Stream-Ringpuffer (`core/stream_buffer.py`)**: Eigener lokaler HTTP-Server (`127.0.0.1`), der MPEG-TS-Pakete im Hintergrund vom Provider liest, anhand der PCR-Zeitstempel taktet und bei kurzen Provider-Aussetzern nahtlos neu verbindet.

---

## 4. High-Throughput Scanner & Stalker Probing Engine
- **Preflight Endpoint Discovery**: Vor dem Start von Multi-Worker-Scans ermittelt der Scanner den echten Stalker-Endpunkt (`portal.php` oder `load.php`) einmalig vorab und cacht ihn global. Dadurch entfallen zeitaufwendige spekulative Fallback-Probes auf 6 verschiedene Endpunkte für jede einzelne MAC.
- **Session Cookie Isolation**: Bei persistenten Worker-Sessions mit HTTP Keep-Alive wird vor jedem Handshake `session.cookies.clear()` ausgeführt. Dies eliminiert `PHPSESSID`-Leckagen und Status-Übertragungen zwischen verschiedenen Accounts.
- **Lightweight Paginierte Kanalabfrage**: Statt ressourcenintensiver Vollkatalog-Downloads (`get_all_channels`, 5–8 MB JSON) fragt der Scanner paginiert `get_ordered_list(genre='*', p='1')` ab und liest direkt das `total_items`-Feld aus (~2 KB Payload, ~100 ms).
- **Resilientes Auto-Requeue**: Bei aktiven Accounts mit Zukunfts-Ablaufdatum, deren Kanalabfrage unter Last ins Timeout oder auf Serverfehler (503/429) läuft, wird die MAC mit Retry-Zähler hinten angestellt (`[⏳ Requeue]`), statt sie mit 0 Sendern abzuspeichern.
- **Dynamisches Thread-Scaling**: Während eines pausierten Scans oder live im Betrieb können Thread-Zahl (1–250) und Micro-Delay (0–2000 ms) angepasst werden. Die Engine skaliert den Worker-Pool nahtlos ohne Neustart.

---

## 5. Stream-Resolution & Auto-Patching
- **MAG Candidate Normalization**: Falls das Portal im Kanal-CMD bereits vorformatierte URLs liefert, extrahiert `create_link` die Stream-ID und priorisiert native STB-Befehle (`ffmpeg http://localhost/ch/{ch_id}_`), wodurch serverseitige Regex-Fehler (`id: null, stream=&`) vermieden werden.
- **Auto-Patching für `stream=&` und `&sn2=`**:
  - Sollte ein Portal dennoch ein leeres `stream=&` zurückliefern, setzt der Client die bekannte Kanal-ID automatisch ein.
  - Ein leeres `&sn2=` im Stream-Link wird automatisch mit der `device_id2` des STB-Clients befüllt, womit HTTP 511 (Network Authentication Required) Fehler auf Streaming-Servern zuverlässig verhindert werden.

---

## 6. Zwei-Phasen Kategorie-Validierung & Auto-Thumbnail-Engine
- **Phase 1: Paralleler Health-Check**:
  - Nutzt einen Worker-Pool mit bis zu 8 Threads, um Erreichbarkeit, Ping/Latenz und echte Decodier-Qualität (`FHD`, `HD`, `UHD`) über `probe_stream` innerhalb von Sekunden zu ermitteln.
  - Blockiert nicht auf rechenintensiven FFmpeg-Einzelbild-Decodierungen, wodurch die Kanalliste reaktionsschnell bleibt.
- **Phase 2: Automatische Thumbnail-Generierung**:
  - Startet unmittelbar nach Phase 1 für alle verifizierten Online-Sender der Gruppe, die noch kein Bild im Festplatten-Cache besitzen.
  - Begrenzt auf einen schonenden 2-Worker-Pool mit 4,5s FFmpeg-Timeout und kooperativem Stopp-Signal (`_val_stop_ev`), um serverseitige Verbindungsabbrüche (HTTP 459 / 429) zu vermeiden.
  - Live-Update via `QAbstractItemDelegate`: Eintreffende Standbilder werden sofort in die Senderkarte gerendert und permanent unter `.cache/thumbs/{profile}:{ch_id}.jpg` abgelegt.
- **Progress-Bar Architektur**:
  - Eigenständiges Widget `QProgressBar#ValidationProgressBar` mit fester Höhe von 18px, zentrierter Schrift und Farbverlauf. Verhindert jedes vertikale Clipping von Statusmeldungen.

---

## 7. IPTV Edge Diagnostik & Geo-IP Handling
- **Status-Code Mapping (`diagnose_iptv_status`)**:
  - Klassifiziert Middleware- und Edge-Antworten in verständliche Statusmeldungen:
    - `HTTP 456`: Geo-Lock / ISP-Datacenter-ASN Filter oder Multi-Connection Limit.
    - `HTTP 407`: Proxy erforderlich (Provider verlangt IP im Heimatland).
    - `HTTP 459`: Stream-Leitung belegt (Concurrent Limit erreicht).
    - `HTTP 511`: Cloudflare WAF Challenge / Hardware-Auth mit `sn2` nötig.
    - `HTTP 429`: Server-Rate-Limit (5s Abklingzeit).
- **Session- & Filter-Regeln**:
  - Striktes Übergehen von Test-Dummy-Accounts mit `Expire: 0000-00-00 00:00:00` (inaktiv seit 2022).
  - Volle Unterstützung von HTTP- und SOCKS5-Proxies entlang der gesamten Kette (`StbClient`, `probe_stream`, `StreamBufferProxy`, `VLCPlayerController`).
