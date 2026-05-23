# ADR 0013 — `DeviceModel`-Protocol als Core-internes Protocol

**Status:** Accepted — kein Validierungs-Spike erforderlich.
Direkter `Proposed → Accepted`-Sprung per `ADR 0006 §2`-Klausel
(„ADR ohne Validierungsbedarf"); die Protocol-Adherence wird in
einem Unit-Test gegen `NullDevice` verifiziert, der mit dieser
ADR mitgeliefert wird.
**Datum:** 2026-05-18
**Status geaendert am:** 2026-05-18 — `Proposed → Accepted`.
**Geschaerft am:** 2026-05-18 (Welle-1-Review-Folge-Commits) —
§§2.5/2.6/2.7/2.8 + §8 ergaenzt, `from_snapshot`-Pflicht in das
Protocol gehoben, Lifecycle-Pre-init-Vertrag fixiert, `device_id`-
Property hinzugefuegt, Protocol-Evolution-Strategy dokumentiert.
Schaerfung folgt `ADR 0011`-Pattern (parallele Schaerfung ohne
Supersedes — der urspruengliche Entscheidungs-Kern in §§2.1..2.4
ist unveraendert; §2.5+ schliessen zuvor implizite Luecken
explizit).
**Erneut geschaerft am:** 2026-05-18 (Welle-3-Review-Folge —
ADR 0016 H-3 Spiegel) — §2.4 ergaenzt um den Post-init-Scope
des Roundtrip-Vertrags (Pre-init-`snapshot()` ist nicht
roundtrippable, das ist per Vertrag so gewollt).
**Bezug:**
[`ADR 0002`](0002-language-and-build-stack.md) §A-1
(`AC-HEXAGON-PURE`, `AC-PORTS-NO-OUT`, `AC-DOMAIN-FROZEN`),
[`ADR 0007`](0007-random-port.md) §5 (`RandomPort.sub_port`-
Vertrag fuer Geraete-Fault-Streams),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-
ADR-Pattern; diese ADR erweitert `ADR 0002 §A-1`-Komponenten-
Liste um `GG-AR-COMP-DEVICES::DeviceModel`),
M2-Slice-Plan
[`done/M2-devices.md`](../planning/done/M2-devices.md)
§3 Welle 1, Lastenheft §9 (`GG-DEV-001..003`).

---

## 1. Kontext

M2 fuellt den bisher leeren `hexagon/core/devices/`-Slot mit den
MVP-Geraetemodellen (`battery`, `pv`, `load`, `smart_meter`,
`grid_connection`). Bevor konkrete Implementationen in M2 Welle 2
beginnen, braucht die Plattform einen **expliziten Vertrag**:
welche Methoden hat jedes Geraet, welche Typen werden ein-/
ausgereicht, wie sieht der Lifecycle aus.

Lastenheft `GG-DEV-001` Akzeptanz:

> Jedes Geraetemodell implementiert mindestens `initialize`,
> `tick`, `apply_command`, `snapshot` und `telemetry`.

Diese Methoden-Liste reicht als Pflicht-Set; die ADR fixiert die
Signaturen, die Modul-Lage und die offenen Auslegungs-Fragen aus
dem M2-Slice-Plan §5 Risiken-Block.

Drei Architektur-Fragen sind im Slice-Plan §5 explizit als offen
markiert und werden hier entschieden:

1. **Placement**: Core-internes Protocol unter
   `hexagon/core/devices/_protocol.py` oder Driving-Port unter
   `hexagon/ports/driving/device.py`?
2. **Tick-Context-Form**: traegt `DeviceTickContext` einen
   `random_sub_port: RandomPort`-Field, oder bekommen Geraete die
   `RandomPort`-Referenz einmalig per `initialize(...)`?
3. **Command-Flow**: ruft der TickLoop `apply_command(cmd)` separat
   pro Pending-Command vor `tick(context)`, oder bekommt
   `tick(context)` ein `pending_commands`-Tuple und ruft sich
   selbst intern apply_command auf?

---

## 2. Entscheidung

### 2.1 Placement: Core-internes Protocol

`DeviceModel` lebt als `typing.Protocol` unter
`hexagon/core/devices/_protocol.py`. Es ist **kein Driving-Port**.

Begruendung — primaer konzeptuell, sekundaer architektonisch:

- **Konzeptuell:** Geraete sind fachliche Modelle, die der
  TickLoop konsumiert (`TickLoop.tick()` ruft
  `device.tick(context)` auf). Ein Driving-Port ist per Definition
  ein Vertrag, ueber den die *Aussenwelt* den Core treibt — Devices
  treiben den Core nicht, sie sind seine Fachschicht.
- **Architektonisch:** `AC-PORTS-NO-OUT` (`ADR 0002 §A-1`)
  erlaubt `hexagon.ports.* → hexagon.core.domain.*`, verbietet
  aber `hexagon.ports.* → hexagon.core.simulation/devices/
  scenario/...`. `DeviceModel` braucht `ScenarioDevice` als
  Argument-Typ — der liegt in `hexagon/core/domain/scenario.py`,
  also formal als Port-Import erlaubt. Der hartere Stopper ist
  also nicht AC-PORTS-NO-OUT, sondern die konzeptuelle Richtung
  oben.
- **Erlaubte Richtung:** `AC-HEXAGON-PURE` erlaubt
  `hexagon/core/devices/* → hexagon.ports.driven.*` (Core darf
  Ports konsumieren). Damit kann `_protocol.py` `RandomPort` als
  Argument-Typ referenzieren, ohne den AC-Vertrag zu brechen.

### 2.2 `DeviceTickContext` ohne `random_sub_port`-Field

`DeviceTickContext` (`hexagon/core/domain/device.py`) traegt nur
Sim-Zeit-Felder: `tick`, `simulation_time`, `tick_ms`. Es enthaelt
**keine** `RandomPort`-Referenz.

Begruendung:

- Domain-Module in `hexagon/core/domain/**` sind in M1 streng
  port-frei. `RandomPort` als Frozen-Dataclass-Field wuerde die
  erste `domain → ports.driven`-Import-Kante einfuehren — eine
  Praezedenz, die unklar in den AC-Contracts ist (`AC-DOMAIN-
  FROZEN` regelt Klassen-Shape, nicht Import-Direktion, aber das
  Pattern „Domain ist pure Daten" ist load-bearing fuer Test-
  Schreibbarkeit und Snapshot-Determinismus).
- Geraete bekommen `RandomPort` einmalig in
  `DeviceModel.initialize(scenario_device, random)`. Devices
  speichern den Port als Instanz-Zustand und nutzen ihn aus
  `tick()`, `apply_command()`, `snapshot()` heraus.
- Der TickLoop ruft `initialize(scenario_device, root_random
  .sub_port(scenario_device.id))` pro Geraet einmal beim Lauf-
  Start auf (ADR 0007 §5 Sub-Port-Konvention).
- **ID-Uniqueness-Vorbedingung:** ADR 0007 §5 `sub_port(name)`
  hashed `f"{parent_seed}:{name}"` zum Sub-Seed; zwei Geraete
  mit identischer `ScenarioDevice.id` wuerden den selben
  Random-Stream teilen (stille Determinismus-Verletzung).
  Diese Bedingung ist NICHT Pflicht der DeviceModel-Implementation;
  sie wird upstream im Scenario-Loader durchgesetzt
  (`hexagon/core/scenario/validator.py::_assert_device_list`,
  Welle-0a-Stand line 142..167, wirft
  `ScenarioDuplicateDeviceIdError` vor Tick-Start). TickLoop
  darf voraussetzen, dass alle gelaufenen Scenarios diese
  Vorbedingung erfuellen.

### 2.3 Command-Flow: separate `apply_command` + `tick`

Der TickLoop ruft **erst** `device.apply_command(cmd)` fuer jeden
Pending-Command, der dieses Geraet adressiert, **dann**
`device.tick(context)`. `DeviceTickContext` enthaelt **kein**
`pending_commands`-Field — die Commands sind zum Zeitpunkt von
`tick()` bereits angewendet.

Begruendung:

- Architecture §6 Datenfluss-Schritt 5: „fuer jedes Device:
  `apply_command -> tick -> telemetry`". Der separate Aufruf-
  Pfad ist die kanonische Form.
- `tick(context)` ist damit eine reine Funktion von
  (internem Zustand vor Tick, Sim-Zeit-Context) → DeviceTickOutcome.
  Das macht Property-Tests einfacher: Seed + Command-Sequenz +
  Tick-Folge erzeugt deterministische Telemetrie.
- Reduziert `DeviceTickContext`-Komplexitaet (drei int-Felder
  statt vier Felder inklusive eines variabel-langen Tuples).

**Ordering und Multiplicity** (Welle-1-Review H-6):

- TickLoop ruft `apply_command(cmd)` in **Scenario-Source-Reihenfolge**
  (`GG-ARCH-006`-Tie-Breaking auf `(time, priority, source,
  sequence, event_id)`) auf. Mehrere Commands fuer dasselbe
  Device im selben Tick werden in dieser Reihenfolge angewendet —
  Devices duerfen sich darauf verlassen.
- **Same-Tick-Multiplicity:** das Protocol macht keine Aussage
  zur Semantik mehrerer Commands desselben Typs im selben Tick
  (z. B. zwei `set_power_setpoint` an dieselbe Battery). Konkrete
  Geraete-Implementationen (ADR 0014 fuer Battery in Welle 2,
  analog fuer PV/Load/SmartMeter/GridConnection) legen die
  Semantik pro Geraetetyp fest: last-wins, accumulate, oder
  reject-later. Default-Empfehlung fuer Welle 2: **last-wins**
  (zweiter Command ueberschreibt den ersten); Welle-2-PR
  dokumentiert die Wahl in ADR 0014 §2.
- **Idempotency:** ein `apply_command(cmd)` darf den internen
  Zustand der Device-Instanz mutieren. Es ist NICHT idempotent
  per Default; zweimaliges Anwenden desselben Commands MAY zu
  unterschiedlichen Zustaenden fuehren (z. B. wenn der Command
  als Rate-Limit-Increment formuliert ist). Welle-2-PR
  dokumentiert pro Geraetetyp.
- **`Command.result`-Field:** der TickLoop aktualisiert das
  `Command.result`-Field NACH dem `apply_command`-Aufruf mit dem
  Rueckgabewert; `apply_command` selbst muss `Command` nicht
  mutieren (Command ist `@dataclass(frozen=True)` — TickLoop
  baut ggf. ein neues Command-Objekt).

### 2.4 Snapshot-Vertrag fuer Geraete

`DeviceModel.snapshot()` MUSS ein `Mapping[str, object]` mit
`version: int` als Erst-Feld liefern (M1 Welle 1 / M2 Welle 0a
Trigger 014 Konvention). `SnapshotEnvelope.__post_init__` prueft
das beim Composition-Aufruf — Geraete-Implementationen brauchen
die Pflicht nicht selbst zu duplizieren.

**Mechanische `from_snapshot`-Pflicht** (Welle-1-Review C-3 hat
das urspruengliche „nicht Teil des Protocols"-Argument als
soft-contract aufgedeckt): `from_snapshot` ist jetzt
**Bestandteil des `DeviceModel`-Protocols** als
`@classmethod`. Python 3.10+/`@runtime_checkable` unterstuetzt
Protocol-Classmethods. `isinstance(BatteryDevice(), DeviceModel)`
schlaegt damit auch bei einer Implementation ohne `from_snapshot`
fehl — die mechanische Adherence-Pruefung greift.

Vertrag der Classmethod:

```python
@classmethod
def from_snapshot(cls, state: Mapping[str, object]) -> Self: ...
```

Rueckgabe ist `Self` (typing.Self, Python 3.11+) — eine konkrete
Battery rekonstruiert sich aus einem Battery-Snapshot, nicht aus
einem PV-Snapshot. Implementationen MUESSEN typed mit
`SnapshotFormatError`-Hierarchie (Welle-0a-Codec) auf Mismatch
reagieren: `MissingKeysError`/`WrongTypeError`/`VersionError`
sind die richtigen Sub-Typen.

**Roundtrip-Test-Pflicht** je Geraet: `from_snapshot(snapshot())
== device` byte-stabil. Welle-2-Battery zeigt das Pattern; PV/
Load/SmartMeter/GridConnection in Welle 3/4 kopieren mechanisch.

**Post-init-Scope (Welle-3-Review H-3-Spiegel):** Der Roundtrip-
Vertrag gilt nur fuer den **post-`initialize()`-Zustand**. Pre-
init liefert `snapshot()` per §2.6 das Minimum
`{"version": SNAPSHOT_VERSION}`, das per Codec-Vertrag (Welle 0a
`MissingKeysError`) NICHT roundtrippable ist — `from_snapshot(
{"version": 1})` wirft typed. Welle 6 TickLoop ruft `snapshot()`
nur ueber initialisierte Geraete; M3 Replay-Resume setzt
initialisierte Geraete voraus. ADR 0016 §2.3 spiegelt den
Vertrag explizit fuer PV/Load.

### 2.5 `telemetry()`-vs-`tick()`-Telemetry-Vertrag

Beide Pfade liefern `tuple[TelemetryPoint, ...]`. Welle-1-Review
C-1 hat zu Recht aufgedeckt, dass das Verhaeltnis unklar war.
Vertrag:

- `tick(context) -> DeviceTickOutcome.telemetry` ist die
  **kanonische Quelle** der Telemetrie eines Ticks. Hier
  entsteht der Wert, hier wird er deterministisch sortiert.
- `telemetry() -> tuple[TelemetryPoint, ...]` ist ein
  **Pure-Read-Accessor** auf das vom letzten `tick()`
  emittierte Tuple. Vertrag:
  - Vor dem ersten Tick: `() ` (leeres Tupel).
  - Nach `tick(ctx_n)`: gibt **`==`-identisch** das selbe Tupel
    wie `DeviceTickOutcome.telemetry` zurueck, das `tick(ctx_n)`
    geliefert hat.
  - Devices implementieren das via Caching (`self._last_telemetry
    : tuple[TelemetryPoint, ...] = ()`, am Ende von `tick()`
    gesetzt).
- Aufrufer-Ergonomie: Aggregator-Code, der ueber alle Geraete
  iteriert und Telemetrie ohne Tick-Fortschreibung braucht
  (z. B. SmartMeter-Aggregation in Welle 4), nutzt
  `device.telemetry()` als read-only-View.

### 2.6 Lifecycle-Vertrag fuer Pre-`initialize()`-Aufrufe

Welle-1-Review C-2 hat zu Recht aufgedeckt, dass das Protocol
ueber Pre-init-Verhalten geschwiegen hat. Vertrag:

- `initialize(scenario_device, random)` ist Pflicht-Erstaufruf.
  Eine **zweite** `initialize()`-Invocation MUSS typed mit
  `DeviceAlreadyInitializedError` (`hexagon/core/errors.py`)
  abgelehnt werden — Devices sind nicht resettable per Protocol.
- `tick(context)` und `apply_command(command)` werfen typed
  `DeviceNotInitializedError`, wenn `initialize()` noch nicht
  gelaufen ist.
- `device_id` (siehe §2.7) wirft `DeviceNotInitializedError`
  pre-init.
- `snapshot()` und `telemetry()` sind pre-init zulaessig und
  liefern minimal:
  - `snapshot()` → `{"version": cls.SNAPSHOT_VERSION}` ohne
    weiteren State (testbar, structurally valide).
  - `telemetry()` → `()` (leeres Tupel).

Die beiden Error-Klassen (`DeviceNotInitializedError`,
`DeviceAlreadyInitializedError`) gehoeren in `hexagon/core/errors.py`
und erben von einer neuen Sammel-Klasse
`DeviceLifecycleError(GridGymError)`.

### 2.7 `device_id`-Access via Protocol-Property

Welle-1-Review H-1 hat zu Recht aufgedeckt, dass der
`device_id`-Zugriff via `self.scenario_device.id` ein implicit
contract war. Schaerfung:

`DeviceModel` hat eine **Pflicht-Property** `device_id: str`:

```python
@property
def device_id(self) -> str: ...
```

Die Property muss `scenario_device.id` zurueckgeben (oder
`DeviceNotInitializedError` pre-init werfen). TickLoop ruft
`device.device_id` statt `device.scenario_device.id` — das Storage-
Pattern (wie und ob `scenario_device` als Attribut lebt) bleibt
Implementation-Sache. Welle 6 Sub-Snapshot-Key
`devices.<device.device_id>` nutzt diese Property.

### 2.8 Protocol-Evolution-Strategie

Welle-1-Review M-4 hat zu Recht aufgedeckt, dass das Hinzufuegen
einer sechsten Protocol-Methode in M3 (`inject_fault(...)`) alle
Welle 2..5 Devices ueber Nacht aus `isinstance(dev, DeviceModel)`
fallen lassen wuerde. Strategie:

- `DeviceModel` ist **closed** durch M2 (Welle 2..7).
- Methoden-Erweiterungen fuer Post-MVP-Features (M3 Faults,
  M4 Protocol-Adapter etc.) kommen als **separate Protocol-
  Klassen**: `FaultInjectableDevice(DeviceModel)`,
  `ExternallyAddressableDevice(DeviceModel)` etc.
- Devices opt-in durch Implementation des erweiterten Protocols.
  Bestehende M2-Devices bleiben `DeviceModel`-konform.
- Tests pruefen sowohl `isinstance(dev, DeviceModel)` (base) als
  auch `isinstance(dev, FaultInjectableDevice)` (extension).

Die Kombination aus 2.1 (Core-Protocol), 2.2 (port-freier
Context), 2.3 (separater Command-Flow) bewahrt drei load-bearing
M1-Patterns:

1. **Domain ist pure Daten.** Keine Port-Referenzen in
   Frozen-Dataclasses unter `hexagon/core/domain/**`.
2. **Ports treiben den Core.** `DeviceModel` ist nicht symmetrisch
   zu Driven-Ports wie `ClockPort`/`RandomPort` — Devices sind
   Konsumenten, nicht Lieferanten von Daten.
3. **Tick-Verarbeitung folgt Architecture §6.** Der dort
   beschriebene Datenfluss (`apply_command → tick → telemetry`)
   ist die kanonische Form; Devices folgen ihm, statt eine
   Batch-Variante zu definieren.

Die `DeviceModel`-Decision-Latitude bleibt offen fuer
M3 (Fault-Injection) und M4 (Protocol-Adapter): beide bauen auf
dem hiesigen Vertrag auf, ohne ihn brechen zu muessen.

---

## 4. Reichweite

Diese ADR gilt fuer:

- Alle Geraete-Implementationen unter `hexagon/core/devices/*`
  (M2 Welle 2..5: Battery, PV, Load, SmartMeter, GridConnection).
- Das Netzbilanzmodell unter `hexagon/core/grid_model/`
  (M2 Welle 5) erbt das Snapshot-Pattern (`version: int`-Erstfeld,
  `from_snapshot`-Classmethod), **nicht** aber das DeviceModel-
  Protocol — `grid_model` ist kein Device.
- Die Tick-Loop-Integration in M2 Welle 6
  (`TickLoop.tick()` ruft `apply_command`/`tick`/`telemetry`/
  `snapshot` in der Architecture-§6-Reihenfolge).

Diese ADR gilt NICHT fuer:

- Future-Geraete jenseits M2 (`GG-DEV-015..018` SOLLTE-Geraete);
  diese erben den Vertrag mechanisch, aber ihre Aktivierung ist
  Post-MVP-Slice-Verantwortung.
- Driving-Adapter (`adapters/driving/http_api/`); die kennen das
  Protocol nicht direkt — sie sprechen den TickLoop an, der
  intern die Geraete iteriert.

---

## 5. Operative Artefakte

Mit Acceptance dieser ADR (post-Welle-1-Review) liegen folgende
Module:

- `src/grid_gym/hexagon/core/devices/__init__.py` —
  Re-Export von `DeviceModel` als Top-Level-Symbol des Pakets.
- `src/grid_gym/hexagon/core/devices/_protocol.py` —
  `DeviceModel` Protocol mit:
  - fuenf Pflicht-Methoden
    (`initialize`/`apply_command`/`tick`/`snapshot`/`telemetry`),
  - `device_id: str`-Pflicht-Property (§2.7),
  - `from_snapshot`-Pflicht-Classmethod (§2.4, mechanisch via
    `@runtime_checkable` enforced).
- `src/grid_gym/hexagon/core/domain/device.py` —
  `DeviceTickContext`/`DeviceTickOutcome` Frozen-Dataclasses,
  port-frei.
- `src/grid_gym/hexagon/core/errors.py` (erweitert):
  `DeviceLifecycleError(GridGymError)` Sammel-Klasse plus
  `DeviceNotInitializedError`/`DeviceAlreadyInitializedError`
  (§2.6).
- `tests/unit/hexagon/core/devices/_fakes.py` — `NullDevice`-
  Test-Double, der das Protocol satisfies (wird in Welle 2..5
  als Baseline fuer per-Device-Adherence-Tests wiederverwendet);
  implementiert `from_snapshot`, `device_id` und Lifecycle-
  Pre-init-Raises.
- `tests/unit/hexagon/core/devices/test_protocol_contract.py` —
  Protocol-Adherence-Test: `isinstance(NullDevice(), DeviceModel)`,
  Methoden-Surface-Check, `snapshot()`-`version`-Erstfeld-Pruefung,
  Pre-init-Raises, Roundtrip via `from_snapshot`, Wrong-Signature-
  Negativ-Pfade.

---

## 6. Konsequenzen

**Was sich aendert:**

- `hexagon/core/devices/` ist ab jetzt produktiv (vorher leer).
- M2 Welle 2..5 Geraete-PRs koennen direkt gegen das Protocol
  programmieren; das `__init__.py` macht
  `from grid_gym.hexagon.core.devices import DeviceModel`
  einzeilig.
- `DeviceTickContext`/`DeviceTickOutcome` werden in M2 Welle 6
  von `TickLoop.tick()` instantiiert; bis dahin nur in Tests
  konsumiert.

**Was load-bearing bleibt:**

- M1-Konvention „Domain ist pure Daten" wird durch die port-freie
  `domain/device.py` fortgesetzt; die in M1 Welle 1..5 etablierte
  Praezedenz steht.
- `AC-HEXAGON-PURE`, `AC-PORTS-NO-OUT`, `AC-DOMAIN-FROZEN`,
  `AC-NO-CYCLES` werden mit der Welle-1-Lieferung weiter erzwungen
  (`make arch-check` als Pflicht-Gate).

**Was offen bleibt (Welle 2+-Material):**

- Konkrete Geraete-Snapshot-Schemata (Battery → ADR 0014,
  Envelope-v1→v2 → ADR 0015) folgen jeweils mit ihrer Welle.
- Fault-Injection-Erweiterung des Protocols (`DeviceModel.inject_fault(...)`)
  ist M3; diese ADR sieht das bewusst nicht vor (`GG-FAULT-001..010`-
  Out-of-Scope-Eintrag im Slice-Plan §4). Die Erweiterungs-
  Mechanik (separate Protocol-Klasse via Sub-Typing) ist in
  §2.8 fixiert.
- **Per-Device-Snapshot-Version-Strategie** (Welle-1-Review I-2):
  jedes Geraet bringt seinen eigenen `version: int`-Wert mit
  (Battery startet mit `version=1` in ADR 0014; PV/Load/etc.
  analog mit Welle-3/4-PR-ADRs). Wenn ein Folge-Slice ein
  zusaetzliches Field einfuehrt, BUMPT die ADR die Version (z. B.
  `Battery v1 → v2`) und `from_snapshot` MUSS typed mit
  `VersionError(subsystem="battery", expected=2, found=1)`
  reagieren — Back-Compat-Read ist explizit M6-Material
  (`GG-PERSIST-*`-Migrations-Slice), kein per-Welle-Pflichtweg.

---

## 7. Nicht Gegenstand dieser ADR

- **Geraete-Faults.** `DeviceModel.inject_fault(...)` oder
  aequivalent kommt mit M3; diese ADR fixiert das nicht.
- **Multi-Agent-Steuerentscheidungen.** `AgentPort` (`GG-AGENT-001`)
  spricht den TickLoop an, nicht die Devices direkt.
- **Protocol-Adapter-Mapping.** MQTT/Modbus/OPC-UA/DNP3/IEC
  (`GG-MQTT/MODB/OPCUA/DNP3/IEC-001`) konsumieren das Geraete-
  Surface via TickLoop und `DeviceProtocolPort` (`GG-AR-PORT-DRN-007`);
  M4-Slice.
- **`DeviceTickOutcome`-Erweiterung um Alarme.** Welle 1 liefert
  nur `telemetry`; Alarm-Felder kommen mit M3 Fault-Injection.
  Die Erweiterungs-Strategie (Default-Tupel hinzufuegen, Frozen-
  Dataclass-Konstruktion bleibt back-compat) ist trivial — die
  ADR fixiert sie hier nicht eigens.

---

## 8. Protocol-Evolution-Beispiele (M3+ Vorschau)

Diese Sektion gibt konkrete Beispiele, wie §2.8 in spaeteren
Meilensteinen angewendet wird. Sie ist **nicht-bindend** — die
M3-PR-Autoren entscheiden zur Aktivierungszeit, ob das Beispiel
passt oder ein neues Pattern noetig ist.

**M3 Fault-Injection:**

```python
@runtime_checkable
class FaultInjectableDevice(DeviceModel, Protocol):
    """Erweitert DeviceModel um per-Tick-Fault-Injection."""

    def inject_fault(self, fault: ScenarioFault) -> None: ...
    def recover_from_fault(self, fault_id: str) -> None: ...
```

M2-Geraete (Battery/PV/Load/...) bleiben `DeviceModel`-konform —
sie sind ohne Adjustment auch in M3 lauffaehig, koennen aber kein
`inject_fault()` annehmen. M3-PR-Autoren entscheiden pro
Geraetetyp, ob das Sub-Protocol implementiert wird; Fault-Aware-
TickLoop prueft `isinstance(dev, FaultInjectableDevice)`.

**M4 Protokoll-Adapter:**

```python
@runtime_checkable
class ExternallyAddressableDevice(DeviceModel, Protocol):
    """Erweitert DeviceModel um externe Protokoll-Adressierung
    (MQTT-Topic, Modbus-Register-Map, etc.)."""

    @property
    def external_address(self) -> Mapping[str, str]: ...
```

Auch hier: M2-Devices bleiben konform; M4-PR-Autoren entscheiden,
welche Geraete extern adressierbar sind.

**Wichtige Konstanz:** `DeviceModel` selbst bleibt **closed** bei
fuenf Methoden + `device_id`-Property + `from_snapshot`-Classmethod
durch M2 Welle 7. Erst nach M2-Closure (Roadmap §3 M2 → Done) ist
eine geschmeidige Welle frei, das Base-Protocol formal um z. B.
`alarms`-Felder zu erweitern; bis dahin sind Erweiterungen
ausschliesslich via Sub-Typing.

---

## 9. Vertragssicherheit pro Stufe

Welle-1-Review N-2 hat zu Recht angemerkt, dass das DeviceModel-
Protocol drei Sicherheits-Stufen mit unterschiedlichen
Reichweiten kombiniert. Diese Sektion fixiert das Mapping
explizit, damit Welle-2-Implementierer wissen, wo welche
Pruefung greift.

| Stufe                       | Werkzeug                                | Reichweite                                                                                                  | Wo geprueft                                                                                             |
| --------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Member-Namen (Stufe 1)      | `@runtime_checkable typing.Protocol` + `isinstance(...)` | Vorhandensein der sieben Pflicht-Member (5 Methoden + Property + Classmethod). Wirft KEINE Signatur-Pruefung. | `tests/unit/hexagon/core/devices/test_protocol_contract.py::test_null_device_satisfies_device_model_protocol` + `test_class_missing_one_method_fails_protocol` + `test_class_missing_device_id_property_fails_protocol` |
| Signaturen (Stufe 2)        | `mypy --strict` (`ADR 0005`)            | Argument-/Rueckgabe-Typen, Generic-/Self-Konformitaet. mypy ueberprueft das konkrete Geraete gegen den Protocol-Vertrag bei Implementation. | `make typecheck` (Dockerfile-Stage). Faellt rot, wenn z. B. `BatteryDevice.tick(self)` ohne `context` deklariert wird. |
| Verhalten / Lifecycle (Stufe 3) | Per-Geraete-Unit-Tests + ADR 0013 §§2.3/2.5/2.6 | Determinismus, Pre-init-Raises, Telemetry-Caching, apply_command-Ordering, from_snapshot-Roundtrip. Soft contracts mechanisch via Tests durchgesetzt. | `tests/unit/hexagon/core/devices/<typ>/test_*.py` (Welle 2..5) + `test_protocol_contract.py`-Konventions-Tests. |

**Bekannte Stufe-1-Beschraenkung:** ein Test in Welle 1
(`test_wrong_signature_still_passes_isinstance`) pinnt das
Verhalten explizit: eine Implementation mit `tick(self)` (ohne
`context`-Parameter) passt `isinstance(obj, DeviceModel)`
trotzdem. Die korrekte Signatur wird erst durch Stufe 2
(`mypy --strict`) abgefangen. Welle-2-Implementierer duerfen
sich NICHT allein auf `isinstance` verlassen — der Vertragsweg
ist isinstance UND mypy UND per-Geraete-Tests.
