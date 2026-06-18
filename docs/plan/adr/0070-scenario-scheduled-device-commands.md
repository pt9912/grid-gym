# ADR 0070 — Scenario-Scheduled Device Commands: `commands`-Block + ScenarioCommandEngine (Provisional)

**Status:** Provisional — Owner traegt die Empfehlung mit (S0, full-Mechanismus-
Mandat; [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md) §2); die
Validierung laeuft ueber S1..S3 des
[`in-progress`-Slice-Plans](../planning/in-progress/scenario-scheduled-device-commands.md).
`Accepted` folgt bei der Implementierungs-Wellen-Closure (gates gruen); bis dahin
bleibt der Entwurf schaerfbar — offener Platzierungs-Punkt (§2.1 top-level vs.
nested) ist begruendet entschieden, aber noch **kein** immutable Beschluss.
**Datum:** 2026-06-18
**Status geaendert am:** 2026-06-18 — `Proposed → Provisional` (S0; Owner-
Mittragung des Voll-Mechanismus statt der schlanken Agents-Deckung).
**Bezug:**

- [`ADR 0022`](0022-fault-injection-protocol.md) + [`ADR 0059`](0059-generic-scenario-fault-engine.md) —
  die tick-genaue **Fault-Planung** (`faults`-Block + `ScenarioFaultEngine`) ist
  das strukturelle Template; diese ADR zieht den analogen Command-Pfad ein
  (kein Supersedes, Pattern [`ADR 0011`](0011-schaerfung-ohne-abloesung.md)).
- [`ADR 0013`](0013-device-model-protocol.md) §2.3 — `apply_command`-Vertrag +
  Command-Reihenfolge aus der Scenario-Source; hier um eine **scenario-getriebene**
  Quelle erweitert (bisher nur Agents/Inline).
- [`ADR 0027`](0027-rule-based-agent-scenario-pattern.md) — der bestehende
  Agents/Rules-Command-Pfad; bewusste Abgrenzung (§3).
- [`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md) — Loader- +
  TickLoop-Event-Verdrahtung (optionale Top-Level-Bloecke, pin-neutral default);
  das `commands`-Schema + die Engine-Naht setzen genau hier an.
- [`ADR 0051`](0051-fault-engine-location-and-naming.md) — Placement-/Naming-
  Konvention der Scenario-Engines (Vorbild fuer `ScenarioCommandEngine`).
- [Trigger 046](../planning/open/046-command-driven-integration-e2e.md) —
  der aufloesende Trigger (Command-E2E der SOLLTE-Geraete).

---

## 1. Kontext

Jedes SOLLTE-Geraet ([`GG-DEV-015`](../../../spec/lastenheft.md#gg-dev-015)..018)
implementiert `apply_command` ([`ADR 0013`](0013-device-model-protocol.md)), aber
die vier Szenario-Smokes fahren **idle**: der `devices`-Layer kennt **keinen**
scenario-scheduled-Command-Mechanismus. Faults werden tick-genau geplant
(`faults`-Block → [`ScenarioFaultEngine`](0059-generic-scenario-fault-engine.md) →
`TickLoop` Schritt A2), Commands nicht. Commands erreichen `apply_command` heute
nur ueber zwei Quellen:

- **Agents** (`rule_based`, [`ADR 0027`](0027-rule-based-agent-scenario-pattern.md)):
  `agents.<name>.rules[*].action` → `_pending_agent_commands` → `TickLoop`-Schritt
  A0a (`_apply_pending_agent_commands`) → `device.apply_command`.
- **Inline Load-Overlay** (`load_events`/`load_profiles`) — direkte Calls, keine
  `Command`-Objekte.

Die generische Command-Routing-Mechanik ist damit gedeckt; es fehlt der
**geraetespezifische, scenario-deklarierte** E2E-Pfad „Command kommt via Szenario
rein → SOLLTE-Geraet reagiert sichtbar im Snapshot".

## 2. Decision

### 2.1 Schema — optionaler Top-Level-`commands`-Block

Ein optionaler Top-Level-`commands`-Block, **strukturell analog zu `faults`**
(beide Top-Level, beide zielen auf ein `target`-Device):

```yaml
commands:
  - simulation_time: 5000        # ms; zugestellt am Tick, dessen Span simulation_time enthaelt
    target: "ev-1"               # device_id
    type: "set_charge_power"
    payload: { value: "20" }     # Decimal-als-String (Variante A — canonical_json verbietet float)
```

**Punkt-in-der-Zeit** (kein `duration_ms` wie bei Faults): ein Command wird genau
**einmal** am geplanten Tick zugestellt (kein Fenster, kein Recovery).

**Top-level statt nested im `devices`-Block** (begruendete Wahl): spiegelt `faults`
1:1 → einheitlicher Loader-/Validator-/`canonical_json`-/Hash-Pfad, und die
Geraete-Definition bleibt rein deklarativ (keine eingebettete Zeitreihe). Die
Trigger-046-Formulierung „im `devices`-Block" meint *an die Geraete gerichtete*
Commands, nicht eine YAML-Verschachtelung. (Nested-per-Device als Alternative in
§3 verworfen.)

### 2.2 Domain — `ScenarioCommand` + `Scenario.commands`

`ScenarioCommand` (frozen dataclass, analog `ScenarioFault`):
`simulation_time: int`, `target: str`, `type: str`, `payload: Mapping[str, object]`.
NEU optionales Feld `Scenario.commands: tuple[ScenarioCommand, ...] = ()` (Default
leer, analog `agents`/`load_events` — **pin-neutral** fuer alle Bestands-Szenarien).
Loader: `_build_commands`/`_build_command` analog `_build_faults`/`_build_fault`.
Validator-Strang fuer den `commands`-Block analog dem `faults`-Strang.

### 2.3 ScenarioCommandEngine + TickLoop-Naht

`ScenarioCommandEngine` ([`ADR 0051`](0051-fault-engine-location-and-naming.md)-
Naming) haelt die geplanten Commands und liefert pro Tick die **faelligen**
`Command`-Objekte: `due_commands(context) -> Sequence[Command]` — jene, deren
`simulation_time` in den aktuellen Tick-Span faellt. Jeder `ScenarioCommand` →
ein [`Command`](../../../src/grid_gym/hexagon/core/domain/command.py)
(`command_id="scenario-cmd-<i>"`, `target_device_id=target`, `type`, `payload`,
`validation_status="scenario"`).

`TickLoop`-Naht: eine neue Vor-Tick-Stufe (analog Fault-Schritt A2) speist die
faelligen Commands in den **bestehenden** Apply-Pfad
(`_device_by_id[target].apply_command`, wie `_apply_pending_agent_commands`).
**Determinismus-Reihenfolge** (festzulegen, [`ADR 0013`](0013-device-model-protocol.md) §2.3):
scenario-Commands werden in Scenario-Source-Reihenfolge zugestellt und laufen
**vor** den Agent-Commands desselben Ticks (scenario-Commands sind externe
geplante Inputs wie Faults; Agents reagieren auf den dadurch entstandenen
Zustand). Nicht-existentes `target` → typisierter Loader-/Validierungs-Fehler
(kein Silent-Drop).

### 2.4 Canonical / Hash / Determinismus

`commands` ist Teil von `Scenario` → automatisch in
`canonical_json(asdict(scenario))` → **`scenario_hash`**. Payload-Werte sind
Decimal-als-String (Variante A; `canonical_json` verbietet `float`). Determinismus
([`GG-SIM-001`](../../../spec/lastenheft.md#gg-sim-001)/004,
[`GG-MVP-002`](../../../spec/lastenheft.md#gg-mvp-002)-Replay): gleicher
`scenario_hash` + Seed → identischer Command-Zeitplan → byte-identische Telemetrie.
**Pin-neutral**: Szenario ohne `commands` → leeres Tupel → Hash unveraendert →
Bestands-Pins (inkl. die vier SOLLTE-Idle-Smokes) bit-genau gueltig.

### 2.5 E2E-Scope (S3, schliesst Trigger 046)

Je SOLLTE-Geraet ein **nicht-idle** Integration-E2E (Command via `commands`-Block
geplant → Snapshot-Assertion):

- **EV-Charger**: `set_charge_power` → `power_kw` springt am geplanten Tick (+ SoC
  bewegt sich); `set_plug_state` optional.
- **Transformer**: `set_power_kw` → `primary_power_kw`.
- **Diesel**: `set_power_kw` (>=0) → `power_kw`/`running`.
- **Wind-Turbine**: nimmt **keine** Commands ([`ADR 0057`](0057-wind-turbine-device-pattern.md)
  §2.1 → `apply_command` = `CommandResult.IGNORED`). E2E belegt: Command wird via
  Zeitplan zugestellt, Wind **ignoriert** ihn (`power_kw` bleibt wettergetrieben) —
  positiver Beleg der `IGNORED`-Semantik.

## 3. Verworfene Alternativen

- **Nested `commands:` pro Device-Definition** — bricht die `faults`-Analogie,
  verteilt Zeitplan-Logik in die Geraete-Bloecke, erschwert Validator/Canonical
  (heterogene Device-Schemata). Verworfen zugunsten Top-Level (§2.1).
- **Nur Agents/Rules-Deckung** (schlanker Pfad) — deckt die `apply_command`-
  Integrations-Luecke, liefert aber **nicht** den scenario-deklarierten
  `devices`-Command-Mechanismus, den Trigger 046 als Closure-Kriterium fordert.
  Vom Owner zugunsten des Voll-Mechanismus verworfen.

## 4. Konsequenzen

- NEU: `commands`-Schema + `ScenarioCommand` + Loader + `ScenarioCommandEngine` +
  `TickLoop`-Naht + 4 SOLLTE-E2E (Slice-Plan S1..S3).
- `scenario_hash` deckt jetzt `commands` ab (additive, default-leere Erweiterung).
- Out-of-Scope: bedingte/konditionale Commands (nur tick-geplant), Command-Result-
  Rueckkopplung ins Szenario, Runtime-API-Command-Injektion (Agents/API-Pfad),
  Recovery/Fenster-Semantik (Punkt-in-der-Zeit).
