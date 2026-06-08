# Welle 5a — M6 Quality-Pipeline-Audit (`GG-SAFE-001..004` MUSS)

**Status:** Done 2026-06-06.
**Liefer-Hash-Stack:** C0 `4b36185` (Slice-Doc-Anlage) → C2
`4c1a693` (Quality-Pipeline-Audit-Substanz: 7 Smokes + Audit-
Doku + 2 NEU `open/`-Triggers 034/035) → C2-Review-Folge
`52cb698` (6 Self-Review-Findings F1..F6 adressiert) → C3
**dieser Commit** (Status/DoD-Sync + aktive Welle auf 5b).
C4a/C4b folgen als Welle-5b-Pre-C0a/Pre-C0b.

**Audit-Ergebnis** (Welle-5a-D-2 Hybrid-Form):

- `GG-SAFE-001` ✓ **produktiv** (Scenario-Loader-Validation +
  Pydantic-API + Adapter-`Quality.INVALID`-Emission).
- `GG-SAFE-002` ✓ **produktiv** (`canonical_json`-NaN/Inf-
  Reject mit `NonFiniteDecimalError`).
- `GG-SAFE-003` ⚠ **partial Lücke** (SmartMeter-pre-attach
  produktiv; Adapter-Verbindungs-Verlust + Alarm fehlt →
  Trigger 035).
- `GG-SAFE-004` ✗ **Lücke** (`max_age`-Substanz fehlt komplett
  im Repository → Trigger 034).

**Vorheriger Status:** In Progress — C0 (Slice-Doc-Anlage).
Welle 5 wird gemaess Welle-5a-D-1 in **5a (Quality-Pipeline-
Audit; `GG-SAFE-001..004` MUSS) + 5b (Sim/Prod-Marker + Input-
Validation; `GG-SAFE-007` + `GG-SAFE-008` MUSS) + 5c (SOLLTE-
Items + IP/Netz-Beschraenkung; `GG-SAFE-005` + `GG-SAFE-006` +
Demo-Compose-Hardening)** sub-geslict. Welle 5a ist die **erste
Sub-Welle** und liefert die End-to-End-Verifikation + Luecken-
Auditierung der existierenden Quality-Pipeline-Substanz fuer die
vier MUSS-IDs.

**Pre-C0 abgeschlossen (M6-Welle-4b-c-Closure-Folge):**

- C4a `7d8ac5a` — `git mv M6-welle-4b-c.md → done/` (Self-
  Close-Move, rename-only).
- C4b `2656304` — Cross-Doc-Refs-Sync nach Move + Hash-Slot-
  Fills. **Welle-4-Subdivision komplett**: 4a + 4b-a/b/c alle
  Done.

**Spec-Reife:** Inhaltlich final fuer Welle 5a. Welle-5a-
Decision-Liste (§3) schliesst Welle-5a-D-1..D-5: Welle-5-Sub-
Slicing-Beschluss, Audit-Form, Luecken-Adressier-Strategie,
Alarm-Emission-Verifikation, ADR-Bedarf.

---

## 1. Context

`GG-SAFE-001..004` MUSS (Lastenheft Z. 1349-1378):

- **`GG-SAFE-001`**: Ungueltige Daten MUESSEN erkannt werden;
  Schema-/Wertebereichs-/Einheiten-Fehler werden vor Uebernahme
  in den Simulationskern als Validierungsfehler ODER
  Qualitaetsstatus `invalid` gemeldet, plus
  Fehler-/Alarm-Datensatz.
- **`GG-SAFE-002`**: NaN-Werte DUERFEN NICHT ungeprueft
  verarbeitet werden; vor Zustandsfortschreibung erkannt, als
  Qualitaetsstatus `nan` serialisiert, plus Alarm/typisierter
  Fehler.
- **`GG-SAFE-003`**: Kommunikationsausfaelle MUESSEN erkannt
  werden; dokumentierter Fehlerstatus, betroffene Telemetrie
  als `missing` ODER `stale`, plus Alarm mit Ziel/Startzeit/
  Ursache.
- **`GG-SAFE-004`**: Veraltete Daten MUESSEN markiert werden;
  Werte deren Sim-Zeitstempel `max_age` ueberschreiten
  bekommen deterministisch Qualitaetsstatus `stale`.

### 1.1 Existierende Substanz (vor Welle 5a)

- **`Quality`-Enum** (`hexagon/core/domain/quality.py`):
  vollstaendig (`VALID`/`STALE`/`ESTIMATED`/`LIMITED`/
  `INVALID`/`NAN`/`MISSING`/`FAULT_INJECTED`); `QUALITY_
  SEVERITY`-Ranking-Mapping.
- **`canonical_json`-Adapter** (`hexagon/core/serialization/
  canonical.py`): NaN/Inf-Reject (`NonFiniteDecimalError`) —
  `GG-SAFE-002`-Substanz auf Domain-Serialisierungs-Ebene
  produktiv.
- **Scenario-Loader-Validierung** (`hexagon/core/scenario/
  loader.py`): Schema-/Wertebereich-Validierung mit
  typisierten `ScenarioValidationError`-Familie —
  `GG-SAFE-001`-Substanz auf Loader-Ebene produktiv.
- **HTTP-API-Pydantic-Validation** (`adapters/driving/
  http_api/_schemas.py`): Pydantic-BaseModel-Validation fuer
  alle REST-Endpunkte; Schema-Fehler → 422 mit
  `ErrorResponse` — `GG-SAFE-001`/`GG-SAFE-008`-Substanz
  produktiv.
- **`Quality.STALE`-Enum-Wert verankert** (`hexagon/core/
  domain/quality.py:24`); **aber `max_age`-Substanz fehlt
  komplett im Repository** — Pre-C0-Vorbelegung dieses Doks
  hatte „TickLoop-Quality-Stage emittiert `STALE` fuer
  `max_age`-Ueberschreitung" angenommen; Welle-5a-C2-Audit
  hat das ueberstimmt (Grep ueber `src/grid_gym/` nach
  `max_age` liefert null Treffer). Status: Lücke. Folge-
  Pfad: [Trigger 034](../open/034-safe-004-max-age-stale-quality.md).
- **Adapter-Quality-Emission**: Protocol-Adapter (OPC-UA/IEC-
  61850) emittieren `INVALID` bei String-Lese-Faellen
  (`protocol_opcua/_port.py:312`, `protocol_iec61850/_port.
  py:368`) — `GG-SAFE-001`-Substanz produktiv. `MISSING`
  bei `SmartMeterDevice`-pre-attach (`devices/smart_meter/
  model.py:202`) ist Konfigurations-Pre-Attach, NICHT echter
  Adapter-Verbindungs-Verlust — `GG-SAFE-003`-Substanz nur
  **partial**, vollstaendige Adapter-Lifecycle-Hook + Alarm-
  Emission fehlt. Folge-Pfad: [Trigger 035](../open/035-safe-003-comm-failure-missing-quality.md).
- **Fault-Injection** (M3 Welle 1/2; ADR 0022 + 0025):
  `FAULT_INJECTED`-Quality + Alarm-Emission per Fault-Adapter.

### 1.2 Welle-5a-Lieferziel

**Audit-Welle** (NICHT primaer NEU-Code-Welle): die existierende
Quality-Pipeline-Substanz wird **End-to-End verifiziert + Lücken
identifiziert**. Drei orthogonale Liefer-Items:

1. **NEU `tests/integration/test_m6_welle_5a_safe_001_004_
   smoke.py`** (Welle-5a-C2) — Sieben Smoke-Tests (4 Pflicht
   + 2 Schwester-Akzeptanz + 2 skip-Marker auf NEU Triggers):
   - `test_safe_001_invalid_scenario_schema_rejected`:
     Scenario mit Schema-Fehler wird vom Loader rejected
     (kein Lauf-Start).
   - `test_safe_001_invalid_scenario_wrong_type_rejected`
     (Schwester): Scenario mit korrekten Pflicht-Keys aber
     wrong-type-Wert wird ebenfalls rejected.
   - `test_safe_002_nan_value_rejected_at_serialization`:
     TelemetryPoint mit `value=NaN` wird canonical_json-
     reject mit `NonFiniteDecimalError`.
   - `test_safe_002_infinity_value_rejected_at_serialization`
     (Schwester): Infinity einheitlich rejected.
   - `test_safe_003_smart_meter_pre_attach_emits_missing`:
     deckt **Teil-Substanz** (SmartMeter-pre-attach →
     `Quality.MISSING`; ADR 0018 §2.3); voller Adapter-
     Comm-Failure-Akzeptanz-Umfang ist `pytest.skip` mit
     Pointer auf [Trigger 035](../open/035-safe-003-comm-failure-missing-quality.md).
   - `test_safe_003_comm_failure_emits_missing_or_stale`:
     `pytest.skip` mit Pointer auf Trigger 035 (voller
     Umfang ist Welle-5a-Audit-Lücke).
   - `test_safe_004_stale_data_quality_after_max_age`:
     `pytest.skip` mit Pointer auf [Trigger 034](../open/034-safe-004-max-age-stale-quality.md)
     (`max_age`-Substanz fehlt komplett im Repository;
     Welle-5a-Audit-Lücke).

2. **NEU Audit-Tabelle in `docs/user/safe-001-004-quality-
   pipeline.md`** (Welle-5a-C2) — Mapping pro `GG-SAFE-00X`-
   ID zur produktiven Substanz-Stelle (Datei-Pfad + Test-
   Pfad), zu festgestellten Luecken, und zur Verifikations-
   Form.

3. **Luecken-Adressierung** (Welle-5a-C2) — falls Audit
   Luecken aufdeckt (z. B. Adapter ohne Quality-Emission bei
   bestimmten Lese-Fehler-Pfaden): Pflicht-Fixes im selben
   C2. Welle-5a-D-3 entscheidet die Form (Inline-Fix vs
   NEU `open/`-Trigger).

### 1.3 Welle-5a-Anti-Scope

- **Kein `GG-SAFE-007` Sim/Prod-Marker** — Welle-5b-Scope.
- **Kein `GG-SAFE-008` Adapter-Input-Validation-Audit** —
  Welle-5b-Scope (HTTP-API ist bereits substanziell ueber
  Pydantic abgedeckt).
- **Kein `GG-SAFE-005/006` SOLLTE-Items** — Welle-5c-Scope.
- **Keine IP-/Netz-Beschraenkung im Demo-Compose** — Welle-
  5c-Scope.
- **Keine neue Quality-Enum-Variante** — die acht Quality-
  Statuswerte sind ausreichend (M5-Welle-6b-Review F15
  fixiert).
- **Kein NEU ADR** — Welle-5a-D-5 schliesst ADR-Bedarf
  negativ aus.
- **Kein NEU Code im Core** — Audit + Tests + Doku; falls
  Luecken im Adapter aufgedeckt werden, dann Adapter-Fix.

---

## 2. Scope

Welle 5a liefert **drei Items** ueber 3 Commits (C0..C3),
plus Self-Close-Folge C4a/C4b.

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses Dokument;
   in-progress/README.md + M6-perf-security-cicd.md §3.1
   Welle-5 in 5a/5b/5c gespalten; aktive Welle auf 5a.
2. **C1 entfaellt** — Welle-5a-D-5 schliesst ADR-Bedarf
   negativ aus; Pattern analog M5-Welle-2 `5234617`.
3. **Code-Substanz** (C2) — NEU `tests/integration/test_m6_
   welle_5a_safe_001_004_smoke.py` + NEU `docs/user/safe-
   001-004-quality-pipeline.md` Audit-Tabelle; ggf.
   Luecken-Fixes (Welle-5a-D-3). Lokal-Verifikation alle
   Gates gruen.
4. **Status/DoD-Sync** (C3) — Status-Flip + Aktive-Welle-
   Block auf Welle 5b; Top-Level-Doku-Sync (`README.md`/
   `README.de.md` NEU Quality-Pipeline-Hinweis falls relevant;
   `roadmap.md §3 M6` aktive Welle auf 5b).

Self-Close-Folge C4a/C4b laufen nach C3 als M6-Welle-5b-Pre-
C0a/Pre-C0b.

---

## 3. Architektur-Entscheidungen (Welle-5a-Decision-Liste)

### Welle-5a-D-1 — Welle-5-Sub-Slicing-Beschluss

**Frage:** Wird Welle 5 als Single-Welle (alle `GG-SAFE-*`)
oder in 5a/5b/5c sub-geslict?

**Welle-5a-Final: Sub-Slicing in 5a + 5b + 5c.** Begruendung:

- Drei thematische Cluster: Quality-Pipeline (001-004 MUSS) /
  Sim-Prod-Trennung + Input-Validation (007/008 MUSS) /
  SOLLTE-Items + IP/Netz (005/006 + Demo-Compose).
- Welle-4b-Pattern-Praezedenz (Sub-Slicing 4b-a/b/c hat sich
  bewaehrt; M5-Welle-6 6a/b/c analog).
- Single-Welle-Slice-Doc waere > 500 Zeilen + > 5 Code-
  Commits — Sub-Slicing-Schwelle aus `M6-perf-security-cicd.
  md §3` greift.

### Welle-5a-D-2 — Audit-Form

**Frage:** Wie wird die GG-SAFE-001..004-Akzeptanz audited?

Optionen:

- **A — Reine Doku-Tabelle** (Mapping pro ID zur Substanz-
  Stelle).
- **B — End-to-End-Smoke-Tests** (vier dedizierte
  Integration-Smokes; pinnt das Verhalten in CI).
- **C — Kombiniert** (Doku-Tabelle + Smoke-Tests).

**Welle-5a-Final: Option C (Doku + Smoke-Tests).**
Begruendung:

- Doku-Tabelle alleine ist nicht CI-belastbar; Drift kann
  ohne Sensor passieren.
- Smoke-Tests alleine ohne Doku sind schwer fuer Reviewer
  zu lokalisieren.
- Kombiniert: Doku ist Audit-Trail; Smoke-Tests sind
  Drift-Sensor.

### Welle-5a-D-3 — Luecken-Adressier-Strategie

**Frage:** Wenn der Audit Luecken aufdeckt (z. B. Adapter X
emittiert nicht `Quality.MISSING` bei Lese-Fehler), wird das
inline gefixt oder als `open/`-Trigger vertagt?

Optionen:

- **A — Alle Luecken inline in Welle-5a-C2 fixen** (substanzielle
  Adapter-Aenderungen moeglich).
- **B — Inline fixen falls minimal; substantielle Luecken als
  NEU `open/`-Trigger** (Welle-5a-Closure-Material).
- **C — Alle Luecken als `open/`-Trigger** (Welle-5a bleibt
  scope-eng auf Audit + Doku).

**Welle-5a-Final: Option B (Hybrid).** Begruendung:

- Minimale Luecken (z. B. fehlender Quality-Marker in einem
  Adapter) sind in Welle-5a-C2-Substanz mit-zu-fixen.
- Substantielle Luecken (z. B. NEU Quality-Pipeline-Stage)
  brauchen eigene Welle-Substanz-Diskussion.
- Welle-5a-C2-Review-Folge-Material falls Luecken erst beim
  Code-Schreiben sichtbar werden.

### Welle-5a-D-4 — Alarm-Emission-Verifikation

**Frage:** `GG-SAFE-001/002/003` verlangen Alarm-Emission
oder typisierten Fehler bei Validation-Failure. Wie wird das
in den Smoke-Tests verifiziert?

**Welle-5a-Final:** **Per-Smoke-Assert auf Alarm-Buffer ODER
auf Exception-Raise.** Begruendung:

- Existierende `InMemoryAlarmStream`/`AlarmHistoryBuffer`-
  Adapter (M5-Welle-4b ADR 0040) erlauben Alarm-Capture im
  Smoke-Test.
- `ScenarioValidationError`-Familie ist typisiert und kann
  per `pytest.raises` verifiziert werden.
- Smoke-Test-Akzeptanz: entweder Alarm-Buffer enthaelt
  Alarm-Datensatz, ODER typisierter Fehler wurde geworfen.

### Welle-5a-D-5 — ADR-Schaerfungs-Bedarf

**Frage:** Erfordert Welle-5a eine NEU ADR oder Schaerfung
einer bestehenden?

**Welle-5a-Final: Nein.** Begruendung:

- Quality-Pipeline-Substanz ist seit M3-Welle-6c verankert
  (ADR 0014/0016/0017/0018-Device-Quality-Emission).
- `canonical_json`-Vertrag (M2-Welle-0a Trigger 014) deckt
  NaN-Reject.
- Scenario-Loader-Validierung (ADR 0021) deckt Schema-
  Validierung.
- Audit + Tests + Doku verlangen keinen neuen Vertrag.
- Pattern analog M5-Welle-2 `5234617` (kein C1-ADR;
  Decision-Substanz im Slice-Doc-Body verankert).

---

## 4. Liefer-Reihenfolge (3 Commits)

### Pre-C0 — bereits erledigt (M6-Welle-4b-c-Closure-Folge)

- `7d8ac5a` (Pre-C0a: `git mv M6-welle-4b-c.md → done/`).
- `2656304` (Pre-C0b: Cross-Doc-Refs-Sync + Hash-Slot-Fills).

### C0 — `docs(plan)`: M6-welle-5a Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU `M6-welle-5a.md` (dieses Dokument).
- `in-progress/README.md` Bestand-Tabelle um Welle-5a-Zeile +
  Aktive-Welle-Block auf M6-Welle-5a.
- `M6-perf-security-cicd.md §3.1` Welle-5-Zeile in 5a/5b/5c
  gespalten; 5a `Pending → In Progress 2026-06-06`; Status-
  Block oben aktive Welle auf 5a.

### C1 entfaellt

Welle-5a-D-5 schliesst ADR-Schaerfungs-Bedarf negativ aus.

### C2 — `feat(security)` + `docs(user)`: GG-SAFE-001..004 Audit + Smokes

Code-Merge mit:

- NEU `tests/integration/test_m6_welle_5a_safe_001_004_smoke.
  py` mit 7 Smoke-Tests (Welle-5a-D-2 + D-4):
  - SAFE-001 (×2): Schema-Validation-Fehler im Loader +
    wrong-type-Schwester.
  - SAFE-002 (×2): NaN-Reject + Infinity-Schwester im
    canonical_json.
  - SAFE-003 (×2): SmartMeter-pre-attach → `Quality.MISSING`
    (Teil-Substanz produktiv) + Adapter-Comm-Failure-Smoke
    `pytest.skip` mit Pointer auf NEU Trigger 035.
  - SAFE-004 (×1): max_age-Ueberschreitung → `Quality.STALE`
    `pytest.skip` mit Pointer auf NEU Trigger 034 (Audit
    hat Vorbelegungs-Annahme „produktiv seit M3" ueberstimmt).
- NEU `docs/user/safe-001-004-quality-pipeline.md` Audit-
  Tabelle mit:
  - Pro GG-SAFE-00X-ID: Lastenheft-Akzeptanz, Substanz-Pfad
    (Code-Datei + Zeile), Test-Pfad, Status (✓ produktiv /
    Lücke).
- Inline-Luecken-Fixes (Welle-5a-D-3) falls Audit Luecken
  aufdeckt.
- **Verifikation (lokal vor C2-Commit):**
  - `make gates` cache-frei gruen (10/10 A-1-Gates; Test-
    Counts: +7 Integration-Smokes, davon 2 `pytest.skip`
    mit Trigger-Pointern → 5 aktive Pass + 2 Skip).
  - `make ci` cache-frei gruen.
  - `make fullbuild` cache-frei gruen.
  - `make docs-check` cache-frei gruen.

### C3 — `docs(plan)`: Status/DoD-Sync

**Welle-5a-Closure-Sync.**

- `M6-welle-5a.md` Status `In Progress → Done 2026-06-06`
  mit Liefer-Hash-Stack.
- `M6-perf-security-cicd.md §3.1` Welle-5a-Zeile `In
  Progress → Done` mit Closure-Hash + Aktive-Welle-Block
  auf Welle 5b.
- **Top-Level-Doku-Sync:**
  - `README.md` + `README.de.md`: NEU Quality-Pipeline-
    Audit-Hinweis falls relevant (Doku-Pointer auf
    `docs/user/safe-001-004-*`).
  - `roadmap.md §3 M6` aktive-Welle-Block auf M6-Welle-5b +
    Welle-5a-Abschluss-Notiz.

### Welle-5a-Closure-Folge (nach C3, Pattern Welle-4b-c)

- C4a `git mv M6-welle-5a.md → done/` (rename-only).
- C4b Cross-Doc-Refs-Sync nach Move + Hash-Slot-Fills.

C4a/C4b dienen gleichzeitig als M6-Welle-5b-Pre-C0a/Pre-C0b.

---

## 5. Critical Files

**Welle-5a-NEU (geschrieben in C0/C2):**

- `docs/plan/planning/in-progress/M6-welle-5a.md` (C0,
  dieser Commit).
- `tests/integration/test_m6_welle_5a_safe_001_004_smoke.py`
  (C2).
- `docs/user/safe-001-004-quality-pipeline.md` (C2).

**Welle-5a-MODIFY (in C0/C2/C3):**

- `docs/plan/planning/in-progress/README.md` (C0 + C3).
- `docs/plan/planning/in-progress/M6-perf-security-cicd.md`
  (C0 + C3) — §3.1 Welle-5-Zeile in 5a/5b/5c gespalten.
- Ggf. Adapter-Code (bei Luecken-Findings; Welle-5a-D-3).
- `docs/plan/planning/in-progress/roadmap.md` (C3) — §3 M6
  aktive-Welle-Block + Welle-5a-Abschluss-Notiz.
- `README.md` + `README.de.md` (C3) — NEU Quality-Pipeline-
  Audit-Hinweis falls relevant.

**Welle-5a-UNBERUEHRT (kein Edit):**

- `Quality`-Enum (`hexagon/core/domain/quality.py`) — bereits
  alle 8 Statuswerte; M5-Welle-6b-Review F15 fixiert.
- ADRs 0001..0044 (Welle 5a ohne C1-ADR; D-5 schliesst
  Schaerfungs-Bedarf negativ aus).
- `pyproject.toml`/`uv.lock`/`Dockerfile`/`Makefile` (kein
  neuer Dep-Bedarf).
- Alle GitHub-Actions-Workflows.

---

## 6. Verifikationspfad

**Welle-5a-Gate:**

- `make docs-check` cache-frei gruen.
- `make gates` cache-frei gruen (10/10 A-1-Gates).
- `make ci` cache-frei gruen.
- `make fullbuild` cache-frei gruen.

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur Doc-Substanz.
- C2 prueft 7 NEU Smoke-Tests (5 Pass + 2 Skip) + NEU
  Audit-Doku + NEU 2 Trigger-Docs (034 + 035) + alle
  bestehenden Gates gruen.
- C3 prueft Status-Flip + Top-Level-Doku-Sync.

**Abnahme-Verifikation:**

- `GG-SAFE-001..004` MUSS-Akzeptanz audited:
  - SAFE-001 ✓ **produktiv**: Schema-Validation per Scenario-
    Loader + Pydantic-API + Adapter-`Quality.INVALID`-Emission.
  - SAFE-002 ✓ **produktiv**: NaN/Infinity-Reject per
    canonical_json-Pipeline mit `NonFiniteDecimalError`.
  - SAFE-003 ⚠ **partial Lücke**: SmartMeter-pre-attach-
    `Quality.MISSING` produktiv (ADR 0018 §2.3); echter
    Adapter-Verbindungs-Verlust + Alarm fehlt → Trigger 035.
  - SAFE-004 ✗ **Lücke**: `max_age`-Substanz fehlt komplett
    im Repository (Welle-5a-Audit hat Vorbelegungs-Annahme
    ueberstimmt) → Trigger 034.

---

## 7. Risiken

**R1 — Audit deckt substantielle Luecke auf.** Welle-5a-
Scope ist Audit + Tests + Doku; falls eine substantielle
Luecke aufgedeckt wird (z. B. NEU Quality-Pipeline-Stage),
sprengt das den Welle-5a-Scope.
**Mitigation:** Welle-5a-D-3 Option B (Hybrid) erlaubt
NEU `open/`-Trigger als Vertagungs-Pfad. Welle-5a-C2-Review-
Folge-Material falls Luecken erst beim Code-Schreiben
sichtbar werden.

**R2 — Smoke-Test-Construction-Overhead.** Integration-Smokes
muessen FastAPI-Client + Run-Setup + Adapter-Mocking
aufbauen. Pattern-Praezedenz aus M5-Welle-4a/b/6a/6b/4b-c
existiert.
**Mitigation:** Tests folgen dem existierenden Pattern;
keine neue Test-Infrastruktur.

**R3 — Welle-5-Sub-Sub-Slicing-Komplexitaet.** 3 Sub-Slices
in Welle 5 sind Pattern-Konsistenz mit M5-Welle-6 + M6-
Welle-4b. Aber 8 Sub-Slices in M6 (0/1/2/3/4a/4b-a/b/c/5a/
b/c/6/7) sind viel.
**Mitigation:** M6-Welle-7-Closure-Sweep S-2 dokumentiert
das Sub-Slicing-Pattern als M6-Erbschaft-Lehre.

**R4 — Adapter-Quality-Emission-Pfade unterschiedlich.**
Pro Adapter-Familie (OPC-UA/IEC-61850/Modbus/DNP3/MQTT)
sind Quality-Emission-Pfade unterschiedlich; Audit-Tabelle
muss differenziert sein.
**Mitigation:** Audit-Tabelle in C2 wird per Adapter-Familie
strukturiert; Welle-5a-C2-Audit-Tabelle-Schaerfung moeglich.

**R5 — Pattern-Drift gegen Welle-4-Audit-Form.** Welle-4b-a
hatte Bench-Tests + ADR + Code; Welle-5a hat Doku + Smoke-
Tests + ggf. minimal-Fix. Substanz-Form unterschiedlich.
**Mitigation:** Welle-5a-D-2 fixiert die Audit-Form explizit
(Doku + Tests); Pattern-Drift ist bewusst (Audit-Welle vs
Feature-Welle).

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack**: nach C3
  schliesst die Welle ihre eigene Commit-Sequenz mit
  `git mv M6-welle-5a.md → ../done/M6-welle-5a.md` (C4a) +
  Cross-Doc-Refs-Sync (C4b). Pattern analog M6-Welle-4b-c-
  C4a `7d8ac5a`/C4b `2656304`.
- C4a/C4b dienen gleichzeitig als M6-Welle-5b-Pre-C0a/Pre-C0b.
- Keine NEU ADRs (Welle 5a ohne C1-ADR; D-5).

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **C0 — NEU `M6-welle-5a.md`** mit §1..§9-Struktur
  (dieser Commit).
- [x] **C0 — `in-progress/README.md`** Bestand-Tabelle
  um `M6-welle-5a.md`-Eintrag + Aktive-Welle-Block auf
  M6-Welle-5a.
- [x] **C0 — `M6-perf-security-cicd.md §3.1`** Welle-5-
  Zeile in 5a/5b/5c gespalten; 5a `Pending → In Progress
  2026-06-06`.
- [x] **C1 entfaellt** — Welle-5a-D-5.
- [x] **C2 — NEU `tests/integration/test_m6_welle_5a_safe_
  001_004_smoke.py`** mit 7 Smoke-Tests (5 Pass + 2 Skip-mit-
  Trigger-Pointer; Welle-5a-D-2 + D-4).
- [x] **C2 — NEU `docs/plan/planning/open/034-safe-004-max-
  age-stale-quality.md`** Trigger fuer `GG-SAFE-004` Lücke.
- [x] **C2 — NEU `docs/plan/planning/open/035-safe-003-comm-
  failure-missing-quality.md`** Trigger fuer `GG-SAFE-003`
  partial Lücke.
- [x] **C2 — NEU `docs/user/safe-001-004-quality-pipeline.
  md`** Audit-Tabelle (pro `GG-SAFE-00X`-ID: Akzeptanz +
  Substanz-Pfad + Test-Pfad + Status).
- [x] **C2 — Luecken-Adressierung** falls Audit Luecken
  aufdeckt (Welle-5a-D-3 Option B inline/Trigger).
- [x] **C2 — `make gates`** cache-frei gruen (10/10 A-1-
  Gates).
- [x] **C2 — `make ci`** cache-frei gruen.
- [x] **C2 — `make fullbuild`** cache-frei gruen.
- [x] **C3 — `M6-welle-5a.md`** Status `In Progress → Done
  2026-06-06` mit Liefer-Hash-Stack.
- [x] **C3 — `M6-perf-security-cicd.md §3.1`** Welle-5a-
  Zeile `In Progress → Done` mit Closure-Hash + Aktive-
  Welle-Block auf Welle 5b.
- [x] **C3 — `README.md` + `README.de.md`** NEU Quality-
  Pipeline-Audit-Hinweis falls relevant.
- [x] **C3 — `roadmap.md §3 M6`** aktive-Welle-Block auf
  M6-Welle-5b + Welle-5a-Abschluss-Notiz mit Stack-Range.
- [x] **C3 — `in-progress/README.md`** Bestand-Tabelle
  Welle-5a-Zeile auf `Done` + Aktive-Welle-Block auf
  M6-Welle-5b.
- [x] **C3 — `make docs-check`** cache-frei gruen.

**Anti-Scope-Verifikation (Welle 5a NICHT):**

- [x] Kein `GG-SAFE-007` Sim/Prod-Marker (Welle-5b-Scope).
- [x] Kein `GG-SAFE-008` Adapter-Input-Validation (Welle-
  5b-Scope).
- [x] Kein `GG-SAFE-005/006` SOLLTE-Items (Welle-5c-Scope).
- [x] Keine IP-/Netz-Beschraenkung (Welle-5c-Scope).
- [x] Keine neue Quality-Enum-Variante (M5-Welle-6b-Review
  F15 fixiert).
- [x] Keine NEU ADR (D-5).
- [x] Kein NEU Code im Core (Adapter-Side wenn ueberhaupt).

---

## References

- [`M6-welle-4b-c.md`](M6-welle-4b-c.md) —
  Welle-4b-c Backpressure-Healthcheck (abgeschlossen); Welle
  5a ist die naechste aktive Welle nach Welle-4-Subdivision-
  Komplett-Abschluss.
- [`../in-progress/M6-perf-security-cicd.md §3.2 Welle 5`](M6-perf-security-cicd.md)
  — M6-Slice-Plan Welle-5-Vorbelegung.
- [`../../../../spec/lastenheft.md §20 GG-SAFE-001..008`](../../../../spec/lastenheft.md)
  — Lastenheft-Akzeptanz fuer die Quality-Pipeline + Input-
  Validation + Sim/Prod-Trennung.
- [`../../adr/0014-battery-snapshot-schema.md`](../../adr/0014-battery-snapshot-schema.md)
  — Device-Quality-Emission-Pattern (analog ADR 0016/0017/
  0018).
- [`../../adr/0021-scenario-loader-and-tick-loop-event-wiring.md`](../../adr/0021-scenario-loader-and-tick-loop-event-wiring.md)
  — Scenario-Loader-Validierungs-Substanz.
- [`../../adr/0022-fault-injection-protocol.md`](../../adr/0022-fault-injection-protocol.md)
  + [`../../adr/0025-fault-recovery-pattern.md`](../../adr/0025-fault-recovery-pattern.md)
  — Fault-Injection-Alarm-Pattern (relevant fuer SAFE-003).
- M2-Welle-0a Trigger 014: `canonical_json`-NaN-Reject-
  Substanz.
