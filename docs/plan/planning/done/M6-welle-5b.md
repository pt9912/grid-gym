# Welle 5b — M6 Sim/Prod-Marker + Input-Validation (`GG-SAFE-007/008` MUSS)

**Status:** Done 2026-06-07.
**Liefer-Hash-Stack:** C0 `0d3bb61` (Slice-Doc-Anlage) → C0-
Review-Folge `369f130` (F1 Adapterkonfig-Scope + F2 C1-Pflicht-
Findings) → C1 `cee5aab` (NEU ADR 0045 `Proposed` + ADR-Index
+ Hygiene-Cleanup ADR 0041-0045 in `9d78b29` als parallele
Hygiene-Welle) → C2 `b580840` (6 Inline-Fixes fuer GG-SAFE-
007-Surfaces + `_BaseRequest`-Mixin + `RunCreateRequest`-
Umzug + 11 Smoke-Tests + Audit-Doku) → C3 **dieser Commit**
(ADR 0045 `Proposed → Provisional` + Status/DoD-Sync +
aktive Welle auf 5c). C4a/C4b folgen als Welle-5c-Pre-C0a/
Pre-C0b.

**Vorheriger Status:** In Progress — C2 abgeschlossen,
ADR 0045 noch `Proposed`.

Welle 5 wird gemaess Welle-5a-D-1 in **5a (Quality-Pipeline-
Audit; `GG-SAFE-001..004` MUSS) + 5b (Sim/Prod-Marker + Input-
Validation; `GG-SAFE-007` + `GG-SAFE-008` MUSS) + 5c (SOLLTE-
Items + IP/Netz-Beschraenkung; `GG-SAFE-005` + `GG-SAFE-006` +
Demo-Compose-Hardening)** sub-geslict. Welle 5b ist die **zweite
Sub-Welle** und liefert die End-to-End-Verifikation + Luecken-
Auditierung der existierenden Sim/Prod-Trennung + Input-
Validation-Substanz fuer die zwei MUSS-IDs.

**Audit-Ergebnis (alle ✓ produktiv nach Welle-5b-C2):**

- `GG-SAFE-007` UI ✓ produktiv (NEU `.sim-banner` in
  `base.html` mit DE/EN-Disclaimer; per Vererbung auf allen
  UI-Pages).
- `GG-SAFE-007` API-Doku ✓ produktiv (OpenAPI `info.
  description` + README + README.de mit Sim/Prod-Disclaimer).
- `GG-SAFE-007` Adapterkonfiguration ✓ produktiv (`gg-demo.
  yaml` Top-Level-Kommentar + 5 `protocol_*/_config.py`-
  Docstring-Disclaimer).
- `GG-SAFE-008` REST-Schema-Vertrag ✓ produktiv (NEU
  `_BaseRequest`-Mixin mit `strict=True` + `extra="forbid"`;
  alle 3 Request-Bodies erben).
- `GG-SAFE-008` REST-Wertebereiche + Zielressourcen ✓
  produktiv (Pydantic-Field-Constraints + Cross-Field-
  Validation aus M5-Welle-6a).
- `GG-SAFE-008` WebSocket Subscribe-only ✓ produktiv
  (Quell-Datei-Inspektion belegt: kein `websocket.receive_*`).
- `GG-SAFE-008` Driven-Side ✓ produktiv (Welle-5a-Audit-
  Substanz; siehe `safe-001-004-quality-pipeline.md`).

**Pre-C0 abgeschlossen (M6-Welle-5a-Closure-Folge):**

- C4a `f35ab67` — `git mv M6-welle-5a.md → done/` (Self-
  Close-Move, rename-only).
- C4b `2e3bf72` — Cross-Doc-Refs-Sync nach Move + Hash-Slot-
  Fills. **Welle 5a komplett**: 7 Smoke-Tests + Audit-Doku +
  2 NEU `open/`-Triggers 034/035; Stack `4b36185..52cb698`.

**Spec-Reife:** Inhaltlich final fuer Welle 5b. Welle-5b-
Decision-Liste (§3) schliesst Welle-5b-D-1..D-6: Audit-Form,
Sim/Prod-Marker-Surfaces, Input-Validation-Audit-Umfang,
Luecken-Adressier-Strategie, Strict-Mode-Schaerfungs-Strategie,
ADR-Bedarf.

---

## 1. Context

`GG-SAFE-007/008` MUSS (Lastenheft Z. 1395-1408):

- **`GG-SAFE-007`**: Die Plattform MUSS Simulations- und
  Produktivkontexte klar trennen. **Akzeptanz:** UI, API-
  Dokumentation und **Adapterkonfiguration** kennzeichnen
  Simulationsadapter als nicht fuer produktive Anlagensteuerung
  freigegeben. **Drei Pflicht-Surfaces** — keine darf im Audit
  weggelassen werden.
- **`GG-SAFE-008`**: Die Plattform MUSS Eingaben an externen
  Schnittstellen validieren. **Akzeptanz:** REST-, WebSocket-
  und alle implementierten Adapter-Eingaben werden gegen
  Schema, Wertebereiche und Zielressourcen validiert, bevor
  sie in den Simulationskern gelangen.

### 1.1 Existierende Substanz (vor Welle 5b)

**`GG-SAFE-007` Sim/Prod-Trennung:**

- **`GG-NONGOAL-001`** Lastenheft Z. 1161-1163: produktive
  Anlagensteuerung ist strukturell ausgeschlossen (verankert
  in `carveouts.md §2.7` Permanent-Out-of-Scope).
- **`README.md` Z. 5** + **`README.de.md` Z. 6**: `grid-gym`
  als „open-source platform for the **deterministic
  simulation**, replay, and validation" deklariert; vollstaendige
  Produktiv-Anlagensteuerungs-Ablehnung im Disclaimer-Block.
- **Architektur-Pruefung in `tools/arch_check.py`**: Lastenheft
  §22 GG-SAFE-007-Realisierung-Zeile nennt
  `AC-HEXAGON-PURE`-Whitelist als Marker; Adapter koennen nur
  ueber Hexagon-Ports an den Simulationskern andocken — kein
  Direct-Wire an reale Steuerungsaktoren moeglich.
- **OpenAPI-Metadata** (`adapters/driving/http_api/app.py`
  Z. 99-103): `_APP_DESCRIPTION` nennt „Driving-Adapter fuer
  den `grid-gym`-Simulationskern" — Simulations-Kontext im
  generierten OpenAPI-Schema sichtbar.
- **UI-Layer**: Templates referenzieren `simulation_time`,
  `Sim time (ms)` — Sim-Kontext im UI sichtbar, aber **kein
  expliziter Banner / Disclaimer** der Sim/Prod-Trennung
  herausstellt (Welle-5b-Audit-Verdacht).
- **Adapterkonfiguration** (Lastenheft Z. 1399 explizit als
  dritte Pflicht-Surface neben UI + API-Doku):
  Scenario-YAML-Konfiguration unter `deploy/scenarios/*.yaml`
  inkl. `gg-demo.yaml`; ggf. Protocol-Adapter-Config-Module
  unter `adapters/driven/protocol_*/_config.py`. **Welle-5b-
  Audit-Verdacht:** Sim-Marker als Top-Level-YAML-Kommentar-
  Block oder als deklaratives Feld (z. B. `simulation_only:
  true`) ist aktuell nicht erkennbar; Adapter-Config-Module
  haben kein Modul-Docstring-Disclaimer.

**`GG-SAFE-008` Input-Validation:**

- **HTTP-API-Pydantic-Validation** (`adapters/driving/http_api/
  _schemas.py` + zusaetzlich `app.py`): Pydantic-BaseModel-
  Validation fuer alle REST-Endpunkte; Schema-Fehler → 422 mit
  `ErrorResponse`. **Modell-Verteilung**:
  - In `_schemas.py`: `RunDetailResponse`, `RunStatusResponse`,
    `ControlRequest/Response`, `SnapshotResponse`,
    `FaultInjectionRequest/Response`, `AlarmDto/sResponse`,
    `DeviceStateEntry/sResponse`, `ErrorResponse`.
  - In `app.py` (Welle-1-Era-Drift): `HealthResponse`,
    **`RunCreateRequest`** (`POST /runs`), `RunCreateResponse`.
    Welle-5b-Audit-Befund: `RunCreateRequest` ist eine
    **externe Eingabe** (`POST /runs`) und damit GG-SAFE-008-
    Pflicht-Surface — der Modell-Pfad muss bei der Strict-
    Mode-Schaerfung mit-erfasst sein (Konsolidierung empfohlen).
  - **Default-Pydantic-Mode** an allen Request-Bodies (kein
    `model_config = ConfigDict(strict=True, extra="forbid")`
    → Welle-5b-Audit-Verdacht: extra-Felder werden silent
    ignoriert, type-Coercion ist aktiv).
- **Scenario-Loader-Validation** (`hexagon/core/scenario/
  loader.py`): Welle-5a-bestaetigt — `GG-SAFE-001`-Substanz
  produktiv inklusive Schema-/Wertebereichs-Validierung mit
  typisierten `ScenarioValidationError`-Familie.
- **WebSocket-Inputs**: `WS /runs/{run_id}/telemetry`-
  Endpoint (Welle 3, ADR 0038) abonniert nur per
  `TelemetryStreamPort.subscribe` — kein Client-WS-Message-
  Payload-Eingang in den Kern; `WS /runs/{run_id}/alarms-stream`
  (Welle 4b, ADR 0040) analog. **`run_id`-Path-Parameter**
  wird ueber FastAPI-Routing als `str` extrahiert ohne explizite
  UUID-Validation → Welle-5b-Audit-Verdacht (`run_id`-Drift-
  Vektor).
- **Adapter-Eingaben** (Protocol-Adapter OPC-UA/IEC-61850/
  Modbus/DNP3/MQTT): pro Adapter eigene Lese-Validation +
  Quality-Emission (siehe Welle-5a-Audit). **DriveSide-Adapter**
  (HTTP-API/UI) deckt REST-Inputs ab; **Driven-Side-Adapter**
  (Protocol-Adapter) deckt Outbound-Reads ab. Welle-5b-Audit
  prueft beide Sides.

### 1.2 Welle-5b-Lieferziel

**Audit-Welle** (Pattern analog Welle 5a, NICHT primaer
NEU-Code-Welle): die existierende Sim/Prod-Marker- und Input-
Validation-Substanz wird **End-to-End verifiziert + Lücken
identifiziert**. Vier orthogonale Liefer-Items:

1. **NEU `tests/integration/test_m6_welle_5b_safe_007_008_
   smoke.py`** (Welle-5b-C2) — **11 Smoke-Tests** fuer GG-SAFE-007
   (Sim/Prod-Marker an drei Pflicht-Surfaces UI + API-Doku +
   Adapterkonfiguration) und GG-SAFE-008 (Input-Validation-
   Pflicht-Pfade):
   - `test_safe_007_openapi_description_marks_simulation`
     (API-Doku-Surface): `GET /openapi.json` enthaelt im
     `info.description` einen Sim/Prod-Marker (Substring
     `simulation` ODER konkreter Disclaimer-Begriff).
   - `test_safe_007_readme_disclaimer_present` (Doku-Smoke;
     API-Doku-Surface ergaenzend): `README.md` UND
     `README.de.md` enthalten den Sim-only-Disclaimer als
     Substring.
   - `test_safe_007_arch_check_hexagon_pure_whitelist`
     (Architektur-Belegung der Sim/Prod-Trennung):
     `AC-HEXAGON-PURE`-Contract ist im `tools/arch_check.py`
     verankert + `make arch-check` gruen ohne neue Whitelist-
     Eintraege fuer Produktiv-Anlagen-Adapter.
   - `test_safe_007_ui_dashboard_has_simulation_marker`
     (UI-Surface): UI-Dashboard-Page (`GET /runs/{id}/
     dashboard`) zeigt einen sichtbaren Sim-Marker (Banner,
     Title oder Footer). Falls Lücke → Inline-Fix (Welle-
     5b-D-3) ODER `open/`-Trigger.
   - `test_safe_007_adapter_config_marks_simulation` (NEU;
     Adapterkonfiguration-Surface): Scenario-YAML
     `deploy/scenarios/gg-demo.yaml` enthaelt einen
     deklarativen Sim-Marker (Top-Level-Kommentar-Block ODER
     Feld). Welle-5b-D-2 Option B fixiert die Form
     (Kommentar-Block + ggf. Loader-Doc-String-Pflicht).
     Falls Lücke → Inline-Fix.
   - `test_safe_008_rest_invalid_payload_rejected_422`:
     `POST /runs` mit invalid `scenario_hash` (zu kurz) →
     422 + `ErrorResponse`.
   - `test_safe_008_rest_extra_field_rejected` (Welle-5b-D-5
     Strict-Vertrag): `POST /runs/{id}/control` mit extra-
     Field (`unknown_key`) wird **rejected** mit 422 +
     `extra_forbidden`-Error-Pointer. **Strict-Assert**: kein
     silent-ignore akzeptiert. Welle-5b-D-3 Inline-Fix-Pflicht
     im selben C2.
   - `test_safe_008_rest_type_coercion_rejected` (Welle-5b-D-5
     Strict-Vertrag): `POST /runs` mit `seed="42"` (String
     statt Int) wird **rejected** mit 422. **Strict-Assert**:
     keine silent-Coercion akzeptiert. Welle-5b-D-3 Inline-
     Fix-Pflicht im selben C2.
   - `test_safe_008_websocket_invalid_run_id_rejected`:
     `WS /runs/{invalid-uuid}/telemetry`-Connect mit nicht-
     UUIDv4-`run_id` wird rejected (404 ODER Connect-Close
     mit Diagnose).
   - `test_safe_008_websocket_no_client_payload_accepted`:
     `WS /runs/{id}/telemetry`-Subscribe ignoriert Client-
     Payloads (Verifikation: keine Eingangs-Wirkung auf den
     Kern).
   - `test_safe_008_fault_injection_target_validated`:
     `POST /runs/{id}/faults` mit unbekanntem `target` →
     422 ODER 404 mit klarer Diagnose.

2. **NEU `docs/user/safe-007-008-sim-prod-input-validation.md`**
   (Welle-5b-C2) — Audit-Tabelle:
   - **GG-SAFE-007 Sim/Prod-Marker** (drei Pflicht-Surfaces aus
     Lastenheft Z. 1399): pro Surface — (a) **UI**
     (UI-Templates + Dashboard-Banner), (b) **API-Doku**
     (OpenAPI `info.description` + README + README.de),
     (c) **Adapterkonfiguration** (Scenario-YAML +
     Protocol-Adapter-Config-Module) → Substanz-Pfad +
     Status (✓ produktiv / Lücke). Zusatzbeleg:
     arch_check `AC-HEXAGON-PURE`-Whitelist.
   - **GG-SAFE-008 Input-Validation:** pro Schnittstelle
     (REST-Endpunkte/WebSocket-Endpunkte/Driven-Adapter) →
     Substanz-Pfad + Test-Pfad + Status. REST-Pydantic-Mode
     (strict/forbid) explizit dokumentiert.

3. **Pydantic-Strict-Mode-Schaerfung** (Welle-5b-C2; Welle-5b-D-5)
   — falls Audit zeigt: extra-Felder silent ignored und/oder
   type-Coercion aktiv: NEU `model_config = ConfigDict(strict=
   True, extra="forbid")` in einem zentralen `_BaseRequest`-
   Mixin oder per-Model. Pflicht-Inline-Fix im selben C2.
   Welle-5b-D-5 entscheidet die Form (zentral vs per-Model).

4. **Luecken-Adressierung** (Welle-5b-C2) — falls Audit
   substantielle Luecken aufdeckt: NEU `open/`-Trigger
   (Welle-5b-D-3 Hybrid analog Welle-5a-D-3). Erwartete
   Kandidaten:
   - **UI-Sim-Marker** falls Dashboard ohne sichtbaren Marker:
     Inline-Fix (Template-Edit) bevorzugt; Trigger nur falls
     UI-Refactor noetig.
   - **Adapter-Config-Sim-Marker** falls Scenario-YAML +
     Protocol-Adapter-Config-Module ohne Disclaimer: Inline-
     Fix (YAML-Kommentar-Block + Docstring-Add) Pflicht im
     selben C2 (kleiner Edit, Welle-5b-D-2 Option B verlangt
     den Marker).
   - **`run_id`-UUID-Validation** falls REST/WS-Endpoints
     `run_id` als `str` ohne UUID-Check akzeptieren:
     Inline-Fix per Pydantic-Field-Constraint ODER FastAPI-
     Path-Parameter-Annotation.

### 1.3 Welle-5b-Anti-Scope

- **Kein `GG-SAFE-005/006` SOLLTE-Items** — Welle-5c-Scope.
- **Keine IP-/Netz-Beschraenkung im Demo-Compose** — Welle-
  5c-Scope.
- **Keine Adapter-Quality-Emission-Aenderungen** — Welle-5a
  hat das audited; Trigger 034/035 sind die Folge-Pfade.
- **Keine neue Quality-Enum-Variante** — M5-Welle-6b-Review
  F15 fixiert (Welle-5a-Erbschaft).
- **Keine substantielle FastAPI-Routing-Refactor** — falls
  `run_id`-UUID-Validation komplex wird, dann `open/`-Trigger.
- **Kein NEU ADR** wenn vermeidbar — Welle-5b-D-6 prueft
  Strict-Mode-Schaerfungs-Bedarf; ADR nur falls Pydantic-Strict-
  Mode als Adapter-Vertrag verankert wird (Schaerfung von
  ADR 0037 HTTP-API-Surface-Pattern moeglich).
- **Kein NEU Code im Core** — Audit + Tests + Doku + ggf.
  Adapter-Side-Pydantic-Schaerfung.

---

## 2. Scope

Welle 5b liefert **drei Items** ueber 3 Commits (C0..C3),
plus Self-Close-Folge C4a/C4b.

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses Dokument;
   `in-progress/README.md` Bestand-Tabelle + Aktive-Welle-Block
   auf Welle 5b; `M6-perf-security-cicd.md §3.1` Welle-5b-Zeile
   `Pending → In Progress`.
2. **C1 Pflicht** — Welle-5b-D-5 hat den Default-Pydantic-Mode
   bereits in §1.1 als Lücke identifiziert und D-6 finalisiert
   Option C (NEU Schaerfungs-ADR). C1 als **NEU eigenstaendige
   Schaerfungs-ADR 0045** (`docs/plan/adr/0045-http-api-
   request-strict-validation.md`) per ADR-0011-Pattern mit
   Bezug auf ADR 0037 + ADR-Index-Update **muss vor C2 landen**,
   damit der in C2 implementierte Strict-Mode-Vertrag einen
   ADR-Anker hat. **ADR 0037 wird NICHT editiert** (bleibt
   `Accepted`). Pattern analog M5-Welle-1-C1 `d468e68` (ADR 0037
   `Proposed` vor C2-Code-Merge).
3. **Code-Substanz** (C2) — NEU `tests/integration/test_m6_
   welle_5b_safe_007_008_smoke.py` (11 Smoke-Tests) + NEU
   `docs/user/safe-007-008-sim-prod-input-validation.md`
   Audit-Tabelle + Pydantic-Strict-Mode-Schaerfung (Welle-5b-D-5)
   + Inline-Luecken-Fixes (Welle-5b-D-3). Lokal-Verifikation
   alle Gates gruen.
4. **Status/DoD-Sync** (C3) — Status-Flip + Aktive-Welle-
   Block auf Welle 5c; Top-Level-Doku-Sync.

Self-Close-Folge C4a/C4b laufen nach C3 als M6-Welle-5c-Pre-
C0a/Pre-C0b.

---

## 3. Architektur-Entscheidungen (Welle-5b-Decision-Liste)

### Welle-5b-D-1 — Audit-Form

**Frage:** Wie wird die GG-SAFE-007/008-Akzeptanz audited?

**Welle-5b-Final: Option C (Doku + Smoke-Tests).**
Begruendung:

- Pattern-Konsistenz mit Welle 5a (gleiches D-2-Argument:
  Doku ist Audit-Trail; Smoke-Tests sind Drift-Sensor).
- Existierende `TestClient`-/HTTPX-/WebSocket-Test-
  Infrastruktur erlaubt End-to-End-Smokes ohne neue
  Test-Surface.

### Welle-5b-D-2 — `GG-SAFE-007`-Marker-Surfaces

**Frage:** Welche Surfaces erhalten einen expliziten Sim/Prod-
Marker? Lastenheft Z. 1399 nennt **drei Pflicht-Surfaces**:
„UI, API-Dokumentation **und Adapterkonfiguration**" — alle
drei sind MUSS, keine darf weggelassen werden.

Optionen:

- **A — Minimal-Marker** (nur OpenAPI-`info.description` +
  README; UI + Adapterkonfiguration implizit). **Verletzt
  Lastenheft-Akzeptanz** (drei Pflicht-Surfaces).
- **B — Pflicht-Marker an allen drei Surfaces** (OpenAPI +
  README + UI-Dashboard-Banner **+ Adapterkonfiguration:
  Scenario-YAML-Sim-Marker (Top-Level-Kommentar-Block oder
  deklaratives Feld) + Protocol-Adapter-Config-Module-
  Docstring-Disclaimer**) + arch_check `AC-HEXAGON-PURE`-
  Whitelist als Architektur-Belegung.
- **C — Maximal-Marker** (B + jede UI-Page + OpenAPI-`x-grid-
  gym-simulation`-Custom-Extension + Adapter-Config-Disclaimer
  pro Protocol-Adapter-Modul).

**Welle-5b-Final: Option B (Pflicht-Marker an allen drei
Surfaces).** Begruendung:

- Lastenheft-Akzeptanz Z. 1399 fordert **drei Pflicht-
  Surfaces** explizit; Option A waere ein Vertrags-Verstoss.
- Adapterkonfiguration-Marker ist im Scope auf **Scenario-
  YAML** (Top-Level-Kommentar-Block in
  `deploy/scenarios/gg-demo.yaml`) **und Protocol-Adapter-
  Config-Module** (`adapters/driven/protocol_*/_config.py`-
  Docstring) begrenzt — kein per-Adapter-Module-Disclaimer
  ueber die Config-Module hinaus.
- Maximal-Marker (C) ist Over-Engineering ueber das Lastenheft
  hinaus; UI-Dashboard-Banner reicht als „UI"-Akzeptanz.
- Pattern-Konsistenz mit GG-SAFE-007 §22 Realisierungs-Zeile
  (arch_check + README) **plus** UI-Dashboard-Marker plus
  Adapter-Config-Marker — alle drei Lastenheft-Surfaces
  abgedeckt.

### Welle-5b-D-3 — Luecken-Adressier-Strategie

**Frage:** Wenn der Audit Luecken aufdeckt (z. B. UI ohne
sichtbaren Sim-Marker, `run_id` ohne UUID-Check), wird das
inline gefixt oder als `open/`-Trigger vertagt?

**Welle-5b-Final: Option B (Hybrid; analog Welle-5a-D-3).**
Begruendung:

- Minimale Luecken (UI-Banner-Template-Edit, Pydantic-
  ConfigDict-Schaerfung) sind in Welle-5b-C2-Substanz
  mit-zu-fixen.
- Substantielle Luecken (z. B. FastAPI-Path-Parameter-
  Refactor ueber alle Endpoints, ADR-Schaerfungs-Bedarf
  ueber das ADR-0037-Vertrags-Scope hinaus) brauchen eigene
  Welle-Substanz-Diskussion.
- C2-Review-Folge-Material falls Luecken erst beim Code-
  Schreiben sichtbar werden.

### Welle-5b-D-4 — `GG-SAFE-008`-Adapter-Audit-Umfang

**Frage:** „Adapter-Eingaben" in der Lastenheft-Akzeptanz —
welche Adapter-Sides werden audited?

Optionen:

- **A — Nur DriveSide** (HTTP-API REST/WS): externe Inputs
  von Clients.
- **B — DriveSide + DrivenSide** (HTTP-API + Protocol-Adapter-
  Reads): alle Schnittstellen zum Kern.
- **C — B + Test-Surface** (HTTP-API + Protocol-Adapter +
  Test-Fixtures): jede Eingabe-Surface inkl. interner.

**Welle-5b-Final: Option B (DriveSide + DrivenSide).**
Begruendung:

- Lastenheft-Akzeptanz nennt explizit „REST-, WebSocket-
  und alle implementierten Adapter-Eingaben" — Protocol-
  Adapter sind „alle implementierten Adapter".
- DrivenSide-Audit ist seit Welle 5a substanziell vorhanden
  (Quality-Emission bei Lese-Faellen). Welle-5b muss das
  zur Input-Validation-Akzeptanz-Aussage konsolidieren.
- Test-Surface (C) ist intern; nicht von der Lastenheft-
  Akzeptanz gefordert.

### Welle-5b-D-5 — Pydantic-Strict-Mode-Schaerfungs-Strategie

**Frage:** REST-Pydantic-Modelle haben Default-Pydantic-Mode
(type-Coercion + extra-ignore). Soll Strict-Mode + extra-
forbid Pflicht werden?

Optionen:

- **A — Beibehalten Default-Mode** (Backward-Compat fuer
  bestehende Tests; GG-SAFE-008 wird durch Pydantic-Schema-
  Validation alleine als erfuellt deklariert).
- **B — Strict-Mode + extra-forbid Pflicht** ueber ein NEU
  `_BaseRequest`-Mixin mit `model_config = ConfigDict(strict=
  True, extra="forbid")`; alle Request-Bodies erben.
- **C — Per-Endpoint-Entscheidung** (Request-Bodies mit
  externer Eingabe strict; Response-Bodies und interne
  Stubs ohne).

**Welle-5b-Final: Option C (Per-Endpoint, mit Request-Bodies-
Default-Strict).** Begruendung:

- Lastenheft GG-SAFE-008 verlangt Validation **bevor Eingaben
  in den Kern gelangen** — das betrifft Request-Bodies, nicht
  Response-Bodies oder interne Stubs.
- Strict-Mode + extra-forbid an Response-Bodies kann
  bestehende UI-Templates brechen (Response-Field-Drift bei
  Welle-Erweiterungen).
- Welle-5b-C2-Substanz: `_BaseRequest`-Mixin in `_schemas.
  py` mit Strict-Mode + extra-forbid; Request-Modelle erben
  (`ControlRequest`, `FaultInjectionRequest`). **Konsolidierung
  `RunCreateRequest`:** das Modell lebt heute in `app.py`
  (Welle-1-Era-Drift); C2 verschiebt es nach `_schemas.py`
  und laesst es ebenfalls vom `_BaseRequest`-Mixin erben, damit
  der Strict-Mode-Vertrag fuer **alle drei** Request-Bodies
  (`POST /runs`, `POST /control`, `POST /faults`) uniform gilt.
  `app.py` importiert anschliessend `RunCreateRequest` aus
  `_schemas`. Response-Modelle (`RunDetailResponse` etc.)
  bleiben unveraendert.
- Wenn Tests durch die Schaerfung brechen: Test-Anpassung im
  selben C2 (Welle-5b-D-3 Inline-Fix-Pflicht; Pattern analog
  M5-Welle-2-Tests-Refactor).

### Welle-5b-D-6 — ADR-Schaerfungs-Bedarf

**Frage:** Erfordert Welle-5b eine NEU ADR oder Schaerfung
einer bestehenden? **ADR-0011-Constraint:** ADR-0037 ist
`Accepted` (gezogen 2026-06-04 mit M5-Welle-7-C1); Schaerfung
darf den `Accepted`-ADR **nicht** mutieren. Pro ADR 0011 §2
muss eine Schaerfungs-ADR `B` als **separate Datei** mit
eigenem Header geschrieben werden, ADR-0037 bleibt unveraendert
`Accepted`.

Optionen:

- **A — Keine ADR** (Audit + Tests + Doku; analog Welle 5a).
- **B — NEU eigenstaendige ADR fuer Input-Validation-Pattern**
  (Pydantic-Strict-Mode + extra-forbid als Adapter-Vertrag;
  kein direkter ADR-0037-Bezug).
- **C — NEU Schaerfungs-ADR (ADR 0045) zu ADR 0037** per
  ADR-0011-Pattern: eigene ADR-Datei `docs/plan/adr/0045-
  http-api-request-strict-validation.md` mit `Bezug:`-Zeile
  auf ADR 0037, plus Eintrag in der „Schaerfungen / Folge-
  ADRs"-Spalte von ADR 0037 in `docs/plan/adr/README.md`.
  **ADR 0037 selbst wird NICHT editiert** (bleibt
  `Accepted`).

**Welle-5b-Final: Option C (NEU Schaerfungs-ADR 0045 per
ADR-0011-Pattern; ADR 0037 unveraendert).** Begruendung:

- ADR-0011 §2 verbietet die Mutation einer `Accepted`-ADR;
  Pflicht ist eine separate Schaerfungs-ADR `B`. ADR 0037
  bleibt `Accepted` und in Kraft.
- Eigener Decision-Punkt ist die Pydantic-Strict-Mode-
  Pflicht fuer Request-Bodies (Bezug zu ADR-0037-Decision-
  Punkt API-2 + §2.x-Schema-Vertrag) — additive Schaerfung,
  kein Zurueckdrehen.
- ADR-Index-Pflege (ADR 0028 Link-Maintenance): NEU Eintrag
  in `docs/plan/adr/README.md` ADR-0037-Zeile-Schaerfungs-
  Spalte; NEU Eintrag fuer ADR 0045 selbst.
- §1.1-Audit-Befund zeigt: Default-Pydantic-Mode an allen
  Request-Bodies ist die aktuelle Realitaet — Strict-Mode-
  Schaerfung ist mithin **noetig**, nicht „ggf."; D-5 hat
  diese Lücke verbindlich gemacht. Option A (keine ADR)
  bleibt nur als **Eskalations-Pfad** offen (siehe §4 C1
  Eskalations-Pfad), nicht als Default.
- **Welle-5b-Final: Option C als verbindlicher Default**;
  C1 ist Pflicht-Commit vor C2.

**Anti-Pattern (explizit verboten):** ADR 0037 direkt mit
einem NEU API-4-Decision-Punkt anreichern oder §2.x-Body
editieren — verletzt ADR-0011 §2.

---

## 4. Liefer-Reihenfolge (3 Commits)

### Pre-C0 — bereits erledigt (M6-Welle-5a-Closure-Folge)

- `f35ab67` (Pre-C0a: `git mv M6-welle-5a.md → done/`).
- `2e3bf72` (Pre-C0b: Cross-Doc-Refs-Sync + Hash-Slot-Fills).

### C0 — `docs(plan)`: M6-welle-5b Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU `M6-welle-5b.md` (dieses Dokument).
- `in-progress/README.md` Bestand-Tabelle um Welle-5b-Zeile +
  Aktive-Welle-Block auf M6-Welle-5b.
- `M6-perf-security-cicd.md §3.1` Welle-5b-Zeile
  `Pending → In Progress 2026-06-07`; Status-Block oben
  aktive Welle auf 5b.

### C1 — `docs(adr)`: NEU ADR 0045 (Schaerfung zu ADR 0037)

**Pflicht-Commit (Welle-5b-D-6 Option C).** Muss vor C2
landen, damit der Strict-Mode-Vertrag einen ADR-Anker hat.

NEU eigenstaendige Schaerfungs-ADR **`docs/plan/adr/0045-
http-api-request-strict-validation.md`** per ADR-0011-Pattern:

- Eigener ADR-Header (`Status: Proposed` in C1; spaeter
  `→ Provisional` in C3 mit Welle-5b-C2-Beleg, Pattern analog
  ADR 0038/0039/0040; `Bezug:` referenziert ADR 0037).
- Decision: Pydantic-Strict-Mode + `extra="forbid"` Pflicht
  fuer Request-Bodies an REST-Endpunkten; Per-Endpoint-
  Schema-Vertrag.
- **ADR 0037 wird NICHT editiert** (bleibt unveraendert
  `Accepted`).
- ADR-Index-Update in `docs/plan/adr/README.md`: (a) NEU
  Zeile fuer ADR 0045; (b) NEU Eintrag in ADR-0037-Zeile-
  Schaerfungs-Spalte mit Verweis auf ADR 0045.

**Eskalations-Pfad:** Falls Welle-5b-C2-Audit gegen die
Strict-Mode-Vorbelegung wider Erwarten ergibt, dass kein
Schaerfungs-Bedarf besteht (z. B. weil Pydantic-Strict-Mode
bereits per-Endpoint produktiv waere — aktuell nicht der
Fall, vgl. §1.1), wird C1 nachtraeglich zu einer C0-Folge-
Sub-Decision umgewandelt und ADR 0045 nicht gezogen. Dieser
Pfad ist explizit als Eskalation gekennzeichnet, nicht als
Default.

### C2 — `feat(security)` + `docs(user)`: GG-SAFE-007/008 Audit + Smokes

Code-Merge mit:

- NEU `tests/integration/test_m6_welle_5b_safe_007_008_smoke.
  py` mit 11 Smoke-Tests (§1.2 + Welle-5b-D-1):
  - SAFE-007 (×5): OpenAPI-description + README-Disclaimer +
    arch_check-Whitelist + UI-Dashboard-Marker +
    **Adapter-Config-Marker (Scenario-YAML)**.
  - SAFE-008 (×6): REST-invalid-payload + REST-extra-field-
    rejected + REST-type-coercion-rejected + WS-invalid-run_id
    + WS-no-client-payload + Fault-target-validation.
- NEU `docs/user/safe-007-008-sim-prod-input-validation.md`
  Audit-Tabelle mit:
  - Pro GG-SAFE-00X-ID: Lastenheft-Akzeptanz, Substanz-Pfad
    (Code-Datei + Zeile), Test-Pfad, Status (✓ produktiv /
    Lücke).
- Pydantic-Strict-Mode-Schaerfung (Welle-5b-D-5; falls Audit
  Lücke aufdeckt): NEU `_BaseRequest`-Mixin oder per-Model-
  `model_config`.
- Inline-Luecken-Fixes (Welle-5b-D-3) falls Audit Luecken
  aufdeckt (z. B. UI-Dashboard-Sim-Marker-Template-Edit).
- **Verifikation (lokal vor C2-Commit):**
  - `make gates` cache-frei gruen (10/10 A-1-Gates; Test-
    Counts: +11 Integration-Smokes; falls Strict-Mode-Schaerfung
    bestehende Tests beruehrt, Test-Anpassung im selben C2).
  - `make ci` cache-frei gruen.
  - `make fullbuild` cache-frei gruen.
  - `make docs-check` cache-frei gruen.

### C3 — `docs(plan)`: Status/DoD-Sync + ADR-0045-Flip

**Welle-5b-Closure-Sync.**

- ADR 0045 `Proposed → Provisional` mit C2-Code-Beleg
  (Pattern analog ADR 0038/0039/0040 M5-Welle-3/4a/4b-C3-
  Flips).
- `M6-welle-5b.md` Status `In Progress → Done 2026-06-07`
  mit Liefer-Hash-Stack.
- `M6-perf-security-cicd.md §3.1` Welle-5b-Zeile `In
  Progress → Done` mit Closure-Hash + Aktive-Welle-Block
  auf Welle 5c.
- **Top-Level-Doku-Sync:**
  - `README.md` + `README.de.md`: NEU Input-Validation-Audit-
    Hinweis falls relevant (Doku-Pointer auf `docs/user/
    safe-007-008-*`).
  - `roadmap.md §3 M6` aktive-Welle-Block auf M6-Welle-5c +
    Welle-5b-Abschluss-Notiz.

### Welle-5b-Closure-Folge (nach C3, Pattern Welle-5a)

- C4a `git mv M6-welle-5b.md → done/` (rename-only).
- C4b Cross-Doc-Refs-Sync nach Move + Hash-Slot-Fills.

C4a/C4b dienen gleichzeitig als M6-Welle-5c-Pre-C0a/Pre-C0b.

---

## 5. Critical Files

**Welle-5b-NEU (geschrieben in C0/C2):**

- `docs/plan/planning/in-progress/M6-welle-5b.md` (C0,
  dieser Commit).
- `tests/integration/test_m6_welle_5b_safe_007_008_smoke.py`
  (C2).
- `docs/user/safe-007-008-sim-prod-input-validation.md` (C2).

**Welle-5b-MODIFY (in C0/C2/C3):**

- `docs/plan/planning/in-progress/README.md` (C0 + C3).
- `docs/plan/planning/in-progress/M6-perf-security-cicd.md`
  (C0 + C3) — §3.1 Welle-5b-Zeile flippen.
- Ggf. `src/grid_gym/adapters/driving/http_api/_schemas.py`
  (C2; Pydantic-Strict-Mode-Schaerfung + NEU `_BaseRequest`-
  Mixin + Umzug `RunCreateRequest` + `RunCreateResponse` aus
  `app.py`; Welle-5b-D-5).
- Ggf. `src/grid_gym/adapters/driving/http_api/app.py` (C2;
  `RunCreateRequest`/`RunCreateResponse` aus `_schemas.py`
  importieren statt lokal definieren; Konsolidierung Welle-
  1-Era-Drift; Welle-5b-D-5).
- Ggf. `src/grid_gym/adapters/driving/ui/templates/_dashboard_
  content.html` (C2; Sim-Marker-Banner falls Lücke; Welle-
  5b-D-3).
- Ggf. NEU `docs/plan/adr/0045-http-api-request-strict-
  validation.md` (C1 falls Welle-5b-D-6 Option C aktiv;
  eigenstaendige Schaerfungs-ADR mit Bezug auf ADR 0037).
- Ggf. `docs/plan/adr/README.md` (C1; ADR-Index-Update:
  NEU ADR-0045-Zeile + Schaerfungs-Spalten-Eintrag in
  ADR-0037-Zeile). **ADR 0037 selbst wird NICHT editiert.**
- `docs/plan/planning/in-progress/roadmap.md` (C3) — §3 M6
  aktive-Welle-Block + Welle-5b-Abschluss-Notiz.
- `README.md` + `README.de.md` (C3) — NEU Input-Validation-
  Audit-Hinweis falls relevant.

**Welle-5b-MODIFY (Adapterkonfigurations-Surface, Welle-5b-D-2
Option B + D-3 Inline-Fix):**

- `deploy/scenarios/gg-demo.yaml` (C2; NEU Top-Level-Kommentar-
  Block mit Sim/Prod-Marker) — Lastenheft-Pflicht-Surface
  „Adapterkonfiguration".
- `src/grid_gym/adapters/driven/protocol_*/_config.py` (C2;
  **nur Modul-Docstring-Disclaimer**, falls Audit Lücke
  zeigt) — Adapter-Config-Module-Marker. **Scope ist eng
  auf Docstring-Add begrenzt**, kein Verhaltens-Edit.

**Welle-5b-UNBERUEHRT (kein Edit):**

- `Quality`-Enum (Welle-5a-Erbschaft; M5-Welle-6b-Review F15
  fixiert).
- Protocol-Adapter-Substanz unter `adapters/driven/protocol_*/`
  **ausserhalb `_config.py`** (`_port.py`/`_codec.py`/
  `_errors.py` etc.) — Welle-5a hat Adapter-Side audited;
  Welle-5b prueft nur die Driving-Side-REST/WS-Eingaben +
  DrivenSide-Audit-Tabelle-Verweis plus den engen Adapter-
  Config-Docstring-Marker oben.
- `pyproject.toml`/`uv.lock`/`Dockerfile`/`Makefile` (kein
  neuer Dep-Bedarf).
- Alle GitHub-Actions-Workflows.

---

## 6. Verifikationspfad

**Welle-5b-Gate:**

- `make docs-check` cache-frei gruen.
- `make gates` cache-frei gruen (10/10 A-1-Gates).
- `make ci` cache-frei gruen.
- `make fullbuild` cache-frei gruen.

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur Doc-Substanz.
- C2 prueft 11 NEU Smoke-Tests + NEU Audit-Doku + ggf.
  Pydantic-Strict-Mode-Schaerfung + ggf. UI-Sim-Marker-Banner;
  alle bestehenden Gates gruen.
- C3 prueft Status-Flip + Top-Level-Doku-Sync.

**Abnahme-Verifikation:**

- `GG-SAFE-007/008` MUSS-Akzeptanz audited:
  - SAFE-007 — **drei Pflicht-Surfaces aus Lastenheft Z. 1399**:
    (a) **UI** (Dashboard-Sim-Marker), (b) **API-Doku**
    (OpenAPI `info.description` + README + README.de),
    (c) **Adapterkonfiguration** (Scenario-YAML-Top-Level-
    Kommentar-Block + Protocol-Adapter-`_config.py`-Docstring-
    Disclaimer). Plus arch_check `AC-HEXAGON-PURE` als
    Architektur-Belegung (Welle-5b-D-2 Option B).
  - SAFE-008 — REST-Pydantic-Validation + WS-`run_id`-Check
    + Driven-Adapter-Audit-Tabelle (Welle-5b-D-4 Option B).
  - Erwartung: 007 ✓ **produktiv** mit ggf. UI-Banner-Inline-
    Fix + ggf. Scenario-YAML-Kommentar-Block + ggf.
    `_config.py`-Docstring-Adds; 008 ✓ **produktiv** mit
    Pydantic-Strict-Mode-Schaerfung.

---

## 7. Risiken

**R1 — Audit deckt substantielle Luecke auf (z. B. systematisches
WS-Input-Validation-Gap).** Welle-5b-Scope ist Audit + Tests +
Doku; falls eine substantielle Luecke aufgedeckt wird, sprengt
das den Welle-5b-Scope.
**Mitigation:** Welle-5b-D-3 Option B (Hybrid) erlaubt
NEU `open/`-Trigger als Vertagungs-Pfad. C2-Review-Folge-
Material falls Luecken erst beim Code-Schreiben sichtbar werden.

**R2 — Pydantic-Strict-Mode-Schaerfung bricht bestehende
Tests.** Type-Coercion-Beruhigung in bestehenden Test-Fixtures
(z. B. `seed="42"`-String-Inputs in Welle-1-Smokes) wird unter
Strict-Mode rejected.
**Mitigation:** Welle-5b-C2 macht `make gates` cache-frei gruen
vor Push; Test-Anpassung im selben C2 (Pattern analog M5-Welle-
2-Tests-Refactor an Welle-1-Vertrag).

**R3 — UI-Sim-Marker-Form-Praezision.** Lastenheft-Akzeptanz
„UI kennzeichnet Simulationsadapter als nicht fuer produktive
Anlagensteuerung freigegeben" laesst Form offen (Banner /
Footer / Title). Risiko: Reviewer-Erwartung != Implementierung.
**Mitigation:** Welle-5b-D-2 Option B fixiert ein UI-Dashboard-
Banner als Welle-5b-Default; Form-Schaerfung in C2-Review-Folge
moeglich.

**R4 — `GG-SAFE-008`-Akzeptanz „Zielressourcen-Validierung"
ist mehrdeutig.** Lastenheft fordert „validiert gegen Schema,
Wertebereiche **und Zielressourcen**" — Zielressourcen-
Validierung (z. B. `fault_type` gegen Device-Type-Compatibility,
`run_id` gegen Existenz) ueberschneidet sich teilweise mit
Endpunkt-spezifischer Logik.
**Mitigation:** Welle-5b-D-4 Option B Audit deckt das per-
Endpoint ab; substantielle Luecken (z. B. fehlende Cross-
Field-Validation) gehen als `open/`-Trigger ueber.

**R5 — NEU Schaerfungs-ADR-0045-Form (Welle-5b-D-6 Option C).**
ADR 0011 §2 verlangt: Schaerfungs-ADR `B` als **separate**
Datei, ADR `A` (= ADR 0037) bleibt unveraendert `Accepted`;
`B` referenziert `A` in der `Bezug:`-Zeile; ADR-Index erhaelt
neuen Eintrag in der „Schaerfungen / Folge-ADRs"-Spalte der
`A`-Zeile. Risiko: Versehentliche Editierung von ADR 0037
oder fehlender Index-Eintrag.
**Mitigation:** Welle-5b-C1 (vorbedingt) folgt streng Pattern
ADR 0011 §2 1..5; Critical-Files-Liste (§5) verbietet
ADR-0037-Edit explizit; ADR-Index-Update (`docs/plan/adr/
README.md`) ist DoD-Checkbox; C1-Review-Folge falls Pattern-
Drift auftritt.

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack**: nach C3
  schliesst die Welle ihre eigene Commit-Sequenz mit
  `git mv M6-welle-5b.md → ../done/M6-welle-5b.md` (C4a) +
  Cross-Doc-Refs-Sync (C4b). Pattern analog M6-Welle-5a-
  C4a `f35ab67`/C4b `2e3bf72`.
- C4a/C4b dienen gleichzeitig als M6-Welle-5c-Pre-C0a/Pre-C0b.
- Ggf. NEU eigenstaendige Schaerfungs-ADR 0045 mit Bezug
  auf ADR 0037 (Welle-5b-D-6 Option C; vorbedingt; ADR 0037
  bleibt unveraendert `Accepted`).

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **C0 — NEU `M6-welle-5b.md`** mit §1..§9-Struktur
  (dieser Commit).
- [x] **C0 — `in-progress/README.md`** Bestand-Tabelle
  um `M6-welle-5b.md`-Eintrag + Aktive-Welle-Block auf
  M6-Welle-5b.
- [x] **C0 — `M6-perf-security-cicd.md §3.1`** Welle-5b-Zeile
  `Pending → In Progress 2026-06-07`.
- [x] **C1 Pflicht (Welle-5b-D-6 Option C)** — NEU
  eigenstaendige Schaerfungs-ADR `docs/plan/adr/0045-http-
  api-request-strict-validation.md` mit Status `Proposed`
  per ADR-0011-Pattern + ADR-Index-Update in `docs/plan/adr/
  README.md` (C1 `cee5aab`).
- [x] **C2 — NEU `tests/integration/test_m6_welle_5b_safe_007_
  008_smoke.py`** mit 11 Smoke-Tests (5 SAFE-007 + 6 SAFE-008;
  alle gruen).
- [x] **C2 — NEU `docs/user/safe-007-008-sim-prod-input-
  validation.md`** Audit-Tabelle (pro Surface Substanz-Pfad +
  Test-Pfad + Status; alle ✓ produktiv).
- [x] **C2 — Pydantic-Strict-Mode-Schaerfung** (Welle-5b-D-5)
  produktiv: NEU `_BaseRequest`-Mixin in `_schemas.py` +
  `RunCreateRequest`-Umzug aus `app.py` + 3 Request-Modelle
  erben.
- [x] **C2 — UI-Sim-Marker-Inline-Fix** (Welle-5b-D-3)
  produktiv: NEU `.sim-banner` in `base.html` + CSS-Klasse +
  Disclaimer in OpenAPI + READMEs + Scenario-YAML + 5
  Protocol-Adapter-`_config.py`-Docstrings.
- [x] **C2 — `make gates`** cache-frei gruen (10/10 A-1-
  Gates).
- [x] **C2 — `make ci`** cache-frei gruen.
- [x] **C2 — `make fullbuild`** cache-frei gruen.
- [x] **C3 — ADR 0045** `Proposed → Provisional` mit C2-Code-
  Beleg (Pattern analog ADR 0038/0039/0040).
- [x] **C3 — `M6-welle-5b.md`** Status `In Progress → Done
  2026-06-07` mit Liefer-Hash-Stack.
- [x] **C3 — `M6-perf-security-cicd.md §3.1`** Welle-5b-
  Zeile `In Progress → Done` mit Closure-Hash + Aktive-
  Welle-Block auf Welle 5c.
- [x] **C3 — `README.md` + `README.de.md`** Sim/Prod-
  Disclaimer-Substanz bereits in C2 verankert.
- [x] **C3 — `roadmap.md §3 M6`** aktive-Welle-Block auf
  M6-Welle-5c + Welle-5b-Abschluss-Notiz mit Stack-Range.
- [x] **C3 — `in-progress/README.md`** Bestand-Tabelle
  Welle-5b-Zeile auf `Done` + Aktive-Welle-Block auf
  M6-Welle-5c.
- [x] **C3 — `make docs-check`** cache-frei gruen.

**Anti-Scope-Verifikation (Welle 5b NICHT):**

- [x] Kein `GG-SAFE-005/006` SOLLTE-Items (Welle-5c-Scope).
- [x] Keine IP-/Netz-Beschraenkung (Welle-5c-Scope).
- [x] Keine Adapter-Quality-Emission-Aenderungen (Welle-5a
  hat das audited; Trigger 034/035 sind die Folge-Pfade).
- [x] Keine neue Quality-Enum-Variante (M5-Welle-6b-Review
  F15 fixiert; Welle-5a-Erbschaft).
- [x] Keine substantielle FastAPI-Routing-Refactor (Welle-
  5b-Anti-Scope; Vertagung als `open/`-Trigger).
- [x] Kein NEU Code im Core (Adapter-Side wenn ueberhaupt;
  Welle-5b-D-5 Option C).

---

## References

- [`../done/M6-welle-5a.md`](../done/M6-welle-5a.md) —
  Welle-5a Quality-Pipeline-Audit (abgeschlossen); Welle
  5b ist die naechste aktive Welle nach Welle-5a-Closure.
- [`../in-progress/M6-perf-security-cicd.md §3.2 Welle 5`](../in-progress/M6-perf-security-cicd.md)
  — M6-Slice-Plan Welle-5b-Vorbelegung.
- [`../../../../spec/lastenheft.md §20 GG-SAFE-007/008`](../../../../spec/lastenheft.md)
  — Lastenheft-Akzeptanz fuer Sim/Prod-Trennung + Input-
  Validation.
- [`../../adr/0037-http-api-surface-pattern.md`](../../adr/0037-http-api-surface-pattern.md)
  — HTTP-API-Surface-Pattern (M5-Welle-1); Welle-5b-D-6
  Option C Schaerfungs-Anker fuer Pydantic-Strict-Mode.
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — ADR-Schaerfung-ohne-Supersedes-Pattern; Welle-5b-D-6
  Option C.
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  — DeviceProtocolPort-Foundation (M4); Welle-5b-D-4 Option
  B DrivenSide-Audit-Tabelle-Anker.
- [`../open/034-safe-004-max-age-stale-quality.md`](../open/034-safe-004-max-age-stale-quality.md)
  + [`../open/035-safe-003-comm-failure-missing-quality.md`](../open/035-safe-003-comm-failure-missing-quality.md)
  — Welle-5a-Audit-Lücken-Trigger (Folge-Pfad; nicht Welle-
  5b-Scope).
