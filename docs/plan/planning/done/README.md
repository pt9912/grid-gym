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
| [`011-hexagon-layout-adr-0002-realign.md`](011-hexagon-layout-adr-0002-realign.md)       | 2026-05-15  | ADR-0002-Contracts an `hexagon/`-Gruppierung ausgerichtet (Pre-Spike-0).                            |
| [`spike-0.md`](spike-0.md)                                   | 2026-05-15  | Spike-0 Pre-Acceptance fuer ADR 0002 + ADR 0005 (5 Wellen). Closure-Notiz §0.                       |
| [`spike-0-results.md`](spike-0-results.md)                           | 2026-05-15  | Detail-Records zu Spike-0: Verstoss-Matrix (§3), Befunde (§4), Review-Trail (§6).                   |
| [`001-code-review-doc.md`](001-code-review-doc.md)                       | 2026-05-15  | `docs/user/code-review.md` + `.github/PULL_REQUEST_TEMPLATE.md` (Trigger Drittes Review).            |
| [`002-check-refs-tool.md`](002-check-refs-tool.md)                       | 2026-05-17  | `tools/check_refs.py` als Querverweis-Linter (ADR 0004); Closure mit Welle-7-Audit-Fix.             |
| [`003-random-port-adr.md`](003-random-port-adr.md)                       | 2026-05-17  | Trigger-Closure: ADR 0007 (`RandomPort`) `Accepted`; Port + Adapter + Tests geliefert.              |
| [`009-tests-integration-compose.md`](009-tests-integration-compose.md)             | 2026-05-17  | `tests/integration/compose.yml` (testcontainers); Closure mit M1 Welle 6c.                           |
| [`010-deploy-compose.md`](010-deploy-compose.md)                        | 2026-05-17  | `deploy/compose.yml` (Compose-Smoke + MVP-Demo); Closure mit M1 Welle 6c/6d.                         |
| [`012-snapshot-composition.md`](012-snapshot-composition.md)                  | 2026-05-17  | Snapshot-Composition fuer `SnapshotEnvelope`; Closure mit ADR-0010-Acceptance + M1-Welle-4.         |
| [`M1-tick-loop-spine.md`](M1-tick-loop-spine.md)                        | 2026-05-17  | M1-Slice-Plan Tick-Loop-Spine (Wellen 0..7); Closure-Hauptdokument.                                 |
| [`M1-tick-loop-results.md`](M1-tick-loop-results.md)                      | 2026-05-17  | M1-Abschluss-Ergebnisse: `make fullbuild` Gruen (mit `CRITICAL_COV_TARGETS`-Override) + Welle-7-Erbschaft. |
| [`013-replay-diff-tick-ms-parameter.md`](013-replay-diff-tick-ms-parameter.md)         | 2026-05-18  | `diff_replay` `tick_ms`-Kwarg + Battery-Pflicht-Test; Closure in M2 Welle 2.                         |
| [`014-generic-snapshot-format-codec.md`](014-generic-snapshot-format-codec.md)         | 2026-05-18  | Generischer Snapshot-/Format-Codec (Welle-5-Review-SC-3/SC-4-Erbe); Closure in M2 Welle 0a.         |
| [`015-runtime-image-hardening.md`](015-runtime-image-hardening.md)               | 2026-05-18  | Production-Image-Hardening (uv-`--no-editable`, Shebang-Rewrite, direkte Binaries); M2 Welle 0b.    |
| [`M2-devices.md`](M2-devices.md)                                | 2026-05-20  | M2-Slice-Plan Geraetemodelle; Closure-Hauptdokument.                                                |
| [`M2-devices-results.md`](M2-devices-results.md)                        | 2026-05-20  | M2-Abschluss-Ergebnisse: `make fullbuild` cache-frei gruen **ohne** Override seit Welle 6c.         |
| [`welle-6c.md`](welle-6c.md)                                  | 2026-05-20  | M2 Welle 6c: MVP-Demo-Szenario + E2E-Tests + Welle-6-Closure.                                       |
| [`welle-7.md`](welle-7.md)                                   | 2026-05-20  | M2-Closure-Welle: Slice-Plan-Move (`git mv` M2-devices/welle-6c → done/) + M2-Closure-Inhalte.       |
| [`welle-0.md`](welle-0.md)                                   | 2026-05-20  | M3 Welle 0: Slice-Plan-Eroeffnung + Trigger-Triage.                                                  |
| [`welle-1.md`](welle-1.md)                                   | 2026-05-20  | M3 Welle 1: Fault-Foundation (`FaultPort` + `FaultInjectableDevice` + Validator-Haertung + TickLoop-Hook). |
| [`welle-2.md`](welle-2.md)                                   | 2026-05-20  | M3 Welle 2: Battery- + Grid-Fault-Konkretisierung (`cell_failure`, `voltage_drop`, Recovery).        |
| [`welle-3.md`](welle-3.md)                                   | 2026-05-21  | M3 Welle 3: Multi-Agent-Foundation (`Agent`-Protocol + `AgentMessageBus` + TickLoop-Hook).           |
| [`welle-4a.md`](welle-4a.md)                                  | 2026-05-21  | M3 Welle 4a: Multi-Agent-Foundation-Plumbing (Drain + Registry + Snapshot + Lifecycle).             |
| [`welle-4b.md`](welle-4b.md)                                  | 2026-05-22  | M3 Welle 4b: Multi-Agent-Konkretisierung (`RuleBasedAgent` + Scenario-`agents`-Block + Plugin-Hook + End-to-End-Demo). |
| [`M3-welle-5.md`](M3-welle-5.md)                                | 2026-05-23  | M3 Welle 5: Observability-Foundation (`LogPort`/`MetricsPort`/`TracePort` + `SpanContext` + Null-Adapter-Trio + additive TickLoop/Agent/Fault-Hooks; ADR 0024 Provisional + ADR 0029 Accepted Hygiene-Folge). Erste Welle-Doc unter `M{N}-welle-{X}.md`-Naming-Konvention. |
| [`M3-welle-6.md`](M3-welle-6.md)                                | 2026-05-25  | M3 Welle 6: OTLP-Adapter-Trio (gRPC) + `build_otlp_adapters`-Factory (C1), `deploy/compose.yml` `otel-collector`-Sibling + `tools/wait_otel_collector.py` + Trivy-Audit (C2), Integration-Smoke `tests/integration/test_otlp_compose_smoke.py` (volles Tripel Span+Metric+Log nach Trigger-029-Closure) + Runbook `docs/user/observability.md` (C3). ADR 0024 §4.5 + `AC-OTLP-ADAPTER-NO-TIME` (12. arch_check-Contract; 13. ist `AC-TICK-LOOP-PRIVATE-RESUME-ERRORS` aus Slice 028). |
| [`027-noqa-abbau.md`](027-noqa-abbau.md)                            | 2026-05-24  | Slice 027 Noqa-Abbau: alle 36 bestehenden `# noqa`-Marker entfernt (Pakete A/E/C/B/D) und `tools/check_noqa.py --fail-on-noqa` als 9. A-1-Gate in `make gates` integriert. Neue Envelope-Types `LogEntry`/`OtlpAdapterConfigOverrides`/`TickLoopWiring`/`RuleBasedAgentConfig` + 15 typisierte Sub-Exception-Klassen. ADR 0024 §2.2 entsprechend geschaerft. |
| [`028-tick-loop-private-error-import-contract.md`](028-tick-loop-private-error-import-contract.md) | 2026-05-25  | Slice 028 (Slice 027 Review-Folge L-5): neuer arch_check-Contract `AC-TICK-LOOP-PRIVATE-RESUME-ERRORS` (13. arch_check-Contract; 19 A-1-Contracts) verbietet `from grid_gym.hexagon.core.simulation.tick_loop import _<...>` ausserhalb des Moduls. Scope generisch auf alle modul-lokalen Underscore-Symbole; eine Whitelist-Ausnahme fuer den `test_loader_factory_sync.py`-Drift-Test (Welle-6b-Review L-1). |
| [`029-otlp-span-grpc-export-edge-case.md`](029-otlp-span-grpc-export-edge-case.md)       | 2026-05-25  | Trigger 029 als **Fehlbefund** geschlossen: der OTLP-Span-Export-Pfad war nie kaputt. Die ursprueng-beobachteten „0 Spans im Collector" lagen am Span-Name-Regex (`^Name` ohne Leading-Whitespace) im Smoke-Test — Debug-Exporter-Output ist `    Name           : tick.cycle` mit 4-Leerzeichen-Padding. Fix: `^\s*Name\s*:`. `tools/diagnose_otlp_span_export.py` bleibt als Pattern fuer OTLP-Debugging, `service.telemetry.metrics`-Endpunkt + tmpfs-`mode=1777` bleiben als nuetzliche Nebenbefunde aktiv. |
| [`025-github-actions-four-gates.md`](025-github-actions-four-gates.md)             | 2026-05-25  | Slice 025 (M3-Vorzieh-Slice): `.github/workflows/ci.yml` mit vier parallelen Pflicht-Gates (`lint-imports`, `ruff check`, `arch-check-custom`, `mypy --strict`). Erster CI-Lauf `26237825003` am 2026-05-21 fuer `01796ae` gruen; alle ~30 Folge-Laeufe bis Closure-Zeitpunkt ebenfalls `success`. Voller CI/CD-Ausbau (`GG-CICD-001..00X`) bleibt M6-Material. |
| [`M3-faults-agents-observability.md`](M3-faults-agents-observability.md) | 2026-05-25  | M3-Slice-Plan: Fault-Injection + Multi-Agent-Bus + Observability ueber Welle 0..7 (drei Sub-Bereiche). Closure-Hauptdokument; Detail-Ergebnisse in `M3-results.md`. |
| [`M3-welle-7.md`](M3-welle-7.md)                                | 2026-05-25  | M3-Closure-Welle: sechs M3-ADRs (0022..0027) `Provisional → Accepted` (C1.1..C1.6); Trigger-006-Decision (C2, verschoben); `M3-results.md` + `roadmap.md` M3 → `Done` + Trigger 030 RL-Adapter (C3); S-1..S-6-End-to-End-Sweep (C4, ausgewertet in `M3-results.md §4`); Slice-Plan-Sync (C5); `make fullbuild`-Sanity (C6); End-of-Wave-Move beider Dokumente nach `done/`. |
| [`M3-results.md`](M3-results.md)                                | 2026-05-25  | M3-Abschluss-Ergebnisse: Welle-Tabelle (Welle 0..7), Abnahme-Belege (`make fullbuild` cache-frei gruen ohne Override seit Welle-6-C2 `c61ab0d`; 1138 Unit-Tests + 21 Integration-Tests; 96 % Total-Coverage; 19 A-1-Contracts), Pro-Welle-Reviews, S-1..S-6-Verification, Welle-7-Erbschaft fuer M4+/M5+/M6+, M3-Wandert-Nach, Nicht-vollzogene Items. |
