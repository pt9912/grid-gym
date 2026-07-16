# 088 — §27.1-Konsistenz-Gate + Generator (Traceability-Ausbaustufe)

**Status:** Open — Trigger-Watch (Cross-Repo-Abhängigkeit).
**Datum:** 2026-07-16
**Quelle:** [`Slice 086`](../done/086-traceability-derived-27-1-finalization.md) —
die `§27.1 authored → derived`-Ausbaustufe aus
[`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §4.4 (iii)/(iv) ist **vertagt**,
weil sie ein neues `d-check`-Feature braucht (nicht repo-lokal baubar).

---

## Kontext

Nach 084 (ARCH-007/008 + SCN-006) und 086 (ARCH-006) ist die
[`traceability.md`](../../traceability.md) §27.1-Design-Tabelle eine **kuratierte,
gegroundete Vorwärts-Map** (Anforderung → implementierende `GG-AR-*`-Artefakte) —
**kein** vollständiger Spiegel der aufwärts zeigenden `architecture.md`-Bezug-Kanten
(Rest-Drift z. B. ARCH-005/P-005). **Genau diese** formale Set-Konsistenz zwischen
§27.1 und den Bezug-Kanten herzustellen ist die Aufgabe dieses Gates. Das
[`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Amendment (086)
beschreibt §27.1 bereits als Verfeinerung des Dreischicht-Modells.

Die **maschinelle** Ausbaustufe fehlt noch — und ist ein **Tooling-/Prozess-Offenpunkt**,
gehört also in die Planung, nicht in die Soll-Spec (siehe
[`ADR 0081`](../../adr/0081-open-points-belong-in-planning.md)).

## Erwartete Lieferung (Ausbaustufe, ADR 0080 §4.4 iii/iv)

1. **Konsistenz-Gate (iii):** ein Gate, das je §27.1-Anforderungs-Zeile die Menge ihrer
   Design-Artefakte ↔ die Menge der aufwärts zeigenden `architecture.md`-Bezug-Kanten
   abgleicht (**Mengen-/Kanten-Konsistenz, 1:N**; requirement-indiziert, Spec-Zwischenknoten
   sind Ableitungs-*Sprünge*). Killt die Bezug↔§27.1-Drift maschinell.
2. **Generator/Report (iv, optional/Endzustand):** §27.1-Positivtabelle nicht mehr
   gespeichert, sondern von `doc-trace` aus den Bezug-Spalten erzeugt (Präzedenz:
   §27.2-Delegation, Slice 066). Erst **nach** dem Gate — „das Gate verdient sich das
   Recht zu generieren".

## Aktivierungs-Bedingung

- Users externes `d-check`-Tool
  (ghcr.io/pt9912/d-check) liefert eine Ableitungs-/Konsistenz-Gate-Fähigkeit für
  requirement→design gegen `architecture.md`-Bezug-Kanten (heute: `matrix`/`trace`
  können das nicht; `--require-complete` ist bewusst nicht verdrahtet). Doku-Check-
  Features gehören ins d-check-Repo, nicht repo-lokal.

## Wandert nach

- `next/` sobald das d-check-Feature verfügbar ist, dann `in-progress/` → `done/`.

## Bezug

- [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §4.4 (iii)/(iv),
  [`ADR 0081`](../../adr/0081-open-points-belong-in-planning.md) (offene Punkte → Planung).
- [`Slice 086`](../done/086-traceability-derived-27-1-finalization.md) (Vertagung),
  [`066`](../done/066-traceability-recut-delegate-27-2.md) (Delegations-Präzedenz).
- [`docs/plan/traceability.md`](../../traceability.md) §27.1.
