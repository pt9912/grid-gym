"""Jinja2Templates-Factory fuer das UI-Driving-Adapter (M5 Welle 2).

Das Modul kapselt die ``Jinja2Templates``-Instanz und ihren
Pfad-Bezug zur Templates-Lokation. Routes (siehe ``routes.py``)
importieren ``get_templates`` statt direkt
``fastapi.templating.Jinja2Templates`` zu instanziieren —
damit bleibt der Pfad-Bezug an genau einem Punkt.

Pfad-Resolution erfolgt relativ zu diesem Modul
(``Path(__file__).parent / "templates"``), damit die UI-
Adapter-Lokation `src/grid_gym/adapters/driving/ui/` als
ein Bundle deploybar bleibt (siehe ADR 0036 §2.1).
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from fastapi.templating import Jinja2Templates

_TEMPLATES_DIR: Final[Path] = Path(__file__).parent / "templates"


def get_templates() -> Jinja2Templates:
    """Erzeugt eine neue ``Jinja2Templates``-Instanz.

    Aufrufer (`routes.py`, Unit-Tests) rufen die Factory direkt
    in den Endpoint-Handlern auf. FastAPI cached intern die
    Jinja2-Environment, weshalb keine modul-globale Instanz
    notwendig ist.
    """
    return Jinja2Templates(directory=str(_TEMPLATES_DIR))
