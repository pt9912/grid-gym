# 003 — ADR fuer `RandomPort`-Implementierung

**Status:** In-Progress — ADR geschrieben (`Provisional`), wartet auf
Acceptance via M1 Welle 2.
**Datum:** 2026-05-15 (geoeffnet); 2026-05-15 ADR-Skizze (siehe
[`ADR 0007`](../../adr/0007-random-port.md)) als `Provisional`.
**Quelle:** [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §7
**Verlinkt:** [`ADR 0007 RandomPort`](../../adr/0007-random-port.md)
(`Provisional`); schliesst diesen Trigger bei Acceptance.

---

## Trigger

`GG-SIM-001`/`GG-SCN-002`/`GG-SEED-001` verlangen einen
seedbaren, gebondeten Zufallsstrom pro Lauf. `GG-AR-PORT-DRN-010`
benennt den `RandomPort` als Driven-Port. ADR 0002 nennt die
Implementierungs-ADR als Folgearbeit:

> ADR fuer `RandomPort`-Implementierung (gebondeter PRNG,
> Seeding-Kette) — Folgearbeit, schliesst keinen `GG-AR-OPEN-*`,
> aber materiell wichtig fuer `GG-SIM-001`.

## Erwartete Lieferung

ADR-Skizze mit:

- PRNG-Wahl (Python stdlib `random.Random` vs. `numpy.random.Generator`),
- Seeding-Kette (Lauf-Seed → Sub-Seeds pro Geraet/Agent/Fault),
- Determinismus-Vertrag (gleiche Sub-Seed-Sequenz ueber Replay-Faktor
  und Pause/Resume),
- Test-Strategie (Property-Tests mit `hypothesis`),
- Schnittstelle (`RandomPort.next_*`-Methoden, Reproduzierbarkeit ueber
  Snapshot/Resume).

## Aktivierungs-Kriterium

Mit dem ersten Domain-Slice, der Zufall benoetigt (Scheduler-
Tie-Breaking, Geraete-Initialisierung, Fault-Sequenz).

## Wandert nach

- `next/`, sobald Slice-M1 die `RandomPort`-Nutzung skizziert,
- `in-progress/`, wenn ADR-Schreibarbeit beginnt.
