# 079 — a-check Hexagon-Architektur-Gate adoptieren (+ Port-Extraktion)

**Status:** **Abgeschlossen (`done/`, 2026-07-14). Released als v0.8.0.** T1–T4 done; a-check
als Gate verdrahtet (**0 Befunde**); `make gates` grün (11 Gates inkl. a-check), **volle
Integration-Suite 171 passed / 4 skip** (IEC-61850-Python-Skips), `make fullbuild` grün.
[`ADR 0079`](../../adr/0079-a-check-arch-gate-and-port-extraction.md) `Accepted`.
**Datum:** 2026-07-14
**Quelle:** Roadmap-Trigger „neues `a-check`-Tool" (sprachagnostischer Hexagon-
Architektur-Validator, [`ghcr.io/pt9912/a-check`](https://github.com/pt9912/a-check),
Schwester-Werkzeug zu d-check). Baseline-Lauf gegen grid-gym: 7 `lateral-adapter`-
Befunde (Driving-Adapter `http_api` importiert driven-Adapter). User-Entscheid
(2026-07-14): **wirklich alles** refaktorieren, damit a-check clean + hartes Gate wird.

---

## Ziel

a-check als **komplementäres** Architektur-Gate adoptieren (zusätzlich zu
import-linter [`ADR 0002`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) +
`tools/arch_check.py`): sprachagnostische Schicht-/Richtungs-Reinheit, hermetisch
(Docker, `--network none`, read-only). a-checks `lateral-adapter`-Regel (Adapter→
anderer Adapter) surfaced eine Kopplung, die import-linter nicht prüft. Der
Baseline-Lauf (faithful Schicht-Mapping domain/app/ports/adapters) meldet **7
Befunde in einem Thema**: der `http_api`-Driving-Adapter importiert vier driven-
Adapter. Zwei Kategorien:

- **Kat. A — Typ-only-Referenzen (4):** `AlarmHistoryBuffer` (`_dependencies.py`,
  `_alarm_setup.py`, `_tick_loop_driver.py`) + `BessEmsFieldPublishAdapter`
  (`_tick_loop_driver.py`). Beide sind heute bewusst port-lose Adapter-Typen
  ([`ADR 0040`](../../adr/0040-alarm-aggregation-and-stream-port.md) Decision 17
  „kein Port" für `AlarmHistoryBuffer`; [`ADR 0078`](../../adr/0078-bess-ems-field-contract-publisher.md)-
  Publisher mit `publish_tick`-Surface ≠ `FieldPublishPort`).
- **Kat. B — echtes Wiring (3):** `app.py` instanziiert `InMemoryRunRepository`/
  `InMemoryTelemetryStream`/`InMemoryAlarmStream`/`AlarmHistoryBuffer` im env-Demo-
  Bootstrap (Composition-im-Adapter) + `isinstance`-Lifespan-Guards.

User-Entscheid **wirklich alles**: Kat. A per **zwei neuen Driven-Ports** auflösen
(statt `ignore_symbols`), Kat. B per **Hook-Inversion** in den Composition-Root.

## Tranchen-Schnitt

| Tranche | Inhalt | ADR-Bezug | Rolle |
| --- | --- | --- | --- |
| **T0** | Dieses Planning-Doc + Roadmap-Eintrag; `.a-check.yml`-Entwurf (faithful Mapping). | — | Planner |
| **T1** | **`AlarmHistoryPort`** (Driven-Port `append`/`get_recent`); `AlarmHistoryBuffer` erfüllt ihn (strukturell, `@runtime_checkable`); Typ-Refs in `_dependencies.py`/`_alarm_setup.py`/`_tick_loop_driver.py` → Port. | [`ADR 0079`](../../adr/0079-a-check-arch-gate-and-port-extraction.md) Decision A (Schärfung [`ADR 0040`](../../adr/0040-alarm-aggregation-and-stream-port.md) Decision 17, Muster [`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md)) | Architect + Implementation |
| **T2** | **`FieldFramePublishPort`** (Driven-Port `start`/`publish_tick(TickResult)`/`stop`); `BessEmsFieldPublishAdapter` erfüllt ihn; Provider-Alias in `_tick_loop_driver.py` → Port. | [`ADR 0079`](../../adr/0079-a-check-arch-gate-and-port-extraction.md) Decision B (Schärfung [`ADR 0078`](../../adr/0078-bess-ems-field-contract-publisher.md)) | Architect + Implementation |
| **T3** | **Kat.-B-Inversion:** env-Demo-Instanziierung + Demo-Generator-Lifecycle aus `app.py` per Registrier-Hook in `composition/asgi.py` (Muster `_register_scenario_configurator`); Verhalten + Welle-5-Guards (F5/F9/F11) erhalten. | [`ADR 0079`](../../adr/0079-a-check-arch-gate-and-port-extraction.md) Decision C | Implementation |
| **T4** | Finale `.a-check.yml` (ohne `ignore_symbols`); `a-check.mk`-Include + `A_CHECK_IMAGE`-Digest-Pin; `make a-check`; ins lokale `docs-check`/`arch-check`-Gate + CI hängen; **a-check 0 Befunde** verifizieren; Docs (ADR-Index, README, CHANGELOG); Closure. | [`ADR 0079`](../../adr/0079-a-check-arch-gate-and-port-extraction.md) Decision (Gate) | Implementation + Verifier |

## DoD

- **a-check clean:** `make a-check` meldet 0 Befunde auf dem faithful Schicht-Mapping
  (domain/app/ports/adapters); als Gate verdrahtet (digest-gepinntes Image).
- **Port-Extraktion:** `http_api`-Adapter importiert keine driven-Adapter mehr — weder
  Typ (Kat. A via `AlarmHistoryPort`/`FieldFramePublishPort`) noch Instanz (Kat. B via
  Composition-Root).
- **Additiv/verhaltensgleich:** Demo-Run, Telemetry-Stream, Alarm-History-REST und
  bess-ems-Publish funktionieren unverändert; `make gates` + `arch-check` (import-linter)
  + `make a-check` + `make fullbuild` grün. Determinismus-/Demo-Golden unberührt
  (T3 berührt nur Wiring-Ort, nicht Simulationslogik).
- **ADR:** [`ADR 0079`](../../adr/0079-a-check-arch-gate-and-port-extraction.md) `Accepted`;
  [`ADR 0040`](../../adr/0040-alarm-aggregation-and-stream-port.md) +
  [`ADR 0078`](../../adr/0078-bess-ems-field-contract-publisher.md) geschärft (nicht abgelöst).
- **Release-Entscheidung:** Runtime-Delta (neue Ports + Wiring-Refactor, additiv, kein
  Vertrags-/Determinismus-Bruch) → Minor-Release-Kandidat; Entscheidung bei Closure.

## Bezug

- [`ADR 0002`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) §A-1
  (import-linter/arch-check-Gate), [`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md)
  (Schärfung ohne Ablösung), [`ADR 0040`](../../adr/0040-alarm-aggregation-and-stream-port.md)
  (AlarmHistoryBuffer „kein Port"), [`ADR 0078`](../../adr/0078-bess-ems-field-contract-publisher.md)
  (bess-ems-Publisher).
- a-check-Handbuch: `github.com/pt9912/a-check/docs/user/benutzerhandbuch.md`.
- Muster-Vorlage: d-check-Adoption (Trigger 002 / `d-check.mk`-Include).

## Verification (2026-07-14)

**Role:** Verifier. **Input:** Slice-DoD, Diff T0–T4, Sensor-Ausgaben.

- **a-check (Gate-Kernnachweis):** `make a-check` (digest-gepinnt `@sha256:203df7ab…` via
  `a-check.mk`) → **0 Befunde** auf dem faithful Schicht-Mapping. Baseline 7 (`lateral-adapter`);
  T1 → 4 (3 Alarm-Kat-A gecleart), T2 → 3 (bess-ems gecleart), T3 → 0 (app.py-Kat-B invertiert).
- **`make gates` grün** (getrennte Läufe T1+T2 `81f67ad` und T3 `09834186`): lint, format-check,
  typecheck (mypy --strict), arch-check (20 import-linter/`arch_check.py`-Contracts — komplementär
  weiter grün), test-unit (2734), coverage-gate (93.86 % line / 89 % branch),
  coverage-gate-critical, dep-audit, noqa-gate, spdx-check. **a-check ist jetzt Teil des
  `gates`-Verbunds** (am arch-check-Verbund, [`ADR 0079`](../../adr/0079-a-check-arch-gate-and-port-extraction.md) §2.1)
  + eigener CI-Job in `ci.yml`.
- **Volle Integration-Suite grün:** 171 passed / 4 skipped (die 4 = IEC-61850-Python-Version-
  Skips, [`ADR 0046`](../../adr/0046-multi-python-test-stage-pattern.md)). Enthält den
  **Demo-Smoke** (`test_m5_welle_5_demo_smoke`), der den env-getriebenen Lifespan-Pfad über den
  neuen `_demo_stack`-Builder-Hook end-to-end fährt → die Composition-Root-Inversion ist
  **verhaltensgleich**.
- **Port-Extraktion belegt:** `grep` bestätigt — der `http_api`-Adapter importiert keinen
  driven-Adapter mehr (weder Typ noch Instanz); Rest-Vorkommen sind Docstrings/Fehlerklassen-Namen.
- **`make fullbuild` grün:** „full closure: ci + runtime image + compose smoke green" (exit 0)
  — validiert das a-check-Gate im vollen `gates`-/`ci`-Verbund + Runtime-Image + Compose-Smoke.

**Open risks:** keiner offen. a-checks Richtungs-Regeln (`port-direction-mismatch` via
explizite `direction: driving/driven`) sind bewusst **nicht** aktiviert (Schichten ohne
`direction`) — Trigger-Kandidat ([`ADR 0079`](../../adr/0079-a-check-arch-gate-and-port-extraction.md) §3).
**Next role:** Planner (Release-Entscheidung: Runtime-Delta additiv/verhaltensgleich → Patch/Minor).
