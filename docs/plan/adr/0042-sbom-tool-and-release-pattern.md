# ADR 0042 — SBOM-Tool + Release-Workflow-Pattern (M6 Welle 2)

**Status:** Accepted — gezogen 2026-06-08 mit M6-Welle-7-C1
(dieser Commit; M6-Closure-Welle). Provisional-Schritt
2026-06-05 (direkter `Proposed → Provisional`-Sprung mit
M6-Welle-2-C1).
**Datum:** 2026-06-05
**Status geaendert am:** 2026-06-05 — `Proposed →
Provisional`; 2026-06-08 — `Provisional → Accepted`
(M6-Welle-7-Closure).
**Bezug:**

- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — Lifecycle- und Supersedes-Pflichten, auf denen die
  Schaerfungs-ohne-Supersedes-Form aufbaut.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) —
  Schaerfung-ohne-Supersedes-Pattern; ADR 0042 verankert
  ein Quality-Gate parallel zu ADR 0002 §A-1, ohne ADR 0002
  textlich zu beruehren.
- [`ADR 0028`](0028-link-maintenance-accepted-adr-bezug.md)
  — Link-Maintenance-Pattern fuer ADR-Index- und Bezug-
  Pflege.
- [`ADR 0029`](0029-no-coverage-pragma-contract.md) —
  Schwester-Pattern (Coverage-Gate-Vertrag); ADR 0042 folgt
  derselben Form fuer den Release-Workflow-Gate.
- [`ADR 0043`](0043-image-audit-strategy.md) — Schwester-
  Pattern fuer Trivy-Image-Audit; ADR 0042 und ADR 0043
  leben parallel ohne Tool-Konflikt (Syft fuer SBOM-
  Generierung, Trivy fuer Vuln-Scanning).
- [Trigger 008](../planning/done-archive/008-sbom-activation.md) —
  SBOM-Aktivierungs-Erst-Anwendungsfall.

---

## 1. Kontext

[`GG-CICD-007`](../../../spec/lastenheft.md#gg-cicd-007)
SOLLTE-Akzeptanz verlangt: „Wenn Artefakterzeugung aktiviert
ist, veroeffentlicht die Pipeline Container-Images, Test-
berichte, Coverage-Berichte, OpenAPI-Spezifikation und
Demo-Abnahmeartefakte." Vor dieser ADR existierte im Repo:

- **`make sbom`-Target im `Makefile`**: nutzte
  `anchore/syft:v1.17.0` mit cyclonedx-json-Output und
  Pflicht-VERSION-Parameter (`make sbom VERSION=v0.1.0`),
  Output `artifacts/sbom-vN.cdx.json`. **Scan-Ziel war
  `dir:/src`** (Source-Tree-SBOM, nicht Runtime-Image-
  SBOM); nicht in `make ci`/`make fullbuild` integriert —
  reines Hilfs-Target.
- **`.github/workflows/ci.yml`**: einziger GitHub-Actions-
  Workflow im Repo; deckt vier A-1-Pflicht-Gates (lint,
  format-check, typecheck, arch-check). **Kein Release-
  Workflow vorhanden**.
- **Trigger 008** ([`done/008-sbom-activation.md`](../planning/done-archive/008-sbom-activation.md))
  als SBOM-Aktivierungs-Anker bereits formalisiert.

Das ist eine A-1-Luecke: ein zukuenftiger Reviewer kann
nicht aus Accepted-ADRs ableiten, wie der SBOM-Workflow,
das Release-Asset-Bundling und das Container-Registry-
Pattern verankert sind. ADR 0042 schliesst diese Luecke
analog [ADR 0043](0043-image-audit-strategy.md) fuer den
Image-Audit-Gate.

---

## 2. Entscheidung

ADR 0042 fixiert vier orthogonale Punkte:

**§2.1 SBOM-Tool + Scan-Ziel.** `make sbom` nutzt
**`anchore/syft:v1.17.0`** mit **`cyclonedx-json`**-Output-
Format. Scan-Ziel ist **das Runtime-Image
`grid-gym-runtime:latest`** (nicht Source-Tree), produziert
via `make build`-Dependency. VERSION-Variable steuert den
Output-Pfad (`artifacts/sbom-v<VERSION>.cdx.json`).

Beide Defaults sind **fester Bestandteil** der ADR-0042-
Substanz:

- Tool-Wechsel (z. B. zu Trivy oder Grype) ist ADR-
  pflichtige Schaerfung per ADR-0011-Pattern.
- Format-Wechsel (z. B. zu SPDX) ist ADR-pflichtig.
- Scan-Ziel-Wechsel (z. B. Source-Tree-Sub-SBOM) waere
  zulaessig als *zusaetzliches* Target (`make sbom-
  source`), nicht als Ersatz fuer das Runtime-Image-SBOM.

**§2.2 Release-Workflow-Trigger.** Der Release-Workflow
(`.github/workflows/release.yml`) wird **hybrid** getriggert:

- **Tag-Push** (Pattern `v*.*.*`) — kanonische Semantic-
  Versioning-Trigger-Form; Tag = Release-Version;
  VERSION-Variable wird via `github.ref_name` abgeleitet.
- **Manual `workflow_dispatch`** — Fallback fuer Re-Runs
  bei Workflow-Bugs ohne neuen Tag-Push; verlangt
  expliziten Version-Input.

Beide Trigger-Pfade laufen durch denselben Job-Graph; der
**`concurrency`-Block** (Tag-Pattern als Key) verhindert
parallele Laeufe gegen denselben Tag.

**§2.3 Asset-Bundling.** Der Release-Workflow produziert
**6 publizierte Artefakte pro Release** — 1 GHCR-Push plus
5 GitHub-Release-Asset-Files, gemappt auf die 5
[`GG-CICD-007`](../../../spec/lastenheft.md#gg-cicd-007)-Lastenheft-Klassen:

| Lastenheft-Klasse | Asset-Form | Datei / Ziel |
| ----------------- | ---------- | ------------ |
| Container-Images | GHCR-Push | `ghcr.io/<owner>/grid-gym:<tag>` (`+latest` auf Default-Branch; via `docker/build-push-action`) |
| Testberichte | JUnit-XML | `test-results-v<X>.xml` |
| Coverage-Berichte | HTML-Tarball | `coverage-html-v<X>.tar.gz` |
| OpenAPI-Spezifikation | JSON | `openapi-v<X>.json` |
| Demo-Abnahmeartefakte | Markdown | `gg-demo-008-abnahme-v<X>.md` (direkt-kopiert aus `docs/user/gg-demo-008-abnahme.md`) |
| (SBOM) | CycloneDX-JSON | `sbom-v<X>.cdx.json` (kein eigener Lastenheft-Eintrag — Trigger-008-Substanz; siehe §2.1) |

Bundling-Pattern ist **Separate Files** (kein Single-
Archive). Begruendung: Lastenheft listet die 5 Klassen
einzeln; separate Auslieferung macht jede Klasse einzeln
pruefbar. Coverage-HTML bleibt als Tarball wegen
Verzeichnis-Struktur (~50 Files).

**§2.4 Container-Registry.** Container-Image wird auf
**GHCR** publiziert (`ghcr.io/<owner>/grid-gym`).
Authentifizierung via `GITHUB_TOKEN` mit `permissions:
packages: write`-Workflow-Block; kein externer Secret-
Manager-Aufwand.

GHCR-Visibility-Default folgt der Repository-Visibility
(private bleibt private; public publiziert public).
Multi-Architektur-Build (linux/arm64) ist out-of-scope
dieser ADR; sie pinnt `linux/amd64`-only.

---

## 3. Begruendung

- **Release-Workflow-Disziplin ist Gate-bezogen, nicht
  stylistisch.** Die vier Knoebe (SBOM-Tool/Scan-Ziel,
  Trigger-Form, Asset-Bundling, Container-Registry) sind
  die einzigen produktionsrelevanten Mechanismen, mit
  denen man einen Release-Workflow scope-konform halten
  kann. Beide Knoebe explizit als ADR-Bestandteil zu
  verankern verhindert stilles Drift (z. B. ein Source-
  Tree-SBOM statt Runtime-Image-SBOM).
- **Runtime-Image-Scan-Ziel** spiegelt die Trigger-008-
  Erwartung („SBOM enthaelt Runtime-Dependencies und
  Container-Image"). Ein Source-Tree-SBOM zeigt
  Entwicklungs-Dependencies, kein produktives Runtime-
  Bild. [ADR 0043](0043-image-audit-strategy.md) verankert
  Trivy gegen dasselbe Runtime-Image-Ziel; ADR 0042 folgt
  derselben Scan-Ziel-Convention.
- **Probe-Beleg fuer Syft-Wahl.** Eine vorgelagerte Probe
  verglich Trivy `0.58.0` vs. Syft `v1.17.0` cache-frei
  gegen denselben `grid-gym-runtime:latest`-Image: beide
  produzieren CycloneDX v1.6 ohne Format-Drift; Trivy
  listet 164 Komponenten (163 library + 1 OS, METADATA-
  Naming), Syft 169 (167 library + 1 OS + 1 application
  + 6 wheel-Entries, PEP-503-normalisiertes Naming);
  funktional decken beide dieselben Python-Pakete ab,
  keine Security-/SBOM-Substanz-Unterschiede. Syft ist
  Status quo + PEP-503-Naming-Konvention (Python-
  Packaging-Standard); ein Tool-Wechsel haette Re-
  Verifikations-Kosten ohne klaren Mehrwert. Die ADR-0043-
  Trivy-Verankerung fuer image-audit bleibt unberuehrt
  (Tools fuer unterschiedliche Aufgaben).
- **Hybrid-Trigger-Form** balanciert Standard-Pattern
  (Tag-Push) mit Operations-Realitaet (Manual-Re-Runs
  bei Workflow-Bugs ohne Tag-Pollution). Concurrency-
  Block verhindert parallele Laeufe.
- **Separate-Files-Bundling** vermeidet Asset-Detail-
  Verstecken hinter Archiv-Wrappern; Reviewer koennen
  jede Asset-Klasse einzeln laden + pruefen.
- **GHCR als Registry-Wahl**: kein neuer Secret-Manager-
  Aufwand; identische Visibility-Default mit Repository;
  GHCR ist GitHub-Actions-Docs-Default-Empfehlung.
- **Schwester-Pattern zu ADR 0029 + ADR 0043.** Beide
  fixieren Quality-Gate-Vertraege analog zu ADR 0042:
  - ADR 0029 verbietet Pragmas, die Coverage-Gates
    unterlaufen.
  - ADR 0043 fixiert Image-Audit-Schwellen und Defer-
    Form.
  - ADR 0042 fixiert SBOM-Tool/Scan-Ziel + Release-
    Workflow-Pattern.
  Alle drei folgen demselben „Quality-Gate-Vertrag-
  separat-von-ADR-0002-§A-1"-Pattern.
- **Schaerfung ohne Supersedes (ADR 0011-Pattern).** ADR
  0002 §A-1 listet die A-1-Gates, ohne `make sbom` oder
  Release-Workflow als eigene Vertraege zu fuehren. ADR
  0042 fixiert den Release-Workflow-Vertrag separat,
  ohne ADR 0002 zu beruehren — Pattern konsistent mit
  ADR 0029 + ADR 0043.

---

## 4. Reichweite

- [ADR 0002](0002-language-and-build-stack.md) bleibt
  textlich unveraendert (`Accepted`-Immutability per
  [ADR 0006](0006-adr-lifecycle-superseding-and-process-corrections.md)
  §3). ADR 0042 ist ein separater Quality-Gate-Vertrag,
  kein §A-1-Eintrag.
- `Makefile` `sbom`-Target wird geschaerft:
  - Scan-Ziel-Umstellung `dir:/src` → `grid-gym-
    runtime:latest`.
  - `sbom: build`-Dependency-Hinzufuegung (analog
    `image-audit: build`).
  - VERSION-Default aus `pyproject.toml [project]
    version` via `PYPROJECT_VERSION`-Make-Variable
    mit `v`-Prefix-Konvention.
  - **`make openapi-export`-Target wird NICHT** angelegt
    — der `openapi-validate`-Stage exportiert bereits,
    ein separater `openapi-export`-Target waere
    redundante Tooling-Duplikation.
- `Dockerfile`-Stage-Edits (Asset-Klassen 3 + 4 Export):
  - `test-unit`-Stage mit NEU `mkdir -p /src/coverage` +
    `--junitxml=/src/coverage/test-results.xml`.
  - `coverage-gate`-Stage mit zusaetzlichem
    `--cov-report=html:/src/coverage/htmlcov`-Block.
- NEU `.github/workflows/release.yml` (3-Job-Pipeline;
  siehe §2.2 + §2.3).
- `.gitignore` Erweiterung um `artifacts/`-Block (Build-
  Output-Schutz).
- ADR 0042 wird im ADR-Index unter ADR 0043 in der
  Aktive-ADRs-Tabelle eingefuegt — ohne Schaerfungs-
  Spalten-Eintrag in ADR 0029, 0043 oder 0002, weil
  ADR 0042 ein eigenstaendiger Vertrag und keine
  Schaerfung an einem bestehenden Vertrag ist.
- Trigger 008 ist der konkrete Erst-Anwendungsfall des
  §2.2-Trigger-Patterns + §2.3-Asset-Patterns; der
  Aufloesungs-Hash wird in §5 (Lieferung) ueber die
  zugehoerige Slice-Doc gefuehrt.

---

## 5. Lieferung

Lieferplan, Commit-Hashes und Verifikations-Gates fuer die
Erst-Anwendung der §2-Substanz (Trigger-008-Aufloesung)
leben in der zugehoerigen Slice-Doc
[`M6-welle-2.md`](../planning/done-archive/M6-welle-2.md). Dort sind
die NEU-Files (`.github/workflows/release.yml`,
`.gitignore`-`artifacts/`-Block) und die Edits am
`Makefile`-`sbom`-Target sowie am `Dockerfile` mit
Commit-Hash dokumentiert. Status-Pfad (`Proposed →
Provisional → Accepted`): siehe Status-Header dieser ADR.

---

## 6. Konsequenzen

- **Positiv:** `make sbom` ist explizit als ADR-
  verankerter Pflicht-Gate gefuehrt mit Runtime-Image-
  Scan-Ziel. Reviewer koennen aus Accepted-ADRs ableiten,
  dass ein Source-Tree-SBOM **nicht** die Trigger-008-
  Akzeptanz erfuellt; ADR-Bruch ist explizit definiert
  (Tool-Wechsel ohne ADR-Schaerfung).
- **Positiv:** Trigger-008-Aufloesung wird produktiv —
  [`GG-CICD-007`](../../../spec/lastenheft.md#gg-cicd-007) SOLLTE-Akzeptanz erfuellt mit 5
  publizierten Lastenheft-Klassen.
- **Positiv:** Release-Workflow ist kanonisch verankert;
  ein spaeterer Workflow-Edit (z. B. zusaetzliche Asset-
  Klasse, Manual-Approval-Step) ist als ADR-Schaerfung
  per ADR-0011-Pattern moeglich, ohne ADR 0042 zu
  brechen.
- **Positiv:** Hybrid-Trigger-Form ermoeglicht Workflow-
  Re-Runs bei Bugs ohne Tag-Pollution; concurrency-
  Block verhindert parallele Laeufe.
- **Negativ:** Release-Workflow ist GitHub-Actions- und
  GHCR-spezifisch. `GITHUB_TOKEN` + `packages: write`-
  Permissions sind an die GitHub-Organisations-/
  Repository-Settings gekoppelt; eine Migration weg von
  GitHub (z. B. zu GitLab CI + GitLab Container Registry)
  waere kein Konfig-Edit, sondern ein kompletter Workflow-
  Re-Write plus eine ADR-Schaerfung an §2.2/§2.4.
- **Negativ:** Tag-Push als kanonische Trigger-Form
  setzt voraus, dass Tags konsistent mit `v*.*.*`-
  Pattern und linearer History angelegt werden. Drift
  in der Tagging-Praxis (z. B. Tags ohne `v`-Prefix,
  Tags auf Side-Branches) faengt den Workflow nicht
  ab und kann zu unerwarteten Releases oder zu
  Workflow-Stillstand fuehren.
- **Neutral:** Multi-Architektur-Image-Build
  (`linux/arm64`) ist M7+-Material. Bei spaeterem
  ARM64-Pflicht-Stakeholder-Druck ist eine ADR-
  Schaerfung noetig (`linux/amd64,linux/arm64` als
  Pflicht-Build-Matrix).
- **Neutral:** Container-Registry-Wechsel von GHCR auf
  andere Registry (Docker Hub, AWS ECR, Azure ACR) waere
  ADR-pflichtige Schaerfung. ADR-0042-Default GHCR
  bleibt stabil bis explizit geschaerft.
- **Neutral:** SBOM-Tool-Wechsel von Syft auf Trivy
  (oder Grype, Cyclone-DX-CLI) waere ADR-Schaerfungs-
  Material. Die Probe in §1 belegt funktionale
  Aequivalenz; ein Wechsel braucht *substanziellen
  Mehrwert* + Re-Verifikations-Cost-Begruendung.

---

## 7. Nicht Gegenstand dieser ADR

- **Wahl des SBOM-Tools** ueber Syft hinaus (Trivy,
  Grype, Cyclone-DX-CLI etc.). Der `SYFT_IMAGE`-Default
  im `Makefile` ist die produktive Wahl; ein Wechsel
  waere ADR-pflichtig (separate ADR oder ADR-0042-
  Schaerfung).
- **SPDX-Format als zusaetzliche SBOM-Variante**.
  CycloneDX bleibt Pflicht; SPDX-Co-Generierung waere
  ADR-Schaerfung.
- **CI-Pflicht-Gate fuer `make sbom`** in `ci.yml`.
  `make sbom` ist heute `make ci`-/`make fullbuild`-
  unabhaengig; ein CI-Pflicht-Gate waere Material fuer
  eine spaetere CI-Erweiterungs-Welle (analog Trigger 031
  fuer den `make fullbuild`-CI-Gate).
- **Container-Image-Signing (Cosign/Notation)**.
  Out-of-scope dieser ADR; Material fuer eine spaetere
  Security-Audit-Welle (`GG-SAFE-*`).
- **Release-Notes-Auto-Generierung** ueber `git log` oder
  Conventional-Commits-Parser. Diese ADR setzt manuelle
  GitHub-Release-Beschreibung voraus; Auto-Generierung
  waere separates Tooling-Material.
- **Multi-Architektur-Build** (`linux/arm64`,
  `linux/arm/v7`). `linux/amd64`-only bleibt Default
  bis ARM64-Pflicht-Stakeholder-Druck.
- **Alternative Container-Registries**. GHCR ist
  Default; Multi-Registry-Push waere ADR-Schaerfung.
- **PyPI-Wheel-Publishing**. grid-gym ist primaer als
  Container-Image deployed (per `compose.yml`); PyPI-
  Veroeffentlichung waere separater Slice mit eigener
  `release.yml`-Erweiterung + ADR.
- **Tagged-Release-Branch-Strategy** (release/v1.x-
  Branch-Pattern). Diese ADR nutzt linear-history-Tag-
  Push direkt vom Default-Branch; Branch-Pattern waere
  Workflow-Schaerfung.
