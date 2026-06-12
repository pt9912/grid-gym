# ADR 0021 — Scenario-Loader-Device-Factory + TickLoop-Event-Wiring + GridConnection-Auto-Schluss (M2 Welle 6b)

**Status:** Accepted — Welle-6c-Closure (`c31052c`) liefert das
End-to-End-MVP-Demo-Szenario inkl. zweier Integrationstests
(Determinismus + Postgres-Roundtrip) und exerziert
`build_devices(...)` + `build_tick_loop(...)` + den Vor-Tick-
Block (LoadProfile/LoadEvent/Auto-Schluss) produktiv ueber
≥ 100 Ticks; ScenarioDevice-Permutations-Property-Test
(`test_scenario_permutation.py`) pinnt die Determinismus-
Pflicht (§2.2/§2.9). `make fullbuild` gruen ohne Override.
**Datum:** 2026-05-19
**Status geaendert am:** 2026-05-19 — `Proposed → Provisional`
(Welle-6b-Merge `0f1c597`); 2026-05-20 —
`Provisional → Accepted` (Welle-6c-Closure `c31052c`).
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
[`done/M2-devices.md`](../planning/done/M2-devices.md)
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

Welle-6b-Implementation ergaenzt **private Methoden** auf der
bestehenden `TickLoop`-Klasse (keine neue Klasse — Welle-6a-
Review-M-6-Spiegel: Schreib-Pfad-Helfer leben innerhalb des
Orchestrator-Bereichs):

```
hexagon/core/simulation/tick_loop.py (Welle 6b)
    TickLoop._consume_load_profile(profile, lookup)
    TickLoop._consume_load_event(event, lookup, sim_time)
    TickLoop._apply_grid_connection_auto_close(...)
    TickLoop._build_device_by_id()
```

Diese Methoden greifen auf interne Felder
(`self._devices`, `self._active_load_events`, etc.) zu — der
Scenario-Loader liefert die Daten, der TickLoop konsumiert sie.

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

### 2.3 `Scenario`-Domain-Erweiterung (Welle-6b-Round-1-High-1)

Welle 6b braucht drei neue Top-Level-Felder im `Scenario`-
Frozen-Dataclass-Datentyp, die mit M1 noch nicht existierten:

- `grid_model_config: GridModelConfig | None` — optionale
  GridModelBilanz-Konfiguration aus dem Scenario-YAML
  (`grid_model:`-Sektion). Wenn `None`, baut der Loader einen
  `GridModelBilanz`-Standard-Setup oder laesst die Bilanz weg.
- `load_events: tuple[LoadEvent, ...]` — Scenario-Lastspruenge
  (`GG-GRID-004`); leeres Tupel wenn keine Events.
- `load_profiles: tuple[LoadProfile, ...]` — Scenario-Last-
  Profile (`GG-GRID-003` „Zeitreihen"); leeres Tupel wenn
  keine Profile.

**Welle-6b-Scope-Pflicht** (Round-1-High-1):

- `hexagon/core/scenario/scenario.py` (oder gleichwertiger
  Domain-Pfad) erweitert um die drei Felder.
- `hexagon/core/scenario/validator.py` (oder gleichwertig)
  validiert die neuen Felder typisiert (canonical-kompatibel).
- `Scenario`-canonical-Hash bleibt deterministisch (alle drei
  Felder sind immutable Dataclasses bzw. Tupel).

**Bezug zu `Scenario.events`:** das bestehende
`events: tuple[ScenarioEvent, ...]`-Feld traegt M1-Scheduler-
Events fuer den `Scheduler`. Welle 6b laesst es unveraendert —
LoadEvents sind **eine separate Konzern-Kategorie** (sie
beziehen sich nicht auf den Scheduler, sondern direkt auf
LoadDevice-Power-Werte). Keine Vermischung.

**ScenarioEvent → Command-Bridge** (Welle-6b-Round-1-High-3):
Der aktuelle TickLoop popped M1-Scheduler-Events nur und gibt
sie in `TickResult.popped_events` zurueck. Es gibt
**keinen** apply_command-Pfad fuer M1-Scheduler-Events. Welle
6b setzt diese Vorraussetzung nicht voraus — die manuelle
Heuristik in §2.7 bezieht sich **ausschliesslich** auf
LoadEvent/LoadProfile (Welle-5b-Datenstrukturen), nicht auf
M1-Scheduler-Events. Ein ScenarioEvent→Command-Bridge ist
explizit out-of-scope und bleibt Welle 6c / M3-Material.

### 2.4 `build_tick_loop(...)`-Builder

```python
def build_tick_loop(
    scenario: Scenario,
    *,
    clock: ClockPort,
    random_root: RandomPort,
) -> TickLoop: ...
```

**Welle-2-Items-7-10-Review N-1 — M3-Welle-1-Erweiterung:**
ADR 0022 §2.5 ergaenzt die Builder-Signatur um einen
keyword-only `fault_port: FaultPort | None = None`-Parameter.
Default bleibt `None`, also brechen bestehende Aufrufe nicht;
der Wert wird nur durchgereicht und nicht weiter verarbeitet.
Symmetrisch zum gleichnamigen TickLoop-Konstruktor-Parameter
(ADR 0022 §2.5):

```python
def build_tick_loop(
    scenario: Scenario,
    *,
    clock: ClockPort,
    random_root: RandomPort,
    fault_port: FaultPort | None = None,  # M3-Welle-1, ADR 0022
) -> TickLoop: ...
```

Der Builder liefert eine produktive `TickLoop`-Instanz aus den
**Welle-6b-erweiterten** Scenario-Feldern:

1. `devices = build_devices(scenario.devices, random_root)`.
2. `grid_model = (GridModelBilanz(scenario.grid_model_config)
   if scenario.grid_model_config is not None else None)`.
3. `scheduler = Scheduler()` neu initialisiert; pro
   `scenario_event` in `scenario.events` wird ein
   `scheduler.add(event)` durchgereicht (M1-Surface,
   unveraendert — Welle 6b legt **keinen** neuen
   `Scheduler.from_scenario_events`-Builder an, weil das
   eine M1-Schaerfung waere, die nicht in Welle 6b gehoert).
4. `loop = TickLoop(run_id, tick_ms, clock, random_root,
   scheduler, devices=devices, grid_model=grid_model,
   active_load_events=scenario.load_events,
   active_load_profiles=scenario.load_profiles)`.

**TickLoop-Konstruktor-Erweiterung (Welle 6b):** Welle 6a
hatte bereits `devices=()` und `grid_model=None`. Welle 6b
ergaenzt `active_load_events: tuple[LoadEvent, ...] = ()` und
`active_load_profiles: tuple[LoadProfile, ...] = ()`.
Welle-6a-Tests bleiben durch die `()`-Defaults kompatibel.

**Welle-6b-Builder-Verantwortung NUR fuer Scenario-Daten:**
Welle-6b liefert KEIN Postgres-Persistierungs-Pfad und kein
End-to-End-Demo-Szenario — das ist Welle 6c.

### 2.5 LoadEvent/LoadProfile-Wiring (Jedes-Tick-Baseline)

**Welle-6b-Round-1-Medium-1-Schaerfung:** statt eines
einmaligen `event_just_expired`-Triggers (der bei nicht-
tick-aligned Endzeiten und Resume scheitern wuerde), nutzt
Welle 6b ein **Jedes-Tick-Baseline + Override**-Pattern. Pro
Tick und pro LoadDevice berechnet TickLoop einen
`intent_power_kw`-Wert, den es per
`apply_command(set_power_kw, value=intent_power_kw)` anwendet:

```
intent_power_kw_by_load_id: dict[str, Decimal] = {
    load_device.device_id: load_device.rated_power_kw
    for load_device in self._load_devices_by_id.values()
}

# Schritt 1 — LoadProfile (Baseline-Overlay).
for profile in self._active_load_profiles:
    profile_index = (self._tick_count * self._tick_ms) // profile.tick_ms
    tick_values = profile.tick_values
    value = tick_values[min(profile_index, len(tick_values) - 1)]
    intent_power_kw_by_load_id[profile.target_device_id] = value

# Schritt 2 — LoadEvent (Event-Overlay).
for event in self._active_load_events:
    if event.start_s <= sim_time_s < event.start_s + event.duration_s:
        intent_power_kw_by_load_id[event.target_device_id] = event.power_kw

# Schritt 3 — apply_command pro Device.
for device_id, intent in intent_power_kw_by_load_id.items():
    device = self._device_by_id[device_id]
    device.apply_command(Command(
        type="set_power_kw",
        payload={"value": intent},
    ))
```

**Vorteile gegenueber expliziter `event_just_expired`-Logik:**

- Resume nach beliebigem Ablauf-Zeitpunkt funktioniert (kein
  „Restore-already-applied"-Marker noetig).
- Nicht-tick-aligned Event-Endzeiten verhalten sich
  deterministisch (Event ist „aktiv" oder nicht; nach Ablauf
  wirkt der Baseline-Wert automatisch).
- Default-Wert ohne Profile/Event = `LoadDevice.rated_power_kw`
  (siehe §2.6 Public-Property-Vertrag).

**Welle-6b-Profil-Index-Konvention:** ADR 0020 §2.3 fixiert
`(context.tick * context.tick_ms) // profile.tick_ms`. In
TickLoop-Implementation ist `context.tick = self._tick_count`
vor dem Tick-Body-Ablauf — der Loop laeuft fuer das erste
`tick()` mit `tick_count = 0`, sodass `tick_values[0]`
waehrend des ersten Tick-Intervalls aktiv ist. Off-by-one-frei.

**TickLoop fuehrt ein `_device_by_id`-Mapping**, das aus dem
Konstruktor automatisch aus `self._devices` aufgebaut wird
(O(N)-Setup, O(1)-Lookup pro Event/Profile).

### 2.6 Public Restore-Source — `LoadDevice.rated_power_kw`

**Welle-6b-Round-1-Medium-2-Schaerfung:** das
Jedes-Tick-Baseline-Pattern aus §2.5 verlangt, dass die
TickLoop pro `LoadDevice` den `rated_power_kw`-Wert lesen
kann, **ohne** auf das private `device._config.rated_power_kw`-
Feld zuzugreifen (verletzt LoadDevice-Modul-Grenze).

Welle 6b ergaenzt die `LoadDevice`-Surface um eine
**Public-Property**:

```python
class LoadDevice:
    ...
    @property
    def rated_power_kw(self) -> Decimal:
        """Welle-6b-Konvention: Public-Restore-Source fuer das
        TickLoop-Jedes-Tick-Baseline (Welle-6b-Review-Round-1-
        Medium-2)."""
        if self._config is None:
            raise DeviceNotInitializedError("rated_power_kw")
        return self._config.rated_power_kw
```

**Pre-init-Raise:** vor `initialize(...)` wirft die Property
`DeviceNotInitializedError` (Welle-1-/Welle-3-Pattern fuer
Pre-init-Felder).

**Pattern-Spiegel-Pflicht:** Welle 6b haelt das `rated_power_kw`-
Property **nur** auf `LoadDevice`. PV/Battery/GridConnection/
SmartMeter haben kein TickLoop-Restore-Bedarf in Welle 6b
(GridConnection wird ueber Auto-Schluss gesetzt; PV emittiert
ohne Welle-6b-Override; Battery wird ueber Welle-7+-Storage-
Strategien gesteuert).

### 2.7 GridConnection-Auto-Schluss (Split-Iteration)

**Welle-6b-Round-1-High-2-Schaerfung:** der ursprueengliche
Vor-Tick-Block-Ansatz (§2.7 / §2.8) hatte einen Phasen-Konflikt
— vor der Device-Iteration fehlt die aktuelle PV/Load/Battery-
Telemetrie; nach der Iteration wirkt `apply_command(set_power_kw)`
an die GridConnection erst im **naechsten** Tick (weil
`pending_power_kw` gesetzt wird und `current_power_kw` erst
beim naechsten `tick()` aktualisiert).

Loesung: **Split-Iteration** in `TickLoop.tick()`. Die
GridConnection-Iteration wird vom Rest der Devices getrennt:

```
# Schritt A — Vor-Tick-Block: LoadProfile + LoadEvent an Loads.
for load_device in self._load_devices:
    intent = ...   # Jedes-Tick-Baseline-Logik aus §2.5
    load_device.apply_command(set_power_kw, intent)

# Schritt B — Erste Device-Iteration: PV + Load + Battery + SmartMeter
#            (alle Devices AUSSER GridConnection).
non_grid_connection_devices = [d for d in self._devices
                                if not isinstance(d, GridConnectionDevice)]
for device in non_grid_connection_devices:
    outcome = device.tick(context)
    emitted.extend(outcome.telemetry)

# Schritt C — GridConnection-Auto-Schluss:
#            berechne pre_grid_residual aus post-tick-Telemetry der
#            non_grid_connection_devices.
pre_grid_residual = (
    sum(pv.power_kw for pv in pv_devices)
    - sum(load.power_kw for load in load_devices)
    - sum(battery.power_kw for battery in battery_devices)
)
for grid_dev in grid_connection_devices:
    if grid_dev.device_id in manual_override_ids:
        continue   # manuelle-Heuristik: LoadEvent/Profile hat schon set_power_kw gemacht
    grid_dev.apply_command(set_power_kw, value=-pre_grid_residual)

# Schritt D — Zweite Device-Iteration: GridConnection ticken.
for grid_dev in grid_connection_devices:
    outcome = grid_dev.tick(context)
    emitted.extend(outcome.telemetry)

# Schritt E — Bilanz-Aggregation aus allen post-tick-Telemetrien.
```

**Manuelle-Heuristik** (`manual_override_ids`) — Welle-6b-
Konvention:

- Wenn ein LoadEvent oder LoadProfile in diesem Tick die
  Device-ID `grid_connection_id` als `target_device_id` setzt,
  gilt der Wert als manuell ueberlagert. Auto-Schluss wird
  uebersprungen.
- **NICHT** aus M1-Scheduler-Events abgeleitet (Welle-6b-
  Round-1-High-3: ScenarioEvent→Command-Bridge ist out-of-
  scope).

**Cap-Limit-Respekt:** ADR 0017 §2.4 enforced
`max_import_kw`/`max_export_kw`. Wenn Auto-Schluss den Cap
sprengt, wird der Wert clamped (intern in `GridConnectionDevice.
apply_command`); der Restposten geht in die `imbalance_kw`-
Berechnung in Schritt E.

### 2.8 Tick-Reihenfolge (Vollstaendige Welle-6b-Sequenz)

Pro `TickLoop.tick()`:

1. `clock.advance(tick_ms)` (M1).
2. Scheduler-Events poppen (M1).
3. **Vor-Tick-Block — Schritt A** (Welle 6b §2.5):
   - LoadProfile + LoadEvent → `apply_command(set_power_kw)`
     an LoadDevices (Jedes-Tick-Baseline + Profile-Overlay
     + Event-Overlay).
4. **Erste Device-Iteration — Schritt B** (Welle 6b §2.7):
   - `device.tick(context)` fuer alle Devices **ausser**
     `GridConnectionDevice`. Telemetry sammeln.
5. **Auto-Schluss-Berechnung — Schritt C** (Welle 6b §2.7):
   - Pre-Grid-Residual aus PV/Load/Battery-Post-Tick-Telemetry.
   - `apply_command(set_power_kw, -residual)` an
     GridConnection-Devices, sofern manuelle-Heuristik leer.
6. **Zweite Device-Iteration — Schritt D** (Welle 6b §2.7):
   - `grid_connection.tick(context)` fuer alle GridConnection-
     Devices. Telemetry sammeln.
7. **Bilanz-Aggregation — Schritt E** (Welle 6a + 6b):
   - `grid_model.update(...)` mit gesamter Post-Tick-Telemetry.
8. `TickResult.emitted_telemetry` zusammenstellen.
9. `_tick_count += 1`.

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
mit dem Lastenheft [`GG-GRID-003`](../../../spec/lastenheft.md#gg-grid-003) (Zeitreihen = Profile, Events =
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

- `hexagon/core/scenario/scenario.py` (oder gleichwertig)
  erweitert um drei Top-Level-Felder
  (`grid_model_config`, `load_events`, `load_profiles`).
- `hexagon/core/scenario/validator.py` (oder gleichwertig)
  validiert die drei neuen Felder.
- `hexagon/core/scenario/loader.py`: `build_devices`,
  `build_tick_loop`, `parse_load_events`,
  `parse_load_profiles`.
- `hexagon/core/simulation/tick_loop.py`:
  `_active_load_events`-/`_active_load_profiles`-Konstruktor-
  kwargs, `_device_by_id`-Lookup, Vor-Tick-Block fuer
  LoadProfile/LoadEvent (§2.5), Split-Iteration fuer
  GridConnection-Auto-Schluss (§2.7).
- `hexagon/core/devices/load/model.py`:
  Public-`rated_power_kw`-Property auf `LoadDevice` (§2.6).
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

- **ScenarioEvent→Command-Bridge** (Welle-6b-Round-1-High-3):
  M1-Scheduler-Events werden weiterhin nur in
  `TickResult.popped_events` zurueckgegeben; eine Uebersetzung
  in `Command.apply_command(set_power_kw, ...)` fuer
  Scheduler-Events (z. B. „setze pv-1 auf 200 kW bei t=10s")
  ist Welle 6c oder M3. Welle 6b's manuelle-Heuristik
  bezieht sich **ausschliesslich** auf LoadEvent/LoadProfile.
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
