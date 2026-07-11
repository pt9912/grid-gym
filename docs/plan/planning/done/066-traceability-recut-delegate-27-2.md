# 066 — traceability.md Re-Cut: §27.2 an `make doc-trace` delegieren

**Status:** Done — 2026-07-11
**Datum:** 2026-07-11
**Quelle:** Folge aus dem d-check-`trace.coverage`-Arc (Commit `cf3234c`,
[`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-RTM jetzt 151 Reqs /
0 Waisen). §27.2 ist die drift-anfaellige Liefer-/Status-Matrix (Status-Spalte
driftete in Slice 056/060).

---

## Kontext / Befund

`traceability.md` §27 fuehrt drei Tabellen: §27.1 Anforderung→Design (`GG-AR-*`),
§27.2 Anforderung→Implementierung (Code-Pfade **+** `✓ M[N]`-Status), §27.3
Anforderung→Test. Die **§27.2-Status-Spalte** ist eine handgepflegte Drift-Quelle
(036/056/060 zogen stale Marker nach). Seit dem `trace.coverage`-Feature (d-check
v0.41.0) leitet `make doc-trace` die Liefer-Rueckverfolgung (Anforderung→Slice/
Welle/ADR + Abdeckungs-/Waisen-Status) **automatisch** aus den Artefakten ab —
kein Handpflege-Artefakt, kein Drift.

## C0 — ZENTRALE ENTSCHEIDUNG (Owner): C0 = A

§27.2 traegt zwei Dinge: die **Status-Spalte** (Drift-Quelle, von `doc-trace`
ersetzt) **und** ein kuratiertes **Code-Pfad-Mapping** (von `doc-trace` **nicht**
ersetzt). Entschieden: **A — §27.2 ganz entfernen.** Begruendung: das Code-Pfad-
Mapping ist ebenfalls handgepflegt/drift-anfaellig; der Liefer-/Impl-Nachweis kommt
aus `make doc-trace` (Slice/Welle/ADR/Trace) + den Slice-/Wellen-Docs + dem Code.
`traceability.md` behaelt die kuratierten, stabilen Mappings §27.1 (Design) + §27.3
(Test). Dies ist ein **[`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Amendment** (analog Slice 063).

## Tranchen

- **C1 — Amendment:** [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-
  Akzeptanz umformulieren: kuratierte Tabellen = Design (§27.1) + Test (§27.3); die
  Liefer-/Implementierungs-Rueckverfolgung wird via `make doc-trace` abgeleitet
  (nicht mehr handgepflegte §27.2-Tabelle inkl. `🔲`-Status).
- **C2 — §27.2 raus:** §27.2-Sektion aus `traceability.md` entfernen; Kopf-Intro
  („drei Tabellen" + Status-Marker-Legende) auf zwei kuratierte Tabellen + `doc-trace`
  umschreiben.
- **C3 — Link-/Prosa-Pflege:** stale `§27.2-Matrix-Zeile auf ✓`-Verweise in
  [`061`](../open/061-replay-time-multipliers.md)/[`062`](../open/062-run-deletion-operation.md)
  auf `make doc-trace` umstellen; historische Erwaehnungen (CHANGELOG, `done/053`)
  bleiben unberuehrt. Keine `#272`-Anker-Links im Repo (gepruft) → kein Link-Bruch.
- **C4 — Verifikation:** `make doc-trace` weiterhin **0 Waisen** (Coverage liest
  §27.1/§27.3, §27.2-Wegfall re-verwaist nichts — vorab gemessen); `make docs-check`
  + `make gates` gruen.
- **C5 — Closure:** Self-Move nach `done/`, Roadmap-Nachzug, CHANGELOG `[Unreleased]`.

## DoD

- [x] [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Akzeptanz amendiert (C0=A); §27.2 aus `traceability.md` entfernt;
      Kopf-Intro/Legende nachgezogen.
- [x] `make doc-trace` unveraendert **151 Reqs / 0 Waisen**; `docs-check` + `gates` gruen.
- [x] Stale §27.2-Prosa in `open/061`/`062` auf `doc-trace` umgestellt.
- [x] Doku-only → **kein Release** (CHANGELOG `[Unreleased]`).

## Betroffene Kennungen

[`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001) (Amendment),
`docs/plan/traceability.md` (§27.2 entfernt; §27.1/§27.3 behalten),
`.d-check.yml` (`trace.coverage` — unveraendert, liest §27.1/§27.3),
[`061`](../open/061-replay-time-multipliers.md)/[`062`](../open/062-run-deletion-operation.md)
(Prosa-Pflege). Bezug: [`063`](../done/063-traceability-doc-auslagern.md) (§27-Auslagerung).

## Risiken

- **Normatives Amendment** der Trace-Anforderung — Owner-Entscheidung C0=A.
- **Verlust des §27.2-Code-Pfad-Mappings** — bewusst akzeptiert (C0=A); Impl-Nachweis
  via `doc-trace` + Slice-/Wellen-Docs + Code.
- **Coverage-Regression** — ausgeschlossen: vorab gemessen (§27.2-Wegfall = weiterhin
  0 Waisen), in C4 re-verifiziert.

---

## Closure 2026-07-11

**C0 = A** (Owner): §27.2 ganz entfernt.

- **C1:** [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Akzeptanz
  amendiert — kuratierte Tabellen = Design (§27.1) + Test (§27.3); die Liefer-/
  Implementierungs-Rueckverfolgung (Slice/Welle/ADR + Abdeckungs-/Waisen-Status)
  wird via `make doc-trace` abgeleitet statt handgepflegt.
- **C2:** §27.2-Sektion aus `traceability.md` entfernt (123 Zeilen, 319 → 196);
  Kopf-Intro auf zwei kuratierte Tabellen + `doc-trace`-Verweis umgeschrieben,
  `✓`/`🔲`-Status-Legende raus.
- **C3:** stale `§27.2-Matrix-Zeile`-Prosa in [`061`](../open/061-replay-time-multipliers.md)/[`062`](../open/062-run-deletion-operation.md)
  auf `make doc-trace` umgestellt; historische Erwaehnungen (CHANGELOG, `done/053`)
  unberuehrt; keine `#272`-Anker-Links im Repo → kein Link-Bruch.
- **C4:** `make doc-trace` = **151 Reqs / 0 Waisen** (alle 151 Trace-covered aus
  §27.1/§27.3); `make docs-check` (0 Befunde) + `make gates` gruen.

**Evidence:** `doc-trace`/`docs-check`/`gates` gruen. Doku-only, **kein Release**
(CHANGELOG `[Unreleased]`).
