# Welle 6c — MVP-Demo-Szenario + E2E-Tests + Welle-6-Closure

**Status:** Done — Welle 6 abgeschlossen am 2026-05-20 mit
`8a3aa2f` (C0, Slice-Doc) + `c31052c` (C1, `feat`) +
`6adb041` (C2, Doc-Sync) + `43aabbd` (C3, Review-Folge-1:
4 Medium + 6 Low Findings) + Review-Folge-2 (C4,
`fix(welle-6c)`: User-Cross-Check-Findings — Doku-Drift +
DoD-Checkbox-Sync + `tool_version`-Fallback).
Schliesst die Wellen-Reihe 6a (`27a441f`) + 6b (`0f1c597` +
`93f784f`) ab. Kanonische Slice-Spezifikation:
`M2-devices.md §3 Welle 6c` — dieses Dokument ist
lesefreundlicher Index + per-Welle-Tracking, nicht Ersatz.

**Spec-Reife:** Inhaltlich final. C2 hat den Header auf `Done`
gezogen und Hash-Platzhalter ersetzt; C3 adressiert Code-
Quality-Findings; C4 adressiert User-Cross-Check-Findings
(Doku-vs-Implementation-Drift, tool_version-Robustness) ohne
Spec-Aenderung. Letzter Findings-Stand: 0 High, 5 Medium,
7 Low — alle adressiert.

## 1. Context

M2 Welle 6b (`0f1c597` + Doc-Sync `93f784f`) hat den
Scenario-Loader und das TickLoop-Event-Wiring inkl. Auto-Schluss
geliefert (ADR 0021, `Provisional`). Welle 6c ist der Abschluss-
Slice von Welle 6 laut `M2-devices.md §3 Welle 6c` und
schliesst gleichzeitig die Welle-6-Closure-Bestandteile ab:

- liefert das **End-to-End-MVP-Demo-Szenario** als YAML-Fixture
  und stellt damit `GG-MVP-002` (End-to-End-Demo) sicher;
- verifiziert per Integrationstest die **deterministische
  Reproduzierbarkeit** (zweifacher Lauf, byte-identische
  `TickResult.emitted_telemetry` ≥ 100 Ticks) plus
  Postgres-`runs`-Roundtrip;
- verifiziert per Unit-Property-Test, dass die
  **`ScenarioDevice`-Eingabereihenfolge** keine Telemetry-Drift
  erzeugt (Welle-3-Scheduler-Pattern);
- hebt **ADR 0015 (Snapshot-Envelope v2)** auf `Accepted` und
  zieht den Status-Header von `M2-devices.md` auf
  „Welle 6 abgeschlossen", `Naechster Schritt: Welle 7`.

Welle 6c bricht keine Architektur-Grenzen: die YAML→Mapping-
Konvertierung lebt als Test-Helper, der Core bleibt
I/O-agnostisch (ADR 0021 unverletzt).

## 2. Scope

**In Scope:**

1. `tests/integration/scenarios/mvp_demo.yaml` als End-to-End-
   MVP-Demo-Szenario (5 MVP-Geraete + `grid_model`-Bilanz +
   1 `LoadEvent` + 1 `LoadProfile`).
2. Test-seitiger YAML-Loader (`tests/integration/_yaml_scenario_loader.py`)
   mit schema-bewusster Decimal-Coercion.
3. Integrationstest (`tests/integration/test_mvp_demo_scenario.py`)
   — Determinismus-Vergleich + Postgres-`runs`-Roundtrip.
4. Unit-Property-Test
   (`tests/unit/hexagon/core/simulation/test_scenario_permutation.py`)
   — `ScenarioDevice`-Permutation → byte-identische Telemetry.
5. Welle-6-Closure-Doc-Sync: ADR 0015 + ADR 0021 → `Accepted`,
   `M2-devices.md` §1/§3, `roadmap.md`, beide README.

**Anti-Scope:**

- Kein produktiver `src/grid_gym/adapters/driving/scenario_yaml/`
  Adapter — bleibt fuer eigenes Slice/ADR nach M2.
- Kein Lese-Migrations-Pfad fuer v1-Snapshots (M6,
  `GG-PERSIST-*`).
- Keine SOLLTE-Geraete-Tests (`GG-DEV-015..018`), keine
  Fault-Injection, keine UI — alles M3+.
- Keine Erweiterung von `CRITICAL_COV_TARGETS` (Default-Liste
  enthaelt `core/scenario` seit Welle 6a).

## 3. Architektur-Entscheidungen

Welle 6c bringt **keine neue ADR**. Hebt zwei Provisional-ADRs
auf `Accepted` (Welle-6b-Closure-Folgeerwartung aus dem
`93f784f`-Commit-Body):

- **ADR 0015** (Snapshot-Envelope v2, `Provisional` seit Welle 6a):
  v1→v2-Implementation und typisierter
  `TickLoopSnapshotVersionError` sind seit Welle 6a aktiv
  (`src/grid_gym/hexagon/core/simulation/tick_loop.py:74,517,562`
  + `tests/unit/hexagon/core/simulation/test_snapshot_envelope_v1_to_v2.py`).
- **ADR 0021** (Scenario-Loader + TickLoop-Event-Wiring,
  `Provisional` seit Welle 6b): `build_devices`/`build_tick_loop`
  + Vor-Tick-Block werden in der MVP-Demo produktiv exerziert;
  der Permutations-Property-Test pinnt §2.2/§2.9 Determinismus.

## 4. Liefer-Reihenfolge (3 Commits)

### C0 — `docs(plan)`: Welle-6c Slice-Doc

Dieses Dokument (`docs/plan/planning/in-progress/welle-6c.md`)
als Welle-Start-Marker. Status: `In Progress`. Kein Code.

### C1 — `feat(welle-6c)`: Szenario-Fixture + Tests

**Neue Dateien:**

1. **`tests/integration/scenarios/mvp_demo.yaml`** —
   End-to-End-MVP-Demo:
   - `schema_version: grid-gym.scenario.v1`
   - `simulation: { tick_ms: 1000, duration_s: 100, seed: 0xC0FFEE }`
   - 5 MVP-Geraete: 1× Battery, 1× PV, 1× Load, 1× GridConnection
     (Auto-Schluss-Empfaenger), 1× SmartMeter
   - `grid_model`-Block (YAML/Validator-Key; wird vom Loader zu
     `Scenario.grid_model_config: GridModelConfig | None` parsed)
     mit den 8 Decimal-Feldern (siehe `_minimal_raw_mapping` bzw.
     `_grid_model_config` in
     `tests/unit/hexagon/core/scenario/test_loader_welle_6b.py`
     — Funktions-Referenz statt Zeilenbereich, da driftet)
   - 1× `LoadEvent` (z. B. `set_power_kw` auf der Load bei Tick 10)
   - 1× `LoadProfile` (kurze Profilreihe, z. B. 10 Stuetzpunkte)
   - **Numerische Werte als Strings** in YAML (`"100.0"`), damit
     der Helper sie nach `Decimal` konvertieren kann ohne
     Float-Praezisionsverlust.

2. **`tests/integration/_constants.py`** — eingefrorene
   Test-Konstanten:
   ```python
   M2_DEMO_SEED: Final[int] = 0xC0FFEE
   MVP_DEMO_SCENARIO_PATH: Final[Path] = (
       Path(__file__).parent / "scenarios" / "mvp_demo.yaml"
   )
   MIN_DETERMINISM_TICKS: Final[int] = 100
   ```

3. **`tests/integration/_yaml_scenario_loader.py`** — Test-Helper:
   ```python
   def load_yaml_scenario(path: Path) -> LoadedScenario:
       raw = yaml.safe_load(path.read_text())
       coerced = _coerce_decimals(raw)   # walks known numeric paths
       return load_scenario(coerced)
   ```
   `_coerce_decimals` macht eine **schema-bewusste** Konvertierung
   auf den YAML/Mapping-Schluesseln (nicht auf den parsed
   `Scenario`-Domain-Feldern):
   `simulation.tick_ms/duration_s/seed` bleiben `int`; in
   `devices[*].params.*`, `grid_model.*` (Validator-Key, wird
   spaeter zu `Scenario.grid_model_config`), `load_events[*].*`
   (Decimal-Felder: `start_s`, `duration_s`, `power_kw`) und
   `load_profiles[*].tick_values[*]` (Decimal-Liste) wird
   `str` → `Decimal(str_value)` umgewandelt. Underscore-Prefix
   am Datei-Namen signalisiert internen Test-Helper.

4. **`tests/integration/test_mvp_demo_scenario.py`** — zwei Tests:
   - **`test_demo_scenario_telemetry_is_byte_identical_across_runs`**:
     Laedt YAML, baut zwei `TickLoop`-Instanzen mit gleichem
     Seed, treibt jede `MIN_DETERMINISM_TICKS=100` Ticks,
     vergleicht
     `tuple(result.emitted_telemetry for result in run_a) ==
     tuple(... run_b)`.
   - **`test_demo_scenario_run_roundtrips_through_postgres`**:
     Persistiert `RunMetadata` (mit `scenario_hash` aus
     `LoadedScenario`, `seed=M2_DEMO_SEED`, `tick_ms=1000`,
     `started_at`/`ended_at` als hardcoded ISO-8601-UTC-Strings
     (kein Live-Clock-Pull noetig, da der Test nur den
     `runs`-Roundtrip pinnt), `tool_version` aus
     `importlib.metadata.version("grid-gym")`) ueber
     `PostgresRunRepository.save(...)`,
     liest per `get_by_id(...)` zurueck, vergleicht 1:1.

5. **`tests/integration/conftest.py`** — `postgres_dsn`-Fixture
   Modul-uebergreifend hochziehen (bisher lokal in
   `test_postgres_run_repository.py:33–60`).

6. **`tests/unit/hexagon/core/simulation/test_scenario_permutation.py`** —
   Hypothesis-Property-Test (Welle-3-Pattern, spiegelt
   `test_scheduler.py:188–208`):
   ```python
   @st.composite
   def _devices_and_permutation(draw): ...   # generiert tuple + permutation

   @given(payload=_devices_and_permutation(), seed=st.integers(0, 2**32 - 1))
   @settings(max_examples=50, deadline=None,
             suppress_health_check=[HealthCheck.too_slow])
   def test_scenario_device_permutation_yields_identical_telemetry(
       payload, seed
   ) -> None:
       devices, perm = payload
       telemetry_a = _run_tickloop(devices, seed, ticks=20)
       telemetry_b = _run_tickloop(perm, seed, ticks=20)
       assert telemetry_a == telemetry_b
   ```
   `_run_tickloop` baut `Scenario` direkt aus dem Tuple
   (kein YAML, kein Postgres) und treibt 20 Ticks — schnell
   genug fuer 50 Hypothesis-Beispiele.

**Edits:**

- `tests/integration/test_postgres_run_repository.py` — lokale
  `postgres_dsn`-Fixture entfernen (nach `conftest.py` umgezogen).

### C2 — `docs(plan)`: Welle-6c Status/DoD-Sync

Spiegelt die fuenf Dateien aus `93f784f` (Welle-6b-Sync), plus
finalen Status-Update auf `welle-6c.md`:

1. **`docs/plan/adr/0015-snapshot-envelope-v2.md`** —
   `Status:`-Block (Zeilen 1–10) auf `Accepted` umschreiben, mit
   Welle-6c-Closure-Commit-Hash.
2. **`docs/plan/adr/README.md`** — ADR-0015-Zeile auf `Accepted`.
3. **`docs/plan/planning/in-progress/M2-devices.md`**:
   - §1 Status-Header (Zeile 1–5): „Welle 0/1/2/3/4/5/6a/6b
     abgeschlossen" → „Welle 0/1/2/3/4/5/6 abgeschlossen" mit
     Welle-6c-Commit-Hash;
   - §3 Welle-6c-Bullets (Zeile 1205–1231): Closure-Notizen
     ergaenzen (Pfade, Commit-Hash);
   - §3 Welle-6-Gate-Erwartung: ADR 0015 → `Accepted` bestaetigt;
   - §1 „Naechster Schritt" → „Welle 7 (Closure)".
4. **`docs/plan/planning/in-progress/README.md`** — M2-Zeile auf
   „Wellen 0..6 abgeschlossen; Welle 7 (Closure) ausstehend".
5. **`docs/plan/planning/in-progress/roadmap.md`** — M2-Block
   (Zeilen 122–166): die DoD-Checkboxen, deren Inhalt durch Welle
   4–6c geliefert wurde (`SmartMeter`, `GridConnection`,
   `TickLoop`-deterministische-Order, Geraete-Snapshot-Sub-
   Snapshots), auf `[x]` mit Commit-Refs setzen. M2-Status bleibt
   `In Progress` — Closure-Flip erfolgt mit Welle 7. (Hinweis:
   C2 hat diese DoD-Updates urspruenglich angekuendigt aber nicht
   geliefert; nachgereicht in Review-Folge-2-Commit C4 — siehe
   §4.C4.)
6. **`docs/plan/planning/in-progress/welle-6c.md`** — Status-
   Header von `In Progress` auf `Done — Welle 6 abgeschlossen
   am 2026-05-20 mit `8a3aa2f` (C0) + `c31052c` (C1) + diesem
   C2-Doc-Sync` gezogen; Verifikationspfad als „erfuellt"
   markiert.

### C3 — `fix(welle-6c)`: Review-Folge (Schaerfung-Pattern)

Code-Review nach C2-Closure hat 0 High, 4 Medium und 6 Low
Findings ergeben — kein Supersede-ADR, alle in einem `fix`-
Commit adressiert (Schaerfung-Pattern aus Welle 6b).

**Medium (4):**

- **M-1**: `test_scenario_permutation.py` deckt SmartMeter
  nicht ab. Permutations-Strategie permutiert jetzt nur
  Nicht-Aggregator-Devices; SmartMeter haengt konstant am Ende
  (spiegelt MVP-Demo-Konvention, ADR 0018 §2.3 Read-Order-
  Constraint dokumentiert).
- **M-2**: `test_demo_scenario_telemetry_is_byte_identical_across_runs`
  prueft jetzt zusaetzlich, dass alle 5 MVP-Geraete-IDs in der
  Telemetry erscheinen und SmartMeter `aggregated_power_kw`
  emittiert. Schliesst Silent-Empty-Telemetry-Regression aus.
- **M-3**: Neuer Test
  `test_yaml_loader_allowlist.py` scannt
  `dataclasses.fields(BatteryConfig|PvConfig|LoadConfig|
  GridConnectionConfig|SmartMeterConfig)` auf `Decimal`-Felder
  und verifiziert Coverage in `_DEVICE_DECIMAL_PARAMS`
  (Drift-Detection). Bonus: Orphan-Eintraege-Pruefung.
- **M-4**: `_coerce_device`/`_coerce_load_event`/
  `_coerce_load_profile` werfen jetzt keinen opaken
  `ValueError` mehr bei Non-Mapping-Inputs — sie reichen
  unveraendert durch, der Scenario-Validator wirft den
  typisierten `ScenarioWrongTypeError`.

**Low (6):**

- **L-1**: §2.5 + §3 listen jetzt explizit ADR 0015 **und**
  ADR 0021 als gehobene ADRs.
- **L-2**: §4.C1.4-Beschreibung sagt jetzt „hardcoded ISO-8601-
  UTC-Strings" statt „aus FakeClock"; §6-Bezug auf FakeClock
  klargestellt (`ClockPort` im `build_tick_loop`, **nicht**
  fuer `started_at`/`ended_at`).
- **L-3**: `DEMO_TOOL_VERSION` kommt jetzt aus
  `importlib.metadata.version("grid-gym")` statt hardcoded
  `"0.1.0"` — synct mit `pyproject.toml`-Bumps.
- **L-4**: §4.C1.1-Verweis auf `test_loader_welle_6b.py`
  zeigt jetzt auf Funktions-Referenz (`_minimal_raw_mapping`
  bzw. `_grid_model_config`), nicht mehr auf einen
  drift-anfaelligen Zeilenbereich.
- **L-5**: Permutations-Property-Test laeuft jetzt mit
  `max_examples=50` statt 25 — deckt alle 4!=24
  Permutationen statistisch ueberzeugend ab.
- **L-6**: `repository`-Fixture in `conftest.py` zentralisiert
  (war in beiden Test-Modulen dupliziert).

**Note (N1–N5):** keine Action-Items, nur Observations
(Image-Pin per Digest, YAML-Doppelload, Status-Block-Pattern)
— in `open/` getriggert, wenn relevant.

### C4 — `fix(welle-6c)`: Review-Folge-2 (User-Cross-Check)

Nach C3-Review-Folge hat ein User-Cross-Check (Spec ↔ Implementation,
keine Test-Ausfuehrung) drei zusaetzliche Findings entdeckt — alle
durch fehlende Synchronisation zwischen Welle-6c-Dokumentation
und tatsaechlich gelieferter Implementation entstanden. Schaerfung-
Pattern, keine Supersede-ADR.

- **M-5 (Medium): Roadmap-DoD-Checkboxen-vs-welle-6c.md-Drift**.
  welle-6c.md §4.C2 hat „Roadmap-DoD-Checkboxen final markieren"
  versprochen, der C2-Commit `6adb041` hat aber nur die Status-
  Zeile (Z. 124–127) editiert, nicht die DoD-Liste. Vier DoDs
  sind durch Welle 4/6a faktisch erledigt und wurden in C4
  nachgereicht: SmartMeter (Welle 4b `94efb2a`, ADR 0018),
  GridConnection (Welle 4a `b73b44a`, ADR 0017), TickLoop-
  Deterministische-Order (Welle 6a `27a441f` + 6c Permutations-
  Property-Test), Snapshot-Sub-Snapshots (Welle 6a, ADR 0015).
  M2-Status bleibt absichtlich `In Progress` — Closure-Flip
  erfolgt mit Welle 7 (M2-Closure-Trigger laut
  `M2-devices.md §6`). Plus Fix der veralteten Klammer
  „(ADR 0017 noch nicht erstellt)" am SmartMeter-Item — SmartMeter
  liegt in ADR 0018, ADR 0017 ist GridConnection (beide `Accepted`).
- **L-7 (Low): Feldnamen-Drift welle-6c.md ↔ Validator/Loader**.
  welle-6c.md §4.C1.1 referenzierte `grid_model_config` als
  YAML-Block-Name; korrekt ist der YAML/Validator-Schluessel
  `grid_model` (der Loader parst ihn zu
  `Scenario.grid_model_config: GridModelConfig | None`).
  Analog war `load_profiles[*].points[*].value` falsch — der
  Validator/Loader nutzt `load_profiles[*].tick_values` als
  Decimal-Liste. Korrigiert in §4.C1.1 + §4.C1.3.
- **L-8 (Low): `DEMO_TOOL_VERSION`-Robustness**. C3 hatte
  `importlib.metadata.version("grid-gym")` direkt zur Importzeit
  aufgerufen. In Runnern ohne installierte Distribution (z. B.
  Ad-hoc-`pytest` ohne `uv sync`) waere das Modul mit
  `PackageNotFoundError` gebrochen. C4 wrappt den Aufruf in
  `try/except` mit Sentinel-Fallback
  `"0.0.0+local"` — die produktive Docker-Test-Stage ruft
  weiterhin `uv sync` und sieht die reale Version.

Damit ist der Welle-6c-Block dokumentations-konsistent zum
Welle-7-Closure-Slice.

## 5. Critical Files to Modify/Create

| Pfad                                                                       | Commit | Aktion |
| -------------------------------------------------------------------------- | ------ | ------ |
| `docs/plan/planning/in-progress/welle-6c.md`                               | C0     | NEU    |
| `tests/integration/scenarios/mvp_demo.yaml`                                | C1     | NEU    |
| `tests/integration/_constants.py`                                          | C1     | NEU    |
| `tests/integration/_yaml_scenario_loader.py`                               | C1     | NEU    |
| `tests/integration/conftest.py`                                            | C1     | NEU    |
| `tests/integration/test_mvp_demo_scenario.py`                              | C1     | NEU    |
| `tests/integration/test_postgres_run_repository.py`                        | C1     | EDIT (Fixture ziehen) |
| `tests/unit/hexagon/core/simulation/test_scenario_permutation.py`          | C1     | NEU    |
| `docs/plan/adr/0015-snapshot-envelope-v2.md`                               | C2     | EDIT   |
| `docs/plan/adr/README.md`                                                  | C2     | EDIT   |
| `docs/plan/planning/in-progress/M2-devices.md`                             | C2     | EDIT   |
| `docs/plan/planning/in-progress/README.md`                                 | C2     | EDIT   |
| `docs/plan/planning/in-progress/roadmap.md`                                | C2     | EDIT   |
| `docs/plan/planning/in-progress/welle-6c.md`                               | C2     | EDIT (Status-Header) |
| `tests/unit/hexagon/core/simulation/test_scenario_permutation.py`          | C3     | EDIT (M-1 + L-5: SmartMeter + max_examples=50) |
| `tests/integration/test_mvp_demo_scenario.py`                              | C3     | EDIT (M-2: Positiv-Assertion + L-6: Fixture-Move) |
| `tests/integration/_yaml_scenario_loader.py`                               | C3     | EDIT (M-4: typed-error guards) |
| `tests/integration/test_yaml_loader_allowlist.py`                          | C3     | NEU (M-3: Allowlist-Drift-Detection) |
| `tests/integration/_constants.py`                                          | C3     | EDIT (L-3: importlib.metadata.version) |
| `tests/integration/conftest.py`                                            | C3     | EDIT (L-6: `repository`-Fixture zentralisiert) |
| `tests/integration/test_postgres_run_repository.py`                        | C3     | EDIT (L-6: lokale Fixture entfernt) |
| `docs/plan/planning/in-progress/welle-6c.md`                               | C3     | EDIT (Status + §4.C3 Review-Folge + Tabelle + §7 Tests-Count) |
| `docs/plan/planning/in-progress/roadmap.md`                                | C4     | EDIT (M-5: 4 DoD-Checkboxen `[ ]`→`[x]`, SmartMeter-ADR-Korrektur) |
| `docs/plan/planning/in-progress/welle-6c.md`                               | C4     | EDIT (L-7: Feldnamen `grid_model`/`tick_values` + §4.C4) |
| `tests/integration/_constants.py`                                          | C4     | EDIT (L-8: `try/except PackageNotFoundError` + Sentinel-Fallback) |

## 6. Bestehender Code zur Wiederverwendung

- `load_scenario(raw)` und `build_tick_loop(...)` aus
  `src/grid_gym/hexagon/core/scenario/loader.py:86,343`.
- `LoadedScenario` mit `scenario_hash`-Feld
  (`loader.py:73,83`).
- `RunMetadata` + `PostgresRunRepository.save/get_by_id` aus
  `src/grid_gym/adapters/driven/persistence_postgres/run_repository.py:55,87`.
- `postgres_dsn`-Fixture-Pattern aus
  `tests/integration/test_postgres_run_repository.py:33–60`
  (mit Alembic-Upgrade-Helper).
- Hypothesis-Permutation-Pattern aus
  `tests/unit/hexagon/core/simulation/test_scheduler.py:149–208`.
- `MersenneTwisterRandomPort(seed=…)` aus
  `src/grid_gym/adapters/driven/random_mt/mersenne_twister.py`.
- `FakeClock` (M1) als `ClockPort` im `build_tick_loop(...)`-
  Aufruf (nicht fuer `RunMetadata.started_at`/`ended_at`; diese
  sind hardcoded ISO-Strings im Test).

## 7. Verifikationspfad — alle Items erfuellt (2026-05-20)

End-to-End ueber `make`-Targets (Dockerfile-Stages, Docker-only
nach Repo-Konvention):

1. **`make test-unit`** — gruen, **762 Tests** (+1 ggue. Welle 6b)
   inkl. `test_scenario_permutation.py` (50 Hypothesis-Beispiele
   nach C3-Review-Folge, vorher 25).
2. **`make test-integration`** — gruen, **9 Tests** (+4 ggue.
   Welle 6b: 2 in C1 = `test_mvp_demo_scenario.py`, 2 in C3 =
   `test_yaml_loader_allowlist.py`):
   - byte-identische `emitted_telemetry` ueber 100 Ticks;
   - `runs`-Row roundtrip durch ephemeren Postgres-Sibling-
     Container.
3. **`make gates`** (Default `CRITICAL_COV_TARGETS`) — gruen
   ohne Override. Default-Liste unveraendert.
4. **`make fullbuild`** — gruen **ohne jeden Override**
   (`/health: ok`). M2-Welle-6c-Abschluss-Gate aus
   `M2-devices.md §3` Zeile 1230 + §7 Tabelle erfuellt.
5. **ADR-0015-Status** sichtbar `Accepted` (`docs/plan/adr/0015-snapshot-envelope-v2.md`
   Zeile 3). Zusaetzlich ADR 0021 auf `Accepted` gehoben (Welle-6b-
   Closure-Folgeerwartung, siehe `93f784f`-Commit-Body).
6. **Git-Pattern**: fuenf neue Welle-6c-Commits in der Reihenfolge
   `docs(plan): welle-6c Slice-Doc (C0)` →
   `feat(welle-6c): ... (C1)` →
   `docs(plan): Welle-6c Status/DoD-Sync (C2)` →
   `fix(welle-6c): Review-Folge (C3, M+L Findings)` →
   `fix(welle-6c): Review-Folge-2 (C4, User-Cross-Check)`.
   `git log --oneline -5` zeigt diese fuenf Hashes als juengste
   Commits.

## 8. Risiken & Fallback

- **Float-Praezision in YAML**: Mitigation durch Decimal-Strings
  + Helper-Coercion. Falls ein YAML-Wert versehentlich als float
  geparst wird, faengt `Decimal(str(value))` das ab, aber wir
  konvertieren bewusst nur von `str`, nicht von `float`, um
  Praezisionsverluste fail-fast zu machen.
- **Hypothesis-Laufzeit**: 50 Beispiele × 20 Ticks × 5 Geraete
  ist konservativ; falls > 60 s in CI, `max_examples=25`
  reduzieren (kein Welle-Split-Trigger, bleibt 6c).
- **Postgres-Container-Spawnzeit**: testcontainers braucht
  bereits `~5 s` fuer den Image-Pull beim ersten Lauf — kein
  neuer Stress, da existing Integrationstest dasselbe macht.
- **Sub-Slicing-Schwelle (`M2-devices.md §3`)**: Welle 6c hat
  4 Liefergegenstaende, aber alle haengen am gleichen Modulset
  (`core/scenario` + bestehende Postgres-Adapter). Schwelle
  greift nicht. **Fallback** bei rotem Integrationstest:
  Welle 6c/6d trennen (6c = YAML + Property-Test + Closure;
  6d = Postgres-Roundtrip). Dokumentiert hier; wird nicht
  praeventiv ausgeloest.

## 9. Wandert nach

- `done/` mit Welle-7-Closure (analog `M2-devices.md §6`).
- Bei umgeplantem M2 (z. B. vorgezogenes M3 wegen Audit-Befund):
  `archive/`-Pfad. Bisher kein Anlass.
