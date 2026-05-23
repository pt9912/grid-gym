"""Architektur-Check fuer grid-gym (ADR 0002 §A-1).

Implementiert die Contracts, die `import-linter` und `ruff` nicht
abdecken — AST- und Graph-basierte Pruefungen ueber den
Importgraph und die Modulinhalte unter `src/grid_gym/`.

Welle 3 deckt:
- AC-HEXAGON-PURE — Whitelist-Imports unter `hexagon/**`
- AC-NO-JSON — `json.dumps`/`json.dump` ausserhalb der Whitelist
- AC-NO-TIME — Wall-Clock-/Monotonic-Aufrufe unter `hexagon/core/**`
- AC-NO-RAND — Random-Aufrufe (`random.*`/`secrets.*`/`numpy.random.*`)
  unter `hexagon/core/**` (Aufruf-Site)
- AC-DOMAIN-FROZEN — Klassen unter `hexagon/core/domain/**` sind
  frozen (Frozen-Dataclass, `FrozenModel`-Vererbung oder
  `Enum`-Subklasse — Enum-Member sind by-construction immutable;
  Enum-Form per `ADR 0008` als dritte zulaessige Frozen-Konvention
  zu `ADR 0002 §A-1` ergaenzt)
- AC-NO-GOD-UTILS — Modul-/Klassen-Namens-Heuristik plus
  oeffentliche-Funktionen-Count
- AC-TYPED-ERRORS — kein `raise Exception(...)` / `except Exception:`
  ausserhalb der `typed-errors-exempt`-Liste
- AC-NO-CYCLES — keine Importzyklen (via `grimp`)
- AC-ADAPTER-LIGHTWEIGHT — zyklomatische Komplexitaet `<= 8` fuer
  Adapter-Funktionen
- AC-NO-COVERAGE-PRAGMA — kein `# pragma: no cover`, `# pragma: no
  branch` oder `# pragma: exclude file` im Repo (Coverage-Gate-
  Disziplin; Protocol-Stubs werden ueber das
  `coverage.report.exclude_lines`-Pattern `\\.\\.\\.` abgedeckt,
  Dead-Code wird geloescht, defensives `if not isinstance(...)` nach
  Vorvalidierung wird ueber `typing.cast` ersetzt)

Konfiguration kommt aus `[tool.grid_gym.arch_check]` in
`pyproject.toml`. Exit-Code 0 = alle Contracts kept, 1 = mindestens
ein Verstoss; Verstoesse landen auf stderr im Format
`{contract_id}\\t{location}\\t{detail}`.
"""

from __future__ import annotations

import ast
import fnmatch
import sys
import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import grimp

# Stdlib-Module, die in `hexagon/**` ohne Whitelist erlaubt sind.
_STDLIB_NAMES: frozenset[str] = frozenset(sys.stdlib_module_names)

# Interner Top-Level-Paketname; jeder Import unterhalb gilt als intern.
_INTERNAL_PACKAGE = "grid_gym"

# AC-NO-TIME — Wall-Clock-/Monotonic-Aufrufe.
_TIME_MODULE = "time"
_TIME_ATTRS: frozenset[str] = frozenset(
    {"time", "monotonic", "perf_counter", "perf_counter_ns", "process_time"}
)

# AC-NO-RAND — Zufalls-Aufrufe.
_RAND_TOP_LEVELS: frozenset[str] = frozenset({"random", "secrets"})
_NUMPY_MODULE = "numpy"
_NUMPY_RANDOM_ATTR = "random"


@dataclass(frozen=True, slots=True)
class Violation:
    """Eine festgestellte Contract-Verletzung."""

    contract_id: str
    location: str
    detail: str

    def format(self) -> str:
        return f"{self.contract_id}\t{self.location}\t{self.detail}"


@dataclass(frozen=True, slots=True)
class ArchCheckConfig:
    """Whitelists aus `[tool.grid_gym.arch_check]`."""

    json_dumps_whitelist: tuple[str, ...]
    domain_frozen_extra: tuple[str, ...]
    typed_errors_exempt: tuple[str, ...]
    hexagon_import_whitelist: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ImportAliases:
    """Pro-Datei-Map: erlaubt Aufloesung aliased Imports auf den
    tatsaechlichen Modul-Namen.

    - `import json` → `module_aliases["json"] = "json"`
    - `import json as j` → `module_aliases["j"] = "json"`
    - `import numpy.random as nr` → `module_aliases["nr"] = "numpy.random"`
    - `import numpy.random` → `module_aliases["numpy"] = "numpy"` (Python
      bindet nur das Top-Level)
    - `from json import dumps` → `from_imports["dumps"] = ("json", "dumps")`
    - `from time import monotonic as m` → `from_imports["m"] = ("time", "monotonic")`

    Hinweis: `_collect_imports` nutzt `ast.walk`, sammelt also auch
    nested Imports (in Funktionen / Klassen). Das ist gewollt:
    `def f(): from time import monotonic` ist syntaktisch lokal,
    aber `monotonic()`-Aufrufe sollen file-weit als AC-NO-TIME-
    Verstoss erkannt werden — Re-Export-Tricks rutschen sonst durch.

    Wildcard-Imports (`from X import *`) werden NICHT erfasst —
    Aufrufer pruefen das ggf. separat.
    """

    module_aliases: dict[str, str]
    from_imports: dict[str, tuple[str, str]]


def _collect_imports(tree: ast.Module) -> ImportAliases:
    module_aliases: dict[str, str] = {}
    from_imports: dict[str, tuple[str, str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    module_aliases[alias.asname] = alias.name
                else:
                    top_level = alias.name.split(".")[0]
                    module_aliases[top_level] = top_level
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            for alias in node.names:
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                from_imports[local] = (node.module, alias.name)
    return ImportAliases(module_aliases=module_aliases, from_imports=from_imports)


def _attribute_chain(node: ast.expr) -> tuple[str, ...] | None:
    """Erweitert eine `ast.Attribute`-Kette zu Namens-Komponenten.

    Gibt `None` zurueck, wenn die Kette nicht in einem `ast.Name` endet
    (z. B. bei dynamischen Aufrufen ueber Subscripts oder Calls).
    """
    parts: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return tuple(reversed(parts))
    return None


def _resolve_call_chain(call: ast.Call, aliases: ImportAliases) -> tuple[str, ...] | None:
    """Loest die Attribute-Kette einer Funktions-Call auf, indem das
    erste Element via `aliases.module_aliases` ersetzt wird.

    Beispiele (jeweils mit den passenden Imports oben):
    - `time.time()` → `("time", "time")`
    - `t.time()` nach `import time as t` → `("time", "time")`
    - `nr.rand()` nach `import numpy.random as nr` → `("numpy", "random", "rand")`
    - `numpy.random.rand()` nach `import numpy` → `("numpy", "random", "rand")`

    Bare-name Calls (`monotonic()` nach `from time import monotonic`)
    geben `None` zurueck; Aufrufer muss `aliases.from_imports` separat
    konsultieren.

    Bekannte Schwaeche: rebindings ueber lokale Variablen mit
    Modul-Namen (`import json; def f(): json = obj; json.foo()`)
    triggern weiterhin den Modul-Alias-Pfad und erzeugen
    False-Positives. In der Praxis durch `PLR0915` /
    `N`-Naming-Conventions gefangen — keine separate AST-Heuristik
    erforderlich.
    """
    chain = _attribute_chain(call.func)
    if chain is None or len(chain) < _MIN_RESOLVABLE_CHAIN_LEN:
        return None
    head = chain[0]
    resolved_head = aliases.module_aliases.get(head)
    if resolved_head is None:
        return None
    return tuple(resolved_head.split(".")) + chain[1:]


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    config = _load_config(repo_root)
    src_root = repo_root / "src" / _INTERNAL_PACKAGE

    violations: list[Violation] = []
    if src_root.exists():
        violations.extend(_check_hexagon_pure(repo_root, src_root, config))
        violations.extend(_check_no_json(repo_root, src_root, config))
        violations.extend(_check_no_time(repo_root, src_root))
        violations.extend(_check_no_rand(repo_root, src_root))
        violations.extend(_check_no_io_mod_nested(repo_root, src_root))
        violations.extend(_check_domain_frozen(repo_root, src_root, config))
        violations.extend(_check_no_god_utils(repo_root, src_root))
        violations.extend(_check_typed_errors(repo_root, src_root, config))
        violations.extend(_check_no_cycles())
        violations.extend(_check_adapter_lightweight(repo_root, src_root))
        violations.extend(_check_no_coverage_pragma(repo_root, src_root))

    for violation in violations:
        print(violation.format(), file=sys.stderr)

    if violations:
        print(
            f"[arch_check] {len(violations)} violation(s) — see stderr",
            file=sys.stderr,
        )
        return 1

    print("[arch_check] all contracts kept")
    return 0


def _load_config(repo_root: Path) -> ArchCheckConfig:
    pyproject_path = repo_root / "pyproject.toml"
    with pyproject_path.open("rb") as fh:
        data: dict[str, Any] = tomllib.load(fh)
    section: dict[str, Any] = data.get("tool", {}).get("grid_gym", {}).get("arch_check", {})
    return ArchCheckConfig(
        json_dumps_whitelist=tuple(section.get("json-dumps-whitelist", [])),
        domain_frozen_extra=tuple(section.get("domain-frozen-extra", [])),
        typed_errors_exempt=tuple(section.get("typed-errors-exempt", [])),
        hexagon_import_whitelist=tuple(section.get("hexagon-import-whitelist", [])),
    )


# ---------------------------------------------------------------------------
# Datei-Walker und AST-Helfer
# ---------------------------------------------------------------------------


def _iter_py_files(root: Path) -> Iterator[Path]:
    if not root.exists():
        return
    yield from sorted(root.rglob("*.py"))


def _parse(py_file: Path) -> ast.Module:
    return ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))


def _rel(repo_root: Path, py_file: Path) -> str:
    """Relativer Pfad als String mit Forward-Slash-Separator,
    unabhaengig vom OS. Whitelist-Strings in `pyproject.toml` nutzen
    `/`; Path-Native-Separator auf Windows waere `\\` und wuerde
    Exakt-Vergleiche brechen."""
    return str(py_file.relative_to(repo_root)).replace("\\", "/")


def _matches_any(rel_path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns)


# ---------------------------------------------------------------------------
# AC-HEXAGON-PURE
# ---------------------------------------------------------------------------


def _check_hexagon_pure(
    repo_root: Path, src_root: Path, config: ArchCheckConfig
) -> Iterator[Violation]:
    hexagon_root = src_root / "hexagon"
    whitelist = frozenset(config.hexagon_import_whitelist)
    for py_file in _iter_py_files(hexagon_root):
        tree = _parse(py_file)
        rel = _rel(repo_root, py_file)
        for node in ast.walk(tree):
            yield from _hexagon_pure_violations(node, rel, whitelist)


def _hexagon_pure_violations(
    node: ast.AST, rel: str, whitelist: frozenset[str]
) -> Iterator[Violation]:
    if isinstance(node, ast.Import):
        for alias in node.names:
            if not _is_allowed_hexagon_import(alias.name, whitelist):
                yield Violation(
                    "AC-HEXAGON-PURE",
                    f"{rel}:{node.lineno}",
                    f"import {alias.name}",
                )
    elif (
        isinstance(node, ast.ImportFrom)
        and node.module is not None
        and not _is_allowed_hexagon_import(node.module, whitelist)
    ):
        yield Violation(
            "AC-HEXAGON-PURE",
            f"{rel}:{node.lineno}",
            f"from {node.module} import ...",
        )


def _is_allowed_hexagon_import(module_name: str, whitelist: frozenset[str]) -> bool:
    top_level = module_name.split(".", 1)[0]
    if top_level in _STDLIB_NAMES:
        return True
    if top_level == _INTERNAL_PACKAGE:
        return True
    return module_name in whitelist or top_level in whitelist


# ---------------------------------------------------------------------------
# AC-NO-JSON
# ---------------------------------------------------------------------------


_JSON_DUMP_NAMES: frozenset[str] = frozenset({"dumps", "dump"})


def _check_no_json(repo_root: Path, src_root: Path, config: ArchCheckConfig) -> Iterator[Violation]:
    whitelist = frozenset(config.json_dumps_whitelist)
    for py_file in _iter_py_files(src_root):
        rel = _rel(repo_root, py_file)
        if rel in whitelist:
            continue
        tree = _parse(py_file)
        aliases = _collect_imports(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            attr = _json_dump_attr(node, aliases)
            if attr is not None:
                yield Violation(
                    "AC-NO-JSON",
                    f"{rel}:{node.lineno}",
                    f"json.{attr}() — use canonical_json()",
                )


def _json_dump_attr(call: ast.Call, aliases: ImportAliases) -> str | None:
    """Gibt 'dumps'/'dump' zurueck, falls `call` direkt oder via
    Alias / from-import ein `json.dumps()` / `json.dump()` ist."""
    # Direkt: `json.dumps(...)` oder `j.dumps(...)` nach `import json as j`.
    chain = _resolve_call_chain(call, aliases)
    if chain is not None and chain[0] == "json" and chain[-1] in _JSON_DUMP_NAMES:
        return chain[-1]
    # Bare: `dumps(...)` nach `from json import dumps`.
    if isinstance(call.func, ast.Name):
        source = aliases.from_imports.get(call.func.id)
        if source is not None and source[0] == "json" and source[1] in _JSON_DUMP_NAMES:
            return source[1]
    return None


# ---------------------------------------------------------------------------
# AC-NO-TIME
# ---------------------------------------------------------------------------


def _check_no_time(repo_root: Path, src_root: Path) -> Iterator[Violation]:
    core_root = src_root / "hexagon" / "core"
    for py_file in _iter_py_files(core_root):
        tree = _parse(py_file)
        rel = _rel(repo_root, py_file)
        aliases = _collect_imports(tree)
        for node in ast.walk(tree):
            yield from _no_time_violations(node, rel, aliases)


def _no_time_violations(node: ast.AST, rel: str, aliases: ImportAliases) -> Iterator[Violation]:
    # `from time import ...` ist im Kern grundsaetzlich verboten —
    # auch wenn die importierte Funktion nicht in _TIME_ATTRS steht,
    # weil `time.sleep`/`time.tzname` etc. ebenfalls Wall-Clock-Logik
    # nahelegen und im Kern nichts zu suchen haben.
    if isinstance(node, ast.ImportFrom) and node.module == _TIME_MODULE:
        imported = ", ".join(a.asname or a.name for a in node.names)
        yield Violation(
            "AC-NO-TIME",
            f"{rel}:{node.lineno}",
            f"from time import {imported} — use ClockPort",
        )
        return
    if not isinstance(node, ast.Call):
        return
    attr = _time_call_attr(node, aliases)
    if attr is None:
        return
    if attr.startswith("asyncio."):
        # asyncio.get_event_loop().time() — bereits voll-qualifiziert
        detail = f"{attr}() (via alias or attribute) — use ClockPort"
    else:
        detail = f"time.{attr}() (via alias or attribute) — use ClockPort"
    yield Violation("AC-NO-TIME", f"{rel}:{node.lineno}", detail)


def _time_call_attr(call: ast.Call, aliases: ImportAliases) -> str | None:
    """Erkennt forbidden time-Aufrufe an den Aufruf-Sites:

    - `time.<attr>()` (auch via `import time as t; t.<attr>()`)
    - `<attr>()` nach `from time import <attr>` (oder `as`)
    - `asyncio.get_event_loop().time()` (ADR 0002 §A-1 expliziter
      Bestandteil von AC-NO-TIME; auch via `import asyncio as a` oder
      `from asyncio import get_event_loop`)
    """
    chain = _resolve_call_chain(call, aliases)
    if chain is not None and chain[0] == _TIME_MODULE and chain[-1] in _TIME_ATTRS:
        return chain[-1]
    if isinstance(call.func, ast.Name):
        source = aliases.from_imports.get(call.func.id)
        if source is not None and source[0] == _TIME_MODULE and source[1] in _TIME_ATTRS:
            return source[1]
    if _is_asyncio_event_loop_time_call(call, aliases):
        return "asyncio.get_event_loop().time"
    return None


def _is_asyncio_event_loop_time_call(call: ast.Call, aliases: ImportAliases) -> bool:
    """True wenn `call` der Form `asyncio.get_event_loop().time()` ist
    (auch via Alias auf `asyncio` oder `from asyncio import get_event_loop`).
    """
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr != "time":
        return False
    inner_call = func.value
    if not isinstance(inner_call, ast.Call):
        return False
    # Variante A: asyncio.get_event_loop() — attribute call
    inner_chain = _resolve_call_chain(inner_call, aliases)
    if (
        inner_chain is not None
        and inner_chain[0] == "asyncio"
        and inner_chain[-1] == "get_event_loop"
    ):
        return True
    # Variante B: get_event_loop() — bare name nach from-import
    inner_func = inner_call.func
    if isinstance(inner_func, ast.Name):
        source = aliases.from_imports.get(inner_func.id)
        if source is not None and source[0] == "asyncio" and source[1] == "get_event_loop":
            return True
    return False


# ---------------------------------------------------------------------------
# AC-NO-RAND
# ---------------------------------------------------------------------------


_NUMPY_RANDOM_PATH: tuple[str, str] = (_NUMPY_MODULE, _NUMPY_RANDOM_ATTR)
_NUMPY_RANDOM_PATH_DOTTED: str = f"{_NUMPY_MODULE}.{_NUMPY_RANDOM_ATTR}"

# Minimal-Laengen fuer aufgeloeste Attribute-Ketten: ein `head.attr`-Call
# braucht mindestens 2 Teile (Head + Methoden-Name); fuer `numpy.random.X()`
# entsprechend 3 (Modul-Praefix + Methode).
_MIN_RESOLVABLE_CHAIN_LEN = 2
_NUMPY_RANDOM_CHAIN_MIN_LEN = 3


def _check_no_rand(repo_root: Path, src_root: Path) -> Iterator[Violation]:
    core_root = src_root / "hexagon" / "core"
    for py_file in _iter_py_files(core_root):
        tree = _parse(py_file)
        rel = _rel(repo_root, py_file)
        aliases = _collect_imports(tree)
        for node in ast.walk(tree):
            yield from _no_rand_violations(node, rel, aliases)


def _no_rand_violations(node: ast.AST, rel: str, aliases: ImportAliases) -> Iterator[Violation]:
    # `from random import ...`, `from secrets import ...`,
    # `from numpy.random import ...` sind im Kern grundsaetzlich verboten.
    if isinstance(node, ast.ImportFrom):
        source = node.module
        if source in _RAND_TOP_LEVELS or source == _NUMPY_RANDOM_PATH_DOTTED:
            imported = ", ".join(a.asname or a.name for a in node.names)
            yield Violation(
                "AC-NO-RAND",
                f"{rel}:{node.lineno}",
                f"from {source} import {imported} — use RandomPort",
            )
            return
    if not isinstance(node, ast.Call):
        return
    detail = _rand_call_detail(node, aliases)
    if detail is not None:
        yield Violation("AC-NO-RAND", f"{rel}:{node.lineno}", detail)


def _rand_call_detail(call: ast.Call, aliases: ImportAliases) -> str | None:
    chain = _resolve_call_chain(call, aliases)
    if chain is not None:
        # `random.X(...)` / `secrets.X(...)` (auch via Alias)
        if chain[0] in _RAND_TOP_LEVELS and len(chain) >= _MIN_RESOLVABLE_CHAIN_LEN:
            return f"{chain[0]}.{chain[-1]}() — use RandomPort"
        # `numpy.random.X(...)` (auch via Alias auf `numpy.random`)
        if len(chain) >= _NUMPY_RANDOM_CHAIN_MIN_LEN and chain[:2] == _NUMPY_RANDOM_PATH:
            return f"numpy.random.{chain[-1]}() — use RandomPort"
    if isinstance(call.func, ast.Name):
        source = aliases.from_imports.get(call.func.id)
        if source is None:
            return None
        src_mod = source[0]
        if src_mod in _RAND_TOP_LEVELS or src_mod == _NUMPY_RANDOM_PATH_DOTTED:
            return f"{src_mod}.{source[1]}() — use RandomPort"
    return None


# ---------------------------------------------------------------------------
# AC-NO-IO-MOD (nested stdlib subpackages, hexagon/core only)
# ---------------------------------------------------------------------------

_NESTED_BANNED_IO_MODULES: frozenset[str] = frozenset(
    {"urllib.request", "http.client", "logging.handlers"}
)


def _check_no_io_mod_nested(repo_root: Path, src_root: Path) -> Iterator[Violation]:
    """AC-NO-IO-MOD (Subpaket-Anteil): import-linter unterstuetzt keine
    Subpakete externer Pakete als `forbidden_modules`. `urllib.request`,
    `http.client`, `logging.handlers` werden hier per AST gefangen — sie
    duerfen unter `hexagon/core/**` weder direkt noch via `from ... import`
    importiert werden.
    """
    core_root = src_root / "hexagon" / "core"
    for py_file in _iter_py_files(core_root):
        tree = _parse(py_file)
        rel = _rel(repo_root, py_file)
        for node in ast.walk(tree):
            yield from _no_io_mod_nested_violations(node, rel)


def _no_io_mod_nested_violations(node: ast.AST, rel: str) -> Iterator[Violation]:
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name in _NESTED_BANNED_IO_MODULES:
                yield Violation(
                    "AC-NO-IO-MOD",
                    f"{rel}:{node.lineno}",
                    f"import {alias.name}",
                )
    elif (
        isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module in _NESTED_BANNED_IO_MODULES
    ):
        yield Violation(
            "AC-NO-IO-MOD",
            f"{rel}:{node.lineno}",
            f"from {node.module} import ...",
        )


# ---------------------------------------------------------------------------
# AC-DOMAIN-FROZEN
# ---------------------------------------------------------------------------


def _check_domain_frozen(
    repo_root: Path, src_root: Path, config: ArchCheckConfig
) -> Iterator[Violation]:
    """AC-DOMAIN-FROZEN: nur Top-Level-Klassen unter `hexagon/core/domain/**`
    werden geprueft (kein `ast.walk` — verschachtelte Klassen in
    Funktionen / Tests sind Implementierungsdetail).

    Zulaessig:
    - `@dataclass(frozen=True, slots=True)` mit beiden Keywords als
      `ast.Constant(value=True)`.
    - Vererbung von `FrozenModel` (`ast.Name` oder `ast.Attribute`
      mit `attr == "FrozenModel"`).
    - Vererbung von `Enum`/`StrEnum`/`IntEnum`/`Flag`/`IntFlag`/
      `ReprEnum` (Bare-Name oder `enum.*`-Attribute). Begruendung:
      Enum-Member sind in Python by-construction immutable — die
      Member-Werte koennen nach Klassenerstellung nicht
      ueberschrieben werden, `enum.Enum.__init_subclass__`
      blockiert Re-Definition. Diese Erweiterung ist in `ADR 0008`
      verankert (Folge-ADR zu `ADR 0002 §A-1`, reine Erweiterung
      ohne Supersedes per `ADR 0006 §3`).
    """
    domain_root = src_root / "hexagon" / "core" / "domain"
    paths_to_check: list[Path] = list(_iter_py_files(domain_root))
    for extra in config.domain_frozen_extra:
        extra_path = repo_root / extra
        if extra_path.is_dir():
            paths_to_check.extend(_iter_py_files(extra_path))
        elif extra_path.is_file():
            paths_to_check.append(extra_path)

    for py_file in paths_to_check:
        tree = _parse(py_file)
        rel = _rel(repo_root, py_file)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and not _is_frozen_class(node):
                yield Violation(
                    "AC-DOMAIN-FROZEN",
                    f"{rel}:{node.lineno}",
                    f"class `{node.name}` is not frozen "
                    "(need @dataclass(frozen=True, slots=True) or FrozenModel)",
                )


def _is_frozen_class(node: ast.ClassDef) -> bool:
    return (
        _has_frozen_dataclass_decorator(node)
        or _inherits_frozen_model(node)
        or _inherits_enum(node)
    )


# Enum-Basisklassen, deren Vererbung als AC-DOMAIN-FROZEN-Form gilt.
# Verankert in `ADR 0008` §2 (Folge-ADR zu `ADR 0002 §A-1`).
# Erweiterung dieser Liste erfordert eine weitere Folge-ADR.
_ENUM_BASE_NAMES: frozenset[str] = frozenset(
    {"Enum", "StrEnum", "IntEnum", "Flag", "IntFlag", "ReprEnum"}
)


def _inherits_enum(node: ast.ClassDef) -> bool:
    """True wenn `node` von einer `enum`-Basisklasse erbt.

    Erkennt sowohl Bare-Name-Imports (`from enum import StrEnum`
    → `class Q(StrEnum): ...`) als auch Attribut-Zugriffe
    (`import enum` → `class Q(enum.StrEnum): ...`). Andere Module,
    die zufaellig eine `StrEnum`-Klasse re-exportieren, matchen
    ebenfalls — das ist die etablierte Konvention der
    `FrozenModel`-Erkennung (literal-Name, kein Import-Resolving).
    """
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id in _ENUM_BASE_NAMES:
            return True
        if isinstance(base, ast.Attribute) and base.attr in _ENUM_BASE_NAMES:
            return True
    return False


def _has_frozen_dataclass_decorator(node: ast.ClassDef) -> bool:
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        if (
            _is_dataclass_decorator_target(dec.func)
            and _has_keyword_true(dec, "frozen")
            and _has_keyword_true(dec, "slots")
        ):
            return True
    return False


def _is_dataclass_decorator_target(func: ast.expr) -> bool:
    if isinstance(func, ast.Name):
        return func.id == "dataclass"
    if isinstance(func, ast.Attribute):
        return func.attr == "dataclass"
    return False


def _has_keyword_true(decorator: ast.Call, kwarg_name: str) -> bool:
    """True wenn `decorator` ein `kwarg_name=True`-Keyword als
    `ast.Constant(value=True)` hat.

    Strikt literal-True: `frozen=True` ja, `frozen=bool(1)` nein,
    `_FROZEN = True; @dataclass(frozen=_FROZEN)` nein. Konvention
    in `hexagon.core.domain.**` ist literal-True — `Final`-Aliases
    oder Variable-Rebinds bei Decorator-Kwargs sind dort unueblich.
    """
    for kw in decorator.keywords:
        if kw.arg == kwarg_name and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            return True
    return False


def _inherits_frozen_model(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "FrozenModel":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "FrozenModel":
            return True
    return False


# ---------------------------------------------------------------------------
# AC-NO-GOD-UTILS
# ---------------------------------------------------------------------------

_BAD_MODULE_STEMS: frozenset[str] = frozenset({"helpers", "common", "misc"})
_BAD_MODULE_SUFFIXES: tuple[str, ...] = ("_utils",)
_BAD_CLASS_SUFFIXES: tuple[str, ...] = ("Utils", "Helper", "Manager", "Misc")
_GOD_UTIL_EXEMPT_PATH_FRAGMENTS: tuple[str, ...] = (
    "src/grid_gym/hexagon/core/domain",
    "src/grid_gym/hexagon/core/serialization",
)
_MAX_PUBLIC_TOPLEVEL_FUNCTIONS = 5


def _is_god_util_exempt(rel: str) -> bool:
    """True wenn `rel` als File unter einem der Exempt-Praefixe liegt.

    Strikt `startswith(fragment + "/")`: ein Geschwister-Pfad wie
    `domain_extra/` matched NICHT das `domain/`-Praefix, anders als
    bei naivem Substring-Match (`fragment in rel`).
    """
    return any(rel.startswith(fragment + "/") for fragment in _GOD_UTIL_EXEMPT_PATH_FRAGMENTS)


def _check_no_god_utils(repo_root: Path, src_root: Path) -> Iterator[Violation]:
    for py_file in _iter_py_files(src_root):
        rel = _rel(repo_root, py_file)
        yield from _module_name_violations(py_file, rel)
        tree = _parse(py_file)
        yield from _class_name_violations(tree, rel)
        yield from _public_function_count_violations(tree, rel)


def _module_name_violations(py_file: Path, rel: str) -> Iterator[Violation]:
    stem = py_file.stem
    if stem in _BAD_MODULE_STEMS or stem.endswith(_BAD_MODULE_SUFFIXES):
        yield Violation(
            "AC-NO-GOD-UTILS",
            rel,
            f"forbidden module name: {py_file.name}",
        )


def _class_name_violations(tree: ast.Module, rel: str) -> Iterator[Violation]:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name.endswith(_BAD_CLASS_SUFFIXES):
            yield Violation(
                "AC-NO-GOD-UTILS",
                f"{rel}:{node.lineno}",
                f"class name ends with forbidden suffix: {node.name}",
            )


def _public_function_count_violations(tree: ast.Module, rel: str) -> Iterator[Violation]:
    """ADR 0002 §A-1 zaehlt nur 'oeffentliche freie Funktionen' auf
    Modul-Ebene. Klassen mit vielen oeffentlichen Methoden sind
    out-of-scope hier — ruffs `PLR0904` (`max-public-methods=12`)
    deckt diese Heuristik ab. Wer einen God-Utility-Klassen-Bypass
    versucht (`class Toolkit: def fn1; def fn2; ...`), wird durch
    `PLR0904` aufgefangen.

    Exempt-Pfad-Match nutzt strikt `startswith(fragment + "/")` —
    Substring-Match wuerde `domain_extra/` faelschlich als „in
    domain/" zaehlen.
    """
    if _is_god_util_exempt(rel):
        return
    public_funcs = sum(
        1
        for child in tree.body
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
        and not child.name.startswith("_")
    )
    if public_funcs > _MAX_PUBLIC_TOPLEVEL_FUNCTIONS:
        yield Violation(
            "AC-NO-GOD-UTILS",
            rel,
            f"{public_funcs} public top-level functions (max {_MAX_PUBLIC_TOPLEVEL_FUNCTIONS})",
        )


# ---------------------------------------------------------------------------
# AC-TYPED-ERRORS
# ---------------------------------------------------------------------------

_FORBIDDEN_EXCEPTION_NAMES: frozenset[str] = frozenset({"Exception", "BaseException"})


def _check_typed_errors(
    repo_root: Path, src_root: Path, config: ArchCheckConfig
) -> Iterator[Violation]:
    exempt_patterns = config.typed_errors_exempt
    for py_file in _iter_py_files(src_root):
        rel = _rel(repo_root, py_file)
        is_exempt = _matches_any(rel, exempt_patterns)
        tree = _parse(py_file)
        for node in ast.walk(tree):
            yield from _typed_errors_violations(node, rel, is_exempt=is_exempt)


def _typed_errors_violations(node: ast.AST, rel: str, *, is_exempt: bool) -> Iterator[Violation]:
    if isinstance(node, ast.Raise):
        name = _raised_exception_name(node)
        if name in _FORBIDDEN_EXCEPTION_NAMES:
            yield Violation(
                "AC-TYPED-ERRORS",
                f"{rel}:{node.lineno}",
                f"raise {name}(...) — use GridGymError subclass",
            )
    elif isinstance(node, ast.ExceptHandler) and not is_exempt:
        caught = _handler_catches_forbidden(node.type)
        if caught is not None:
            yield Violation(
                "AC-TYPED-ERRORS",
                f"{rel}:{node.lineno}",
                f"except {caught} outside boundary-translation",
            )


def _handler_catches_forbidden(node_type: ast.expr | None) -> str | None:
    """Gibt den Namen der gefangenen verbotenen Exception zurueck —
    abgedeckt: `except Exception`, `except (Exception, X)`,
    `except builtins.Exception`, `except (mod.Exception, ...)`."""
    if node_type is None:
        return None
    if isinstance(node_type, ast.Name):
        return node_type.id if node_type.id in _FORBIDDEN_EXCEPTION_NAMES else None
    if isinstance(node_type, ast.Attribute):
        return node_type.attr if node_type.attr in _FORBIDDEN_EXCEPTION_NAMES else None
    if isinstance(node_type, ast.Tuple):
        for elt in node_type.elts:
            caught = _handler_catches_forbidden(elt)
            if caught is not None:
                return caught
    return None


def _raised_exception_name(node: ast.Raise) -> str | None:
    """Gibt den Namen der direkt geworfenen Exception zurueck —
    abgedeckt: `raise Exception`, `raise Exception(...)`,
    `raise builtins.Exception(...)`."""
    exc = node.exc
    if exc is None:
        return None
    target = exc.func if isinstance(exc, ast.Call) else exc
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


# ---------------------------------------------------------------------------
# AC-NO-CYCLES (Importzyklen via grimp)
# ---------------------------------------------------------------------------


def _check_no_cycles() -> Iterator[Violation]:
    """AC-NO-CYCLES — Importzyklen via grimp.

    Iteriert ueber alle direkten internen Import-Kanten und sucht
    Rueckpfade via `find_shortest_chain`. Jeder Zyklus wird ueber
    kanonische Rotation (lexikographisch kleinstes Modul am Anfang)
    dedupliziert, damit dieselbe Schleife nicht n-mal je Start-Wahl
    gemeldet wird.

    Fangt `Exception` breit, weil grimps API-Fehlerspektrum stabil
    weiterentwickelt wird (`NotATopLevelModule`, `ModuleNotPresent`,
    `NoSuchChainExists`, ...). Ein fehlgeschlagenes grimp-Query darf
    den Lauf nicht stillschweigend zerstoeren, deshalb Log auf stderr.
    """
    try:
        graph = grimp.build_graph(_INTERNAL_PACKAGE)
    except Exception as exc:  # noqa: BLE001 — grimp-API-Fehlerspektrum bewusst breit
        print(f"[arch_check] grimp build_graph failed: {exc}", file=sys.stderr)
        return

    seen_cycles: set[tuple[str, ...]] = set()
    for importer in sorted(graph.modules):
        if not importer.startswith(_INTERNAL_PACKAGE):
            continue
        try:
            direct_imports = graph.find_modules_directly_imported_by(importer)
        except Exception as exc:  # noqa: BLE001 — siehe oben
            print(
                f"[arch_check] grimp direct-imports failed for {importer}: {exc}",
                file=sys.stderr,
            )
            continue
        for imported in sorted(direct_imports):
            if not imported.startswith(_INTERNAL_PACKAGE):
                continue
            try:
                chain = graph.find_shortest_chain(imported, importer)
            except Exception as exc:  # noqa: BLE001 — siehe oben
                print(
                    f"[arch_check] grimp shortest-chain failed {imported}->{importer}: {exc}",
                    file=sys.stderr,
                )
                continue
            if not chain:
                continue
            full_cycle: tuple[str, ...] = (importer, *tuple(chain))
            canonical = _canonical_cycle(full_cycle)
            if canonical in seen_cycles:
                continue
            seen_cycles.add(canonical)
            yield Violation(
                "AC-NO-CYCLES",
                f"{importer} <-> {imported}",
                "cycle: " + " -> ".join(full_cycle),
            )


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    """Rotiert den Zyklus so, dass das alphabetisch kleinste Modul am
    Anfang steht. Dadurch wird derselbe Zyklus mit unterschiedlicher
    Start-Wahl auf die gleiche Kanonisierung abgebildet.

    Selbst-Zyklen (`A → A`) sind in grimp 3.x praktisch nicht
    erreichbar: `find_shortest_chain(A, A)` liefert in der Regel
    einen echten Rueckpfad oder `None`. Die `if not cycle: return`
    Sicherung deckt nur den theoretischen Fall ab, dass nach dem
    Schluss-Knoten-Strip ein leeres Tupel ueberbleibt.
    """
    # Closed cycles enden auf dem Start-Knoten — den fuer die Rotation
    # entfernen, sonst stimmt die Laenge nicht.
    if len(cycle) > 1 and cycle[0] == cycle[-1]:
        cycle = cycle[:-1]
    if not cycle:
        return cycle
    min_idx = min(range(len(cycle)), key=lambda i: cycle[i])
    return cycle[min_idx:] + cycle[:min_idx]


# ---------------------------------------------------------------------------
# AC-ADAPTER-LIGHTWEIGHT
# ---------------------------------------------------------------------------

_ADAPTER_MAX_COMPLEXITY = 8

# Minimal-Anzahl Pfad-Segmente fuer einen gueltigen Adapter-Pfad:
# `src/grid_gym/adapters/<layer>/<file>` = 5 Teile.
_ADAPTER_PATH_MIN_PARTS = 5


def _is_adapter_lightweight_path(rel: str) -> bool:
    """True wenn `rel` unter `src/grid_gym/adapters/driving/` (beliebige
    Tiefe) oder `src/grid_gym/adapters/driven/protocol_*` /
    `persistence_*` liegt.

    Eigener Matcher statt `fnmatch`, weil `fnmatch` `**` nicht als
    rekursive Wildcard unterstuetzt — und Adapter-Module duerfen direkt
    unter dem Driving-/Driven-Layer oder beliebig tief verschachtelt
    liegen.
    """
    parts = Path(rel).parts
    if len(parts) < _ADAPTER_PATH_MIN_PARTS or parts[:3] != (
        "src",
        "grid_gym",
        "adapters",
    ):
        return False
    layer = parts[3]
    if layer == "driving":
        return True
    if layer == "driven":
        bucket = parts[4]
        return bucket.startswith("protocol_") or bucket.startswith("persistence_")
    return False


def _check_adapter_lightweight(repo_root: Path, src_root: Path) -> Iterator[Violation]:
    adapters_root = src_root / "adapters"
    for py_file in _iter_py_files(adapters_root):
        rel = _rel(repo_root, py_file)
        if not _is_adapter_lightweight_path(rel):
            continue
        tree = _parse(py_file)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            complexity = _cyclomatic_complexity(node)
            if complexity > _ADAPTER_MAX_COMPLEXITY:
                yield Violation(
                    "AC-ADAPTER-LIGHTWEIGHT",
                    f"{rel}:{node.lineno}",
                    f"function `{node.name}` complexity {complexity} > {_ADAPTER_MAX_COMPLEXITY}",
                )


# ---------------------------------------------------------------------------
# AC-NO-COVERAGE-PRAGMA
# ---------------------------------------------------------------------------

# Forbiddene Coverage-Pragmas — Disziplin-Gate (M3-Welle-5-Folge).
# `pragma: no cover` und Geschwister markieren Code, der von der
# Coverage-Messung explizit ausgenommen wird. Erlaubt waeren sie nur
# fuer wirklich unerreichbaren Code; in der Praxis verstecken sie aber
# meist unzureichend getestete Pfade. Repo-Konvention: Protocol-Stubs
# werden ueber den `\\.\\.\\.`-Pattern in `[tool.coverage.report]
# exclude_lines` abgedeckt, defensives Dead-Code wird geloescht
# (`typing.cast` nach vorgelagerter Type-Validation), und echte
# Sub-Class-Pflicht-Methoden tragen `raise NotImplementedError`
# (das ebenfalls in `exclude_lines` steht).
_FORBIDDEN_COVERAGE_PRAGMAS: tuple[str, ...] = (
    "pragma: no cover",
    "pragma: no branch",
    "pragma: exclude file",
)


def _check_no_coverage_pragma(repo_root: Path, src_root: Path) -> Iterator[Violation]:
    """AC-NO-COVERAGE-PRAGMA — Coverage-Pragmas sind verboten.

    Scannt alle `*.py`-Dateien unter `src_root` zeilenweise nach den
    drei verbotenen Pragma-Markern. Auch in Kommentaren, Docstrings
    und Strings: ein `pragma: no cover` als String-Literal sollte
    es nicht geben (Test-Strings, die genau diesen Marker carry'n,
    waeren ein Wartungs-Risiko); falls so ein Bedarf real wird,
    haendelt das eine Folge-ADR.

    Tests (`tests/**`) sind nicht im Scan-Pfad — die Bug-Fix-
    Faelle, in denen ein Test temporaer einen Marker tragen wuerde,
    sind nicht durch `src_root` erfasst. Falls in Zukunft auch
    Tests gescannt werden sollen, wird dies dem Aufrufer in
    `main()` ueberlassen.
    """
    for py_file in _iter_py_files(src_root):
        rel = _rel(repo_root, py_file)
        for lineno, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), start=1):
            for marker in _FORBIDDEN_COVERAGE_PRAGMAS:
                if marker in line:
                    yield Violation(
                        "AC-NO-COVERAGE-PRAGMA",
                        f"{rel}:{lineno}",
                        f"`# {marker}` verboten (Coverage-Gate-Disziplin)",
                    )


def _cyclomatic_complexity(func: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Naehert ruffs `C901` McCabe-Komplexitaet an.

    Zaehlt: `If`, `For`, `While`, `ExceptHandler`, `IfExp` (ternaer),
    `Match`-Cases, `BoolOp` (jede Verkettung jenseits des ersten
    Operanden), Comprehension-`ifs`.

    Geht NICHT in nested `FunctionDef`/`AsyncFunctionDef`/`ClassDef`
    hinein — die haben einen eigenen Komplexitaets-Scope.

    Verhaeltnis zu ruff `C901`: Adapter-Lightweight nutzt Schwelle
    `> 8`, ruff `C901` ist auf `max-complexity = 10` gesetzt. Damit
    ist jede ruff-C901-Verletzung automatisch auch ein
    AC-ADAPTER-LIGHTWEIGHT-Verstoss; Adapter-Lightweight ist
    strenger. Bei Detail-Unterschieden in der Zaehlung (z. B.
    `assert`-Statements zaehlt mccabe historisch unterschiedlich)
    bleibt diese Reihenfolge.
    """
    complexity = 1
    for node in _iter_function_body_skip_nested(func):
        if isinstance(node, ast.If | ast.For | ast.While | ast.ExceptHandler | ast.IfExp):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
        elif isinstance(node, ast.Match):
            complexity += len(node.cases)
        elif isinstance(node, ast.comprehension):
            complexity += len(node.ifs)
    return complexity


def _iter_function_body_skip_nested(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Iterator[ast.AST]:
    """Iteriert ueber alle AST-Nodes im Funktionskoerper, springt aber
    nicht in verschachtelte `FunctionDef`/`AsyncFunctionDef`/`ClassDef`
    hinein."""
    stack: list[ast.AST] = list(func.body)
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        stack.extend(ast.iter_child_nodes(node))


if __name__ == "__main__":
    sys.exit(main())
