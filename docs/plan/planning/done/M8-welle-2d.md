# Welle 2d — Diesel-Generator (`GG-DEV-018`, ADR 0058)

**Status:** Done (M8-Welle-2d, geschlossen 2026-06-14) — viertes (letztes)
SOLLTE-Geraet aus [`M8-welle-2.md`](M8-welle-2.md) §3. **Schliesst die
Welle-2-Geraete-Reihe ab.**

**Container:** [`M8-welle-2.md`](M8-welle-2.md); [`roadmap.md`](../in-progress/roadmap.md)
§4 M8. Design (C1):
[`ADR 0058`](../../adr/0058-diesel-generator-device-pattern.md) `Accepted`.
Trigger: [`019`](../open/019-sollte-diesel-device.md) (mit dieser Welle
aufgeloest).

---

## 1. Lieferziel

Das Dieselgenerator-Modell (`GG-DEV-018`, Lastenheft §9.4) als
`DeviceModel` + `FaultInjectableDevice` im Core: dispatchbarer Generator
nach dem Battery-Muster ([`ADR 0014`](../../adr/0014-battery-snapshot-schema.md))
mit Kraftstoff-Vorrat, Verbrauch, Ramp, Anfahr-/Abstell-Hysterese und
`genset_fault`-Schutz
([`ADR 0058`](../../adr/0058-diesel-generator-device-pattern.md)).
Geraetetyp `diesel_generator`.

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [x] **Modell + Tests**: NEU `hexagon/core/devices/diesel_generator/`
      (`config`/`commands`/`snapshot`/`model`) — Anfahr-/Abstell-
      Hysterese, Ramp, Kraftstoff-Limit/run-dry, Command-Clamp,
      ≥ 100-Tick-Determinismus, Snapshot-Roundtrip (inkl. `running`-Bool)
      + `genset_fault`
      ([`test_diesel_generator_device.py`](../../../../tests/unit/hexagon/core/devices/diesel_generator/test_diesel_generator_device.py),
      [`test_fault_injection.py`](../../../../tests/unit/hexagon/core/devices/diesel_generator/test_fault_injection.py)).
- [x] **End-to-End-Verdrahtung** (9 Naehte inkl. Bilanz): die 8 Standard-
      Naehte + `_BILANZ_SOURCE_BUCKETS["diesel_generator"] = "generation"`
      (proaktiv aus der 2c-Review-Folge) + NEU
      `snapshot_codec.assert_bool`; Szenario-Beispiel
      [`diesel_demo.yaml`](../../../../tests/integration/scenarios/diesel_demo.yaml)
      + Smoke
      ([`test_diesel_scenario.py`](../../../../tests/integration/test_diesel_scenario.py)).
- [x] **Gates**: `make gates` gruen (10 A-1-Gates), inkl.
      `coverage-gate-critical` ≥ 90 % auf `devices/diesel_generator`;
      `make docs-check` gruen. [`ADR 0058`](../../adr/0058-diesel-generator-device-pattern.md)
      `Accepted`, Trigger 019 aufgeloest.

## 3. Realization-Notes

- **Erste Zustandsmaschine im Geraete-Core**: `running`-Hysterese
  (STOPPED↔RUNNING mit `min_start`/`min_stop`-Band,
  [`ADR 0058`](../../adr/0058-diesel-generator-device-pattern.md) §2.4). Das
  `running`-Flag ist ein Top-Level-Bool im Snapshot → NEU
  `snapshot_codec.assert_bool` (geteilter Codec-Primitive, Komplement zu
  `assert_int`).
- **Endliche nicht-elektrische Ressource**: Kraftstoff (l) statt SoC;
  Run-Dry-Limit analog EV-Energie-Limit
  ([`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md) §2.8) — `power_kw` und
  Verbrauch bleiben konsistent, ein leergefahrener Genset stoppt und
  kann ohne Sprit nicht wieder anfahren.
- **Bilanz-Naht proaktiv**: aus der 2c-Review-Folge gelernt — ein
  Generator MUSS in `_BILANZ_SOURCE_BUCKETS` (`generation`), sonst faellt
  seine `power_kw` als `unknown_source` aus der Netzbilanz. Diesmal von
  Anfang an verdrahtet (nicht erst im Review).
- **Abstellen instant** (kein Ramp-Down), Ramp nur beim Hochfahren —
  bewusste Minimal-Vereinfachung
  ([`ADR 0058`](../../adr/0058-diesel-generator-device-pattern.md) §6).

## 4. Lerneintrag (Closure-Pflicht)

**Geschaerfte Regel (Checkliste ist jetzt 9 Naehte):** Die „8-Naht"-
Checkliste aus [`M8-welle-2a.md`](M8-welle-2a.md) §4 ist um die in 2c
schmerzhaft gelernte **Bilanz-Naht** zu erweitern: jedes Geraet, das
`power_kw` mit eigener `source` emittiert UND an der Netzbilanz teilnimmt
(Generator/Last/Speicher), MUSS in `_BILANZ_SOURCE_BUCKETS` — Pass-
Through-Geraete (Transformer, eigene `primary_/secondary_power_kw`-
Metriken) bleiben draussen. **Prozess-Schaerfung (aus dem 0057-Miss):**
der ADR-Status-Flip `Proposed → Accepted` muss bei C3 in **Datei UND
Index** erfolgen — `make docs-check` prueft Status-Konsistenz nicht, also
ist es ein manueller Closure-Schritt. Welle 2 (alle vier SOLLTE-Geraete)
ist mit 2d abgeschlossen.

## 5. Review-Folge

High-effort `/code-review` (Rollentrennung, 3 separate Finder-Kontexte).
**Echter Korrektheits-Bug gefunden** (Finder 1, mit konkretem Szenario):

- **Run-Dry-Invariante verletzt**: `_consume_fuel` setzte beim
  Leerfahren `running=False`, gab aber `limited_power > 0` zurueck →
  im selben Tick `power_kw > 0` UND `running = 0` (Invariante
  `running==False ⇒ power_kw==0` gebrochen; `current_power_kw > 0` im
  Snapshot eines gestoppten Gensets). **Fix**
  ([`ADR 0058`](../../adr/0058-diesel-generator-device-pattern.md) §2.5-konform):
  der Leerfahr-Tick bleibt der letzte erzeugende Tick (`running` an,
  erzeugt `limited_power`, Tank→0); der Stopp passiert im Folge-Tick
  ueber einen NEU `fuel_l <= 0`-Check in `_run_dispatch`. Damit haelt
  die Invariante. Test `test_fuel_run_dry_*` auf die korrigierte
  2-Tick-Semantik aktualisiert.

**Test-Schaerfungen** (Recall-Luecken):

- NEU `test_generated_kwh_exact_value_at_default_tick` + Energie-
  Konsistenz im Run-Dry-Test — `generated_kwh` war nur monoton, nie
  wertgenau gepinnt (ein dt-Konversions- oder Pre-Limit-Akkumulations-
  Bug waere durchgerutscht).
- NEU `test_ramp_limits_power_descent` — der Ramp-**Down**-Zweig
  (`delta < -max_delta`) war ungetestet (nur Hochfahren).

**Bewusst deferred**: command-getriebener Integration-E2E (der Smoke
faehrt idle wie EV/Transformer; das generische Command-Routing durch den
Loop ist via Agents/Battery-Integration gedeckt) + `_clamp_power`-
Unterschranke (defensiv, per Sign-Konvention `power_kw >= 0`); Snapshot-
State-Range-Validierung (etabliertes Geraete-Muster: Devices vertrauen
eigenen Snapshots). Der Command-E2E-Teil ist als Trigger
[`046`](../open/046-command-driven-integration-e2e.md) getrackt.
