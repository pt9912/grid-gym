"""Planted-Violator-Property-Tests fuer `AC-ADAPTER-LIGHTWEIGHT`
(M4-Welle-1-§7-Folge-Pflicht, in Welle-6a-C3 eingezogen).

Welle-1 hat in `done/M4-welle-1.md` §7 die Folge-Pflicht
markiert: ein Test, der absichtlich einen Adapter mit
cyclomatic complexity > 8 unter einem `protocol_*`-Pfad
einbaut und prueft, dass `_check_adapter_lightweight` die
Verletzung tatsaechlich faengt.

Bisher (Welle 2/3/4/5a/5b) lief der Smoke-Regression-Schutz
nur via `make arch-check` 19/19 KEPT — bestaetigt die
Abwesenheit von Verletzungen im **realen** Code, **nicht**
die Korrektheit des Filters. Falls der Filter durch einen
Refactor (z. B. Pfad-Logik-Drift in
`_is_adapter_lightweight_path`) false-clean wuerde, haetten
wir keinen Aufschrei.

Dieser Test schliesst die Luecke:

1. Erstellt eine temp-Repo-Struktur mit einer Datei unter
   `src/grid_gym/adapters/driven/protocol_planted_violator/`
   mit einer Funktion `complex_business_logic()` mit
   cyclomatic complexity ~ 12 (5 `if`-Branches + 2
   `elif` + 4 `and`/`or` Conditions).
2. Rufe `_check_adapter_lightweight(repo_root, src_root)`
   direkt auf.
3. Assert: violations enthaelt
   `AC-ADAPTER-LIGHTWEIGHT` mit dem korrekten Pfad.

Plus zwei Negativ-Tests:

4. Datei OUTSIDE `protocol_*`/`persistence_*`/`driving/`
   triggert den Check **nicht** (Pfad-Filter-Korrektheit).
5. Datei UNDER `protocol_*` aber MIT Funktion mit
   complexity <= 8 triggert den Check **nicht**.
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
    """Importiert `tools/arch_check.py` als Modul fuer
    direkten Zugriff auf `_check_adapter_lightweight`.

    `tools/arch_check.py` ist kein installiertes Paket; wir
    laden es via `importlib.util.spec_from_file_location`.

    Slice 034 F6: `sys.modules`-Eintrag wird durch Yield-
    Cleanup wieder entfernt — keine process-wide Mutation,
    pytest-xdist-Race-frei. Zuvor: direkte `sys.modules[...]
    = module`-Assignment ohne Teardown.
    """
    spec = importlib.util.spec_from_file_location("_arch_check_under_test", _TOOLS_PATH)
    if spec is None or spec.loader is None:
        pytest.fail(f"konnte arch_check.py nicht laden: {_TOOLS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_arch_check_under_test"] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop("_arch_check_under_test", None)


def _write_temp_repo(tmp_path: Path, rel_path: str, source: str) -> tuple[Path, Path]:
    """Baut eine temp-Repo-Struktur und schreibt eine Python-
    Datei unter `rel_path`. Gibt `(repo_root, src_root)`
    zurueck. `resolve()` normalisiert Symlinks (auf macOS ist
    `/tmp` ein Symlink auf `/private/tmp`; ohne resolve()
    schlaegt `Path.relative_to` mit cross-symlink-Pfaden fehl)."""
    repo_root = (tmp_path / "fake_repo").resolve()
    target = repo_root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    src_root = repo_root / "src" / "grid_gym"
    return repo_root, src_root


# Source-Snippet mit cyclomatic complexity ~ 12.
# Cyclomatic complexity = 1 (base) + Anzahl Branches.
# Hier: 5 `if`/`elif`-Verzweigungen + 4 `and`/`or` = 12+.
_HIGH_COMPLEXITY_SOURCE = '''
"""Planted Violator — absichtlich komplexe Adapter-Funktion."""

def complex_business_logic(x: int, y: int, z: int, w: int, v: int) -> int:
    """Cyclomatic complexity > 8 — soll AC-ADAPTER-LIGHTWEIGHT triggern."""
    if x > 0 and y > 0:
        return x + y
    elif x < 0 or y < 0:
        if z > 10:
            return z
        elif w > 5 and v > 3:
            return w + v
        elif w < 0 or v < 0:
            return -1
        else:
            return 0
    elif z == 0:
        return -2
    else:
        return -3
'''

_LOW_COMPLEXITY_SOURCE = '''
"""Lightweight Adapter — complexity <= 8."""

def lightweight_operation(x: int) -> int:
    """Simple branch — complexity 2."""
    if x > 0:
        return x
    return 0
'''


# ---------------------------------------------------------------------------
# Positive: Planted-Violator wird gefangen
# ---------------------------------------------------------------------------


def test_planted_violator_under_protocol_path_is_caught(
    _arch_check_module: object, tmp_path: Path
) -> None:
    """Datei unter `src/grid_gym/adapters/driven/protocol_planted_violator/`
    mit komplexer Funktion -> `_check_adapter_lightweight` muss
    eine Violation produzieren."""
    rel = "src/grid_gym/adapters/driven/protocol_planted_violator/violator.py"
    repo_root, src_root = _write_temp_repo(tmp_path, rel, _HIGH_COMPLEXITY_SOURCE)

    violations = list(
        _arch_check_module._check_adapter_lightweight(repo_root, src_root)  # type: ignore[attr-defined]
    )

    assert len(violations) >= 1, "AC-ADAPTER-LIGHTWEIGHT muss die Planted-Violator-Funktion fangen"
    matching = [
        v
        for v in violations
        if v.contract_id == "AC-ADAPTER-LIGHTWEIGHT" and "protocol_planted_violator" in v.location
    ]
    assert matching, f"erwartet AC-ADAPTER-LIGHTWEIGHT-Violation; got {violations}"


def test_planted_violator_under_persistence_path_is_caught(
    _arch_check_module: object, tmp_path: Path
) -> None:
    """Analog Test 1, aber unter `persistence_*` (zweiter
    Pfad-Filter-Branch)."""
    rel = "src/grid_gym/adapters/driven/persistence_planted_violator/violator.py"
    repo_root, src_root = _write_temp_repo(tmp_path, rel, _HIGH_COMPLEXITY_SOURCE)

    violations = list(
        _arch_check_module._check_adapter_lightweight(repo_root, src_root)  # type: ignore[attr-defined]
    )

    assert len(violations) >= 1
    assert any(v.contract_id == "AC-ADAPTER-LIGHTWEIGHT" for v in violations), (
        f"erwartet AC-ADAPTER-LIGHTWEIGHT-Violation; got {violations}"
    )


def test_planted_violator_under_driving_path_is_caught(
    _arch_check_module: object, tmp_path: Path
) -> None:
    """Analog Test 1, aber unter `adapters/driving/` (dritter
    Pfad-Filter-Branch — beliebige Tiefe erlaubt)."""
    rel = "src/grid_gym/adapters/driving/http_api/v1/violator.py"
    repo_root, src_root = _write_temp_repo(tmp_path, rel, _HIGH_COMPLEXITY_SOURCE)

    violations = list(
        _arch_check_module._check_adapter_lightweight(repo_root, src_root)  # type: ignore[attr-defined]
    )

    assert any(v.contract_id == "AC-ADAPTER-LIGHTWEIGHT" for v in violations)


# ---------------------------------------------------------------------------
# Negativ: Pfade ausserhalb der Adapter-Boundary triggern den Check NICHT
# ---------------------------------------------------------------------------


def test_path_filter_rejects_paths_outside_adapter_boundary(
    _arch_check_module: object,
) -> None:
    """Slice 034 F4: zuvor war dieser Test vacuous — er schrieb
    eine Datei unter `hexagon/core/` und assertierte
    `violations == []`, aber `_check_adapter_lightweight` ruft
    `_iter_py_files(adapters_root)` auf, das hexagon-Pfade
    niemals erreicht. Der Test war false-clean.

    Korrekter Filter-Praezisions-Test: direktes Pruefen von
    `_is_adapter_lightweight_path` mit Pfaden ausserhalb der
    Adapter-Boundary — die einzige Schicht, die die Property
    'hexagon/ wird ignoriert' tatsaechlich enforced."""
    is_adapter_path = _arch_check_module._is_adapter_lightweight_path  # type: ignore[attr-defined]

    # Pfade ausserhalb adapters/ muessen False zurueckgeben.
    assert is_adapter_path("src/grid_gym/hexagon/core/simulation/foo.py") is False
    assert is_adapter_path("src/grid_gym/hexagon/ports/driven/bar.py") is False
    assert is_adapter_path("tools/arch_check.py") is False
    assert is_adapter_path("tests/unit/foo.py") is False
    # Pfade UNTER adapters/ aber im falschen Layer.
    assert is_adapter_path("src/grid_gym/adapters/observability_null/x.py") is False
    # Driven-Layer, aber kein protocol_*/persistence_*-Bucket.
    assert is_adapter_path("src/grid_gym/adapters/driven/observability_null/x.py") is False
    assert is_adapter_path("src/grid_gym/adapters/driven/_protocol_otel_wrap.py") is False
    # Positiv-Kontrollen (zur Sicherheit dass die Funktion nicht trivial False ist).
    assert is_adapter_path("src/grid_gym/adapters/driving/http_api/v1/x.py") is True
    assert is_adapter_path("src/grid_gym/adapters/driven/protocol_modbus/foo.py") is True
    assert is_adapter_path("src/grid_gym/adapters/driven/persistence_postgres/foo.py") is True


def test_high_complexity_under_unrelated_adapter_bucket_is_ignored(
    _arch_check_module: object, tmp_path: Path
) -> None:
    """Datei unter `adapters/driven/observability_null/` (kein
    `protocol_*` / `persistence_*`) muss vom Filter ignoriert
    werden (Pfad-Filter-Praezision)."""
    rel = "src/grid_gym/adapters/driven/observability_null/violator.py"
    repo_root, src_root = _write_temp_repo(tmp_path, rel, _HIGH_COMPLEXITY_SOURCE)

    violations = list(
        _arch_check_module._check_adapter_lightweight(repo_root, src_root)  # type: ignore[attr-defined]
    )

    assert violations == [], (
        f"observability_null/ soll von AC-ADAPTER-LIGHTWEIGHT ignoriert werden; got {violations}"
    )


def test_low_complexity_under_protocol_path_is_clean(
    _arch_check_module: object, tmp_path: Path
) -> None:
    """Datei UNDER protocol_*/ aber mit complexity <= 8 darf
    keine Violation triggern (Schwellwert-Korrektheit)."""
    rel = "src/grid_gym/adapters/driven/protocol_clean/violator.py"
    repo_root, src_root = _write_temp_repo(tmp_path, rel, _LOW_COMPLEXITY_SOURCE)

    violations = list(
        _arch_check_module._check_adapter_lightweight(repo_root, src_root)  # type: ignore[attr-defined]
    )

    assert violations == [], (
        f"lightweight Funktion soll AC-ADAPTER-LIGHTWEIGHT nicht triggern; got {violations}"
    )
