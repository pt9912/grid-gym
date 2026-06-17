# Welle 2c — Wind-Turbine (`GG-DEV-017`, ADR 0057)

**Status:** Done (M8-Welle-2c, geschlossen 2026-06-14) — drittes SOLLTE-
Geraet aus [`M8-welle-2.md`](M8-welle-2.md) §3.

**Container:** [`M8-welle-2.md`](M8-welle-2.md); [`roadmap.md`](../in-progress/roadmap.md)
§4 M8. Design (C1):
[`ADR 0057`](../../adr/0057-wind-turbine-device-pattern.md) `Accepted`.
Trigger: [`018`](../open/018-sollte-wind-device.md) (mit dieser Welle
aufgeloest).

---

## 1. Lieferziel

Das Windkraftanlagen-Modell ([`GG-DEV-017`](../../../../spec/lastenheft.md#gg-dev-017), Lastenheft §9.4) als
`DeviceModel` im Core: command-loser Generator nach dem PV-Muster
([`ADR 0016`](../../adr/0016-pv-load-device-pattern.md)) mit **kubischer
Leistungskennlinie** (cut-in/rated/cut-out) und **stochastischem seeded
`RandomPort`-Windeingang** ([`ADR 0057`](../../adr/0057-wind-turbine-device-pattern.md)).
Geraetetyp `wind_turbine` (Lastenheft-kanonisch).

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [x] **Modell + Tests**: NEU `hexagon/core/devices/wind_turbine/`
      (`config`/`snapshot`/`model`) — kubische Kennlinie (direkt +
      via konstantem Wind `min == max`), ≥ 100-Tick-Determinismus-
      Property (seeded), Snapshot-Roundtrip + `attach_random`-Resume-
      Lifecycle
      ([`test_wind_turbine_device.py`](../../../../tests/unit/hexagon/core/devices/wind_turbine/test_wind_turbine_device.py)).
- [x] **End-to-End-Verdrahtung** (6 Naehte; **keine** Alarm-/Fault-Naht):
      `_DEVICE_FACTORIES`, `DEVICE_DECIMAL_PARAMS`,
      `_DEVICE_TYPE_BY_CLASS_NAME`, `_runs_router`-State-Subset,
      `CRITICAL_COV_TARGETS`; Szenario-Beispiel
      [`wind_turbine_demo.yaml`](../../../../tests/integration/scenarios/wind_turbine_demo.yaml)
      + Smoke
      ([`test_wind_turbine_scenario.py`](../../../../tests/integration/test_wind_turbine_scenario.py)).
- [x] **Gates**: `make gates` gruen (10 A-1-Gates), inkl.
      `coverage-gate-critical` ≥ 90 % auf `devices/wind_turbine`;
      `make docs-check` gruen. [`ADR 0057`](../../adr/0057-wind-turbine-device-pattern.md)
      `Accepted`, Trigger 018 aufgeloest.

## 3. Realization-Notes (Abweichungen ggue. ADR-Wortlaut)

- **Erster echter `RandomPort`-Konsument**: Wind zieht pro Tick eine
  `next_float()`-Ziehung
  ([`ADR 0057`](../../adr/0057-wind-turbine-device-pattern.md) §2.4). Nach
  `from_snapshot` ist `_random = None`; der erste Tick wirft fail-loud
  `DeviceNotInitializedError`, bis `attach_random` lief. **Voller
  stand-kontinuierlicher Resume stochastischer Geraete ist NICHT Teil
  von 2c** (Review-Folge-Befund): der TickLoop-Resume re-attached
  Geraete-RandomPorts derzeit nicht, und `sub_port(name)` liefert ohnehin
  nur den Initial-Zustand — die Sub-Stream-Position wird nicht
  persistiert. Fresh-Start ist voll deterministisch (heute genutzter
  Pfad); per-Geraet-Random-State im `SnapshotEnvelope` ist Folge-Slice
  ([`ADR 0057`](../../adr/0057-wind-turbine-device-pattern.md) §2.6/§6).
- **Command-/Alarm-/Fault-los**: anders als EV/Transformer hat Wind
  keinen `set_*`-Command (stochastisch getrieben). `apply_command` →
  `IGNORED`; kein `commands.py`, kein Alarm (→ keine `alarm_mappers`-
  Naht), kein Fault (→ keine `_FAULT_TYPE_TO_DEVICE_TYPE`-Naht). Wind
  beruehrt nur 6 der 8 Naehte.
- **Typ vs. Dir**: Trigger 018 schlug `devices/wind/` vor; die
  Realisierung folgt der dir==type-Konvention der Welle-2-Geraete +
  dem Lastenheft-kanonischen Typ-String → `devices/wind_turbine/` +
  `WindTurbineDevice` + Typ `wind_turbine`.
- **`min == max` = konstanter Wind**: bewusst nicht-strikt (`max >= min`),
  damit die kubische Kennlinie RNG-frei (deterministisch) testbar ist;
  zugleich ein valider „konstanter Wind"-Degenerat.

## 4. Lerneintrag (Closure-Pflicht)

**Geschaerfte Regel (8-Naht-Checkliste ist bedingt):** Die Checkliste aus
[`M8-welle-2a.md`](M8-welle-2a.md) §4 hat **konditionale** Naehte — Alarm
(5) und Fault (6) entfallen fuer command-/fault-lose Geraete (Wind). Die
beiden Drift-Tests (`test_loader_factory_sync` +
`test_yaml_loader_allowlist`) bleiben die verlaesslichen Sensoren; die
Map-Konsistenz haelt auch fuer ein Geraet ohne Alarm/Fault. **Neue
Schaerfung:** ein Geraet, das `RandomPort` konsumiert, MUSS einen
`_random is None`-Guard im Tick tragen (Resume ohne `attach_random` sonst
`AttributeError` statt typisiert) und seinen RandomPort aus `__eq__`/
Snapshot ausschliessen. Das ist die Vorlage fuer kuenftige stochastische
Geraete.

## 5. Review-Folge

High-effort `/code-review` (Rollentrennung, 3 separate Finder-Kontexte).
**Echter Bug gefunden** (von zwei Findern bestaetigt) — kein blosses
Test-Manko:

- **Bilanz-Naht (7. Naht) fehlte**: `_BILANZ_SOURCE_BUCKETS` (TickLoop)
  kannte `wind_turbine` nicht → Wind-`power_kw` (`source="wind_turbine"`)
  fiel als `unknown_source` aus der Netzbilanz; Wind war fuer den
  Grid-Connection-Auto-Close unsichtbar. **Fix**: `"wind_turbine" →
  "generation"`. **Cross-Befund**: derselbe Defekt traf `ev_charger`
  (Welle 2a) — ebenfalls ergaenzt (`"ev_charger" → "storage"`, EV ist ein
  Speicher, vorzeichenkonsistent wie Battery). Transformer ist korrekt
  draussen (emittiert `primary_/secondary_power_kw`, nicht `power_kw` →
  vom Metrik-Filter uebersprungen). EV-Demo unveraendert (idle, power 0).
- **Resume-„Harness-Luege" korrigiert**:
  [`ADR 0057`](../../adr/0057-wind-turbine-device-pattern.md) §2.6
  behauptete, der TickLoop garantiere `attach_random` beim Resume —
  nicht verdrahtet, und
  `sub_port` liefert ohnehin nur den Initial-Zustand. ADR + Slice-Doc +
  Modell-Docstring auf die ehrliche Resume-Grenze korrigiert (Fresh-Start
  deterministisch; per-Geraet-Random-State = Folge-Slice).

**Test-Schaerfungen** (Recall-Luecken):

- NEU `test_curve_cubic_exact_value_with_nonzero_cut_in` — der bisherige
  Exaktwert-Test hatte `cut_in = 0` (der `cut_in**3`-Term verschwand);
  jetzt `cut_in = 3` (rp=1701 cancelt den Nenner → exakt 316).
- `run_id` ueberlebt den Snapshot-Roundtrip jetzt nicht-trivial.
- NEU `_CountingRandom`-Fake + zwei Tests: **genau eine** `next_float()`-
  Ziehung pro Tick (auch bei `min == max`) — pinnt die §2.4-Stream-
  Konsistenz.

**Bewusst nicht geaendert**: Snapshot-State-Range-Validierung +
Full-Precision-State-Speicherung sind das etablierte Geraete-Muster
(Devices vertrauen eigenen Snapshots).
