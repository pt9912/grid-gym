"""Tests fuer `Quality` und `CommandResult` (`GG-DATA-003`/`004`)."""

from __future__ import annotations

from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.quality import Quality

# ---------------------------------------------------------------------------
# Quality — GG-DATA-003
# ---------------------------------------------------------------------------

_EXPECTED_QUALITY_VALUES: frozenset[str] = frozenset(
    {
        "valid",
        "stale",
        "estimated",
        "limited",
        "invalid",
        "nan",
        "missing",
        "fault_injected",
    }
)


def test_quality_covers_spec_values() -> None:
    """Alle in `GG-DATA-003` geforderten Werte sind als Member da."""
    assert {q.value for q in Quality} == _EXPECTED_QUALITY_VALUES


def test_quality_has_no_extra_values() -> None:
    """Nur die Spec-Werte sind enthalten — kein Drift."""
    extras = {q.value for q in Quality} - _EXPECTED_QUALITY_VALUES
    assert not extras


def test_quality_is_str_for_canonical_json() -> None:
    """`Quality` muss `str`-Instanz sein, damit `canonical_json` den
    Member als JSON-String emittiert (StrEnum-Konvention)."""
    assert isinstance(Quality.VALID, str)
    assert Quality.VALID == "valid"


# ---------------------------------------------------------------------------
# CommandResult — GG-DATA-004
# ---------------------------------------------------------------------------

_EXPECTED_COMMAND_RESULT_VALUES: frozenset[str] = frozenset(
    {"accepted", "rejected", "limited", "expired", "failed", "ignored"}
)


def test_command_result_covers_spec_values() -> None:
    """Alle in `GG-DATA-004` geforderten Werte sind als Member da."""
    assert {c.value for c in CommandResult} == _EXPECTED_COMMAND_RESULT_VALUES


def test_command_result_has_no_extra_values() -> None:
    extras = {c.value for c in CommandResult} - _EXPECTED_COMMAND_RESULT_VALUES
    assert not extras


def test_command_result_is_str_for_canonical_json() -> None:
    assert isinstance(CommandResult.ACCEPTED, str)
    assert CommandResult.ACCEPTED == "accepted"
