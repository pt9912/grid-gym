# Slice 053 — Planungsmodell: Slices statt Meilensteine

**Status:** Geplant — Slice-Plan zur Review (Umsetzung C0..C4 nach Freigabe).
**Datum:** 2026-07-01.
**Release-Entscheidung:** **nein** — reine Prozess-/Doku-Aenderung ohne
Runtime-Delta; Delta sammelt unter [`CHANGELOG.md`](../../../../CHANGELOG.md)
`[Unreleased]` (Regel „kein Doku-only-Release").
**Bezug:** [`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md)
(Planungsstruktur; wird geschaerft), [`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md)
(Schaerfung-ohne-Abloesung), [`roadmap.md`](roadmap.md),
[`carveouts.md`](carveouts.md), [`../README.md`](../README.md) (Lifecycle),
[`harness/conventions.md`](../../../../harness/conventions.md),
[`AGENTS.md`](../../../../AGENTS.md), [`done/M8-results.md`](../done/M8-results.md)
(letzte Meilenstein-Closure).

---

## 1. Context

Die Meilenstein-Ebene (`M1..M8`) war bisher die oberste Planungs-
Gruppierung ueber Wellen und Slices, normativ verankert in
[`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md)
(`M{N}`-Marker + Abnahmeschnitte). Mit **M8 abgeschlossen + v0.2.0 released**
ist die MUSS-Roadmap geliefert. Kuenftig soll **slice-getrieben** gearbeitet
werden (Wellen/Slices als oberste Einheit); die **Release-Entscheidung faellt
pro Slice**, nicht pro Meilenstein.

Der Verzeichnis-Lifecycle (`open → next → in-progress → done`) und die
Wellen/Slice-Mechanik bleiben unveraendert. Die Spec ist per SDP ohnehin
meilensteinfrei ([`AGENTS.md`](../../../../AGENTS.md) §2.5); nur die
historische [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Matrix
([`spec/lastenheft.md §27.2`](../../../../spec/lastenheft.md#gg-trace-001))
traegt `M{N}`-Statusmarker.

---

## 2. Scope

**In Scope:** Umstellung der **Planungsschicht** von milestone-first auf
slice-first + Formalisierung per neuer ADR (Schaerfung von
[`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md)).

**Anti-Scope (bewusst nicht):** Umschreiben der **Historie** — alle
`done/`/`done-archive/`-Closure-Docs (`M{N}-results.md`, `M{N}-welle-*.md`) und
die `M{N}`-Marker in `spec/lastenheft.md §27.2` bleiben eingefroren (sie sind
die Aufzeichnung dessen, was passiert ist). Kein Code, keine Spec-Straten-
Aenderung (ausser ggf. einer Praezisierung der §27.2-Legende — s. D-4).

---

## 3. Architektur-Entscheidungen

### D-1 — Meilenstein-Ebene als forward-Planungseinheit entfaellt

Neue Arbeit wird als **Slice** (ggf. in Wellen gruppiert) direkt ueber
`open → next → in-progress → done` gefuehrt, ohne Meilenstein-Container. Es
werden keine neuen `M{N}` eroeffnet; „aktiver Meilenstein"/„naechster
Meilenstein M9/M10" entfaellt als Konzept.

### D-2 — Naming: repo-weit fortlaufende Slice-Nummern

Neue Docs heissen `NNN-slug.md` (repo-weit eindeutige Nummer, Muster wie die
bestehenden Standalone-Slices `041`/`045`/`051`). Grosse Slices sub-slicen als
`NNN-a`/`NNN-b` (bestehende Wave-Sub-Slice-Mechanik). Das `M{N}-welle-*`-
Praefix wird fuer **neue** Docs retired; es bleibt nur in der Historie.

### D-3 — Release-Entscheidung pro Slice

Jeder Slice-Plan traegt ein DoD-Feld **„Release-Entscheidung: ja/nein
(+ SemVer-Ziel)"**:

- `nein` → Delta sammelt unter `CHANGELOG.md` `[Unreleased]`.
- `ja` → der Abschluss-Commit schneidet den Tag (`pyproject`-Bump +
  CHANGELOG-Finalisierung + `v*.*.*`-Tag → `release.yml`), unveraendert
  gebunden an **kein Doku-only-Release** (Runtime-Delta-Pflicht) +
  `make fullbuild` vor dem Tag.

### D-4 — Historie friert ein; `M{N}`-Marker bleiben

`done/`/`done-archive/`-Closure-Docs und die [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-§27.2-`M{N}`-Marker
werden **nicht** umgeschrieben (Aufzeichnung). Es werden keine neuen `M{N}`
vergeben; neue Anforderungs-Erfuellung wird per Slice/Release-Version
referenziert. Die §27.2-Legende bleibt; hoechstens eine minimale Praezisierung
„`M{N}` historisch, neue Arbeit slice-referenziert" (kein Marker-Rewrite).

### D-5 — Formalisierung als Schaerfung von ADR 0001

Die Umstellung wird als **neue ADR (Nummer 0072 reserviert)** dokumentiert —
Schaerfung-ohne-Abloesung von
[`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md) per
[`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md) (kein Supersede;
Directory-Lifecycle unveraendert). Status `Proposed` (C0) → `Accepted` (C4).

---

## 4. Liefer-Reihenfolge (C0..C4)

- **C0** `docs(plan)`: dieser Slice-Plan (053) + `in-progress/README.md`-
  Bestand-Zeile + die neue ADR (Nummer 0072, `Proposed`) +
  [`adr/README.md`](../../adr/README.md)-Index.
- **C1** `docs(plan)`: [`roadmap.md`](roadmap.md) slice-first-Umbau — §3
  (MVP-Abnahmescope) + §4 (Meilenstein-Detail M1..M8) → **kompakte
  „Gelieferte Historie"-Tabelle** mit Pointern auf die `M{N}-results.md`-Docs
  unter [`done/`](../done/) (Detail bleibt dort eingefroren); NEU Abschnitte
  „Aktive Slices" + „Release-Modell (pro Slice)"; §1-Notiz zu den `M{N}`-
  Markern praezisiert.
- **C2** `docs(harness/plan)`: [`harness/conventions.md`](../../../../harness/conventions.md)
  + [`AGENTS.md`](../../../../AGENTS.md) + [`../README.md`](../README.md) +
  [`carveouts.md`](carveouts.md) — Rahmung „Cross-Meilenstein"/„Welle-/
  Meilenstein-Closure"/`M{N}`-Praefix-Naming auf slice-first umstellen;
  Historie-Verweise bleiben.
- **C3** `docs`: [`../../../../README.md`](../../../../README.md) +
  [`README.de.md`](../../../../README.de.md) minimal reframen (M1..M8-Status-
  Tabelle bleibt als gelieferte Historie; Notiz „ab hier slice-getrieben,
  Release pro Slice") + `CHANGELOG.md` `[Unreleased]`-Notiz.
- **C4** `docs(plan)`: ADR (0072) → `Accepted`; dieser Slice-Plan per
  `git mv` → [`done/`](../done/) (rename-only) + DoD abgehakt.

Jeder Commit sofort nach `origin/main` (Auto-Push, kein History-Rewrite).

---

## 5. Critical Files

**NEU:** dieser Slice-Plan; die neue ADR (0072).
**MODIFY:** [`roadmap.md`](roadmap.md), [`carveouts.md`](carveouts.md),
[`../README.md`](../README.md),
[`harness/conventions.md`](../../../../harness/conventions.md),
[`AGENTS.md`](../../../../AGENTS.md),
[`../../../../README.md`](../../../../README.md),
[`README.de.md`](../../../../README.de.md),
[`CHANGELOG.md`](../../../../CHANGELOG.md),
[`adr/README.md`](../../adr/README.md).
**UNBERUEHRT (eingefroren):** [`done/`](../done/) + `done-archive/` (alle
`M{N}-results.md`/`M{N}-welle-*.md`), `spec/lastenheft.md §27.2`-Marker,
`spec/architecture.md`, aller Code.

---

## 6. Verifikationspfad

- `make docs-check` cache-frei gruen nach **jedem** Doc-Commit (faengt Link-
  Fan-out aus dem Roadmap-Umbau + ADR-Index-Drift).
- `make gates` cache-frei gruen am Closure-Stand (Doku-only — Test-Counts
  unveraendert; Handoff-Gate braucht `gates` + `docs-check`).
- Grep-Gegenprobe: keine forward-„aktiver Meilenstein"/„M9/M10"-Rahmung mehr in
  den **living** Planungsdocs (`in-progress/`, `harness/`, `AGENTS.md`,
  READMEs); Historie in `done/` unveraendert.
- Kein Tag/Release (D-3: Release-Entscheidung **nein**).

---

## 7. Risiken

- **R1 Roadmap-Link-Fan-out** — der Umbau kuerzt viel Milestone-Prosa; interne/
  eingehende Links muessen intakt bleiben. Mitigation: `make docs-check` nach
  C1; Pointer auf die `done/`-Results-Docs statt Loeschen.
- **R2 Konsistenz zu [`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md)**
  — die neue ADR (0072) ist Schaerfung, kein Supersede; der ADR-Body bleibt
  unveraendert, nur Bezug/Lineage-Link. Mitigation: `matrix`-Supersede-Lineage-
  Gate + explizite Schaerfungs-Formulierung.
- **R3 Naming-Luecke** — ohne `M{N}`-Praefix braucht neue Arbeit ein eindeutiges
  Schema. Mitigation: repo-weite `NNN-slug`-Nummern (bereits etabliert) in D-2
  fixiert.

---

## 8. Wandert nach

Nach C4 liegt dieser Slice-Plan in [`done/`](../done/); die neue ADR (0072) ist
`Accepted`. Aktive Arbeit danach: **keine** (Trigger-Watch, [`open/`](../open/)).
Ab hier ist das Planungsmodell slice-getrieben; das naechste Release ist eine
bewusste Pro-Slice-Entscheidung.

---

## 9. DoD-Checkliste (mit C4 abzuhaken)

- [ ] C0: Slice-Plan 053 + Bestand-Zeile + ADR (0072, `Proposed`) + ADR-Index.
- [ ] C1: [`roadmap.md`](roadmap.md) slice-first (Historie-Tabelle + Pointer);
      `make docs-check` gruen.
- [ ] C2: Konventionen ([`harness/conventions.md`](../../../../harness/conventions.md),
      [`AGENTS.md`](../../../../AGENTS.md), [`../README.md`](../README.md)) +
      [`carveouts.md`](carveouts.md) auf slice-first.
- [ ] C3: READMEs reframe + `CHANGELOG.md` `[Unreleased]`-Notiz.
- [ ] C4: ADR (0072) `Accepted`; Slice-Plan `git mv` → [`done/`](../done/).
- [ ] `make gates` + `make docs-check` cache-frei gruen am Closure-Stand.
- [ ] **Release-Entscheidung: nein** — kein Tag; Delta unter `[Unreleased]`.

---

## References

- [`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md) —
  Planungsstruktur (wird geschaerft).
- [`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md) — Schaerfung-ohne-
  Abloesung.
- [`done/M8-results.md`](../done/M8-results.md) — letzte Meilenstein-Closure.
- [`roadmap.md`](roadmap.md) + [`carveouts.md`](carveouts.md) +
  [`../README.md`](../README.md) — betroffene living Planungsdocs.
