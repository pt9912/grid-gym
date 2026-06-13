# ADR 0050 — AC-ADAPTER-PURE Bridge-Rueckbau fuer HTTP-Demo-Wiring

**Status:** Accepted
**Datum:** 2026-06-09
**Bezug:**

- [`ADR 0002`](0002-language-and-build-stack.md) — A-1-
  Architekturtests, besonders `AC-ADAPTER-PURE` und
  `AC-PORTS-NO-OUT`.
- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — ADR-Lifecycle.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung
  ohne Supersedes.
- [`ADR 0022`](0022-fault-injection-protocol.md) und
  [`ADR 0025`](0025-fault-recovery-pattern.md) — FaultPort- und
  Fault-Adapter-Vertraege.
- [`ADR 0039`](0039-run-control-and-status-tracking.md) —
  Run-Control, `control_state`, `request(...)` und die historische
  HTTP-Kompositions-Bridge.
- [`ADR 0040`](0040-alarm-aggregation-and-stream-port.md) —
  Stream-Port-Praezedenz fuer Driving-Port-Surfaces.
- [`spec/architecture.md`](../../../spec/architecture.md#2-architekturprinzipien) —
  `GG-AR-P-002`, `GG-AR-P-003`, `GG-AR-TABU-001..004` und
  Driving-Port-Liste.
- [`041-adapter-pure-ignore-imports-rueckbau.md`](../planning/in-progress/041-adapter-pure-ignore-imports-rueckbau.md)
  — Umsetzungsslice (M8-Welle-0/1 aktiv).

---

## 1. Kontext

`AC-ADAPTER-PURE` verbietet `grid_gym.adapters.*`-Imports auf
`hexagon.core.simulation`, `hexagon.core.devices`,
`hexagon.core.scenario`, `hexagon.core.replay`, `hexagon.core.faults`
und `hexagon.core.agents`. Der aktuelle `pyproject.toml` enthaelt
acht `ignore_imports`-Eintraege fuer den HTTP-Demo-/Run-Pfad:

- `_demo_setup -> hexagon.core.simulation.{tick_loop,scheduler}`
- `_tick_loop_registry -> hexagon.core.simulation.tick_loop`
- `_tick_loop_driver -> hexagon.core.simulation.tick_loop`
- `_tick_loop_healthcheck -> hexagon.core.simulation.tick_loop`
- `_demo_scenario_setup -> hexagon.core.scenario.loader`
- `_demo_scenario_setup -> hexagon.core.faults`
- `_runs_action_router -> hexagon.core.faults.types`

Die Ausnahmen sind historisch begruendet: ADR 0039 hat fuer den
Welle-4a-Demo-Lauf bewusst eine kleine Kompositions-Bridge erlaubt,
und spaetere Wellen haben Scenario-Loader-, Healthcheck- und
Fault-Wiring auf derselben Stelle erweitert. Inzwischen ist daraus
aber eine dauerhafte Adapter->Core-Abhaengigkeit geworden.

Gleichzeitig nennt `spec/architecture.md` bereits Driving-Port-
Verantwortungen wie `RunControlPort`, `ScenarioPort`,
`FaultInjectionPort`, `SnapshotPort`, `TelemetryQueryPort` und
`HealthPort`. Im Code existieren davon heute nur einzelne Stream-
Ports; der HTTP-Adapter greift fuer Run-Ausfuehrung und Demo-
Bootstrap direkt auf konkrete Core-Klassen zu.

## 2. Entscheidung

ADR 0050 fixiert den Rueckbau der `AC-ADAPTER-PURE`-Bruecken als
additive Schaerfung. Ziel ist nicht, `AC-ADAPTER-PURE` zu lockern,
sondern die Ausnahmen durch echte Port- und Kompositionsgrenzen zu
ersetzen.

### 2.1 Keine neuen `AC-ADAPTER-PURE`-Ausnahmen

Neue HTTP-/UI-/Driving-Adapter duerfen keine zusaetzlichen Imports auf
die verbotenen `hexagon.core.*`-Pakete erhalten. Wenn Adapter
Run-Ausfuehrung, Healthcheck, Scenario-Load oder Fault-Validierung
brauchen, muss die Surface ueber `hexagon.ports.*` oder
`hexagon.core.domain.*` laufen.

Bestehende `ignore_imports` werden nur noch abgebaut oder durch diese
ADR explizit in einen Folge-Slice ueberfuehrt. Eine Erweiterung der
Liste ist ADR-pflichtig.

### 2.2 Fault-Vokabular wird adapter-sichtbar ohne `core.faults`

Die Fault-Type-Konstanten, die HTTP-Request-Validation braucht, werden
in eine erlaubte, domain-nahe Surface verschoben oder gespiegelt, z. B.
`hexagon.core.domain.fault` oder ein Driving-Port-Modul. Der
HTTP-Adapter darf nicht mehr `hexagon.core.faults.types` importieren.

Der Single-Source-of-Truth-Vertrag bleibt erhalten: Device- und
Fault-Implementierungen konsumieren dieselben String-Konstanten wie
die API-Validation.

### 2.3 Run-Ausfuehrung bekommt eine Driving-Port-Surface

Die Registry, der Driver, die Router und der Healthcheck werden gegen
eine kleine Driving-Port-Surface typisiert, nicht gegen den konkreten
`TickLoop`. Arbeitsname: `ActiveRunPort` oder `RunExecutionPort`.

Mindest-Surface:

- `run_id: str`
- `tick_ms: int`
- `tick_count: int`
- `control_state: RunStatus`
- `device_types: Mapping[str, str]`
- `devices: tuple[object, ...]`
- `request(action: ControlAction) -> None`
- `tick() -> TickResult`
- `finalize() -> tuple[ReplayDelta, ...]`

`ControlAction` darf dabei nicht in `hexagon.core.simulation` bleiben,
wenn der Port es importiert. Der Alias wandert nach
`hexagon.core.domain.run` oder in ein anderes erlaubtes Domain-Modul.

`TickLoop` implementiert diese Surface strukturell; der HTTP-Adapter
sieht nur noch den Port.

### 2.4 Healthcheck misst einen Run-Port, keinen `TickLoop`

`TickLoopHealthcheckAdapter` wird so geschnitten, dass er nur `tick_ms`
und die vom Driver gemessenen Dauern braucht. Falls ein direkter
Run-Zugriff noetig bleibt, ist der Typ der neue Run-Port, nicht
`TickLoop`.

Damit fallen `_tick_loop_driver`, `_tick_loop_registry` und
`_tick_loop_healthcheck` aus der direkten
`hexagon.core.simulation.tick_loop`-Abhaengigkeit.

### 2.5 Demo- und Scenario-Bootstrap wandern aus `adapters/`

Module, die konkrete Core-Builder (`TickLoop`, `Scheduler`,
`load_scenario`, `build_tick_loop`) mit konkreten Adaptern
verdrahten, sind Composition Root, nicht HTTP-Adapter.

Die Demo-Bootstrap-Module wandern deshalb in ein neues, nicht unter
`grid_gym.adapters` liegendes Paket, z. B. `grid_gym.composition` oder
`grid_gym.bootstrap`. Dort duerfen Core und Adapter zusammengefuehrt
werden, ohne `AC-ADAPTER-PURE` zu verletzen.

Wenn Dateien verschoben und inhaltlich umgebaut werden, gilt die
Repo-Regel: erst reiner `git mv`-Commit, danach Inhaltsrewrite.

### 2.6 Fault-Adapter-Standort bleibt eigener Folgepunkt

`BatteryFaultAdapter` und `GridFaultAdapter` liegen historisch unter
`hexagon.core.faults`, obwohl Name und Doku sie als Adapter bezeichnen.
ADR 0050 erzwingt keinen sofortigen Move dieser Klassen. Die
Standort-/Naming-Entscheidung ist in
[`ADR 0051`](0051-fault-engine-location-and-naming.md) ausgelagert.

Der erste Rueckbau-Schritt darf die Klassen weiterhin dort lassen,
solange sie nur von Core oder Composition Root importiert werden, nicht
von `grid_gym.adapters.*`. Ein spaeterer Slice entscheidet separat:

- Umbenennen als Core-Fault-Engines, oder
- Verschieben nach `adapters/driven/fault_*` mit sauberer
  Port-/Protocol-Neuschneidung.

### 2.7 `ignore_imports` wird pro Tranche reduziert

Der `ignore_imports`-Block wird nicht pauschal geloescht. Jede Tranche
entfernt nur die Eintraege, deren Importpfad durch Code- und
Architekturtests tatsaechlich gruen ist.

Pflichtsensor pro Tranche: `make arch-check`. Bei produktiven
Codeaenderungen zusaetzlich die engsten Unit-/Integration-Tests und
als normaler Handoff `make gates`.

## 3. Konsequenzen

Positive Konsequenzen:

- `AC-ADAPTER-PURE` wird wieder als harte Grenze lesbar.
- HTTP-/UI-Adapter testen gegen kleine Port-Protokolle statt gegen
  konkrete `TickLoop`-Interna.
- Composition Root wird explizit und ist nicht mehr im Adapterpaket
  versteckt.
- Der bestehende `pyproject.toml`-Kommentarblock kann nach dem
  Rueckbau deutlich kleiner werden oder ganz entfallen.

Kosten und Risiken:

- Tests, die heute direkt `TickLoopRegistry.register(tick_loop)` nutzen,
  muessen auf den neuen Porttyp oder Fakes angepasst werden.
- `ControlAction`-Verschiebung beruehrt `TickLoop`, Schemas und Tests.
- Bootstrap-Moves brauchen wegen Rename-Detection eigene Commits.
- `docs/plan/adr/0039-run-control-and-status-tracking.md` bleibt
  historisch; die Schaerfung steht in ADR 0050 und im ADR-Index.

## 4. Out-of-Scope

- Neue oeffentliche HTTP-API-Surface.
- Semantische Aenderung von Pause/Resume/Stop.
- Neue Fault-Typen oder neue Fault-Recovery-Semantik.
- Vollstaendiger Move der Fault-Adapter aus `hexagon.core.faults`.
- `make gates`- oder `arch-check`-Lockerungen.

## 5. Acceptance

ADR 0050 kann auf `Provisional` springen, sobald der erste
Umsetzungsslice mindestens einen `ignore_imports`-Eintrag entfernt und
`make arch-check` ohne neue Ausnahme gruen ist. → **`Provisional`
2026-06-13 mit 041-C1**: Fault-Type-Konstanten nach
`hexagon.core.domain.fault` verschoben (`core.faults.types`
re-exportiert), `_runs_action_router`-Eintrag entfernt (8 → 7 Bruecken),
`make arch-check` 7/7 gruen. **041-C2**: NEU `RunExecutionPort`
(`hexagon/ports/driving/run_execution.py`, §2.3-Surface), `ControlAction`
nach `hexagon.core.domain.run`; Registry/Driver/Healthcheck gegen den
Port typisiert, 3 weitere Eintraege entfernt (7 → 4 Bruecken),
`make typecheck` Success. **041-C3a**: NEU `grid_gym.composition`-Paket
(§2.5), `_demo_setup` per `git mv` dorthin (kein src-Adapter-Importer),
2 Eintraege entfernt (4 → 2 Bruecken). **041-C3b**: App-Bootstrap-
Inversion ([`ADR 0054`](0054-composition-asgi-entrypoint-and-scenario-hook.md))
— `_demo_scenario_setup` nach `composition/`, `app.py` registriert den
Scenario-Konfigurator per Hook statt ihn zu importieren, neuer
`composition.asgi`-Entrypoint; letzte 2 Eintraege entfernt →
**`ignore_imports = []`** (0 Bruecken).

→ **`Accepted` 2026-06-13**: alle acht Bruecken entfernt,
`make arch-check` 7/7 + `tools/arch_check.py` clean (0 Ignores),
`make fullbuild` gruen.

`Accepted` ist erst sinnvoll, wenn alle acht oben genannten
`ignore_imports`-Eintraege entfernt oder per Folge-ADR bewusst neu
entschieden sind.
