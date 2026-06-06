# ADR 0044 — Generated-Trivyignore-Permit aus strukturierter Audit-Source-of-Truth (M6 Welle 4a)

**Status:** Provisional — direkter `Proposed → Provisional`-
Sprung in M6-Welle-4a-C1 (dieser ADR) zusammen mit Trigger-
033-Hash-Anchor-Block (Welle-3-Post-Closure-Substanz
`ede21ad` = Trigger-Eroeffnungs-Stand; M6-Welle-4a-C2 =
Pattern-Import-Hash, in §5 nachgetragen). `Accepted` folgt
in M6-Welle-7-Closure-C1 gebuendelt mit ADR 0041 + ADR 0042
+ ADR 0043 (Pattern analog M5-Welle-7-C1 `62f988d`).
**Datum:** 2026-06-06
**Status geaendert am:** 2026-06-06 — `Proposed → Provisional`
mit M6-Welle-4a-C1 (dieser Commit).
**Bezug:**
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Schaerfung-
ohne-Supersedes-Pattern — ADR 0044 ist eine additive
Schaerfung an ADR 0043 §2.2 ohne ADR-0043-Aufhebung),
[`ADR 0043`](0043-image-audit-strategy.md) (Image-Audit-
Strategie; ADR 0044 erweitert §2.2-Defer-Form um eine
zweite zulaessige Variante; ADR-0043-§2.1-Pflicht-Schwelle
und §2.3-Defer-Aufloesungs-Pattern bleiben textlich
unveraendert),
[`ADR 0028`](0028-link-maintenance-accepted-adr-bezug.md)
(Link-Maintenance fuer Accepted-ADR-Bezuege),
[`open/033-otel-collector-go-stdlib-cve-bump.md`](../planning/open/033-otel-collector-go-stdlib-cve-bump.md)
(Erst-Anwendungsfall — CVE-2026-42504 Go-stdlib MIME-Header-
DoS im OTel-Collector-Image; Trigger 033 bleibt offen als
Stable-Watch, vulnignore-Pattern ist Temp-Deferral).

---

## 1. Kontext

ADR 0043 §2.2 (Image-Audit-Strategie, `Provisional` seit
M6-Welle-1-C1 `c44e6d5`) verbietet folgende Defer-Formen
als ADR-Bruch:

> - Bloss-`.trivyignore`-Eintrag ohne `open/`-Begleit-Trigger.
> - Trivy-Argument-Anpassung (`--skip-vuln <CVE>` o. ae.)
>   ohne ADR-Schaerfungs-Commit.
> - `make image-audit`-Pflicht-Gate-Entfernung aus `make
>   ci`/`make fullbuild` ohne ADR-Schaerfungs-Commit.
> - Stilles `--ignore-unfixed`-Toggle oder `TRIVY_SEVERITY`-
>   Lockerung ohne ADR-Schaerfungs-Commit.

ADR 0043 §7 verankert `.trivyignore`-Pfad explizit als
„out-of-scope, auch wenn ein zukuenftiges Compliance-Audit
das verlangt (waere dann **ADR-Schaerfungs-Material**)" —
das antizipierte Schaerfungs-Material wird mit dieser ADR
geliefert.

M6-Welle-3-Post-Closure (Welle-3-`§10`-Korrektur-Stack
`0891f65`/`ede21ad`) hat NEU Trigger 033 angelegt: CVE-2026-
42504 (Go-stdlib MIME-Header-DoS; HIGH; fixed in 1.25.11 /
1.26.4) im `otel/opentelemetry-collector-contrib:0.153.0`-
Image (gobinary linked gegen `go1.26.3`). Aktivierungs-
Bedingung von Trigger 033 ist eine OTel-Collector-Release
> 0.153.0 mit `go1.26.4+`-Build; erwarteter Stable-Korridor
2026-06-09 bis 2026-06-12 per ~14-Tage-Kadenz. Bis dahin:
`make fullbuild` rot in `main`.

**Pattern-Vorbild**: das Schwester-Repo m-trace
(`/Development/m-trace/`) verankert seit Plan-0.8.5 eine
strukturierte `.security/vulnignore.yaml`-Source-of-Truth
mit Pflicht-Feldern `reason` + `expires` + `scope` und
einem `scripts/render-trivyignore.sh`-Renderer, der eine
Plain-Text-`.trivyignore` (Trivy-natives Format) ableitet
und `expires`-Pflicht zur Build-Time prueft (abgelaufene
Eintraege brechen den Render-Lauf). Das Pattern hat sich
in m-trace ueber mehrere Plan-Zyklen produktiv bewaehrt
(siehe m-trace `vulnignore.yaml`-Eintraege mit 90-Tage-
Default-Ablauf und Re-Review-Zyklus).

**Strukturelle Differenz zum §2.2-Verbot:** ADR 0043 §2.2
verbietet **bloss**-`.trivyignore` (ohne Begleit-Trigger;
ohne Source-of-Truth; ohne Ablauf-Mechanismus). Die
m-trace-Pattern-Form ist **nicht** „bloss" `.trivyignore`:

- Source-of-Truth ist eine versionierte `.yaml`-Audit-Datei
  mit obligatorischen Begruendungs-/Ablauf-/Scope-Feldern.
- `.trivyignore` selbst ist **NICHT versioniert**
  (`.gitignore`-Eintrag); der Renderer erzeugt sie
  reproduzierbar aus der `.yaml`.
- Ablauf-Pflicht erzwingt Maintenance ohne externe
  Erinnerung.
- Begleit-Trigger-Pflicht aus ADR 0043 §2.2 bleibt in Kraft
  — die `.yaml`-Audit-Eintraege ergaenzen den Trigger, sie
  ersetzen ihn nicht.

ADR 0044 schliesst die Luecke per ADR-0011-Pattern: §2.2-
Verbote von ADR 0043 bleiben textlich unveraendert; ADR
0044 fuegt **eine zweite zulaessige Defer-Form** additiv
hinzu.

---

## 2. Entscheidung

ADR 0044 fixiert vier orthogonale Punkte:

### §2.1 Permit-Form fuer generierte `.trivyignore`

Eine Trivy-`--ignorefile`-Konsumption ist **zulaessig**,
wenn die Ignore-Datei aus einer **strukturierten Audit-
Source-of-Truth-YAML** (`deploy/security/vulnignore.yaml`)
gerendert wurde. Die `.yaml` ist die kanonische Quelle;
die `.trivyignore` ist generated, NICHT versioniert.

Zulaessigkeit dieser Form **ergaenzt** ADR 0043 §2.2 —
beide Pfade gelten parallel:

- **Pfad A (ADR 0043 §2.2 Original)**: `open/`-Trigger als
  einzige Defer-Form fuer offene CVEs ohne aktive Ignore-
  Konsumption. Kanonischer Pfad fuer **kurze** Defers, wo
  die CI-Pflicht-Rot-Linie tolerabel ist.
- **Pfad B (ADR 0044, NEU)**: `open/`-Trigger PLUS
  `vulnignore.yaml`-Audit-Eintrag, wenn der CI-Pflicht-Rot-
  Zustand nicht tolerabel ist (z. B. `make fullbuild`
  blockiert weitere Welle-Substanz). `vulnignore.yaml`-
  Eintrag ist **Temp-Deferral**; der `open/`-Trigger bleibt
  die kanonische CVE-Aufloesungs-Spur.

Pfad B ersetzt Pfad A **nicht**; ein Trigger ohne
`vulnignore.yaml`-Eintrag bleibt zulaessig.

### §2.2 Schema-Pflicht-Felder

Jeder `vulnignore.yaml`-Eintrag unter `trivy.ignore[]` MUSS
folgende Felder haben:

```yaml
trivy:
  ignore:
    - id: <CVE-YYYY-NNNNN | GHSA-XXXX>     # Pflicht
      reason: "<knappe Begruendung mit Vektor-Aussage>"  # Pflicht
      expires: <YYYY-MM-DD>                # Pflicht, max. +90 Tage ab Eintrag-Datum
      scope: "<image-name oder *>"         # Pflicht; CSV-Liste zulaessig
```

- **`reason`**: knappe, audit-faehige Begruendung. SOLLTE
  den Angriffsvektor benennen und warum er in grid-gym-
  Container-Surface NICHT erreichbar ist (oder warum eine
  bewusste Temp-Akzeptanz vorliegt mit Verweis auf den
  Begleit-Trigger). Eine Begruendung wie „Aufloesung
  pendet — siehe Trigger 033" reicht; eine Vollvektor-
  Analyse ist NICHT Pflicht.
- **`expires`**: harte Ablauf-Schwelle. **Maximum +90 Tage**
  ab Eintrag-Datum (Konsistenz mit m-trace-Default). Render-
  Script bricht abgelaufene Eintraege als Build-Fehler.
- **`scope`**: Image-Name (z. B. `otel-collector`) oder
  `*` (alle Images im Audit-Lauf). Renderer akzeptiert
  CSV-Liste (`mtrace-dashboard, mtrace-analyzer-service`-
  Pattern aus m-trace).

Eintraege OHNE eines dieser Felder fuehren zu Render-
Script-Bruch (kein Default-Fill; Pflicht).

### §2.3 Render-Script-Vertrag

Das Render-Script `tools/render_trivyignore.py`:

1. Liest `deploy/security/vulnignore.yaml` per
   `yaml.safe_load` (PyYAML ist bereits grid-gym-Dep,
   produktiv im `_yaml_scenario_loader`).
2. Filtert Eintraege per `--scope`-Argument (z. B.
   `make render-trivyignore TRIVYIGNORE_SCOPE=otel-
   collector`); Eintraege mit `scope: otel-collector` oder
   `scope: *` matchen.
3. Bricht bei abgelaufenen `expires`-Werten mit EXIT=1
   und Fehlermeldung pro Eintrag.
4. Bricht bei fehlendem `expires`- oder `id`-Feld mit
   EXIT=1.
5. Schreibt `deploy/security/.trivyignore` (Plain-Text;
   eine CVE-ID pro Zeile mit Begruendungs-Kommentar).
6. **File-Praesenz-Invariante**: bei keinem Treffer wird
   die Output-Datei trotzdem mit Header-only geschrieben
   — `image-audit` mountet die Datei per `--ignorefile`,
   deshalb darf sie nicht fehlen (Trivy akzeptiert
   Header-only-Form).

Der Script ist die einzige Stelle, an der `.trivyignore`-
Inhalte produziert werden. Direkte `.trivyignore`-Edits
bleiben ADR-Bruch per ADR 0043 §2.2 — `.trivyignore` ist
im `.gitignore` UND nicht-direkt-bearbeitbar (Maschinen-
Output).

### §2.4 Trivy-Integration-Form

Die `make image-audit`-Substanz wird wie folgt erweitert:

- NEU `render-trivyignore`-Makefile-Target (PHONY) baut
  die `source`-Stage des Multi-Stage-Dockerfile und ruft
  darin `uv run python tools/render_trivyignore.py --scope
  $(TRIVYIGNORE_SCOPE)` per `docker run` mit Repo-Bind-
  Mount auf (Pattern analog `make format`-Target Z.139-
  148; PyYAML ist im `source`-Stage durch das
  `uv sync --frozen --all-groups --extra iec61850`
  bereits installiert).
- `image-audit`-Target bekommt `render-trivyignore` als
  Vorlauf-Dependency neben `build`.
- Der Trivy-Run gegen den Scope-relevanten Image (z. B.
  OTel-Collector) bekommt `-v "$(pwd)/deploy/security/
  .trivyignore":/security/.trivyignore:ro` als RO-Volume
  + `--ignorefile /security/.trivyignore` als CLI-Argument.
  Der Runtime-Image-Run bleibt **ohne** `--ignorefile`
  (kein Scope-Match in der Erstanwendung; das Runtime-
  Image hat 0 HIGH/0 CRITICAL).
- `TRIVY_SEVERITY=HIGH,CRITICAL` + `--ignore-unfixed`
  (ADR 0043 §2.1-Pflicht-Schwelle) bleiben unveraendert.

`--skip-vuln <CVE>` als CLI-Argument-Allowlist bleibt
verboten per ADR 0043 §2.2 — das ist eine **andere** Form
(Inline-CLI ohne Audit-Trail) als `--ignorefile` (Datei-
basiert mit Audit-Trail durch `vulnignore.yaml`).

---

## 3. Begruendung

- **Antizipiertes Schaerfungs-Material aus ADR 0043 §7
  liefern.** ADR 0043 §7 nennt `.trivyignore`-Pfad
  explizit als „ADR-Schaerfungs-Material". ADR 0044 ist
  dieser Schaerfungs-Commit; das Lifecycle-Vertrag-Versprechen
  aus §7 wird eingehalten.
- **Ablauf-Forcing als Differenzierungs-Substanz.** Der
  strukturelle Unterschied zum §2.2-Verbot ist die
  Pflicht-`expires`-Schwelle. Eine bloss-`.trivyignore`
  ohne Source-of-Truth haette keine Maintenance-Schwelle;
  vulnignore-Pattern hat sie eingebaut.
- **Begleit-Trigger bleibt Pflicht.** Pfad B ersetzt Pfad
  A nicht: ein Trigger wird zusaetzlich angelegt, nicht
  alternativ. Die Audit-Lifecycle-Substanz aus ADR 0043
  §2.2 (Slice-Lifecycle-Sichtbarkeit, `done/`-Aufloesung)
  bleibt vollstaendig erhalten.
- **Schwester-Pattern zu m-trace.** Cross-Project-
  Pattern-Konsistenz erleichtert Reviewer-Audit-Pfad —
  ein Reviewer, der m-trace kennt, erkennt das grid-gym-
  Pattern sofort wieder.
- **Schaerfung ohne Supersedes (ADR 0011-Pattern).** ADR
  0043 §2.1 + §2.3 bleiben textlich unveraendert; nur §2.2-
  Defer-Form wird additiv erweitert. ADR 0043-Substanz
  bleibt in Kraft, ADR 0044 liegt parallel.

---

## 4. Reichweite

- ADR 0043 bleibt textlich unveraendert (Provisional-
  Edit-Vermeidung; `Accepted`-Immutability per ADR 0006 §3
  greift bei Welle-7-Closure). ADR 0044 ist ein paralleles
  Schwester-Dokument per ADR 0011 §4.
- `Makefile` Z.25-26 (Trivy-Defaults) bleiben unveraendert.
  Z.279-302 (`image-audit`-Target) wird in Welle-4a-C2
  erweitert um `--ignorefile`-Argument + `render-
  trivyignore`-Vorlauf.
- NEU `deploy/security/vulnignore.yaml` (Audit-Source-of-
  Truth) + NEU `tools/render_trivyignore.py` (Renderer)
  + NEU `.gitignore`-Eintrag `deploy/security/.trivyignore`
  in Welle-4a-C2.
- ADR-Index Aktive-ADRs-Tabelle ADR-0043-Zeile bekommt
  „Schaerfungen / Folge-ADRs"-Spalte um ADR-0044-Eintrag
  (Index-Pflege per ADR 0011 §4); ADR-0044-Zeile NEU
  angelegt.
- Trigger 033 bleibt offen — vulnignore.yaml-Eintrag ist
  Temp-Deferral, Stable-Release-Watch bleibt kanonische
  Aufloesungs-Spur (siehe `M6-welle-4a.md §3 Welle-4a-D-4`).
- Bestehende `open/`-Trigger ohne `vulnignore.yaml`-Eintrag
  (010, 015, 031 in `done/`; etc.) bleiben unveraendert —
  Pfad B ist optional, nicht Pflicht.

---

## 5. Operative Artefakte (Erstanwendung in M6-Welle-4a)

Mit dieser ADR sind die folgenden Welle-4a-Substanz-Items
verbunden:

1. **M6-Welle-4a-C0** (`9bb6a92`):
   - NEU `docs/plan/planning/done/M6-welle-4a.md` (in
     Welle-4a-C0 als `in-progress/M6-welle-4a.md` angelegt;
     in Welle-4a-C4a `3bc58b8` self-close per `git mv` nach
     `done/`)
     (Slice-Doc-Anlage; Welle-4-Sub-Slicing-Beschluss).
   - `in-progress/README.md` + `M6-perf-security-cicd.md`
     §3.1 Welle-Status-Tabelle (4 → 4a + 4b gespalten).

2. **M6-Welle-4a-C1** (`94dff9e`):
   - NEU `docs/plan/adr/0044-generated-trivyignore-permit.md`
     (`Provisional`, dieser Text).
   - `docs/plan/adr/README.md` Aktive-ADRs-Tabelle um
     ADR-0044-Zeile ergaenzt; ADR-0043-Zeile-Schaerfungen-
     Spalte um ADR-0044-Bezug ergaenzt (ADR-0011 §4-Pattern).

3. **M6-Welle-4a-C2** (`8fbd17c`):
   - NEU `tools/render_trivyignore.py` (Renderer; Python-
     Port aus `/Development/m-trace/scripts/render-
     trivyignore.sh` mit grid-gym-Layout-Anpassung —
     bash+awk → Python+PyYAML, weil PyYAML bereits
     grid-gym-Dep und das `tools/`-Konvention auf Python-
     Skripte normiert ist).
   - NEU `deploy/security/vulnignore.yaml` mit Initial-
     Eintrag CVE-2026-42504 (`scope: otel-collector`,
     `expires: 2026-06-20`, `reason`: Trigger-033-Stable-
     Watch).
   - `.gitignore` um `deploy/security/.trivyignore`-Eintrag
     ergaenzt.
   - `Makefile` NEU `render-trivyignore`-Target (Pattern
     analog `make format`; source-Stage + Bind-Mount-
     `docker run`) + `image-audit`-Target-Erweiterung um
     `--ignorefile`-Argument fuer den OTel-Collector-
     Trivy-Run.
   - Verifikation: `make render-trivyignore` EXIT=0;
     `make image-audit` + `make ci` + `make fullbuild`
     cache-frei gruen ohne `CRITICAL_COV_TARGETS`-Override;
     Trivy meldet „Some vulnerabilities have been ignored/
     suppressed" beim OTel-Run als Filter-Greif-Beweis.

4. **M6-Welle-4a-C3** (`f19837f`; Closure-Sync):
   - **Hash-Anchor-Block** (dieser Block in §5): Welle-4a-
     C2 = `8fbd17c` als Trigger-033-Temp-Deferral-Beleg
     (NEU `tools/render_trivyignore.py` + `deploy/security/
     vulnignore.yaml` + Makefile-Integration; lokal `make
     image-audit` + `make ci` + `make fullbuild` cache-
     frei gruen).

5. **M6-Welle-4a-Post-Push-CI-Fix** (`f46e789`):
   - `deploy/compose.yml` `simulation`-Service Healthcheck
     `test: ["NONE"]` → `test: ["CMD", "true"]` mit
     `interval/timeout/retries`-Defaults (Always-Healthy
     fuer Stub-Container; Compose-v2-`--wait`-Strictness-
     Aufloesung). Pre-existing latente Drift seit M6-Welle-
     3-C2 `ce13253` (`fullbuild.yml`-CI-Pflicht-Gate
     angelegt), versteckt hinter Trigger-010-/-033-Image-
     Audit-Failures; erstmals sichtbar nach Welle-4a-C2
     `8fbd17c` (vulnignore-Pattern laesst image-audit
     gruen → runtime-Stage erreicht). CI-Sensor-Beleg:
     fullbuild.yml-Lauf 27055273876 gruen (6m56s) —
     erstmalig seit fullbuild.yml-Anlage in M6-Welle-3-C2.

6. **M6-Welle-4a-C4a** (`3bc58b8`) + **C4b** (Cross-Doc-
   Refs-Sync, dieser Commit):
   - C4a: `git mv docs/plan/planning/in-progress/M6-welle-
     4a.md → docs/plan/planning/done/M6-welle-4a.md`
     (rename-only).
   - C4b: ADR-0044 §5 Hash-Anchor-Block + Cross-Doc-Refs
     in `in-progress/README.md` + `M6-perf-security-cicd.md`
     + `roadmap.md` von `<C3>` auf `f19837f`/`<TBD>` auf
     `f46e789` konkretisiert; `M6-welle-4a.md`-Pfad-Refs
     von `in-progress/` auf `done/` umgehakt. `make docs-
     check` cache-frei gruen.
   - `M6-welle-4a.md` Status `In Progress → Done` mit
     Liefer-Hash-Stack.
   - `M6-perf-security-cicd.md §3.1` Welle-4a-Zeile `In
     Progress → Done` mit Closure-Hash + Aktive-Welle-Block
     auf Welle 4b.
   - `open/033-otel-collector-go-stdlib-cve-bump.md`
     Status-Block um „Temp-Deferral via Welle-4a-vulnignore-
     Pattern" ergaenzt; Trigger 033 bleibt offen.
   - `carveouts.md §2.X` NEU Trigger-033-Eintrag (Welle-3-
     Post-Closure-Vergesslichkeit nachgepflegt).
   - Top-Level-Doku-Sync (`README.md`/`README.de.md` NEU
     vulnignore.yaml-Hinweis; `roadmap.md §3 M6` aktive-
     Welle-Block auf M6-Welle-4b).

7. **M6-Welle-7-Closure-C1** (Folge-Welle):
   - ADR 0044 `Provisional → Accepted` gebuendelt mit
     ADR 0041 + ADR 0042 + ADR 0043 (Pattern analog
     M5-Welle-7-C1 `62f988d`).

`make gates` bleibt cache-frei gruen ohne Override in C1 +
C2 + C3 (10/10 A-1-Gates; Test-Counts unveraendert
1722/80/4 — Welle 4a fuegt keine neuen Tests hinzu).

---

## 6. Konsequenzen

- **Positiv:** ADR-0043-§7-Lifecycle-Vertrag-Versprechen
  eingehalten; `.trivyignore`-Pfad ist jetzt ADR-konform
  zulaessig unter strikten Pflicht-Feldern.
- **Positiv:** `make fullbuild`-Rot-Linie bei kurzfristigen
  Upstream-Drifts (z. B. OTel-Collector-CVE-Drift mit
  bekannter Stable-Release-ETA) kann temporaer gruen werden,
  ohne die ADR-0043-Substanz zu unterlaufen.
- **Positiv:** Ablauf-Pflicht erzwingt Maintenance ohne
  externe Erinnerung. Abgelaufene Eintraege brechen den
  Build; kein „stilles Drift"-Risiko.
- **Positiv:** Pattern-Konsistenz mit m-trace-Schwester-Repo
  erleichtert Cross-Project-Audit.
- **Neutral:** Erweitert die `image-audit`-Surface um zwei
  NEU Files (`deploy/security/vulnignore.yaml` + `tools/
  render_trivyignore.py`) und ein NEU Makefile-Target.
  Maintenance-Schwelle: gering (Audit-Eintraege sind
  selten; Renderer ist ~220 Zeilen Python und faellt unter
  `make lint`/`make format-check` wie die anderen `tools/
  check_*.py`-Skripte).
- **Neutral:** Begleit-Trigger-Pflicht aus ADR 0043 §2.2
  bleibt — vulnignore.yaml-Eintrag erspart den Trigger
  NICHT.
- **Neutral:** `expires`-Maximum 90 Tage ist eine
  Verhandlungs-Schwelle (m-trace-Default); bei laenger
  laufenden Defers (z. B. nicht-fixbare CVEs) ist eine
  ADR-Schaerfung an dieser Schwelle moeglich.

---

## 7. Nicht Gegenstand dieser ADR

- **Aufhebung von ADR 0043 §2.2-Verboten.** Bloss-
  `.trivyignore` (ohne Source-of-Truth), `--skip-vuln`-
  Argument-Allowlist und Pflicht-Gate-Entfernung bleiben
  ADR-Bruch per ADR 0043 §2.2 — ADR 0044 erweitert nur die
  zulaessige Defer-Form um Pfad B.
- **`govulncheck`-Ignore-Pfad.** `vulnignore.yaml`-Schema
  hat einen `govulncheck.ignore[]`-Sub-Block (m-trace-
  Vorbild); grid-gym hat **keinen** `govulncheck`-Lauf
  (Go-Code-Scan ist nicht Teil der grid-gym-Audit-Surface).
  Der Sub-Block bleibt leer (`govulncheck.ignore: []` als
  Schema-Treue-Stub), wird aber nicht ausgewertet.
- **Pre-Commit-Hook fuer render-Script.** Render-Script
  laeuft ausschliesslich als Makefile-Vorlauf vor `image-
  audit`. Pre-Commit-Integration bleibt M7+ oder spaeter
  (Trigger-007-Pattern; Dev-Tooling-Substanz).
- **CI-Pflicht-Gate fuer `expires`-Erinnerung.** Der
  Render-Lauf-Bruch ist die Pflicht-Schwelle; eine
  separate „14-Tage-vor-Ablauf"-Erinnerung ist nicht
  vorgesehen (m-trace-Vorbild: gleicher Stand).
- **Trivy-Version-Pin-Bump.** Trivy `0.58.0` (`Makefile`
  Z.25) bleibt unangetastet. `--ignorefile` wird seit Trivy
  0.21+ unterstuetzt; kein Bump-Bedarf.
- **Vendor-Specific Audit-Format** (Snyk, GHSA-Database).
  vulnignore.yaml folgt dem Trivy-nativen Format; Cross-
  Scanner-Konvergenz waere M7+ Tooling-Slice.
- **OTel-Collector-Stable-Release-Bump.** Trigger 033
  bleibt die kanonische Spur fuer die CVE-2026-42504-
  Aufloesung. ADR 0044 ist Temp-Deferral-Form, nicht
  Aufloesungs-Substanz.
- **Carveout-Aufloesungs-Welle-Folge** (Pattern Welle-1
  Trigger 010 + Welle-2 Trigger 008 + Welle-3 Trigger 031).
  Trigger 033 wandert NICHT in `done/` mit Welle-4a-
  Closure; die echte Aufloesung erfolgt spaeter bei
  Stable-Release-Bump (separater Slice oder Welle-4a-Post-
  Closure-Korrektur).
