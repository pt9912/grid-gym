# 086 — Traceability-Modell-Finalisierung: GG-TRACE-001-Amendment + §27.1 authored→derived

**Status:** **Abgeschlossen (`done/`, 2026-07-16) — Arc-Abschluss.** Slice 4/4 des
Migrations-Arcs (Spec-Schichtung). [`ADR 0080`](../../adr/0080-three-layer-spec-model.md)
§2d/§2e + §4.4. **Doku-/Config-only → kein Release.**
**Datum:** 2026-07-16

> **Closure / Verifikation (2026-07-16).** Umgesetzt: (1) **ARCH-006-§27.1-Fix** — die
> ARCH-006-Zeile um COMP-CORE ergänzt (aus der 084-Closure verankert; COMP-CORE ist ein
> realer Aufwärts-Zeiger für ARCH-006). §27.1 bleibt eine **kuratierte Vorwärts-Map**
> (req→Design), **kein** vollständiger Bezug-Spiegel — die formale Set-Konsistenz gegen die
> `Bezug`-Kanten stellt erst Trigger 088s Gate her (Rest-Drift z. B. ARCH-005/P-005). (2)
> **[`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Amendment** (Vertrag, rank-1, wie
> Slice 066): die Akzeptanz beschreibt jetzt §27.1 als Verfeinerung des Dreischicht-
> Modells (Lastenheft → Spezifikation → Architektur; ableitbar aus den Aufwärts-Zeigern,
> konsistent gehalten). (3) §27.1-Intro nachgezogen (authored-**aber-konsistent**).
> **Ausbaustufe vertagt (konform zu [`ADR 0081`](../../adr/0081-open-points-belong-in-planning.md)):** das maschinelle Konsistenz-**Gate** (iii)
> und der **Generator** (iv) brauchen ein neues d-check-Feature (`--require-complete`
> bewusst nicht verdrahtet) → als **offener Tooling-Punkt** in die Planung ausgelagert
> ([`Trigger 088`](../open/088-27-1-consistency-gate-generator.md)), **nicht** in die
> Spec. §27.1.1 unverändert kuratiert. **`make docs-check` + `make gates` grün.**
>
> **Arc-Abschluss:** der [`ADR 0080`](../../adr/0080-three-layer-spec-model.md)-Arc (083/084/085/086 + 087) ist **komplett**. Der
> Vertrag enthält nur noch echte Anforderungen; jede Umzugs-Familie hat **eine**
> autoritative Heimat (spezifikation.md); die **Schicht-Struktur** für die Auflösung der
> §18/„Bezug"↔§27.1-Redundanz steht. Die **maschinelle** Auflösung (derived/gegatete §27.1)
> bleibt Trigger 088.

---

## Motivation

Mit dem harten Kern (083) und den QS-Familien (085) umgezogen und der
Bezug-Drift behoben (084) ist die Voraussetzung erfüllt, das §27.1-Modell
formal zu schließen: von **`authored` (handgepflegt)** zu **`derived`/gegatet**
(ADR §2d). Weil jede Spezifikation aufwärts auf ihre Anforderung und jedes
Architektur-Artefakt aufwärts auf seine Spezifikation zeigt, ist die
Anforderung→Design-Kette aus den Aufwärts-Zeigern **ableitbar**.

Zugleich muss [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)
(Vertrag) die Dreischicht + die abgeleitete/gegatete §27.1 beschreiben
(Präzedenz: Slice 066).

## Betroffene Kennungen

- [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001) (Vertrag) —
  Amendment (letzter Vertrag-Eingriff des Arcs).
- §27.1-Generator-Promotion + Konsistenz-Gate — als **offene Tooling-/
  Traceability-Punkte** hier bzw. in der Roadmap geführt (**nicht** als
  `GG-SPEC-OPEN`-Eintrag in `spezifikation.md`: die Spezifikations-Schicht
  beschreibt das *Ziel*, keine Prozess-/Werkzeug-Offenpunkte — Owner-Korrektur zu
  [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §4.5).
- §27.1 / §27.1.1 (`traceability.md`) — Modell-Umstellung.

## Umfang / Erwartete Lieferung

1. **[`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Amendment** in
   `lastenheft.md`: Akzeptanz beschreibt das Dreischicht-Modell + die abgeleitete/
   gegatete §27.1. **Am realen Wortlaut ansetzen:** die heutige
   [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Akzeptanz
   verweist bereits auf `docs/plan/traceability.md` (ausgelagert Slice 063, re-cut
   066) und nennt **kein** architecture.md §18 mehr — den vorhandenen Text
   fortschreiben, keinen §18-Baseline erfinden. Vertrag-Eingriff → atomar.
2. **§27.1 → `derived` (Konsistenz-Gate zuerst, ADR §4.4 iii):** ein Gate, das je
   **Anforderungs-Zeile** die **vollständige Menge** ihrer Design-Artefakte gegen
   die Menge der aufwärts zeigenden `architecture.md`-Bezug-Kanten abgleicht
   (**Mengen-/Kanten-Konsistenz, 1:N** — ARCH-007 hat fünf Zeiger, s. 084 — **nicht**
   1:1/„genau einen"). Die Ableitung ist **requirement-indiziert**; Spec-Zwischenknoten
   (architecture→spezifikation) sind Ableitungs-*Sprünge*, keine eigenen §27.1-Zeilen
   (sonst flaggte das Gate die gelöschten Spec-Familien-Zeilen fälschlich). Killt Drift,
   den *eigentlichen* Defekt. **Cross-Repo-Abhängigkeit:** braucht eine neue
   d-check-Ableitungs-/Gate-Fähigkeit → Users externes d-check-Tool
   (ghcr.io/pt9912/d-check; nicht repo-lokal, Doku-Check-Features gehören
   dorthin). Ist die Fähigkeit **verfügbar** → hier verdrahten (`make`-Target).
   Ist sie **noch nicht verfügbar** → §27.1 bleibt *authored-aber-konsistent*
   (durch 084 sauber), und das Gate wird als offener Punkt hier/in der Roadmap
   vertagt (Aktivierung bei d-check-Feature-Release).
3. **Generator/Report (ADR §4.4 iv, optional/Endzustand):** Positivtabelle nicht
   mehr gespeichert, sondern von `doc-trace` aus den Bezug-Spalten erzeugt
   (Präzedenz §27.2-Delegation, Slice 066). Bleibt **vertagt**, bis das
   Konsistenz-Gate die Quelle sauber erzwingt — „das Gate verdient sich das Recht
   zu generieren" (ADR §4.4).
4. **§27.1.1 bleibt kuratiert** (ADR §2d): gewollte Waisen (`GG-TERM-*` /
   `GG-NONGOAL-*`) sind menschliches Urteil, kein invertierter Zeiger — nicht
   automatisieren.

## Design-Entscheidungen / Risiken

- **§27.1-Quelle vervollständigen (Rest aus 084 — Nebenbefund).** 084 richtete die
  Drift für ARCH-007/008 + SCN-006; **ARCH-006 trägt dieselbe Drift-Klasse**: die
  §5-COMP-CORE-Bezug-Spalte nennt 006, aber die §27.1-ARCH-006-Zeile nennt nur
  COMP-SCHED + P-008 (COMP-CORE fehlt). Als Teil des Konsistenz-Gates hier die
  §27.1-ARCH-006-Zeile um COMP-CORE ergänzen (1-Zeilen-Fix, gleiches Muster wie 084) —
  sonst flaggt das Gate sie zu Recht. Befund aus der
  [`084`](084-architecture-bezug-drift-fix.md)-Closure; bewusst hier statt als
  eigener Slice geführt.
- **Warum Gate vor Generator:** ein Generator auf driftender Quelle produzierte
  selbstbewusst Falsches; erst das Gate erzwingt die Quelle sauber (ADR §4.4).
  084 hat die Quelle weitgehend gerichtet (bis auf den ARCH-006-Rest oben) — dieser
  Slice zementiert das per Gate.
- **d-check-Feature-Risiko:** ob (iii) hier landet oder vertagt wird, hängt allein
  am externen Tool-Stand. Beim Aktivieren prüfen.
- **ADR-Immutabilität:**
  [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Amendment folgt
  dem Slice-066-Muster (Akzeptanz-Fortschreibung, kein Neu-ADR).

## Verifikationspfad

- `make gates` + `make docs-check` grün; falls Gate verdrahtet: neues
  Konsistenz-Gate grün (jede §27.1-Zeile ↔ ein Schicht-Zeiger).
- Gesamt-Arc-Abschluss-Prüfung: Vertrag enthält nur echte Anforderungen; jede
  umgezogene Familie hat **eine** autoritative Heimat (spezifikation.md); §18/
  „Bezug"↔§27.1-Redundanzklasse strukturell aufgelöst.

## DoD

- [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001) amendiert
  (Dreischicht + derived/gated §27.1).
- §27.1 auf `derived`/gegatet umgestellt **oder** als offener Punkt (mit
  Aktivierungs-Bedingung) vertagt; §27.1-Generator-Promotion als Endzustand
  festgehalten (in Roadmap/Slice, nicht in `spezifikation.md`).
- §27.1.1 unverändert kuratiert.
- **Release-Entscheidung: nein.** Doku/Config, kein Runtime-Delta → `[Unreleased]`.
  **Hinweis:** der **gesamte** Arc (083–086) ist doku-/config-/kommentar-only →
  **kein Release, kein Image, kein Tag** über alle vier Slices.

## Wandert nach

- `in-progress/` bei Aktivierung, dann `done/`.

## Bezug

- [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §2d/§2e + §4.4 (iii)/(iv).
- Präzedenz: [`066`](../done/066-traceability-recut-delegate-27-2.md)
  (Traceability-Ableitung +
  [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Amendment).
- Vorgänger [`083`](083-spezifikation-layer-discipline-core-move.md)/[`084`](084-architecture-bezug-drift-fix.md)/[`085`](085-spezifikation-layer-qs-families-move.md).
- [`docs/plan/traceability.md`](../../traceability.md) §27.1/§27.1.1,
  [`spec/lastenheft.md`](../../../../spec/lastenheft.md)
  [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001).
