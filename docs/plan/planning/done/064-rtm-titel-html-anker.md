# 064 — RTM-Titel via HTML-Anker (`make doc-trace` Titel-Spalte)

**Status:** Done — 2026-07-11
**Datum:** 2026-07-11
**Quelle:** Session-Follow-up zum d-check-v0.40.0-Bump (Trace-RTM konfiguriert,
Commit `f30382c`). `make doc-trace` fuellt die `Titel`-Spalte nicht, weil
`spec/lastenheft.md` **bare-ID-Headings** nutzt (`## GG-XXX-NNN` ohne Titeltext,
0 von 243).

---

## Kontext / Befund

d-check zieht den RTM-Titel aus dem **Heading-Text nach der ID** (empirisch
belegt — siehe Ansatz unten: ein Heading mit Titeltext liefert den Titel, ein
bare-ID-Heading liefert leer). grid-gyms Requirement-Headings sind aber bewusst
bare IDs — der Anforderungstext steht im Body (Ø 57 Zeichen, kein Titel).

**Naiver Fix (Titel ans Heading) bricht Anker:** der GitHub-Slug haengt dann am
Titel (`#gg-rt-005` → `#gg-rt-005-wall-clock-multiplikatoren`). Das wuerde
**1388 Verweise** auf Lastenheft-Requirement-Anker (178 distinct Anker, 144
Dateien, davon nur 40 in `done-archive/`) brechen und ~20 **Accepted**-ADRs
anfassen (Aenderungsverbot) — und es widerspraeche
[`ADR 0004`](../../adr/0004-identifier-based-cross-references.md)
(kennungsbasierte, titel-**un**abhaengige Querverweise).

## Ansatz (verifiziert)

**Expliziter HTML-Anker pro Requirement** haelt den ID-Anker stabil, waehrend
das Heading einen Titel bekommt:

```
## GG-RT-005 Wall-Clock-Multiplikatoren
<a id="gg-rt-005"></a>
```

Empirisch gegen d-check v0.40.0 belegt: alte `#gg-...`-Links loesen gegen den
HTML-Anker auf (`docs-check` 0 Befunde), `<a id>` **und** `<a name>` werden
akzeptiert, `ids`/`anchors`/`spans` flaggen den betitelten Heading nicht, und
`--trace` fuellt den Titel. Damit: **keine** der 1388 Links wird angefasst,
**keine** ADR editiert, und der stabile ID-Anker bleibt konform zu
[`ADR 0004`](../../adr/0004-identifier-based-cross-references.md) (titel-unabhaengig).

**Scope:** nur die **226** RTM-erfassten Requirements (38 normative
`GG-<FAMILIE>`, siehe `.d-check.yml` `trace.requirements.id-pattern`). Die
definitorischen Familien `GG-TERM`/`GG-NONGOAL`/`GG-FUTURE` bleiben bare (nicht
in der RTM).

## Tranchen

- **C1 — Pilot (1 Familie, z. B. `GG-RT`):** Anker + Titel fuer eine Familie;
  `make doc-trace` (Titel gefuellt) + `make docs-check` (Links aufgeloest) gruen.
  **Titel-Stil zur Abnahme vorlegen** (Kurz-Nominalphrase aus dem Body-Normsatz).
- **C2 — Titel-Entwuerfe (alle 226):** aus den Body-Normsaetzen kondensierte
  Kurztitel (Nominalphrase, keine Modalverben/Akzeptanz), zum Review.
- **C3 — Rollout (Skript):** `<a id="gg-xxx-nnn"></a>` deterministisch je
  Requirement einfuegen; Titel je Heading setzen; nur die 226 Familien.
- **C4 — Verifikation:** `make doc-trace` (226 Titel gefuellt), `make docs-check`
  (0 Befunde — kein `anchor-missing`/`target-missing`), `make gates` gruen.
- **C5 — Closure:** Self-Move nach `done/`, Roadmap-Nachzug, Verification-
  Evidence, DoD, CHANGELOG `[Unreleased]`.

## DoD

- [x] Alle 226 RTM-Requirements tragen Titel + stabilen `<a id>`-Anker.
- [x] `make doc-trace`: `Titel`-Spalte fuer die 226 gefuellt, `total`/`orphans`
      unveraendert (226), Familien-Set unveraendert.
- [x] `make docs-check` + `make gates` gruen (kein Link-/Anker-Bruch).
- [x] Bestehende Lastenheft-Requirement-Anker (`#gg-...`) unveraendert & gueltig.
- [x] Konform zu [`ADR 0004`](../../adr/0004-identifier-based-cross-references.md)
      (ID-Anker titel-unabhaengig); keine ADR editiert.
- [x] Doku-only → **kein Release** (CHANGELOG `[Unreleased]`).

## Betroffene Kennungen

Alle 226 RTM-Requirements aus den 38 normativen `GG-<FAMILIE>`-Familien
(`.d-check.yml` `trace.requirements.id-pattern`); der `trace:`-Block +
`make doc-trace`-Advisory; [`ADR 0004`](../../adr/0004-identifier-based-cross-references.md)
(kennungsbasierte Querverweise — Leitplanke); `spec/lastenheft.md`
(`contract`-Stratum). Kuratierte Quelle bleibt
[`traceability.md`](../../traceability.md)
([`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)).

## Risiken

- **`contract`-Stratum-Churn:** 226 Headings im stabilsten Doku aendern sich
  (referenz-sicher via HTML-Anker, aber grosser Diff) — daher eigener Slice,
  nicht an den Tooling-Bump gehaengt.
- **Slug-Korrektheit:** der d-check-Anker-Resolver muss `#gg-xxx-nnn` gegen den
  HTML-Anker matchen (C1/C4 verifizieren; empirisch bereits gruen).
- **GitHub.com-Rendering:** rohe `<a id/name>`-Anker koennen im Browser je
  Sanitizer (`user-content-`-Praefix) abweichen — fuer das Repo-Gate irrelevant,
  nur falls primaer via github.com-Anker navigiert wird.
- **Titel-Qualitaet:** Auto-Kondensat aus dem Body braucht Review (C1/C2).

---

## Closure 2026-07-11

Umgesetzt wie geplant; Titel-Stil in C1 (`GG-RT`) + erweiterter Probe
(`GG-QA`/`GG-PERSIST`/`GG-COV`) abgenommen, dann auf alle 226 ausgerollt.

- **C1–C3:** Alle **226** RTM-Requirements (38 normative Familien) tragen jetzt
  eine Kurz-Nominalphrase im Heading + einen stabilen `<a id="gg-...">`-Anker
  (Skript-getrieben, idempotent; 452 Zeilen +, 226 −). Definitorische Familien
  (`GG-TERM`/`GG-NONGOAL`/`GG-FUTURE`) blieben bare.
- **C4 — Verifikation:** `make doc-trace` = **226/226 Titel gefuellt**,
  `total=226 / orphans=171 / 38 Familien` unveraendert; `make docs-check`
  **0 Befunde** (alle bestehenden `#gg-...`-Verweise loesen via HTML-Anker auf —
  kein `anchor-missing`); `make gates` gruen. Keine ADR editiert; ID-Anker
  bleibt titel-unabhaengig ([`ADR 0004`](../../adr/0004-identifier-based-cross-references.md)-konform).
- **Vorarbeit:** d-check-Bump v0.40.0 + `trace:`-Block (Commit `f30382c`), der
  `--trace` ueberhaupt erst kennungs-konfigurierbar machte.

**Evidence:** `make doc-trace`/`docs-check`/`gates` gruen. Doku-only, **kein
Release** (CHANGELOG `[Unreleased]`).
