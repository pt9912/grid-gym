#!/usr/bin/env python3
"""Core-Checks fuer neue Dateien im hexagon/core.

Nutzung:
  python tools/check_core_determinism.py --mode determinism --mode state-floats -- <files...>
"""
from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable
from pathlib import Path
import sys


FORBIDDEN_ROOT_MODULES = frozenset({"random", "secrets", "uuid", "time", "datetime", "numpy"})
ALLOWED_IDENTIFIERS = frozenset({"RandomPort", "ScenarioEvent", "RandomEvent", "EventPort"})


def _collect_forbidden_aliases(
    tree: ast.AST,
) -> tuple[dict[str, str], dict[str, str]]:
    module_aliases: dict[str, str] = {}
    from_imports: dict[str, str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_ROOT_MODULES:
                    module_aliases[alias.asname or alias.name] = root
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            root = node.module.split(".")[0]
            if root not in FORBIDDEN_ROOT_MODULES:
                continue
            if any(alias.name == "*" for alias in node.names):
                # Wildcard import kann nicht sinnvoll aufgelöst werden.
                module_aliases[f"*from:{root}"] = root
                continue
            for alias in node.names:
                from_imports[alias.asname or alias.name] = root
    return module_aliases, from_imports


def _call_root_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        current: ast.AST = node
        while isinstance(current, ast.Attribute):
            value = current.value
            if isinstance(value, ast.Name):
                return value.id
            current = value
    return None


def _has_float_annotation(annotation: ast.AST | None) -> bool:
    if annotation is None:
        return False
    return any(
        isinstance(child, ast.Name) and child.id == "float"
        or isinstance(child, ast.Attribute) and child.attr == "float"
        for child in ast.walk(annotation)
    )


def _is_float_call(node: ast.Call) -> bool:
    return (isinstance(node.func, ast.Name) and node.func.id == "float") or (
        isinstance(node.func, ast.Attribute) and node.func.attr == "float"
    )


def _is_dataclass_decorator(expr: ast.expr) -> bool:
    if isinstance(expr, ast.Name) and expr.id == "dataclass":
        return True
    if isinstance(expr, ast.Attribute) and expr.attr == "dataclass":
        return True
    if isinstance(expr, ast.Call):
        return _is_dataclass_decorator(expr.func)
    return False


def _is_dataclass(node: ast.ClassDef) -> bool:
    return any(_is_dataclass_decorator(decorator) for decorator in node.decorator_list)


def _check_determinism(
    tree: ast.AST,
    file: Path,
    module_aliases: dict[str, str],
    from_imports: dict[str, str],
) -> list[str]:
    violations: list[str] = []
    wildcard_forbidden = {name for name in module_aliases if name.startswith("*from:")}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_ROOT_MODULES:
                    violations.append(f"{file}:{node.lineno}:{node.col_offset}: forbidden import '{alias.name}'")
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            root = node.module.split(".")[0]
            if root in FORBIDDEN_ROOT_MODULES and any(alias.name == "*" for alias in node.names):
                violations.append(f"{file}:{node.lineno}:{node.col_offset}: forbidden wildcard import from '{node.module}'")
            elif root in FORBIDDEN_ROOT_MODULES:
                violations.append(f"{file}:{node.lineno}:{node.col_offset}: forbidden from-import '{node.module}'")
        elif isinstance(node, ast.Call):
            root = _call_root_name(node.func)
            if not root or root in ALLOWED_IDENTIFIERS:
                continue
            if root in module_aliases and module_aliases[root] in FORBIDDEN_ROOT_MODULES:
                violations.append(
                    f"{file}:{node.lineno}:{node.col_offset}: forbidden core-call '{ast.unparse(node.func)}()' via '{root}'"
                )
            if root in from_imports and from_imports[root] in FORBIDDEN_ROOT_MODULES:
                violations.append(
                    f"{file}:{node.lineno}:{node.col_offset}: forbidden core-call '{ast.unparse(node.func)}()' via imported '{root}'"
                )

    for name in sorted(wildcard_forbidden):
        root = name.removeprefix("*from:")
        violations.append(f"{file}:<module>:0: wildcard import from forbidden module '{root}'")

    return violations


def _check_state_floats(tree: ast.AST, file: Path) -> list[str]:
    violations: list[str] = []

    def walk(node: ast.AST, in_dataclass: bool = False) -> None:
        if isinstance(node, ast.ClassDef):
            dataclass_scope = in_dataclass or _is_dataclass(node)
            for stmt in node.body:
                walk(stmt, in_dataclass=dataclass_scope)
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return

        if in_dataclass and isinstance(node, ast.AnnAssign):
            if _has_float_annotation(node.annotation):
                violations.append(f"{file}:{node.lineno}:{node.col_offset}: typed float field '{ast.unparse(node.target)}'")
            if isinstance(node.value, ast.Call) and _is_float_call(node.value):
                violations.append(
                    f"{file}:{node.lineno}:{node.col_offset}: float() default in persisted field '{ast.unparse(node.target)}'"
                )

        for child in ast.iter_child_nodes(node):
            walk(child, in_dataclass)

    walk(tree, False)
    return violations


def _check_files(paths: Iterable[Path], modes: tuple[str, ...]) -> list[str]:
    bad: list[str] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        module_aliases, from_imports = _collect_forbidden_aliases(tree)
        if "determinism" in modes:
            bad.extend(_check_determinism(tree, path, module_aliases, from_imports))
        if "state-floats" in modes:
            bad.extend(_check_state_floats(tree, path))
    return bad


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    parser.add_argument("--mode", action="append", required=True, choices=("determinism", "state-floats"))
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if not args.files:
        print("No files provided; nothing to check.")
        return 0
    bad = _check_files([Path(p) for p in args.files], tuple(args.mode))
    for violation in bad:
        print(violation)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
