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
  frozen
- AC-NO-GOD-UTILS — Modul-/Klassen-Namens-Heuristik plus
  oeffentliche-Funktionen-Count
- AC-TYPED-ERRORS — kein `raise Exception(...)` / `except Exception:`
  ausserhalb der `typed-errors-exempt`-Liste
- AC-NO-CYCLES — keine Importzyklen (via `grimp`)
- AC-ADAPTER-LIGHTWEIGHT — zyklomatische Komplexitaet `<= 8` fuer
  Adapter-Funktionen

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
        violations.extend(_check_domain_frozen(repo_root, src_root, config))
        violations.extend(_check_no_god_utils(repo_root, src_root))
        violations.extend(_check_typed_errors(repo_root, src_root, config))
        violations.extend(_check_no_cycles())
        violations.extend(_check_adapter_lightweight(repo_root, src_root))

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
    section: dict[str, Any] = (
        data.get("tool", {}).get("grid_gym", {}).get("arch_check", {})
    )
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
    return str(py_file.relative_to(repo_root))


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


def _check_no_json(
    repo_root: Path, src_root: Path, config: ArchCheckConfig
) -> Iterator[Violation]:
    whitelist = frozenset(config.json_dumps_whitelist)
    for py_file in _iter_py_files(src_root):
        rel = _rel(repo_root, py_file)
        if rel in whitelist:
            continue
        tree = _parse(py_file)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            attr = _json_dump_attr(node)
            if attr is not None:
                yield Violation(
                    "AC-NO-JSON",
                    f"{rel}:{node.lineno}",
                    f"json.{attr}() — use canonical_json()",
                )


def _json_dump_attr(call: ast.Call) -> str | None:
    """Gibt 'dumps'/'dump' zurueck, falls `call` ein `json.dumps()` /
    `json.dump()` ist, sonst `None`."""
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None
    value = func.value
    if not isinstance(value, ast.Name):
        return None
    if value.id == "json" and func.attr in {"dumps", "dump"}:
        return func.attr
    return None


# ---------------------------------------------------------------------------
# AC-NO-TIME
# ---------------------------------------------------------------------------


def _check_no_time(repo_root: Path, src_root: Path) -> Iterator[Violation]:
    core_root = src_root / "hexagon" / "core"
    for py_file in _iter_py_files(core_root):
        tree = _parse(py_file)
        rel = _rel(repo_root, py_file)
        for node in ast.walk(tree):
            location = _time_call_location(node, rel)
            if location is not None:
                yield Violation("AC-NO-TIME", location[0], location[1])


def _time_call_location(node: ast.AST, rel: str) -> tuple[str, str] | None:
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if not isinstance(func, ast.Attribute):
        return None
    value = func.value
    if not isinstance(value, ast.Name):
        return None
    if value.id == _TIME_MODULE and func.attr in _TIME_ATTRS:
        return (f"{rel}:{node.lineno}", f"{value.id}.{func.attr}()")
    return None


# ---------------------------------------------------------------------------
# AC-NO-RAND
# ---------------------------------------------------------------------------


def _check_no_rand(repo_root: Path, src_root: Path) -> Iterator[Violation]:
    core_root = src_root / "hexagon" / "core"
    for py_file in _iter_py_files(core_root):
        tree = _parse(py_file)
        rel = _rel(repo_root, py_file)
        for node in ast.walk(tree):
            yield from _rand_call_violations(node, rel)


def _rand_call_violations(node: ast.AST, rel: str) -> Iterator[Violation]:
    if not isinstance(node, ast.Call):
        return
    func = node.func
    if not isinstance(func, ast.Attribute):
        return
    value = func.value
    # random.X(), secrets.X()
    if isinstance(value, ast.Name) and value.id in _RAND_TOP_LEVELS:
        yield Violation(
            "AC-NO-RAND",
            f"{rel}:{node.lineno}",
            f"{value.id}.{func.attr}() — use RandomPort",
        )
        return
    # numpy.random.X()
    if (
        isinstance(value, ast.Attribute)
        and isinstance(value.value, ast.Name)
        and value.value.id == _NUMPY_MODULE
        and value.attr == _NUMPY_RANDOM_ATTR
    ):
        yield Violation(
            "AC-NO-RAND",
            f"{rel}:{node.lineno}",
            f"numpy.random.{func.attr}() — use RandomPort",
        )


# ---------------------------------------------------------------------------
# AC-DOMAIN-FROZEN
# ---------------------------------------------------------------------------


def _check_domain_frozen(
    repo_root: Path, src_root: Path, config: ArchCheckConfig
) -> Iterator[Violation]:
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
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not _is_frozen_class(node):
                yield Violation(
                    "AC-DOMAIN-FROZEN",
                    f"{rel}:{node.lineno}",
                    f"class `{node.name}` is not frozen "
                    "(need @dataclass(frozen=True, slots=True) or FrozenModel)",
                )


def _is_frozen_class(node: ast.ClassDef) -> bool:
    return _has_frozen_dataclass_decorator(node) or _inherits_frozen_model(node)


def _has_frozen_dataclass_decorator(node: ast.ClassDef) -> bool:
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        if _is_dataclass_decorator_target(dec.func) and _has_frozen_true_keyword(dec):
            return True
    return False


def _is_dataclass_decorator_target(func: ast.expr) -> bool:
    if isinstance(func, ast.Name):
        return func.id == "dataclass"
    if isinstance(func, ast.Attribute):
        return func.attr == "dataclass"
    return False


def _has_frozen_true_keyword(decorator: ast.Call) -> bool:
    for kw in decorator.keywords:
        if (
            kw.arg == "frozen"
            and isinstance(kw.value, ast.Constant)
            and kw.value.value is True
        ):
            return True
    return False


def _inherits_frozen_model(node: ast.ClassDef) -> bool:
    return any(
        isinstance(base, ast.Name) and base.id == "FrozenModel"
        for base in node.bases
    )


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


def _public_function_count_violations(
    tree: ast.Module, rel: str
) -> Iterator[Violation]:
    if any(fragment in rel for fragment in _GOD_UTIL_EXEMPT_PATH_FRAGMENTS):
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
            f"{public_funcs} public top-level functions "
            f"(max {_MAX_PUBLIC_TOPLEVEL_FUNCTIONS})",
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


def _typed_errors_violations(
    node: ast.AST, rel: str, *, is_exempt: bool
) -> Iterator[Violation]:
    if isinstance(node, ast.Raise):
        name = _raised_exception_name(node)
        if name in _FORBIDDEN_EXCEPTION_NAMES:
            yield Violation(
                "AC-TYPED-ERRORS",
                f"{rel}:{node.lineno}",
                f"raise {name}(...) — use GridGymError subclass",
            )
    elif (
        isinstance(node, ast.ExceptHandler)
        and not is_exempt
        and isinstance(node.type, ast.Name)
        and node.type.id in _FORBIDDEN_EXCEPTION_NAMES
    ):
        yield Violation(
            "AC-TYPED-ERRORS",
            f"{rel}:{node.lineno}",
            f"except {node.type.id} outside boundary-translation",
        )


def _raised_exception_name(node: ast.Raise) -> str | None:
    exc = node.exc
    if exc is None:
        return None
    target = exc.func if isinstance(exc, ast.Call) else exc
    if isinstance(target, ast.Name):
        return target.id
    return None


# ---------------------------------------------------------------------------
# AC-NO-CYCLES (Importzyklen via grimp)
# ---------------------------------------------------------------------------


def _check_no_cycles() -> Iterator[Violation]:
    try:
        graph = grimp.build_graph(_INTERNAL_PACKAGE)
    except grimp.exceptions.NotATopLevelModule:
        return

    seen_pairs: set[tuple[str, str]] = set()
    for importer in sorted(graph.modules):
        if not importer.startswith(_INTERNAL_PACKAGE):
            continue
        for imported in sorted(graph.find_modules_directly_imported_by(importer)):
            if not imported.startswith(_INTERNAL_PACKAGE):
                continue
            if (imported, importer) in seen_pairs:
                continue
            chain = graph.find_shortest_chain(imported, importer)
            if chain:
                seen_pairs.add((importer, imported))
                yield Violation(
                    "AC-NO-CYCLES",
                    f"{importer} <-> {imported}",
                    "cycle: " + " -> ".join(chain) + f" -> {imported}",
                )


# ---------------------------------------------------------------------------
# AC-ADAPTER-LIGHTWEIGHT
# ---------------------------------------------------------------------------

_ADAPTER_LIGHTWEIGHT_PATH_PATTERNS: tuple[str, ...] = (
    "src/grid_gym/adapters/driven/protocol_*/**/*.py",
    "src/grid_gym/adapters/driven/persistence_*/**/*.py",
    "src/grid_gym/adapters/driving/**/*.py",
)
_ADAPTER_MAX_COMPLEXITY = 8


def _check_adapter_lightweight(repo_root: Path, src_root: Path) -> Iterator[Violation]:
    adapters_root = src_root / "adapters"
    for py_file in _iter_py_files(adapters_root):
        rel = _rel(repo_root, py_file)
        if not _matches_any(rel, _ADAPTER_LIGHTWEIGHT_PATH_PATTERNS):
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
                    f"function `{node.name}` complexity {complexity} > "
                    f"{_ADAPTER_MAX_COMPLEXITY}",
                )


def _cyclomatic_complexity(func: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    complexity = 1
    for node in ast.walk(func):
        if isinstance(node, ast.If | ast.For | ast.While | ast.ExceptHandler):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    return complexity


if __name__ == "__main__":
    sys.exit(main())
