"""Property-Tests fuer `AC-IEC61850-GPL-BOUNDARY` (M4 Welle 6b C2).

Pattern analog `tests/unit/test_arch_check_planted_violator.py`
(Slice 034 F4: yield-fixture-Cleanup, direkter
`_is_adapter_lightweight_path`-Property-Aufruf statt
vacuous-pass-Tests via file-creation).

Verifiziert die GPL-Boundary-Property (ADR 0035 Decision I-f,
Welle-5b-Closure): MIT-Code darf
`grid_gym.adapters.driven.protocol_iec61850.*` nicht direkt
importieren; nur Dateien unter `protocol_iec61850/*` selbst
duerfen das.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest


_TOOLS_PATH = Path(__file__).resolve().parents[2] / "tools" / "arch_check.py"


@pytest.fixture(scope="module")
def _arch_check_module() -> Iterator[object]:
    """Laedt `tools/arch_check.py` analog
    `test_arch_check_planted_violator.py` (Slice-034-F6-Pattern:
    yield-Cleanup statt direkter `sys.modules`-Assignment)."""
    spec = importlib.util.spec_from_file_location("_arch_check_iec61850_under_test", _TOOLS_PATH)
    if spec is None or spec.loader is None:
        pytest.fail(f"konnte arch_check.py nicht laden: {_TOOLS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_arch_check_iec61850_under_test"] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop("_arch_check_iec61850_under_test", None)


def _write_temp_repo(tmp_path: Path, rel_path: str, source: str) -> tuple[Path, Path]:
    """Baut eine temp-Repo-Struktur und schreibt eine Python-
    Datei unter `rel_path`. Gibt `(repo_root, src_root)` zurueck.
    Analog `test_arch_check_planted_violator._write_temp_repo`."""
    repo_root = (tmp_path / "fake_repo").resolve()
    target = repo_root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    src_root = repo_root / "src" / "grid_gym"
    return repo_root, src_root


# Source-Snippets fuer die Property-Tests.
_DIRECT_IMPORT_SOURCE = """\
\"\"\"Caller, der die GPL-Boundary verletzt.\"\"\"
import grid_gym.adapters.driven.protocol_iec61850
"""

_FROM_IMPORT_SOURCE = """\
\"\"\"Caller, der die GPL-Boundary via from-import verletzt.\"\"\"
from grid_gym.adapters.driven.protocol_iec61850 import Iec61850DeviceProtocolPort
"""

_SUBMODULE_IMPORT_SOURCE = """\
\"\"\"Caller, der ein Sub-Modul der GPL-Boundary direkt importiert.\"\"\"
from grid_gym.adapters.driven.protocol_iec61850._port import Iec61850DeviceProtocolPort
"""

_CLEAN_SOURCE = """\
\"\"\"Caller ohne GPL-Boundary-Verletzung.\"\"\"
from grid_gym.hexagon.ports.driven.device_protocol import DeviceProtocolPort
"""

_TYPE_CHECKING_SOURCE = """\
\"\"\"Caller mit TYPE_CHECKING-only Import.

Slice 034 F8-Lehre: TYPE_CHECKING-Imports sind statisch im AST
und werden vom Contract gefangen — das ist intendiert, weil
TYPE_CHECKING-Imports trotzdem Static-Linker-Footprint haben
(z. B. wenn mypy-stubs heruntergeladen sind).
\"\"\"
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grid_gym.adapters.driven.protocol_iec61850 import Iec61850DeviceProtocolPort
"""


# ---------------------------------------------------------------------------
# Positiv-Pfade: GPL-Boundary verletzt → Contract muss fangen
# ---------------------------------------------------------------------------


def test_direct_import_from_mit_code_is_caught(_arch_check_module: object, tmp_path: Path) -> None:
    """`import grid_gym.adapters.driven.protocol_iec61850` aus
    MIT-Code → AC-IEC61850-GPL-BOUNDARY-Violation."""
    rel = "src/grid_gym/adapters/driving/some_caller.py"
    repo_root, src_root = _write_temp_repo(tmp_path, rel, _DIRECT_IMPORT_SOURCE)

    violations = list(
        _arch_check_module._check_iec61850_gpl_boundary(  # type: ignore[attr-defined]
            repo_root, src_root
        )
    )

    assert len(violations) == 1
    assert violations[0].contract_id == "AC-IEC61850-GPL-BOUNDARY"
    assert "grid_gym.adapters.driven.protocol_iec61850" in violations[0].detail


def test_from_import_from_mit_code_is_caught(_arch_check_module: object, tmp_path: Path) -> None:
    """`from grid_gym.adapters.driven.protocol_iec61850 import X`
    aus MIT-Code → AC-IEC61850-GPL-BOUNDARY-Violation."""
    rel = "src/grid_gym/hexagon/core/some_caller.py"
    repo_root, src_root = _write_temp_repo(tmp_path, rel, _FROM_IMPORT_SOURCE)

    violations = list(
        _arch_check_module._check_iec61850_gpl_boundary(  # type: ignore[attr-defined]
            repo_root, src_root
        )
    )

    assert len(violations) == 1
    assert violations[0].contract_id == "AC-IEC61850-GPL-BOUNDARY"
    assert "Iec61850DeviceProtocolPort" in violations[0].detail


def test_submodule_import_from_mit_code_is_caught(
    _arch_check_module: object, tmp_path: Path
) -> None:
    """Sub-Modul-Import wie `from
    grid_gym.adapters.driven.protocol_iec61850._port import X`
    aus MIT-Code → Violation."""
    rel = "src/grid_gym/some_other_caller.py"
    repo_root, src_root = _write_temp_repo(tmp_path, rel, _SUBMODULE_IMPORT_SOURCE)

    violations = list(
        _arch_check_module._check_iec61850_gpl_boundary(  # type: ignore[attr-defined]
            repo_root, src_root
        )
    )

    assert len(violations) == 1
    assert violations[0].contract_id == "AC-IEC61850-GPL-BOUNDARY"


def test_type_checking_import_from_mit_code_is_caught(
    _arch_check_module: object, tmp_path: Path
) -> None:
    """TYPE_CHECKING-only Import wird AST-statisch gefangen.
    Begruendung: AST-Knoten existiert; Static-Linker-Footprint
    bleibt (Lizenz-Aggregation laeuft ueber Source-Distribution,
    nicht nur Runtime-Imports)."""
    rel = "src/grid_gym/adapters/driving/typed_caller.py"
    repo_root, src_root = _write_temp_repo(tmp_path, rel, _TYPE_CHECKING_SOURCE)

    violations = list(
        _arch_check_module._check_iec61850_gpl_boundary(  # type: ignore[attr-defined]
            repo_root, src_root
        )
    )

    assert len(violations) == 1
    assert violations[0].contract_id == "AC-IEC61850-GPL-BOUNDARY"


# ---------------------------------------------------------------------------
# Negativ-Pfade: kein illegaler Import → Contract muss schweigen
# ---------------------------------------------------------------------------


def test_clean_import_from_mit_code_is_not_caught(
    _arch_check_module: object, tmp_path: Path
) -> None:
    """MIT-Code importiert nur via `DeviceProtocolPort`-Port-
    Surface → keine Violation."""
    rel = "src/grid_gym/adapters/driving/clean_caller.py"
    repo_root, src_root = _write_temp_repo(tmp_path, rel, _CLEAN_SOURCE)

    violations = list(
        _arch_check_module._check_iec61850_gpl_boundary(  # type: ignore[attr-defined]
            repo_root, src_root
        )
    )

    assert violations == []


def test_import_from_within_gpl_boundary_is_not_caught(
    _arch_check_module: object, tmp_path: Path
) -> None:
    """Files UNTER `protocol_iec61850/*` selbst duerfen
    untereinander importieren — sie sind ja Teil des GPL-Sub-
    Moduls. Pfad-Filter Whitelist."""
    rel = "src/grid_gym/adapters/driven/protocol_iec61850/_internal_helper.py"
    # Innerhalb der GPL-Boundary darf das Module sich selbst importieren.
    source = (
        '"""Internal helper inside protocol_iec61850.""""""\n'
        "from grid_gym.adapters.driven.protocol_iec61850._port import (\n"
        "    Iec61850DeviceProtocolPort,\n"
        ")\n"
    )
    repo_root, src_root = _write_temp_repo(tmp_path, rel, source)

    violations = list(
        _arch_check_module._check_iec61850_gpl_boundary(  # type: ignore[attr-defined]
            repo_root, src_root
        )
    )

    assert violations == []


def test_import_of_unrelated_module_with_similar_prefix_is_not_caught(
    _arch_check_module: object, tmp_path: Path
) -> None:
    """Prefix-Match-Praezision: ein hypothetisches
    `protocol_iec61850_helper.py` (ohne Underscore-Slash-
    Boundary) darf NICHT als GPL-Boundary-Verletzung gefangen
    werden — `protocol_iec61850.` (mit Dot) ist der Boundary,
    nicht `protocol_iec61850`-Prefix-Match auf Modul-Namen.

    Hier konkret: `grid_gym.protocol_iec61850_compat` (z. B.
    hypothetisches MIT-Compat-Modul auf Top-Level) waere
    nicht unter `adapters.driven.protocol_iec61850.` →
    keine Violation. Dummy-File mit unrelated Modul.
    """
    rel = "src/grid_gym/some_module.py"
    source = (
        '"""Module that does NOT import the GPL boundary."""\n'
        "from grid_gym.hexagon.ports.driven.device_protocol import "
        "DeviceProtocolPort\n"
    )
    repo_root, src_root = _write_temp_repo(tmp_path, rel, source)

    violations = list(
        _arch_check_module._check_iec61850_gpl_boundary(  # type: ignore[attr-defined]
            repo_root, src_root
        )
    )

    assert violations == []


# ---------------------------------------------------------------------------
# Live-Repo-Check
# ---------------------------------------------------------------------------


def test_live_repo_holds_iec61850_gpl_boundary(
    _arch_check_module: object,
) -> None:
    """Real-Repo-Check: der aktuelle Repo-Code haelt
    AC-IEC61850-GPL-BOUNDARY (Welle-5b-Closure-Postcondition).

    Wenn dieser Test failed, hat irgendein MIT-Modul einen
    direkten Import des GPL-isolierten `protocol_iec61850/*`-
    Moduls eingefuehrt — das macht das gesamte Aggregat
    GPL-pflichtig (ADR 0035 §I-f).
    """
    repo_root = _TOOLS_PATH.resolve().parents[1]
    src_root = repo_root / "src" / "grid_gym"
    violations = list(
        _arch_check_module._check_iec61850_gpl_boundary(  # type: ignore[attr-defined]
            repo_root, src_root
        )
    )

    assert violations == [], (
        f"Repo hat AC-IEC61850-GPL-BOUNDARY-Verletzung: {[v.format() for v in violations]}"
    )
