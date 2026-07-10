# 063 — §27-Traceability aus `lastenheft.md` in ein eigenes Dokument auslagern

**Status:** In Progress — Slice-Plan (Tranchen + DoD)
**Datum:** 2026-07-10
**Quelle:** Session-Entscheidung nach der SDP-Bereinigung (Welle-Removal +
`## Historie`-Aufloesung in `protocol_profiles.md`/`architecture.md` +
`Historie` aus `.d-check.yml` `exclude-sections`). §27 ist der letzte
`exclude-sections`-Anhang im `contract`-Stratum.

---

## Kontext / Befund

§27 „V-Modell-aehnliche Rueckverfolgbarkeit" (Zeilen 2107–EOF, ~312 Zeilen:
§27.1 Design, §27.1.1, §27.2 Implementierung, §27.3 Test) ist ein
**abwaerts-verweisender Anhang** im `contract`-Stratum
([`spec/lastenheft.md`](../../../../spec/lastenheft.md)) — Anforderung →
Design/Impl/Test → Architektur, ADRs, Code, Slices. Er kommt nur via
`matrix.exclude-sections` durch das SDP-Referenzrichtungs-Gate. Zusaetzlich
ist die §27.2-Matrix **volatil** (driftete in Slice 056/060), waehrend der
Vertrag eingefroren sein soll.

Auslagern → `lastenheft.md`-Body wird abwaerts-verweis-frei, die §27-Ausnahmen
fallen weg, und die volatile Trace-Matrix wird vom Vertrag entkoppelt.

## C0 — ZENTRALE ENTSCHEIDUNG (Owner): Anforderungs-Amendment

[`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001) (MUSS) verlangt
woertlich, dass **das Lastenheft** die drei Tabellen fuehrt. Auslagern ist
daher eine **normative Anforderungs-Aenderung**, keine reine Reorg. Optionen:

- **A (Auslagern):** die Anforderung lockern — die Rueckverfolgbarkeit wird in
  einem **verlinkten** Traceability-Dokument gefuehrt (Intent „Traceability
  MUSS existieren" bleibt; nur der physische Ort wird frei). Ggf. Schaerfung
  von [`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md)
  (Dokumentstruktur) per [`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md)-Pattern.
- **B (Status quo):** §27 bleibt im Lastenheft, per `exclude-sections`
  ausgenommen — der **dokumentierte, gueltige** d-check-Pattern (SDP Regel 5).
  Kein Amendment. Dann entfaellt dieser Slice.

**Empfehlung:** A, wenn die „keine exclude-sections-Kruecke"-Linie
konsequent zu Ende gefuehrt werden soll; B ist legitim, wenn die
Traceability-im-Vertrag bewusst gewollt ist. **C1–C4 gelten nur bei A.**

## Tranchen (bei C0 = A)

- **C1 — NEU Traceability-Dokument** (Default-Ort: docs/plan/traceability.md):
  §27.1/27.1.1/27.2/27.3 wortgetreu verschoben; §27-interne Anker/Querverweise
  nachgezogen; Matrix-Klasse geklaert (der Default-Ort matcht keine
  `matrix.classes`-Glob → **unclassified → keine Richtungs-Regel** →
  Abwaerts-Verweise erlaubt; falls d-check das anders behandelt: eigene Klasse
  ergaenzen oder Pfad anpassen).
- **C2 — `lastenheft.md` schlank:** §27 herausgeloest; die Akzeptanz der
  Trace-Anforderung auf „gefuehrt im verlinkten Traceability-Dokument"
  umgeschrieben (Amendment aus C0); eingehende `§27.x`-Verweise repo-weit
  nachgezogen.
- **C3 — `.d-check.yml`:** `27. …`/`27.1 …`/`27.2 …` aus
  `matrix.exclude-sections` entfernt; `make docs-check` gruen (Lastenheft-Body
  abwaerts-frei; `matrix` erzwingt; Trace-Doc frei; `ids` linkt Kennungen).
- **C4 — Closure:** Self-Move nach `done/`, Roadmap-Nachzug,
  Verification-Evidence, DoD.

## DoD (bei A)

- [ ] Amendment beschlossen + Akzeptanz umformuliert (C0/C2).
- [ ] §27 vollstaendig im Traceability-Dokument; `lastenheft.md`-Body ohne
      Abwaerts-Verweise (kein `ADR NNNN`/Slice/Code-Link).
- [ ] `27.*` aus `exclude-sections`; `make docs-check` + `make gates` gruen.
- [ ] Eingehende `§27`-Verweise repo-weit gueltig (Link-Pflege).
- [ ] Doku-only → **kein Release**.

## Betroffene Kennungen

[`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001) (Amendment),
das `make docs-check`-Gate (d-check),
[`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md) (ggf.
Schaerfung), §27.1–27.3, `.d-check.yml` (`matrix.exclude-sections` + Klassen).

## Risiken

- **Normatives Amendment** der Trace-Anforderung — Owner-Entscheidung, C0.
- **Link-Pflege:** §27-interne Anker + eingehende `§27`-Verweise (spec/, ADRs,
  Slices) muessen nachgezogen werden — sonst `anchor-missing`/`target-missing`.
- **Matrix-Klassifizierung** des neuen Docs (unclassified vs. neue Klasse) —
  in C1 verifizieren.
