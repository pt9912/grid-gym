# GG-MVP-003 Closure — Abnahme-CLI mit maschinenlesbarem Status

**Status:** Next — Scope-Skizze (noch nicht aktiv).
**Datum:** 2026-06-07.
**Quelle:** [`roadmap.md §3 GG-MVP-003`](../in-progress/roadmap.md)
+ Lastenheft §3 Z. 138-144.

---

## 1. Context

`GG-MVP-003` ist die **einzige ✗ Lücke** in der GG-MVP-
Vier-Punkte-Liste (siehe `roadmap.md §3 MVP-Abnahmescope`).

**Lastenheft-Akzeptanz (Z. 138-144, GG-MVP-003):**

> Der MVP MUSS eine CLI oder ein Script fuer
> Abnahmepruefungen bereitstellen. Akzeptanz: Ein einzelner
> Befehl fuehrt deterministische Replay-Pruefung,
> Szenario-Validierung und Demo-Healthcheck aus und liefert
> einen **maschinenlesbaren Status**.

**Stand der drei Sub-Pruefungen:**

| Sub-Pruefung | Substanz heute | CLI-Aggregation |
| --- | --- | --- |
| Deterministische Replay-Pruefung | Core-Diff `diff_replay()` ✓ produktiv (M6-Welle-5c-Audit); plus optional `ReplaySourcePort`-E2E aus [`replay-source-integration.md`](replay-source-integration.md) (`GG-MVP-002`). | ✗ kein Aggregat-Aufruf |
| Szenario-Validierung | `hexagon/core/scenario/validator.py::validate_scenario_mapping` ✓ produktiv (Welle 5, vor M2; `GG-SCN-008`-Vorab-Validierung) | ✗ kein Aggregat-Aufruf |
| Demo-Healthcheck | `GET /health` ✓ produktiv (Liveness); `GET /ready` Three-State produktiv nach M6-Welle-6-C2 (siehe [`../in-progress/M6-welle-6.md`](../in-progress/M6-welle-6.md) — aktiv) | ✗ kein Aggregat-Aufruf |
| **Maschinenlesbarer Aggregat-Status** | ✗ **Lücke** | — |

**Was es heute gibt** (in der Naehe, aber nicht das, was
GG-MVP-003 verlangt):

- `make demo` → Demo-Start, kein Status-Output.
- `make runtime` → Compose-Smoke + `/health`-Poll, kein
  Aggregat.
- `make test-integration` → Pytest + JUnit-XML, aber kein
  Abnahme-Fokus.
- `make ci` / `make fullbuild` → CI-Gate-Aggregat, aber kein
  Stakeholder-fokussiertes „Demo-laeuft-und-ist-deterministisch"-
  Statement.

**Vorhandene Substanz, die wiederverwendet wird:**

- `validate_scenario_mapping(raw)` (Pure-Function-Validator).
- `load_scenario(raw)` → `LoadedScenario(scenario,
  scenario_hash)` (`loader.py:113-125`; ruft intern
  `validate_scenario_mapping` + baut Domain-Form + hasht via
  `sha256(canonical_json(asdict(scenario))).hexdigest()`; es
  gibt **keine** separat aufrufbare
  `compute_scenario_hash`-Funktion — Hash-Berechnung lebt
  ausschliesslich in `load_scenario`).
- `diff_replay(expected, actual, ...)` (Core-Diff).
- `GET /ready`-Endpoint (Three-State; nach Welle-6-C2).
- `make demo` / `make runtime` (Compose-Smoke-Substanz).

## 2. Lieferziel

Ein eigenstaendiger Slice (vermutlich M6-Welle-6-Erweiterung
oder M7-Welle-X; siehe §5) liefert:

1. **NEU `make accept`-Makefile-Target**: ein-Schritt-
   Aufruf, der die drei Sub-Pruefungen orchestriert + den
   maschinenlesbaren JSON-Status auf stdout schreibt.
   Exit-Code reflektiert Aggregat-Pass/Fail.

2. **NEU `tools/accept.py`-Script** (Python; primaer als
   `uv run`-Aufruf aus `make accept` — analog
   `tools/wait_otel_collector.py`; importiert
   `grid_gym.hexagon.core.*` und braucht daher die uv-
   environment oder ein Docker-Build-Target. Docker-Variante
   ist additiv via Compose-Stage abbildbar, nicht
   Default-Pfad) **plus NEU Headless-TickLoop-Runner-Helper**
   (`tools/headless_run.py` oder integriert in
   `tools/accept.py`; Baseline-Substanz, kein
   wiederverwendbares Pattern vorhanden — siehe §6 R1
   Mitigation): die eigentliche Orchestrierungs-Logik. Drei
   Sub-Steps:
   - **Step A — Szenario-Validierung**: laed
     `deploy/scenarios/gg-demo.yaml`, ruft
     `load_scenario(raw)` (`loader.py:113-125`; ein Aufruf
     erledigt **beides** — `validate_scenario_mapping`
     intern + Hash-Berechnung inline; eine separate
     `compute_scenario_hash`-Funktion existiert **nicht**).
     Erwartet keine `ScenarioError`-Subklasse (Hierarchie:
     `ScenarioMissingKeysError`, `ScenarioWrongTypeError`,
     `ScenarioUnsupportedSchemaVersionError` u.a.; gemeinsame
     Basisklasse `ScenarioError` in
     `grid_gym.hexagon.core.errors`, siehe Validator-Imports
     `validator.py:32-44` + Docstring „Wirft typisierte
     `ScenarioError`-Subklassen"). Plus Vergleich
     `LoadedScenario.scenario_hash` gegen einen gepinten
     Erwartungs-Hash (Deterministische Hash-Reproduktion;
     Pin-Lifecycle siehe §3 D-8).
   - **Step B — Deterministischer Replay**: zwei Optionen,
     Welle-X-D-2 entscheidet:
     - **Sub-Form A** (standalone, KEINE Abhaengigkeit zu
       GG-MVP-002-Plan): laeuft das Demo-Szenario zweimal
       mit identischem Seed gegen einen Headless-Runner
       (kein FastAPI noetig — Core-`TickLoop` + Snapshot-
       Sequenz). Vergleicht die zwei Snapshot-Streams via
       `diff_replay()`. Erwartet leeren Diff oder nur
       `VOLATIL`-Klassifikation.
     - **Sub-Form B** (E2E-Pfad ueber laufenden API):
       nutzt `POST /runs` zweimal, vergleicht persistierte
       Replay-Samples ueber `ReplaySourcePort`. Benoetigt
       [`replay-source-integration.md`](replay-source-integration.md)
       als Vorbedingung.
     - Default-Vorschlag: A (standalone, weil unabhaengig
       von GG-MVP-002-Aktivierung).
   - **Step C — Demo-Healthcheck**: pollt das laufende
     Demo-Stack via `GET /ready` (Three-State-Endpoint von
     Welle-6-C2). Erwartet HTTP 200 + Top-Level
     `status == "healthy"`. Im Vorschlags-Pfad (D-5 Option A
     + D-7 Option A) ist `/ready` immer verfuegbar und der
     Stack laeuft via `make demo` vor `make accept`.
     **Kein `/health`-Fallback im Schema-Vertrag**:
     `AbnahmeReport.checks.demo_healthcheck.status` ist per
     D-3 (`pass`/`fail`-Literal, `extra="forbid"`) auf zwei
     Werte gepinnt; ein dritter „degraded reporting"-Wert
     oder zusaetzliche Fallback-Felder waeren ein
     Schema-Bump und ein Smoke-`pinned`-Bruch und sind
     deshalb **nicht** in dieser Welle modelliert. Folge:
     **D-5 Option B/C (Slice unabhaengig von Welle 6
     aktiviert) verlangt produktives `/ready` als Vorbedingung
     in §5** — wenn `/ready` fehlt, ist Step C deterministisch
     `fail` mit Ursache `"/ready endpoint not available; run
     after M6-Welle-6-C2"` und der Aggregat-Status `fail`
     (klar zuordenbar, kein Schema-Drift). Ein echter
     `/health`-Fallback braucht eine eigene Folge-Welle mit
     `AbnahmeReportV2`-Schema-Bump (`schema_version: "2"`).

3. **NEU `AbnahmeReport`-JSON-Schema** (siehe §3 D-3): per-
   Sub-Pruefung-Status (`pass`/`fail` + `reason`) + Top-
   Level-Aggregat-Status. Beispiel:
   ```json
   {
     "schema_version": "1",
     "overall_status": "pass",
     "checks": {
       "scenario_validation": {"status": "pass", "scenario_hash": "<sha256>"},
       "replay_determinism": {"status": "pass", "diff_count": 0, "volatile_only": true},
       "demo_healthcheck": {"status": "pass", "endpoint": "/ready", "ready_payload": {...}}
     }
   }
   ```
   Das `ready_payload`-Feld ist **pass-through** aus dem
   `/ready`-Response-Body (Welle-6-C2; vier
   Lastenheft-Pflicht-Komponenten `api` + `ui` + `db` +
   `simulation` per Lastenheft Z. 1876-1879, fixiert in
   `M6-welle-6.md §3 D-2 Z. 386-454`; `otel-collector` ist
   **nicht** in der Liste — Welle-6-D-2 Z. 448-454 schliesst
   ihn explizit aus, weil er Observability-Sibling und kein
   Lastenheft-Pflicht-Dienst ist) und ist im
   `AbnahmeReport`-Modell **bewusst nicht strict-typed**
   (`Mapping[str, Any]`), damit additive `/ready`-Komponenten-
   Erweiterungen den Schema-Vertrag und den Smoke
   `test_accept_machine_readable_json_schema_pinned` nicht
   brechen. Stricter Vertrag gilt fuer Top-Level + `checks`-
   Keys + `status`-Werte.

4. **NEU `docs/user/abnahme-cli.md`** Maintainer-Doku: wie
   `make accept` lokal + im CI verwendet wird; JSON-Schema-
   Vertrag; Aggregat-Status-Semantik.
   - **Abgrenzung zu vorhandenem
     [`docs/user/gg-demo-008-abnahme.md`](../../../user/gg-demo-008-abnahme.md)**
     (M5-Welle-6c, Lebende 6-Schritt-Abnahmereihenfolge fuer
     `GG-DEMO-008`, manuell durch Operator/Reviewer
     abgearbeitet): bleibt unveraendert produktiv. Die NEU
     `abnahme-cli.md` deckt den **automatisierten**
     `GG-MVP-003`-Pfad ab (ein-Schritt-Aufruf + JSON-Status)
     und referenziert `gg-demo-008-abnahme.md` als manuelle
     Demo-Reihenfolge fuer Reviewer-Walkthrough. Kein Ersatz,
     keine Migration — beide Doks koexistieren mit
     getrennten Anwendungsfaellen (automat vs manuell).

5. **NEU `tests/integration/test_m_welle_x_abnahme_cli_smoke.py`**
   mit drei Smokes:
   - `test_accept_happy_path_returns_pass_status`: alle
     drei Sub-Pruefungen gruen → `overall_status == "pass"`,
     Exit-Code 0, JSON-Schema-conform.
   - `test_accept_invalid_scenario_returns_fail_status`:
     manipuliertes `gg-demo.yaml` → `scenario_validation`
     Sub-Step `fail` + `overall_status == "fail"`, Exit-
     Code != 0.
   - `test_accept_machine_readable_json_schema_pinned`:
     JSON-Output-Schema (Pydantic-`AbnahmeReport`-Modell)
     bleibt rueckwaerts-kompatibel ueber Schema-Version.

6. **`roadmap.md §3 MVP-Abnahmescope` Status-Sync**:
   GG-MVP-003-Zeile von ✗ Lücke auf ✓ produktiv flippen
   nach Closure.

## 3. Architektur-Entscheidungs-Skizze (Welle-X-Decisions; nicht final)

### D-1 — Aufruf-Form (Make vs Python vs Bash)

- **A**: `make accept` + `tools/accept.py` Python-Script
  (Pattern analog `tools/wait_otel_collector.py` aus Welle-
  3-C2; passt zu uv-environment).
- **B**: Eigene CLI-Subcommand-Surface (`grid-gym accept ...`)
  im `pyproject.toml`-Console-Script-Block. Vorbedingung:
  **`[project.scripts]`-Block existiert heute nicht**
  (Code-verifiziert in `pyproject.toml`) und muss neu
  etabliert werden — Aufwand ueber „Eintrag hinzufuegen"
  hinaus (Argparse-Subcommand-Surface + Entry-Point + uv-
  Sync-Hook + Smoke fuer den Entry-Point).
- **C**: Bash-Script-Only.

Vorschlag: A (geringster Boilerplate; passt zur bestehenden
`tools/`-Konvention; uv-environment ueber `make`-Hook).

### D-2 — Replay-Pruefungs-Form (Sub-Form A vs B)

Siehe §2 Step B. Vorschlag: A (standalone Sub-Form), weil
unabhaengig von der Aktivierung von
[`replay-source-integration.md`](replay-source-integration.md).
Falls die GG-MVP-002-Substanz zuerst kommt, kann der CLI
spaeter auf Sub-Form B migrieren.

### D-3 — JSON-Schema-Verstaerkung

- **A**: Pydantic-Modell mit `model_config = ConfigDict(
  strict=True, extra="forbid")` (analog ADR 0045
  `_BaseRequest`-Mixin).
- **B**: Plain `dict`-Output ohne Schema.

Vorschlag: A (maschinenlesbar = strenger Vertrag; Schema-
Versionierung via `schema_version`-Feld).

### D-4 — Sub-Slicing-Beschluss

- **A**: Monolithischer Slice (Make-Target + Script + Smokes
  + Doku in einer Welle).
- **B**: Sub-Slicing — eigener Slice fuer Replay-Step
  (falls Sub-Form B per D-2 gewaehlt wird und
  `replay-source-integration.md` noch nicht aktiv ist).

Vorschlag: A (wenn D-2 Option A; standalone Replay-Step ist
klein genug fuer eine Welle).

### D-5 — Welle-Zuordnung

- **A**: M6-Welle-6-Scope-Erweiterung (additive 4. Substanz-
  Item neben `/ready` + DevContainer + IEC-Pfad-B). Passt
  thematisch zum NEU `/ready`-Endpoint.
- **B**: Eigenstaendiger M6-Welle-7-Vorlauf-Slice (`make
  accept` als M6-Closure-Beleg).
- **C**: M7-Welle-X (Post-MVP).

Vorschlag: A wenn Welle-6-Scope nicht ueberlaeuft (die
Welle 6 hat bereits 3 Lücken zu schliessen; Erweiterung um
GG-MVP-003 macht sie zu „Alles fixen plus Abnahme-CLI" —
Aufwand ~+0.5 Tag).

### D-6 — ADR-Bedarf

- **Wahrscheinlich kein NEU ADR**. Begruendung:
  - `make accept` ist Operations-/Doku-Substanz, kein
    Architektur-Vertrag.
  - JSON-Schema-Strict-Mode ist ADR-0045-Pattern;
    `AbnahmeReport`-Modell schaerft das nicht weiter.
  - Falls D-5 Option A (Welle-6-Erweiterung): Welle-6-D-6
    bleibt bei NEU ADR 0046 fuer Multi-Python-Test-Stage;
    Abnahme-CLI braucht keinen eigenen ADR.

### D-7 — Stack-Start-Verantwortung fuer Step C (Healthcheck)

Step C (`/ready`-Poll) braucht ein laufendes Demo-Stack
(Compose-up + Postgres + OTel + API). Zwei Modelle:

- **A — erwartet laufenden Stack** (User-Pflicht): Aufrufer
  startet `make demo` oder `make runtime` vor `make accept`;
  `tools/accept.py` pollt nur. Step C `fail` → klar dem User
  zuordenbar (Stack nicht hochgefahren). Skript bleibt klein
  (~0.5-1 Tag, siehe §7).
- **B — Skript startet/stoppt selbst** (analog `make
  runtime`-Pattern): `tools/accept.py` macht
  `docker compose up` + Wait + `down`. Self-contained, aber
  Compose-Lifecycle-Boilerplate + Cleanup-on-Failure +
  Volumes-Frage (DESTRUKTIV?) verdoppelt Cost-Estimate
  (~+1 Tag, siehe §7-Adjust).

Vorschlag: **A** (User-Pflicht). Begruendung: `make demo` ist
bereits Pflicht-Path (Makefile:469 — „make demo ist das
Pflicht-Demo-Pattern"); Composability mit CI-Pipelines
(Stack-Up als separater Gate-Step); kleinerer Slice. In
`docs/user/abnahme-cli.md` wird der Reihenfolge-Aufruf
`make demo && make accept` dokumentiert.

### D-8 — Hash-Pin-Lifecycle fuer Step A Erwartungs-Hash

**Frage:** Wo lebt der gepinte Erwartungs-Hash fuer
`deploy/scenarios/gg-demo.yaml`, und wer aktualisiert ihn
bei intendierten Aenderungen am Demo-Szenario?

- **A — Modul-Konstante in `tools/accept.py`**:
  `EXPECTED_DEMO_SCENARIO_HASH: Final[str] = "<sha256>"`
  mit `# Update bei Aenderung von deploy/scenarios/gg-
  demo.yaml`-Kommentar. Pattern analog vorhandener
  Pin-Konstanten in `tools/check_*.py`.
- **B — Separate Pin-Datei**:
  `deploy/scenarios/gg-demo.expected-hash` mit Rohem-Hash;
  `tools/accept.py` liest die Datei.
- **C — Pytest-Fixture-Pin im Smoke**: Hash lebt nur im
  Smoke-Test (`test_accept_happy_path_returns_pass_status`),
  nicht im CLI selbst — CLI loggt den Hash, der Smoke
  verifiziert.

Vorschlag: **A** (Pin im CLI). Begruendung: macht den
CLI-Output selbst-validierend (Aggregat-Pass/Fail beruht
auf dem Pin); Aenderungs-Lifecycle ist nachvollziehbar via
`git blame` auf der Konstante; keine zusaetzliche Datei.
Demo-Szenario-Aenderungen erzwingen Konstanten-Update im
selben Commit (Reviewer sieht beide Aenderungen
nebeneinander). Pattern-Vorbild ist u.a. der Hash-Pin in
ADR-0021-Folge-Substanz.

## 4. Sub-Scope (Welle-Vorbelegung)

Falls D-5 Option A (Welle-6-Erweiterung) + D-4 Option A
(monolithisch):

- **M6-Welle-6-C2** erweitert um zusaetzliche Substanz-
  Items:
  - NEU `make accept`-Makefile-Target.
  - NEU `tools/accept.py` mit drei Sub-Steps.
  - NEU Headless-TickLoop-Runner-Helper
    (`tools/headless_run.py` oder integriert in
    `tools/accept.py` — siehe §6 R1, baseline-Substanz).
  - NEU `AbnahmeReport` Pydantic-Modell.
  - NEU `docs/user/abnahme-cli.md`.
  - NEU drei Integration-Smokes (siehe §2 Punkt 5).
- Welle-6-C0-Slice-Doc wird im selben Review-Zyklus
  aktualisiert (zusaetzliches Lieferziel + die Abnahme-CLI-
  Decision D-7).

Falls D-5 Option B (eigenstaendiger M6-Welle-7-Vorlauf-
Slice):

- Eigener Slice `M6-welle-6b-abnahme-cli.md` mit C0/C2/C3-
  Stack analog Welle-5c.
- C1 entfaellt (D-6 kein NEU ADR).

## 5. Vorbedingungen + Aktivierungs-Bedingungen

**Vorbedingungen** (alle erfuellt; eine bedingt erfuellt):

- ✓ `validate_scenario_mapping` produktiv (Welle 5, vor M2 —
  Validator hat M2-Welle-0a + M3-Welle-4b-Erweiterungen,
  Initial-Welle entsprechend frueher).
- ✓ `load_scenario` produktiv (Welle 5, vor M2;
  `loader.py:113-125` — liefert `LoadedScenario.scenario_hash`
  inline, keine separate `compute_scenario_hash`-Helper-
  Funktion).
- ✓ `diff_replay` Core-Algorithm produktiv (M6-Welle-5c-
  Audit).
- ✓ `make demo` produktiv (M5-Welle-5 Demo-Stack, Makefile-
  Kommentar Z. 468) + `make runtime` Compose-Smoke
  (aelter, M3-Vorgaenger).
- ⚠ `GET /ready` Three-State-Endpoint: produktiv erst nach
  M6-Welle-6-C2 (aktiv; siehe
  [`../in-progress/M6-welle-6.md`](../in-progress/M6-welle-6.md)).
  Falls dieser CLI-Slice in M6-Welle-6-Scope-Erweiterung
  geht (D-5 Option A), ist die Vorbedingung im selben Slice
  erfuellt. Fuer **D-5 Option B/C** (Slice unabhaengig von
  Welle 6): `/ready` ist **harte Vorbedingung** — kein
  `/health`-Fallback im aktuellen Schema (siehe §2 Step C +
  D-3); Aktivierung erst nach Welle-6-C2-Closure oder mit
  einem `AbnahmeReportV2`-Schema-Bump in einer Folge-Welle.

**Aktivierungs-Bedingungen** (eine genuegt):

- **M6-Welle-6-Scope-Erweiterung** (D-5 Option A): aktiviert
  sofort als zusaetzliches Lieferziel in Welle-6-C2; passt
  zum NEU `/ready`-Endpoint.
- **GG-MVP-003-Closure vor M6-Welle-7-Closure**: aktiviert
  als eigener Welle-6b-Slice (D-5 Option B).
- **Stakeholder-Bedarf fuer maschinenlesbares Abnahme-
  Statement**: Releases / Demo-Praesentation / Compliance-
  Belege.
- **CI-Pipeline-Erweiterung**: ein `make accept`-Gate als
  zusaetzlicher CI-Smoke gibt Maintainern frueher Feedback
  als das volle `make ci`.

**Wenn nichts davon eintritt:** `GG-MVP-003` bleibt
✗ Lücke bis M7+; Roadmap §3 GG-MVP-003-Zeile bleibt ✗.
M6-Welle-7-Closure notiert den Defer-Vermerk.

## 6. Risiken

**R1 — Replay-Determinismus-Pruefung ist nicht trivial
ohne `ReplaySourcePort`.** Sub-Form A (standalone) braucht
einen Headless-Runner, der das Demo-Szenario zweimal mit
identischem Seed durchlaeuft + die Snapshot-Sequenzen
sammelt. Der bestehende `TickLoop` ist als asyncio-Loop in
`adapters/driving/http_api/_tick_loop_driver.py` verkabelt
— kann er headless aufgerufen werden?
**Mitigation:** Welle-X-C0 auditiert den `TickLoop`-
Standalone-Pfad. **Wichtig:** Das vorhandene
`make test-determinism` ist `pytest -m determinism`
(Makefile:96, 203) und das vorhandene
`tools/check_core_determinism.py` ist ein **statisches Lint-
Tool** fuer verbotene Imports in Core-Source
(`FORBIDDEN_ROOT_MODULES`, siehe
`check_core_determinism.py:17`) — **kein** Headless-Runner.
Ein NEU `tools/headless_run.py`-Helper (oder direkt in
`tools/accept.py` integriert) ist daher **baseline-Substanz
des Slices**, nicht „falls noetig"-Optional. Das `pytest -m
determinism`-Pattern kann als Test-Vorbild dienen, liefert
aber keine wiederverwendbare Runner-API. Cost-Adjust: der
Baseline-Cost-Estimate §7 verschiebt den `+0.5 Tag`-
Headless-Runner-Posten von „falls noetig" auf „baseline".

**R2 — `/ready`-Endpoint ist von Welle-6-Aktivierung
abhaengig.** Sub-Form fuer Step C macht den `make accept`-
Lauf von Welle-6-Closure abhaengig.
**Mitigation:** Wenn D-5 Option A (Welle-6-Erweiterung),
ist die Abhaengigkeit aufgeloest (`/ready` und `make accept`
landen im selben Slice). Bei Option B ist Welle 6 als
Vorbedingung explizit in §5 markiert.

**R3 — JSON-Schema-Drift.** Wenn der `AbnahmeReport`-
Schema-Vertrag spaeter erweitert wird (z. B. zusaetzliche
Sub-Checks), brechen rueckwaerts-kompatible CI-Parser.
**Mitigation:** `schema_version`-Feld + Pydantic-`extra="
forbid"` machen Schema-Erweiterungen sichtbar. Smoke
`test_accept_machine_readable_json_schema_pinned` pinnt das
in CI.

**R4 — Reihenfolge der drei Sub-Pruefungen.** Demo-
Healthcheck braucht ein laufendes Stack; Szenario-Validierung
ist stack-agnostisch; Replay-Pruefung (Sub-Form A) ist
ebenfalls stack-agnostisch (headless TickLoop).
**Mitigation:** `tools/accept.py` orchestriert: A (Szenario)
→ B (Replay headless) → C (Healthcheck gegen laufenden
Stack). Stack-Start-Verantwortung ist per **D-7** fixiert
(Vorschlag A: Aufrufer-Pflicht via `make demo` vor
`make accept`); Step C `fail` ohne laufenden Stack ist
erwartetes, klar-zuordenbares Verhalten und kein Bug. Sub-
Steps sind unabhaengig und ihre Failures werden separat
aggregiert (kein fail-fast — alle drei laufen immer, damit
der JSON-Status alle drei `pass`/`fail`-Werte enthaelt).

## 7. Cost-Estimate

Grobe Schaetzung (Welle-X-Substanz, falls Welle-6-
Erweiterung):

- C2-Erweiterung (zusaetzlich zur Welle-6-Substanz):
  - NEU `tools/accept.py` mit drei Sub-Steps: 0.5-1 Tag.
  - NEU `make accept`-Makefile-Target: 0.1 Tag.
  - NEU `AbnahmeReport` Pydantic-Modell + Smokes: 0.3 Tag.
  - NEU `docs/user/abnahme-cli.md` (inkl. Abgrenzungs-
    Verweis auf `gg-demo-008-abnahme.md`): 0.2 Tag.
  - NEU Headless-TickLoop-Runner (baseline, siehe R1
    Mitigation — kein wiederverwendbares Pattern
    vorhanden): +0.5 Tag.

Summe: 1.5-2.5 Tage zusaetzlich zur Welle 6. Falls eigener
Welle-6b-Slice (D-5 Option B), zusaetzlich C0/C3/C4a/C4b-
Boilerplate-Overhead: +0.5-1 Tag. Falls D-7 Option B
(Skript startet Stack selbst), nochmals +1 Tag (Compose-
Lifecycle + Cleanup-on-Failure).

## 8. References

- [`../in-progress/roadmap.md §3 GG-MVP-003`](../in-progress/roadmap.md)
  — MVP-Abnahmescope-Tabelle; ✗ Lücke; wird mit Welle-X-
  Closure auf ✓ produktiv geflippt.
- [`../../../../spec/lastenheft.md §3 GG-MVP-003`](../../../../spec/lastenheft.md)
  — Akzeptanz-Quelle (Z. 138-144).
- [`./replay-source-integration.md`](replay-source-integration.md)
  — Schwester-Plan fuer `GG-MVP-002`; potenzielle
  Sub-Form-B-Abhaengigkeit fuer Step B (Replay-Pruefung
  ueber `ReplaySourcePort`-E2E).
- [`../in-progress/M6-welle-6.md`](../in-progress/M6-welle-6.md)
  — aktive Welle 6 mit NEU `/ready`-Endpoint; potenzielles
  Scope-Erweiterungs-Ziel (D-5 Option A).
- [`../../adr/0045-http-api-request-strict-validation.md`](../../adr/0045-http-api-request-strict-validation.md)
  — Pydantic-Strict-Mode-Vorbild fuer `AbnahmeReport`-
  Schema-Form (D-3).
- [`../../../user/safe-007-008-sim-prod-input-validation.md`](../../../user/safe-007-008-sim-prod-input-validation.md)
  — Audit-Doku-Vorbild fuer `docs/user/abnahme-cli.md`-
  Form.
- [`../../../user/gg-demo-008-abnahme.md`](../../../user/gg-demo-008-abnahme.md)
  — Lebende manuelle 6-Schritt-Abnahmereihenfolge fuer
  `GG-DEMO-008` (seit M5-Welle-6c). Bleibt unveraendert
  produktiv; NEU `abnahme-cli.md` deckt orthogonal den
  automatisierten `GG-MVP-003`-Pfad ab (Abgrenzung siehe
  §2.4).
- `src/grid_gym/hexagon/core/scenario/validator.py::validate_scenario_mapping`
  — Sub-Step A Substanz.
- `src/grid_gym/hexagon/core/scenario/loader.py::load_scenario`
  (Z. 113-125) — Sub-Step A Validierung **und**
  Hash-Determinismus (Hash inline via
  `sha256(canonical_json(asdict(scenario))).hexdigest()`;
  Resultat als `LoadedScenario.scenario_hash`).
- `src/grid_gym/hexagon/core/replay/diff.py::diff_replay`
  — Sub-Step B Substanz.
