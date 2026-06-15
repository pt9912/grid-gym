# ADR 0059 — Generische `ScenarioFaultEngine` (M8 Welle 2, Carveout D-8)

**Status:** Accepted
**Datum:** 2026-06-14
**Bezug:**

- [`ADR 0022`](0022-fault-injection-protocol.md) — `FaultPort` +
  `FaultInjectableDevice` (Protocol-Surface).
- [`ADR 0025`](0025-fault-recovery-pattern.md) — Recovery-Pattern
  (half-open `[start, end)`, idempotenter inject/clear, manual-recovery);
  die `BatteryFaultEngine`/`GridFaultEngine`-Scheduling-Logik, die hier
  generalisiert wird.
- [`ADR 0051`](0051-fault-engine-location-and-naming.md) —
  `FaultPort`-Implementierung im Core (kein Outer-Ring-Adapter).
- [`ADR 0055`](0055-ev-charger-device-pattern.md) /
  [`ADR 0056`](0056-transformer-device-pattern.md) /
  [`ADR 0058`](0058-diesel-generator-device-pattern.md) §6 — die drei
  neuen Fault-Typen (`connection_loss`/`winding_fault`/`genset_fault`),
  deren Runtime-Engine je ADR §6 deferred wurde (Carveout D-8).
- [`carveouts.md`](../planning/in-progress/carveouts.md) §2.1 **D-8** —
  der mit diesem ADR aktivierte Carveout (Slice-Origin).
- [`M8-welle-2.md`](../planning/done/M8-welle-2.md) — Welle-2-Plan;
  Cross-Cutting-Review (`5792ab8`), der die Altitude-Schuld benannte.

---

## 1. Kontext

Der **Cross-Cutting-Review der Welle 2** (`5792ab8`) hat zwei verbundene
Befunde konsolidiert:

1. **Altitude-Schuld**: `BatteryFaultEngine` und `GridFaultEngine` sind bis
   auf **zwei Stellen** (die gefilterte Fault-Typ-Konstante und der
   Subsystem-Name in `assert_supported_type`) byte-identisch. Die gesamte
   Scheduling-Logik (Fenster-Check, Target-Resolution, idempotenter
   inject/clear, manual-recovery) ist dupliziert.
2. **Carveout D-8**: Die drei neuen Welle-2-Geraete (EV-Charger,
   Transformer, Diesel) tragen geraeteseitig `inject_fault`/`clear_fault`
   + HTTP-Whitelist-Verdrahtung, aber **keine Runtime-Engine**. Eine
   Szenario-YAML mit `connection_loss`/`winding_fault`/`genset_fault`
   crasht fail-loud beim Startup (`_DemoScenarioUnknownFaultTypeError`),
   weil `_KNOWN_FAULT_TYPES = {cell_failure, voltage_drop}` stale ist und
   keine Engine die neuen Typen verarbeitet.

Die naive D-8-Aufloesung — **drei weitere** Engine-Klassen nach dem
Battery/Grid-Muster — wuerde die Duplikation vervierfachen. Schluessel-
Erkenntnis: **eine Fault-Engine muss den Fault-Typ gar nicht kennen.**
`device.inject_fault(fault.type, payload)` reicht den Typ an das per
`fault.target` aufgeloeste Geraet durch, das ihn intern validiert
(`FaultUnsupportedTypeError` bei Mismatch). Die einzige typ-spezifische
Verantwortung — „welcher Typ gehoert zu welchem Geraet" — liegt also
bereits **im Geraet**, nicht in der Engine. Die Engine ist reines
Scheduling.

## 2. Entscheidung

### 2.1 Generische `ScenarioFaultEngine`

NEU `hexagon/core/faults/scenario_fault_engine.py`:
`ScenarioFaultEngine(faults, supported_types, subsystem="scenario")`.
Sie haelt die **einzige** Kopie der Scheduling-Logik (ADR 0025):

- Konstruktor filtert `faults` auf `supported_types` und belegt
  `f"fault-{i}"`-IDs mit dem **Original-Scenario-Index** `i` (stabil ueber
  Typ-Hinzufuegungen, ADR 0025 §2.1 + Welle-2-Review-Folge M-2).
- `apply_active_faults(devices, context)`: half-open `[start, end)`-Fenster,
  Target-Resolution + `isinstance(d, FaultInjectableDevice)`, idempotenter
  `inject_fault` bei inactive→active, `clear_fault` bei active→inactive,
  manual-recovery-Prioritaet (ADR 0025 §2.1/§2.3/§2.4).
- `register_manual_recovery(fault_id, target)` mit
  `FaultUnknownReferenceError`-Validierung.
- `clear_fault` reicht `fault.type` durch (kein hartkodierter Typ mehr) —
  derselbe Typ, der injiziert wurde.

### 2.2 `BatteryFaultEngine`/`GridFaultEngine` als duenne Subklassen

Beide werden auf je ~3 Zeilen reduziert: Subklassen von
`ScenarioFaultEngine`, die `supported_types` auf ihren Einzeltyp und
`subsystem` setzen. Begruendung: die M3-Welle-2-Unit-/Integration-Tests
(`test_battery_fault_engine.py`, `test_grid_fault_engine.py`,
`test_recovery_window_property.py`, `_fault_composite.py`,
`test_fault_demo_scenario.py`) konstruieren diese Klassen direkt — sie
bleiben das **feinkoernige Regressionsnetz** fuer die geteilte Logik und
erhalten das ADR-0025-Vokabular. Die Duplikation verschwindet (Logik lebt
einmal in der Basis); die Namen bleiben als duenne, dokumentierte Compat-
Shims.

### 2.3 Produktive Composition: eine Engine statt N

`_compose_fault_port` (in `_demo_scenario_setup.py`) liefert kuenftig
**eine** `ScenarioFaultEngine(faults, supported_types=_KNOWN_FAULT_TYPES)`.
Die Klasse `_FaultPortComposition` (Battery+Grid-Sequenz mit try/finally-
Exception-Isolation, Welle-6a-Decision-19/F12) **entfaellt** — bei einer
einzigen Engine gibt es kein Cross-Adapter-Ordering und keine
Teil-Anwendung-unter-Exception mehr; die Fault-Listen-Reihenfolge ist
inhaerent deterministisch (ADR 0021 §2.9). `_KNOWN_FAULT_TYPES` wird die
**single source of truth** fuer den Fail-Fast und um die drei neuen Typen
auf **fuenf** erweitert.

### 2.4 Die drei neuen Fault-Typen ohne per-Geraet-Engine-Code

`connection_loss`/`winding_fault`/`genset_fault` funktionieren damit
**end-to-end ohne neue Engine-Klasse**: die produktive `ScenarioFaultEngine`
loest das Ziel-Geraet auf und ruft `inject_fault(fault.type, payload)`; das
EV-/Transformer-/Diesel-Geraet validiert + mutiert seinen Physik-State.
Carveout D-8 ist damit aufgeloest.

### 2.5 Wrong-Target-Edge (unveraendert zum Status quo)

Zielt ein Fault auf ein Geraet, dessen Typ den Fault nicht kennt (z. B.
`genset_fault` auf eine Battery), wirft `device.inject_fault` beim Tick
`FaultUnsupportedTypeError`. Das ist **identisch** zum bisherigen Verhalten
(auch Battery/Grid-Engine loesten Target per `device_id` auf und riefen
`inject_fault` ungeprueft auf Typ-Kompatibilitaet auf). Eine Target-Typ-
Vorvalidierung beim Laden ist bewusst **nicht** Teil dieser ADR (§6).

### 2.6 Aufgeraeumte Dead-Surface

`assert_supported_type` (in beiden alten Engines `@staticmethod`, **nirgends
aufgerufen**, kein Test) entfaellt ersatzlos (Simplification-Befund des
Reviews; entfernt ungetesteten Code → Coverage-neutral bis -positiv).

## 3. Begruendung

Der Review-Altitude-Winkel: „special cases layered on shared infrastructure
are a sign the fix isn't deep enough — prefer generalizing the underlying
mechanism." Die generische Engine ist genau diese Generalisierung: ein
Mechanismus, parametrisiert ueber die unterstuetzten Typen, statt eine
Klasse pro Typ. Sie macht D-8 **kleiner** (eine Generalisierung statt drei
neuer Engines) und zahlt zugleich die M3-Duplikations-Schuld zurueck. Die
Subklassen-Compat haelt das Regressionsnetz intakt — die Aenderung ist
verhaltens-erhaltend fuer den bewaehrten Battery/Grid-Pfad.

## 4. Reichweite + Operative Artefakte

- NEU `hexagon/core/faults/scenario_fault_engine.py` (`ScenarioFaultEngine`).
- `battery_fault_engine.py`/`grid_fault_engine.py` → duenne Subklassen;
  `faults/__init__.py` exportiert zusaetzlich `ScenarioFaultEngine`.
- `_demo_scenario_setup.py`: `_compose_fault_port` → Single-Engine;
  `_FaultPortComposition` entfernt; `_KNOWN_FAULT_TYPES` += die drei neuen
  Typen (fuenf gesamt).
- `_KNOWN_FAULT_TYPES`-Eintrag referenziert die `FAULT_TYPE_*`-Konstanten
  aus `core.faults.types` statt String-Literalen (single source of truth).
- Tests: NEU Unit-Tests fuer die generische Engine ueber die drei neuen
  Typen; `test_fault_port_composition.py` +
  `test_m5_welle_6a_fault_smoke.py` auf die Single-Engine-Form migriert;
  alle uebrigen M3-Fault-Tests bleiben unveraendert gruen. Demo-Szenario-
  Fault-Beispiel + Smoke fuer einen der neuen Typen.

## 5. Konsequenzen

- Eine Scheduling-Logik statt zwei (kuenftig fuenf) Kopien; neue Fault-
  faehige Geraete brauchen **null** Engine-Code — nur ihren Typ in
  `_KNOWN_FAULT_TYPES` und die geraeteseitige `inject_fault`-Validierung.
- `_FaultPortComposition` + `assert_supported_type` entfallen (weniger
  Surface).
- Battery/Grid behalten Namen + Tests (kein M3-Regressionsrisiko).

## 6. Nicht Gegenstand dieser ADR

- Target-Typ-Vorvalidierung beim Szenario-Laden (Fault-Typ ↔ Ziel-Geraete-
  typ) — Folge-Slice, falls ein Stakeholder Fail-Fast-beim-Laden statt
  Fail-Fast-beim-Tick fordert.
- Produktiver Composite-`FaultPort`-Adapter unter `adapters/driven/` — die
  Engine bleibt Core (ADR 0051); die Demo-Komposition lebt weiter im
  Lifespan-Pfad.
- Command-getriebene manual-recovery durch den AgentBus — Welle-3+
  (`register_manual_recovery` ist verdrahtet, aber nur test-getrieben).
- Weitere Fault-Typen pro Geraet (Ueberhitzung, Oeldruck etc.) — je
  Geraete-Folge-ADR.

## 7. Acceptance (Fitness Functions)

`Accepted` mit dem D-8-Slice. Maschinell gebunden:

- **Generische Engine — Scheduling-Semantik ueber alle Typen** —
  [`tests/unit/hexagon/core/faults/test_scenario_fault_engine.py`](../../../tests/unit/hexagon/core/faults/test_scenario_fault_engine.py)
  (Fenster, idempotenter inject/clear, manual-recovery, neue Typen).
- **Battery/Grid-Verhaltens-Erhalt** — die unveraenderten
  `test_battery_fault_engine.py` / `test_grid_fault_engine.py` /
  `test_recovery_window_property.py` bleiben gruen (Subklassen-Compat).
- **End-to-End Single-Engine** —
  [`test_fault_port_composition.py`](../../../tests/unit/adapters/driving/http_api/test_fault_port_composition.py)
  + Demo-Fault-Szenario-Smoke (neuer Fault-Typ wirkt am Geraet).
- **Gates** — `make gates` gruen, inkl. `coverage-gate-critical`.
