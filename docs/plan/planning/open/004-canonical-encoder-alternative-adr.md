# 004 — ADR fuer Alternativ-Encoder kanonischer Serialisierung

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-15
**Quelle:** [`ADR 0002`](../../adr/0002-language-and-build-stack.md)
§7 „Offene Folge-Punkte" und A-2 Vertrag

---

## Trigger

[`ADR 0002`](../../adr/0002-language-and-build-stack.md) fixiert das **Format** der kanonischen Serialisierung
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
- Performance-Messpunkte (Telemetrie-Pfad, [`GG-RT-005`](../../../../spec/lastenheft.md#gg-rt-005)),
- Migrations-Strategie (Feature-Flag, Vergleichslauf in CI).

## Aktivierungs-Kriterium

Bei messbarem Performance-Druck auf dem Telemetrie-/Replay-Pfad
([`GG-RT-005`](../../../../spec/lastenheft.md#gg-rt-005) SOLLTE: 10.000 Punkte/s) oder spaetestens, wenn das
Demo-Szenario in CI deutlich mehr Zeit fuer Serialisierung als fuer
Tick-Verarbeitung benoetigt.

## Wandert nach

- `next/`, sobald ein Benchmark-Befund vorliegt,
- `in-progress/`, wenn ADR-Schreibarbeit beginnt.

---

## M4-Welle-6a-C3-Re-Eval (2026-06-01)

**Befund:** Trigger 004 bleibt in `open/` mit Defer auf M5/M6.
Begruendung:

- **Kein messbarer Performance-Druck** im aktuellen Repo:
  `canonical_json` ist im OTLP-Pfad (M3-Welle-6) der
  Default-Serialisierer; Compose-Smoke
  (`test_otlp_compose_smoke.py`) misst nicht den Encoder-
  Throughput separat. Der MQTT-Compose-Smoke
  (`test_mqtt_compose_smoke.py`) ist single-Message-Roundtrip,
  kein Throughput-Pfad. Welle-6a-C3 hatte den Compose-Smoke-
  MQTT-Throughput-Benchmark als optionalen Pfad — ein
  belastbarer Benchmark braucht aber dedizierte Last-Generierung
  (z. B. 10.000 Points/s im Tick), die in Welle 6a-Scope nicht
  produktiv-installiert wurde.
- **[`GG-RT-005`](../../../../spec/lastenheft.md#gg-rt-005)-SOLLTE-Schwelle (10.000 Punkte/s)** ist nicht
  fertig aktiviert. M4-Welle-7 (Closure) bringt voraussichtlich
  einen breiteren E2E-Benchmark; M5/M6 schaerft die
  Performance-Pfade systematisch (vgl. `M6 — Performance + Security
  + CI/CD` in `roadmap.md`).
- **Aktivierungs-Kriterium** (Original-Body §Aktivierungs-Kriterium)
  ist nicht erfuellt: kein gemessenes Demo-Szenario mit
  signifikantem Serialisierungs-Anteil.

**Entscheidung:** verbleibt in `open/` als Trigger-Watch.
Naechste Re-Eval-Pflicht: M5-Welle-0 (UI + Demo-Schaerfung)
oder M6-Welle-0 (Performance + Security), je nachdem, welche
zuerst startet. Falls Welle-7-Closure einen produktiven
Throughput-Benchmark einfuehrt, kann der Trigger dort
re-evaluiert werden.

**Welle-6a-C3-Action**: Verbleibt in `open/`; diese Re-Eval-
Notiz dokumentiert die Decision.

**M5-Welle-0-C2-Triage 2026-06-01:** verbleibt in `open/`.
M5-Welle-3 (Live-Telemetry-Dashboard mit WebSocket-Stream)
ist der natuerliche M5-Touch-Point, an dem ein messbarer
Throughput-Druck am Telemetrie-Pfad sichtbar werden koennte
(WebSocket-Push mit `canonical_json`-Serialisierung pro
Telemetrie-Tick). M5-Welle-3-Slice-Doc soll diesen Trigger
als Re-Eval-Pflicht-Punkt im DoD listen. Falls Welle 3
einen messbaren Druck zeigt, kann der Trigger dort
aktiviert werden; sonst bleibt er bis M6-Welle-0
deferred.
