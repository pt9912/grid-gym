# Offene architektonische Punkte (`GG-AR-OPEN-*`)

**Status:** Trigger-Watch-Register (Planung, Rang 5).
**Quelle:** ausgelagert aus `architecture.md` §19 gemäß
[`ADR 0081`](../../adr/0081-open-points-belong-in-planning.md) (Soll-Specs
enthalten keine offenen Punkte; offene Fragen leben in der Planung). Umsetzung:
[`Slice 087`](../done/087-architecture-open-points-to-planning.md).

> **Lebenszyklus** ([`ADR 0081`](../../adr/0081-open-points-belong-in-planning.md)):
> offene Frage → **hier** (Trigger-Watch) · in Klärung → `Proposed`-ADR · entschieden
> → ADR hält die Entscheidung, die Soll-Spec (`architecture.md`) wird auf den neuen Soll
> aktualisiert, und der Punkt wandert als **Provenienz** in den ADR-Index
> ([`docs/plan/adr/README.md`](../../adr/README.md), Abschnitt „Geschlossene
> architektonische Punkte"). Ein Punkt steht also entweder hier (offen) **oder** dort
> (geschlossen) — nie in `architecture.md`.

---

## Offene Punkte

| Kennung | Frage | Aktivierung |
| ------- | ----- | ----------- |
| <a id="gg-ar-open-005"></a>`GG-AR-OPEN-005` | Replay-Diff-Klassifikation: Liste fachlich vs. volatil als Konfiguration oder hartcodiert? | bei Replay-Diff-Erweiterung / Konfigurierbarkeits-Druck |
| <a id="gg-ar-open-006"></a>`GG-AR-OPEN-006` | Snapshot-Format: einheitlich JSON-kanonisch, binär, oder hybrid? | bei Performance-/Größen-Druck am Snapshot-Pfad |
| <a id="gg-ar-open-007"></a>`GG-AR-OPEN-007` | UI-Architektur: SSR vs. SPA; eigene REST-Konsumentenschicht oder direkte WebSocket-Anbindung? | bei UI-Ausbau über die Demo hinaus |
| <a id="gg-ar-open-009"></a>`GG-AR-OPEN-009` | Welche Protokolladapter sind ab MVP enthalten? Heute alle SOLLTE (`GG-MQTT/MODB/OPCUA/DNP3/IEC-001`) | bei formeller MVP-Adapter-Abnahme |
| <a id="gg-ar-open-010"></a>`GG-AR-OPEN-010` | Authentifizierung der API — heute nicht im Lastenheft normiert; spätere `GG-SAFE-…`-Erweiterung | bei Auth-/Security-Anforderung an die API |

Wird ein Punkt geschlossen, wandert er (mit Verweis auf die auflösende ADR) in den
ADR-Index; die zugehörige Anforderung/Struktur wird in `architecture.md` als Soll
nachgezogen.
