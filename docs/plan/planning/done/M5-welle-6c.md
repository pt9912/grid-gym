# Welle 6c — M5 Abnahmedoku (`GG-DEMO-008`)

**Status:** Done 2026-06-04 — eroeffnet 2026-06-04 mit C0
`3db9fcd` (Slice-Doc) + C2 `0e604e4` (Abnahmedoku
[`docs/user/gg-demo-008-abnahme.md`](../../../user/gg-demo-008-abnahme.md)
+ Top-Level-Doku-Sync + Status-Kompression) + C3 (dieser
Commit; Status/DoD-Sync + Welle-6-Subdivision-Abschluss-
Note). Ausstehend: C4a Self-Close-Move
`M5-welle-6c.md → done/` + C4b Cross-Doc-Refs-Sync.
Dritte und letzte Sub-Welle der Welle-6-Subdivision (siehe
[`M5-welle-6a.md`](M5-welle-6a.md)
§0 Sub-Slicing-Beschluss). Welle 6c loest die letzte
Welle-5-Anti-Scope-Erbschaft auf (Welle-5-C2-Folge-
Entscheid 2026-06-03 in `done/M5-welle-5.md §10.1`:
`GG-DEMO-008` auf Welle 6 verschoben fuer Range-
Konsistenz mit `GG-DEMO-006`). **Welle-6-Subdivision
komplett:** 6a (`Done 2026-06-03`) + 6b (`Done 2026-06-04`)
+ 6c (`Done 2026-06-04`).

Welle 6c ist die **neunte (und letzte) Welle der Welle-6-
Subdivision** ohne neuen Backend-Code. Reiner Doku-Slice:
ein Markdown-Dokument unter `docs/user/`, das alle bereits
in Welle 1..6b gebauten Mechanismen in reproduzierbarer
Abnahmereihenfolge zusammenfasst.

**Erfuellt:** `GG-DEMO-008` (1 SOLLTE).

---

## 1. Context

### 1.1 Existierende Substanz (M5-Welle-1..6b)

Welle 6c dokumentiert eine bereits voll lieferfaehige
Demo-Pipeline:

**HTTP-API (Welle 1..4b):**

- `POST /runs` (Welle 1) erzeugt einen Lauf mit
  `scenario_hash`/`seed`/`tick_ms` (`GG-API-001`).
- `GET /health` (M1 Welle 6a) Liveness-Probe.
- `GET /runs/{run_id}` + `/status` + `/snapshot` (Welle
  1+4a) — Run-Metadaten + Lifecycle-State.
- `POST /runs/{run_id}/control` (Welle 4a) —
  `pause`/`resume`/`stop` (`GG-UI-004`).
- `WS /runs/{run_id}/telemetry` (Welle 3) +
  `WS /alarms-stream` (Welle 4b) — Live-Streams.
- `GET /alarms-history` (Welle 4b) — REST-Fallback
  (`GG-UI-005`).
- `POST /runs/{run_id}/faults` (Welle 6a) —
  Cross-Field-Validation-Form (`GG-UI-007`).
- `GET /runs/{run_id}/devices/state` (Welle 6b) —
  per-Device-State + Quality (`GG-UI-006`).

**UI-Pages (Welle 2..6b):**

- `/`, `/ui/health`, `/runs/{id}/dashboard`,
  `/runs/{id}/control`, `/runs/{id}/alarms`,
  `/runs/{id}/faults`, `/runs/{id}/devices`,
  `/runs/{id}/system` — voller Navigations-Stack.

**Demo-Stack (Welle 5 + 6a):**

- [`deploy/scenarios/gg-demo.yaml`](../../../../deploy/scenarios/gg-demo.yaml)
  — Demo-Scenario mit `faults:`-Block (Welle-6a).
- `python -m grid_gym demo` + `make demo`/`make demo-stop`
  (Welle 5).
- Lifespan-env-var `GRID_GYM_DEMO_SCENARIO_PATH`
  (Welle 5 Decision 6).

**Tests (Stand 2026-06-04):**

- 1722 Unit-Tests + 80 Integration-Tests + 4 skipped.
- `make gates` cache-frei gruen ohne Override (10/10
  A-1-Gates).

### 1.2 Welle-6c-Lieferziel

Welle 6c liefert produktiv:

1. **NEU `docs/user/gg-demo-008-abnahme.md`**
   — Abnahmedoku mit reproduzierbarer Schritt-Folge:
   - Voraussetzungen (Docker, `make`, optional uv).
   - Start (`make demo`) + Healthcheck (`/health`).
   - Scenario-Ausfuehrung (`/runs/{id}/dashboard` Live-
     Telemetry; `/runs/{id}/devices` State-Tabelle;
     `/runs/{id}/system` Status + Service-Health).
   - Fault-Injection (UI-Form unter `/runs/{id}/faults`
     + YAML-side via `gg-demo.yaml`-`faults:`-Block).
   - Replay-Controls (`/runs/{id}/control`
     pause/resume/stop).
   - Export (Snapshot-Stub heute; Telemetry-Stream via
     WS — Welle-7+/M6 ergaenzt CSV/JSONL-Export).
   - Bekannte Einschraenkungen + Forward-Pointer.
2. **Top-Level-Doku-Sync** — `README.md` + `README.de.md`
   um einen kurzen Pointer auf die Abnahmedoku ergaenzt
   (kein neuer Top-Level-Doku-Block).

### 1.3 Welle-6c-Anti-Scope

Welle 6c liefert **explizit nicht**:

- **CSV/JSONL-Export-Endpunkt** — gehoert zu
  `GG-ACCEPT-003`-Welle 7 (Beispielartefakte) und ggf.
  M6-Performance-Slice.
- **Neue ADRs** — pure Doku, keine neue Decision.
- **Neue Tests** — Demo-Pipeline ist durch Welle-5-Smoke
  (`test_m5_welle_5_demo_smoke.py`) + Welle-6a-Smoke
  (`test_m5_welle_6a_fault_smoke.py`) + Welle-6b-Smoke
  (`test_m5_welle_6b_visualization_smoke.py`) bereits
  abgedeckt. Welle 6c verifiziert ueber Abnahme-Review,
  nicht ueber neue automatisierte Tests.
- **Tutorial / Onboarding** — `GG-DEMO-008` verlangt
  Abnahmereihenfolge, kein Tutorial. Tutorial gehoert
  zu `GG-ACCEPT-001` (M5-Welle 7 Closure-Doku).
- **`make demo`-Refactor** — bleibt unveraendert; die
  Doku zeigt die existierende Surface.

---

## 2. Scope

**Lastenheft-Pflichtanforderung** (`spec/lastenheft.md
§24 GG-DEMO-008`):

> Die Demo MUSS eine klare Abnahmereihenfolge dokumentieren.
> Akzeptanz: Die Dokumentation beschreibt Start,
> Healthcheck, Szenarioausfuehrung, Fault Injection,
> Replay und Export in reproduzierbaren Schritten.

Welle 6c liefert genau diese sechs Abnahme-Schritte als
Schritt-Liste mit Kommandos, erwarteten Outputs und
Verweisen auf die produzierenden Wellen.

---

## 3. Architektur-Entscheidungen

**Keine neuen Decisions in Welle 6c.** Pure Doku-Slice;
alle architektonischen Entscheidungen sind in Welle
0..6b verankert. Welle 6c referenziert die existierenden
ADRs 0036 (UI-Stack), 0037 (HTTP-API-Surface), 0038
(Telemetry-Stream), 0039 (TickLoop-Control), 0040
(Alarm-Stream) und die Slice-Docs der Vorgaenger-Wellen.

Welle 6c verzichtet bewusst auf einen C1-ADR-Commit
(Pattern Welle-1/5/6a/6b: kein neuer Port, kein neuer
Vertrag, kein neuer Decision-Slot).

---

## 4. Liefer-Reihenfolge (3..4 Commits)

### Pre-C0 — bereits erledigt (Welle-6b-Closure)

Welle-6b-Self-Close-Move (`b30280e`) + Cross-Doc-Refs-
Sync (`3a6f150`) + Review-Folge (`cd7cfc6`) + EoD-Sync
(`01e4bf5`) sind die Welle-6c-Pre-C0-Pflicht-Sync-
Schritte. Welle 6c startet damit direkt mit C0 (kein
eigener Pre-C0a/Pre-C0b noetig — Welle-6b-Closure-Stack
ist der effektive Pre-C0).

### C0 — `docs(plan)`: M5-welle-6c Slice-Doc

**Dieser Commit.** Enthaelt:

- Slice-Doc [`M5-welle-6c.md`](M5-welle-6c.md) mit
  §1..§9-Struktur (Pattern analog Welle-6a/6b minus
  §3-Decisions).
- Liefer-Reihenfolge (C0 → C2 → C3 → C4a/b).
- DoD-Checkliste (initial leer; C3 hakt ab).

Keine ADR-Aenderung in C0 — Welle 6c hat keinen neuen
Vertrag.

### C1 — **bewusst entfaellt** (Pattern Welle-1 + 5 + 6a + 6b)

Welle 6c fuehrt keinen neuen Port, kein neues Schema,
keine neue Decision ein — daher kein C1-ADR-Commit.

### C2 — `docs(user)`: NEU `gg-demo-008-abnahme.md` +
Top-Level-Doku-Sync

**Doku-Lieferung** mit:

- NEU `docs/user/gg-demo-008-abnahme.md`
  mit 6 Abnahme-Schritten + Voraussetzungen + bekannten
  Einschraenkungen.
- `README.md` + `README.de.md` Pointer-Bullet im
  „Quick Start" / „Demo"-Block auf die Abnahmedoku.
- Tests: `make docs-check` cache-frei gruen (Links
  resolved).

### C3 — `docs(plan)`: Welle-6c Status/DoD-Sync + Top-
Level-Doku-Sync

**Status/DoD-Sync** mit:

- `M5-welle-6c.md` Status `In Progress → Done`.
- `M5-ui-demo.md §3.1 Welle-Status-Tabelle` Zeile
  Welle 6c auf `Done` + Welle-7-Aktive-Welle-Marker.
- `in-progress/README.md` Welle-6c-Closure-Block +
  Welle-7-Aktive-Welle-Marker.
- `in-progress/roadmap.md` Welle-6c-Closure-Entry.
- Welle 6 Sub-Subdivision-Abschluss-Note (alle 3 Sub-
  Slices 6a/6b/6c jetzt Done).

### C4 — `chore` + `docs`: Self-Close-Move + Cross-Doc-
Refs-Sync

Pflicht-Closure-Sequenz per
[`planning/README.md`](../README.md) Wave-Self-Close-
Commit-Konvention:

- **C4a** — `chore: git mv in-progress/M5-welle-6c.md
  → done/` (rename-only).
- **C4b** — Cross-Doc-Refs-Sync nach Move (Pattern
  analog Welle-6b-C4b `3a6f150`).

---

## 5. Critical Files

**Welle-6c-NEU (geschrieben in C2):**

- `docs/user/gg-demo-008-abnahme.md`.

**Welle-6c-MODIFY (in C2):**

- `README.md` — Pointer-Bullet auf die Abnahmedoku im
  Demo/Quick-Start-Block.
- `README.de.md` — gleiches.

**Welle-6c-UNBERUEHRT (kein Edit):**

- Aller Code (`src/`).
- Alle Tests (`tests/`).
- Bestehende `docs/user/*.md`.
- ADRs (`docs/plan/adr/`).
- Welle-5..6b-Demo-Smokes (laufen unveraendert).

---

## 6. Verifikationspfad

**Welle-6c-Gate (per `M5-ui-demo.md §3.1` neue Zeile):**

- `make docs-check` cache-frei gruen (Links aufgeloest).
- `make gates` cache-frei gruen ohne Override (keine
  Test-Aenderungen → Test-Counts bleiben 1722/80).
- Manuelle Abnahme: Reviewer geht die 6 Schritte der
  Abnahmedoku durch, prueft Reproduzierbarkeit gegen
  `make demo` lokal.

**Abnahme-Verifikation (Lastenheft):**

- `GG-DEMO-008` (Abnahmereihenfolge mit 6 Schritten:
  Start, Health, Scenario, Fault, Replay, Export).

**Test-Verifikation:**

- `make test-unit` + `make test-integration` unveraendert
  gruen (keine Test-Aenderungen).

---

## 7. Risiken

**R1 — Doku-Drift gegen Code.** Die Abnahmedoku
referenziert konkrete Endpunkte (`/runs/{id}/devices/
state`, `/runs/{id}/system`, etc.). Wenn Welle-7+/M6
URLs aendert, driftet die Doku.
**Mitigation:** Die Doku verlinkt zu den Slice-Docs der
produzierenden Wellen (Welle 1..6b) als Single-Source-
of-Truth; `make docs-check` faengt broken-link-Drift.
Welle-7-Closure schiebt die Doku ggf. ohnehin in den
M5-Results-Block.

**R2 — Reproduzierbarkeit-Drift gegen `make demo`.**
Wenn `make demo`-Target oder env-vars sich aendern,
zeigt die Doku falsche Kommandos.
**Mitigation:** Die Doku zitiert das Makefile-Target
namentlich; bei Aenderung muss `M5-welle-5.md` (Demo-
Owner-Slice) sowieso syncen, dort wird auch die
Welle-6c-Abnahmedoku als Folge-Update gepflegt.

**R3 — Anti-Scope-Drift.** Reviewer koennte erwarten,
dass die Abnahmedoku auch `GG-ACCEPT-001..003` mit
abdeckt — die gehoeren zu M5-Welle-7-Closure (separate
`M5-results.md`).
**Mitigation:** Welle-6c-Anti-Scope in §1.3 explizit;
Welle-7-Closure-Plan in `M5-ui-demo.md §3.2 Welle 7`
verankert.

---

## 8. Wandert nach

- Bei C3-Closure: `M5-welle-6c.md` bleibt in
  `in-progress/` bis C4a Self-Close-Move.
- `docs/user/gg-demo-008-abnahme.md` bleibt nach C2-
  Lieferung **live** (lebendes End-User-Dokument; kein
  Move).
- Welle 7 (`M5-results.md` + ADR-Acceptance + Self-
  Close-Move `M5-ui-demo.md`) als naechster aktiver
  Schritt nach Welle 6c.

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **NEU `docs/user/gg-demo-008-abnahme.md`** mit
  6 Abnahme-Schritten:
  - Voraussetzungen + Start (`make demo`).
  - Healthcheck (`GET /health`).
  - Scenario-Ausfuehrung (Dashboard + Devices + System-
    Pages).
  - Fault-Injection (UI-Form + YAML).
  - Replay-Controls (pause/resume/stop).
  - Export (Snapshot-Stub-Pointer + WS-Streams).
- [x] **`README.md` + `README.de.md`** Pointer-Bullet
  auf die Abnahmedoku (zusammen mit Status-Block-
  Kompression auf User-Feedback).
- [x] **`make docs-check`** cache-frei gruen.
- [x] **`make gates`** cache-frei gruen ohne Override.
- [x] **`GG-DEMO-008`** erfuellt.
- [x] **`M5-ui-demo.md §3.1 Welle-Status-Tabelle`**
  Welle-6c-Zeile auf `Done 2026-06-04` geflipt (dieser
  Commit).
- [x] **`in-progress/README.md`** Welle-6c-Closure-
  Block + Welle-7-Aktive-Welle-Marker (dieser Commit).
- [x] **`roadmap.md`** Welle-6c-Closure-Entry +
  Welle-6-Subdivision-Abschluss-Note (6a/6b/6c alle
  Done; dieser Commit).
- [ ] **NEU C4 Self-Close-Move + Cross-Doc-Refs-Sync**
  als zwei separate Folge-Commits nach C3 (Pattern
  Welle-6b `b30280e`/`3a6f150`).

**Anti-Scope-Verifikation (Welle 6c NICHT):**

- [x] Keine neuen Tests (Demo-Pipeline durch Welle-
  5/6a/6b-Smokes gedeckt; Test-Counts bleiben 1722/80).
- [x] Keine neuen Endpunkte / kein neuer Code.
- [x] Kein C1-ADR.
- [x] Kein CSV/JSONL-Export (Welle 7+/M6).
- [x] Kein Tutorial (`GG-ACCEPT-001`-Welle-7-Closure).

---

## References

- [`M5-ui-demo.md`](M5-ui-demo.md)
  §3.2 Welle 6c Plan-Items (kanonische Sub-Slicing-
  Aufnahme; Welle-6c-Abnahmedoku-Sub-Bereich).
- [`M5-welle-6a.md`](M5-welle-6a.md)
  §0 Sub-Slicing-Beschluss — Welle 6 → 6a/6b/6c.
- [`M5-welle-5.md`](M5-welle-5.md)
  §10.1 — `GG-DEMO-008`-Defer-Begruendung
  (Range-Konsistenz mit `GG-DEMO-006`).
- [`M5-welle-6b.md`](M5-welle-6b.md)
  — Welle-6b-Devices/System-Pages (von Abnahmedoku
  zitiert).
- [`../../../../spec/lastenheft.md §24`](../../../../spec/lastenheft.md)
  `GG-DEMO-008` Akzeptanztext.
- Pattern-Vorbild **Welle-ohne-C1 + ohne neue Tests**:
  ueber `M5-welle-5` / `M5-welle-6a` / `M5-welle-6b`
  hinaus erste reine Doku-Welle ohne automatisierte
  Test-Substanz; Verifikation per Review.
