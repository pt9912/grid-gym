# 011 — Sub-Seed-Wortbreite fuer `MLRandomPort` / Multi-Agent

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-17
**Quelle:** [`ADR 0007`](../../adr/0007-random-port.md) §5.2
(Sub-Seeding ueber SHA-256 mit 64 bit) und §6 (`MLRandomPort` als
spaetere Folge-ADR).

---

## Trigger

`MersenneTwisterRandomPort.sub_port(name)` leitet den Sub-Seed
aus den **ersten 16 Hex-Stellen** der SHA-256-Hash-Bytes ab —
Wortbreite ist also 64 bit (`0..2^64-1`,
`_SUB_SEED_HEX_DIGITS = 16` in
`src/grid_gym/adapters/driven/random_mt/mersenne_twister.py`).

Birthday-Schwelle bei 64 bit: Kollisions-Wahrscheinlichkeit
erreicht 50 % bei `~ 2^32` (~ 4.3 Mrd) Sub-Ports. Bei M1-Slice-
realistischen Zahlen (`< 10^4` Sub-Ports pro Lauf, etwa Geraete ×
Faults × Agents) bleibt die Kollisions-Wahrscheinlichkeit
`< 10^-11` — unproblematisch.

Wenn aber `MLRandomPort` (`GG-FUTURE-001/002`) oder ein
Multi-Agent-Bus (`GG-AGENT-001..008`) die Sub-Port-Zahl in den
Millionen- bis Milliardenbereich treibt, wird die 64-bit-Grenze
relevant.

## Erwartete Lieferung

- ADR-Folge zu `ADR 0007 §5.2` mit der Entscheidung:
  - Wortbreite auf 128 bit erhoehen (`_SUB_SEED_HEX_DIGITS = 32`)
    und Snapshot-Schema-Version bumpen, ODER
  - separate `MLRandomPort`-Schicht mit eigener Seeding-Kette
    (z. B. `PCG64`-basiert) und eigenem Snapshot-Vertrag.
- Falls Snapshot-Schema-Bump: Migrationsregel fuer `version: 1`-
  Snapshots aus M1-Welle-2-Laeufen.
- Anpassung der Konstante `_SUB_SEED_HEX_DIGITS` + zugehoeriger
  Doku-/Kommentar-Stellen.

## Aktivierungs-Kriterium

- Ein Slice plant `> 10^6` Sub-Ports pro Lauf, ODER
- die Spike fuer `MLRandomPort` startet (mit Trainings-Workloads,
  die fortlaufend neue Sub-Streams ableiten).

## Wandert nach

- `next/`, sobald ein konkreter Slice den Sub-Port-Zaehler in den
  relevanten Bereich treibt,
- `in-progress/`, wenn Folge-ADR-Schreibarbeit beginnt.
