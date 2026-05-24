#!/usr/bin/env python3
"""Findet `# noqa`-Marker im Repository.

Standardmodus: nur berichten, Exit-Code 0. Fuer das spaetere
Scharfschalten kann `--fail-on-noqa` genutzt werden; dann fuehrt jeder
gefundene Marker zu Exit-Code 1.

Output-Format:
`location<TAB>ruff-code<TAB>begruendung`
"""

from __future__ import annotations

import argparse
import re
import sys
import tokenize
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path


_NOQA_PATTERN = re.compile(
    r"#\s*noqa"
    r"(?:\s*:\s*(?P<codes>[A-Z][A-Z0-9]*(?:\s*,\s*[A-Z][A-Z0-9]*)*))?"
    r"(?:\s*(?:--|-|\u2014)\s*(?P<reason>.*))?"
)

_DEFAULT_TOP_LEVELS = ("src", "tests", "tools")
_SKIPPED_DIRS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
        "site-packages",
        "venv",
    }
)


@dataclass(frozen=True, slots=True)
class NoqaMarker:
    """Eine gefundene `# noqa`-Stelle."""

    path: Path
    lineno: int
    codes: str
    reason: str

    def format(self, repo_root: Path) -> str:
        rel = self.path.relative_to(repo_root)
        return f"{rel}:{self.lineno}\t{self.codes}\t{self.reason}"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        help="Dateien oder Verzeichnisse; Default: src tests tools",
    )
    parser.add_argument(
        "--fail-on-noqa",
        action="store_true",
        help="Exit-Code 1, wenn mindestens ein # noqa gefunden wird.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    scan_roots = _scan_roots(repo_root, args.paths)
    markers = list(_find_noqa_markers(repo_root, scan_roots))

    if not markers:
        print("[check_noqa] no # noqa markers found")
        return 0

    print("location\truff-code\tbegruendung")
    for marker in markers:
        print(marker.format(repo_root))
    print(f"[check_noqa] {len(markers)} # noqa marker(s) found")
    return 1 if args.fail_on_noqa else 0


def _scan_roots(repo_root: Path, raw_paths: list[str]) -> tuple[Path, ...]:
    if not raw_paths:
        return tuple(repo_root / name for name in _DEFAULT_TOP_LEVELS)
    return tuple((repo_root / raw_path).resolve() for raw_path in raw_paths)


def _find_noqa_markers(repo_root: Path, roots: Iterable[Path]) -> Iterator[NoqaMarker]:
    for source in _iter_python_files(repo_root, roots):
        yield from _find_noqa_markers_in_file(source)


def _iter_python_files(repo_root: Path, roots: Iterable[Path]) -> Iterator[Path]:
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        candidates = (root,) if root.is_file() else sorted(root.rglob("*.py"))
        for candidate in candidates:
            if candidate.suffix != ".py":
                continue
            resolved = candidate.resolve()
            try:
                resolved.relative_to(repo_root)
            except ValueError:
                continue
            if resolved in seen or _is_in_skipped_dir(resolved, repo_root):
                continue
            seen.add(resolved)
            yield resolved


def _is_in_skipped_dir(path: Path, repo_root: Path) -> bool:
    rel_parts = path.relative_to(repo_root).parts
    return any(part in _SKIPPED_DIRS for part in rel_parts[:-1])


def _find_noqa_markers_in_file(path: Path) -> Iterator[NoqaMarker]:
    with tokenize.open(path) as handle:
        tokens = tokenize.generate_tokens(handle.readline)
        for token in tokens:
            if token.type != tokenize.COMMENT:
                continue
            match = _NOQA_PATTERN.search(token.string)
            if match is None:
                continue
            codes = _normalize_codes(match.group("codes") or "<all>")
            reason = (match.group("reason") or "").strip()
            yield NoqaMarker(path=path, lineno=token.start[0], codes=codes, reason=reason)


def _normalize_codes(codes: str) -> str:
    return ", ".join(code.strip() for code in codes.split(",") if code.strip())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
