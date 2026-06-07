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
   Exit-Code reflektiert Aggregat-Pass/Fail (0/1/2
   Tri-State per D-9).
   **stdout-Vertrag (Pflicht):** stdout ist JSON-only — der
   `AbnahmeReport` als ein einziges JSON-Objekt, kein
   Bootstrap-Banner, kein Log, kein Trace-Output. Alle
   Logs/Bootstrap-Meldungen/`diff_replay`-Debug-Output/
   uv-Sync-Banner (durch den `make`-Hook) muessen nach
   stderr umgeleitet werden, damit CI-Consumer
   `make accept | jq '.overall_status'` ohne Vorfilter
   parsen koennen. Der Smoke pinnt das via
   `json.loads(captured.stdout)` ohne Pre-Strip (siehe §2
   Punkt 5).

2. **NEU `tools/accept.py`-Script** (Python; primaer als
   `uv run`-Aufruf aus `make accept` — analog
   `tools/wait_otel_collector.py`; importiert
   `grid_gym.hexagon.core.*` und braucht daher die uv-
   environment oder ein Docker-Build-Target. Docker-Variante
   ist additiv via Compose-Stage abbildbar, nicht
   Default-Pfad) **inkl. duennem Headless-TickLoop-Runner-
   Stub** (integriert in `tools/accept.py`; nutzt den
   hexagon-puren Core-`TickLoop` aus
   `hexagon/core/simulation/tick_loop.py` direkt — kein
   Adapter-Lift noetig, siehe §6 R1): die eigentliche
   Orchestrierungs-Logik. **Drei Sub-Steps laufen
   unabhaengig und sequenziell A → B → C; ein Sub-Step-Fail
   bricht den Lauf NICHT ab (kein fail-fast)** — der CLI
   aggregiert alle drei `pass`/`fail`-Werte und entscheidet
   `overall_status` erst nach Step C. Das ist die
   Voraussetzung dafuer, dass der JSON-Status fuer CI-Consumer
   immer alle drei Sub-Step-Status traegt (siehe auch §6 R4,
   Smoke pinnt das in §2 Punkt 5).
   **Datenabhaengigkeits-Vertrag (kein Widerspruch zu
   no-fail-fast):** Step B konsumiert das `Scenario`-Objekt
   aus Step A (siehe Step B unten). Wenn Step A fehlschlaegt
   (kein `LoadedScenario` verfuegbar), fuehrt Step B seine
   Kernlogik nicht aus, sondern wird im JSON mit
   `status="fail"` + `reason="dependency: scenario load
   failed (see scenario_validation)"` aufgenommen. Step C ist
   stack-, nicht scenario-abhaengig und laeuft unabhaengig
   von Step A/B. So bleiben **alle drei Sub-Step-Entries im
   JSON immer praesent** (Vertrag fuer CI-Consumer), waehrend
   die Daten-Reihenfolge respektiert wird:
   - **Step A — Szenario-Validierung**: laed
     `deploy/scenarios/gg-demo.yaml`, ruft
     `load_scenario(raw)` (`loader.py:113-125`; ein Aufruf
     erledigt **beides** — `validate_scenario_mapping`
     intern + Hash-Berechnung inline; eine separate
     `compute_scenario_hash`-Funktion existiert **nicht**).
     Faengt die gemeinsame Basisklasse `ScenarioError` aus
     `grid_gym.hexagon.core.errors` (Subklassen-Beispiele:
     `ScenarioMissingKeysError`, `ScenarioWrongTypeError`,
     `ScenarioUnsupportedSchemaVersionError`, siehe
     Validator-Imports `validator.py:32-44`); im Fail-Pfad
     wird der Subklassen-Name + `str(exc)` in
     `scenario_validation.reason` durchgereicht. Plus Vergleich
     `LoadedScenario.scenario_hash` gegen einen gepinten
     Erwartungs-Hash (Deterministische Hash-Reproduktion;
     Pin-Lifecycle siehe §3 D-8). Bei Step-A-Fail laufen
     **B und C trotzdem** (siehe Vertrag oben).
   - **Step B — Deterministischer Replay**: zwei Optionen,
     Welle-X-D-2 entscheidet:
     - **Sub-Form A** (standalone, KEINE Abhaengigkeit zu
       GG-MVP-002-Plan): laeuft das Demo-Szenario zweimal
       mit identischem Seed gegen einen Headless-Runner —
       kein FastAPI noetig, Core-`TickLoop` direkt aus
       `hexagon/core/simulation/tick_loop.py`, Devices +
       GridModel + `active_load_events` +
       `active_load_profiles` per Scenario-Loader-
       Aufrufer injiziert (Modul-Docstring Z. 34-38;
       vollstaendiges Wiring-Inventar siehe §6 R1).
       **Re-Use Step A:** Step B konsumiert das bereits
       in Step A geladene `LoadedScenario.scenario`-Objekt
       (kein zweiter YAML-Parse, kein zweiter
       `load_scenario`-Aufruf) — die Step-A-vor-Step-B-
       Reihenfolge ist damit eine explizite
       Datenabhaengigkeit, nicht nur eine Lauf-Reihenfolge.
       Vergleicht die zwei Snapshot-Streams via
       `diff_replay()` (erwartet leeren Diff oder nur
       `VOLATIL`-Klassifikation) **plus** vergleicht den
       gemeinsamen Snapshot-Stream-Hash beider Laeufe
       (bei Determinismus identisch) gegen einen gepinten
       Erwartungs-Hash `EXPECTED_DEMO_SNAPSHOT_STREAM_HASH`
       (Pin-Lifecycle siehe D-8). **Stream-Hash-Konstruktion
       (Pflicht-Vertrag, damit Lint und CLI bauartbedingt
       identisch rechnen)**:
       `sha256(canonical_json(list(snapshots))).hexdigest()`
       aus
       `hexagon/core/serialization/canonical.py::canonical_json`
       — dieselbe Primitive, die `LoadedScenario.scenario_hash`
       in `loader.py:113-125` nutzt; Konsistenz mit Step A
       ohne extra Bytes-Vertrag. Damit prueft Step B **zwei**
       Eigenschaften:
       1. Determinismus (same-seed → identische Streams,
          via `diff_replay`).
       2. Referenz-Treue (Stream-Hash entspricht
          aufgezeichnetem Demo-Referenz-Verhalten).
       Ohne (2) wuerde ein Code-Change, der die Snapshot-
       Semantik gleichfoermig verschiebt (beide Laeufe
       aendern sich gleich), unentdeckt durchgehen. Mit
       (2) bricht der Stream-Hash → Step B `fail` →
       Code-Change muss intendierten Pin-Update
       mitliefern.
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
   **`schema_version`-Typ-Pin:** String-monoton — `"1"`,
   `"2"`, `"3"` etc. (nicht semver `"1.0"`, nicht Integer
   `1`); Schema-Bumps inkrementieren um genau 1. Pydantic-
   Feld `schema_version: Literal["1"]` (strict, kein Drift).
   **`replay_determinism.volatile_only`-Semantik:**
   `true` iff **jeder** Eintrag in der `diff_replay()`-Diff-
   Liste die `ReplayDeltaClassification.VOLATIL`-
   Klassifikation traegt. Bei `diff_count == 0` per
   Konvention `true` (vacuously). Der Sub-Step-Status
   `pass` setzt voraus: `diff_count == 0 OR volatile_only
   == true` **UND** Stream-Hash entspricht Pin.
   **`demo_healthcheck.ready_payload` — pass-through** aus
   dem `/ready`-Response-Body (Welle-6-C2; vier
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
   brechen.
   **Strict-Pin-Scope (was der Smoke pinnt):** Top-Level-
   Keys + `checks`-Sub-Keys (`scenario_validation`,
   `replay_determinism`, `demo_healthcheck`) + `status`-
   Werte (Literal `"pass"`/`"fail"`) + `schema_version`-
   Wert. **Nicht gepinnt:** Inhalt/Felder von `ready_payload`
   (additive `/ready`-Erweiterungen sollen den Smoke nicht
   brechen). So bleiben D-3 strict-mode (auf den fixen
   Schema-Teilen) und additive `/ready`-Evolution
   kompatibel.

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

5. **NEU Integration-Smokes** (drei in einem File;
   D-5-abhaengiger Dateiname per Konvention
   `test_m{N}_welle_{X}_*.py` — bestehende Beispiele:
   `test_m6_welle_5c_safe_005_006_compose_smoke.py`):
   - D-5 Option A (Welle-6-Erweiterung) →
     `tests/integration/test_m6_welle_6_abnahme_cli_smoke.py`.
   - D-5 Option B (eigener 6b-Slice) →
     `tests/integration/test_m6_welle_6b_abnahme_cli_smoke.py`.
   - D-5 Option C (M7-Welle-X) → Filename in der
     M7-Slice-Doc zu fixieren; `welle_x`-Platzhalter
     ist **nicht** zulaessig.

   Drei Smokes:
   - `test_accept_happy_path_returns_pass_status`: alle
     drei Sub-Pruefungen gruen → `overall_status == "pass"`,
     Exit-Code 0, JSON-Schema-conform.
   - `test_accept_invalid_scenario_returns_fail_status`:
     manipuliertes `gg-demo.yaml` → `scenario_validation`
     Sub-Step `fail` + `overall_status == "fail"`, Exit-
     Code == 1 (Aggregate-Fail-Pin per D-9; **nicht**
     „!= 0" — Tool-Error 2 ist explizit anderes Signal).
     **Zusatz-Assertions (no-fail-fast-Vertrag aus §2):**
     `report.checks` enthaelt **alle drei** Keys
     (`scenario_validation`, `replay_determinism`,
     `demo_healthcheck`), nicht nur den fehlgeschlagenen
     ersten — `replay_determinism.status == "fail"` mit
     `reason` der das Dependency-Propagation-Pattern
     spiegelt (`"dependency: scenario load failed (see
     scenario_validation)"`), `demo_healthcheck.status`
     ist `pass` oder `fail` (stack-, nicht
     scenario-abhaengig — Step C laeuft trotz
     Step-A-Fail). Damit pinnt der Smoke
     bauartbedingt, dass `tools/accept.py` keinen
     fail-fast-Bypass einbaut.
   - `test_accept_machine_readable_json_schema_pinned`:
     JSON-Output-Schema (Pydantic-`AbnahmeReport`-Modell)
     bleibt rueckwaerts-kompatibel ueber Schema-Version.
     Pin-Scope siehe §2 Punkt 3 (Top-Level + `checks`-
     Keys + `status`-Literal + `schema_version`-Wert;
     **nicht** `ready_payload`-Inhalt).

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
- **B**: Eigenstaendiger M6-Welle-6b-Slice (`make accept`
  als zusaetzlicher M6-Welle-6-Folge-Slice, vor Welle-7-
  Closure — Naming-Praezedenz `M5-welle-6b` /
  `M5-welle-6c`). Bei dieser Option ist `/ready` aus
  M6-Welle-6-C2 harte Vorbedingung (siehe §5 + §2 Step C).
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

### D-8 — Hash-Pin-Lifecycle fuer Step A + Step B Erwartungs-Hashes

**Frage:** Wo leben die **zwei** gepinten Erwartungs-Hashes
— (i) `EXPECTED_DEMO_SCENARIO_HASH` fuer Step A (Szenario-
Hash aus `LoadedScenario.scenario_hash`) und (ii)
`EXPECTED_DEMO_SNAPSHOT_STREAM_HASH` fuer Step B Referenz-
Treue (siehe §2 Step B Sub-Form A) — und wer aktualisiert
sie bei intendierten Aenderungen am Demo-Szenario?

- **A — Modul-Konstanten in `tools/accept.py`**:
  `EXPECTED_DEMO_SCENARIO_HASH: Final[str] = "<sha256>"`
  + `EXPECTED_DEMO_SNAPSHOT_STREAM_HASH: Final[str] =
  "<sha256>"` mit `# Update bei Aenderung von
  deploy/scenarios/gg-demo.yaml`-Kommentar. Pattern
  analog vorhandener Pin-Konstanten in `tools/check_*.py`.
- **B — Separate Pin-Datei**:
  `deploy/scenarios/gg-demo.expected-hashes` (zwei Zeilen
  `scenario:<sha>` / `stream:<sha>`); `tools/accept.py`
  liest die Datei.
- **C — Pytest-Fixture-Pin im Smoke**: Hashes leben nur im
  Smoke-Test (`test_accept_happy_path_returns_pass_status`),
  nicht im CLI selbst — CLI loggt die Hashes, der Smoke
  verifiziert.

Vorschlag: **A + CI-Drift-Lint** (kombiniert). Begruendung:
Option A macht den CLI-Output selbst-validierend
(Aggregat-Pass/Fail beruht auf den Pins); Aenderungs-
Lifecycle ist via `git blame` auf den Konstanten
nachvollziehbar; keine zusaetzliche Datei. Pattern-Vorbild
ist u.a. der Hash-Pin in ADR-0021-Folge-Substanz.

**Wichtig — Drift-Erkennung haerten:** Option A allein
hat einen Lifecycle-Smell. Eine YAML-Whitespace-/Key-
Order-Aenderung in `deploy/scenarios/gg-demo.yaml` flippt
die Hashes und bricht den Smoke, **ohne** dass die `.py`-
Konstanten im selben Diff stehen; Reviewer sieht den
Bruch erst in CI nach dem Merge des YAML-Commits — das
„Reviewer sieht beide Aenderungen nebeneinander"-Argument
ist optimistisch und reicht nicht. Mitigation: **NEU
`tools/check_demo_scenario_pin.py`** als CI-Pre-Commit-
Lint (`make ci`-Gate):
- ladet `deploy/scenarios/gg-demo.yaml`, recomputed
  beide Hashes (Scenario via `load_scenario(...)
  .scenario_hash`; Stream via Headless-`TickLoop`-Lauf
  identisch zur Step-B-Sub-Form-A-Pipeline);
- vergleicht gegen `EXPECTED_DEMO_SCENARIO_HASH` +
  `EXPECTED_DEMO_SNAPSHOT_STREAM_HASH`;
- bricht mit klarer Fehlermeldung, **welcher** Pin drift
  hat und **welches** `.py`-File anzupassen ist.

**Code-Standort des gemeinsamen Headless-Pfads
(Lint + CLI):** der Replay-Stub-Code muss zwischen
`tools/check_demo_scenario_pin.py` und `tools/accept.py`
geteilt sein — Duplikation ist genau die Drift-Quelle,
die der Lint verhindern soll. Vorschlag: **NEU
`tools/_demo_replay.py`-Helper** (Leading-Underscore =
tools-internal, kein API-Vertrag) mit den Funktionen
`run_demo_replay(seed: int) -> list[Mapping[str, object]]`
+ `hash_snapshot_stream(stream) -> str` (per F-new-1-
Vertrag aus §2 Step B Sub-Form A). Beide Tools
importieren daraus; Drift ist damit bauartbedingt
ausgeschlossen.

Damit landet der Bruch im selben PR wie die YAML-
Aenderung, nicht im nachgelagerten Smoke-Run. Cost-Adjust
§7: die Headless-Stub-Substanz wandert aus
`tools/accept.py` in den NEU `_demo_replay.py`-Helper
(Sum-Net ~konstant; Lint wird trivial, Helper traegt die
Stub-Substanz — siehe §7-Posten-Reorganisation).

### D-9 — Exit-Code-Vertrag fuer `tools/accept.py`

**Frage:** Welche numerischen Exit-Codes liefert
`tools/accept.py` an CI-Consumer, und wie unterscheiden
sie „Abnahme failed" von „Tool selbst kaputt"?

Vorschlag: **drei Werte fixiert** (Pattern analog Unix-
Konvention + `tools/check_core_determinism.py`-Stil):

- **`0` — Aggregate-Pass**: alle drei Sub-Pruefungen
  `pass`; `AbnahmeReport.overall_status == "pass"`;
  JSON-Status auf stdout vollstaendig.
- **`1` — Aggregate-Fail**: mindestens eine Sub-Pruefung
  `fail`; JSON-Status valide auf stdout,
  `overall_status == "fail"`. CI-Consumer kann den JSON-
  Report parsen + reagieren (z. B. welche Sub-Pruefung
  brach).
- **`2` — Tool-Error**: unerwartete Exception im CLI
  selbst — Pydantic-Validation-Crash beim Bau des
  `AbnahmeReport`, YAML-Parser-Exception (File **lesbar**,
  aber Parser-Bruch ist CLI-Internals), Headless-Runner-
  Crash fuer Step B mit unerwartetem Traceback,
  Konfigurations-Fehler im CLI selbst. JSON-Status
  moeglicherweise unvollstaendig oder fehlend; stderr
  traegt Traceback.

**Wichtig — Abgrenzung zu Exit 1 (siehe D-7 Option A):**
HTTP-Connection-Refused / Timeout / Non-200 beim
`/ready`-Poll gehoert **nicht** zu Exit 2. „Demo-Stack
nicht hochgefahren" ist genau das Failure-Signal, das
Step C deterministisch fangen soll → Aggregate-Fail
(Exit 1), nicht Tool-Error. **Analog: HTTP 200 mit
`status != "healthy"`** (z. B. `"starting"` waehrend
Stack-Up oder `"degraded"`, weil eine der vier
Pflicht-Komponenten `api`/`ui`/`db`/`simulation` nicht
ready ist; Three-State-Endpoint per Welle-6-C2)
→ Step C `fail` mit `reason="ready status not healthy:
<status>"` → Exit 1, **nicht** Exit 2. Das ist genau das
Signal, das Step C melden soll, und nicht ein CLI-Bug.
Analog: `gg-demo.yaml`
nicht-existent oder Permission-Denied → Step A `fail` →
Exit 1 (deterministisches Sub-Step-Fail mit
`reason="scenario file not readable"`), nicht Exit 2.
Exit 2 ist reserviert fuer **CLI-interne** Bugs, die
das JSON-Status-Building selbst brechen.

Damit unterscheidet CI klar zwischen „Abnahme failed
(erwartetes Fail-Signal, JSON liefert Details — Team
fixt das Demo-Szenario / Stack)" und „CLI selbst kaputt
(Tool-Bug, Maintainer-Investigation noetig)" —
unterschiedliche Eskalations-Pfade.

Smoke-Vertrag (siehe §2 Punkt 5):
- `test_accept_happy_path_returns_pass_status` → Exit 0.
- `test_accept_invalid_scenario_returns_fail_status` →
  Exit 1 (auf konkreten Wert gepinnt, **nicht** „!= 0").
- Tool-Error-Pfad (Exit 2) wird im Slice nicht eigens
  gesmoked — Coverage ergibt sich aus Pyright-Type-
  Lint + Pytest-Standard-Substanz.

## 4. Sub-Scope (Welle-Vorbelegung)

Falls D-5 Option A (Welle-6-Erweiterung) + D-4 Option A
(monolithisch):

- **M6-Welle-6-C2** erweitert um zusaetzliche Substanz-
  Items:
  - NEU `make accept`-Makefile-Target.
  - NEU `tools/_demo_replay.py`-Helper (Headless-
    `TickLoop`-Stub um den hexagon-puren Core +
    `hash_snapshot_stream`-Primitive per
    `canonical_json`-Vertrag; siehe §6 R1 Wiring-Inventar
    + D-8 Code-Standort-Klaerung). Gemeinsam importiert
    von `tools/accept.py` und
    `tools/check_demo_scenario_pin.py` — Drift
    bauartbedingt ausgeschlossen.
  - NEU `tools/accept.py` als Orchestrator der drei
    Sub-Steps (importiert Replay-Stub aus
    `_demo_replay.py`).
  - NEU `AbnahmeReport` Pydantic-Modell mit
    `EXPECTED_DEMO_SCENARIO_HASH` +
    `EXPECTED_DEMO_SNAPSHOT_STREAM_HASH`-Pin-Konstanten
    (siehe D-8) + Exit-Code-Vertrag (siehe D-9).
  - NEU `tools/check_demo_scenario_pin.py` CI-Drift-Lint
    (siehe D-8 Mitigation; importiert Replay-Stub +
    Hash-Primitive aus `_demo_replay.py`; `make ci`-Gate).
  - NEU `docs/user/abnahme-cli.md`.
  - NEU drei Integration-Smokes (siehe §2 Punkt 5).
- Welle-6-C0-Slice-Doc wird im selben Review-Zyklus
  aktualisiert (zusaetzliches Lieferziel + die Abnahme-CLI-
  Decision D-7).

Falls D-5 Option B (eigenstaendiger M6-Welle-6b-Slice
nach Welle-6-C2; Welle-6-C2 ist Vorbedingung wegen
`/ready`, siehe §5):

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
  als eigener `M6-welle-6b-abnahme-cli`-Slice (D-5
  Option B; M6-Welle-6-C2 ist Vorbedingung wegen
  `/ready`).
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
sammelt.
**Strukturelle Lage (Code-verifiziert):** Der **Core**-
`TickLoop` lebt in
`src/grid_gym/hexagon/core/simulation/tick_loop.py` (M1-
Welle-4 / M2-Welle-6a) und ist **hexagon-pure** — keine
asyncio-Kopplung, keine FastAPI-Imports, nimmt `ClockPort`
+ `RandomPort` + Devices + `grid_model` ueber den
Konstruktor und liefert `tick()` + `snapshot()` direkt.
`adapters/driving/http_api/_tick_loop_driver.py` ist nur
der **Driving-Adapter**, der den Core in die FastAPI-
Async-Welt einhaengt — der Core selbst braucht ihn nicht.
Headless-Aufruf ist daher strukturell duenn (nicht
„trivial", aber ueberschaubar): Core-`TickLoop(...)`
direkt instantiieren, `tick()` in einer synchronen
Schleife rufen, `snapshot()` pro Tick sammeln.
**Wiring-Inventar (Code-verifiziert
`tick_loop.py:218-239`, keyword-only-Konstruktor)** —
der Stub muss instanziieren:
- `run_id: str` (synthetisch, z. B.
  `"abnahme-replay-1"` / `"abnahme-replay-2"`);
- `tick_ms: int` (aus dem geladenen Szenario);
- `scheduler: Scheduler`;
- eine `ClockPort`-Impl (deterministisch, Step-getrieben
  — konkrete Adapter-Klasse waehlt der Implementations-
  Schritt; Audit-Sub-Step der C2-Vorbereitung);
- eine `RandomPort`-Impl (seeded);
- `devices: tuple[DeviceModel, ...]` + `grid_model`
  vom Scenario-Loader-Aufrufer-Pattern (Modul-Docstring
  Z. 34-38);
- **`active_load_events: tuple[LoadEvent, ...]` +
  `active_load_profiles: tuple[LoadProfile, ...]` aus
  dem Scenario** — `Scenario.load_events` /
  `Scenario.load_profiles`, die der Loader via
  `parse_load_events` / `parse_load_profiles` aus dem
  YAML liest (`loader.py:158-159`). **Pflicht-
  Injektion, nicht Konstruktor-Default:** der produktive
  Driver setzt sie genau so (`loader.py:474-475` und
  `:493-494`); `gg-demo.yaml` enthaelt `load_events:`
  (Z. 96) und `load_profiles:` (Z. 106). Ein Stub, der
  bei den Defaults `()` bleibt, tickt **anders als der
  echte Demo-Lauf** — der Stream-Hash entspricht dann
  nicht dem Demo-Referenz-Verhalten, und die
  Referenz-Treue-Eigenschaft (Step B Sub-Form A
  Punkt 2) bricht still, ohne dass der Lint die Ursache
  zeigt. Der Stub muss diese beiden Felder explizit aus
  `LoadedScenario.scenario` durchreichen.

Weitere keyword-only-Parameter mit Defaults bleiben auf
Konstruktor-Default (Replay braucht keine Side-Effects):
- Optionale Ports `fault_port`, `agent_bus`,
  `log_port`, `metrics_port`, `trace_port`,
  `protocol_ports`, `run_repository` → `None`;
- `agents: tuple[Agent, ...]` → `()` (Demo-Szenario
  hat keine Agent-Substanz, ansonsten gilt dieselbe
  Pflicht-Injektion wie fuer LoadEvents/-Profiles —
  Audit-Sub-Step muss das bestaetigen);
- `alarm_id_source: Callable | None` → `None`
  (Alarm-Generierung off-pfad fuer Replay).
**Audit-Pflicht in der C2-Vorbereitung (bzw. Welle-6b-C0
bei D-5 Option B):** verifizieren, dass `gg-demo.yaml`
**keine** Agent-Felder enthaelt — sonst gehoert `agents`
analog zu den LoadEvents/-Profiles in die Pflicht-
Injektions-Liste.
**Mitigation:** Vor der `tools/_demo_replay.py`-Helper-
Implementation muss der Core-`TickLoop`-Konstruktor-Pfad
auditiert sein (Devices + GridModel-Injection ueber den
Scenario-Loader, plus die Auswahl konkreter Clock-/Random-
Adapter-Klassen aus dem Wiring-Inventar). Bei D-5 Option A
(Welle-6-Erweiterung; Vorschlag) landet der Audit in der
C2-Vorbereitung; bei Option B in einem separaten Welle-
6b-C0. In beiden Faellen Auditor-Arbeit, kein Neu-
Implement. **Nicht verwechseln:** Das vorhandene
`make test-determinism` ist `pytest -m determinism`
(Makefile:96, 203) und das vorhandene
`tools/check_core_determinism.py` ist ein **statisches
Lint-Tool** fuer verbotene Imports in Core-Source
(`FORBIDDEN_ROOT_MODULES`, siehe
`check_core_determinism.py:17`) — **kein** Headless-
Runner. Der NEU Headless-Stub in `tools/_demo_replay.py`
(siehe D-8 Code-Standort) ist ein duenner in-process-
Driver um den hexagon-puren Core, nicht eine Neu-
Implementation. Cost-Posten und Begruendung siehe §7.

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
  - NEU `tools/_demo_replay.py`-Helper (Headless-
    `TickLoop`-Stub um den hexagon-puren Core +
    `hash_snapshot_stream`-Primitive; traegt die R1-
    Wiring-Substanz — Scheduler/Clock/Random-Port-
    Instanzen + Devices-/GridModel-Injection per
    Scenario-Loader): 0.5-0.7 Tag.
  - NEU `tools/accept.py` als Orchestrator der drei
    Sub-Steps (Step A: `load_scenario` + Hash-Vergleich;
    Step B: zwei Replay-Laeufe via `_demo_replay`
    + `diff_replay` + Stream-Hash-Vergleich; Step C:
    `/ready`-Poll; JSON-Status-Build + Exit-Code-Vertrag
    per D-9): 0.2-0.3 Tag.
  - NEU `make accept`-Makefile-Target: 0.1 Tag.
  - NEU `AbnahmeReport` Pydantic-Modell + zwei Pin-
    Konstanten (siehe D-8) + drei Smokes (siehe §2 Punkt
    5, Exit-Code-Vertrag per D-9): 0.3 Tag.
  - NEU `docs/user/abnahme-cli.md` (inkl. Abgrenzungs-
    Verweis auf `gg-demo-008-abnahme.md`): 0.2 Tag.
  - NEU `tools/check_demo_scenario_pin.py` CI-Drift-Lint
    (siehe D-8 Mitigation; importiert
    `_demo_replay.run_demo_replay` +
    `_demo_replay.hash_snapshot_stream` + nutzt
    `load_scenario` direkt, recomputed beide Hashes,
    bricht im `make ci`-Gate; durch Helper-Extraktion
    trivial — kein eigener Stub-Code): 0.1 Tag.

Summe: 1.4-1.7 Tage zusaetzlich zur Welle 6 (vorher
1.5-1.8 ohne `_demo_replay`-Helper-Extraktion;
Helper-Pfad ist netto leicht guenstiger, weil der Pin-
Lint von 0.2 auf 0.1 Tag faellt). Falls eigener
Welle-6b-Slice (D-5 Option B), zusaetzlich
C0/C3/C4a/C4b-Boilerplate-Overhead: +0.5-1 Tag. Falls
D-7 Option B (Skript startet Stack selbst), nochmals
+1 Tag (Compose-Lifecycle + Cleanup-on-Failure).

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
