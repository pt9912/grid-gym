# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Multi-Run-Execution-Pfad geplant: NEU `ADR 0069` (`Provisional` nach S0; per-
  Run-Driver + Scenario-Store A1 + Replay-Konsumnaht) + `next/multi-run-execution-path.md`;
  entsperrt Slice 039 Phase B (der Run-Execution-Pfad war Anti-Scope). Slice 039
  als blocked-by markiert. `Accepted` folgt bei der Implementierungs-Closure
  (gates gruen). Reine Planungs-/Doku-Aenderung, kein Runtime-Delta.
- Harness-Baseline auf Kurs-Release `v1.2.0` re-gepinnt
  (`harness/conventions.md` Baseline + Quellen-URLs: `templates-v2`/`47af124`
  → `v1.2.0`/`0473cc55`) nach v1.2.0-Delta-Analyse — kein Inhaltskonflikt mit
  den Adaptionen `MR-000..005` (die konkrete Source-Precedence-Rangwahl bleibt
  laut v1.2.0 Repo-Sache). Reine Doku-Aktualisierung.
- Trigger-Watch 051 (Durchsetzungsschicht: Tool-Call-/Handoff-Gate) + 052
  (Carveout-Audit-Slice pro Welle + Werkzeug-Wahl-Trichter) unter
  `docs/plan/planning/open/` — zwei neue v1.2.0-Mechaniken als Folgearbeit
  verankert (nicht umgesetzt).
- Driver-unabhaengige Run-End-Naht fuer `TickLoop.finalize()` (ADR 0067,
  Slice 040, Trigger 040): NEU `run_session()`-Kontextmanager garantiert
  `finalize()` im `finally` fuer jeden Konsumenten (Headless-Runner ohne
  asyncio-Driver / Abnahme-CLI) + NEU `mark_run_failed()`/Partial-Run-
  Markierung — ein per Tick-Failure abgebrochener Lauf wird nicht mehr
  irrefuehrend als `diverged` gedifft (kein `replay_diff_status`,
  `partial_run`-Reject-Log). `DemoTickLoopDriver` finalisiert auf jedem
  Exit-Pfad (natuerliche Terminierung / Failure / Cancel) statt nur bei
  `stop()`. Additive Schaerfung von ADR 0049 §2.1 (ADR 0011).
- API-Replay-Bindung (ADR 0068, Slice 039 Phase A, Trigger 039): `POST /runs`
  nimmt ein optionales `replay_of: <run_id>`-Feld an und legt den Lauf als
  Replay des Referenzlaufs an; die Bindung wird persistent in
  `RunMetadata.replay_of` (nullable Postgres-Spalte, Migration
  `0003_add_replay_of`; InMemory automatisch) gehalten + in
  `RunCreateResponse`/`GET /runs/{id}` exponiert. Unbekannte Referenz → HTTP
  422 `reference_run_not_found` (Reject vor Lauf-Start). Additive Schaerfung
  von ADR 0049 §2.2 (ADR 0011). (Phase B: `finalize()`-Konsum der
  persistierten Bindung — Folge-Schritt.)
- `docs/plan/planning/done-archive/` — eingefrorene
  Detail-Historie abgeschlossener Meilensteine (91 Wellen-/
  Slice-/Trigger-Docs per Move; `done/` haelt dauerhaft die
  `M*-results.md` + die in-flight-Artefakte des aktiven
  Meilensteins). `docs/archive/` materialisiert (war seit
  ADR 0001 versprochen).
- d-check-Module `ids` (Linkpflicht fuer Kennungen
  `GG-*`/`GG-AR-*`/`AC-*`/`ADR NNNN` inkl. Familien-Wildcards)
  und `codepaths` (Pfade in Inline-Code) produktiv in
  `.d-check.yml` — moeglich durch d-check v0.3.0
  `<modul>.scope` (Change Request dieses Repos). Ausnahmen nur
  eingefrorene Historie (`done-archive/**`, `CHANGELOG.md`).
- Trigger 043 (ids-Linkpflicht) aufgeloest; NEU Trigger 044
  (Linkpflicht auch fuer Inline-Code-Kennungen; wartet auf
  d-check-`inline-code`-Option, CR #3).
- d-check-Modul `matrix` (Referenzrichtungs-Gate, SDP) produktiv
  in `.d-check.yml` (Trigger 048 Resolved / Slice 049, Option A
  Voll-SDP): Stabilitaets-Rang Vertrag › Technik › Sicht › ADR ›
  Slice; Abwaerts-Verweise im bindenden Spec-Text + Verweise auf
  inaktive ADRs sind `make docs-check`-Befunde. Die Spec-Straten
  (`spec/lastenheft.md`/`protocol_profiles.md`/`architecture.md`)
  sind zeitlos umgebaut: **kein** Status/Welle/ADR-Bezug/Decision-
  Prozess im Body, Provenance je Datei unter ausgenommener
  `## Historie`-Sektion (bzw. Traceability-Matrizen via
  `exclude-sections`); Aufwaerts-Refs (`GG-*`/`GG-AR-*`) verlinkt.
  `ADR 0004`-Bezug bereinigt (redundanter `ADR 0003`-Link).
  `AGENTS.md` §2.5 nachgezogen.
- d-check **v0.11.0** gepinnt (`D_CHECK_IMAGE`-Digest) + `matrix`-
  Supersede-Lineage-Carve-out aktiviert (`allow-supersede-lineage` +
  `supersede-fields: [Supersedes, Aenderungstyp]`, Trigger 050 Resolved):
  die abloesende ADR darf ihre abgeloeste verlinken — `ADR 0006`-Bezug auf
  `ADR 0003` wieder als klickbarer Link (Inline-Code-Workaround entfernt).
  Boundary verifiziert: Nicht-Lineage-Verweise auf inaktive ADRs bleiben
  `matrix-inactive`.
- `harness/conventions.md` (NEU) — formale Adoption des
  AI-Harness-Kurses als Baseline (gepinnt Tag `v1.2.0`),
  Adaptions-Block `MR-000..005`, Modus-Deklaration pro Sub-Area;
  plus `docs/reviews/`-Review-Report-Template.
- M8-ADRs: NEU `ADR 0050` (AC-ADAPTER-PURE-Bridge-Rueckbau),
  `ADR 0051` (Fault-Engine-Standort/Naming), `ADR 0054`
  (Composition-ASGI-Entrypoint + Scenario-Hook-Inversion), `ADR 0055`
  (EV-Charger-Device-Pattern: SoC + CC/CV + V2G + `connection_loss`-
  Fault), `ADR 0056` (Transformer-Device-Pattern: Wandlungsverhaeltnis
  + Eisen-/Kupferverluste + Saettigung + `winding_fault`), `ADR 0057`
  (Wind-Turbine-Device-Pattern: kubische Kennlinie + stochastischer
  seeded `RandomPort`-Windeingang), `ADR 0058` (Diesel-Generator-Device-
  Pattern: Kraftstoff + Verbrauch + Anfahr-/Abstell-Hysterese + Ramp +
  `genset_fault`), `ADR 0059` (generische `ScenarioFaultEngine`: eine Engine
  ueber `supported_types` statt einer Klasse pro Fault-Typ; Carveout D-8),
  `ADR 0060` (Inselnetz-Bilanzmodell: `is_islanded`/`forming_device_id` +
  Forming-Geraet als Slack + opt-in Snapshot-/Scenario-Hash),
  `ADR 0061` (Transformatorgrenzen im Netzbilanzmodell: `TransformerLimitConfig`
  + Single-Zonen-Thermomodell als Zeit-Strom-Mechanismus +
  `GridConstraintViolationEvent`),
  `ADR 0062` (Blindleistung im Netzbilanzmodell, 3c-a: `imbalance_kvar` +
  Q-Spannungskopplung + GridModelSnapshot v2→v3),
  `ADR 0063` (PV-Q(U)-Emission + Spannungs-Feedback, 3c-b-1:
  `DeviceTickContext.grid_voltage_v` lagged + opt-in `VoltVarConfig`),
  `ADR 0064` (GridConnection-Q-Auto-Schluss + Transformer-Scheinleistung
  `S=sqrt(P²+Q²)`, 3c-b-2: schliesst `GG-GRID-007`),
  `ADR 0065` (Battery-Temperatur-Telemetrie, 4a: opt-in `ThermalConfig` +
  stateful Single-Zonen-Euler + opt-in `temperature_celsius`-Telemetrie/
  -Snapshot; schliesst `GG-BESS-006`),
  `ADR 0066` (Battery-Zellspannung-Telemetrie, 4b: opt-in `CellConfig` +
  erster Battery-`RandomPort`-Konsum + per-Zelle tick-gekeytes Rauschen +
  opt-in `cell_voltage_delta_v`-Telemetrie/`cell_voltages_v`-Snapshot;
  schliesst `GG-BESS-007`) — alle
  `Accepted`.
- **M8-Welle 2a — EV-Charger (`GG-DEV-015`)**: NEU
  `hexagon/core/devices/ev_charger/` (`EvChargerDevice` als
  `DeviceModel` + `FaultInjectableDevice`) mit Fahrzeug-SoC,
  CC/CV-Ladekennlinie (linearer Taper ab `cv_phase_start_soc`),
  durchgaengigem V2G (hart bei `soc=0` gestoppt), Stecker-Zustand und
  `connection_loss`-Fault (NEU `FAULT_TYPE_CONNECTION_LOSS`). Verdrahtet
  ueber `_DEVICE_FACTORIES["ev_charger"]`, `DEVICE_DECIMAL_PARAMS`,
  `_DEVICE_TYPE_BY_CLASS_NAME`, Alarm-Mapper, HTTP-`POST /faults`-
  Whitelist und Visualization-State-Subset. NEU Szenario-Beispiel
  `tests/integration/scenarios/ev_charger_demo.yaml` + Unit-/
  Integration-Smokes (≥ 100-Tick-Determinismus, Snapshot-Roundtrip).
  `CRITICAL_COV_TARGETS`-Default um `devices/ev_charger` erweitert.
  Trigger 016 aufgeloest. ([`M8-welle-2a.md`](docs/plan/planning/done/M8-welle-2a.md))
- **M8-Welle 2b — Transformer (`GG-DEV-016`)**: NEU
  `hexagon/core/devices/transformer/` (`TransformerDevice` als
  `DeviceModel` + `FaultInjectableDevice`) nach dem GridConnection-Set-
  Power-Muster — Wandlungsverhaeltnis (`turns_ratio`), Eisen-/Leerlauf-
  verlust (konstant) + Kupfer-/Lastverlust (quadratisch), Saettigungs-
  Hard-Cap bei `rated_power_kw` und `winding_fault`-Schutzausloesung
  (NEU `FAULT_TYPE_WINDING_FAULT` → Sekundaer/Verlust hart `0`).
  Verdrahtet ueber dieselben 8 Integrations-Naehte; NEU Szenario-Beispiel
  `tests/integration/scenarios/transformer_demo.yaml` + Unit-/
  Integration-Smokes. `CRITICAL_COV_TARGETS`-Default um
  `devices/transformer` erweitert. Trigger 017 aufgeloest.
  ([`M8-welle-2b.md`](docs/plan/planning/done/M8-welle-2b.md))
- **M8-Welle 2c — Wind-Turbine (`GG-DEV-017`)**: NEU
  `hexagon/core/devices/wind_turbine/` (`WindTurbineDevice` als
  `DeviceModel`) nach dem PV-Muster — command-loser Generator mit
  kubischer Leistungskennlinie (cut-in/rated/cut-out) und
  **stochastischem seeded `RandomPort`-Windeingang** (erster echter
  `RandomPort`-Konsument; aktiviert die `attach_random`-Resume-Mechanik).
  Kein Command/Alarm/Fault. Verdrahtet ueber 6 Naehte; NEU Szenario-
  Beispiel `tests/integration/scenarios/wind_turbine_demo.yaml` +
  Unit-/Integration-Smokes. `CRITICAL_COV_TARGETS`-Default um
  `devices/wind_turbine` erweitert. Trigger 018 aufgeloest.
  ([`M8-welle-2c.md`](docs/plan/planning/done/M8-welle-2c.md))
- **M8-Welle 2d — Diesel-Generator (`GG-DEV-018`)**: NEU
  `hexagon/core/devices/diesel_generator/` (`DieselGeneratorDevice` als
  `DeviceModel` + `FaultInjectableDevice`) nach dem Battery-Muster —
  Kraftstoff-Vorrat (l) + Verbrauch (l/kWh) + Min-Startleistung + Ramp +
  Anfahr-/Abstell-Hysterese (running-Zustandsmaschine) + Kraftstoff-Run-
  Dry + `genset_fault`-Schutz (NEU `FAULT_TYPE_GENSET_FAULT`). Verdrahtet
  ueber 9 Naehte inkl. `_BILANZ_SOURCE_BUCKETS` (`generation`); NEU
  `snapshot_codec.assert_bool`. NEU Szenario-Beispiel
  `tests/integration/scenarios/diesel_demo.yaml` + Unit-/Integration-
  Smokes. `CRITICAL_COV_TARGETS` um `devices/diesel_generator` erweitert.
  Trigger 019 aufgeloest. **Damit ist M8-Welle 2 (alle vier SOLLTE-
  Geraete `GG-DEV-015..018`) komplett.**
  ([`M8-welle-2d.md`](docs/plan/planning/done/M8-welle-2d.md))
- **M8-Welle 2-D8 — Generische `ScenarioFaultEngine`** (Cross-Cutting-
  Review-Folge, [`ADR 0059`](docs/plan/adr/0059-generic-scenario-fault-engine.md)
  `Accepted`): NEU `hexagon/core/faults/scenario_fault_engine.py`
  generalisiert die bis auf zwei Stellen identischen `BatteryFaultEngine`/
  `GridFaultEngine` (ADR 0025-Scheduling) zu **einer** Engine
  (`faults, supported_types, subsystem`); Battery/Grid bleiben duenne
  Compat-Subklassen (M3-Tests unveraendert gruen). `_compose_fault_port`
  liefert nun eine Single-Engine (Klasse `_FaultPortComposition` entfernt),
  `_KNOWN_FAULT_TYPES` auf 5 Typen (single source of truth). **Damit wirken
  `connection_loss`/`winding_fault`/`genset_fault` end-to-end ueber YAML-
  Szenarien ohne per-Typ-Engine-Code (Carveout D-8 aufgeloest).** Dead
  `assert_supported_type` entfernt. NEU
  `tests/integration/scenarios/diesel_fault_demo.yaml` + Unit-/Integration-
  Smokes. ([`M8-welle-2-d8.md`](docs/plan/planning/done/M8-welle-2-d8.md))
- **M8-Welle 3a — Inselnetz-Bilanzmodell (`GG-GRID-005`)**
  ([`ADR 0060`](docs/plan/adr/0060-island-grid-bilanz-pattern.md)
  `Accepted`, Schaerfung von `ADR 0019` ohne Supersedes): `GridModelConfig`
  bekommt additiv `is_islanded`/`forming_device_id` (Presence-Biconditional
  am Config-Rand). Im Inselnetz haelt ein internes **Grid-Forming-Geraet**
  (Diesel/Battery) den Slack statt des `GridConnectionDevice` — der TickLoop-
  Fork spiegelt den GridConnection-Auto-Schluss: Forming-Geraet aus erster
  Iteration ausgeschlossen, Residual `gen-load-storage+grid` ihm via
  `set_power_kw` zugewiesen, **Vorzeichen pro `_BILANZ_SOURCE_BUCKETS`**
  (Generation `-residual`, Storage `+residual`). Existenz-Check im TickLoop-
  Wiring (NEU `TickLoopUnknownFormingDeviceError`), nicht in der Config.
  Snapshot **und** Scenario-Hash opt-in (Insel-Keys nur bei `is_islanded`):
  kein Schema-Bump, `EXPECTED_DEMO_*` unberuehrt; backward-compat-Lesepfad.
  Scenario-YAML-`grid_model`-Sektion liest die Insel-Felder. Forming-Ueberlast
  via Geraete-eigenem `set_power_kw`-Clamp (Diesel/Battery `LIMITED`-Alarm);
  dedizierter `GridConstraintViolationEvent` deferred → 3b.
  `is_islanded=False` bit-genau wie heute. Trigger 020 aufgeloest.
  ([`M8-welle-3a.md`](docs/plan/planning/done/M8-welle-3a.md))
- **M8-Welle 3b — Transformatorgrenzen im Netzbilanzmodell (`GG-GRID-006`)**
  ([`ADR 0061`](docs/plan/adr/0061-transformer-limit-bilanz-pattern.md)
  `Accepted`, Schaerfung von `ADR 0019` ohne Supersedes): NEU
  `TransformerLimitConfig` (nested, opt-in) in `GridModelConfig` — die
  **Netz-Grenze** im Bilanzmodell, klar abgegrenzt vom Transformer-**Geraet**
  (`ADR 0056`, Per-Device-Saettigung). Vereinfachtes Single-Zonen-
  **Thermomodell als Zeit-Strom-Mechanismus**: `S=|grid_connection_kw|`
  (≈|P| bis 3c), Top-Oil-Euler-Integration + Hot-Spot-Gradient; bei
  `hot_spot > limit` pro-Tick NEU `GridConstraintViolationEvent` (frozen
  Domain-Event in `domain/event.py`, getragen in
  `TickResult.emitted_grid_events`). Die thermische Traegheit τ **ist** die
  Zeit-Strom-Kennlinie (kurze Ueberlast erlaubt, dauerhafte nicht).
  `top_oil_temp_c` ist akkumulierter State; Snapshot + Scenario-Hash opt-in
  (kein Versions-Bump, `EXPECTED_DEMO_*` unberuehrt). YAML-`transformer_limit`-
  Block (Validator + Loader). `transformer_limit=None` bit-genau wie heute.
  Trigger 021 aufgeloest.
  ([`M8-welle-3b.md`](docs/plan/planning/done/M8-welle-3b.md))
- **M8-Welle 3c-a — Blindleistung im Netzbilanzmodell: Q-Bilanz + Schema-Bump
  (`GG-GRID-007`, teilweise)**
  ([`ADR 0062`](docs/plan/adr/0062-reactive-power-bilanz-pattern.md)
  `Accepted`, Schaerfung von `ADR 0019` ohne Supersedes; Re-Tranche von 3c):
  `GridModelBilanz.update(reactive_power_kvar=0)` fuehrt `last_imbalance_kvar`
  parallel zu `last_imbalance_kw`; **Q koppelt nur an die Spannung**
  (`voltage_v += voltage_sensitivity_v_per_kvar * imbalance_kvar`), nicht an
  die Frequenz. NEU opt-in Config-Feld `voltage_sensitivity_v_per_kvar`
  (Default `0.2`; Serialisierung opt-in → Scenario-Hash byte-stabil).
  `GridModelSnapshot` **v2→v3** (`last_imbalance_kvar` immer present;
  v1/v2-Backward-Compat liest `0`) — pin-neutral (`EXPECTED_DEMO_*` hashen
  Telemetry-Stream + Scenario-Hash, nicht den Snapshot). `Q=0` bit-genau wie
  heute. **Deferred → 3c-b:** Geraete-Q-Emission (PV-Q(U)/GridConnection-Q),
  Device-Snapshots, TickLoop-Q-Aggregation, Transformer `S=sqrt(P²+Q²)`,
  Demo-Telemetry-Re-Pin; **Trigger 022 bleibt offen bis 3c-b**.
  ([`M8-welle-3c.md`](docs/plan/planning/done/M8-welle-3c.md))
- **M8-Welle 3c-b-1 — PV-Q(U)-Emission + Spannungs-Feedback (`GG-GRID-007`,
  teilweise)**
  ([`ADR 0063`](docs/plan/adr/0063-pv-volt-var-q-emission-pattern.md)
  `Accepted`, Folge zu `ADR 0016`; Re-Tranche von 3c-b): die erste Q-Quelle.
  NEU `DeviceTickContext.grid_voltage_v` (optional) — der TickLoop reicht die
  **aktuelle `GridModelBilanz.voltage_v` (lagged = voriger Tick)** an die
  Geraete, damit die Q(U)-Kopplung deterministisch ohne Iteration ist. NEU
  opt-in `VoltVarConfig` in `PvConfig` (Deadband + Droop + Clamp); das PV
  emittiert `reactive_power_kvar`-Telemetrie **nur bei konfigurierter Kurve**
  (kein Curve → **kein** Punkt, nicht `0 kvar`). Der TickLoop aggregiert einen
  `reactive_kvar`-Bucket → `grid_model.update(reactive_power_kvar=...)`.
  PvSnapshot serialisiert `volt_var` opt-in (kein Versions-Bump). **Pin-neutral**:
  der Q-freie Demo emittiert keine Q-Telemetrie → `EXPECTED_DEMO_*` unberuehrt.
  **Deferred → 3c-b-2:** GridConnection-Q-Auto-Schluss, Transformer
  `S=sqrt(P²+Q²)` (re-pinnt 3b-Boundary), Trigger-022-Closure.
  ([`M8-welle-3c.md`](docs/plan/planning/done/M8-welle-3c.md))
- **M8-Welle 3c-b-2 — GridConnection-Q-Auto-Schluss + Transformer-
  Scheinleistung (`GG-GRID-007`, schliesst die Welle)**
  ([`ADR 0064`](docs/plan/adr/0064-grid-connection-q-transformer-apparent-power.md)
  `Accepted`, Folge zu `ADR 0017`/`ADR 0061`; Re-Tranche von 3c-b): der
  zweite Q-Pfad + die Scheinleistungs-Grenze. Der **Netzanschluss absorbiert
  den Q-Residual** (Spiegel zum P-Slack-Auto-Schluss): der TickLoop reicht
  `grid_connection_kvar = -Σ(geraete-Q)` als Command (`reactive_value`) an
  das `GridConnectionDevice`, das `reactive_power_kvar` **opt-in** emittiert
  (Q=0 → **kein** Punkt) und in `grid_model.update(grid_connection_kvar=...)`
  einspeist → `imbalance_kvar` schliesst sich (Q gehalten). Die
  **Transformer-Grenze rechnet jetzt auf `S=sqrt(P²+Q²)`** der
  Netzanschluss-Leistung statt `|P|` — `sqrt(P²)=|P|` exakt fuer
  terminierende Decimals, daher bleiben die 3b-Boundary-Tests als
  Q=0-Regressionspin gruen. `GridConnectionDevice` + `GridConnectionSnapshot`
  fuehren `current/pending_reactive_power_kvar` (opt-in serialisiert, kein
  Versions-Bump). **Pin-neutral**: Q-frei byte-identisch, `EXPECTED_DEMO_*`
  unberuehrt. **Trigger 022 aufgeloest** — `GG-GRID-007` komplett; damit ist
  **M8-Welle 3 (Netz, `GG-GRID-005..007`) abgeschlossen**.
  ([`M8-welle-3c.md`](docs/plan/planning/done/M8-welle-3c.md))
- **M8-Welle 4a — Battery-Temperatur-Telemetrie (`GG-BESS-006`)**
  ([`ADR 0065`](docs/plan/adr/0065-battery-thermal-telemetry-pattern.md)
  `Accepted`, Schaerfung zu `ADR 0014` ohne Supersede; spiegelt die
  Single-Zonen-Euler-Thermik aus `ADR 0061` aufs Battery-Pack): NEU opt-in
  `ThermalConfig` (nested) auf `BatteryConfig` (`ambient_temp_c`,
  `thermal_rise_c_at_full_load`, `thermal_time_constant_s`). `BatteryDevice`
  fuehrt `temperature_celsius` als **stateful** Geraete-State
  (`theta += (theta_ss - theta)·dt/tau`, `theta_ss = ambient + rise·load_pu²`,
  `load_pu = abs(power_kw)/max(max_charge_kw,max_discharge_kw)`; Kaltstart auf
  `ambient_temp_c`) und emittiert einen `temperature_celsius`-`TelemetryPoint`
  (`unit="degC"`) **nur bei aktivem Block** (inaktiv → kein Punkt, nicht `0`;
  alphabetisch hinter `soc_pct`). `BatterySnapshot` serialisiert den
  Thermo-Block + State **opt-in ohne Versions-Bump** (v1-backward-compat-
  Lesepfad; strenger als der immer emittierte `fault_state`). Reine
  Telemetrie — **kein** Trip/Alarm/Derating (M3). **Pin-neutral**:
  Demo-Battery ohne `thermal`-Block → keine T-Telemetrie/-State,
  `EXPECTED_DEMO_*` + Scenario-Hash unberuehrt. **Trigger 023 aufgeloest.**
  ([`M8-welle-4a.md`](docs/plan/planning/done/M8-welle-4a.md))
- **M8-Welle 4b — Battery-Zellspannung-Telemetrie (`GG-BESS-007`)**
  ([`ADR 0066`](docs/plan/adr/0066-battery-cell-voltage-telemetry-pattern.md)
  `Accepted`, Schaerfung zu `ADR 0014` ohne Supersede; Schwester-Slice zu
  `ADR 0065`): NEU opt-in `CellConfig` (nested) auf `BatteryConfig`
  (`nominal_pack_voltage_v`, `n_cells`, `noise_amplitude_v`) — **erster
  Battery-`RandomPort`-Konsum** (Praezedenz `ADR 0057` Wind). `cell_voltages_v`
  je Tick aus Basis `nominal_pack_voltage_v/n_cells`; bei `noise_amplitude_v>0`
  pro Zelle `(draw*2-1)*amp` aus
  `random.sub_port("cell-<i>").sub_port("tick-<t>").next_float()` — per-Zelle
  unabhaengig, per-Tick variierend, **tick-gekeyt → resume-kontinuierlich**;
  `noise=0` → alle Zellen identisch (kein `RandomPort`-Zug). Opt-in aggregierte
  `cell_voltage_delta_v`-`TelemetryPoint` (`max-min`, `unit="V"`) **nur bei
  aktivem Block** (bounded statt N per-Zelle); Emission alphabetisch sortiert.
  `BatterySnapshot` opt-in (Config-`cell`-Block mit `n_cells:int` +
  `cell_voltages_v: tuple[Decimal,...]` nur bei Non-Empty) **ohne
  Versions-Bump** (v1-Lesepfad, Tuple-Kanonik). **Resume**: aktives Rauschen
  ohne `attach_random` → fail-loud, danach byte-kontinuierlich. Reine
  Telemetrie — **kein** Balancing/Abschaltung (M3). **Pin-neutral**: Demo ohne
  `cell`-Block → `EXPECTED_DEMO_*` unberuehrt. **Trigger 024 aufgeloest** —
  damit ist **M8-Welle 4 (BESS-Telemetrie, `GG-BESS-006/007`) abgeschlossen**.
  ([`M8-welle-4b.md`](docs/plan/planning/done/M8-welle-4b.md))
- NEU `grid_gym/composition/`-Paket (Composition Root) mit
  `composition.asgi`-Entrypoint; NEU
  `hexagon/ports/driving/run_execution.py` (`RunExecutionPort`); NEU
  `hexagon/core/domain/fault.py` (Fault-Type-Single-Source).
- NEU `M8-welle-2.md` (Geraete-Wellen-Plan) + Welle-1-Closure/Lerneintrag
  in `M8-welle-0.md`.

### Changed

- **Slice 045 — `fault_state`-Flag-Reader-Dedup**: NEU
  `snapshot_codec.assert_optional_fault_flag(...)` als geteilter Reader
  fuer optionale Fault-Bool-Flags (ADR 0025 §2.2-Konvention); die vier
  Device-Snapshots (battery/grid_connection/ev_charger/transformer)
  konsumieren ihn jetzt statt je einer eigenen Kopie. Verhaltensneutral
  (alle Fault-Roundtrip-Tests unveraendert gruen).
- Roadmap erweitert: NEU Meilenstein **M8 — SOLLTE-Geraete & Netz**
  (→ Release v0.2.0). Wellen: 0 = Eroeffnung, 1 = Architektur-Cleanup
  (Done), 2 = Geraete `T-016..019`, 3 = Netz `T-020..022`,
  4 = BESS-Telemetry `T-023/024`; M9/M10 als Skizze.
- **M8-Welle 1 (Architektur-Cleanup) abgeschlossen** (Slices 041+042,
  verhaltensneutral, je `make fullbuild` + CI verifiziert):
  `AC-ADAPTER-PURE`-`ignore_imports` **8 → 0** (`ignore_imports = []`)
  — Run-Ausfuehrung ueber NEU `RunExecutionPort`, Fault-Konstanten +
  `ControlAction` nach `core.domain.*`, Demo-/Scenario-Bootstrap nach
  `composition/` mit App-Bootstrap-Hook-Inversion +
  `composition.asgi`-uvicorn-Entrypoint (`Dockerfile`/`__main__`/
  Compose); Fault-Engines `*FaultAdapter` → `*FaultEngine` (Standort
  bleibt `hexagon/core/faults`). M8-Wellen-Nummerierung vereinheitlicht.

- Doku-Sweeps zur Linkpflicht: ~620 nackte Kennungen auf ihre
  Definition verlinkt (mit Abschnitts-Ankern; `AC-*`-Target =
  deklarierendes ADR), ~120 Bestands-Links um Kapitel-/
  ID-Anker ergaenzt, 70 Inline-Code-Pfade korrigiert/markiert
  (`d-check:ignore` fuer Geplantes/Historisches).
- READMEs (en/de) Stale-Sweep nach M7-Closure + v0.1.0
  (Test-Counts 1796/139+4, Arch-Contracts 7+13,
  Projektbaum, Release-Verweis).
- `carveouts.md` neu geordnet: Ein-Tabellen-Design mit
  ID-Schema (`D-n`/`T-nnn`/`P-n`), Begruendungen per ID,
  Nummern-Historie-Map.
- Trivy-Scanner-Pin `0.71.0 → 0.71.1` (Makefile `TRIVY_IMAGE`).
- NEU `make static-gates` — schneller Pre-Push-Sweep der **statischen**
  Code-Gates (`lint` + `format-check` + `typecheck` + `arch-check` +
  `noqa-gate` + `spdx-check`) ohne die pytest-Stages (`test-unit`/
  `coverage-gate*`) und `dep-audit`. Faengt alle ruff-/mypy-/arch-Befunde
  in einem Lauf (kein Einzel-Gate uebersehen) und ist frei vom lokalen
  `pyiec61850`-Env-Artefakt; die volle `make gates`-Linie bleibt
  unveraendert.

### Security

- Dependency-Bump zur Behebung der von `dep-audit` (`pip-audit --strict`)
  gemeldeten Bestands-CVEs: `cryptography 48.0.0 → 49.0.0`
  (GHSA-537c-gmf6-5ccf), `starlette 1.0.1 → 1.3.1` (CVE-2026-48818 /
  -48817 / -54283 / -54282), `pyopenssl 26.2.0 → 26.3.0` (transitiv).
  `fastapi` bleibt `0.136.1` (akzeptiert `starlette 1.3.1`). Verifiziert:
  `dep-audit`/`typecheck`/`test-unit` (2108)/`openapi-validate`/
  `image-audit` gruen.

## [0.1.0] - 2026-06-12

Erstes Release — **der MVP ist geliefert** (M1..M7: alle vier
`GG-MVP-*`-Punkte + alle vier `GG-SAFE-001..004`-MUSS-IDs
produktiv; 49 ADRs `Accepted`, Closure-Artefakt
`docs/plan/planning/done/M7-results.md`). Der Tag-Push dieses
Releases ist zugleich der erste reale Lauf des
Release-Workflows (`.github/workflows/release.yml`, ADR 0042)
und loest Trigger 032 auf. Alle folgenden Eintraege sind die
kumulierte Historie seit Projektstart.

### Added

- `spec/architecture.md` v0.1.0 — Architekturbeschreibung mit
  hexagonaler Sicht, Driving-/Driven-Ports (`GG-AR-PORT-*`),
  Architektur-Tabus (`GG-AR-TABU-*`), Komponenten (`GG-AR-COMP-*`),
  offenen Punkten (`GG-AR-OPEN-*`).
- `spec/lastenheft.md` §27 V-Modell-Rueckverfolgbarkeit mit drei
  Tabellen (Anforderung → Design / Implementierung / Test) und neuer
  Anforderung `GG-TRACE-001`.
- `docs/`-Skelett mit `plan/adr/`, `plan/planning/{open,next,in-progress,done}/`,
  `user/`, `archive/`.
- `docs/plan/adr/0001-documentation-and-planning-structure.md` —
  Dokumentations- und Planungsstruktur.
- `docs/plan/adr/0003-adr-lifecycle.md` — historischer ADR-Lifecycle als
  Ergaenzung zu ADR 0001 (Statuswerte
  `Proposed`/`Provisional`/`Accepted`/`Rejected`/`Withdrawn`/`Superseded`,
  Uebergangsregeln, Verhaeltnis zu ADR 0001 §3/§4, Pflege-Regeln
  fuer `architecture.md §19`-Eintraege je Status). Loest den
  impliziten Konflikt zwischen ADR 0001 (ADRs = Entscheidungen)
  und ADR 0002 (Spike-getriebener Vorschlag) auf, ohne ADR 0001
  inhaltlich zu ueberschreiben. Inzwischen durch ADR 0006 abgeloest.
- `docs/plan/adr/0006-adr-lifecycle-superseding-and-process-corrections.md`
  — aktive ADR-Lifecycle-Regel. Supersedes ADR 0003; klaert
  `Superseded`-Metadaten, Header-Schema, operative Spike-Artefakte,
  `Rejected` vs. `Withdrawn` und die Einordnung der ADR-0004-
  Retrofit-Regel fuer Lifecycle-Aenderungen.
- `docs/plan/adr/0004-identifier-based-cross-references.md` —
  Querverweise zwischen Spec-/Planungsartefakten nutzen Kennungen
  (`GG-*`, `GG-AR-*`, `GG-TRACE-*`, `AC-*`, ADR-Nummern) als
  primaere Referenz; `§…`-Hinweise sind nur Lesehilfen in Klammern.
  Retrofit-Regel: bei naechster Beruehrung umstellen.
- `docs/plan/adr/0005-type-check-gate.md` — `mypy --strict` als
  Pflicht-Gate fuer `GG-QG-005` Static-Analysis und automatisierte
  Teilabdeckung von `GG-PRINC-004` (LSP via Variance) und
  `GG-PRINC-005` (ISP via Protocol-Konformitaet). Status:
  `Provisional`, Acceptance synchron mit `ADR 0002`. `pyright` bleibt
  Developer-Tool ueber Pylance, nicht CI-Gate.
- `Dockerfile`-Stage `typecheck` und Makefile-Target `make typecheck`
  ergaenzt; Aggregator `gates` enthaelt jetzt `typecheck` zwischen
  `format-check` und `arch-check`.
- `docs/plan/adr/0002-language-and-build-stack.md` — Entwurf zur
  Sprach- und Build-Wahl (Status: Provisional; schliesst bei Annahme
  `GG-AR-OPEN-001`). Begruendung MVP-getrieben; Future-Punkte als
  Zusatznutzen ausgewiesen. Auflage A-1 als Drei-Tool-Suite
  (`import-linter` + `ruff` + eigenes AST-Skript `tools/arch_check.py`)
  (inkl. `grimp`-SCC-Zykluscheck) mit fuenfzehn Contracts:
  AC-CORE-NO-ADAPTERS, AC-CORE-NO-DRIVING, AC-PORTS-NO-OUT,
  AC-PORTS-NO-FW (`GG-ARCHTEST-004`), AC-ADAPTER-PURE,
  AC-ADAPTER-LIGHTWEIGHT (AST-Heuristik), AC-NO-FW, AC-NO-IO-MOD,
  AC-NO-CYCLES (Graph-SCC statt `independence`), AC-NO-TIME,
  AC-NO-RAND, AC-NO-JSON, AC-DOMAIN-FROZEN, AC-NO-GOD-UTILS,
  AC-TYPED-ERRORS. Tabu-Abdeckungs-Matrix ausgewiesen mit
  Reststeuerung: `GG-AR-TABU-003` Logik-Anteil ist
  review-pflichtig. `ruff`-Per-File-Ignores normiert (`tests/**`,
  Error-Translation-Module, Adapter-DTZ-Scope) plus konkrete
  `flake8-tidy-imports`-Konfiguration (`banned-api` fuer
  `datetime.datetime.utcnow`, `banned-module-level-imports` fuer
  `random`/`secrets`/`numpy.random` in `core.*`). Rollenverteilung
  zwischen `ruff` und `tools/arch_check.py` ehrlich getrennt:
  `time.time`/`time.monotonic`/`asyncio.get_event_loop().time` und
  Aufruf-Site-Random sind explizit `tools/arch_check.py`,
  nicht `ruff`. `AC-NO-JSON` mit Whitelist fuer
  `src/grid_gym/core/serialization/canonical.py` (loest A-2-
  Selbstblockade). Auflage A-2 mit hartem Format-/Roundtrip-Vertrag:
  Vor-Normalisierung via `Decimal.quantize` + `ROUND_HALF_EVEN`,
  NaN/Infinity-Verbot (`allow_nan=False`), ISO-8601-UTC fuer
  Wall-Clock-Zeit, ganzzahlige Millisekunden fuer Simulationszeit,
  UTF-8-Bytes als Vertragsschnittstelle; `orjson` als
  Alternativ-Encoder mit Bytes-Gleichheits-Test zugelassen.
  Fallback-Trigger an `GG-RT-001/004/005`, `GG-REPLAY-007`,
  `GG-SAFE-006` gekoppelt; `GG-RT-004/005` als bewusst zu
  Go/No-Go hochgestufte `SOLLTE`-Anforderungen ausgewiesen.
  Konsequenzen (§6) fixieren Paketmanager (`uv` mit `uv.lock`),
  PEP-735-Dependency-Groups, Repo-Layout (Monolith
  `src/grid_gym/` mit `import-linter`-Layern; uv-Workspaces nicht
  verwendet); §6 ausdruecklich als „bei Acceptance" formuliert,
  §6.2 trennt Acceptance- von Provisional-Wirkung. **Status-Pfad
  dreistufig** (`Proposed → Provisional → Accepted`) mit
  Pre-Acceptance-Spike-0-Vertrag; `GG-AR-OPEN-001` wird erst nach
  gruenem Spike-0 in `architecture.md §19` als geschlossen
  markiert. `ruff.toml`-Block korrigiert: `banned-module-level-imports`
  unter `[tool.ruff.lint.flake8-tidy-imports]` platziert (vorher
  faelschlich eigene Sub-Tabelle); Spike-0 prueft die Konfiguration
  ueber `ruff check --no-cache`. K-CONTAIN auf `o` korrigiert.
  A-2-Vertrag implementierbar gemacht: numerisches Repraesentations-
  Modell (`Decimal` mit max. 6 Nachkommastellen, kein `float` im Kern),
  eigene `CanonicalEncoder`-Subklasse von `json.JSONEncoder` die
  `Decimal` ueber `format(value, "f")` emittiert (loest die Luecke,
  dass `json.dumps` `Decimal` nativ nicht kennt), Standard-Implementierung
  als konkrete Python-Skizze hinterlegt. AC-NO-JSON-Whitelist von
  Pseudo-`per-file-ignores`-Eintrag auf echte
  `[tool.grid_gym.arch_check]`-Konfigurationssektion umgestellt,
  die `tools/arch_check.py` als Single-Source-of-Truth liest
  (`json-dumps-whitelist`, `domain-frozen-extra`, `typed-errors-exempt`).
  Status-Pfad verweist jetzt auf ADR 0006 als aktive
  Lifecycle-Definition.
- `docs/plan/planning/in-progress/roadmap.md` — Roadmap-Skelett als
  Quelle fuer §27.2-Meilenstein-Marker.
- Quality-Gate-Erweiterung in `Dockerfile`/`Makefile`:
  `coverage-gate` zusaetzlich mit `--cov-branch` und 85%-Branch-Schwelle
  (`GG-COV-002`); neuer Stage `coverage-gate-critical` mit
  Modul-Filter `core/{simulation,devices/battery,scenario,replay}`
  und 90% Line/Branch (`GG-COV-003` MUSS); neuer Stage `dep-audit`
  mit `pip-audit --strict` gegen die per `uv export` materialisierte
  Lockfile (`GG-QG-002`/`GG-QA-005`); Makefile-Target `image-audit`
  mit `trivy image --exit-code 1 --severity HIGH,CRITICAL`
  (`GG-QG-002` SOLLTE); neuer Stage `openapi-validate` (FastAPI-Spec-
  Export + `openapi-spec-validator`, `GG-QG-006`). Aggregator
  `gates` erweitert um `coverage-gate-critical` und `dep-audit`;
  `ci` erweitert um `openapi-validate` und `image-audit`.
- `Dockerfile` (Multi-Stage) und `Makefile` als Spike-0-Geruest zu
  ADR 0002. Stages: `base`, `deps`, `source`, `lint`, `format-check`,
  `arch-check`/`arch-check-imports`/`arch-check-custom`,
  `test-unit`/`test-determinism`/`test-replay`/`test-fault`,
  `coverage-gate`, `build-app`, `runtime` (non-root, /health
  HEALTHCHECK, Port 8080). Makefile-Targets pro Stage plus
  Aggregator (`gates`, `ci`, `fullbuild`) und Maintenance
  (`lock-refresh`, `sbom`, `clean`). Stack
  gemaess ADR 0002 (Python 3.13+/3.14, `uv`, `ruff`, `import-linter`,
  `tools/arch_check.py`, `pytest`, `hypothesis`, `testcontainers`).
  Artefakte greifen die Spike-0-Lieferliste auf und setzen die
  noch fehlenden Spike-0-Bausteine (`pyproject.toml`,
  `src/grid_gym/`, `tests/`, `tools/arch_check.py`) als kuenftig
  voraus. ADR-0002-Status ist `Provisional`; die Artefakte sind als
  Spike-0-Pfad gemaess ADR 0006 gekennzeichnet.
- `docs/plan/planning/open/` mit elf Trigger-Watch-Dateien
  (`001-code-review-doc.md` bis `011-hexagon-layout-adr-0002-realign.md`)
  und aktualisiertem `README.md` mit Bestandstabelle. Macht die
  bisher impliziten Folgearbeiten aus ADR 0002/0004/0005, Makefile
  und Dockerfile sichtbar (`docs/user/code-review.md`,
  `tools/check_refs.py`, `RandomPort`-ADR, Alternativ-Encoder-ADR,
  mypy/pyright-Re-Eval, `--strict-bytes`, pyright-Pre-Commit-ADR,
  SBOM-Scharfschaltung, `tests/integration/compose.yml`,
  `deploy/compose.yml`, ADR-0002-Contract-Anpassung an `hexagon/`).
  Schliesst die Luecke gegenueber `ADR 0001` §4 („Offene Trigger
  bleiben in `open/`").

### Changed

- `spec/lastenheft.md` Version `0.6` → `0.8` (V-Modell-Abschnitt §27,
  §27.1 gegen `architecture.md` verknuepft).
- `spec/lastenheft.md` §27.1 praezisiert: `GG-CC-*`-Zeile in einzelne
  Tabu-Mappings aufgeteilt; `GG-CC-001/005` als Code-Review-Gegenstand
  markiert; neue Zeilen fuer `GG-ACCEPT/DEMO/TRACE/TEST/COV/QG/QA`;
  neuer Unterabschnitt §27.1.1 listet Scope-/Definitions-Anforderungen
  (`GG-TERM/SEED/MVP/NONGOAL/FUTURE`), die bewusst kein Design-Artefakt haben.
- Verweise auf „Roadmap §26" praezisiert: aktive Meilensteine leben
  in `docs/plan/planning/in-progress/roadmap.md`; §26 listet nur
  `GG-FUTURE-*`.
- `README.md` Projektstruktur aktualisiert.
- `GG-AR-OPEN-001`-Beschreibung in `architecture.md` praezisiert:
  betrifft Sprache und Runtime des Simulationskerns, der Adapter
  und der Build-Toolchain; Modulgrenzen aus `GG-AR-P-002` und
  `GG-AR-TABU-001..008` bleiben sprachunabhaengig.
- ADR 0002 Python-Versions-Anker auf den Lebenszyklus-Stand
  vom 2026-05-14 aktualisiert: Minimum-Floor von `3.12+` auf
  `3.13+` gehoben (3.12 ist nur noch Security-Only), Referenz-
  Runtime und Container-Image auf `3.14` gesetzt (Bugfix bis
  2030-10), CI-Matrix laeuft gegen `3.13` und `3.14`. Versions-
  Begruendung als eigener Block in der Option-A-Sektion hinterlegt.
- Retrofit ADR 0004: alle `§…`-Verweise in ADR 0002,
  `lastenheft.md` `GG-TRACE-001`-Tabellen, `architecture.md`
  Rueckverfolgbarkeitstabelle und `roadmap.md` durch
  Kennungs-Verweise ersetzt. Verbleibende `§…`-Eintraege beziehen
  sich nur auf Sektionen ohne eigene Kennung (Testarchitektur in
  `architecture.md`) und sind als Klammer-Lesehilfen gekennzeichnet.
- ruff-Auswahl in ADR 0002 erweitert um Klassen-Ebene-Heuristiken
  und Code-Hygiene: `PLR0902/PLR0903/PLR0904` (SRP/ISP-Signale),
  `PLR0916`/`PLR2004` (Bedingungs- und Magic-Number-Detection),
  `B`/`RET`/`SIM`/`ARG`/`RUF` (Design-Bugs, Kontrollfluss,
  Refaktorisierung), `N` (pep8-naming als Heuristik fuer
  `GG-CC-005`). `[tool.ruff.lint.pylint]` mit
  `max-public-methods=12`, `max-attributes=7`, `max-bool-expr=4`.
  `tests/**`-Per-File-Ignore entsprechend gelockert.
- §27.1-Mapping fuer `GG-PRINC-001..006` in fuenf Einzel-Zeilen
  aufgespalten (SOLID-Prinzipien einzeln zugeordnet zu ruff-Regeln,
  ADR 0005, Architektur-Tabus); `GG-CC-005` von „Code-Review" auf
  ruff `N` plus Code-Review-Rest umgestellt; `GG-CC-001`-Anteil
  bleibt bei ruff (`PLR0915` etc.).
- ADR 0002 `ruff`-Konfiguration um Methodenlaengen-Gate ergaenzt:
  `C901`, `PLR0911`, `PLR0912`, `PLR0913`, `PLR0915` mit
  `max-complexity=10`, `max-statements=30`, `max-branches=12`,
  `max-args=5`, `max-returns=6` — bildet `GG-CC-001`
  Methodenlaengen-Akzeptanzkriterium 1:1 auf ruff ab.
  `tests/**`-Per-File-Ignore um `PLR*`/`C901` erweitert (Tests
  duerfen lang/komplex sein).
- `GG-CC-001` in §27.1 von „Code-Review-Gegenstand" auf
  automatisierten ruff-Check umgestellt; Restanteil bleibt Review.
- `spec/architecture.md` §4.2 Verzeichnisstruktur: `core/` und
  `ports/` zu einer `hexagon/`-Gruppierungsebene zusammengefasst
  (`hexagon/core/{domain,simulation,devices,scenario,replay,faults,agents}`,
  `hexagon/ports/{driving,driven}`). Folge-Updates in derselben
  Datei: Tabu-Familie `GG-AR-TABU-001/002` referenziert
  `hexagon/core/*`; Komponentensicht §5 fuehrt `hexagon/core/*`
  als Modul-Pfade; Prosa-Erwaehnungen `core/devices/battery` und
  `core/agents` umgestellt. ADR-0002-Contracts und Coverage-Pfade
  in `Dockerfile`/`Makefile` referenzieren noch `core.*` —
  Anpassung als Trigger-Watch
  (`docs/plan/planning/open/011-hexagon-layout-adr-0002-realign.md`)
  vor `ADR 0002 Accepted` vorgesehen.
- `spec/architecture.md` §17 Testarchitektur erhaelt die Kennung
  `GG-AR-TEST-001` (gemaess `ADR 0004` §2.2: Sektion ohne Kennung
  bei naechster Beruehrung umstellen). `spec/architecture.md` §18
  Rueckverfolgbarkeitstabelle und `spec/lastenheft.md` §27.1
  Design-Tabelle (neun Zeilen: `GG-TESTTYPE-*`, `GG-ARCHTEST-*`,
  `GG-CICD-*`, `GG-DEMO-*`, `GG-ACCEPT-*`, `GG-TEST-*`, `GG-COV-*`,
  `GG-QG-*`, `GG-QA-*`) verweisen jetzt auf `GG-AR-TEST-001` statt
  „Testarchitektur in `architecture.md` (§17 — noch keine eigene
  Kennung)".
- `spec/architecture.md` §4.2 Verzeichnisstruktur: Hinweis ergaenzt,
  dass sprachspezifische Paketnamen (z. B. `src/grid_gym/...` fuer
  Python) erst mit Acceptance von `ADR 0002` in die
  Verzeichnisstruktur uebernommen werden.
- `spec/architecture.md` §18 SOLID-Zeile (`GG-AR-P-001..014`) um
  Hinweis ergaenzt, dass das Detail-Mapping pro `GG-PRINC-*` in
  `GG-TRACE-001` (`lastenheft.md` §27.1) zu finden ist.
- `spec/lastenheft.md` §27.3 Anforderung-zu-Test um `GG-TRACE-001`
  ergaenzt (Documentation Test — Self-Verification der drei
  Trace-Tabellen; Folgearbeit `tools/check_refs.py`).
- `docs/plan/adr/0002-language-and-build-stack.md` Pre-Acceptance-
  Schliff (Trigger 011 abgearbeitet, `ADR 0006` §3-konform):
  Repository-Layout in §6.1 auf
  `src/grid_gym/{hexagon/{core,ports},adapters}/` praezisiert;
  alle fuenfzehn A-1 Contracts auf `hexagon.core.*`/`hexagon.ports.*`
  umgestellt (AC-CORE-NO-ADAPTERS/CORE-NO-DRIVING/PORTS-NO-OUT/
  PORTS-NO-FW/ADAPTER-PURE/ADAPTER-LIGHTWEIGHT/NO-FW/NO-IO-MOD/
  NO-CYCLES/NO-TIME/NO-RAND/NO-JSON/DOMAIN-FROZEN/NO-GOD-UTILS/
  TYPED-ERRORS); AC-NO-JSON-Whitelist und
  `[tool.grid_gym.arch_check]` `json-dumps-whitelist`-Pfad auf
  `src/grid_gym/hexagon/core/serialization/canonical.py`;
  Spike-0-Skelett-Pfad und A-2 Custom-Emitter-Verweise auf
  `grid_gym.hexagon.core.serialization.canonical`. Header
  `Letzte inhaltliche Aenderung` auf 2026-05-15 aktualisiert.
- `Dockerfile` `coverage-gate-critical`: vier `--cov=`-Pfade
  auf `src/grid_gym/hexagon/core/{simulation,devices/battery,scenario,replay}`
  umgestellt (downstream zu Trigger 011).
- `docs/plan/planning/`: Trigger
  `011-hexagon-layout-adr-0002-realign.md` von `open/` nach
  `done/` verschoben (Closure-Notiz mit Lieferumfang); `open/`-
  und `done/`-README-Bestandstabellen entsprechend gepflegt.
- `docs/plan/planning/next/spike-0.md` — Slice-Plan fuer Spike-0
  als Pre-Acceptance-Pflichtnachweis fuer `ADR 0002` und
  `ADR 0005`. Fuenf Wellen (Toolchain/Skelett, A-2 Custom-Emitter,
  `tools/arch_check.py` Contracts, 16 Verstoss-Branches,
  Acceptance-Hebung); Erfolgskriterien, Out-of-Scope-Liste,
  Risiken/Fallback und Verifikationspfad explizit ausgewiesen.
  `docs/plan/planning/next/README.md` Bestandstabelle ergaenzt.
- `docs/plan/planning/in-progress/roadmap.md` §4 Vorbedingungen
  praezisiert: `GG-AR-OPEN-001` verweist auf `next/spike-0.md`;
  Repository-Layout-Punkt verweist auf `hexagon/`-Gruppierung in
  `architecture.md` §4.2.
- **Spike-0 Welle 1** — Toolchain und Skelett:
  - `pyproject.toml` mit `[project]`, `[build-system]`
    (hatchling), `[dependency-groups]` (lint/arch/typecheck/
    test/audit/dev), `[tool.ruff.lint]` mit A-1-Regeln und
    Preview-Mode (`PLR0904`/`PLR0916` brauchen Preview in ruff
    0.15), `[tool.ruff.lint.flake8-tidy-imports]`,
    `[tool.ruff.lint.per-file-ignores]`,
    `[tool.ruff.lint.mccabe]`, `[tool.ruff.lint.pylint]`,
    `[tool.mypy]` `strict = true` mit Scope `files = ["src/grid_gym", "tools"]`,
    `[tool.importlinter]` mit `include_external_packages = true`
    und sieben Forbidden-Contracts (AC-CORE-NO-ADAPTERS,
    AC-CORE-NO-DRIVING, AC-PORTS-NO-OUT, AC-PORTS-NO-FW,
    AC-ADAPTER-PURE, AC-NO-FW, AC-NO-IO-MOD),
    `[tool.grid_gym.arch_check]` mit Whitelists,
    `[tool.pytest.ini_options]` mit Markern (`determinism`,
    `replay`, `fault`), `[tool.coverage.*]`.
  - `.python-version` → `3.14`.
  - `uv.lock` mit 65 Packages, alle aktuelle Versionen
    (ruff 0.15.13, mypy 2.1.0, import-linter 2.11, grimp 3.14,
    pytest 9.0.3, pytest-cov 7.1.0, hypothesis 6.152.7,
    pip-audit 2.10.0, openapi-spec-validator 0.8.5).
  - Skelett: `src/grid_gym/__init__.py` plus
    `hexagon/{__init__.py,core/{__init__.py,errors.py,
    domain,simulation,devices,scenario,replay,faults,agents,
    serialization}/__init__.py,ports/{driving,driven}/__init__.py}`
    und `adapters/{__init__.py,driving/__init__.py,driven/__init__.py}`.
    Sub-Pakete `domain..serialization` sind als leere Module
    angelegt, damit import-linter sie als Modulreferenz aufloesen
    kann.
  - `hexagon/core/errors.py` mit `GridGymError(Exception)` als
    Wurzel-Fehlerklasse (AC-TYPED-ERRORS, GG-CC-008).
  - `tools/arch_check.py` als ausfuehrbares Skelett (laedt
    `[tool.grid_gym.arch_check]` aus `pyproject.toml`, baut
    Import-Graph via `grimp`, gibt Zusammenfassung aus —
    Contract-Logik kommt in Welle 3).
  - `tests/__init__.py`, `tests/unit/__init__.py`,
    `tests/arch/__init__.py` plus
    `tests/unit/test_skeleton.py` mit zwei Smoke-Tests fuer
    `GridGymError`.
  - **Gate-Verifikation (alle gruen via Dockerfile-Stage):**
    `make lint` (ruff check, 23 files), `make format-check`
    (23 files), `make typecheck` (mypy --strict, 19 source
    files, 0 issues), `make arch-check` (7 Contracts kept),
    `make test-unit` (2 tests passed), `make dep-audit`
    (0 vulnerabilities in 65 packages).
- `Dockerfile` `source`-Stage: `COPY LICENSE README.md ./`
  ergaenzt — hatchling braucht beide fuer den editable Install
  im `uv sync --frozen --all-groups`.
- `Makefile` `lock-refresh`: Bug behoben. Das distroless
  `ghcr.io/astral-sh/uv:VERSION`-Image hat `/uv` als ENTRYPOINT
  und keine Shell — `uv lock` schlug mit ELF-Interpreter-Fehler
  fehl. Jetzt laeuft `lock-refresh` im projekteigenen
  `base`-Stage (python:3.14-slim + uv 0.5.31 gepinnt) als
  aktueller User (`--user $(id -u):$(id -g)` plus
  `UV_CACHE_DIR=/tmp/uv-cache`), produziert `uv.lock` mit
  korrekter User-Ownership.
- `docs/plan/planning/next/spike-0.md` Welle 3: neuer Contract
  `AC-HEXAGON-PURE` aufgenommen (Whitelist-basiert via
  `tools/arch_check.py`: Module unter `src/grid_gym/hexagon/**`
  duerfen nur stdlib, `grid_gym.*` und explizit whitelistete
  Dritt-Pakete (z. B. `pydantic` fuer `FrozenModel`)
  importieren — ersetzt brueckhafte Blacklist-Pflege in
  `AC-NO-FW` durch robuste Positive-Liste).
- `.gitignore` erweitert um Python-Build-/Test-Artefakte
  (`.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`,
  `.ruff_cache/`, `.mypy_cache/`, `coverage/`, `.hypothesis/`),
  Build-Output (`build/`, `dist/`) und IDE-Dateien
  (`.idea/`, `.vscode/`, `*.swp`). Projekt-Policy ist
  Docker-only — lokale Python-Umgebungen sollen nicht entstehen;
  die Eintraege fangen versehentliche Artefakte ab.
- `.dockerignore` neu angelegt. Reduziert den Build-Kontext auf
  die tatsaechlich per `COPY` referenzierten Pfade
  (`pyproject.toml`, `uv.lock`, `.python-version`, `src/`,
  `tests/`, `tools/`, `spec/`, `LICENSE`, `README.md`).
  Schliesst `.git/`, `.github/`, `docs/`, Editor-/IDE-Dateien,
  alle Python-Caches und die Projekt-Agent-Verzeichnisse aus.
  Beschleunigt jeden `docker build`-Aufruf und stabilisiert
  den Layer-Cache.
- **Spike-0 Welle 2** — A-2 Custom-Emitter + Property-Tests:
  - `src/grid_gym/hexagon/core/serialization/canonical.py` mit
    `canonical_json(value: object) -> bytes` nach ADR 0002 §A-2
    Punkt 3 (stdlib-only Custom-Emitter, kein `json.dumps`).
    Eigenschaften: lexikographisch sortierte Dict-Keys,
    Fixed-Point-Notation fuer `Decimal` (`format(d, "f")`,
    Tail-Nullen bleiben erhalten), RFC-8259-konformes
    String-Escape (Steuerzeichen als `\\u00XX`), UTF-8-Bytes
    als Ergebnistyp.
  - Vier typisierte Fehlerklassen (AC-TYPED-ERRORS-konform,
    TRY003-clean): `CanonicalSerializationError` als Wurzel
    (erbt von `GridGymError`), `FloatNotAllowedError`,
    `NonFiniteDecimalError` (NaN/Infinity),
    `NonStringDictKeyError`, `UnsupportedTypeError(type_name)`.
  - `tests/unit/hexagon/core/serialization/test_canonical.py`
    mit 42 Tests: Basis-Typen (None/bool/int/str/list/dict),
    Decimal-Verhalten, Fehler-Faelle, sechs `hypothesis`-
    Property-Tests (Fixed-Point-Equivalence, Dict-Reihenfolge-
    Unabhaengigkeit, String-Roundtrip via `json.loads`,
    Listen-Laenge, Integer-Roundtrip, Decimal-in-Dict),
    Domain-Skizzen fuer Telemetry/Command/Event mit Roundtrip-
    Byte-Stabilitaet.
  - Test-Package-Skelett (`tests/unit/hexagon/__init__.py`,
    `tests/unit/hexagon/core/__init__.py`,
    `tests/unit/hexagon/core/serialization/__init__.py`).
  - **Gate-Verifikation:**
    - `make test-unit`: 44 tests passed (2 Skelett + 42 canonical).
    - `make coverage-gate-critical CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization`:
      100 % Line + Branch auf 79 Statements / 38 Branches.
    - `make coverage-gate`: 100 % Branch auf `src/grid_gym`.
    - Regression: `make lint`, `make typecheck`, `make arch-check`
      bleiben gruen.
- `Dockerfile` `coverage-gate-critical`-Stage parametrisiert: neuer
  `ARG CRITICAL_COV_TARGETS` (Default: kritische Domain laut
  GG-COV-003 — `simulation`/`devices/battery`/`scenario`/`replay`),
  ueberschreibbar via `--build-arg` fuer Wellen mit Teilbereich.
  Shell-Loop expandiert die leerzeichengetrennte Liste zu
  `--cov=`-Argumenten fuer pytest.
- `Makefile` `coverage-gate-critical`-Target reicht
  `CRITICAL_COV_TARGETS` als optionalen Build-Arg-Override durch
  (`make coverage-gate-critical CRITICAL_COV_TARGETS=...`).
- `docs/plan/planning/next/spike-0-results.md` als Living Document
  fuer Spike-0 angelegt: Welle-Status, Verstoss-Branch × Gate
  Matrix (sechzehn Branches), Befunde aus Welle 1+2 (uv-Image-
  Eigenheiten, hatchling-LICENSE/README-Bedarf, ruff-0.15-Drift
  gegenueber ADR 0002 §A-1, import-linter-Subpaket-Limit,
  coverage-gate Build-Arg-Parametrisierung) und Drift-Liste fuer
  den finalen ADR-Schliff vor Acceptance.
- **Spike-0 Welle 5 — Acceptance-Hebung (Milestone):** `ADR 0002`
  und `ADR 0005` von `Provisional → Accepted` (Status geaendert am
  2026-05-15). Per `ADR 0006` §3 sind beide Entscheidungstexte ab
  jetzt immutable; Aenderungen an A-1-/A-2-Vertraegen oder am
  mypy-Strict-Gate erfordern Nachfolge-ADRs.
  - **Pre-Acceptance-Review** (zweiter Review durch `code-reviewer`-
    Subagent) abgearbeitet: 3 Blocker (B-A asyncio, B-B HEXAGON-PURE-
    Listung, B-C `make fullbuild`-Reduktion) und 10 Drift-Items
    (D-1..D-10) eingearbeitet in vier Commits `fb90154`, `201daee`,
    `658c037`, `46b4ce6`.
  - **`spec/architecture.md §19`**: `GG-AR-OPEN-001` von „Offen
    (Spike-0 laeuft)" auf „Geschlossen mit `ADR 0002` (Accepted
    2026-05-15)" — mit Verweis auf beide Accepted-ADRs.
  - **`roadmap.md §4`**: Vorbedingungen 1 (`GG-AR-OPEN-001`) und 3
    (initiales Repository-Layout) mit Haken markiert und mit
    Closure-Notiz verlinkt; Vorbedingung 2 (`GG-AR-OPEN-002`) bleibt
    offen — eigene Folge-ADR.
  - **Headers verbindlich**: `Dockerfile`, `Makefile`, `pyproject.toml`
    von „Spike-0-Pfad gemaess ADR 0006 (Provisional)" auf
    „Verbindlicher Stack gemaess ADR 0002 Accepted 2026-05-15"
    umgestellt. Aenderungen an `pyproject.toml`-Vertraegen brauchen
    fortan Folge-ADRs.
  - **Closure-Notiz**: `docs/plan/planning/next/spike-0.md` und
    `spike-0-results.md` per `git mv` nach `done/` verschoben
    (100 %-Rename via Zwei-Commit-Pattern, Memory-konform);
    `done/spike-0.md` §0 traegt Welle-1..5-Tabelle (Commit-Refs),
    Verweise auf Matrix (§3 in `spike-0-results.md`), Befunde (§4),
    Review-Trail (§6), Drift-Items-Liste (§5), „was bleibt offen"
    (`GG-AR-OPEN-002..010`, Triggers 009/010, M1-Vorbereitungen).
  - **Spike-0-Abschluss-Gate**: `make gates` (Aggregator: `lint`,
    `format-check`, `typecheck`, `arch-check`, `test-unit`,
    `coverage-gate`, `coverage-gate-critical
    CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization`,
    `dep-audit`) gruen. `make fullbuild` wandert als
    M1-Abnahmebedingung (siehe Triggers 009/010 in `open/`).
  - **Commits**: `5763445` (ADRs + arch.md §19 + roadmap.md §4),
    `3645473` (Headers), `522ec17` (pure rename next/ → done/),
    plus dieser Commit (Closure-Section + READMEs).
- **Spike-0 Welle 4** — Verstoss-Verifikation (18 von 18 Contracts mit
  Zaehnen): pro Contract eine Violation auf `main` eingebaut, das
  erwartete Gate als rot bestaetigt, Violation sauber zurueckgerollt.
  Matrix in `docs/plan/planning/next/spike-0-results.md` §3 vollstaendig.
  Verify-and-revert ohne persistente Branches (Stay-on-Main-Policy).
  - 5 Contracts via `import-linter` (`AC-CORE-NO-ADAPTERS`,
    `AC-CORE-NO-DRIVING`, `AC-PORTS-NO-OUT`, `AC-PORTS-NO-FW`,
    `AC-ADAPTER-PURE`, `AC-NO-FW`, `AC-NO-IO-MOD` top-level).
  - 11 Contracts via `tools/arch_check.py` (`AC-HEXAGON-PURE`,
    `AC-NO-IO-MOD` nested, `AC-ADAPTER-LIGHTWEIGHT`, `AC-NO-CYCLES`,
    `AC-NO-TIME`, `AC-NO-RAND`, `AC-NO-JSON`, `AC-DOMAIN-FROZEN`,
    `AC-NO-GOD-UTILS`, `AC-TYPED-ERRORS` (Tuple-Form bestaetigt
    Welle-3-Fix B-3)).
  - 1 Contract via `mypy --strict` (LSP variance: `[override]` +
    `[explicit-override]` bei Return-Typ-Erweiterung `int` → `object`).
  - `AC-NO-CYCLES` Dedup-Mechanik aus dem B-2-Fix bestaetigt: ein
    2-Modul-Zyklus erzeugt eine einzige Violation, nicht zwei.
- **Coverage-Gate Negativ-Verifikation (Welle 2):**
  - **pytest-cov-Schiene** (`--cov-fail-under=90`, kombiniert):
    bewusst eingefuegte ungetestete Funktion drueckte Coverage
    auf 79.73 %, Stage rot mit `FAIL Required test coverage of
    90% not reached`. Nach Revert wieder 100 %, working tree clean.
  - **XML-Branch-Schiene** in Isolation: synthetische
    `coverage-critical.xml` mit `branch-rate="0.5"` an die
    Python-Check-Logik des Dockerfile-Stages gefuettert; meldet
    `50.00% < 90.00%`, exit 1. Sanity mit `branch-rate="0.95"`:
    exit 0.
  - **Erkenntnis:** coverage.py mit `--cov-branch` decomposiert
    one-line `if cond: body` nicht in separate Branch-Arcs;
    Statement-Level-Branches fuehren immer dazu, dass Line- und
    Branch-Coverage zusammen fallen. Damit feuert pytest-cov's
    kombinierter Check vor dem XML-Branch-Check. Die XML-Schiene
    ist defense-in-depth, nicht Hauptgate. Befund dokumentiert
    in `spike-0-results.md` §4.2.
- **Spike-0 Welle 3** — `tools/arch_check.py` Contract-Implementierung:
  - Framework: `Violation`-Datentyp (`@dataclass(frozen=True, slots=True)`),
    `ArchCheckConfig` aus `[tool.grid_gym.arch_check]` in
    `pyproject.toml`, AST-Walker, stderr-Output im Format
    `{contract_id}\\t{location}\\t{detail}`, Exit-Code 0/1.
  - Neun Contracts implementiert, die `import-linter` und `ruff`
    nicht abdecken:
    - **`AC-HEXAGON-PURE`** (Whitelist): Module unter
      `src/grid_gym/hexagon/**` duerfen nur stdlib (via
      `sys.stdlib_module_names`), `grid_gym.*` und explizit
      whitelistete Dritt-Pakete (`hexagon-import-whitelist` in
      `[tool.grid_gym.arch_check]`) importieren.
    - **`AC-NO-JSON`**: `json.dumps`/`json.dump`-Aufrufe ausserhalb
      der `json-dumps-whitelist` (heute nur
      `hexagon/core/serialization/canonical.py`).
    - **`AC-NO-TIME`** (Aufruf-Site): `time.time`/`time.monotonic`/
      `time.perf_counter`/`time.perf_counter_ns`/`time.process_time`
      unter `hexagon/core/**`.
    - **`AC-NO-RAND`** (Aufruf-Site): `random.*`/`secrets.*`/
      `numpy.random.*` unter `hexagon/core/**`.
    - **`AC-DOMAIN-FROZEN`**: Klassen in `hexagon/core/domain/**`
      (plus `domain-frozen-extra`) muessen
      `@dataclass(frozen=True, ...)` oder von `FrozenModel` erben.
    - **`AC-NO-GOD-UTILS`**: Modul-Namen (`*_utils.py`, `helpers.py`,
      `common.py`, `misc.py`), Klassen-Namens-Suffixe
      (`Utils`/`Helper`/`Manager`/`Misc`), max. 5 oeffentliche
      Top-Level-Funktionen ausserhalb `hexagon/core/domain` und
      `hexagon/core/serialization`.
    - **`AC-TYPED-ERRORS`**: kein `raise Exception(...)` /
      `raise BaseException(...)`; `except Exception:` nur in
      `typed-errors-exempt`-Pfaden.
    - **`AC-NO-CYCLES`**: Importzyklen via `grimp.build_graph`
      und `find_shortest_chain`-Rueckpfaden zwischen direkten
      Import-Paaren.
    - **`AC-ADAPTER-LIGHTWEIGHT`**: zyklomatische Komplexitaet
      `<= 8` fuer Funktionen unter
      `adapters/driven/protocol_*`/`persistence_*` und
      `adapters/driving/**`.
  - `[tool.grid_gym.arch_check]` um `hexagon-import-whitelist`
    erweitert.
  - **Gate-Verifikation (alle gruen via Dockerfile-Stages + make):**
    - `make arch-check`: 7 import-linter Contracts kept,
      arch_check.py meldet „all contracts kept" (9 AST-/grimp-
      Contracts gruen).
    - `make lint`/`format-check`/`typecheck`: Regression gruen
      (mypy --strict, 21 source files).
    - `make test-unit`: 44 tests passed.
    - `make coverage-gate-critical CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization`:
      100 % Line + Branch.
- `tests/unit/hexagon/core/serialization/test_canonical.py`:
  Float-Equality-Vergleiche auf `pytest.approx` umgestellt
  (`RUF069`-Compliance unter ruff 0.15 preview-Mode).

### Fixed

- A-2 in ADR 0002: `json.JSONEncoder`-Subklassen-Ansatz konnte
  verschachtelte `Decimal`-Werte nicht serialisieren
  (`json.dumps`/`default()`-Mechanik laesst rohe JSON-Zahlen aus
  `default` nicht zu). Ersetzt durch einen kleinen Custom-Emitter
  (~60 Zeilen, stdlib-only) mit deterministischer Reihenfolge,
  Fixed-Point-`Decimal`-Ausgabe und explizitem `float`-Verbot.
- Lifecycle-Sprache in ADR 0002 an ADR 0006 angeglichen: Vor
  Acceptance scheitert Spike-0 nach `Rejected`; nach Acceptance
  unhaltbare A-1/A-2 fuehren zu `Superseded` durch Nachfolge-ADR
  (nicht „zurueckgezogen", was per ADR 0006 nur als `Withdrawn`
  und nur pre-Beschluss zulaessig waere).
- Spike-0-Vertrag von drei auf vier Gates erweitert
  (`lint-imports`, `ruff check`, `arch_check.py`, `mypy --strict`).
  ADR 0005 ist damit synchroner Bestandteil der Acceptance, nicht
  optionale Folge-Entscheidung.
- ADR 0002 von `Proposed` auf `Provisional` gehoben — die
  Spike-0-Artefakte (`Dockerfile`, `Makefile`) liegen vor und
  bilden den validierten Pfad gemaess ADR 0006. ADR 0005
  ebenfalls auf `Provisional` (synchron). Status-Header beider
  ADRs um `Status geaendert am` und `Letzte inhaltliche Aenderung`
  ergaenzt.
- Dockerfile- und Makefile-Header als Spike-0-Pfad gekennzeichnet
  (ADR 0006).
- `GG-AR-OPEN-001`-Eintrag in `architecture.md` an den neuen
  Provisional-Status angepasst („Vorgeschlagen, Spike-0 laufend",
  Status-Spalte „Offen (Spike-0 laeuft)") gemaess ADR 0006
  Formelhilfe.
- ADR 0003 per `Superseded`-Metadaten auf ADR 0006 umgestellt; der
  historische Entscheidungstext bleibt unveraendert.
- §7 Offene Folge-Punkte in ADR 0002: Kanonische-Serialisierung-
  Eintrag von „Formatdetails verfeinern" auf „Performance-/
  Implementierungs-Alternativen" umgestellt — die Format-Details
  sind durch A-2 jetzt fix, eine Folge-ADR darf nur die
  Umsetzungsroute aendern und muss Byte-Gleichheit nachweisen.
- `Dockerfile` `typecheck`-Stage: `uv run mypy --config-file pyproject.toml`
  ohne Kommandozeilen-Pfade aufgerufen. Die `[tool.mypy] files`-
  Direktive (`ADR 0005` §5.1) ist damit alleinige Single-Source-of-
  Truth fuer den Scope-Vertrag; Kommandozeilen-Pfade haetten die
  Direktive ueberlagert.
