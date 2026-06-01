"""M5-Welle-1-Pre-C0 HTMX-FastAPI-Smoke-Probe-Run.

Validiert die Maintainer-Decision-Indication aus ADR 0036
(„Option 1: FastAPI + HTMX + Jinja2 + Chart.js") **vor**
M5-Welle-1-C0-Slice-Doc-Anlage. Pattern analog M4-Welle-5a-
C1-Probe-Run (`b0fea7e` `nfm-dnp3`-Master-API-Inspektion +
`dnp3-outstation`-Wire-Compat-Probe vor C2-Code-Lieferung).

**Probe-Scope (minimal):**

Dieser Test verifiziert die drei kritischen Composition-
Punkte des HTMX+FastAPI+WS-Patterns auf Server-Seite — ohne
Browser-Roundtrip (das kommt in Welle 2/3 mit echten
Templates). Die drei Punkte:

1. **FastAPI rendert HTML-Response** (`HTMLResponse`-Pattern;
   Jinja2-Templates kommen in M5-Welle-2-C2 als Dep-Add).
2. **HTMX-Element triggert Partial-Server-Call**: GET mit
   `HX-Request: true`-Header → Server-Antwort ist ein
   HTML-Partial mit korrekten `hx-*`-Attributen.
3. **WebSocket pusht Server-side-Updates**: Client subscribt
   `WS /ws-counter`, Server pusht Counter-JSON-Updates.

**Anti-Scope (Probe):**

- Kein Browser-Driven-Test (keine Selenium/Playwright-
  Integration; das waere Welle-7-E2E-Smoke).
- Keine Jinja2-Template-Engine (Maintainer-Indication
  besagt Jinja2 als Welle-2-Foundation; Probe nutzt
  inline-HTML).
- Keine Chart.js-Probe (Charting-Library-Final ist
  Welle-3-Decision; ADR-0036-§2.5 hat das schon validiert
  per Sondierung).
- Keine HTMX-JavaScript-Library-Probe (HTMX wird in Welle 2
  als Static-Asset vendored; Server-Side-HTMX-Pattern
  reichen fuer Probe).

**Probe-Status:** Pre-C0-Validation. Bei Erfolg: ADR 0036
kann in M5-Welle-1-C1 von `Proposed → Provisional` gezogen
werden (Pattern analog ADR 0030..0035, die alle in C3 nach
C2-Code-Merge auf `Provisional` kamen — hier vorgezogen
weil ADR 0036 als Pre-Welle-0-Sondierungs-ADR existiert).
Bei Misserfolg: Welle-1-Sub-Slicing oder Stack-Wahl-Re-
Sondierung (sehr unwahrscheinlich, weil FastAPI + HTMX +
WS etablierte Patterns sind).

**Probe-Lebenszeit:** Dieser Test bleibt in `tests/
integration/` bis M5-Welle-2-C2-Implementation, dann wird
er entweder (a) durch produktive Tests in `tests/
integration/test_m5_ui_*.py` ersetzt oder (b) zu einem
reduzierten Smoke-Test umgebaut, der nur die Server-Side-
Composition-Garantie pruefte. Welle-2-C0-Slice-Doc
entscheidet.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient


@pytest.fixture
def probe_app() -> FastAPI:
    """Minimal-FastAPI-App mit 3 Routes fuer M5-Welle-1-Pre-C0-Probe.

    - `GET /` rendert HTML mit HTMX-Attributen.
    - `GET /htmx-partial` rendert Partial-Response fuer
      HX-Request-Header.
    - `WS /ws-counter` pusht Counter-Updates.

    Inline-Definition (kein src/grid_gym/-Touch in Pre-C0).
    """
    app = FastAPI(title="M5-Welle-1-Pre-C0-Probe")

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return (
            "<!DOCTYPE html><html><body>"
            "<button hx-get='/htmx-partial' hx-target='#out'>Refresh</button>"
            "<div id='out'>initial</div>"
            "</body></html>"
        )

    @app.get("/htmx-partial", response_class=HTMLResponse)
    def htmx_partial(request: Request) -> str:
        # HTMX-Pattern: HX-Request-Header signalisiert, dass der
        # Caller ein Partial erwartet (statt der vollen Seite).
        is_htmx = request.headers.get("HX-Request") == "true"
        if is_htmx:
            return "<div id='out' hx-swap-oob='true'>partial-updated</div>"
        return "<html><body>full-page-fallback</body></html>"

    @app.websocket("/ws-counter")
    async def ws_counter(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            for tick in range(3):
                await websocket.send_json({"tick": tick, "value": tick * 10})
                await asyncio.sleep(0.01)
        finally:
            await websocket.close()

    return app


@pytest.fixture
def probe_client(probe_app: FastAPI) -> AsyncIterator[TestClient]:
    """`TestClient` (sync), basierend auf `httpx.AsyncClient` —
    deckt HTTP-Routes + WebSocket via `client.websocket_connect`."""
    with TestClient(probe_app) as client:
        yield client


# ---------------------------------------------------------------------------
# Probe-Punkt 1: FastAPI rendert HTML-Response
# ---------------------------------------------------------------------------


def test_probe_1_fastapi_renders_html_response(probe_client: TestClient) -> None:
    """Validiert: FastAPI gibt `HTMLResponse` mit Content-Type
    `text/html` zurueck (Maintainer-Indication „FastAPI rendert
    Templates" — hier ohne Jinja2, inline-HTML)."""
    response = probe_client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "<!DOCTYPE html>" in body
    assert "hx-get='/htmx-partial'" in body
    assert "<div id='out'>initial</div>" in body


# ---------------------------------------------------------------------------
# Probe-Punkt 2: HTMX-Element triggert Partial-Server-Call
# ---------------------------------------------------------------------------


def test_probe_2_htmx_partial_response_with_hx_request_header(
    probe_client: TestClient,
) -> None:
    """Validiert: GET mit `HX-Request: true`-Header → Server
    returnt ein HTML-Partial (kein Full-Page-Fallback)."""
    response = probe_client.get("/htmx-partial", headers={"HX-Request": "true"})
    assert response.status_code == 200
    body = response.text
    assert "partial-updated" in body
    assert "hx-swap-oob='true'" in body
    # Negativ-Check: kein Full-Page-HTML-Skeleton im Partial.
    assert "<!DOCTYPE html>" not in body


def test_probe_2_fallback_full_page_without_hx_request_header(
    probe_client: TestClient,
) -> None:
    """Validiert: ohne `HX-Request`-Header gibt der Server eine
    Full-Page-Fallback zurueck (Pattern fuer Direct-Browser-
    Navigation analog Progressive-Enhancement)."""
    response = probe_client.get("/htmx-partial")
    assert response.status_code == 200
    body = response.text
    assert "full-page-fallback" in body
    assert "partial-updated" not in body


# ---------------------------------------------------------------------------
# Probe-Punkt 3: WebSocket pusht Server-side-Updates
# ---------------------------------------------------------------------------


def test_probe_3_websocket_pushes_counter_updates(
    probe_client: TestClient,
) -> None:
    """Validiert: WebSocket-Subscribe + Server-Side-Push mit JSON-
    Messages funktioniert (Pattern fuer M5-Welle-3-Live-Telemetry)."""
    with probe_client.websocket_connect("/ws-counter") as websocket:
        msg0 = websocket.receive_json()
        msg1 = websocket.receive_json()
        msg2 = websocket.receive_json()

    assert msg0 == {"tick": 0, "value": 0}
    assert msg1 == {"tick": 1, "value": 10}
    assert msg2 == {"tick": 2, "value": 20}
