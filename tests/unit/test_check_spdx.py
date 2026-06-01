"""Tests fuer `tools/check_spdx.py` (M4 Welle 6b C1).

Pattern analog `tests/unit/test_check_noqa.py` und
`tests/unit/test_check_refs.py` — direktes Laden des Moduls
via `importlib.util` (kein installiertes Paket).
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest


_TOOLS_PATH = Path(__file__).resolve().parents[2] / "tools" / "check_spdx.py"


@pytest.fixture(scope="module")
def _check_spdx_module() -> Iterator[object]:
    """Laedt `tools/check_spdx.py` als Modul fuer direkten Zugriff
    auf die internen Funktionen. Cleanup via yield-Pattern
    (analog Slice-034-F6-Lehre)."""
    spec = importlib.util.spec_from_file_location("_check_spdx_under_test", _TOOLS_PATH)
    if spec is None or spec.loader is None:
        pytest.fail(f"konnte check_spdx.py nicht laden: {_TOOLS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_check_spdx_under_test"] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop("_check_spdx_under_test", None)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Positiv-Pfade
# ---------------------------------------------------------------------------


def test_file_with_correct_spdx_header_passes(_check_spdx_module: object, tmp_path: Path) -> None:
    """Datei mit korrektem GPL-3.0-only-Header → keine Violation."""
    target = tmp_path / "src" / "foo.py"
    _write(
        target,
        '# SPDX-License-Identifier: GPL-3.0-only\n"""Doc."""\n',
    )
    violations = list(
        _check_spdx_module._check_files(  # type: ignore[attr-defined]
            [target], expected_identifier="GPL-3.0-only"
        )
    )
    assert violations == []


def test_cfg_file_with_correct_header_passes(_check_spdx_module: object, tmp_path: Path) -> None:
    """libiec61850-CFG-Fixture mit Hash-Comment-Header passt."""
    target = tmp_path / "fixture.cfg"
    target.write_text(
        "# SPDX-License-Identifier: GPL-3.0-only\nMODEL{...}\n",
        encoding="utf-8",
    )
    violations = list(
        _check_spdx_module._check_files(  # type: ignore[attr-defined]
            [target], expected_identifier="GPL-3.0-only"
        )
    )
    assert violations == []


def test_header_anywhere_in_file_passes(_check_spdx_module: object, tmp_path: Path) -> None:
    """SPDX-Header darf irgendwo in der Datei stehen (z. B. nach
    Shebang oder im Modul-Docstring)."""
    target = tmp_path / "foo.py"
    _write(
        target,
        "#!/usr/bin/env python3\n"
        '"""Module docstring."""\n'
        "# SPDX-License-Identifier: GPL-3.0-only\n"
        "x = 1\n",
    )
    violations = list(
        _check_spdx_module._check_files(  # type: ignore[attr-defined]
            [target], expected_identifier="GPL-3.0-only"
        )
    )
    assert violations == []


# ---------------------------------------------------------------------------
# Negativ-Pfade
# ---------------------------------------------------------------------------


def test_file_without_spdx_header_fails(_check_spdx_module: object, tmp_path: Path) -> None:
    """Datei ohne SPDX-Header → 1 Violation mit `missing`-Reason."""
    target = tmp_path / "foo.py"
    _write(target, '"""Doc."""\nx = 1\n')
    violations = list(
        _check_spdx_module._check_files(  # type: ignore[attr-defined]
            [target], expected_identifier="GPL-3.0-only"
        )
    )
    assert len(violations) == 1
    assert "missing" in violations[0].reason
    assert "GPL-3.0-only" in violations[0].reason


def test_file_with_wrong_identifier_fails(_check_spdx_module: object, tmp_path: Path) -> None:
    """Datei mit MIT-Header (statt GPL-3.0-only) → 1 Violation
    mit `wrong`-Reason."""
    target = tmp_path / "foo.py"
    _write(target, "# SPDX-License-Identifier: MIT\nx = 1\n")
    violations = list(
        _check_spdx_module._check_files(  # type: ignore[attr-defined]
            [target], expected_identifier="GPL-3.0-only"
        )
    )
    assert len(violations) == 1
    assert "wrong" in violations[0].reason
    assert "MIT" in violations[0].reason


def test_multiple_files_with_mixed_violations(_check_spdx_module: object, tmp_path: Path) -> None:
    """3 Files: 1 OK, 1 missing, 1 wrong → 2 Violations."""
    ok = tmp_path / "ok.py"
    _write(ok, "# SPDX-License-Identifier: GPL-3.0-only\nx = 1\n")
    missing = tmp_path / "missing.py"
    _write(missing, "x = 1\n")
    wrong = tmp_path / "wrong.py"
    _write(wrong, "# SPDX-License-Identifier: Apache-2.0\nx = 1\n")

    violations = list(
        _check_spdx_module._check_files(  # type: ignore[attr-defined]
            [ok, missing, wrong], expected_identifier="GPL-3.0-only"
        )
    )
    assert len(violations) == 2
    paths = {v.path for v in violations}
    assert ok not in paths
    assert missing in paths
    assert wrong in paths


# ---------------------------------------------------------------------------
# Live-Repo-Check
# ---------------------------------------------------------------------------


def test_repo_iec61850_files_all_have_correct_header(
    _check_spdx_module: object,
) -> None:
    """Real-Repo-Check: alle Default-GPL-Pfade haben korrekten
    Header (Welle-5b-Postcondition)."""
    repo_root = _TOOLS_PATH.resolve().parents[1]
    files = list(
        _check_spdx_module._iter_target_files(  # type: ignore[attr-defined]
            repo_root, []
        )
    )
    violations = list(
        _check_spdx_module._check_files(  # type: ignore[attr-defined]
            files, expected_identifier="GPL-3.0-only"
        )
    )
    assert violations == [], (
        f"Repo-IEC-61850-Pfade haben Header-Verletzungen: "
        f"{[v.format(repo_root) for v in violations]}"
    )
    # Sanity: es werden tatsaechlich Dateien gefunden
    # (Welle-5b hat mind. 5 src + 4 tests + 1 fixture + 1 integration
    # test = 11 Dateien).
    assert len(files) >= 11, (
        f"erwartet >= 11 GPL-Boundary-Dateien; nur {len(files)} "
        f"gefunden — Default-GPL-Pfade-Liste evtl. veraltet"
    )


# ---------------------------------------------------------------------------
# CLI / main()
# ---------------------------------------------------------------------------


def test_main_returns_zero_on_clean_default_scan(
    _check_spdx_module: object,
) -> None:
    """`main([])` ueber den echten Default-Scan: Exit-Code 0
    (Welle-5b-Postcondition halten)."""
    rc = _check_spdx_module.main([])  # type: ignore[attr-defined]
    assert rc == 0


def test_main_returns_one_on_violation_via_extra_path(
    _check_spdx_module: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Extra-Pfad mit Violation → Exit-Code 1."""
    bad = tmp_path / "no_header.py"
    _write(bad, "x = 1\n")
    # _iter_target_files macht Pfade relativ zum repo_root; wir
    # uebergeben den absoluten temp_path als CLI-Argument. Aber:
    # die Funktion macht `(repo_root / rel).resolve()`. Wenn `rel`
    # absolut ist, ignoriert `repo_root /` das und resolved direkt.
    rc = _check_spdx_module.main([str(bad)])  # type: ignore[attr-defined]
    assert rc == 1
