"""Vollstaendigkeits-Test fuer die Contract-Registrierung in
`tools/arch_check.py main()`.

Faengt den Fall, dass jemand einen `_check_*`-Aufruf in `main()`
auskommentiert oder entfernt — ohne diesen Test wuerde
`make arch-check` weiterhin „all contracts kept" zurueckgeben,
obwohl ein Contract still nicht mehr geprueft wird.

Bezug: drittes Review §3 Operative Folge-Pflichten,
M1-Vorbereitung. Test liegt unter `tests/unit/`, damit er via
`make test-unit` mitlaeuft; ein eigener `tests/arch/`-Stage waere
sauberer, aber ist M1-territory.
"""

from __future__ import annotations

import ast
from pathlib import Path

# Erwartete `_check_*`-Aufrufe in `arch_check.py main()`. Reihenfolge
# entspricht der operativen Order. Wenn jemand einen Check entfernt,
# ergaenzt oder umbenennt, muss diese Konstante mitgezogen werden —
# und das wiederum triggert eine Folge-ADR fuer ADR 0002 §A-1
# (per ADR 0006 §3, weil ADR 0002 `Accepted` ist).
_EXPECTED_CHECK_FUNCTIONS: frozenset[str] = frozenset(
    {
        "_check_hexagon_pure",
        "_check_no_json",
        "_check_no_time",
        "_check_no_rand",
        "_check_no_io_mod_nested",
        "_check_domain_frozen",
        "_check_no_god_utils",
        "_check_typed_errors",
        "_check_no_cycles",
        "_check_adapter_lightweight",
        # AC-NO-COVERAGE-PRAGMA (ADR 0029, Schaerfung von ADR 0002 §A-1
        # per ADR 0011-Pattern; 11. arch_check-Contract).
        "_check_no_coverage_pragma",
        # AC-OTLP-ADAPTER-NO-TIME (M3-Welle-6-Review-Folge-H-2, ADR 0024
        # §4.5.5 D-4; 12. arch_check-Contract). Scoped auf
        # `adapters/driven/telemetry_otlp/**`; forbids `time` + `datetime`.
        "_check_otlp_adapter_no_time",
        # AC-TICK-LOOP-PRIVATE-RESUME-ERRORS (Slice 028 / Slice 027
        # Review-Folge L-5; 13. arch_check-Contract). Verbietet
        # `from grid_gym.hexagon.core.simulation.tick_loop import _<...>`
        # ausserhalb des `tick_loop.py`-Moduls; Whitelist via pyproject.
        "_check_tick_loop_private_resume_errors",
        # AC-IEC61850-GPL-BOUNDARY (M4 Welle 6b C2, ADR 0035 Decision
        # I-f; 14. arch_check-Contract). Verbietet direkten Import von
        # `grid_gym.adapters.driven.protocol_iec61850.*` aus MIT-Code
        # (Welle-5b-Decision-I-f-Static-Enforcement: bisher Konvention,
        # jetzt Static-Check).
        "_check_iec61850_gpl_boundary",
    }
)


def _extract_main_check_calls() -> frozenset[str]:
    """Parsed `tools/arch_check.py`, findet `main()` und sammelt
    alle aufgerufenen `_check_*`-Funktions-IDs."""
    arch_check_path = Path(__file__).resolve().parents[2] / "tools" / "arch_check.py"
    source = arch_check_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    main_func: ast.FunctionDef | None = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            main_func = node
            break
    assert main_func is not None, "arch_check.py main() function not found"
    calls: set[str] = set()
    for node in ast.walk(main_func):
        if not isinstance(node, ast.Call):
            continue
        # Pattern: `violations.extend(_check_*(...))` — der aeussere
        # Call ist `violations.extend(...)`, das Argument enthaelt
        # den eigentlichen `_check_*`-Call.
        for arg in node.args:
            if (
                isinstance(arg, ast.Call)
                and isinstance(arg.func, ast.Name)
                and arg.func.id.startswith("_check_")
            ):
                calls.add(arg.func.id)
        # Pattern: direkter Aufruf `_check_*(...)`
        if isinstance(node.func, ast.Name) and node.func.id.startswith("_check_"):
            calls.add(node.func.id)
    return frozenset(calls)


def test_all_expected_checks_are_registered_in_main() -> None:
    """Jeder erwartete `_check_*` ist in `main()` registriert."""
    registered = _extract_main_check_calls()
    missing = _EXPECTED_CHECK_FUNCTIONS - registered
    assert not missing, (
        f"missing _check_* in arch_check.py main(): {sorted(missing)} — "
        "auskommentiert oder entfernt? Verbindlicher Vertrag aus "
        "ADR 0002 §A-1 (Accepted 2026-05-15)."
    )


def test_no_unexpected_checks_registered_in_main() -> None:
    """Keine neuen `_check_*`-Aufrufe ohne Update der Erwartungsliste.

    Strikter Spiegel-Assert: ein neuer Contract ohne Update von
    `_EXPECTED_CHECK_FUNCTIONS` oben ist ein bewusster Trigger,
    dass die ADR-Tabelle in `ADR 0002 §A-1` mitgepflegt werden muss
    (Folge-ADR, weil ADR 0002 `Accepted` ist).
    """
    registered = _extract_main_check_calls()
    unexpected = registered - _EXPECTED_CHECK_FUNCTIONS
    assert not unexpected, (
        f"new _check_* in arch_check.py main() ohne Update der Test-"
        f"Konstante: {sorted(unexpected)} — Folge-ADR fuer ADR 0002 "
        "§A-1 erforderlich."
    )


def test_registered_count_matches_adr_count() -> None:
    """Die Zahl ist heute genau 14: zehn urspruengliche A-1-Contracts
    (`ADR 0002 §A-1`) plus AC-NO-COVERAGE-PRAGMA per `ADR 0029` plus
    AC-OTLP-ADAPTER-NO-TIME per M3-Welle-6-Review-Folge-H-2
    (Schaerfung-ohne-Supersedes von `ADR 0024 §4.5.5 D-4` per ADR 0011-
    Pattern) plus AC-TICK-LOOP-PRIVATE-RESUME-ERRORS per Slice 028
    (Slice 027 Review-Folge L-5) plus AC-IEC61850-GPL-BOUNDARY per
    M4-Welle-6b-C2 (Welle-5b-Decision-I-f-Static-Enforcement,
    ADR 0035); zusammen 14 ueber `tools/arch_check.py` und 6 ueber
    `import-linter`."""
    expected_arch_check_contracts = 14
    registered = _extract_main_check_calls()
    assert len(registered) == expected_arch_check_contracts, (
        f"arch_check.py main() registriert {len(registered)} Contracts, "
        f"erwartet {expected_arch_check_contracts} "
        "(ADR 0002 §A-1 + ADR 0029 + ADR 0024 §4.5.5 + Slice 028 + "
        "ADR 0035 §I-f Welle-6b-C2)."
    )
