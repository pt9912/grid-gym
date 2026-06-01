"""UI-Driving-Adapter (M5 Welle 2, ADR 0036).

Liefert die Web-UI-Hülse fuer den ``grid-gym``-Simulationskern:
Jinja2-Templates + vendored Static-Assets (HTMX + Chart.js) +
FastAPI-Routes als Driving-Adapter parallel zum HTTP-API-
Adapter unter ``adapters/driving/http_api/``.

Welle-2-Scope (siehe
[`docs/plan/planning/in-progress/M5-welle-2.md`](../../../../../../docs/plan/planning/in-progress/M5-welle-2.md)):
Base-Layout + Navigation + Healthcheck-Page + Demo-Hello-
Page. Live-Telemetry-Dashboard (Welle 3), Replay-Controls
(Welle 4), Scenario-Editor (Welle 5) und Fault-Injection-UI
(Welle 6) liegen in Folgewellen.
"""
