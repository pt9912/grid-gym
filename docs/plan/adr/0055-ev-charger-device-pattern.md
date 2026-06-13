# ADR 0055 — EV-Charger-Device-Pattern (M8 Welle 2a)

**Status:** Proposed
**Datum:** 2026-06-13
**Bezug:**

- [`ADR 0013`](0013-device-model-protocol.md) — `DeviceModel`-
  Protocol (Pflicht-Surface: `initialize`/`apply_command`/`tick`/
  `snapshot`/`telemetry`/`from_snapshot`/`device_id`/`set_run_id`).
- [`ADR 0017`](0017-grid-connection-device-pattern.md) — GridConnection-
  Pattern; Muster fuer Set-Power-Command + Energie-Akkumulation +
  Sign-Konvention, an dem sich dieses Geraet eng orientiert.
- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — ADR-Lifecycle.
- [`spec/lastenheft.md`](../../../spec/lastenheft.md) — `GG-DEV-015`
  (EV-Ladepunkt, SOLLTE).
- [`016-sollte-ev-charger-device.md`](../planning/open/016-sollte-ev-charger-device.md)
  — Trigger-Doc; [`M8-welle-2.md`](../planning/in-progress/M8-welle-2.md)
  — Wellen-Plan.

---

## 1. Kontext

`GG-DEV-015` definiert einen **EV-Ladepunkt** als SOLLTE-Geraet. Akzeptanz:
ein **Minimalmodell**, ein **Szenario-Beispiel** und ein **deterministischer
Smoke-Test**. M2 hielt das out-of-scope; M8-Welle 2 aktiviert es als erstes
SOLLTE-Geraet (Welle 2a).

Ein EV-Ladepunkt ist fachlich eine **steuerbare Last** (Laden) mit
optionaler **bidirektionaler Einspeisung** (V2G, Entladen) am
Anschlusspunkt, plus einem **Stecker-Zustand** (ob ein Fahrzeug verbunden
ist). Das Set-Power-Command + Energie-Akkumulations-Muster von
[`ADR 0017`](0017-grid-connection-device-pattern.md) (GridConnection)
passt direkt; dieses Geraet ergaenzt es um Lade-/Entlade-Caps und den
Stecker-Zustand.

## 2. Entscheidung

### 2.1 Modul-Struktur

Submodul `hexagon/core/devices/ev_charger/` analog `grid_connection/`:
`config.py` (`EvChargerConfig` + Validierungs-Fehler), `model.py`
(`EvChargerDevice`), `snapshot.py` (`EvChargerSnapshot` + `to_dict`/
`from_dict` + `SNAPSHOT_VERSION = 1` + `CONFIG_FIELD_NAMES`),
`commands.py` (Command-Validierung), `__init__.py` (Re-Export).

### 2.2 Sign- und Plug-Konvention

- `power_kw > 0` = **Laden** (Fahrzeug bezieht Energie, Last am Netz).
- `power_kw < 0` = **V2G-Entladen** (Fahrzeug speist ein).
- `power_kw == 0` = idle.
- `plug_state ∈ {"plugged", "unplugged"}`. **Bei `unplugged` ist
  `power_kw` hart `0`** — ohne Fahrzeug kein Energiefluss.

### 2.3 Config

`EvChargerConfig` (frozen, `slots`, `Decimal`-Felder; Validierung in
`__post_init__`, Verstoss → `EvChargerConfigInvalidValueError`):

- `max_charge_kw` — Lade-Cap (positiver Betrag), `> 0`.
- `max_discharge_kw` — V2G-Entlade-Cap (positiver Betrag), `>= 0`
  (`0` deaktiviert V2G; ein negatives Set-Power-Command wird dann
  `rejected`).
- `nominal_voltage_v` — Nennspannung am Ladepunkt, `> 0`.

Der **Initial-Stecker-Zustand** kommt aus dem optionalen Scenario-Param
`initial_plug_state` (`"plugged"`/`"unplugged"`, Default `"unplugged"`)
und ist **kein** Config-Feld (dynamischer Zustand, nicht im
`scenario_hash`-relevanten Static-Set).

### 2.4 Command-Surface

Zwei Verben (typisierte `CommandResult`-Antworten, keine Exceptions fuer
Out-of-Bounds — analog ADR 0017 §2.4):

- `set_charge_power` (`value` in kW): bei `unplugged` → `rejected`. Sonst
  Clamp auf `[-max_discharge_kw, +max_charge_kw]`; ausserhalb → `limited`
  (auf den Cap gesetzt), innerhalb → `accepted`. Setzt `_pending_power_kw`.
- `set_plug_state` (`value` ∈ `{"plugged","unplugged"}`): wechselt den
  Stecker-Zustand; `→ unplugged` setzt `_pending_power_kw = 0`.

### 2.5 Tick-Mechanik

Welle-2a-Minimum (kein Ramp/Wirkungsgrad, analog ADR 0017 §2.5),
in `Decimal`-Localcontext (`prec=28`, `ROUND_HALF_EVEN`):

1. `new_power_kw = 0` falls `unplugged`, sonst `self._pending_power_kw`.
2. `self._current_power_kw = new_power_kw`.
3. `delta_kwh = abs(new_power_kw) * Decimal(tick_ms) / 3_600_000`;
   `new_power_kw > 0` → `charged_kwh += delta_kwh`; `< 0` →
   `discharged_kwh += delta_kwh`.
4. Telemetrie (alphabetisch sortiert, `quantize(0.000001)`):
   `charged_kwh` (kWh), `discharged_kwh` (kWh), `plug_state` (`1`/`0`,
   Einheit `"bool"`), `power_kw` (kW), `voltage_v` (V).

### 2.6 Snapshot-Layout

`EvChargerSnapshot` mit `version: int` als Erst-Feld, dann `device_id`,
`run_id`, `sequence`, `config` (alle 3 Felder), `plug_state`,
`current_power_kw`, `pending_power_kw`, `charged_kwh`, `discharged_kwh`.
`from_snapshot(snapshot()) == device` ist byte-stabil (`__eq__`/`__hash__`
ueber alle State-Felder + `device_id`/`run_id`/`sequence`).

### 2.7 Initialisierung + Determinismus

- `initialize`: Config aus `params` (`MissingKeysError`/`WrongTypeError`
  bei Struktur-Fehlern), `plug_state` aus `initial_plug_state`-Param,
  `power`/`energy` = `0`. Zweite Invocation → `DeviceAlreadyInitializedError`.
- Pre-init-Guards (`tick`/`apply_command`/`device_id` →
  `DeviceNotInitializedError`; `snapshot()` → `{"version": 1}`;
  `telemetry()` → `()`).
- Determinismus (`GG-SIM-001/004`): gleicher Seed + gleiche Command-Sequenz
  → byte-identische Telemetrie; `_random` wird im Welle-2a-Minimum nicht
  konsumiert (`attach_random` fuer spaetere Stochastik vorbereitet).

## 3. Begruendung

Das EV-Charger-Modell ist eine **steuerbare bidirektionale Last** — exakt
das GridConnection-Set-Power-Muster, ergaenzt um zwei Caps (statt
symmetrischer Import/Export) und einen Stecker-Zustand als hartes
Power-Gate. Wiederverwendung des etablierten Musters statt Neuerfindung
haelt die Determinismus-/Snapshot-Disziplin konsistent und den Smoke-Test
trivial vergleichbar.

## 4. Reichweite

Welle 2a liefert das Minimalmodell + Szenario-Beispiel
(`deploy/scenarios/`-YAML-Fragment) + deterministischen Smoke-Test
(`GG-DEV-015`-Akzeptanz). `CRITICAL_COV_TARGETS` um `devices/ev_charger`
erweitert; `_DEVICE_FACTORIES["ev_charger"]` in `core/scenario/loader.py`;
Scenario-Validator schaerft die `params`-Felder.

## 5. Konsequenzen

- Vierter steuerbarer Last-/Quelle-Typ neben Battery/PV/GridConnection;
  Muster bleibt einheitlich.
- Neue Snapshot-Familie (`ev_charger`-Subsystem) im Generic-Codec.
- `plug_state` als erster nicht-numerischer Geraete-Zustand — im Snapshot
  als String, in der Telemetrie als `1`/`0` projiziert.

## 6. Nicht Gegenstand dieser ADR

- Wirkungsgrad / Lade-Curve-Kennlinien (CC/CV-Phasen) / SoC eines
  konkreten Fahrzeug-Akkus — Welle-3+-Schaerfung.
- Multi-EV-Pool / Smart-Charging-Logik — eigenes ML-Slice.
- Protokollanschluss (ISO 15118 / OCPP) — Adapter-Slice (M4-Material).
- Fault-Injection fuer EV-Charger (`FaultInjectableDevice`) — kein
  EV-Fault-Typ im Welle-2-Closed-Set; spaetere Folge-ADR.
