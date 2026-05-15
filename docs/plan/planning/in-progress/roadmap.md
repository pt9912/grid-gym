# Roadmap — grid-gym

**Status:** Aktiv — Vorbedingungen 1+3+4 geschlossen, M1 In Progress
**Stand:** 2026-05-15 (M1 Welle 0 abgeschlossen)
**Bezug:** [Lastenheft](../../../../spec/lastenheft.md), [Architektur](../../../../spec/architecture.md)

---

## 1. Zweck

Diese Roadmap fuehrt die Meilensteine, die sich aus dem Lastenheft und
der Architektur ergeben. Sie ist die Quelle fuer die Status-Spalte
der `GG-TRACE-001`-Implementierungsmatrix
([Lastenheft §27.2](../../../../spec/lastenheft.md#272-anforderung-zu-implementierung))
mit `M[N]`-Markern.

`GG-AR-OPEN-001` (Sprach- und Build-Wahl) ist mit `ADR 0002`
(`Accepted` 2026-05-15) geschlossen. M1 (Tick-Loop-Spine) ist seit
2026-05-15 `In Progress` (Welle 0 abgeschlossen) — Details im
[Slice-Plan](M1-tick-loop-spine.md). M2+ wird mit dem M1-Abschluss
vorbelegt.

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
  [`ADR 0007`](../../adr/0007-random-port.md), `Provisional`
  seit 2026-05-15, Acceptance synchron mit Welle 2).
- **Abnahmekriterium:** `make fullbuild` gruen (impliziert
  Triggers 009 `tests/integration/compose.yml` und 010
  `deploy/compose.yml`) **und** `make gates` ohne
  `CRITICAL_COV_TARGETS`-Override gruen (Default-kritische
  Domain `simulation/scenario/replay/devices/battery` hat
  jeweils mindestens ein produktives Modul, Coverage ≥ 90 %
  Line + Branch).
- **Status:** In Progress — Slice-Plan
  [`M1-tick-loop-spine.md`](M1-tick-loop-spine.md) aktiv.
  Welle 0 abgeschlossen 2026-05-15: ADR 0007 (RandomPort)
  `Provisional`, Trigger 001 (`docs/user/code-review.md` +
  PR-Template) geliefert, Lock-Refresh sauber. Welle 1
  (Domain-Modelle) ist der naechste Schritt.

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
- ✓ **Trigger 001 (Code-Review-Doku + PR-Template)** — Post-
  Acceptance-Vorbedingung aus dem Dritten Spike-0-Review
  ([`done/spike-0-results.md`](../done/spike-0-results.md) §6).
  Erfuellt 2026-05-15 mit
  [`docs/user/code-review.md`](../../../user/code-review.md) und
  `.github/PULL_REQUEST_TEMPLATE.md`; Closure-Notiz in
  [`done/001-code-review-doc.md`](../done/001-code-review-doc.md).
