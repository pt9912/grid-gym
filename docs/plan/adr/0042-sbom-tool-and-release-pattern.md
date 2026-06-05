# ADR 0042 — SBOM-Tool + Release-Workflow-Pattern (M6 Welle 2)

**Status:** Provisional — direkter `Proposed → Provisional`-
Sprung in M6-Welle-2-C1 (dieser ADR) zusammen mit Trigger-
008-Hash-Anchor-Block (M5-Welle-0-C2-Triage `112efd3` =
Trigger-Eroeffnungs-Stand; M6-Welle-0-C2-Triage `74d9452`
= `Active in M6-Welle-X`-Markierung; M6-Welle-2-C2 =
Aufloesungs-Hash, in C3 nachgetragen). `Accepted` folgt in
M6-Welle-7-Closure-C1 gebuendelt mit ADR 0041 + ADR 0043
(Pattern analog M5-Welle-7-C1 `62f988d`).
**Datum:** 2026-06-05
**Status geaendert am:** 2026-06-05 — `Proposed →
Provisional` mit M6-Welle-2-C1 (dieser Commit).
**Bezug:**
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Schaerfung-
ohne-Supersedes-Pattern — ADR 0042 verankert ein Quality-
Gate-Pattern fuer `make sbom` + Release-Workflow neben den
ADR-0002-§A-1-Gate-Vertraegen, ohne ADR 0002 textlich zu
beruehren),
[`ADR 0028`](0028-link-maintenance-accepted-adr-bezug.md)
(Link-Maintenance fuer Accepted-ADR-Bezuege),
[`ADR 0029`](0029-no-coverage-pragma-contract.md) (Quality-
Gate-Vertrag-Pattern-Vorbild — ADR 0029 fixiert die
Coverage-Gate-Disziplin als wiederverwendbaren A-1-
Vertrag, ADR 0042 folgt derselben Form fuer den Release-
Workflow-Gate),
[`ADR 0043`](0043-image-audit-strategy.md) (Schwester-
Pattern Quality-Gate-Vertrag fuer Trivy-Image-Audit;
ADR 0042 und ADR 0043 leben parallel ohne Tool-Konflikt —
Syft fuer SBOM-Generierung, Trivy fuer Vuln-Scanning),
[Trigger 008](../planning/done/008-sbom-activation.md)
(SBOM-Aktivierungs-Anker; M5-Welle-0-Eroeffnung +
M6-Welle-0-C2-`Active`-Markierung; in M6-Welle-2-C3 nach
`done/` gewandert).

---

## 1. Kontext

[`GG-CICD-007`](../../../spec/lastenheft.md) SOLLTE-
Akzeptanz verlangt: „Wenn Artefakterzeugung aktiviert ist,
veroeffentlicht die Pipeline Container-Images, Test-
berichte, Coverage-Berichte, OpenAPI-Spezifikation und
Demo-Abnahmeartefakte." Vor dieser ADR existierte im
Repo:

- **`Makefile` Z.455-464 `make sbom`-Target**: nutzt
  `anchore/syft:v1.17.0` mit cyclonedx-json-Output;
  VERSION-Parameter Pflicht (`make sbom VERSION=v0.1.0`);
  produziert `artifacts/sbom-vN.cdx.json`. **Scan-Ziel
  war `dir:/src`** (Source-Tree-SBOM, nicht Runtime-
  Image-SBOM); bisher **nicht in `make ci`/`make
  fullbuild` integriert** — reines Hilfs-Target.
- **`.github/workflows/ci.yml`**: einziger GitHub-
  Actions-Workflow im Repo; deckt vier A-1-Pflicht-Gates
  (lint, format-check, typecheck, arch-check). **Kein
  Release-Workflow vorhanden**.
- **Trigger 008** ([`done/008-sbom-activation.md`](../planning/done/008-sbom-activation.md))
  in M5-Welle-0-C2 eroeffnet (`112efd3`) + M6-Welle-0-
  C2-Triage `74d9452` als `Active in M6-Welle-2`
  markiert.

**Welle-2-C0-Pre-C0c-Probe** (siehe
[`../planning/done/M6-welle-2.md §1.2`](../planning/done/M6-welle-2.md)):

- **Trivy 0.58.0** vs. **Syft v1.17.0** gegen denselben
  `grid-gym-runtime:latest`-Image cache-frei verglichen.
- Beide produzieren **CycloneDX v1.6** ohne Format-Drift.
- Trivy: 164 Komponenten (163 library + 1 OS; Original-
  METADATA-Naming).
- Syft: 169 Komponenten (167 library + 1 OS + 1
  application + 6× „Simple Launcher"-wheel-Entries;
  PEP-503-normalisiertes Naming).
- Beide listen funktional dieselben Python-Pakete; keine
  Security-/SBOM-Substanz-Unterschiede.

Das ist eine A-1-Lueck: ein zukuenftiger Reviewer kann
nicht aus Accepted-ADRs ableiten, wie der SBOM-Workflow,
das Release-Asset-Bundling und das Container-Registry-
Pattern verankert sind. ADR 0042 schliesst diese Lueck
analog ADR 0043 fuer den Image-Audit-Gate.

---

## 2. Entscheidung

ADR 0042 fixiert vier orthogonale Punkte (Welle-2-D-1..
D-4, konsolidiert aus
[`../planning/done/M6-welle-2.md §3`](../planning/done/M6-welle-2.md)):

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
**6 publizierte Artefakte pro Release** (kanonische
Begrifflichkeit; siehe
[`../planning/done/M6-welle-2.md §1.3`](../planning/done/M6-welle-2.md)):

1. **1× GHCR-Push** (Container-Image): `ghcr.io/<owner>/
   grid-gym:<tag>` + `latest` falls Default-Branch; via
   `docker/build-push-action`.
2. **5× GitHub-Release-Asset-Files**:
   - SBOM-CycloneDX-JSON (`sbom-v<X>.cdx.json`).
   - Test-Reports-JUnit-XML (`test-results-v<X>.xml`).
   - Coverage-HTML-Tarball (`coverage-html-v<X>.tar.gz`).
   - OpenAPI-JSON (`openapi-v<X>.json`).
   - Demo-Abnahme-Markdown (`gg-demo-008-abnahme-v<X>.md`;
     direkt-kopiert aus `docs/user/gg-demo-008-abnahme.md`).

Asset-Klassen-Mapping zu `GG-CICD-007`-Lastenheft-
Akzeptanz:

| Lastenheft-Klasse | Asset-Form |
| ----------------- | ---------- |
| Container-Images | GHCR-Push |
| Testberichte | JUnit-XML |
| Coverage-Berichte | HTML-Tarball |
| OpenAPI-Spezifikation | JSON |
| Demo-Abnahmeartefakte | Markdown |

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
Multi-Architektur-Build (linux/arm64) ist M7+-Material;
Welle 2 publiziert `linux/amd64`-only.

---

## 3. Begruendung

- **Release-Workflow-Disziplin ist Gate-bezogen, nicht
  stylistisch.** Die vier Knoebe (SBOM-Tool/Scan-Ziel,
  Trigger-Form, Asset-Bundling, Container-Registry) sind
  die einzigen produktionsrelevanten Mechanismen, mit
  denen man einen Release-Workflow scope-konform halten
  kann. Beide Knoebe explizit als ADR-Bestandteil zu
  verankern verhindert stilles Drift (z. B. eines
  Source-Tree-SBOM statt Runtime-Image-SBOM — siehe
  M6-Welle-2-C0-Review-Folge F1-Korrektur).
- **Runtime-Image-Scan-Ziel** spiegelt die Trigger-008-
  Erwartung („SBOM enthaelt Runtime-Dependencies und
  Container-Image"). Ein Source-Tree-SBOM zeigt
  Entwicklungs-Dependencies, kein produktives Runtime-
  Bild. Welle-1-ADR-0043 verankert Trivy gegen dasselbe
  Runtime-Image-Ziel; ADR 0042 folgt derselben Scan-
  Ziel-Convention.
- **Pre-C0c-Probe-Beleg fuer Syft-Wahl.** Trivy und Syft
  sind funktional aequivalent; Syft ist Status quo +
  PEP-503-Naming-Konvention (Python-Packaging-Standard).
  Tool-Wechsel haette Re-Verifikations-Kosten ohne
  klaren Mehrwert; ADR-0043-Trivy-Verankerung fuer
  image-audit bleibt unberuehrt (Tools fuer
  unterschiedliche Aufgaben).
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

- ADR 0002 bleibt textlich unveraendert (Accepted-
  Immutability per ADR 0006 §3). ADR 0042 ist ein
  separater Quality-Gate-Vertrag, kein §A-1-Eintrag.
- `Makefile` Z.452-471 wird in Welle-2-C2 `235395e`
  geschaerft:
  - Scan-Ziel-Umstellung `dir:/src` → `grid-gym-
    runtime:latest`.
  - `sbom: build`-Dependency-Hinzufuegung (analog
    `image-audit: build`).
  - VERSION-Default aus `pyproject.toml [project]
    version` via `PYPROJECT_VERSION`-Make-Variable
    mit `v`-Prefix-Konvention.
  - **`make openapi-export`-Target nicht angelegt**
    (Slice-Doc §10.1 Realization-Note); `openapi-
    validate`-Stage exportiert bereits, separater
    `openapi-export`-Target waere redundante Tooling-
    Duplikation.
- `Dockerfile` Z.206-211 (`test-unit`-Stage) + Z.244-
  247 (`coverage-gate`-Stage) werden in Welle-2-C2
  `235395e` geschaerft (Asset-Klassen 3 + 4 Export):
  - `test-unit` mit NEU `mkdir -p /src/coverage` +
    `--junitxml=/src/coverage/test-results.xml`.
  - `coverage-gate` mit zusaetzlichem `--cov-report=
    html:/src/coverage/htmlcov`-Block.
- `.github/workflows/release.yml` ist NEU in Welle-2-C2
  `235395e` (~165 Zeilen YAML; 3-Job-Pipeline; siehe
  §2.2-§2.3).
- `.gitignore` Erweiterung um `artifacts/`-Block in
  Welle-2-C2 `235395e` (Build-Output-Schutz).
- ADR 0042 wird im ADR-Index unter ADR 0043 in der
  Aktive-ADRs-Tabelle eingefuegt (Welle-2-C1, dieser
  Commit) — ohne Schaerfungs-Spalten-Eintrag in ADR
  0029, 0043 oder 0002, weil ADR 0042 ein eigenstaendiger
  Vertrag und keine Schaerfung an einem bestehenden
  Vertrag ist.
- Trigger 008 ist der konkrete Erst-Anwendungsfall des
  §2.2-Trigger-Patterns + §2.3-Asset-Patterns. M6-
  Welle-2-C3 verankert den Aufloesungs-Hash (Welle-2-
  C2-Commit) in §5 dieser ADR als Hash-Anchor-Block.

---

## 5. Operative Artefakte (Erstanwendung in M6-Welle-2)

Mit dieser ADR sind die folgenden Welle-2-Substanz-Items
verbunden:

1. **M6-Welle-2-C1** (`4b1062b`):
   - NEU `docs/plan/adr/0042-sbom-tool-and-release-
     pattern.md` (`Provisional`, dieser Text).
   - `docs/plan/adr/README.md` Aktive-ADRs-Tabelle um
     ADR-0042-Zeile ergaenzt (Hard Rule per `harness/
     README.md` Z.81; Pattern analog Welle-1-C0-Review-
     Folge-2 `cff5944`).

2. **M6-Welle-2-C2** (`235395e`; Code-Merge):
   - `Makefile` Z.452-471 Schaerfung: `make sbom` Scan-
     Ziel von `dir:/src` auf `grid-gym-runtime:latest`
     umgestellt + `sbom: build`-Dependency analog
     `image-audit: build` (Z.279) + NEU `PYPROJECT_
     VERSION`-Make-Variable mit `v`-Prefix-Default.
   - `Dockerfile` Z.206-211 + Z.244-247 Stage-Edits:
     `test-unit` mit `--junitxml=/src/coverage/test-
     results.xml`; `coverage-gate` mit zusaetzlichem
     `--cov-report=html:/src/coverage/htmlcov`.
   - NEU `.github/workflows/release.yml` (~165 Zeilen
     YAML; 3 Jobs: build-and-publish-image / produce-
     assets / create-release) mit 1 GHCR-Push + 5
     Release-Asset-Files.
   - NEU `.gitignore` `artifacts/`-Block (Release-
     Workflow-Artifacts; Build-Output, kein Source).
   - **Plan-Abweichung (Slice-Doc §10.1 Realization-
     Note):** `make openapi-export`-Target **nicht**
     angelegt — bestehender `openapi-validate`-Stage
     (`Dockerfile` Z.353-358) exportiert bereits
     `/src/artifacts/openapi.json`; Workflow nutzt
     `make openapi-validate` direkt und extrahiert via
     `docker cp`.
   - **Verifikation (lokal vor C2-Push):** `make gates`
     EXIT=0; `make fullbuild` EXIT=0; `make sbom` ohne
     explizites VERSION produziert `artifacts/sbom-
     v0.1.0.cdx.json` (498 KB, CycloneDX v1.6, 169
     Komponenten; Runtime-Image-Scan). Asset-
     Extraktionen lokal validiert (JUnit-XML 1722
     tests, Coverage-HTML 9.2 MB, OpenAPI-JSON 15
     paths, Demo-Abnahme-MD).

3. **M6-Welle-2-C3** (dieser Commit; Closure-Sync):
   - **Hash-Anchor-Block** (dieser Block in §5): Welle-2-
     C2 = `235395e` als Trigger-008-Aufloesungs-Beleg.
   - `git mv open/008-sbom-activation.md → done/008-
     sbom-activation.md` (rename-only; Bezug-Refs in
     dieser ADR `§0 Bezug` + `§1 Kontext` auf
     `../planning/done/` umgestellt — Pattern analog ADR
     0043-C3 in M6-Welle-1-C3 `4517614`; Provisional-
     Edit-Pattern erlaubt; ADR-0006-§3-Accepted-
     Immutability greift erst ab M6-Welle-7-Closure-C1).
   - Done-Trigger-008-Datei mit Closure-Notiz-Block
     (Pattern analog Trigger 010 in M6-Welle-1-C3-
     Review-Folge `1029249`).
   - `carveouts.md §2.5` Trigger-008-Eintrag auf
     `Aufgeloest in M6-Welle-2-C2 235395e`.
   - Top-Level-Doku-Sync (`README.md`/`README.de.md`
     NEU Release-Workflow-Hinweis + `make sbom`-Scan-
     Ziel-Praezisierung; `roadmap.md §3 M6` aktive-
     Welle-Block auf M6-Welle-3 + Welle-2-Abschluss-
     Notiz).
   - `M6-welle-2.md` Status `In Progress → Done` mit
     Liefer-Hash-Stack.
   - `M6-perf-security-cicd.md §3.1` Welle-2-Zeile
     `In Progress → Done` mit Closure-Hash.
   - **Reale Workflow-Run-Sensor-Check** (Pattern analog
     Welle-1-D-1-Mitzieh-Variante): Manual-`workflow_
     dispatch`-Run gegen C2-Hash + Pre-Release-Tag wird
     nach Push der C2/C3-Hashes als Folge-Schritt
     verifiziert.

4. **M6-Welle-7-Closure-C1** (Folge-Welle):
   - ADR 0042 `Provisional → Accepted` gebuendelt mit
     ADR 0041 + ADR 0043 (Pattern analog M5-Welle-7-C1
     `62f988d`).

`make gates` bleibt cache-frei gruen ohne Override in C1 +
C2 + C3 (10/10 A-1-Gates; Test-Counts bleiben 1722/80 +
4 skipped — Welle 2 fuegt keine neuen Tests hinzu, nur
Test-Runner-Output-Format wird geschaerft).

---

## 6. Konsequenzen

- **Positiv:** `make sbom` ist explizit als ADR-
  verankerter Pflicht-Gate gefuehrt mit Runtime-Image-
  Scan-Ziel. Reviewer koennen aus Accepted-ADRs ableiten,
  dass ein Source-Tree-SBOM **nicht** die Trigger-008-
  Akzeptanz erfuellt; ADR-Bruch ist explizit definiert
  (Tool-Wechsel ohne ADR-Schaerfung).
- **Positiv:** Trigger-008-Aufloesung produktiv mit
  Welle-2-C2 — `GG-CICD-007` SOLLTE-Akzeptanz erfuellt
  mit 5 publizierten Lastenheft-Klassen.
- **Positiv:** Release-Workflow ist kanonisch verankert;
  ein spaeterer Workflow-Edit (z. B. zusaetzliche Asset-
  Klasse, Manual-Approval-Step) ist als ADR-Schaerfung
  per ADR-0011-Pattern moeglich, ohne ADR 0042 zu
  brechen.
- **Positiv:** Hybrid-Trigger-Form ermoeglicht Workflow-
  Re-Runs bei Bugs ohne Tag-Pollution; concurrency-
  Block verhindert parallele Laeufe.
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
  Material. Probe-Substanz aus Welle-2-C0-Pre-C0c
  belegt funktionale Aequivalenz; ein Wechsel braucht
  *substanziellen Mehrwert* + Re-Verifikations-Cost-
  Begruendung.

---

## 7. Nicht Gegenstand dieser ADR

- **Wahl des SBOM-Tools** ueber Syft hinaus (Trivy,
  Grype, Cyclone-DX-CLI etc.). `Makefile` Z.455
  `SYFT_IMAGE ?= anchore/syft:v1.17.0` ist die Default-
  Wahl; Wechsel waere ADR-pflichtig (M7+ Tooling-Slice
  oder ADR-0042-Schaerfung).
- **SPDX-Format als zusaetzliche SBOM-Variante**.
  CycloneDX bleibt Pflicht; SPDX-Co-Generierung waere
  ADR-Schaerfung.
- **CI-Pflicht-Gate fuer `make sbom`** in `ci.yml`.
  `make sbom` ist heute `make ci`-/`make fullbuild`-
  unabhaengig; ein CI-Pflicht-Gate waere Welle-3-CI-
  Vollausbau-Material (analog Trigger 031 fuer `make
  fullbuild`-CI-Gate).
- **Container-Image-Signing (Cosign/Notation)**. M7+
  oder Welle-5-Security-Audit-Material (`GG-SAFE-*`).
- **Release-Notes-Auto-Generierung** ueber `git log` oder
  Conventional-Commits-Parser. Welle 2 nutzt manuelle
  GitHub-Release-Beschreibung; Auto-Generierung waere
  M7+ Tooling-Slice.
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
  Branch-Pattern). Welle 2 nutzt linear-history-Tag-
  Push direkt vom Default-Branch; Branch-Pattern waere
  Workflow-Schaerfung.
