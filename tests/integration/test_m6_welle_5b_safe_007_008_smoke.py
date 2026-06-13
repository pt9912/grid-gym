"""Integration-Smoke fuer `GG-SAFE-007` + `GG-SAFE-008` (M6 Welle 5b;
Sim/Prod-Marker + REST-Input-Validation).

Elf Smoke-Tests:

- SAFE-007 (x5): Sim/Prod-Marker an drei Pflicht-Surfaces aus
  Lastenheft Z. 1399 (UI + API-Doku + Adapterkonfiguration) plus
  arch_check-Belegung:
  - OpenAPI `info.description` enthaelt Sim/Prod-Marker.
  - README.md + README.de.md enthalten Sim-only-Disclaimer.
  - arch_check `AC-HEXAGON-PURE`-Contract ist verankert.
  - UI-`base.html` rendert sichtbaren Sim/Prod-Banner an jeder
    UI-Page.
  - Scenario-YAML + Protocol-Adapter-`_config.py` enthalten den
    Sim-only-Marker im Top-Level-Kommentar bzw. Modul-Docstring.

- SAFE-008 (x6): Pydantic-Strict-Mode + extra-forbid auf
  REST-Request-Bodies (ADR 0045) und WebSocket-Subscribe-Surface:
  - `POST /runs` mit invalid `scenario_hash`-Laenge → 422.
  - `POST /runs/{id}/control` mit extra-Field wird rejected
    (extra-forbid Beleg).
  - `POST /runs` mit `seed="42"` (String statt Int) wird
    rejected (Strict-Mode Beleg).
  - `WS /runs/{invalid-uuid}/telemetry`-Connect schliesst sauber
    mit Policy-Close (nicht-existenter Run).
  - WebSocket-Handler iteriert nur ueber Subscribe-Pfad und
    konsumiert keine Client-Payloads (Quell-Datei-Inspektion).
  - `POST /runs/{id}/faults` mit unbekanntem `target` →
    422 mit `fault_unknown_target`.

Audit-Trail: `docs/user/safe-007-008-sim-prod-input-validation.md`.
"""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from grid_gym.composition._demo_scenario_setup import _DEMO_RUN_ID
from grid_gym.adapters.driving.http_api.app import _DEMO_SCENARIO_ENV_VAR
from grid_gym.composition.asgi import app


_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEMO_SCENARIO_PATH: Path = _REPO_ROOT / "deploy" / "scenarios" / "gg-demo.yaml"
_VALID_SCENARIO_HASH = "a" * 64


def _reset_app_state() -> None:
    """Welle-5-Review F15: Reset ueber Starlette-internes
    `_state`-Dict (Pattern aus test_m5_welle_5_demo_smoke)."""
    app.state._state.clear()


@pytest.fixture
def smoke_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Welle-5-Lifespan-Pfad mit echtem Demo-Stack — liefert UI-Pages,
    OpenAPI-Schema, REST + WS-Endpunkte einsatzbereit."""
    _reset_app_state()
    monkeypatch.setenv(_DEMO_SCENARIO_ENV_VAR, str(_DEMO_SCENARIO_PATH))
    with TestClient(app) as client:
        yield client
    _reset_app_state()


# ---------------------------------------------------------------------------
# GG-SAFE-007 — Sim/Prod-Marker (Lastenheft Z. 1399: drei Pflicht-Surfaces)
# ---------------------------------------------------------------------------


def test_safe_007_openapi_description_marks_simulation(
    smoke_client: TestClient,
) -> None:
    """`GG-SAFE-007` API-Doku-Surface: OpenAPI `info.description`
    nennt sowohl `simulation` als auch den expliziten Negativ-
    Disclaimer „not approved for production"."""
    response = smoke_client.get("/openapi.json")
    assert response.status_code == 200

    payload = response.json()
    description = payload["info"]["description"].lower()

    assert "simulation" in description
    assert "production" in description or "produktiv" in description


def test_safe_007_readme_disclaimer_present() -> None:
    """`GG-SAFE-007` API-Doku-Surface: README.md UND README.de.md
    enthalten den Sim-only-Disclaimer."""
    readme_en = (_REPO_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (_REPO_ROOT / "README.de.md").read_text(encoding="utf-8")

    assert "Simulation only" in readme_en
    assert "not approved for production" in readme_en
    assert "Nur Simulation" in readme_de
    assert "nicht fuer produktive Anlagensteuerung" in readme_de


def test_safe_007_arch_check_hexagon_pure_whitelist() -> None:
    """`GG-SAFE-007` Architektur-Belegung: `AC-HEXAGON-PURE`-
    Contract ist in `tools/arch_check.py` verankert und im
    `pyproject.toml`-Allowlist-Block dokumentiert. Damit ist
    eine Direct-Wire-Anbindung von Produktiv-Anlagen-Adaptern
    an `hexagon/**` strukturell ausgeschlossen."""
    arch_check = (_REPO_ROOT / "tools" / "arch_check.py").read_text(encoding="utf-8")
    pyproject = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "AC-HEXAGON-PURE" in arch_check
    assert "AC-HEXAGON-PURE" in pyproject


def test_safe_007_ui_base_renders_simulation_banner(
    smoke_client: TestClient,
) -> None:
    """`GG-SAFE-007` UI-Surface: jede UI-Page rendert den Sim/Prod-
    Banner aus `base.html`. Smoke prueft auf semantische Anker
    (`role="note"` + `aria-label`) statt auf die CSS-Klasse,
    damit ein Refactor der Banner-Darstellung den Vertrag nicht
    bricht, solange der ARIA-Marker bleibt."""
    semantic_marker = 'role="note"'
    aria_label = 'aria-label="Simulation-only disclaimer"'
    visible_en = "Simulation only"
    visible_de = "nicht fuer produktive Anlagensteuerung"

    demo_response = smoke_client.get("/")
    assert demo_response.status_code == 200
    assert semantic_marker in demo_response.text
    assert aria_label in demo_response.text
    assert visible_en in demo_response.text
    assert visible_de in demo_response.text

    dashboard_response = smoke_client.get(f"/runs/{_DEMO_RUN_ID}/dashboard")
    assert dashboard_response.status_code == 200
    assert semantic_marker in dashboard_response.text
    assert aria_label in dashboard_response.text
    assert visible_en in dashboard_response.text
    assert visible_de in dashboard_response.text


def test_safe_007_adapter_config_marks_simulation() -> None:
    """`GG-SAFE-007` Adapterkonfigurations-Surface: das kanonische
    Demo-Scenario `deploy/scenarios/gg-demo.yaml` und die fuenf
    Protocol-Adapter-`_config.py`-Module tragen den Sim-only-
    Marker im Top-Level-Kommentar bzw. Modul-Docstring."""
    scenario = (_REPO_ROOT / "deploy" / "scenarios" / "gg-demo.yaml").read_text(encoding="utf-8")
    assert "SIMULATION ONLY" in scenario
    assert "GG-SAFE-007" in scenario

    protocol_dir = _REPO_ROOT / "src" / "grid_gym" / "adapters" / "driven"
    for adapter in ("dnp3", "iec61850", "modbus", "mqtt", "opcua"):
        config = (protocol_dir / f"protocol_{adapter}" / "_config.py").read_text(encoding="utf-8")
        assert "Simulation only" in config, f"sim-marker missing in {adapter}/_config.py"
        assert "GG-SAFE-007" in config, f"sim-marker missing in {adapter}/_config.py"


# ---------------------------------------------------------------------------
# GG-SAFE-008 — REST + WebSocket Input-Validation (ADR 0045)
# ---------------------------------------------------------------------------


def test_safe_008_rest_invalid_payload_rejected_422(
    smoke_client: TestClient,
) -> None:
    """`GG-SAFE-008` REST-Schema-Validation: `POST /runs` mit
    `scenario_hash`-String < 64 Zeichen wird mit 422 rejected
    (Pflicht-Length-Schwelle aus dem `scenario_hash`-Feld-
    Constraint)."""
    response = smoke_client.post(
        "/runs",
        json={
            "scenario_hash": "too-short",
            "seed": 42,
            "tick_ms": 100,
        },
    )
    assert response.status_code == 422


def test_safe_008_rest_extra_field_rejected(smoke_client: TestClient) -> None:
    """`GG-SAFE-008` extra-forbid Beleg (ADR 0045 §2.1):
    `POST /runs/{id}/control` mit zusaetzlichem `unknown_key`-
    Feld wird mit 422 rejected statt silent zu verwerfen."""
    response = smoke_client.post(
        f"/runs/{_DEMO_RUN_ID}/control",
        json={"action": "pause", "unknown_key": "evil_payload"},
    )
    assert response.status_code == 422
    body_text = json.dumps(response.json())
    assert "extra_forbidden" in body_text or "Extra" in body_text


def test_safe_008_rest_type_coercion_rejected(
    smoke_client: TestClient,
) -> None:
    """`GG-SAFE-008` Strict-Mode Beleg (ADR 0045 §2.1):
    `POST /runs` mit `seed="42"` (String statt Int) wird mit
    422 rejected statt silent zu `42` umzuwandeln."""
    response = smoke_client.post(
        "/runs",
        json={
            "scenario_hash": _VALID_SCENARIO_HASH,
            "seed": "42",
            "tick_ms": 100,
        },
    )
    assert response.status_code == 422
    body_text = json.dumps(response.json())
    assert "int" in body_text.lower()


def test_safe_008_websocket_unknown_run_id_rejected(
    smoke_client: TestClient,
) -> None:
    """`GG-SAFE-008` WebSocket-Surface: ein WS-Connect gegen ein
    nicht-existentes `run_id` schliesst sauber mit Policy-Close
    (Close-Code 1008), statt eine Live-Subscription ohne Backing-
    Run zu oeffnen."""
    from starlette.websockets import WebSocketDisconnect

    invalid_run_id = str(uuid.uuid4())
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        smoke_client.websocket_connect(f"/runs/{invalid_run_id}/telemetry") as ws,
    ):
        ws.receive_json()
    assert exc_info.value.code == 1008
    assert invalid_run_id in (exc_info.value.reason or "")


def test_safe_008_websocket_no_client_payload_consumed() -> None:
    """`GG-SAFE-008` WebSocket-Subscribe-only-Belegung (ADR 0045
    §2.3): kein WebSocket-Handler in `http_api/` ruft
    `websocket.receive_*` auf. Beleg: Scan ueber alle `*.py`-
    Dateien im http_api-Modul. Sensor faengt damit auch
    zukuenftige WS-Handler in neuen Routern (z. B. `_demo_setup`,
    `_runs_router`) auf, nicht nur den aktuellen
    `_runs_action_router`."""
    http_api_dir = _REPO_ROOT / "src" / "grid_gym" / "adapters" / "driving" / "http_api"
    ws_decorator = re.compile(r"\.websocket\(")
    receive_call = re.compile(r"websocket\.receive_\w+\(")

    files_with_ws_handler: list[str] = []
    for py_file in sorted(http_api_dir.glob("*.py")):
        src = py_file.read_text(encoding="utf-8")
        if not ws_decorator.search(src):
            continue
        files_with_ws_handler.append(py_file.name)
        assert not receive_call.search(src), (
            f"WS-Handler in `http_api/{py_file.name}` ruft "
            "`websocket.receive_*` — verletzt ADR 0045 §2.3 "
            "(WebSocket-Subscribe-only-Vertrag)."
        )

    # Sanity: ohne mindestens einen WS-Handler waere die Assertion
    # leerlaufend; das Modul muss die zwei bekannten Handler in
    # `_runs_action_router.py` (telemetry + alarms-stream) tragen.
    assert files_with_ws_handler, (
        "Erwartet mindestens ein `http_api/*.py` mit "
        "@*.websocket(...)-Dekorator; Sensor sonst leerlaufend."
    )


def test_safe_008_fault_injection_unknown_target_rejected(
    smoke_client: TestClient,
) -> None:
    """`GG-SAFE-008` Zielressourcen-Validation:
    `POST /runs/{id}/faults` mit `target=<unbekannte Device-ID>`
    wird mit 422 rejected + `code='fault_unknown_target'` in der
    `ErrorResponse` (Cross-Field-Validation aus M5-Welle-6a
    Decision 20)."""
    response = smoke_client.post(
        f"/runs/{_DEMO_RUN_ID}/faults",
        json={
            "fault_type": "cell_failure",
            "target": "device-that-does-not-exist",
            "start_at_tick": 0,
            "duration_ticks": 10,
            "recovery": "auto-recover-after-N-ticks",
        },
    )
    assert response.status_code == 422
    body = response.json()
    detail = body.get("detail", body)
    assert detail.get("code") == "fault_unknown_target"
