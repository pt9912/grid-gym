# ADR 0076 — Exogen-Input-Recording: Inbound-Write→`Command` als record-only + materialisierbares Szenario

**Status:** Accepted (2026-07-13) — der Determinismus-Nachweis ist belegt: der
erfasste Write-Strom wird materialisiert (`commands`-Block) und **zweimal
byte-identisch** ueber den A0s-Pfad abgespielt, deckungsgleich mit dem „Live"-Lauf
des kommandierten (agenten-freien) Geraets. Status-Pfad (kapazitaetsbasiert,
[`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md) §4,
liefer-agnostisch): Proposed → **Provisional** (Write→`Command`-Naht mit Capture,
erreicht) → **Accepted** (Determinismus-E2E, **erreicht**). Das Delivery-Mapping
(welche Slices die Transitionen liefern) lebt im **ADR-Index + Roadmap**, nicht im
ADR-Body.
**Datum:** 2026-07-13 (Accepted; Provisional 2026-07-13; Proposed 2026-07-12)
**Bezug:**

- [`ADR 0075`](0075-field-server-surface-device-endpoint-port.md) §7 — hat den
  Inbound-Write→`Command`-Pfad aus der Field-Server-Surface **ausgegliedert** und
  auf genau diese Folge-ADR verwiesen. ADR 0076 loest den dort offenen Punkt.
- [`ADR 0070`](0070-scenario-scheduled-device-commands.md) — scenario-scheduled
  Commands: der **Vor-Tick-Command-Pfad** (Schritt A0s) + die **statuslose**,
  resume-sichere Faelligkeits-Ableitung aus `simulation_time`. ADR 0076 nutzt
  genau diesen bereits gepinnten Pfad als Replay-Naht.
- [`ADR 0013`](0013-device-model-protocol.md) — `apply_command` (Command wird
  **vor** `tick()` angewandt; Default last-wins pro Geraet).
- [`ADR 0012`](0012-api-simulation-two-processes.md) — API- und Simulation-
  Prozess getrennt, Kommunikation nur ueber die Persistenz-Bus (kein direktes
  IPC). Relevant fuer den Capture-Transport.
- [`ADR 0030`](0030-device-protocol-port-surface.md) §2.3 — der **reversible**
  Stateless-Default + additive Sub-Snapshot-Slots (Muster
  [`ADR 0015`](0015-snapshot-envelope-v2.md)); das Amendment-Verfahren, falls je
  Live-Run-Cursor-State in den Snapshot muss.
- [`GG-TEST-004`](../../../spec/lastenheft.md#gg-test-004) (HIL, **vollstaendige
  SUT-Steuerbarkeit**) + [`GG-SAFE-007`](../../../spec/lastenheft.md#gg-safe-007)
  (Nur-Sim-Netz).

---

## 1. Kontext

Der Field-Server-`DeviceServerPort` ([`ADR 0075`](0075-field-server-surface-device-endpoint-port.md))
serviert heute **read-only**: ein externes EMS pollt simulierte Geraetewerte. Fuer
die volle HIL/SUT-Steuerbarkeit ([`GG-TEST-004`](../../../spec/lastenheft.md#gg-test-004))
fehlt der **Schreib**-Pfad: ein Master schreibt einen Sollwert (Modbus-Write-
Register/-Coil) → grid-gym soll ihn als `Command` an das Zielgeraet anwenden.

**Warum das ausgegliedert war.** grid-gyms Determinismus-Vertrag ist **geschlossenes
Self-Replay**: ein Lauf ist eine reine Funktion von `(Szenario, Seed, tick_ms)`
(plus Seed-RNG). Ein Live-Master-Write kommt aber zu **Wall-Clock-Zeit** ueber den
Feldbus an — asynchron zum Tick-Loop, in einem eigenen Adapter-Loop-Thread. Auf
welchem Tick er landet, haengt an realem Timing (Thread-Scheduling, Netz-Jitter);
dieser Ankunftszeitpunkt ist **kein** Bestandteil von `(Szenario, Seed, tick_ms)`.
Ein naiver Live-Write bricht damit das geschlossene Self-Replay.

**Bestehende Vor-Tick-Command-Quellen** (die Naht, an die Inbound andocken muss):
`apply_command` laeuft **vor** `tick()`; heute erreichen genau zwei Quellen den
Geraete-Command-Pfad — **scenario-scheduled** (Schritt A0s, faellig iff
`now <= simulation_time < now + tick_ms`, statuslos aus dem Kontext abgeleitet,
[`ADR 0070`](0070-scenario-scheduled-device-commands.md)) und **Agenten** (Schritt
A0a, im Vor-Tick gepuffert, naechsten Tick angewandt). Die Ordnung ist
**scenario vor agent** — externe geplante Inputs zuerst, Agenten reagieren auf den
Folge-Zustand.

---

## 2. Entscheidung

### §2.1 Modell: record-only + Materialisierung (Option B)

Ein Inbound-Write wird **erfasst** und deterministisch **abspielbar gemacht**,
statt einen exogenen Live-Input in den Determinismus-Kern zu bolzen:

1. **Capture** am Adapter-Rand: jeder **angewandte** Write wird als Tupel
   `(aufgeloester_sim_tick, target_device_id, command_type, payload,
   arrival_sequence)` festgehalten.
2. **Materialisierung**: der erfasste Write-Strom wird 1:1 in einen Szenario-
   `commands`-Block ueberfuehrt (ein Inbound-Write mappt strukturgleich auf einen
   scenario-scheduled Command).
3. **Replay** laeuft ueber den **bereits gepinnten Vor-Tick-Pfad A0s**
   ([`ADR 0070`](0070-scenario-scheduled-device-commands.md)): `(Szenario **inkl.
   commands**, Seed, tick_ms)` beschreibt den Lauf vollstaendig → zweimal
   abgespielt **byte-identisch by construction**. Der `scenario_hash` erfasst den
   `commands`-Block bereits.

### §2.2 Ehrlicher Determinismus-Vertrag

Die **Tick-Aufloesung eines Wall-Clock-Arrivals ist die irreduzible Nicht-
Determinismus-Quelle** und wird **nicht versteckt**:

- Der Live-Lauf ist **nicht** aus `(Szenario, Seed, tick_ms)` allein reproduzierbar
  — der Ankunftszeitpunkt ist exogen. Die Capture (der **aufgeloeste** Tick) **ist**
  die Aufzeichnung/Source-of-Truth; ohne sie gibt es keine Reproduktion (das gilt
  fuer jede Recording-Variante, auch fuer ein Journal).
- **Sobald erfasst**, ist der Strom deterministisch: der materialisierte
  `commands`-Block ist eine reine Funktion und replayt byte-identisch.
- Ein Live-Lauf darf darum **nie** als Replay-Referenz dienen; der Determinismus-
  Nachweis erfolgt am **materialisierten** Szenario (zweimal replayen).
- **Alle Laeufe ohne Inbound-Writes bleiben unveraendert** byte-identisch
  (pin-neutral).

### §2.3 Injektion + Ordnung

- Eine additive Vor-Tick-Stufe **A0i** analog A0s/A0a; die Faelligkeit wird
  **statuslos** aus dem materialisierten Strom abgeleitet (Muster
  scenario-command).
- **Ordnung: scenario → agent → inbound.** Der Inbound-Write wird **nach** den
  Agenten aufgeloest, d. h. der Master **ueberschreibt** eine Agenten-Entscheidung
  im selben Tick (last-wins, [`ADR 0013`](0013-device-model-protocol.md)). Das ist
  eine bewusste, tragende Wahl: sie steht in Spannung zu
  [`ADR 0070`](0070-scenario-scheduled-device-commands.md) §2.3 (externe Inputs
  **vor** Agenten), wird hier aber als „HIL-Master hat das letzte Wort" gesetzt und
  in der liefernden Slice-S1-Design-Notiz final gepinnt.
- **Mid-Tick-Arrival**: ein Write, der zwischen `clock.advance` und dem naechsten
  Tick-Rand ankommt, wird **auf den naechsten Tick-Rand** aufgeloest (das
  race-freie, bereits getestete Agenten-Puffer-Muster A0a).
- **Same-Tick-Multiplizitaet / Concurrency**: mehrere Writes (auch von mehreren
  Mastern) auf denselben Tick werden per **`arrival_sequence`** (bei Capture
  vergeben) deterministisch getie-breakt — die Cross-Thread-Ankunftsordnung ist
  selbst nicht-deterministisch und darf nicht die Semantik bestimmen.

### §2.4 Snapshot-Grenze bleibt intakt

Weil die A0i-Faelligkeit **statuslos** aus dem materialisierten `commands`-Block
re-abgeleitet wird (kein Delivered-Set, kein Cursor), muss **nichts** in den
`SnapshotEnvelope` — die [`ADR 0075`](0075-field-server-surface-device-endpoint-port.md)
§2.5-Grenze (Server-State volatil) bleibt gewahrt, **kein** Snapshot-Versions-Bump.
Sollte ein kuenftiger **Live-Run-Resume mitten in einer Session** doch Cursor-/
Dedup-State ueber den Snapshot tragen muessen, ist das ein additiver, **reversibler**
Slot nach dem [`ADR 0030`](0030-device-protocol-port-surface.md) §2.3-Muster
([`ADR 0015`](0015-snapshot-envelope-v2.md)) — nicht Teil dieser Entscheidung.

### §2.5 Prozessgrenze ([`ADR 0012`](0012-api-simulation-two-processes.md))

In der Zwei-Prozess-Topologie lebt der `DeviceServerPort` im **API-Prozess-Driver**,
der `TickLoop` im **Simulation-Worker**; beide kommunizieren nur ueber die
Persistenz-Bus. Die Capture muss darum **den Prozess-Split ueberleben**: sie wird
**append-only, wall-clock-frei, per `run_id`** persistiert (dieselbe Disziplin wie
die Telemetrie-Senke) und dient zugleich als Transport zum Worker. Das kostet einen
Write→Read-Hop, bevor der Tick den Command anwenden kann — bewusst in Kauf genommen,
weil es das [`ADR 0012`](0012-api-simulation-two-processes.md)-Persistenz-Bus-Modell
respektiert statt eine direkte Prozess-Kopplung einzufuehren.

### §2.6 Option-A-Kompatibilitaet (additiv nachruestbar)

Das Capture-Format (§2.1) ist **identisch** zu dem, was ein Write-Journal (Option A,
Runtime-Re-Injektion unter der **originalen** `run_id`) braeuchte. A ist damit
**spaeter ohne Rework** als Runtime-Konsument derselben Aufzeichnung nachruestbar.
A wird **nur** gezogen, wenn ein harter Bedarf entsteht: (a) Audit-/Forensik-Re-Run
unter der originalen `run_id` (statt eines abgeleiteten Szenarios), oder (b)
Re-Injektion beim Resume mitten in einer laufenden Live-Session.

### §2.7 Sim-/Test-Charakter + Sicherheit

Ein **beschreibbarer** Feldbus ohne Auth erweitert die Angriffsflaeche gegenueber
Read-Serving. Der Write-Pfad ist — wie die ganze Field-Server-Surface — **Nur-Sim-
Netz** ([`GG-SAFE-007`](../../../spec/lastenheft.md#gg-safe-007)); keine produktive
Anlagensteuerung. Der Sim-/Test-Charakter steht im Adapter-Docstring.

---

## 3. Begruendung

- **Der Determinismus-Kern bleibt unangetastet.** B bolzt keinen Exogen-Input-
  Pfad in `(Szenario, Seed, tick_ms)`; es macht die Aufzeichnung ueber die schon
  gepinnte scenario-command-Naht replaybar. Das geschlossene Self-Replay gilt
  unveraendert fuer alle Bestands-Laeufe.
- **Maximale Wiederverwendung, minimale neue Flaeche.** B nutzt A0s, die statuslose
  Faelligkeit, die `scenario_hash`-Abdeckung von `commands` und **keinen** Snapshot-
  Bump. Der Determinismus-Nachweis faellt **by construction**.
- **A liefert im Kern dieselbe Garantie zu hoeheren Kosten.** Auch A macht den
  Live-Lauf nicht aus dem Nichts reproduzierbar — es replayt die **Aufzeichnung**.
  Der Mehrwert (originale `run_id`, Mid-Session-Resume) ist real, aber
  spezialisiert; ihn vorzuziehen hiesse neuen Port + Migration + Replay-Engine fuer
  einen Bedarf zu bauen, der heute nicht besteht. B haelt A additiv offen.
- **Ehrlichkeit ueber die Grenze.** Der Vertrag benennt die irreduzible
  Nicht-Determinismus-Quelle (Tick-Aufloesung des Arrivals) explizit, statt eine
  „byte-identisch"-DoD-Formulierung sie verdecken zu lassen.

---

## 4. Alternativen

- **(A) Write-Journal + Runtime-Re-Injektion (verworfen als primaer):** neuer
  driven `WriteJournalPort` + Persistenz-Migration + Replay-Modus-Engine; replayt
  unter der originalen `run_id`. Verworfen als Standard, weil ~gleiche Garantie bei
  deutlich groesserer Flaeche; **additiv nachruestbar** (§2.6), nicht dauerhaft
  ausgeschlossen.
- **Read-only belassen (verworfen):** kein Schreib-Pfad. Verworfen — verfehlt die
  volle SUT-Steuerbarkeit aus [`GG-TEST-004`](../../../spec/lastenheft.md#gg-test-004).
- **Live-Write direkt in den laufenden Tick ohne Recording (verworfen):** braeche
  das geschlossene Self-Replay ersatzlos und macht Laeufe mit Inbound
  nicht-reproduzierbar — genau der Grund der Ausgliederung.

---

## 5. Lieferschnitt (kapazitaetsbasiert)

Design-first (diese ADR), dann **liefer-agnostisch** in zwei Kapazitaets-
Inkrementen (welche Slices sie liefern, steht im ADR-Index + Roadmap):

1. **Write→`Command`-Naht + Capture:** die Adapter-seitige Uebersetzung
   (Modbus-Write → `Command`), die A0i-Vor-Tick-Stufe mit Next-Tick-Aufloesung +
   `arrival_sequence`, und die append-only/wall-clock-freie Capture-Persistenz.
   → zieht die ADR auf `Provisional`.
2. **Determinismus-E2E:** den erfassten Strom materialisieren + ueber A0s zweimal
   abspielen → byte-identisch; Ordnung scenario→agent→inbound belegt. → zieht die
   ADR (mit Closure) auf `Accepted`.

Jedes Inkrement traegt Akzeptanzkriterien, Verifikationspfad und Release-Feld im
liefernden Slice; die Verifikation (`make gates`/`make docs-check`/`make
fullbuild`) lebt in dessen Closure.

---

## 6. Konsequenzen

- **Positiv:** volle HIL-Steuerbarkeit ([`GG-TEST-004`](../../../spec/lastenheft.md#gg-test-004)),
  **ohne** dass grid-gyms Determinismus bricht; Nachweis by construction ueber den
  gepinnten A0s-Pfad; kein Snapshot-Bump.
- **Positiv:** additive Vor-Tick-Quelle; Laeufe ohne Inbound bleiben byte-identisch.
- **Neutral:** neue Capture-Persistenz (per `run_id`, Muster Telemetrie-Senke) + die
  A0i-Stufe; ein Write→Read-Hop ueber die Prozessgrenze.
- **Bewusste Grenze:** der **Live-Lauf** ist nicht self-reproduzierbar (nur die
  Aufzeichnung ist es); Re-Run unter originaler `run_id` + Mid-Session-Resume-Re-
  Injektion sind auf eine spaetere Option-A-Erweiterung (§2.6) vertagt.

---

## 7. Nicht Gegenstand dieser ADR / offene Punkte

- **Ordnungs-Semantik + Materialisierungs-Grenze (gepinnt).** Live gilt
  scenario→agent→inbound (A0i **nach** A0a): der Inbound-Write **verdraengt** eine
  agenten-erzeugte Command desselben Ticks/Geraets (last-wins) — belegt in
  `test_tick_loop_inbound_commands.py` (`test_pre_tick_command_order_is_scenario_
  then_agent_then_inbound`). **Folge fuer die Materialisierung:** ein Inbound-Write
  wird in den `commands`-Block = **A0s** = **vor** den Agenten materialisiert. Fuer
  ein Ziel **ohne** Agent im selben Tick ist der Replay damit **byte-treu** (A0s ==
  Live-A0i-Effekt) — belegt in `test_inbound_write_determinism_e2e.py`.
  Kommandiert ein Agent dasselbe Ziel im selben Tick, wuerde der Replay den Agenten
  **nach** dem materialisierten Inbound anwenden (Agent gewinnt) → Divergenz zum
  Live-Lauf (Inbound gewinnt). Das ist eine **bewusste, akzeptierte Modell-B-
  Grenze** (HIL+Agent-auf-gleichem-Ziel/Tick ist heute kein realer Bedarf); eine
  A0i-treue Materialisierung waere Option-A-Territorium (§2.6, additiv nachruestbar).
- **Option A** (Write-Journal, Runtime-Re-Injektion, originale `run_id`) — §2.6:
  additiv nachruestbar, hier bewusst nicht geliefert.
- **Auth/Autorisierung** auf dem Write-Pfad — out of scope; Nur-Sim-Netz
  ([`GG-SAFE-007`](../../../spec/lastenheft.md#gg-safe-007)).
- **Nicht-`float32`/Nicht-Register-Write-Typen** (Coils, andere Protokolle) — die
  ADR fixiert das Modell, nicht die Encoding-Matrix je Protokoll.
