# ADR 0030 — DeviceProtocolPort-Surface (M4 Welle 1)

**Status:** Provisional — geschaerft 2026-05-30 (M4-Welle-1-C3,
dieser Commit) nach M4-Welle-1-C2-Merge `d09adf3` (feat:
`DeviceProtocolPort`-Protocol-Surface + `TickLoop`-Lifecycle-
Methoden + 23 neue Unit-Tests; `make gates` cache-frei gruen
ohne `CRITICAL_COV_TARGETS`-Override).
Status-Pfad: Proposed (2026-05-26 `b840e7a` + Review-Folge
`ad3dff8` + H4-Korrektur `111c464`) → Provisional (dieser
Commit) → Accepted (geplant mit M4-Welle-7-Closure).
**Datum:** 2026-05-26 (Erstfassung) / 2026-05-30 (Provisional-Schaerfung)
**Bezug:**
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md)
(Schaerfungs-/Erweiterungs-ADR-Pattern — ADR 0030 ist
neuer Port-Slot, kein Supersedes; aber `AC-ADAPTER-
LIGHTWEIGHT` aus `ADR 0002 §A-1` greift weiter),
[`ADR 0015`](0015-snapshot-envelope-v2.md) §2 (Snapshot-
Envelope-Schema-Bump-Pfad fuer Decision 7
Reversibilitaet),
[`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
§2.8 (Tick-Reihenfolge / Vor-Tick-Block — Praezedenz-
Anker fuer vor-Tick-/nach-Tick-Hook-Punkte; **Lifecycle
fuer `start`/`stop` rund um die Caller-getriebene
Tick-Schleife ist mit dieser ADR neu**, in ADR 0021 noch
nicht spezifiziert),
[`ADR 0022`](0022-fault-injection-protocol.md) §2.5
(neuer Driven-Port-Slot-Pattern: `FaultPort` als
Praezedenz fuer neuen Driven-Port mit Konstruktor-Kwarg-
Symmetrie + None-Default-Hook-Skip),
[`ADR 0024`](0024-observability-port-trio.md) §2.1
(Gemeinsame Port-Surface-Form — Praezedenz fuer
Decision 2 „Port bleibt Protokoll-Library-frei";
Trio-Definitionen in §2.2–§2.4 spiegeln das Pattern
pro Port).
M4-Slice-Plan
[`in-progress/M4-protocol-adapters.md`](../planning/in-progress/M4-protocol-adapters.md)
§3 Welle 1; M4-Welle-0-Decision-Liste
[`done/M4-welle-0.md`](../planning/done/M4-welle-0.md) §3
(Items 1, 2, 3, 7).
Lastenheft §16 (`GG-MQTT-001`, `GG-MODB-001`,
`GG-OPCUA-001`, `GG-DNP3-001`, `GG-IEC-001` — alle
SOLLTE; Z. 1120–1163 inkl. Cross-Cutting-Pflicht
„Simulations-/Testadapter").
Architektur §7 (`GG-AR-PORT-DRN-007` Driven-Ports-
Tabelle, Z. 249) + §8.2 (Adapter-Interfaces-Driven-
Beschreibung, Z. 510–512) + §16 (Deployment-Sicht
listet `simulation` als einzigen Worker-Service ohne
explizite Adapter-Verortung — daraus folgt, und **diese
ADR schreibt es normativ fest**, dass Protokoll-Adapter
im `simulation`-Container leben und keinen eigenen
Compose-Service erhalten; vgl. Welle-0-Inferenz in
[`done/M4-welle-0.md`](../planning/done/M4-welle-0.md)
§1).

---

## 1. Kontext

`GG-AR-PORT-DRN-007` (`DeviceProtocolPort`) ist in der
Architektur seit Roadmap-Initialstand als Driven-Port-Slot
vorbelegt, im Quellcode aber bis 2026-05-26 nicht
implementiert. M4 (Protokolladapter) ist der naechste
aktive Slice — die Welle-1-Foundation legt die
Port-Surface, auf der Welle 2..5 die konkreten Adapter
(MQTT/Modbus/OPC-UA/DNP3/IEC) aufsetzen.

Die M4-Welle-0-Decision-Liste
([`done/M4-welle-0.md`](../planning/done/M4-welle-0.md) §3)
hat sieben offene Fragen gesammelt. ADR 0030 entscheidet
die Surface-relevanten Fragen — Decision 2 (Sync/Async),
Decision 3 (Lifecycle), Decision 7 (Snapshot-Pflicht) —
**final**; Decision 1 (DNP3/IEC-Disposition) **provisorisch**
als Verzicht-Default. Die Adapter-Profil-Fragen
(Decision 4 Topic/Register/Node-Schema, Decision 5
Test-Sibling-Container, Decision 6
`AC-ADAPTER-LIGHTWEIGHT`-Pfad-Filter) sind nicht
Surface-relevant und wandern in die jeweiligen
Adapter-Wellen (Decision 4/5 in Welle 2; Decision 6 ist
bereits seit M3-Welle-6 erfuellt durch
`tools/arch_check.py:1089`
`bucket.startswith("protocol_")`, Regression-Schutz in
Welle-1-C2).

**Spannungsfeld:**

- TickLoop ist sync (Architektur-Anker `GG-AR-COMP-CORE`).
  Eine async-`DeviceProtocolPort`-Surface wuerde einen
  Sync->Async-Shim im Kern erfordern, der alle bestehenden
  Driven-Port-Aufrufer (Persistenz, Telemetry, Random,
  Faults, Observability) nicht stoert, sich aber durch das
  ganze TickLoop-Innere zieht.
- Protokoll-Bibliotheken sind gemischt: `paho-mqtt` ist
  sync (interner Thread im Client), `pymodbus` ≥ 3 bietet
  sync **und** async, `asyncua` ist nur async,
  DNP3/IEC-Stacks sind ueberwiegend async.
- Adapter-Lifecycle (Connect/Subscribe) ist
  verbindungsabhaengig und in Replay-Mode unnoetig — die
  Replay-Source-Pfade speisen Telemetry/Commands aus
  `ReplaySamplePort`, nicht aus Protokoll-Brokern.
- Snapshot-Vertrag: Welle-2+-Adapter koennten
  Reconnect-State (z. B. Modbus-Read-Cursor) persistent
  brauchen — oder nicht. Die Welle-1-Default-Wahl ist
  reversibel via ADR-0015-Schema-Bump-Pfad.

---

## 2. Entscheidung

ADR 0030 legt vier Surface-Decisions fest.

### 2.1 Decision 2 — Sync-Charakter (final); Methoden-Signaturen (Welle-1-C2-Skizze + Welle-2-Schaerfung)

`DeviceProtocolPort` ist ein sync-`typing.Protocol`. Async-
Stacks (`asyncua`, ggf. DNP3/IEC) marshalen Calls
**adapter-intern** ueber einen eigenen asyncio-Event-Loop-
Thread + Queue / `asyncio.run_coroutine_threadsafe`.

**Surface (Skizze, finale Signatur in Welle-1-C2-feat):**

```text
class DeviceProtocolPort(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def read(self, target: str) -> TelemetryPoint | None: ...
    def write(self, target: str, command: Command) -> None: ...
```

Konkrete Methoden-Signaturen (Multi-Target-Read,
Subscribe-Pattern, Batched-Write) ergeben sich aus dem
Welle-2-MQTT-Adapter und werden in Welle-2-Adapter-ADR
geschaerft. Welle 1 liefert das Surface-Minimum.

**Begruendung:**

- TickLoop bleibt unveraendert sync. Kein Sync->Async-
  Shim im Kern.
- Komplexitaet ist im Adapter eingekapselt — pro
  Adapter konfigurierbar (z. B. asyncua-Adapter
  startet eigenen `asyncio.new_event_loop()` in
  `start()`).
- Pattern-Praezedenz `telemetry_otlp/` ist
  **eingeschraenkt** ein Vorbild: das Modul ist
  single-threaded; das interne Batching uebernimmt
  das OTel-SDK selbst (`opentelemetry-sdk` mit
  `BatchSpanProcessor`/`BatchLogRecordProcessor`).
  Fuer asyncua-Adapter braucht der eigene
  Thread+Loop-Konstruktion — das Vorbild fehlt im
  bestehenden Codebase, ist aber Standard-Pattern
  (siehe asyncua-Doku „Synchronous wrapper").
- `pymodbus` (sync-Client) fuegt sich direkt in den
  sync-Port ein, ohne Adapter-internen Thread-Marshal.
- `paho-mqtt` ist nur **halb** sync: der Client laeuft
  per `loop_start()` in einem internen Thread, und
  Callbacks (`on_message`, `on_connect`) feuern aus
  diesem Thread. Welle-2-MQTT-Adapter loest den
  Callback→Sync-Port-Marshal **adapter-intern** ueber
  eine thread-sichere `queue.Queue` (oder
  `loop_forever()`-in-eigenem-Thread mit interner
  Queue). Welle-2-Implementer-Auflage in §4.

**Konsequenz:** Welle 4 (OPC-UA) tragt die Thread+Loop-
Konstruktion fuer einen rein-async-Stack zum ersten Mal
real. Falls sich dort die Wahl als zu schmerzhaft
erweist, schaerft eine Folge-ADR den Vertrag (Schaerfung-
ohne-Supersede per ADR 0011) — entweder durch async-
`Protocol`-Ergaenzung oder durch dedizierten
`AsyncDeviceProtocolPort` als **Schwester-Port**
(eigenstaendiger, parallel-existierender Port mit
eigenem Protocol-Vertrag, beide ueber separate
TickLoop-Kwargs verkabelt).

### 2.2 Decision 3 — Lifecycle um die Caller-getriebene Tick-Schleife (final)

`DeviceProtocolPort.start()` / `stop()` werden durch
explizite `TickLoop`-Methoden gesteuert:
`start_protocol_ports()` startet die konfigurierten
Adapter **vor** dem ersten Caller-`tick()`;
`stop_protocol_ports()` stoppt sie nach dem letzten
Caller-`tick()` oder bei Exception, wenn der Caller den
Tick-Block in `try/finally` wrappt.

Normativer Caller-Scope:

```text
loop.start_protocol_ports()
try:
    for _ in range(ticks):
        loop.tick()
finally:
    loop.stop_protocol_ports()
```

`TickLoop` fuehrt **keine** neue `run(ticks)`-Methode ein.
Die Tick-Granularitaet bleibt beim bestehenden Pattern:
Caller pumpen einzelne Ticks und behalten Kontrolle ueber
Pause/Resume, Snapshot-Zeitpunkte, API-Abbruch und Demo-
Schleifen.

**Begruendung:**

- Adapter-Lifetime == expliziter Run-Scope des Callers,
  nicht Service-Lifetime. Replay-Mode (`ReplaySamplePort`
  als Eingabe) ruft `start_protocol_ports()` nicht auf
  oder uebergibt keine `protocol_ports` — der Replay-Pfad
  laeuft, ohne dass MQTT-Verbindungen oder Modbus-Polls
  aufgemacht werden.
- Konsistenz mit `GG-AR-OPEN-002`-Entscheidung
  ([`ADR 0012`](0012-api-simulation-two-processes.md)):
  der `simulation`-Worker kann mehrere Runs hintereinander
  fahren, ohne dass Protokoll-Verbindungen zwischen
  Runs persistieren.
- Konsistenz mit `GG-SIM-001`/`GG-ARCH-007`: `TickLoop`
  bleibt tick-granular; die Anzahl und Kadenz der Ticks
  bleibt eine Caller-Entscheidung.
- Konsistenz mit dem bestehenden Caller-pumpt-Pattern in
  HTTP-API, MVP-Demo, Tests und Integration: C2 muss keine
  breite Migration auf eine neue Runner-API erzwingen.
- Connect-Latency-Spike am ersten Tick wird durch
  Adapter-internes Lazy-Connect-Pattern + Retry-
  Backoff mitigiert — der `start()`-Call kann
  asynchron Backgrounds aufsetzen, der erste Tick
  blockt nicht zwingend auf die Verbindung.

**Konsequenz:** TickLoop bekommt einen Konstruktor-Kwarg
`protocol_ports: tuple[DeviceProtocolPort, ...] | None =
None` (keyword-only, Default `None` skippt Lifecycle —
Pattern analog ADR 0022 §2.5 `fault_port`-Default).
**Tuple statt Single-Port**, weil Welle 2..5
koexistierende Adapter-Instanzen erwartet (MQTT + Modbus
+ OPC-UA gleichzeitig im selben Run).

**Reihenfolge-Vertrag (Decision 3 normativ):**

- `start()` in **FIFO** (Tuple-Index aufsteigend) —
  Reihenfolge ist deterministisch und steuerbar ueber
  die Tuple-Konstruktion im Caller.
- `stop()` in **LIFO** (Tuple-Index absteigend) — falls
  Adapter N auf Ressourcen von Adapter N-1 angewiesen
  ist (z. B. gemeinsamer Connection-Pool, geteilter
  Bus), wird er **vor** N-1 abgebaut. Standard-
  Lifecycle-Pattern; kostet nichts, wenn Adapter
  unabhaengig sind.

**Partial-Start-Failure-Vertrag (Decision 3 normativ):**

- Wirft `protocol_ports[i].start()` (mit i > 0) eine
  Exception, fuehrt `start_protocol_ports()` **Best-
  Effort-Cleanup** aus: bereits gestartete
  `protocol_ports[0..i-1]` werden in **LIFO**-Reihenfolge
  mit `stop()` abgebaut. Exceptions aus `stop()` waehrend
  Cleanup werden als `__context__` an die Original-Start-
  Exception gehaengt (`raise ... from None` nicht
  verwenden).
- Anschliessend wird die Original-Start-Exception
  propagiert. Der Caller beginnt **nicht** mit dem ersten
  Tick, wenn ein Adapter den `start()` verweigert hat.
- `stop_protocol_ports()` ist idempotent fuer den
  "nichts gestartet"-Fall und stoppt nur Ports, die seit
  dem letzten erfolgreichen `start_protocol_ports()` als
  gestartet markiert wurden.
- Der Caller-`try/finally` deckt den Erfolgs-Pfad und den
  Tick-Exception-Pfad; `TickLoop` kapselt nur FIFO/LIFO und
  Partial-Cleanup, nicht die Tick-Schleife selbst.

### 2.3 Decision 7 — Stateless aus Replay-Sicht (final, reversibel)

`DeviceProtocolPort`-Adapter sind **stateless** aus
Replay-Sicht. Reconnect-State (z. B. Modbus-Read-Cursor,
MQTT-Subscribe-Acks) ist **volatile** und wird **nicht** in
`SnapshotEnvelope` persistiert. `TickLoop.snapshot()` /
`from_snapshot(...)` fuegen **keinen** `protocol_ports`-
Sub-Snapshot-Slot hinzu.

**Begruendung:**

- Replay-Determinismus haengt am `RandomPort`-Seed und
  am `TickLoop`-Sub-Snapshots — nicht am Adapter-
  internen Verbindungs-State.
- Reconnect bei Restart aus Snapshot ist die
  Adapter-Verantwortung (Retry-Backoff aus
  Decision 3-Lazy-Connect-Pattern).
- Snapshot-Schema bleibt `v2` (M3-Welle-6a-Stand);
  kein Bump in M4-Welle-1.

**Snapshot-Restore-Pfad:** wenn ein Run aus
`SnapshotEnvelope` via `from_snapshot(...)` fortgesetzt
wird, ruft der Caller `start_protocol_ports()` der
konfigurierten `protocol_ports` **regulaer wie aus
Cold-Start** auf, bevor er einzelne `tick()`-Aufrufe
pumpt. Es gibt **keinen** gesonderten `from_snapshot()`-
Lifecycle-Pfad fuer Adapter; Reconnect-Logik ist
vollstaendig Adapter-Verantwortung (Retry-Backoff aus
Decision 3-Lazy-Connect-Pattern).

**Konsequenz:** Falls Welle 3+ (Modbus, OPC-UA) zeigt,
dass Adapter-State persistent gebraucht wird (z. B.
Modbus-Holding-Register-Cursor), kann eine Folge-ADR
den Snapshot-Vertrag schaerfen — Schema-Bump v2 → v3
folgt dem ADR-0015-Pattern (additive Sub-Snapshot-Slots,
toleranter Read-Pfad). Welle 1 dokumentiert den
stateless-Default explizit als **reversibel**.

### 2.4 Decision 1 — DNP3 + IEC-61850 Verzicht-Default (provisorisch)

ADR 0030 schreibt den **Verzicht-Default** fuer DNP3 und
IEC 61850 **provisorisch** fest. Die finale Disposition
faellt in M4-Welle 5, informiert durch die
asyncua-Erfahrung aus Welle 4.

**Begruendung:**

- Roadmap §3 M4 DoD erlaubt explizit „dokumentierter
  Verzicht via Out-of-Scope-Note".
- `pydnp3`/`asyncio-iec61850`-Bibliotheken haben
  Lizenz-/Maintenance-Lasten; Test-Sibling-Container
  sind schwer verfuegbar.
- Welle 4 (OPC-UA via asyncua) gibt belastbare
  Erfahrung zur async-Stack-Integration in die sync-
  Surface — diese Erfahrung informiert die Welle-5-
  Entscheidung.

**Konsequenz:**

- Welle 1..4 implementiert keine DNP3/IEC-Adapter.
- Welle 5 entscheidet:
  - (5a) **Verzicht-Anhang** zu dieser ADR (Welle 1
    fuegt §6 als „Verzicht-Anhang-Slot" ein, Welle 5
    fuellt ihn). Kein eigener ADR.
  - (5b) **Spike-Slice** mit reduziertem Scope
    (Read-Pfad-only, ein Profil). Eigener
    M4-Welle-5-ADR.

---

## 3. Alternativen

**A1 (verworfen) — Async-`DeviceProtocolPort`-Surface mit
TickLoop-Sync-Shim:** wuerde alle bestehenden Sync-
Driven-Ports unberuehrt lassen, aber das `TickLoop`-
Innere mit einem Sync->Async-Bridge belasten (z. B.
`asyncio.run_in_executor` oder eigenes `asyncio.run()`-
Pattern um den ganzen Tick-Block). Verworfen, weil der
Kern dadurch eine asyncio-Abhaengigkeit bekaeme, ohne
dass `TickLoop` selbst async profitiert. Sync-Stacks
(`paho-mqtt`, `pymodbus`) muessten ueberdies in einen
async-Wrapper gezwungen werden.

**A2 (verworfen) — Dedizierte sync/async-Schwester-Ports
(`DeviceProtocolPort` + `AsyncDeviceProtocolPort`) ab Welle
1:** wuerde die spaetere Wahl offen halten, aber bereits in
Welle 1 zwei parallele Surface-Vertraege spezifizieren.
Verworfen wegen YAGNI — Welle 4 hat noch keinen
async-Bedarf bewiesen. Wenn er auftritt, schaerft eine
Folge-ADR per ADR-0011-Pattern (Schaerfung-ohne-
Supersedes); Schwester-Port ist dann legitim, weil
Welle-4-Erfahrung die Notwendigkeit konkret zeigt.

**A3 (verworfen) — `TickLoop.run(ticks)` mit internem
Lifecycle:** wuerde den Lifecycle fuer Caller sehr bequem
machen, aber eine zweite TickLoop-Bedienform einfuehren:
`tick()` fuer alte Caller, `run(ticks)` fuer neue Caller.
Verworfen, weil das gegen die bisherige Tick-Granularitaet
aus `GG-SIM-001`/`GG-ARCH-007` driftet und HTTP-API,
MVP-Demo, Tests und Integration breit migriert werden
muessten. Die Lifecycle-Sicherheit wird stattdessen ueber
`start_protocol_ports()` / `stop_protocol_ports()` plus
Caller-`try/finally` erreicht.

**A4 (verworfen) — `TickLoop.protocol_lifecycle()` als
Context-Manager:** waere Python-idiomatisch und wuerde den
Scope sauber ausdruecken (`with loop.protocol_lifecycle():
...`). Verworfen fuer Welle 1, weil kein anderer Driven-
Port am TickLoop aktuell eine eigene Context-Manager-
Konvention hat; `fault_port`/`agent_bus`/Observability-
Hooks bleiben Konstruktor-Kwarg + Hook-Methode/`tick()`-
Pattern.

**A5 (verworfen) — `build_tick_loop()` liefert optionalen
Runner:** ein `TickLoopRunner`-Wrapper koennte `run(ticks)`
besitzen, waehrend roher `TickLoop` rueckwaertskompatibel
bleibt. Verworfen wegen unnoetig breiter Surface: zwei
Klassen mit ueberlappender Verantwortung, obwohl Welle 1
nur FIFO/LIFO-Lifecycle und Partial-Cleanup braucht.

**A6 (verworfen) — Adapter-Lifecycle bei Service-Boot in
`bootstrap`:** wuerde MQTT-/Modbus-Verbindungen
prozess-lebenslang halten, analog `PostgresRunRepository`.
Verworfen, weil Replay-Mode dann zwingend Protokoll-
Verbindungen aufmachen wuerde (oder einen Skip-Flag
braucht) — beides ist Komplexitaet, die die
explizite Caller-Scope-Variante nicht hat.

**A7 (verworfen) — Adapter-Snapshot-Slot in
`SnapshotEnvelope` ab Welle 1 (Default ON):** wuerde
Welle 3+ ohne Schema-Bump erlauben, Reconnect-State zu
persistieren. Verworfen wegen YAGNI — Welle 1 hat keinen
konkreten Beleg, dass Persistenz gebraucht wird; das
ADR-0015-Pattern erlaubt den Bump spaeter, wenn der
Bedarf konkret ist.

---

## 4. Konsequenzen

- **Welle-2+-Adapter-Implementer-Auflage:** alle
  `adapters/driven/protocol_*/`-Module implementieren
  `DeviceProtocolPort` sync. Async-Stacks marshalen
  intern (Adapter-Thread+Queue oder asyncio-Loop-
  Thread). Architektur-Test
  `AC-ADAPTER-LIGHTWEIGHT` greift unveraendert
  (`tools/arch_check.py:1089`).
- **TickLoop-Erweiterung in Welle-1-C2:** neuer
  Konstruktor-Kwarg `protocol_ports` (keyword-only,
  `None`-Default skippt Lifecycle); neue Methoden
  `start_protocol_ports()` / `stop_protocol_ports()`
  kapseln FIFO-Start, LIFO-Stop und Partial-Cleanup.
  Caller wrappen ihre bestehende Tick-Schleife in
  `try/finally`. Pattern analog
  `fault_port`/`agent_bus`/`log_port`-Kwargs aus
  ADR 0022/0023/0024, ohne neue Runner-API.
- **Snapshot-Vertrag bleibt v2 in M4.** Schema-Bump
  v2 → v3 ist Folge-ADR-Material, falls Welle 3+
  Persistenz-Bedarf zeigt.
- **Replay-Mode-Skip:** Replay-Pfad uebergibt
  `protocol_ports=None` (oder leere Tuple) — Adapter-
  Lifecycle laeuft nicht; Telemetry/Commands kommen
  aus `ReplaySamplePort`.
- **DNP3/IEC-Out-of-Scope-Notiz** ist in dieser ADR §2.4
  provisorisch festgehalten; M4-Welle-5 schaerft sie
  final (Anhang oder Spike-ADR).
- **OTel-Span-Wrap** fuer Adapter-Calls ist optionale
  Welle-6-Material (Cross-Adapter-Hardening); ADR 0024
  `TracePort` bleibt der Bezug.
- **Cross-Cutting-Doku-Pflicht** (Lastenheft
  Z. 1161–1163): alle
  `adapters/driven/protocol_*/`-Module dokumentieren
  explizit den **Test-/Simulationscharakter** in
  README oder Modul-Docstring; keine
  Produktivsteuerung-Versprechen. Welle 6 prueft den
  Sweep ueber alle `protocol_*`-Module
  (`M4-protocol-adapters.md §3 Welle 6 Lastenheft-Sync`).

---

## 5. Status-Pfad

- **Proposed** — 2026-05-26 (M4-Welle-1-C1 `b840e7a`).
  Initial-Entwurf. Review-Folge `ad3dff8` (3 High + 4 Medium
  + 5 Low Findings, alle adressiert) und H4-Korrektur
  `111c464` (Decision 3 auf Caller-Scope —
  `TickLoop.run()` existiert nicht, der Caller pumpt
  einzelne Ticks) sind eingearbeitet.
- **Provisional** — 2026-05-30 (M4-Welle-1-C3, dieser
  Commit). M4-Welle-1-C2-Merge `d09adf3` (feat) lieferte
  `src/grid_gym/hexagon/ports/driven/device_protocol.py`
  (Protocol-Surface + `*Error`-Hierarchie) und die
  `TickLoop.start_protocol_ports()` /
  `stop_protocol_ports()`-Methoden (FIFO-Start, LIFO-Stop,
  idempotenter Stop, Best-Effort-Partial-Cleanup mit
  `__context__`-Chain). 23 neue Unit-Tests (1138 → 1161:
  12 Protocol-Surface + 11 TickLoop-Lifecycle). EoD-Sync
  `f8ed791` hat die Top-Level-Doku auf den C2-Stand
  gezogen. `make arch-check` (19/19 Contracts KEPT — 7
  lint-imports + 12 `tools/arch_check.py`; finales
  Gates-Echo: `arch-check (19 contracts)`) und
  `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override.
- **Accepted** — geplant mit M4-Welle-7-Closure
  (analog ADR 0022..0027). Voraussetzung: drei
  produktive Adapter (Welle 2/3/4) implementieren
  die Surface ohne Folge-ADR-Schaerfung, oder die
  Folge-ADR-Schaerfung ist explizit dokumentiert
  (ADR-0011-Pattern).

---

## 6. Verzicht-Anhang-Slot (Decision 1, fuer Welle 5)

Dieser Abschnitt ist in der Welle-1-Version
**Platzhalter** — die Metabeschreibung darunter
beschreibt die zwei moeglichen Welle-5-Fuellungen, der
normative Anhang-Inhalt selbst ist in Welle 1
**inhaltslos**.

Welle 5 fuellt den Anhang entweder mit dem **Verzicht-
Text** (Begruendung Lizenz/Maintenance, Hinweis auf
SOLLTE-Charakter der `GG-DNP3-001`/`GG-IEC-001`-IDs) oder
laesst ihn als Platzhalter und referenziert einen eigenen
Spike-ADR.

Bis Welle 5 gilt: **DNP3 und IEC 61850 sind in M4
out-of-scope**; Lastenheft §16 Z. 1146–1159 bleiben durch
den SOLLTE-Status erfuellt (kein Implementations-Zwang).
