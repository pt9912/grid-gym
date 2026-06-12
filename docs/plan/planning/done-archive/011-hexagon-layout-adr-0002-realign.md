# 011 — ADR-0002-Kontrakte an `hexagon/`-Layout anpassen (Closure)

**Status:** Done
**Eroeffnet:** 2026-05-15
**Geschlossen:** 2026-05-15
**Quelle:** Strukturelle Refinierung in `spec/architecture.md` §4.2
(`hexagon/`-Gruppierung von `core/` und `ports/`);
[`ADR 0002`](../../adr/0002-language-and-build-stack.md) A-1
Contracts (`Provisional`).

---

## Geliefert

Pre-Acceptance-Schliff an `ADR 0002` (`Provisional`, gemaess
`ADR 0006` §3 erlaubt; siehe `Letzte inhaltliche Aenderung`
2026-05-15 im ADR-Header):

- §6.1 Repository-Layout-Zeile auf
  `src/grid_gym/{hexagon/{core,ports},adapters}/` praezisiert.
- A-1 Contracts: alle fuenfzehn Eintraege auf `hexagon.core.*`/
  `hexagon.ports.*` umgestellt (AC-CORE-NO-ADAPTERS,
  AC-CORE-NO-DRIVING, AC-PORTS-NO-OUT, AC-PORTS-NO-FW,
  AC-ADAPTER-PURE, AC-ADAPTER-LIGHTWEIGHT,
  AC-NO-FW, AC-NO-IO-MOD, AC-NO-CYCLES, AC-NO-TIME,
  AC-NO-RAND, AC-NO-JSON, AC-DOMAIN-FROZEN, AC-NO-GOD-UTILS,
  AC-TYPED-ERRORS).
- AC-NO-JSON-Whitelist auf
  `src/grid_gym/hexagon/core/serialization/canonical.py`.
- `[tool.grid_gym.arch_check]` `json-dumps-whitelist`-Pfad
  angepasst; `typed-errors-exempt` (Adapter-Pfade) unveraendert.
- `tools/arch_check.py`-Heuristik-Beschreibung (`hexagon/core/*`)
  und ruff-Reichweiten-Vertrag entsprechend.
- A-2 Custom-Emitter-Pfade auf
  `grid_gym.hexagon.core.serialization.canonical` und
  `src/grid_gym/hexagon/core/serialization/canonical.py`.
- Spike-0-Vertrag: Repository-Skelett
  (`src/grid_gym/{hexagon/{core,ports},adapters}`).
- §6.2 Wirkung auf andere Dokumente: Python-Paketnamen-Hinweis
  (`src/grid_gym/hexagon/core/...`, `src/grid_gym/hexagon/ports/...`,
  `src/grid_gym/adapters/...`).
- Header: `Letzte inhaltliche Aenderung` auf 2026-05-15 aktualisiert,
  Vorgaenger-Aenderung verkettet.

Downstream-Artefakte:

- `Dockerfile` `coverage-gate-critical`: vier `--cov=`-Pfade auf
  `src/grid_gym/hexagon/core/...` umgestellt.
- `Makefile` Helptext (`coverage-gate-critical`-Beschreibung):
  unveraendert — die Modul-Liste ist rein deskriptiv und bleibt
  fachlich korrekt.
- `[tool.mypy] files = ["src/grid_gym", "tools"]` in `ADR 0005`
  unveraendert — Scope deckt `src/grid_gym/hexagon/...` bereits ab.

## Lastenheft-IDs

Kein direkter Abschluss von `GG-*`-Anforderungen. Die Arbeit
ist Voraussetzung fuer:

- `GG-AR-OPEN-001` (Sprach- und Build-Wahl) — wird erst mit
  Spike-0-Abschluss und `ADR 0002 Accepted` geschlossen.

## Was bleibt offen

- Spike-0 selbst ist nicht Bestandteil dieser Closure — bleibt
  als naechster Slice (`docs/plan/planning/in-progress/roadmap.md`,
  M1-Vorbedingung).
- ADR 0002 bleibt `Provisional` bis Spike-0 alle vier Gates
  gruen meldet.

## CHANGELOG

Eintrag unter „Unreleased / Changed" im
[CHANGELOG.md](../../../../CHANGELOG.md) (Commit-Tag folgt mit
naechstem Release).
