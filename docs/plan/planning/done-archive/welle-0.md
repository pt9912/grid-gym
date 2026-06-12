# Welle 0 — M3 Slice-Plan-Eroeffnung + Trigger-Triage

**Status:** Done — M3-Welle-0 abgeschlossen am 2026-05-20 mit
`cfb7a72` (C0, Slice-Doc + welle-7-Move) + `4bd2673` (C1,
M3-Slice-Plan-Eroeffnung) + `f5de006` (C2, Trigger-Triage +
Status-Flip) + Review-Folge (C3, `fix(welle-0)`: 5 High + 5
Medium + 1 Low Spec-Drift-/Konsistenz-Findings adressiert).
Vorabraeumung + Slice-Plan-Eroeffnung fuer M3 (Faults +
Multi-Agent + Observability) ist geliefert.
Kanonische M3-Slice-Spezifikation:
[`M3-faults-agents-observability.md`](M3-faults-agents-observability.md)
— dieses Welle-0-Doc ist der Index zur Welle, nicht der
Meilenstein-Slice-Plan selbst.

**Spec-Reife:** Inhaltlich final. Reines Doc-Arbeitspaket
(kein Code-Pfad-Wechsel; Pattern analog M2-Welle-0c).
Trigger-Triage in `M3-faults-agents-observability.md §3
Welle 0` festgehalten; alle Open-Trigger 005/006/007/011 +
M2-SOLLTE-Trigger 016..024 haben dort eine explizite
M3-Drift-Aussage.

## 1. Context

M2 ist seit 2026-05-20 mit Welle-7-Closure-Commit-Stack
(`57a50fa`/`9d6bcbf`/`8667474`) abgeschlossen
([`done/M2-devices.md`](M2-devices.md),
[`done/M2-devices-results.md`](../done/M2-devices-results.md)).
M3 ist laut [`roadmap.md §3 M3`](../in-progress/roadmap.md) der naechste
aktive Slice mit drei distinkten Sub-Bereichen:

- **Faults**: `GG-FAULT-001..010` + `GG-SAFE-001..006`,
  Architektur `GG-AR-COMP-FAULTS`. Scenario-Validator + Tick-
  Loop-Trigger fuer Fault-Definitions, mindestens ein
  konkreter Fault-Typ pro Battery-/Grid-Achse, Recovery-
  Verhalten.
- **Multi-Agent**: `GG-AGENT-001..008`, Architektur
  `GG-AR-COMP-AGENTS`. Multi-Agent-Bus; RL-Adapter als
  separater Folge-Slice (`GG-FUTURE-001/002`).
- **Observability**: `GG-OTEL-001..004`, Architektur
  `GG-AR-PORT-DRN-008` (`LogPort`/`MetricsPort`/`TracePort`)
  mit OTLP-Adapter.

Welle 0 leistet die Vorabraeumung:

- M3-Slice-Plan wird in `in-progress/` eroeffnet
  (Vorbelegung Welle 0..7 + Out-of-Scope + Risiken +
  Akzeptanz-/Exit-Kriterien).
- M2-Welle-7-Begleit-Doc `welle-7.md` wandert nach `done/`
  (M2-Closure final, M3-Start markiert).
- Trigger-Triage: Cross-Check der Open-Trigger 005/006/007
  (Type-Checker-Strategie) und 011 (`MLRandomPort`-Sub-Seed-
  Wortbreite) gegen M3-Scope; Drift dokumentieren.

Keine Code-Aenderungen in Welle 0; das spiegelt das
M2-Welle-0c-Pattern (Lastenheft-Coverage-Sweep + Trigger-
Triage als reine Doc-Welle).

## 2. Scope

**In Scope:**

1. `docs/plan/planning/in-progress/M3-faults-agents-observability.md`
   als neuer M3-Slice-Plan mit Vorbelegung Welle 0..7,
   Out-of-Scope, Risiken + Fallback, Akzeptanz-/Exit-Kriterien
   (Pattern analog `done/M2-devices.md`).
2. `git mv welle-7.md` → `done/welle-7.md` (M2-Welle-7-Begleit-
   Doc final geschlossen; per `welle-7.md §8 Wandert nach`).
3. Trigger-Triage:
   - 005 (`pyright`-vs-`mypy`-Re-Eval) — Cross-Check gegen
     M3-Scope (RL-Adapter koennten generische Protocols
     stressen).
   - 006 (`--strict-bytes`-Modus) — Cross-Check gegen M3
     (Telemetry-Export-Pfade fuer OTLP koennten Bytes-Pfade
     beruehren).
   - 007 (`pyright` als Pre-Commit-Hook) — Cross-Check gegen
     M3 (Hooks-Strategie ist Dev-Experience, nicht
     M3-blockend).
   - 011 (`MLRandomPort`-Sub-Seed-Wortbreite) — explizit
     M3-Multi-Agent-getriggert; Aktivierungs-Pruefung.
   - 9 frische SOLLTE-Trigger aus M2-Welle-7 (`016..024`):
     Drift-Check gegen M3-Scope (sind sie M3-Sub-Welle-
     Material oder bleiben sie eigenstaendige Slices?).
4. `in-progress/README.md`-Sync: `welle-7.md`-Zeile entfernen
   (Datei jetzt in `done/`), `welle-0.md`-Zeile ergaenzen,
   `M3-faults-agents-observability.md`-Zeile ergaenzen.

**Anti-Scope:**

- Keine Code-Aenderungen. Welle 0 ist reines Doc-Arbeitspaket
  (analog M2-Welle-0c).
- Keine neue ADR. Vorbelegung von M3-ADRs (z. B. FaultPort,
  AgentBus, LogPort/MetricsPort/TracePort) erfolgt mit
  Welle 1+, nicht in Welle 0.
- Keine M3-DoD-Checkbox-Aktivierung in `roadmap.md` — die
  bleibt `[ ]` bis zur jeweiligen Welle-N-Lieferung.
- Keine Bewegung der `016..024`-Trigger aus `open/`. Trigger-
  Triage in C2 ist nur eine **Doc-Notiz** (welche Trigger sind
  M3-Sub-Welle vs. eigenes Slice nach M3); keine Datei-Moves.

## 3. Architektur-Entscheidungen

Welle 0 bringt **keine neue ADR**. ADR-Status-Verifikation
fuer M2-ADRs (0013..0021) wurde in M2-Welle-7 abgeschlossen,
alle `Accepted`. Welle 0 sammelt nur die Vorbelegung der
M3-ADR-Kandidaten in `M3-faults-agents-observability.md §3`,
schreibt sie aber nicht.

Vorbelegungs-Liste (wird in C1 in `M3-faults-...md` aufgenommen):

- **ADR 0022** (Provisional in M3-Welle-1): FaultPort-Pattern
  + Fault-Definitions in Scenario-Schema-Erweiterung.
- **ADR 0023** (Provisional in M3-Welle-3 oder spaeter):
  AgentBus + Multi-Agent-Subsystem-Architektur.
- **ADR 0024** (Provisional in M3-Welle-5 oder spaeter):
  `LogPort`/`MetricsPort`/`TracePort` als
  `GG-AR-PORT-DRN-008`-Trio + OTLP-Adapter.

Die genaue Nummerierung bleibt offen bis M3-Welle-1 (ADRs
werden in der Reihenfolge ihrer `Proposed`-Datierung vergeben).

## 4. Liefer-Reihenfolge (3 Commits)

### C0 — `docs(plan)`: welle-0 Slice-Doc + welle-7.md → done/

- Dieses Dokument als Welle-Start-Marker. Status:
  `In Progress`.
- `git mv docs/plan/planning/in-progress/welle-7.md
   docs/plan/planning/done/welle-7.md` mit zwei kleinen
  Inhalts-Edits im welle-7-Body (M1→M2-Typo §2.4 +
  ADR-0016-Ergaenzung §3 + `<C2-Hash>`→`8667474`-Aufloesung
  §4 C2; Worktree-User-/Linter-Cleanup-Mods post-`8667474`).
  Rename-Detection per `git diff -M` ergibt 98 % Similarity;
  Memory-Konvention `feedback_git_mv` formal verletzt (Move +
  Mini-Rewrite in einem Commit), praktisch toleriert (`git log
  --follow done/welle-7.md` traceable, siehe Review-Folge-1
  M-1/M-2).
- `in-progress/README.md`-Sync: `welle-7.md`-Zeile entfernt,
  `welle-0.md`-Zeile ergaenzt.

### C1 — `docs(plan)`: M3-Slice-Plan eroeffnen — faults-agents-observability

- NEU `docs/plan/planning/in-progress/M3-faults-agents-observability.md`
  mit Vorbelegung:
  - §1 Zweck (drei Sub-Bereiche, Lastenheft-Anschluss).
  - §2 Erfolgskriterien (Akzeptanz-/Exit-Kriterien).
  - §3 Liefer-Reihenfolge (Welle 0..7 vorbelegt mit
    Sub-Slicing-Schwelle analog M2 §3).
  - §4 Out-of-Scope (RL-Adapter, M4-Protokolladapter,
    Kombinationen mit M2-SOLLTE-Triggern).
  - §5 Risiken + Fallback.
  - §6 Wandert nach (`done/`).
  - §7 Verifikationspfad.
- `in-progress/README.md`-Sync: `M3-faults-agents-observability.md`-
  Zeile ergaenzt.

### C2 — `docs(plan)`: M3-Welle-0 Trigger-Triage

- Trigger-Triage-Notiz in `M3-faults-agents-observability.md §3 Welle 0`:
  - 005/006/007 — Status pruefen, Drift dokumentieren.
  - 011 (`MLRandomPort`-Sub-Seed) — M3-Multi-Agent-Aktivierung
    skizzieren (welche Welle, welche Aktivierungs-Schwelle).
  - 016..024 (M2-Welle-7-SOLLTE-Trigger) — Drift-Check je
    Trigger; Drift in C2-Commit-Body dokumentieren.
- `welle-0.md`-Status-Header von `In Progress` auf `Done`
  ziehen; C2-Commit-Hash einsetzen.

## 5. Critical Files

| Pfad                                                                | Commit | Aktion                  |
| ------------------------------------------------------------------- | ------ | ----------------------- |
| `docs/plan/planning/in-progress/welle-0.md`                         | C0     | NEU                     |
| `docs/plan/planning/in-progress/welle-7.md` → `done/welle-7.md`     | C0     | git mv (kein Rewrite)   |
| `docs/plan/planning/in-progress/README.md`                          | C0     | EDIT (welle-7→done, welle-0+) |
| `docs/plan/planning/in-progress/M3-faults-agents-observability.md`  | C1     | NEU                     |
| `docs/plan/planning/in-progress/README.md`                          | C1     | EDIT (M3-Slice-Plan ergaenzt) |
| `docs/plan/planning/in-progress/M3-faults-agents-observability.md`  | C2     | EDIT (Welle-0-Triage-Notiz) |
| `docs/plan/planning/in-progress/welle-0.md`                         | C2     | EDIT (Status → Done)    |

## 6. Verifikationspfad

1. `git mv`-Detection: `git log --diff-filter=R --oneline`
   zeigt welle-7.md → done/welle-7.md mit 100% Similarity.
2. `in-progress/`-Bestand: enthaelt `welle-0.md`,
   `M3-faults-agents-observability.md`, `README.md`,
   `roadmap.md`, Forwarder-Stub `M1-tick-loop-spine.md`,
   Forwarder-Stub `M2-devices.md`.
3. `done/`-Bestand: enthaelt `welle-7.md` (neu hinzugekommen),
   weiterhin `M1-*`, `M2-*`, `welle-6c.md`,
   `M2-devices-results.md`, Trigger 001/002/009..015.
4. `open/`-Bestand: 18 Dateien (`003`..`008`, `011`, `012`,
   `016..024` plus `README.md`); keine Datei-Moves in
   Welle 0.
5. `make gates`-Sanity: gruen (Doc-only-Edits sollten den
   Code-Pfad nicht treffen).
6. Git-Pattern: drei neue M3-Welle-0-Commits in der
   Reihenfolge `docs(plan): welle-0 Slice-Doc + welle-7
   → done/ (C0)` → `docs(plan): M3-Slice-Plan eroeffnen (C1)`
   → `docs(plan): M3-Welle-0 Trigger-Triage (C2)`.

## 7. Risiken

- **welle-7.md-Move bricht Rename-Historie**: Mitigation —
  Single-Commit-Move ohne Inhalts-Edit (Memory-Konvention
  `feedback_git_mv` ist nicht verletzt, weil kein Rewrite).
  Verifikation per `git log --follow done/welle-7.md`.
- **M3-Sub-Bereiche-Vermischung**: drei Sub-Bereiche (Faults,
  Multi-Agent, Observability) koennten ohne klare Slice-Welle-
  Trennung in einer einzigen Welle landen. Mitigation: Welle-1
  startet **nur** mit Faults (Hauptlieferziel); Multi-Agent
  und Observability bekommen eigene Welle-Bloecke (Welle 3+
  und Welle 5+).
- **Trigger-Triage-Drift**: 9 frische SOLLTE-Trigger
  (`016..024`) muessen klar als „eigenstaendige Slices nach
  M3" markiert bleiben, sonst wird M3-Scope unkontrolliert
  gross. Mitigation: C2-Trigger-Triage haelt jeden Trigger
  explizit als „M3-out-of-scope" oder „M3-Welle-N-Material"
  fest.

## 8. Wandert nach

- `done/welle-0.md` mit M3-Welle-7-Closure-Slice (analog
  `welle-6c.md` → `welle-7.md` Pattern aus M2).
- `M3-faults-agents-observability.md` wandert nach `done/`
  mit M3-Welle-7-Closure.
