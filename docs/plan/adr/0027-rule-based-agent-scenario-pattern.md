# ADR 0027 — RuleBasedAgent + Scenario-Agents-Block-Pattern (M3 Welle 4b)

**Status:** Provisional — Validierung erfolgt mit M3-Welle-4b-
C2-Merge (`95979e5`) + C2-Review-Folge (`11b2ca9`): 992
Unit-Tests gruen (Welle-4a-Endstand 923 → +65 Welle-4b-
Tests + 4 Review-Folge-Tests), 19 Integration-Tests
(Welle-4a-Endstand 14 → +5 Welle-4b-E2E + Review-Folge),
`make fullbuild` cache-frei gruen **ohne** Override (volle
CI-Linie + Runtime-Image + Compose-Smoke `make ci + make
runtime`); coverage 94.51% line / 90.47% critical-branch;
dep-audit gruen (starlette-Upgrade `ac7b47f`).
Akzeptanz mit M3-Welle-7-Closure (gemeinsam mit ADR 0023 /
ADR 0026 oder einzeln).
**Datum:** 2026-05-22
**Status geaendert am:** 2026-05-22 — `Proposed → Provisional`
mit M3-Welle-4b-C2-Merge (`95979e5`: feat-Commit liefert
RuleBasedAgent + ScenarioAgent + agents-Top-Level-Block-
Validator + `_assert_agent_list` + `_build_agents`-Factory
+ `_AGENT_PLUGIN_FACTORIES`-Hook + agents.<type>.<id>-
Sub-Snapshot + bidirektionaler Resume-Match-Check + 7 neue
Error-Klassen + 65 neue Tests + Demo-Szenario) sowie
C2-Review-Folge `11b2ca9` (Sentinel-Pattern fuer
build_tick_loop-`agents`-Kwarg + Plugin-Restore-Scope-
Schnitt-Doku + SoC-Assertion).
**Geaendert am:** 2026-05-22 — Welle-4b-C1-Review-Folge
(F-1 blocking + F-2 important + F-3..F-6 nits, alle vor
Provisional adressiert):

- §2.1 `sorted(agents.keys())` explizit als **lexikographisch**
  qualifiziert + Zero-Padding-Hinweis (F-3).
- §2.3 Decision-Surface komplett auf **context-basiert**
  umgestellt: Metric-Whitelist `tick` / `simulation_time`
  (statt Bus-Telemetry-Pull, der eine Telemetry-Bridge
  erfordert haette, die Welle 4b nicht liefert) (F-1).
- §2.3 Plugin-Restore-Vertrag praezisiert: Plugin-Snapshot
  ist Single Source of Truth; `params` sind nur fuer
  Construction, nicht fuer Restore (F-2).
- §2.3 Metric-Whitelist-Reject-Error `ScenarioInvalidRule
  MetricError` ergaenzt (F-4); Edge-Case „weder Rules noch
  Plugin" als `ScenarioInvalidAgentParamsError` (F-5);
  YAML-Quoting-Hinweis fuer Comparator + Decimal-Threshold
  ergaenzt (F-6).
- §2.6 Demo-Inhalt auf zeitgesteuerte Phasen (Idle/Charge/
  Discharge per `tick`-Threshold) statt SoC-Reaktion
  umgestellt (F-1-Folge).
- §7 Telemetry-Forwarding-Out-of-Scope-Block expliziter
  mit ADR-0023-§2.1-Forward-Pointer + zwei Resolution-Pfaden
  fuer Welle 4c+.
**Bezug:**
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-
ADR-Pattern — diese ADR schaerft ADR 0026 §6 verbindliche
Welle-4b-Konsequenzen ohne Supersede),
[`ADR 0013`](0013-device-model-protocol.md) §2.4
(`from_snapshot`-Roundtrip-Vertrag — `RuleBasedAgent.snapshot/
from_snapshot` spiegelt das Pattern),
[`ADR 0015`](0015-snapshot-envelope-v2.md) §2.3 (Sub-Snapshot-
Mapping ist erweiterbar; Welle 4b fuegt
`agents.<agent_type>.<agent_id>` additiv ein, ohne v2 → v3-Bump),
[`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
§2.2 (Factory-Dispatch-Pattern — Welle 4b ergaenzt
`_AGENT_FACTORIES` + optional `_AGENT_PLUGIN_FACTORIES`),
[`ADR 0022`](0022-fault-injection-protocol.md) §2.3
(`_assert_fault_list`-Validator-Pattern — Welle 4b spiegelt mit
`_assert_agent_list`),
[`ADR 0023`](0023-agent-bus-protocol.md) §2.1 + §6
(`Agent`-Protocol-Surface; Welle 4b liefert produktiven
Implementer + §6 Verbindlichkeit „Welle 4 schreibt eine eigene
ADR-Folge fuer agents-Top-Level-Block + Sub-Snapshot-Slot"),
[`ADR 0025`](0025-fault-recovery-pattern.md) (Pattern-Pendant:
ADR 0025 = Welle-2-Konkretisierung von Welle-1-ADR 0022;
ADR 0027 = Welle-4b-Konkretisierung von Welle-3-ADR 0023 +
Welle-4a-ADR 0026),
[`ADR 0026`](0026-agent-drain-registry-pattern.md) §2.6 + §6
(Foundation-State-Snapshot + Welle-4b-Pflicht-Konsequenzen),
M3-Slice-Plan
[`in-progress/M3-faults-agents-observability.md`](../planning/in-progress/M3-faults-agents-observability.md)
§3 Welle 4 + Welle-4b-Slice-Doc
[`in-progress/welle-4b.md`](../planning/in-progress/welle-4b.md).
Lastenheft §15 Multi-Agent-System (`GG-AGENT-001..006`); §16
Kommunikationsschnittstellen (`GG-DATA-004` `Command`).
Architektur §6 Datenfluss Tick-Loop (Schritt D2 + A0v/A0a),
§14 Multi-Agent-Subsystem.

---

## 1. Kontext

M3-Welle-4a (`a24f733..da18c6d` + Welle-4a-Review-Folge
`38272f6`) hat die Foundation-Plumbing-Schicht produktiv
abgeschlossen (siehe ADR 0026): TickLoop-`agents`-Konstruktor-
Kwarg + Auto-Bus + `_attach_agents()`-Lifecycle, Schritt-A0v/
A0a-Drain mit Atomizitaets-Vertrag, `AgentMessageBus.
consume_for(receiver)` Direct-Inbox-Drain, Agent-Foundation-
State-Sub-Snapshots (`agent_bus` + `pending_agent_commands`)
und Resume-Match-Checks.

Welle 4a hat **keine** konkreten Agent-Implementer und
**keinen** `agents`-Top-Level-Block im Scenario-Schema —
Welle-4a-Tests pinnen alle Pflicht-Pfade via `_NullAgent` und
`_OrderRecordingAgent`-Stubs. ADR 0026 §6 verlangt fuer
Welle 4b verbindlich:

- `Agent`-Protocol vollstaendig erfuellender Implementer
  (`RuleBasedAgent` o. ae.).
- `agents.<agent_type>.<agent_id>`-Sub-Snapshots additiv per
  ADR 0015 §2.3 (kein Schema-Bump).
- `agents`-Top-Level-Block im Scenario-Schema + Validator
  (`_assert_agent_list`) analog ADR 0022 §2.3.
- `make fullbuild` ohne Override als Welle-4-Abschluss-Gate
  mit Agent-Demo-Szenario.

ADR 0023 §6 Welle-4-Verbindlichkeiten ueberlappen sich
zusaetzlich mit ADR 0026 §6 (RuleBasedAgent + agents-Block +
Sub-Snapshot-Slot). ADR 0027 ist die schwester-ADR zu ADR 0026
und Pattern-Pendant zu ADR 0025 (Welle-2-Konkretisierung von
Welle-1-ADR 0022).

ADR 0027 fixiert die fuenf substantiellen Architektur-
Entscheidungen, die Welle-4b-Code produktiv treffen muss
(geklaert in Welle-4b-C1-Triage 2026-05-22, vgl.
`welle-4b.md §3`).

---

## 2. Entscheidung

ADR 0027 fixiert fuenf Punkte:

### 2.1 `agents`-Top-Level-Block-Schema: nested Mapping

Der `agents`-Block im Scenario-Schema ist ein **nested
Mapping** mit `agent_id` als Schluessel:

```yaml
agents:
  bess-controller:
    type: rule_based
    params:
      target_device_id: battery-1
      rules: [...]
  grid-watcher:
    type: rule_based
    params: {...}
```

**Begruendung (Welle-4b-C1-Triage):**

- **Schema-eindeutige `agent_id`**: Dict-Keys sind by-design
  eindeutig — der Validator muss keinen separaten
  Duplicate-Check fuehren. Die Welle-4a-`AgentDuplicateIdError`-
  Fail-Fast im TickLoop-Konstruktor (ADR 0026 §2.5) bleibt
  produktiv fuer Aufrufer, die das Scenario umgehen
  (Test-Code, direkte Konstruktor-Nutzung).
- **Konsistenz-Bruch zu `devices`/`faults`/`load_events` ist
  beabsichtigt**: Devices/Faults/Events haben eine fachlich
  geordnete Reihenfolge (Konstruktion-Reihenfolge, Schedule-
  Reihenfolge); Agents haben das **nicht** — ihr Verhalten
  ist per `agent_id`-sortierte Iteration deterministisch
  (analog Bus-Sortierung in ADR 0023 §2.2). Die Map-Form
  macht das in der Schema-Definition transparent.
- **Determinismus-Vertrag**: Validator + Loader iterieren
  ueber `sorted(agents.keys())` **lexikographisch** (Python-
  Default-`str`-Sortierung; explizit, damit YAML-Loader-
  spezifische Reihenfolge keine Drift erzeugt — pattern-
  konsistent zu ADR 0023 §2.2 Bus-Sortierung mit
  lexikographischem `sender`-Glied). Welle-4a-TickLoop-
  `agents=tuple[Agent, ...]` ist eine lexikographisch
  sortierte Tuple (nicht insertion-order). Aufrufer, die
  Agent-IDs mit Zahlen mischen, sollten Zero-Padding nutzen
  (`agent-01` statt `agent-1`), falls ihnen natural-order
  wichtig ist; lexikographisch sortiert sich `agent-10` vor
  `agent-2`.

**Welle-3-Pattern-Konsistenz**: AgentMessageBus-Sortierung
ist bereits per `(simulation_time, sender, sequence)`
deterministisch (ADR 0023 §2.2); Agent-Tick-Reihenfolge im
TickLoop folgt der `_agents`-Tuple-Reihenfolge — beide
profitieren von der lexikographisch `sorted(agent_id)`-
Konstruktion.

### 2.2 `ScenarioAgent`-Domain-Klasse + `_assert_agent_list`-Validator

Welle-4b ergaenzt die `hexagon/core/domain/scenario.py`-Familie:

```python
@dataclass(frozen=True, slots=True)
class ScenarioAgent:
    id: str
    type: str
    params: Mapping[str, object]
```

Analog `ScenarioDevice` (Welle 5), `ScenarioFault` (Welle 1),
`ScenarioEvent` (Welle 5). `Scenario`-Top-Level-Domain wird
um `agents: tuple[ScenarioAgent, ...] = ()` erweitert (Default
leer, damit Welle-1..6-Szenarien ohne Agent-Block weiter
gueltig sind).

Validator-Funktion in `scenario/validator.py`:

```python
def _assert_agent_list(
    raw: Mapping[str, object],
    devices: list[Mapping[str, object]],
) -> None:
    """Welle-4b (ADR 0027 §2.2): `agents`-Block (optional)
    valid... Pattern parallel zu `_assert_fault_list`."""
```

**Pflicht-Pruefungen:**

- Top-Level-Sektion `agents` ist optional (default leer);
  fehlt sie, ist der Block leer.
- Wenn vorhanden: muss `Mapping[str, Mapping]` sein
  (`ScenarioWrongTypeError` analog Pattern).
- Pro Eintrag (`agent_id → agent_def`):
  - `agent_id` ist nicht-leerer String.
  - `agent_def` hat Pflicht-Keys `type` (str) + `params`
    (Mapping).
  - `type` ist in der Welle-4b-Factory-Map registriert
    (`ScenarioUnknownAgentTypeError` analog
    `ScenarioUnknownDeviceTypeError`).
  - Wenn `params.target_device_id` vorhanden ist
    (RuleBasedAgent-Pflicht): muss in `devices` existieren
    (`ScenarioUnknownAgentTargetError` analog
    `ScenarioUnknownEventTargetError`).

**Loader-Verdrahtung** in `scenario/loader.py`:

```python
def build_agents(
    scenario_agents: tuple[ScenarioAgent, ...],
    random_root: RandomPort,
) -> tuple[Agent, ...]:
    """Welle-4b (ADR 0027 §2.2): Factory-Dispatch nach
    `ScenarioAgent.type` zu konkreten Agent-Implementern.
    Pattern parallel zu `build_devices(...)` aus Welle 6b."""
```

`build_tick_loop(...)` reicht `build_agents(...)`-Resultat
via Welle-4a-`agents=`-Kwarg in den `TickLoop`-Konstruktor.

### 2.3 `RuleBasedAgent`-Decision-Surface: Hybrid Rules + Plugin-Hook

Der `RuleBasedAgent`-Implementer in `hexagon/core/agents/
rule_based.py` hat zwei Decision-Pfade:

**Default-Pfad — Threshold-Rules-Liste:**

```yaml
params:
  target_device_id: battery-1
  rules:
    - condition:
        metric: simulation_time
        comparator: ">="
        threshold: 10000
      command:
        type: charge
        payload: {power_kw: "50"}
    - condition:
        metric: tick
        comparator: ">="
        threshold: 30
      command:
        type: discharge
        payload: {power_kw: "50"}
```

> **YAML-Quoting-Hinweis**: `comparator`-Werte muessen als
> Strings quoted sein (`comparator: ">="` mit Anfuehrungs-
> zeichen), sonst interpretiert PyYAML `>` als
> Block-Scalar-Indikator. `threshold`-Werte fuer
> Decimal-Felder (siehe Whitelist unten) muessen ebenfalls
> als String quoted sein (`threshold: "20.5"`), damit
> `GG-DATA-005` (kein `float`) eingehalten wird. Int-Felder
> wie `tick` koennen unquoted bleiben.

**Vertrag:**

- Regeln werden als geordnete Liste evaluiert (Scenario-
  Reihenfolge bleibt erhalten — Liste ist eine
  `tuple[RuleBasedRule, ...]`).
- **First-match-wins**: die erste passende Regel emittiert
  den Command; nachfolgende Regeln werden uebersprungen.
- Wenn keine Regel passt: kein Command (leeres
  `Sequence[Command]`-Return).
- **Welle-4b-Metric-Whitelist (context-basiert)**: der
  RuleBasedAgent liest Metric-Werte **ausschliesslich aus
  dem `DeviceTickContext`**, der dem Agent in
  `Agent.tick(context, bus)` uebergeben wird (Welle-4a-
  Protocol-Surface; siehe ADR 0023 §2.1). Welle-4b-zulaessige
  Metric-Namen:
  - `tick` (`int`, 0-basiert; entspricht `context.tick`).
  - `simulation_time` (`int` in ms; entspricht
    `context.simulation_time`).
  Andere `metric`-Namen werden vom Validator typisiert mit
  `ScenarioInvalidRuleMetricError` abgewiesen.

  **Bewusster Welle-4b-Scope-Schnitt**: Decision-Logik
  basiert auf Tick-Counter / Simulation-Zeit, **nicht** auf
  Live-Telemetry (Device-SoC, GridConnection-Power etc.).
  Welle 4b liefert Foundation-Konkretisierung — die Demo
  zeigt End-to-End-Plumbing (`RuleBasedAgent` produziert
  Commands, A0a wendet sie an, Snapshot/Resume ist
  byte-stabil) ohne Telemetry-Bridge.

  Telemetry-basierte Decision-Logik (z. B. Battery-SoC-
  Threshold) erfordert einen Telemetry-Forwarding-Mechanismus
  am AgentMessageBus oder einen `TelemetryQueryPort` (ADR
  0023 §2.1 Forward-Pointer „Welle 4 wird einen optionalen
  TelemetryQueryPort hinzufuegen, falls Decision-Logik
  Live-Telemetry braucht"). Beides ist Welle 4c+ Material
  und bleibt explizit out-of-scope (§7).
- Comparator-Set: `"<"`, `"<="`, `"=="`, `"!="`, `">="`,
  `">"` (deterministische Liste; andere werden mit
  `ScenarioInvalidRuleComparatorError` abgewiesen). Welle 4b
  vergleicht `int`-gegen-`int` (beide Metric-Werte sind
  `int`); spaetere Welle-4c+-Erweiterungen mit Decimal-
  Metrics nutzen denselben Comparator-Set wertbasiert ueber
  `Decimal.__lt__` etc.
- Payload-Werte fuer Decimal-Felder (`power_kw` o. ae.) sind
  Decimal-Strings (kein `float`, `GG-DATA-005`).

**Erweiterungs-Pfad — Plugin-Hook (optional):**

```yaml
params:
  plugin: "custom_decision_v1"
  plugin_params: {...}
```

Bei vorhandenem `plugin`-Key delegiert der `RuleBasedAgent`
seinen `tick(...)`-Decision-Schritt an eine **registrierte
Plugin-Factory**:

```python
_AGENT_PLUGIN_FACTORIES: Final[Mapping[str, Callable[
    [Mapping[str, object]], AgentPlugin
]]] = {
    # Welle 4b ist leer — Plugins sind Welle-4c+-Material.
    # Pattern-Konsistenz zu `_DEVICE_FACTORIES` (ADR 0021 §2.2).
}
```

**Welle-4b liefert KEINE konkreten Plugins** — nur die
Hook-Surface + Factory-Map. Plugins sind Welle 4c+ Material
(z. B. `LearnedPolicyPlugin`, `MPCControllerPlugin` etc.).
Wenn ein Scenario `plugin: "..."` ohne registrierte Factory
nutzt, wirft der Builder `ScenarioUnknownAgentPluginError`
(Fail-fast vor erstem Tick).

**`AgentPlugin`-Protocol** (in `agents/_protocol.py` als
neues `@runtime_checkable`-Protocol):

```python
@runtime_checkable
class AgentPlugin(Protocol):
    def decide(
        self,
        context: DeviceTickContext,
        bus: "AgentMessageBus",
        params: Mapping[str, object],
    ) -> Sequence[Command]: ...

    def snapshot(self) -> Mapping[str, object]: ...

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self: ...
```

Plugin haelt seinen eigenen State (snapshot-bar via Plugin-
selbst-implementierten `snapshot/from_snapshot`-Methoden).
Der `RuleBasedAgent` persistiert das Plugin-State-Mapping
unter `plugin_state` in seinem eigenen Snapshot
(siehe §2.4).

**Plugin-Restore-Vertrag (Welle-4b-Review-Folge F-2,
2026-05-22):** beim Restore via `RuleBasedAgent.from_
snapshot(state)` ist der **Plugin-Snapshot** die einzige
Source-of-Truth fuer den Plugin-Zustand. Aufrufer-Pfad:

1. `plugin_name = state["plugin"]` lesen.
2. Plugin-Klasse aus `_AGENT_PLUGIN_FACTORIES[plugin_name]`
   holen (Modul-Level-Map; analog `_DEVICE_TYPE_BY_CLASS_
   NAME`-Lookup).
3. **`PluginClass.from_snapshot(state["plugin_state"])`
   aufrufen — OHNE Scenario-`plugin_params`.** Das ist
   analog zu `DeviceModel.from_snapshot(state)`: kein
   Scenario-Bezug, alles Notwendige liegt im Snapshot-State.
4. Scenario-`plugin_params` fliessen nur in den **Fresh-
   Start-Pfad** ein (`PluginClass`-Konstruktor oder
   Factory-Function); beim Resume werden sie ignoriert.

Damit gilt: wenn ein Scenario zwischen Snapshot und Restore
veraendert wird (Plugin-Params unterscheiden sich), bleibt
der Resume korrekt — Plugin-State ist authoritative.
Drift-Detection zwischen Scenario und Snapshot ist
**out-of-scope** (Aufrufer-Verantwortung; pattern-konsistent
zu Welle-6a-`TickLoop.from_snapshot`, das auch keine
Cross-Scenario-Drift erkennt).

**Mutual Exclusivity**: ein Agent nutzt **entweder** Rules
**oder** Plugin, nicht beides — wenn beide gesetzt sind,
wirft der Validator `ScenarioInvalidAgentParamsError`.
Begruendung: Hybrid-Reihenfolge (Rules-First-Plugin-Fallback
vs. Plugin-First-Rules-Fallback) waere Quelle stiller
Determinismus-Drift. Welle-4c kann das aufweichen, wenn
ein konkretes Plugin das braucht.

**Edge-Case „weder Rules noch Plugin" (Welle-4b-Review-Folge
F-5):** wenn `params` weder einen `rules`-Block noch einen
`plugin`-Key enthaelt, wirft der Validator
`ScenarioInvalidAgentParamsError` (gleiche Error-Klasse wie
Mutual-Exclusivity-Verstoss; Message unterscheidet die
beiden Faelle). Kein stiller No-op-Agent — produktiver
Agent ohne Decision-Surface ist immer ein Schema-Fehler.

### 2.4 `agents.<agent_type>.<agent_id>`-Sub-Snapshot-Layout

Welle 4b ergaenzt `TickLoop.snapshot()` /
`from_snapshot(...)` um konkrete Agent-Instanz-Sub-Snapshots
(additiv per ADR 0015 §2.3 — kein Schema-Bump v2 → v3).

**Schreib-Pfad** (`TickLoop.snapshot()`):

```python
for agent in self._agents:
    agent_type = _agent_type_for(agent)  # analog _device_type_for
    key = f"agents.{agent_type}.{agent.agent_id}"
    sub_snapshots[key] = agent.snapshot()
```

**Lese-Pfad** (`TickLoop.from_snapshot(...)`):

Resume-Match-Check bidirektional (analog Welle-4a-Review-
Folge `38272f6`): jeder injizierte Agent muss einen Snapshot-
Slot haben, jeder Snapshot-Slot muss einen injizierten Agent
haben. Mismatch wirft `TickLoopAgentInstanceSnapshotMismatch
Error` (neue Error-Klasse in `errors.py`).

**Snapshot-Format** pro `RuleBasedAgent`-Instanz:

```json
{
  "version": 1,
  "agent_id": "bess-controller",
  "target_device_id": "battery-1",
  "rules": [
    {"condition": {...}, "command": {...}},
    ...
  ],
  "plugin": null,
  "plugin_state": null
}
```

Falls Plugin aktiv: `"plugin": "custom_decision_v1"` +
`"plugin_state": {<plugin-internal>}` (Plugin-Snapshot in
Plugin-Verantwortung; `RuleBasedAgent.from_snapshot(...)`
ruft `plugin_factory(params).from_snapshot(plugin_state)`).

**Roundtrip-Vertrag**: `from_snapshot(snapshot())` ist
byte-stabil (ADR 0013 §2.4-Pattern; Property-Test fuer
hypothesis-generierte Rule-Listen).

### 2.5 Welle-4-Abschluss-Gate: `make fullbuild` ohne Override

Welle-4b-C3 verifiziert das Welle-4-Abnahme-Kriterium:

```
make fullbuild
```

ohne `OVERRIDE=…`-Flag muss cache-frei gruen sein. Das Gate
umfasst (Stand 2026-05-22; Auspraegung haengt vom
`fullbuild`-Target-Reifegrad ab):

- Alle A-1-Gates (lint, format-check, mypy `--strict`,
  arch-check, test-unit, test-integration, coverage-gate,
  coverage-gate-critical, dep-audit).
- **Agent-Demo-Szenario-Lauf** ueber `tests/integration/
  scenarios/agents_demo.yaml` (siehe §2.6) als
  Integration-Test, der 60 s Simulationszeit ohne Crash
  durchlaeuft, Telemetry emittiert, einen Snapshot zieht
  und per `from_snapshot(...)`-Roundtrip byte-stabil
  restored.
- Optional (wenn Welle-4-Reife erreicht): Compose-Smoke
  ueber `deploy/compose.yml` mit Agent-Demo-Szenario;
  Trivy-Image-Audit.

**Risiko-Mitigation** (siehe `welle-4b.md §7 R-5`): falls
`make fullbuild` Stage noch nicht voll Compose-Smoke
liefert, reduziert C3 das Gate auf
`make gates A-1 + Agent-Demo-Integration-Test` und
dokumentiert die Compose-Smoke-Pflicht als Welle-5-Forward-
Pointer.

### 2.6 Demo-Szenario-Location: `tests/integration/scenarios/`

`tests/integration/scenarios/agents_demo.yaml` ist die
kanonische Location fuer das Welle-4b-Demo-Szenario.
Pattern-Konsistenz zu `mvp_demo.yaml` und `fault_demo.yaml`;
kein neues Top-Level-`scenarios/`-Verzeichnis (waere
Inkonsistenz zu Welle-6b/Welle-2-Demo-Setup).

**Demo-Inhalt** (geplant, finalisiert in Welle-4b-C2):

- 1 × `PvDevice` (z. B. `pv-1`, 500 kWp).
- 1 × `LoadDevice` (z. B. `load-1`, mit `load_profile`).
- 1 × `BatteryDevice` (z. B. `battery-1`).
- 1 × `GridConnectionDevice` (z. B. `grid-1`).
- 1 × `SmartMeterDevice` (Aggregator).
- 1 × `RuleBasedAgent` (`bess-controller`) mit
  **zeitgesteuerten Threshold-Rules** (siehe §2.3 Welle-4b-
  Metric-Whitelist `tick` / `simulation_time`):
  - Phase 1 (Tick 0..9, simulation_time < 10 s): Idle,
    keine Battery-Commands.
  - Phase 2 (Tick 10..29, simulation_time 10..29 s):
    Charge-Command (`type: charge`, `power_kw: "20"`).
  - Phase 3 (Tick 30..59, simulation_time 30..59 s):
    Discharge-Command (`type: discharge`, `power_kw: "20"`).
- Simulation: 60 s, `tick_ms=1000`, fixer Seed.

Die Demo zeigt End-to-End-Plumbing (Agent emittiert
Commands ueber A0a, Snapshot/Resume ist byte-stabil),
**nicht** echte BESS-Steuerung mit SoC-Feedback. Telemetry-
gesteuerte Decision-Logik (SoC-Threshold etc.) ist Welle-4c+-
Material und braucht einen Telemetry-Forwarding-Mechanismus
am AgentMessageBus oder einen `TelemetryQueryPort` (ADR 0023
§2.1 Forward-Pointer).

---

## 3. Begründung

### 3.1 Nested Schema gewaehlt (vs. flach)

**Pro nested:**

- `agent_id` ist Dict-Key → Schema-Eindeutigkeit erzwingt
  keine separate Validierungs-Logik.
- Map-Form macht klar, dass Agents kein fachlich geordnetes
  Tupel sind (keine Schedule-Reihenfolge wie Events).
- `sorted(agents.keys())`-Iteration im Loader liefert
  deterministische Reihenfolge unabhaengig von YAML-Loader-
  Internals.

**Pro flach (Konsistenz):**

- Existing `devices`/`events`/`faults`/`load_events`/
  `load_profiles` sind alle flache Listen.
- Validator-Pattern (`_assert_device_list`,
  `_assert_event_list`, `_assert_fault_list`) ist auf
  Listen ausgelegt; Mapping braucht neues Pattern.

**Resolution:** Die fachliche Semantik (Map-artige Agents
ohne Schedule-Reihenfolge) ueberwiegt die kosmetische
Konsistenz. Welle-4b-C2 ergaenzt `_assert_agent_list` als
neuen Validator-Pattern mit `sorted(keys)`-Iteration; das
Pattern ist im Code als Mapping-Form klar erkennbar.
Welle 4b dokumentiert die Inkonsistenz als bewusste
fachliche Entscheidung in der Validator-Funktion und im
`welle-4b.md §2`.

**Alternativen ausgeschlossen:**

- **`agents: list[{id, type, params}]` flach mit
  Duplicate-Check im Validator**: redundant zur Welle-4a-
  `AgentDuplicateIdError`-Fail-Fast im Konstruktor; bricht
  die fachliche Map-Semantik.
- **Hybrid `agents: list[{id, type, params}] | Mapping`**:
  Schema-Drift, Validator-Komplexitaet, kein klarer
  Determinismus-Vertrag.

### 3.2 Hybrid Rules + Plugin gewaehlt (vs. Threshold-Map only oder Hook-Callbacks)

**Pro Threshold-Map only:**

- Deterministisch by-construction.
- Snapshot-bar (Daten, nicht Code).
- Property-Test-freundlich (Hypothesis kann Rule-Listen
  generieren).
- YAML-Scenario-spezifizierbar ohne Plugin-Registrierung.

**Pro Hook-Callbacks (Python-Funktionen):**

- Flexibler (beliebige Decision-Logik).
- Bricht Snapshot-Determinismus (Funktion-Identitaeten
  persistieren ist nicht praktikabel).

**Pro Hybrid:**

- **Default-Pfad ist Threshold-Rules** — alle obigen Vorteile.
- **Plugin-Pfad ist Hook fuer Welle-4c+-Erweiterungen**
  (`LearnedPolicy`, `MPCController` etc.) — sauber via
  registrierter Factory mit eigenem Snapshot-Vertrag,
  ohne Determinismus-Bruch (Plugin-Implementer ist fuer
  Determinismus verantwortlich; AC-Test mit `GG-AGENT-003`
  pinnt das).
- **Mutual Exclusivity** (Rules ODER Plugin, nicht beides)
  vermeidet Reihenfolge-Drift.

**Resolution:** Hybrid liefert die Flexibilitaet fuer
spaetere RL-/MPC-Agents (kein Refactor von RuleBasedAgent
in Welle 4c noetig) und behaelt den Welle-4b-Standard-Pfad
(Threshold-Rules) deterministisch und snapshot-bar.

### 3.3 Eigenstaendiges ADR (vs. Decision-Memo)

Pattern-Konsistenz zu ADR 0025 (Welle-2-Recovery-Pattern,
Konkretisierung von Welle-1-ADR 0022) und ADR 0026 (Welle-4a-
Drain-Pattern, Konkretisierung von Welle-3-ADR 0023).
Welle 4b trifft drei substantielle neue Architektur-
Entscheidungen (Schema-Form, Decision-Surface, Sub-Snapshot-
Layout) — rechtfertigt ein eigenstaendiges ADR fuer
Audit-Trail und nachvollziehbare Welle-7-Closure-
Akzeptanz.

Welle-4b-Decision-Memo waere ausreichend gewesen, wenn alle
Decisions in ADR 0023/0026 bereits gefasst — sie sind es
nicht (Schema-Form ist neu; Plugin-Hook ist neu;
Sub-Snapshot-Layout ist neu).

---

## 4. Reichweite

**In Scope (Welle 4b):**

- `hexagon/core/agents/rule_based.py` (NEU) —
  `RuleBasedAgent`-Klasse mit Hybrid Rules + Plugin-Hook.
- `hexagon/core/agents/_protocol.py` — `AgentPlugin`-
  Sub-Protocol (`@runtime_checkable`).
- `hexagon/core/agents/__init__.py` — Re-Exports.
- `hexagon/core/domain/scenario.py` — `ScenarioAgent`-Domain
  + Aufnahme in `Scenario`-Tupel.
- `hexagon/core/scenario/validator.py` —
  `_assert_agent_list(...)` neu.
- `hexagon/core/scenario/loader.py` — `build_agents(...)`
  neu + `_AGENT_FACTORIES` + `_AGENT_PLUGIN_FACTORIES` +
  `build_tick_loop(...)`-Verdrahtung.
- `hexagon/core/simulation/tick_loop.py` —
  `agents.<agent_type>.<agent_id>`-Sub-Snapshot-Schreib- und
  Lese-Pfad + bidirektionaler Resume-Match-Check.
- `hexagon/core/errors.py` — neue Error-Klassen
  (`ScenarioUnknownAgentTypeError`,
  `ScenarioUnknownAgentTargetError`,
  `ScenarioInvalidRuleComparatorError`,
  `ScenarioInvalidRuleMetricError`,
  `ScenarioInvalidAgentParamsError`,
  `ScenarioUnknownAgentPluginError`,
  `TickLoopAgentInstanceSnapshotMismatchError`).
- `tests/unit/hexagon/core/agents/test_rule_based.py` (NEU).
- `tests/unit/hexagon/core/scenario/test_loader_welle_4b.py`
  (NEU oder Aufnahme in bestehende `test_loader_welle_6b.py`).
- `tests/unit/hexagon/core/simulation/test_tick_loop_welle_
  4b_snapshot.py` (NEU).
- `tests/property/test_rule_based_determinism.py` (NEU
  oder Aufnahme in bestehendes Property-Test-Modul).
- `tests/integration/test_agents_demo_e2e.py` (NEU).
- `tests/integration/scenarios/agents_demo.yaml` (NEU).

**Out of Scope (Welle 4c oder spaeter):**

- Konkrete `AgentPlugin`-Implementer (`LearnedPolicy`,
  `MPCController` etc.) — Welle-4b liefert nur die Hook-
  Surface + Factory-Map (leer).
- **`AgentPlugin`-Restore-Pfad in `RuleBasedAgent.from_
  snapshot`** (Welle-4b-Review-Folge F-2, 2026-05-22):
  Welle-4b rekonstruiert nur Rules + `plugin_name` (zur
  Tracking-Persistenz), persistiert aber **nicht** den
  Plugin-Zustand. `self._plugin` und `self._plugin_params`
  bleiben `None`. Welle 4c+ schliesst das durch eine
  erweiterte `from_snapshot`-Surface (Plugin-Factory-
  Injection-Kwarg oder Lookup ueber zentralen Registry-
  Service). Pinning-Test
  `test_plugin_state_is_lost_in_welle_4b_from_snapshot`
  pinnt den Welle-4b-Scope-Schnitt; bidirektionaler
  TickLoop-Resume-Match-Check
  (`_assert_agent_instance_resume_match`) macht jeden
  Plugin-Roundtrip nach Welle-4b-Stand sichtbar
  (`TickLoopAgentInstanceSnapshotMismatchError`).
- `GG-AGENT-005` Priorisierung konkurrierender Agents
  (Welle 4c+; ADR 0023 §7 erlaubt Aufschub).
- `GG-AGENT-007` Deadlines / `GG-AGENT-008` Async
  (M5/ADR-Folge zu ADR 0007).
- Telemetry-Forwarding-Schema im Bus (`message_type=
  "telemetry_metric"` ist Welle-4b-Konvention; produktive
  Telemetry-Subscription-Logik ggf. Welle-4c/Welle-5).
- LogPort/MetricsPort/TracePort-Injektion (Welle 5/6,
  ADR 0024).

---

## 5. Operative Artefakte

- **Tests neu:** ~25-30 (Welle-4a-Endstand 923 → erwartet
  ≥ 950).
- **ADR-Status:** `Proposed → Provisional` mit C2-Merge;
  `Provisional → Accepted` mit M3-Welle-7-Closure (analog
  ADR 0022/0023/0025/0026).
- **Critical-Coverage:** `core/agents/rule_based.py` neu in
  Coverage-Gate-Critical-Liste.
- **Lastenheft-Bezug:** `GG-AGENT-001..006` produktiv erfuellt
  durch Welle-4b-Closure (`GG-AGENT-007/008` bleiben
  Forward-Pointer).
- **Welle-4-Gate**: `make fullbuild` (oder reduzierte
  Variante per §2.5-Mitigation) cache-frei gruen ohne
  Override.

---

## 6. Konsequenzen

**Positive Konsequenzen:**

- Multi-Agent-Subsystem ist auf produktivem Welle-4-Stand —
  Welle 5 (Observability) kann darauf aufbauen.
- Welle-4a-Foundation-Surface (Drain, Registry, Snapshot,
  Lifecycle, Bus-Eviction) ist End-to-End validiert durch
  einen konkreten Implementer.
- Hybrid-Decision-Surface erlaubt Welle-4c+-Plugins
  (RL/MPC) ohne RuleBasedAgent-Refactor.
- Snapshot-Vertrag bleibt ADR-0015-v2-konform (additiv); kein
  Schema-Bump.

**Verbindliche Konsequenzen fuer Welle 4c+ (falls erforderlich):**

- Plugin-Implementer muessen `AgentPlugin`-Protocol-Surface
  vollstaendig erfuellen + Determinismus-Vertrag
  (`GG-AGENT-003`) per Property-Test selbst sichern.
- Multi-Agent-Priorisierung (`GG-AGENT-005`) braucht neue
  ADR-Folge (Welle 4c oder spaeter).
- Telemetry-Forwarding-Schema (Bus `message_type=
  "telemetry_metric"`) ggf. in ADR 0024 (Observability)
  formalisiert.

**Restpost — Snapshot-Schema:**

- ADR 0015 bleibt v2; Welle 4b fuegt nur additive Sub-
  Snapshots ein.
- Snapshot-Bump v2 → v3 bleibt M6-Material (`GG-PERSIST-*`-
  Slice).

**Pflege-Gleichheit:**

- `_DEVICE_FACTORIES`-Pattern als Vorlage fuer
  `_AGENT_FACTORIES` (Scenario-Loader).
- `_DEVICE_TYPE_BY_CLASS_NAME`-Pattern als Vorlage fuer
  `_AGENT_TYPE_BY_CLASS_NAME` (TickLoop, Sub-Snapshot-Key).

---

## 7. Nicht Gegenstand

**Konkrete `AgentPlugin`-Implementer** — Welle 4c+ Material.

**`GG-AGENT-005` Priorisierung konkurrierender Agents** —
ADR 0023 §7 erlaubt Aufschub; Welle 4c+ Material.

**`GG-AGENT-007` Deadlines** — kein Welle-4-Material;
M5/ADR-Folge.

**`GG-AGENT-008` Async-Kommunikation** — kein Welle-4-Material;
ADR-Folge zu ADR 0007 `AsyncRandomPort`.

**Observability-Ports** (`GG-OTEL-001..004`) — Welle 5/6;
ADR 0024.

**Telemetry-Forwarding-Mechanismus** (Live-Telemetry-Zugriff
fuer Agents) — bewusst out-of-scope in Welle 4b:

- ADR 0023 §2.1 Forward-Pointer: „Welle 4 wird einen
  optionalen `TelemetryQueryPort` (oder aequivalent)
  hinzufuegen, falls Decision-Logik Live-Telemetry braucht."
  Welle 4b nimmt diesen Pointer **nicht** auf — der
  RuleBasedAgent operiert auf `context`-Feldern (`tick`,
  `simulation_time`), siehe §2.3 Metric-Whitelist.
- Telemetry-Forwarding-Optionen fuer Welle 4c+ (zwei
  Pfade, Entscheidung dort):
  1. TickLoop-Bridge: TickLoop publiziert Device-Telemetry
     als typisierte `AgentMessage` (z. B.
     `message_type="telemetry_metric"`) auf den
     `AgentMessageBus` nach Schritt D / vor Schritt D2.
     Vorteil: bestehender Bus, kein neuer Port.
  2. `TelemetryQueryPort` als Driven-Port: explizite
     Query-Surface, vom TickLoop oder einem Read-Adapter
     erfuellt. Vorteil: Pull-Modell, kein Bus-Buffer-Druck.
- Schema-Definition (Message-Format, Sub-Snapshot-Slot
  fuer subscribed Metric-Channels o. ae.) ist Welle-4c+-
  ADR-Material.

**Sub-Seed-Wortbreite-Erhoehung** (Trigger 011) — bleibt in
`open/`. Welle 4b mit einem konkreten Agent-Implementer
erreicht das Aktivierungs-Kriterium (`> 10⁶ Sub-Ports`)
nicht; naechste Pruefung mit Multi-Strategien-Pattern
(Welle 4c+) oder M3-Welle-7-Closure.

**Snapshot-Schema-Bump v2 → v3** — additive Sub-Snapshots
reichen (ADR 0015 §2.3). v3-Bump bleibt M6.
