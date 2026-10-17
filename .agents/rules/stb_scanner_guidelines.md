---
description: Richtlinien für High-Speed Stalker/Ministra MAC-Scanning, Telemetrie, UI-Design und Hit-Export
trigger: always_on
---

# STB Scanner & Stalker Probing Richtlinien

## 1. High-Performance Stalker API Probing
- **Keine Full-Catalog-Downloads**: Für Kanalzählungen im Scanner niemals `get_all_channels` verwenden. Ausschließlich paginierte Endpoints wie `get_ordered_list(genre='*', sortby='number', p='1')` abfragen und das `total_items`-Feld auslesen (~2 KB Payload, ~100 ms Abfragezeit).
- **Session Cookie Isolation**: Bei persistenten Worker-Sessions vor jedem MAC-Handshake zwingend `session.cookies.clear()` ausführen, um Session-Leaks (z. B. `PHPSESSID`) zwischen verschiedenen Accounts zu verhindern.
- **Single-Probe Endpoint Cache**: Vor dem Start von Multi-Thread-Scans den korrekten Stalker-Endpoint (`load_url` / `portal.php`) einmalig ermitteln und thread-übergreifend cachen.

## 2. Resilienz & Auto-Requeue
- **Transiente Kanalfehler nicht schlucken**: Accounts mit aktivem Ablaufdatum in der Zukunft, deren Kanalabfrage ins Timeout oder auf Serverfehler (503/502/429) läuft, dürfen niemals vorzeitig mit 0 Kanälen als abgeschlossen markiert werden.
- **Auto-Requeue**: Solche Accounts automatisch mit Retry-Zähler hinten anstellen (`[⏳ Requeue]`), bis ein definitives Ergebnis vorliegt.

## 3. UI-Standards für Scanner-Tabellen
- **Filter-Pills Beschriftung**:
  - `ALL`: Alle gescannten Accounts (ohne Zähler)
  - `HOT (N)`: Nur Treffer mit >0 Kanälen (einziger Reiter mit Live-Zähler)
  - `OK`: Gültige Accounts ohne gebuchte Kanäle (ohne Zähler)
  - `ERR`: Ungültige / geblockte Accounts (ohne Zähler)
- **Status-Klarheit**: Echte 0-Kanal-Testaccounts mit `0` anzeigen, ungültige mit `—`. Nicht autorisierte MACs einheitlich als `Ungültig / Nicht autorisiert` formatieren.

## 4. Hit-Export Standards
- **Nur HOT-Treffer**: Beim Export ausschließlich Accounts mit `tag == 'hot'` und `channels > 0` exportieren.
- **Dateinamen-Konvention**: `<hostname>_<hits>hits_<YYYY-MM-DD>.txt` (z. B. `iptvgarden.streamtv.to_3hits_2026-10-17.txt`).
- **Block-Format**:
  ```text
  ---------------------------------------------
  Portal: <url>
  Status: <status>
  Mac: <mac>
  Scandate: <YYYY-MM-DD HH:MM:SS>
  Expire: <date>
  Channels: <count>
  ---------------------------------------------
  ```
