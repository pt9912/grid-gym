# Offene Plaene und Trigger-Watch

Dieses Verzeichnis sammelt **trigger-getriebene Folgearbeit** und
**Vorabklaerungen**, die noch nicht in die aktive Roadmap aufgenommen
wurden.

Eintraege wandern entweder:

- nach `next/`, sobald ein Scope skizziert ist, aber noch kein Slice aktiv,
- nach `in-progress/`, wenn sie direkt aktiviert werden, oder
- nach `archive/`, wenn sie bewusst verworfen werden.

---

## Bestand

Alle Eintraege sind Trigger-Watch-Notizen (`Status: Open`) ohne
harten Aktivierungs-Zwang. Die `Aktivierung`-Spalte beschreibt den
konkreten Anlass, der eine Aktivierung ausloesen soll.

**Tooling / Build / Type-System:**

| Datei                                          | Trigger                                                                   | Aktivierung |
| ---------------------------------------------- | ------------------------------------------------------------------------- | ----------- |
| [`004-canonical-encoder-alternative-adr.md`](004-canonical-encoder-alternative-adr.md)     | ADR fuer Performance-/Implementierungs-Alternativen (orjson, msgspec)      | bei messbarem Perf-Druck am Telemetrie-Pfad |
| [`005-pyright-vs-mypy-reeval.md`](005-pyright-vs-mypy-reeval.md)                | Re-Eval mypy vs. pyright bei generischen Protocols                        | sobald `ports/*` Generic-Protocols einfuehrt |
| [`../done/006-mypy-strict-bytes.md`](../done/006-mypy-strict-bytes.md) | `--strict-bytes`-Aktivierung (ADR 0005) | **Closed 2026-06-01** (M4-Welle-6a-C3) — `[tool.mypy] strict_bytes = true` aktiv; Trigger gewandert nach `done/` |
| [`007-pyright-precommit-adr.md`](007-pyright-precommit-adr.md)                 | ADR fuer pyright als Pre-Commit-Hook                                      | bei Editor-Parity-Druck |
| [`../done/008-sbom-activation.md`](../done/008-sbom-activation.md) | `make sbom` scharfschalten (`GG-CICD-007`) | **Closed 2026-06-05** (M6-Welle-2-C2 `235395e`) — `make sbom` produktiv gegen Runtime-Image; NEU `.github/workflows/release.yml` mit 3 Jobs + 6 publizierten Artefakten (1 GHCR-Push + 5 Release-Asset-Files); ADR 0042 `Provisional`; Trigger gewandert nach `done/` |
| [`009-iec61850-smoke-reactivation.md`](009-iec61850-smoke-reactivation.md) | IEC-61850 In-Process-Smoke reaktivieren (`tests/integration/test_iec61850_in_process_smoke.py`-Skip aufheben) | pyiec61850-ng publishet cp314-Manylinux-Wheel (Pfad A) ODER Pfad-B-Slice (Multi-Python-Test-Stage) wird angepackt |
| [`../done/010-base-image-krb5-cve-bump.md`](../done/010-base-image-krb5-cve-bump.md) | Base-Image-Bump fuer krb5-CVE-Drift (`make fullbuild` pre-existing rot seit M3-Welle-7-`c61ab0d`; `CVE-2026-40356` + 3 weitere HIGH-CVEs) | **Closed 2026-06-05** (M6-Welle-1-C2 `b514170`) — Null-Code-Edit; Debian-13.5-Upstream-Drift + Trigger-015-Pattern; Trigger gewandert nach `done/` |
| [`../done/031-ci-make-fullbuild-gate.md`](../done/031-ci-make-fullbuild-gate.md) | CI-Pflicht-Gate fuer `make fullbuild` (M6-Welle-1-Welle-1-D-1-Vertagung; `make fullbuild` lokal cache-frei gruen seit Welle-1-C2, aber nicht GitHub-seitig enforced) | **Closed 2026-06-05** (M6-Welle-3-C2 `ce13253`) — NEU `.github/workflows/fullbuild.yml` mit Hybrid Push/PR-Paths-Filter + workflow_dispatch; Trigger gewandert nach `done/` |
| [`032-release-workflow-sensor-run.md`](032-release-workflow-sensor-run.md) | Reale GitHub-Actions-Release-Workflow-Run-Verifikation (M6-Welle-2-Post-Closure-Review-Folge F1; alle lokal-verifizierbaren Substanzen gruen, aber GHCR-Push + Release-Create + Multi-Job-Artifact-Sharing nur via realen Lauf bestaetigbar) | erster echter `v*.*.*`-Tag-Push ODER M6-Welle-3-Entscheidung (Pre-Substanz vs. spaeter) ODER Compliance-Druck |
| [`033-otel-collector-go-stdlib-cve-bump.md`](033-otel-collector-go-stdlib-cve-bump.md) | OTel-Collector Go-stdlib CVE-2026-42504-Bump (`make fullbuild`-Defer seit M6-Welle-3-`ede21ad`; `otel/opentelemetry-collector-contrib:0.153.0` baut gegen `go1.26.3` mit MIME-Header-DoS-CVE; ADR-0043-konformer Defer-Pfad) | OTel-Collector-Release > 0.153.0 mit `go1.26.4+`-Build (erwartet 2026-06-09..06-12) ODER Compliance-Druck |

**M3-/Multi-Agent-Folge:**

| Datei                                          | Trigger                                                                   | Aktivierung |
| ---------------------------------------------- | ------------------------------------------------------------------------- | ----------- |
| [`011-mlrandomport-subseed-width.md`](011-mlrandomport-subseed-width.md)            | `MLRandomPort` Sub-Seed-Wortbreite (ADR 0007 §5.2/§6)                      | bei `> 10⁶` Sub-Ports / hochskalierter Multi-Agent-Welle (M3-Welle 3+4 hat Schwelle nicht erreicht) |
| [`026-bess-simulation-reserve-market-spike.md`](026-bess-simulation-reserve-market-spike.md)  | Lokale BESS-Simulation als Vorlage fuer Reserve-Market-/LER-Strategien     | bei Reserve-Market-Agent, BESS-SOC-Management-Agent oder LER-Demo |

**SOLLTE — M2-Welle-7-Erbschaft** (Quelle: [`done/M2-devices.md`](../done/M2-devices.md) §4 Out-of-Scope):

| Datei                                          | Trigger                                                                   | Aktivierung |
| ---------------------------------------------- | ------------------------------------------------------------------------- | ----------- |
| [`016-sollte-ev-charger-device.md`](016-sollte-ev-charger-device.md)              | EV-Charger-Device (`GG-DEV-015`, Lastenheft §9.4)                          | wenn konkreter Bedarf — eigener Slice |
| [`017-sollte-transformer-device.md`](017-sollte-transformer-device.md)             | Transformer-Device (`GG-DEV-016`, Lastenheft §9.4)                         | wenn konkreter Bedarf — eigener Slice |
| [`018-sollte-wind-device.md`](018-sollte-wind-device.md)                    | Wind-Device (`GG-DEV-017`, Lastenheft §9.4)                                | wenn konkreter Bedarf — eigener Slice |
| [`019-sollte-diesel-device.md`](019-sollte-diesel-device.md)                  | Diesel-Device (`GG-DEV-018`, Lastenheft §9.4)                              | wenn konkreter Bedarf — eigener Slice |
| [`020-sollte-island-grid.md`](020-sollte-island-grid.md)                    | Inselnetz-Bilanzmodell (`GG-GRID-005`, Lastenheft §11.5)                   | wenn konkreter Bedarf — eigener Slice |
| [`021-sollte-transformer-limits.md`](021-sollte-transformer-limits.md)             | Transformatorgrenzen im Netzbilanzmodell (`GG-GRID-006`, Lastenheft §11.5) | wenn konkreter Bedarf — eigener Slice |
| [`022-sollte-reactive-power.md`](022-sollte-reactive-power.md)                 | Blindleistung im Netzbilanzmodell (`GG-GRID-007`, Lastenheft §11.5)        | wenn konkreter Bedarf — eigener Slice |
| [`023-sollte-battery-temperature.md`](023-sollte-battery-temperature.md)            | Battery-Temperatur-Telemetry (`GG-BESS-006`, Lastenheft §10.6)             | wenn konkreter Bedarf — eigener Slice |
| [`024-sollte-battery-cell-voltage.md`](024-sollte-battery-cell-voltage.md)           | Battery-Zellspannung-Telemetry (`GG-BESS-007`, Lastenheft §10.6)           | wenn konkreter Bedarf — eigener Slice |

Architektonische offene Punkte (`GG-AR-OPEN-002..010`) leben weiterhin
in `architecture.md` §19 und sind dort die kanonische Liste. Wenn
einer dieser Punkte einen konkreten Scope-Trigger erhaelt, wandert
eine Notiz auch hier nach `open/`.
