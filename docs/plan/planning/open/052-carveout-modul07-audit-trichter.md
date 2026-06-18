# 052 — Carveout-Disziplin: Audit-Slice pro Welle + Werkzeug-Wahl-Trichter (v1.2.0)

**Status:** Open
**Datum:** 2026-06-18
**Quelle:** v1.2.0-Regelwerk-Delta-Analyse — Modul 07 (Carveout
Management). Repo-Ist: [`carveouts.md`](../in-progress/carveouts.md) fuehrt
einen lebenden Index mit 4-Typen-Taxonomie (`MR-003`), aber ohne formalen
per-Welle-Audit-Slice und ohne expliziten Werkzeug-Wahl-Trichter.

---

## Trigger

v1.2.0 Modul 07 schaerft die Carveout-Disziplin um zwei Mechaniken, die
der templates-v2-Stand (Basis von `MR-003`) noch nicht trug:

1. **Carveout-Audit-Slice pro Welle-Closure** (v1.2.0-Notation
   `SL-CO-AUDIT-<welle>`): ein wiederkehrender Audit, ob Aufloesungs-Trigger
   eingetreten sind — die strukturelle Antwort auf Carveout-Wildwuchs
   (Entropy Management).
2. **Werkzeug-Wahl-Trichter:** Disambiguierung Carveout vs.
   Brownfield-Sub-Area vs. Folge-ADR ueber **Granularitaet** (einzeln vs.
   Cluster) *vor* **Temporalitaet** — bevor ein Carveout ueberhaupt
   angelegt wird.

grid-gyms Carveout-Form ist bewusst ein **Index** statt Datei-pro-Carveout
(`MR-003`); beide Mechaniken sind davon unabhaengig und liessen sich
additiv einziehen.

## Erwartete Lieferung

- Entscheidung, ob der Audit-Slice als wiederkehrender Schritt pro
  Welle-/Meilenstein-Closure in die Welle-Self-Close-Konvention gefaltet
  wird, **oder** ob der bestehende Self-Close-Move den Audit bereits
  faktisch traegt (dann: explizit dokumentieren statt neu bauen).
- Werkzeug-Wahl-Trichter als kurze Checkliste in
  [`carveouts.md`](../in-progress/carveouts.md) §1 (Konvention).
- Falls die Repo-Form bewusst abweicht: ein `MR-006`-Eintrag in
  [`harness/conventions.md`](../../../../harness/conventions.md), der die
  Abweichung deklariert (sonst stille Setzung).

## Aktivierungs-Kriterium

- Naechste Welle-/M8-Meilenstein-Closure, bei der ein Carveout-Audit
  faellig waere, **oder**
- [`carveouts.md`](../in-progress/carveouts.md) erreicht ≥ 50 Eintraege
  (`MR-003` §4 Split-Trigger) — der natuerliche Moment, die Audit-Mechanik
  mitzuziehen.

## Out-of-scope

- Umstellung der `MR-003`-Index-Form auf das Datei-pro-Carveout-Modell
  (Baseline-Verzeichnis docs/plan/carveouts/) — bewusst abgelehnt
  (`MR-003` Begruendung).

## Bezug

- v1.2.0 Modul 07 (Carveout-Audit-Slice, Werkzeug-Wahl-Trichter).
- [`harness/conventions.md`](../../../../harness/conventions.md) `MR-003`
  (Carveout-Index-Form).
- [`carveouts.md`](../in-progress/carveouts.md) (lebender Index).
