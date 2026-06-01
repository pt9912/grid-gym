#!/usr/bin/env python3
"""SPDX-License-Identifier-Header-Konsistenz-Check (M4 Welle 6b).

Verifiziert, dass alle GPL-isolierten Dateien (Welle-5b Decision I-f,
ADR 0035) einen `SPDX-License-Identifier: GPL-3.0-only`-Header tragen.

Pattern-Praezedenz: `tools/check_noqa.py` (CLI-Struktur,
`_iter_files`-Pattern); `tools/check_refs.py` (Lint-Fail-Mode).

Output-Format:
`location<TAB>reason`

Exit-Code 0 wenn alle Pfade Header-konform; 1 wenn mindestens
ein Pfad fehlt oder einen falschen Identifier traegt.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path


_SPDX_PATTERN = re.compile(r"SPDX-License-Identifier:\s*(?P<identifier>[A-Za-z0-9.\-+ ()]+)")

# Welle-6b-Decision: alle GPL-isolierten Pfade brauchen Header.
# Mehrere Pfade moeglich; jeder Pfad ist eine Verzeichnis-Wurzel oder
# eine Datei.
_DEFAULT_GPL_PATHS = (
    "src/grid_gym/adapters/driven/protocol_iec61850",
    "tests/unit/adapters/driven/protocol_iec61850",
    "tests/integration/fixtures/iec61850",
)

# Einzelne Test-Dateien (Glob-Pattern, weil sie nicht in einem
# eigenen Verzeichnis liegen).
_DEFAULT_GPL_FILE_GLOBS = ("tests/integration/test_iec61850_*.py",)

# Dateien mit diesen Suffixen werden gepruft.
_CHECKED_SUFFIXES = frozenset({".py", ".cfg"})

# Erwarteter SPDX-Identifier fuer GPL-Modul.
_EXPECTED_IDENTIFIER = "GPL-3.0-only"

# Wird beim rekursiven rglob uebersprungen.
_SKIPPED_DIRS = frozenset(
    {
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)


@dataclass(frozen=True, slots=True)
class SpdxViolation:
    """Eine SPDX-Lint-Verletzung."""

    path: Path
    reason: str

    def format(self, repo_root: Path) -> str:
        try:
            rel: Path | str = self.path.relative_to(repo_root)
        except ValueError:
            # Caller-supplied extra path outside the repo root —
            # use the absolute path as-is in the report.
            rel = self.path
        return f"{rel}\t{self.reason}"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lintet GPL-3.0-only-SPDX-Header in der IEC-61850-Adapter-"
            "Boundary (ADR 0035 Decision I-f, M4 Welle 6b)."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help=(
            "Optionale Dateien oder Verzeichnisse, die zusaetzlich "
            "gepruft werden. Ohne Argument: Default-GPL-Pfade "
            "(protocol_iec61850/ + tests/.../iec61850/ + "
            "tests/integration/test_iec61850_*.py)."
        ),
    )
    parser.add_argument(
        "--expected-identifier",
        default=_EXPECTED_IDENTIFIER,
        help=(f"SPDX-Identifier, der erwartet wird (Default: {_EXPECTED_IDENTIFIER})."),
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    files = list(_iter_target_files(repo_root, args.paths))
    violations = list(_check_files(files, expected_identifier=args.expected_identifier))

    if not violations:
        print(
            f"[check_spdx] all {len(files)} GPL-boundary file(s) carry "
            f"SPDX-License-Identifier: {args.expected_identifier}"
        )
        return 0

    print("location\treason")
    for violation in violations:
        print(violation.format(repo_root))
    print(
        f"[check_spdx] {len(violations)} SPDX-header violation(s) — see stderr",
        file=sys.stderr,
    )
    return 1


def _iter_target_files(repo_root: Path, extra_paths: list[str]) -> Iterator[Path]:
    """Iteriert ueber alle zu pruefenden Dateien.

    Default: GPL-Pfade aus `_DEFAULT_GPL_PATHS` +
    `_DEFAULT_GPL_FILE_GLOBS`. Zusaetzlich werden vom Caller
    via CLI uebergebene Pfade beruecksichtigt.
    """
    seen: set[Path] = set()
    for path in _iter_default_directories(repo_root):
        if path not in seen:
            seen.add(path)
            yield path
    for path in _iter_default_globs(repo_root):
        if path not in seen:
            seen.add(path)
            yield path
    for path in _iter_extra_paths(repo_root, extra_paths):
        if path not in seen:
            seen.add(path)
            yield path


def _iter_default_directories(repo_root: Path) -> Iterator[Path]:
    for rel in _DEFAULT_GPL_PATHS:
        root = repo_root / rel
        if root.exists():
            yield from _walk(root)


def _iter_default_globs(repo_root: Path) -> Iterator[Path]:
    for pattern in _DEFAULT_GPL_FILE_GLOBS:
        for path in repo_root.glob(pattern):
            resolved = path.resolve()
            if resolved.suffix in _CHECKED_SUFFIXES:
                yield resolved


def _iter_extra_paths(repo_root: Path, extra_paths: list[str]) -> Iterator[Path]:
    for rel in extra_paths:
        candidate = (repo_root / rel).resolve()
        if candidate.is_file():
            yield candidate
        elif candidate.is_dir():
            yield from _walk(candidate)


def _walk(root: Path) -> Iterator[Path]:
    """Rekursive File-Iteration unter `root`, ueberspringt Cache-
    Verzeichnisse und Dateien ohne `.py`/`.cfg`-Suffix."""
    for entry in sorted(root.rglob("*")):
        if not entry.is_file():
            continue
        if entry.suffix not in _CHECKED_SUFFIXES:
            continue
        rel_parts = entry.relative_to(root).parts
        if any(part in _SKIPPED_DIRS for part in rel_parts):
            continue
        yield entry.resolve()


def _check_files(files: Iterable[Path], *, expected_identifier: str) -> Iterator[SpdxViolation]:
    """Prueft jede Datei auf Header-Praesenz + Identifier-Konformitaet."""
    for path in files:
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            yield SpdxViolation(
                path=path,
                reason=f"could not read file: {exc.__class__.__name__}",
            )
            continue
        match = _SPDX_PATTERN.search(content)
        if match is None:
            yield SpdxViolation(
                path=path,
                reason=f"missing SPDX-License-Identifier (expected {expected_identifier})",
            )
            continue
        identifier = match.group("identifier").strip()
        if identifier != expected_identifier:
            yield SpdxViolation(
                path=path,
                reason=(
                    f"wrong SPDX-License-Identifier "
                    f"(expected {expected_identifier}, got {identifier})"
                ),
            )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
