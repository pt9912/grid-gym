# ADR 0022 — Fault-Injection-Protocol + Scenario-Validator-Härtung (M3 Welle 1)

**Status:** Accepted — M3-Welle-7-Closure 2026-05-25 (C1.1).
Validierung lieferten Welle 1 (Foundation, `79bb50a`: 773 Unit-
Tests gruen, FaultPort + Sub-Protocol + Validator-Haertung +
TickLoop-Hook) und Welle 2 (Konkretisierung, `1debd5e..91d44e2`:
840 Unit-Tests + 14 Integration-Tests, Battery `cell_failure` +
Grid `voltage_drop` + Recovery-Engine via ADR 0025, Property-
Tests, Fault-Demo-Szenario + Postgres-Roundtrip). `make gates`
cache-frei gruen **ohne** `CRITICAL_COV_TARGETS`-Override
(Default-Liste enthaelt `core/faults`); `make fullbuild` gruen;
`AC-PORTS-NO-OUT` bleibt KEPT.
**Datum:** 2026-05-20
**Status geaendert am:** 2026-05-25 — `Provisional → Accepted`
(M3-Welle-7-Closure-Lauf C1.1; ADR-Header-Schliff ohne
Architektur-Aenderung).
**Vorherige Aenderung (2026-05-20)** — `Proposed → Provisional`
(M3-Welle-1-Merge `79bb50a`, feat-Commit lieferte Sub-
Protocol + FaultPort + Validator-Haertung + TickLoop-Hook +
11 Tests).
**Letzte inhaltliche Aenderung:** 2026-05-25 — `Provisional →
Accepted`-Closure-Schliff (Status-Update + Welle-1/2-Beleg
ergaenzt; keine Architektur-Aenderung).
**Bezug:**
[`ADR 0013`](0013-device-model-protocol.md) §2.8
(Sub-Protocol-Mandate fuer Post-MVP-Erweiterungen — `M3 Faults`
ist explizit als Beispiel genannt: „`FaultInjectableDevice(DeviceModel)`,
etc., nicht als Methoden-Erweiterung des Base"),
[`ADR 0013`](0013-device-model-protocol.md) §4
(`DeviceModel`-Erweiterungs-Pattern, das diese ADR ohne
Supersede schaerft — analog ADR 0014/0016/0017/0018),
[`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
§2.5 (Vor-Tick-Block in `TickLoop.tick()` — Fault-Hook
fluegt sich in dieselbe Block-Struktur ein, nach
`_consume_load_inputs_into` und vor erster
`_run_device_iteration`),
[`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
§2.3 (Scenario-Validator-Erweiterungs-Pattern fuer optionale
Top-Level-Sektionen — ADR 0022 schaerft `_assert_fault_list`
ohne neue Top-Level-Sektion),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-
ADR-Pattern — diese ADR erweitert ADR 0013 §2.8 fuer den
Fault-spezifischen Sub-Protocol-Vertrag, kein Supersedes),
[`ADR 0015`](0015-snapshot-envelope-v2.md) §2 (Snapshot-
Envelope-v2-Vertrag — Welle 1 fuegt **keine** neuen
Sub-Snapshots hinzu; Snapshot-Bump v2 → v3 ist erst
Welle-2/M6-Material, siehe §2.6 unten).
M3-Slice-Plan
[`in-progress/M3-faults-agents-observability.md`](../planning/done-archive/M3-faults-agents-observability.md)
§3 Welle 1.
Lastenheft §14 Fault Injection (`GG-FAULT-001..010`), §20
Sicherheitsanforderungen (`GG-SAFE-001..006`).
Architektur §5 Komponentensicht (`GG-AR-COMP-FAULTS`),
§13 Fault-Injection-Architektur, §4.2 Driven-Ports-Tabelle
(`GG-AR-PORT-DRN-008` ist Observability — Fault-Port ist
**kein** PORT-DRN-008, sondern eigener neuer Port-Slot —
Architektur §4.2 Erweiterung wird in der ADR-Folge oder
M3-Welle-7-Closure formalisiert).

---

## 1. Kontext

M3-Welle-1 ist die erste produktive Code-Welle in M3
(Faults + Multi-Agent + Observability) nach M3-Welle-0
(Slice-Plan-Eroeffnung + Trigger-Triage). Welle 1 liefert
die **Fault-Foundation** — die Architektur-Schichten, auf
denen Welle 2 die konkreten Fault-Typen (`cell_failure`,
`voltage_drop`) und Recovery-Logik aufbaut.

Drei Beobachtungen aus dem M1/M2-Bestand begruenden den
Entscheidungs-Bedarf:

**Beobachtung 1 — M1-Welle-5-Validator hat Strukturvertrag,
aber keine Target-Validierung.** Der `faults`-Block im
Scenario-Schema ist seit M1-Welle-5 (`d4029e3` ff.) als
optionales Top-Level-Element validiert: `start_simulation_time`,
`duration_ms`, `target`, `type`, `payload`, `recovery` sind
strukturell gepinnt
(`src/grid_gym/hexagon/core/scenario/validator.py:243-263`,
`_assert_fault_list`). **Aber**: der Validator prueft NICHT,
ob `fault.target` in `devices` existiert — anders als der
parallel laufende `_assert_event_list` (Zeile 198-222), der
genau diesen Target-Existenz-Check via
`ScenarioUnknownEventTargetError` durchsetzt. Konsequenz: ein
Szenario mit `faults[0].target = "ghost-battery-99"` ist
heute syntaktisch akzeptiert und fliegt erst zur TickLoop-
Laufzeit aus (oder gar nicht, wenn nie eine Fault-Engine den
unbekannten Target nachfragt). M3-Welle-1 schliesst diese
Luecke fail-fast.

**Beobachtung 2 — Devices haben keinen Fault-Hook.** Die
`DeviceModel`-Surface
(`src/grid_gym/hexagon/core/devices/_protocol.py`) hat fuenf
Methoden (`initialize`, `tick`, `apply_command`, `snapshot`,
`telemetry`). Keine davon ist fault-bewusst. ADR 0013 §2.8
hat den Hook-Punkt explizit weggeschoben: „Post-MVP-
Erweiterungen (M3 Faults, M4 Protocol-Adapter) kommen als
separate Sub-Protocols (`FaultInjectableDevice(DeviceModel)`,
etc.), nicht als Methoden-Erweiterung des Base." Welle 1
realisiert genau diese Sub-Protocol-Schicht.

**Beobachtung 3 — TickLoop hat kein Fault-Konsument.**
Der Welle-6b-Vor-Tick-Block
(`src/grid_gym/hexagon/core/simulation/tick_loop.py:289-302`,
`_consume_load_inputs_into`) konsumiert LoadEvents +
LoadProfiles, aber kein Pendant fuer Faults. ADR 0021 §2.5
fixiert das Vor-Tick-Block-Pattern; Welle 1 fuegt einen
weiteren Hook in derselben Position ein, ohne den bestehenden
Pfad zu brechen.

Welle 1 entscheidet, **wie** der Fault-Pfad strukturell
aussieht, ohne konkrete Fault-Typen oder Recovery-Logik zu
liefern (das ist Welle 2). Konkret: das Sub-Protocol-Format
fuer Devices, der Driven-Port-Vertrag fuer Fault-
Orchestrierung, der Validator-Pruef-Punkt, und der TickLoop-
Hook-Punkt.

---

## 2. Entscheidung

ADR 0022 fixiert sechs Punkte:

### 2.1 `FaultInjectableDevice(DeviceModel)` Sub-Protocol

Neuer Protocol unter
`src/grid_gym/hexagon/core/faults/_protocol.py`:

```python
class FaultInjectableDevice(DeviceModel, Protocol):
    """Sub-Protocol fuer Devices, die Fault-Injection unterstuetzen.

    ADR 0013 §2.8-konform: keine Erweiterung der Base-`DeviceModel`-
    Surface; stattdessen ein eigener Sub-Protocol-Slot, den
    fault-faehige Devices in Welle 2+ explizit implementieren.
    Welle 1 definiert nur die Form; konkrete Implementer kommen
    in Welle 2 (BatteryDevice + GridConnectionDevice).
    """

    def inject_fault(
        self,
        fault_type: str,
        payload: Mapping[str, object],
    ) -> None:
        """Wendet einen Fault auf das Device an.

        `fault_type` ist die kanonische Type-Bezeichnung aus
        `ScenarioFault.type` (z. B. `"cell_failure"`,
        `"voltage_drop"`). `payload` traegt fault-typ-spezifische
        Parameter (z. B. `{"affected_cell_index": 3}` fuer
        `cell_failure`).

        **Welle-1-Stand**: Welle 1 liefert nur den Protocol-
        Vertrag, keine konkrete Implementation. Welle 2 fuegt
        BatteryDevice + GridConnectionDevice in den Implementer-
        Set ein und definiert die Type-/Payload-Vertraege.
        """
        ...
```

**Closed-Set-Pattern**: `FaultInjectableDevice` ist explizit
**nicht** in `DeviceModel` ge-bundled. M2-Geraete (PV, Load,
SmartMeter) bleiben `DeviceModel`-only und werden **nicht**
implizit fault-faehig. Welle 2 entscheidet pro Geraet
explizit, ob es `FaultInjectableDevice` implementiert.

Re-export in `src/grid_gym/hexagon/core/faults/__init__.py`,
damit Aufrufer `from grid_gym.hexagon.core.faults import
FaultInjectableDevice` schreiben koennen.

### 2.2 `FaultPort` Driven-Port-Protocol

Neuer Driven-Port unter
`src/grid_gym/hexagon/ports/driven/fault.py`:

```python
class FaultPort(Protocol):
    """Driven-Port fuer Fault-Injection-Orchestrierung.

    Welle-1-Vertrag: pro Tick ruft die TickLoop genau einmal
    `apply_active_faults(devices, context)` und delegiert die
    gesamte Entscheidung — welcher Fault wann auf welches
    Device — an den Adapter. Welle 1 liefert keinen produktiven
    Adapter; Welle 2 liefert `BatteryFaultAdapter` +
    `GridFaultAdapter`.
    """

    def apply_active_faults(
        self,
        devices: Sequence[object],
        context: DeviceTickContext,
    ) -> None:
        """Wendet alle bei dieser Tick aktiven Faults auf die
        passenden Geraete an.

        Der Adapter ist verantwortlich fuer:
        1. Iteration durch die `scenario.faults`-Liste
           (die er ueber Konstruktor-Injection erhaelt).
        2. Aktivitaets-Check pro Fault: ist
           `context.simulation_time in
           [start_simulation_time, start_simulation_time
           + duration_ms)`?
        3. Target-Resolution: finde Device mit passender
           `device_id` in `devices`.
        4. `isinstance(device, FaultInjectableDevice)`-Check.
        5. Aufruf `device.inject_fault(fault.type, fault.payload)`.

        Welle 1 macht **keinen** dieser Punkte. Welle 2
        implementiert sie.

        **Welle-1-Port-Surface ist `Sequence[object]`** (nicht
        `Sequence[DeviceModel]`), weil AC-PORTS-NO-OUT
        (`ADR 0002 §A-1`) den Runtime-Import von
        `core.devices._protocol.DeviceModel` aus
        `hexagon/ports/driven/` verbietet. Welle-2-Adapter
        typisieren intern strenger (z. B. `Sequence[DeviceModel]`)
        und kapseln den `isinstance(d, FaultInjectableDevice)`-
        Check (Schritt 4 oben). Welle-3+/M3-Welle-7 koennen ein
        minimales `_DeviceIdentifiable`-Protocol unter
        `core/domain/` einfuehren, falls Type-Safety an der Port-
        Grenze relevant wird.

        **Empty-`devices`-Vertrag** (Welle-1-Review L-7): leere
        Sequenz ist zulaessig und produziert einen No-Op. Adapter
        muessen das absorbieren, ohne zu werfen.
        """
        ...
```

**Orchestrierungs-Hook statt Per-Device-Hook**: Die TickLoop
kennt nur einen Aufruf-Punkt, nicht N Per-Device-Aufrufe.
Vorteil — TickLoop bleibt sauber von Fault-Logik; Adapter
kann beliebig komplexe Aktivitaets-/Auswahl-Logik haben (z. B.
„nur den hoechsten-Priority-Fault pro Tick anwenden"). Welle 1
fixiert nur den Aufruf-Punkt.

### 2.3 Scenario-Validator-Härtung (Target-Existenz)

`_assert_fault_list` in
`src/grid_gym/hexagon/core/scenario/validator.py` wird um
einen Target-Existenz-Check erweitert — analog
`_assert_event_list` (Zeile 198-222). Signatur:

```python
def _assert_fault_list(
    raw: Mapping[str, object],
    devices: list[Mapping[str, object]],
) -> None:
    ...
    target = entry["target"]
    if isinstance(target, str) and target not in device_ids:
        raise ScenarioUnknownFaultTargetError(target)
```

Neuer typed Fehler unter
`src/grid_gym/hexagon/core/errors.py`:

```python
class ScenarioUnknownFaultTargetError(ScenarioSchemaError):
    def __init__(self, target: str) -> None:
        super().__init__(f"scenario fault targets unknown device: {target!r}")
```

Pattern exakt parallel zu
`ScenarioUnknownEventTargetError` (Zeile 629-634).

**Welle-1-Scope-Klausel**: NUR Target-Existenz. **KEINE**
Type-Whitelist (z. B. `type` nur aus `{"cell_failure",
"voltage_drop", ...}` erlaubt) und **KEINE** semantische
Validation (`duration_ms > 0`, `recovery` aus Whitelist).
Beides wuerde Welle 2-Semantik vorwegnehmen (welche
Fault-Typen sind ueberhaupt definiert? Welche Recovery-Modi?)
— dieser Vorgriff bleibt verboten.

### 2.4 TickLoop-Hook im Vor-Tick-Block

`TickLoop.tick()`
(`src/grid_gym/hexagon/core/simulation/tick_loop.py:240-332`)
erhaelt einen neuen Hook-Punkt **nach** dem LoadEvent-/Profile-
Overlay (Zeile 302 `_consume_load_inputs_into`) und **vor**
der ersten Device-Iteration (Zeile 306 erste
`_run_device_iteration`):

```python
# Schritt A — Vor-Tick-Block (ADR 0021 §2.5).
self._consume_load_inputs_into(...)  # LoadProfile + LoadEvent

# Schritt A2 — Fault-Injection (ADR 0022 §2.4).
if self._fault_port is not None:
    self._fault_port.apply_active_faults(self._devices, context)

# Schritt B — Erste Iteration (non-GridConnection devices).
unknown_count += self._run_device_iteration(
    non_grid_devices, context, emitted, bucket_sums
)
```

**Order-Pflicht**: Faults werden VOR `device.tick(...)`
angewandt, damit Devices in derselben Tick auf den
gemutateten State reagieren koennen (z. B. Battery mit
`cell_failure` reduziert in dieser Tick den abrufbaren
`max_discharge_kw`). Reverse-Order (Faults nach Tick)
wuerde einen Tick-Delay einfuehren — abgelehnt, weil
weniger erwartungstreu.

**Exception-Propagation-Vertrag** (Welle-1-Review M-4):
Adapter-Exceptions aus `apply_active_faults(...)` propagieren
ungewrappt aus `TickLoop.tick()` heraus. TickLoop fuegt kein
try/except hinzu — Welle-2-Adapter entscheiden selbst, ob sie
Fail-Fast werfen oder einen Alarm-Pfad ueber Welle-3-/Welle-5-
Observability emittieren. Konsequenz fuer Welle 2: der
Adapter sollte typisierte `FaultPort*Error`-Subklassen werfen,
damit Aufrufer auf der Hexagon-Boundary differenzieren koennen.

**Fault-auf-GridConnection-Constraint** (Welle-1-Review M-5):
Faults auf `GridConnectionDevice` duerfen **NICHT**
`_pending_power_kw` oder `_current_power_kw` mutieren. Der
Welle-6b-Auto-Schluss (ADR 0021 §2.7, Schritt C in `tick()`)
ueberschreibt diese Felder in derselben Tick mit
`-pre_grid_residual_kw` — eine Power-Flow-Mutation durch einen
Fault wuerde verloren gehen. Welle-2-Grid-Faults (z. B.
`voltage_drop`) muessen Voltage-/Frequency-State mutieren
(Felder, die der Auto-Schluss nicht beruehrt). Falls ein
zukuenftiger Fault-Typ doch Power-Flow betreffen soll, ist die
korrekte Loesung ein Welle-2-Eintrag in
`manual_override_grid_ids` (analog LoadEvent-Override), damit
der Auto-Schluss-Schritt das Geraet ueberspringt.

### 2.5 `FaultPort | None`-Kwarg ohne Default

TickLoop-Konstruktor (Zeile 152-207) erhaelt einen neuen
keyword-only-Parameter:

```python
def __init__(
    self,
    *,
    run_id: str,
    ...
    active_load_profiles: tuple[LoadProfile, ...] = (),
    fault_port: FaultPort | None = None,
) -> None:
    ...
    self._fault_port: FaultPort | None = fault_port
```

**`None`-Default** (kein produktiver `NullFaultPort`-Adapter):
- Welle 1 hat keinen produktiven Adapter; alle bestehenden
  Tests setzen `fault_port` nicht (default `None`); der Hook
  in §2.4 skippt sauber.
- Welle-2-Test-Code, der einen `FaultPort` mocken will,
  schreibt einen Inline-Stub (3-4 Zeilen) — kein Test-Fake-
  Modul noetig.
- `*,`-Marker (keyword-only) verhindert positional-Aufrufe;
  bestehende `TickLoop(...)`-Aufrufer brechen nicht.

**Welle-2-Items-7-10-Review N-1 — `build_tick_loop`-Builder-
Symmetrie:** der Scenario-Loader-Builder aus ADR 0021 §2.4
(`build_tick_loop(scenario, *, clock, random_root)`) wird in
M3-Welle-1 ebenfalls um den `fault_port: FaultPort | None =
None`-Kwarg ergaenzt und reicht den Wert unveraendert an den
TickLoop-Konstruktor durch. Default bleibt `None`; M2-Welle-6b-
Tests, die `build_tick_loop` ohne Fault-Port aufrufen, bleiben
gruen. Siehe ADR 0021 §2.4 fuer die Builder-Signatur-Notiz.

### 2.6 Snapshot-Vertrag: kein neuer State in Welle 1

`FaultPort` selbst haelt **keinen** State in Welle 1; die
ADR-Surface ist nur ein Protocol-Vertrag, kein Adapter.
Konsequenzen:

- `TickLoop.snapshot()` (ADR 0015 §2.3 Sub-Snapshots-Vertrag)
  bekommt **keinen** neuen Sub-Snapshot-Key in Welle 1.
- Snapshot-Schema bleibt auf v2 (ADR 0015 unveraendert).
- Welle-2-Adapter koennen Fault-State haben (z. B.
  `active_fault_ticks_remaining: int` in BatteryDevice).
  **Falls** das eine Snapshot-Surface-Erweiterung erfordert,
  wird in Welle 2 eine Folge-ADR zu ADR 0015 (oder direkt
  Snapshot-Schema v2 → v3) entschieden. **Falls** der Fault-
  State im jeweiligen Device-Sub-Snapshot kapselt
  (Battery snapshot enthaelt `fault`-Block), bleibt es
  additiv im Sub-Snapshot-Format und braucht keinen
  Top-Level-Bump (ADR 0015 §2.3 ist explizit „Sub-Snapshot-
  Mapping" erweiterbar).

Welle-1-Stand: alle Wege offen, kein Vorgriff.

---

## 3. Begründung

**Sub-Protocol vs. Base-Erweiterung**: ADR 0013 §2.8 hat den
Pfad explizit vorgegeben („nicht als Methoden-Erweiterung des
Base"). Konsistenz-Argument: M2-Geraete sind seit Welle 2..6
auf der `DeviceModel`-Surface festgeschrieben; eine
Erweiterung mit `inject_fault(...)` wuerde alle fuenf
MVP-Geraete + alle Test-Doubles + alle bisherigen Snapshot-
Roundtrip-Tests beruehren. Sub-Protocol bricht keine
bestehende Surface.

**Orchestrierung vs. Per-Device-Hook**: drei Varianten waren
denkbar:

1. **Per-Device-Hook im TickLoop** — TickLoop iteriert
   `scenario.faults`, sucht selbst Target, ruft
   `device.inject_fault(...)`. *Abgelehnt*: TickLoop wird zur
   Fault-Engine, kann nicht durch Adapter ersetzt werden,
   testen aufwendig.
2. **Per-Device-Hook im Device** — Device-Konstruktor
   bekommt `faults: tuple[ScenarioFault, ...]`-Kwarg und
   prueft pro Tick selbst. *Abgelehnt*: kapselt Fault-Logik
   schlecht; jedes Device-Modell muesste eigene Fault-
   Engine-Logik haben.
3. **Orchestrierungs-Port** (gewaehlt) — TickLoop ruft genau
   einmal pro Tick einen abstrakten `FaultPort.apply_active_faults(...)`-
   Adapter, der die gesamte Entscheidung kapselt. *Vorteil*:
   TickLoop bleibt sauber; Adapter ist test-tauschbar;
   Adapter kann beliebig komplexe Aktivitaets-/Auswahl-Logik
   haben.

**ScenarioFault-Wiederverwendung**: `ScenarioFault` (M1-Welle-
5, `src/grid_gym/hexagon/core/domain/scenario.py:100-114`)
hat schon alle sechs Pflicht-Felder
(`start_simulation_time`, `duration_ms`, `target`, `type`,
`payload`, `recovery`). Keine neue Domain-Form noetig; Welle 1
nutzt das bestehende Datenmodell unveraendert. Welle 2 kann
ggf. einen Wrapper-Typ
(`ActiveFault(scenario_fault, remaining_ticks)`) einfuehren,
falls Adapter-State noetig — das ist Welle-2-Material.

**Target-Existenz-Check nur in Welle 1**: drei Alternativen
waren denkbar:

1. **Voll-Validation in Welle 1** (Type-Whitelist + Recovery-
   Whitelist + Duration-Bounds). *Abgelehnt*: Type-Whitelist
   ist Welle-2-Wissen (welche Faults sind ueberhaupt
   definiert?). Recovery-Whitelist ebenso.
2. **Keine Validation in Welle 1** (komplett verschoben auf
   Welle 2). *Abgelehnt*: die Target-Asymmetrie zu
   `_assert_event_list` ist eine echte Schema-Schwaeche;
   Fail-fast bei unbekanntem Target ist nuetzlich auch ohne
   konkrete Fault-Typen.
3. **Nur Target-Existenz** (gewaehlt) — minimal-invasiv,
   symmetrisch zu Events, ohne Welle-2-Wissen.

---

## 4. Reichweite

**In Scope (Welle 1):**

- `FaultInjectableDevice(DeviceModel)` Sub-Protocol-Definition
  unter `hexagon/core/faults/`.
- `FaultPort` Driven-Port-Definition unter `ports/driven/`.
- `ScenarioUnknownFaultTargetError` in `core/errors.py`.
- `_assert_fault_list`-Erweiterung um Target-Check.
- TickLoop-Konstruktor-Kwarg + Hook-Aufruf-Punkt.
- Tests fuer Protocol-Adherence, Validator-Negativ-Pfad,
  TickLoop-Hook-Order.
- `CRITICAL_COV_TARGETS`-Default-Erweiterung um
  `core/faults`.

**Out of Scope (Welle 2+):**

- Konkrete `FaultPort`-Adapter (`BatteryFaultAdapter`,
  `GridFaultAdapter`).
- Konkrete Fault-Typen (`cell_failure`, `voltage_drop`,
  `cell_failure_payload_schema`).
- `BatteryDevice` + `GridConnectionDevice` als Implementer
  von `FaultInjectableDevice`.
- Recovery-Logik (Modi `auto-recover-after-N-ticks`,
  `manual-via-command`, `permanent`).
- Type-Whitelist im Validator.
- Property-Tests fuer Fault-Determinismus.
- Integrationstest mit `fault_demo.yaml`-Szenario.

**Out of Scope (M3-Welle-7+ oder M6):**

- Multi-Agent-Bus, Agent-Decision-Loop (ADR 0023, M3-Welle-3+).
- OTLP-Observability-Adapter (ADR 0024, M3-Welle-5+).
- Snapshot-Schema-Bump v2 → v3 (falls Welle 2 keine
  Sub-Snapshot-Erweiterung reicht, dann eigene Folge-ADR;
  sonst M6 `GG-PERSIST-*`).
- RL-Adapter (`GG-FUTURE-001/002`).

---

## 5. Operative Artefakte

| Pfad                                                                | Aktion |
| ------------------------------------------------------------------- | ------ |
| `src/grid_gym/hexagon/core/faults/_protocol.py`                     | NEU (`FaultInjectableDevice`) |
| `src/grid_gym/hexagon/core/faults/__init__.py`                      | EDIT (re-export) |
| `src/grid_gym/hexagon/ports/driven/fault.py`                        | NEU (`FaultPort`) |
| `src/grid_gym/hexagon/core/errors.py`                               | EDIT (`ScenarioUnknownFaultTargetError`) |
| `src/grid_gym/hexagon/core/scenario/validator.py`                   | EDIT (`_assert_fault_list` Target-Check) |
| `src/grid_gym/hexagon/core/simulation/tick_loop.py`                 | EDIT (Konstruktor-Kwarg + Hook) |
| `tests/unit/hexagon/core/faults/test_protocol.py`                   | NEU |
| `tests/unit/hexagon/ports/driven/test_fault.py`                     | NEU |
| `tests/unit/hexagon/core/scenario/test_validator_fault_target.py`   | NEU |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_1_fault.py`| NEU |
| `Dockerfile`                                                        | EDIT (`CRITICAL_COV_TARGETS` + `core/faults`) |

ADR-Cross-Refs (read-only fuer Welle 1):
- ADR 0013 §2.8 zitiert in Code-Docstrings.
- ADR 0021 §2.5 zitiert im TickLoop-Hook-Kommentar.
- Diese ADR wird mit Welle-7-Closure auf `Accepted` gehoben
  (Pattern aus ADR 0017/0018/0021).

---

## 6. Konsequenzen

**Positive Konsequenzen:**

- `DeviceModel`-Surface bleibt M2-stabil; M3-Faults sind
  additive Sub-Protocol-Erweiterung. M2-Tests bleiben gruen.
- TickLoop hat einen klar definierten Hook-Punkt analog
  Welle-6b-LoadEvent-Overlay; Welle-2-Adapter kann sich
  einklinken.
- Scenario-Validator faengt unbekannte Fault-Targets fail-
  fast ab, parallel zu Events.
- Welle 2 hat eine klare Schnittstelle, an die
  `BatteryFaultAdapter` + `GridFaultAdapter` einsteigen
  koennen.

**Verbindliche Konsequenzen fuer Welle 2:**

- `BatteryDevice` muss `FaultInjectableDevice` implementieren
  (oder explizit nicht — dann wirft FaultPort eine typisierte
  Fehlermeldung beim Versuch).
- `GridConnectionDevice` ebenso.
- Pro Geraet wird in Welle 2 entschieden: welche
  `fault_type`-Werte versteht es? Was ist das Payload-Schema?
  (Beispiel: `cell_failure` -> `{"affected_cell_index": int}`).
- Welle-2-ADR (z. B. ADR 0025) kann `FaultPort`-Adapter-
  Vertrag schaerfen (Welle-1-Pattern: `Schaerfung ohne
  Supersedes`).

**Restpost — Snapshot-Schema:**

- ADR 0015 bleibt v2; Welle 1 fuegt keinen Sub-Snapshot-Key
  hinzu.
- Welle-2-Adapter koennen Fault-State haben; ob das einen
  Snapshot-Bump v2 → v3 erfordert, wird in Welle 2 entschieden
  (ADR 0015-Pattern: typisierter `TickLoopSnapshotVersionError`
  mit M6-`GG-PERSIST-*`-Pointer).

**Pflege-Gleichheit:**

- `_DEVICE_FACTORIES` (Scenario-Loader,
  `src/grid_gym/hexagon/core/scenario/loader.py:59-65`)
  ist von Welle 1 **nicht** betroffen — Fault-Adapter sind
  nicht ueber Loader-Factory dispatched. Welle 2 entscheidet,
  ob ein Fault-Adapter-Registry analog `_DEVICE_FACTORIES`
  noetig ist.
- `_DEVICE_TYPE_BY_CLASS_NAME` (TickLoop,
  `tick_loop.py:115-121`) bleibt unveraendert.

---

## 7. Nicht Gegenstand

**Multi-Agent-Subsystem** (`GG-AGENT-001..008`) — eigene ADR
0023 in M3-Welle-3+. AgentBus + AgentPort sind orthogonal zu
FaultPort und kommen mit ihrer eigenen Welle-Folge.

**Observability-Ports** (`GG-OTEL-001..004`,
`GG-AR-PORT-DRN-008`) — eigene ADR 0024 in M3-Welle-5+.
`LogPort`/`MetricsPort`/`TracePort` sind orthogonal zu
FaultPort und kommen spaeter. Welle-5-ADR-Folge entscheidet,
ob FaultPort-Aktivitaet ueber MetricsPort/TracePort
beobachtbar wird (Cross-Concern aus
`M3-faults-agents-observability.md §5 Risiken`).

**Konkrete Fault-Typen** (`cell_failure`, `voltage_drop`,
weitere aus `GG-FAULT-001..010`) — Welle 2 entscheidet pro
Geraet, welche Typen unterstuetzt werden. Welle-2-ADR (z. B.
ADR 0025) kann FaultPort-Adapter-Vertrag schaerfen.

**Recovery-Logik** (`auto-recover-after-N-ticks`,
`manual-via-command`, `permanent` aus
`GG-FAULT-001..010` + `GG-SAFE-001..006`) — Welle 2.
ScenarioFault.recovery ist syntaktisch validiert; die
semantische Interpretation lebt im Adapter.

**RL-Adapter** (`GG-FUTURE-001/002`) — Folge-Slice nach
M3-Closure. M3-Multi-Agent-Bus ist RL-faehig, aber der RL-
Trainings-Loop bleibt extern.

**M4-Protokolladapter** (MQTT/Modbus/OPC-UA/DNP3/IEC) — M4.

**Performance-Benchmarks** (`GG-RT-004/005`) — M6.

**SOLLTE-Geraete-/Netz-/Battery-Trigger** (`016..024` aus
M2-Welle-7-Erbschaft) — eigene Slices nach M3-Closure.

**Snapshot-Migration v2 → v3** — Welle 2 oder spaetere ADR-
Folge entscheidet, ob ein Bump noetig ist; falls ja, kommt der
Lese-Migrations-Pfad als M6 `GG-PERSIST-*`-Material
(ADR 0015-Pattern).
