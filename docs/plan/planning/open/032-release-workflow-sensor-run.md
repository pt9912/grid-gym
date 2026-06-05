# 032 — Release-Workflow-Sensor-Run-Verifikation

**Status:** Open — Trigger-Watch
**Datum:** 2026-06-05
**Quelle:** M6-Welle-2-Post-Closure-Review-Folge F1 HIGH
([`../done/M6-welle-2.md §9 DoD`](../done/M6-welle-2.md);
1 verbleibendes DoD-Item nach Welle-2-C4b-Closure).

---

## Trigger

M6-Welle-2 hat `.github/workflows/release.yml` produktiv
geliefert + lokal verifiziert (actionlint + shellcheck +
`make sbom`/`make fullbuild` gruen). Was im Repo-only-Stand
**nicht erbracht** ist:

- Reale GitHub-Actions-Workflow-Ausfuehrung mit allen drei
  Jobs (`build-and-publish-image` / `produce-assets` /
  `create-release`).
- GHCR-Push gegen `ghcr.io/<owner>/grid-gym:<tag>` + `:latest`
  (letzteres nur bei Tag-Push; siehe ADR 0042 §2.3).
- GitHub-Release-Erstellung via
  `softprops/action-gh-release@v2` mit allen 5 Asset-Files
  (SBOM + JUnit-XML + Coverage-HTML + OpenAPI-JSON + Demo-
  Abnahme-MD).
- Job-zu-Job-Artifact-Sharing (`upload-artifact@v4` ↔
  `download-artifact@v4`) inkl. SBOM-Sharing zwischen
  `build-and-publish-image` und `produce-assets` (post-F2-
  Refactor).
- Tag-Trigger-Routing (`v*.*.*`-Glob-Pattern matcht
  korrekt; `github.ref_name` resolved zur Version).
- `workflow_dispatch`-Input-Wiring
  (`inputs.version`-Read-Pfad).
- `docker buildx imagetools create`-Pattern fuer
  Conditional-`:latest`-Push (F3-Substanz).

Diese Verifikationen sind nur durch realen Lauf gegen GitHub
moeglich; lokales `act` (https://github.com/nektos/act) ist
keine vollwertige Alternative (kein Push-Mock, kein
Release-Create, kein Multi-Job-Artifact-Store).

## Erwartete Lieferung

Eigenstaendiger Sensor-Run-Slice (M6-Welle-3-Pre-Substanz
oder spaeterer):

- **Push** aller Welle-2-Commits (`0cc28f3..b41b7fc`) auf
  `origin/main` plus die Welle-2-Post-Closure-Review-Folge
  (F1..F4-Korrekturen).
- **Workflow-Aktivierungs-Variante A**: Manual
  `workflow_dispatch` ueber GitHub-UI gegen einen Pre-
  Release-Tag-Namen (z. B. `v0.0.0-welle2-sensor-run`).
- **Workflow-Aktivierungs-Variante B**: Echter Tag-Push
  (`git tag v0.1.0 && git push --tags`) wenn ein erstes
  Release geplant ist.
- **Verifikation**:
  - Alle 3 Jobs gruen.
  - GHCR-Image publiziert (`docker pull ghcr.io/<owner>/
    grid-gym:<tag>` lokal nachpruefbar).
  - GitHub-Release angelegt mit 5 Asset-Files (UI-
    Pruefung).
  - SBOM-Asset enthaelt korrekten Image-Digest-Bezug.
  - `:latest`-Tag nur bei Tag-Push, NICHT bei
    workflow_dispatch (ADR 0042 §2.3 + F3-Korrektur aus
    Welle-2-Post-Closure-Review-Folge).
- **Slice-Doc**:
  - `done/M6-welle-2.md §9 DoD` Box „Reale Workflow-Run-
    Verifikation" auf `[x]` mit Sensor-Run-Hash + Run-ID-
    Pointer + GHCR-Image-Digest-Beleg.

## Aktivierung

Aktivierung erfolgt sobald **eine** der folgenden
Bedingungen eintritt:

1. **Erster echter Release-Tag** (`v0.1.0` oder erste
   `v*.*.*`-Veroeffentlichung) wird gepusht.
2. **M6-Welle-3-C0** (CI/CD-Vollausbau) entscheidet,
   ob Sensor-Run als Welle-3-Pre-Substanz oder als
   spaetere Operation lebt.
3. **Stakeholder-Druck** (z. B. erstes
   Compliance-Audit) verlangt einen produktiven Release-
   Lauf.

## Konsequenz wenn ungeloest

- ADR-0042-Substanz bleibt **substantiell verifiziert
  aber nicht produktiv-bewiesen**: SBOM-Tool gegen
  Runtime-Image (lokal verifiziert), Release-Workflow-
  Form (actionlint + shellcheck gruen), Asset-Extraktion
  (lokal verifiziert) — aber das End-to-End-GitHub-
  Mechanismus-Substrat ist unbestaetigt.
- 5 GitHub-Actions-Standard-Pattern-Klassen bleiben
  Restrisiko-behaftet (siehe
  [`../done/M6-welle-2.md §10.3`](../done/M6-welle-2.md)):
  GHCR-Push-Permission, Release-Create, Artifact-Sharing,
  Tag-Trigger-Routing, workflow_dispatch-Input-Wiring.
  Alle sind millionenfach-vorbild-getestet im OSS-
  Ecosystem; **kein grid-gym-spezifisches Risiko**.

## Bezuege

- [`../done/M6-welle-2.md §9 DoD`](../done/M6-welle-2.md)
  — 1 verbleibendes DoD-Item nach Welle-2-C4b-Closure.
- [`../done/M6-welle-2.md §10.3`](../done/M6-welle-2.md)
  — Restrisiko-Inventar mit 5 GitHub-Actions-Standard-
  Pattern-Klassen.
- [`../../adr/0042-sbom-tool-and-release-pattern.md §5`](../../adr/0042-sbom-tool-and-release-pattern.md)
  — Welle-2-C2-Hash-Anchor + Welle-2-C3-Substanz +
  M6-Welle-7-Closure-Accept-Plan.
- [`../../../../.github/workflows/release.yml`](../../../../.github/workflows/release.yml)
  — Workflow-Substanz (Sensor-Ziel).
- [`../../../../README.md`](../../../../README.md) +
  [`../../../../README.de.md`](../../../../README.de.md)
  — User-Doku zum Release-Workflow.
