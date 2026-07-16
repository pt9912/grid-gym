# 085 — Spezifikations-Schicht: QS-/Abnahme-Familien-Umzug (QA/QG/COV/TESTTYPE/ARCHTEST)

**Status:** **Abgeschlossen (`done/`, 2026-07-16).** Slice 3 des Migrations-Arcs
(Spec-Schichtung), **größter Cut** (30 IDs). [`ADR 0080`](../../adr/0080-three-layer-spec-model.md)
§2b/§4.2b — Umzug der QS-/Durchsetzungs-Familien in die Spezifikations-Schicht.
Baute auf [`083`](083-spezifikation-layer-discipline-core-move.md) + [`084`](084-architecture-bezug-drift-fix.md).
**Doku-/Config-only → kein Release.**
**Datum:** 2026-07-16

> **Closure / Verifikation (2026-07-16).** Atomarer rank-1-Cut: **30 IDs**
> (`GG-QA-*`/`GG-QG-*`/`GG-COV-*`/`GG-TESTTYPE-*`/`GG-ARCHTEST-*`) aus `lastenheft.md`
> §21.2–§21.5 (254 Zeilen) → `spezifikation.md` §5–§8 (Anforderungstext **verbatim** +
> Werkzeug-/Gate-Durchsetzung je Subsektion: `make test-*`/`coverage-gate`/`gates`/
> `arch-check`/`a-check`/`lint`/`dep-audit`). §21.1 (`GG-TEST-*`) + §22 (`GG-CICD-*`) +
> Abnahme-Anker `GG-ACCEPT-*`/`GG-MVP-*` **unberührt** im Vertrag. §27.1: die **5
> nicht-kontiguen** Zeilen (113/114 TESTTYPE/ARCHTEST + 121/122/123 COV/QG/QA) entfernt,
> die 6 dazwischen (CICD/DEPLOY/DEMO/ACCEPT/TRACE/TEST) bleiben. **53 Links** →
> spezifikation.md repointet (14 Dateien: ADRs + `done/` + `code-review.md` +
> architecture.md §17/§4.2). `.d-check.yml` `ids`-Alternation um QA/QG/COV/TESTTYPE/ARCHTEST
> erweitert + `trace`-Kommentar. **Differenzierung:** nur TESTTYPE/ARCHTEST hatten einen
> architecture.md-Aufwärts-Zeiger (§17/§4.2, jetzt auf spezifikation.md repointet); für
> QA/QG/COV entfiel die §27.1-Design-Zuordnung **ersatzlos** (architecture.md hat dort
> null Zeiger — verifiziert). Ein Vertrags-Rest
> ([`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Akzeptanz nannte
> `GG-TESTTYPE-*` abwärts) auf „Testtyp-Klassifikation" neutralisiert. **`make docs-check`
> + `make gates` grün;** gate-blinder Sweep: QS-Refs Klartext/Prefix bleibt → kein Bruch.

---

## Motivation

Nach dem harten Kern (083) die **QS-/Abnahme-Familien**: `GG-QA-*`, `GG-QG-*`,
`GG-COV-*`, `GG-TESTTYPE-*`, `GG-ARCHTEST-*` (30 IDs). Sie haben
Abnahmekriterium-**Charakter**, gehören aber auf die Ebene „*wie/womit wird
spezifiziert und geprüft*" (ADR §1). Owner-Entscheidung (ADR §4.2b): **ganz in die
Spezifikation, inkl. Schwellwert — kein per-ID-Split.** Ein Split klonte jeden ID
über zwei Schichten und reproduzierte exakt die Wurzel (jede Spec-Sache
gespalten → Drift).

## Betroffene Kennungen

- **Umzug:** `GG-QA-*` (001–006, §21.5), `GG-QG-*` (001–007, §21.4), `GG-COV-*`
  (001–005, §21.3), `GG-TESTTYPE-*` (001–007, §21.2), `GG-ARCHTEST-*` (001–005,
  §21.5) — 30 IDs.
- **Bleibt im Vertrag (nicht anfassen):** der Kunden-**Abnahme-Anker**
  `GG-ACCEPT-*` + `GG-MVP-*` (E2E-Referenzszenario + Abnahme-CLI, ADR §4.2b);
  `GG-TEST-*` (§21/§21.1) bleiben Vertrags-Testbarkeit — **nur** die Testarten-
  (`GG-TESTTYPE-*`), Coverage- (`GG-COV-*`), Gate- (`GG-QG-*`), QS- (`GG-QA-*`) und
  Architektur-Test- (`GG-ARCHTEST-*`) Familien ziehen um.

## Umfang / Erwartete Lieferung (atomarer Vertrag-Cut)

1. **Append** der fünf Familien an spezifikation.md (Definition **inkl.
   Schwellwerte**, z. B. [`GG-COV-001`](../../../../spec/spezifikation.md#gg-cov-001)
   90 %, [`GG-COV-002`](../../../../spec/spezifikation.md#gg-cov-002) 85 %; ihre
   Werkzeug-/Gate-Realisierung als spezifikationseigener Inhalt).
2. **Cut** von `lastenheft.md` §21.2–§21.5 (Z. ~1743–2000; `GG-TEST-*`-Sektionen
   §21/§21.1 **bleiben** stehen — sauber um sie herum schneiden).
3. **Repoint** der ~39 brechenden Markdown-Links (u. a.
   [`GG-QG-002`](../../../../spec/spezifikation.md#gg-qg-002)×9,
   [`GG-QG-005`](../../../../spec/spezifikation.md#gg-qg-005)×5,
   [`GG-ARCHTEST-001`](../../../../spec/spezifikation.md#gg-archtest-001)×5,
   [`GG-TESTTYPE-001`](../../../../spec/spezifikation.md#gg-testtype-001)×3,
   [`GG-COV-001`](../../../../spec/spezifikation.md#gg-cov-001)×3) auf
   spezifikation.md-Anker. Repoint-Fläche vollständig: `architecture.md`-Bezug —
   [`GG-AR-TEST-001`](../../../../spec/architecture.md#17-testarchitektur) §17
   realisiert TESTTYPE/ARCHTEST, **ARCHTEST-001 auch §4.2 (Z. 298)** → **aufwärts**
   auf die Spezifikations-IDs, SDP-konform; dazu `docs/user/code-review.md`,
   historische `done/`-Slices (Anker-Hygiene) und die ADR-Links (8 ADR-Dateien,
   [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §3, kein Inhalts-Edit).
4. **Gate-blinder Konfidenz-Sweep** (manuell): `src/`, `tests/`, `.github/`,
   `pyproject.toml`, `Makefile` — **~17** QS-Refs (
   [`GG-QG-002`](../../../../spec/spezifikation.md#gg-qg-002)×5,
   [`GG-QG-006`](../../../../spec/spezifikation.md#gg-qg-006)×3,
   [`GG-COV-001`](../../../../spec/spezifikation.md#gg-cov-001)×3,
   [`GG-COV-003`](../../../../spec/spezifikation.md#gg-cov-003)×2,
   [`GG-QA-005`](../../../../spec/spezifikation.md#gg-qa-005)×2,
   [`GG-QG-001`](../../../../spec/spezifikation.md#gg-qg-001)/[`GG-QG-005`](../../../../spec/spezifikation.md#gg-qg-005);
   **TESTTYPE/ARCHTEST haben null** gate-blinde Refs). Etwa gleicher Umfang wie
   083 (17/17), **nicht** der Löwenanteil. Wie 083: Prefixe bleiben (ADR §4.3) →
   Klartext-Refs brechen nicht → Konfidenz-/Kontext-Prüfung, keine Reparatur;
   docs-check prüft `src/**`/`.github/**` nicht.
5. **d-check-Config:** `ids`-Alternation (aus 083) um
   `QA|QG|COV|TESTTYPE|ARCHTEST` erweitern → Ziel spezifikation.md; den
   `trace`-Ausnahme-Kommentar (`.d-check.yml` Z. 103–107) für diese Familien von
   „via traceability.md" auf „via spezifikation.md" nachziehen (Regex unverändert).

## Design-Entscheidungen / Risiken

- **§27.1-Zeilen — nur die fünf nicht-kontiguen Zeilen** entfernen: **Z. 124
  (TESTTYPE), 125 (ARCHTEST), 132 (COV), 133 (QG), 134 (QA)** — **nicht** die
  Spanne „124–134"! Dazwischen liegen Z. 126–131 = CICD/DEPLOY/DEMO/**ACCEPT**/
  **TRACE**/TEST, die alle im Vertrag **bleiben** (eine Bereichs-Löschung zerstörte
  deren Traceability).
- **§27.1-Design-Beziehung — differenziert:** nur TESTTYPE/ARCHTEST haben heute
  einen architecture.md-Zeiger
  ([`GG-AR-TEST-001`](../../../../spec/architecture.md#17-testarchitektur) §17,
  ARCHTEST auch §4.2) → deren Beziehung bleibt als Aufwärts-Bezug. Für **QA/QG/COV
  existiert kein architecture.md-Zeiger** (verifiziert: null Treffer) → deren
  Design-Zuordnung **entfällt ersatzlos**; Realisierung wird selbst-enthalten in
  spezifikation.md dokumentiert (keine „rekonstruierbare" Traceability behaupten).
  §27.1-Modell final in 086.
- **§27.3 (Anforderung→Test):** keine Zeilen-Änderung (die Umzugs-Familien haben
  dort keine eigenen Zeilen-Schlüssel); aber die §27.3-Intro (`traceability.md`
  Z. 154 „Testtypen … `GG-TESTTYPE-*`") und die
  [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Zeile (Z. 210)
  nennen Umzugs-Familien im **Text** → Verweis-Text angleichen (kein Gate-Bruch,
  aber Doku-Drift).
- **Abnahme-Anker-Trennung:** genau prüfen, dass `GG-ACCEPT-*`/`GG-MVP-*` und
  `GG-TEST-*` im Vertrag bleiben — die Schnittkante läuft **zwischen** §21.1
  (bleibt) und §21.2 (zieht um).

## Verifikationspfad

- `make gates` + `make docs-check` grün.
- **Manueller Grep-Sweep** (Nachweis im Handoff): `grep -rnE
  'GG-(QA|QG|COV|TESTTYPE|ARCHTEST)-[0-9]{3}' src tests .github pyproject.toml Makefile`
  → jede Fundstelle auf existierenden Anker.
- `static-gates` vor Push; RUF003 beachten.

## DoD

- Fünf Familien **nur** in spezifikation.md; aus `lastenheft.md` entfernt;
  `GG-ACCEPT-*`/`GG-MVP-*`/`GG-TEST-*` unberührt im Vertrag.
- Alle Links + gate-blinden Refs repointet; docs-check grün + Sweep sauber.
- **Release-Entscheidung: nein.** Doku/Config + Kommentar-Deltas → `[Unreleased]`.

## Wandert nach

- `in-progress/` bei Aktivierung, dann `done/`.

## Bezug

- [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §2b/§4.2b.
- Vorgänger [`083`](083-spezifikation-layer-discipline-core-move.md)/[`084`](084-architecture-bezug-drift-fix.md),
  Nachfolger [`086`](086-traceability-derived-27-1-finalization.md).
- [`spec/lastenheft.md`](../../../../spec/lastenheft.md) §21.2–§21.5,
  [`spec/architecture.md`](../../../../spec/architecture.md) §17,
  [`docs/plan/traceability.md`](../../traceability.md) §27.1.
