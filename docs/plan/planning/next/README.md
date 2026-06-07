# Next

Plan- und Slice-Notizen fuer **konkret geplante, aber noch nicht
aktive** Arbeit.

## Bestand

| Datei                                                                 | Gegenstand |
| --------------------------------------------------------------------- | ---------- |
| [`replay-source-integration.md`](replay-source-integration.md) | `GG-MVP-002` Closure-Plan: `ReplaySourcePort`-Adapter + `replay_diff_status`-Metrik + Core-Spine-Lifecycle-Hook; aktiviert die [Trigger 036](../open/036-safe-006-replay-diff-status-replay-source-integration.md)-Substanz-Skizze zu einem konkreten Welle-X-Slice. Geschaetzter Aufwand 4-5 Tage. Aktivierungs-Bedingungen siehe §5 des Plans. |
| [`abnahme-cli.md`](abnahme-cli.md) | `GG-MVP-003` Closure-Plan: NEU `make accept` + `tools/accept.py` (inkl. Headless-TickLoop-Runner-Helper als Baseline-Substanz) mit drei Sub-Steps (Szenario-Validierung + deterministischer Replay + `/ready`-Healthcheck) + `AbnahmeReport` JSON-Schema (Pydantic-strict). Bevorzugt als M6-Welle-6-Scope-Erweiterung; alternativ eigener Welle-6b-Slice oder M7+. Geschaetzter Aufwand 1.5-2.5 Tage zusaetzlich zur Welle 6. Aktivierungs-Bedingungen siehe §5 des Plans. |
