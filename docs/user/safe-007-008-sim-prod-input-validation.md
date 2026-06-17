# Sim/Prod-Marker + REST-Input-Validation (`GG-SAFE-007/008`)

**Quelle:** M6-Welle-5b (Sim/Prod-Marker + Input-Validation;
[`../plan/planning/done/M6-welle-5b.md`](../plan/planning/done-archive/M6-welle-5b.md)).
**Stand:** 2026-06-07.

Dieses Dokument auditiert die produktive Substanz fuer die beiden
MUSS-Akzeptanzen [`GG-SAFE-007`](../../spec/lastenheft.md#gg-safe-007) (Sim/Prod-Trennung) und
[`GG-SAFE-008`](../../spec/lastenheft.md#gg-safe-008) (Input-Validation) aus dem Lastenheft (§20). Pro
Surface werden Substanz-Pfade, Test-Pfade und Lieferstatus
dokumentiert.

---

## Übersicht

### `GG-SAFE-007` — Sim/Prod-Marker (drei Pflicht-Surfaces)

Lastenheft Z. 1399 verlangt **drei** sichtbare Marker-Surfaces:
„UI, API-Dokumentation und Adapterkonfiguration kennzeichnen
Simulationsadapter als nicht fuer produktive Anlagensteuerung
freigegeben."

| Surface | Substanz-Pfad | Test-Pfad | Status |
| ------- | ------------- | --------- | ------ |
| **UI** | `adapters/driving/ui/templates/base.html` rendert `<div class="sim-banner">` ueber `<header>` mit englischem + deutschem Disclaimer; per `base.html`-Vererbung auf allen UI-Pages sichtbar. CSS in `adapters/driving/ui/static/style.css` `.sim-banner`. | `tests/integration/test_m6_welle_5b_safe_007_008_smoke.py` (`test_safe_007_ui_base_renders_simulation_banner`) (Demo-Page + Dashboard-Page) | ✓ **Produktiv** |
| **API-Doku (OpenAPI)** | `adapters/driving/http_api/app.py::_APP_DESCRIPTION` nennt explizit `Simulation only — not approved for production grid control` plus [`GG-SAFE-007`](../../spec/lastenheft.md#gg-safe-007)/[`GG-NONGOAL-001`](../../spec/lastenheft.md#gg-nongoal-001). Im OpenAPI-Schema unter `info.description` sichtbar. | `::test_safe_007_openapi_description_marks_simulation` | ✓ **Produktiv** |
| **API-Doku (README)** | `README.md` + `README.de.md` Blockquote unmittelbar nach dem Intro-Absatz: „Simulation only — not approved for production grid control." / „Nur Simulation — nicht fuer produktive Anlagensteuerung freigegeben." Inkl. Protocol-Adapter-Liste. | `::test_safe_007_readme_disclaimer_present` | ✓ **Produktiv** |
| **Adapterkonfiguration (Scenario)** | `deploy/scenarios/gg-demo.yaml` Top-Level-Kommentar-Block (`# SIMULATION ONLY — NOT APPROVED FOR PRODUCTION GRID CONTROL.`) mit Verweis auf [`GG-SAFE-007`](../../spec/lastenheft.md#gg-safe-007)/[`GG-NONGOAL-001`](../../spec/lastenheft.md#gg-nongoal-001). | `::test_safe_007_adapter_config_marks_simulation` | ✓ **Produktiv** |
| **Adapterkonfiguration (Protocol-Modul)** | Modul-Docstring in `adapters/driven/protocol_{dnp3,iec61850,modbus,mqtt,opcua}/_config.py` (5 Module) trägt 3-Zeilen-Disclaimer mit [`GG-SAFE-007`](../../spec/lastenheft.md#gg-safe-007)-Ref. | `::test_safe_007_adapter_config_marks_simulation` (deckt alle 5 Module ab) | ✓ **Produktiv** |
| **Architektur-Belegung** | `tools/arch_check.py` ([`AC-HEXAGON-PURE`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert))-Contract + `pyproject.toml` Allowlist verhindert Direct-Wire-Bypass: `hexagon/**` darf nur Whitelist-Pakete importieren, kein Driving-/Driven-Adapter kann den Kern umgehen. | `::test_safe_007_arch_check_hexagon_pure_whitelist` (Quell-Inspektion) + `make arch-check` (20/20 Contracts KEPT) | ✓ **Produktiv** |

### `GG-SAFE-008` — Input-Validation (REST + WebSocket + Adapter)

Lastenheft Z. 1404-1408 verlangt: „REST-, WebSocket- und alle
implementierten Adapter-Eingaben werden gegen Schema, Wertebereiche
und Zielressourcen validiert, bevor sie in den Simulationskern
gelangen."

| Surface | Substanz-Pfad | Test-Pfad | Status |
| ------- | ------------- | --------- | ------ |
| **REST Schema (Strict-Mode)** | `_BaseRequest`-Mixin in `adapters/driving/http_api/_schemas.py` setzt `ConfigDict(strict=True, extra="forbid")`. `ControlRequest`, `FaultInjectionRequest` und `RunCreateRequest` erben den Mixin ([`ADR 0045`](../plan/adr/0045-http-api-request-strict-validation.md) §2.1 + §2.4). | `::test_safe_008_rest_invalid_payload_rejected_422` (Length-Constraint) + `::test_safe_008_rest_extra_field_rejected` (extra-forbid) + `::test_safe_008_rest_type_coercion_rejected` (Strict-Mode) | ✓ **Produktiv** |
| **REST Wertebereiche** | Pydantic-`Field`-Constraints pro Modell (`scenario_hash` 64-Char-Length; `seed` `ge=0, le=2**32-1`; `tick_ms` `gt=0`; `action` `Literal["pause","resume","stop"]`). | gleicher Smoke wie oben (422 fuer ausserhalb des Wertebereichs) + bestehende Endpoint-Tests unter `tests/unit/adapters/driving/http_api/` decken die Field-Constraints indirekt mit. | ✓ **Produktiv** |
| **REST Zielressourcen** | `adapters/driving/http_api/_runs_action_router.py::post_run_faults` Cross-Field-Validation (M5-Welle-6a Decision 20): drei Schichten (target-existiert / fault_type-bekannt / type↔target-passt), alle → 422 mit `ErrorResponse.code`. `_healthcheck_router._require_run_or_404`-Helper deckt `run_id`-Existenz an REST-/UI-Pfaden ab. | `::test_safe_008_fault_injection_unknown_target_rejected` + bestehende `tests/integration/test_m5_welle_6a_fault_smoke.py` | ✓ **Produktiv** |
| **WebSocket Subscribe-only** | `adapters/driving/http_api/_runs_action_router.py`: beide WS-Handler (`ws_run_telemetry`, `ws_run_alarms_stream`) rufen `await websocket.accept()` und iterieren ueber `TelemetryStreamPort.subscribe` bzw. `AlarmStreamPort.subscribe`. Es gibt **keinen** `websocket.receive_*`-Call — keine Client-Payload-Konsumption am Kern ([`ADR 0045`](../plan/adr/0045-http-api-request-strict-validation.md) §2.3). | `::test_safe_008_websocket_no_client_payload_consumed` (Quell-Datei-Inspektion) | ✓ **Produktiv** |
| **WebSocket `run_id`-Validation** | Repository-Lookup im WS-Handler vor `subscribe`; bei unbekanntem `run_id` → Policy-Close 1008 mit Reason. UUID-Format-Validation an Path-Parameters ist explizit out-of-scope ([`ADR 0045`](../plan/adr/0045-http-api-request-strict-validation.md) §7) — der Repository-Lookup faengt invalid-Strings ab. | `::test_safe_008_websocket_unknown_run_id_rejected` (Close-Code 1008-Belegung) | ✓ **Produktiv** |
| **Driven-Adapter-Input** | Welle 5a ([`GG-SAFE-001`](../../spec/lastenheft.md#gg-safe-001)..004-Audit; siehe [`safe-001-004-quality-pipeline.md`](safe-001-004-quality-pipeline.md)) hat die Adapter-Side-Quality-Emission auditiert: Schema-Validierung im Scenario-Loader (`hexagon/core/scenario/loader.py`), NaN-Reject im Serialisierungs-Pfad (`canonical_json`), Quality-Emission bei Lese-Fehlern pro Adapter (`protocol_*`-`_port.py`-Familie). | Welle-5a-Smoke-Suite `tests/integration/test_m6_welle_5a_safe_001_004_smoke.py` (4 Pflicht + 2 Schwester + 2 Trigger-Skips) | ✓ **Produktiv** (siehe Welle 5a) |

**Legende**:
- ✓ Produktiv: Akzeptanz vollstaendig erfuellt + Smoke-Test
  pinnt das in CI.
- ⚠ Partial Lücke: Sub-Substanz existiert, voller Akzeptanz-
  Umfang nicht abgedeckt; Trigger verankert den Folge-Pfad.
- ✗ Lücke: keine produktive Substanz; Trigger verankert den
  Folge-Pfad.

---

## Detail pro ID

### `GG-SAFE-007` — Sim/Prod-Trennung klar gekennzeichnet

**Lastenheft-Akzeptanz (Z. 1395-1400)**: „UI, API-Dokumentation
und Adapterkonfiguration kennzeichnen Simulationsadapter als
nicht fuer produktive Anlagensteuerung freigegeben."

`grid-gym` kennzeichnet sich als reine Simulations-Umgebung an
allen drei Lastenheft-Pflicht-Surfaces:

- **UI** — Jede UI-Page (Dashboard, Demo, Control, Devices,
  System, Alarms, Faults, Health) rendert ueber das
  `base.html`-Template einen sichtbaren gelben Banner mit dem
  Doppel-Disclaimer auf Englisch + Deutsch.
- **API-Doku** — Das OpenAPI-Schema (`GET /openapi.json`)
  liefert `info.description` mit explizitem Sim/Prod-Marker.
  Beide READMEs tragen einen Blockquote-Disclaimer direkt im
  Intro-Bereich.
- **Adapterkonfiguration** — Das kanonische Demo-Scenario
  (`deploy/scenarios/gg-demo.yaml`) traegt einen
  augenfaelligen Top-Level-Kommentar-Block. Die fuenf Protocol-
  Adapter-Profile (`adapters/driven/protocol_{dnp3,iec61850,
  modbus,mqtt,opcua}/_config.py`) tragen einen Disclaimer im
  Modul-Docstring.

Plus die Architektur-Belegung: `tools/arch_check.py` mit dem
[`AC-HEXAGON-PURE`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Contract verhindert strukturell, dass ein
Adapter den Hexagon-Kern direkt mit einem produktiven Anlagen-
Backend verschaltet — der Kern darf nur Whitelist-Pakete
importieren, und ein hypothetischer Produktiv-Anlagen-Adapter
liesse sich nicht unbemerkt anbinden.

### `GG-SAFE-008` — Eingabe-Validation an externen Schnittstellen

**Lastenheft-Akzeptanz (Z. 1404-1408)**: „REST-, WebSocket- und
alle implementierten Adapter-Eingaben werden gegen Schema,
Wertebereiche und Zielressourcen validiert, bevor sie in den
Simulationskern gelangen."

Die Validation laeuft auf drei Layern:

1. **Schema-Layer** — Pydantic-`_BaseRequest`-Mixin ([`ADR 0045`](../plan/adr/0045-http-api-request-strict-validation.md)
   §2.1) schaltet fuer alle REST-Request-Bodies
   `strict=True` + `extra="forbid"` ein:
   - Strict-Mode lehnt Type-Coercion ab. Ein Body `{"seed":
     "42"}` (String statt Int) wird mit `int_type`-Fehler
     abgelehnt statt silent zu `42` umgewandelt zu werden.
   - `extra="forbid"` macht unbekannte Felder zu 422-Fehlern
     mit `extra_forbidden`-Pointer. Tippfehler im Client
     (`"actoin"` statt `"action"`) werden sichtbar.
2. **Wertebereich-Layer** — Pydantic-`Field`-Constraints pro
   Modell setzen min/max-Length, ge/le-Schwellen,
   `Literal`-Allowlists; ausserhalb-Wertebereich → 422.
3. **Zielressourcen-Layer** — Endpoint-Logik validiert vor
   Kern-Zugriff: `_require_run_or_404`-Helper deckt
   Run-Existenz an REST-/UI-Pfaden ab; `post_run_faults`
   prueft Target-Existenz, Fault-Typ-Whitelist und
   Typ-Target-Kompatibilitaet.

WebSocket-Endpunkte (`WS /runs/{id}/telemetry`,
`WS /runs/{id}/alarms-stream`) sind Subscribe-only: die
Server-Side liest keine Client-Payloads in den Kern ([`ADR 0045`](../plan/adr/0045-http-api-request-strict-validation.md)
§2.3); der Repository-Lookup vor `subscribe` faengt invalid-
`run_id`-Strings via Policy-Close 1008 ab.

Driven-Side-Adapter-Input (Protocol-Reads von externen
Geraeten) ist die Substanz der Welle-5a-Quality-Pipeline-Audit:
Schema-Validierung im Scenario-Loader, NaN-Reject im
canonical_json-Pfad, Quality-Emission bei Lese-Fehlern pro
Adapter — Status siehe [`safe-001-004-quality-pipeline.md`](safe-001-004-quality-pipeline.md).

---

## Verifikation

`tests/integration/test_m6_welle_5b_safe_007_008_smoke.py`
deckt mit 11 Integration-Smokes (5 SAFE-007 + 6 SAFE-008) den
Vertrag in CI ab. Plus die `make gates`-Aggregat-Substanz
(Lint, Format, Typecheck, Arch-Check, Tests, Coverage,
Dep-Audit, NoQA, SPDX, plus Image-Audit ueber `make ci`/
`make fullbuild`).

---

## Architektur-Bezug

- [ADR 0045 — HTTP-API-Request-Body-Strict-Validation](../plan/adr/0045-http-api-request-strict-validation.md):
  fixiert den `_BaseRequest`-Vertrag fuer REST-Request-Bodies.
- [ADR 0037 — HTTP-API-Surface-Pattern](../plan/adr/0037-http-api-surface-pattern.md):
  REST + WebSocket-Surface-Foundation; bleibt unveraendert
  `Accepted`, [`ADR 0045`](../plan/adr/0045-http-api-request-strict-validation.md) schaerft additiv ohne Supersedes.
- [ADR 0011 — Schaerfung ohne Abloesung](../plan/adr/0011-schaerfung-ohne-abloesung.md):
  Pattern fuer die [`ADR-0045`](../plan/adr/0045-http-api-request-strict-validation.md)/0037-Schaerfungs-Form.
- [`safe-001-004-quality-pipeline.md`](safe-001-004-quality-pipeline.md):
  Schwester-Audit fuer die Driven-Side-Quality-Substanz.
