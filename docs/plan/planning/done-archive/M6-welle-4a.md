# Welle 4a — M6 Generated-Trivyignore-Permit (Pattern-Import + ADR-0044)

**Status:** Done 2026-06-06 — Liefer-Stack: C0 `9bb6a92`
(Slice-Doc-Anlage) + C1 `94dff9e` (NEU ADR-0044 `Provisional`
+ ADR-Index-Update) + C2 `8fbd17c` (NEU `tools/
render_trivyignore.py` + NEU `deploy/security/vulnignore.yaml`
mit CVE-2026-42504-Eintrag + Makefile-Integration; `make
image-audit` + `make fullbuild` cache-frei gruen) + C3
`f19837f` (Status/DoD-Sync + Trigger-033-Status-Block-
Erweiterung + carveouts.md-Pflege + ADR-0044-§5-Hash-
Anchor-Update + Top-Level-Doku-Sync) + Post-Push-CI-Fix
`f46e789` (simulation-Healthcheck Always-Healthy gegen
Compose-v2-`--wait`-Strictness; pre-existing latente Drift;
siehe §10) + C4a `3bc58b8` (Self-Close-Move; `git mv` rename-
only) + C4b `789ac50` (Cross-Doc-Refs-Sync nach Move +
ADR-0044-§5-Hash-Anchor-Konkretisierung + §10-Hash-Slot-
Fill). `make fullbuild` cache-frei gruen **lokal UND CI-
Sensor** (Lauf 27055273876 gruen 6m56s) — erstmaliger CI-
Beleg seit `fullbuild.yml`-Anlage in M6-Welle-3-C2 `ce13253`.
Welle 4 ist gemaess
§3 Welle-4a-D-1 in **4a (Generated-Trivyignore-Permit) + 4b
(Performance-Benchmark)** sub-geslict; Pattern folgt M5-Welle-
4 (`M5-welle-4a.md` + `M5-welle-4b.md`). Welle 4a ist die
**erste Sub-Welle** und liefert die strukturierte Defer-Form
fuer den OTel-Collector-Go-stdlib-CVE-2026-42504-Befund
(Trigger 033, Welle-3-Post-Closure-Folge), inklusive ADR-
0011-Schaerfung an ADR-0043 §2.2. Trigger 033 bleibt OFFEN
als kanonische Stable-Watch — vulnignore-Pattern ist Temp-
Deferral, echte Aufloesung weiter bei OTel-Stable-Release
0.154.0+.

**Pre-C0 abgeschlossen (M6-Welle-3-Closure-Folge):**

- C4a `3b6d9bf` — `git mv M6-welle-3.md → done/` (Self-
  Close-Move, rename-only).
- C4b `c36f734` — Cross-Doc-Refs-Sync nach Move.
- Post-Closure-Korrekturen `0891f65..f34ddc5` — Welle-3-
  Substanz-Schaerfungen (`docs/plan/planning/done/M6-welle-3.md` §10).

**Spec-Reife:** Inhaltlich final fuer Welle 4a. Welle-4a-
Decision-Liste (§3) schliesst Welle-4a-D-1..D-4: Sub-Slicing-
Beschluss, ADR-Form, Layout-Konvention, Trigger-033-Lifecycle.

---

## 1. Context

**Welle-4-Vorbelegung** in [`M6-perf-security-cicd.md §3.2 Welle 4`](M6-perf-security-cicd.md)
ist **Performance-Benchmark** (`GG-RT-001..005` inkl. 10000-
Points/s-Benchmark `GG-RT-005` SOLLTE). Die Welle wird in
Welle-4-C0 in 4a/4b gespalten, weil **NEU Trigger 033 (OTel-
Collector Go-stdlib CVE-Bump, Welle-3-Post-Closure)** die
substanzielle Aufloesung im `make fullbuild`-CI-Pfad
blockiert — bevor Welle-4b (Performance-Benchmark) sinnvoll
gefahren werden kann, muss `make fullbuild` cache-frei gruen
auf `main` sein. Die Welle-4-Subdivision folgt der M5-Welle-
4-Form (4a/4b) und macht den OTel-CVE-Pfad zur Welle-4a-
Substanz.

### 1.1 Existierende Substanz (vor Welle 4a)

- **ADR-0043 `Provisional`** (Welle-1-C1 `c44e6d5`) — Image-
  Audit-Strategie + Trivy-Defer-Aufloesungs-Pattern. §2.2
  verbietet:
  - „Bloss-`.trivyignore`-Eintrag ohne `open/`-Begleit-
    Trigger."
  - „Trivy-Argument-Anpassung (`--skip-vuln <CVE>` o. ae.)
    ohne ADR-Schaerfungs-Commit."
  §7 „Nicht Gegenstand" verankert `.trivyignore`-Pfad als
  **ADR-Schaerfungs-Material**: „Bleibt out-of-scope, auch
  wenn ein zukuenftiges Compliance-Audit das verlangt
  (waere dann ADR-Schaerfungs-Material)."
- **`open/033-otel-collector-go-stdlib-cve-bump.md`** —
  Trigger-Watch mit Aktivierungs-Bedingung „OTel-Collector-
  Release > 0.153.0 mit `go1.26.4+`-Build". Erwarteter
  Release-Korridor 2026-06-09 bis 2026-06-12 per ~14-Tage-
  Kadenz. Trigger-033-Konsequenz-Block: „`make fullbuild`
  bleibt rot in `main`."
- **`Makefile` Z.279-302** — `image-audit`-Target mit zwei
  Trivy-Runs (`grid-gym-runtime:latest` + `OTEL_COLLECTOR_
  IMAGE`); `TRIVY_SEVERITY=HIGH,CRITICAL` + `--ignore-
  unfixed` (ADR-0043 §2.1-Pflicht-Schwelle).
- **`Makefile` Z.35** — `OTEL_COLLECTOR_IMAGE ?=
  otel/opentelemetry-collector-contrib:0.153.0`-Pin.
- **`ADR-0011`** — Schaerfung-durch-parallele-ADR-ohne-
  Supersedes-Pattern (Accepted 2026-05-17). ADR-0011 ist der
  vorgeschriebene Pfad fuer additive Erweiterungen an einer
  bestehenden Accepted-/Provisional-ADR ohne Aufhebung der
  Originalsubstanz.
- **m-trace-Pattern** (`/Development/m-trace/scripts/render-
  trivyignore.sh` + `/Development/m-trace/.security/
  vulnignore.yaml`) — externes Schwester-Repo verankert
  bereits die Source-of-Truth-Pattern-Form mit
  Pflicht-`expires`/`reason`/`scope`-Feldern und automatischer
  Ablauf-Pruefung. Welle 4a importiert das Pattern in grid-
  gym mit Layout-Anpassung an grid-gym-`tools/`-Konvention.

### 1.2 Welle-4a-Lieferziel

Drei orthogonale Liefer-Items:

1. **NEU ADR-0044 `Provisional`** (Welle-4a-C1) — Schaerfung
   an ADR-0043 §2.2 per ADR-0011-Pattern. **Permittet**
   `.trivyignore` als Defer-Form, wenn aus einer
   strukturierten Audit-Source-of-Truth-Datei generiert mit
   Pflicht-Feldern (`reason` + `expires` + `scope`),
   render-Script erzwingt `expires`-Check (abgelaufene
   Eintraege brechen den Render-Lauf). `.trivyignore` selbst
   bleibt **NICHT-versioniert** (`.gitignore`-Eintrag); die
   `vulnignore.yaml` ist die kanonische Source-of-Truth.
   Bestehende §2.2-Verbote (Bloss-`.trivyignore` ohne
   `open/`-Begleit-Trigger; CVE-Allow-Argument-Edit)
   bleiben in Kraft. Trigger-033-Pflicht aus §2.2 bleibt
   ebenfalls verankert; ADR-0044 zieht **nur** die Form
   nach, mit der ein zeitlich begrenzter Defer maschinen-
   lesbar wird.
2. **NEU `deploy/security/vulnignore.yaml`** + **NEU
   `tools/render_trivyignore.py`** (Welle-4a-C2) — Pattern-
   Import aus m-trace mit Layout-Anpassung an grid-gym
   (`tools/`-Konvention statt `scripts/`; `deploy/security/`
   statt `.security/`). Initial-Eintrag fuer CVE-2026-42504
   mit `expires: 2026-06-20` (2-Wochen-Safety-Margin
   gegenueber dem erwarteten OTel-Release-Korridor 2026-
   06-09 bis 2026-06-12), `scope: otel-collector`,
   `reason: Trigger-033-Stable-Watch`.
3. **Makefile-Integration** (Welle-4a-C2) — NEU `render-
   trivyignore`-Target als Pflicht-Vorlauf vor `image-
   audit`; Trivy-Run um `--ignorefile deploy/security/
   .trivyignore` erweitert (kein `--skip-vuln`-Argument-
   Edit; ADR-0043-konform). Substanz: `make image-audit`
   cache-frei gruen, `make fullbuild` cache-frei gruen.
   **Trigger 033 bleibt offen** (Stable-Watch); die
   vulnignore.yaml-Substanz ist Temp-Deferral, NICHT die
   echte CVE-Aufloesung.

### 1.3 Welle-4a-Anti-Scope

- **Kein OTel-Collector-Image-Bump** — Trigger-033-Substanz
  bleibt offen. Bei Stable-Release 0.154.0+ erfolgt der
  echte Bump als separater Slice oder als Welle-4a-Post-
  Closure-Korrektur.
- **Keine Performance-Bench** — `GG-RT-001..005` ist Welle-
  4b-Scope (M6-Welle-4-Subdivision-Beschluss).
- **Keine ADR-0029-Beruehrung** — Coverage-Gate-Pragma-
  Vertrag bleibt unangetastet. ADR-0044 ist ADR-0043-Schaerfung,
  nicht ADR-0029-Schaerfung.
- **Keine `--skip-vuln`-Argument-Anpassung** — ADR-0043
  §2.2 verbietet das weiterhin. `--ignorefile` ist eine
  **Datei-basierte** Ignore-Form (Trivy-Standard); §2.2
  zielt auf CLI-Argument-Allowlisting fuer Einzel-CVEs.
- **Keine permanente Defer-Form** — `expires`-Pflicht (max.
  90 Tage analog m-trace) erzwingt Maintenance. Stable-
  Release-Watch bleibt der **kanonische** Aufloesungs-Pfad
  per Trigger 033.
- **Keine `pre-commit`-Hook-Substanz** — `tools/render-
  trivyignore.sh` wird ausschliesslich vor `image-audit`
  als Makefile-Vorlauf aufgerufen. Pre-Commit ist M7+ oder
  spaeter.

---

## 2. Scope

Welle 4a liefert **drei Items** ueber 3-4 Commits (C0..C3),
plus Self-Close-Folge C4a/C4b.

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses
   Dokument; in-progress/README.md-Bestand-Tabelle +
   M6-perf-security-cicd.md §3.1 Welle-4-Zeile in 4a/4b
   gespalten.
2. **ADR-Substanz** (C1) — NEU ADR-0044 `Provisional`
   (Generated-Trivyignore-Permit; ADR-0011-Schaerfung an
   ADR-0043 §2.2); README.md ADR-Index um ADR-0044-Zeile
   ergaenzt; ADR-0043-Zeile bekommt „Schaerfung via ADR
   0044"-Marker (rein Index-Pflege, keine ADR-0043-Text-
   Aenderung).
3. **Code-Substanz** (C2) — NEU `deploy/security/
   vulnignore.yaml` + NEU `tools/render_trivyignore.py` +
   `.gitignore` um `deploy/security/.trivyignore` ergaenzt
   + `Makefile`-Integration (NEU `render-trivyignore`-
   Target + `image-audit`-Erweiterung um `--ignorefile`).
   Lokal-Verifikation `make image-audit` + `make fullbuild`
   cache-frei gruen.
4. **Status/DoD-Sync** (C3) — `M6-welle-4a.md` auf `Done`;
   `M6-perf-security-cicd.md §3.1` Welle-4a-Zeile auf
   `Done`; Top-Level-Doku-Sync (`README.md`/`README.de.md`
   NEU Hinweis auf `deploy/security/vulnignore.yaml`-
   Source-of-Truth + Welle-4a-Substanz; `roadmap.md §3 M6`
   aktive Welle auf M6-Welle-4b). **Trigger 033 bleibt
   offen** — `open/033-*.md` Status-Block um „Temp-Deferral
   via Welle-4a-vulnignore-Pattern; echte Aufloesung weiter
   bei OTel-Stable-Release 0.154.0+" ergaenzt.

Self-Close-Folge C4a/C4b laufen nach C3 als M6-Welle-4b-Pre-
C0a/Pre-C0b.

---

## 3. Architektur-Entscheidungen (Welle-4a-Decision-Liste)

### Welle-4a-D-1 — Sub-Slicing-Beschluss

**Frage:** Wird Welle 4 als Single-Welle (nur Performance-
Bench) oder Sub-Slicing 4a/4b geliefert?

Optionen:

- **A — Renumber**: Vulnignore-Pattern wird NEU Welle 4;
  Performance-Bench wird Welle 5; alle Folge-Wellen
  ruecken um eins.
- **B — Sub-Slicing 4a/4b**: Welle 4a = Vulnignore-Pattern;
  Welle 4b = Performance-Bench. Plan-Numerierung bleibt
  unangetastet.
- **C — Post-Closure-Korrektur-Stack-Extension** in
  Welle 3: Welle-3-`§10`-Korrektur-Stack um vulnignore-
  Stufe-3 erweitern.

**Welle-4a-Final: Option B (Sub-Slicing 4a/4b).** Begruendung:

- Welle 4 ist konzeptuell „Performance + Security-Defer-
  Aufloesung"; beide Concerns sind voneinander unabhaengig.
- Sub-Slicing-Pattern-Vorbild M5-Welle-4 (4a Replay-Controls
  + 4b Alarm-Aggregation) zeigt die Form ist akzeptiert.
- Renumber-Option A bricht den `M6-perf-security-cicd.md
  §3.2`-Welle-Plan zu massiv.
- Korrektur-Stack-Option C ist nicht passend, weil ADR-
  0044-Substanz zu gross fuer einen `§10`-Eintrag.

### Welle-4a-D-2 — ADR-Form

**Frage:** Wird ADR-0044 als Schaerfung (ADR-0011) oder
als komplette Supersedes-Ablösung von ADR-0043 geschrieben?

**Welle-4a-Final: Schaerfung per ADR-0011-Pattern.**
Begruendung:

- ADR-0043 §2.1 (Pflicht-Schwelle) + §2.3 (Defer-Aufloesungs-
  Pattern) bleiben **vollstaendig in Kraft**. ADR-0044
  schaerft nur §2.2 (Defer-Form) und §7 (Nicht-Gegenstand-
  Stelle).
- ADR-0011 §2 erlaubt explizit „additive Erweiterung"; eine
  zusaetzlich erlaubte Defer-Form ist additiv (verbietet
  keine bestehende Form, fuegt eine neue hinzu).
- ADR-0043 ist `Provisional`; ADR-0044 ist auch `Provisional`
  und wird im selben M6-Welle-7-Closure-C1 auf `Accepted`
  gebuendelt mit ADR 0041 + ADR 0042 + ADR 0043 (Pattern
  analog M5-Welle-7-C1 `62f988d`).

### Welle-4a-D-3 — Layout-Konvention

**Frage:** Welche Pfade fuer Source-of-Truth + Render-
Script + generierte Datei?

Optionen:

- **A — m-trace 1:1**: `.security/vulnignore.yaml` +
  `.security/.trivyignore` + `scripts/render-trivyignore.sh`.
- **B — grid-gym-Konvention**: `deploy/security/vulnignore.
  yaml` + `deploy/security/.trivyignore` + `tools/render-
  trivyignore.sh`.

**Welle-4a-Final: Option B (grid-gym-Konvention).**
Begruendung:

- grid-gym hat keinen `scripts/`-Top-Level (`tools/` ist
  die etablierte Konvention; `tools/check_noqa.py`,
  `tools/check_spdx.py`, `tools/arch_check.py`, etc.).
- grid-gym hat keinen `.security/`-Top-Level. `deploy/`
  ist der etablierte Container fuer Deployment-/Security-
  bezogene Konfiguration (`deploy/compose.yml`,
  `deploy/otel-collector-config.yaml`).
- Cross-Project-Konsistenz mit m-trace ist sekundaer; intra-
  grid-gym-Konvention primaer.

### Welle-4a-D-4 — Trigger-033-Lifecycle

**Frage:** Wird Trigger 033 nach `done/` verschoben (mit
ADR-0044-Substanz als Aufloesungs-Pfad) oder bleibt er
offen?

**Welle-4a-Final: Trigger 033 bleibt OFFEN als Stable-Watch.**
Begruendung:

- Die `vulnignore.yaml`-Substanz ist **Temp-Deferral**,
  nicht die echte CVE-Aufloesung. CVE-2026-42504 ist eine
  reale HIGH-Severity-Vulnerability mit verfuegbarem Fix
  (go1.26.4+).
- Trigger-033-Aktivierungs-Bedingung (OTel-Stable-Release
  0.154.0+ mit go1.26.4+) bleibt unveraendert kanonisch.
- `vulnignore.yaml`-Eintrag hat `expires: 2026-06-20`; bei
  Ablauf erzwingt der render-Script Maintenance — entweder
  Stable-Release vorhanden (Trigger 033 wird dann
  geschlossen) oder `expires` verlaengert (mit neuer
  Begruendung).
- Trigger-033-Status-Block wird in C3 um eine
  „Temp-Deferral-via-Welle-4a"-Notiz ergaenzt, ohne den
  Aktivierungs-Pfad zu beruehren.

---

## 4. Liefer-Reihenfolge (3-4 Commits)

### Pre-C0 — bereits erledigt (M6-Welle-3-Closure-Folge)

- `3b6d9bf` (Pre-C0a: `git mv M6-welle-3.md → done/`).
- `c36f734` (Pre-C0b: Cross-Doc-Refs-Sync nach Move).
- `0891f65..f34ddc5` (Post-Closure-Korrekturen; Welle-3-
  Substanz, siehe Welle-3-`§10`).

### C0 — `docs(plan)`: M6-welle-4a Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU `M6-welle-4a.md` (dieses Dokument).
- `in-progress/README.md` Bestand-Tabelle um Welle-4a-Zeile
  ergaenzt + Aktive-Welle-Block auf M6-Welle-4a aktualisiert.
- `M6-perf-security-cicd.md §3.1` Welle-4-Zeile in 4a/4b
  gespalten (4a `In Progress 2026-06-06`; 4b bleibt
  `Pending`); §3.2 Welle-4-Block um Welle-4a-Sub-Slicing-
  Notiz erweitert.

### C1 — `docs(adr)`: NEU ADR-0044 `Provisional`

Code-Merge mit:

- NEU `docs/plan/adr/0044-generated-trivyignore-permit.md`
  `Provisional` (ADR-0011-Schaerfung an ADR-0043 §2.2).
- `docs/plan/adr/README.md` Aktive-ADRs-Tabelle um
  ADR-0044-Zeile + ADR-0043-Zeile-„Schaerfungen"-Spalte
  um „ADR 0044"-Eintrag (ADR-0011 §4-Pattern).
- `M6-welle-4a.md §3` Decision-D-2 (ADR-Form) auf
  „erfuellt durch C1 `<hash>`"-Marker.

### C2 — `feat(security)`: vulnignore-Pattern-Import

Code-Merge mit:

- NEU `deploy/security/vulnignore.yaml` mit:
  - CVE-2026-42504-Eintrag (`reason` + `expires:
    2026-06-20` + `scope: otel-collector`).
  - Datei-Header-Schema-Block analog m-trace (Trivy-Format
    + govulncheck-Stub + Wartungsregel-Block).
- NEU `tools/render_trivyignore.py`:
  - Logik adaptiert aus `/Development/m-trace/scripts/
    render-trivyignore.sh` (m-trace nutzt bash+awk; grid-
    gym-Form nutzt Python+PyYAML, weil PyYAML bereits
    grid-gym-Dep ist und das `tools/`-Konvention auf
    Python-Skripte normiert ist — `check_noqa.py`/
    `check_spdx.py`/`check_refs.py`-Pattern).
  - Layout-Anpassung: `--source deploy/security/
    vulnignore.yaml`; `--target deploy/security/
    .trivyignore`; `--scope <name>` als Filter-Argument.
  - SPDX-Header optional (tools/check_spdx.py scannt nur
    GPL-Boundary; ADR 0035).
  - `expires`-Pflicht + Ablauf-Bruch unveraendert
    (EXIT=1 bei fehlendem oder abgelaufenem Feld).
- `.gitignore` um `deploy/security/.trivyignore`-Eintrag
  ergaenzt (generated; nicht versioniert).
- `Makefile`-Integration:
  - NEU `render-trivyignore`-Target (PHONY): laeuft
    `uv run python tools/render_trivyignore.py --scope
    $(TRIVYIGNORE_SCOPE)` via source-Stage + Bind-Mount
    des Repo-Trees (Pattern analog `make format`); Default-
    Scope `otel-collector`.
  - `image-audit`-Target um `render-trivyignore`-
    Vorlauf-Dependency erweitert.
  - Trivy-Run gegen `OTEL_COLLECTOR_IMAGE` um `--ignorefile
    /security/.trivyignore` erweitert (Bind-Mount von
    `deploy/security/.trivyignore` als RO-Volume; NUR
    fuer den OTel-Run; runtime-Image-Run unangetastet,
    kein Ignore-Wirkungsbereich).
- **Verifikation (lokal vor C2-Commit):**
  - `make render-trivyignore` EXIT=0; Output
    `deploy/security/.trivyignore` enthaelt CVE-2026-42504-
    Eintrag mit Begruendungs-Kommentar.
  - `make image-audit` cache-frei gruen (beide Trivy-Runs;
    runtime-Image weiterhin 0 HIGH/0 CRITICAL, OTel-
    Collector mit `--ignorefile`-Filter gruen via Trivy-
    Output „Some vulnerabilities have been ignored/
    suppressed").
  - `make ci` cache-frei gruen.
  - `make fullbuild` cache-frei gruen ohne `CRITICAL_COV_
    TARGETS`-Override; Compose-Smoke `/health` + OTel-
    Collector-`:13133` gruen.
  - `make docs-check` cache-frei gruen.
  - `make gates` cache-frei gruen (10/10 A-1-Gates inkl.
    `make lint` ueber NEU `tools/render_trivyignore.py`;
    Test-Counts unveraendert 1722/80/4 skipped).

### C3 — `docs(plan)`: Status/DoD-Sync

**Welle-4a-Closure-Sync.**

- `M6-welle-4a.md` Status `In Progress → Done 2026-06-06`
  mit Liefer-Hash-Stack.
- `M6-perf-security-cicd.md §3.1` Welle-4a-Zeile `In
  Progress → Done` mit Closure-Hash + §3 Aktive-Welle-
  Block auf Welle 4b (Performance-Bench).
- `open/033-otel-collector-go-stdlib-cve-bump.md` Status-
  Block um „Temp-Deferral via Welle-4a-vulnignore-Pattern
  (Hash `<C2-Hash>`); echte Aufloesung weiter bei OTel-
  Stable-Release 0.154.0+ mit go1.26.4+ (per
  Aktivierungs-Bedingungen unveraendert)" ergaenzt.
- `carveouts.md §2.X` NEU Trigger-033-Eintrag (in Welle-3-
  Post-Closure nicht eingepflegt; hier nachgepflegt) als
  `Active in M6-Welle-4a-Temp-Deferral; Open bis OTel-
  Stable-Release 0.154.0+`.
- **Top-Level-Doku-Sync:**
  - `README.md` + `README.de.md`: NEU Hinweis auf
    `deploy/security/vulnignore.yaml`-Source-of-Truth
    (kurzer Satz: „Image-Audit-Ignores werden aus
    `deploy/security/vulnignore.yaml` generiert"); Welle-
    4a-Abschluss-Notiz.
  - `roadmap.md §3 M6` aktive-Welle-Block auf M6-Welle-4b
    + Welle-4a-Abschluss-Notiz mit Stack-Range.

### Welle-4a-Closure-Folge (nach C3, Pattern Welle-3)

- C4a `git mv M6-welle-4a.md → done/` (rename-only).
- C4b Cross-Doc-Refs-Sync nach Move.

C4a/C4b dienen gleichzeitig als M6-Welle-4b-Pre-C0a/Pre-
C0b.

---

## 5. Critical Files

**Welle-4a-NEU (geschrieben in C0/C1/C2):**

- `docs/plan/planning/in-progress/M6-welle-4a.md` (C0,
  dieser Commit).
- `docs/plan/adr/0044-generated-trivyignore-permit.md` (C1)
  — NEU `Provisional`-ADR.
- `tools/render_trivyignore.py` (C2) — NEU Render-Script;
  Source-of-Truth-Renderer.
- `deploy/security/vulnignore.yaml` (C2) — NEU Audit-
  Source-of-Truth mit CVE-2026-42504-Initial-Eintrag.

**Welle-4a-MODIFY (in C0/C1/C2/C3):**

- `docs/plan/planning/in-progress/README.md` (C0 + C3) —
  Bestand-Tabelle + Aktive-Welle-Block.
- `docs/plan/planning/in-progress/M6-perf-security-cicd.md`
  (C0 + C3) — §3.1 Welle-Status-Tabelle (4 → 4a + 4b
  gespalten); §3.2 Welle-4-Block um Sub-Slicing-Notiz.
- `docs/plan/adr/README.md` (C1) — ADR-Index Aktive-ADRs-
  Tabelle ADR-0044-Zeile + ADR-0043-Schaerfungen-Spalte.
- `Makefile` (C2) — `render-trivyignore`-Target + `image-
  audit`-Erweiterung.
- `.gitignore` (C2) — `deploy/security/.trivyignore`-
  Eintrag.
- `docs/plan/planning/in-progress/roadmap.md` (C3) — §3 M6
  aktive-Welle-Block + Welle-4a-Abschluss-Notiz.
- `docs/plan/planning/in-progress/carveouts.md` (C3) —
  NEU Trigger-033-Eintrag.
- `docs/plan/planning/open/033-otel-collector-go-stdlib-
  cve-bump.md` (C3) — Status-Block-Erweiterung um Temp-
  Deferral-Notiz; bleibt in `open/`.
- `README.md` + `README.de.md` (C3) — NEU
  vulnignore.yaml-Hinweis.

**Welle-4a-UNBERUEHRT (kein Edit):**

- Aller Code unter `src/` (Welle 4a ist Security-Pattern-
  Substanz, kein Python-Code-Pfad-Wechsel).
- Alle Tests unter `tests/` (Test-Counts bleiben
  1722/80/4).
- `Dockerfile` (Welle-1/2-Substanz bereits stabil; Welle
  4a beruehrt keine Build-Stage).
- Alle GitHub-Actions-Workflows (Welle-3-Substanz
  unangetastet; `make fullbuild`-CI-Pflicht-Gate aus
  fullbuild.yml ruft das Makefile auf, das durch Welle-4a-
  C2 grueun wird).
- ADRs 0001..0043 (Welle 4a fuegt NEU ADR-0044 hinzu;
  Bestehende `Provisional`/`Accepted`-Texte bleiben
  unangetastet per ADR-0006 §3 + ADR-0011 §4).
- `deploy/compose.yml` + `deploy/otel-collector-config.
  yaml` (Welle-1/2-Substanz; Welle 4a beruehrt keine
  Compose-Konfiguration).

---

## 6. Verifikationspfad

**Welle-4a-Gate:**

- `make docs-check` cache-frei gruen ueber alle Welle-4a-
  Commits.
- `make gates` cache-frei gruen (10/10 A-1-Gates; Test-
  Counts unveraendert 1722/80/4 skipped).
- `make ci` cache-frei gruen (inkl. `image-audit` mit
  `--ignorefile`-Erweiterung).
- `make fullbuild` cache-frei gruen ohne `CRITICAL_COV_
  TARGETS`-Override.
- `make render-trivyignore` EXIT=0; Output-Datei
  `deploy/security/.trivyignore` enthaelt CVE-2026-42504-
  Zeile + Begruendungs-Kommentar + `expires`-Marker.
- GitHub-Actions-Workflow `fullbuild.yml` cache-frei gruen
  beim Push der C2/C3-Hashes (reale CI-Sensor-Verifikation
  analog Welle-3-C2 `ce13253` + Post-Closure-Korrekturen-
  Fluss).

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur Doc-Substanz.
- C1 prueft ADR-0044-Body + ADR-Index-Konsistenz +
  ADR-0043-Schaerfungs-Spalte.
- C2 prueft Render-Script + vulnignore.yaml-Schema +
  Makefile-Hook + alle bestehenden Gates gruen.
- C3 prueft Status-Flip + Trigger-033-Status-Block-Pflege
  + Top-Level-Doku-Sync.

**Abnahme-Verifikation:**

- ADR-0043 §2.2-Verbots-Block bleibt textlich unveraendert.
- ADR-0044 als ADR-0011-konforme Schaerfung verankert.
- `make fullbuild` cache-frei gruen auf `main` (Trigger-
  033-`Konsequenz-wenn-ungeloest`-Block-Aufloesung im
  CI-Sinne, ohne Trigger-033-Sub-Substanz aufzuloesen).

**Verbleibendes Item (bedingt):**

- Reale GitHub-Actions-Run-Verifikation des `fullbuild.yml`-
  Workflows beim naechsten Push. Lokal verifiziert (alle
  make-Targets gruen); echter GitHub-Lauf folgt mit Push
  (User-Operation).

---

## 7. Risiken

**R1 — ADR-0044-`Provisional`-Status nicht ausreichend.**
Falls ein Compliance-Audit innerhalb der ADR-0043+ADR-0044-
Provisional-Phase die `vulnignore.yaml`-Form als unzulaessig
bewertet, koennte ADR-0044 zur ADR-0043-Supersedes-Pflicht
werden.
**Mitigation:** ADR-0044 bleibt strikt additiv (Pflicht-
Felder + Ablauf-Forcing); §2.2-Verbote von ADR-0043 bleiben
in Kraft. M6-Welle-7-Closure-C1 buendelt ADR-0044 mit ADR-
0041/0042/0043 auf `Accepted` — bei dem Closure ist
Aufmerksamkeit fuer Compliance-Konfliktpotential erforderlich.

**R2 — `expires: 2026-06-20` zu kurz / zu lang.** Falls
OTel-Stable-Release 0.154.0+ frueher kommt (z. B. 2026-
06-08), wird der vulnignore-Eintrag obsolet bevor `expires`
abgelaufen. Falls spaeter (z. B. 2026-06-25), bricht
render-Script und Welle-4b ist blockiert.
**Mitigation:** 2-Wochen-Safety-Margin gegenueber OTel-
Release-Korridor (2026-06-09 bis 2026-06-12); bei Drift
ueber `expires` kann der Eintrag in einem 5-min-Folge-Commit
erneuert werden (kurze Maintenance-Schwelle). Bei Stable-
Release < `expires`: vulnignore-Eintrag wird im Stable-Bump-
Commit entfernt (Trigger 033 wird dann geschlossen).

**R3 — Trivy-`--ignorefile`-Pfad-Aufloesung im Container.**
`tools/render_trivyignore.py` schreibt `deploy/security/
.trivyignore` ins Host-Repo-Verzeichnis; Trivy laeuft im
Docker-Container. Pfad-Mount erforderlich.
**Mitigation:** Makefile-Trivy-Aufruf bindet die Datei per
`-v "$(pwd)/deploy/security/.trivyignore":/security/
.trivyignore:ro` ein und verwendet `--ignorefile /security/
.trivyignore`. Verifikation in C2 (Trivy meldet „Some
vulnerabilities have been ignored/suppressed" als
Bestaetigung des Filter-Greifens).

**R4 — vulnignore.yaml-YAML-Schema-Drift.** Render-Script
liest YAML-Subgraph per awk; Schema-Aenderungen im m-trace-
Pattern werden nicht automatisch synced.
**Mitigation:** Welle-4a-Slice-Doc §1.1 verankert m-trace-
Quelle; Cross-Project-Konsistenz ist sekundaer; intra-
grid-gym-Konvention primaer. Bei m-trace-Schema-Drift wird
das in einem Folge-Slice nachgezogen, nicht automatisch.

**R5 — Trigger-033-Status-Block-Pflege-Drift.** Bei OTel-
Stable-Release-Aufloesung muss Trigger 033 nach `done/`
gewandert werden UND vulnignore-Eintrag entfernt werden
UND `Makefile`-Pin gebumpt werden.
**Mitigation:** Trigger 033 `open/`-Doc Status-Block in C3
verankert den 3-Schritt-Aufloesungs-Pfad explizit. Welle-
4b-Pre-C0c oder spaeterer Slice fuehrt das aus.

**R6 — `--ignorefile`-Trivy-Version-Pin.** Trivy `0.58.0`
(grid-gym `TRIVY_IMAGE`-Pin) unterstuetzt `--ignorefile`;
bei Trivy-Bump koennte sich die Pfad-Semantik aendern.
**Mitigation:** Trivy-Version-Pin in Makefile bleibt
unangetastet in Welle 4a. Bei Trivy-Bump muss `--ignorefile`-
Semantik re-verifiziert werden (M7+ oder spaeter).

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack** (per
  [`../README.md`](../README.md) Wave-Self-Close-Commit-
  Konvention): sobald `M6-welle-4a.md` Status `Done`
  erreicht (am Ende von C3), schliesst die Welle ihre
  eigene Commit-Sequenz mit einem reinen `git mv
  M6-welle-4a.md → ../done/M6-welle-4a.md` (C4a) +
  Cross-Doc-Refs-Sync (C4b). Pattern analog M6-Welle-3-
  C4a `3b6d9bf`/C4b `c36f734`.
- C4a/C4b dienen gleichzeitig als M6-Welle-4b-Pre-C0a/
  Pre-C0b.
- NEU ADR 0044 wird in C1 angelegt; `Provisional → Accepted`
  in M6-Welle-7-Closure-C1 gebuendelt mit ADR 0041 + ADR
  0042 + ADR 0043.
- Trigger 033 (`open/033-otel-collector-go-stdlib-cve-
  bump.md`) bleibt offen; wandert erst bei OTel-Stable-
  Release-Aufloesung nach `done/` (separater Slice oder
  Welle-4a-Post-Closure-Korrektur).

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **C0 — NEU `M6-welle-4a.md`** mit §1..§9-Struktur
  (dieser Commit).
- [x] **C0 — `in-progress/README.md`** Bestand-Tabelle
  um `M6-welle-4a.md`-Eintrag ergaenzt + Aktive-Welle-
  Block auf M6-Welle-4a.
- [x] **C0 — `M6-perf-security-cicd.md §3.1`** Welle-4-
  Zeile in 4a/4b gespalten; 4a `Pending → In Progress
  2026-06-06`.
- [x] **C1 — NEU `docs/plan/adr/0044-generated-
  trivyignore-permit.md`** `Provisional` (ADR-0011-
  Schaerfung an ADR-0043 §2.2).
- [x] **C1 — `docs/plan/adr/README.md`** ADR-Index um
  ADR-0044-Zeile + ADR-0043-Schaerfungen-Spalte um
  „ADR 0044" ergaenzt (ADR-0011 §4-Pattern).
- [x] **C2 — NEU `deploy/security/vulnignore.yaml`** mit
  CVE-2026-42504-Eintrag (`reason` + `expires:
  2026-06-20` + `scope: otel-collector`); Datei-Header-
  Schema-Block analog m-trace.
- [x] **C2 — NEU `tools/render_trivyignore.py`**
  Python-Port aus m-trace-`render-trivyignore.sh` (bash+
  awk → Python+PyYAML; CLI-Pattern analog `tools/
  check_noqa.py`/`check_spdx.py`).
- [x] **C2 — `.gitignore`** um `deploy/security/
  .trivyignore`-Eintrag ergaenzt.
- [x] **C2 — `Makefile`** NEU `render-trivyignore`-Target
  (PHONY) + `image-audit`-Erweiterung um `--ignorefile`-
  Argument fuer den OTel-Collector-Run.
- [x] **C2 — `make render-trivyignore`** EXIT=0 lokal;
  `deploy/security/.trivyignore` enthaelt CVE-2026-42504-
  Eintrag.
- [x] **C2 — `make image-audit`** cache-frei gruen lokal.
- [x] **C2 — `make ci`** cache-frei gruen lokal.
- [x] **C2 — `make fullbuild`** cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override lokal.
- [x] **C2 — `make gates`** cache-frei gruen (10/10 A-1-
  Gates; Test-Counts unveraendert 1722/80/4 skipped).
- [x] **C3 — `M6-welle-4a.md`** Status `In Progress →
  Done 2026-06-06` mit Liefer-Hash-Stack.
- [x] **C3 — `M6-perf-security-cicd.md §3.1`** Welle-4a-
  Zeile `In Progress → Done` mit Closure-Hash + §3
  Aktive-Welle-Block auf Welle 4b.
- [x] **C3 — `open/033-otel-collector-go-stdlib-cve-
  bump.md`** Status-Block um „Temp-Deferral via
  Welle-4a-vulnignore-Pattern; echte Aufloesung weiter
  bei OTel-Stable-Release 0.154.0+" ergaenzt; Trigger 033
  bleibt offen.
- [x] **C3 — `carveouts.md §2.X`** NEU Trigger-033-Eintrag
  als `Active in M6-Welle-4a-Temp-Deferral` (Welle-3-
  Post-Closure-Vergesslichkeit nachgepflegt).
- [x] **C3 — `README.md` + `README.de.md`** NEU
  vulnignore.yaml-Source-of-Truth-Hinweis.
- [x] **C3 — `roadmap.md §3 M6`** aktive-Welle-Block auf
  M6-Welle-4b + Welle-4a-Abschluss-Notiz mit Stack-Range.
- [x] **C3 — `in-progress/README.md`** Bestand-Tabelle
  Welle-4a-Zeile auf `Done` + Aktive-Welle-Block auf
  M6-Welle-4b.
- [x] **C3 — `make docs-check`** cache-frei gruen.
- [x] **C3 — Reale GitHub-Actions-Run-Sensor-Check** beim
  Push der C2/C3/Post-Push-Fix-Hashes (`fullbuild.yml`
  cache-frei gruen auf `main`) — Lauf 27055273876 gruen
  (6m56s, 2026-06-06T06:41:55Z); Post-Push-CI-Fix `f46e789`
  loest pre-existing latente Compose-v2-`--wait`-Drift
  (siehe §10).

**Anti-Scope-Verifikation (Welle 4a NICHT):**

- [x] Kein OTel-Collector-Image-Bump (Trigger 033 bleibt
  offen).
- [x] Keine Performance-Bench (Welle-4b-Scope; `GG-RT-
  001..005`).
- [x] Keine ADR-0029-Beruehrung (Coverage-Gate-Vertrag
  unangetastet).
- [x] Keine `--skip-vuln`-Argument-Anpassung (`--ignorefile`
  ist Datei-basierte Form, nicht CLI-Allowlist).
- [x] Keine permanente Defer-Form (`expires`-Pflicht).
- [x] Keine `pre-commit`-Hook-Substanz.

---

## 10. Post-Closure-Korrekturen-Index (Pflege nach Welle-4a-C3)

**Pflege-Pattern:** analog Welle-3-Done-Slice-Doc §10. Die hier
dokumentierte Substanz ist Welle-4a-Stand zum C3-Closure-
Zeitpunkt (`f19837f`); nach Closure entdeckte CI-Sensor-Drifts
werden in Folge-Commits korrigiert, OHNE die Closure-Substanz
oben zu revidieren. Dieser Index listet die kanonischen Post-
Closure-Korrektur-Hashes.

**Korrektur-Stack:**

| Commit | Stufe | Substanz |
| ------ | ----- | -------- |
| `f46e789` | Post-Push-CI-Fix | **F1 HIGH (CI-only)** `docker compose up --wait` in Compose-v2-CI-Version exit-1 bei `simulation`-Service mit `healthcheck: test: ["NONE"]` (dokumentierte Disable-Form). Pre-existing latente Drift seit M6-Welle-3-C2 `ce13253` (`fullbuild.yml`-CI-Pflicht-Gate angelegt), hinter Trigger-010-/-033-Image-Audit-Failures versteckt. Erstmals sichtbar nach Welle-4a-C2 `8fbd17c` (vulnignore-Pattern laesst `image-audit` gruen, runtime-Stage erreicht). Korrektur: `deploy/compose.yml` Z.152 `test: ["NONE"]` → `test: ["CMD", "true"]` + `interval/timeout/retries`-Defaults (Always-Healthy fuer `sleep infinity`-Stub-Container; M2-Geraete-Runner bringen produktiven Healthcheck zurueck). Lokal `make runtime` cache-frei gruen (Compose-Smoke + `/health` + `:13133`-Poll + Teardown). CI-Sensor-Beleg: `fullbuild.yml`-Lauf 27055273876 gruen (6m56s) — erstmalig seit `fullbuild.yml`-Anlage in M6-Welle-3-C2 `ce13253`. |
| `<TBD-F2>` | Post-Closure-Review-Folge | **F2 HIGH** (ADR-0044-§2.2-Vertragsbruch) `tools/render_trivyignore.py` erzwang `reason` + `scope` **nicht** als Pflicht-Felder — fehlende `reason` lieferte einen leeren Kommentar, fehlende `scope` wurde je nach Scope-Filter still ignoriert oder als `*` behandelt. Eine HIGH/CRITICAL-CVE konnte dadurch ohne auditfaehige Begruendung oder sauberen Scope in die generierte `.trivyignore` gelangen — direkter ADR-0044-§2.2-Vertragsbruch. Korrektur: `_emit_entry` prueft `reason` und `scope` vor dem Scope-Matching und bricht mit EXIT=1 bei leerem/fehlendem Feld; `scope_display`-Fallback `or "*"` entfernt (Always-Echo des konkreten Scope). NEU `tests/unit/test_render_trivyignore.py` (10 Tests; deckt id/expires/expired/reason-missing/reason-whitespace/scope-missing/scope-empty-even-without-filter/scope-filter-skip/wildcard-match/valid-entry ab; +10 Unit-Tests = 1722→1732). Plus **F3 LOW** `deploy/security/vulnignore.yaml` Wartungsregel-Kommentar nannte `bash tools/render-trivyignore.sh <scope>` (Pre-Python-Port-Stand); auf `make render-trivyignore` (`tools/render_trivyignore.py` via docker-source-Stage) korrigiert und Pflicht-Felder-Regel ergaenzt. Plus **F4 LOW** `done/M6-welle-4a.md §0` Status-Block + Stack-Range in `in-progress/README.md` + `M6-perf-security-cicd.md` + `roadmap.md` von `9bb6a92..3bc58b8` (C4a-Hash) auf `9bb6a92..789ac50` (C4b-Hash; tatsaechliche Welle-Closure-End-Form) konkretisiert; „C4b dieser Commit"-Verbiage auf konkreten `789ac50`-Hash umgehakt. |

**Aktueller Compose-Stand** (Post-Closure-Korrektur-Stand
nach `f46e789`):

- `deploy/compose.yml` `simulation`-Service Healthcheck:
  `test: ["CMD", "true"]` mit `interval: 5s` / `timeout: 1s`
  / `retries: 1`. Stub-Container ist immer-healthy ohne
  echte Probe.
- `api` / `postgres` / `otel-collector`-Healthcheck-Substanz
  unveraendert gegenueber Welle-4a-C3-Stand.
- `make runtime` cache-frei gruen lokal; `make fullbuild`
  cache-frei gruen lokal UND CI-Sensor (Lauf 27055273876
  gruen 6m56s).
- CI-Sensor-Beleg: `fullbuild.yml`-Lauf 27055273876 cache-
  frei gruen (push von `f46e789` 2026-06-06T06:41:55Z) —
  erstmaliger CI-`make fullbuild`-Gruen-Beleg seit
  `fullbuild.yml`-Anlage in M6-Welle-3-C2 `ce13253`.

---

## References

- [`../done/M6-welle-3.md §10`](M6-welle-3.md) —
  M6-Welle-3-Post-Closure-Korrekturen-Index; Quelle der
  Trigger-033-Substanz und der `make fullbuild`-Rot-Diagnose.
- [`M6-perf-security-cicd.md §3.2 Welle 4`](M6-perf-security-cicd.md)
  — M6-Slice-Plan Welle-4-Vorbelegung (Performance-Bench;
  wird durch Welle-4a-Subdivision in 4a/4b gespalten).
- [`../open/033-otel-collector-go-stdlib-cve-bump.md`](../open/033-otel-collector-go-stdlib-cve-bump.md)
  — Trigger 033 mit Aktivierungs-Substanz; bleibt OFFEN.
- [`../../adr/0011-schaerfung-ohne-abloesung.md §2`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — Schaerfungs-Pattern-Vertrag (ADR-0044 folgt diesem
  Pattern).
- [`../../adr/0043-image-audit-strategy.md §2.2 + §7`](../../adr/0043-image-audit-strategy.md)
  — Image-Audit-Defer-Form-Verbote; ADR-0044 schaerft
  additiv ohne §2.2-Verbote zu beruehren.
- [`../../adr/0028-link-maintenance-accepted-adr-bezug.md`](../../adr/0028-link-maintenance-accepted-adr-bezug.md)
  — Link-Maintenance-Pattern fuer ADR-Index-Pflege.
- m-trace-Schwester-Repo `/Development/m-trace/scripts/
  render-trivyignore.sh` + `/Development/m-trace/.security/
  vulnignore.yaml` — externe Source-of-Truth-Form-Quelle.
- https://avd.aquasec.com/nvd/cve-2026-42504 — CVE-Detail
  (Go-stdlib MIME-Header-DoS).
- https://github.com/open-telemetry/opentelemetry-collector-
  releases/releases — OTel-Collector-Release-Index zur
  Trigger-033-Aktivierungs-Pruefung.
