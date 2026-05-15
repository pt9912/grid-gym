# 011 — ADR-0002-Kontrakte an `hexagon/`-Layout anpassen

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-15
**Quelle:** Strukturelle Refinierung in `spec/architecture.md` §4.2
(`hexagon/`-Gruppierung von `core/` und `ports/`);
[`ADR 0002`](../../adr/0002-language-and-build-stack.md) A-1
Contracts (`Provisional`).

---

## Trigger

`spec/architecture.md` §4.2 zeigt nun `hexagon/core/*` und
`hexagon/ports/*` als sprachunabhaengige Modulgrenzen. Die A-1
Contracts in `ADR 0002` referenzieren weiterhin `core.*` und
`ports.*` als Python-Modul-Muster, und das Spike-0-Skelett aus
`ADR 0002` §6.1 nennt `src/grid_gym/{core,ports,adapters}/`. Beide
Quellen muessen vor `Accepted` ausgerichtet werden, sonst wird
`GG-AR-OPEN-001` auf inkonsistente Architektur-/Layout-Aussagen
geschlossen.

## Erwartete Lieferung

Pre-Acceptance-Schliff an `ADR 0002` (`Provisional` → zulaessig
gemaess `ADR 0006` §3 / „Letzte inhaltliche Aenderung"):

- Repository-Layout: `src/grid_gym/hexagon/{core,ports}/` plus
  `src/grid_gym/adapters/...`.
- A-1 Contracts: Modul-Muster auf `grid_gym.hexagon.core.*` /
  `grid_gym.hexagon.ports.*` umstellen
  (`AC-CORE-NO-ADAPTERS`, `AC-CORE-NO-DRIVING`, `AC-PORTS-NO-OUT`,
  `AC-PORTS-NO-FW`, `AC-ADAPTER-PURE`, `AC-NO-FW`, `AC-NO-IO-MOD`,
  `AC-NO-CYCLES`, `AC-NO-TIME`, `AC-NO-RAND`, `AC-NO-JSON`,
  `AC-DOMAIN-FROZEN`, `AC-NO-GOD-UTILS`, `AC-TYPED-ERRORS`).
- `AC-NO-JSON`-Whitelist:
  `src/grid_gym/hexagon/core/serialization/canonical.py`.
- `[tool.grid_gym.arch_check]`-Konfiguration in `pyproject.toml`
  und `tools/arch_check.py`-Default-Pfade entsprechend.
- Downstream-Update der Coverage-Pfade in `Dockerfile`
  (`coverage-gate-critical`) und `Makefile`-Helptext:
  `src/grid_gym/hexagon/core/{simulation,devices/battery,scenario,replay}`.
- `[tool.mypy]` `files = ["src/grid_gym/hexagon", "src/grid_gym/adapters", "tools"]`
  (oder schlanker `["src/grid_gym", "tools"]`, falls Scope identisch).

## Aktivierungs-Kriterium

Vor `ADR 0002` → `Accepted`. Spaetestens, wenn Spike-0 startet
und ein lauffaehiges Skelett angelegt werden soll.

## Wandert nach

- `in-progress/`, sobald der Schliff aktiv geplant ist,
- `archive/`, falls die Hexagon-Gruppierung in architecture.md
  doch wieder zugunsten einer flacheren Struktur zurueckgenommen
  wird.
