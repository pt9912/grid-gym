# Welle 2a — EV-Charger (`GG-DEV-015`, ADR 0055)

**Status:** Done (M8-Welle-2a, geschlossen 2026-06-14) — erstes SOLLTE-
Geraet aus [`M8-welle-2.md`](M8-welle-2.md) §3. Reine Core-Domain-
Erweiterung (kein neuer Port/Adapter-Typ) + die zugehoerigen
Verdrahtungs- und Validierungs-Naehte.

**Container:** [`M8-welle-2.md`](M8-welle-2.md) (Welle-2-C0-Plan, Sub-
Slicing 2a..2d); [`roadmap.md`](../in-progress/roadmap.md) §4 M8. Design (C1):
[`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md) `Accepted`.
Trigger: [`016`](../open/016-sollte-ev-charger-device.md) (mit dieser
Welle aufgeloest).

---

## 1. Lieferziel

Das EV-Ladepunkt-Modell ([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015), Lastenheft §9.4) als
`DeviceModel` + `FaultInjectableDevice` im Core, mit Fahrzeug-SoC,
CC/CV-Ladekennlinie, durchgaengigem V2G und `connection_loss`-Fault
([`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md)). Inklusive Loader-Factory, Scenario-YAML-Coercion,
TickLoop-Snapshot-Key, Alarm-Mapper, HTTP-`POST /faults`-Whitelist,
Visualization-State-Subset und `CRITICAL_COV_TARGETS`-Erweiterung.

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [x] **Modell + Tests**: NEU `hexagon/core/devices/ev_charger/`
      (`config`/`commands`/`snapshot`/`model`) — Snapshot-Roundtrip +
      ≥ 100-Tick-Determinismus-Property + CC/CV/V2G/Energie-Limit +
      `connection_loss`-Fault gepinnt
      ([`test_ev_charger_device.py`](../../../../tests/unit/hexagon/core/devices/ev_charger/test_ev_charger_device.py),
      [`test_fault_injection.py`](../../../../tests/unit/hexagon/core/devices/ev_charger/test_fault_injection.py)).
- [x] **End-to-End-Verdrahtung**: `_DEVICE_FACTORIES["ev_charger"]`,
      `DEVICE_DECIMAL_PARAMS`, `_DEVICE_TYPE_BY_CLASS_NAME`,
      Alarm-Mapper, `_FAULT_TYPE_TO_DEVICE_TYPE`, Szenario-Beispiel
      [`ev_charger_demo.yaml`](../../../../tests/integration/scenarios/ev_charger_demo.yaml)
      + Smoke
      ([`test_ev_charger_scenario.py`](../../../../tests/integration/test_ev_charger_scenario.py)).
- [x] **Gates**: `make gates` gruen (10 A-1-Gates), inkl.
      `coverage-gate-critical` ≥ 90 % auf `devices/ev_charger`
      (Dockerfile-`CRITICAL_COV_TARGETS`-Default erweitert);
      `make docs-check` gruen. [`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md) `Accepted`, Trigger 016
      aufgeloest.

## 3. Realization-Notes (Abweichungen ggue. ADR-Wortlaut)

- **Fault-Flag im `fault_state`-Sub-Block**: [`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md) §2.8 listet
  `connection_loss_active` als Snapshot-Feld; die Realisierung legt es
  — wie Battery/GridConnection ([`ADR 0025`](../../adr/0025-fault-recovery-pattern.md) §2.2) — in den additiven
  `fault_state`-Block, damit der UI-`_snap_fault_flag`-Extractor und
  die Backward-Compat-Defaults uniform greifen.
- **Param-Validierung am Config-Rand**: [`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md) §4 /
  [`016`](../open/016-sollte-ev-charger-device.md) sprechen von einer
  Validator-Schaerfung; analog zu allen fuenf Bestandsgeraeten lebt die
  `params`-Pruefung im `EvChargerConfig.__post_init__` +
  `_config_from_params` (struktureller Validator bleibt typ-generisch).
  Extra-`params`-Keys werden — wie bei den Bestandsgeraeten — still
  ignoriert (kein `extra="forbid"` auf Loader-Ebene).
- **Scenario-getriebener EV-Fault** ist NICHT enthalten: Welle 2a
  liefert die `FaultInjectableDevice`-Surface + den HTTP-`POST /faults`-
  Pfad; eine zeitgefensterte `EvChargerFaultEngine` (analog
  `BatteryFaultEngine`) ist Folge-Slice ([`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md) §6). Der
  Integration-Smoke faehrt den EV daher idle (Determinismus + Wiring),
  die Lade-/V2G-/Fault-Dynamik ist im Unit-Test gepinnt.
- **`D-7`-Adoption** (Pre-init-Defense, [`M8-welle-2.md`](M8-welle-2.md)
  §3): die `snapshot()`/`telemetry()`-Pre-init-Pfade liefern minimal
  (`{"version": 1}` / `()`); `_extract_ev_charger_state` gibt bei
  pre-init `None` zurueck (Aufrufer silent-droppt). Erste device-
  iterierende Sub-Welle → `D-7` hier adoptiert.

## 4. Lerneintrag (Closure-Pflicht)

**Geschaerfte Regel:** Ein neues Device-Submodul beruehrt **acht**
Naehte, nicht nur Factory + Snapshot — der Erst-Reflex „Factory +
`_DEVICE_TYPE_BY_CLASS_NAME`" ist unvollstaendig. Vollstaendige
Checkliste fuer Welle 2b-d (Transformer/Wind/Diesel): (1) Submodul,
(2) `_DEVICE_FACTORIES`, (3) `_DEVICE_TYPE_BY_CLASS_NAME` +
`test_loader_factory_sync`, (4) `DEVICE_DECIMAL_PARAMS` +
`test_yaml_loader_allowlist` (das die Config-Klassen-Liste mitfuehrt),
(5) `alarm_mappers` (falls Alarme), (6) `_FAULT_TYPE_TO_DEVICE_TYPE`
(falls Fault), (7) `_runs_router._STATE_EXTRACTORS` (UI), (8)
`CRITICAL_COV_TARGETS` (Dockerfile-Default). Die zwei Sync-/Drift-Tests
(3)+(4) fangen das Vergessen fail-fast — sie sind der Sensor, der den
Lerneintrag bereits computational durchsetzt.

## 5. Review-Folge

High-effort `/code-review` (Rollentrennung, separate Finder-Kontexte) ueber
den Welle-2a-Diff. **Adressiert:**

- Test-Schaerfung: `test_energy_limit_caps_charge_near_full` pinnt jetzt
  zusaetzlich die Energie-Konsistenz (`charged_kwh == power * dt ==
  headroom`, [`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md)
  §2.8 Schritt 3) — vorher nur `power_kw`/`soc`,
  sodass eine falsche `energy_signed`-Akkumulation unentdeckt geblieben
  waere.
- NEU `test_cc_cv_boundary_at_threshold_charges_full` — Boundary bei
  `soc == cv_phase_start_soc` (Kennlinien-Stetigkeit am CC→CV-Uebergang).
- Cleanup/Altitude: SoC-Berechnung in EIN `_soc(config)`-Helper extrahiert
  (vorher zweifach: Kennlinie + Telemetrie), beseitigt das Drift-Risiko.

**Bewusst deferred** (Rationale dokumentiert, nicht still verworfen):

- Command-Pfad-Clamp laeuft ausserhalb des `prec=28`-Localcontext (nur
  `tick()` ist gepinnt) — **identisches Muster in Battery/GridConnection**;
  ein konsistenter Fix ist cross-device und out-of-scope fuer 2a.
- `_connection_loss_from_state` ist die dritte Kopie des optionalen
  `fault_state`-Bool-Readers (Battery/GridConnection teilen sie) — ein
  geteilter `snapshot_codec`-Helper beruehrt drei Devices; eigener
  Dedup-Folge-Slice.
- Scenario-getriebene `EvChargerFaultEngine` +
  command-getriebener Integration-E2E — Folge-Slice
  ([`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md) §6); 2a
  liefert Device-Surface + HTTP-Fault-Pfad, der Smoke faehrt idle.
  Command-E2E-Teil getrackt als Trigger
  [`046`](046-command-driven-integration-e2e.md).
