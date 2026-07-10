# 059 — Hygiene-Buendel: ADR-Index-Status-Sync + App-Version-Single-Source

**Status:** Done — 2026-07-10
**Datum:** 2026-07-10
**Quelle:** Buendel-Aktivierung der Trigger
[`056`](056-adr-index-status-sync.md) (Doku-Drift) +
[`057`](057-app-version-single-source.md) (Runtime-Drift), beide aus der
Slice-038-Session; roadmap §4 Planner-Notiz.

---

## Kontext

Zwei aus Slice 038 zurueckgestellte Hygiene-Befunde, gebuendelt geliefert:
056 ist Doku-only, 057 traegt das einzige Runtime-Delta.

## Teil 057 — App-/Tool-Version Single-Sourcing (Runtime)

**Befund:** `_APP_VERSION` war doppelt hart auf `"0.1.0"` gepinnt
(`http_api/app.py` + `composition/_demo_scenario_setup.py`), waehrend das
Paket seit v0.3.0 bei `0.3.0` steht. Folge: FastAPI-`info.version` und das
`RunMetadata.tool_version`-Feld (`GG-TERM-003`) neuer Laeufe trugen eine
falsche Version.

**Lieferung:** NEU zyklenfreies Leaf
[`src/grid_gym/_app_version.py`](../../../../src/grid_gym/_app_version.py)
mit `resolve_app_version()` — `importlib.metadata.version("grid-gym")` +
Sentinel-Fallback `0.0.0+local` (Praezedenz: `_resolve_tool_version` in
`tests/integration/_constants.py`). Beide Pin-Stellen lesen jetzt daraus.

**Cycle-Zwang beachtet:** `app.py` importiert `_demo_scenario_setup`, deshalb
darf keine Version-Quelle aus `app.py` lesen (`AC-NO-CYCLES`). Das Leaf hat
**keine** internen `grid_gym`-Importe und liegt top-level (nicht unter
`http_api/`, dessen `__init__` `app` importiert) — beide Verbraucher
importieren es zyklenfrei.

**Konsequenz (dokumentiert):** neue Laeufe sind nicht mehr replay-vergleichbar
mit Alt-Laeufen, deren `tool_version` `"0.1.0"` traegt — fachlich korrekt per
`GG-TERM-002` („bei gleicher Version"), exakt die Preflight-Semantik aus
[`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) §2.6.

**Release-Entscheidung:** Runtime-Delta, aber der Fix bringt die Laufzeit nur
auf die bereits released `0.3.0`. **Kein Tag geschnitten** — unter
`[Unreleased]` gesammelt; ein Patch `v0.3.1` ist Maintainer-Option.

## Teil 056 — ADR-Index-Status-Sync (Doku)

**Befund:** Die Statusspalte im ADR-Index
([`docs/plan/adr/README.md`](../../adr/README.md)) zeigte 11 Zeilen
`Provisional`, obwohl die Datei-Header (kanonisch per
[`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)
§4) `Accepted` sind — Meilenstein-Sweeps zogen die Dateien, nicht die
Index-Spalte.

**Lieferung:**

- 10 Drift-Zeilen (0022–0027, 0036, 0038–0040) im Index `Provisional →
  Accepted` angeglichen.
- [`ADR 0008`](../../adr/0008-enum-as-domain-frozen-form.md) als **vergessener
  M1-Welle-1-Sweep** identifiziert und auf `Accepted` nachgezogen (Datei-Header
  + Index): die Acceptance war allein an die M1-Welle-1-PR-Mergung gebunden
  (laengst erfolgt), die dritte Frozen-Form ist produktiv verankert
  (`tools/arch_check.py` `_inherits_enum`, `AC-DOMAIN-FROZEN` gruen mit
  `Quality`/`CommandResult` als `StrEnum`).
- README/README.de-ADR-Zaehlung korrigiert: **72 von 73 ADRs `Accepted`
  (1 `Superseded` = 0003, 0 `Provisional`)**.

Damit sind Datei-Header, Index-Spalte und README-Zaehlung konsistent.

## Verification-Evidence

- `make gates` gruen (2368 Unit-Tests; kein Pin bricht — die `tool_version=
  "0.1.0"`-Vorkommen in Unit-Tests sind reine Fixture-Inputs; `arch-check`
  „All checks passed", kein Cycle).
- `make test-integration` gruen (165 passed / 4 skipped): die Demo-Pfad-Tests
  nutzen `DEMO_TOOL_VERSION` (Resolver) und matchen den App-Output — Beweis,
  dass die Version real auf `0.3.0` aufloest (nicht Fallback).
- `make openapi-validate` gruen (`info.version` 0.3.0 valide).
- `make docs-check` gruen (Index/0008/README/CHANGELOG konsistent).

## DoD

- [x] 057: `info.version` + `tool_version` aus einer Quelle, `== pyproject`.
- [x] 057: Duplikat-Pin entfernt; Cycle-Zwang respektiert; Konsequenz dokumentiert.
- [x] 056: Index-Spalte == Datei-Header; 0008 geklaert (accepted); README-Zaehlung korrekt.
- [x] Runtime-Delta ohne Tag (unter `[Unreleased]`; Patch-Option benannt).

## Bezug

- Trigger [`056`](056-adr-index-status-sync.md) + [`057`](057-app-version-single-source.md).
- [`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) §2.6 (Preflight),
  [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §4 (Header kanonisch).
