"""Tests fuer `tools/render_trivyignore.py` (M6 Welle 4a; ADR 0044).

Pattern analog `tests/unit/test_check_spdx.py` / `test_check_noqa.py` /
`test_check_refs.py` — direktes Laden des Moduls via `importlib.util`
(kein installiertes Paket).

Schaerfungs-Fokus (Post-Closure-Korrektur-Stack): ADR 0044 §2.2-
Pflicht-Felder (`id` + `reason` + `expires` + `scope`) muessen alle
einzeln zum Render-Lauf-Bruch fuehren — sonst kann eine HIGH/CRITICAL-
CVE ohne auditfaehige Begruendung in die generierte `.trivyignore`
gelangen.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest


_TOOLS_PATH = Path(__file__).resolve().parents[2] / "tools" / "render_trivyignore.py"


@pytest.fixture(scope="module")
def _render_module() -> Iterator[object]:
    """Laedt `tools/render_trivyignore.py` als Modul fuer direkten
    Zugriff auf die internen Funktionen. Cleanup via yield-Pattern."""

    spec = importlib.util.spec_from_file_location(
        "_render_trivyignore_under_test", _TOOLS_PATH
    )
    if spec is None or spec.loader is None:
        pytest.fail(f"konnte render_trivyignore.py nicht laden: {_TOOLS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_render_trivyignore_under_test"] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop("_render_trivyignore_under_test", None)


_TODAY = dt.date(2026, 6, 6)
_FUTURE = "2026-12-31"


def _valid_entry() -> dict[str, object]:
    return {
        "id": "CVE-2026-99999",
        "reason": "test vector not reachable; container has no exposure",
        "expires": _FUTURE,
        "scope": "otel-collector",
    }


def test_valid_entry_renders_without_error(_render_module: object) -> None:
    lines, had_error = _render_module._emit_entry(  # type: ignore[attr-defined]
        _valid_entry(), today=_TODAY, scope_filter="otel-collector"
    )

    assert had_error is False
    assert lines == [
        "# CVE-2026-99999 - test vector not reachable; container has no exposure"
        " (expires 2026-12-31, scope otel-collector)",
        "CVE-2026-99999",
    ]


def test_missing_id_breaks_render(_render_module: object) -> None:
    entry = _valid_entry()
    del entry["id"]

    lines, had_error = _render_module._emit_entry(  # type: ignore[attr-defined]
        entry, today=_TODAY, scope_filter="otel-collector"
    )

    assert had_error is True
    assert lines == []


def test_missing_expires_breaks_render(_render_module: object) -> None:
    entry = _valid_entry()
    del entry["expires"]

    lines, had_error = _render_module._emit_entry(  # type: ignore[attr-defined]
        entry, today=_TODAY, scope_filter="otel-collector"
    )

    assert had_error is True
    assert lines == []


def test_expired_breaks_render(_render_module: object) -> None:
    entry = _valid_entry()
    entry["expires"] = "2026-01-01"  # in the past relative to _TODAY

    lines, had_error = _render_module._emit_entry(  # type: ignore[attr-defined]
        entry, today=_TODAY, scope_filter="otel-collector"
    )

    assert had_error is True
    assert lines == []


def test_missing_reason_breaks_render(_render_module: object) -> None:
    """ADR 0044 §2.2: `reason` ist Pflicht. Ein Eintrag ohne reason
    darf NICHT als gerendert mit leerem Kommentar in der .trivyignore
    landen — Audit-Trail-Bruch."""

    entry = _valid_entry()
    del entry["reason"]

    lines, had_error = _render_module._emit_entry(  # type: ignore[attr-defined]
        entry, today=_TODAY, scope_filter="otel-collector"
    )

    assert had_error is True
    assert lines == []


def test_empty_reason_breaks_render(_render_module: object) -> None:
    """Whitespace-Reason zaehlt nicht als gueltige Begruendung."""

    entry = _valid_entry()
    entry["reason"] = "   "

    lines, had_error = _render_module._emit_entry(  # type: ignore[attr-defined]
        entry, today=_TODAY, scope_filter="otel-collector"
    )

    assert had_error is True
    assert lines == []


def test_missing_scope_breaks_render(_render_module: object) -> None:
    """ADR 0044 §2.2: `scope` ist Pflicht. Vor der Korrektur wurde
    eine fehlende `scope` je nach Aufruf still ignoriert oder als
    `*` behandelt; jetzt bricht der Lauf."""

    entry = _valid_entry()
    del entry["scope"]

    lines, had_error = _render_module._emit_entry(  # type: ignore[attr-defined]
        entry, today=_TODAY, scope_filter="otel-collector"
    )

    assert had_error is True
    assert lines == []


def test_empty_scope_breaks_render_even_without_filter(
    _render_module: object,
) -> None:
    """Auch ohne Scope-Filter (z. B. `--scope ""`) bleibt scope-Pflicht
    gueltig — sonst koennte ein Aufrufer mit leerem Filter den Vertrag
    umgehen."""

    entry = _valid_entry()
    entry["scope"] = ""

    lines, had_error = _render_module._emit_entry(  # type: ignore[attr-defined]
        entry, today=_TODAY, scope_filter=""
    )

    assert had_error is True
    assert lines == []


def test_scope_filter_skips_non_matching_entry(_render_module: object) -> None:
    """Scope-Filter bleibt funktional: nicht-matchende Eintraege werden
    OHNE Fehler stillschweigend uebersprungen (keine Lines, kein Error).
    """

    entry = _valid_entry()
    entry["scope"] = "mtrace-dashboard"

    lines, had_error = _render_module._emit_entry(  # type: ignore[attr-defined]
        entry, today=_TODAY, scope_filter="otel-collector"
    )

    assert had_error is False
    assert lines == []


def test_wildcard_scope_matches_any_filter(_render_module: object) -> None:
    """`scope: *` darf jedes Scope-Filter matchen (Cross-Image-Eintrag).
    """

    entry = _valid_entry()
    entry["scope"] = "*"

    lines, had_error = _render_module._emit_entry(  # type: ignore[attr-defined]
        entry, today=_TODAY, scope_filter="any-image"
    )

    assert had_error is False
    assert lines == [
        "# CVE-2026-99999 - test vector not reachable; container has no exposure"
        " (expires 2026-12-31, scope *)",
        "CVE-2026-99999",
    ]
