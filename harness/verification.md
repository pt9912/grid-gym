# Verification Evidence

Diese Datei definiert, wie `grid-gym` Slice-Ergebnisse verifiziert.
Verification beantwortet: Wurde der Slice richtig gebaut, gemessen an
Spec, ADR, DoD und ausgefuehrten Sensors?

Validation ist getrennt: Sie fragt, ob das Ergebnis den realen Nutzer-,
Demo- oder Release-Bedarf trifft. Siehe [`harness/roles.md`](roles.md).

## Pflicht bei Slice-Closure

Jeder Slice, der nach `docs/plan/planning/done/` bewegt wird, braucht
eine sichtbare Verification-Evidence. Sie kann direkt im Slice stehen.
Nur bei sehr grosser Evidence entsteht ein eigenes Artefakt, das im
Slice verlinkt wird.

Minimum:

| Feld | Pflicht | Inhalt |
| --- | --- | --- |
| Scope | ja | Slice-ID, betroffene `GG-*`-/`GG-AR-*`-/`ADR-*`-IDs, relevante Dateien |
| DoD-Abgleich | ja | Welche DoD-Punkte sind erfuellt, welche nicht |
| Sensors | ja | Ausgefuehrte Make-Targets oder Tests mit Ergebnis |
| Traceability | ja | Welche Tests/Gates belegen welche Spec- oder ADR-ID |
| Replay / Golden | wenn betroffen | Determinismus-, Replay-, Fault- oder Demo-Cases |
| Carveouts | ja | Neue, geloeste oder unveraenderte Ausnahmen |
| Nicht ausgefuehrt | ja | Ausgelassene Sensors mit Grund |
| Commit / Artefakt | wenn vorhanden | Commit-Hash, Image-Tag, SBOM, Demo-Artefakt oder generiertes Artefakt |

## Evidence Block

Standardblock fuer Slice-Closure:

```markdown
## Verification Evidence

Scope:
- Slice: `<slice-id>`
- IDs: `<GG-...>`, `<GG-AR-...>`, `<ADR-...>`
- Artefakte: `<Dateien/Pakete/Commands>`

DoD-Abgleich:
- [x] `<DoD-Punkt>` - Evidence: `<Test/Gate/Diff>`
- [ ] `<DoD-Punkt>` - offen: `<Grund/Folge-Slice/Carveout>`

Sensors:
| Sensor | Ergebnis | Evidence |
| --- | --- | --- |
| `make test-unit` | pass/fail/not run | `<kurzer Beleg>` |
| `make test-determinism` | pass/fail/not run | `<kurzer Beleg>` |
| `make test-replay` | pass/fail/not run | `<kurzer Beleg>` |
| `make test-fault` | pass/fail/not run | `<kurzer Beleg>` |
| `make docs-check` | pass/fail/not run | `<kurzer Beleg>` |
| `make gates` | pass/fail/not run | `<kurzer Beleg>` |

Traceability:
| ID | Beleg |
| --- | --- |
| `<GG-...>` | `<Test/Gate/Doku>` |
| `<GG-AR-...>` | `<arch-check/Test/Review>` |
| `<ADR-...>` | `<Gate/Test/Doku>` |

Replay / Golden:
- Affected flows: `<none|simulation|replay|fault|demo|ui>`
- Cases added: `<none|Liste>`
- Cases updated: `<none|Liste + Begruendung>`
- Cases replayed: `<none|Sensoren>`
- Intentional output changes: `<none|Begruendung>`

Carveouts:
- Neu: `<none|Eintrag + Plan-Anker>`
- Geloest: `<none|Eintrag>`
- Unveraendert: `<none|Eintrag>`

Nicht ausgefuehrt:
- `<Sensor>` - `<Grund>`

Commit / Artefakt:
- `<hash|image-tag|release-asset|n/a>`
```

## Sensor-Auswahl

Der Verifier waehlt den engsten sinnvollen Sensor, muss aber begruenden,
wenn ein naheliegender Sensor nicht gelaufen ist.

| Aenderung | Mindest-Sensor | Normaler Closure-Sensor |
| --- | --- | --- |
| Nur Markdown/Doku | `make docs-check` | `make docs-check` |
| Python-Code ohne Runtime/Integration | `make test-unit` | `make gates` |
| Architektur-/Importregeln | `make arch-check` | `make gates` |
| Coverage-relevanter Code | `make coverage-gate` oder `make coverage-gate-critical` | `make gates` |
| Simulation/Random/Scheduler/Scenario | `make test-determinism` | `make gates` plus relevante Marker |
| Replay/Snapshot/Diff | `make test-replay` | `make gates` plus Replay-Evidence |
| Fault/Safety/Recovery | `make test-fault` | `make gates` plus Fault-Evidence |
| HTTP-API | `make openapi-validate` oder relevanter API-Test | `make ci` |
| Persistenz/OTLP/Compose | `make test-integration` | `make ci` |
| Runtime/Demo/Release | engster Runtime- oder Demo-Smoke | `make fullbuild` |
| Dependency/Lockfile | `make dep-audit` | `make gates`; bei Runtime-Relevanz `make ci` |
| Image/Security | `make image-audit` | `make ci` oder `make fullbuild` |

## Harte Regeln

- Ein gruenes `make gates` ersetzt nicht den DoD-Abgleich.
- Ein einzelner Unit-Test ersetzt nicht den Link auf die betroffene
  `GG-*`-, `GG-AR-*`- oder `ADR-*`-ID.
- Replay-, Fault-, Determinismus- und Demo-Aenderungen brauchen Evidence
  nach [`harness/replay.md`](replay.md).
- Nicht ausgefuehrte Sensors sind erlaubt, aber nur mit Grund.
- Neue temporaere Ausnahmen brauchen einen Plan-Anker und muessen in der
  Closure-Evidence sichtbar bleiben.
- Reviewer-Findings sind keine Verification-Evidence. Sie koennen
  Evidence ausloesen, aber der Verifier prueft DoD, Spec und Sensors
  separat.
