# ADR 0013 — `DeviceModel`-Protocol als Core-internes Protocol

**Status:** Accepted — kein Validierungs-Spike erforderlich.
Direkter `Proposed → Accepted`-Sprung per `ADR 0006 §2`-Klausel
(„ADR ohne Validierungsbedarf"); die Protocol-Adherence wird in
einem Unit-Test gegen `NullDevice` verifiziert, der mit dieser
ADR mitgeliefert wird.
**Datum:** 2026-05-18
**Status geaendert am:** 2026-05-18 — `Proposed → Accepted`.
**Bezug:**
[`ADR 0002`](0002-language-and-build-stack.md) §A-1
(`AC-HEXAGON-PURE`, `AC-PORTS-NO-OUT`, `AC-DOMAIN-FROZEN`),
[`ADR 0007`](0007-random-port.md) §5 (`RandomPort.sub_port`-
Vertrag fuer Geraete-Fault-Streams),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-
ADR-Pattern; diese ADR erweitert `ADR 0002 §A-1`-Komponenten-
Liste um `GG-AR-COMP-DEVICES::DeviceModel`),
M2-Slice-Plan
[`in-progress/M2-devices.md`](../planning/in-progress/M2-devices.md)
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

Begruendung:

- Geraete sind fachliche Modelle, die der TickLoop konsumiert
  (`TickLoop.tick()` ruft `device.tick(context)` auf). Ein
  Driving-Port ist per Definition ein Vertrag, ueber den die
  Aussenwelt den Core treibt — Devices treiben den Core nicht.
- `AC-PORTS-NO-OUT` (`ADR 0002 §A-1`) verbietet `hexagon.ports.*`
  Importe in `hexagon.core.simulation`/`devices`/`scenario`/etc.
  `DeviceModel` braucht aber `ScenarioDevice` aus
  `hexagon/core/domain/scenario.py` als Argument-Typ. Ein Port-
  Placement wuerde diesen Import-Pfad blockieren (Ports duerfen
  nur `core.domain.*` importieren, nicht im erweiterten
  Domain-Umfeld).
- `AC-HEXAGON-PURE` erlaubt `hexagon/core/devices/*` den Import
  von `hexagon.ports.driven.*` (Core darf Ports konsumieren).
  Damit kann `_protocol.py` `RandomPort` als Argument-Typ
  referenzieren, ohne den AC-Vertrag zu brechen.

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

### 2.4 Snapshot-Vertrag fuer Geraete

`DeviceModel.snapshot()` MUSS ein `Mapping[str, object]` mit
`version: int` als Erst-Feld liefern (M1 Welle 1 / M2 Welle 0a
Trigger 014 Konvention). `SnapshotEnvelope.__post_init__` prueft
das beim Composition-Aufruf — Geraete-Implementationen brauchen
die Pflicht nicht selbst zu duplizieren.

Zusaetzlich MUSS jede Implementation eine Classmethod
`from_snapshot(state: Mapping[str, object]) -> Self` anbieten
(nicht Teil des Protocols, weil Classmethods im
`typing.Protocol`-Vertrag unhandlich sind). Tests pruefen
`from_snapshot(snapshot()) == device` byte-stabil je Geraet
(Welle-1-Konvention fuer Welle 2..5; siehe Slice-Plan §3 Welle 1).

---

## 3. Begruendung

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

Mit Acceptance dieser ADR liegen folgende Module:

- `src/grid_gym/hexagon/core/devices/__init__.py` —
  Re-Export von `DeviceModel` als Top-Level-Symbol des Pakets.
- `src/grid_gym/hexagon/core/devices/_protocol.py` —
  `DeviceModel` Protocol mit den fuenf Pflicht-Methoden
  (`initialize`/`apply_command`/`tick`/`snapshot`/`telemetry`).
- `src/grid_gym/hexagon/core/domain/device.py` —
  `DeviceTickContext`/`DeviceTickOutcome` Frozen-Dataclasses,
  port-frei.
- `tests/unit/hexagon/core/devices/_fakes.py` — `NullDevice`-
  Test-Double, der das Protocol satisfies (wird in Welle 2..5
  als Baseline fuer per-Device-Adherence-Tests wiederverwendet).
- `tests/unit/hexagon/core/devices/test_protocol_contract.py` —
  Protocol-Adherence-Test: `isinstance(NullDevice(), DeviceModel)`,
  Methoden-Surface-Check, `snapshot()`-`version`-Erstfeld-Pruefung.

Der gemeinsame `from_snapshot`-Classmethod-Vertrag wird in jedem
konkreten Geraete-Modul mitgeliefert (Welle 2..5).

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
  Out-of-Scope-Eintrag im Slice-Plan §4).

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
