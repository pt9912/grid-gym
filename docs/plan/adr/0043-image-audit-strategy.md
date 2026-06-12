# ADR 0043 — Image-Audit-Strategie + Trivy-Defer-Aufloesungs-Pattern (M6 Welle 1)

**Status:** Accepted — gezogen 2026-06-08 mit M6-Welle-7-C1
(dieser Commit; M6-Closure-Welle). Provisional-Schritt
2026-06-05 (direkter `Proposed → Provisional`-Sprung mit
M6-Welle-1-C1).
**Datum:** 2026-06-05
**Status geaendert am:** 2026-06-05 — `Proposed → Provisional`;
2026-06-08 — `Provisional → Accepted` (M6-Welle-7-Closure).
**Bezug:**

- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — Lifecycle- und Supersedes-Pflichten, auf denen die
  Schaerfungs-ohne-Supersedes-Form aufbaut.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) —
  Schaerfung-ohne-Supersedes-Pattern; ADR 0043 verankert
  ein Quality-Gate parallel zu ADR 0002 §A-1, ohne ADR 0002
  textlich zu beruehren.
- [`ADR 0028`](0028-link-maintenance-accepted-adr-bezug.md)
  — Link-Maintenance-Pattern fuer ADR-Index- und Bezug-
  Pflege.
- [`ADR 0029`](0029-no-coverage-pragma-contract.md) —
  Schwester-Pattern (Coverage-Gate als eigenstaendiger
  Vertrag); ADR 0043 folgt derselben Form fuer den Image-
  Audit-Gate.
- [Trigger 010](../planning/done-archive/010-base-image-krb5-cve-bump.md)
  — Erst-Anwendungsfall des §2.2-Defer-Patterns; krb5-CVE-
  Famille als Drift-Quelle.

---

## 1. Kontext

`make fullbuild` (`ci + image-audit + test-integration +
openapi-validate`) war ueber mehrere Meilenstein-Closures
pre-existing rot wegen einer Familie von HIGH-CVEs im
Debian-13-Base-Image, fuehrende ID **`CVE-2026-40356`** in
`krb5`-Paketen (`libkrb5-3`/`libk5crypto3`/`libgssapi-krb5-2`)
mit Fix-Version `1.21.3-5+deb13u1`. Die CVE-Drift ist eine
reine Base-Image-Lieferketten-Drift, nicht durch grid-gym-
Code verursacht — sie wurde ueber mehrere M-Closures als
dokumentierter Defer-Pfad gefuehrt, formalisiert in
[Trigger 010](../planning/done-archive/010-base-image-krb5-cve-bump.md);
ADR 0043 verankert das Aufloesungs-Pattern als Pflicht-
Vertrag.

Vor dieser ADR war im Repo keine kanonische Image-Audit-
Pflicht-Strategie verankert:

- `make image-audit` ist Pflicht-Gate in `make ci` und
  `make fullbuild` (siehe `Makefile`, `image-audit`-Target
  + `TRIVY_*`-Defaults).
- Trivy-Konfiguration: `TRIVY_SEVERITY=HIGH,CRITICAL` plus
  `--ignore-unfixed`.
- Defer-Lifecycle: ad-hoc dokumentiert in M-results-§4-S-4-
  Notes und in `open/`-Triggers, ohne ADR-Verankerung
  welcher Defer-Pfad zulaessig ist.

Das ist eine A-1-Luecke: ein zukuenftiger Reviewer kann
nicht aus Accepted-ADRs ableiten, ob ein `.trivyignore`-
Eintrag, ein `--skip-vuln`-Argument oder ein anderer
Defer-Pfad ADR-konform ist.

---

## 2. Entscheidung

ADR 0043 fixiert drei orthogonale Punkte:

**§2.1 Image-Audit-Pflicht-Schwelle.** Der `make image-audit`-
Pflicht-Gate verlangt einen Trivy-Lauf gegen das `make build`-
Runtime-Image mit folgenden Defaults aus `Makefile`:

- `TRIVY_SEVERITY=HIGH,CRITICAL` — nur HIGH- und CRITICAL-CVEs
  brechen das Gate; LOW und MEDIUM sind ausgeblendet (kein
  Sensor-Rauschen).
- `--ignore-unfixed` — CVEs ohne verfuegbaren Fix werden aus
  dem Report herausgefiltert (kein „Marker"-Mechanismus,
  sondern Filter im Trivy-Lauf).

Beide Defaults sind **fester Bestandteil** der ADR-0043-
Substanz. Eine Schwellen-Lockerung (z. B. nur CRITICAL)
oder eine Schwellen-Verschaerfung (z. B. MEDIUM mit
einbeziehen) waere ADR-pflichtige Schaerfung per
[ADR 0011](0011-schaerfung-ohne-abloesung.md)-Pattern.

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
  Slice-Lifecycle-Disziplin bisheriger Meilenstein-Closures
  (Defer-Pfade werden in den Closure-Notes der jeweiligen
  M-results-Doks gefuehrt). `.trivyignore` wuerde die Defer-
  Lifecycle aus dem sichtbaren Slice-Lifecycle herausziehen —
  dann ist nicht mehr nachvollziehbar, *welcher* Slice einen
  Defer-Pfad geoeffnet hat und *welcher* ihn schliesst.
- **Schwester-Pattern zu [ADR 0029](0029-no-coverage-pragma-contract.md).**
  AC-NO-COVERAGE-PRAGMA verbietet Pragma-Annotations, die
  einen Coverage-Gate unterlaufen wuerden, und ist Pflicht
  in `src/grid_gym/**`. ADR 0043 folgt derselben Form fuer
  den Image-Audit-Gate: Defer-Form wird auf eine einzige
  sichtbare Lifecycle-Variante eingeschraenkt; alternative
  Wege gelten als ADR-Bruch.
- **Schaerfung ohne Supersedes (ADR-0011-Pattern).**
  [ADR 0002](0002-language-and-build-stack.md) §A-1 listet
  die A-1-Gates, ohne `make image-audit` als eigenen Vertrag
  zu fuehren — `image-audit` ist
  [`GG-QG-002`](../../../spec/lastenheft.md#gg-qg-002)
  `SOLLTE` per Lastenheft und in der A-1-Welt ueber
  `make ci`/`make fullbuild` verankert, nicht in der
  10-Contracts-Tabelle. ADR 0043 fixiert den Image-Audit-
  Vertrag separat, ohne ADR 0002 zu beruehren — Pattern
  konsistent mit ADR 0029.

---

## 4. Reichweite

- [ADR 0002](0002-language-and-build-stack.md) bleibt
  textlich unveraendert (`Accepted`-Immutability per
  [ADR 0006](0006-adr-lifecycle-superseding-and-process-corrections.md)
  §3). ADR 0043 ist ein separater Quality-Gate-Vertrag,
  kein §A-1-Eintrag.
- Trivy-Defaults und `image-audit`-Target im `Makefile`
  bleiben textlich unveraendert — die ADR verankert nur
  den existierenden Code-Stand als Pflicht-Vertrag.
- ADR 0043 wird im ADR-Index unter ADR 0040 in der Aktive-
  ADRs-Tabelle eingefuegt — ohne „Schaerfungen / Folge-
  ADRs"-Eintrag in ADR 0029 oder ADR 0002, weil ADR 0043
  ein eigenstaendiger Vertrag und keine Schaerfung an
  einem bestehenden Vertrag ist.
- Trigger 010 ist der erste konkrete Anwendungsfall des
  §2.2-Defer-Patterns; der Aufloesungs-Hash wird in §5
  (Lieferung) ueber die zugehoerige Slice-Doc gefuehrt.

---

## 5. Lieferung

Lieferplan, Commit-Hashes und Verifikations-Gates fuer die
Erst-Anwendung der §2-Substanz (Trigger-010-Aufloesung)
leben in der zugehoerigen Slice-Doc
[`M6-welle-1.md`](../planning/done-archive/M6-welle-1.md). Status-
Pfad (`Proposed → Provisional → Accepted`): siehe Status-
Header dieser ADR.

---

## 6. Konsequenzen

- **Positiv:** `make image-audit` ist explizit als ADR-
  verankerter Pflicht-Gate gefuehrt. Reviewer koennen aus
  Accepted-ADRs ableiten, dass `.trivyignore`-Eintraege
  ohne `open/`-Begleit-Trigger ADR-Bruch sind.
- **Positiv:** Trigger-010-Aufloesung beseitigt die zuvor
  pre-existing `make fullbuild`-Rotlinie — alle vier A-1-
  Gate-Folge-Lieferungen (`make ci`/`make fullbuild`/
  `make image-audit`/`make gates`) sind cache-frei gruen
  ohne Override.
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
  noetig — ADR 0043 bleibt textlich, eine separate Folge-
  ADR traegt die geschaerfte Schwelle.
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
  GitHub-Dependabot). Der `TRIVY_IMAGE`-Default im
  `Makefile` ist die produktive Wahl; ein Wechsel waere
  ADR-pflichtig, aber ausserhalb ADR 0043.
- **SBOM-Generierung im Release-Workflow** (`GG-CICD-007`
  + Trigger 008). Liegt bei
  [ADR 0042](0042-sbom-tool-and-release-pattern.md), die
  die SBOM-Tool-Wahl + den CI-Hook-Pattern traegt.
- **CI-Pflicht-Gate fuer `make fullbuild`** in GitHub
  Actions. Orthogonal zu ADR 0043: diese ADR verankert das
  Image-Audit-Pattern lokal im Makefile, unabhaengig vom
  CI-Workflow-Edit.
- **Container-Hardening jenseits Base-Image-CVE-Aufloesung**
  (`GG-DEPLOY-*`-Vollausbau: Container-Smoke-Test mit
  Compose, Healthcheck-Pollung, Read-only-Filesystem,
  User-Capabilities). Out-of-scope dieser ADR.
- **`.trivyignore`-Pfad fuer unfixed-CVEs.** Trivy filtert
  unfixed-CVEs ueber `--ignore-unfixed` bereits aus dem
  Report; eine zusaetzliche `.trivyignore`-Datei waere
  redundant und wuerde Defer-Lifecycle aus dem `open/`-
  Trigger-System herausziehen. Bleibt out-of-scope, auch
  wenn ein zukuenftiges Compliance-Audit das verlangt
  (waere dann ADR-Schaerfungs-Material, vgl.
  [ADR 0044](0044-generated-trivyignore-permit.md), die
  §2.2 fuer Source-of-Truth-getriebene Permits schaerft).
- **Per-CVE-Allowlist** im Trivy-Lauf (`--skip-vuln
  <CVE>`). Verboten per §2.2 als ADR-Bruch. Falls eine
  konkrete Allow-Schaerfung noetig wird (z. B. CVE in
  einer dev-only-Dependency), ist eine Folge-ADR der
  Pfad — nicht ein `Makefile`-Edit.
