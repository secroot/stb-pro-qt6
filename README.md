# ⚡ STB-Emulator Pro by InfoHazard & H7CFoX

<p align="center">
  <img src="assets/app_icon.png" alt="STB-Emulator Pro Logo" width="128" height="128">
</p>

<p align="center">
  <b>High-Performance Qt6 IPTV Cyber-Cinema, Protocol-Inspector & Multi-Thread MAC Pentesting Suite</b><br>
  Entwickelt für Red-Team Security-Analysen, Stalker/Ministra Middleware-Probing und kompromissloses 120-FPS 4K UHD Streaming.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/GUI-Qt6%20%7C%20PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="Qt6 PySide6">
  <img src="https://img.shields.io/badge/Engine-LibVLC%20x64-FF8800?style=for-the-badge&logo=vlcmediaplayer&logoColor=white" alt="LibVLC">
  <img src="https://img.shields.io/badge/Proxy-Zero--Drop%20Ringbuffer-00D2FF?style=for-the-badge" alt="Zero-Drop Ringbuffer">
  <img src="https://img.shields.io/badge/Scanner-Uncapped%20250%20Threads-FF0055?style=for-the-badge" alt="Uncapped 250 Threads">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-00FF66?style=for-the-badge" alt="Production Ready">
</p>

---

## 🌟 Schnellübersicht

Dank reaktiver **EventBus-Architektur** und virtueller GPU-Listen rendert die Anwendung selbst Kataloge mit über **100.000 Sendern** bei stabilen **120 FPS** mit Latenzen unter 1 ms und 0 % CPU-Last im Leerlauf.

| 🎯 Multi-Thread Pentest Scanner | 🌲 Host-Gruppierter HOT-Baum | 🏷️ Intelligente Bouquet-Tags |
| :--- | :--- | :--- |
| Bis zu **250 parallele Worker**, adaptive Delays, Session-Isolation & automatische Rekursion. | Treffer übersichtlich nach Servern gruppiert mit **Live-Ablauf-Countdown** in Tagen. | Automatische Unterscheidung von **`[DE]`**, **`[18+ TV]`** und **`[18+ VOD]`** pro Account. |

| 🎬 120 FPS 4K Cyber-Cinema | 🔍 Live Protokoll-Inspector | 📂 Integrierte MAC-Datenbank |
| :--- | :--- | :--- |
| LibVLC mit D3D11/VAAPI, **Zero-Drop Ringbuffer** und lokalem Flow-Control HTTP-Proxy. | Echtzeit-Erfassung aller API-Requests, Fehler-Sampling und **1-Click cURL Generator**. | Persistente SQLite/JSON-Datenbank mit Duplikatschutz, Tags und **1-Click Connect**. |

---

## 🚀 Die Kernfeatures im Detail

### 1. 🎯 High-Throughput MAC Scanner & Pentest Engine

Die integrierte Scanner-Engine wurde speziell für ressourcenschonendes und maximal schnelles Stalker/Ministra-Probing entwickelt:

* **Uncapped Multi-Threading**: Frei skalierbar von **1 bis 250 Threads** mit Micro-Delays (`0 ms` bis `2500 ms`) für lokale Audits oder WAF-geschützte Edge-Server.
* **🌲 Einklappbarer HOT-Treffer-Baum (`QTreeWidget`)**:
  * **Host-Header**: Gruppiert Treffer übersichtlich unter `[hostname] | [X Hot Hits]`. Ein Klick klappt den gesamten Server auf oder zu.
  * **Account-Zeilen**: Zeigt MAC-Adresse, Ablaufdatum mit **Live-Countdown** (`noch X Tage`, `heute`, `abgelaufen vor X Tagen`, `Unbegrenzt`), Senderanzahl und Tags.
  * **Direktverbindung**: Doppelklick auf einen Account verbindet sofort und startet die Wiedergabe.
* **🏷️ Präzise Bouquet- & Content-Erkennung**:
  * **`[DE]`**: Erkennt deutsche Regionalbouquets (`DE:`, `DE -`, `DE ⭐`, `DE|`, `[DE]`, `AT`, `CH`) mit strikter Symbol-Prüfung – verhindert False Positives auf spanische/französische Wörter wie *de peliculas* oder *de cinema*.
  * **`[18+ TV]`**: Erkennt Live-TV-Sender mit Altersbeschränkung.
  * **`[18+ VOD]`**: Erkennt Erwachsenen-Kategorien im Video-on-Demand (Filme / Serien).
  * **Strikte Account-Isolation**: Genres und VOD-Kategorien werden für jeden validen Treffer isoliert auf dessen aktiver Session geprüft – kein Cache-Leak zwischen verschiedenen Accounts auf demselben Portal.
* **Resilientes Auto-Requeue (`[⏳ Requeue]`)**:
  * Accounts mit aktivem Ablaufdatum, deren Kanalabfrage unter hoher Last in einen transienten Timeout, HTTP 503 oder 429 läuft, werden **nicht** vorzeitig mit 0 Kanälen verworfen.
  * Sie werden automatisch mit Retry-Zähler hinten angestellt, bis ein definitives Ergebnis vorliegt.
* **Session Cookie Isolation**: Zwingendes `session.cookies.clear()` vor jedem Handshake verhindert Token- und Session-Leaks (`PHPSESSID`) zwischen Accounts.
* **Geglättete Telemetrie**: Live-Anzeige von **Hit-Rate in %** (`🎯 Hit-Rate: X.X%`), exponentiell geglätteter **CPS-Rate** (Checks per Second) und realistischer Restzeit (**ETA**).
* **Standardisierter Hit-Export**: Exportiert ausschließlich echte Treffer (`channels > 0`) im sauberen Block-Format (`<hostname>_<hits>hits_<YYYY-MM-DD>.txt`).

---

### 2. 🎬 Hardware-Accelerated Cyber-Cinema (Player)

* **LibVLC 64-Bit Integration**: Volle Hardwarebeschleunigung via **Direct3D11** (Windows) und **VAAPI** für butterweiches 4K UHD Streaming bei 120 FPS.
* **Zero-Drop Ringbuffer HTTP-Proxy (`127.0.0.1`)**:
  * Lokaler Loopback-Proxy verhindert Verbindungsabbrüche durch Player-Jitter.
  * **Upstream Flow-Control Pacing**: Liest Upstream-Daten exakt bis zum konfigurierten Pufferziel (z. B. 15 s) und stoppt dann – schützt zuverlässig vor Provider-Sperren durch unkontrolliertes Vorsaugen.
  * **PCR Bitrate Smoothing**: Ermittelt die exakte Bitrate direkt aus den MPEG-TS Program Clock References.
* **Vollbild & Kinomodus**:
  * **Vollbild (`F11`)**: Mit transparentem OSD-HUD (aktuelle Sendung, EPG-Restzeit, Bitrate, Codec-Pills) und einblendbarem **Quick-Channel-Drawer (`[C]`)**.
  * **Kinomodus (`[T]`)**: Blendet Bedienelemente komplett aus für ungestörten Filmgenuss.
  * **Picture-in-Picture (`[P]`)**: Rahmenloser Always-on-Top Mini-Player am Bildschirmrand.
* **Live-Recording**: Sofortaufnahme laufender Live-Sendungen auf Knopfdruck (`[R]`).

---

### 3. 📺 Live TV & GPU-Virtualisierte Senderliste

* **120 FPS GPU-Virtualisierung**: Nutzung von `QAbstractListModel` + `QSortFilterProxyModel` + `ChannelCardDelegate`. Nur sichtbare Zeilen werden gerendert – absolut kein Lag selbst bei Katalogen mit über **100.000 Kanälen**.
* **Zwei-Phasen Kategorie-Validator**:
  * **Phase 1 (Health-Check)**: Prüft alle Sender einer Gruppe parallel mit bis zu 8 Threads auf Erreichbarkeit, Ping und echte Auflösung (`UHD`, `FHD`, `HD`).
  * **Phase 2 (Auto-Thumbnail Grabber)**: Extrahiert vollautomatisch Vorschaubilder aus dem Live-Stream (0,12s TS-Probe) und speichert sie im lokalen Disk-Cache (`.cache/thumbs/`).
* **Smart Filter-Pills**: Blitzschneller Wechsel zwischen `Alle`, `⭐ Favoriten`, `🕘 Zuletzt gespielt` und `HD / 4K`.
* **M3U8-Export**: Exportiert Senderlisten und Favoriten mit einem Klick als standardkonforme `.m3u8`-Playlist.

---

### 4. 🍿 VOD (Filme) & Serien-Browser

* **Moderne Cinema-Ansicht**: Schnelle Suche und Sortierung nach IMDb-Bewertung, Titel, Genre, Auflösung und Erscheinungsjahr.
* **Serien- & Staffelauswahl**: Strukturierter Episoden-Browser mit Inhaltsangabe und Stream-Details.
* **Hintergrund-Downloader**: Paralleler Download von Filmen und Episoden im Hintergrund mit automatischer Wiederaufnahme bei Netzwerkunterbrechung.

---

### 5. 🔍 Interaktiver HTTP & Protokoll-Inspector

* **Live Traffic-Capture**: Protokolliert jeden API-Aufruf, Handshake, Token-Refresh und Kanalwechsel mit Header-Details und Statuscodes.
* **Fehler-Sampling**: Sporadische Verbindungsabbrüche, Timeouts und WAF-Responses (429/504) werden automatisch erfasst und übersichtlich aufbereitet.
* **1-Click cURL Generator**: Generiert mit einem Klick den exakten cURL-Befehl inklusive aller MAG-Tokens, Cookies und Hardware-Headers für Tests im Terminal oder Postman.
* **14 Hardware-Profile**: Emulation von MAG 250, 254, 322, 420, 520, AuraHD, Formuler Z8 u.v.m. inklusive exakter Seriennummern- und Geräte-Signaturen (`dev1`, `dev2`, `sig`).

---

## 🛠 Installation & Schnellstart

### Voraussetzungen
* **Windows 10 / 11 (64-Bit)**
* **Python 3.12+ (64-Bit)**
* **VLC Media Player (64-Bit)** installiert (für `libvlc.dll` unter `C:\Program Files\VideoLAN\VLC`)

### 1. Repository klonen
```powershell
git clone https://github.com/secroot/stb-pro-qt6.git
cd stb-pro-qt6
```

### 2. Virtuelle Umgebung einrichten & installieren
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Starten
Starte die Suite entweder per Doppelklick auf die **`start_qt6.bat`** oder direkt im Terminal:
```powershell
.\.venv\Scripts\python.exe main.py
```

---

## ⌨️ Tastaturkürzel (Hotkeys)

| Taste | Kontext | Funktion |
| :--- | :--- | :--- |
| `F11` / Doppelklick | Video | Vollbildmodus mit transparentem OSD-HUD umschalten |
| `C` | Vollbild | Schnell-Senderliste (Quick-Channel-Drawer) rechts ein-/ausblenden |
| `P` | Global | Picture-in-Picture (PiP) Always-on-Top Player umschalten |
| `T` | Global | Kinomodus (Seitenleiste & Toolbars ausblenden) umschalten |
| `Esc` | Player | Vollbild-, PiP- oder Kinomodus verlassen |
| `Leertaste` | Video | Wiedergabe pausieren / fortsetzen |
| `M` | Video | Ton stummschalten (Mute) |
| `PgUp` / `PgDn` | Live TV | Vorheriger / Nächster Sender (Direct Zapping) |
| `R` | Live TV | Sofortaufnahme starten / stoppen (`REC`) |
| `F2` | Senderliste | Sender als Favorit markieren / entfernen |
| `Ctrl+F` | Global | Schnellsuche in der Senderliste fokussieren |

---

## 📁 Projektstruktur & Architektur-Dokumentation

Eine vollständige Dokumentation der internen Modul-Zusammenhänge und des Symbol-Registers findest du in den separaten Dokumenten:

* 📐 **[ARCHITECTURE.md](file:///c:/Users/basti/Desktop/iptv/stb_pro_qt6/ARCHITECTURE.md)**: Detaillierte Architektur, EventBus-Design, Thread-Modelle & Sequenzdiagramme.
* 📖 **[CODE_INDEX.md](file:///c:/Users/basti/Desktop/iptv/stb_pro_qt6/CODE_INDEX.md)**: Zeilen-exaktes Symbol- und Klassenregister aller Funktionen und Widgets.
* 📌 **[CHECKPOINTS.md](file:///c:/Users/basti/Desktop/iptv/stb_pro_qt6/CHECKPOINTS.md)**: Release-Meilensteine, Audit-Historie und Optimierungs-Logs.

---

## Download: 
```powershell
https://github.com/secroot/stb-pro-qt6/archive/refs/heads/main.zip
```

