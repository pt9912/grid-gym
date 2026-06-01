"""Tests fuer `_templates.py` (M5 Welle 2, ADR 0036).

Prueft die Jinja2Templates-Factory: Pfad-Resolution + erfolgreiches
Rendering eines einfachen Templates (Smoke).
"""

from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from grid_gym.adapters.driving.ui._templates import get_templates


def test_get_templates_returns_jinja2templates_instance() -> None:
    """Factory liefert eine konkrete ``Jinja2Templates``-Instanz."""
    templates = get_templates()
    assert isinstance(templates, Jinja2Templates)


def test_templates_directory_resolves_to_adapter_local_path() -> None:
    """Templates-Verzeichnis lebt direkt unter dem UI-Adapter-Modul."""
    from grid_gym.adapters.driving.ui import _templates as templates_module

    expected = Path(templates_module.__file__).parent / "templates"
    assert expected.is_dir()
    assert (expected / "base.html").is_file()
    assert (expected / "navigation.html").is_file()


def test_templates_render_base_partial_without_crash() -> None:
    """Rendering eines Templates ueber die Factory-Instanz ist
    kollisionsfrei (Smoke: kein Jinja2-SyntaxError, Includes
    werden aufgeloest).
    """
    templates = get_templates()
    env = templates.env
    rendered = env.get_template("navigation.html").render()
    assert "grid-gym" in rendered
