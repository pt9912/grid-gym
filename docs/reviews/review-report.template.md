# Review-Report: <slice-NN | PR-Ref> — <YYYY-MM-DD>

> **Template-Hinweis.** Vorlage fuer einen Review-Report (Uebergabe-
> Artefakt Reviewer → Implementation). Kopiere nach
> `docs/reviews/<YYYY-MM-DD>-<slice-oder-diff-ref>.md`, ersetze die
> `<Platzhalter>` und loesche diesen Block. Ein Report pro Lauf —
> Folgelaeufe bekommen eine neue Datei, keine Ueberschreibung
> (Auditierbarkeit). Kategorien, Prueflinsen und Output-Schema sind in
> [`harness/review.md`](../../harness/review.md) verbindlich; die
> grid-gym-spezifischen Linsen in
> [`docs/user/code-review.md`](../user/code-review.md).

**Review-Art:** Plan | Design | Code — *wogegen* geprueft wird:
Plan-Review gegen Spec/ADR, Design-Review gegen Architektur,
Code-Review gegen Plan + Konventionen.

**Gegenstand:** <Slice-ID / Diff-Range / Commit-Hash>

**Schema:** [`harness/review.md`](../../harness/review.md) ·
**Modell:** <Modell-ID> · **Datum:** <YYYY-MM-DD>

**Eingangs-Kontext** (die Vertraege, gegen die geprueft wurde — ohne
diese Liste ist der Lauf nicht reproduzierbar):

- <Slice-Plan / Plan-Dokument>
- <aktive ADRs, z. B. `ADR-<NNNN>`>
- <beruehrte `GG-*` / `GG-AR-*`-IDs>
- [`AGENTS.md`](../../AGENTS.md) (Hard Rules)

---

## Findings

Jedes Finding folgt dem **verbindlichen Output-Schema aus
[`harness/review.md`](../../harness/review.md) §Output Schema** — hier nur
gespiegelt, nicht neu definiert. Bei Abweichung gilt `harness/review.md`
(eine Quelle, kein Drift):

```text
<CATEGORY> <path>:<line> - <kurzer Titel>
Quelle: <GG-*|GG-AR-*|ADR-*|Hard Rule|Maintainability>
Befund: <1-2 beobachtbare Saetze, ohne Loesungsvorschlag>
Risiko: <warum das relevant ist>
Verifizierbar: <Sensor/Test/Review-only>
```

## Geprueft ohne Befund

<!--
Eine Zeile pro betrachteter Linse/Bereich. Ohne diesen Block ist "keine
Findings" nicht von "nicht geprueft" unterscheidbar.
-->

- <Linse oder Pfad>

## Nicht geprueft

- <Linse oder Pfad> — <Grund>

## Summary

| Kategorie | Anzahl |
|---|---|
| HIGH | <n> |
| MEDIUM | <n> |
| LOW | <n> |
| INFO | <n> |

## Verdikt

**Merge-blockierend:** ja | nein — HIGH und MEDIUM blockieren
typischerweise; eine Abweichung davon wird hier begruendet, nicht
still entschieden.

**Uebergabe:** Findings gehen an die Implementation (Rueckkante
Review → Plan bei Plan-Defekt). Der Report ersetzt keine Verifikation —
DoD-/Spec-Konformitaet prueft der Verifier separat nach
[`harness/verification.md`](../../harness/verification.md) (anderes
Pruef-Artefakt, anderer Eingabe-Kontext).
