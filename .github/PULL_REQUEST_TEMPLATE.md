<!--
  grid-gym PR Template
  Vollstaendige Review-Checkliste: docs/user/code-review.md
  ADR-Querverweise: docs/plan/adr/0002-language-and-build-stack.md §A-1
                    docs/plan/adr/0005-type-check-gate.md §5.1
                    docs/plan/adr/0006-adr-lifecycle-superseding-and-process-corrections.md §3
-->

## Was aendert sich?

<!-- 1-3 Saetze, fokussiert auf das Warum, nicht das Was -->

## Bezug zu Lastenheft / Architektur / ADR

<!--
  Kennungen wie `GG-SIM-001`, `GG-AR-COMP-CORE`, `AC-NO-RAND`,
  `ADR 0007`. Pflicht, wenn die PR fachliche oder strukturelle
  Aenderungen enthaelt.
-->

- ...

## Checkliste

**Vor dem Review-Anfrage muss `make gates` (oder
`make gates CRITICAL_COV_TARGETS=...` im M1-Stand) gruen sein.**
Output im Kommentar belegen, solange GitHub-Actions-CI nicht aktiv
ist (kommt mit M1-Welle-6).

- [ ] `make lint` gruen (`ruff check` mit A-1-Regelgruppen)
- [ ] `make format-check` gruen
- [ ] `make typecheck` gruen (`mypy --strict`, ADR 0005)
- [ ] `make arch-check` gruen (16 A-1-Contracts, davon 10 via
      `tools/arch_check.py`)
- [ ] `make test-unit` gruen (inkl. `hypothesis`-Property-Tests)
- [ ] `make coverage-gate-critical` gruen (mit Spike-0/M1-spezifischem
      `CRITICAL_COV_TARGETS`-Override falls noetig)
- [ ] Review-Checkliste aus `docs/user/code-review.md` §3 durchgegangen

### Falls Adapter-Aenderung

- [ ] §3.1 `AC-ADAPTER-PURE`-Reststeuerung: Adapter trifft keine
      fachlichen Entscheidungen (Wertebereich-Pruefung, Routing-
      Logik, Geraete-Spezifisches). Mapping-Funktionen sind im
      Doc-String dokumentiert.

### Falls Domain-Aenderung

- [ ] §3.2 `GG-CC-001` Methoden-/Funktionsgroesse inhaltlich kohaerent
- [ ] §3.3 `GG-CC-005` Naming konsistent zum Architektur-Vokabular
- [ ] §3.4 SOLID-Restanteil (SRP/OCP/LSP/ISP/DIP) geprueft
- [ ] §3.6 `hypothesis`-Property-Tests fuer Determinismus-Pfade

### Falls `pyproject.toml`-Aenderung (`ADR 0006 §3`-Pflicht)

**Beruehrt diese PR eine ADR-konforme Konfiguration?** (siehe
`docs/user/code-review.md` §3.5 fuer die vollstaendige Liste.)

- [ ] Nein — reine Format-/Kommentar-/Major-stabile Versionspin-
      Aenderung. Kein Folge-ADR noetig.
- [ ] Ja — Folge-ADR verlinkt: `ADR XXXX` (mindestens `Provisional`,
      Acceptance synchron zur PR-Mergung; per `ADR 0006 §3` Pflicht).
- [ ] Unklar — Reviewer wird zur Entscheidung gerufen. Bei Zweifel
      Folge-ADR schreiben (im Zweifel mehr Doku, nicht weniger).

## Test plan

<!--
  Was wurde lokal getestet? Bei UI-/Adapter-Aenderungen Output im
  Browser/curl belegen. Bei Determinismus-Aenderungen mindestens
  zwei Laeufe vergleichen.
-->

- [ ] ...

## Risiken / offene Punkte

<!--
  Was bleibt offen? Hat die PR eine ADR-relevante Wirkung, die in
  spaeteren Slices nachgezogen werden muss? Triggers in
  `docs/plan/planning/open/` zu aktualisieren?
-->

- ...
