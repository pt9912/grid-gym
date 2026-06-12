# Welle 2 — M6 SBOM-Aktivierung + Release-Workflow (`GG-CICD-007`)

**Status:** Done 2026-06-05 — Liefer-Stack: C0 `0cc28f3`
(Slice-Doc-Anlage) + C0-Review-Folge `69d73d3` (4 Findings:
2 HIGH + 1 MED + 1 LOW) + C0-Review-Folge-2 `63c4cb6` (3
Findings: 2 MED + 1 LOW) + C1 `4b1062b` (NEU ADR 0042
`Provisional` + ADR-Index-Sync) + C2 `235395e` (Code-Merge:
NEU `.github/workflows/release.yml` 3 Jobs + Makefile sbom-
Scan-Ziel-Umstellung + Dockerfile test-unit JUnit-XML +
coverage-gate HTML + `.gitignore` artifacts/-Block + §10
C2-Realization-Notes) + C3 `98a1fa1` (Status/DoD-Sync +
ADR-0042-§5-Hash-Anchor + Trigger-008-`open/ → done/`-Move
+ Top-Level-Doku-Sync) + C3-Sensor-Erweiterung (dieser
Commit; actionlint v1.7.12 + shellcheck via Docker-Images
gegen `release.yml` gruen; §10.3 + §6 + §9 DoD-Box „Lint-
frei" auf [x] mit Restrisiko-Inventar). Welle 2 ist die
**zweite Code-Welle in M6**
nach M6-D-1-Option-B-Vorbelegung („pro Triggerebene": krb5-
Bump + SBOM klein vor CI/CD/Performance/Security gross) und
loest **Trigger 008**
([`../done/008-sbom-activation.md`](008-sbom-activation.md))
durch produktive Aktivierung von `make sbom` plus einen
neuen GitHub-Actions-Release-Workflow auf.

**Pre-C0 abgeschlossen (2 Commits aus M6-Welle-1-Closure-
Folge):**

1. Pre-C0a `1fbd0ac` — `git mv in-progress/M6-welle-1.md
   → done/` (Self-Close-Move, rename-only).
2. Pre-C0b `d51d6e7` — Cross-Doc-Refs-Sync nach Move
   (M6-Welle-1-C4b).

**Pre-C0c-Probe (Trivy vs. Syft SBOM-Tool-Vergleich)** —
ad-hoc als Conversation-Substanz durchgefuehrt (kein
separater Commit). Befunde in §1.2 verankert; ADR-0042-
Decision in §3 Welle-2-D-1 mit Probe-Resultat fixiert.

**Spec-Reife:** Inhaltlich final fuer Welle 2. Welle-2-
Decision-Liste (§3) schliesst die offenen Welle-0-Decision
M6-D-4-Teil (ADR 0042 ja/nein → ja) sowie NEU Welle-2-
spezifische Decisions D-1..D-5 (SBOM-Tool / Release-
Trigger / Asset-Bundling / Container-Registry / Sub-
Slicing).

---

## 1. Context

[`M6-perf-security-cicd.md §3.2 Welle 2`](M6-perf-security-cicd.md)
hat Welle 2 als „SBOM-Aktivierung + Release-Workflow"
vorbelegt mit ADR-Lifecycle-Vorbelegung „NEU ADR 0042
(SBOM-Tool-Wahl) + CI-Hook-Pattern". Welle 2 deckt die
volle [`GG-CICD-007`](../../../../spec/lastenheft.md#gg-cicd-007)-
Akzeptanz ab (5 Asset-Klassen, siehe §1.3).

### 1.1 Existierende Substanz (vor Welle 2)

- **`Makefile` Z.452-464 `make sbom`-Target**: nutzt
  `anchore/syft:v1.17.0` mit cyclonedx-json-Output;
  VERSION-Parameter Pflicht (`make sbom VERSION=v0.1.0`);
  produziert `artifacts/sbom-vN.cdx.json`. Bisher
  **nicht in `make ci`/`make fullbuild` integriert** —
  reines Hilfs-Target.
- **`.github/workflows/ci.yml`**: einziger GitHub-Actions-
  Workflow im Repo; deckt vier A-1-Pflicht-Gates (lint,
  format-check, typecheck, arch-check). **Kein Release-
  Workflow vorhanden**.
- **`make ci`-Pipeline-Outputs** (lokal; F3-Korrektur
  Welle-2-C0-Review-Folge): die existierenden Targets
  sind **partiell unzureichend** fuer Release-Asset-
  Export. Konkret:
  - `Dockerfile` Z.206-207 `test-unit`-Stage hat **kein
    `--junitxml=`-Output** — JUnit-XML-Asset noetigt einen
    Stage-Edit (`--junitxml=/src/coverage/test-results.
    xml`) oder NEU `make test-report`-Target.
  - `Dockerfile` Z.242-246 `coverage-gate`-Stage erzeugt
    nur `coverage.xml` (kein HTML). Coverage-HTML-Asset
    noetigt zusaetzlichen `--cov-report=html:/src/
    coverage/htmlcov`-Block.
  - `Makefile` Z.106 hat `make openapi-validate`
    (validiert nur, exportiert nicht). OpenAPI-JSON-Asset
    noetigt NEU `make openapi-export`-Target oder
    Workflow-Direct-Call (`uv run python -m grid_gym
    ...openapi-export`).

  C2 nimmt diese drei Target-Edits als **Pflichtscope**
  auf (nicht als „nur Wiring").
- **`GG-CICD-007` Akzeptanz** (Lastenheft Z.1825-1827):
  „Wenn Artefakterzeugung aktiviert ist, veroeffentlicht
  die Pipeline Container-Images, Testberichte, Coverage-
  Berichte, OpenAPI-Spezifikation und Demo-Abnahme-
  artefakte."

### 1.2 Pre-C0c-Probe: Trivy vs. Syft SBOM-Vergleich

Probe-Run 2026-06-05 (cache-frei, `grid-gym-runtime:
latest` als Image):

| Tool | Version | CycloneDX | Components | Naming | File-Groesse |
| ---- | ------- | --------- | ---------- | ------ | ------------ |
| Trivy | 0.58.0 | v1.6 | 164 (163 library + 1 OS) | Original-Casing aus METADATA | 290 KB |
| Syft | v1.17.0 | v1.6 | 169 (167 library + 1 OS + 1 application) | PEP-503-normalisiert (lowercase + dash) | 498 KB |

**Befund:** Beide Tools listen funktional dieselben
Python-Pakete; Differenz liegt in:

- **Naming-Casing**: Syft normalisiert nach PEP 503
  (`jinja2`, `pyopenssl`, `sqlalchemy`); Trivy nutzt
  Original-METADATA-Casing (`Jinja2`, `pyOpenSSL`,
  `SQLAlchemy`). Beide Conventions sind valide; PEP-503-
  Form ist die offizielle Python-Packaging-Convention.
- **Syft-Zusatz**: 6× „Simple Launcher"-Entries (wheel-
  console-script-Launcher) plus 1× „application"-Eintrag
  (grid-gym selbst). Trivy listet diese nicht (kosmetisch;
  keine Security-/SBOM-Substanz-Auswirkung).
- **Trivy-Zusatz**: 2× `psycopg_binary`-Eintrag (vermutlich
  aus zwei verschiedenen Locations entdeckt).

Beide Tools produzieren **CycloneDX v1.6** ohne Format-
Drift. Keine relevanten Library-Lücken in einer der
Tools.

### 1.3 Welle-2-Lieferziel — `GG-CICD-007` Vollscope

Acht Sub-Items (geschaerft in C0-Review-Folge; 1 SBOM-
Target-Schaerfung + 1 Release-Workflow + 6 Asset-Klassen-
Sub-Items):

1. **`make sbom` Scan-Ziel-Umstellung** (C2-Pflicht;
   F1-Korrektur Welle-2-C0-Review-Folge): Heute scannt
   `Makefile` Z.461 `dir:/src` (Source-Tree-SBOM); das
   widerspricht Trigger-008-Akzeptanz
   ([`../done/008-sbom-activation.md`](008-sbom-activation.md))
   und §2.1-Decision-Substanz (Container-Image-SBOM).
   C2 stellt den Scan-Befehl auf `grid-gym-runtime:latest`
   um (Pattern `syft <image-tag> -o cyclonedx-json=...`)
   mit voriger `make build`-Dependency. Plus VERSION-
   Default-Schaerfung (aus `pyproject.toml [project]
   version` oder Git-Tag); `make sbom`-Hilfe-Text
   verfeinern; ggf. SBOM-Output-Verifikation
   (`tools/check_sbom.py`-Style) als Pre-Release-Gate.
2. **NEU `.github/workflows/release.yml`**: Tag-Push-
   getriggert (Pattern `v*.*.*`); produziert und
   publiziert alle 5 `GG-CICD-007`-Asset-Klassen.
3. **Asset-Klasse 1 — Container-Image**: via
   `docker/build-push-action` an GHCR (`ghcr.io/<owner>/
   grid-gym`); Tag = Git-Tag + `latest` falls Default-
   Branch.
4. **Asset-Klasse 2 — SBOM (Runtime-Image)**: via `make
   sbom VERSION=...` im Workflow (nach `make build`); Scan-
   Ziel = `grid-gym-runtime:latest`; Upload als GitHub-
   Release-Asset (CycloneDX-JSON).
5. **Asset-Klasse 3 — Test-Reports (JUnit-XML)**: Heute
   hat `Makefile` Z.193-194 `make test-unit` ohne
   JUnit-Export (`Dockerfile` Z.206-207). C2 ergaenzt
   `--junitxml=/src/coverage/test-results.xml` im
   `test-unit`-Stage oder erstellt NEU `make test-report`-
   Target; Workflow lade die XML-Datei hoch.
6. **Asset-Klasse 4 — Coverage-Reports (HTML)**: Heute
   erzeugt `Makefile`/`Dockerfile` Z.242-246
   `coverage.xml` (kein HTML). C2 ergaenzt
   `--cov-report=html:/src/coverage/htmlcov` neben dem
   bestehenden XML-Output; Workflow packe das `htmlcov/`-
   Verzeichnis als `coverage-html-v<X>.tar.gz`.
7. **Asset-Klasse 5 — OpenAPI-Spec (JSON)**: Heute hat
   `Makefile` Z.106 `make openapi-validate` (validiert
   nur, exportiert nicht). C2 fuegt NEU `make openapi-
   export`-Target hinzu (`uv run python -m grid_gym
   ...openapi-export > artifacts/openapi-v<X>.json` oder
   via FastAPI-CLI); Workflow lade JSON-Datei hoch.
8. **Asset-Klasse 6 — Demo-Abnahmedoku** (F2-Korrektur
   Welle-2-C0-Review-Folge): `docs/user/gg-demo-008-
   abnahme.md` wird **direkt als Release-Asset
   hochgeladen** (Markdown-File). `GG-CICD-007`-Akzeptanz
   verlangt „Pipeline veroeffentlicht ... Demo-
   Abnahmeartefakte"; ein blosser Release-Notes-Link
   erfuellt die Veroeffentlichungs-Pflicht nicht. Plus
   ergaenzender Release-Notes-Link auf die Doku in der
   Repo-Anzeige (kein Ersatz fuer Asset-Upload).

Plus **NEU ADR 0042** als Welle-2-C1-Substanz.

**Asset-Klassen-Bilanz** (geschaerft in C0-Review-Folge-2;
F3-Korrektur — kanonische Begrifflichkeit):

- **6 publizierte Artefakte total** pro Release:
  - 1× GHCR-Push (Container-Image; nicht als GitHub-
    Release-Asset, sondern als Registry-Push).
  - 5× GitHub-Release-Asset-Files (SBOM-CycloneDX-JSON
    + Test-Reports-JUnit-XML + Coverage-HTML-Tarball
    + OpenAPI-JSON + Demo-Abnahme-MD).
- **5 Lastenheft-`GG-CICD-007`-Klassen** alle als
  publiziertes Asset abgedeckt (Container-Images +
  Testberichte + Coverage-Berichte + OpenAPI-Spezifikation
  + Demo-Abnahmeartefakte).

Diese Begrifflichkeit (1 GHCR + 5 Release-Asset-Files =
6 Artefakte) wird kanonisch in §3 Welle-2-D-3, §4 C2 +
§9 DoD-Checkliste verwendet.

### 1.4 Welle-2-Anti-Scope

- **Kein CI/CD-Vollausbau** — `make test-unit` /
  `coverage-gate` / `dep-audit` als CI-Pflicht-Jobs +
  Python-3.13/3.14-Matrix bleiben Welle-3-Scope
  (`GG-CICD-001..006`). Welle 2 nutzt die existierenden
  `make`-Targets fuer Asset-Erzeugung, nicht fuer
  CI-Gate-Erweiterung.
- **Kein Performance-Bench** — `GG-RT-005`-Bench ist
  Welle-4-Scope.
- **Kein Security-Audit** — `GG-SAFE-001..008` ist
  Welle-5-Scope (Eingabevalidierung etc.; Welle 2 traegt
  nur den SBOM-Hook, der von Welle-5-Audits genutzt
  wird).
- **Kein Deploy-Hardening-Vollausbau** — `GG-DEPLOY-*`
  bleibt Welle-6-Scope (Container-Smoke + Image-Audit-
  CI-Pflicht-Gate; Welle 2 publiziert das Image, aber
  kein Compose-Smoke).
- **Kein Container-Registry-Auth-Setup** — die GHCR-
  Authentifizierung nutzt das vom GitHub-Actions-
  Standard zur Verfuegung gestellte `GITHUB_TOKEN` mit
  `packages: write`-Permission; kein eigener `docker
  login`-Secret-Manager.
- **Kein Multi-Architektur-Image-Build** — Welle 2
  publiziert `linux/amd64`-only; ARM64-Build ist
  M7+-Material.
- **Keine `Deferred`-Carveout-Aufloesung opportunistisch**
  — die 6 M5-Erbschafts-`Deferred`-Items
  ([`carveouts.md §2.1`](../in-progress/carveouts.md)) bleiben in Welle
  2 unangefasst.

---

## 2. Scope

Welle 2 liefert **vier Items** ueber 4 Commits (C0..C3),
plus Self-Close-Folge C4a/C4b. **Single-Welle-Vorbelegung**
(siehe §3 Welle-2-D-5 Sub-Slicing-Beobachtung).

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses
   Dokument.
2. **NEU ADR 0042** (C1) — `SBOM-Tool-Wahl + Release-
   Workflow-Pattern`. Start als `Provisional` mit
   Trigger-008-Hash-Anchor-Block; bleibt `Provisional`
   nach C3 (Accept in M6-Welle-7-Closure-C1 gebuendelt
   mit ADR 0041 + ADR 0043; Pattern analog M5-Welle-7-C1
   `62f988d`).
3. **Code-Merge** (C2) — NEU
   `.github/workflows/release.yml` mit Tag-Push-Trigger
   + 5 Asset-Klassen; ggf. `Makefile`-`make sbom`-
   Schaerfung (VERSION-Default, Hilfe-Text); ggf. NEU
   `tools/check_sbom.py` Sanity-Pruefer; `make gates`
   + `make ci` + `make fullbuild` cache-frei gruen.
4. **Status/DoD-Sync** (C3) — `M6-welle-2.md` auf `Done`,
   `M6-perf-security-cicd.md §3.1` Welle-2-Zeile auf
   `Done`, ADR 0042 §5 Hash-Anchor-Block mit C2-Hash;
   Trigger 008 `open/ → done/` Move + `carveouts.md
   §2.5` Sync + `open/README.md` Sync; Top-Level-Doku-
   Sync (`README.md`/`README.de.md` Release-Workflow-
   Hinweis; `roadmap.md §3 M6` aktive-Welle-Block auf
   M6-Welle-3 ausrichten).

Self-Close-Folge C4a/C4b laufen nach C3 als M6-Welle-3-
Pre-C0a/Pre-C0b (Pattern analog M6-Welle-1).

---

## 3. Architektur-Entscheidungen (Welle-2-Decision-Liste)

Welle 2 schliesst diese Decisions aus
[`../done/M6-welle-0.md §3`](M6-welle-0.md):

### M6-D-4-Teil — ADR 0042 SBOM-Tool

**Frage:** Wird ADR 0042 (SBOM-Tool-Wahl + CI-Hook) in
M6 erstellt?

Welle-0-Vorbelegung (M6-D-4): **NEU ADR 0042** als
Welle-2-C1-Substanz.

**Welle-2-Final:** **Ja, ADR 0042 wird erstellt** in C1
mit dem Welle-2-D-1 (Tool-Wahl) + Welle-2-D-2 (Release-
Workflow-Pattern) als Hauptdecisions im ADR-Body.

### Welle-2-D-1 — SBOM-Tool-Wahl (Syft vs. Trivy)

**Frage:** Welches Tool fuer `make sbom`?

Optionen (mit Probe-Resultaten aus §1.2):

- **A — Syft** (Status quo): `anchore/syft:v1.17.0` mit
  cyclonedx-json. Bereits im Makefile; PEP-503-Naming;
  167 Library-Komponenten + 1 OS + 1 Application.
- **B — Trivy**: `aquasec/trivy:0.58.0` (bereits durch
  ADR 0043 fuer image-audit verankert) mit `--format
  cyclonedx`. Konsolidierung auf ein Tool; Original-
  METADATA-Naming; 163 Library + 1 OS.

**Welle-2-Final: Option A (Syft).** Begruendung:

- Status-quo-Wahl ohne neue Tool-Dependency.
- PEP-503-Naming-Normalisierung ist die offizielle
  Python-Packaging-Convention; vereinfacht Vergleich mit
  `uv.lock`-Eintraegen + `pip-audit`-Output (`make dep-
  audit`).
- Funktionale Aequivalenz aus Probe (§1.2) — keine
  Security-/SBOM-Substanz-Unterschiede.
- Wechsel haette Re-Verifikations-Kosten + `Makefile`-
  Edit ohne klaren Mehrwert; ADR-0043-`Provisional`-
  Verankerung von Trivy fuer image-audit bleibt
  unberuehrt.

ADR 0042 §2 fixiert Syft + cyclonedx-json + Container-
Image (`runtime`-Stage = `grid-gym-runtime:latest`) als
Scan-Ziel. Versionierung ueber `VERSION`-Variable
(Git-Tag bei Tag-Push; optional Manual-Override).

**Wichtig (F1-Korrektur Welle-2-C0-Review-Folge):** Der
aktuelle `Makefile` Z.461 scannt `dir:/src` — das ist ein
**Source-Tree-SBOM**, kein Runtime-Image-SBOM. Trigger
008 ([`../done/008-sbom-activation.md`](008-sbom-activation.md))
verlangt explizit „SBOM enthaelt alle Runtime-Dependencies
aus `uv.lock` und das Container-Image". C2-Pflicht-Substanz:

- `make sbom` Scan-Befehl von `dir:/src` auf `grid-gym-
  runtime:latest` umstellen (Syft-Aufruf-Form: `syft
  grid-gym-runtime:latest -o cyclonedx-json=...`).
- Build-Dependency hinzufuegen: `sbom: build` (analog
  `image-audit: build` in Z.279).
- Falls ein zusaetzlicher Source-Tree-SBOM gewuenscht
  ist (z. B. fuer Dependency-Audit-Cross-Check), als
  separates Target `make sbom-source` mit eigenem
  Output-File (Welle-2-Pre-Beobachtung; nicht in
  Welle-2-Pflichtscope).

### Welle-2-D-2 — Release-Workflow-Trigger

**Frage:** Welcher Trigger startet den Release-Workflow?

Optionen:

- **A — Tag-Push** (`v*.*.*`-Pattern): klassisches
  Semantic-Versioning-Trigger; Tag = Release-Version.
- **B — Manual `workflow_dispatch`**: Manueller Trigger
  ueber GitHub-UI; flexibler, aber kein Git-Tag-Anker.
- **C — Hybrid (Tag-Push primaer + Manual-Override)**:
  Tag-Push als Default; Manual fuer Re-Run / Hotfix-
  Pattern.

**Welle-2-Final: Option C (Hybrid).** Begruendung:

- Tag-Push ist die kanonische Release-Trigger-Form
  (Standard im OSS-Python-Ecosystem; `setuptools-scm`-
  Pattern; PyPI-Release-Convention).
- Manual `workflow_dispatch` als Fallback fuer Re-Runs
  bei Workflow-Bugs ohne neuen Tag-Push (vermeidet Tag-
  Pollution).
- VERSION-Variable wird aus dem Trigger abgeleitet:
  `github.ref_name` bei Tag-Push, expliziter Input-
  Parameter bei Manual.

### Welle-2-D-3 — Asset-Bundling-Strategie

**Frage:** Wie werden die 5 Asset-Klassen ausgeliefert?

Optionen:

- **A — Separate Files** als GitHub-Release-Assets
  (5 Files: SBOM, test-junit.xml, coverage.html.tar.gz,
  openapi.json, demo-abnahme.md).
- **B — Single-Archive**: alle Assets in einem
  `release-v<X>.tar.gz` gebuendelt.
- **C — Mix**: Container-Image separat (GHCR-Push, kein
  GitHub-Release-Asset); SBOM separat (per `GG-CICD-
  007`-Akzeptanz prominent); Reports/OpenAPI/Demo in
  einem `reports-v<X>.tar.gz`.

**Welle-2-Final: Option A (Separate Files).** Begruendung:

- Lastenheft `GG-CICD-007` listet die 5 Asset-Klassen
  einzeln; separate Auslieferung macht jede Klasse
  einzeln pruefbar.
- Bundle-Archive verstecken Asset-Details vor Reviewers
  (User muss erst entpacken).
- Container-Image ist per GHCR-Push bereits separat
  (kein GitHub-Release-Asset noetig); **5 verbleibende
  Asset-Files** (SBOM + JUnit-XML + Coverage-HTML-Tarball
  + OpenAPI + Demo-Abnahme-MD) als GitHub-Release-Assets.

**F2-Korrektur Welle-2-C0-Review-Folge:** Die initial
in §1.3 Sub-Item 6 vorgesehene „Release-Notes-Link-only"-
Auslieferung der Demo-Abnahmedoku war ein
Lastenheft-`GG-CICD-007`-Drift (Akzeptanz „veroeffentlicht
... Demo-Abnahmeartefakte" wird nicht durch Repository-
internen Markdown-Link erfuellt). C2-Pflicht: `docs/user/
gg-demo-008-abnahme.md` als 5. Release-Asset hochladen
(Markdown-File direkt; kein PDF-Build noetig — User-
Doku-Format ist Markdown-native). Release-Notes traegt
zusaetzlich einen Anker-Link zur Repo-Version der Datei.

Coverage-HTML bleibt im Tarball (Verzeichnis-Struktur
mit ~50 Files; einzelne Files unhandlich).

### Welle-2-D-4 — Container-Registry-Wahl

**Frage:** GHCR vs. Docker Hub vs. selbst-gehostet?

Optionen:

- **A — GHCR** (`ghcr.io/<owner>/grid-gym`): direkt
  ueber `GITHUB_TOKEN` authentifiziert; keine externe
  Account-Pflege; private-by-default mit explizitem
  Public-Toggle.
- **B — Docker Hub** (`docker.io/<owner>/grid-gym`):
  bekanntere Registry; verlangt aber separate Secrets
  (`DOCKERHUB_USERNAME` + `DOCKERHUB_TOKEN`).
- **C — Keine Registry** (Image bleibt lokal-only):
  Anti-Scope per `GG-CICD-007`-Akzeptanz „Container-
  Images veroeffentlicht".

**Welle-2-Final: Option A (GHCR).** Begruendung:

- Kein neuer Secret-Manager-Aufwand (`GITHUB_TOKEN`
  reicht).
- Identische Visibility-Default mit dem Repository
  (private bleibt private; public publiziert public).
- GHCR ist der Default-Empfehlungs-Pfad in
  GitHub-Actions-Docs.

### Welle-2-D-5 — Sub-Slicing-Beobachtung

**Frage:** Wird Welle 2 als Single-Welle oder als
Sub-Slicing 2a/2b geliefert?

**Welle-2-Final (geschaerft in C0-Review-Folge-2): Single-
Welle mit expliziter Ausnahmen-Begruendung.**

**Schwellen-Stand am C0-Review-Folge-2-Stand:**

- **Slice-Doc-Volumen:** 947 Zeilen vor Folge-2-
  Konsolidierung — formal **ueber** der 300-Zeilen-
  Schwelle. **Wachstumsquelle:** Plan-Pflege durch C0-
  Review-Folgen (F1+F2 SBOM-Scan-Ziel + Demo-Asset-Drift,
  F3 Report-Targets), nicht Code-Substanz-Wachstum.
- **Code-Commit-Anzahl:** erwartet 4 (C0/C1/C2/C3) + Self-
  Close-Folge C4a/C4b — unter 5-Commit-Schwelle.
- **Sub-Bereiche:** Welle-2-C0-Review-Folge fuegt
  Pflicht-Substanz in 2 zusaetzlichen Targets-Familien
  hinzu (`make sbom`/`make openapi-export` lokal +
  `Dockerfile` test-unit/coverage-gate-Stages). Plus 1
  `.github/workflows/release.yml` CI-Substanz. Formal
  drei Sub-Bereiche.

**Ausnahmen-Begruendung fuer Single-Welle (statt 2a/2b):**

- **Substanz-Kopplung:** SBOM und Release-Workflow sind
  **kausal verbunden** — der SBOM ist ein *Asset* des
  Release-Workflows, kein eigenstaendiges Lieferziel.
  Trennung 2a (SBOM lokal) / 2b (Release-Workflow + andere
  Assets) wuerde die zentrale `GG-CICD-007`-Akzeptanz
  („Pipeline veroeffentlicht ...") aufspalten, ohne
  Substanz-Mehrwert.
- **Target-Edits als Support-Substanz:** Die 3 Makefile-/
  2 Dockerfile-Edits sind **Asset-Export-Wrapper**, nicht
  eigenstaendige Quality-Gates. Sie haben weder neue
  Quality-Schwellen noch ADR-Substanz; die Edits sind
  in Summe ~30 Zeilen Makefile + ~3 Zeilen Dockerfile.
- **Doc-Volumen ist Plan-Pflege-bedingt, nicht Code-
  bedingt:** Die 947 Zeilen entstehen durch zwei Review-
  Folge-Schaerfungen (F1/F2/F3-Korrekturen + 4 Welle-2-
  Decisions D-1..D-5 mit Optionen + Alternativen-
  Diskussionen). Die Code-Substanz selbst ist weiter
  scope-eng (1 NEU Workflow-YAML + 5 Edit-Hunks in
  Makefile/Dockerfile).
- **Empirische Vorbilder:** M5-Welle-Slice-Docs 368..1319
  Zeilen ohne Sub-Slicing-Pflicht; Doc-Volumen-Schwelle
  ist eine Heuristik mit „voraussichtlich"-Qualifier in
  der Originaldefinition (`M6-perf-security-cicd.md §3`),
  nicht harte Closure-Regel.
- **Schwelle als Plan-Zeit-Heuristik, nicht Closure-Gate:**
  Die >300-Zeilen-Schwelle markiert „wahrscheinlich Sub-
  Slicing noetig" zur Plan-Zeit; tatsaechliche Sub-Slicing-
  Pflicht folgt aus *eigenstaendiger Substanz pro Sub-
  Bereich*, nicht aus Doc-Volumen allein.

**Sub-Slicing-Beobachtung in C2 (Fallback):** Falls die
`release.yml`-Substanz waehrend C2 ueberschwillt (z. B.
wenn GHCR-Push komplexer wird als erwartet ODER wenn ein
Asset-Klassen-Subtarget grundlegend neue Tool-Substanz
braucht — z. B. ein dedizierter SBOM-Verifikations-Schritt
mit eigenem Quality-Gate), wird in C2 nachtraeglich auf
Sub-Slicing 2a (SBOM-Target-Schaerfung + Report-Target-
Edits + ADR 0042) / 2b (Release-Workflow mit allen
Asset-Klassen) gewechselt. C2-Commit-Message dokumentiert
ggf. den Wechsel mit konkreter Begruendung.

Welle 2 trifft **keine** dieser Decisions:

- M6-D-1/D-2/D-3 (Welle-Strategie, Carveout-Triage,
  `Deferred`-Welle-Zuordnung) — bereits in M6-Welle-0-C2
  entschieden.
- M6-D-3b (`Pattern-Forward`) — opportunistisch in
  Welle 5/6.
- M6-D-5 (`make fullbuild`-Drift) — bereits in M6-Welle-
  1-C2 aufgeloest.
- M6-D-6 (Python-3.13/3.14-Matrix) — Welle-3-Scope.
- M6-D-7 (Bench-Framework) — Welle-4-Scope.

---

## 4. Liefer-Reihenfolge (4 Commits + C4a/C4b)

### Pre-C0 — bereits erledigt (M6-Welle-1-Closure-Folge)

- `1fbd0ac` (Pre-C0a: `git mv M6-welle-1.md → done/`).
- `d51d6e7` (Pre-C0b: Cross-Doc-Refs-Sync nach Move).
- **Pre-C0c** (ad-hoc Conversation-Substanz; kein
  separater Commit): Trivy-vs-Syft-SBOM-Probe; Befunde
  in §1.2 verankert.

### C0 — `docs(plan)`: M6-welle-2 Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU [`M6-welle-2.md`](M6-welle-2.md) mit §1..§9-
  Struktur.
- `in-progress/README.md` Bestand-Tabelle um Welle-2-
  Zeile ergaenzt; Aktive-Welle-Block bestaetigt auf
  M6-Welle-2.
- `M6-perf-security-cicd.md §3.1` Welle-2-Zeile `Pending
  → In Progress 2026-06-05`.

### C1 — `docs(adr)`: NEU ADR 0042 SBOM-Tool + Release-Pattern

NEU `docs/plan/adr/0042-sbom-tool-and-release-pattern.md`
als `Provisional` mit:

- §1 Context: `GG-CICD-007`-Akzeptanz + Trigger-008-
  Vorhanden-Substanz (`make sbom` Stub).
- §2 Decision: Welle-2-D-1 (Syft + cyclonedx-json) +
  Welle-2-D-2 (Hybrid Tag-Push + workflow_dispatch) +
  Welle-2-D-3 (Separate Files) + Welle-2-D-4 (GHCR)
  konsolidiert.
- §3 Begruendung: Status-quo-Wahl-Pfad; Pre-C0c-Probe-
  Beleg.
- §4 Reichweite + §5 Operative Artefakte (Welle-2-C2-
  Hash-Anchor-Slot) + §6 Konsequenzen + §7 Out-of-Scope
  (Multi-Arch, andere Registries, alternative Tools).
- Plus `docs/plan/adr/README.md` Aktive-ADRs-Tabelle
  um ADR-0042-Zeile (Hard Rule per `harness/README.md`
  Z.81; Welle-1-C0-Review-Folge-2-Pattern).

### C2 — `feat(ci)`: Release-Workflow + Makefile/Dockerfile-Pflichtscope

Code-Merge mit (alle drei Bloecke **Pflicht**; Konsistenz
mit §5 Critical Files + §9 DoD-Checkliste; F1-Korrektur
Welle-2-C0-Review-Folge-2):

- **NEU `.github/workflows/release.yml`** (Pflicht):
  Tag-Push (`v*.*.*`) + `workflow_dispatch`-Trigger;
  Jobs:
  1. `build-and-publish-image`: `docker/build-push-
     action` → GHCR (`linux/amd64`).
  2. `produce-assets`: `make sbom` + `make test-unit`
     (JUnit-XML-Export) + `make coverage-gate` (HTML-
     Tarball) + `make openapi-export`.
  3. `create-release`: GitHub-Release-Anlage mit allen
     5 Asset-Files (SBOM + JUnit-XML + Coverage-HTML-
     Tarball + OpenAPI-JSON + Demo-Abnahme-MD).
- **`Makefile`-Schaerfung** (Pflicht; F1+F3-Korrektur):
  - `make sbom` Scan-Ziel-Umstellung von `dir:/src`
    (Source-Tree) auf `grid-gym-runtime:latest`
    (Runtime-Image) + `sbom: build`-Dependency analog
    `image-audit: build` (Z.279).
  - `make sbom` VERSION-Default-Schaerfung (aus
    `pyproject.toml [project] version`).
  - NEU `make openapi-export`-Target (analog
    `openapi-validate` aber mit Datei-Output unter
    `artifacts/openapi-v<X>.json`).
- **`Dockerfile`-Schaerfung** (Pflicht; F3-Korrektur):
  - `test-unit`-Stage (Z.206-207) um `--junitxml=/src/
    coverage/test-results.xml` ergaenzen.
  - `coverage-gate`-Stage (Z.242-246) um zusaetzlichen
    `--cov-report=html:/src/coverage/htmlcov`-Block
    ergaenzen.
- **ggf. NEU `tools/check_sbom.py`** (bedingt, nur falls
  Sanity-Pruefer als Pre-Release-Gate substanziell wird):
  Component-Count > 100, CycloneDX-Format-Konformitaet,
  Schluessel-Pakete vorhanden.
- **Verifikation:**
  - `make gates` cache-frei gruen (10/10 A-1-Gates).
  - `make ci` + `make fullbuild` cache-frei gruen.
  - `make sbom VERSION=v0.0.0-welle2-probe` cache-frei
    gruen (lokal-validierbar).
  - `release.yml`-Workflow Syntax-Check via `actionlint`
    oder GitHub-Actions-Lint.
  - **Reale Workflow-Run-Verifikation** in C3 mit Manual
    `workflow_dispatch` gegen Pre-Release-Tag (z. B.
    `v0.0.0-welle2-probe`) — Sensor-Check, nicht nur
    Workflow-Datei-Anwesenheit.
- Falls Sub-Slicing-Beobachtung (§3 Welle-2-D-5) in C2
  ergreift: Welle 2 wandert nach 2a/2b und dieses C2
  wird zu 2a-C2; 2b-Slice-Doc entsteht parallel.

### C3 — `docs(plan)`: Status/DoD-Sync + ADR-0042-Hash-Anchor + Trigger-008-Move

**Welle-2-Closure-Sync.**

- ADR 0042 §5 Operative Artefakte: C2-Hash als Trigger-
  008-Aufloesungs-Beleg in den ADR-Body nachgetragen.
- `M6-welle-2.md` Status `In Progress → Done` mit
  Liefer-Hash-Stack.
- `M6-perf-security-cicd.md §3.1` Welle-2-Zeile `In
  Progress → Done` mit Closure-Hash + Naechster-Slice-
  Block auf Welle 3.
- DoD-Checkliste (§9) abhaken.
- **Trigger 008 `open/ → done/`-Move**: `git mv open/
  008-sbom-activation.md done/`; `carveouts.md §2.5`
  Trigger-Eintrag auf `Aufgeloest in M6-Welle-2`;
  `open/README.md` Trigger-008-Zeile auf `done/`-Pfad +
  `Closed`-Marker.
- **Top-Level-Doku-Sync:**
  - `README.md` + `README.de.md`: NEU Release-Workflow-
    Hinweis (Tag-Push triggert SBOM + Container-Image +
    Reports); `make sbom`-Erwaehnung schaerfen
    (`VERSION=...` jetzt produktiv).
  - `roadmap.md §3 M6` aktive-Welle-Block auf M6-Welle-
    3 (CI-Vollausbau) + Welle-2-Abschluss-Notiz mit
    Hash-Stack.
- **Reale Workflow-Run-Verifikation** vor C3-
  Freigabe: ein Manual-`workflow_dispatch`-Run gegen den
  C2-Hash + Pre-Release-Tag muss gruen sein. Sensor-
  Check-DoD-Item (Pattern analog Welle-1-D-1-Mitzieh-
  Variante).

### Welle-2-Closure-Folge (nach C3, Pattern Welle-6c)

- C4a `git mv M6-welle-2.md → done/` (rename-only).
- C4b Cross-Doc-Refs-Sync nach Move.

C4a/C4b dienen gleichzeitig als M6-Welle-3-Pre-C0a/
Pre-C0b (Pattern analog M6-Welle-1→2).

---

## 5. Critical Files

**Welle-2-NEU (geschrieben in C0/C1/C2):**

- `docs/plan/planning/in-progress/M6-welle-2.md` (C0,
  dieser Commit).
- `docs/plan/adr/0042-sbom-tool-and-release-pattern.md`
  (C1).
- `.github/workflows/release.yml` (C2) — NEU Release-
  Workflow mit Tag-Push + `workflow_dispatch`-Trigger
  + 5 Asset-Klassen.
- `tools/check_sbom.py` (C2, **bedingt** — nur falls
  Sanity-Pruefer als Pre-Release-Gate noetig wird;
  Welle-2-D-1-Konsequenz).

**Welle-2-MODIFY (in C0/C2/C3):**

- `docs/plan/planning/in-progress/README.md` (C0 + C3)
  — Bestand-Tabelle + Aktive-Welle-Block.
- `docs/plan/planning/in-progress/M6-perf-security-
  cicd.md` (C0 + C3) — §3.1 Welle-Status-Tabelle.
- `docs/plan/planning/in-progress/roadmap.md` (C3) — §3
  M6 aktive-Welle-Block + Welle-2-Abschluss-Block.
- `docs/plan/planning/in-progress/carveouts.md` (C3) —
  §2.5 Trigger-008-Eintrag auf `Aufgeloest in M6-Welle-
  2`.
- `docs/plan/planning/open/README.md` (C3) — Trigger-
  008-Zeile auf `done/`-Pfad umgehakt.
- `docs/plan/planning/open/008-sbom-activation.md` →
  `docs/plan/planning/done/008-sbom-activation.md` (C3,
  `git mv` als Teil des C3-Commits; Closure-Notiz-Block
  analog Trigger 010 in M6-Welle-1-C3-Review-Folge).
- `docs/plan/adr/README.md` (C1) — Aktive-ADRs-Tabelle
  um ADR-0042-Zeile (Hard Rule).
- `Makefile` (C2, **Pflicht**; F1+F3-Korrektur Welle-2-
  C0-Review-Folge):
  - `make sbom` Scan-Ziel von `dir:/src` auf `grid-gym-
    runtime:latest` + `sbom: build`-Dependency (F1).
  - `make sbom` VERSION-Default-Schaerfung (aus
    `pyproject.toml [project] version`).
  - NEU `make openapi-export`-Target (F3; analog
    bestehendem `make openapi-validate` aber mit
    Datei-Output unter `artifacts/openapi-v<X>.json`).
- `Dockerfile` (C2, **Pflicht**; F3-Korrektur):
  - `test-unit`-Stage (Z.206-207) um `--junitxml=/src/
    coverage/test-results.xml` ergaenzen.
  - `coverage-gate`-Stage (Z.242-246) um zusaetzlichen
    `--cov-report=html:/src/coverage/htmlcov`-Block
    ergaenzen.
  - Welle-1-Stand bleibt unangetastet (`runtime`-Stage
    + base-Layer); nur die Test-/Coverage-Stages werden
    geschaerft.
- `README.md` + `README.de.md` (C3) — NEU Release-
  Workflow-Hinweis + `make sbom`-Scan-Ziel-Hinweis
  (Runtime-Image) + ggf. NEU `make openapi-export`-
  Eintrag im Top-Level-Make-Listing.

**Welle-2-UNBERUEHRT (kein Edit):**

- Aller Code unter `src/` (Welle 2 ist CI/Doku/Build-
  Tooling-Substanz, kein Python-Code-Pfad-Wechsel).
- Alle Tests unter `tests/` (Test-Counts bleiben
  1722/80; nur Test-Runner-Output-Format geschaerft).
- ADRs 0001..0041 + 0043 (Welle 2 fuegt nur ADR 0042
  hinzu).
- Welle-Slice-Docs unter `done/` (eingefroren modulo
  Cross-Doc-Refs-Sync).

---

## 6. Verifikationspfad

**Welle-2-Gate:**

- `make docs-check` cache-frei gruen ueber alle 4
  Welle-2-Commits + ggf. Review-Folgen.
- `make gates` cache-frei gruen (10/10 A-1-Gates).
- `make ci` cache-frei gruen (gates + test-integration +
  openapi-validate + image-audit).
- `make fullbuild` cache-frei gruen ohne `CRITICAL_COV_
  TARGETS`-Override.
- **`make sbom VERSION=v0.0.0-welle2-probe`** cache-frei
  gruen mit produktivem SBOM-Output unter
  `artifacts/sbom-v0.0.0-welle2-probe.cdx.json`.
- **`release.yml`-Workflow** Lint-frei via Docker-Image-
  Verifikation (C3-Sensor-Erweiterung; siehe §10.3):
  `rhysd/actionlint:latest` (v1.7.12) → „Found 0 errors
  in 2 files" (release.yml + ci.yml). Plus
  `koalaman/shellcheck:stable` auf 5 extrahierte `run:`-
  Bloecke → EXIT=0 ohne SC*-Warnungen. Lokal ohne
  Installation ausfuehrbar.
- **Reale Workflow-Run-Verifikation** (bedingte Folge-
  Operation): Manual `workflow_dispatch`-Run gegen
  C2-Hash + Pre-Release-Tag gruen mit allen 6 Artefakten
  publiziert (Restrisiko-Inventar in §10.3; 5 Klassen
  alle GitHub-Actions-Standard-Patterns).

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur Doc-Substanz.
- C1 prueft ADR-0042-Substanz + Bezug-Refs + ADR-Index-
  Eintrag.
- C2 prueft `release.yml`-Substanz + lokale `make sbom`-
  Lauf + alle bestehenden Gates gruen.
- C3 prueft Status-Flip + ADR-0042-Hash-Anchor + Trigger-
  008-Move + Top-Level-Doku-Sync + Reale Workflow-Run-
  Verifikation.

**Abnahme-Verifikation (Lastenheft):**

- `GG-CICD-007` Akzeptanz „Pipeline veroeffentlicht
  Container-Images, Testberichte, Coverage-Berichte,
  OpenAPI-Spezifikation und Demo-Abnahmeartefakte"
  produktiv erfuellt.
- `make sbom` produktiv aktiv (Trigger 008 aufgeloest).

---

## 7. Risiken

**R1 — GHCR-Publishing-Permission-Drift.** GitHub-Actions
`GITHUB_TOKEN` braucht `packages: write`-Permission im
Workflow-`permissions:`-Block, sonst Push-Fehler.
**Mitigation:** Workflow-Permission-Block explizit
setzen; Lint-Pruefung via `actionlint`.

**R2 — Tag-Push-Race mit `workflow_dispatch`.** Wenn
beide Trigger gleichzeitig laufen, koennte derselbe Tag
zweimal publiziert werden (Race).
**Mitigation:** `release.yml` traegt einen
`concurrency`-Block mit Tag-Pattern; Manual-Dispatch
schlaegt fehl falls Tag-Push parallel laeuft.

**R3 — SBOM-Determinismus.** Syft kann je nach Trivy-DB-
oder Wheel-Layer-Stand leicht differenzierende Outputs
produzieren (Reproducibility-Risiko gegen Diff-Reviews).
**Mitigation:** ADR 0042 §6 dokumentiert die
Determinismus-Erwartung (Best-Effort, nicht byte-
reproduzierbar; Component-Liste reproduzierbar);
Welle-2-C2-Probe mit `make sbom VERSION=...` zweimal
hintereinander gegen denselben Image laufen lassen und
Component-Count-Stabilitaet pruefen.

**R4 — Coverage-HTML-Tarball-Groesse.** `make coverage-
gate` produziert HTML-Reports unter `htmlcov/` mit
~50 Files (kann 5-10 MB sein). GitHub-Release-Asset-
Limit ist 2 GB pro File, also unkritisch — aber Diff-
Review-Belastung bei Asset-Inspektion.
**Mitigation:** Tarball-Komprimierung mit `tar -czf`;
keine weitere Inhalts-Pruefung in Welle 2 (Coverage-
Schwellen sind bereits durch `make coverage-gate`
geprueft).

**R5 — Reale Workflow-Run-Sensor-Check-Latenz.** C3 darf
nicht ohne reale Workflow-Run-Verifikation gemerged
werden; das verlangt eine GitHub-Push-Operation
zwischen C2 und C3 (Push der Welle-2-C2-Commit-Hash
auf einen Pre-Merge-Branch oder via
`workflow_dispatch`).
**Mitigation:** C3-DoD-Item explizit „Sensor-Check, nicht
nur Workflow-Datei-Anwesenheit" markiert; falls Sensor-
Check fehlschlaegt, C2 wird mit Fix-Commit ergaenzt
und Sensor erneut gepruegt vor C3.

**R6 — Sub-Slicing-Schwellen-Ueberschreitung in C2.** Wenn
`release.yml`-Substanz waechst (z. B. Asset-Klassen-
spezifische Sub-Workflows), kann Welle 2 die Sub-
Slicing-Schwelle ueberschreiten.
**Mitigation:** §3 Welle-2-D-5 Sub-Slicing-Beobachtung
verankert die Schwellen-Pruefung; bei Ueberschreitung
wechselt C2 auf 2a/2b mit dokumentierter Begruendung.

**R7 — Demo-Abnahmedoku-Pointer-Stabilitaet.**
`docs/user/gg-demo-008-abnahme.md` (M5-Welle-6c-Liefer-
substanz) wird per `release.yml`-Schritt als Release-
Notes-Anhang verlinkt; ein spaeterer M6/M7-Move dieser
Datei wuerde den Release-Workflow brechen.
**Mitigation:** ADR 0042 §7 markiert Demo-Abnahmedoku-
Pfad als „stabilisiert per `GG-CICD-007`-Pflicht"; ein
spaeterer Move erforderte einen Workflow-Edit + ADR-
Schaerfung.

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack** (per
  [`../README.md`](../README.md) Wave-Self-Close-Commit-
  Konvention): sobald `M6-welle-2.md` Status `Done`
  erreicht (am Ende von C3), schliesst die Welle ihre
  eigene Commit-Sequenz mit einem reinen `git mv
  M6-welle-2.md → ../done/M6-welle-2.md` (C4a) +
  Cross-Doc-Refs-Sync (C4b). Pattern analog M6-Welle-1-
  C4a `1fbd0ac`/C4b `d51d6e7`.
- C4a/C4b dienen gleichzeitig als M6-Welle-3-Pre-C0a/
  Pre-C0b.
- ADR 0042 (NEU in C1) bleibt unter `docs/plan/adr/` —
  ADR-Lifecycle wandert nicht mit dem Slice-Doc.
- Trigger 008 (`open/008-sbom-activation.md`) wandert
  in C3 nach `done/` als Teil des Status-Sync-Commits;
  Pattern analog Trigger 010 in M6-Welle-1-C3.

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **C0 — NEU `M6-welle-2.md`** mit §1..§9-Struktur
  (dieser Commit).
- [x] **C0 — `in-progress/README.md`** Bestand-Tabelle
  um `M6-welle-2.md`-Eintrag ergaenzt + Aktive-Welle-
  Block auf M6-Welle-2 bestaetigt.
- [x] **C0 — `M6-perf-security-cicd.md §3.1`** Welle-2-
  Zeile `Pending → In Progress` mit C0-Hash-Stub.
- [x] **C1 — NEU `docs/plan/adr/0042-sbom-tool-and-
  release-pattern.md`** als `Provisional` mit Trigger-
  008-Hash-Anchor-Block + ADR-Standard-Struktur
  (§1..§7) + Bezug zu ADR 0028 + ADR 0043 (`4b1062b`).
- [x] **C1 — `docs/plan/adr/README.md`** Aktive-ADRs-
  Tabelle um ADR-0042-Zeile ergaenzt (Hard Rule per
  `harness/README.md` Z.81) (`4b1062b`).
- [x] **C2 — NEU `.github/workflows/release.yml`** mit
  Tag-Push + `workflow_dispatch`-Trigger + 3 Jobs
  (build-and-publish-image / produce-assets / create-
  release) + 1 GHCR-Push + 5 GitHub-Release-Asset-Files
  produktiv (SBOM + JUnit-XML + Coverage-HTML-Tarball +
  OpenAPI-JSON + Demo-Abnahme-MD).
- [x] **C2 — `Makefile` `make sbom` Scan-Ziel-Umstellung**
  (F1-Pflicht): Scan-Befehl von `dir:/src` auf
  `grid-gym-runtime:latest` umgestellt + `sbom: build`-
  Dependency analog `image-audit: build` (Z.279) +
  VERSION-Default aus `pyproject.toml [project] version`
  (PYPROJECT_VERSION-Make-Variable). Lokal-Verifikation:
  `make sbom` ohne explizites VERSION produziert
  `artifacts/sbom-v0.1.0.cdx.json` mit Runtime-Image-
  Scan: CycloneDX v1.6, 169 Komponenten (passt zu
  Pre-C0c-Probe-Range).
- [x] **C2 — `Makefile` NEU `make openapi-export`** —
  **n/a (Realization-Note §11.1)**: `openapi-validate`-
  Stage exportiert bereits `/src/artifacts/openapi.json`
  (Dockerfile Z.353-358); ein separates `openapi-export`-
  Target waere redundante Tooling-Duplikation. Workflow
  nutzt `make openapi-validate` direkt und extrahiert
  Artifact per `docker cp` aus dem build-Image.
- [x] **C2 — `Dockerfile` `test-unit`-Stage JUnit-XML**
  (F3-Pflicht): Z.206-209 um `mkdir -p /src/coverage` +
  `--junitxml=/src/coverage/test-results.xml` ergaenzt.
  `make test-unit` produziert JUnit-XML mit `tests=1722,
  failures=0, errors=0, skipped=0`. Test-Counts unveraendert.
- [x] **C2 — `Dockerfile` `coverage-gate`-Stage HTML**
  (F3-Pflicht): Z.247 um zusaetzlichen `--cov-report=
  html:/src/coverage/htmlcov`-Block ergaenzt. `coverage.
  xml` bleibt erhalten (bestehende Branch-Schwelle-Logik
  unangetastet); HTML neu (9.2 MB Verzeichnis mit
  `index.html` etc.) fuer Asset-Auslieferung.
- [x] **C2 — ggf. NEU `tools/check_sbom.py`** — **n/a**
  (bedingt; nicht in Welle 2 angelegt). Begruendung:
  Syft erzeugt cleanes CycloneDX v1.6 ohne erkennbare
  Drift; ein zusaetzlicher Sanity-Pruefer waere Mehrwert
  nur bei Pre-Release-Gate-Pflicht-Substanz, die in
  Welle 2 nicht entsteht. Bei spaeterer Drift-Beobachtung
  kann Welle-3+ das nachziehen.
- [x] **C2 — `make gates`** cache-frei gruen (10/10
  A-1-Gates; EXIT=0; Test-Counts unveraendert 1722/80).
- [x] **C2 — `make ci`** cache-frei gruen (gates +
  test-integration + openapi-validate + image-audit;
  verifiziert via `make fullbuild`-Lauf).
- [x] **C2 — `make fullbuild`** cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override (EXIT=0; `[fullbuild]
  full closure: ci + runtime image + compose smoke green`).
- [x] **C2 — `make sbom`** cache-frei gruen mit
  produktivem CycloneDX-SBOM-Output `artifacts/sbom-
  v0.1.0.cdx.json` (169 Komponenten, CycloneDX v1.6).
- [x] **C2 — `release.yml` Lint-frei** — verifiziert in
  C3-Sensor-Erweiterung (post-`98a1fa1`) via Docker-
  Images (keine lokale Installation noetig):
  - `rhysd/actionlint:latest` (v1.7.12): EXIT=0, „Found
    0 errors in 2 files" (release.yml + ci.yml). Voller
    Action-Schema-Check + Expression-Validitaet +
    Step-ID-Konsistenz.
  - `koalaman/shellcheck:stable` auf die 5 extrahierten
    `run:`-Bloecke: EXIT=0, keine SC*-Warnungen.
  - Siehe §10.3 Realization-Note fuer Restrisiko-
    Inventar.
- [x] **C2 — Sub-Slicing-Beobachtung** entschieden:
  Single-Welle bestaetigt (Welle-2-C0-Review-Folge-2
  hatte die Ausnahmen-Begruendung in §3 Welle-2-D-5
  verankert; C2-Substanz substanziell scope-eng
  geliefert).
- [x] **C3 — ADR 0042** bleibt `Provisional`; C2-Hash
  `235395e` als Trigger-008-Aufloesungs-Beleg in §5 als
  Hash-Anchor-Block nachgetragen + Bezug-Refs in §0/§1
  auf `../planning/in-progress/`-Pfad belassen (Slice-
  Doc noch in `in-progress/` bis Welle-2-C4a/C4b in
  Welle-3-Pre-C0a/Pre-C0b). (`Accepted` passiert in
  M6-Welle-7-Closure-C1 gebuendelt mit ADR 0041/0043.)
- [x] **C3 — `M6-welle-2.md`** Status `In Progress →
  Done 2026-06-05` mit Liefer-Hash-Stack
  `0cc28f3..<C3-Hash>` (dieser Commit).
- [x] **C3 — `M6-perf-security-cicd.md §3.1`** Welle-2-
  Zeile `In Progress → Done` mit Closure-Hash + §3
  Naechster-Slice-Block auf Welle 3 ausgerichtet.
- [x] **C3 — Trigger 008** `git mv open/008-* → done/
  008-*` + `carveouts.md §2.5` (Trigger-Gated →
  Aufgeloest mit C2-Hash) + `open/README.md` (Trigger-
  008-Zeile auf `done/`-Pfad mit `Closed`-Marker) +
  Closure-Notiz-Block im `done/008-...`-Trigger
  (Pattern analog Trigger 010 in Welle-1-C3-Review-
  Folge) + `done/M6-welle-0.md` + `done/M4-protocol-
  adapters.md` Link-Pflege (Pattern analog ADR 0028
  Link-Maintenance).
- [x] **C3 — `README.md` + `README.de.md`** NEU
  Release-Workflow-Hinweis (Tag-Push + GHCR + 5 Asset-
  Files) + `make sbom`-Erwaehnung produktiv geschaerft
  (Runtime-Image-Scan + VERSION-Default aus pyproject).
- [x] **C3 — `roadmap.md §3 M6`** aktive-Welle-Block
  auf M6-Welle-3 (CI/CD-Vollausbau) ausgerichtet +
  Welle-2-Abschluss-Notiz mit Hash-Stack + DoD-
  Checkboxen „SBOM-Generierung im CI" + „Release-
  Workflow `GG-CICD-007`" beide auf `[x]` mit C2-
  Hash-Beleg geflippt.
- [x] **C3 — `in-progress/README.md`** Bestand-Tabelle
  Welle-2-Zeile auf `Done` + Aktive-Welle-Block auf
  M6-Welle-3.
- [ ] **C3 — Reale Workflow-Run-Verifikation**
  (verbleibendes Restrisiko): Manual-`workflow_dispatch`-
  Run gegen C2-Hash + Pre-Release-Tag gruen mit allen 6
  Artefakten veroeffentlicht (Sensor-Check). **Bedingte
  Folge-Operation** nach Push der C3/C4a/C4b-Hashes;
  Restrisiko-Inventar in §10.3 (5 Klassen: GHCR-Push +
  Release-Create + Artifact-Sharing + Tag-Trigger +
  workflow_dispatch-Input — alle GitHub-Actions-Standard-
  Patterns mit Millionen-fachem Vorbild). YAML-/Action-
  Schema-/Shell-Quality bereits ueber actionlint +
  shellcheck-Sensor-Erweiterung lokal-verifiziert.
- [x] **C3 — `make docs-check`** cache-frei gruen ueber
  alle Welle-2-Commits (C0/Review-Folgen/C1/C2/C3
  inkl. Trigger-008-Move + Link-Pflege in done-Docs).

**Anti-Scope-Verifikation (Welle 2 NICHT):**

- [x] Kein CI/CD-Vollausbau (`GG-CICD-001..006` bleibt
  Welle-3-Scope; CI-Pflicht-Gate `test-unit`/
  `coverage-gate`/`dep-audit` als CI-Jobs wandert
  in Welle 3).
- [x] Kein Performance-Bench (Welle-4-Scope; `GG-RT-
  005`).
- [x] Kein Security-Audit (Welle-5-Scope; `GG-SAFE-
  001..008`).
- [x] Kein Deploy-Hardening-Vollausbau (Welle-6-Scope;
  `GG-DEPLOY-*`; Welle 2 publiziert Image ueber GHCR,
  aber kein Compose-Smoke).
- [x] Kein Multi-Arch-Image-Build (M7+-Material).
- [x] Keine Carveout-`Deferred`-Aufloesung opportunis-
  tisch (keine Welle-2-URL-Versionierung `/api/v1`).
- [x] Kein Container-Registry-Wechsel von GHCR auf
  Docker Hub (Welle-2-D-4-Entscheidung).

---

## 10. C2-Realization-Notes (in C2 verankert)

Pattern analog M5-Welle-4a/4b-Realization-Notes-Block.

### 10.1 `make openapi-export` redundant — `openapi-validate` exportiert bereits

**Befund:** Slice-Doc §1.3 + §5 Critical Files + §9 DoD
hatten NEU `make openapi-export`-Target als Pflicht
gefuehrt (F3-Korrektur Welle-2-C0-Review-Folge). Bei
Lokal-Verifikation in C2: der bestehende
`openapi-validate`-Stage (`Dockerfile` Z.353-358) **macht
bereits den Export**:

```dockerfile
RUN mkdir -p /src/artifacts \
 && uv run python -c "import json; from grid_gym.adapters.driving.http_api import app; \
print(json.dumps(app.openapi(), sort_keys=True, indent=2))" \
        > /src/artifacts/openapi.json \
 && uv run openapi-spec-validator /src/artifacts/openapi.json
```

Validierung + Export laufen in derselben Stage; das
Artifact landet unter `/src/artifacts/openapi.json` im
Image. Ein separates `make openapi-export`-Target waere
redundante Tool-Duplikation (dieselbe FastAPI-`app.
openapi()`-Logik in zwei Targets).

**Konsequenz:** Welle-2-C2 legt **kein** `make openapi-
export`-Target an. Der Release-Workflow nutzt `make
openapi-validate` direkt und extrahiert `/src/artifacts/
openapi.json` via `docker create` + `docker cp` aus dem
gebauten Stage-Image (Pattern wie bei test-unit JUnit-
XML + coverage-gate HTML).

**Plan-Abweichung:** §1.3 Sub-Item 7 + §3 Welle-2-D-3
Asset-Klassen-Mapping bleiben textlich unveraendert
(„OpenAPI-JSON-Asset" als Lieferung); §5 Critical Files
+ §9 DoD-Item „make openapi-export" sind als „n/a
(Realization-Note §10.1)"-Marker abgehakt.

### 10.2 SBOM-Output-Probe-Resultat (Validierung der Welle-2-D-1-Decision)

**Befund:** `make sbom` (mit pyproject-Default-VERSION
`v0.1.0`) gegen `grid-gym-runtime:latest` produziert
`artifacts/sbom-v0.1.0.cdx.json`:

- File-Groesse: 498 KB.
- Format: CycloneDX v1.6.
- Komponenten: 169 (passt zu Welle-2-Pre-C0c-Probe-
  Range; siehe §1.2 Probe-Befund).

Damit ist die Welle-2-D-1-Decision (Syft + Runtime-Image-
Scan-Ziel) produktiv verifiziert. Pre-C0c-Probe-Substanz
war Conversation-only; C2 zeigt dass dasselbe Resultat
auch via `make sbom` (Makefile-Pflicht-Target) erzeugbar
ist.

### 10.3 release.yml-Lint-Check via Docker-Image lokal verifiziert (C3-Sensor-Erweiterung)

**Befund (geschaerft in C3-Sensor-Erweiterung post-`98a1fa1`):**
§9 DoD verlangt `release.yml` Lint-frei (`actionlint`
oder GitHub-Actions-Lint). Die initiale C2-Realization-
Notiz hatte „lokal nicht installiert"-Vertagung gefuehrt;
das war ein Faulheitsfehler: **`actionlint` laeuft als
Docker-Image** (`rhysd/actionlint:latest`, aktuell v1.7.12)
ohne lokale Installation. Lokal ausgefuehrt nach C3
`98a1fa1`:

```text
$ docker run --rm -v "$(pwd):/repo" -w /repo \
    rhysd/actionlint:latest -verbose
verbose: Linting 2 files
verbose: Linting .github/workflows/release.yml
verbose: Linting .github/workflows/ci.yml
verbose: Found 0 parse errors in 0 ms for release.yml
verbose: Found 0 parse errors in 0 ms for ci.yml
verbose: Found total 0 errors in 12 ms for release.yml
verbose: Found 0 errors in 2 files
EXIT=0
```

Plus `shellcheck` (`koalaman/shellcheck:stable` Docker-
Image) auf die extrahierten `run:`-Bloecke (5 Shell-
Skripte; build-and-publish-image step1 + 4 produce-
assets-Steps): EXIT=0, keine SC*-Warnungen.

**Damit lokal-verifiziert:**

- YAML-Syntax (Parser + Schema-Validierung).
- Action-Schema-Validierung (`docker/build-push-action@v6`,
  `softprops/action-gh-release@v2`, `actions/upload-
  artifact@v4`, `actions/download-artifact@v4`,
  `docker/login-action@v3`, `actions/checkout@v4`,
  `docker/setup-buildx-action@v3` — alle Inputs/Outputs
  + Versions-Tags valide).
- Expression-Validitaet (`${{ ... }}` Refs auf `inputs`,
  `github`, `needs`, `secrets`, `steps` alle aufgeloest).
- Step-ID-Konsistenz (`steps.resolve-version.outputs.
  version` matcht `id: resolve-version`).
- Embedded-Shell-Quality (kein SC2086, kein SC2129,
  korrekte `>>` mit `"$GITHUB_OUTPUT"`-Quoting).

**Verbleibendes Restrisiko (nur via realen GitHub-Run
testbar):**

| Klasse | Restrisiko |
| ------ | ---------- |
| GHCR-Push-Permission | `GITHUB_TOKEN` mit `permissions: packages: write` — Workflow-Permission-Block ist gesetzt; reale Push-Operation erstmal beim ersten Tag-Push verifiziert. |
| GitHub-Release-Create | `softprops/action-gh-release@v2` Action-Output. Standard-Pattern (millionenfach verwendet); kein bekanntes Konfigurations-Issue. |
| Job-zu-Job-Artifact-Sharing | `actions/upload-artifact@v4` ↔ `actions/download-artifact@v4` mit gleichem `name: release-assets`. Standard-Pattern. |
| Tag-Trigger-Routing | `on.push.tags: ['v*.*.*']` glob-Pattern. Standard. |
| workflow_dispatch-Input-Wiring | `inputs.version` (`required: true`, `type: string`) wird in `resolve-version`-Step gelesen. Standard. |

Alle 5 Restrisiko-Klassen sind **GitHub-Actions-Standard-
Patterns** mit Millionen-fachem Vorbild im OSS-
Ecosystem; keine grid-gym-spezifischen Strukturen.

**Konsequenz:** Die in §9 DoD `[ ] release.yml Lint-frei`-
Box wird auf `[x]` gehoben mit actionlint+shellcheck-
Beleg; die `[ ] Reale Workflow-Run-Verifikation`-Box
bleibt `[ ]` als bedingte Folge-Operation — Restrisiko
ist konkret enumeriert und niedrig.

**Folge-Pfad fuer Sensor-Check:** Beim ersten realen
Release-Tag-Push (`git tag v0.1.0 && git push --tags`)
oder Manual-`workflow_dispatch` gegen einen Pre-Release-
Tag wird der reale Lauf beobachtet; Welle-3-Slice kann
ggf. `actionlint`-Pre-Commit-Hook ergaenzen (Welle-3-D-X-
Material, analog Trigger-007-pyright-precommit-
Vertagungs-Substanz).

### 10.4 Test-Counts unveraendert + Sub-Slicing-Final-Bestaetigung

**Test-Counts:** 1722 Unit + 80 Integration + 4 skipped
am Welle-2-C2-Stand (`grid-gym-test-unit:latest`-Build);
JUnit-XML zeigt explizit `tests=1722, failures=0,
errors=0, skipped=0`. **Test-Counts unveraendert seit
M5-Welle-7-Closure (`5087c8a`).**

**Sub-Slicing-Final (Welle-2-D-5):** C2-Substanz-Volumen
bestaetigt die Single-Welle-Vorbelegung mit Ausnahmen-
Begruendung aus Welle-2-C0-Review-Folge-2. Code-Diff
in C2:

- 1× `Makefile` Hunk (8 Zeilen vor → 19 Zeilen nach;
  Scan-Ziel + Dependency + VERSION-Default-Logik).
- 2× `Dockerfile` Hunks (2 Stages: test-unit + coverage-
  gate; je 1 Zeile zusaetzlich plus Kommentar-Block).
- 1× NEU `.github/workflows/release.yml` (~160 Zeilen
  YAML; 3 Jobs).

Substanz blieb scope-eng wie in §3 Welle-2-D-5
prognostiziert; keine `release.yml`-Substanz-Ueberlauf,
keine Sub-Slicing-Trigger-Ereignisse.

### 10.5 Hash-Anchor-Plan fuer C3

C3-Substanz wird in §5 ADR 0042 verankert:

- C2-Hash (dieser Commit) als Trigger-008-Aufloesungs-
  Beleg.
- `git mv open/008-sbom-activation.md → done/`
  + Closure-Notiz-Block (Pattern analog Trigger 010 in
  Welle-1-C3-Review-Folge).
- `carveouts.md §2.5` Trigger-008-Eintrag auf
  `Aufgeloest in M6-Welle-2-C2`.
- Top-Level-Doku-Sync (`README.md`/`README.de.md` NEU
  Release-Workflow-Hinweis; `roadmap.md §3 M6` aktive-
  Welle auf M6-Welle-3 + Welle-2-Abschluss-Notiz).

### 10.6 Post-Closure-Korrekturen-Index (Pflege nach Welle-2-C4b)

**Pflege-Pattern:** analog ADR 0028 Link-Maintenance. Die
hier dokumentierte Substanz ist Welle-2-Stand zum
C4b-Closure-Zeitpunkt (`b41b7fc`); nach Closure entdeckte
Drifts in der `release.yml`-Substanz werden in Folge-
Commits korrigiert, OHNE die Closure-Substanz oben zu
revidieren. Dieser Index listet die kanonischen Post-
Closure-Korrektur-Hashes — der aktuelle Workflow-Stand
folgt **dem Hash am Ende der Liste**, nicht der §10.3-
Evidence oben.

**Korrektur-Stack** (Pattern analog M5-Welle-4b-Review-
Folge `cd7cfc6`):

| Commit | Stufe | Substanz |
| ------ | ----- | -------- |
| `febbd22` | Folge-1 | F2 SBOM-Digest-Bindung (Refactor Job 1 → SBOM in build-and-publish-image); F3 `:latest` conditional `event_name == 'push'`; F4 Cross-Doc-Drift in 4 in-progress-Stellen; F1 NEU `open/032`-Trigger fuer Sensor-Run. |
| `aeca644` | Folge-2 | F1 SBOM-`sbom: build`-Override-Bug (Direkt-Syft statt `make sbom`); F3 strikteres Conditional (war noch Ancestor); F4 Workflow-Header-Drift + in-progress/README.md:29. |
| `769adc0` | Folge-3 | F1 Syft-Auth (private GHCR; `docker pull` + `docker:`-Prefix); F3 strikter Tip-Match (Ancestor → Tip); F4 workflow_dispatch-Ref-Substanz (NEU `Resolve refs`-Step; alle 3 Jobs nutzen `outputs.ref`); F5 Header-Kommentar conditional. |
| `<this commit>` | Folge-4 | F1 workflow_dispatch-Input-Shell-Injection (env-Pass + strikte SemVer-Regex-Validation); F3 Concurrency-Key auf `inputs.version \|\| ref_name` (statt `github.ref`); F4 §10.6 dieser Index (Evidence-Drift-Aufloesung). |

**Aktueller Workflow-Stand** (Folge-4 + spaeter):

- `Resolve refs`-Step (statt `resolve-version`) ist
  ALLERERSTER Step in `build-and-publish-image`. Outputs:
  `version` + `ref` (beide ueber den ganzen Job-Graph
  konsumiert).
- Step-IDs aktuell: `resolve-refs` /
  `build-push` / `tag-on-default-tip`.
- Embedded-Shell-Bloecke aktuell: `resolve-refs` +
  `tag-on-default-tip` + `Pull pushed image into local
  Docker daemon` + `Generate SBOM via Syft against local
  daemon image` (`docker:`-Prefix Pflicht) + alle 4
  produce-assets-Asset-Extract-Bloecke + Demo-Copy.
- `actions/checkout@v4` ueberall mit `ref:
  ${{ needs.build-and-publish-image.outputs.ref }}` und
  `fetch-depth: 0` im build-and-publish-image.
- Concurrency-Key: `release-${{ github.event.inputs.
  version || github.ref_name }}`.
- workflow_dispatch-Input-Hardening: env-Pass +
  SemVer-Regex `^v[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$`.

**§10.3-Evidence-Aktualisierung (Welle-2-Post-Closure-
Review-Folge-4 F4-Korrektur):** Die in §10.3 oben
zitierte `actionlint`-/`shellcheck`-Output-Evidence
spiegelt den Welle-2-C3-Sensor-Erweiterungs-Stand
(`9815d23`); aktuelle Lint-Verifikation am Post-
Closure-Korrektur-Stand (`<this commit>`):

- `rhysd/actionlint:latest` (v1.7.12): EXIT=0 fuer beide
  Workflows (release.yml + ci.yml) inkl. NEU Steps +
  Outputs + Concurrency-Key-Expression.
- `koalaman/shellcheck:stable` auf alle aktuellen
  `run:`-Bloecke: EXIT=0 (resolve-refs mit env-Pass +
  regex-Validation + tag-on-default-tip mit Tip-SHA-
  Vergleich + docker-pull + docker:-prefix Syft).

**Sensor-Run-Pflicht** (siehe
[`032-release-workflow-sensor-run.md`](032-release-workflow-sensor-run.md)):
unveraendert; die F1+F3+F4-Verifikations-Pflichten sind
in Trigger 032 verankert (drei Klassen).

---

## References

- [`../done/M6-welle-0.md §3 M6-D-4`](M6-welle-0.md)
  — M6-Welle-0-Decision-Liste mit ADR-0042-Vorbelegung
  („NEU ADR 0042 SBOM-Tool + CI-Hook").
- [`../done/M6-welle-1.md`](M6-welle-1.md) —
  M6-Welle-1-Slice-Doc (Pattern-Vorbild fuer Welle-2-C0-
  Struktur; Welle-1-Pre-C0c-Probe-Pattern).
- [`M6-perf-security-cicd.md §3.2 Welle 2`](M6-perf-security-cicd.md)
  — M6-Slice-Plan Welle-2-Vorbelegung.
- [`../done/008-sbom-activation.md`](008-sbom-activation.md)
  — Trigger 008 mit erwarteter Lieferung + Aktivierungs-
  Kriterium („mit der ersten Release-Veroeffentlichung").
- [`../../adr/0043-image-audit-strategy.md`](../../adr/0043-image-audit-strategy.md)
  — ADR-0043-Schwester-Pattern (Quality-Gate-Vertrag fuer
  Trivy-image-audit; ADR-0042-Pattern analog fuer Syft-
  SBOM).
- [`../../adr/0028-link-maintenance-accepted-adr-bezug.md`](../../adr/0028-link-maintenance-accepted-adr-bezug.md)
  — Link-Maintenance-Pattern fuer ADR-0042-Hash-Anchor-
  Block in C3.
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — Schaerfung-ohne-Supersedes-Pattern fuer ADR-0042-
  Erweiterung (ADR 0002 §A-1 bleibt unangefasst; ADR
  0042 ist eigenstaendiger Quality-Gate-Vertrag analog
  ADR 0029/0043).
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md#gg-cicd-007)
  §22 `GG-CICD-007` — Akzeptanz „Pipeline veroeffentlicht
  Container-Images, Testberichte, Coverage-Berichte,
  OpenAPI-Spezifikation und Demo-Abnahmeartefakte".
- [`../../../../Makefile`](../../../../Makefile) Z.452-464
  — bestehender `make sbom`-Target mit Syft-Pin.
- [`../../../../.github/workflows/ci.yml`](../../../../.github/workflows/ci.yml)
  — bestehender CI-Workflow (Welle 2 fuegt
  `release.yml` als Schwester-Workflow hinzu, keine
  Edits an `ci.yml`).
- [`../../../user/gg-demo-008-abnahme.md`](../../../user/gg-demo-008-abnahme.md)
  — Demo-Abnahmedoku (M5-Welle-6c-Lieferung; Asset-
  Klasse 5 fuer Release-Workflow).
