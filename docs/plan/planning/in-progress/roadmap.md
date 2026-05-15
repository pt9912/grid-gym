# Roadmap — grid-gym

**Status:** Aktiv — Vorbedingungen 1+3 geschlossen mit Spike-0
**Stand:** 2026-05-15
**Bezug:** [Lastenheft](../../../../spec/lastenheft.md), [Architektur](../../../../spec/architecture.md)

---

## 1. Zweck

Diese Roadmap fuehrt die Meilensteine, die sich aus dem Lastenheft und
der Architektur ergeben. Sie ist die Quelle fuer die Status-Spalte
der `GG-TRACE-001`-Implementierungsmatrix
([Lastenheft §27.2](../../../../spec/lastenheft.md#272-anforderung-zu-implementierung))
mit `M[N]`-Markern.

Die Roadmap ist noch ein Skelett. Sie wird mit dem ersten ADR zur
Sprach- und Build-Wahl (`GG-AR-OPEN-001`) und der ersten
Implementierungs-Slice gefuellt.

---

## 2. Konvention

- Meilensteine werden fortlaufend numeriert (`M1`, `M2`, …).
- Jeder Meilenstein hat:
  - Lieferziel (was wird umgesetzt),
  - Lastenheft-IDs (`GG-*`),
  - Architekturartefakte (`GG-AR-*`),
  - Abnahmekriterium (Verifikationspfad),
  - Status (Pending / In Progress / Done).
- Abgeschlossene Meilensteine wandern als Closure-Notiz nach
  `docs/plan/planning/done/`.
- Themes fuer kommende Meilensteine werden in `docs/plan/planning/next/`
  als Scope-Skizze gefuehrt, bevor sie hier als aktiver Slice aufgenommen
  werden.

---

## 3. Meilensteine

### M1 — Tick-Loop-Spine (Vorbelegung)

- **Lieferziel:** deterministischer Tick-Loop ohne Geraete:
  `ClockPort` (Driven), `RandomPort` (Driven, eigener ADR),
  Scheduler mit stabiler Tie-Breaking-Regel, leere Domain-Modelle
  (`Telemetry`, `Command`, `Event` als Frozen-Dataclasses),
  `canonical_json`-Anbindung an Snapshot-Pfad. Geraetemodelle
  (Battery, PV, Load, ...) folgen in M2+.
- **Lastenheft-IDs:** `GG-SIM-001..004` (Determinismus, Tick,
  Reproduzierbarkeit, parallele Geraete), `GG-SIM-005` (Snapshot),
  `GG-DATA-001..005` (Telemetry-Modell + kanonische
  Serialisierung), `GG-ARCH-005..008` (Event-Scheduler,
  Tie-Breaking, ClockPort, Replay-/Live-Spine geteilt),
  `GG-PRINC-001..006` (SOLID-Restanteil ueber `make arch-check`).
- **Architekturartefakte:** `GG-AR-COMP-CORE`
  (`hexagon/core/simulation`), `GG-AR-COMP-DOMAIN`
  (`hexagon/core/domain`), `GG-AR-COMP-SCHED`
  (`hexagon/core/simulation/scheduler`), `GG-AR-PORT-DRN-001`
  (`ClockPort`), `GG-AR-PORT-DRN-010` (`RandomPort` — via
  Folge-ADR aus Trigger `003-random-port-adr.md`).
- **Abnahmekriterium:** `make fullbuild` gruen (impliziert
  Triggers 009 `tests/integration/compose.yml` und 010
  `deploy/compose.yml`) **und** `make gates` ohne
  `CRITICAL_COV_TARGETS`-Override gruen (Default-kritische
  Domain `simulation/scenario/replay/devices/battery` hat
  jeweils mindestens ein produktives Modul, Coverage ≥ 90 %
  Line + Branch).
- **Status:** Pending — Slice-Plan wird in
  `docs/plan/planning/next/M1-tick-loop-spine.md` skizziert,
  sobald M1-Start-Termin steht.

---

## 4. Vorbedingungen

Vor M1 muessen folgende Punkte geklaert sein:

- ✓ **`GG-AR-OPEN-001` Sprach- und Build-Wahl** — geschlossen mit
  `ADR 0002` (`Accepted` 2026-05-15) und synchron `ADR 0005`
  (`Accepted` 2026-05-15). Spike-0 Closure-Notiz:
  [`docs/plan/planning/done/spike-0.md`](../done/spike-0.md).
- `GG-AR-OPEN-002` API/Simulation als ein oder zwei Prozesse —
  offen, eigene Folge-ADR.
- ✓ **Initiales Repository-Layout** gemaess der Hexagonalen Sicht
  (`GG-AR-P-002`, `GG-AR-TABU-001..008`) — sprachunabhaengig in
  `spec/architecture.md` §4.2 mit `hexagon/`-Gruppierung fixiert;
  Python-Paketnamen (`src/grid_gym/hexagon/{core,ports}/`,
  `src/grid_gym/adapters/`) durch `ADR 0002` §6.1 (`Accepted`
  2026-05-15) verbindlich.
