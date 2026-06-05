# ADR 0043 — Image-Audit-Strategie + Trivy-Defer-Aufloesungs-Pattern (M6 Welle 1)

**Status:** Provisional — direkter `Proposed → Provisional`-
Sprung in M6-Welle-1-C1 (dieser ADR) zusammen mit Trigger-
010-Hash-Anchor-Block (M3-Welle-7 `c61ab0d` = Drift-Origin;
M4-Welle-7 = Defer-Pfad-Erbschaft; M6-Welle-1-C2 = Aufloesungs-
Hash, in C3 nachgetragen). `Accepted` folgt in M6-Welle-7-
Closure-C1 gebuendelt mit ADR 0041 + ADR 0042 (Pattern analog
M5-Welle-7-C1 `62f988d`).
**Datum:** 2026-06-05
**Status geaendert am:** 2026-06-05 — `Proposed → Provisional`
mit M6-Welle-1-C1 (dieser Commit).
**Bezug:**
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Schaerfung-
ohne-Supersedes-Pattern — ADR 0043 verankert ein Quality-Gate-
Pattern fuer `make image-audit` neben den ADR-0002-§A-1-Gate-
Vertraegen, ohne ADR 0002 textlich zu beruehren),
[`ADR 0028`](0028-link-maintenance-accepted-adr-bezug.md)
(Link-Maintenance fuer Accepted-ADR-Bezuege),
[`ADR 0029`](0029-no-coverage-pragma-contract.md) (Quality-
Gate-Vertrag-Pattern-Vorbild — ADR 0029 fixiert die Coverage-
Gate-Disziplin als wiederverwendbaren A-1-Vertrag, ADR 0043
folgt derselben Form fuer den Image-Audit-Gate),
[Trigger 010](../planning/done/010-base-image-krb5-cve-bump.md)
(M3/M4/M5-Defer-Pfad — krb5-CVE-Famille seit M3-Welle-7 ohne
Code-Verursacher; in M6-Welle-1-C3 nach `done/` gewandert).

---

## 1. Kontext

`make fullbuild` (`ci + image-audit + test-integration +
openapi-validate`) ist seit M3-Welle-7-Closure `c61ab0d`
(2026-05-25) pre-existing rot. Verursacher ist eine
Familie von vier neuen HIGH-CVEs im Debian-13-Base-Image,
fuehrende ID **`CVE-2026-40356`** in `krb5`-Paketen
(`libkrb5-3`/`libk5crypto3`/`libgssapi-krb5-2`) mit Fix-
Version `1.21.3-5+deb13u1`. Die CVE-Drift ist **nicht durch
M3-/M4-/M5-Code verursacht** — sie ist eine reine Base-
Image-Lieferketten-Drift.

M4-Welle-7-Closure hat das als dokumentierten Defer-Pfad
verankert (siehe
[`done/M4-results.md §2 + §4 S-4`](../planning/done/M4-results.md)).
M5-Welle-0-C2 hat den Defer-Pfad als expliziten Open-Trigger
in [`done/010-base-image-krb5-cve-bump.md`](../planning/done/010-base-image-krb5-cve-bump.md)
formalisiert. M6-Welle-1 loest den Defer-Pfad auf.

Vor dieser ADR war im Repo keine kanonische Image-Audit-
Pflicht-Strategie verankert:

- `make image-audit` ist Pflicht-Gate in `make ci` und
  `make fullbuild` (`Makefile` Z.343).
- Trivy-Konfiguration: `TRIVY_SEVERITY=HIGH,CRITICAL` plus
  `--ignore-unfixed` (`Makefile` Z.25-26 + Z.279-294).
- Defer-Lifecycle: ad-hoc dokumentiert in M3/M4/M5-results-
  §4-S-4-Notes und in `open/010-*`-Trigger, ohne ADR-
  Verankerung welcher Defer-Pfad zulaessig ist.

Das ist eine A-1-Lueck: ein zukuenftiger Reviewer kann
nicht aus Accepted-ADRs ableiten, ob ein `.trivyignore`-
Eintrag, ein `--skip-vuln`-Argument oder ein anderer
Defer-Pfad ADR-konform ist.

---

## 2. Entscheidung

ADR 0043 fixiert drei orthogonale Punkte:

**§2.1 Image-Audit-Pflicht-Schwelle.** Der `make image-audit`-
Pflicht-Gate verlangt einen Trivy-Lauf gegen das `make build`-
Runtime-Image mit den Default-Parametern aus `Makefile`
Z.25-26:

- `TRIVY_SEVERITY=HIGH,CRITICAL` — nur HIGH- und CRITICAL-CVEs
  brechen das Gate; LOW und MEDIUM sind ausgeblendet (kein
  Sensor-Rauschen).
- `--ignore-unfixed` — CVEs ohne verfuegbaren Fix werden aus
  dem Report herausgefiltert (kein „Marker"-Mechanismus,
  sondern Filter im Trivy-Lauf).

Beide Defaults sind **fester Bestandteil** der ADR-0043-
Substanz. Eine Schwellen-Lockerung (z. B. nur CRITICAL)
oder eine Schwellen-Verschaerfung (z. B. MEDIUM mit
einbeziehen) waere ADR-pflichtige Schaerfung per ADR-0011-
Pattern.

**§2.2 Defer-Form fuer HIGH/CRITICAL-CVEs mit Fix.** Die
einzig zulaessige Defer-Form fuer einen `make image-audit`-
Befund mit verfuegbarem Fix ist:

1. Ein `open/`-Trigger im Slice-Lifecycle (Pattern
   [`docs/plan/planning/open/`](../planning/open/)) mit
   konkreter CVE-ID + Fix-Version + dokumentiertem
   Aktivierungs-Pfad. Beispiel: Trigger 010 (`open/010-
   base-image-krb5-cve-bump.md`).
2. Eine Erwaehnung des Defer-Pfads in der jeweiligen
   M-results.md §4-S-4-Note.

Verbotene Defer-Formen (ADR-Bruch):

- Bloss-`.trivyignore`-Eintrag ohne `open/`-Begleit-Trigger.
- Trivy-Argument-Anpassung (`--skip-vuln <CVE>` o.ae.)
  ohne ADR-Schaerfungs-Commit.
- `make image-audit`-Pflicht-Gate-Entfernung aus `make ci`/
  `make fullbuild` ohne ADR-Schaerfungs-Commit.
- Stilles `--ignore-unfixed`-Toggle oder `TRIVY_SEVERITY`-
  Lockerung ohne ADR-Schaerfungs-Commit.

**§2.3 Defer-Aufloesungs-Pattern.** Sobald ein `open/`-
Trigger geloest ist (Code-Stand `make image-audit` cache-
frei gruen), erfolgt im selben Slice-Closure-Commit:

1. `git mv open/<trigger>.md → done/<trigger>.md` (kein
   inhaltlicher Edit beim Move).
2. `carveouts.md`-Sync (Trigger-Eintrag auf `Aufgeloest in
   <Slice-Hash>`).
3. Hash-Anchor-Block im verankernden ADR (ADR 0043 fuer
   Trigger 010; analoge ADRs koennen weitere `open/`-Trigger
   verankern).
4. Top-Level-Doku-Sync falls `README.md`/`README.de.md`/
   `roadmap.md §1` den Defer-Pfad an einer User-sichtbaren
   Stelle erwaehnt haben.

---

## 3. Begruendung

- **Image-Audit-Disziplin ist Gate-bezogen, nicht
  stylistisch.** Die zwei Trivy-Knoebe (Severity-Schwelle,
  unfixed-Filter) sind die einzigen produktionsrelevanten
  Mechanismen, mit denen man einen `make image-audit`-Gate
  technisch gruen halten kann, ohne dass die CVE-Last
  tatsaechlich beseitigt ist. Beide Knoebe explizit als
  ADR-Bestandteil zu verankern verhindert stilles Drift.
- **`open/`-Trigger als einzige Defer-Form** spiegelt die
  Slice-Lifecycle-Disziplin der M3/M4/M5-results §4-S-4-
  Notes. `.trivyignore` wuerde die Defer-Lifecycle aus dem
  sichtbaren Slice-Lifecycle herausziehen — dann ist nicht
  mehr nachvollziehbar, *welcher* Slice einen Defer-Pfad
  geoeffnet hat und *welcher* ihn schliesst.
- **Schwester-Pattern zu ADR 0029.** AC-NO-COVERAGE-PRAGMA
  verbietet Pragma-Annotations, die einen Coverage-Gate
  unterlaufen wuerden, und ist Pflicht in `src/grid_gym/**`.
  ADR 0043 folgt derselben Form fuer den Image-Audit-Gate:
  Defer-Form wird auf eine einzige sichtbare Lifecycle-
  Variante eingeschraenkt; Alternative Wege gelten als
  ADR-Bruch.
- **Schaerfung ohne Supersedes (ADR 0011-Pattern).** ADR
  0002 §A-1 listet die A-1-Gates, ohne `make image-audit`
  als eigenen Vertrag zu fuehren — `image-audit` ist
  `GG-QG-002 SOLLTE` per Lastenheft und in der A-1-Welt
  ueber `make ci`/`make fullbuild` verankert, nicht in der
  10-Contracts-Tabelle. ADR 0043 fixiert den Image-Audit-
  Vertrag separat, ohne ADR 0002 zu beruehren — Pattern
  konsistent mit ADR 0029.

---

## 4. Reichweite

- ADR 0002 bleibt textlich unveraendert (Accepted-
  Immutability per ADR 0006 §3). ADR 0043 ist ein
  separater Quality-Gate-Vertrag, kein §A-1-Eintrag.
- `Makefile` Z.25-26 + Z.279-294 (Trivy-Defaults +
  image-audit-Target) bleiben textlich unveraendert in
  Welle-1-C2 — die ADR verankert nur den existierenden
  Code-Stand als Pflicht-Vertrag.
- ADR 0043 wird im ADR-Index unter ADR 0040 in der
  Aktive-ADRs-Tabelle eingefuegt (Welle-1-C1, dieser
  Commit) — ohne `Schaerfungen / Folge-ADRs`-Eintrag in
  ADR 0029 oder ADR 0002, weil ADR 0043 ein eigenstaendiger
  Vertrag und keine Schaerfung an einem bestehenden Vertrag
  ist.
- Trigger 010 ist der erste konkrete Anwendungsfall des
  §2.2-Defer-Patterns. M6-Welle-1-C3 verankert den
  Aufloesungs-Hash (Welle-1-C2-Commit) in §5 dieser ADR
  als Hash-Anchor-Block.

---

## 5. Operative Artefakte (Erstanwendung in M6-Welle-1)

Mit dieser ADR sind die folgenden Welle-1-Substanz-Items
verbunden:

1. **M6-Welle-1-C1** (`c44e6d5`):
   - NEU `docs/plan/adr/0043-image-audit-strategy.md`
     (`Provisional`, dieser Text).
   - `docs/plan/adr/README.md` Aktive-ADRs-Tabelle um
     ADR-0043-Zeile ergaenzt (Hard Rule per `harness/
     README.md` Z.81).

2. **M6-Welle-1-C2** (`b514170`; Verifikations-Commit ohne
   Code-Edit):
   - **Befund:** Trigger-010-Aufloesung ohne Code-Edit
     durch Upstream-Patch-Drift + Trigger-015-Pattern
     (`Dockerfile` Z.422-426 `apt-get update && apt-get
     upgrade --yes` im `runtime`-Stage). Debian-13.5-
     Security-Mirrors haben den krb5-`1.21.3-5+deb13u1`-
     Fix zwischen 2026-06-01 und 2026-06-05 ausgespielt;
     der bestehende `apt-get upgrade`-Block zieht den
     Fix automatisch beim cache-freien Layer-Rebuild.
   - **Beleg:** `make image-audit` EXIT=0 (`grid-gym-
     runtime:latest (debian 13.5) Total: 0 (HIGH: 0,
     CRITICAL: 0)` + `otel/opentelemetry-collector-
     contrib:0.152.1` clean); `make fullbuild` EXIT=0
     ohne `CRITICAL_COV_TARGETS`-Override.
   - **Welle-1-D-1** vertagt auf M6-Welle-3 (CI-Vollausbau)
     ueber NEU [`../planning/open/031-ci-make-fullbuild-gate.md`](../planning/open/031-ci-make-fullbuild-gate.md).
   - Slice-Doc `M6-welle-1.md` §10 (C2-Realization-Notes)
     verankert die Plan-Abweichung (Null-Code-Edit).

3. **M6-Welle-1-C3** (dieser Commit; Closure-Sync):
   - **Hash-Anchor-Block** (dieser Block in §5): Welle-1-
     C2 = `b514170` als Trigger-010-Aufloesungs-Beleg.
   - `git mv open/010-base-image-krb5-cve-bump.md →
     done/010-base-image-krb5-cve-bump.md` (rename-only;
     Bezug-Refs in dieser ADR `§0 Bezug` + `§1 Kontext`
     auf `../planning/done/` umgestellt — Pattern analog
     ADR 0028 Link-Maintenance fuer `Provisional`-ADR-
     Edits ist erlaubt; `Accepted`-Immutability per
     ADR 0006 §3 greift erst ab M6-Welle-7-Closure-C1).
   - `carveouts.md §2.2` Trigger-010-Eintrag auf
     `Aufgeloest in M6-Welle-1` mit Welle-1-C2-Hash.
   - Top-Level-Doku-Sync (`README.md`/`README.de.md`
     `make fullbuild`-`CVE-2026-40356`-Hinweis aufgeloest;
     `roadmap.md §0` Build-Status-Block + `§1`
     Status-Header-`make fullbuild`-Defer-Pfad-Notiz
     aufgeloest; `roadmap.md §3 M6` aktive-Welle-Block
     auf M6-Welle-2 ausgerichtet).
   - `M6-welle-1.md` Status `In Progress → Done` mit
     Liefer-Hash-Stack.
   - `M6-perf-security-cicd.md §3.1` Welle-1-Zeile
     `In Progress → Done` mit Closure-Hash.

4. **M6-Welle-7-Closure-C1** (Folge-Welle):
   - ADR 0043 `Provisional → Accepted` gebuendelt mit
     ADR 0041 + ADR 0042 (Pattern analog M5-Welle-7-C1
     `62f988d`).

`make gates` bleibt cache-frei gruen ohne Override in C1 +
C2 + C3 (10/10 A-1-Gates; Test-Counts unveraendert
1722/80 — Welle 1 fuegt keine neuen Tests hinzu).

---

## 6. Konsequenzen

- **Positiv:** `make image-audit` ist explizit als ADR-
  verankerter Pflicht-Gate gefuehrt. Reviewer koennen aus
  Accepted-ADRs ableiten, dass `.trivyignore`-Eintraege
  ohne `open/`-Begleit-Trigger ADR-Bruch sind.
- **Positiv:** Trigger-010-Aufloesung loest die `make
  fullbuild`-pre-existing-Drift seit M3-Welle-7 — alle
  vier A-1-Gate-Folge-Lieferungen (`make ci`/`make
  fullbuild`/`make image-audit`/`make gates`) sind cache-
  frei gruen ohne Override.
- **Positiv:** Defer-Lifecycle ist sichtbar im Slice-
  Lifecycle (`open/` → `done/`-Move). Eine CVE, die heute
  ohne Fix-Version ankommt, kann ueber `--ignore-unfixed`
  durchrutschen, ohne Sensor-Rauschen zu erzeugen — sobald
  ein Fix verfuegbar wird, faengt das Gate die CVE auf,
  und ein neuer `open/`-Trigger entsteht.
- **Neutral:** `TRIVY_SEVERITY=HIGH,CRITICAL` ist eine
  bewusste Wahl, die LOW/MEDIUM ausblendet. Bei spaeterer
  Compliance-Druck-Erhoehung (z. B. externe Audit-Pflicht
  auf MEDIUM) ist eine ADR-Schaerfung per ADR-0011-Pattern
  noetig — ADR 0043 bleibt textlich, ein Folge-ADR (z. B.
  ADR 0050) traegt die geschaerfte Schwelle.
- **Neutral:** `--ignore-unfixed` bedeutet, dass Trivy-Reports
  unfixed-CVEs ueberhaupt nicht zeigen. Image-Audit-Sensor
  warnt also nicht bei neu entdeckten unfixed-CVEs; nur
  beim ersten Run nach Fix-Release. Das ist akzeptiert, weil
  die Alternative (alle unfixed-CVEs zeigen) Sensor-Rauschen
  erzeugt, das die Pflege-Aufmerksamkeit von tatsaechlich
  handlungsfaehigen Befunden ablenkt.

---

## 7. Nicht Gegenstand dieser ADR

- **Wahl des Vuln-Scanners** (Trivy vs. Grype vs. Snyk vs.
  GitHub-Dependabot). `Makefile` Z.25 `TRIVY_IMAGE ?=
  aquasec/trivy:0.58.0` ist die Default-Wahl; Wechsel
  waere ADR-pflichtig, aber ausserhalb ADR 0043 (ggf.
  M7+ Tooling-Slice).
- **SBOM-Generierung im Release-Workflow** (`GG-CICD-007`
  + Trigger 008). Ist M6-Welle-2-Scope; ADR 0042 traegt
  die SBOM-Tool-Wahl + CI-Hook-Pattern.
- **CI-Pflicht-Gate fuer `make fullbuild`** in GitHub
  Actions. Ist Welle-1-D-1-Entscheidung; entscheidet sich
  in M6-Welle-1-C2 (Mitziehen vs. Vertagen auf Welle 3).
  ADR 0043 ist orthogonal — sie verankert das Image-Audit-
  Pattern lokal, unabhaengig vom CI-Workflow-Edit.
- **Container-Hardening jenseits Base-Image-CVE-Aufloesung**
  (`GG-DEPLOY-*`-Vollausbau: Container-Smoke-Test mit
  Compose, Healthcheck-Pollung, Read-only-Filesystem,
  User-Capabilities). Ist M6-Welle-6-Scope.
- **`.trivyignore`-Pfad fuer **unfixed**-CVEs.** Trivy
  filtert unfixed-CVEs ueber `--ignore-unfixed` bereits aus
  dem Report; eine zusaetzliche `.trivyignore`-Datei waere
  redundant und wuerde Defer-Lifecycle aus dem `open/`-
  Trigger-System herausziehen. Bleibt out-of-scope, auch
  wenn ein zukuenftiges Compliance-Audit das verlangt
  (waere dann ADR-Schaerfungs-Material).
- **Per-CVE-Allowlist** im Trivy-Lauf (`--skip-vuln
  <CVE>`). Verboten per §2.2 als ADR-Bruch. Falls eine
  konkrete Allow-Schaerfung noetig wird (z. B. CVE in
  einer dev-only-Dependency), ist eine Folge-ADR der
  Pfad — nicht ein `Makefile`-Edit.
