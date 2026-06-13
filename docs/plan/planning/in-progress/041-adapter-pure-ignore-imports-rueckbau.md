# 041 — AC-ADAPTER-PURE-`ignore_imports`-Rueckbau

**Status:** In Progress (M8-Welle-1) — C1..C3b Done 2026-06-13 (**8 von 8
Bruecken entfernt**, `ignore_imports = []`, [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)
`Accepted`); offen nur C4 (`pyproject.toml`-Kommentar-Cleanup)
**Datum:** 2026-06-09
**Bezug:**

- [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)
  — Architekturentscheidung fuer den Bridge-Rueckbau.
- [`ADR 0002`](../../adr/0002-language-and-build-stack.md)
  — A-1-Architekturtests (`AC-ADAPTER-PURE`,
  `AC-PORTS-NO-OUT`).
- [`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md)
  — historische Run-Control-/TickLoop-Bridge.
- [`spec/architecture.md`](../../../../spec/architecture.md#2-architekturprinzipien)
  — `GG-AR-P-002`, `GG-AR-P-003`, `GG-AR-TABU-001..004`.
- [`pyproject.toml`](../../../../pyproject.toml)
  — aktueller `AC-ADAPTER-PURE`-`ignore_imports`-Block.

---

## 1. Ziel

Der aktuelle `AC-ADAPTER-PURE`-Contract ist nur mit acht
`ignore_imports`-Eintraegen gruen. Dieser Slice baut diese Bruecken
schrittweise ab, ohne die Gate-Regeln zu lockern und ohne Verhalten am
HTTP-/Demo-Pfad zu aendern.

Erfolgskriterium fuer die erste Aktivierung: mindestens ein Eintrag
verschwindet aus `pyproject.toml`, und `make arch-check` bleibt gruen.

## 2. Ist-Liste

Aktuelle Ausnahmen:

1. `_demo_setup -> hexagon.core.simulation.tick_loop`
2. `_demo_setup -> hexagon.core.simulation.scheduler`
3. `_tick_loop_registry -> hexagon.core.simulation.tick_loop`
4. `_tick_loop_driver -> hexagon.core.simulation.tick_loop`
5. `_tick_loop_healthcheck -> hexagon.core.simulation.tick_loop`
6. `_demo_scenario_setup -> hexagon.core.scenario.loader`
7. `_demo_scenario_setup -> hexagon.core.faults`
8. `_runs_action_router -> hexagon.core.faults.types`

## 3. Tranchierung

### C0 — Planungs-/ADR-Artefakte

- [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md) anlegen.
- Diesen `next/`-Plan anlegen.
- `docs/plan/adr/README.md` und `docs/plan/planning/next/README.md`
  synchronisieren.
- Sensor: `make docs-check`.

### C1 — Fault-Type-Quick-Win (Done 2026-06-13)

- ✅ Fault-Type-Konstanten nach `hexagon.core.domain.fault` (NEU)
  verschoben; `hexagon.core.faults.types` re-exportiert von dort
  (4 Core-Konsumenten unveraendert, Single-Source-of-Truth gewahrt).
- ✅ `_runs_action_router.py` importiert die Konstanten aus
  `hexagon.core.domain.fault`.
- ✅ `pyproject.toml`-Eintrag
  `_runs_action_router -> grid_gym.hexagon.core.faults.types`
  entfernt (8 → 7 `ignore_imports`).
- ✅ Sensoren: `make arch-check` 7/7 KEPT, `make typecheck`/`lint`/
  `format-check` gruen, `make test-unit` 1796 passed. Verhaltensneutral.

### C2 — Run-Ausfuehrungs-Port (Done 2026-06-13)

- ✅ NEU `hexagon/ports/driving/run_execution.py` —
  `RunExecutionPort` (Protocol, 9-Member-Surface aus `ADR 0050` §2.3:
  `run_id`/`tick_ms`/`tick_count`/`control_state`/`device_types`/
  `devices` + `request`/`tick`/`finalize`). `devices` als
  `tuple[object, ...]` (keine `DeviceModel`-Import-Pflicht).
- ✅ `ControlAction` aus `core.simulation.tick_loop` nach
  `core.domain.run` verschoben (`tick_loop` importiert von dort;
  `Literal`-Import dort entfernt).
- ✅ `TickLoopRegistry`, `_tick_loop_driver.py`,
  `_tick_loop_healthcheck.py` gegen `RunExecutionPort` typisiert;
  `_runs_router.py`/`_runs_action_router.py` sehen den Port
  transparent ueber die Registry (nur Surface-Member genutzt).
  `TickLoop` erfuellt den Port strukturell — kein Vererbungs-Zwang.
- ✅ 3 `pyproject.toml`-Eintraege entfernt
  (`_tick_loop_registry`/`_tick_loop_driver`/`_tick_loop_healthcheck`
  -> `simulation.tick_loop`); jetzt **4** Bruecken (von 8).
- ✅ Sensoren: `make arch-check` 7/7 KEPT, `make typecheck` Success
  (180 Dateien), `make lint`/`format-check` gruen, `make test-unit`
  1796 passed. Verhaltensneutral.

### C3 — Demo-/Scenario-Bootstrap aus `adapters/` herausziehen

Gesplittet nach Befund (2026-06-13): `AC-ADAPTER-PURE` (`type = forbidden`,
kein `allow_indirect_imports`) prueft **indirekte** Ketten. `_demo_setup`
hat keinen src-Adapter-Importer → risikoarmer Sofort-Move.
`_demo_scenario_setup` wird per `app.py`-Lifespan
(`_configure_scenario_demo_from_env_if_requested`, lazy import) gezogen —
ein reiner Move liesse die Kette `app` (Adapter) → `composition` →
`core.scenario`/`core.faults` bestehen → Verletzung. Loesung braucht eine
App-Bootstrap-Inversion.

#### C3a — `_demo_setup` nach `composition/` (Done 2026-06-13)

- ✅ NEU `src/grid_gym/composition/`-Paket (Composition Root, `ADR 0050` §2.5).
- ✅ `_demo_setup.py` per reinem `git mv` (byte-identisch, 100% Rename) nach
  `composition/`; einziger Importer (1 Unit-Test) nachgezogen.
- ✅ 2 `pyproject.toml`-Eintraege entfernt
  (`_demo_setup -> simulation.tick_loop`/`scheduler`); jetzt **2** Bruecken.
- ✅ Sensoren: `make arch-check` 7/7 KEPT, `make gates` gruen.

#### C3b — `_demo_scenario_setup`-Inversion (Done 2026-06-13, `ADR 0054`)

- ✅ App-Bootstrap invertiert: `app.py` exportiert den
  `_`-Hook `_register_scenario_configurator` + fail-closed Default;
  der Lifespan-Env-Branch ruft den registrierten Konfigurator statt
  das Scenario-Bootstrap zu importieren.
- ✅ `_demo_scenario_setup.py` per `git mv` nach `composition/`;
  NEU `grid_gym.composition.asgi` verdrahtet + registriert beim Import.
- ✅ uvicorn-Target (`Dockerfile`-ENTRYPOINT, `__main__`, Env-Smokes)
  → `composition.asgi:app`.
- ✅ Letzte 2 Eintraege entfernt → **`ignore_imports = []`** (0 Bruecken)
  → [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md) `Accepted`.
- ✅ NEU [`ADR 0054`](../../adr/0054-composition-asgi-entrypoint-and-scenario-hook.md)
  (Entrypoint-Wechsel + Hook-Inversion). Hook `_`-prefixt
  (`AC-NO-GOD-UTILS` max 5 public top-level functions in `app.py`).
- ✅ Sensoren: `make arch-check` 7/7 + `tools/arch_check.py` clean
  (0 Ignores), `make fullbuild` gruen (Compose-Smoke ueber neuen
  Entrypoint), NEU `tests/unit/composition/test_asgi.py`.

### C4 — Kommentar- und Doku-Rueckbau

- `pyproject.toml`-Kommentarblock fuer die historischen Bruecken
  kuerzen oder entfernen.
- ADR-/Plan-Referenzen aktualisieren.
- Falls alle acht Eintraege weg sind: [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md) fuer spaetere
  `Accepted`-Closure vormerken.

## 4. Nicht-Ziele

- Keine neue oeffentliche HTTP-API.
- Keine Semantikaenderung an Pause/Resume/Stop.
- Kein sofortiger Move von `BatteryFaultAdapter`/`GridFaultAdapter`
  aus `hexagon.core.faults`.
- Keine Gate-Lockerung und kein neuer `ignore_imports`-Eintrag.

## 5. Risiken

- `ControlAction`-Verschiebung kann viele Tests anfassen, obwohl die
  Semantik unveraendert bleibt.
- Bootstrap-Move kann Importzyklen in `app.py` sichtbar machen.
- Tests koennen bisher konkrete `TickLoop`-Instanzen erwarten; Fakes
  fuer den neuen Port muessen sauber genug sein, damit sie keine
  produktiven Vertraege verschleiern.

## 6. DoD

- `pyproject.toml` enthaelt mindestens einen `ignore_imports`-Eintrag
  weniger.
- `make arch-check` gruen.
- Engste betroffene Unit-/Integration-Tests gruen oder mit Grund im
  Handoff genannt.
- `make docs-check` gruen nach ADR-/Plan-Aenderungen.
- Keine neue `AC-ADAPTER-PURE`-Ausnahme.
