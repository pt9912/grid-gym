# ADR 0007 — `RandomPort` Implementierung

**Status:** Accepted
**Datum:** 2026-05-15
**Status geaendert am:** 2026-05-17 — `Provisional → Accepted`.
Validierungs-Spike aus §4a abgeschlossen: `RandomPort`-Protocol
(`hexagon/ports/driven/random.py`) + `MersenneTwisterRandomPort`
(`adapters/driven/random_mt/`) sind in M1 Welle 2 geliefert; alle
sechs Akzeptanzkriterien aus §4a per `make test-unit` gruen
(`tests/unit/adapters/driven/random_mt/test_mersenne_twister.py`).
Vorher: 2026-05-15 — `Proposed → Provisional` mit Freigabe des
Validierungs-Spikes (siehe §4a).
**Letzte inhaltliche Aenderung:** 2026-05-17 — §5.1 geschaerft:
`random_port_from_snapshot` lebt nicht im Port-Modul (`AC-PORTS-
NO-OUT` verbietet `ports → adapters`-Importe), sondern als
`classmethod` am konkreten Adapter (`MersenneTwisterRandomPort.
from_snapshot`). Vorher 2026-05-15 — erste Fassung.
**Bezug:** [Lastenheft](../../../spec/lastenheft.md),
[Architektur](../../../spec/architecture.md),
[`ADR 0002`](0002-language-and-build-stack.md) §A-1 [`AC-NO-RAND`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert),
[`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
(Lifecycle), [`docs/plan/planning/done/003-random-port-adr.md`](../planning/done-archive/003-random-port-adr.md)
(geschlossen durch diese ADR — wandert nach `done/` bei Acceptance).

---

## 1. Kontext

[`GG-SIM-001`](../../../spec/lastenheft.md#gg-sim-001) (Determinismus), [`GG-SCN-002`](../../../spec/lastenheft.md#gg-scn-002) (deterministische
Szenarien), [`GG-SEED-001`](../../../spec/spezifikation.md#gg-seed-001) (Seeds explizit seedbar) und
[`GG-AR-PORT-DRN-010`](../../../spec/architecture.md#driven-ports-vom-kern-aufgerufen) (`RandomPort` als Driven-Port) verlangen einen
deterministisch-reproduzierbaren Zufallsstrom je Simulationslauf.
`ADR 0002 §A-1 AC-NO-RAND` verbietet direkte Aufrufe von `random.*`,
`secrets.*` und `numpy.random.*` unter `hexagon/core/**`. Diese ADR
legt fest, wie der Port konkret implementiert wird.

Die Frage ist dreiteilig:

1. **Welcher PRNG?** stdlib `random.Random`, `numpy.random.Generator`
   (z. B. `PCG64`), oder eine eigene Implementation.
2. **Wie wird die Seeding-Kette aufgebaut?** Lauf-Seed → Sub-Seeds
   pro Domain/Komponente, damit Tests einzelne Sub-Ports isoliert
   betrachten koennen, ohne die globale Sequenz zu stoeren.
3. **Wie sieht das Snapshot-/Resume-Vertrag aus?** Tick-Loop-Snapshots
   muessen den Random-State so erfassen, dass Resume bit-identisch
   weiterlaeuft.

---

## 2. Bewertungskriterien

Gewichtung: P0 (Knock-out) > P1 > P2.

| Kennung   | Kriterium                                                                            | Bezug                                          | Gewicht |
| --------- | ------------------------------------------------------------------------------------ | ---------------------------------------------- | ------- |
| K-DET     | Vollstaendige Determinismus-Garantie ueber Python-Versionen, Plattformen, Builds      | [`GG-SIM-001`](../../../spec/lastenheft.md#gg-sim-001), [`GG-RT-002`](../../../spec/lastenheft.md#gg-rt-002)                          | P0      |
| K-RESUME  | Random-State serialisierbar; Snapshot/Resume bit-identisch                            | [`GG-SIM-005`](../../../spec/lastenheft.md#gg-sim-005)                                     | P0      |
| K-SUB     | Sub-Seeding stabil: gleicher Sub-Name → gleicher Sub-Stream, unabhaengig vom         | [`GG-SCN-002`](../../../spec/lastenheft.md#gg-scn-002), [`GG-SIM-001`](../../../spec/lastenheft.md#gg-sim-001)                         | P0      |
|           | Aufruf-Pfad der Parent-Generators                                                    |                                                |         |
| K-STDLIB  | Keine zusaetzliche C-Extension oder externe Dependency                                | [`GG-DEPLOY-002`](../../../spec/lastenheft.md#gg-deploy-002) (offline), [`GG-CICD-001`](../../../spec/lastenheft.md#gg-cicd-001) (reprod.) | P1      |
| K-FUTURE  | Erweiterbar fuer ML/RL-Workloads ([`GG-FUTURE-001`](../../../spec/lastenheft.md#gg-future-001)/002) ohne Determinismus-Bruch       | [`GG-FUTURE-001`](../../../spec/lastenheft.md#gg-future-001)/002                              | P2      |
| K-PERF    | Ausreichend schnell fuer [`GG-RT-005`](../../../spec/lastenheft.md#gg-rt-005) (10.000 Punkte/s; Random-Calls << 1 ms)          | [`GG-RT-005`](../../../spec/lastenheft.md#gg-rt-005)                                      | P2      |

---

## 3. Optionen

### Option A: Python stdlib `random.Random`

- Mersenne Twister (MT19937), seit Python 1.5 stabil.
- Determinismus: garantiert ueber Python-Versionen, sofern der
  Seed identisch ist (CPython-`random`-Modul dokumentiert das
  explizit). `K-DET ++`.
- Snapshot/Resume: `random.Random.getstate()` / `.setstate()`
  liefert ein vollstaendiges Tupel. Serialisierbar via
  `pickle` — fuer kanonische Snapshots ueber `canonical_json`
  muss der State auf `int`/`tuple[int, ...]` reduziert und in
  einem Domain-Wrapper gefuehrt werden. Konkret: `getstate()`
  gibt `(3, tuple_of_624_ints + (index,), None)` — 625 Ints,
  vollstaendig deterministisch. `K-RESUME +`.
- Sub-Seeding: keine native Sub-Port-API; Sub-Seeds werden ueber
  einen Hash der Sub-Port-Namen abgeleitet. Vertrag: SHA-256 des
  String `f"{parent_seed}:{sub_name}"`, erste 16 Hex-Stellen als
  Integer. Deterministisch, plattform-unabhaengig, kollisionsarm.
  `K-SUB ++`.
- Stdlib-only: keine Extra-Deps. `K-STDLIB ++`.
- Future: ML/RL-Workloads brauchen typischerweise `numpy.random.Generator`
  oder `torch.manual_seed`; `random.Random` ist zu schmal. Aber
  RL-Agenten leben in `hexagon/core/agents` als Folge-Slice und
  koennen einen separaten `MLRandomPort` einfuehren. `K-FUTURE o`.
- Performance: MT19937 ist langsamer als PCG64 (~3x), aber fuer
  einzelne Calls << 100 ns. Bei 10.000 Punkten/s ([`GG-RT-005`](../../../spec/lastenheft.md#gg-rt-005))
  irrelevant. `K-PERF +`.

### Option B: `numpy.random.Generator` (PCG64)

- Modern, statistisch besser, deutlich schneller.
- Determinismus: garantiert ueber numpy-Versionen 1.17+, die
  `Generator`-API ist explizit als API-stabil gekennzeichnet.
  `K-DET +`.
- Snapshot/Resume: `bit_generator.state` ist ein dict mit nested
  numpy-Arrays — Serialisierung nicht trivial fuer
  `canonical_json` (numpy-Typen sind verboten). `K-RESUME o`.
- Sub-Seeding: numpy bietet `SeedSequence.spawn(n)` als first-
  class API. Sehr sauber, aber das `SeedSequence`-Konzept braucht
  Disziplin (jeder Sub-Stream muss vom Parent abgespalten werden).
  `K-SUB ++`.
- Stdlib-only: numpy ist 70 MB zusaetzliche Runtime-Dependency.
  Bricht das [`GG-DEPLOY-002`](../../../spec/lastenheft.md#gg-deploy-002)-Offline-Versprechen nicht, aber
  vergroessert das Image und macht den Spike-0-Lock dicker.
  `K-STDLIB --`.
- Future: ML/RL-Workloads nutzen `numpy.random` direkt — kein
  Bridge noetig. `K-FUTURE ++`.
- Performance: PCG64 ist ~3x schneller als MT19937. Fuer
  [`GG-RT-005`](../../../spec/lastenheft.md#gg-rt-005) ohnehin irrelevant.

### Option C: Custom PRNG (z. B. xoshiro256**)

- Eigene Implementation in `~50` Zeilen Python.
- Determinismus voll kontrollierbar. `K-DET ++`.
- Sub-Seeding und Snapshot/Resume frei designbar. `K-SUB ++` / `K-RESUME ++`.
- Stdlib-only. `K-STDLIB ++`.
- Future: ohne ML-/RL-Interface. `K-FUTURE -`.
- **Hauptrisiko:** eigene PRNG-Implementation ist eine Wartungsbuerde
  und ein Test-Risiko. Mersenne Twister ist seit Jahrzehnten
  durchgetestet; eigener Code waere ein unnoetiger Vertrauensbruch.
  `K-DEV --`.

---

## 4. Entscheidung

**Empfohlen: Option A (`random.Random` aus der stdlib) mit
SHA-256-basierter Sub-Seeding-Kette.**

Begruendung:

- `K-DET` und `K-STDLIB` sind P0/P1 und in Option A perfekt erfuellt;
  Mersenne Twister ist plattform- und Python-versions-stabil seit
  ueber zwei Jahrzehnten.
- `K-RESUME` ist mit einem Domain-Wrapper sauber loesbar, der
  `getstate()` als Tuple persistiert und ueber `canonical_json`
  serialisiert (siehe §5.1).
- `K-SUB` wird ueber eine dokumentierte SHA-256-Sub-Seeding-Regel
  abgebildet — explizit deterministisch und reproducible.
- `K-STDLIB`: kein numpy-Runtime-Dep im Spike-0-Lock, bleibt offline-
  konsistent.
- Fuer [`GG-FUTURE-001`](../../../spec/lastenheft.md#gg-future-001)/002 (ML/RL) wird bei Bedarf ein separater
  `MLRandomPort`-Adapter eingefuehrt — Folge-Slice, nicht Bestandteil
  dieser ADR.

**Nicht empfohlen:** Option B (`numpy.random`) — Snapshot-Vertrag zu
unklar fuer `canonical_json`, Dep-Buerde zu hoch. Option C — Wartung
ohne Mehrwert.

---

## 4a. Validierungs-Spike-Vertrag

Lokaler Vertrag fuer den Provisional-Status (per Lifecycle-Pflicht
aus `ADR 0006`). Die Durchfuehrung geschieht in M1 Welle 2 (siehe
[`docs/plan/planning/done/M1-tick-loop-spine.md`](../planning/done-archive/M1-tick-loop-spine.md) §3 Welle 2).

**Akzeptanzkriterien:**

1. `hexagon/ports/driven/random.py` liefert das `RandomPort`-Protocol
   gemaess §5.1 (siehe unten).
2. Fake-Implementation `FixedSeedRandom` in
   `tests/unit/hexagon/ports/driven/conftest.py` oder als Test-Helfer. <!-- d-check:ignore (historisch: Fakes leben heute in _fakes.py) -->
3. `hypothesis`-Property-Test: zwei Generatoren mit demselben Seed
   produzieren identische Sequenzen ueber `next_int`, `next_float`
   und Sub-Port-Aufrufe.
4. `hypothesis`-Property-Test: `sub_port(name).next_*()` ist
   reproduzierbar — gleicher Parent-Seed + gleicher Sub-Name →
   gleicher Sub-Stream, **unabhaengig** davon, wie viele Calls auf
   dem Parent vorher gemacht wurden.
5. Snapshot/Resume-Test: `snapshot()` → `from_snapshot(state)` →
   nachfolgende Calls identisch zu einem ununterbrochenen Lauf.
6. `next_float()`-Determinismus auf CPython: derselbe Seed liefert
   ueber 10.000 Calls auf CPython 3.13.x und 3.14.x byte-identische
   `canonical_json`-Decimal-Strings (verifiziert die `repr(float)`-
   Round-Trip-Annahme aus §5.1).

**Dauer:** Innerhalb des M1-Welle-2-Zeitfensters (1 Personentag);
diese ADR fuegt keine zusaetzliche Dauer hinzu.

**Erfolgs-Definition:** Alle sechs Akzeptanzkriterien per
`make test-unit` (Dockerfile-Stage `test-unit`) gruen → diese ADR
geht auf `Accepted`.

**Misserfolgs-Definition:** Wenn ein Akzeptanzkriterium reproduzierbar
nicht erfuellt werden kann (z. B. `random.Random.getstate()` zeigt
auf einer bestimmten Python-Version ein anderes Tuple-Format), geht
diese ADR auf `Rejected`. Eine Nachfolge-ADR mit Option B oder C
tritt an die Stelle.

---

## 5. Konsequenzen (bei Acceptance)

### 5.1 `RandomPort`-Interface

```python
# src/grid_gym/hexagon/ports/driven/random.py
from __future__ import annotations
from decimal import Decimal
from typing import Protocol


class RandomPort(Protocol):
    """Deterministisch-reproduzierbarer Zufalls-Port (ADR 0007)."""

    def next_int(self, low: int, high: int) -> int:
        """Liefert einen Integer in [low, high] inklusive."""
        ...

    def next_float(self) -> Decimal:
        """Liefert einen Decimal-Wert in [0, 1) mit max. 6
        Nachkommastellen (GG-DATA-005-konform).

        Implementation: `random.random()` liefert float; wird via
        `Decimal(str(x)).quantize(Decimal("0.000001"),
        rounding=ROUND_HALF_EVEN)` an der Port-Grenze quantisiert.

        Stabilitaet: die Quantisierung verlaesst sich darauf, dass
        `str(float)` plattformuebergreifend stabil ist. CPython
        garantiert das ueber `repr(float)` (PEP 3101, Round-Trip-
        Eigenschaft seit CPython 3.1). Auf alternativen Python-
        Runtimes (PyPy, GraalPy, MicroPython) ist der Vertrag
        nicht garantiert; Spike-Vertrag AC 5 verifiziert das nur
        gegen CPython 3.13+/3.14.
        """
        ...

    def sub_port(self, name: str) -> RandomPort:
        """Erzeugt einen unabhaengigen Sub-Port mit deterministischem
        Sub-Seed (SHA-256 von `f"{parent_seed}:{name}"`, erste 16
        Hex-Stellen als Integer)."""
        ...

    def snapshot(self) -> bytes:
        """Serialisiert den internen Zustand als UTF-8-Bytes
        (canonical_json-Format). Enthaelt mindestens: Seed,
        Sub-Port-Pfad, Mersenne-Twister-State (`getstate()`-Tuple).

        Der Snapshot-Envelope traegt einen `version: int`-
        Discriminator (siehe §5.2), damit `core/simulation/Snapshot`
        in Welle 4 alle Sub-Snapshots versioniert nebeneinander
        ablegen kann (Forward-Compat: Sub-Schemata duerfen sich
        unabhaengig versionieren)."""
        ...


# Hinweis (Acceptance-Schaerfung 2026-05-17): der frueher hier
# skizzierte `random_port_from_snapshot`-Modul-Helper liegt NICHT
# im Port-Modul, sondern als `classmethod` am konkreten Adapter
# (`MersenneTwisterRandomPort.from_snapshot`, §5.2). Grund:
# `AC-PORTS-NO-OUT` (`ADR 0002 §A-1`) verbietet `ports → adapters`-
# Importe — eine Modul-Funktion im Port-Modul muesste den Adapter
# importieren und wuerde den Vertrag brechen. Aufrufer mit
# unbekannter Snapshot-Quelle sprechen den Adapter direkt an:
# `MersenneTwisterRandomPort.from_snapshot(state_bytes)`.
```

### 5.2 Konkrete Implementierung (`MersenneTwisterRandomPort`)

In `hexagon/core/simulation/random_impl.py` (oder besser:
unter `adapters/driven/random_*/` als „in-process Driven Adapter").
Die Diskussion „in core/ oder in adapters/" wird in §6 als offener
Folge-Punkt aufgelistet.

Wesentliche Eigenschaften:

- **PRNG:** `random.Random` (Mersenne Twister).
- **Seed-Format:** `int` (0 ≤ seed < 2^64).
- **Sub-Seeding:** SHA-256 von `f"{seed}:{sub_name}"`-UTF-8-Bytes;
  die ersten 16 Hex-Stellen als Integer (0..2^64-1) dienen als
  Sub-Seed.
- **`next_float()`-Quantisierung:** `Decimal(str(rng.random()))
  .quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)`.
- **Snapshot:** `canonical_json`-Bytes mit:
  ```json
  {
    "version": 1,
    "seed": <int>,
    "sub_path": ["root", "scheduler", ...],
    "state": [<int>, ..., <int>]  // 625-Tupel aus getstate()
  }
  ```
- **`from_snapshot`:** liest das JSON, setzt `random.Random.setstate()`
  zurueck. Schlaegt mit `RandomPortVersionError` (Subklasse von
  `GridGymError`) bei unbekannter `version` fehl.

### 5.3 Schliesst / verbindet

Bei Acceptance schliesst diese ADR:

- **Trigger 003** (`docs/plan/planning/done-archive/003-random-port-adr.md`)
  wandert nach `done/`.
- [`GG-AR-PORT-DRN-010`](../../../spec/architecture.md#driven-ports-vom-kern-aufgerufen) ist damit implementierungs-spezifiziert
  (sprach- und PRNG-Wahl).
- `AC-NO-RAND`-Vertrag aus `ADR 0002 §A-1` bekommt einen
  legitimen Zugangspfad: `RandomPort.next_*()` ueber
  `hexagon.ports.driven.random` ist die einzige erlaubte
  Zufalls-Quelle in `hexagon/core/**`.

### 5.4 Wirkung auf andere Dokumente

**Bei `Provisional`** (jetzt):

- Diese ADR darf in `done/M1-tick-loop-spine.md §3 Welle 2`
  referenziert werden — als „RandomPort-Vertrag pro ADR 0007
  (Provisional)".
- Keine Aenderung an `architecture.md` §19 oder `roadmap.md` §4.

**Bei `Accepted`** (synchron zu M1 Welle 2):

- Trigger 003 → `done/`.
- Closure-Notiz in `done/spike-0-results.md §6` ergaenzen (Hinweis,
  dass die im Spike-0 Welle 5 angekuendigte Folge-ADR jetzt
  geschlossen ist).
- `done/M1-tick-loop-spine.md §3 Welle 2` wird zu „Welle 2 fertig,
  ADR 0007 Accepted".
- `architecture.md §9.x` (Driven-Port-Beschreibung von
  [`GG-AR-PORT-DRN-010`](../../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)) bekommt einen Backlink-Satz „PRNG-Wahl
  und Seeding-Kette sind in ADR 0007 spezifiziert". Verhindert
  die Drift, die im Welle-5-Review beim Spike-0-Abschluss
  beobachtet wurde (zwei Stellen, an denen `RandomPort`-Vertrag
  steht, ohne dass eine die andere zitiert).

### 5.5 Migrations-Pfad

Welle 2 implementiert direkt nach der Provisional-Veroeffentlichung;
es gibt keinen Migrations-Pfad aus einer Vor-RandomPort-Welt, weil
M1 selbst die erste Welle mit Zufallsverbrauch ist.

---

## 6. Offene Folge-Punkte

- **Modul-Platzierung der Implementation**: `hexagon/core/...` (als
  „interne Spine-Implementation, gleicher Sprach-Stack wie Domain"
  betrachtet) vs. `adapters/driven/random_*/` (als „Driven Adapter
  mit Wahl der PRNG-Bibliothek"). Empfehlung Welle 2: zunaechst
  unter `adapters/driven/random_mt/` (analog zu Persistence-/
  Protocol-Adaptern). Entscheidung in Welle 2 final, ggf. mit
  kleinem Folge-ADR.
- **`MLRandomPort`**: separater Port fuer ML/RL-Workloads
  ([`GG-FUTURE-001`](../../../spec/lastenheft.md#gg-future-001)/002); eigene ADR sobald MPC/RL aktiv wird.
- **`AsyncRandomPort`** fuer asyncio-Multi-Agent-Bus
  ([`GG-AGENT-008`](../../../spec/lastenheft.md#gg-agent-008)): heute synchroner Vertrag; Async-Variante kommt
  mit Multi-Agent-Slice.

---

## 7. Nicht Gegenstand dieser ADR

- Wahl der ML/RL-Bibliothek (PyTorch vs. JAX) — siehe [`GG-FUTURE-002`](../../../spec/lastenheft.md#gg-future-002).
- Kryptographisch sichere Zufallsquellen (`secrets`) — werden in
  `hexagon/core` nicht benoetigt; Authentifizierung ist
  [`GG-AR-OPEN-010`](../../../spec/architecture.md#19-offene-architektonische-punkte) und kommt mit eigener Slice.
- Quasi-zufaellige Sequenzen (Halton/Sobol) fuer Sampling-MPC —
  spaeter, eigene ADR.
- Konkrete `random.Random`-Subclassing-Strategien (das ist
  Implementation-Detail, Welle 2 entscheidet).
