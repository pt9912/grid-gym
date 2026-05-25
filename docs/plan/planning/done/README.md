# Abgeschlossene Plaene

Dieses Verzeichnis sammelt Closure-Notizen zu abgeschlossenen
Meilensteinen und Plaenen.

Eine Closure-Notiz fasst zusammen:

- was wurde geliefert (Code, Specs, ADRs),
- welche Lastenheft-IDs sind damit umgesetzt,
- was wurde explizit nicht erledigt und wandert weiter (`open/` oder
  Folge-Meilenstein),
- Verweis auf Tag/Release im CHANGELOG.

## Bestand

| Datei                                          | Geschlossen | Gegenstand                                                                                          |
| ---------------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------- |
| `011-hexagon-layout-adr-0002-realign.md`       | 2026-05-15  | ADR-0002-Contracts an `hexagon/`-Gruppierung ausgerichtet (Pre-Spike-0).                            |
| `spike-0.md`                                   | 2026-05-15  | Spike-0 Pre-Acceptance fuer ADR 0002 + ADR 0005 (5 Wellen). Closure-Notiz §0.                       |
| `spike-0-results.md`                           | 2026-05-15  | Detail-Records zu Spike-0: Verstoss-Matrix (§3), Befunde (§4), Review-Trail (§6).                   |
| `001-code-review-doc.md`                       | 2026-05-15  | `docs/user/code-review.md` + `.github/PULL_REQUEST_TEMPLATE.md` (Trigger Drittes Review).            |
| `002-check-refs-tool.md`                       | 2026-05-17  | `tools/check_refs.py` als Querverweis-Linter (ADR 0004); Closure mit Welle-7-Audit-Fix.             |
| `003-random-port-adr.md`                       | 2026-05-17  | Trigger-Closure: ADR 0007 (`RandomPort`) `Accepted`; Port + Adapter + Tests geliefert.              |
| `009-tests-integration-compose.md`             | 2026-05-17  | `tests/integration/compose.yml` (testcontainers); Closure mit M1 Welle 6c.                           |
| `010-deploy-compose.md`                        | 2026-05-17  | `deploy/compose.yml` (Compose-Smoke + MVP-Demo); Closure mit M1 Welle 6c/6d.                         |
| `012-snapshot-composition.md`                  | 2026-05-17  | Snapshot-Composition fuer `SnapshotEnvelope`; Closure mit ADR-0010-Acceptance + M1-Welle-4.         |
| `M1-tick-loop-spine.md`                        | 2026-05-17  | M1-Slice-Plan Tick-Loop-Spine (Wellen 0..7); Closure-Hauptdokument.                                 |
| `M1-tick-loop-results.md`                      | 2026-05-17  | M1-Abschluss-Ergebnisse: `make fullbuild` Gruen (mit `CRITICAL_COV_TARGETS`-Override) + Welle-7-Erbschaft. |
| `013-replay-diff-tick-ms-parameter.md`         | 2026-05-18  | `diff_replay` `tick_ms`-Kwarg + Battery-Pflicht-Test; Closure in M2 Welle 2.                         |
| `014-generic-snapshot-format-codec.md`         | 2026-05-18  | Generischer Snapshot-/Format-Codec (Welle-5-Review-SC-3/SC-4-Erbe); Closure in M2 Welle 0a.         |
| `015-runtime-image-hardening.md`               | 2026-05-18  | Production-Image-Hardening (uv-`--no-editable`, Shebang-Rewrite, direkte Binaries); M2 Welle 0b.    |
| `M2-devices.md`                                | 2026-05-20  | M2-Slice-Plan Geraetemodelle; Closure-Hauptdokument.                                                |
| `M2-devices-results.md`                        | 2026-05-20  | M2-Abschluss-Ergebnisse: `make fullbuild` cache-frei gruen **ohne** Override seit Welle 6c.         |
| `welle-6c.md`                                  | 2026-05-20  | M2 Welle 6c: MVP-Demo-Szenario + E2E-Tests + Welle-6-Closure.                                       |
| `welle-7.md`                                   | 2026-05-20  | M2-Closure-Welle: Slice-Plan-Move (`git mv` M2-devices/welle-6c → done/) + M2-Closure-Inhalte.       |
| `welle-0.md`                                   | 2026-05-20  | M3 Welle 0: Slice-Plan-Eroeffnung + Trigger-Triage.                                                  |
| `welle-1.md`                                   | 2026-05-20  | M3 Welle 1: Fault-Foundation (`FaultPort` + `FaultInjectableDevice` + Validator-Haertung + TickLoop-Hook). |
| `welle-2.md`                                   | 2026-05-20  | M3 Welle 2: Battery- + Grid-Fault-Konkretisierung (`cell_failure`, `voltage_drop`, Recovery).        |
| `welle-3.md`                                   | 2026-05-21  | M3 Welle 3: Multi-Agent-Foundation (`Agent`-Protocol + `AgentMessageBus` + TickLoop-Hook).           |
| `welle-4a.md`                                  | 2026-05-21  | M3 Welle 4a: Multi-Agent-Foundation-Plumbing (Drain + Registry + Snapshot + Lifecycle).             |
| `welle-4b.md`                                  | 2026-05-22  | M3 Welle 4b: Multi-Agent-Konkretisierung (`RuleBasedAgent` + Scenario-`agents`-Block + Plugin-Hook + End-to-End-Demo). |
| `M3-welle-5.md`                                | 2026-05-23  | M3 Welle 5: Observability-Foundation (`LogPort`/`MetricsPort`/`TracePort` + `SpanContext` + Null-Adapter-Trio + additive TickLoop/Agent/Fault-Hooks; ADR 0024 Provisional + ADR 0029 Accepted Hygiene-Folge). Erste Welle-Doc unter `M{N}-welle-{X}.md`-Naming-Konvention. |
| `M3-welle-6.md`                                | 2026-05-25  | M3 Welle 6: OTLP-Adapter-Trio (gRPC) + `build_otlp_adapters`-Factory (C1), `deploy/compose.yml` `otel-collector`-Sibling + `tools/wait_otel_collector.py` + Trivy-Audit (C2), Integration-Smoke `tests/integration/test_otlp_compose_smoke.py` (Duo Metric+Log) + Runbook `docs/user/observability.md` (C3). Span-Sicht im Collector auf Trigger 029 verschoben (Adapter SDK-side korrekt). ADR 0024 §4.5 + `AC-OTLP-ADAPTER-NO-TIME` (13. arch_check-Contract). |
| `027-noqa-abbau.md`                            | 2026-05-24  | Slice 027 Noqa-Abbau: alle 36 bestehenden `# noqa`-Marker entfernt (Pakete A/E/C/B/D) und `tools/check_noqa.py --fail-on-noqa` als 9. A-1-Gate in `make gates` integriert. Neue Envelope-Types `LogEntry`/`OtlpAdapterConfigOverrides`/`TickLoopWiring`/`RuleBasedAgentConfig` + 15 typisierte Sub-Exception-Klassen. ADR 0024 §2.2 entsprechend geschaerft. |
| `028-tick-loop-private-error-import-contract.md` | 2026-05-25  | Slice 028 (Slice 027 Review-Folge L-5): neuer arch_check-Contract `AC-TICK-LOOP-PRIVATE-RESUME-ERRORS` (13. arch_check-Contract; 19 A-1-Contracts) verbietet `from grid_gym.hexagon.core.simulation.tick_loop import _<...>` ausserhalb des Moduls. Scope generisch auf alle modul-lokalen Underscore-Symbole; eine Whitelist-Ausnahme fuer den `test_loader_factory_sync.py`-Drift-Test (Welle-6b-Review L-1). |
| `025-github-actions-four-gates.md`             | 2026-05-25  | Slice 025 (M3-Vorzieh-Slice): `.github/workflows/ci.yml` mit vier parallelen Pflicht-Gates (`lint-imports`, `ruff check`, `arch-check-custom`, `mypy --strict`). Erster CI-Lauf `26237825003` am 2026-05-21 fuer `01796ae` gruen; alle ~30 Folge-Laeufe bis Closure-Zeitpunkt ebenfalls `success`. Voller CI/CD-Ausbau (`GG-CICD-001..00X`) bleibt M6-Material. |
