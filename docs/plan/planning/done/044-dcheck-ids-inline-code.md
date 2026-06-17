# 044 — `ids`-Linkpflicht auch fuer Inline-Code-Kennungen (`link-policy: always`)

**Status:** **Geliefert (2026-06-17)** — die per-Pattern Inline-Code-Linkpflicht
(`link-policy: always`, d-check v0.11.0, CR #3) ist auf die fuenf
Nicht-Wildcard-Patterns aktiviert; der Link-Sweep hat **1519** Backtick-IDs
in 124 Dateien in die Link-Form gebracht; `make docs-check` gruen (244 Dateien,
0 Befunde). Wildcards bleiben `prose`.
**Datum:** 2026-06-12
**Quelle:** User-Review der Zwei-Stufen-Konvention aus
[Trigger 043](../done-archive/043-dcheck-ids-linkpflicht.md)-Lieferung
(„`` [`ADR 0042`](../../adr/0042-sbom-tool-and-release-pattern.md) `` hat einen Link" — Code-Optik und Link sind
kein Widerspruch).

---

## Trigger

Die `DC-FA-ID-001`-Code-Span-Ausnahme behandelt zwei Faelle
gleich: (a) Kurzschrift/Wildcards/Beispiel-IDs ohne
verlinkbare Einzel-Definition (`GG-DEMO-*`) und (b) konkrete
Kennungen in Code-Optik, die verlinkbar sind —
[`GG-DEMO-006`](../../../user/gg-demo-008-abnahme.md) ist
gerendert nahezu identisch zu [`GG-DEMO-006`](../../../../spec/lastenheft.md#gg-demo-006).

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
   Inline-Code-Vorkommen einer (nicht-Wildcard-)Kennung ohne Link →
   `id-unlinked`; Default `prose` unveraendert.
2. **Digest-Pin-Bump:** ✅ erledigt — `D_CHECK_IMAGE` auf den v0.11.0-Digest
   (Slice 050).
3. **`.d-check.yml`:** ✅ die fuenf Nicht-Wildcard-Patterns (`GG-*-NNN`,
   `GG-AR-*`, `GG-AR-COMP-*`, `AC-*`, `ADR NNNN`) auf `link-policy: always`;
   Wildcard-Muster bleiben `prose`.
4. **Sweep:** ✅ **1519** Backtick-IDs in die Link-Form gebracht (124 Dateien).
   Anker-Aufloesung: `GG-*-NNN` → `lastenheft.md`, `GG-AR-*` →
   `architecture.md`-Sektion, `AC-*` → die Architektur-Test-Contract-Liste
   (mit Datei-Overrides fuer AC mit eigener ADR:
   [`AC-NO-COVERAGE-PRAGMA`](../../adr/0029-no-coverage-pragma-contract.md),
   [`AC-OTLP-ADAPTER-NO-TIME`](../../adr/0024-observability-port-trio.md),
   [`AC-IEC61850-GPL-BOUNDARY`](../../adr/0035-iec61850-adapter-profile.md)),
   ADR-Nummern → ADR-Datei.
   **Carve-out:** Refs auf das superseded `ADR 0003` sind nicht verlinkbar <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
   (ausser vom Supersedeer `ADR 0006`) → 18 zeilen-scoped `d-check:ignore`-
   Marker in 048/049/050. Compound-Spans (`GG-X + GG-Y` in einem Backtick-Span)
   wurden je-ID verlinkt.

## Aktivierung

✅ Vollstaendig erledigt — Tool (d-check v0.11.0) + grid-gym (Schritte 3 + 4).

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
