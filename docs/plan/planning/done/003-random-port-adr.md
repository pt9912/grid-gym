# 003 — ADR fuer `RandomPort`-Implementierung — Closure-Notiz

**Status:** Done — geschlossen 2026-05-17 mit Acceptance von
[`ADR 0007`](../../adr/0007-random-port.md) (`Provisional → Accepted`)
synchron zur M1-Welle-2-Lieferung.
**Datum:** 2026-05-15 (geoeffnet); 2026-05-15 ADR-Skizze als
`Provisional`; 2026-05-17 ADR-`Accepted` + Trigger-Closure.
**Quelle:** [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §7
**Verlinkt:** [`ADR 0007 RandomPort`](../../adr/0007-random-port.md)
(`Accepted`); M1-Slice-Plan
[`docs/plan/planning/in-progress/M1-tick-loop-spine.md`](../in-progress/M1-tick-loop-spine.md)
§3 Welle 2.

---

## Trigger (historisch)

`GG-SIM-001`/`GG-SCN-002`/`GG-SEED-001` verlangen einen seedbaren,
gebondeten Zufallsstrom pro Lauf. `GG-AR-PORT-DRN-010` benennt den
`RandomPort` als Driven-Port. ADR 0002 §7 nannte die
Implementierungs-ADR als Folgearbeit:

> ADR fuer `RandomPort`-Implementierung (gebondeter PRNG,
> Seeding-Kette) — Folgearbeit, schliesst keinen `GG-AR-OPEN-*`,
> aber materiell wichtig fuer `GG-SIM-001`.

## Lieferung

- **ADR 0007 `Accepted`** (2026-05-17): PRNG-Wahl
  `random.Random` (Mersenne Twister), SHA-256-Sub-Seeding,
  `canonical_json`-Snapshot-Format.
- **Operative Artefakte:**
  - `src/grid_gym/hexagon/ports/driven/random.py` —
    `RandomPort`-Protocol (`next_int`/`next_float`/`sub_port`/
    `snapshot`).
  - `src/grid_gym/adapters/driven/random_mt/mersenne_twister.py`
    — `MersenneTwisterRandomPort` mit `from_snapshot`-classmethod
    (statt der urspruenglich in `ADR 0007 §5.1` skizzierten
    Modul-Funktion; `AC-PORTS-NO-OUT` verbot den ports → adapters
    Import — §5.1 wurde 2026-05-17 bei Acceptance entsprechend
    geschaerft).
  - `src/grid_gym/hexagon/core/errors.py` —
    `RandomPortError`-Hierarchie mit Versions-/Format-/Gauss-
    Validierungs-Subklassen.
- **Validierungs-Spike (`ADR 0007 §4a` AC1-AC6) gruen:**
  `tests/unit/adapters/driven/random_mt/test_mersenne_twister.py`
  pinnt Protocol-Konformitaet, Seed-Determinismus (hypothesis),
  Sub-Seeding-Stabilitaet unabhaengig von Parent-Calls,
  Snapshot/Resume-Bit-Identitaet und den 10.000-Call-
  `canonical_json`-Stabilitaetstest.

## Governance-Klarstellung zur Reihenfolge in Commit `efe6f60`

Commit `efe6f60` traegt atomar (a) den Statuswechsel
`Provisional → Accepted` an ADR 0007 und (b) die §5.1-Schaerfung
zum `from_snapshot`-Pfad. Per `ADR 0006 §3` ist der
Entscheidungstext erst NACH `Accepted` immutable — der
§5.1-Edit greift in diesem Commit also auf den
Pre-Commit-Provisional-Text (legal per Lifecycle-Tabelle in
`ADR 0006 §2`). Status-Flip und Inhaltsedit erscheinen im
gleichen `git`-Snapshot, weil die Reihenfolge ueber zwei Commits
keinen zusaetzlichen Audit-Wert haette (der Pre-Acceptance-Stand
ist im Diff `git show efe6f60^^!` jederzeit rekonstruierbar) und
die `Letzte inhaltliche Aenderung`-Zeile im ADR-0007-Header die
Schaerfung explizit als Pre-Acceptance-Akt ausweist
(`ADR 0006 §4`). Diese Notiz lebt hier, weil ADR-0007-Header
nach Acceptance pro `ADR 0006 §3` selbst nicht mehr inhaltlich
angefasst werden darf.

## Aktivierungs-Kriterium (erfuellt)

Aktivierung erfolgte mit M1 Welle 2 durch den
**Validierungs-Spike-Vertrag aus ADR 0007 §4a** (AC1-AC6
gruen) — also durch die Bereitstellung von Port-Protocol,
Adapter-Implementation und Snapshot-Vertrag, nicht durch
produktive Nutzung im Tick-Loop. Die produktive Inanspruchnahme
(`RandomPort` im Scheduler-Tie-Breaking, in der Geraete-
Initialisierung, in Fault-Sequenzen) folgt in:

- **Welle 3** (`Scheduler` mit Tie-Breaking
  `(time, priority, source, sequence, event_id)`,
  `GG-ARCH-006`): einer der Tie-Breaking-Inputs (`sequence`)
  kann aus dem `RandomPort` kommen, sofern Event-Source kein
  eigenes Counter-Schema mitbringt.
- **Welle 4** (`TickLoop` + Snapshot, `GG-SIM-005`):
  `RandomPort.snapshot()` wird als Sub-Snapshot in den
  `SnapshotEnvelope` aufgenommen — die `version: int`-Konvention
  aus Welle-1-`SnapshotEnvelope` und das `rng_state`/
  `rng_version`-Feld-Layout aus `MersenneTwisterRandomPort.
  snapshot()` greifen dort ineinander.
- **Welle 5+** (Scenario, Replay, Devices): Verbrauch durch
  Geraete-Initialisierung und Fault-Injection.

Frueher in dieser Notiz stand „Mit M1 Welle 2 (Domain-Slice mit
Zufallsverbrauch im Tick-Loop-Scheduler) aktiviert" — das war
unpraezise: Welle 2 hat den `RandomPort` bereitgestellt und
validiert (`§4a`-Spike), aber der Scheduler-Tick-Loop kommt erst
in Welle 3/4. Die ADR-Acceptance haengt am Spike-Vertrag, nicht
an einer produktiven Inanspruchnahme.

## Wandert nach

`done/` (jetzt). Keine weiteren Folge-Schritte zur Acceptance —
`MLRandomPort` und `AsyncRandomPort` sind eigene Folge-ADRs in
spaeteren Slices (siehe `ADR 0007 §6`).
