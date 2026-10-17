# Code-Index Konsultations- & Synchronisations-Richtlinie (stb_pro_qt6)

Diese Richtlinie ist für alle Agents verbindlich, die im Repository `stb_pro_qt6` Code analysieren, debuggen, erweitern oder refaktorisieren.

---

## 1. Obligatorische Index-Konsultation (Token- & Quota-Schutz)
- **Erst `CODE_INDEX.md` prüfen**: Vor jeder großflächigen Textsuche, vor rekursivem Greppen oder vor dem blinden Einlesen ganzer Verzeichnisse MUSS zuerst die Datei [`stb_pro_qt6/CODE_INDEX.md`](file:///c:/Users/basti/Desktop/iptv/stb_pro_qt6/CODE_INDEX.md) konsultiert werden.
- **Zielgerichteter Zugriff**: Der Index enthält ein alphabetisches Master-Symbolverzeichnis aller Klassen, Methoden, Funktionen, Signals und Konstanten sowie modulare Sektionen (Clients, Core, Player, UI, Tests) inklusive exakter Start- und Endzeilen sowie Funktionssignaturen.
- **Kontext-Effizienz**: Durch den direkten Sprung auf exakte Zeilenbereiche (`file:///...#L120-L180`) wird das Token-Budget geschont und Kontext-Verschwendung vermieden.

---

## 2. Automatische Synchronisation nach Code-Änderungen
- **Pflicht nach Modifikationen**: Sobald Klassen, Methoden, Funktionen, Views, Dialoge, Models, Tests oder Dateien hinzugefügt, umbenannt, verschoben oder gelöscht werden, MUSS der Code-Index synchronisiert werden.
- **Befehl zur Aktualisierung**:
  ```powershell
  # Im Verzeichnis stb_pro_qt6 ausführen:
  .venv\Scripts\python.exe tools/generate_code_index.py
  # bzw.
  python tools/generate_code_index.py
  ```
- **Keine manuellen Zeilenanpassungen in `CODE_INDEX.md`**: Der Index wird zu 100% deterministisch via Python AST (`tools/generate_code_index.py`) erzeugt. Manuelle Edits in `CODE_INDEX.md` sind untersagt.

---

## 3. Struktur- & Ablagestandards
- **Keine Ad-hoc-Skripte im Root**: Manuelle Tests und temporäre Debug-Skripte gehören nach `tests/manual/`. Tools zur Code-Generierung, Wartung und Profiling gehören nach `tools/`.
- **Eindeutige Klassendokumentation**: Jede neue Klasse und jede öffentliche Methode sollte einen einzeiligen Docstring besitzen, damit der AST-Generator die Kurzbeschreibung im Index automatisch füllt.
