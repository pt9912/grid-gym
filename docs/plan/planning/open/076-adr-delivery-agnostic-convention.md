# 076 — ADRs liefer-agnostisch (keine spezifischen Slice-Referenzen im ADR-Body)

**Status:** Open — Trigger-Watch
**Datum:** 2026-07-12
**Quelle:** Owner-Entscheidung 2026-07-12 bei der Field-Server-Slice-073-Arbeit —
[`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) wurde
bewusst **liefer-agnostisch** gefasst (Status-Pfad kapazitaetsbasiert; keine
`[Slice NNN]`-Links im Body; Delivery-Mapping nur in ADR-Index + Roadmap).

---

## Kontext

Konventions-Entscheidung: ein ADR beschreibt die **Architektur-Entscheidung**,
nicht ihren Liefer-Schnitt. Slice-/Wellen-Referenzen sind **Abwaerts-Verweise**
(ADR = Source-Precedence Rang 4 → Planning = Rang 5); sie gehoeren in den
**ADR-Index** ([`docs/plan/adr/README.md`](../../adr/README.md)) und die
[`Roadmap`](../in-progress/roadmap.md), die als Living-Tracking-Docs das
Delivery-Mapping fuehren. Slices verweisen **aufwaerts** auf ihre ADR (sauber).

[`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) folgt
der Konvention bereits (design-first eingefuehrt). Bestehende ADRs koppeln
Lifecycle/`Lieferung` noch an konkrete Slices im Body:

- [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) — Status
  „gezogen mit Slice 071"; §5 „Lieferung" listet + verlinkt Slice A/B.
- [`ADR 0030`](../../adr/0030-device-protocol-port-surface.md) — referenziert die
  M4-Wellen-Slice-Plaene im Body.

## Erwartete Lieferung

Ein Doku-Slice (kein Runtime-Delta → kein Release):

1. **Konventions-Anker:** kurze Notiz in
   [`docs/plan/adr/README.md`](../../adr/README.md) (Konvention-Sektion) und/oder
   [`harness/conventions.md`](../../../../harness/conventions.md): „ADR-Body ist
   liefer-agnostisch; Delivery-Mapping lebt im Index/Roadmap."
2. **Nachzug bestehender ADRs:** Status-Pfad kapazitaets-/bedingungsbasiert statt
   slice-benannt formulieren; `[Slice NNN]`-Links aus dem Body in die Index-Zeile
   verschieben. **Wichtig:** [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md)
   und [`ADR 0030`](../../adr/0030-device-protocol-port-surface.md) sind
   **`Accepted`** — Textaenderung nur per [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)
   §3-konformem Pfad (Living-Index-Pflege ist mutabel; der immutable ADR-
   Entscheidungstext bleibt — ggf. reicht es, nur Status-Pfad-/Index-Zeilen
   anzupassen und den historischen Lieferungs-Text stehenzulassen). Genauer
   Scope beim Aktivieren klaeren.
3. **Sweep:** `grep -rnE 'Slice [0-9]|planning/(next|done)' docs/plan/adr/*.md`
   fuer weitere Fundstellen.

## Aktivierungs-Bedingung

- Naechste bewusste ADR-Hygiene-/Doku-Runde, oder
- wenn ein weiterer neuer ADR die Frage erneut aufwirft.

Niedrige Prioritaet — reine Konsistenz/Hygiene, kein Funktions- oder
Vertragsdefekt.

## Wandert nach

- `next/`, sobald der Doku-Slice geschnitten ist,
- `done/`, wenn die ADRs nachgezogen + der Konventions-Anker gesetzt ist.

## Bezug

- [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
  (Konventions-Praezedenz, liefer-agnostisch).
- [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)
  §3/§4 (ADR-Lifecycle + Immutabilitaet des Entscheidungstexts).
- [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) /
  [`ADR 0030`](../../adr/0030-device-protocol-port-surface.md) (bekannte
  Nachzug-Kandidaten).
