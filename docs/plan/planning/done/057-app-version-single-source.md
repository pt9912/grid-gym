# 057 — `_APP_VERSION`-Drift: `tool_version`/OpenAPI melden 0.1.0 statt Paket-Version

**Status:** Done — 2026-07-10 (Buendel-Closure via Slice 059)
**Datum:** 2026-07-03
**Quelle:** Slice-038-C1 (beim Umbau der `RunMetadata`-Konstruktions-
stellen beobachtet); Handoff-Befund, hier repo-persistent verankert.

---

## Befund

`_APP_VERSION` ist doppelt hart auf `"0.1.0"` gepinnt, waehrend das
Paket (seit v0.3.0) bei `0.3.0` steht:

- `src/grid_gym/adapters/driving/http_api/app.py` (`_APP_VERSION`,
  speist die FastAPI-`info.version` **und** `tool_version` jeder
  per `POST /runs` bzw. Demo-Setup konstruierten `RunMetadata`).
- `src/grid_gym/composition/_demo_scenario_setup.py` (bewusste
  Duplikation „per Konvention synchron zu `app._APP_VERSION`" —
  die Konvention haelt seit zwei Releases nicht).

Wirkung: `tool_version` ist das [`GG-TERM-003`](../../../../spec/lastenheft.md#gg-term-003)-Feld
**„Version"** — neue Laeufe tragen eine falsche Versionsangabe in
ihren Reproduzierbarkeits-Metadaten, und die OpenAPI-Doku meldet
eine veraltete API-Version. Der Replay-Preflight bricht dadurch
heute **nicht** (er vergleicht nur Gleichheit, und alle Laeufe
desselben Servers tragen denselben Wert) — der Befund ist ein
Korrektheits-/Doku-Problem, kein Determinismus-Bruch.

## Erwartete Lieferung

- **Single-Sourcing** der Version aus den Paket-Metadaten
  (`importlib.metadata.version("grid-gym")` mit Sentinel-Fallback;
  Praezedenzmuster existiert in
  `_resolve_tool_version` in `tests/integration/_constants.py`), statt
  Release-manueller Pin-Pflege an zwei Stellen.
- Duplikat-Pin in `composition/_demo_scenario_setup.py` entfernen
  (eine Quelle statt „per Konvention synchron").
- Test-Pins nachziehen (OpenAPI-`info.version`-Erwartungen,
  Fixture-`tool_version`-Werte, soweit sie `"0.1.0"` hart erwarten).
- **Dokumentierte Konsequenz** (in Slice-Plan/Commit): nach dem Fix
  sind neue Laeufe nicht mehr replay-vergleichbar mit Alt-Laeufen,
  deren `tool_version` `"0.1.0"` traegt — fachlich korrekt per
  [`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002) („bei gleicher
  Version") und exakt die Preflight-Semantik aus
  [`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) §2.6.
- Runtime-Delta → Release-Entscheidung im aufloesenden Slice
  (Patch-Kandidat oder Sammeln unter `[Unreleased]` bis zum
  naechsten Minor).

## Aktivierungs-Kriterium

Naechster Release-Zyklus (damit die Versionsangabe ab dann stimmt)
ODER Buendel-Aktivierung als Hygiene-Slice mit
[`056`](056-adr-index-status-sync.md) (054-Marker-Sweep
2026-07-10 erledigt → `done/`).

## Wandert nach

`done/`, sobald `info.version` und `tool_version` aus einer Quelle
kommen und mit `pyproject.toml` uebereinstimmen.

---

## Closure 2026-07-10 (Slice 059)

Geliefert im Hygiene-Buendel [`059`](059-hygiene-bundle-adr-index-app-version.md):
NEU zyklenfreies Leaf `grid_gym._app_version.resolve_app_version()`
(`importlib.metadata` + Sentinel-Fallback); beide `"0.1.0"`-Pin-Stellen
(`http_api.app`, `composition._demo_scenario_setup`) lesen jetzt daraus.
`info.version` + `tool_version` == `pyproject`-Version (0.3.0), verifiziert via
`make gates` + `make test-integration` (Demo-Pfad matcht Resolver) +
`make openapi-validate`. Runtime-Delta ohne Tag (unter `[Unreleased]`;
Patch v0.3.1 = Maintainer-Option). Details + DoD in Slice 059.
