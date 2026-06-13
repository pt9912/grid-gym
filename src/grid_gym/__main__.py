"""`python -m grid_gym` Entry-Point (M5 Welle 5, Slice-Doc
Decision 6).

Welle-5-Subcommand: ``demo`` — startet die FastAPI-App lokal
ueber `uvicorn` mit `GRID_GYM_DEMO_SCENARIO_PATH` auf das
kanonische `deploy/scenarios/gg-demo.yaml` gesetzt. Der Lifespan
verdrahtet anschliessend den scenario-getriebenen Demo-Stack
ueber `_demo_scenario_setup.configure_scenario_demo_run`
(Decision 6).

Welle-6+/M6-Forward-Pointer: `replay` und `validate` sind als
Subcommand-Slots reserviert, aber noch nicht implementiert —
ein Versuch wirft `SystemExit(2)` ueber den argparse-Default.
Welle 5 liefert nur `demo`.

R2 (Slice-Doc §7): der Uvicorn-Programmatic-Start ist in Tests
nicht trivial isolierbar; der Welle-5-Integration-Smoke
exerciert deshalb den **Lifespan-Pfad ohne Uvicorn**
(`tests/integration/test_m5_welle_5_demo_smoke.py`), und
`make demo` ist der Container-Smoke (GG-DEMO-008 manuelle
Abnahme).
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final


def _detect_default_scenario_path() -> Path:
    """Welle-5-Review F7: robust gegenueber dev-checkout VS
    installed-wheel-Layout.

    Dev-Checkout: `__file__ = <repo>/src/grid_gym/__main__.py`,
    `parents[2]` = `<repo>`, → `<repo>/deploy/scenarios/gg-demo.yaml`.

    Installed wheel (`pip install grid_gym`): `__file__` lebt in
    `site-packages/grid_gym/__main__.py`; `parents[2]` zeigt in den
    venv-Layout (nicht repo-deploy/). Wir versuchen das Repo-Layout,
    und fallen sonst zurueck auf cwd-relative `deploy/scenarios/
    gg-demo.yaml` — der User muss `--scenario` explizit setzen oder
    aus dem Repo-Root starten."""
    repo_layout = Path(__file__).resolve().parents[2] / "deploy" / "scenarios" / "gg-demo.yaml"
    if repo_layout.is_file():
        return repo_layout
    cwd_layout = Path.cwd() / "deploy" / "scenarios" / "gg-demo.yaml"
    if cwd_layout.is_file():
        return cwd_layout
    # Letzter Fallback: repo-Layout-Pfad zurueckgeben, damit die
    # Fehlermeldung wenigstens den erwarteten Pfad zeigt.
    return repo_layout


_DEFAULT_DEMO_SCENARIO_PATH: Final[Path] = _detect_default_scenario_path()
"""Welle-5-Default: kanonisches Demo-YAML; Layout-Detection in
`_detect_default_scenario_path` (dev-checkout vs. installed wheel
vs. cwd-Relativ). Wird per `--scenario` ueberschrieben."""

_DEFAULT_HOST: Final[str] = "127.0.0.1"
"""Welle-5-Local-Default: `python -m grid_gym demo` bindet auf
Loopback. Container-Form bindet auf `0.0.0.0` via env-var
`GRID_GYM_HOST` (Dockerfile + compose.yml)."""

_DEFAULT_PORT: Final[int] = 8000
"""Slice-Doc Decision 6: `make demo` liefert `http://localhost:
8000`. Modul-Form spiegelt das Port-Default."""


def main(argv: Sequence[str] | None = None) -> int:
    """argparse-Subcommand-Dispatch. Gibt einen exit-code zurueck.

    `argv=None` nutzt `sys.argv[1:]` (Default-CLI-Verhalten);
    Tests koennen explizit Argumente uebergeben.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.subcommand == "demo":
        return _run_demo(args)
    # Welle-5-Hard-Stop: nur `demo` ist heute registriert,
    # `argparse.required=True` blockt fehlende Subcommands. Der
    # `else`-Pfad existiert fuer Welle-6+/M6-Forward-Pointer
    # (`replay`/`validate`-Stubs werden hier ankommen, sobald sie
    # registriert sind, aber noch nicht implementiert).
    print(
        f"[grid_gym] Unknown subcommand: {args.subcommand!r}",
        file=sys.stderr,
    )
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m grid_gym",
        description="grid-gym CLI — Welle 5 liefert `demo`; "
        "Welle 6+/M6 ergaenzen `replay` und `validate`.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    demo = subparsers.add_parser(
        "demo",
        help="Startet die FastAPI-App lokal mit dem kanonischen Demo-Szenario.",
    )
    demo.add_argument(
        "--scenario",
        type=Path,
        default=_DEFAULT_DEMO_SCENARIO_PATH,
        help=f"Pfad zur Demo-YAML (Default: {_DEFAULT_DEMO_SCENARIO_PATH}).",
    )
    demo.add_argument(
        "--host",
        type=str,
        default=_DEFAULT_HOST,
        help=f"Bind-Host (Default: {_DEFAULT_HOST}).",
    )
    demo.add_argument(
        "--port",
        type=int,
        default=_DEFAULT_PORT,
        help=f"Bind-Port (Default: {_DEFAULT_PORT}).",
    )
    return parser


def _run_demo(args: argparse.Namespace) -> int:
    """Welle-5-`demo`-Subcommand: setzt env-var + uvicorn-
    Programmatic-Start.

    Der env-var-Pfad ist die Single Source of Truth fuer den
    Demo-Lifespan-Branch — derselbe Mechanismus laeuft im
    Container (`make demo` → compose.yml env). Damit verdrahten
    beide Surfaces den Demo-Stack ueber denselben Lifespan-Code-
    Pfad (Welle-5-Anti-Duplikat).
    """
    scenario_path: Path = args.scenario
    if not scenario_path.is_file():
        print(
            f"[grid_gym demo] Scenario-YAML nicht gefunden: {scenario_path}",
            file=sys.stderr,
        )
        return 1
    # Welle-5-Review F8: absolute Pfad-Resolution VOR env-var-write.
    # uvicorn (oder ein zukuenftiger `reload=True`-Worker-Fork)
    # resolved die env-var relativ zur worker-cwd; absoluter Pfad
    # immunisiert dagegen.
    os.environ["GRID_GYM_DEMO_SCENARIO_PATH"] = str(scenario_path.resolve())
    import uvicorn

    uvicorn.run(
        "grid_gym.composition.asgi:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
