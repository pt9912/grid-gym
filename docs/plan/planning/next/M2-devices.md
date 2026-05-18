# Slice-Plan — M2 Geraetemodelle — Next

**Status:** Next — Scope skizziert, Welle 0 noch nicht gestartet.
Naechster aktiver Slice nach M1-Closure (2026-05-17). M1-Spine
(`Tick-Loop`, `Scheduler`, `RandomPort`, `ClockPort`, Scenario,
Replay, FastAPI-Adapter, Postgres-Persistenz) liegt; M2 fuellt
den bisher leeren `hexagon/core/devices/`-Slot mit den MVP-
Geraetemodellen `battery`, `pv`, `load`, `smart_meter`,
`grid_connection` und macht `TickResult.emitted_telemetry`
produktiv.
**Datum:** 2026-05-18 (in `next/` eroeffnet).
**Bezug:**
- [`roadmap.md`](../in-progress/roadmap.md) §3 M2 (Vorbelegung,
  „Naechster aktiver Slice: M2").
- M1-Closure-Notiz
  [`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md)
  + Ergebnisse
  [`done/M1-tick-loop-results.md`](../done/M1-tick-loop-results.md)
  §7 (Welle-7-End-to-End-Sweep, S-1..S-6).
- [`ADR 0002`](../../adr/0002-language-and-build-stack.md)
  §A-1 (`AC-HEXAGON-PURE`, `AC-PORTS-NO-OUT`, `AC-DOMAIN-FROZEN`).
- [`ADR 0007`](../../adr/0007-random-port.md) §5 (`RandomPort.
  sub_port`-Konvention fuer Geraete-Fault-Streams).
- [`ADR 0010`](../../adr/0010-randomport-snapshot-as-mapping.md)
  (`RandomPort.snapshot_as_mapping`-Composition-API — Geraete-
  Sub-Snapshots koppeln hier rein).
- Lastenheft §9 (`GG-DEV-001..018`), §10 (`GG-BESS-001..008`),
  §11 (`GG-GRID-001..007`), §3 (`GG-MVP-002`: End-to-End-
  Szenario mit Netzanschluss/PV/Load/Smart-Meter/Battery).
- Open-Triggers
  [`open/013-replay-diff-tick-ms-parameter.md`](../open/013-replay-diff-tick-ms-parameter.md),
  [`open/014-generic-snapshot-format-codec.md`](../open/014-generic-snapshot-format-codec.md),
  [`open/015-runtime-image-hardening.md`](../open/015-runtime-image-hardening.md).

---

## 1. Zweck

M2 liefert die **produktiven Geraetemodelle** als
Konsumenten des M1-Tick-Loops:

- `DeviceModel`-Vertrag (`GG-DEV-001`) mit `initialize`/`tick`/
  `apply_command`/`snapshot`/`telemetry` als Protocol,
- die MVP-Geraete `battery`, `pv`, `load`, `smart_meter`,
  `grid_connection` unter `hexagon/core/devices/<typ>/`
  (`GG-DEV-010..014`, `GG-MVP-002`-Pflicht; deckt sich mit
  `GG-AR-COMP-DEVICES`-Geraeteliste in `spec/architecture.md`
  §5),
- Batteriemodell mit SOC, Lade-/Entlade-Grenzen, Wirkungsgraden,
  Ramp-Limits, Sicherheitsgrenzen, Initialvalidierung
  (`GG-BESS-001..005`/`008`),
- vereinfachtes **Netzbilanzmodell** unter
  `hexagon/core/grid_model/` (**nicht** unter `devices/`, weil
  `GG-AR-COMP-DEVICES` §5 das Modell nicht als Geraet listet;
  systemweite Bilanz ist eine Tick-Loop-Verantwortung neben
  dem Geraete-Tick) mit Frequenz-/Spannungs-/Lastpfaden
  (`GG-GRID-001..004`),
- `TickResult.emitted_telemetry` befuellt mit deterministisch
  sortierten `TelemetryPoint`-Tupeln pro Tick,
- Geraete-Sub-Snapshots in `SnapshotEnvelope`-Composition
  (via Trigger 014 generalisierter Snapshot-Codec).

M2 schliesst zugleich die **drei Welle-7-Erbschafts-Triggers**
ab, die als „M2-Welle-0-Pflicht-Aktivierung" markiert sind
(siehe `done/M1-tick-loop-results.md` §7):

- Trigger 014 (`generic-snapshot-format-codec`) — sechstes
  Subsystem (`devices/battery`-Validierung) loest die
  Generalisierung mechanisch aus.
- Trigger 015 (`runtime-image-hardening`) — vor neuen Adaptern
  raeumen (`uv sync --no-editable`, Shebang-Rewrite, Base-Image-
  Patch-Strategie).
- Trigger 013 (`replay-diff-tick-ms-parameter`) — Welle 2
  enthaelt einen Battery-Property-Test mit `tick_ms=100`, der
  Trigger 013 ueber `diff_replay(..., tick_ms=100)` mechanisch
  schliesst. Das Demo-Szenario `mvp_demo.yaml` bleibt bei
  `tick_ms=1000` (M1-Konsistenz, siehe §3 Welle 2 und §3
  Welle 6).

**Fault Injection** (`GG-FAULT-001..010`), **Multi-Agent**
(`GG-AGENT-001..008`), **Protokolladapter** (MQTT/Modbus/OPC-UA/
DNP3/IEC) und **OTEL-Tracing** (`GG-OTEL-001..004`) bleiben
explizit out-of-scope — siehe §4. Sie sind M3/M4.

## 2. Erfolgskriterien

M2 ist erfolgreich, wenn:

1. **Default `make gates` ohne `CRITICAL_COV_TARGETS`-Override
   gruen** (S-3 aus M1-Welle-7-Sweep). Erfordert:
   - `src/grid_gym/hexagon/core/devices/battery/` ≥ 90 % Line +
     Branch — Default-`CRITICAL_COV_TARGETS` aus Dockerfile
     `coverage-gate-critical`-Stage (`hexagon/core/simulation
     devices/battery scenario replay`) faellt ohne Override
     durch.
   - kein Welle-Plan darf einen erweiterten `CRITICAL_COV_TARGETS=
     …`-Override als M2-Akzeptanz-Pfad eintragen; Override gilt
     nur als kurzfristiger Welle-Lokal-Krueck, niemals als
     M2-Abschluss-Gate.
2. **`make fullbuild` gruen** auf `main` ohne Welle-6d-Hack-
   Restposten:
   - `deploy/compose.yml` benutzt `uvicorn` und `alembic` direkt
     (kein `python -m`-Indirection),
   - `PYTHONPATH=/app/src`-Workaround und
     `apt-get upgrade -y`-Workaround sind entfernt
     (`uv sync --no-editable` + shebang-Rewrite oder Pip-Relocate,
     Base-Image-Patch-Strategie via Trigger 015).
3. **MVP-Demo-Szenario (`GG-MVP-002`) liegt im Repo**:
   `tests/integration/scenarios/mvp_demo.yaml` oder gleichwertig
   mit Netzanschluss + PV + Load + Smart Meter + Battery,
   deterministischem Smoke-Test (`make test-integration` startet
   das Szenario, verifiziert ≥ 1 Tick Live-Telemetrie).
4. **Determinismus-Property je Geraet**:
   - gleicher Seed + Scenario-Hash → byte-identische
     `TickResult.emitted_telemetry` ueber ≥ 100 Ticks.
   - `Battery.snapshot()` → `Battery.from_snapshot()` → Roundtrip
     produziert byte-identische Folge-Ticks (`GG-SIM-005`).
5. **Trigger-Abarbeitung**:
   - Trigger 014 (`generic-snapshot-format-codec`) nach `done/`
     mit generischer `SnapshotFormatError`-Basis und Aliasen fuer
     die bestehenden M1-Subklassen (Backward-Compat zu Welle-5-
     Tests).
   - Trigger 015 (`runtime-image-hardening`) nach `done/` mit
     dokumentiertem `Dockerfile`-`runtime`-Stage ohne Pragma-
     Hacks.
   - **Trigger 013** (`replay-diff-tick-ms-parameter`) nach
     `done/` — **Welle 2 ist verbindlich**, nicht „sobald
     irgendein Geraet". Closure-Anker ist der Battery-Pflicht-
     Test `tests/unit/hexagon/core/devices/battery/
     test_replay_diff_tick_ms.py` (`tick_ms=100`,
     `diff_replay(..., tick_ms=100)` byte-stabil; siehe §3
     Welle 2 „`tick_ms`-Konvention").
6. **`SnapshotEnvelope.sub_snapshots` enthaelt Geraete-Sub-
   Snapshots** mit `version: int`-Discriminator (ADR 0007/0010-
   Konvention auf Geraete uebertragen). **Pro-Geraet-Pflicht:**
   jede der fuenf MVP-Implementationen (`BatteryDevice`,
   `PvDevice`, `LoadDevice`, `SmartMeterDevice`,
   `GridConnectionDevice`) plus das Welle-5-Netzbilanzmodell
   liefern einen Snapshot-Roundtrip-Contract-Test
   (`from_snapshot(snapshot()) == device` byte-stabil) +
   `version: int`-Erst-Feld-Pruefung. Diese sechs Tests sind
   Welle-N-DoD-Items (siehe Welle 2..5); fehlt einer, ist die
   jeweilige Welle nicht abgeschlossen. Welle 6 verifiziert
   zusaetzlich, dass alle sechs Sub-Snapshots in
   `SnapshotEnvelope.sub_snapshots` zusammengefuehrt sind.
7. **Welle-7-S-1..S-6-Items adressiert**:
   - S-1 (Trigger 014) — Welle 0.
   - S-2 (Sub-Slicing-Heuristik) — §3 Praeambel dieses Plans,
     siehe „Sub-Slicing-Schwelle" unten.
   - S-3 (kein Override) — Erfolgskriterium 1.
   - S-4 (Trigger 015) — Welle 0.
   - S-5 (ADR-Erweiterungs-Pattern fortfuehren) — Welle 1/2
     liefern neue Domain-Form ⇒ neue Erweiterungs-ADR ohne
     Supersedes (z. B. ADR 0013 `DeviceModel`-Protocol, ADR 0014
     `Battery`-Snapshot-Schema).
   - S-6 (Lastenheft §6..§25 Coverage-Sweep) — Welle 0
     mechanisch durchdiffen, Restposten als neue Open-Triggers
     anlegen.

## 3. Liefer-Reihenfolge (Wellen)

**Sub-Slicing-Schwelle (S-2 aus M1-Welle-7-Sweep):** Eine Welle
wird **vor** dem Start in 2 oder mehr Sub-Wellen geteilt, wenn
mindestens eine der folgenden Schwellen erkennbar ist:

- Lieferung beruehrt mehr als ein Driving- *und* ein Driven-
  Adapter-Modul gleichzeitig (M1-Welle-6-Lehre: FastAPI +
  Postgres in einer Welle haben ungeplant in 6a/b/c/d zerfallen).
- DoD-Checkliste der Welle hat > 6 Items, von denen mindestens
  zwei auf unterschiedlichen `make`-Gates aufsetzen
  (`openapi-validate` vs. `test-integration` vs. `image-audit`).
- Welle muesste zwei `*FormatError`-Subsysteme gleichzeitig
  einfuehren (verschaerft Trigger 014).

Wird eine Schwelle nach Start sichtbar, ist Sub-Slicing der
Default — die Welle-Bezeichnung wandert von `Welle N` zu
`Welle Na/Nb/...` mit Eintrag in den Closure-Ergebnissen, **nicht
in diesem Plan rueckwirkend**. Dieser Plan dokumentiert
Welle 0..7 als Erwartungswert.

Wellen sind atomar; jede Welle endet mit einem gruenen Lauf
der bis dahin aktiven Gates (`make gates` — moeglichst ohne
Override, sonst mit explizitem Welle-lokalem
`CRITICAL_COV_TARGETS`).

### Welle 0 — Pflicht-Vorabraeumung (1 Tag)

Diese Welle leistet ausschliesslich Welle-7-Erbschafts-Arbeit
aus M1; **kein** Geraete-Code, **kein** Verbreitern der
Domain-Form.

- **S-1 / Trigger 014** (`generic-snapshot-format-codec`):
  - Refactor `hexagon/core/errors.py`: gemeinsame Basis
    `SnapshotFormatError(GridGymError, subsystem: str)` + Free-
    Functions `assert_required_keys`, `assert_int`,
    `assert_mapping`, `assert_payload_canonical_compatible`
    (siehe `open/014` §„Erwartete Lieferung" Schritt 1-5).
  - Alle fuenf bestehenden M1-`*SnapshotFormatError`-Subklassen
    bleiben als Alias erhalten (Welle-1..5-Tests muessen byte-
    identisch gruen bleiben).
  - `Scheduler._assert_payload_canonical` wird zur Free-Function
    `assert_payload_canonical_compatible` befoerdert und im
    Scenario-Loader nach dem strukturellen Validator aufgerufen
    (siehe Welle-5-Review MF-3).
- **S-4 / Trigger 015** (`runtime-image-hardening`):
  - `uv sync --no-editable` im `build-app`-Stage; entferne den
    `PYTHONPATH=/app/src`-Workaround aus `Dockerfile`
    `runtime`-Stage.
  - Shebang-Rewrite (`sed`-Loop) oder Pip-Relocate-Strategie,
    sodass `uvicorn`/`alembic` als direkte Binaries laufen.
  - `deploy/compose.yml` benutzt direkte Binary-Aufrufe (`uvicorn`,
    `alembic upgrade head`) statt `python -m`-Indirection;
    `entrypoint: []`-Hack faellt weg.
  - Base-Image-Patch-Strategie dokumentieren: entweder eigenes
    `grid-gym-base`-Image oder `--pull always` + `make
    rebase-base`-Routine. `apt-get upgrade -y` faellt im
    runtime-Stage weg (oder wandert in `make rebase-base`).
- **S-6 / Lastenheft-Sweep**:
  - `spec/lastenheft.md` §6..§25 mechanisch durchdiffen gegen
    M1-Implementierung; jede `GG-*`-ID ohne Implementierungs-
    Eintrag in `spec/lastenheft.md §27.2`
    (`GG-TRACE-001`-Matrix) bekommt entweder einen
    Implementierungs-Verweis (wenn bereits in M1 erfuellt) oder
    eine neue Open-Trigger-Notiz (z. B.
    `016-<short-name>.md`).
- **Tests** fuer Welle 0:
  - Welle-0-Tests sind reine Refactor-Tests — bestehende M1-Tests
    bleiben gruen, neue Generic-Codec-Tests (siehe Trigger 014)
    decken die Basis ab.
  - `make fullbuild` ohne Override-Hacks gruen (`PYTHONPATH=
    /app/src` weg, `apt-get upgrade -y` weg, `entrypoint: []` weg).
- **Gate-Status nach Welle 0**: `make fullbuild` gruen mit
  M1-Override-Liste (devices/battery noch leer — Default-Gate
  bleibt rot bis Welle 2). Trigger 014 nach `done/`,
  Trigger 015 nach `done/`.

### Welle 1 — `DeviceModel`-Protocol + Device-Domain (1/2 Tag)

- `src/grid_gym/hexagon/core/devices/_protocol.py` (oder
  `hexagon/ports/driving/device.py`, sobald entschieden):
  - `DeviceModel`-Protocol mit
    - `initialize(self, scenario_device: ScenarioDevice,
       random: RandomPort) -> None`,
    - `tick(self, context: DeviceTickContext) ->
       DeviceTickOutcome`,
    - `apply_command(self, command: Command) -> CommandResult`,
    - `snapshot(self) -> Mapping[str, object]` (mit
       `version: int`-Discriminator),
    - `telemetry(self) -> tuple[TelemetryPoint, ...]`.
  - `DeviceTickContext` + `DeviceTickOutcome` als Frozen-
    Dataclasses in `hexagon/core/domain/device.py`. Felder:
    `tick`, `simulation_time`, `tick_ms`, `pending_commands`,
    `random_sub_port` (vgl. ADR 0007 §5).
- ADR 0013 `DeviceModel`-Protocol (`Provisional` → `Accepted`
  synchron mit Welle 1-Merge); strikt nach ADR-0008+0011-
  Erweiterungs-Pattern, **kein** Supersedes.
- Tests:
  - `tests/unit/hexagon/core/devices/test_protocol_contract.py`
    — Protocol-Adherence-Test mit Test-Double (`NullDevice`),
    deckt das Protocol-Surface ab **inkl. der Pflichtpruefung,
    dass `device.snapshot()` ein Mapping mit `version: int` als
    Erst-Feld liefert** (ADR 0007/0010-Konvention auf Geraete
    uebertragen).
  - **Konvention fuer Folge-Wellen (Welle 2..5):** jede
    konkrete Geraete-Implementation (Battery, PV, Load,
    SmartMeter, GridConnection) wiederholt den Protocol-
    Adherence-Test mit ihrer eigenen Klasse als Parameter und
    prueft zusaetzlich `from_snapshot(snapshot()) == device`
    byte-stabil. Diese Pflicht ist Welle-N-DoD-Item und kein
    Welle-7-Restposten.
- **Gate-Status nach Welle 1**: erweiterter Override
  `CRITICAL_COV_TARGETS="… hexagon/core/devices"` gruen
  (Welle-0-Override-Liste erweitert um `devices`-Pfad ohne
  `battery`).

### Welle 2 — Battery (`GG-DEV-010` + `GG-BESS-001..005`/`008`) (2 Tage)

**Kritische Welle** — diese Welle macht das Default-Gate gruen.

- `src/grid_gym/hexagon/core/devices/battery/`:
  - `config.py` — `BatteryConfig` Frozen-Dataclass: `capacity_
    kwh`, `initial_soc_pct`, `min_soc_pct`, `max_soc_pct`,
    `max_charge_kw`, `max_discharge_kw`, `charge_efficiency`,
    `discharge_efficiency`, `ramp_kw_per_s`. Initial-Validator
    nach `GG-BESS-008`.
  - `model.py` — `BatteryDevice` implementiert `DeviceModel`-
    Protocol. SOC-Fortschreibung aus Leistung × Tick-Dauer ×
    Wirkungsgrad (`GG-BESS-001`/`003`). Ramp-Limits
    (`GG-BESS-004`). Sicherheitsgrenzen-Validierung
    (`GG-BESS-005`): unzulaessige SOC-/Leistung-/Temperatur-/
    Spannungswerte werden nicht in den naechsten Tick
    uebernommen.
  - `commands.py` — Command-Validator. Innerhalb-Grenzen-
    Power-Befehle bekommen `CommandResult.LIMITED` + Alarm
    (`GG-BESS-002`), Grenzwert-verletzende Befehle bekommen
    `CommandResult.REJECTED` + Alarm.
  - `snapshot.py` — `BatterySnapshot` Frozen-Dataclass +
    `from_snapshot` als classmethod, konsumiert generische
    `SnapshotFormatError`-Codec aus Welle 0.
- `BatteryDevice.telemetry()` liefert mindestens `soc_pct`,
  `soc_kwh`, `power_kw`, `command_status` als
  `TelemetryPoint`-Tupel (deterministisch nach Metrikname
  sortiert).
- **`tick_ms`-Konvention fuer Welle 2** (loest §1 / Trigger 013
  konkret aus):
  - Demo-Szenario `mvp_demo.yaml` (in Welle 6) faehrt mit
    `tick_ms=1000` (M1-Konsistenz, lesbar in CI).
  - **Welle-2-Pflicht-Test**:
    `tests/unit/hexagon/core/devices/battery/test_replay_diff_tick_ms.py`
    laeuft eine SOC-Spur mit `tick_ms=100` (10x feiner als M1-
    Default), exportiert die `TelemetryPoint`-Folge und
    vergleicht sie via `diff_replay(expected, actual,
    tick_ms=100)` byte-stabil — schliesst Trigger 013
    (`replay-diff-tick-ms-parameter`) mechanisch und ist
    Welle-2-DoD-Item.
- Tests:
  - Unit-Tests pro Akzeptanz-Kriterium `GG-BESS-001..005`/
    `008`. Determinismus-Property via
    `hypothesis @given(seed=integers(min_value=0))`: gleicher
    Seed + identische Command-Sequenz → byte-identische SOC-Spur
    ueber ≥ 100 Ticks.
  - Snapshot-Roundtrip-Test (Welle-1-Konvention):
    `BatteryDevice.snapshot()` → `BatteryDevice.from_snapshot()`
    produziert byte-identische Folge-Ticks; Snapshot-Mapping
    fuehrt `version: int` als Erst-Feld.
  - Trigger-013-Pflicht-Test (siehe `tick_ms`-Konvention oben).
  - Integration-Test fuegt `BatteryDevice` an den `TickLoop`
    an und fuellt `TickResult.emitted_telemetry` ueber 10 Ticks.
  - Negativ-Tests: ungueltige Config (`GG-BESS-008`),
    Command-Out-of-Range (`GG-BESS-002`), Safety-Limit-Verstoss
    (`GG-BESS-005`).
- **Gate-Status nach Welle 2**: **Default `make gates` ohne
  `CRITICAL_COV_TARGETS`-Override gruen** — `devices/battery` ≥
  90 % Line + Branch. Welle 2 ist der Punkt, ab dem M2-
  Erfolgskriterium 1 erreicht ist. Folgewellen duerfen den
  Default nicht wieder rot machen.

### Welle 3 — PV + Load (`GG-DEV-011`/`013`) (1 Tag)

- `hexagon/core/devices/pv/` + `hexagon/core/devices/load/`:
  - `PvDevice` mit Generationsprofil-Eingang (Zeitreihe oder
    konstanter Faktor; Welle 5 Replay-Pfad nutzt
    `csv`/`json`-Mapper aus M1-Welle 5).
  - `LoadDevice` mit Last-Profil-Eingang (konstant / Zeitreihe /
    Szenario-Event nach `GG-GRID-003`).
- Beide Geraete liefern Telemetry (`power_kw`, ggf.
  `forecast_kw`).
- Tests:
  - Smoke-Tests (`GG-DEV-011`/`013`-Akzeptanz: deterministischer
    Smoke; gleicher Seed + identisches Profil → byte-identische
    Telemetry **ueber ≥ 100 Ticks** — einheitlich mit
    Erfolgskriterium 4, kein Welle-lokaler Sondersatz).
  - **Protocol-Adherence-Test je Geraet** (Welle-1-Konvention):
    `PvDevice` und `LoadDevice` durchlaufen den Protocol-Test
    aus Welle 1 mit ihrer eigenen Klasse; `snapshot()`-Mapping
    fuehrt `version: int` als Erst-Feld, Snapshot-Roundtrip ist
    byte-stabil.
- Sub-Slicing-Check: wenn die Welle den PV-Generations- und
  den Load-Profil-Loader gleichzeitig anfasst (zwei neue
  Driving-Pfade), in 3a/3b teilen.
- **Gate-Status nach Welle 3**: Default-Gate bleibt gruen.

### Welle 4 — SmartMeter + GridConnection (`GG-DEV-012`/`014`) (1 Tag)

- `hexagon/core/devices/smart_meter/`:
  - `SmartMeterDevice` aggregiert Telemetry aus angeschlossenen
    Geraeten (PV/Load/Battery) nach `GG-DEV-014`-Akzeptanz.
- `hexagon/core/devices/grid_connection/`:
  - `GridConnectionDevice` als Anschlusspunkt mit
    Importsumme/Exportsumme (`GG-DEV-012`).
- Tests:
  - Smoke-Tests (`GG-DEV-012`/`014`-Akzeptanz: deterministischer
    Smoke; gleicher Seed + identische Eingaben → byte-identische
    Telemetry **ueber ≥ 100 Ticks** — einheitlich mit
    Erfolgskriterium 4).
  - **Protocol-Adherence-Test je Geraet** (Welle-1-Konvention):
    `SmartMeterDevice` und `GridConnectionDevice` mit `version:
    int`-Discriminator und byte-stabilem Snapshot-Roundtrip.
- **Gate-Status nach Welle 4**: Default-Gate bleibt gruen.

### Welle 5 — Netzbilanzmodell (`GG-GRID-001..004`) (1 Tag)

**Abgrenzung gegenueber Welle 4:** `grid_connection` aus
Welle 4 ist ein **Geraetetyp** (`GG-DEV-012`,
`hexagon/core/devices/grid_connection/`). Das **Netzbilanzmodell**
hier ist *kein* Geraet — Bezeichnung und Pfad sind bewusst
verschieden, weil `GG-AR-COMP-DEVICES` §5 das Modell nicht als
Device listet und die Bilanz aggregiert ueber alle
Connection-Points laeuft. Welle 6 verdrahtet die zwei Schichten
ueber den TickLoop.

- `hexagon/core/grid_model/` (Top-Level neben `devices/`,
  `scenario/`, `replay/`):
  - `bilanz.py` — vereinfachtes Leistungsbilanzmodell
    (`GG-GRID-001`/`002`) leitet Frequenz-/Spannungsabweichungen
    aus Erzeugung, Last, Speicherleistung ab.
  - `loads.py` — `GG-GRID-003`/`004`: Lasten als konstant /
    Zeitreihe / Szenario-Event; Lastspruenge mit
    Start/Dauer/Leistung.
  - `snapshot.py` — `GridModelSnapshot` Frozen-Dataclass mit
    `version: int`-Erst-Feld + `from_snapshot` als classmethod,
    konsumiert generischen `SnapshotFormatError`-Codec aus
    Welle 0. Snapshot-Sub-Key in `SnapshotEnvelope.sub_snapshots`
    ist `grid_model` (Single-Instance, kein `devices.<id>`).
  - Annahmen, Grenzen und Parametrisierung in Docstrings +
    Lastenheft-Verweis.
- `GG-GRID-005..007` (SOLLTE: Inselnetz / Transformatorgrenzen /
  Blindleistung) bleiben **out-of-scope** fuer M2 (siehe §4),
  werden als eigene Open-Triggers angelegt, falls in Welle 0
  S-6-Sweep noch nicht erfasst.
- Tests:
  - Property-Tests fuer Leistungsbilanz via
    `hypothesis @given(seed=integers())`: Summe (Erzeugung −
    Last − Speicherleistung) ist deterministisch konsistent mit
    Frequenzabweichung und seed-stabil.
  - **Snapshot-Roundtrip-Contract-Test** (Welle-1-Konvention,
    auf das Bilanzmodell uebertragen, ohne `DeviceModel`-
    Protocol-Adherence-Test — das Bilanzmodell ist kein
    `DeviceModel`): `version: int` als Erst-Feld + byte-stabiler
    `from_snapshot(snapshot())`-Roundtrip ist Welle-5-DoD-Item
    (siehe Erfolgskriterium 6 „Pro-Geraet-Pflicht" — sechster
    Eintrag der Snapshot-Liste).
- **Gate-Status nach Welle 5**: Default-Gate bleibt gruen.

### Welle 6 — TickLoop-Integration + Scenario (1 Tag)

- `TickLoop.tick()`:
  - Geraete werden in stabiler Reihenfolge aufgerufen
    (Scenario-Device-Definitionsreihenfolge ⇒ kanonische
    Liste). Tie-Breaking-Vertrag dokumentiert in
    `hexagon/core/simulation/tick_loop.py`.
  - `TickResult.emitted_telemetry` ist befuellt mit
    deterministisch nach
    `(device_id, metric, sequence)` sortierten Tupeln.
- `TickLoop.snapshot()` haengt Sub-Snapshots in
  `SnapshotEnvelope.sub_snapshots` zusammen:
  - `devices.<device_id>` je Geraete-Instanz (Welle 2..4 plus
    PV/Load aus Welle 3),
  - `grid_model` (Single-Instance) aus Welle 5 — Schluessel ohne
    `devices.`-Praefix, weil `grid_model` kein Device ist.
  Welle 6 verifiziert, dass alle sechs Snapshot-Quellen aus
  Erfolgskriterium 6 zusammengefuehrt werden (5 Geraete +
  Bilanzmodell).
- `Scenario`-Loader (`hexagon/core/scenario/loader.py`) befuellt
  konkrete Geraete-Instanzen (`BatteryDevice`, etc.) aus den
  bisher nur als Mapping vorgehaltenen `ScenarioDevice`-
  Definitionen (`GG-SCN-001`).
- ADR 0014 `Battery`-Snapshot-Schema (`Provisional` → `Accepted`
  synchron mit Welle 6-Merge) — strikt nach ADR-Erweiterungs-
  Pattern, kein Supersedes.
- `tests/integration/scenarios/mvp_demo.yaml` als End-to-End-
  Szenario (`GG-MVP-002`-Pflicht) mit **`tick_ms=1000`** und
  einer eingefrorenen Seed-Konstante in den Test-Helfern
  (`M2_DEMO_SEED` in `tests/integration/_constants.py` oder
  Conftest, Wert z. B. `0xC0FFEE`). `make test-integration`
  startet das Szenario **zweimal** mit der gleichen Konstante
  und verifiziert byte-identische
  `TickResult.emitted_telemetry`-Folge ueber **mindestens 100
  Ticks** (einheitlich mit Erfolgskriterium 4) plus
  persistierte `runs`-Zeile. Zweite-Lauf-Pflicht schliesst die
  Reproduzierbarkeits-Spalte fuer CI-Audits.
- TickLoop-Geraete-Tick-Reihenfolge ist durch einen Property-
  Test gegen Permutation der `ScenarioDevice`-Eingabereihenfolge
  gesichert (analog Welle-3-Scheduler-Property aus M1).
- **SnapshotEnvelope-Versionsschritt v1 → v2** (loest F-2 aus
  Review-3): das Welle-6-Envelope-Mapping bekommt sechs neue
  Sub-Snapshot-Keys (`devices.<id>` x 5 + `grid_model`); das
  ist ein strukturierender Bruch zum M1-Welle-4-Envelope.
  `SnapshotEnvelope.version` wird in Welle 6 von `1` auf `2`
  gehoben.
  - **Pflicht-Verhalten:** `TickLoop.from_snapshot(envelope)`
    auf einem v1-Envelope wirft einen typisierten
    `SnapshotEnvelopeSchemaVersionError` (Subklasse der
    generischen `SnapshotFormatError`-Basis aus Welle 0) mit
    Klartext „Envelope-Version 1 wird in M2 nicht mehr
    gelesen; Lauf in M1 abgeschlossen oder Snapshot-Migrations-
    Slice abwarten (M6, `GG-PERSIST-*`)".
  - **Pflicht-Test:** `tests/unit/hexagon/core/simulation/
    test_snapshot_envelope_v1_to_v2.py` baut einen
    v1-Envelope (Welle-4-M1-Format) und erwartet den
    typisierten Fehler. Backward-Compat-Reader ist
    out-of-scope (M6 `GG-PERSIST-*`-Migrations-Slice).
- ADR 0015 `SnapshotEnvelope`-Versions-Bump v1 → v2
  (`Provisional` → `Accepted` synchron mit Welle 6-Merge):
  dokumentiert den Bruch, fixiert den typisierten Fehler-
  Vertrag, verweist auf M6 fuer Lese-Migrations-Pfade. Strikt
  nach ADR-Erweiterungs-Pattern, kein Supersedes.
- **Gate-Status nach Welle 6**: `make fullbuild` gruen ohne
  jeden Override.

### Welle 7 — Closure (1/2 Tag)

- ADR 0013 + ADR 0014 + ADR 0015 `Accepted` (wenn noch
  `Provisional`).
- Trigger 013 (`replay-diff-tick-ms-parameter`) ist bereits in
  Welle 2 mechanisch geschlossen (siehe Battery-Pflicht-Test
  `test_replay_diff_tick_ms.py`). Welle 7 verifiziert nur, dass
  die Closure-Notiz in `done/013-…md` liegt; faellt sonst aus.
- `done/M2-devices.md` Closure-Notiz + `done/M2-devices-results.md`
  Welle-Tabelle analog `done/M1-tick-loop-results.md`.
- `roadmap.md`: M2 auf `Done`, M2-DoD-Checkboxen
  aktivieren, `Naechster aktiver Slice: M3` setzen.
- Out-of-Scope-Restposten als Open-Triggers vermerkt:
  `GG-DEV-015..018` (SOLLTE-Geraete: EV-Charger,
  Transformer, Wind, Diesel), `GG-GRID-005..007`
  (SOLLTE-Netz: Inselnetz, Transformatorgrenzen, Blindleistung),
  `GG-BESS-006`/`007` (SOLLTE-Battery: Temperatur, Zellspannung).
- M2-Welle-7-End-to-End-Sweep (analog M1-Welle-7 §7): Reviewer-
  Stempel je Welle, S-1..S-6-Verification ist Pflicht-Punkt.

## 4. Out-of-Scope (bleibt fuer M3+ oder eigene Triggers)

- **Fault Injection** (`GG-FAULT-001..010`) — M3. Geraete-
  Schnittstelle (z. B. `BatteryDevice.inject_fault(...)`) wird
  in M2 *nicht* praeventiv vorgesehen; `RandomPort.sub_port`-
  Konvention reicht fuer M3-Aktivierung.
- **Multi-Agent-Subsystem** (`GG-AGENT-001..008`) — M3.
- **OpenTelemetry-Tracing** (`GG-OTEL-001..004`) — M3.
- **Protokolladapter** (MQTT/Modbus/OPC-UA/DNP3/IEC) — M4.
- **UI / Demo-Seite** (`GG-UI-001..009`, Demo-System aus §24) —
  M5. M2 liefert nur das Demo-*Szenario* (`mvp_demo.yaml`), nicht
  die Demo-Seite.
- **SOLLTE-Geraete** `GG-DEV-015..018` (EV-Charger, Transformer,
  Wind, Diesel) — eigene Slices nach M2-Closure.
- **SOLLTE-Netz** `GG-GRID-005..007` (Inselnetz,
  Transformatorgrenzen, Blindleistung) — eigene Slices.
- **SOLLTE-Battery** `GG-BESS-006`/`007` (Temperatur,
  Zellspannung) — Trigger nach M2-Closure (Telemetry-Metriken-
  Erweiterung ist additiv und kann jederzeit folgen).
- **Performance-Benchmarks** (`GG-RT-004`/`005`) — M6.
- **SBOM-Generierung** (Trigger 008) — M6.

## 5. Risiken und Fallback

- **Trigger-014-Refactor brennt Welle-0**: die Generalisierung
  von fuenf `*SnapshotFormatError`-Hierarchien gleichzeitig kann
  Welle-1..5-Tests rot machen, wenn ein Alias falsch
  weiter-verdrahtet ist. *Fallback:* Welle 0 in 0a (Codec-Basis +
  Aliase) und 0b (Free-Function-Migration) teilen — siehe
  Sub-Slicing-Schwelle in §3.
- **Trigger-015-Image-Refactor verlangsamt CI**: `uv sync
  --no-editable` baut Wheels statt Editable-Links — moeglicher-
  weise spuerbar laenger. *Fallback:* Build-Cache-Layer im
  Dockerfile-Stage einziehen, ggf. `--mount=type=cache`. Falls
  zu invasiv: Trigger 015 in 0b (Shebang-Rewrite only) und 0c
  (Base-Image-Strategie) teilen.
- **Default-Gate-Sprung in Welle 2 verfehlt**: wenn `devices/
  battery` < 90 % Coverage erreicht, M2-Welle-2-Closure muss in
  2a/2b/2c aufgespalten werden bis Default-Gate gruen. Niemals
  M1-Override-Pattern wiederholen (S-3-Direktive).
- **`DeviceModel`-Protocol vs. Driving-Port-Wahl unklar**:
  Welle 1 muss entscheiden, ob `DeviceModel` als
  `hexagon/core/devices/_protocol.py` (Core-internes Protocol)
  oder als `hexagon/ports/driving/device.py` (Driving-Port)
  liegt. *Fallback:* die Welle-1-PR entscheidet via ADR 0013;
  `AC-HEXAGON-PURE` und `AC-PORTS-NO-OUT` schliessen Driven-
  Port aus.
- **Demo-Szenario hat keinen UI-Konsumenten in M2**: `GG-MVP-002`
  verlangt Live-Telemetrie ueber API. *Fallback:* M2-Demo-
  Verifikation reicht ueber `make test-integration` + Postgres-
  Roundtrip; UI-Konsum kommt mit M5.
- **`SnapshotEnvelope`-Sub-Snapshots brechen Welle-4-M1-Format**:
  Welle 6 erweitert das Envelope-Mapping um sechs neue Keys —
  fuenf unter `devices.<id>` plus einen `grid_model`-Single-
  Instance-Key. *Fallback:* der Bruch ist im Plan bereits als
  Pflicht-Schritt verankert (siehe Welle 6 „SnapshotEnvelope-
  Versionsschritt v1 → v2") — `SnapshotEnvelope.version`
  zaehlt auf `2` hoch, v1-Envelopes werfen typisierten
  `SnapshotEnvelopeSchemaVersionError` (Fail-Fast, kein
  Backward-Read). ADR 0015 fixiert den Vertrag; ein Lese-
  Migrations-Pfad ist explizit M6 (`GG-PERSIST-*`).
- **`grid_model` vs. `grid_connection` Naming-Drift**: das
  Bilanzmodell (Welle 5, `hexagon/core/grid_model/`) und der
  Geraetetyp `grid_connection` (Welle 4,
  `hexagon/core/devices/grid_connection/`) sind sprachlich nah,
  aber strukturell verschieden — Geraet vs. Systemmodell. Risiko:
  Code-Review mischt die beiden in Welle 4/5 versehentlich.
  *Fallback:* Welle 4 Code-Review-Checkliste enthaelt einen
  expliziten Punkt „`grid_connection` ist Device, `grid_model`
  ist Systemmodell — keine Cross-Imports". `AC-HEXAGON-PURE`
  faengt das nicht ab; nur Review/Naming-Disziplin schuetzt.

## 6. Wandert nach

- `in-progress/M2-devices.md`, sobald Welle 0 oder 1 startet.
- `done/M2-devices.md` mit Closure-Notiz nach Welle 7.
- Eventueller `archive/`-Pfad, falls M2 umgeplant wird (z. B.
  vorgezogenes M3 wegen Audit-Befund).

Forwarder-Stubs bleiben nur dann liegen, wenn `Accepted`-ADRs
auf den `next/`- oder `in-progress/`-Pfad zeigen (Immutability
nach ADR 0006 §3).

## 7. Verifikationspfad

| Erfolg                                                                       | Verifikation (Dockerfile-Stage via `make <target>`)                                                                                  |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Generischer Snapshot-Codec + Alias-Migration                                 | `make test-unit` mit bestehenden M1-`*SnapshotFormatError`-Tests gruen + neue Codec-Tests                                              |
| Trigger-015-Image-Hardening                                                  | `make fullbuild` ohne `PYTHONPATH`/`apt-get upgrade`/`entrypoint: []`-Hack-Restposten                                                  |
| `DeviceModel`-Protocol-Contract                                              | `make test-unit` mit Protocol-Adherence-Test (`NullDevice`)                                                                          |
| Battery-Akzeptanz (`GG-BESS-001..005`/`008`)                                  | `make test-unit` + `hypothesis @given(seed=integers())`-Property (seed-stabile SOC-Spur ueber ≥ 100 Ticks)                            |
| **Default `make gates` ohne `CRITICAL_COV_TARGETS`-Override gruen**          | `make gates` (Default-Liste aus Dockerfile-Default; `devices/battery` ≥ 90 %)                                                         |
| PV/Load/SmartMeter/GridConnection-Smoke-Tests                                | `make test-unit` (`GG-DEV-011..014` Akzeptanz)                                                                                       |
| `DeviceModel`-Snapshot-Versionierung pro Geraet (5 Stueck)                    | `make test-unit` Protocol-Adherence-Test je Geraet (`BatteryDevice`, `PvDevice`, `LoadDevice`, `SmartMeterDevice`, `GridConnectionDevice` — jeweils `version: int`-Erst-Feld + `from_snapshot(snapshot()) == device` byte-stabil) |
| `grid_model`-Snapshot-Versionierung                                          | `make test-unit` Snapshot-Roundtrip-Test `GridModelSnapshot` (`version: int`-Erst-Feld + byte-stabiler Roundtrip; **kein** Protocol-Adherence-Test, da kein `DeviceModel`) |
| Netzbilanz-Determinismus                                                     | `make test-unit` Property-Test via `hypothesis @given(seed=integers())` (seed-stabile Leistungsbilanz vs. Frequenz)                  |
| Demo-Szenario `mvp_demo.yaml` deterministisch                                | `make test-integration` mit `mvp_demo.yaml` (`tick_ms=1000`, Seed-Konstante `M2_DEMO_SEED`); zweifacher Lauf → byte-identische `emitted_telemetry` **ueber ≥ 100 Ticks**; Postgres-Roundtrip |
| SnapshotEnvelope v1 → v2 Schema-Bump (Fail-Fast)                              | `make test-unit` mit `test_snapshot_envelope_v1_to_v2.py` — v1-Envelope wirft typisierten `SnapshotEnvelopeSchemaVersionError`         |
| `make fullbuild` gruen ohne Override                                         | `make fullbuild` — **M2-Abschluss-Gate**                                                                                              |
| Trigger 013 (`replay-diff-tick-ms-parameter`) geschlossen                    | `make test-unit` mit Battery-Pflicht-Test `test_replay_diff_tick_ms.py` (`tick_ms=100`, `diff_replay(..., tick_ms=100)`)             |
| Trigger 014 + 015 nach `done/`                                                | `docs/plan/planning/done/014-…md`, `015-…md` mit Closure-Notiz                                                                       |
| Trigger 013 nach `done/`                                                      | `docs/plan/planning/done/013-…md` mit Closure-Notiz (synchron mit Battery-Welle-2-Test oben)                                          |
| ADR 0013 (`DeviceModel`) + ADR 0014 (`Battery`-Snapshot-Schema) + ADR 0015 (Envelope v1→v2) `Accepted` | `docs/plan/adr/0013-device-model-protocol.md`, `docs/plan/adr/0014-battery-snapshot-schema.md`, `docs/plan/adr/0015-snapshot-envelope-v2.md` mit `Accepted`-Status |
