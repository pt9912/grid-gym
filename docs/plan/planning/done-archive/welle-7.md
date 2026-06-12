# Welle 7 — M2-Closure

**Status:** Done — Welle 7 abgeschlossen am 2026-05-20 mit
`57a50fa` (C0, Slice-Doc) + `9d6bcbf` (C1, `git mv` M2-devices.md
+ welle-6c.md → done/) + diesem C2-Doc-Sync (M2-Closure-
Inhalte). Schliesst M2 vollstaendig ab; aktiviert M3 als
naechsten Slice. Kanonische Slice-Spezifikation:
[`done/M2-devices.md §3 Welle 7`](M2-devices.md) —
dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht Ersatz.

**Spec-Reife:** Inhaltlich final. Reines Doc-Arbeitspaket
(kein Code-Pfad-Wechsel). Verifikationspfad in §6 als
erfuellt markiert; `git log --follow done/M2-devices.md`
zeigt komplette Historie ueber den Rename-Punkt hinweg
(Memory-Regel `feedback_git_mv` erfuellt).

## 1. Context

Welle 6c (`8a3aa2f..7a3c171`, fuenf Commits) hat den M2-Code-Pfad
final geliefert: alle fuenf MVP-Geraete + Netzbilanzmodell +
Scenario-Loader + TickLoop-Event-Wiring + MVP-Demo-E2E +
Determinismus-/Permutations-Tests. ADR-Status-Verifikation am
2026-05-20: alle 9 M2-ADRs (0013..0021) sind `Accepted`.

Welle 7 leistet die Closure-Dokumentation:

- M2-Slice-Plan + welle-6c-Slice-Doc wandern nach `done/`
  (per `git mv` + separater Content-Commit; siehe Memory-
  Konvention `feedback_git_mv`).
- Ein `done/M2-devices-results.md` fasst Wellen-Tabelle,
  Abnahme-Belege, Pro-Welle-Review-Tabelle, S-1..S-6-
  Verification und Welle-7-Erbschaft zusammen (Pattern
  analog `done/M1-tick-loop-results.md`).
- SOLLTE-Out-of-Scope-Items werden als 9 neue Open-Trigger
  in `open/` angelegt.
- `roadmap.md` flippt M2 → `Done` und schaltet M3 als
  „Naechster aktiver Slice".

## 2. Scope

**In Scope:**

1. `git mv` zwei Dateien nach `done/`: `M2-devices.md`,
   `welle-6c.md`.
2. Closure-Notizen in beiden `done/`-Dateien (`Status: Done`).
3. Forwarder-Stub `in-progress/M2-devices.md` (per ADR 0006 §3
   fuer Accepted-ADRs, die auf den `in-progress/`-Pfad zeigen —
   diverse ADRs `Bezug:`-Linien referenzieren
   `in-progress/M2-devices.md`).
4. **NEU** `done/M2-devices-results.md` mit
   - Wellen-Tabelle 0a..7 (Datum, Lieferung, Commits);
   - Abnahme-Belegen (Unit-Test-Count, Integration-Test-Count,
     Coverage, `make fullbuild` ohne Override);
   - Pro-Welle-Review-Tabelle (Welle-N-Review-Folge-Commit);
   - S-1..S-6-Verification aus dem M2-Welle-7-End-to-End-Sweep;
   - Welle-7-Erbschaft fuer M3+/M6+ (SOLLTE-Trigger-Nummern,
     Snapshot-Migration-Pfad, Performance-Benchmarks).
5. 9 Open-Trigger in `open/` fuer SOLLTE-Items
   (`016-024`-Nummerierung):
   - `016-sollte-ev-charger-device.md` (`GG-DEV-015`)
   - `017-sollte-transformer-device.md` (`GG-DEV-016`)
   - `018-sollte-wind-device.md` (`GG-DEV-017`)
   - `019-sollte-diesel-device.md` (`GG-DEV-018`)
   - `020-sollte-island-grid.md` (`GG-GRID-005`)
   - `021-sollte-transformer-limits.md` (`GG-GRID-006`)
   - `022-sollte-reactive-power.md` (`GG-GRID-007`)
   - `023-sollte-battery-temperature.md` (`GG-BESS-006`)
   - `024-sollte-battery-cell-voltage.md` (`GG-BESS-007`)
6. `roadmap.md`: §3 M2 → `Done` mit Closure-Hash, alle DoD-
   Checkboxen abgehakt, M3-Block auf „Naechster aktiver Slice"
   gehoben.
7. `in-progress/README.md`: M2 + welle-6c-Zeilen auf Done-
   Pointer; `welle-7.md`-Zeile ergaenzt; nach Welle-7-Closure
   nochmal `welle-7.md` als Pointer-Eintrag entfernen.
8. `welle-7.md` Status-Header → `Done` mit C2-Commit-Hash.

**Anti-Scope:**

- Kein ADR-Status-Bump (alle 9 M2-ADRs sind bereits
  `Accepted`).
- Keine M3-inhaltlichen-Entscheidungen — M3-Slice-Plan kommt
  mit M3-Welle-0-Start; Welle 7 schaltet M3 nur als „naechsten
  aktiven Slice" frei.
- Keine Code-Aenderungen.
- Keine `CRITICAL_COV_TARGETS`-Anpassungen (Default-Liste
  ist M2-konsistent seit Welle 5b).

## 3. Architektur-Entscheidungen

Welle 7 bringt **keine neue ADR**. ADR-Status-Verifikation
ergibt fuer alle 9 M2-ADRs (0013..0021) `Accepted` zum
2026-05-20 (siehe `docs/plan/adr/README.md`).

ADR-Immutability nach ADR 0006 §3 erzwingt einen Forwarder-Stub
unter `in-progress/M2-devices.md`, weil diverse Accepted-ADRs
(0013/0014/0015/0016/0017/0018/0019/0020/0021) den `Bezug:`-Pfad
auf `in-progress/M2-devices.md` festschreiben — analog
`in-progress/M1-tick-loop-spine.md` aus M1-Welle-7.

## 4. Liefer-Reihenfolge (3 Commits)

### C0 — `docs(plan)`: welle-7 Slice-Doc

Dieses Dokument als Welle-Start-Marker. Status: `In Progress`.
Kein Code, keine Datei-Renames.

### C1 — `chore(welle-7)`: `git mv` M2-devices.md + welle-6c.md → done/

Pure Rename-Commit ohne Content-Edits (Memory-Konvention
`feedback_git_mv`: bei Move + Rewrite zwei Commits, sonst geht
Rename-Historie verloren). Diff zeigt 100% Similarity je
Rename. Keine Edits an anderen Dateien.

### C2 — `docs(plan)`: M2-Welle-7-Closure

- **Closure-Notiz** oben in `done/M2-devices.md`: Status-Block
  auf „Done — M2 abgeschlossen am 2026-05-20 mit Welle-7-
  Closure-Commit `8667474`" gezogen; Welle-Tabellen-Zeilen
  fuer 6c/7 ergaenzt.
- **Closure-Notiz** in `done/welle-6c.md`: Status bestaetigt
  M2-Closure-Stand (Hinweis auf `done/M2-devices-results.md`).
- **Forwarder-Stub** `in-progress/M2-devices.md` (analog
  `in-progress/M1-tick-loop-spine.md`) — kurze Datei mit
  Verweis auf `done/`.
- **NEU** `done/M2-devices-results.md` mit
  Welle-Tabelle (0a..7), Abnahme-Belegen, Pro-Welle-Review-
  Tabelle, S-1..S-6-Verification, Welle-7-Erbschaft.
- **9 Open-Trigger**: `open/016..024-*.md` mit
  einheitlichem Header (`Status: Open — Trigger-Watch`,
  `Datum`, `Quelle`, „Trigger", „Erwartete Lieferung",
  „Out-of-scope").
- **`roadmap.md`**: §3 M2 von `In Progress` auf `Done`
  ziehen; M3-Block auf `Naechster aktiver Slice` mit
  Vorbelegung-Hinweis.
- **`in-progress/README.md`**: M2-/welle-6c-Zeilen entfernen
  oder als Done-Pointer markieren; `welle-7.md`-Zeile
  ergaenzen (wird nach Closure wieder entfernt mit naechstem
  Slice-Eroeffnungs-Commit).
- **`welle-7.md`**: Status-Header von `In Progress` → `Done`
  mit C2-Commit-Hash; Hash-Platzhalter im Body ersetzt.

## 5. Critical Files

| Pfad                                                       | Commit | Aktion |
| ---------------------------------------------------------- | ------ | ------ |
| `docs/plan/planning/in-progress/welle-7.md`                | C0     | NEU    |
| `docs/plan/planning/in-progress/M2-devices.md` → `done/M2-devices.md` | C1 | git mv |
| `docs/plan/planning/in-progress/welle-6c.md` → `done/welle-6c.md` | C1 | git mv |
| `docs/plan/planning/done/M2-devices.md`                    | C2     | EDIT (Closure-Notiz Header)  |
| `docs/plan/planning/done/welle-6c.md`                      | C2     | EDIT (Closure-Notiz Header)  |
| `docs/plan/planning/in-progress/M2-devices.md`             | C2     | NEU (Forwarder-Stub)         |
| `docs/plan/planning/done/M2-devices-results.md`            | C2     | NEU                          |
| `docs/plan/planning/open/016-sollte-ev-charger-device.md`  | C2     | NEU |
| `docs/plan/planning/open/017-sollte-transformer-device.md` | C2     | NEU |
| `docs/plan/planning/open/018-sollte-wind-device.md`        | C2     | NEU |
| `docs/plan/planning/open/019-sollte-diesel-device.md`      | C2     | NEU |
| `docs/plan/planning/open/020-sollte-island-grid.md`        | C2     | NEU |
| `docs/plan/planning/open/021-sollte-transformer-limits.md` | C2     | NEU |
| `docs/plan/planning/open/022-sollte-reactive-power.md`     | C2     | NEU |
| `docs/plan/planning/open/023-sollte-battery-temperature.md`| C2     | NEU |
| `docs/plan/planning/open/024-sollte-battery-cell-voltage.md`| C2    | NEU |
| `docs/plan/planning/in-progress/roadmap.md`                | C2     | EDIT (M2 → Done, M3 next)    |
| `docs/plan/planning/in-progress/README.md`                 | C2     | EDIT (M2/welle-6c-Pointers)  |
| `docs/plan/planning/in-progress/welle-7.md`                | C2     | EDIT (Status → Done)         |

## 6. Verifikationspfad

1. **Rename-Historie**: `git log --follow done/M2-devices.md`
   zeigt die Historie vor und nach dem `git mv` (Memory-Regel
   `feedback_git_mv` erfuellt).
2. **`done/`-Bestand**: enthaelt `M2-devices.md`,
   `welle-6c.md`, `M2-devices-results.md`.
3. **`open/`-Bestand**: 9 neue Trigger-Dateien (`016..024`)
   mit dem etablierten Header-Format
   (Status/Datum/Quelle/Trigger/Erwartete Lieferung/Out-of-
   scope).
4. **ADR-Verifikation**: alle 9 M2-ADRs (0013..0021) sind
   `Accepted` (read-only Cross-Check via
   `grep '^\*\*Status' docs/plan/adr/00{13..21}-*.md`).
5. **`make fullbuild`-Sanity**: gruen ohne Override (Doc-
   Edits sollten den Code-Pfad nicht treffen, aber wir
   pruefen).
6. **Git-Pattern**: drei neue Welle-7-Commits in der
   Reihenfolge
   `docs(plan): welle-7 Slice-Doc (C0)` →
   `chore(welle-7): git mv ... → done/ (C1)` →
   `docs(plan): M2-Welle-7-Closure (C2)`.
   `git log --oneline -3` zeigt diese drei Hashes als
   juengste Commits.

## 7. Risiken

- **Memory-Regel `feedback_git_mv`** muss eingehalten werden:
  `git mv` (C1) ohne Content-Edit, Closure-Notizen erst in
  C2 — sonst geht Rename-Historie verloren.
- **Forwarder-Stub-Pfad**: ein Editor-Glitsch koennte den
  Stub durch den Original-Inhalt ersetzen. Verifikation per
  `wc -l in-progress/M2-devices.md` (sollte < 30 Zeilen
  sein, nicht > 1400 wie das Original).
- **ADR-Bezug-Pfade**: Welle 7 darf nicht versehentlich auf
  `done/`-Pfade umlinken — Accepted-ADRs sind nach ADR 0006
  §3 immutable, und der Forwarder-Stub erfuellt die
  Pfad-Stabilitaet.

## 8. Wandert nach

- `done/welle-7.md` mit eigener Closure-Notiz, sobald das
  naechste Welle-Modul (M3-Welle-0-Start) den `in-progress/`-
  Trakt aktiviert.
