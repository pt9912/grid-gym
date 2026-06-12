# 008 — SBOM scharfschalten

**Status:** Done — Aktivierung produktiv mit M6-Welle-2-C2
`235395e` 2026-06-05. `make sbom` cache-frei gruen gegen
`grid-gym-runtime:latest` (CycloneDX v1.6, 169 Komponenten);
NEU `.github/workflows/release.yml` mit Tag-Push +
`workflow_dispatch`-Trigger + 3 Jobs + 6 publizierten
Artefakten (1 GHCR-Push + 5 Release-Asset-Files: SBOM +
JUnit-XML + Coverage-HTML-Tarball + OpenAPI-JSON + Demo-
Abnahme-MD); Trigger gewandert nach `done/` mit M6-Welle-
2-C3 (Pattern analog Trigger 010 in M6-Welle-1-C3
`4517614`).
**Datum:** 2026-05-15 (eroeffnet), 2026-06-01 (M5-Welle-0-
C2-Triage `112efd3` — bleibt in `open/`), 2026-06-04
(M6-Welle-0-C2-Triage `74d9452` — `Active in M6-Welle-2`),
2026-06-05 (M6-Welle-2-C2 Aktivierung + Welle-2-C3 Self-
Close-Move).
**Quelle:** [`Makefile`](../../../../Makefile) Target `sbom`
(Kommentar bei `SYFT_IMAGE`); `GG-CICD-007` (Artefakt-Veroeffentlichung)

---

## Closure-Notiz (M6-Welle-2-C2, 2026-06-05)

Die in §"Trigger" unten beschriebene `make sbom`-
Aktivierungs-Pflicht wurde in M6-Welle-2-C2 `235395e`
produktiv realisiert:

- **`Makefile` Z.452-471** geschaerft: Scan-Ziel von
  `dir:/src` (Source-Tree-SBOM) auf `grid-gym-runtime:
  latest` (Runtime-Image-SBOM) umgestellt; `sbom: build`-
  Dependency analog `image-audit: build` hinzugefuegt;
  NEU `PYPROJECT_VERSION`-Make-Variable extrahiert
  `pyproject.toml [project] version` mit `v`-Prefix.
- **NEU `.github/workflows/release.yml`** mit 3 Jobs:
  `build-and-publish-image` (GHCR-Push), `produce-assets`
  (SBOM + 4 weitere Asset-Files), `create-release` (GitHub-
  Release-Anlage). Trigger: Tag-Push (`v*.*.*`) +
  Manual-`workflow_dispatch`.
- **`Dockerfile` test-unit + coverage-gate Stage-Edits**
  fuer JUnit-XML + Coverage-HTML-Asset-Export.

**Beleg (vor C2-Commit):**

- `make gates` cache-frei gruen ohne Override (EXIT=0;
  10/10 A-1-Gates).
- `make fullbuild` cache-frei gruen ohne Override
  (EXIT=0).
- `make sbom` ohne explizites VERSION produziert
  `artifacts/sbom-v0.1.0.cdx.json` (CycloneDX v1.6; 169
  Komponenten; entspricht Welle-2-Pre-C0c-Probe-Range).

**ADR-Verankerung:** ADR 0042
[`SBOM-Tool + Release-Workflow-Pattern`](../../adr/0042-sbom-tool-and-release-pattern.md)
(`Provisional` per Welle-2-C1 `4b1062b`; `Accepted` in
M6-Welle-7-Closure-C1 gebuendelt mit ADR 0041 + ADR 0043)
verankert SBOM-Tool/Scan-Ziel + Release-Workflow-Pattern
als wiederverwendbaren Quality-Gate-Vertrag (Schwester-
Pattern zu ADR 0029 + ADR 0043). ADR-0042-§5 traegt den
Welle-2-C2-Hash als Aufloesungs-Anker.

Die unten unter „Trigger" und „Erwartete Lieferung"
beschriebenen Punkte sind damit **historisch** und
stehen nur noch als Trigger-Watch-Kontext (Welle-0-
Eroeffnungs-Stand bis Welle-2-C2-Aktivierung).

---

## Trigger (historisch — Welle-0-Eroeffnungs-Stand)

`make sbom` ist heute eingerichtet, aber als kommentierte
Folgearbeit markiert:

> SBOM-Erzeugung als Release-Asset. Wird in spaeterer Welle scharf
> geschaltet, sobald `GG-CICD-007` (Artefakt-Veroeffentlichung)
> aktiv wird.

Aktivierung ergibt erst Sinn, wenn `GG-CICD-007` (Release-Pipeline
mit Artefakt-Publikation) ein konkretes Release-Vehikel hat.

## Erwartete Lieferung

- `make sbom VERSION=v0.1.0` laeuft in CI als Pflicht-Schritt fuer
  Release-Tags und produziert `artifacts/sbom-vN.cdx.json`.
- Release-Workflow lade das SBOM-Asset zur Release-Veroeffentlichung
  hoch.
- Pruefung: SBOM enthaelt alle Runtime-Dependencies aus `uv.lock`
  und das Container-Image.

## Aktivierungs-Kriterium

Mit der ersten Release-Veroeffentlichung (Tag, GitHub Release oder
Container-Registry-Push).

## Wandert nach

- `next/`, sobald Release-Pipeline skizziert ist,
- `in-progress/`, wenn aktiver Release-Slice geplant ist.

## M5-Welle-0-C2-Triage 2026-06-01

Verbleibt in `open/`. M5-Closure liefert keine produktive
Release-Pipeline (M5 ist UI + Demo, kein Release-Workflow).
M5-Welle-7-Closure koennte allerdings SBOM-Aktivierung
mitnehmen falls ein Demo-Release-Tag erwogen wird —
optional, kein DoD-Pflicht-Punkt. Realistischer
Aktivierungs-Pfad bleibt M6 (`GG-CICD-007` Release-
Workflow als Pflicht-Lieferung).
