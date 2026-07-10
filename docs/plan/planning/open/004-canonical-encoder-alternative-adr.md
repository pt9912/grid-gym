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

---

## Re-Eval 2026-07-10 — Benchmark-Befund liegt vor (Trigger bleibt `open/`)

Die frueheren Notizen deferrten mit der Begruendung „kein produktiver
Throughput-Benchmark, deshalb kein messbarer Druck". Dieser Zustand ist
aufgeloest: der von der `Wandert nach`-Regel geforderte **Benchmark-Befund
liegt jetzt vor** — und er ist negativ (kein Druck).

**Befund (harte Evidenz):**

- [`GG-RT-005`](../../../../spec/lastenheft.md#gg-rt-005) (10.000 Punkte/s SOLLTE) ist
  produktiv **abgenommen** (M6-Welle-4b-b, `beb5dee..c8625f7`; siehe
  [`../done/M6-results.md`](../done/M6-results.md) Welle-Tabelle 4b-b). Der Bench
  `tests/perf/test_telemetry_port_bench.py` fuehrt den **Default-Emitter
  `canonical_json`** auf 10.000 `TelemetryPoint`s aus:
  - **Payload-Schwelle:** jeder Point canonical-serialisiert `<= 256 Byte`
    (Pre-Bench-Assert, alle 10.000 gruen) — der Custom-Emitter erfuellt den
    Groessen-Vertrag ohne Alternativ-Encoder.
  - **Throughput-Schwelle:** der Telemetrie-Port-Publish-Pfad liegt bei
    Median ~8,5 ms/10.000 Publishes (`baseline.json`), also ~0,85 us/Publish
    gegen die 100 us/Publish-Schwelle (1e-4 s) — rund **zwei
    Groessenordnungen Headroom**.
- Der Tick-Loop-Bench (`tests/perf/test_tick_loop_bench.py`,
  [`GG-RT-004`](../../../../spec/lastenheft.md#gg-rt-004): 100 Geraete x 10.000 Ticks,
  Median ~0,92 s) ist der naechste Proxy fuer die zweite Aktivierungs-Klausel
  („Demo-Szenario braucht deutlich mehr Zeit fuer Serialisierung als fuer
  Tick-Verarbeitung"): kein Hinweis, dass Serialisierung die Tick-Verarbeitung
  dominiert.
- Es existiert ein produktiver Baseline-Compare-Gate (`make perf`,
  20 % Median-Drift, [`ADR 0041`](../../adr/0041-performance-bench-pattern.md) §2.6).

Ehrlich abgegrenzt: der Bench timet den **Publish-Pfad** und die
**canonical-Payload-Groesse**, nicht die `canonical_json`-Serialisierungs-Rate
als isolierten Mikro-Bench. Er belegt damit nicht „Serialisierung ist beliebig
schnell", sondern das Entscheidungsrelevante: auf dem
[`GG-RT-005`](../../../../spec/lastenheft.md#gg-rt-005)-Vertragspfad
ist mit dem Default-Emitter **kein serialisierungs-attribuierbarer Druck
messbar**, und der SOLLTE-Schwellenwert wird mit grossem Abstand gehalten.

**Aktivierungs-Kriterium-Pruefung:** weiterhin **nicht erfuellt** — jetzt aber
positiv belegt (Benchmark gruen mit Headroom) statt nur „mangels Benchmark
nicht beurteilbar".

**Entscheidung:** Trigger 004 bleibt in `open/` als Trigger-Watch.

**Stale-Sprache aufgeloest (ersetzt die Re-Eval-Anker der 2026-06-01-Notizen):**
die dort genannten Re-Eval-Pflichten „M5-Welle-0 / M6-Welle-0" bzw.
„Welle-7-Closure fuehrt Throughput-Benchmark ein" sind erledigt — M6-Welle-4b-a/4b-b
hat den Bench geliefert, M6 ist `Done`. Die Planung ist seit
[`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md)
**slice-getrieben** (keine Meilensteine/Wellen mehr), deshalb traegt der Trigger
ab hier **keinen Milestone-Anker** mehr.

**Neues (slice-getriebenes) Re-Eval-Kriterium:** aktivieren (→ `next/`), wenn

- der `make perf`-Baseline-Compare eine **serialisierungs-attribuierbare
  Regression** am Telemetrie-/Replay-Pfad ueber die 20 %-Median-Drift-Schwelle
  ([`ADR 0041`](../../adr/0041-performance-bench-pattern.md)) flaggt, **oder**
- eine neue/verschaerfte SOLLTE-Schwelle oberhalb des aktuellen
  `canonical_json`-Headrooms eingefuehrt wird, **oder**
- ein Slice einen dedizierten `canonical_json`-Mikro-Bench einfuehrt, der einen
  konkreten Serialisierungs-Engpass zeigt.

Sonst bleibt der Trigger deferred — ohne Re-Eval-Pflichttermin, da
slice-getrieben.
