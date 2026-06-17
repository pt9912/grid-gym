# Demo-Abnahmereihenfolge (`GG-DEMO-008`)

**Status:** Lebend ab M5-Welle-6c-C2 (2026-06-04).
**Bezug:**
[`spec/lastenheft.md §24 GG-DEMO-008`](../../spec/lastenheft.md#24-demo-system),
M5-Welle-5 (Demo-Pipeline + Scenario-Loader, `Done` 2026-06-03),
M5-Welle-6a (Fault-Flow, `Done` 2026-06-03), M5-Welle-6b
(UI-Visualization, `Done` 2026-06-04).

Diese Doku beschreibt die **reproduzierbare Abnahmereihenfolge**
fuer den grid-gym-MVP-Demo-Lauf. Die sechs Schritte spiegeln den
Akzeptanztext von [`GG-DEMO-008`](../../spec/lastenheft.md#gg-demo-008) 1:1 und sind so durchnummeriert,
wie sie ein Operator oder Reviewer abarbeiten soll.

Jeder Schritt nennt das auszufuehrende Kommando, das erwartete
Ergebnis und einen Verweis auf die produzierende Welle, in der
das Verhalten implementiert wurde — falls der Reviewer den
Hintergrund nachlesen will.

---

## 0. Voraussetzungen

- **Docker + Docker Compose v2** (lokal verfuegbar; `docker
  compose version` muss laufen).
- **`make`** im PATH.
- **Freie Host-Ports:** `8000` (UI + REST/WebSocket),
  `5432` (Postgres-Sibling), `4317`/`4318` (OTel-Collector).
- **Optional:** `curl` + ein Browser (Firefox/Chromium) fuer die
  UI-Schritte. WebSocket-Abnahme nutzt den Browser via HTMX, kein
  separater Client noetig.
- **Optional:** `uv` (Astral) — nur falls Tests oder die Toolchain
  ausserhalb von Docker laufen sollen. Die Abnahme braucht es nicht.

Der Demo-Stack baut sein eigenes Container-Image (`api`); ein
Kaltstart kann ~70 s dauern (Postgres + OTel-Collector-Pull). Die
Folge-Starts ziehen Cache.

---

## 1. Start

```bash
make demo
```

**Erwartet:** Compose orchestriert vier Sibling-Services
(`api`, `db` Postgres, `otel-collector`, `mosquitto`) mit
`docker compose up -d --wait --wait-timeout 90`. Die Schluss-
zeile lautet:

```
[demo] /health ok; UI verfuegbar unter http://localhost:8000
[demo] Stop mit 'make demo-stop' (DESTRUKTIV: -v entfernt postgres-data)
```

Der Demo-Lauf laeuft unter der kanonischen Run-ID
`demo-run-0001` (Welle 5; `_demo_scenario_setup._DEMO_RUN_ID`).
TickLoop tickt mit `tick_ms=1000` (siehe
[`deploy/scenarios/gg-demo.yaml`](../../deploy/scenarios/gg-demo.yaml)).

**Stop (destruktiv, loescht Postgres-Volumes):**

```bash
make demo-stop
```

**Welle:** M5-Welle-5 (Demo-Pipeline +
`GRID_GYM_DEMO_SCENARIO_PATH`-Lifespan-Branch + `make demo`-
Target);
[`docs/plan/planning/done/M5-welle-5.md`](../plan/planning/done-archive/M5-welle-5.md).

---

## 2. Healthcheck

```bash
curl -s http://localhost:8000/health
```

**Erwartet:**

```json
{"status":"ok"}
```

Plus die UI-Variante im Browser unter `http://localhost:8000/ui/
health` — rendert dieselbe Antwort via HTMX-Partial-Refresh, ohne
Vollseiten-Reload.

Service-Health ist ausserdem im Welle-6b-System-Dashboard sichtbar
(siehe Schritt 3.3 unten).

**Welle:** M1-Welle-6a (Liveness-Probe) + M5-Welle-2 (UI-Health-
Page);
[`docs/plan/planning/done/M5-welle-2.md`](../plan/planning/done-archive/M5-welle-2.md).

---

## 3. Szenario-Ausfuehrung

Das Demo-Scenario `gg-demo.yaml` enthaelt fuenf MVP-Geraete
(`battery-1`, `pv-1`, `load-1`, `grid-connection-1`,
`smart-meter-1`) + einen `RuleBasedAgent`, der die Battery
zeitgesteuert steuert. Drei UI-Pages decken die Akzeptanz von
[`GG-UI-002`](../../spec/lastenheft.md#gg-ui-002)/`003`/`006`/`008`/`009` ab.

### 3.1 Live-Telemetry-Dashboard

Browser:
[`http://localhost:8000/runs/demo-run-0001/dashboard`](http://localhost:8000/runs/demo-run-0001/dashboard)

**Erwartet:**

- Chart.js-Time-Series-Plot fuer `power_kw`, `soc_kwh`,
  Qualitaets-Marker (`valid`/`fault_injected`/...) pro Geraet.
- HTMX-WebSocket-Subscribe an `WS /runs/demo-run-0001/telemetry`
  liefert kontinuierlich neue Punkte (1 Hz, Tick-getrieben).
- Quality-Marker wechseln im Fault-Window (siehe Schritt 4).

**Welle:** M5-Welle-3 (Live-Telemetry-Dashboard);
[`docs/plan/planning/done/M5-welle-3.md`](../plan/planning/done-archive/M5-welle-3.md).

### 3.2 Geraete-Tabelle (`GG-UI-006`)

Browser:
[`http://localhost:8000/runs/demo-run-0001/devices`](http://localhost:8000/runs/demo-run-0001/devices)

**Erwartet:** 4-Spalten-Tabelle mit allen fuenf Devices,
HTMX-Polling auf `/runs/demo-run-0001/devices/state` (1 s):

| ID | Type | State | Quality |
| --- | --- | --- | --- |
| `battery-1` | `battery` | `soc_kwh`, `current_power_kw`, `cell_failure_active` | `valid` (oder `fault_injected` waehrend Tick 900..949) |
| `pv-1` | `pv` | `current_power_kw` | `valid` |
| `load-1` | `load` | `current_power_kw` | `valid` |
| `grid-connection-1` | `grid_connection` | `current_power_kw`, `current_voltage_v`, `voltage_drop_active` | `valid` (oder `fault_injected` waehrend Tick 1200..1259) |
| `smart-meter-1` | `smart_meter` | `{}` | `valid` |

REST-Variante (JSON):

```bash
curl -s http://localhost:8000/runs/demo-run-0001/devices/state | jq .
```

**Welle:** M5-Welle-6b (UI-Visualization-Pages + Devices-API);
[`docs/plan/planning/done/M5-welle-6b.md`](../plan/planning/done-archive/M5-welle-6b.md).

### 3.3 Simulations-Zustands-Dashboard (`GG-UI-008`)

Browser:
[`http://localhost:8000/runs/demo-run-0001/system`](http://localhost:8000/runs/demo-run-0001/system)

**Erwartet:** Zwei Polling-Bloecke:

- **Run Status** (1 s, gegen `/runs/demo-run-0001/status`): zeigt
  `state` (`pending`/`running`/`paused`/`stopped`/`completed`),
  `sim time: <ms>`, `ticks: <n>`. Wachsen ueber Zeit, solange der
  Lauf nicht pausiert ist.
- **Service Health** (5 s, gegen `/health`): zeigt
  „Service: OK".

REST-Variante:

```bash
curl -s http://localhost:8000/runs/demo-run-0001/status | jq .
```

**Welle:** M5-Welle-4a (Status-Endpunkt + TickLoop-Wiring) +
M5-Welle-6b (System-Page);
[`docs/plan/planning/done/M5-welle-4a.md`](../plan/planning/done-archive/M5-welle-4a.md)
+
[`docs/plan/planning/done/M5-welle-6b.md`](../plan/planning/done-archive/M5-welle-6b.md).

### 3.4 Alarme

Browser:
[`http://localhost:8000/runs/demo-run-0001/alarms`](http://localhost:8000/runs/demo-run-0001/alarms)

**Erwartet:** 6-Spalten-Tabelle (Zeit/Ziel/Schweregrad/Code/
Nachricht/Status) mit HTMX-WS-Subscribe auf
`/runs/demo-run-0001/alarms-stream` + REST-Hydration aus
`/runs/demo-run-0001/alarms-history`. Waehrend des Demo-Laufs
erscheinen die im Fault-Window emittierten Alarme (siehe
Schritt 4).

**Welle:** M5-Welle-4b (Alarm-Aggregation + Alarm-Tabelle);
[`docs/plan/planning/done/M5-welle-4b.md`](../plan/planning/done-archive/M5-welle-4b.md).

---

## 4. Fault-Injection

Zwei Pfade — beide reproduzierbar.

### 4.1 YAML-side (Demo-Default, `GG-DEMO-006`)

Das Demo-Scenario aktiviert zwei Faults automatisch:

- **`cell_failure`** auf `battery-1` ab Sim-Zeit **900 000 ms**
  (Tick 900) fuer 50 000 ms (50 Ticks). Effekt: halbiert
  `max_discharge_kw` auf 25 kW; der RuleBasedAgent versucht
  weiter mit −30 kW zu entladen → `power_clamp_limited`-Alarm
  auf der Alarms-Page (Schritt 3.4); Devices-Page zeigt
  `cell_failure_active: true`; Quality-Marker flippt auf
  `fault_injected`.
- **`voltage_drop`** auf `grid-connection-1` ab Sim-Zeit
  **1 200 000 ms** (Tick 1200) fuer 60 000 ms. Effekt: halbiert
  `current_voltage_v`; Devices-Page zeigt `voltage_drop_active:
  true`; kein Alarm (Telemetry-Only-Effekt per [`ADR 0025`](../plan/adr/0025-fault-recovery-pattern.md)).

**Verifikation (manuell):**

```bash
# Pre-Fault-Window (Tick 100): keine Faults aktiv
curl -s http://localhost:8000/runs/demo-run-0001/devices/state | \
    jq '.devices[] | {id: .device_id, q: .quality, state: .state}'

# Warten bis Tick 920 (1000 ms tick_ms = 920 s wall time bei
# 1:1; in der Demo laeuft tick_interval_s=0.1, also ~92 s real).
# Dann erneut pollen → battery-1.cell_failure_active = true.
```

Reproduzierbarkeit: das Scenario laeuft mit fixem Seed (siehe
`gg-demo.yaml`-Header); identische Tick-Counts liefern identische
Outputs ([`GG-SIM-001`](../../spec/lastenheft.md#gg-sim-001)).

**Welle:** M5-Welle-6a (`_compose_fault_port` Battery + Grid-
Adapter; YAML-`faults:`-Block);
[`docs/plan/planning/done/M5-welle-6a.md`](../plan/planning/done-archive/M5-welle-6a.md).

### 4.2 UI-Form-Validation (`GG-UI-007`)

Browser:
[`http://localhost:8000/runs/demo-run-0001/faults`](http://localhost:8000/runs/demo-run-0001/faults)

**Erwartet:** Form mit fuenf Feldern (`fault_type`, `target`,
`start_at_tick`, `duration_ticks`, `recovery`). Submit pruefst
server-side per Cross-Field-Validation (Decision 20):

- `fault_unknown_target` (422): unbekannte Device-ID.
- `fault_invalid_type_for_target` (422): z. B. `voltage_drop` auf
  `battery-1` oder `cell_failure` auf `grid-connection-1`.
- 201 + `fault_id` (UUIDv4) bei valider Eingabe.

**Welle-6a-Anti-Scope:** die UI-Form aktiviert den Fault **nicht
dynamisch** im laufenden TickLoop (Decision 19); produktive Demo-
Faults laufen ueber YAML (Schritt 4.1). Die UI-Form ist Form-
Validation-only — Welle-7+/M6 ergaenzt das dynamische
Activation-Pfad.

---

## 5. Replay-Controls (`GG-UI-004`)

Browser:
[`http://localhost:8000/runs/demo-run-0001/control`](http://localhost:8000/runs/demo-run-0001/control)

Drei Buttons + Status-Polling.

### 5.1 Pause

Klick **Pause** → `POST /runs/demo-run-0001/control` mit Body
`{"action": "pause"}`. Status-Block flippt auf
`paused`; `tick_count`/`simulation_time` bleiben stehen; der
Pre-Tick-Guard im TickLoop schluckt weitere Ticks (No-op).

### 5.2 Resume

Klick **Resume** → analog mit `action: "resume"`. Status flippt
zurueck auf `running`; Counter steigen wieder.

### 5.3 Stop

Klick **Stop** → analog mit `action: "stop"`. Status flippt auf
`stopped`. Weiterer `resume`-Click liefert HTTP 409 mit
`code: "invalid_transition"` — der `stopped`-State ist terminal.

Repository-Mirror: `GET /runs/demo-run-0001` spiegelt jeden
Transition-Schritt persistent in Postgres.

REST-Variante:

```bash
curl -s -X POST http://localhost:8000/runs/demo-run-0001/control \
    -H 'Content-Type: application/json' \
    -d '{"action": "pause"}'
```

**Welle:** M5-Welle-4a (TickLoop-Control + Replay-UI);
[`docs/plan/planning/done/M5-welle-4a.md`](../plan/planning/done-archive/M5-welle-4a.md).

---

## 6. Export

[`GG-DEMO-008`](../../spec/lastenheft.md#gg-demo-008) verlangt einen Export-Schritt — der MVP deckt die
zwei produktiven Export-Surfaces ab:

### 6.1 Snapshot (REST)

```bash
curl -s http://localhost:8000/runs/demo-run-0001/snapshot | jq .
```

**Erwartet (MVP-Stand):**

```json
{
  "run_id": "demo-run-0001",
  "schema_ref": "grid-gym.snapshot.envelope.v2"
}
```

Heutiger Endpoint liefert nur den **Schema-Pointer**; der volle
`SnapshotEnvelope`-v2-Body kommt mit M5-Welle-7-Closure /
M6-Replay-Surface (siehe Bekannte Einschraenkungen unten).

**Welle:** M5-Welle-1 (Endpoint-Stub) + [`ADR 0015`](../plan/adr/0015-snapshot-envelope-v2.md) (Envelope-v2);
[`docs/plan/planning/done/M5-welle-1.md`](../plan/planning/done-archive/M5-welle-1.md).

### 6.2 Live-Telemetry-Stream (WebSocket)

Programmatisch via `wscat` oder Browser-Devtools:

```bash
wscat -c ws://localhost:8000/runs/demo-run-0001/telemetry
```

Pro Tick werden alle `TelemetryPoint`-JSON-Saetze gepusht
(`run_id`, `tick`, `simulation_time`, `device_id`, `metric`,
`value` als String, `unit`, `quality`, `source`, `sequence`).

Analog fuer Alarme:

```bash
wscat -c ws://localhost:8000/runs/demo-run-0001/alarms-stream
```

REST-Fallback fuer Alarme:

```bash
curl -s 'http://localhost:8000/runs/demo-run-0001/alarms-history?limit=50' | jq .
```

**Welle:** M5-Welle-3 (Telemetry-WS) + M5-Welle-4b (Alarm-WS +
History);
[`docs/plan/planning/done/M5-welle-3.md`](../plan/planning/done-archive/M5-welle-3.md)
+
[`docs/plan/planning/done/M5-welle-4b.md`](../plan/planning/done-archive/M5-welle-4b.md).

### 6.3 Postgres-Persistenz

Run-Metadaten + Lifecycle-Transitions sind in Postgres
persistiert (Container `db`, Schema via alembic-Migration).
Direkter Zugriff fuer Audit / Export:

```bash
docker compose -f deploy/compose.yml exec db \
    psql -U grid_gym -d grid_gym -c \
    "SELECT run_id, state, scenario_hash FROM runs;"
```

**Welle:** M1-Welle-6c (Postgres-Repository + alembic-Migration).

---

## Bekannte Einschraenkungen (MVP-Stand 2026-06-04)

- **`GET /snapshot`** liefert nur Schema-Pointer, keinen vollen
  Envelope. Volle Serialisierung ist M5-Welle-7-Closure /
  M6-Material.
- **Kein CSV/JSONL-Export-Endpunkt.** Telemetry/Alarme sind
  ueber WS streambar; Datei-Export ist [`GG-ACCEPT-003`](../../spec/lastenheft.md#gg-accept-003)-Welle-7-
  Material.
- **`POST /runs/{id}/faults`** ist Form-Validation-only — keine
  dynamische TickLoop-Activation (Welle-6a Decision 19;
  produktive Faults via YAML-Scenario, Schritt 4.1).
- **`POST /runs`** ist Welle-1-Stub; persistiert nur die
  `RunMetadata`-Skelett-Felder. Voll-Lifecycle-Erzeugung laeuft
  ueber den Lifespan-getriebenen `_demo_scenario_setup` mit
  fixem Run-ID `demo-run-0001` — die Demo nutzt also nicht den
  POST-Endpunkt sondern den Auto-Setup.
- **[`GG-UI-006`](../../spec/lastenheft.md#gg-ui-006)-Geraete-Grafik** ist Tabellen-basiert
  (HTMX-Polling); kein Inline-SVG-Anlagen-Schaltbild. Inline-
  SVG ist Welle-7+/M6.
- **IEC-61850-Protocol-Adapter** ist `2c-Mock-only-Fallback`
  aktiv ([`ADR 0035`](../plan/adr/0035-iec61850-adapter-profile.md) §2.5; Trigger 009) — `python -m grid_gym demo`
  laeuft ohne IEC-Adapter.

---

## Reproduzierbarkeits-Belege

Die folgenden automatisierten Tests pinnen alle in dieser Abnahme-
Doku zitierten Pfade:

- [`tests/integration/test_m5_welle_5_demo_smoke.py`](../../tests/integration/test_m5_welle_5_demo_smoke.py)
  — Lifespan-Setup + `make demo`-Pfad + Determinismus-Hash-Pin.
- [`tests/integration/test_m5_welle_6a_fault_smoke.py`](../../tests/integration/test_m5_welle_6a_fault_smoke.py)
  — Fault-Injection (UI-Form + YAML; Schritt 4).
- [`tests/integration/test_m5_welle_6b_visualization_smoke.py`](../../tests/integration/test_m5_welle_6b_visualization_smoke.py)
  — Devices-Endpoint + UI-Pages (Schritt 3.2 + 3.3).
- [`tests/integration/test_m5_welle_4a_replay_controls_smoke.py`](../../tests/integration/test_m5_welle_4a_replay_controls_smoke.py)
  — Pause/Resume/Stop (Schritt 5).
- [`tests/integration/test_m5_welle_4b_alarms_smoke.py`](../../tests/integration/test_m5_welle_4b_alarms_smoke.py)
  — Alarm-Tabelle (Schritt 3.4).

Stand am M5-Welle-6c-C2-Lieferzeitpunkt: **1722 Unit-Tests + 80
Integration-Tests + 4 skipped** (`make gates` cache-frei gruen
ohne Override; `make test-integration` gruen).

---

## Forward-Pointer

- **M5-Welle-7 (M5-Closure):** schliesst [`GG-ACCEPT-001`](../../spec/lastenheft.md#gg-accept-001)..003
  (Abnahme-Artefakte, Modellgrenzen-Doku) ab; ueberfuehrt alle
  M5-ADRs (0036..0040) auf `Accepted`.
- **M6 (Performance + Security + CI/CD):** liefert die volle
  Snapshot-Envelope-Serialisierung, CSV/JSONL-Export,
  Inline-SVG-Geraete-Grafik, IEC-61850-Adapter-Reaktivierung
  (Trigger 009).

Siehe
[`docs/plan/planning/in-progress/M5-ui-demo.md §3.2 Welle 7`](../plan/planning/done-archive/M5-ui-demo.md)
fuer den Welle-7-Closure-Plan.
