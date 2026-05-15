# 004 — ADR fuer Alternativ-Encoder kanonischer Serialisierung

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-15
**Quelle:** [`ADR 0002`](../../adr/0002-language-and-build-stack.md)
§7 „Offene Folge-Punkte" und A-2 Vertrag

---

## Trigger

ADR 0002 fixiert das **Format** der kanonischen Serialisierung
(A-2 Punkt 2) und die **Standard-Implementierung** (Custom-Emitter,
A-2 Punkt 3). Eine Folge-ADR darf die Umsetzungsroute aendern
(z. B. `orjson`-Bridge, `msgspec`, Rust-Backend), muss aber:

- die Format-Details aus A-2 Punkt 2 unveraendert erfuellen,
- **Byte-Gleichheit** gegenueber dem Standard-Emitter nachweisen,
- die Vor-Normalisierung (Decimal-Quantize, ISO-8601-UTC, …)
  unveraendert davor laufen lassen.

## Erwartete Lieferung

ADR-Skizze mit:

- Bewertung Encoder-Optionen (`orjson` + Decimal-Stream-Adapter,
  `msgspec`, Rust-PyO3),
- Byte-Gleichheits-Test gegen `core.serialization.canonical`,
- Performance-Messpunkte (Telemetrie-Pfad, `GG-RT-005`),
- Migrations-Strategie (Feature-Flag, Vergleichslauf in CI).

## Aktivierungs-Kriterium

Bei messbarem Performance-Druck auf dem Telemetrie-/Replay-Pfad
(`GG-RT-005` SOLLTE: 10.000 Punkte/s) oder spaetestens, wenn das
Demo-Szenario in CI deutlich mehr Zeit fuer Serialisierung als fuer
Tick-Verarbeitung benoetigt.

## Wandert nach

- `next/`, sobald ein Benchmark-Befund vorliegt,
- `in-progress/`, wenn ADR-Schreibarbeit beginnt.
