# GitHub Issue-Driven Workflow & Repository Synchronisations-Richtlinie

Diese Richtlinie ist für alle Agents verbindlich, die im Repository `stb_pro_qt6` arbeiten. Sie regelt das automatisierte Issue-Tracking via GitHub CLI (`gh`), saubere Commit-Referenzierung und kontinuierliche Synchronisation mit dem Remote-Repository.

---

## 1. Issue-Driven Development (IDD)
- **Erfassung von Aufgaben & Bugs**: Jede neue Anforderung, jeder Bug-Report, jedes geplante Refactoring und jedes Feature muss transparent als GitHub Issue erfasst oder einem bestehenden Issue zugeordnet werden.
  ```powershell
  # Prüfen bestehender Issues:
  gh issue list
  
  # Neues Issue anlegen:
  gh issue create --title "feat: <Titel>" --body "<Beschreibung & Akzeptanzkriterien>" --label "enhancement"
  # bzw.
  gh issue create --title "fix: <Titel>" --body "<Fehlerbeschreibung & Reproduktion>" --label "bug"
  ```
- **Lifecycle & Fortschritt**:
  - Bei mehrstufigen Aufgaben können Zwischenstände auf dem Issue dokumentiert werden:
    ```powershell
    gh issue comment <ID> --body "Zwischenstand: Phase 1 abgeschlossen."
    ```
  - Nach erfolgreicher Verifikation und Tests wird das Issue automatisch über die Commit-Message (`closes #<ID>` / `fixes #<ID>`) oder explizit geschlossen:
    ```powershell
    gh issue close <ID> --comment "Erfolgreich implementiert, verifiziert und gepusht."
    ```

---

## 2. Kontinuierliche Repository-Synchronisation (Auto-Push)
- **Keine ungesicherten Stände**: Nach Abschluss einer logischen Aufgabe, eines Bugfixes oder eines Checkpoints darf die Session niemals mit uncommitted oder unpushed Änderungen beendet werden.
- **Workflow-Ablauf vor jedem Push**:
  1. **Tests ausführen**:
     ```powershell
     .venv\Scripts\python.exe -m unittest tests/test_ui_and_engine.py
     ```
  2. **Code-Index synchronisieren**:
     ```powershell
     .venv\Scripts\python.exe tools/generate_code_index.py --check
     # Falls abweichend:
     .venv\Scripts\python.exe tools/generate_code_index.py
     ```
  3. **Staging & Commit**:
     ```powershell
     git add .
     git commit -m "<type>: <Beschreibung> (fixes #<ID>)"
     ```
  4. **Push zum Remote**:
     ```powershell
     git push origin main
     ```

---

## 3. Standardisierte Commit-Präfixe (Conventional Commits)
- `feat:` Neues Feature / Erweiterung
- `fix:` Bugfix / Fehlerbehebung
- `perf:` Performance-Optimierung (z. B. Latenz, GPU-Rendering, Memory-Pipes)
- `refactor:` Code-Umbau ohne Verhaltensänderung
- `docs:` Dokumentation, Checkpoints, Regeln
- `test:` Unittests, Integrationstests
- `chore:` Wartungsaufgaben, CI/CD, Paketkonfiguration

---

## 4. Private Repository Datensicherheit & Session-Restore
- Da das Repository als `Private` geführt wird, dürfen `config.json`, `mac_database.json`, `ALL MACS.txt`, `stalker_portals.txt` und `mac_scans/` mitgeführt werden, um nahtloses Session-Resuming auf anderen Arbeitsstationen zu ermöglichen.
- Lokale temporäre Cache-Dateien (`recordings/`, `thumbs/`, `logos/`, `.thumb_cache/`, `*.log`, `.venv/`) bleiben strikt gitignored.
