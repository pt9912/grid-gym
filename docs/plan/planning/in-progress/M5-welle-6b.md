# Welle 6b — M5 UI-Visualization (Geraete-Grafik + Sim-Zustand-Dashboard)

**Status:** In Progress — eroeffnet 2026-06-03 mit C0
(dieser Commit). Zweite Sub-Welle der Welle-6-
Subdivision (siehe [`../done/M5-welle-6a.md`](../done/M5-welle-6a.md)
§0 Sub-Slicing-Beschluss). Welle 6b deckt den UI-
Visualization-Sub-Bereich ab (`GG-UI-006` Geraete-
Grafik + `GG-UI-008` Simulationszustaende-Dashboard).

Welle 6b ist die **achte Code-Welle** in M5 und die
letzte Welle-6-Subdivision mit substantiellem Backend-
Code. Welle 6c (Abnahmedoku `gg-demo-008-abnahme.md`)
schliesst ohne Code-Substanz an.

**Erfuellt:** `GG-UI-006` (1 SOLLTE) + `GG-UI-008` (1
SOLLTE).

---

## 1. Context

### 1.1 Existierende Substanz (M5-Welle-1..6a + M2/M3)

Welle 6b baut auf voll ausgereifter UI- und Backend-
Substanz auf:

**HTTP-API (Welle 1..6a):**

- `GET /runs/{run_id}/status` (Welle 4a) liefert
  `run_id` + `state` + `simulation_time` +
  `tick_count`. **Exakt** die `GG-UI-008`-Pflicht-
  Felder.
- `GET /health` (Welle 1) liefert `{"status": "ok"}`.
  Erfuellt `GG-UI-008`-Akzeptanz „Zustand des
  Simulationsdienstes".
- `GET /runs/{run_id}` (Welle 1) liefert die
  `RunMetadata` (scenario_hash + seed + tick_ms).
- `tick_loop.device_types` (Welle 6a) liefert
  `Mapping[device_id, device_type-string]` —
  Grundlage fuer die `GG-UI-006`-Geraete-Liste.

**Device-State-Surface (M2/M3):**

- `DeviceModel`-Protocol unter
  [`hexagon/core/devices/_protocol.py`](../../../../src/grid_gym/hexagon/core/devices/_protocol.py)
  hat `.device_id`, `.snapshot() -> Mapping[str, object]`
  (canonical State-Dump pro Device-Typ), `.telemetry()
  -> tuple[TelemetryPoint, ...]` (letzte Tick-Telemetry).
- Pro Device-Typ exponiert `.snapshot()` typ-spezifische
  State-Felder:
  - **Battery:** `soc_kwh`, `current_power_kw`,
    `pending_power_kw`, `cell_failure_active`.
  - **PV:** `current_power_kw`, `pending_power_kw`.
  - **Load:** `current_power_kw`, `pending_power_kw`.
  - **GridConnection:** `current_power_kw`,
    `import_kwh`, `export_kwh`, `current_voltage_v`,
    `voltage_drop_active`.
  - **SmartMeter:** kein eigener Power-State (reiner
    Aggregator).
- **TelemetryPoint.quality** (`Quality`-Enum in
  [`hexagon/core/domain/quality.py`](../../../../src/grid_gym/hexagon/core/domain/quality.py))
  hat 5 Werte: `VALID`/`INVALID`/`NAN`/`MISSING`/
  `FAULT_INJECTED`.

**UI-Foundation (Welle 1..6a):**

- Template-Konvention: `<page>.html` (full layout) +
  `_<page>_content.html` (HTMX-Partial), `_is_htmx_
  request`-Switch.
- `templates/navigation.html` traegt heute 6 Links
  (Demo, Health, Dashboard, Control, Alarms, Faults).
- AC-NO-GOD-UTILS: `routes.py` hat 5 public Functions
  (am Limit); `_runs_router.py` hat 4 public Routes
  (1 Slot frei); `_runs_action_router.py` hat 4 public
  Routes (1 Slot frei).

Welle 6b ergaenzt diesen Stack um **einen neuen Backend-
Endpunkt** (`GET /runs/{id}/devices`) und **zwei neue
UI-Pages**.

### 1.2 Welle-6b-Lieferziel

Welle 6b liefert produktiv:

1. **NEU `GET /runs/{run_id}/devices`** unter
   `_runs_router.py` (5. + letzter Slot vor AC-NO-GOD-
   UTILS-Limit) mit Response per Decision 21.
2. **NEU UI-Page `/runs/{run_id}/devices`** mit HTMX-
   Polling auf `/devices` (1s-Trigger). 4-Spalten-
   Tabelle (ID / Typ / Zustand-Subset / Quality-
   Marker). Erfuellt `GG-UI-006`.
3. **NEU UI-Page `/runs/{run_id}/system`** mit HTMX-
   Polling auf `/status` + `/health` (1s-Trigger).
   Layout: Run-Status-Block (state + tick_count +
   sim_time) + Service-Health-Block (status="ok"
   sichtbar). Erfuellt `GG-UI-008`.
4. **NEU `routes_visualization.py`** UI-Modul mit
   beiden Routes (Pattern analog Welle-6a-
   `routes_faults.py`-Split). `routes.py` bleibt am
   Limit.
5. **Navigation-Erweiterung** in
   `templates/navigation.html` um „Devices" + „System"-
   Links.
6. **NEU `tests/integration/test_m5_welle_6b_
   visualization_smoke.py`** mit:
   - `GET /devices` Response-Schema (alle 5 MVP-
     Geraete + Decision-21-Felder).
   - `GET /system` rendert Run-Status + Health-Status.
   - `GET /devices` UI-Page rendert die Tabelle mit
     allen 5 Devices.

### 1.3 Welle-6b-Anti-Scope

Welle 6b liefert **explizit nicht**:

- **Inline-SVG-Geraete-Grafik** — `GG-UI-006`-
  Akzeptanz „grafisch darstellen" ist mit HTMX-
  Partial-Tabelle erfuellt (Lastenheft sagt
  „mindestens MVP-Geraetetypen mit ID, Typ, aktuellem
  Zustand und Qualitaetsstatus"). Inline-SVG /
  Plotly-Anlagengrafik ist Welle 7+/M6 mit eigenem
  Slice + ADR-Pflicht-Check.
- **WebSocket-Live-Updates fuer `/devices`** —
  HTMX-Polling-Pattern analog Welle-4a-Control reicht.
  WS-Push fuer Geraete-State waere ein neuer Stream-
  Port (Architektur-Vertrag), Welle 7+/M6.
- **`GG-DEMO-008` Abnahmedoku** — Welle 6c.
- **Charting-Library-Wechsel** — Decision 23 bleibt
  Chart.js (kein Plotly/ECharts in 6b).
- **Geraete-Detail-Page** (`/runs/{id}/devices/
  {device_id}`) — Welle 7+, falls Stakeholder-
  Druck entsteht.
- **C1 ADR-Commit** — Decision 21 ist API-Schema-
  Erweiterung (kein neuer Driving-Port, kein neuer
  Architektur-Vertrag); Pattern analog Welle-5
  `64d5129` + Welle-6a (Slice-Doc + Code ohne C1).

---

## 2. Scope

| Ebene | Welle-6b-Erweiterung | Welle-6b-Anti-Scope |
| ----- | -------------------- | ------------------- |
| Domain / Simulation | — | — |
| Adapters/driven | — | — |
| Adapters/driving | NEU `GET /runs/{id}/devices` in `_runs_router.py` | WS-Live-Devices-Stream |
| UI | NEU `templates/devices.html` + `_devices_content.html` + `templates/system.html` + `_system_content.html` + NEU `routes_visualization.py` + Navigation-Links | Inline-SVG-Anlagengrafik |
| Konfiguration / Deploy | — | — |
| Doku | — | `gg-demo-008-abnahme.md` (Welle 6c) |
| Tests | 1 Integration-Smoke + Unit-Tests fuer Schema + Quality-Aggregation | — |

---

## 3. Architektur-Entscheidungen (Welle-6b-Decisions)

### 3.1 NEU Decision 21 (Devices-API-Surface) — final fixiert

**Decision:** NEU `GET /runs/{run_id}/devices` antwortet
mit einem JSON-Body, der pro Device im Run einen
Eintrag enthaelt mit:

```json
{
  "run_id": "demo-run-0001",
  "devices": [
    {
      "device_id": "battery-1",
      "device_type": "battery",
      "state": {
        "soc_kwh": "50.000",
        "current_power_kw": "0.000",
        "cell_failure_active": false
      },
      "quality": "valid"
    },
    {
      "device_id": "pv-1",
      "device_type": "pv",
      "state": {
        "current_power_kw": "0.000"
      },
      "quality": "valid"
    },
    {
      "device_id": "load-1",
      "device_type": "load",
      "state": {
        "current_power_kw": "0.000"
      },
      "quality": "valid"
    },
    {
      "device_id": "grid-connection-1",
      "device_type": "grid_connection",
      "state": {
        "current_power_kw": "0.000",
        "current_voltage_v": "400.000",
        "voltage_drop_active": false
      },
      "quality": "valid"
    },
    {
      "device_id": "smart-meter-1",
      "device_type": "smart_meter",
      "state": {},
      "quality": "valid"
    }
  ]
}
```

**`state`-Subset pro Device-Typ** (Welle-6b-Pflicht):

- **battery:** `soc_kwh`, `current_power_kw`,
  `cell_failure_active`.
- **pv** / **load:** `current_power_kw`.
- **grid_connection:** `current_power_kw`,
  `current_voltage_v`, `voltage_drop_active`.
- **smart_meter:** `{}` (kein eigener State).

`Decimal`-Werte werden als Strings serialisiert
(`canonical_json`-Konsistenz; ADR 0021 §2.9 +
Welle-3-Pattern fuer `TelemetryPoint.value`).

**`quality`-Aggregation pro Device:** das Feld ist die
**worst-case-Quality** aus allen `TelemetryPoint`-
Eintraegen der letzten `device.telemetry()`-Sequenz.
Worst-case-Ordnung (von schlechtest nach besser):
`MISSING` > `NAN` > `INVALID` > `FAULT_INJECTED` >
`VALID`. Wenn `device.telemetry()` leer ist (Pre-
First-Tick), faellt der Wert auf `VALID` zurueck.

**Begruendung:**

- `device.snapshot()` ist die Single-Source-of-Truth
  fuer den Device-State (ADR 0014/0015/0016/0017/0018
  Snapshot-Vertraege); wir nehmen nur die UI-Pflicht-
  Felder ins JSON, nicht den vollen Snapshot
  (Snapshot enthaelt z. B. `config`/`run_id`/
  `sequence` — irrelevant fuer Visualization).
- Worst-case-Quality-Aggregation ist die einzige
  semantisch sinnvolle Reduktion: das UI zeigt EINEN
  Quality-Marker pro Device; ein Device mit einer
  FAULT_INJECTED-Telemetry darf nicht als VALID
  erscheinen.
- Welle-1-Pattern: ein neuer GET-Endpunkt fuer eine
  neue UI-Page; kein neuer Driving-Port.

**Out-of-Scope:**

- Device-Detail-Page mit Full-Snapshot (Welle 7+).
- Quality-Drift-Telemetry-Index (separate Welle).
- Pagination / Filter / Sort — Demo hat 5 Devices,
  reicht.

### 3.2 NEU Decision 22 (UI-Pages + Modul-Split) — final fixiert

**Decision:** Zwei neue UI-Pages, beide unter dem
NEU Schwester-Modul `routes_visualization.py`
(Pattern analog Welle-6a `routes_faults.py`-Split):

- `GET /runs/{run_id}/devices` — HTMX-Polling auf
  `/runs/{run_id}/devices` (1s-Trigger), 4-Spalten-
  Tabelle (`ID` / `Type` / `State` / `Quality`).
  Erfuellt `GG-UI-006`.
- `GET /runs/{run_id}/system` — HTMX-Polling auf
  `/runs/{run_id}/status` (1s-Trigger) + `/health`
  (5s-Trigger). Layout: Run-Status-Block (state +
  tick_count + sim_time) + Service-Health-Block
  (`status="ok"` als „Service: OK" oder „Service:
  DEGRADED"). Erfuellt `GG-UI-008`.

**Begruendung:**

- `routes.py` ist mit 5 public Functions am AC-NO-GOD-
  UTILS-Limit; Schwester-Modul wie in Welle-6a.
- Beide Pages teilen sich kein Inline-JS und kein
  Form-Element — getrennte UI-Bereiche, kein Split
  innerhalb 6b noetig.
- Polling-Interval `1s` analog Welle-4a-Control;
  Health-Polling `5s` reicht (kein hoch-frequenter
  Drift).

**Out-of-Scope:**

- Page-Layout-CSS-Polish (Spaltenbreiten, Farben).
  Welle-6b liefert funktionierende Tabelle; Polish
  ist Welle 7+/M6.
- Auto-Refresh-Pause bei Tab-Inactive.

### 3.3 NEU Decision 23 (Charting-Library-Re-Eval) — final fixiert

**Decision:** Kein Charting-Library-Wechsel in Welle
6b. Chart.js (Welle-0-Decision 7) bleibt als Welle-3-
Dashboard-Library. Re-Eval-Ergebnis: keine produktive
Welle-3/4 Limitation aufgetreten, kein Stakeholder-
Druck.

**Konsequenz:**

- `templates/devices.html` nutzt **keine** Chart.js-
  Visualisierung; Welle-6b-Lieferung ist HTMX-Tabelle.
- Welle-3-Dashboard (`/runs/{id}/dashboard`) bleibt
  Chart.js-getrieben unveraendert.
- Re-Eval als Welle-7+/M6-Forward-Pointer dokumentiert.

**Begruendung:**

- ADR 0036 §2.5 verankert Chart.js als M5-Default;
  Re-Eval-Schwelle ist „Stakeholder-Druck oder
  konkrete Limitation". Welle 3/4 zeigten keine.
- Plotly/ECharts-Migration ist Welle-7+/M6-Slice mit
  eigener ADR-Lifecycle-Klausel.

**Out-of-Scope:**

- Plotly/ECharts-Spike-Test in Welle 6b.

---

## 4. Liefer-Reihenfolge (3..4 Commits)

### Pre-C0 — bereits erledigt (Welle-6a-Closure)

1. **Welle-6a-C4a** `70fb82c` — Self-Close-Move
   `M5-welle-6a.md → done/` (rename-only).
2. **Welle-6a-C4b** `b19aeae` — Cross-Doc-Refs-Sync.
3. **Welle-6a-Review-Folge** `1e3a793` — 15 Findings
   adressiert (zwischen C4b und Welle-6b-C0).

Welle 6b startet damit direkt mit C0 (kein eigener
Pre-C0a/Pre-C0b noetig — die Konvention macht Welle-6a-
Closure-Move zum effektiven Pre-C0 der Folge-Welle).

### C0 — `docs(plan)`: M5-welle-6b Slice-Doc + Decisions 21/22/23

**Dieser Commit.** Schreibt
`docs/plan/planning/in-progress/M5-welle-6b.md` mit:

- Decisions 21/22/23 final fixiert (siehe §3).
- Scope + Anti-Scope (kein WS-Live, kein Inline-SVG,
  kein Chart.js-Wechsel).
- Liefer-Reihenfolge (C0 → C2 → C3 → C4a/b).
- Critical Files + Verifikationspfad + Risiken.
- DoD-Checkliste (initial leer; C3 hakt ab).

Keine ADR-Aenderung in C0 — Welle 6b hat keinen neuen
Driving-Port-Slot und keinen neuen Architektur-Vertrag.

### C1 — **bewusst entfaellt** (Pattern Welle-1 + Welle-5 + Welle-6a)

Welle 6b fuehrt **keinen neuen Driving-Port** und
**keinen neuen Architektur-Vertrag** ein. Decision 21
ist Schema-Erweiterung im bestehenden HTTP-API;
Decisions 22/23 sind UI-Routing/Library-Layout-
Entscheidungen. Falls C2-Pre-Research eine unerwartete
neue Vertrags-Substanz findet, kann C1 als
`docs(adr): M5-Welle-6b-C1 — NEU ADR 0041 (...)`
nachgereicht werden — heute kein Anlass.

### C2 — `feat(welle-6b)`: Devices-Endpunkt + UI-Pages + Smoke-Test

**Code-Merge** mit:

- Erweiterung
  `src/grid_gym/adapters/driving/http_api/_runs_router.
  py`: NEU `GET /runs/{run_id}/devices`-Endpunkt (5.
  + letzter Slot vor AC-NO-GOD-UTILS-Limit).
- Erweiterung
  `src/grid_gym/adapters/driving/http_api/_schemas.py`:
  NEU `DevicesResponse` + `DeviceStateEntry`-Pydantic-
  Modelle.
- NEU Helper-Modul fuer
  Worst-case-Quality-Aggregation +
  State-Subset-Extraction (entweder in
  `_runs_router.py` als private Helfer oder in
  `_devices_view.py` Schwester-Modul, abhaengig von
  Komplexitaet).
- NEU `src/grid_gym/adapters/driving/ui/templates/
  devices.html` + `_devices_content.html`.
- NEU `src/grid_gym/adapters/driving/ui/templates/
  system.html` + `_system_content.html`.
- NEU `src/grid_gym/adapters/driving/ui/
  routes_visualization.py` mit beiden Routes.
- Erweiterung
  `src/grid_gym/adapters/driving/http_api/app.py`:
  `routes_visualization.visualization_router`
  zusaetzlich mounten.
- Erweiterung `templates/navigation.html`: NEU
  „Devices" + „System"-Links.
- NEU `tests/integration/
  test_m5_welle_6b_visualization_smoke.py`
  (Schema-Pin + UI-Page-Rendering + Quality-
  Aggregation-Smoke).
- NEU Unit-Tests fuer Quality-Aggregation +
  State-Subset-Extraction.
- Tests: Coverage-Gates gruen halten, `make gates`
  cache-frei gruen.

### C3 — `docs(plan)`: Welle-6b Status/DoD-Sync + Top-Level-Doku-Sync

**Status/DoD-Sync** mit:

- `M5-welle-6b.md` Status `In Progress → Done` +
  §10 C2-Realization-Notes (falls vorhanden).
- `M5-ui-demo.md §3.1 Welle-Status-Tabelle` Zeile
  Welle 6b auf `Done` + Welle-6c-Aktive-Welle-Marker.
- `in-progress/README.md` Welle-6b-Closure-Block +
  Welle-6c-Aktive-Welle-Marker.
- `in-progress/roadmap.md` Welle-6b-Closure-Entry.
- `README.md` + `README.de.md` Test-Counts +
  GG-UI-006/008-Coverage-Bullet.

### C4 — `chore`: Self-Close-Move + Cross-Doc-Refs-Sync

Pflicht-Closure-Sequenz per
[`planning/README.md`](../README.md) Wave-Self-Close-
Commit-Konvention:

- **C4a** — `chore: git mv in-progress/M5-welle-6b.md
  → done/` (rename-only).
- **C4b** — Cross-Doc-Refs-Sync nach Move
  (Pattern analog Welle-6a-C4b `b19aeae`).

---

## 5. Critical Files

**Welle-6b-NEU (geschrieben in C2):**

- `src/grid_gym/adapters/driving/ui/templates/
  devices.html` + `_devices_content.html`.
- `src/grid_gym/adapters/driving/ui/templates/
  system.html` + `_system_content.html`.
- `src/grid_gym/adapters/driving/ui/
  routes_visualization.py`.
- `tests/integration/test_m5_welle_6b_visualization_
  smoke.py`.
- NEU Unit-Tests fuer Quality-Aggregation +
  State-Subset-Extraction.

**Welle-6b-MODIFY (in C2):**

- `src/grid_gym/adapters/driving/http_api/
  _runs_router.py` — NEU 5. Route `get_run_devices`.
- `src/grid_gym/adapters/driving/http_api/
  _schemas.py` — NEU `DevicesResponse` +
  `DeviceStateEntry`-Modelle.
- `src/grid_gym/adapters/driving/http_api/app.py` —
  `routes_visualization.visualization_router`
  einbinden.
- `src/grid_gym/adapters/driving/ui/templates/
  navigation.html` — NEU 2 Links.

**Welle-6b-UNBERUEHRT (kein Edit):**

- `tick_loop.device_types` (Welle 6a) bleibt
  unveraendert; wir greifen darauf zu.
- Welle-3-Dashboard-Page.
- Welle-4a-Control-Page.
- Welle-4b-Alarms-Page.
- Welle-6a-Faults-Page.

---

## 6. Verifikationspfad

**Welle-6b-Gate (per `M5-ui-demo.md §3.1` neue Zeile):**

- `make gates` cache-frei gruen ohne Override.
- `make demo` lokal: Devices-Page zeigt alle 5
  Demo-Geraete mit `quality="valid"` initial; nach
  Tick 900 (cell_failure-Window) zeigt
  `battery-1.state.cell_failure_active = true`.
  System-Page zeigt Run-Status + Service: OK.

**Test-Verifikation:**

- `make test-unit` gruen (kein Regress).
- `make test-integration` gruen:
  - NEU `test_m5_welle_6b_visualization_smoke.py`
    (65 → 66 Integration-Tests).
- Coverage-Gates gruen.

**Abnahme-Verifikation (Lastenheft):**

- `GG-UI-006` (Geraete-Grafik per Tabelle mit ID +
  Typ + Zustand + Quality fuer alle 5 MVP-
  Geraetetypen).
- `GG-UI-008` (Simulationszustaende per Dashboard mit
  state + tick_count + sim_time + Service-Health).

---

## 7. Risiken

**R1 — `Decimal`-Serialisierung in Pydantic.** Pydantic
v2 serialisiert `Decimal` Default-mässig als float oder
string je nach Konfiguration. Welle-3-Pattern (TelemetryPoint)
serialisiert `value` als string. **Mitigation:** explizit
`@field_serializer` oder `model_config = {"json_
encoders": {Decimal: str}}` setzen; Welle-3-Pattern
nachschauen + uebernehmen.

**R2 — Quality-Aggregation bei leerer Telemetry.**
Pre-First-Tick haben Devices `telemetry() == ()`.
**Mitigation:** Explizit `VALID`-Default; Smoke-Test
prueft den Pre-Tick-Pfad.

**R3 — `tick_loop.device_types` und
`tick_loop._devices` Sync.** Welle-6a `device_types`
skippt unbekannte Klassen; aber `_devices` enthaelt
sie noch. Wenn wir die Liste durchwandern, muessen wir
das _device_type_for-Pattern symmetrisch nutzen.
**Mitigation:** Helper-Funktion `_collect_device_views`
nutzt die gleiche `_device_type_for`-Logik per Welle-
6a-Pattern (try/except); unbekannte Devices werden
silent gedroppt, konsistent.

**R4 — AC-NO-GOD-UTILS auf `_runs_router.py`.** Mit
dem neuen `get_run_devices` waeren 5 public Functions
im Modul (am Limit). Falls Welle 7+ noch einen GET-
Endpunkt braucht, muss gesplittet werden.
**Mitigation:** Slice-Doc dokumentiert das im
Realization-Note; Welle-7+/M6-Refactor-Pflicht.

**R5 — HTMX-Polling-Performance.** 1s-Polling auf
`/devices` + `/status` gleichzeitig erzeugt
2 Requests/s bei aktivem Tab. **Mitigation:**
Welle-6b-Default ist OK; Auto-Pause bei Tab-Inactive
ist Welle 7+/M6.

---

## 8. Wandert nach

- Bei C3-Closure: `M5-welle-6b.md` bleibt in
  `in-progress/` bis C4a Self-Close-Move.
- `M5-ui-demo.md` bleibt in `in-progress/` bis
  M5-Welle-7-Closure.
- Welle 6c (`GG-DEMO-008` Abnahmedoku) als naechster
  aktiver Schritt nach Welle 6b — letzte Sub-Welle
  der Welle-6-Subdivision.

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [ ] **NEU `GET /runs/{run_id}/devices`** in
  `_runs_router.py` mit Decision-21-Schema.
- [ ] **NEU `DevicesResponse` + `DeviceStateEntry`**
  Pydantic-Modelle in `_schemas.py`.
- [ ] **NEU `templates/devices.html` +
  `_devices_content.html`** (HTMX-Polling-Tabelle,
  Decision 22).
- [ ] **NEU `templates/system.html` +
  `_system_content.html`** (HTMX-Polling-Status +
  Health-Anzeige).
- [ ] **NEU `routes_visualization.py`** mit zwei
  Routes (devices + system).
- [ ] **`app.py`** mountet
  `visualization_router`.
- [ ] **Navigation um „Devices" + „System"-Links
  erweitert**.
- [ ] **NEU `tests/integration/
  test_m5_welle_6b_visualization_smoke.py`** mit:
  - GET /devices Schema-Pin (alle 5 Devices, alle
    Decision-21-Felder).
  - GET /devices-UI rendert die Tabelle.
  - GET /system-UI rendert Status + Health.
  - Quality-Aggregation: Telemetry mit
    `FAULT_INJECTED` → Device-quality = `fault_
    injected`.
- [ ] **NEU Unit-Tests** fuer Quality-Aggregation +
  State-Subset-Extraction.
- [ ] **`make test-unit`** gruen.
- [ ] **`make test-integration`** gruen mit dem
  neuen Welle-6b-Smoke.
- [ ] **`make arch-check`** alle Contracts kept.
- [ ] **`make typecheck`** gruen.
- [ ] **`make gates`** cache-frei gruen ohne
  Override.
- [ ] **`make docs-check`** cache-frei gruen.
- [ ] **`make demo`** zeigt Devices-Page mit allen 5
  Geraeten + Quality-Markern; System-Page mit
  Service: OK (manuelle Verifikation).
- [ ] **`GG-UI-006 + GG-UI-008`** erfuellt.
- [ ] **`M5-ui-demo.md §3.1 Welle-Status-Tabelle`**
  Welle-6b-Zeile auf `Done <C3-Datum>` geflipt.
- [ ] **`in-progress/README.md`** Welle-6b-Closure-
  Block + Welle-6c-Aktive-Welle-Marker.
- [ ] **`roadmap.md`** Welle-6b-Closure-Entry.
- [ ] **Top-Level-Doku-Sync** (`README.md` +
  `README.de.md` Test-Counts + GG-UI-006/008-Bullet).
- [ ] **NEU C4 Self-Close-Move + Cross-Doc-Refs-
  Sync** als zwei separate Folge-Commits nach C3.

**Anti-Scope-Verifikation (Welle 6b NICHT):**

- [ ] Keine Inline-SVG-Geraete-Grafik (Welle 7+/M6).
- [ ] Kein WS-Live-Stream fuer `/devices` (Welle 7+/M6).
- [ ] Kein `GG-DEMO-008` Abnahmedoku (Welle 6c).
- [ ] Kein Charting-Library-Wechsel (Decision 23).
- [ ] Kein Geraete-Detail-Page (Welle 7+).
- [ ] Kein C1-ADR-Commit.

---

## References

- [`M5-ui-demo.md`](M5-ui-demo.md) §3.2 Welle 6b
  Plan-Items (kanonische Sub-Slicing-Aufnahme; Welle-
  6b UI-Visualization-Sub-Bereich).
- [`../done/M5-welle-6a.md`](../done/M5-welle-6a.md)
  §0 Sub-Slicing-Beschluss — Welle 6 → 6a/6b/6c
  drei-Sub-Slices-Pattern.
- [`../done/M5-welle-4a.md`](../done/M5-welle-4a.md)
  — Welle-4a-`/status`-Endpunkt (Welle-6b-System-
  Page nutzt ihn unveraendert via HTMX-Polling).
- [`../done/M5-welle-3.md`](../done/M5-welle-3.md)
  — Welle-3-Dashboard-Pattern + TelemetryPoint
  Quality-Marker.
- [`../../adr/0014-battery-snapshot-schema.md`](../../adr/0014-battery-snapshot-schema.md)
  + [`../../adr/0017-grid-connection-device-pattern.md`](../../adr/0017-grid-connection-device-pattern.md)
  + [`../../adr/0016-pv-load-device-pattern.md`](../../adr/0016-pv-load-device-pattern.md)
  + [`../../adr/0018-smart-meter-device-pattern.md`](../../adr/0018-smart-meter-device-pattern.md)
  — Device-Snapshot-Schemas (Welle-6b-Decision-21-
  State-Subset entstammt diesen ADRs).
- [`../../../../spec/lastenheft.md §17`](../../../../spec/lastenheft.md)
  `GG-UI-006` + `GG-UI-008` Akzeptanztexte.
- Pattern-Vorbild **AC-NO-GOD-UTILS-Modul-Split**:
  [`../done/M5-welle-6a.md`](../done/M5-welle-6a.md)
  §10.2 (Welle-6a-`routes_faults.py`-Split aus
  `routes.py`).
- Pattern-Vorbild **Welle-ohne-C1**:
  [`../done/M5-welle-5.md`](../done/M5-welle-5.md)
  + [`../done/M5-welle-6a.md`](../done/M5-welle-6a.md)
  (kein neuer Port, kein neuer Vertrag).
