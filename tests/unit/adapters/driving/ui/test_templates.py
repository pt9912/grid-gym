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


def test_base_html_loads_htmx_websocket_extension() -> None:
    """Slice 078 (Regression): die HTMX-WebSocket-Extension ist in HTMX 2.x aus
    dem Core ausgelagert; `base.html` MUSS sie laden **und** das Asset MUSS im
    Static-Verzeichnis liegen. Ohne sie tut `hx-ext="ws"` nichts und der
    Dashboard-/Alarms-Live-Feed bleibt dauerhaft „Waiting for live data"
    (`GG-UI-002`/`003`/`005`-Regression, im Browser nicht von den TestClient-
    Smokes erfassbar)."""
    from grid_gym.adapters.driving.ui import _templates as templates_module

    ui_dir = Path(templates_module.__file__).parent
    base_html = (ui_dir / "templates" / "base.html").read_text(encoding="utf-8")
    assert "htmx-ext-ws.min.js" in base_html
    ws_ext = ui_dir / "static" / "htmx-ext-ws.min.js"
    assert ws_ext.is_file()
    # Die Extension registriert sich als htmx-`ws`-Extension (Sanity gegen ein
    # leeres/falsches Asset).
    assert 'defineExtension("ws"' in ws_ext.read_text(encoding="utf-8")


def test_navigation_exposes_all_welle_5_and_6a_pages() -> None:
    """Welle-6a-Review F15: Navigation muss alle 5 UI-Pages
    sichtbar als Link tragen. Ohne diesen Assertion-Pin koennte
    ein Templates-Refactor den Faults-Link still entfernen und
    GG-UI-007 wuerde UI-side regressen, ohne CI-Signal.

    Pflicht-Links:
    - Demo (/)
    - Health (/ui/health)
    - Dashboard (/runs/.../dashboard)
    - Control (/runs/.../control)
    - Alarms (/runs/.../alarms)
    - Faults (/runs/.../faults) — Welle-6a-NEU
    """
    templates = get_templates()
    env = templates.env
    rendered = env.get_template("navigation.html").render()
    for href in (
        '"/"',
        '"/ui/health"',
        "/dashboard",
        "/control",
        "/alarms",
        "/faults",
    ):
        assert href in rendered, f"Navigation fehlt Link {href!r}"
