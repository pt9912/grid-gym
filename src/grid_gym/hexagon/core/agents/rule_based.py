"""`RuleBasedAgent` — produktiver Agent-Implementer (M3 Welle 4b, ADR 0027).

`RuleBasedAgent` ist der erste konkrete `Agent`-Implementer
oberhalb der Welle-4a-Foundation-Plumbing-Schicht (ADR 0026).
Welle 4b liefert eine Hybrid-Decision-Surface mit zwei
Pfaden (ADR 0027 §2.3):

- **Default-Pfad — Threshold-Rules-Liste**: deterministische,
  context-basierte Regeln (Welle-4b-Metric-Whitelist `tick`,
  `simulation_time`). First-match-wins, leeres
  `Sequence[Command]`-Return bei keinem Match.
- **Erweiterungs-Pfad — Plugin-Hook (optional)**: delegiert
  Decision an einen registrierten `AgentPlugin`. Welle 4b
  liefert keine konkreten Plugins; Welle 4c+ kann z. B.
  `LearnedPolicyPlugin` einbringen.

Welle-4b-Scope-Schnitt: kein Live-Telemetry-Pull. Decision-
Logik ist context-basiert (`tick` / `simulation_time` aus
`DeviceTickContext`). Telemetry-getriebene Decision-Logik
(Battery-SoC-Threshold u. ae.) braucht einen Telemetry-
Forwarding-Mechanismus, der Welle 4c+ Material ist (ADR 0027
§7, ADR 0023 §2.1 `TelemetryQueryPort`-Forward-Pointer).

Mutual Exclusivity (ADR 0027 §2.3): ein Agent nutzt entweder
Rules oder Plugin, nicht beides. Validator erzwingt das per
`ScenarioInvalidAgentParamsError` (siehe `scenario/validator.py`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, Self

from grid_gym.hexagon.core.agents._protocol import AgentPlugin
from grid_gym.hexagon.core.agents.bus import AgentMessageBus
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext

_SNAPSHOT_VERSION: Final[int] = 1
"""RuleBasedAgent-Snapshot-Schema-Version (ADR 0027 §2.4)."""

WELLE_4B_METRIC_WHITELIST: Final[tuple[str, ...]] = ("tick", "simulation_time")
"""ADR 0027 §2.3: zulaessige Metric-Namen in Welle 4b.

Welle-4b-Decision-Surface ist context-basiert; Telemetry-
basierte Metrics (SoC u. ae.) sind Welle 4c+ Material und
erfordern einen Telemetry-Forwarding-Mechanismus."""

COMPARATOR_WHITELIST: Final[tuple[str, ...]] = ("<", "<=", "==", "!=", ">=", ">")
"""ADR 0027 §2.3: deterministischer Comparator-Set."""


class RuleBasedAgentInvariantError(RuntimeError):
    """Konstruktor-/Validator-Invariante verletzt (Slice 027 Paket E).

    Wird in defensiven Guards verwendet, an denen der ADR-0027-Validator
    eigentlich garantiert, dass ein Wert gesetzt ist. Ein Treffer
    bedeutet einen Bug im Validator-Pfad — nicht ein normaler Aufrufer-
    Fehler.
    """


class _MissingTargetDeviceIdError(RuleBasedAgentInvariantError):
    """`target_device_id` ist None, obwohl der Validator es garantiert.

    Message-Bildung in `__init__` (Codebase-Konvention; verhindert TRY003
    am Aufruferort).
    """

    def __init__(self) -> None:
        super().__init__(
            "RuleBasedAgent.target_device_id ist None, obwohl der Validator "
            "es im Rules-Pfad garantiert (ADR 0027 §2.3)."
        )


def _required_target_device_id(target: str | None) -> str:
    """Typisierter Guard fuer Konstruktor-Vertrag aus ADR 0027 §2.3.

    Ersetzt das frueher dort stehende `assert target is not None`
    (Slice 027 Paket E, S101-Drop). Der Validator garantiert das per
    Konstruktor-Pfad; falls der Vertrag bricht, ist das ein Bug —
    typisierte Exception statt `AssertionError`.
    """
    if target is None:
        raise _MissingTargetDeviceIdError
    return target


@dataclass(frozen=True, slots=True)
class RuleCondition:
    """Bedingungs-Vertrag fuer eine `RuleBasedAgent`-Regel
    (ADR 0027 §2.3).

    - `metric` ist der Context-Feld-Name (`tick`/`simulation_time`
      in Welle 4b).
    - `comparator` ist ein String aus `COMPARATOR_WHITELIST`.
    - `threshold` ist `int` (Welle 4b vergleicht int-gegen-int;
      Welle 4c+ kann Decimal-Thresholds ergaenzen).
    """

    metric: str
    comparator: str
    threshold: int


@dataclass(frozen=True, slots=True)
class RuleAction:
    """Command-Template fuer eine `RuleBasedAgent`-Regel
    (ADR 0027 §2.3).

    Das produktive `Command` wird beim Match aus `type` +
    `payload` + dem aktuellen `context.simulation_time` +
    `target_device_id` der Agent-Instanz konstruiert.
    """

    type: str
    payload: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class Rule:
    """`RuleBasedAgent`-Regel mit Bedingung + Aktion
    (ADR 0027 §2.3 First-match-wins)."""

    condition: RuleCondition
    action: RuleAction


class RuleBasedAgent:
    """Konkreter `Agent`-Implementer mit Hybrid Decision-Surface
    (M3 Welle 4b, ADR 0027 §2.3).

    Konstruktor-Vertrag — Mutual Exclusivity:
    - **Rules-Pfad**: `target_device_id != None` UND
      `rules != ()` UND `plugin is None`.
    - **Plugin-Pfad**: `plugin is not None` UND
      `rules == ()` UND `target_device_id is None`.

    Verstoesse werden bereits vom Scenario-Validator typisiert
    abgewiesen (`ScenarioInvalidAgentParamsError`); der
    Konstruktor verlaesst sich auf vorgelagerte Validierung.
    """

    def __init__(  # noqa: PLR0913 — Hybrid Rules + Plugin-Pfad-Konstruktor mit Mutual Exclusivity (ADR 0027 §2.3); kein sauberer Split-Pfad ohne Vertrags-Bruch.
        self,
        *,
        agent_id: str,
        target_device_id: str | None = None,
        rules: tuple[Rule, ...] = (),
        plugin: AgentPlugin | None = None,
        plugin_name: str | None = None,
        plugin_params: Mapping[str, object] | None = None,
    ) -> None:
        self._agent_id: str = agent_id
        self._target_device_id: str | None = target_device_id
        self._rules: tuple[Rule, ...] = rules
        self._plugin: AgentPlugin | None = plugin
        self._plugin_name: str | None = plugin_name
        self._plugin_params: Mapping[str, object] | None = (
            dict(plugin_params) if plugin_params is not None else None
        )
        self._run_id: str = ""

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def target_device_id(self) -> str | None:
        """Welle-4b-Public-Sicht. Wird in Rules-Pfad fuer Command-
        Konstruktion benutzt; im Plugin-Pfad `None`."""
        return self._target_device_id

    @property
    def rules(self) -> tuple[Rule, ...]:
        return self._rules

    @property
    def plugin(self) -> AgentPlugin | None:
        return self._plugin

    @property
    def plugin_name(self) -> str | None:
        return self._plugin_name

    def set_run_id(self, run_id: str) -> None:
        """Welle-4a-Lifecycle-Hook (ADR 0026 §2.3). Wird vom
        TickLoop-Konstruktor via `_attach_agents()` aufgerufen."""
        self._run_id = run_id

    def tick(
        self,
        context: DeviceTickContext,
        bus: AgentMessageBus,
    ) -> Sequence[Command]:
        """Agent-Tick (Welle-4a-Protocol-Surface, ADR 0023 §2.1).

        Welle-4b-Behavior:
        - Plugin-Pfad: delegiert an `self._plugin.decide(...)`.
        - Rules-Pfad: First-match-wins ueber `self._rules`,
          emittiert maximal **einen** Command pro Tick.
        - Kein Match / Plugin-leer-Return: leere Sequenz.

        Bus-Parameter wird in Welle 4b nur an Plugins durchgereicht;
        Rules-Pfad liest **nicht** vom Bus (siehe ADR 0027 §2.3
        Welle-4b-Metric-Whitelist).
        """
        if self._plugin is not None:
            params = self._plugin_params if self._plugin_params is not None else {}
            return tuple(self._plugin.decide(context, bus, params))
        for rule in self._rules:
            if _condition_matches(rule.condition, context):
                command = self._command_for_rule(rule, context)
                return (command,)
        return ()

    def _command_for_rule(self, rule: Rule, context: DeviceTickContext) -> Command:
        """Baut einen `Command` aus einem gematchten `Rule`-Eintrag.

        `command_id` ist deterministisch aus `agent_id` + `tick` +
        `rule_index` abgeleitet (Welle-4a-Pattern fuer
        Auto-Close-Commands).
        """
        # target_device_id wird im Rules-Pfad immer gesetzt; per
        # Konstruktor-Vertrag (Validator erzwingt das). Slice 027
        # Paket E ersetzt das `assert` durch einen typisierten Guard.
        target = _required_target_device_id(self._target_device_id)
        rule_index = self._rules.index(rule)
        return Command(
            command_id=f"rule_based_{self._agent_id}_tick_{context.tick}_rule_{rule_index}",
            simulation_time=context.simulation_time,
            target_device_id=target,
            type=rule.action.type,
            payload=dict(rule.action.payload),
            validation_status="validated",
            result=CommandResult.IGNORED,
        )

    def snapshot(self) -> Mapping[str, object]:
        """RuleBasedAgent-Snapshot (ADR 0027 §2.4).

        Format:

        ```json
        {
          "version": 1,
          "agent_id": "<id>",
          "target_device_id": "<id>" | null,
          "rules": [...],
          "plugin": "<name>" | null,
          "plugin_state": {...} | null
        }
        ```

        Plugin-Pfad persistiert das Plugin-Snapshot als
        `plugin_state` (Plugin-eigene `snapshot()`-Surface).
        """
        rules_serialized: tuple[Mapping[str, object], ...] = tuple(
            {
                "condition": {
                    "metric": rule.condition.metric,
                    "comparator": rule.condition.comparator,
                    "threshold": rule.condition.threshold,
                },
                "action": {
                    "type": rule.action.type,
                    "payload": dict(rule.action.payload),
                },
            }
            for rule in self._rules
        )
        plugin_state: Mapping[str, object] | None = (
            self._plugin.snapshot() if self._plugin is not None else None
        )
        return {
            "version": _SNAPSHOT_VERSION,
            "agent_id": self._agent_id,
            "target_device_id": self._target_device_id,
            "rules": rules_serialized,
            "plugin": self._plugin_name,
            "plugin_state": plugin_state,
        }

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:  # noqa: PLR0915 — pro-Feld-typed-Errors fuer 6 Pflichtfelder + Rules-Sub-Mapping; Pattern-Konsistenz zu TickLoop-_restore_pending_command_entry.
        """Rekonstruiert `RuleBasedAgent` aus seinem Snapshot.

        **Welle-4b-Plugin-Restore-Scope-Schnitt** (ADR 0027 §2.3
        + §7 Welle-4b-Review-Folge F-2, 2026-05-22):

        Welle 4b liefert die **Hook-Surface** + Factory-Map
        (Welle-4b leer); konkrete `AgentPlugin`-Implementer und
        damit auch der Plugin-Restore-Pfad sind explizit
        **Welle 4c+ Material**. `from_snapshot(...)` rekonstruiert
        Rules + `plugin_name` (zur Tracking-Persistenz im
        Snapshot), persistiert aber **nicht** den Plugin-Zustand
        — `self._plugin` bleibt `None`, `self._plugin_params`
        bleibt `None`.

        Konsequenz fuer Plugin-Snapshots: `agent.snapshot()` vor
        und nach `from_snapshot(snapshot())` weicht ab
        (`plugin_state: {...}` → `plugin_state: null`). Bei
        TickLoop-Resume mit `_assert_agent_instance_resume_match`
        wuerde das einen `TickLoopAgentInstanceSnapshotMismatchError`
        triggern, sobald ein Plugin produktiv verwendet wird.
        Welle 4c+ wird das durch eine erweiterte
        `from_snapshot`-Surface schliessen (z. B. Plugin-Factory-
        Injection-Kwarg oder Plugin-Lookup ueber zentralen
        Registry-Service).

        Welle-4b-Tests (siehe `test_rule_based.py`) decken den
        Plugin-Roundtrip-Loss explizit ab, damit der Welle-4c+-
        Trigger sichtbar ist.

        Strukturelle Pruefungen (Welle-0a-Codec-Pattern):
        Pflicht-Keys + Typ-Match per Helper-Funktionen.
        """
        version = state.get("version")
        if version != _SNAPSHOT_VERSION:
            from grid_gym.hexagon.core.errors import VersionError

            raise VersionError("rule_based_agent", _SNAPSHOT_VERSION, version)
        agent_id_raw = state.get("agent_id")
        if not isinstance(agent_id_raw, str):
            from grid_gym.hexagon.core.errors import WrongTypeError

            raise WrongTypeError("rule_based_agent", "agent_id", "str", type(agent_id_raw).__name__)
        target_raw = state.get("target_device_id")
        target: str | None
        if target_raw is None:
            target = None
        elif isinstance(target_raw, str):
            target = target_raw
        else:
            from grid_gym.hexagon.core.errors import WrongTypeError

            raise WrongTypeError(
                "rule_based_agent",
                "target_device_id",
                "str | None",
                type(target_raw).__name__,
            )
        rules_raw = state.get("rules", ())
        if not isinstance(rules_raw, Sequence) or isinstance(rules_raw, (str, bytes)):
            from grid_gym.hexagon.core.errors import WrongTypeError

            raise WrongTypeError("rule_based_agent", "rules", "Sequence", type(rules_raw).__name__)
        rules: tuple[Rule, ...] = tuple(_rule_from_mapping(entry) for entry in rules_raw)
        plugin_raw = state.get("plugin")
        plugin_name: str | None
        if plugin_raw is None:
            plugin_name = None
        elif isinstance(plugin_raw, str):
            plugin_name = plugin_raw
        else:
            from grid_gym.hexagon.core.errors import WrongTypeError

            raise WrongTypeError(
                "rule_based_agent", "plugin", "str | None", type(plugin_raw).__name__
            )
        # Plugin-Instanz-Restore wird vom Aufrufer (Scenario-Loader)
        # durchgefuehrt — siehe Klassen-Docstring.
        return cls(
            agent_id=agent_id_raw,
            target_device_id=target,
            rules=rules,
            plugin=None,
            plugin_name=plugin_name,
            plugin_params=None,
        )


def _condition_matches(condition: RuleCondition, context: DeviceTickContext) -> bool:
    """Wertet eine `RuleCondition` gegen den `DeviceTickContext` aus.

    Welle-4b-Metric-Whitelist (ADR 0027 §2.3): nur `tick` und
    `simulation_time` sind zulaessig. Andere Metric-Werte sollten
    bereits vom Validator abgewiesen worden sein; hier defensive
    Loop ueber das Whitelist-Tuple, damit ein etwaiger Drift im
    Validator-Pfad sichtbar bricht statt still default-zu-False.
    """
    if condition.metric == "tick":
        value = context.tick
    elif condition.metric == "simulation_time":
        value = context.simulation_time
    else:
        # Defensive: Validator haette das schon abgewiesen.
        # Hier liefern wir `False`, damit die Regel nicht
        # matched (kein Crash zur Laufzeit).
        return False
    return _apply_comparator(value, condition.comparator, condition.threshold)


def _apply_comparator(value: int, comparator: str, threshold: int) -> bool:  # noqa: PLR0911 — 6 Comparator-Branches + Default-Fallback aus deterministischer Whitelist (ADR 0027 §2.3).
    """Wertbasierter Vergleich mit der Welle-4b-Comparator-Liste."""
    if comparator == "<":
        return value < threshold
    if comparator == "<=":
        return value <= threshold
    if comparator == "==":
        return value == threshold
    if comparator == "!=":
        return value != threshold
    if comparator == ">=":
        return value >= threshold
    if comparator == ">":
        return value > threshold
    # Defensive: Validator haette das schon abgewiesen.
    return False


def _rule_from_mapping(raw: object) -> Rule:  # noqa: PLR0915 — pro-Feld-typed-Errors fuer condition (3) + action (2) Pflichtfelder; Pattern-Konsistenz zu TickLoop-_restore_pending_command_entry.
    """Rekonstruiert eine `Rule` aus dem Snapshot-Mapping.

    Strukturelle Pruefung mit typisierten Fehlern aus dem
    Welle-0a-Generic-Codec (`hexagon/core/errors.py`).
    """
    if not isinstance(raw, Mapping):
        from grid_gym.hexagon.core.errors import WrongTypeError

        raise WrongTypeError("rule_based_agent", "rules[*]", "Mapping", type(raw).__name__)
    condition_raw = raw.get("condition")
    action_raw = raw.get("action")
    if not isinstance(condition_raw, Mapping):
        from grid_gym.hexagon.core.errors import WrongTypeError

        raise WrongTypeError(
            "rule_based_agent",
            "rules[*].condition",
            "Mapping",
            type(condition_raw).__name__,
        )
    if not isinstance(action_raw, Mapping):
        from grid_gym.hexagon.core.errors import WrongTypeError

        raise WrongTypeError(
            "rule_based_agent",
            "rules[*].action",
            "Mapping",
            type(action_raw).__name__,
        )
    metric = condition_raw.get("metric")
    comparator = condition_raw.get("comparator")
    threshold = condition_raw.get("threshold")
    if not isinstance(metric, str):
        from grid_gym.hexagon.core.errors import WrongTypeError

        raise WrongTypeError(
            "rule_based_agent",
            "rules[*].condition.metric",
            "str",
            type(metric).__name__,
        )
    if not isinstance(comparator, str):
        from grid_gym.hexagon.core.errors import WrongTypeError

        raise WrongTypeError(
            "rule_based_agent",
            "rules[*].condition.comparator",
            "str",
            type(comparator).__name__,
        )
    if isinstance(threshold, bool) or not isinstance(threshold, int):
        from grid_gym.hexagon.core.errors import WrongTypeError

        raise WrongTypeError(
            "rule_based_agent",
            "rules[*].condition.threshold",
            "int",
            type(threshold).__name__,
        )
    action_type = action_raw.get("type")
    payload = action_raw.get("payload")
    if not isinstance(action_type, str):
        from grid_gym.hexagon.core.errors import WrongTypeError

        raise WrongTypeError(
            "rule_based_agent",
            "rules[*].action.type",
            "str",
            type(action_type).__name__,
        )
    if not isinstance(payload, Mapping):
        from grid_gym.hexagon.core.errors import WrongTypeError

        raise WrongTypeError(
            "rule_based_agent",
            "rules[*].action.payload",
            "Mapping",
            type(payload).__name__,
        )
    return Rule(
        condition=RuleCondition(metric=metric, comparator=comparator, threshold=threshold),
        action=RuleAction(type=action_type, payload=dict(payload)),
    )
