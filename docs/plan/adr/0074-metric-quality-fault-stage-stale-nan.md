# ADR 0074 — Scenario-Fault-getriebene, metrik-adressierte Quality-Fault-Stage (`STALE`/`NAN`-Emitter) fuer GG-FAULT-002/003

**Status:** Accepted — gezogen 2026-07-11 mit Slice 071 / [`GG-FAULT-003`](../../../spec/lastenheft.md#gg-fault-003)-Lieferung
(NaN-Injection = Foundation + NaN-Verhalten). Der Last-Value-Cache +
`stale_data`-Emitter ([`GG-FAULT-002`](../../../spec/lastenheft.md#gg-fault-002)) folgt mit Slice B.
Owner-Sign-off 2026-07-11 (Design-first-Beschluss).
**Datum:** 2026-07-11
**Bezug:**

- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — Lifecycle-/Status-Pfad.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung-ohne-
  Supersedes-Pattern (Form-Anker; ADR 0074 aktiviert additiv die von
  [`ADR 0052`](0052-max-age-stale-quality-stage.md) §7 und
  [`ADR 0053`](0053-comm-failure-wrapper-missing-quality-alarm.md) §7
  ausdruecklich reservierten Folge-Scopes; kein bestehender Vertrag wird
  abgeloest).
- [`ADR 0022`](0022-fault-injection-protocol.md) — Fault-Injection-Protokoll
  (`FaultPort` + `FaultInjectableDevice`); ADR 0074 fuehrt einen
  **parallelen, metrik-adressierten** Quality-Fault-Pfad ein, der den
  device-adressierten Physik-Fault-Pfad **nicht** beruehrt.
- [`ADR 0025`](0025-fault-recovery-pattern.md) — Fault-Recovery-Fenster
  (`start ≤ now < start+duration`, idempotent); die Quality-Stage nutzt
  dieselbe Fenster-Semantik.
- [`ADR 0040`](0040-alarm-aggregation-and-stream-port.md) — `Alarm`-Domain +
  Severity-Konvention; ADR 0074 ergaenzt einen stabilen Alarm-Code ohne
  Schema-Change.
- [`ADR 0052`](0052-max-age-stale-quality-stage.md) — `max_age`-`STALE`-
  Quality-Stage im Spine; ADR 0074 ist ihr **scenario-fault-getriebenes,
  metrik-adressiertes Geschwister** und aktiviert die dort (§7) reservierten
  Scopes „per-Metric-Schwellen" + „`Quality.NAN`-Emitter".
- [`ADR 0053`](0053-comm-failure-wrapper-missing-quality-alarm.md) — Comm-
  Failure-`MISSING`-Quality + Alarm; ADR 0074 aktiviert die dort (§2.3/§7)
  reservierte „`STALE`-Variante mit Last-Value-Cache".
- [`ADR 0059`](0059-generic-scenario-fault-engine.md) — generischer
  `ScenarioFaultEngine`; bleibt fuer Physik-Faults zustaendig, Quality-Faults
  laufen den parallelen Spine-Pfad.
- [`GG-DATA-003`](../../../spec/lastenheft.md#gg-data-003) — `Quality`-Enum
  (Werte inkl. `stale`/`nan` bestehen als Forward-Compat); die kanonische
  Serialisierung (`serialization/canonical.py`, `NonFiniteDecimalError`)
  reserviert `quality = "nan"` bereits als **einzige** NaN-Darstellung.

---

## 1. Kontext

Zwei MUSS-Anforderungen ohne dedizierten Fault-Typ (aufgedeckt in der
GG-FAULT-Konsolidierungs-Investigation; `make doc-trace` meldete 0 Waisen und
verbarg die Luecke):

- [`GG-FAULT-002`](../../../spec/lastenheft.md#gg-fault-002) (Stale Data,
  MUSS): „Ein Stale-Data-Fault kann fuer ein Ziel und eine Metrik aktivieren,
  dass der letzte gueltige Wert weitergeliefert wird, bis `max_age`
  ueberschritten ist. Danach wird der Qualitaetsstatus `stale` gesetzt."
- [`GG-FAULT-003`](../../../spec/lastenheft.md#gg-fault-003) (NaN-Injection,
  MUSS): „Ein NaN-Fault kann fuer ein Ziel und eine Metrik einen nicht
  numerischen Eingangswert erzeugen. Der Wert wird nicht ungeprueft in den
  Geraetezustand uebernommen, sondern mit Qualitaetsstatus `nan` und Alarm
  protokolliert."

Beide adressieren ein **(Ziel, Metrik)**-Paar und manipulieren den
**Qualitaetsstatus emittierter Telemetrie** — kein Geraete-Physik-Effekt wie
[`GG-FAULT-004`](../../../spec/lastenheft.md#gg-fault-004)/[`GG-FAULT-005`](../../../spec/lastenheft.md#gg-fault-005)
(`frequency_drop`/`voltage_drop`).

**Code-Ist-Stand (verifiziert, C0-Investigation):**

- `Quality.STALE`/`Quality.NAN` existieren als Forward-Compat-Enum-Werte
  (`hexagon/core/domain/quality.py`), **ohne** scenario-fault-getriebenen
  Emitter. `QUALITY_SEVERITY` rankt `STALE`=3, `NAN`=6.
- `TelemetryPoint` traegt `metric`, `value: Decimal`, `quality: Quality`,
  `simulation_time: int` — alle Vergleichs-/Ziel-Groessen vorhanden, **kein
  neues Domain-Feld** noetig, um Punkte zu markieren.
- [`ADR 0052`](0052-max-age-stale-quality-stage.md) markiert `STALE` ueber
  eine **globale** `max_age_ms`-`TickLoop`-Stage — **nicht** scenario-fault-
  getrieben, **nicht** per-Metric, und **ohne** Wert-Weiterlieferung (kein
  Last-Value-Cache).
- [`ADR 0053`](0053-comm-failure-wrapper-missing-quality-alarm.md) §2.3/§7
  hat den Last-Value-Cache **bewusst abgelehnt** („bei konkretem Bedarf").
- `serialization/canonical.py` weist `Decimal("NaN")`/`Decimal("Infinity")`
  hart ab (`NonFiniteDecimalError`); die Fehler-Docstring + [`GG-DATA-003`](../../../spec/lastenheft.md#gg-data-003)
  reservieren `quality = "nan"` als **einzige** NaN-Darstellung. [`ADR 0052`](0052-max-age-stale-quality-stage.md)
  §7 fuehrt den „`Quality.NAN`-Emitter" als eigenen, noch offenen Scope.
- `ScenarioFault` (`hexagon/core/domain/scenario.py`) ist **device-
  adressiert**: `target` = Device-ID, **kein `metric`-Feld**; `payload:
  Mapping[str, object]` flieszt Engine → `device.inject_fault(type, payload)`.
  Der `ScenarioFaultEngine` ([`ADR 0059`](0059-generic-scenario-fault-engine.md))
  loest `target` zu einem `FaultInjectableDevice` auf und mutiert **Physik-
  State** — es gibt keinen Geraete-Pfad, der die Quality emittierter Punkte
  setzt (Devices emittieren unbedingt `quality=Quality.VALID`).
- **Hash-Pin-Kopplung:** `scenario_hash = sha256(canonical_json(asdict(
  scenario)))` — ein **neues `Scenario`-Dataclass-Feld** flippt den Hash
  **aller** Szenarien (`EXPECTED_DEMO_SCENARIO_HASH` +
  `EXPECTED_DEMO_TELEMETRY_STREAM_HASH`, `make accept`-Gate). Ein **neuer
  Fault-Typ-Wert** flippt nur den Hash von Szenarien, die ihn deklarieren —
  das Demo nutzt ihn nicht.

---

## 2. Entscheidung

ADR 0074 fixiert sieben Punkte fuer den metrik-adressierten Quality-Fault-Pfad.

### §2.1 Neue Fault-Typen + Metrik-Targeting via `payload` (kein Pin-Bruch)

NEU `FAULT_TYPE_STALE_DATA = "stale_data"` und `FAULT_TYPE_NAN_INJECTION =
"nan_injection"` als Single Source in `hexagon/core/domain/fault.py`; Re-Export
in `hexagon/core/faults/types.py`.

- Die **Metrik** und die Parameter reisen im **`payload`**:
  `stale_data` → `{"metric": <str>, "max_age_ms": <int > 0>}`;
  `nan_injection` → `{"metric": <str>}`.
- **BEWUSST KEIN `ScenarioFault.metric`-Schema-Feld:** ein Feld wuerde den
  `asdict`-basierten `scenario_hash` **aller** Szenarien flippen (Pin-Bruch,
  §1) — exakt die [`ADR 0052`](0052-max-age-stale-quality-stage.md) §2.1-
  Begruendung: „fuer ein Ziel und eine Metrik" bindet an **Konfigurierbarkeit**,
  nicht an einen Szenario-Datei-Standort. Die Metrik im `payload` ist canonical-
  kompatibel (`str`) und aendert nur den Hash von Szenarien, die den Fault
  deklarieren (Demo unberuehrt).
- **Validator-Schaerfung** (`hexagon/core/scenario/validator.py`): fuer
  `type ∈ {stale_data, nan_injection}` MUSS `payload` ein `metric: str`
  tragen; `stale_data` zusaetzlich `max_age_ms: int > 0`. `target` bleibt die
  existenz-gepruefte Device-ID (bestehende `ScenarioUnknownFaultTargetError`-
  Pruefung). Fehlende/fehltypisierte Payload-Schluessel → typisierter
  Validator-Fehler (kein stiller Unsinn).

### §2.2 Naht: neue Scenario-Fault-getriebene Quality-Stage im Spine

NEU `_apply_quality_fault_stage` in `TickLoop.tick()`, **Geschwister** von
`_apply_max_age_stage` ([`ADR 0052`](0052-max-age-stale-quality-stage.md) §2.2),
laeuft auf der gesammelten `emitted`-Liste **unmittelbar vor** dem
`TickResult`-Bau.

- **NICHT `device.inject_fault`:** Impedanz-Mismatch — das Geraet re-emittiert
  unbedingt `quality=VALID`, hat keinen Metrik-Quality-Pfad und keinen Last-
  Value-Cache. Quality-Semantik gehoert in den Spine ([`GG-AR-P-003`](../../../spec/architecture.md#2-architekturprinzipien),
  [`ADR 0052`](0052-max-age-stale-quality-stage.md) §2.2): eine Stelle, drei
  Konsumenten (Stream/Persistenz/Replay).
- Der device-adressierte `ScenarioFaultEngine` bleibt fuer **Physik-Faults**
  zustaendig; `stale_data`/`nan_injection` sind **nicht** in seinen
  `supported_types` und laufen den **parallelen** Spine-Pfad. Ein
  `QualityFaultRuntime` (spine-intern, pro Lauf konstruiert) haelt die aktiven
  Quality-Faults und den Last-Value-Cache (§2.3) und den Alarm-Transitions-
  State (§2.5).
- **Aktive-Fenster-Semantik identisch** zum Physik-Engine ([`ADR 0025`](0025-fault-recovery-pattern.md)):
  `start_simulation_time ≤ now < start_simulation_time + duration_ms`. Die
  Stage rewritet fuer jeden aktiven Quality-Fault die matchenden Punkte in
  `emitted` (`point.device_id == fault.target` **und** `point.metric ==
  payload["metric"]`) via `dataclasses.replace` (frozen+slots gewahrt; `source`/
  `sequence` unberuehrt → Scheduler-Tie-Breaking unangetastet).

### §2.3 STALE-Verhalten + Last-Value-Cache (GG-FAULT-002)

Der `QualityFaultRuntime` fuehrt einen deterministischen per-`(device_id,
metric)`-**Last-Valid-Value-Cache** `(value, simulation_time)`.

- **Cache-Update:** liegt fuer `(device_id, metric)` **kein** aktiver
  `stale_data`-Fault an und ist der Punkt `Quality.VALID`, wird `(value,
  simulation_time)` gecacht (der „letzte gueltige Wert").
- **Aktiver `stale_data`-Fault** auf `(device_id, metric)`: der emittierte
  Punkt-Wert wird durch den gecachten Last-Valid-Wert **ersetzt**
  (weitergeliefert). Solange `(now - cached_simulation_time) ≤ max_age_ms`
  bleibt die Quality unveraendert (Wert eingefroren, aber gueltig); sobald
  `(now - cached_simulation_time) > max_age_ms` (strikt `>`, [`ADR 0052`](0052-max-age-stale-quality-stage.md)
  §2.5-Grenzsemantik) → `quality = Quality.STALE`.
- **Kein Cache-Eintrag vorhanden** (Fault ab Tick 0 aktiv, nie ein gueltiger
  Vorwert): der Punkt wird **nicht** wert-ersetzt, aber ab `max_age`-
  Ueberschreitung `STALE` markiert (ehrliche Grenze: ohne gueltigen Vorwert
  gibt es nichts weiterzuliefern).
- Dieser Last-Value-Cache ist die von [`ADR 0053`](0053-comm-failure-wrapper-missing-quality-alarm.md)
  §7 reservierte additive Schaerfung — [`GG-FAULT-002`](../../../spec/lastenheft.md#gg-fault-002) ist der konkrete Bedarf.
- **Determinismus:** Cache-Key `(device_id, metric)`; nur **Sim-Zeit**
  (`AC-NO-TIME`); deterministische Fault-Iteration (Szenario-Reihenfolge). Der
  Cache ist Runtime-State und wird **opt-in im `TickLoop`-Snapshot**
  serialisiert (§2.7) — leer/abwesend wenn keine Quality-Faults → byte-
  identisch; nicht-leer, damit Snapshot/Resume mitten in einem aktiven Stale-
  Fenster den letzten gueltigen Wert nicht verliert.

### §2.4 NAN-Verhalten + Versoehnung mit der NaN-Reject-Policy (GG-FAULT-003)

Aktiver `nan_injection`-Fault auf `(device_id, metric)`: der emittierte Punkt
traegt einen **endlichen Sentinel** `Decimal("0")` (Praezedenz [`ADR 0053`](0053-comm-failure-wrapper-missing-quality-alarm.md)
§2.6 `MISSING`-Point) **plus** `quality = Quality.NAN`.

- Der **reale Geraetewert wird nicht uebernommen** — das Geraet bleibt
  unberuehrt (nur der emittierte Punkt wird ersetzt), erfuellt „nicht
  ungeprueft in den Geraetezustand uebernommen".
- **Versoehnung mit M2-Trigger-014 / `canonical.py`:** **kein** numerischer
  NaN betritt die Domaene — `NonFiniteDecimalError` (`Decimal("NaN")` verboten)
  bleibt **unangetastet**. `quality = "nan"` ist die von der `canonical.py`-
  Docstring + [`GG-DATA-003`](../../../spec/lastenheft.md#gg-data-003) bereits
  reservierte Darstellung. ADR 0074 ist damit der **erste `Quality.NAN`-
  Emitter**, den [`ADR 0052`](0052-max-age-stale-quality-stage.md) §7 als
  eigenen Scope reserviert hat — eine additive Aktivierung, keine Reversierung.

### §2.5 Alarm-Vertrag (NAN Pflicht; STALE kein Alarm)

- [`GG-FAULT-003`](../../../spec/lastenheft.md#gg-fault-003) fordert einen
  Alarm; [`GG-FAULT-002`](../../../spec/lastenheft.md#gg-fault-002) fordert
  **nur** `quality=stale` (**kein** Alarm — konsistent mit [`ADR 0052`](0052-max-age-stale-quality-stage.md)
  §7 „Alarm-Emission bei `STALE`" als eigenem [`GG-SAFE-003`](../../../spec/lastenheft.md#gg-safe-003)-Scope).
- Pro `nan_injection`-Fault genau **ein** `Alarm`, gehoben **einmal beim
  `inactive → active`-Uebergang** (nicht pro Tick — sonst Alarm-Flut). Der
  `QualityFaultRuntime` trackt den Transitions-State (wie der Physik-Engine).

| Feld | Wert |
| --- | --- |
| `code` | `"quality_fault_nan_injection"` (NEU, stabiler Code; Muster `grid_fault_*` / `adapter_communication_lost`) |
| `severity` | `"warning"` ([`ADR 0040`](0040-alarm-aggregation-and-stream-port.md) §2.1; `critical` bleibt Command-Reject) |
| `target` | `<device_id>` (Ziel) |
| `simulation_time_ms` | `now` (Sim-Zeit, `AC-NO-TIME`) |
| `message` | `"nan injection on metric <metric>"` (Ursache, maschinenlesbar) |
| `status` / `fault_id` | `"active"` / `None` |

- **Emissions-Pfad:** ein neuer Raw-Alarm-Typ (analog `GridConnectionFaultAlarm`)
  wird von der Stage in den Spine-Alarm-Kanal (`TickResult.emitted_alarms`)
  gehoben und via neuem Mapper in `dispatch_alarm_mapper`
  (`hexagon/core/simulation/alarm_mappers.py`) auf den Unified `Alarm`
  gemappt (Dispatch fail-fast bei unbekanntem Typ, [`ADR 0053`](0053-comm-failure-wrapper-missing-quality-alarm.md)
  §2.4-Muster).

### §2.6 Severity-Override-Regel + Determinismus

`NAN` (Severity 6) und `STALE` (3) ersetzen nur Punkte mit **niedrigerer**
Severity (bestehendes `QUALITY_SEVERITY`-Ranking, [`ADR 0052`](0052-max-age-stale-quality-stage.md)
§2.3) — kein Informationsverlust ueber schwerere Befunde (`INVALID`(5),
`MISSING`(7) bleiben). Die Alterspruefung vergleicht ausschliesslich
Simulationszeit gegen Simulationszeit (`AC-NO-TIME`; Replay-stabil).

### §2.7 Demo-Wiring aus + Snapshot opt-in → byte-identisch

Das Demo-Szenario nutzt **keine** Quality-Faults → die Stage ist no-op → kein
Verhaltens-/Stream-Hash-Delta (`make accept`-Pins + `scenario_hash` unberuehrt).
Der Last-Value-Cache-Snapshot-Anteil (§2.3) ist **opt-in** (leer/abwesend ohne
aktiven Quality-Fault → byte-identisch, Muster Slice 070 `frequency_drop`-
Snapshot-Opt-in) — **kein** Snapshot-Versions-Bump.

---

## 3. Begruendung

- **Spine statt Device ([`GG-AR-P-003`](../../../spec/architecture.md#2-architekturprinzipien)).**
  Quality-Manipulation emittierter Telemetrie ist eine zentrale Prozessor-
  Aufgabe (eine Pruefstelle fuer Stream/Persistenz/Replay), kein Geraete-
  Physik-Effekt; der device-adressierte Fault-Pfad kann sie strukturell nicht
  ausdruecken.
- **Metrik im `payload`, kein Schema-Feld.** Vermeidet den `scenario_hash`-
  Pin-Bruch bei voller Metrik-Adressierung ([`ADR 0052`](0052-max-age-stale-quality-stage.md)
  §2.1-Linie).
- **Schaerfung ohne Ablösung ([`ADR 0011`](0011-schaerfung-ohne-abloesung.md)).**
  ADR 0074 aktiviert **exakt** die von [`ADR 0052`](0052-max-age-stale-quality-stage.md)
  §7 und [`ADR 0053`](0053-comm-failure-wrapper-missing-quality-alarm.md) §7
  reservierten Folge-Scopes; kein bestehender Vertrag wird abgeloest oder
  textlich geaendert (Index-Cross-Refs sind mutable Living-Index-Pflege).
- **NaN versoehnt statt reversiert.** Der endliche Sentinel + `quality=NAN`
  respektiert die stehende „NaN nie numerisch in der Domaene"-Policy
  (`canonical.py` unangetastet) und liefert zugleich die von [`GG-DATA-003`](../../../spec/lastenheft.md#gg-data-003)
  vorgesehene Darstellung.

---

## 4. Reichweite

Geliefert ueber die liefernden Slices (§5); ADR 0074 fixiert die Architektur,
nicht die Slice-Buchhaltung.

- NEU Fault-Typ-Konstanten (`hexagon/core/domain/fault.py`) + Re-Export
  (`hexagon/core/faults/types.py`).
- NEU Validator-Payload-Schaerfung (`hexagon/core/scenario/validator.py`).
- NEU `QualityFaultRuntime` + `_apply_quality_fault_stage` im TickLoop-Spine
  (`hexagon/core/simulation/tick_loop.py`) + `build_tick_loop`-Verdrahtung
  (`hexagon/core/scenario/loader.py`).
- NEU Raw-Alarm-Typ + Mapper (`hexagon/core/simulation/alarm_mappers.py`).
- Opt-in Snapshot-Anteil fuer den Last-Value-Cache (§2.3/§2.7).
- HTTP-Fault-Whitelist + `_KNOWN_FAULT_TYPES` (produktiver
  `ScenarioFaultEngine`-Demo-Setup) erweitert, damit die neuen Typen als
  bekannt gelten (kein „unbekannter Fault-Typ"-Reject).
- NEU Unit-Tests unter `tests/unit/hexagon/core/simulation/` +
  `tests/unit/hexagon/core/scenario/`.
- ADR-Index NEU 0074-Zeile + Folge-ADR-Cross-Refs in den 0052-/0053-Zeilen
  (`docs/plan/adr/README.md`, mutable Living-Index).
- `docs/plan/traceability.md` §27.3 [`GG-FAULT-002`](../../../spec/lastenheft.md#gg-fault-002)/[`GG-FAULT-003`](../../../spec/lastenheft.md#gg-fault-003); `CHANGELOG.md`.
- **Unberuehrt:** `Quality`-Enum + `QUALITY_SEVERITY` (nur konsumiert),
  `TelemetryPoint`-Domain, `ScenarioFault`-Schema + `scenario_hash`-Pfad,
  `serialization/canonical.py` (NaN-Reject bleibt), device-adressierter
  `ScenarioFaultEngine`/Physik-Faults, Demo-Wiring, `make accept`-Pins.

---

## 5. Lieferung

Owner-Beschluss 2026-07-11: **Design-first**, dann liefern in zwei Slices, die
sich die Foundation teilen:

- **Slice A — [`GG-FAULT-003`](../../../spec/lastenheft.md#gg-fault-003)
  (NaN-Injection):** bringt die Foundation (Konstanten, Validator-Schaerfung,
  `QualityFaultRuntime` + Spine-Stage, Alarm-Raw-Typ + Mapper) und das
  einfachere Verhalten (Sentinel + `quality=NAN` + Alarm, **ohne** Cache). Zieht
  ADR 0074 auf `Accepted`.
- **Slice B — [`GG-FAULT-002`](../../../spec/lastenheft.md#gg-fault-002)
  (Stale Data):** setzt den Last-Value-Cache + `max_age`-Weiterlieferung + den
  opt-in Snapshot-Anteil obenauf.

Jede Slice traegt Akzeptanzkriterien, Verifikationspfad und Release-Feld; die
Verifikation (`make gates`/`make docs-check`/`make doc-trace`) lebt in der
jeweiligen Slice-Closure.

---

## 6. Konsequenzen

- **Positiv:** [`GG-FAULT-002`](../../../spec/lastenheft.md#gg-fault-002) +
  [`GG-FAULT-003`](../../../spec/lastenheft.md#gg-fault-003) werden von echten
  Feature-Luecken (RTM verbarg sie) zu belegten, testgetriebenen Deliverables;
  `Quality.STALE`/`NAN` erhalten ihren ersten scenario-fault-getriebenen
  Emitter.
- **Positiv:** eine Stage, drei Konsumenten — Stream/Persistenz/Replay sehen
  identisch markierte Punkte.
- **Neutral:** der Core haelt einen weiteren spine-internen Runtime (`Quality
  FaultRuntime`); ohne Quality-Faults ist er inert und byte-identisch.
- **Neutral (Replay alt/neu):** Laeufe mit Quality-Faults erzeugen gegenueber
  Vor-0074-Referenzen andere Quality-/Value-Werte — kein realer Bruch (der
  `GG-TERM`-Preflight vergleicht nur konfigurationsgleiche Laeufe; Demo aus).
- **Bewusste Grenze:** kein gueltiger Vorwert → keine Wert-Weiterlieferung, nur
  `STALE`-Markierung ab `max_age` (§2.3).

---

## 7. Nicht Gegenstand dieser ADR

- **`ScenarioFault.metric`-Schema-Feld** — additive [`ADR 0011`](0011-schaerfung-ohne-abloesung.md)-
  Schaerfung mit bewusstem Pin-Update, falls je eine schema-verankerte
  Metrik-Adressierung gefordert wird (§2.1).
- **Alarm bei `STALE`** — [`GG-SAFE-003`](../../../spec/lastenheft.md#gg-safe-003)-Scope ([`ADR 0052`](0052-max-age-stale-quality-stage.md)
  §7); [`GG-FAULT-002`](../../../spec/lastenheft.md#gg-fault-002) verlangt nur die Markierung.
- **Quality-gewichtete Netzbilanz** — die Bilanz bleibt quality-agnostisch
  ([`ADR 0052`](0052-max-age-stale-quality-stage.md) §2.2); Markierung ≠
  Filterung.
- **Weitere Quality-Emitter** (`ESTIMATED`/`LIMITED`) — eigene Scopes bei
  Bedarf.
- **Metrik-Fan-out ueber alle Metriken eines Ziels** — der Fault adressiert
  genau eine Metrik; ein „alle Metriken"-Faecher ist additive Folgearbeit.
