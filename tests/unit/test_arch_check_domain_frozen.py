"""Direkter Test fuer `_inherits_enum` (AC-DOMAIN-FROZEN, ADR 0008).

Pinnt die in `ADR 0008 §2` festgelegte Liste der zulaessigen Enum-
Basisklassen (`Enum`, `StrEnum`, `IntEnum`, `Flag`, `IntFlag`,
`ReprEnum`). Faengt versehentliches Loeschen oder Umbenennen der
Helper-Funktion ohne ADR-Begleitung.

Test-Doppelung mit `make arch-check` ist gewollt: der Live-Run
prueft nur, dass die im Repo vorhandenen Enum-Klassen
(`Quality`, `CommandResult`) durchgehen — die Rejection-Pfade
und die Attribut-Form (`enum.StrEnum`) werden hier zusaetzlich
abgesichert.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

# tools/ liegt nicht im Python-Pfad — direkt importieren.
_TOOLS_PATH = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS_PATH) not in sys.path:
    sys.path.insert(0, str(_TOOLS_PATH))

from arch_check import _inherits_enum  # type: ignore[import-not-found]


def _classdef(source: str) -> ast.ClassDef:
    """Parst `source` und gibt die erste Top-Level-ClassDef zurueck."""
    tree = ast.parse(source)
    node = tree.body[0]
    assert isinstance(node, ast.ClassDef), f"expected ClassDef, got {type(node).__name__}"
    return node


# ---------------------------------------------------------------------------
# Happy-Path: Bare-Name-Vererbung (`from enum import StrEnum`)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "base_name",
    ["Enum", "StrEnum", "IntEnum", "Flag", "IntFlag", "ReprEnum"],
)
def test_inherits_enum_accepts_bare_name(base_name: str) -> None:
    """Alle in ADR 0008 §2 gelisteten Basisklassen werden als
    `ast.Name` erkannt."""
    node = _classdef(f"class Q({base_name}):\n    pass\n")
    assert _inherits_enum(node)


# ---------------------------------------------------------------------------
# Happy-Path: Attribut-Vererbung (`import enum` → `class Q(enum.StrEnum)`)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "base_name",
    ["Enum", "StrEnum", "IntEnum", "Flag", "IntFlag", "ReprEnum"],
)
def test_inherits_enum_accepts_attribute_form(base_name: str) -> None:
    """`enum.StrEnum` (Attribut-Form) wird erkannt — gleiche
    Heuristik wie bei `FrozenModel`."""
    node = _classdef(f"class Q(enum.{base_name}):\n    pass\n")
    assert _inherits_enum(node)


# ---------------------------------------------------------------------------
# Happy-Path: Mehrfachvererbung mit Enum-Basis
# ---------------------------------------------------------------------------


def test_inherits_enum_accepts_mixin_with_enum_base() -> None:
    """`class Q(str, Enum)` — Python-Idiom vor `StrEnum`. Auch erkannt."""
    node = _classdef("class Q(str, Enum):\n    pass\n")
    assert _inherits_enum(node)


# ---------------------------------------------------------------------------
# Rejection: Nicht-Enum-Basen
# ---------------------------------------------------------------------------


def test_inherits_enum_rejects_plain_class() -> None:
    """Klasse ohne Basen → nicht als Enum erkannt."""
    node = _classdef("class C:\n    pass\n")
    assert not _inherits_enum(node)


def test_inherits_enum_rejects_object_base() -> None:
    node = _classdef("class C(object):\n    pass\n")
    assert not _inherits_enum(node)


def test_inherits_enum_rejects_unrelated_base() -> None:
    """Eine zufaellige andere Basisklasse matcht nicht."""
    node = _classdef("class C(SomeOtherBase):\n    pass\n")
    assert not _inherits_enum(node)


def test_inherits_enum_rejects_partial_name_match() -> None:
    """`EnumLike` enthaelt `Enum` als Substring, ist aber kein
    literaler Match — die Erkennung ist namentlich exakt."""
    node = _classdef("class C(EnumLike):\n    pass\n")
    assert not _inherits_enum(node)


def test_inherits_enum_rejects_frozen_model() -> None:
    """`FrozenModel` ist eine andere Frozen-Form, nicht Enum;
    `_inherits_enum` darf hier `False` liefern."""
    node = _classdef("class C(FrozenModel):\n    pass\n")
    assert not _inherits_enum(node)


def test_inherits_enum_rejects_attribute_with_unrelated_attr() -> None:
    """`enum.EnumMeta` ist `enum.*`, aber kein gelisteter
    Basisklassen-Name."""
    node = _classdef("class C(enum.EnumMeta):\n    pass\n")
    assert not _inherits_enum(node)
