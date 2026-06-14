# ADR 0055 — EV-Charger-Device-Pattern (M8 Welle 2a)

**Status:** Accepted
**Datum:** 2026-06-13
**Bezug:**

- [`ADR 0013`](0013-device-model-protocol.md) — `DeviceModel`-Protocol
  (Pflicht-Surface: `initialize`/`apply_command`/`tick`/`snapshot`/
  `telemetry`/`from_snapshot`/`device_id`/`set_run_id`).
- [`ADR 0014`](0014-battery-snapshot-schema.md) — Battery-Pattern; Muster
  fuer eine **endliche Ressource mit SoC** (Lade-/Entlade-Bilanz, Snapshot).
- [`ADR 0017`](0017-grid-connection-device-pattern.md) — GridConnection-
  Pattern; Muster fuer Set-Power-Command + Sign-Konvention + Energie-
  Akkumulation.
- [`ADR 0022`](0022-fault-injection-protocol.md) /
  [`ADR 0025`](0025-fault-recovery-pattern.md) — `FaultInjectableDevice` +
  Recovery-Muster (Vorbild fuer den EV-Fault).
- [`spec/lastenheft.md`](../../../spec/lastenheft.md) — `GG-DEV-015`.
- [`016-sollte-ev-charger-device.md`](../planning/open/016-sollte-ev-charger-device.md)
  — Trigger; [`M8-welle-2.md`](../planning/in-progress/M8-welle-2.md) — Plan.

---

## 1. Kontext

`GG-DEV-015` definiert einen **EV-Ladepunkt** (SOLLTE). Stakeholder-
Entscheidung (M8-Welle-2a): **realistisches Modell** statt Power-Flow-
Minimum — mit Fahrzeug-SoC, CC/CV-Ladekennlinie, **durchgaengig
bidirektionalem V2G** und EV-Fault-Injection. Damit ist der EV-Ladepunkt
fuer Demand-Response- und V2G-Demos brauchbar, nicht nur ein Stub.

Das Geraet kombiniert zwei bestehende Muster: das **Battery-Pattern**
([`ADR 0014`](0014-battery-snapshot-schema.md)) fuer den endlichen
Fahrzeug-Akku (SoC) und das **GridConnection-Set-Power-Muster**
([`ADR 0017`](0017-grid-connection-device-pattern.md)) fuer die steuerbare
bidirektionale Leistung am Anschlusspunkt.

## 2. Entscheidung

### 2.1 Modul-Struktur

Submodul `hexagon/core/devices/ev_charger/` analog `grid_connection/`:
`config.py`, `model.py` (`EvChargerDevice`, implementiert `DeviceModel` +
`FaultInjectableDevice`), `snapshot.py`, `commands.py`, `__init__.py`.

### 2.2 Sign-, SoC- und Plug-Konvention

- `power_kw > 0` = **Laden** (Bezug; fuellt den Fahrzeug-Akku).
- `power_kw < 0` = **V2G-Entladen** (Einspeisung; entleert den Akku).
- Fahrzeug-Akku-Zustand intern als `stored_kwh` (`0 .. battery_capacity_kwh`)
  gefuehrt — vermeidet Division-Drift; `soc = stored_kwh /
  battery_capacity_kwh` wird nur fuer Kennlinie + Telemetrie berechnet.
- `plug_state ∈ {"plugged","unplugged"}`. `unplugged` ODER aktiver
  `connection_loss`-Fault ⇒ `power_kw` hart `0`.

### 2.3 Config

`EvChargerConfig` (frozen, `slots`, `Decimal`; `__post_init__`-Validierung,
Verstoss → `EvChargerConfigInvalidValueError`):

- `max_charge_kw` — Lade-Cap, `> 0`.
- `max_discharge_kw` — V2G-Entlade-Cap, `> 0` (V2G ist durchgaengig aktiv,
  kein Opt-out).
- `nominal_voltage_v` — Nennspannung, `> 0`.
- `battery_capacity_kwh` — Kapazitaet des verbundenen Fahrzeug-Akkus, `> 0`.
- `cv_phase_start_soc` — SoC-Schwelle des CC→CV-Uebergangs,
  `0 < x <= 0.99` (z. B. `0.8`; Obergrenze haelt den Taper-Nenner
  `1 - cv_phase_start_soc` endlich).

Init-Params sind Scenario-`params` und damit **Teil des `scenario_hash`**
(`asdict(scenario)`) — gleicher Hash ⇒ gleicher Lauf, ADR-konform:
`initial_soc` (`0 .. 1`, Default `0.5`; in `initialize` zu
`initial_stored_kwh = initial_soc * battery_capacity_kwh` umgerechnet),
`initial_plug_state` (Default `"unplugged"`).

### 2.4 CC/CV-Ladekennlinie (Lade-Richtung)

Die **effektive** Lade-Leistung haengt vom SoC ab (Strombegrenzung bei
hohem SoC):

- **CC-Phase** (`soc < cv_phase_start_soc`): `effective_max_charge_kw =
  max_charge_kw` (Konstantstrom).
- **CV-Phase** (`cv_phase_start_soc ≤ soc < 1`): linearer Taper —
  `effective_max_charge_kw = max_charge_kw * (1 - soc) / (1 -
  cv_phase_start_soc)` (faellt von `max_charge_kw` bei `cv_phase_start_soc`
  auf `0` bei `soc = 1`).
- `soc = 1` (voll): `effective_max_charge_kw = 0`.

Ein Lade-Command wird auf `min(requested, effective_max_charge_kw)`
geclampt (`limited`, wenn der Request den effektiven Cap ueberschreitet).
Der lineare Taper ist die bewusst einfachste CV-Approximation; eine
exponentielle Kennlinie waere eine spaetere Schaerfung.

### 2.5 V2G-Entladung (Entlade-Richtung)

Entladung ist auf `max_discharge_kw` gecappt (flach, kein Taper) und
**hart bei `soc = 0` gestoppt** (leerer Akku ⇒ kein Entladen → `limited`/
`rejected`). Welle 2a hat keinen Entlade-seitigen CV-Taper.

### 2.6 Command-Surface

- `set_charge_power` (`value` kW): bei `unplugged`/`connection_loss` →
  `rejected`. Sonst nur **grobe Cap-Pruefung** gegen `[-max_discharge_kw,
  +max_charge_kw]` (ausserhalb → `limited` auf den Cap, sonst `accepted`);
  setzt `_pending_power_kw`. **Die SoC-/Kennlinien-abhaengige Begrenzung
  passiert NICHT hier, sondern pro Tick** (§2.8) — sonst clampte ein
  gehaltenes Command gegen einen veralteten SoC.
- `set_plug_state` (`value ∈ {"plugged","unplugged"}`): `→ unplugged`
  setzt `_pending_power_kw = 0` (Re-Aktivierung nach `plugged` braucht ein
  neues `set_charge_power`).

### 2.7 Fault-Injection

`EvChargerDevice` implementiert `FaultInjectableDevice` (ADR 0022 §2.1).
Welle-2a-Closed-Set: **ein** Typ `FAULT_TYPE_CONNECTION_LOSS =
"connection_loss"` (NEU in `core.domain.fault`, der Single-Source aus
041-C1) — simuliert einen Verbindungsabriss waehrend der Session: solange
aktiv, ist `power_kw` hart `0` (kein Energiefluss, SoC eingefroren), analog
`unplugged`. `inject_fault`/`clear_fault` symmetrisch + idempotent
(ADR 0025 §2.4); unbekannter Typ → `FaultUnsupportedTypeError`.

### 2.8 Tick-Mechanik + Snapshot + Determinismus

- Tick (`Decimal`-Localcontext, `prec=28`, `ROUND_HALF_EVEN`) — **die
  SoC-Begrenzung passiert pro Tick gegen den aktuellen `stored_kwh`, nicht
  beim Command** (sonst veralteter Clamp):
  1. `unplugged`/`connection_loss` ⇒ `new_power_kw = 0`.
  2. Sonst `requested = _pending_power_kw`, gegen den **aktuellen** SoC neu
     begrenzen: Laden auf `+effective_max_charge_kw(soc)` (CV-Taper §2.4),
     Entladen auf `-max_discharge_kw`.
  3. **Energie-Limit**: die Tick-Energie wird auf den verfuegbaren Rest
     gedeckelt — Laden auf `battery_capacity_kwh - stored_kwh`, Entladen auf
     `stored_kwh`. Reicht der Rest nicht fuer die volle Tick-Dauer, wird
     `new_power_kw` entsprechend reduziert, sodass **`power_kw`-Telemetrie
     und tatsaechlich gespeicherte Energie konsistent sind** (nie `soc > 1`
     oder `soc < 0`, keine Energie aus dem Nichts).
  4. `stored_kwh` um die tatsaechliche Tick-Energie fortschreiben (Ergebnis
     liegt per Konstruktion in `[0, battery_capacity_kwh]`); `charged_kwh`/
     `discharged_kwh` akkumulieren; `_current_power_kw = new_power_kw`.
- Telemetrie (alphabetisch, `quantize(0.000001)`): `charged_kwh`,
  `connection_loss` (`1`/`0`), `discharged_kwh`, `plug_state` (`1`/`0`),
  `power_kw`, `soc` (`0..1`), `voltage_v`.
- `EvChargerSnapshot` (`version=1`, Erst-Feld): `device_id`/`run_id`/
  `sequence`/`config`/`plug_state`/`stored_kwh`/`current_power_kw`/
  `pending_power_kw`/`charged_kwh`/`discharged_kwh`/`connection_loss_active`.
  `from_snapshot(snapshot()) == device` byte-stabil.
- Voll-`DeviceModel`-Surface inkl. `device_id`/`set_run_id` und
  `attach_random` (Random-Re-Attach nach `from_snapshot`, wie die fuenf
  Bestandsgeraete); Pre-init-Guards + `initialize`-Once analog ADR 0013/0017.

## 3. Begruendung

SoC + CC/CV macht den Ladepunkt fuer Demand-Response/V2G-Demos
realistisch; durchgaengiges V2G + Fault halten ihn als Multi-Agent-/
Resilienz-Szenario-Baustein brauchbar. Wiederverwendung der Battery-(SoC)-
und GridConnection-(Set-Power)-Muster haelt Determinismus + Snapshot
konsistent. Linearer CV-Taper + Single-Fault-Typ sind die bewusst
minimalen Realismus-Stufen mit klarem Schaerfungspfad.

## 4. Reichweite + Operative Artefakte

Welle 2a-C2/C3 — Integrationspunkte:

- `devices/ev_charger/`-Submodul; `_DEVICE_FACTORIES["ev_charger"]` in
  `core/scenario/loader.py`; Scenario-Validator-Schaerfung der `params`.
- NEU `FAULT_TYPE_CONNECTION_LOSS` in `core.domain.fault` (+ Re-Export ueber
  `core.faults.types`); **der HTTP-Fault-Validator-Whitelist
  `_FAULT_TYPE_TO_DEVICE_TYPE` in `_runs_action_router.py` bekommt
  `connection_loss → ev_charger`** (sonst lehnt `POST /faults` ihn mit 422 ab).
- `CRITICAL_COV_TARGETS += src/grid_gym/hexagon/core/devices/ev_charger`
  (`Dockerfile`-ARG + Makefile).

Akzeptanz `GG-DEV-015`: Modell + Szenario-YAML-Beispiel + deterministischer
Smoke-Test (Lade-CC/CV-Verlauf, V2G, `connection_loss`-Fault,
Snapshot-Roundtrip).

## 5. Konsequenzen

- Erster Geraete-Typ mit **SoC + Kennlinie + Fault** in einem Modell —
  zugleich das komplexeste SOLLTE-Geraet; setzt die Messlatte fuer Welle 2b-d.
- NEU Fault-Typ `connection_loss` im Closed-Set (`core.domain.fault`).
- `plug_state` als erster nicht-numerischer Zustand (Snapshot-String,
  Telemetrie-`1`/`0`).

## 6. Nicht Gegenstand dieser ADR

- Exponentielle/temperaturabhaengige Ladekennlinie, Entlade-CV-Taper —
  Welle-3+-Schaerfung (linearer CC/CV reicht fuer Welle 2a).
- Multi-EV-Pool / Smart-Charging-Logik — eigenes ML-Slice.
- Protokollanschluss (ISO 15118 / OCPP) — Adapter-Slice (M4-Material).
- Weitere EV-Fault-Typen (Ueberhitzung, Ladeabbruch-Codes) — Folge-ADR.
- Scenario-getriebene EV-Fault-Engine (`EvChargerFaultEngine` analog
  `BatteryFaultEngine`) fuer zeitgefensterte `connection_loss`-Injection
  im TickLoop — Folge-Slice (Welle-2a deckt die `FaultInjectableDevice`-
  Surface + den HTTP-`POST /faults`-Pfad; die zeitgesteuerte Window-
  Engine ist M-Folge-Material wie die produktive Composite-FaultPort).

## 7. Acceptance (Fitness Functions)

`Accepted` mit Welle 2a-C2/C3. Die Entscheidung ist maschinell gebunden:

- **Device-Submodul + Determinismus + Snapshot-Roundtrip** —
  [`tests/unit/hexagon/core/devices/ev_charger/test_ev_charger_device.py`](../../../tests/unit/hexagon/core/devices/ev_charger/test_ev_charger_device.py)
  (Config-Range, CC/CV-Taper, V2G, Energie-Limit, ≥ 100-Tick-
  Determinismus-Property, byte-stabiler Snapshot-Roundtrip) +
  [`test_fault_injection.py`](../../../tests/unit/hexagon/core/devices/ev_charger/test_fault_injection.py)
  (`connection_loss` Inject/Clear/Idempotenz, SoC-Freeze, `fault_state`-
  Roundtrip).
- **End-to-End-Wiring** — Szenario-Beispiel
  [`tests/integration/scenarios/ev_charger_demo.yaml`](../../../tests/integration/scenarios/ev_charger_demo.yaml)
  + Smoke
  [`test_ev_charger_scenario.py`](../../../tests/integration/test_ev_charger_scenario.py)
  (YAML → Decimal-Coercion → `load_scenario` → `build_tick_loop`,
  Determinismus, 7-Metrik-Surface).
- **Map-Konsistenz** — `_DEVICE_FACTORIES` ↔ `_DEVICE_TYPE_BY_CLASS_NAME`
  per `test_loader_factory_sync.py`; `DEVICE_DECIMAL_PARAMS`-Drift per
  `test_yaml_loader_allowlist.py`.
- **Gates** — `make gates` gruen (10 A-1-Gates), inkl.
  `coverage-gate-critical` ≥ 90 % auf
  `src/grid_gym/hexagon/core/devices/ev_charger` (Dockerfile-
  `CRITICAL_COV_TARGETS`-Default erweitert).
