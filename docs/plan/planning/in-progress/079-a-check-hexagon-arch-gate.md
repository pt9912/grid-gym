# 079 — a-check Hexagon-Architektur-Gate adoptieren (+ Port-Extraktion)

**Status:** In Arbeit (`in-progress/`, 2026-07-14). T0 (Plan) angelegt; T1–T4 offen.
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
