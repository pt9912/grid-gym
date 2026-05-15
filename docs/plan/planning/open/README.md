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

| Datei                                          | Trigger                                                                  | Aktivierung |
| ---------------------------------------------- | ------------------------------------------------------------------------ | ----------- |
| `001-code-review-doc.md`                       | `docs/user/code-review.md` + PR-Template (ADR 0002 A-1 Reststeuerung)     | spaetestens vor erster Adapter-PR (Slice-M1) |
| `002-check-refs-tool.md`                       | `tools/check_refs.py` als Querverweis-Linter (ADR 0004)                   | wenn Querverweis-Drift beobachtet wird |
| `003-random-port-adr.md`                       | ADR fuer `RandomPort`-Implementierung (gebondeter PRNG, Seeding-Kette)    | mit erstem Domain-Slice (Scheduler/Devices) |
| `004-canonical-encoder-alternative-adr.md`     | ADR fuer Performance-/Implementierungs-Alternativen (orjson, msgspec)      | bei messbarem Perf-Druck am Telemetrie-Pfad |
| `005-pyright-vs-mypy-reeval.md`                | Re-Eval mypy vs. pyright bei generischen Protocols                        | sobald `ports/*` Generic-Protocols einfuehrt |
| `006-mypy-strict-bytes.md`                     | `--strict-bytes`-Aktivierung (ADR 0005)                                   | nach Konsolidierung des `GG-DATA-005`-Bytes-Vertrags |
| `007-pyright-precommit-adr.md`                 | ADR fuer pyright als Pre-Commit-Hook                                      | bei Editor-Parity-Druck |
| `008-sbom-activation.md`                       | `make sbom` scharfschalten (`GG-CICD-007`)                                | mit erster Artefakt-Veroeffentlichung |
| `009-tests-integration-compose.md`             | `tests/integration/compose.yml` (testcontainers)                          | mit erstem Persistenz-Adapter-Slice |
| `010-deploy-compose.md`                        | `deploy/compose.yml` (Compose-Smoke + Demo)                                | mit erstem Deploy-Slice (`GG-DEPLOY-001/005`) |
| `011-hexagon-layout-adr-0002-realign.md`       | ADR-0002-Contracts an `hexagon/`-Gruppierung in architecture.md anpassen   | vor `ADR 0002 Accepted` |

Architektonische offene Punkte (`GG-AR-OPEN-002..010`) leben weiterhin
in `architecture.md` §19 und sind dort die kanonische Liste. Wenn
einer dieser Punkte einen konkreten Scope-Trigger erhaelt, wandert
eine Notiz auch hier nach `open/`.
