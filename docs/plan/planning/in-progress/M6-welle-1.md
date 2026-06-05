# Welle 1 — M6 Base-Image-Bump (krb5-CVE-Aufloesung)

**Status:** In Progress — eroeffnet mit C0 (dieser Commit;
NEU Slice-Doc). Welle 1 ist die **erste Code-Welle in M6**
und loest die seit M3-Welle-7-Closure (`c61ab0d`,
2026-05-25) pre-existing rote `make fullbuild`-Pipeline auf
([`../open/010-base-image-krb5-cve-bump.md`](../open/010-base-image-krb5-cve-bump.md)
Trigger 010 = M4-Welle-7-Erbschaft;
[`../done/M4-results.md §2 + §4 S-4`](../done/M4-results.md)).

**Pre-C0 abgeschlossen (2 Commits aus M6-Welle-0-Closure-
Folge):**

1. Pre-C0a `76f892d` — `git mv in-progress/M6-welle-0.md
   → done/` (Self-Close-Move, rename-only; Pattern Welle-
   6c-C4a `c317200`).
2. Pre-C0b `960f6ed` — Cross-Doc-Refs-Sync nach Move
   (M6-Welle-0-C4b; Refs in `M6-perf-security-cicd.md`,
   `roadmap.md`, `carveouts.md`, `in-progress/README.md`).

**Kein Pre-C0c-Smoke-Probe-Run noetig** — krb5-Bump ist
ein Dockerfile-`FROM`-Edit, kein API-Surface-Wechsel; die
ADR-0036-Indikations-Validierungsproblematik aus M5-Welle-1
(`9c20dad` HTMX-FastAPI-Probe) hat in Welle 1 kein Pendant.
Trivy-Probe gegen das neue Base-Image laeuft in C2 als Teil
der `make image-audit`-Verifikation.

**Spec-Reife:** Inhaltlich final fuer Welle 1. Welle-1-
Decision-Liste (§3) schliesst die offenen Welle-0-Decisions
M6-D-4-Teil (ADR 0043 ja/nein) und M6-D-5 (`make fullbuild`-
Drift-Aufloesung). Welle-1-D-1 (CI-Pflicht-Gate fuer `make
fullbuild`) bleibt in C0 offen und wird in C2/C3 entschieden
nach Mass der lokalen `make fullbuild`-Sauberkeit + CI-
Editing-Aufwand.

---

## 1. Context

[`../done/M6-welle-0.md`](../done/M6-welle-0.md) hat den
M6-Slice-Plan
[`M6-perf-security-cicd.md`](M6-perf-security-cicd.md)
produktiv eroeffnet mit 8 Wellen 0..7. Welle 1 ist nach
M6-D-1-Option-B-Vorbelegung („pro Triggerebene") die erste
Code-Welle und traegt das kleinste, am besten isolierte
Trigger-Item: krb5-Bump.

### 1.1 Pre-existing Drift-Stand

Per [`../open/010-base-image-krb5-cve-bump.md`](../open/010-base-image-krb5-cve-bump.md):

- `make gates` (10 A-1-Gates): **cache-frei gruen ohne
  Override** — harte DoD-Gates sind unbeeintraechtigt.
- `make image-audit` (`trivy --ignore-unfixed`): rot wegen
  vier HIGH-CVEs in der krb5-Famille.
- `make fullbuild` (`ci + image-audit + test-integration +
  openapi-validate`): rot wegen `image-audit`.

Die fuehrende CVE-ID ist **`CVE-2026-40356`** in
`krb5`-Paketen mit Fix `1.21.3-5+deb13u1` verfuegbar (plus
drei weitere HIGH-CVEs der gleichen Famille).

### 1.2 Dockerfile-Status (Stand 2026-06-05)

`./Dockerfile` (Repository-Root):

- `ARG PYTHON_VERSION=3.14` + `ARG UV_VERSION=0.5.31`.
- Base-Stage: `FROM python:${PYTHON_VERSION}-slim AS base`
  — Python-3.14-Slim-Variante. Debian-13-Trixie liegt
  darunter. Die krb5-CVE-Famille trifft den `libkrb5-3` +
  `libk5crypto3` + `libgssapi-krb5-2`-Stack im Base-Layer.
- Multi-Stage mit `base → builder → runtime`-Pattern (ADR
  0002-Spike-0-Closure-Stack).

### 1.3 Welle-1-Lieferziel

Vier Sub-Items:

1. **`Dockerfile`-`FROM`-Update** auf eine neuere Debian-
   13-Punktversion mit krb5-Patch (oder explizit pinning
   auf `python:3.14-slim-trixie` falls ein neueres Tag mit
   krb5-Fix verfuegbar ist). Falls Debian-13-Stand noch
   nicht patched, alternativ Bookworm-Variante oder
   explizites `apt-get install -y libkrb5-3 libk5crypto3
   libgssapi-krb5-2`-Hardening **im `runtime`-Stage**
   (`Dockerfile` Z.405ff `FROM python:${PYTHON_VERSION}-slim
   AS runtime`; das Runtime-Image laeuft eigenstaendig und
   ist das `make image-audit`-Scan-Ziel, nicht der `base`-
   Stage). Der bestehende `apt-get upgrade --yes` im
   runtime-Stage (Z.422-426; Trigger-015-Pattern) ist die
   verbindliche Lokation; krb5-spezifische `apt-get install`-
   Erweiterung wird in derselben `RUN`-Layer angehaengt. Ein
   reines `base`-Stage-Hardening wuerde Trivy nicht im
   Runtime-Image sehen (multi-stage-Build laesst base-only-
   Layers nicht ins finale Image durch).
2. **`uv.lock`-Refresh** falls Library-Pins durch Image-
   Bump beruehrt werden (z. B. `cryptography`-Wheel mit
   OpenSSL-3.x-Dependency).
3. **NEU ADR 0043** (`Image-Audit-Strategie`) als M6-D-4-
   Vorbelegung-Schaerfung; siehe §3 Decision M6-D-4-Teil.
4. **Status/DoD-Sync** + Top-Level-Doku-Sync inkl.
   `README.md`/`README.de.md`-`make fullbuild`-Hinweis-
   Aufloesung + Roadmap-Notiz-Update.

### 1.4 Welle-1-Anti-Scope

- **Kein CI/CD-Vollausbau** — `make test-unit` +
  `coverage-gate` + `dep-audit` + Python-3.13/3.14-Matrix
  als CI-Jobs sind Welle-3-Scope (`GG-CICD-001..006`).
- **Kein SBOM-Hook** — `make sbom` + Release-Workflow ist
  Welle-2-Scope (Trigger 008 + `GG-CICD-007`).
- **Kein Performance-Bench** — `make perf` + `GG-RT-005`-
  Bench ist Welle-4-Scope.
- **Kein Security-Audit** — `GG-SAFE-001..008` ist Welle-
  5-Scope.
- **Kein Deploy-Hardening-Vollausbau** — `GG-DEPLOY-*` ist
  Welle-6-Scope; Welle 1 traegt nur das Image-Audit-Drift-
  Aufloesungs-Stueck.
- **Kein IEC-Smoke-Pfad-B** — Trigger 009 + Multi-Python-
  Test-Stage ist Welle-6-Scope.
- **Keine Carveout-`Deferred`-Aufloesung opportunistisch**
  — die 6 M5-Erbschafts-`Deferred`-Items (`carveouts.md
  §2.1`) bleiben in Welle 1 unangefasst; insbesondere die
  in M6-D-3 vorgemerkte URL-Versionierung `/api/v1` wandert
  nicht proaktiv in Welle 1 mit (User-Klaerung 2026-06-05:
  Single-Welle scope-eng halten).

---

## 2. Scope

Welle 1 liefert **vier Items** ueber 4 Commits (C0..C3),
plus den optional bedingten CI-Gate-Folge-Slice (siehe
Welle-1-D-1):

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses
   Dokument.
2. **NEU ADR 0043** (C1) — `Image-Audit-Strategie + Trivy-
   Defer-Aufloesungs-Pattern`. Start als `Provisional` mit
   Trigger-010-Hash-Anchor-Block. **Bleibt `Provisional`
   nach C3** — M6-Welle-7-Closure-Convention
   ([`M6-perf-security-cicd.md §2 ADR-Lifecycle`](M6-perf-security-cicd.md))
   zieht alle M6-ADRs (0041..0043) gebuendelt auf `Accepted`
   (Pattern analog M5-Welle-7-C1 `62f988d`: „5 M5-ADRs
   0036..0040 `Provisional → Accepted`"). C3 vermerkt
   stattdessen nur den C2-Hash als Provisional-Beleg im
   ADR-Body (Trigger-010-Aufloesungs-Hash).
3. **Dockerfile-Bump + Verifikation** (C2) — Dockerfile-
   `FROM`-Update + ggf. `uv.lock`-Refresh + `make image-
   audit` + `make fullbuild` cache-frei gruen.
4. **Status/DoD-Sync** (C3) — `M6-welle-1.md` auf `Done`,
   `M6-perf-security-cicd.md §3.1` Welle-1-Zeile auf
   `Done`, ADR 0043 bleibt `Provisional` mit C2-Hash-
   Beleg im ADR-Body (Accept in Welle 7), Top-Level-Doku-
   Sync
   (`README.md`/`README.de.md` `make fullbuild`-Hinweis
   aufgeloest), `roadmap.md §1` Status-Header-`make
   fullbuild`-Defer-Pfad-Notiz aufloesen, Trigger 010
   `open/ → done/`-Move (Trigger-Aufloesungs-Pattern).

Self-Close-Move + Cross-Doc-Refs-Sync (Welle-1-C4a/C4b)
sind die Welle-1-Closure-Folge nach C3, parallel zur
Welle-2-Pre-C0a/Pre-C0b-Eroeffnung (Pattern Welle-6c-C4a
`c317200`/C4b `cfb9626`).

---

## 3. Architektur-Entscheidungen (Welle-1-Decision-Liste)

Welle 1 schliesst diese Decisions aus
[`../done/M6-welle-0.md §3`](../done/M6-welle-0.md):

### M6-D-5 — `make fullbuild`-Drift-Aufloesung

**Frage:** Wird `make fullbuild` in M6 cache-frei gruen?

Welle-0-Vorbelegung: **Ja**, durch Trigger 010 krb5-Bump in
Welle 1. Welle-7-S-3-Sweep verifiziert.

**Welle-1-Final:** Decision steht; konkrete Aufloesungs-
Variante (Dockerfile-Punktversion-Pin vs. explizites apt-
Hardening) wird in C2 nach Trivy-Probe-Resultat
entschieden. ADR 0043 verankert das Aufloesungs-Pattern,
nicht die konkrete Variante.

### M6-D-4-Teil — ADR 0043 Image-Audit-Strategie

**Frage:** Wird ADR 0043 (Image-Audit-Pflicht-Strategie)
in M6 erstellt?

Welle-0-Vorbelegung (M6-D-4): **ggf. ADR 0043** — bewusst
konservativ als „ggf." markiert; tatsaechliche Anzahl
haengt vom Welle-X-C0-Schaerfen ab.

**Welle-1-Final:** **Ja, ADR 0043 wird erstellt** in C1.
Begruendung: Welle 1 macht `make image-audit` + `make
fullbuild` nicht nur als einmalige Sensoren relevant,
sondern definiert faktisch:

- Welche Image-Audit-Pflicht-Schwelle gilt repo-weit
  (Makefile-Status `TRIVY_SEVERITY=HIGH,CRITICAL` plus
  `--ignore-unfixed`; siehe `Makefile` Z.25-26 + Z.279-294).
- Wie ein Trivy-Defer-Pfad (`open/`-Trigger der
  Variante 010) wieder aufgeloest wird.
- Wie das in `make fullbuild` als Pflicht-Gate-Vorbedingung
  verankert ist.

Das ist ein **wiederverwendbarer Architektur-/Quality-Gate-
Vertrag**, nicht nur Slice-Lokalitaet — und damit ADR-
pflichtig analog ADR 0029 (No-Coverage-Pragma-Contract) +
ADR 0028 (Link-Maintenance).

**ADR-0043-Inhalt (Vorbelegung, C1 fixiert final):**

- §1 Context: M3-Welle-7-pre-existing-`make fullbuild`-rot
  durch krb5-CVE-Famille; M4/M5 hatten das als dokumentierten
  Defer-Pfad gefuehrt; M6-Welle-1 loest auf.
- §2 Decision: `make image-audit` ist Pflicht-Gate mit
  zwei orthogonalen Trivy-Filter-Auspraegungen, beide
  Makefile-Default (`Makefile` Z.25-26 + Z.279-294):
  (a) `TRIVY_SEVERITY=HIGH,CRITICAL` pinned die Schwellen-
  Klassen (LOW/MEDIUM ausgeblendet); (b) `--ignore-unfixed`
  filtert CVEs ohne verfuegbaren Fix aus dem Report
  heraus (nicht als „Marker", sondern als Filter im
  Trivy-Run). Die einzig zulaessige Defer-Form fuer
  HIGH/CRITICAL-CVEs mit Fix ist ein `open/`-Trigger mit
  konkreter CVE-ID + Fix-Version; ein blosses
  `.trivyignore`-Eintragen ohne `open/`-Begleiteintrag ist
  ADR-Bruch.
- §3 Konsequenzen: `make image-audit` ist Pflicht in `make
  ci` und `make fullbuild`; `open/`-Trigger ist die einzige
  Defer-Lifecycle-Form; `done/`-Move erfolgt sobald Bump
  cache-frei gruen ist (Welle-1-C3-Substanz).
- §4 Bezug: ADR 0028 (Link-Maintenance) + ADR 0029 (Pragma-
  Contract als Gate-Vertrag-Vorbild) + Trigger 010 + M3/M4/
  M5-results §4-S-4-Notes.

### Welle-1-D-1 — CI-Pflicht-Gate fuer `make fullbuild`

**Frage:** Wird ein CI-Pflicht-Gate fuer `make fullbuild`
in Welle 1 mitgezogen, oder vertagt auf einen Folge-Slice?

**Welle-1-C0-Stand:** Offen. Entscheidet sich in C2 nach
folgendem Mass:

- **Mitziehen in Welle 1** wenn (a) `make fullbuild` lokal
  sauber gruen nach Dockerfile-Bump UND (b) GitHub-Actions-
  Workflow-Editing klein ist (≤ 1 Job-Definition-Block
  oder ≤ 1 Step-Erweiterung in einem bestehenden Job).
- **Vertagen auf Folge-Slice** wenn (a) `make fullbuild`
  weitere Hardening-Schritte braucht (Library-Drift durch
  Image-Bump, Test-Brueche) ODER (b) CI-Editing neue
  Pipeline-Risiken aufmacht (Job-Konditional, Matrix-
  Wiring, Secret-Anforderungen).

**Begruendung der C0-Offenheit:** krb5-Bump-Side-Effects
sind erst nach C2-Probe sicher einschaetzbar; vorzeitige
Sub-Slicing-Vorbelegung (Welle 1a/1b) wuerde Plan-Overhead
einfuehren ohne Mehrwert. Falls Vertagung noetig wird,
entsteht ein NEU `open/`-Trigger („CI-Pflicht-Gate `make
fullbuild` fuer M6-Welle-3") in C3.

### Welle 1 trifft **keine** dieser Decisions

- M6-D-1 (Welle-Strategie) — bereits in M6-Welle-0-C2
  praktisch entschieden durch Welle-1-Eroeffnung als
  krb5-Slice (Option-B-Bestaetigung).
- M6-D-2 (Carveout-Triage) — bereits in M6-Welle-0-C2
  entschieden; Trigger 008/009/010 markiert.
- M6-D-3 (`Deferred`-Welle-Zuordnung) — bleibt offen fuer
  Welle 3+ (URL-Versionierung `/api/v1` ist Welle-3-
  Vorbelegung; nicht proaktiv in Welle 1).
- M6-D-3b (`Pattern-Forward` Pre-init-Defense) — opportunis-
  tisch in Welle 5/6; nicht in Welle 1.
- M6-D-4 (ADR-Anzahl) — Welle 1 fixiert nur ADR 0043;
  ADR 0041 (Performance-Bench) + ADR 0042 (SBOM-Tool)
  bleiben Welle-4-/Welle-2-Material.
- M6-D-6 (Python-3.13/3.14-Matrix) — Welle-3-Scope (CI-
  Vollausbau).
- M6-D-7 (Bench-Framework) — Welle-4-Scope.

---

## 4. Liefer-Reihenfolge (4 Commits)

### Pre-C0 — bereits erledigt (M6-Welle-0-Closure-Folge)

- `76f892d` (Pre-C0a: `git mv M6-welle-0.md → done/`).
- `960f6ed` (Pre-C0b: Cross-Doc-Refs-Sync nach Move).

### C0 — `docs(plan)`: M6-welle-1 Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU [`M6-welle-1.md`](M6-welle-1.md) mit §1..§9-Struktur.
- `in-progress/README.md` Bestand-Tabelle um Welle-1-Zeile
  ergaenzt (analog M5-Welle-1-C0-Pattern; Aktive-Welle-
  Block bleibt M6-Welle-1).
- M6-Slice-Plan
  [`M6-perf-security-cicd.md §3.1`](M6-perf-security-cicd.md)
  Welle-1-Zeile `Pending → In Progress` mit C0-Hash-Stub.

### C1 — `docs(adr)`: NEU ADR 0043 Image-Audit-Strategie

NEU `docs/plan/adr/0043-image-audit-strategy.md` als
`Provisional` mit:

- §1..§4 nach ADR-Standard-Pattern (vgl. ADR 0029).
- Trigger-010-Hash-Anchor-Block (M3-Welle-7 `c61ab0d` als
  Drift-Origin; M4-Welle-7-Defer-Pfad als Erbschafts-Stand;
  Welle-1-C2-Hash als Aufloesungs-Hash, in C3 nachgetragen).
- Status `Provisional` zunaechst (ADR-0011-Schaerfung-ohne-
  Supersedes-Pattern); **bleibt `Provisional` nach Welle-1-
  C3**. Accept passiert in M6-Welle-7-Closure gebuendelt mit
  ADR 0041 + ADR 0042 (M6-Plan-§2-Convention; Pattern analog
  M5-Welle-7-C1 `62f988d`). C3 traegt nur den C2-Hash als
  Provisional-Aufloesungs-Beleg in den ADR-Body nach.

### C2 — `chore(deploy)`: Dockerfile krb5-Bump

Code-Merge mit:

- **Dockerfile-`FROM`-Update**: `python:3.14-slim` →
  konkrete Punktversion-Pin ODER explizites apt-`libkrb5-*`-
  Hardening (entscheidet sich nach Trivy-Probe in C2).
- **ggf. `uv.lock`-Refresh** falls Library-Pin-Side-Effects
  durch Image-Bump.
- **Verifikation:**
  - `make gates` cache-frei gruen (10/10 A-1-Gates).
  - `make image-audit` cache-frei gruen (Trivy-Report ohne
    HIGH-CVE-krb5-Famille).
  - `make fullbuild` cache-frei gruen ohne `CRITICAL_COV_
    TARGETS`-Override.
  - Test-Counts unveraendert (1722 Unit + 80 Integration);
    Welle 1 fuegt keine neuen Tests hinzu.

### C3 — `docs(plan)`: Status/DoD-Sync + ADR-0043-Hash-Anchor

**Welle-1-Closure-Sync.**

- ADR 0043 bleibt `Provisional`; C2-Hash als Trigger-010-
  Aufloesungs-Beleg in den ADR-Body nachgetragen (Hash-
  Anchor-Block; Accept-Pflicht-Pfad geht ueber M6-Welle-7-
  Closure-C1 gebuendelt mit ADR 0041/0042 — Pattern analog
  M5-Welle-7-C1 `62f988d`).
- `M6-welle-1.md` Status `In Progress → Done` mit Liefer-
  Hash-Stack (C0..C3).
- `M6-perf-security-cicd.md §3.1` Welle-1-Zeile `In
  Progress → Done` mit Closure-Hash.
- DoD-Checkliste (§9) abhaken.
- Top-Level-Doku-Sync:
  - `README.md` + `README.de.md`: `make fullbuild`-`CVE-
    2026-40356`-Hinweis aufgeloest (Trigger 010-Erbschafts-
    Notiz raus).
  - `roadmap.md §1` Status-Header-`make fullbuild`-Defer-
    Pfad-Notiz aufloesen.
  - `roadmap.md §3 M6` aktive-Welle-Block auf
    M6-Welle-2 ausrichten (SBOM-Aktivierung Trigger 008).
- **Trigger 010 `open/ → done/`-Move**: `git mv
  open/010-base-image-krb5-cve-bump.md done/`; Cross-Doc-
  Refs-Sync in `carveouts.md §2.2` + `open/README.md`.
- **Welle-1-D-1 final** (in C2 entschieden, in C3 nur
  abgebildet): falls **Vertagen**, NEU `open/`-Trigger fuer
  M6-Welle-3 in C3 angelegt + `carveouts.md §2.X` Sync;
  falls **Mitziehen**, C3 verlangt zusaetzlich, dass der
  C2-CI-Workflow-Lauf gegen den C2-Hash gruen war (siehe §9
  DoD).

### Welle-1-Closure-Folge (nach C3, Pattern Welle-6c)

- C4a `git mv M6-welle-1.md → done/` (rename-only).
- C4b Cross-Doc-Refs-Sync nach Move (refs in
  `M6-perf-security-cicd.md`, `roadmap.md`, `carveouts.md`,
  `in-progress/README.md`).

C4a/C4b laufen parallel zur Welle-2-Eroeffnung als deren
Pre-C0a/Pre-C0b (Pattern analog Welle-6c→7).

---

## 5. Critical Files

**Welle-1-NEU (geschrieben in C0/C1):**

- `docs/plan/planning/in-progress/M6-welle-1.md` (C0,
  dieser Commit).
- `docs/plan/adr/0043-image-audit-strategy.md` (C1).

**Welle-1-MODIFY (in C0/C2/C3):**

- `Dockerfile` (C2) — `FROM`-Update oder apt-`libkrb5-*`-
  Hardening-Erweiterung des bestehenden `apt-get upgrade
  --yes`-Blocks im `runtime`-Stage (Z.422-426).
- `uv.lock` (C2, ggf.) — Library-Pin-Refresh.
- `.github/workflows/ci.yml` (C2, **conditional** — nur
  wenn Welle-1-D-1 zu „Mitziehen in Welle 1" entscheidet;
  siehe §3 Welle-1-D-1). Edits: NEU `make fullbuild`-Job-
  Step in bestehender Job-Definition ODER NEU Job-Block
  mit Image-Audit-Cache-Konfiguration. **Wenn Welle-1-D-1
  zu „Vertagen" entscheidet, bleibt diese Datei unangefasst
  und ein NEU `open/`-Trigger fuer Welle 3 wird in C3
  angelegt — siehe §4 C3 + §9 DoD.**
- `docs/plan/planning/in-progress/README.md` (C0 + C3) —
  Bestand-Tabelle + Aktive-Welle-Block.
- `docs/plan/planning/in-progress/M6-perf-security-cicd.md`
  (C0 + C3) — §3.1 Welle-Status-Tabelle Welle-1-Zeile.
- `docs/plan/planning/in-progress/roadmap.md` (C3) — §1
  Status-Header (`make fullbuild`-Defer-Notiz aufloesen)
  + §3 M6 aktive-Welle-Block.
- `docs/plan/planning/in-progress/carveouts.md` (C3) — §2.2
  Trigger-010-Eintrag auf `Aufgeloest in M6-Welle-1`.
- `docs/plan/planning/open/README.md` (C3) — Trigger-010-
  Zeile entfernt + Verweis auf done-Move-Hash.
- `docs/plan/planning/open/010-base-image-krb5-cve-bump.md`
  → `docs/plan/planning/done/010-base-image-krb5-cve-bump.md`
  (C3, `git mv` als Teil des C3-Commits).
- `README.md` + `README.de.md` (C3) — `make fullbuild`-
  `CVE-2026-40356`-Hinweis aufloesen.

**Welle-1-UNBERUEHRT (kein Edit):**

- Aller Code unter `src/` (krb5-Bump ist Build-Stack-
  Substanz, kein Code-Pfad-Wechsel).
- Alle Tests unter `tests/` (keine neuen Tests; Test-Counts
  bleiben 1722/80).
- ADRs 0001..0042 (ADR 0028-Link-Maintenance erfolgt
  separat falls noetig; Welle-1 fuegt nur ADR 0043 hinzu).
- Welle-Slice-Docs unter `done/` (eingefroren).
- M6-`Deferred`-Carveouts (`carveouts.md §2.1`) — bleiben
  unangefasst.

---

## 6. Verifikationspfad

**Welle-1-Gate:**

- `make docs-check` cache-frei gruen ueber alle 4 Welle-1-
  Commits.
- `make gates` cache-frei gruen (10/10 A-1-Gates) — Test-
  Counts unveraendert.
- **`make image-audit`** cache-frei gruen — Trivy-Report
  ohne HIGH-CVE-krb5-Famille (`CVE-2026-40356` + 3 weitere
  aufgeloest).
- **`make fullbuild`** cache-frei gruen ohne `CRITICAL_COV_
  TARGETS`-Override — Erbschafts-Loesung des M3-Welle-7-
  pre-existing-Drifts.

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur Doc-Substanz; DoD-Boxen
  pruefen Slice-Doc + Bestand-Tabelle + Slice-Plan-Welle-
  Zeile.
- C1 prueft ADR-0043-Substanz + Bezug-Refs.
- C2 prueft Dockerfile-Bump + 3 Gates cache-frei gruen.
- C3 prueft Status-Flip + ADR-0043-`Provisional`-Hash-
  Anchor-Eintrag (C2-Hash) + Trigger-010-Move + Top-Level-
  Doku-Sync. ADR-0043-`Accepted`-Pflicht-Pruefung
  passiert erst in M6-Welle-7-Closure-DoD.

**Abnahme-Verifikation:**

- Lastenheft-Coverage Welle 1: `GG-DEPLOY-001` (Container-
  basierte Bereitstellung mit Hardening) — Anteil
  „aktuelle Base-Image-CVE-Aufloesung" produktiv.
  `GG-DEPLOY-001`-Full-Erfuellung bleibt Welle-6-Scope
  (Image-Audit-CI-Gate + Container-Smoke).
- M6-Slice-Plan `§7 Verifikationspfad` Welle-1-Anteil
  („`make fullbuild` cache-frei gruen") produktiv.

---

## 7. Risiken

**R1 — krb5-Bump-Side-Effects (Library-Drift).** Base-Image-
Bump kann ungeplante Library-Drifts ausloesen (Debian-13-
Bibliotheks-Versionen). Risiko: bestehende Tests brechen
ueber Indirekt-Pfade (z. B. `cryptography`-Wheel-Stack mit
neuer OpenSSL-Variante).
**Mitigation:** C2 prueft `make gates` (10 A-1-Gates inkl.
Tests) cache-frei gruen vor Push; falls rot, ggf. Pinning
auf konkrete Debian-Punktversion oder explizites
`libkrb5-*`-apt-Hardening ohne Base-Image-Wechsel.

**R2 — Welle-1-D-1-CI-Gate-Editing-Komplexitaet.** Falls
das CI-Pflicht-Gate fuer `make fullbuild` doch in Welle 1
mitgezogen werden soll, kann GitHub-Actions-Editing groesser
werden als gedacht (Job-Konditional fuer `build`-Stage,
Trivy-Datenbank-Caching, Docker-Layer-Cache).
**Mitigation:** Welle-1-D-1 wird in C2 nach lokaler
`fullbuild`-Probe entschieden; Vertagungs-Pfad ueber NEU
`open/`-Trigger fuer Welle 3 ist als Default vorbereitet.

**R3 — ADR-0043-Pattern-Generalisierung.** ADR 0043 fixiert
das Trivy-Defer-Aufloesungs-Pattern. Risiko: spaetere
Welle-6-Deploy-Hardening-ADR koennte mit ADR 0043 in
Konflikt geraten (z. B. CRITICAL-Schwelle-Differenzierung).
**Mitigation:** ADR 0043 explizit auf Image-Audit-Pattern
beschraenken; Deploy-Hardening-Vollausbau (Welle 6) kann
ADR 0043 per ADR-0011-Schaerfungs-Pattern erweitern ohne
Supersedes.

**R4 — Trigger-010-Move-Aktualitaet.** Wenn zwischen C0
und C3 neue CVEs in Debian-13 entstehen, koennte Trigger
010-`done/`-Move den falschen Eindruck erwecken, dass die
Image-Audit-Pflege beendet ist.
**Mitigation:** ADR 0043 §3 verankert, dass `open/`-Trigger
die Defer-Lifecycle-Form ist — neue CVEs gehen als NEU
`open/`-Trigger ein, nicht als Re-Open von Trigger 010.
Trigger 010 ist konkret auf die M3-Welle-7-CVE-Famille
pinned.

**R5 — Doku-Sync-Vollstaendigkeit.** `README.md` +
`README.de.md` enthalten `make fullbuild`-`CVE-2026-40356`-
Hinweise auf User-Ebene; `roadmap.md §1` Status-Header hat
eine entsprechende Defer-Pfad-Notiz.
**Mitigation:** C3-Doku-Sync ist als expliziter Sub-Punkt
gefuehrt; `make docs-check` faengt fehlende Doku-Refs.

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack** (per
  [`../README.md`](../README.md) Wave-Self-Close-Commit-
  Konvention): sobald `M6-welle-1.md` Status `Done` erreicht
  (am Ende von C3), schliesst die Welle ihre eigene Commit-
  Sequenz mit einem reinen `git mv M6-welle-1.md
  → ../done/M6-welle-1.md` (C4a). Inhalts-Edits in einem
  unmittelbar nachfolgenden Cross-Doc-Refs-Sync-Commit
  (C4b). Pattern analog Welle-6c-C4a `c317200`/C4b
  `cfb9626` bzw. M6-Welle-0-C4a `76f892d`/C4b `960f6ed`.
- C4a/C4b dienen gleichzeitig als M6-Welle-2-Pre-C0a/
  Pre-C0b (Pattern analog M5-Welle-1→2 `c7c2641`/
  `a0c8ba3`).
- ADR 0043 (NEU in C1) bleibt unter `docs/plan/adr/` —
  ADR-Lifecycle wandert nicht mit dem Slice-Doc.
- Trigger 010 (`open/010-base-image-krb5-cve-bump.md`)
  wandert in C3 nach `done/` als Teil des Status-Sync-
  Commits.

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **C0 — NEU `M6-welle-1.md`** mit §1..§9-Struktur
  (dieser Commit).
- [x] **C0 — `in-progress/README.md`** Bestand-Tabelle um
  `M6-welle-1.md`-Eintrag ergaenzt + Aktive-Welle-Block
  bestaetigt.
- [x] **C0 — `M6-perf-security-cicd.md §3.1`** Welle-1-Zeile
  `Pending → In Progress` mit C0-Hash-Stub.
- [ ] **C1 — NEU `docs/plan/adr/0043-image-audit-strategy.md`**
  als `Provisional` mit Trigger-010-Hash-Anchor-Block +
  ADR-Standard-Struktur (§1..§4) + Bezug zu ADR 0028/0029.
- [ ] **C2 — `Dockerfile`** krb5-Bump (`FROM`-Update oder
  apt-Hardening-Block; entscheidet sich nach Trivy-Probe).
- [ ] **C2 — ggf. `uv.lock`** Refresh nach Library-Drift-
  Pruefung.
- [ ] **C2 — `make gates`** cache-frei gruen (10/10 A-1-
  Gates; Test-Counts unveraendert 1722/80).
- [ ] **C2 — `make image-audit`** cache-frei gruen (Trivy-
  Report ohne HIGH-CVE-krb5-Famille).
- [ ] **C2 — `make fullbuild`** cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override.
- [ ] **C2 — Welle-1-D-1 final entschieden** (Mitziehen vs.
  Vertagen). Wenn **Mitziehen**: NEU `.github/workflows/
  ci.yml`-Edit in C2 mitkommittet (Job-Step oder Block fuer
  `make fullbuild`; image-audit-Cache-Konfiguration falls
  noetig) **und** der CI-Workflow muss in einem realen
  GitHub-Actions-Lauf (auf einem Pre-Merge-Branch oder via
  `workflow_dispatch`) gegen den C2-Hash gruen sein, bevor
  C3 freigegeben wird (Sensor-Check, nicht nur Workflow-
  Datei-Anwesenheit). Wenn **Vertagen**: kein Edit an
  `.github/workflows/`, stattdessen NEU `open/`-Trigger in
  C3 angelegt.
- [ ] **C3 — ADR 0043** bleibt `Provisional`; C2-Hash als
  Trigger-010-Aufloesungs-Beleg in den ADR-Body als Hash-
  Anchor-Block nachgetragen. (`Accepted` passiert in M6-
  Welle-7-Closure-C1 gebuendelt mit ADR 0041/0042.)
- [ ] **C3 — `M6-welle-1.md`** Status `In Progress → Done`
  mit Liefer-Hash-Stack.
- [ ] **C3 — `M6-perf-security-cicd.md §3.1`** Welle-1-Zeile
  `In Progress → Done` mit Closure-Hash.
- [ ] **C3 — Trigger 010** `git mv open/010-* → done/010-*`
  + `carveouts.md §2.2` + `open/README.md` Sync.
- [ ] **C3 — `README.md` + `README.de.md`** `make
  fullbuild`-`CVE-2026-40356`-Hinweis aufgeloest.
- [ ] **C3 — `roadmap.md §1`** Status-Header-`make
  fullbuild`-Defer-Pfad-Notiz aufgeloest.
- [ ] **C3 — `roadmap.md §3 M6`** aktive-Welle-Block auf
  M6-Welle-2 ausgerichtet.
- [ ] **C3 — `make docs-check`** cache-frei gruen ueber
  alle 4 Welle-1-Commits.
- [ ] **C3 — Welle-1-D-1-Vertagungs-Pfad** (nur wenn C2-
  Entscheidung „Vertagen"): NEU `open/`-Trigger fuer M6-
  Welle-3 angelegt (CI-Pflicht-Gate fuer `make fullbuild`)
  mit `carveouts.md §2.X` Sync. (Wenn C2 „Mitziehen"
  entschieden hat, ist das C2-DoD-Item oben der Sensor-
  Check; hier dann „n/a" eintragen.)

**Anti-Scope-Verifikation (Welle 1 NICHT):**

- [ ] Kein CI/CD-Vollausbau (`GG-CICD-001..006` bleibt
  Welle-3-Scope).
- [ ] Kein SBOM-Hook (Welle-2-Scope; Trigger 008).
- [ ] Kein Performance-Bench (Welle-4-Scope; `GG-RT-005`).
- [ ] Kein Security-Audit (Welle-5-Scope; `GG-SAFE-*`).
- [ ] Kein IEC-Smoke-Pfad-B (Welle-6-Scope; Trigger 009).
- [ ] Keine Carveout-`Deferred`-Aufloesung opportunistisch
  (keine Welle-1-URL-Versionierung `/api/v1`; M6-D-3 bleibt
  Welle-3-Vorbelegung).

---

## References

- [`../done/M6-welle-0.md`](../done/M6-welle-0.md) — M6-
  Welle-0-Slice-Doc mit Welle-0-Decision-Liste (M6-D-1..7).
- [`M6-perf-security-cicd.md`](M6-perf-security-cicd.md) —
  M6-Slice-Plan §3.2 Welle-1-Vorbelegung + §5 Risiken
  (`krb5-Bump-Side-Effects` = R4).
- [`../open/010-base-image-krb5-cve-bump.md`](../open/010-base-image-krb5-cve-bump.md)
  — Trigger 010 mit konkreten CVE-IDs + Fix-Version
  (`CVE-2026-40356` + `krb5 1.21.3-5+deb13u1`).
- [`../done/M4-results.md §2 + §4 S-4 + §5`](../done/M4-results.md)
  — M4-Welle-7-Defer-Pfad-Origin + Erbschafts-Notiz nach
  M5/M6.
- [`../done/M3-results.md`](../done/M3-results.md) — M3-
  Welle-7-Closure-Stand `c61ab0d` als Drift-Origin-Hash.
- [`carveouts.md §2.2`](carveouts.md) — Trigger-Gated-
  Index mit Trigger-010-Aktivierungs-Status.
- [`../../adr/0028-link-maintenance-accepted-adr-bezug.md`](../../adr/0028-link-maintenance-accepted-adr-bezug.md)
  — Link-Maintenance-Pattern als ADR-0043-Vorbild.
- [`../../adr/0029-no-coverage-pragma-contract.md`](../../adr/0029-no-coverage-pragma-contract.md)
  — Gate-Vertrag-ADR-Pattern als ADR-0043-Vorbild
  (Quality-Gate-Contract analog Image-Audit-Contract).
- [`../../../../README.md`](../../../../README.md) +
  [`../../../../README.de.md`](../../../../README.de.md)
  — Top-Level-`make fullbuild`-Hinweis mit `CVE-2026-40356`-
  Erwaehnung (C3-Sync-Ziel).
- Pattern-Vorbild Welle-1-Substanz-Welle nach Welle-0-
  Plan-Welle: M5-Welle-1
  ([`../done/M5-welle-1.md`](../done/M5-welle-1.md)) +
  M4-Welle-1 ([`../done/M4-welle-1.md`](../done/M4-welle-1.md)).
