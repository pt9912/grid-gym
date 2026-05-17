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

## Aktivierungs-Kriterium (erfuellt)

Mit M1 Welle 2 (Domain-Slice mit Zufallsverbrauch im Tick-Loop-
Scheduler) aktiviert; in der gleichen Welle abgearbeitet.

## Wandert nach

`done/` (jetzt). Keine weiteren Folge-Schritte — `MLRandomPort`
und `AsyncRandomPort` sind eigene Folge-ADRs in spaeteren Slices
(siehe `ADR 0007 §6`).
