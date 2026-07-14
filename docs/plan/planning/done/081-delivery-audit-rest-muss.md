# 081 — Delivery-Audit: restliche `— | Trace`-MUSS (Verifikations-Slice)

**Status:** **Abgeschlossen (`done/`, 2026-07-14). Doku-only, kein Release.** Zweiter
**Verifikations-Slice** (Muster aus [`080`](080-delivery-audit-sim-replay.md)): auditiert
den **gesamten verbleibenden** `— | Trace`-**MUSS**-Satz (17 Anforderungen ohne
Liefervehikel in der doc-trace-`Slices`-Spalte) gegen Code + Test. **Ergebnis: 17/17
geliefert, 0 versteckte Lücken.** Verankert die IDs → doc-trace-Attribution (Slice 081).
**Datum:** 2026-07-14

---

## Zweck & Abgrenzung

Nach [`080`](080-delivery-audit-sim-replay.md) (Sim/Replay-Familie, 6/6) den **Rest** des
`— | Trace`-MUSS-Satzes in **einem** konsolidierten Durchgang schliessen (statt 5 Slices
pro Familie). Grund + Mechanik siehe [`080`](080-delivery-audit-sim-replay.md); Caveat:
die `Slices`-Spalte ist **referenz**-basiert (advisory), der belastbare Liefer-Status
steht in Code + Test — **dieser Slice zitiert genau den** (die Attribution ist Nebeneffekt).

## Audit (17 MUSS/MUESSEN)

| Anforderung | Verdict | Code-Artefakt | Test/Beleg |
| --- | --- | --- | --- |
| [`GG-ACCEPT-002`](../../../../spec/lastenheft.md#gg-accept-002) Dokumentierte Modellgrenzen | ✅ (Doku) | `README.md` + `spec/lastenheft.md`-Disclaimer, [`GG-NONGOAL-001`](../../../../spec/lastenheft.md#gg-nongoal-001)/[`GG-SAFE-007`](../../../../spec/lastenheft.md#gg-safe-007) | Doku-Anforderung: Disclaimer-Existenz (kein Code-Test) |
| [`GG-BESS-003`](../../../../spec/lastenheft.md#gg-bess-003) Wirkungsgrade | ✅ | `hexagon/core/devices/battery/model.py` (charge/discharge-Effizienz) | `tests/unit/hexagon/core/devices/battery/` |
| [`GG-DEMO-003`](../../../../spec/lastenheft.md#gg-demo-003) Demo-Batterie | ✅ | `deploy/scenarios/gg-demo.yaml` (Battery-Device) | `tests/integration/test_m5_welle_5_demo_smoke.py` |
| [`GG-DEMO-004`](../../../../spec/lastenheft.md#gg-demo-004) Demo-Live-Telemetrie | ✅ | UI-Dashboard (`hexagon/adapters`-UI + WS-Stream, Slice 078-Fix) | `tests/unit/adapters/driving/ui/test_dashboard.py` |
| [`GG-DEPLOY-002`](../../../../spec/lastenheft.md#gg-deploy-002) Offline-Betrieb | ✅ | `deploy/compose.yml` + `Dockerfile` (Docker-only, keine Runtime-Netz-Abhängigkeit) | Compose-Smoke (`make fullbuild`) |
| [`GG-DEPLOY-003`](../../../../spec/lastenheft.md#gg-deploy-003) Linux-Deployment | ✅ | `Dockerfile` (Linux-Base, distroless-Runtime) | CI/`make fullbuild` (Linux-Runner) |
| [`GG-DEV-002`](../../../../spec/lastenheft.md#gg-dev-002) Geräte-Telemetrie-Export | ✅ | `hexagon/core/simulation/tick_loop.py` (`TickResult.emitted_telemetry`) + `core/domain/telemetry.py` | `tests/unit/hexagon/core/domain/` |
| [`GG-DEV-013`](../../../../spec/lastenheft.md#gg-dev-013) Lastprofil-Simulation | ✅ | `hexagon/core/grid_model/loads.py` (`LoadProfile`) | `tests/unit/hexagon/core/grid_model/test_loads.py` |
| [`GG-FAULT-007`](../../../../spec/lastenheft.md#gg-fault-007) Geräteausfälle | ✅ | Fault-Framework + `connection_loss`/`cell_failure`/`genset_fault`/`winding_fault` (Start/Dauer/Ziel) | `tests/unit/hexagon/core/faults/` |
| [`GG-GRID-002`](../../../../spec/lastenheft.md#gg-grid-002) Spannungsabweichungen | ✅ | `hexagon/core/grid_model/bilanz.py` (`v = v_nom + k_v·imbalance`) | `tests/unit/hexagon/core/grid_model/` |
| [`GG-OTEL-002`](../../../../spec/lastenheft.md#gg-otel-002) Strukturierte Logs | ✅ | `hexagon/ports/driven/observability.py` (`LogPort`) + `adapters/driven/telemetry_otlp/` | `tests/integration/test_otlp_compose_smoke.py` |
| [`GG-OTEL-003`](../../../../spec/lastenheft.md#gg-otel-003) Metrik-Export | ✅ | `hexagon/ports/driven/observability.py` (`MetricsPort`) + `adapters/driven/telemetry_otlp/` | `tests/integration/test_otlp_compose_smoke.py` |
| [`GG-PERSIST-002`](../../../../spec/lastenheft.md#gg-persist-002) Replay-Daten-Persistenz | ✅ | `adapters/driven/persistence_postgres/replay_snapshot_repository.py` + `telemetry_sink_repository.py` | `tests/integration/test_postgres_run_repository.py` |
| [`GG-PERSIST-008`](../../../../spec/lastenheft.md#gg-persist-008) Versionierte DB-Migrationen | ✅ | `alembic.ini` + `adapters/driven/persistence_postgres/migrations/` | Postgres-Integration-Smoke |
| [`GG-SCN-004`](../../../../spec/lastenheft.md#gg-scn-004) Exportierbare Szenarien | ✅ | Scenario-Store/Intake ([`ADR 0069`](../../adr/0069-multi-run-execution-and-scenario-store.md), `composition/scenario_intake.py`) | `tests/unit/composition/test_scenario_intake.py` |
| [`GG-SCN-005`](../../../../spec/lastenheft.md#gg-scn-005) Zeitbasierte Ereignisse | ✅ | `hexagon/core/grid_model/loads.py` (`LoadEvent`) + scheduled Commands ([`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md)) | `tests/unit/hexagon/core/grid_model/test_loads.py` |
| [`GG-SCN-006`](../../../../spec/lastenheft.md#gg-scn-006) Szenario-Fault-Injection | ✅ | `hexagon/core/scenario/validator.py` (`faults`-Block) + `core/faults/` | `tests/unit/hexagon/core/faults/` |

## Befund

- **17/17 erfüllt, 0 versteckte funktionale Lücken.** Zusammen mit [`080`](080-delivery-audit-sim-replay.md)
  (6/6) ist damit der **komplette `— | Trace`-MUSS-Satz** gegen Code+Test verifiziert —
  kein zweites GG-FAULT-artiges Loch. Die „—"-Slices-Spalte war reine **Attributions-**Lücke
  (M1..M8-Lieferung ohne ID-Nennung in Planning-Docs), keine Liefer-Lücke.
- **Modalitäts-Korrektur:** die drei Scenario-Anforderungen im Audit sind **MUESSEN**
  (nicht KANN — die Anforderungssätze sagen „Szenarien MUESSEN …").
- Die **Modellgrenzen-Anforderung** ([`GG-ACCEPT-002`](../../../../spec/lastenheft.md#gg-accept-002))
  ist eine **Doku-Anforderung** — erfüllt durch die „Nur Simulation"-Disclaimer, kein Code-Test.

## DoD

- Jede der 17 MUSS hat ein Code- **und** Test-Artefakt (bzw. Doku-Beleg für die
  Doku-Anforderung). ✅
- IDs im `done/`-Doc verankert → `make doc-trace` attribuiert Slice 081. ✅ (verifiziert)
- Doku-only, **kein Runtime-Delta → kein Release**.

## Bezug

- Muster + Caveat: [`080`](080-delivery-audit-sim-replay.md),
  [`docs/plan/traceability.md`](../../traceability.md) (§27, `Slices`-Spalte advisory),
  [`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) (slice-getrieben).
- Offen: der `— | Trace`-**SOLLTE/KANN**-Rest (niedrigere Priorität) + der
  d-check-`modality`-Bump (RTM-Prioritäts-Spalte, braucht neuere d-check-Version).
