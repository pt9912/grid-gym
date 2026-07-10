"""Sensor-Marker-Drift-Guard (Slice 058, Folge zu Slice 054).

Jeder in `pyproject.toml` deklarierte pytest-Marker hat einen
`make test-<marker>`-Sensor (`determinism`/`replay`/`fault`). Verliert
eine Marker-Familie ihren letzten Traeger, faellt `pytest -m <marker>`
still auf Exit 5 (0 selektiert) zurueck — genau die Sensor-Drift, die
Slice 054 behoben hat. Weil die Marker-Targets in keiner CI-Stage laufen
(bewusst deferred in 054), wuerde die Drift sonst unbemerkt wiederkehren.

Dieser Meta-Test laeuft unter `make test-unit` / `make gates` und faellt,
sobald ein deklarierter Marker keinen Traeger (`pytest.mark.<marker>`)
mehr im Testbaum hat. Statischer AST-Scan ueber `tests/**` — damit
scope-unabhaengig (anders als ein Session-Hook, der nur die aktuelle
Selektion sieht) und ohne verschachteltes pytest.

Grenze: erkannt wird die Idiom-Form `pytest.mark.<name>` (Modul-Level
`pytestmark`, Dekorator, parametrisiert). Ein Alias wie
`from pytest import mark` wuerde nicht erfasst — die Repo-Konvention
nutzt durchgaengig `pytest.mark.<name>`.
"""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TESTS_DIR = Path(__file__).resolve().parents[1]
_PYPROJECT = _REPO_ROOT / "pyproject.toml"


def _declared_markers() -> frozenset[str]:
    """Marker-Namen aus `[tool.pytest.ini_options].markers`."""
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    raw = data["tool"]["pytest"]["ini_options"]["markers"]
    return frozenset(entry.split(":", 1)[0].strip() for entry in raw)


def _pytest_mark_name(node: ast.AST) -> str | None:
    """Gibt `<name>` fuer einen `pytest.mark.<name>`-Ausdruck zurueck, sonst None."""
    if not isinstance(node, ast.Attribute):
        return None
    mark = node.value
    if not (isinstance(mark, ast.Attribute) and mark.attr == "mark"):
        return None
    root = mark.value
    if isinstance(root, ast.Name) and root.id == "pytest":
        return node.attr
    return None


def _markers_with_carriers() -> frozenset[str]:
    """Marker-Namen, die im Testbaum als `pytest.mark.<name>` vorkommen."""
    used: set[str] = set()
    for path in _TESTS_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            name = _pytest_mark_name(node)
            if name is not None:
                used.add(name)
    return frozenset(used)


def test_every_declared_marker_has_at_least_one_carrier() -> None:
    """Kein deklarierter Marker ohne Traeger (Sensor-Drift-Guard)."""
    declared = _declared_markers()
    carriers = _markers_with_carriers()
    orphaned = declared - carriers
    assert not orphaned, (
        f"Deklarierte pytest-Marker ohne Traeger: {sorted(orphaned)} — "
        f"`make test-<marker>` selektiert dafuer 0 Tests (pytest-Exit 5, "
        "stille Sensor-Drift, Slice-054-Bug-Klasse). Fix: Traeger via "
        "`pytestmark = pytest.mark.<marker>` ergaenzen ODER den Marker aus "
        "pyproject.toml + Makefile/Dockerfile-Sensor entfernen."
    )
