# 044 — `ids`-Linkpflicht auch fuer Inline-Code-Kennungen (`link-policy: always`)

**Status:** **In Arbeit (in-progress, 2026-06-17)** — der d-check-Blocker ist
weg: v0.11.0 liefert die per-Pattern Inline-Code-Linkpflicht als
**`link-policy: always`** (CR #3; andere Schreibweise als das urspruenglich
vorgeschlagene `inline-code: pruefen`, funktional identisch) und ist bereits
gepinnt (Slice 050). Offen ist die grid-gym-Seite: `.d-check.yml`-Aktivierung
+ Link-Sweep.
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

**Messung (frisch 2026-06-17, `link-policy: always`-Trockenlauf ueber die
fuenf Nicht-Wildcard-Patterns):** **421 `id-unlinked`-Befunde** der Klasse (b)
— planning 152, `spec/lastenheft.md` 119, `docs/plan/adr` 104,
`docs/user/code-review.md` 23, READMEs 10, `spec/architecture.md` 5, Rest ~8.
Deutlich weniger als die 1072 vom 2026-06-12 (seither viel verlinkt; zudem
sind `done-archive/**` + `CHANGELOG.md` per `ids.scope.ignore` ausgenommen).
Wildcards (`GG-*-*`/`AC-*-*`) behalten die Exemption (`prose`) als
Design-Bestandteil.

## Erwartete Lieferung

1. **d-check-Feature:** ✅ geliefert in **v0.11.0** als per-Pattern
   `ids.patterns[].link-policy: prose | always` (Default `prose` = Bestand
   byte-identisch). Bei `always` gilt die Linkpflicht auch in Inline-Code-
   Spans; Fenced-Bloecke bleiben ausgenommen; die Target-Datei-/Verzeichnis-
   Exemption ist unveraendert (orts-, nicht form-basiert); `exempt-paths`
   ergaenzt orts-basierte Ausnahmen. Empirisch verifiziert: ein nacktes
   `` `ADR 0099` `` → `id-unlinked`; Default `prose` unveraendert.
2. **Digest-Pin-Bump:** ✅ erledigt — `D_CHECK_IMAGE` auf den v0.11.0-Digest
   (Slice 050).
3. **`.d-check.yml`:** numerische + benannte Muster auf `link-policy: always`;
   Wildcard-Muster bleiben `prose`. (offen)
4. **Sweep:** ~421 Ersetzungen in die Link-Form `` [`ID`](datei#anker) `` —
   exakt abgegrenzte Vorkommen, fertige Anker-Maps; der einfachste Sweep der
   Serie. (offen)

## Aktivierung

✅ Tool-seitig erledigt (d-check v0.11.0 `link-policy: always`, gepinnt). Offen
sind nur noch die grid-gym-Schritte 3 + 4.

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
