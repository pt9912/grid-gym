# 044 — `ids`-Linkpflicht auch fuer Inline-Code-Kennungen (d-check `inline-code`-Option)

**Status:** Open — Trigger-Watch
**Datum:** 2026-06-12
**Quelle:** User-Review der Zwei-Stufen-Konvention aus
[Trigger 043](../done-archive/043-dcheck-ids-linkpflicht.md)-Lieferung
(„`` `ADR 0042` `` hat einen Link" — Code-Optik und Link sind
kein Widerspruch).

---

## Trigger

Die `DC-FA-ID-001`-Code-Span-Ausnahme behandelt zwei Faelle
gleich: (a) Kurzschrift/Wildcards/Beispiel-IDs ohne
verlinkbare Einzel-Definition (`GG-DEMO-*`) und (b) konkrete
Kennungen in Code-Optik, die verlinkbar sind —
[`GG-DEMO-006`](../../../user/gg-demo-008-abnahme.md) ist
gerendert nahezu identisch zu `GG-DEMO-006`.

**Messung (2026-06-12, lebende Doku):** 1144 verlinkte
ID-Vorkommen vs. **1072 Backtick-Vorkommen der Klasse (b)**
(444 ADRs, 328 planning, 170 spec, 97 docs/user, 30 READMEs);
213 weitere sind automatisch target-exempt
(Definitionsdatei), ~30 Wildcards behalten die Exemption als
Design-Bestandteil.

## Erwartete Lieferung

1. **d-check-CR #3** (uebergeben 2026-06-12): per-Pattern-
   Option `ids.patterns[].inline-code: pruefen | exempt`
   (Default `exempt` = Bestand byte-identisch). Bei `pruefen`
   gilt die Linkpflicht auch in Inline-Code-Spans;
   Fenced-Bloecke bleiben immer ausgenommen; Target-Datei-/
   Verzeichnis-Exemption unveraendert (orts-, nicht
   form-basiert). AK-Skizze: Happy nacktes Code-Span-Vorkommen
   → Befund; Boundary Default unveraendert / Link-Text-Span
   kein Befund / Target-File kein Befund; Negative ungueltiger
   Optionswert → Exit 2. Out-of-Scope: globaler Schalter
   (Wildcard-Muster brauchen die Exemption).
2. **Digest-Pin-Bump** auf das Release mit der Option.
3. **`.d-check.yml`:** numerische + benannte Muster auf
   `pruefen`; Wildcard-Muster bleiben `exempt`.
4. **Sweep:** ~1072 Ersetzungen in die Link-Form
   `` [`ID`](datei#anker) `` —
   exakt abgegrenzte Vorkommen, fertige Anker-Maps; der
   einfachste Sweep der Serie.

## Aktivierung

d-check-Release mit `inline-code`-Option verfuegbar.

## Konsequenz wenn ungeloest

Die Zwei-Stufen-Konvention bleibt: nackte Kennungen bricht das
Gate, Backtick-Kennungen sind unverlinkt zulaessig — Leser
verlieren den Ein-Klick-Sprung zur Definition bei ~1072
Vorkommen.

## Bezuege

- [Trigger 043](../done-archive/043-dcheck-ids-linkpflicht.md) —
  Vorgaenger (Linkpflicht-Aktivierung + Modul-Scope-CR; dort die
  Sweep-Methodik).
- [`.d-check.yml`](../../../../.d-check.yml) — aktuelle Muster.
- d-check `spec/lastenheft.md` `DC-FA-ID-001` (externes Repo
  `pt9912/d-check`) — Boundary-AK, das die Option ergaenzt.
