# Offene Plaene und Trigger-Watch

Dieses Verzeichnis sammelt **trigger-getriebene Folgearbeit** und
**Vorabklaerungen**, die noch nicht in die aktive Roadmap aufgenommen
wurden.

Eintraege wandern entweder:

- nach `next/`, sobald ein Scope skizziert ist, aber noch kein Slice aktiv,
- nach `in-progress/`, wenn sie direkt aktiviert werden, oder
- nach `archive/`, wenn sie bewusst verworfen werden.

Aufgeloeste Trigger werden mit der aufloesenden Slice-Closure
nach [`../done/`](../done/) verschoben (rename-only) und sind
dort in der `done/`-Bestand-Tabelle gelistet — nicht hier.

---

## Bestand

Alle Eintraege sind Trigger-Watch-Notizen (`Status: Open`) ohne
harten Aktivierungs-Zwang. Die `Aktivierung`-Spalte beschreibt den
konkreten Anlass, der eine Aktivierung ausloesen soll.

**Tooling / Build / Type-System:**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`004-canonical-encoder-alternative-adr.md`](004-canonical-encoder-alternative-adr.md) | ADR fuer Performance-/Implementierungs-Alternativen (orjson, msgspec) | bei messbarem Perf-Druck am Telemetrie-Pfad |
| [`005-pyright-vs-mypy-reeval.md`](005-pyright-vs-mypy-reeval.md) | Re-Eval mypy vs. pyright bei generischen Protocols | sobald `ports/*` Generic-Protocols einfuehrt |
| [`007-pyright-precommit-adr.md`](007-pyright-precommit-adr.md) | ADR fuer pyright als Pre-Commit-Hook | bei Editor-Parity-Druck |
| [`009-iec61850-smoke-reactivation.md`](009-iec61850-smoke-reactivation.md) | IEC-61850 In-Process-Smoke reaktivieren (`tests/integration/test_iec61850_in_process_smoke.py`-Skip aufheben) | pyiec61850-ng publishet cp314-Manylinux-Wheel (Pfad A) ODER Pfad-B-Slice (Multi-Python-Test-Stage) wird angepackt |
| [`032-release-workflow-sensor-run.md`](032-release-workflow-sensor-run.md) | Reale GitHub-Actions-Release-Workflow-Run-Verifikation (GHCR-Push + Release-Create + Multi-Job-Artifact-Sharing) | erster echter `v*.*.*`-Tag-Push ODER Compliance-Druck |
| [`033-otel-collector-go-stdlib-cve-bump.md`](033-otel-collector-go-stdlib-cve-bump.md) | OTel-Collector Go-stdlib CVE-2026-42504-Bump (ADR-0043-konformer Defer-Pfad ueber ADR-0044-vulnignore-Pattern) | OTel-Collector-Release > 0.153.0 mit `go1.26.4+`-Build ODER Compliance-Druck |

**M3-/Multi-Agent-Folge:**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`011-mlrandomport-subseed-width.md`](011-mlrandomport-subseed-width.md) | `MLRandomPort` Sub-Seed-Wortbreite (ADR 0007 §5.2/§6) | bei `> 10⁶` Sub-Ports / hochskalierter Multi-Agent-Welle |
| [`026-bess-simulation-reserve-market-spike.md`](026-bess-simulation-reserve-market-spike.md) | Lokale BESS-Simulation als Vorlage fuer Reserve-Market-/LER-Strategien | bei Reserve-Market-Agent, BESS-SOC-Management-Agent oder LER-Demo |
| [`030-rl-adapter.md`](030-rl-adapter.md) | RL-Adapter ueber den Multi-Agent-Bus (`GG-FUTURE-001/002`) | bei konkreter RL-Stakeholder-Anforderung (M7+-Material) |

**Quality-/Determinismus-Lücken (M6-Welle-5a/5c-Audit-Folge):**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`034-safe-004-max-age-stale-quality.md`](034-safe-004-max-age-stale-quality.md) | `GG-SAFE-004` max_age-basierte `STALE`-Quality-Markierung; Substanz fehlt komplett im Repository | eigener Slice ueber TickLoop-Quality-Stage + `max_age`-Konfigurationsfeld + Smoke-Reaktivierung |
| [`035-safe-003-comm-failure-missing-quality.md`](035-safe-003-comm-failure-missing-quality.md) | `GG-SAFE-003` Adapter-Kommunikationsausfall → `MISSING`/`STALE` + Alarm-Emission (partial Lücke) | eigener Slice ueber Adapter-Lifecycle-Hook + Quality-Emission im Connection-Lost-Pfad |
| [`036-safe-006-replay-diff-status-replay-source-integration.md`](036-safe-006-replay-diff-status-replay-source-integration.md) | `GG-SAFE-006` Per-Lauf-Status-Marker `replay_diff_status` (Architektur §8.2 Z. 820 + 823) + `ReplaySourcePort`-Verkabelung mit `diff_replay()` (Lastenheft Z. 2292) — partial Lücke (Core-Diff ✓ produktiv) | `GG-REPLAY-004..006`-Aktivierung in M3+ ODER CI-Bench-Determinismus-Drift |

**SOLLTE — M2-Welle-7-Erbschaft** (Quelle: [`../done/M2-devices.md`](../done/M2-devices.md) §4 Out-of-Scope):

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`016-sollte-ev-charger-device.md`](016-sollte-ev-charger-device.md) | EV-Charger-Device (`GG-DEV-015`, Lastenheft §9.4) | wenn konkreter Bedarf — eigener Slice |
| [`017-sollte-transformer-device.md`](017-sollte-transformer-device.md) | Transformer-Device (`GG-DEV-016`, Lastenheft §9.4) | wenn konkreter Bedarf — eigener Slice |
| [`018-sollte-wind-device.md`](018-sollte-wind-device.md) | Wind-Device (`GG-DEV-017`, Lastenheft §9.4) | wenn konkreter Bedarf — eigener Slice |
| [`019-sollte-diesel-device.md`](019-sollte-diesel-device.md) | Diesel-Device (`GG-DEV-018`, Lastenheft §9.4) | wenn konkreter Bedarf — eigener Slice |
| [`020-sollte-island-grid.md`](020-sollte-island-grid.md) | Inselnetz-Bilanzmodell (`GG-GRID-005`, Lastenheft §11.5) | wenn konkreter Bedarf — eigener Slice |
| [`021-sollte-transformer-limits.md`](021-sollte-transformer-limits.md) | Transformatorgrenzen im Netzbilanzmodell (`GG-GRID-006`, Lastenheft §11.5) | wenn konkreter Bedarf — eigener Slice |
| [`022-sollte-reactive-power.md`](022-sollte-reactive-power.md) | Blindleistung im Netzbilanzmodell (`GG-GRID-007`, Lastenheft §11.5) | wenn konkreter Bedarf — eigener Slice |
| [`023-sollte-battery-temperature.md`](023-sollte-battery-temperature.md) | Battery-Temperatur-Telemetry (`GG-BESS-006`, Lastenheft §10.6) | wenn konkreter Bedarf — eigener Slice |
| [`024-sollte-battery-cell-voltage.md`](024-sollte-battery-cell-voltage.md) | Battery-Zellspannung-Telemetry (`GG-BESS-007`, Lastenheft §10.6) | wenn konkreter Bedarf — eigener Slice |

Architektonische offene Punkte (`GG-AR-OPEN-002..010`) leben weiterhin
in `architecture.md` §19 und sind dort die kanonische Liste. Wenn
einer dieser Punkte einen konkreten Scope-Trigger erhaelt, wandert
eine Notiz auch hier nach `open/`.
