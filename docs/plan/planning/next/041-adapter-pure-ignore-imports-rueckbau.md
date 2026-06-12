# 041 — AC-ADAPTER-PURE-`ignore_imports`-Rueckbau

**Status:** Next — Scope skizziert, noch nicht aktiv
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

- ADR 0050 anlegen.
- Diesen `next/`-Plan anlegen.
- `docs/plan/adr/README.md` und `docs/plan/planning/next/README.md`
  synchronisieren.
- Sensor: `make docs-check`.

### C1 — Fault-Type-Quick-Win

- Fault-Type-Konstanten in eine adapter-erlaubte Surface ziehen
  (`hexagon.core.domain.fault` oder Port-Modul).
- `_runs_action_router.py` auf diese Surface umstellen.
- `pyproject.toml`-Eintrag
  `_runs_action_router -> grid_gym.hexagon.core.faults.types`
  entfernen.
- Tests: `make arch-check`, engste Router-/Fault-Tests.

### C2 — Run-Ausfuehrungs-Port

- Neuen Driving-Port einfuehren, Arbeitsname
  `ActiveRunPort`/`RunExecutionPort`.
- `ControlAction` aus `hexagon.core.simulation.tick_loop` in eine
  erlaubte Domain-Surface verschieben.
- `TickLoopRegistry`, `_runs_action_router.py`, `_runs_router.py`,
  `_tick_loop_driver.py` und `_tick_loop_healthcheck.py` gegen den
  Port typisieren.
- Entfernbare `pyproject.toml`-Eintraege:
  `_tick_loop_registry`, `_tick_loop_driver`,
  `_tick_loop_healthcheck` -> `simulation.tick_loop`.
- Tests: `make arch-check`, `make test-unit`.

### C3 — Demo-/Scenario-Bootstrap aus `adapters/` herausziehen

- `_demo_setup.py` und `_demo_scenario_setup.py` in ein neues
  Composition-Root-Paket verschieben, z. B.
  `src/grid_gym/composition/`.
- Reiner `git mv`-Commit zuerst, Inhaltsrewrite danach.
- `app.py`, `__main__.py`, Tests und Doku-Referenzen anpassen.
- Entfernbare `pyproject.toml`-Eintraege:
  `_demo_setup -> simulation.tick_loop`,
  `_demo_setup -> simulation.scheduler`,
  `_demo_scenario_setup -> scenario.loader`,
  `_demo_scenario_setup -> core.faults`.
- Tests: `make arch-check`, Demo-/HTTP-Smokes, danach `make gates`
  nach Moeglichkeit.

### C4 — Kommentar- und Doku-Rueckbau

- `pyproject.toml`-Kommentarblock fuer die historischen Bruecken
  kuerzen oder entfernen.
- ADR-/Plan-Referenzen aktualisieren.
- Falls alle acht Eintraege weg sind: ADR 0050 fuer spaetere
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
