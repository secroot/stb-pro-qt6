# Media Engine, Thumbnail Extraction & Streaming Performance Patterns

Diese Richtlinien definieren die verbindlichen Architektur-Muster für Stream-Probing, Vorschaubild-Generierung und 120-FPS UI-Rendering im IPTV- und Streaming-Kontext.

---

## 1. High-Speed In-Memory Thumbnail Extraction (FFmpeg Pipe Pattern)
- **Keine redundanten HTTP-Stream Downloads**: Niemals FFmpeg direkt auf Remote-HTTP-Live-Streams ansetzen, um ein einzelnes Vorschaubild zu generieren. Auf instabilen oder überlasteten IPTV-Servern führt dies mit Standard-Buffering (`probesize=1.5M`, `analyzeduration=1.5M`) zu Latenzen von 5,5s–7,5s und Timeouts.
- **Single-Pass In-Memory TS Piping**: Den bereits in Phase 1 (Stream-Health-Probe) heruntergeladenen MPEG-TS Chunk (512 KB – 1 MB) direkt im RAM halten und via `stdin` an FFmpeg übergeben (`pipe:0`):
  ```python
  cmd = [
      ffmpeg_bin, "-y", "-loglevel", "quiet",
      "-f", "mpegts", "-i", "pipe:0",
      "-vframes", "1", "-q:v", "3",
      "-vf", f"scale={width}:-1", "-f", "image2pipe", "pipe:1"
  ]
  ```
  - **Laufzeit**: Reduziert die Extraktionszeit von ~6 Sekunden auf **unter 0,12 Sekunden**.
  - **Durchsatz**: Ermöglicht parallele Vorschaubild-Generierung für 8–16 Streams gleichzeitig ohne Bandbreiten-Overhead.

---

## 2. Artefakt- & Black-Frame-Filterung (`is_blank_or_black_jpeg`)
- **Dummy- & Kanal-Separator-Schutz**: IPTV-Kataloge enthalten oft Dummy-Kanäle (z. B. `### SKY SPORT ###`) oder Streams, die mit statischen Schwarzbildern initialisieren. Diese erzeugen korrupte oder nutzlose 581-Byte JPEGs (`#000000`).
- **Validierungs-Filter**: Jedes extrahierte Frame vor dem Schreiben in den Disk-Cache mit `is_blank_or_black_jpeg(data)` prüfen:
  - Header-Prüfung (`\xff\xd8\xff`).
  - Mindestgröße (> 1.200 Bytes für echte Bildinhalte).
  - Statistische Helligkeits- & Standardabweichungs-Prüfung über Sub-Sampling (`Pillow` / ImageStat).
- Nur valide, informative Thumbnails in `.cache/thumbs/` persistieren.

---

## 3. Viewport-Debouncing & Scroll-Laden
- **Kein pauschales Hintergrund-Spamming**: Tausende Thumbnails einer 5.000-Sender-Liste nicht blind in Endlosschleife laden.
- **Entprellter Viewport-Timer**: Einen QTimer (300–400 ms) an das Scroll-Event der Liste (`verticalScrollBar().valueChanged`) binden.
- Nur Sender im aktuell sichtbaren Viewport (`listView.rect()`) on-demand im Hintergrund anfordern, die noch keinen Cache-Treffer besitzen.

---

## 4. Live-Wiedergabe Snapshots (LibVLC Surface Capture)
- **Instant Snapshot nach Stream-Start**: Nach dem Starten eines Senders im Player 1,8 Sekunden warten (bis der Video-Decoder stabil läuft und Keyframes gerendert sind).
- Snapshot direkt aus dem HW-Surface (`vlc_ctrl.snapshot()`) ziehen und im Cache ablegen.
- Aktualisiert die Senderkarte unmittelbar mit einem gestochen scharfen Live-Bild und `LIVE`-Badge.

---

## 5. 120-FPS Delegate Rendering & Zero-I/O Paint Cycle
- **Pre-Scaling bei Ingest**: Bilder beim Laden im Delegate einmalig auf die exakte Kartengröße vor-skalieren (z. B. `56x32` mit `Qt.TransformationMode.SmoothTransformation`).
- **Niemals Disk-I/O oder Bildskalierung in `paint()`**:
  - Im Paint-Event des QStyledItemDelegate dürfen ausschließlich vorberechnete `QPixmap` / `QImage` Objekte gezeichnet werden.
  - Fehlende Bilder (Cache-Misses) in einem Set `_missing_keys` vormerken, um wiederholte Zugriffsversuche auf das Dateisystem pro Frame vollständig zu eliminieren.
