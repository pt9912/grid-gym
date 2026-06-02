"""Markdown-Link-Validator (Trigger 002, Welle-7-Audit-Erbe).

Scant alle Markdown-Dateien unter `docs/`, `spec/`, `harness/` sowie
`AGENTS.md` nach relativen `[text](path)`-Links und meldet alle nicht
aufgeloesten Pfade. Externe Links (`http://`, `https://`, `mailto:`,
`#anchor`-only) werden uebersprungen.

Stdlib-only — kein Runtime-Dep. Aufruf: `make docs-check` oder
direkt `python tools/check_refs.py`.

Scope-Abgrenzung (Trigger 002):
- Diese erste Variante deckt nur Markdown-Link-Pfade ab.
- Kennungs-Aufloesung (`GG-*`/`AC-*`/`ADR-NNNN`-Querverweise)
  und `§`-Sektions-Verweise bleiben fuer eine spaetere Erweiterung
  (siehe Closure-Notiz in `done/002-check-refs-tool.md`).

Output-Format pro Verstoss: `{source_rel}:{lineno}\t{target}\t{reason}`.
Exit-Code 0 = alle Links aufloesbar, 1 = mindestens ein Verstoss.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

# Markdown-Link `[text](target)`. `text` darf escapte Klammern enthalten,
# aber fuer den Minimal-Linter reicht non-greedy. Bilder `![alt](src)`
# fangen wir mit demselben Pattern — die Markdown-Spec erlaubt dort
# die gleiche Pfad-Syntax.
_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")

# Inline-Code `` `...` ``-Spans werden vor dem Link-Match aus der
# Zeile entfernt — Closure-Notizen demonstrieren Markdown-Patterns
# in Backticks (z. B. ``[text](path)``-Demo-Strings), die sonst als
# echte Links interpretiert wuerden.
_INLINE_CODE_PATTERN = re.compile(r"`+[^`]*`+")

# Pfade mit einem dieser Praefixe sind keine relativen Filesystem-Refs.
_EXTERNAL_PREFIXES: tuple[str, ...] = (
    "http://",
    "https://",
    "mailto:",
    "ftp://",
)


@dataclass(frozen=True, slots=True)
class BrokenRef:
    """Eine festgestellte, nicht aufloesbare Pfad-Referenz."""

    source: Path
    lineno: int
    target: str
    reason: str

    def format(self, repo_root: Path) -> str:
        rel = self.source.relative_to(repo_root)
        return f"{rel}:{self.lineno}\t{self.target}\t{self.reason}"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sources = _iter_markdown_files(repo_root)
    violations: list[BrokenRef] = []
    for source in sources:
        violations.extend(_check_file(repo_root, source))
    if not violations:
        print("[check_refs] all markdown link targets resolved")
        return 0
    for violation in violations:
        print(violation.format(repo_root), file=sys.stderr)
    print(
        f"[check_refs] {len(violations)} broken markdown reference(s) — see stderr",
        file=sys.stderr,
    )
    return 1


def _iter_markdown_files(repo_root: Path) -> Iterator[Path]:
    """Liefert alle Harness-relevanten `*.md`-Dateien.

    Andere Top-Level-Verzeichnisse (z. B. `tests/`, `tools/`)
    enthalten heute keine fachlichen Markdown-Querverweise; bei Bedarf
    in spaeteren Wellen erweitern.
    """
    agents = repo_root / "AGENTS.md"
    if agents.exists():
        yield agents
    for top in ("docs", "spec", "harness"):
        root = repo_root / top
        if not root.exists():
            continue
        yield from sorted(root.rglob("*.md"))


def _check_file(repo_root: Path, source: Path) -> Iterator[BrokenRef]:
    text = source.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        # Inline-Code-Spans (``...``) ausblenden, damit Demo-Strings
        # in Backticks nicht als echte Links interpretiert werden.
        scannable = _INLINE_CODE_PATTERN.sub("", line)
        for match in _LINK_PATTERN.finditer(scannable):
            target = match.group(1).strip()
            problem = _classify_target(repo_root, source, target)
            if problem is not None:
                yield BrokenRef(source=source, lineno=lineno, target=target, reason=problem)


def _classify_target(repo_root: Path, source: Path, target: str) -> str | None:
    """`None` wenn der Target aufloesbar (oder bewusst extern) ist,
    sonst Begruendungs-String.

    Drei Phasen: (1) externe/leere/anker-only Targets fruehzeitig
    aussondern, (2) Pfad-Form pruefen, (3) Resolve + Existenz-
    Check.
    """
    if _is_external_or_anchor(target):
        return None
    path_part = target.split("#", 1)[0]
    if not path_part:
        return None
    if path_part.startswith("/"):
        return "absolute path; expected repo-relative"
    return _check_relative_path(repo_root, source, path_part)


def _is_external_or_anchor(target: str) -> bool:
    """`True` fuer Targets, die nicht als Repo-Pfad zu pruefen sind:
    leerer String, reine `#anchor`-Refs (siehe Trigger 002 v2-Scope),
    `http://`, `https://`, `mailto:`, `ftp://`.
    """
    if not target or target.startswith("#"):
        return True
    return target.startswith(_EXTERNAL_PREFIXES)


def _check_relative_path(repo_root: Path, source: Path, path_part: str) -> str | None:
    """Resolve `path_part` relativ zu `source.parent` und prueft
    Existenz im Repo."""
    candidate = (source.parent / path_part).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError:
        return f"escapes repo root ({candidate})"
    if not candidate.exists():
        return "target file does not exist"
    return None


if __name__ == "__main__":
    raise SystemExit(main())
