# ADR 0045 — HTTP-API-Request-Body-Strict-Validation (M6 Welle 5b)

**Status:** Proposed — Erstwurf in M6-Welle-5b-C1 (dieser
Commit). `Provisional` folgt mit M6-Welle-5b-C3 nach C2-Code-
Merge (Pattern analog ADR 0038/0039/0040 M5-Welle-3/4a/4b-C3
nach C2-Substanz-Merge). `Accepted` folgt in M6-Welle-7-Closure-
C1 gebuendelt mit ADR 0041 + ADR 0042 + ADR 0043 + ADR 0044
(Pattern analog M5-Welle-7-C1 `62f988d`).
**Datum:** 2026-06-07
**Status geaendert am:** 2026-06-07 — Erstwurf `Proposed`
mit M6-Welle-5b-C1 (dieser Commit).
**Bezug:**
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Schaerfung-
ohne-Supersedes-Pattern — ADR 0045 ist eine additive Schaerfung
zu ADR 0037 ohne ADR-0037-Aufhebung; ADR 0037 §2.1 (Action-
Body-Vertrag) + §2.2 (kein UICommandPort) + §2.3 (DRG-002-
Verwerfung) bleiben textlich unveraendert),
[`ADR 0037`](0037-http-api-surface-pattern.md) (HTTP-API-
Surface-Pattern, M5-Welle-1, `Accepted`; ADR 0045 schaerft den
Pydantic-Schema-Vertrag fuer Request-Bodies, ohne den REST-/
WebSocket-Surface-Vertrag oder die Action-Body-Decision API-1
zu beruehren),
[`ADR 0028`](0028-link-maintenance-accepted-adr-bezug.md)
(Link-Maintenance fuer Accepted-ADR-Bezuege; ADR-Index-Update
fuer ADR-0037-Zeile-Schaerfungen-Spalte plus NEU-Zeile fuer
ADR 0045),
[`open/M6-welle-5b.md`](../planning/in-progress/M6-welle-5b.md)
(Welle-5b-Slice-Doc; Decisions D-5 + D-6 mit Strict-Mode-
Default + Schaerfungs-ADR-Pflicht).

---

## 1. Kontext

ADR 0037 (HTTP-API-Surface-Pattern, M5-Welle-1, `Accepted`
2026-06-04) verankert die REST + WebSocket-Surface fuer
`GG-API-001..004`. Drei Decisions sind dort final: §2.1
Action-Body-Vertrag (`POST /runs/{id}/control` mit
`{"action": "..."}`-Body), §2.2 kein separater
`UICommandPort`-Slot, §2.3 Roadmap-Typo `DRG-002`-Verwerfung.

Die Pydantic-Schema-Substanz wird in ADR 0037 §2.1 nur
**implizit** beruehrt: das Code-Beispiel zeigt
`ControlRequest` als Pydantic-`BaseModel`, der „Action vor
TickLoop-Call" validiert. Welcher Pydantic-Mode (Default vs
Strict, `extra`-Verhalten) gilt, ist nicht festgelegt — die
Welle-1-Implementation hat Default-Pydantic-Mode genommen,
weil das die Pydantic-Default-Position ist.

**M6-Welle-5b-Audit-Befund** (vgl. Slice-Doc §1.1): das
Default-Verhalten ist fuer **Response-Bodies** akzeptabel
(Server kontrolliert die Felder), aber fuer **Request-Bodies**
problematisch gegen `GG-SAFE-008` MUSS:

- **Extra-Felder werden silent ignoriert** (Default-Pydantic-
  `extra="ignore"`). Ein Client kann ein
  `POST /runs/{id}/control`-Body mit `{"action": "pause",
  "unknown_key": "evil_payload"}` schicken — der unknown_key
  wird verworfen ohne Diagnose. Bei Typo (`{"actoin":
  "pause"}`) gibt es einen anderen 422 (`field required`),
  aber das ist Glueck — kein Vertrag.
- **Type-Coercion ist aktiv** (Default-Pydantic-`strict=False`).
  Ein Body `{"seed": "42"}` (String statt Int) wird silent
  zu `42` konvertiert; `{"seed": "42abc"}` wird mit klarem
  Fehler abgelehnt. Asymmetrische Strenge — was strikter sein
  sollte, ist es nicht.

`GG-SAFE-008` MUSS-Akzeptanz (Lastenheft Z. 1404-1408):
„REST-, WebSocket- und alle implementierten Adapter-Eingaben
werden gegen Schema, Wertebereiche und Zielressourcen
validiert, bevor sie in den Simulationskern gelangen." Die
Default-Pydantic-Mode-Substanz erfuellt „gegen Schema" nur
mit Schwaechen: Extra-Felder UND Type-Coercion verstecken
Fehler in einer Schicht, deren Aufgabe es ist, sie zu fangen.

**ADR-0011-Constraint:** ADR 0037 ist `Accepted`; per ADR
0006 §3 + ADR 0011 §2 sind direkte Edits am Accepted-Text
verboten. Die Schaerfung muss als **separate** ADR `B` mit
eigenem Header geschrieben werden; ADR 0037 bleibt
unveraendert; der ADR-Index wird per ADR 0028-Pattern
gepflegt.

ADR 0045 schliesst die Luecke: Pydantic-Strict-Mode +
`extra="forbid"` werden zur **Pflicht-Substanz fuer
Request-Bodies** an REST-Endpunkten gemacht. Response-Bodies
bleiben unveraendert (siehe §4 Out-of-Scope).

---

## 2. Entscheidung

ADR 0045 fixiert vier orthogonale Punkte:

### §2.1 Pflicht-Substanz fuer Request-Bodies

Jeder Pydantic-`BaseModel`, der als FastAPI-Request-Body an
einem REST-Endpunkt unter `src/grid_gym/adapters/driving/
http_api/` konsumiert wird, MUSS folgende `model_config`-
Substanz haben:

```python
from pydantic import BaseModel, ConfigDict

class _BaseRequest(BaseModel):
    """Welle-5b: gemeinsame Strict-Mode-Basis fuer alle
    REST-Request-Bodies (ADR 0045 §2.1)."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )
```

- **`strict=True`**: keine Type-Coercion. Pydantic akzeptiert
  nur Inputs, die im exakten Ziel-Typ angeliefert werden
  (Int kommt als JSON-Number, String kommt als JSON-String,
  Bool kommt als JSON-Bool). Ein Body mit `{"seed": "42"}`
  wird mit `Input should be a valid integer [type=int_type,
  input_value='42', input_type=str]` rejected.
- **`extra="forbid"`**: unbekannte Felder fuehren zu 422 mit
  `Extra inputs are not permitted [type=extra_forbidden]`.
  Tippfehler im Client (z. B. `"actoin"` statt `"action"`)
  werden sichtbar statt silent verworfen.

Konkrete Welle-5b-C2-Anwendung: `_BaseRequest` lebt in
`src/grid_gym/adapters/driving/http_api/_schemas.py`. Alle
drei aktuellen Request-Modelle erben:

- `ControlRequest` (`POST /runs/{id}/control`).
- `FaultInjectionRequest` (`POST /runs/{id}/faults`).
- `RunCreateRequest` (`POST /runs`) — Welle-5b-Konsolidierung:
  das Modell wird in C2 aus `app.py` nach `_schemas.py`
  verschoben (siehe §2.4), damit die Strict-Mode-Substanz
  uniform gilt.

Pattern-Verbot: per-Endpunkt-Bypass via
`model_config = ConfigDict(strict=False)` oder
`extra="allow"` an einem Request-Body ist **ADR-Bruch**.
Wenn ein konkreter Endpunkt Strict-Mode strukturell nicht
einhalten kann (z. B. wegen externer Vertrags-Anforderung),
muss eine ADR-Schaerfung an ADR 0045 §2.1 die Ausnahme
explizit zulassen (Pattern analog ADR-0011-Schaerfungs-Welle
ueber ADR 0045 selbst).

### §2.2 Response-Bodies bleiben unveraendert

Response-Bodies (`RunDetailResponse`, `RunStatusResponse`,
`ControlResponse`, `SnapshotResponse`,
`FaultInjectionResponse`, `AlarmDto`/`AlarmsResponse`,
`DeviceStateEntry`/`DevicesResponse`, `ErrorResponse`,
`HealthResponse`, `RunCreateResponse`) sind NICHT betroffen.
Default-Pydantic-Mode bleibt fuer Response-Bodies, weil:

- Der Server kontrolliert die Felder (kein externer Eingang).
- Strict-Mode an Response-Bodies bricht bei Welle-Erweiterungen
  (neue Felder in Response-Modellen wuerden Tests brechen,
  die Snapshots der Vor-Welle haben).
- Lastenheft `GG-SAFE-008` adressiert Eingaben („bevor sie
  in den Simulationskern gelangen"), nicht Ausgaben.

§2.2 fixiert das explizit, damit kuenftige Reviews nicht
versehentlich Response-Bodies in den Strict-Mode ziehen.

### §2.3 WebSocket-Subscribe-Inputs

WebSocket-Endpunkte unter `WS /runs/{run_id}/telemetry` und
`WS /runs/{run_id}/alarms-stream` sind in der aktuellen
Welle-3/4b-Implementation **Subscribe-only** — die Server-
Side liest keine Client-Payloads in den Kern (vgl. Slice-
Doc §1.1 Audit-Befund).

ADR 0045 schreibt deshalb fuer WebSocket-Inputs **keinen**
Pydantic-Strict-Mode-Vertrag vor. Wenn eine zukuenftige
Welle einen Client-WS-Payload-Pfad einfuehrt (z. B. Bidi-
Steuerung), muss die NEU Surface separat audited werden
(Welle-X-Decision; ggf. ADR-Schaerfung an ADR 0045).

`run_id`-Path-Parameter-Validation an WebSocket-Endpoints
ist gesondert (Welle-5b-D-3 Inline-Fix-Material; nicht in
ADR 0045 verankert, weil es FastAPI-Routing-Surface ist,
nicht Pydantic-Schema-Surface).

### §2.4 RunCreateRequest-Konsolidierung

`RunCreateRequest` und `RunCreateResponse` leben in der
M1-Welle-7-Era-Substanz in `src/grid_gym/adapters/driving/
http_api/app.py:139-160` (Welle-Drift gegen die M5-Welle-1-
Konsolidierung von Request-/Response-Schemas in
`_schemas.py`).

In M6-Welle-5b-C2 werden beide Modelle nach `_schemas.py`
verschoben:

```python
# In _schemas.py:
class RunCreateRequest(_BaseRequest):
    """POST /runs Request-Body."""

    scenario_hash: str = Field(..., min_length=64, max_length=64)
    seed: int = Field(..., ge=0, le=2**32 - 1)
    tick_ms: int = Field(..., gt=0)


class RunCreateResponse(BaseModel):
    """POST /runs Response-Body."""

    run_id: str = Field(...)
    state: RunState = Field(...)
```

`app.py` importiert anschliessend beide Modelle aus
`_schemas` statt sie lokal zu definieren. Damit:

- Strict-Mode-Vertrag (§2.1) wirkt auch auf `POST /runs` —
  ohne Konsolidierung wuerde `RunCreateRequest` der einzige
  Default-Mode-Request bleiben (Vertrags-Loch).
- Konsistenz mit der M5-Welle-1-Konsolidierung der anderen
  REST-Schemas in `_schemas.py`.
- `app.py` bleibt schlank (M5-Welle-1-Pattern).

Die Konsolidierung ist Pflicht-Substanz der Welle-5b-C2,
nicht optional. Ohne sie ist ADR 0045 §2.1 fuer
`RunCreateRequest` nicht erfuellt.

---

## 3. Begruendung

- **GG-SAFE-008-MUSS-Akzeptanz erfuellen.** Lastenheft
  Z. 1404-1408 verlangt Validation „gegen Schema,
  Wertebereiche und Zielressourcen, bevor Eingaben in den
  Simulationskern gelangen". Default-Pydantic-Mode mit
  silent extra-Field-Drop und Type-Coercion erfuellt
  „gegen Schema" nur mit Schwaechen; Strict-Mode +
  extra-forbid macht den Vertrag verbindlich.
- **Schwester-Pattern zu Quality-Pipeline (Welle 5a).**
  Welle 5a hat per Audit + Smokes verifiziert, dass
  Quality-Statuswerte deterministisch emittiert werden.
  Welle 5b liefert die analoge Strenge an der Eingangs-
  Schicht — kein silent-Drop, kein silent-Convert.
- **Tippfehler-Sichtbarkeit.** Ein Client, der
  `{"actoin": "pause"}` schickt (Tippfehler), bekommt
  unter Default-Mode entweder einen `field required`-
  Fehler (Glueck) oder eine missverstaendliche Antwort
  („Action default-validiert"; aber `action` fehlt
  tatsaechlich, der unknown_key wurde verworfen). Mit
  `extra="forbid"` ist die Diagnose direkt: „Extra inputs
  are not permitted: actoin". Reduzierter Debug-Aufwand.
- **Schaerfung ohne Supersedes (ADR 0011-Pattern).** ADR
  0037 §2.1 + §2.2 + §2.3 bleiben textlich unveraendert;
  nur die implizite Pydantic-Mode-Substanz wird additiv
  geschaerft. ADR 0037-Substanz bleibt in Kraft, ADR 0045
  liegt parallel. Pattern-Vorbild ist ADR 0044 (Schaerfung
  zu ADR 0043 §2.2) — gleiches Strukturmuster: separate
  ADR-Datei, Bezug-Zeile, ADR-Index-Update, A bleibt
  `Accepted`.
- **Per-Endpoint-Entscheidung wurde verworfen** (Welle-5b-
  D-5 Option B). Strict-Mode + extra-forbid als gemeinsame
  Basis-Klasse `_BaseRequest` ist kohaerenter als per-Model-
  Repetition: ein zentraler Vertrags-Anker, drei (spaeter
  ggf. mehr) erbende Konkrete. Vermeidet Drift.

---

## 4. Reichweite

- ADR 0037 bleibt textlich unveraendert (`Accepted`-
  Immutability per ADR 0006 §3 + ADR 0011 §2). ADR 0045 ist
  ein paralleles Schwester-Dokument.
- `src/grid_gym/adapters/driving/http_api/_schemas.py` wird
  in Welle-5b-C2 erweitert um NEU `_BaseRequest`-Mixin +
  NEU verschobene `RunCreateRequest`/`RunCreateResponse`.
  Bestehende Request-Modelle (`ControlRequest`,
  `FaultInjectionRequest`) erben `_BaseRequest`.
- `src/grid_gym/adapters/driving/http_api/app.py` wird in
  Welle-5b-C2 zurueckgeschnitten: `RunCreateRequest` +
  `RunCreateResponse` werden aus `_schemas.py` importiert
  statt lokal definiert.
- Response-Modelle, WebSocket-Endpoints, FastAPI-Routing-
  Surface, Snapshot-/Domain-Schemas bleiben **unangetastet**.
- ADR-Index Aktive-ADRs-Tabelle ADR-0037-Zeile bekommt
  „Schaerfungen / Folge-ADRs"-Spalte um ADR-0045-Eintrag
  (Index-Pflege per ADR 0011 §4); ADR-0045-Zeile NEU
  angelegt.
- Welle-5b-Smokes (`tests/integration/test_m6_welle_5b_safe_
  007_008_smoke.py`; Welle-5b-C2) belegen die Vertrags-
  Substanz:
  - `test_safe_008_rest_extra_field_rejected` (extra-forbid
    Beleg).
  - `test_safe_008_rest_type_coercion_rejected` (Strict-Mode
    Beleg).
- Bestehende Tests in `tests/unit/` und `tests/integration/`,
  die `RunCreateRequest`/`ControlRequest`/`FaultInjectionRequest`
  mit Type-Coercion-Eingaben (`seed="42"`) oder extra-Feldern
  konstruieren, werden in C2 an den Strict-Vertrag
  angeglichen (Pattern analog M5-Welle-2-Tests-Refactor an
  Welle-1-Vertrag).

---

## 5. Operative Artefakte (Erstanwendung in M6-Welle-5b)

Mit dieser ADR sind die folgenden Welle-5b-Substanz-Items
verbunden:

1. **M6-Welle-5b-C0** (`0d3bb61`) + **C0-Review-Folge**
   (`369f130`):
   - NEU `docs/plan/planning/in-progress/M6-welle-5b.md`
     (Slice-Doc-Anlage; Welle-5b-Decisions D-1..D-6 final
     inkl. D-5 Strict-Mode-Default + D-6 NEU Schaerfungs-
     ADR 0045).
   - `in-progress/README.md` + `M6-perf-security-cicd.md`
     §3.1 Welle-5-Zeile in 5a/5b/5c gespalten; 5b auf
     `In Progress`.
   - C0-Review-Folge: F1 Adapterkonfig-Scope + F2 C1-
     Pflicht-Findings adressiert (C1 ist Pflicht-Commit
     vor C2).

2. **M6-Welle-5b-C1** (dieser Commit):
   - NEU `docs/plan/adr/0045-http-api-request-strict-
     validation.md` (`Proposed`, dieser Text).
   - `docs/plan/adr/README.md` Aktive-ADRs-Tabelle um
     ADR-0045-Zeile ergaenzt; ADR-0037-Zeile-Schaerfungen-
     Spalte um ADR-0045-Bezug ergaenzt (ADR-0011 §4-
     Pattern).

3. **M6-Welle-5b-C2** (vorbedingt; Hash `<TBD>`):
   - NEU `_BaseRequest`-Mixin in `_schemas.py` mit
     `ConfigDict(strict=True, extra="forbid")`.
   - Umzug `RunCreateRequest` + `RunCreateResponse` aus
     `app.py` nach `_schemas.py`; `app.py` importiert.
   - `ControlRequest` + `FaultInjectionRequest` +
     `RunCreateRequest` erben `_BaseRequest`.
   - NEU `tests/integration/test_m6_welle_5b_safe_007_008_
     smoke.py` mit 11 Smoke-Tests (5×GG-SAFE-007 +
     6×GG-SAFE-008; 2 davon belegen den Strict-Vertrag).
   - NEU `docs/user/safe-007-008-sim-prod-input-validation.md`
     Audit-Tabelle.
   - Ggf. Inline-Fixes fuer GG-SAFE-007-Surfaces (UI-
     Dashboard-Sim-Marker, Scenario-YAML-Top-Level-
     Kommentar-Block, Protocol-Adapter-`_config.py`-
     Docstring-Disclaimer).
   - Test-Anpassungen falls Strict-Mode bestehende Tests
     mit Type-Coercion-Eingaben bricht (Pattern analog
     M5-Welle-2-Tests-Refactor).
   - Verifikation: `make gates` + `make ci` +
     `make fullbuild` cache-frei gruen ohne `CRITICAL_COV_
     TARGETS`-Override.

4. **M6-Welle-5b-C3** (vorbedingt; Hash `<TBD>`):
   - ADR 0045 `Proposed → Provisional` mit Welle-5b-C2-
     Code-Beleg (Pattern analog ADR 0038/0039/0040 M5-
     Welle-3/4a/4b-C3-Flips).
   - `M6-welle-5b.md` Status `In Progress → Done 2026-06-07`
     mit Liefer-Hash-Stack.
   - `M6-perf-security-cicd.md §3.1` Welle-5b-Zeile `In
     Progress → Done` + Aktive-Welle-Block auf Welle 5c.

5. **M6-Welle-5b-C4a/C4b** (Self-Close-Folge; vorbedingt):
   - C4a: `git mv M6-welle-5b.md → done/` (rename-only).
   - C4b: Cross-Doc-Refs-Sync nach Move + Hash-Slot-Fills.

6. **M6-Welle-7-Closure-C1** (Folge-Welle):
   - ADR 0045 `Provisional → Accepted` gebuendelt mit
     ADR 0041 + ADR 0042 + ADR 0043 + ADR 0044 (Pattern
     analog M5-Welle-7-C1 `62f988d`).

`make gates` bleibt cache-frei gruen ohne Override in C1
(reine Doku-Substanz; keine Test-Counts-Aenderung).

---

## 6. Konsequenzen

- **Positiv:** `GG-SAFE-008`-MUSS-Akzeptanz fuer REST-
  Request-Bodies wird verbindlich („gegen Schema" mit
  exakter Type- und Field-Strenge). Audit-Trail durch
  zentralen `_BaseRequest`-Mixin.
- **Positiv:** Tippfehler-Diagnose ist eindeutig (extra-
  forbid 422-Fehler statt silent-Drop). Client-Entwicklung
  wird einfacher zu debuggen.
- **Positiv:** Schaerfung ohne Supersedes — ADR 0037-
  Substanz bleibt textlich unangetastet. Pattern-Konsistenz
  mit ADR 0011 + ADR 0044.
- **Positiv:** `_BaseRequest`-Mixin ist Erweiterungspunkt
  fuer zukuenftige Request-Modelle; neue Request-Bodies
  erben automatisch den Vertrag.
- **Negativ:** Bestehende Tests, die Pydantic-Default-
  Mode-Coercion ausnutzen (z. B. `RunCreateRequest(seed=
  "42", ...)` in Unit-Tests), brechen. Welle-5b-C2
  adressiert das per Test-Refactor (Pflicht-Inline-Fix;
  Pattern analog M5-Welle-2).
- **Negativ:** Strict-Mode schliesst Client-Konvenienz aus
  (z. B. einen `tick_ms` als JSON-String `"100"` zu schicken
  funktioniert nicht mehr). Akzeptabel, weil
  `GG-SAFE-008`-Vertragsstrenge ueber Client-Convenience
  geht.
- **Neutral:** Response-Bodies bleiben unveraendert. Drift-
  Risiko gegen Welle-Erweiterungen wird vermieden.
- **Neutral:** WebSocket-Subscribe-Inputs bleiben out-of-
  scope (Subscribe-only-Welle-3/4b-Substanz; keine
  Client-Payload-Konsumption am Kern).
- **Neutral:** `run_id`-Path-Parameter-Validation bleibt
  out-of-scope (FastAPI-Routing-Surface, nicht Pydantic-
  Schema-Surface; Welle-5b-D-3 Inline-Fix-Material).

---

## 7. Nicht Gegenstand dieser ADR

- **Aufhebung von ADR 0037 §2.1/§2.2/§2.3.** Action-Body-
  Vertrag, kein-UICommandPort-Decision, DRG-002-Verwerfung
  bleiben unveraendert.
- **Strict-Mode an Response-Bodies.** Explizit ausgeklammert
  in §2.2.
- **WebSocket-Client-Payload-Validation.** WebSocket-
  Endpunkte sind Subscribe-only; explizit ausgeklammert
  in §2.3. Wenn zukuenftige Welle einen Bidi-Pfad
  einfuehrt, ADR-Schaerfung an ADR 0045 noetig.
- **`run_id`-UUID-Validation an Path-Parameters.** FastAPI-
  Routing-Surface; nicht Pydantic-Schema-Surface; Welle-
  5b-D-3 Inline-Fix-Material.
- **Adapter-Side-Input-Validation** (Protocol-Adapter-
  Reads von externen Geraeten). Welle-5b-D-4 Option B
  Audit-Tabellen-Belegung, nicht Pydantic-Vertrag.
- **Custom Pydantic-Validators** (z. B. Cross-Field-
  Validation in `FaultInjectionRequest`). Welle-6a hat das
  bereits per `model_validator` produktiv. ADR 0045
  beruehrt das nicht; Custom-Validators sind orthogonal
  zu `model_config`-Mode.
- **Pydantic-Version-Pin-Bump.** `pydantic>=2.13` (siehe
  `pyproject.toml`) bleibt unangetastet; `strict=True` +
  `extra="forbid"` werden seit Pydantic 2.0 unterstuetzt.
- **Vendor-spezifische Schema-Formate** (z. B. JSON-Schema-
  Draft-2020-12). Pydantic-erzeugte OpenAPI-Schemata bleiben
  Pydantic-natives Format.
- **Multi-Layer-Validation-Strategie** (Schema → Wertebereich
  → Zielressource). ADR 0045 deckt nur Schema-Layer (Type
  + Field-Set); Wertebereiche bleiben Per-Endpoint-
  Pydantic-`Field`-Constraints (z. B. `Field(..., ge=0,
  le=2**32 - 1)`); Zielressourcen-Validation bleibt
  Endpoint-Logik (z. B. `_require_run_or_404`-Helper).
