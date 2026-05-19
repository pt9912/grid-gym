# ADR 0021 — Scenario-Loader-Device-Factory + TickLoop-Event-Wiring + GridConnection-Auto-Schluss (M2 Welle 6b)

**Status:** Proposed
**Datum:** 2026-05-19
**Bezug:**
[`ADR 0013`](0013-device-model-protocol.md) (DeviceModel-Protocol —
Factory-Dispatch nach `ScenarioDevice.type` erzeugt
Protocol-konforme Instanzen),
[`ADR 0014`](0014-battery-snapshot-schema.md),
[`ADR 0016`](0016-pv-load-device-pattern.md),
[`ADR 0017`](0017-grid-connection-device-pattern.md) §2.2
(GridConnection-Sign-Konvention; ADR 0021 §2.6
Auto-Schluss-Mechanik fixiert),
[`ADR 0018`](0018-smart-meter-device-pattern.md) §2.3
(SmartMeter-`attach_sources`-Hook — Welle 6b Loader haengt die
Quellen-Devices an),
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.2 + §6
(Imbalance-Formel + Welle-6-Auto-Schluss-Begruendung — Welle 6b
implementiert den vor-Grid-Residual-Pfad),
[`ADR 0020`](0020-load-profile-and-event-pattern.md) §2.2 + §2.3
(LoadEvent / LoadProfile-Konsum-Verträge — Welle 6b verdrahtet
die TickLoop-Konsum-Seite),
[`ADR 0015`](0015-snapshot-envelope-v2.md) §4
(TickLoop-from_snapshot rekonstruiert in Welle 6a Devices/
grid_model NICHT — Welle 6b-Scenario-Loader wird das Pre-
Konstruktor-Injekt-Pattern bestaetigen),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-
ADR-Pattern — Welle 6b erweitert ADR 0013/0017/0018/0019/0020
ohne Supersedes).
M2-Slice-Plan
[`in-progress/M2-devices.md`](../planning/in-progress/M2-devices.md)
§3 Welle 6b. Lastenheft §3 (`GG-MVP-002`),
`GG-SCN-001` (Scenario-Loader-Verantwortung).

---

## 1. Kontext

Welle 6a hat den `TickLoop` so erweitert, dass er **vorkonstruierte**
`DeviceModel`-Instanzen + ein optionales `GridModelBilanz` ueber
den Konstruktor entgegennimmt und in jedem `tick()`-Aufruf
durchiteriert. Aufrufer-Pflicht: alle Geraete vor dem ersten
Tick-Aufruf instantiieren, initialisieren, mit `set_run_id` /
`attach_random` / (SmartMeter:) `attach_sources` verdrahten.

Welle 6b liefert genau diese Aufrufer-Verantwortung als **produktiven
Scenario-Loader** unter `hexagon/core/scenario/loader.py`:

- **Device-Factory-Dispatch** nach `ScenarioDevice.type` →
  konkrete `DeviceModel`-Implementation (`BatteryDevice`,
  `PvDevice`, `LoadDevice`, `GridConnectionDevice`,
  `SmartMeterDevice`).
- **LoadEvent / LoadProfile-Parsing** aus Scenario-YAML-Sektionen
  `events:` und `load_profiles:` (`GG-GRID-003` / `004`).
- **GridConnection-Auto-Schluss-Mechanik**: in jedem Tick, der
  keine manuelle `set_power_kw`-Anweisung an die GridConnection
  hat, wird `grid_connection.power_kw :=
  -pre_grid_residual_kw` automatisch gesetzt (ADR 0019 §6).
- **LoadEvent/Profile-Wiring im TickLoop**: pro Tick werden
  aktive Events/Profiles in `LoadDevice.apply_command(
  set_power_kw, value=...)` uebersetzt; nach Event-Ablauf
  Restore auf `LoadConfig.rated_power_kw` (ADR 0020 §2.2).

Welle-6b-Minimum laesst die Scenario-YAML-Format-Erweiterung
schmal: keine OTEL-Hooks, kein Multi-Run-Scheduler, keine
Plugin-Registry — alles M3-Material. M2-Welle-6b liefert nur
das, was `GG-MVP-002` (End-to-End-Szenario) braucht.

---

## 2. Entscheidung

### 2.1 Modul-Struktur

Welle 6b ergaenzt das bestehende `hexagon/core/scenario/loader.py`-
Modul um eine Factory-Funktion und einen TickLoop-Builder, ohne
ein neues Top-Level-Modul anzulegen:

```
hexagon/core/scenario/
    loader.py            # Welle 1: ScenarioDevice-Daten-Parsing
                         # Welle 6b: + build_devices(...) Factory
                         #            + build_tick_loop(...) Builder
                         #            + parse_load_events(...)
                         #            + parse_load_profiles(...)
```

Welle-6b-Implementation traegt sich auch eine neue Helfer-Klasse
im TickLoop ein:

```
hexagon/core/simulation/tick_loop.py
    TickLoop._apply_load_event(event, device)
    TickLoop._apply_load_profile(profile, device, tick_index)
    TickLoop._auto_close_grid_connection(devices)
```

Diese Helfer leben **innerhalb** des `TickLoop`-Bereichs (private
Methoden), weil sie auf interne Felder (`self._devices`,
`self._active_load_events`, etc.) zugreifen — der Scenario-Loader
liefert die Daten, der TickLoop konsumiert sie.

### 2.2 Device-Factory-Dispatch

`build_devices(scenario_devices, random_root)` ist die
Factory-Funktion in `loader.py`. Sie nimmt ein Tupel von
`ScenarioDevice`-Daten + einen `RandomPort.sub_port`-Producer
entgegen und liefert ein **Tupel von initialisierten
`DeviceModel`-Instanzen** in Scenario-Definitionsreihenfolge.

```python
def build_devices(
    scenario_devices: tuple[ScenarioDevice, ...],
    random_root: RandomPort,
) -> tuple[DeviceModel, ...]: ...
```

**Dispatch-Pattern** (Welle-6b-Hartzweig analog
`_DEVICE_TYPE_BY_CLASS_NAME` in TickLoop):

```python
_DEVICE_FACTORIES: Final[Mapping[str, Callable[[], DeviceModel]]] = {
    "battery": BatteryDevice,
    "pv": PvDevice,
    "load": LoadDevice,
    "grid_connection": GridConnectionDevice,
    "smart_meter": SmartMeterDevice,
}
```

Pro `ScenarioDevice`:

1. Factory aus dem Mapping holen (`scenario_device.type` →
   `factory()`). Unknown Type → `ScenarioUnknownDeviceTypeError`
   (neue Exception-Klasse).
2. `device = factory()`.
3. `random_sub = random_root.sub_port(scenario_device.id)`
   (ADR 0007 §5).
4. `device.initialize(scenario_device, random_sub)`.

**SmartMeter-Sonderbehandlung:** SmartMeter braucht zusaetzlich
einen `attach_sources(sources_by_id)`-Aufruf (ADR 0018 §2.3),
**bevor** der erste `tick()` laeuft. Welle-6b-Konvention:

- Scenario-Loader konstruiert zuerst **alle** Devices in Reihenfolge.
- Anschliessend iteriert der Loader nochmal ueber die Liste und
  ruft `attach_sources(sources_by_id)` fuer jede `SmartMeterDevice`-
  Instanz mit einem Mapping aller bekannten Devices nach
  `device_id`.
- `aggregate_device_ids` aus `SmartMeterConfig` muss vollstaendig
  im Mapping vorhanden sein; sonst `ScenarioMissingSourceDeviceError`
  (Welle-6b-spezifisch, vor dem ersten Tick — verhindert
  Welle-4b-`SmartMeterSourceMissingError` zur Laufzeit).

### 2.3 `build_tick_loop(...)`-Builder

```python
def build_tick_loop(
    scenario: Scenario,
    *,
    clock: ClockPort,
    random_root: RandomPort,
) -> TickLoop: ...
```

Der Builder liefert eine produktive `TickLoop`-Instanz:

1. `devices = build_devices(scenario.devices, random_root)`.
2. `grid_model = build_grid_model(scenario.grid_model_config)`
   (kann `None` sein, wenn das Scenario kein Bilanz-Modell
   deklariert — Welle-6b-Default ist ein
   `GridModelBilanz`-Standard-Setup).
3. `scheduler = Scheduler.from_scenario_events(scenario.events)`.
4. `load_events = parse_load_events(scenario.load_events)`.
5. `load_profiles = parse_load_profiles(scenario.load_profiles)`.
6. `loop = TickLoop(run_id, tick_ms, clock, random_root,
   scheduler, devices=devices, grid_model=grid_model)`.
7. Loop intern: `loop._active_load_events = load_events`,
   `loop._active_load_profiles = load_profiles` (Welle-6b-
   Erweiterung). Hint: TickLoop-Konstruktor bekommt zwei neue
   kwargs `active_load_events=()`, `active_load_profiles=()`.

**Welle-6b-Builder-Verantwortung NUR fuer Scenario-Daten:**
Welle-6b liefert KEIN Postgres-Persistierungs-Pfad und kein
End-to-End-Demo-Szenario — das ist Welle 6c.

### 2.4 LoadEvent-Wiring im TickLoop

`TickLoop.tick()` (Welle-6b-Erweiterung) bekommt vor der
Device-Iteration einen neuen Vor-Tick-Block:

```
fuer jeden LoadEvent in self._active_load_events:
    falls event_active(event, simulation_time):
        device = self._device_by_id[event.target_device_id]
        device.apply_command(Command(
            type="set_power_kw",
            payload={"value": event.power_kw},
        ))
    elif event_just_expired(event, simulation_time):
        device.apply_command(Command(
            type="set_power_kw",
            payload={"value": device._config.rated_power_kw},
        ))
```

mit:

- `event_active(event, sim_time) := event.start_s <= sim_time <
   event.start_s + event.duration_s`.
- `event_just_expired(event, sim_time) := sim_time ==
   event.start_s + event.duration_s` (einmaliger Restore-Trigger;
   weitere Ticks lassen den `rated_power_kw`-Wert bestehen).

**TickLoop fuehrt ein `_device_by_id`-Mapping**, das aus dem
Konstruktor automatisch aus `self._devices` aufgebaut wird
(O(N)-Setup, O(1)-Lookup pro Event).

### 2.5 LoadProfile-Wiring im TickLoop

Analog zu Event-Wiring, aber mit Tick-Index statt
Sim-Zeit-Intervall:

```
fuer jedes LoadProfile in self._active_load_profiles:
    profile_index = (self._tick_count * self._tick_ms) // profile.tick_ms
    tick_values = profile.tick_values
    if profile_index < len(tick_values):
        value = tick_values[profile_index]
    else:
        value = tick_values[-1]   # Repeat-Last-Value (ADR 0020 §2.3)
    device = self._device_by_id[profile.target_device_id]
    device.apply_command(Command(
        type="set_power_kw",
        payload={"value": value},
    ))
```

**Welle-6b-Profil-Index-Konvention:** ADR 0020 §2.3 fixiert
`(context.tick * context.tick_ms) // profile.tick_ms`. In
TickLoop-Implementation ist `context.tick = self._tick_count`
**vor** dem `tick()`-Body-Ablauf — der Loop laeuft fuer das
erste `tick()` mit `tick_count = 0`, sodass `tick_values[0]`
waehrend des ersten Tick-Intervalls aktiv ist. Off-by-one-frei
gegen Welle-4-Clock-Konvention (TickLoop advanced die Clock
vor dem Tick-Body, aber `tick_count` zaehlt nach Tick-Body).

### 2.6 Event-vs-Profile-Konflikt-Resolution

Mehrere Quellen koennen gleichzeitig `set_power_kw` an dasselbe
Device richten. Welle-6b-Konvention (Pflicht-Reihenfolge im
Tick):

1. **LoadProfile** zuerst — setzt einen Baseline-Wert pro Tick.
2. **LoadEvent** danach — ueberschreibt den Profile-Wert
   wenn ein Event in diesem Tick aktiv ist (Event hat hoehere
   Prioritaet, weil es eine bewusst-zeitliche-Anweisung ist).
3. **Manuelle Scenario-Events** (`Scenario.events` aus M1-
   Scheduler) sind seit M1 vor dem Tick-Body verarbeitet —
   sie ueberschreiben LoadProfile, werden aber von LoadEvent
   ueberschrieben (wenn beides im selben Tick aktiv ist).

**Reihenfolge in TickLoop._consume_load_inputs():**

```
for profile in self._active_load_profiles:
    apply_profile_value(profile, ...)
for event in self._active_load_events:
    if event_active_or_just_expired(event, sim_time):
        apply_event_value_or_restore(event, ...)
```

Damit ist die Resolution deterministisch und unabhaengig von
der Iteration-Reihenfolge der Devices selbst.

### 2.7 GridConnection-Auto-Schluss

Pro Tick (Welle-6b-Erweiterung in `TickLoop.tick()`, **nach** der
Device-Iteration aber **vor** der Bilanz-Aggregation):

1. Sammle alle `GridConnectionDevice`-Instanzen aus
   `self._devices`.
2. Pruefe pro GridConnection, ob ihre `current_power_kw`
   bereits **manuell** gesetzt wurde:
   - **Manuell** = Welle 6b liefert ein einfaches Heuristik:
     wenn fuer diese Device-ID in diesem Tick ein
     `LoadEvent` aktiv ist ODER ein `LoadProfile`-Wert
     angewendet wurde ODER ein M1-Scheduler-Event mit
     `target = grid_connection.device_id` und
     `type = "set_power_kw"` aufgetaucht ist, gilt der
     Wert als manuell.
   - **Sonst** automatisch: berechne
     `pre_grid_residual = sum(pv) - sum(load) - sum(battery)`
     und setze `grid_connection.power_kw :=
     -pre_grid_residual` via `apply_command(set_power_kw,
     ...)`.
3. **Cap-Limit-Respekt:** ADR 0017 §2.4 enforced Caps. Wenn
   Auto-Schluss den Cap sprengt, wird der Wert clamped und
   der Restposten geht in die `imbalance_kw`-Berechnung
   (Frequenz/Spannungs-Drift).

**Welle-6b-Implementation-Hinweis:** der Auto-Schluss ist
**konservativ** — wenn die manuelle-Heuristik schwer zu
entscheiden ist (z. B. Scenario-Event und Auto-Schluss
gleichzeitig im selben Tick), gewinnt die manuelle-Quelle
(Reihenfolge: Profile → Event → Auto-Schluss). Welle-7+/M3
kann den Auto-Schluss um eine explizite
`Scenario.auto_close_grid_connection: bool`-Konfiguration
ergaenzen.

### 2.8 Tick-Reihenfolge (Vollstaendige Welle-6b-Sequenz)

Pro `TickLoop.tick()`:

1. `clock.advance(tick_ms)` (M1).
2. Scheduler-Events poppen (M1).
3. **Vor-Tick-Block** (Welle 6b):
   a. LoadProfile-Werte an LoadDevices anwenden (Profile-
      Baseline).
   b. LoadEvent-Werte an LoadDevices anwenden / Restore bei
      Ablauf (Event-Overlay).
   c. GridConnection-Auto-Schluss-Werte berechnen und
      anwenden, sofern manuelle Heuristik leer.
4. Device-Iteration: `device.tick(context)` fuer alle Devices
   (Welle 6a).
5. Bilanz-Aggregation: aggregiere `power_kw`-Telemetry,
   `grid_model.update(...)` (Welle 6a, jetzt mit
   GridConnection-Auto-Schluss-Werten gespeist).
6. `TickResult.emitted_telemetry` zusammenstellen.
7. `_tick_count += 1`.

### 2.9 Determinismus

Welle-6b-Pflicht-Property:

- Gleicher `Scenario` (inkl. Events + Profiles) + identische
  TickLoop-Konfiguration (clock, random, scheduler) →
  byte-identische `TickResult.emitted_telemetry`-Sequenz ueber
  ≥ 100 Ticks.
- Auto-Schluss-Pfad ist deterministisch (haengt nur an
  Device-States, die wiederum deterministisch sind).
- LoadEvent/Profile-Anwendung ist deterministisch
  (`_active_load_events` ist `tuple`, Iteration in
  Konstruktor-Reihenfolge).

---

## 3. Begruendung

**Scenario-Loader als einzige Aufrufer-Pflicht-Schicht:** Welle
6a hat den TickLoop bewusst Aufrufer-toleranter gehalten
(devices/grid_model als optional kwargs). Welle 6b liefert die
**produktive** Aufrufer-Verantwortung im `build_tick_loop(...)`-
Builder. Test-Setups duerfen weiterhin direkt mit `TickLoop(...)`
arbeiten; der Scenario-YAML-Pfad geht ueber den Builder.

**Hartzweig-Factory statt Plugin-Registry:** Welle-6b-Minimum
laesst die Factory-Map als Code-Konstante. Plugin-Registry-Pattern
(Loading externer DeviceModel-Klassen via Entry-Points) ist
M5/M6-Material — nur sinnvoll, wenn dritter Code DeviceModel-
Klassen liefert.

**Profile vor Event in der Resolution:** semantisch ist ein
Profile ein **Baseline-Verlauf**, ein Event eine **Stoerung
darueber**. Profile setzt den Default-Wert pro Tick, Event
ueberschreibt fuer seine Dauer. Diese Reihenfolge ist konsistent
mit dem Lastenheft GG-GRID-003 (Zeitreihen = Profile, Events =
Spruenge) und macht die Welle-6c-MVP-Demo-Szenario-Aufschriebe
intuitiv.

**Auto-Schluss heuristisch statt explizit konfigurierbar:**
Welle-6b-Minimum verlaesst sich auf eine einfache
„manuelle-Quelle"-Heuristik (Profile + Event + Scenario-Event
fuer die GridConnection). M3 kann das verfeinern oder durch
eine explizite Scenario-Config-Option ersetzen. Welle 6b liefert
nur den MVP-Pfad.

**Determinismus ueber Tupel-Iteration:** alle Listen
(`_active_load_events`, `_active_load_profiles`, `_devices`)
sind unveraenderliche `tuple`-Instanzen ueber den Konstruktor.
Iteration ist immer in Konstruktor-Reihenfolge, kein Hash-
basiertes Set-Verhalten — Determinismus per Bauplan.

---

## 4. Reichweite

Diese ADR gilt fuer:

- `hexagon/core/scenario/loader.py`: `build_devices`,
  `build_tick_loop`, `parse_load_events`, `parse_load_profiles`.
- `hexagon/core/scenario/`-Erweiterungen fuer Scenario-YAML-
  Format (`events:` / `load_profiles:`-Sektionen).
- `hexagon/core/simulation/tick_loop.py`:
  `_active_load_events`-/`_active_load_profiles`-Felder,
  `_device_by_id`-Lookup, Vor-Tick-Block fuer Event/Profile-
  Anwendung + Auto-Schluss.
- `hexagon/core/errors.py`:
  `ScenarioUnknownDeviceTypeError`,
  `ScenarioMissingSourceDeviceError`.
- `tests/unit/hexagon/core/scenario/test_loader_welle_6b.py`
  (neu).
- `tests/unit/hexagon/core/simulation/test_tick_loop_welle_6b.py`
  (neu).

Diese ADR gilt NICHT fuer:

- MVP-Demo-Szenario (`mvp_demo.yaml`) — Welle 6c.
- E2E-Integration-Tests mit Postgres-Roundtrip — Welle 6c.
- Plugin-Registry fuer externe DeviceModel-Klassen — M5/M6.
- Multi-Run-Scheduler, parallele Szenarien — M3/Post-MVP.
- Komplexe Auto-Schluss-Konfigurations-Optionen — M3.

---

## 5. Operative Artefakte

Mit Acceptance dieser ADR (synchron mit M2-Welle-6b-PR-Merge)
liegen folgende Module:

- `hexagon/core/scenario/loader.py` erweitert um die vier
  Welle-6b-Funktionen.
- `hexagon/core/simulation/tick_loop.py` traegt
  `_active_load_events`/`_active_load_profiles`,
  `_device_by_id`-Lookup und Vor-Tick-Block.
- `hexagon/core/errors.py` traegt
  `ScenarioUnknownDeviceTypeError` und
  `ScenarioMissingSourceDeviceError`.
- `tests/unit/hexagon/core/scenario/test_loader_welle_6b.py`
  fuer Factory-Dispatch + Parser.
- `tests/unit/hexagon/core/simulation/test_tick_loop_welle_6b.py`
  fuer Event/Profile-Wiring + Auto-Schluss + Reihenfolge.

Volle Test-Anzahl-Inkrement gegen Welle 6a wird in der Welle-6b-
Closure-Notiz verzeichnet (Erwartung: ~30..50 neue Tests).

---

## 6. Konsequenzen

**Was sich aendert:**

- Scenario-YAML kann ab Welle 6b `events:`- und
  `load_profiles:`-Sektionen tragen.
- Welle 6b's `build_tick_loop(scenario, clock=..., random_root=...)`
  ist der produktive Pfad zur TickLoop-Konstruktion.
- TickLoop konsumiert pro Tick LoadEvents/Profiles und macht
  GridConnection-Auto-Schluss.
- ADR-0019-§2.2-Imbalance-Formel wird durch den Auto-Schluss
  in der MVP-Demo per Konstruktion 0.

**Was load-bearing bleibt:**

- ADR 0013 DeviceModel-Protocol (unveraendert).
- ADR 0014/0016/0017/0018 (Geraete-Sub-Snapshot-Schemas).
- ADR 0019/0020 (grid_model + LoadEvent/LoadProfile-Datenstrukturen).
- ADR 0015 (TickLoop-Snapshot v2).

**Was offen bleibt (Welle 6c+):**

- MVP-Demo-Szenario.
- E2E-Tests + Postgres-Roundtrip.
- Plugin-Registry, Multi-Run, OTEL — M3+.
- Welle-6a-`_DEVICE_TYPE_BY_CLASS_NAME` und Welle-6b-
  `_DEVICE_FACTORIES` muessen synchron gepflegt werden (eine
  Folge-Welle koennte sie ueber eine `device_type`-Protocol-
  Property zusammenfuehren — ADR 0015 §4 Forward-Pointer).

---

## 7. Nicht Gegenstand dieser ADR

- **MVP-Demo-Szenario** (`mvp_demo.yaml`). Welle 6c.
- **Postgres-Persistierung des Builder-Outputs**. Welle 6c +
  M3.
- **Plugin-Registry fuer DeviceModel-Klassen**. M5/M6.
- **Multi-Run-Scheduler**. Welle 6b-Builder konstruiert genau
  einen `TickLoop`; parallele Szenarien sind M3+.
- **`device_type`-Protocol-Property** (Welle-6a-Review-H-1-
  Forward-Pointer). Welle 7+/M3.
- **Komplexe Auto-Schluss-Konfiguration** (Scenario-Config-
  Opt-In statt Heuristik). M3.
- **OTEL-Hooks im Scenario-Loader**. M3.
- **YAML-Schema-Validierung** ueber Welle-6b-Minimum hinaus
  (z. B. JSONSchema-Externalisierung). Welle 6c oder M3.
