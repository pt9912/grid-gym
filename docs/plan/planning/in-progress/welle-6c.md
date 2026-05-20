# Welle 6c — MVP-Demo-Szenario + E2E-Tests + Welle-6-Closure

**Status:** In Progress — Slice-Begleit-Dokument angelegt
2026-05-20. Welle-6-Closure-Slice, schliesst die Wellen-Reihe
6a (`27a441f`) + 6b (`0f1c597` + `93f784f`) ab. Kanonische
Slice-Spezifikation: `M2-devices.md §3 Welle 6c`
(Zeile 1205–1231) — dieses Dokument ist lesefreundlicher Index
+ per-Welle-Tracking, nicht Ersatz.

**Spec-Reife:** Inhaltlich final (Liefergegenstaende §4.C1,
Verifikation §7, Risiken §8). Das `Status:`-Feld oben spiegelt
ausschliesslich den **Umsetzungs-Fortschritt**, nicht den Reife-
grad der Spezifikation. Welle-Closure (C2) aktualisiert den
Header auf `Done` und ersetzt die `<…-Commit-Hash>`-Platzhalter
in §4.C2 / §7 durch die realen Hashes aus C1 und C2.

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
5. Welle-6-Closure-Doc-Sync: ADR 0015 → `Accepted`,
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

Welle 6c bringt **keine neue ADR**. Hebt ADR 0015 (Snapshot-
Envelope v2, `Provisional` seit Welle 6a) auf `Accepted`. Die
v1→v2-Implementation und der typisierte
`TickLoopSnapshotVersionError` sind seit Welle 6a aktiv
(`src/grid_gym/hexagon/core/simulation/tick_loop.py:74,517,562`
+ `tests/unit/hexagon/core/simulation/test_snapshot_envelope_v1_to_v2.py`).

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
   - `grid_model_config` mit den 8 Decimal-Feldern (siehe
     `_minimal_raw_mapping` in
     `tests/unit/.../test_loader_welle_6b.py:399–416`)
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
   `_coerce_decimals` macht eine **schema-bewusste** Konvertierung:
   `simulation.tick_ms/duration_s/seed` bleiben `int`; in
   `devices[*].params.*`, `grid_model_config.*`,
   `load_events[*].power_kw`, `load_profiles[*].points[*].value`
   wird `str` → `Decimal(str_value)` umgewandelt. Underscore-
   Prefix verhindert pytest-Collection.

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
     `started_at`/`ended_at` aus `FakeClock`, `tool_version` aus
     einer Konstante) ueber `PostgresRunRepository.save(...)`,
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
   (Zeilen 122–166): DoD-Checkboxen final markieren; Welle-
   Tabelle in M2-Zeile auf 6 von 7 (Welle 7 offen).
6. **`docs/plan/planning/in-progress/welle-6c.md`** — Status-
   Header von `In Progress` auf `Done — Welle 6 abgeschlossen
   am 2026-05-20 mit <C1-Commit-Hash> + <C2-Commit-Hash>` ziehen;
   Verifikationspfad als „erfuellt" markieren.

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
- `FakeClock` (M1) fuer deterministisches `started_at`/`ended_at`.

## 7. Verifikationspfad

End-to-End ueber `make`-Targets (Dockerfile-Stages, Docker-only
nach Repo-Konvention):

1. **`make test-unit`** — gruen inkl. neuem
   `test_scenario_permutation.py`. Hypothesis braucht keine
   Postgres-Container; lauft in der `unit`-Stage.
2. **`make test-integration`** — gruen inkl. neuem
   `test_mvp_demo_scenario.py` (beide Tests):
   - byte-identische `emitted_telemetry` ueber ≥ 100 Ticks;
   - `runs`-Row roundtrip durch ephemeren Postgres-Sibling-
     Container.
3. **`make gates`** (Default `CRITICAL_COV_TARGETS`) — gruen
   ohne Override. Default-Liste bleibt unveraendert.
4. **`make fullbuild`** — gruen **ohne jeden Override**. Das ist
   das M2-Welle-6c-Abschluss-Gate laut `M2-devices.md §3`
   Zeile 1230 + §7 Tabelle „make fullbuild gruen ohne Override".
5. **ADR-0015-Status sichtbar `Accepted`**: nach C2-Commit
   `head` des ADR-Files manuell verifizieren.
6. **Git-Pattern**: drei neue Welle-6c-Commits in der Reihenfolge
   `docs(plan): welle-6c Slice-Doc (C0)` →
   `feat(welle-6c): ... (C1)` →
   `docs(plan): Welle-6c Status/DoD-Sync (C2)`. `git log --oneline -3`
   zeigt diese drei Hashes als juengste Commits. Der absolute
   Abstand zu `origin/main` haengt vom Push-Stand ab (Welle 6c
   addiert +3 zu dem, was schon `ahead` war) und wird hier
   bewusst nicht eingefroren.

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
