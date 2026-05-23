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

Spalte „Prioritaet": `M1-blockierend` = muss vor / waehrend M1-Slice
1-2 abgearbeitet sein; `M1-koppelbar` = bietet sich an, ist aber kein
Block; `Post-M1` = nach M1-Abschluss.

| Prioritaet           | Datei                                          | Trigger                                                                  | Aktivierung |
| -------------------- | ---------------------------------------------- | ------------------------------------------------------------------------ | ----------- |
| **M1-blockierend**   | `009-tests-integration-compose.md`             | `tests/integration/compose.yml` (testcontainers)                          | erforderlich fuer `make fullbuild` als M1-Abnahmebedingung |
| **M1-blockierend**   | `010-deploy-compose.md`                        | `deploy/compose.yml` (Compose-Smoke + Demo)                                | erforderlich fuer `make fullbuild` als M1-Abnahmebedingung |
| **M1-koppelbar**     | `002-check-refs-tool.md`                       | `tools/check_refs.py` als Querverweis-Linter (ADR 0004)                   | wenn Querverweis-Drift beobachtet wird; ideal mit Trigger 001 |
| **M1-koppelbar**     | `005-pyright-vs-mypy-reeval.md`                | Re-Eval mypy vs. pyright bei generischen Protocols                        | sobald `ports/*` Generic-Protocols einfuehrt |
| **M1-koppelbar**     | `006-mypy-strict-bytes.md`                     | `--strict-bytes`-Aktivierung (ADR 0005)                                   | nach Konsolidierung des `GG-DATA-005`-Bytes-Vertrags |
| **Post-M1**          | `004-canonical-encoder-alternative-adr.md`     | ADR fuer Performance-/Implementierungs-Alternativen (orjson, msgspec)      | bei messbarem Perf-Druck am Telemetrie-Pfad |
| **Post-M1**          | `007-pyright-precommit-adr.md`                 | ADR fuer pyright als Pre-Commit-Hook                                      | bei Editor-Parity-Druck |
| **Post-M1**          | `008-sbom-activation.md`                       | `make sbom` scharfschalten (`GG-CICD-007`)                                | mit erster Artefakt-Veroeffentlichung |

Architektonische offene Punkte (`GG-AR-OPEN-002..010`) leben weiterhin
in `architecture.md` §19 und sind dort die kanonische Liste. Wenn
einer dieser Punkte einen konkreten Scope-Trigger erhaelt, wandert
eine Notiz auch hier nach `open/`.
