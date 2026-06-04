"""Jinja2Templates-Factory + HTMX-Request-Detection fuer das UI-
Driving-Adapter (M5 Welle 2; Welle-6b-Review F14 hoist).

Das Modul kapselt die ``Jinja2Templates``-Instanz und ihren
Pfad-Bezug zur Templates-Lokation. Routes (siehe ``routes.py``,
``routes_faults.py``, ``routes_visualization.py``) importieren
``get_templates`` und ``is_htmx_request`` statt direkt
``fastapi.templating.Jinja2Templates`` zu instanziieren oder den
HX-Request-Header in jedem Route-Modul neu zu parsen —
damit bleiben Pfad-Bezug + Header-Konvention an genau einem Punkt.

Pfad-Resolution erfolgt relativ zu diesem Modul
(``Path(__file__).parent / "templates"``), damit die UI-
Adapter-Lokation `src/grid_gym/adapters/driving/ui/` als
ein Bundle deploybar bleibt (siehe ADR 0036 §2.1).
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from fastapi import Request
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


def is_htmx_request(request: Request) -> bool:
    """``True`` wenn HTMX den Request als Sub-Request markiert hat.

    M5-Welle-6b-Review F14: einziger Owner der HX-Request-Header-
    Konvention. Frueher in drei Route-Modulen (``routes.py``,
    ``routes_faults.py``, ``routes_visualization.py``) als
    `_is_htmx_request` dupliziert; Pattern erlaubt jetzt zentrale
    Evolution (z. B. fuer `HX-Boosted` oder HTMX-2.x-Header).
    """
    return request.headers.get("hx-request", "").lower() == "true"
