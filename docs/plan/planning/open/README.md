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
| `004-canonical-encoder-alternative-adr.md`     | ADR fuer Performance-/Implementierungs-Alternativen (orjson, msgspec)      | bei messbarem Perf-Druck am Telemetrie-Pfad |
| `005-pyright-vs-mypy-reeval.md`                | Re-Eval mypy vs. pyright bei generischen Protocols                        | sobald `ports/*` Generic-Protocols einfuehrt |
| `006-mypy-strict-bytes.md`                     | `--strict-bytes`-Aktivierung (ADR 0005)                                   | nach Konsolidierung des `GG-DATA-005`-Bytes-Vertrags |
| `007-pyright-precommit-adr.md`                 | ADR fuer pyright als Pre-Commit-Hook                                      | bei Editor-Parity-Druck |
| `008-sbom-activation.md`                       | `make sbom` scharfschalten (`GG-CICD-007`)                                | mit erster Artefakt-Veroeffentlichung |

**M3-/Multi-Agent-Folge:**

| Datei                                          | Trigger                                                                   | Aktivierung |
| ---------------------------------------------- | ------------------------------------------------------------------------- | ----------- |
| `011-mlrandomport-subseed-width.md`            | `MLRandomPort` Sub-Seed-Wortbreite (ADR 0007 §5.2/§6)                      | bei `> 10⁶` Sub-Ports / hochskalierter Multi-Agent-Welle (M3-Welle 3+4 hat Schwelle nicht erreicht) |

**SOLLTE — M2-Welle-7-Erbschaft** (Quelle: [`done/M2-devices.md`](../done/M2-devices.md) §4 Out-of-Scope):

| Datei                                          | Trigger                                                                   | Aktivierung |
| ---------------------------------------------- | ------------------------------------------------------------------------- | ----------- |
| `016-sollte-ev-charger-device.md`              | EV-Charger-Device (`GG-DEV-015`, Lastenheft §9.4)                          | wenn konkreter Bedarf — eigener Slice |
| `017-sollte-transformer-device.md`             | Transformer-Device (`GG-DEV-016`, Lastenheft §9.4)                         | wenn konkreter Bedarf — eigener Slice |
| `018-sollte-wind-device.md`                    | Wind-Device (`GG-DEV-017`, Lastenheft §9.4)                                | wenn konkreter Bedarf — eigener Slice |
| `019-sollte-diesel-device.md`                  | Diesel-Device (`GG-DEV-018`, Lastenheft §9.4)                              | wenn konkreter Bedarf — eigener Slice |
| `020-sollte-island-grid.md`                    | Inselnetz-Bilanzmodell (`GG-GRID-005`, Lastenheft §11.5)                   | wenn konkreter Bedarf — eigener Slice |
| `021-sollte-transformer-limits.md`             | Transformatorgrenzen im Netzbilanzmodell (`GG-GRID-006`, Lastenheft §11.5) | wenn konkreter Bedarf — eigener Slice |
| `022-sollte-reactive-power.md`                 | Blindleistung im Netzbilanzmodell (`GG-GRID-007`, Lastenheft §11.5)        | wenn konkreter Bedarf — eigener Slice |
| `023-sollte-battery-temperature.md`            | Battery-Temperatur-Telemetry (`GG-BESS-006`, Lastenheft §10.6)             | wenn konkreter Bedarf — eigener Slice |
| `024-sollte-battery-cell-voltage.md`           | Battery-Zellspannung-Telemetry (`GG-BESS-007`, Lastenheft §10.6)           | wenn konkreter Bedarf — eigener Slice |

Architektonische offene Punkte (`GG-AR-OPEN-002..010`) leben weiterhin
in `architecture.md` §19 und sind dort die kanonische Liste. Wenn
einer dieser Punkte einen konkreten Scope-Trigger erhaelt, wandert
eine Notiz auch hier nach `open/`.
