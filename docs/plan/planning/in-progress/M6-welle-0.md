# Welle 0 — M6 Slice-Plan-Eroeffnung + Trigger-Triage

**Status:** In Progress — eroeffnet 2026-06-04 mit C0
(dieser Commit). Vorabraeumung + Slice-Plan-Eroeffnung fuer
M6 (Performance + Security + CI/CD-Haertung — `GG-RT-001..005`
+ `GG-SAFE-001..008` + `GG-CICD-001..007` +
`GG-DEPLOY-001..00X`; SBOM ueber `GG-CICD-007` +
[`Trigger 008`](../open/008-sbom-activation.md), keine eigene
`GG-SBOM-*`-Familie). Pattern analog M5-Welle-0
([`../done/M5-welle-0.md`](../done/M5-welle-0.md)) und
M4-Welle-0 ([`../done/M4-welle-0.md`](../done/M4-welle-0.md)).

**Pre-C0 — bereits erledigt** (M5-Closure-Stack):

- M5-Welle-7-Closure-Stack `c28a11b` → `015eada` (C0..C4b
  inkl. C2-Review-Folge).
- M5-Closure-Konsistenz-Audit `dde9c7c` (Bestand-Bereinigung
  + Roadmap-M5→M6-Flip).
- NEU [`../in-progress/carveouts.md`](carveouts.md) `fa032b1`
  + `40ce6ce` (Cross-Meilenstein-Carveout-Index mit
  4-Klassen-Typologie).

Welle 0 startet damit direkt mit C0 — der M5-Closure-Stack
+ Carveouts-Index ist der effektive Pre-C0.

**Spec-Reife:** Inhaltlich final. Reines Doc-Arbeitspaket
(kein Code-Pfad-Wechsel; Pattern analog `M4-Welle-0` /
`M5-Welle-0`). Welle-0-Decision-Liste (§3) sammelt offene
Fragen, entscheidet sie aber nicht — Entscheidungen wandern
in M6-Welle 1+ und werden im jeweiligen M6-ADR
konkretisiert.

**Bereits vor M6-Welle-0 angelegt:** keine M6-Sondierungs-
ADR (M5-Welle-0-Vorbild ADR 0036 war Spezial-Fall fuer
UI-Stack-Wahl mit pre-existing Maintainer-Decision-
Indication; M6-Performance/Security/CI/CD haben keine
analoge Pre-Sondierung).

---

## 1. Context

M5 ist seit 2026-06-04 mit Welle-7-Closure abgeschlossen
([`../done/M5-results.md`](../done/M5-results.md)). M6 ist
laut [`roadmap.md §3 M6`](roadmap.md) der naechste aktive
Slice mit **fuenf Sub-Bereichen** entlang
[`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md):

| Sub-Bereich | Lastenheft-IDs | Beleg-Familie |
| ----------- | -------------- | ------------- |
| **Performance** | `GG-RT-001..005` | 10 000-Points/s-Benchmark + Tick-Drift-Schranken |
| **Security** | `GG-SAFE-001..008` | Sicherheits-Audit + externe Eingabevalidierung (`GG-SAFE-008` REST/WS/Adapter-Inputs) + IP-/Netz-Beschraenkung im Demo-Compose |
| **CI/CD-Vollausbau** | `GG-CICD-001..007` | GitHub-Actions-Matrix Python 3.13+3.14, Tests/Coverage/Dep-Audit als CI-Jobs, Release-Workflow inkl. SBOM (`GG-CICD-007`) |
| **Deploy-Hardening** | `GG-DEPLOY-001..00X` | Image-Audit + Container-Smoke + krb5-CVE-Bump (M4-Erbschaft) |
| **SBOM-Pfad** | via `GG-CICD-007` + Trigger 008 | `make sbom` scharfschalten + Release-Workflow-Hook. **Keine eigene `GG-SBOM-*`-Lastenheft-Familie** — SBOM ist via CI-Pflicht-Gate-Familie verankert. |

### 1.1 Carveout-Eingangsbestand

Per [`carveouts.md`](carveouts.md) Stand 2026-06-04: **31
Carveouts** im Cross-M-Index — davon **strict M6-Bezug
(M5-Erbschaft + selbst-aktivierbare Trigger): 10**:

| Carveout-Typ | Anzahl im Index | M6-Relevanz |
| ------------ | --------------- | ----------- |
| `Deferred` (M5-Erbschaft, §2.1) | 6 | **alle 6** sind M6-Pflicht-Substanz — Welle-Zuordnung in §3 Decision M6-D-3 |
| `Pattern-Forward` (M5-Erbschaft, §2.1) | 1 | **opportunistisch** in M6-Welle-X-Hardening-Sweep (Welle-3-Pre-init-Defense); kein eigener Lieferpunkt — Lifecycle-Konvention unterscheidet sich von `Deferred` |
| `Trigger-Gated` (§2.2..§2.6) | 18 | **3 sind selbst-aktivierbar** in M6 (Trigger 008 SBOM, Trigger 009 IEC-Smoke-Pfad-B, Trigger 010 krb5); **15 warten weiter** auf externen Trigger (5 Tooling + 9 SOLLTE-Geraete + 1 RL-Adapter — siehe `carveouts.md §2.3..§2.6` Aktivierungs-Bedingungen) |
| `Out-of-Scope` (permanent, §2.7) | 6 | **0** — bleiben permanent im Index; kein M6-Lieferpunkt |

Welle-0-C2-Trigger-Triage entscheidet pro Item: aktiv in
M6-Welle-X / bleibt Trigger-Gated / Out-of-Scope-Move.

### 1.2 Existierende Substanz im Repo

M5-Welle-7-Closure-Stand (siehe
[`../done/M5-results.md §2`](../done/M5-results.md)):

- **1722 Unit-Tests + 80 Integration + 4 skipped**
  (IEC-61850-2c-Mock-only-Fallback).
- **10/10 A-1-Gates** gruen cache-frei ohne Override:
  lint / format-check / typecheck (mypy --strict) /
  arch-check (20 Contracts) / test-unit / coverage-gate
  (90 % line / 85 % branch) / coverage-gate-critical /
  dep-audit / noqa-gate / spdx-check.
- **`make fullbuild`** pre-existing rot seit M3-Welle-7-
  `c61ab0d` wegen krb5-CVE-Drift (4 HIGH-CVEs in
  Debian-13-Base; nicht durch Code verursacht). Trigger 010
  in [`../open/`](../open/010-base-image-krb5-cve-bump.md).
- **Vier CI-Pflicht-Gates** in GitHub Actions (Slice 025):
  lint, format-check, typecheck, arch-check. Test-unit +
  coverage + dep-audit sind **lokal in `make gates`**, aber
  nicht GitHub-seitig enforced — Slice 025 §2 hatte das
  bewusst auf M6 verschoben.
- **`make sbom`-Target** existiert, aber Trigger 008 (SBOM-
  Aktivierung) wartet auf erste Artefakt-Veroeffentlichung.

### 1.3 M6-Spec-Lage

**Lastenheft-Hauptpflichten** ([`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md)):

- `GG-RT-001..005` (5 IDs): Echtzeit-/Performance-Schranken;
  `GG-RT-005` ist die 10 000-Points/s-Benchmark-Pflicht.
- `GG-SAFE-001..008` (8 IDs): Sicherheits-Audit-Familie.
  `GG-SAFE-008` ist **externe Eingabevalidierung an REST/
  WebSocket/Adapter-Schnittstellen** (Lastenheft-Original-
  Text: „Die Plattform MUSS Eingaben an externen
  Schnittstellen validieren"). IP-/Netz-Beschraenkung im
  Demo-Compose ist eine **separate Auflagen-Schicht** (kein
  einzelner `GG-SAFE-*`-ID); ADR/Welle-X-Decision verlinkt
  die Compose-Konfiguration mit der entsprechenden
  Lastenheft-ID.
- `GG-CICD-001..007` (7 IDs): CI-Pflicht-Gate-Familie inkl.
  `GG-CICD-002` (Tests in CI), `GG-CICD-003` (Coverage in
  CI), `GG-CICD-006` (Dep-Audit in CI), **`GG-CICD-007`
  (Release-Workflow mit SBOM-Hook)** — SBOM-Generierung ist
  im Release-Workflow verankert, **keine eigene
  `GG-SBOM-*`-ID-Familie** im Lastenheft.
- `GG-DEPLOY-001..00X` (≥X IDs): Container-Hardening +
  Image-Audit + Healthcheck-Pollung.

**Architektur-Erbschaft aus M5:** ADR 0037 (HTTP-API-
Surface) + ADR 0038 (TelemetryStreamPort) + ADR 0039
(Run-Control + Status) + ADR 0040 (Alarm-Aggregation) sind
alle auf `Accepted` — kein neuer Decision-Druck auf der
Driving-Side. M6 ergaenzt **Performance- + Sicherheits-
Querschnitt** ueber den bestehenden Stack.

---

## 2. Scope

Welle 0 liefert **drei Closure-Items** ueber 3 Commits
(Pattern analog M5-Welle-0):

1. **C0 — NEU `M6-welle-0.md` Slice-Doc** (dieser Commit)
   mit §1..§9-Struktur, Welle-0-Decision-Liste (§3),
   DoD-Checkliste (§9).

2. **C1 — NEU `M6-perf-security-cicd.md`** als
   kanonischer M6-Slice-Plan. Inhalt analog
   `M5-ui-demo.md`:
   - §1 Zweck + Architektur-Familie + Sub-Slicing-
     Schwelle.
   - §2 Erfolgskriterien (MUSS-IDs / SOLLTE-IDs / DoD-
     Gates).
   - §3 Liefer-Reihenfolge (Welle 0..7) mit `§3.1 Welle-
     Status-Tabelle` (initial Welle 0 = `In Progress`,
     Rest `Pending`) + `§3.2 Pending-Wellen-Plan-Items`
     (Welle 1+ Vorbelegung).
   - §4 Out-of-Scope (bleibt fuer M7+; aktuell keine M7
     vorgesehen, also „bleibt offen oder wandert in
     `done/M6-results.md §8`").
   - §5 Risiken + Fallback.
   - §6 Wandert nach (M6-Welle-7-Closure).
   - §7 Verifikationspfad.

3. **C2 — Trigger-Triage + Status-Flip:** pro Carveout in
   [`carveouts.md`](carveouts.md) entscheiden, ob aktiv in
   M6-Welle-X / `Trigger-Gated` bleibt / Out-of-Scope-Move
   (siehe Decision M6-D-2 unten). Plus `roadmap.md §3 M6`
   Status `Vorbelegung → In Progress`. Plus
   `in-progress/README.md` Aktive-Welle-Block auf
   M6-Welle-1 ausrichten.

---

## 3. Architektur-Entscheidungen (Welle-0-Decision-Liste)

Welle-0-Decisions sind **offen** — sie sammeln Fragen, die
in Welle 1+ entschieden werden. Konkrete Decisions wandern
ins jeweilige M6-ADR (per ADR-0011-Schaerfungs-ohne-
Supersede-Pattern, analog M5-ADRs 0036..0040).

### M6-D-1 — Sub-Slicing-Strategie

**Frage:** Wie wird M6 in Wellen geschnitten?

Optionen:

- **Option A — Pro Lastenheft-Familie:** Welle 1
  Performance (`GG-RT-*`), Welle 2 Security (`GG-SAFE-*`),
  Welle 3 CI/CD-Vollausbau (`GG-CICD-*`), Welle 4 Deploy +
  SBOM (`GG-DEPLOY-*` + `GG-SBOM-*`), Welle 5+ Closure.
- **Option B — Pro Triggerebene:** Welle 1 krb5-Bump
  (Trigger 010, klein), Welle 2 SBOM (Trigger 008,
  klein), Welle 3 CI-Vollausbau (gross), Welle 4
  Performance-Benchmark, Welle 5 Security-Audit, Welle 6+
  Closure.
- **Option C — Hybrid:** Welle 1 Sammel-Foundation
  (krb5-Bump + SBOM + CI-Erweiterungen klein), Welle 2
  Performance, Welle 3 Security, Welle 4 Closure.

Vorbelegung: **Option B** scheint passend, weil krb5-Bump
+ SBOM beide eigenstaendige Slices sind und nicht auf
Performance/Security warten muessen. Welle-1-C0 entscheidet
final.

### M6-D-2 — Carveout-Triage (Trigger-Gated → Aktive Welle)

**Frage:** Welche `Trigger-Gated`-Carveouts werden in M6
aktiv geliefert, welche bleiben offen?

Per [`carveouts.md`](carveouts.md) gibt es 18 `Trigger-
Gated`-Items. Triage-Vorbelegung (C2-Substanz):

| Trigger | Empfehlung | Begruendung |
| ------- | ---------- | ----------- |
| **Trigger 008 SBOM** | **Aktivieren in M6-Welle-X** | `GG-SBOM-*` ist M6-Pflicht; Release-Workflow blockiert sonst. |
| **Trigger 009 IEC-Smoke Pfad-B** | **Aktivieren in M6-Welle-X** (separater Slice) | Multi-Python-Test-Stage ist Repo-Novum; loest M4-Erbschaft auf. |
| **Trigger 010 krb5-Bump** | **Aktivieren in M6-Welle-1** | `make fullbuild` ist seit M3-Welle-7 rot; CI-Pflicht-Gate-Vorbedingung. |
| Trigger 004 canonical-encoder | Bleibt `Trigger-Gated` | Kein gemessener Perf-Druck (`GG-RT-005`-Benchmark muss zuerst laufen). |
| Trigger 005 pyright-vs-mypy | Bleibt `Trigger-Gated` | Keine Generic-Protocols heute. |
| Trigger 007 pyright-precommit | Bleibt `Trigger-Gated` | Kein Editor-Parity-Druck. |
| Trigger 011 mlrandomport-subseed | Bleibt `Trigger-Gated` | Sub-Port-Schwelle unerreicht. |
| Trigger 030 RL-Adapter | Bleibt `Trigger-Gated` | Kein Forschungs-Bedarf signalisiert. |
| Trigger 016..024 (SOLLTE-Geraete) | Bleiben `Trigger-Gated` | „bei konkretem Bedarf" — kein Bedarf in M6. |
| Trigger 026 BESS-Reserve-Market | Bleibt `Trigger-Gated` | Optionaler Spike; kein Reserve-Market-Agent in M6. |

Welle-1-C0 + C2 entscheiden final pro Trigger.

### M6-D-3 — `Deferred`-Welle-Zuordnung (M5-Erbschaft)

**Frage:** Wie werden die 7 M5-Erbschafts-`Deferred`-Items
auf M6-Wellen verteilt?

Vorbelegung:

- **Snapshot-Envelope-v2-Body** → M6-Welle-X (Replay-
  Surface-Welle ggf. eigene Welle).
- **CSV/JSONL-Export** → M6-Welle-X oder M7+ falls keine
  konkrete Use-Case-Welle.
- **Inline-SVG-Geraete-Grafik** → M6-Welle-X (UI-Polish)
  ODER M7+ (kein Lastenheft-MUSS, bereits `GG-UI-006`
  per Tabelle erfuellt).
- **Dynamische Fault-Activation** → M6-Welle-X (Fault-
  Pipeline-Erweiterung).
- **URL-Versionierung `/api/v1`** → M6-Welle-1 (proaktiv,
  vor naechster Kollision) ODER M6-Welle-X.
- **WS `/devices`** → M6-Welle-X (UI-Live-Updates) ODER
  M7+.
- **Pre-init-Defense-Pattern verallgemeinern** →
  opportunistisch in M6-Welle-X-Hardening-Sweep.

Welle-1-C0 entscheidet pro Item.

### M6-D-4 — ADR-Anzahl-Vorbelegung

**Frage:** Wie viele M6-ADRs erwartet?

Vorbelegung: **1-3 ADRs** typisch fuer M-Closure (analog
M3=6, M4=6, M5=5 — M5 war Ausreisser-hoch wegen vieler
unabhaengiger Driving-Concerns). M6-typische Decisions:

- ADR 0041 (provisional) — Performance-Benchmark-Pattern
  (Bench-Framework + Tick-Drift-Methodologie); Welle-X-C1.
- ADR 0042 (provisional) — SBOM-Tool-Wahl + CI-Hook;
  Welle-X-C1.
- Ggf. ADR 0043 — Image-Audit-Pflicht-Strategie + krb5-
  CVE-Defer-Pfad-Aufloesung; Welle-X-C1.

S-1..S-6-Sweep-S-5 bei M6-Welle-7-Closure pinned die
finale ADR-Anzahl.

### M6-D-5 — `make fullbuild`-Drift-Aufloesung

**Frage:** Wird `make fullbuild` in M6 cache-frei gruen?

Vorbelegung: **Ja**, durch Trigger 010 krb5-Bump in
Welle 1. Welle-7-S-3-Sweep verifiziert.

### M6-D-6 — Python-3.13/3.14-Test-Matrix

**Frage:** Wird GitHub-Actions auf eine Test-Matrix mit
beiden Python-Versionen erweitert (Spike-0-Closure-D-8 +
ADR 0002 §6.1)?

Vorbelegung: **Ja**, in M6-Welle-3 (CI-Vollausbau).
Aktuell CI laeuft nur 3.14; ADR 0002 §6.1 verlangt
Matrix.

### M6-D-7 — Bench-Framework

**Frage:** Welches Bench-Framework fuer `GG-RT-005` 10k-
Points/s-Benchmark?

Optionen:

- pytest-benchmark (existierend, leichtgewichtig)
- pyperf (Python-Standard, robuster fuer Mikro-Bench)
- asv (komplettes Bench-Suite-Tool)

Vorbelegung: **pytest-benchmark** (existiert bereits,
keine neue Dep, schneller Einstieg). Welle-Performance-C1
ADR entscheidet final.

### Trigger-Drift-Notiz (zur Aufnahme in C2)

Bei Welle-0-C2-Triage werden die folgenden Items in den
Carveout-Index aufgenommen oder umklassifiziert:

- Trigger 008 SBOM: `Trigger-Gated` → `Active in
  M6-Welle-X`.
- Trigger 009 IEC-Smoke: `Trigger-Gated` → `Active in
  M6-Welle-X` (separater Slice).
- Trigger 010 krb5-Bump: `Trigger-Gated` → `Active in
  M6-Welle-1`.

`carveouts.md` wird in C2 entsprechend gepatched (siehe
M6-D-2 Tabelle).

---

## 4. Liefer-Reihenfolge (3 Commits)

### C0 — `docs(plan)`: M6-welle-0 Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU [`M6-welle-0.md`](M6-welle-0.md) mit §1..§9-
  Struktur.
- Welle-0-Decision-Liste (7 Decisions, alle offen).
- DoD-Checkliste (initial leer; C2 hakt ab).
- `in-progress/README.md` Bestand-Tabelle um
  Welle-0-Zeile ergaenzt (in C0; analog M5-Welle-0-
  Pattern).

### C1 — `docs(plan)`: NEU `M6-perf-security-cicd.md`

**M6-Slice-Plan-Eroeffnung.** NEU
`M6-perf-security-cicd.md` als
kanonischer M6-Slice-Plan analog `M5-ui-demo.md`:

- §1 Zweck + Architektur-Familie.
- §2 Erfolgskriterien.
- §3 Liefer-Reihenfolge (Welle 0..7 oder anders je
  M6-D-1).
- §4 Out-of-Scope.
- §5 Risiken.
- §6 Wandert nach.
- §7 Verifikationspfad.

Plus `in-progress/README.md` Bestand-Tabelle um den
Slice-Plan-Eintrag.

### C2 — `docs(plan)`: Trigger-Triage + Status-Flip

**Welle-0-Closure-Sync.**

- **Carveout-Triage** per M6-D-2: Trigger 008/009/010 +
  ggf. weitere markieren als `Active in M6-Welle-X`;
  `carveouts.md` Index entsprechend updaten.
- **`roadmap.md §3 M6`** Status `Vorbelegung → In
  Progress` (analog M5-Welle-0-C2 Decision 10);
  Welle-Status-Tabelle in M6-Slice-Plan-§3.1
  initialisieren.
- **`in-progress/README.md`** Aktive-Welle-Block auf
  M6-Welle-1 ausrichten.
- DoD-Checkliste (§9) abhaken.

---

## 5. Critical Files

**Welle-0-NEU (geschrieben in C0/C1/C2):**

- `docs/plan/planning/in-progress/M6-welle-0.md` (C0,
  dieser Commit).
- `docs/plan/planning/in-progress/M6-perf-security-cicd.md`
  (C1).

**Welle-0-MODIFY (in C0/C2):**

- `docs/plan/planning/in-progress/README.md` — Bestand-
  Tabelle + Aktive-Welle-Block (C0 + C2).
- `docs/plan/planning/in-progress/roadmap.md` — §3 M6
  Status-Flip (C2).
- `docs/plan/planning/in-progress/carveouts.md` — Trigger-
  Triage-Updates (C2).

**Welle-0-UNBERUEHRT (kein Edit):**

- Aller Code (`src/`).
- Alle Tests (`tests/`).
- Welle-Slice-Docs unter `done/` (eingefroren).
- ADRs (`docs/plan/adr/`).
- `README.md` + `README.de.md` (M6-Status-Sync ist
  Welle-7-Closure-Material; Welle 0 ist Slice-Plan-
  intern).

---

## 6. Verifikationspfad

**Welle-0-Gate:**

- `make docs-check` cache-frei gruen ueber alle 3
  Welle-0-Commits.
- `make gates` unveraendert gruen (keine Code-
  Aenderungen; Test-Counts bleiben 1722/80).

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur den Slice-Doc; DoD-
  Boxen pruefen nur Doc-Substanz.
- C1 + C2 verifizieren die jeweiligen DoD-Items pro
  Lieferung.

**Abnahme-Verifikation:**

- M6 wird **nicht** in M6-Welle-0 abgenommen; Welle 0
  ist Plan-Welle. Abnahme erfolgt pro Sub-Welle und
  final in M6-Welle-7-Closure (`M6-results.md`).

---

## 7. Risiken

**R1 — M6-Scope-Drift.** M6 hat 5 Sub-Bereiche (Perf /
Security / CI/CD / Deploy / SBOM). Risiko: Scope-Creep
ueber Welle-X-Zaehlung hinaus.
**Mitigation:** Sub-Slicing-Schwelle (analog M4/M5: > 300
Zeilen Slice-Doc ODER > 5 Code-Commits ODER > 2
unabhaengige Sub-Bereiche) wird streng eingehalten;
Welle-X-C0-Sub-Slicing-Beschluss pro Welle.

**R2 — Carveout-Triage-Konflikt.** M6-D-2-Vorbelegung
markiert 3 Trigger als `Active in M6-Welle-X`. Risiko:
einige der 15 anderen `Trigger-Gated`-Items koennten
unerwartet aktiviert werden.
**Mitigation:** C2-Trigger-Triage-Tabelle in `carveouts.md`
ist der Single-Source; Welle-X-C0-Sub-Slicing-Beschluss
re-evaluiert pro Welle.

**R3 — `make fullbuild`-krb5-CVE-Pfad bleibt rot.** Wenn
Trigger 010-Bump in Welle 1 sich verzoegert, bleibt der
Defer-Pfad bestehen.
**Mitigation:** Welle 1 ist als erste Code-Welle nach
Welle 0 vorbelegt (M6-D-1 Option B); krb5-Bump ist klein
und gut isoliert.

**R4 — Performance-Benchmark-Methodologie unklar.** 10k-
Points/s ist eine Lastenheft-Schranke ohne dokumentierte
Mess-Methodologie.
**Mitigation:** M6-D-7-Decision-Vorbelegung (pytest-
benchmark) + Welle-Performance-C1 ADR fixiert
Methodologie; ggf. Pre-C0c-Smoke-Probe.

**R5 — CI-Erweiterungen erfordern GitHub-Actions-Editing.**
4 neue CI-Jobs (Tests/Coverage/Dep-Audit/Release) brauchen
`.github/workflows/`-Edits, die Slice-025-Konfiguration
beruehren.
**Mitigation:** Welle-CI/CD-Vollausbau-C2 macht alle 4
Jobs in einem Commit (analog Slice 025).

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack** (per
  [`../README.md`](../README.md) Wave-Self-Close-Commit-
  Konvention): sobald `M6-welle-0.md` Status `Done` erreicht
  (am Ende von C2), schliesst die Welle ihre eigene Commit-
  Sequenz mit einem reinen `git mv M6-welle-0.md
  → ../done/M6-welle-0.md` (Inhalts-Edits in einem
  unmittelbar nachfolgenden Cross-Doc-Refs-Sync-Commit).
  Pattern analog Welle-6c-C4a `c317200`/Welle-6b-C4a
  `b30280e` — **NICHT** das alte M5-Welle-0-Muster
  (`fd642df` als Pre-C0a der Welle 1), das vor der
  Konventions-Schaerfung galt.
- `M6-perf-security-cicd.md` (C1-Lieferung) bleibt in
  `in-progress/` bis M6-Welle-7-Closure (analog
  `M5-ui-demo.md` in M5-Welle-7-C4a).

---

## 9. DoD-Checkliste (mit C2 abzuhaken)

- [x] **C0 — NEU `M6-welle-0.md`** mit §1..§9-Struktur
  (dieser Commit).
- [ ] **C1 — NEU `M6-perf-security-cicd.md`** als M6-
  Slice-Plan.
- [ ] **C2 — Carveout-Triage**: Trigger 008/009/010 (und
  ggf. weitere) als `Active in M6-Welle-X` markiert in
  `carveouts.md`.
- [ ] **C2 — `roadmap.md §3 M6`** Status `Vorbelegung →
  In Progress`.
- [ ] **C2 — `in-progress/README.md`** Aktive-Welle-Block
  auf M6-Welle-1 ausgerichtet.
- [ ] **C2 — `in-progress/README.md`** Bestand-Tabelle
  hat `M6-welle-0.md` + `M6-perf-security-cicd.md`
  Eintraege.
- [ ] **`make docs-check`** cache-frei gruen ueber alle 3
  Welle-0-Commits.
- [ ] **`make gates`** unveraendert gruen (Test-Counts
  bleiben 1722/80; reine Doku-Welle).

**Anti-Scope-Verifikation (Welle 0 NICHT):**

- [ ] Kein Code-Diff.
- [ ] Keine neuen Tests.
- [ ] Keine neuen ADRs (Sondierungs-ADRs wie ADR 0036
  bei M5 sind in M6 nicht erwartet).
- [ ] Keine Welle-1+-Decisions final entschieden (Welle-
  0-Decision-Liste sammelt nur).

---

## References

- [`../done/M5-results.md`](../done/M5-results.md) —
  M5-Closure-Artefakt + §5 Welle-7-Erbschaft fuer M6+.
- [`../done/M5-welle-0.md`](../done/M5-welle-0.md) +
  [`../done/M4-welle-0.md`](../done/M4-welle-0.md) —
  Welle-0-Vorbild-Slice-Docs.
- [`carveouts.md`](carveouts.md) — Cross-M-Carveout-
  Index (31 Eintraege; M6-Welle-0-C2-Triage ist die
  primaere Pflege-Welle).
- [`roadmap.md §3 M6`](roadmap.md) — M6-Vorbelegung mit
  Lieferziel + Lastenheft-IDs + DoD-Checkboxen.
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md)
  §22 (`GG-RT-*`) + §23 (`GG-SAFE-*`) +
  CI/CD-Kapitel (`GG-CICD-*` + `GG-DEPLOY-*` +
  `GG-SBOM-*`).
- Pattern-Vorbild **Welle-ohne-C1-ADR**:
  M5-Welle-0 (Welle-0 ist Doc-only; M6-ADR-Sondierungen
  kommen erst pro Sub-Welle).
- [`../open/`](../open/) Bestand-Tabelle — 18 aktive
  Trigger-Watch-Eintraege; C2-Trigger-Triage pflegt sie.
