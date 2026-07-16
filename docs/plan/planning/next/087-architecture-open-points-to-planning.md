# 087 — architecture.md §19 auflösen: offene Punkte in die Planung (`GG-AR-OPEN-*`)

**Status:** Geplant (`next/`) — **erster Umsetzungs-Slice von
[`ADR 0081`](../../adr/0081-open-points-belong-in-planning.md)** (Soll-Specs frei
von offenen Punkten).
**Datum:** 2026-07-16
**Quelle:** [`ADR 0081`](../../adr/0081-open-points-belong-in-planning.md) §4 —
`architecture.md` §19 (`GG-AR-OPEN-*`) ist die verbliebene „Offene Punkte"-Sektion
in einer Soll-Spec und aufzulösen.

---

## Motivation

Nach [`ADR 0081`](../../adr/0081-open-points-belong-in-planning.md) enthalten
Soll-Specs (Rang 1–3) nur Entschiedenes. `spezifikation.md` ist bereits frei
(Slice-083-Korrektur); `architecture.md` §19 „Offene architektonische Punkte"
(`GG-AR-OPEN-*`, 001–010) ist der letzte Verstoß.

## Betroffene Kennungen

- `GG-AR-OPEN-*` (10 Einträge, 001–010): **5 offen** (`005` Replay-Diff-Klassifikation,
  `006` Snapshot-Format, `007` UI-Architektur, `009` MVP-Protokolle, `010` API-Auth);
  **5 geschlossen** (`001`→[`ADR 0002`](../../adr/0002-language-and-build-stack.md)/[`ADR 0005`](../../adr/0005-type-check-gate.md),
  `002`/`003`→[`ADR 0012`](../../adr/0012-api-simulation-two-processes.md),
  `004`→[`ADR 0023`](../../adr/0023-agent-bus-protocol.md),
  `008`→[`ADR 0024`](../../adr/0024-observability-port-trio.md)).
- `architecture.md` §19 + `.d-check.yml` `matrix.exclude-sections`.
- **Referenz-Web:** `GG-AR-OPEN-*` ist in ~15 ADRs + `traceability.md` (§27.1-Intro),
  `roadmap.md`, `open/README.md`, `CHANGELOG.md`, `docs/user/code-review.md`
  referenziert (viele ADRs zeigen **zurück** auf ihren geschlossenen Punkt).

## Design-Entscheidungen / Risiken (VOR Umsetzung zu klären)

1. **Anker-Web der *geschlossenen* Punkte — der Knackpunkt.** Auflösende ADRs
   verlinken `GG-AR-OPEN-00X` → `architecture.md#19-offene-architektonische-punkte`.
   Wird §19 entfernt **und** die geschlossenen Einträge gelöscht
   ([`ADR 0081`](../../adr/0081-open-points-belong-in-planning.md) §2c-Intent
   „Provenienz nur im ADR"), brechen diese ADR-Links — ihr Anker verschwindet ersatzlos.
   **Auflösung (Empfehlung):** **alle** `GG-AR-OPEN-*` (001–010) in einen **Planungs-
   Register** übernehmen (offene *und* geschlossene, mit Status/ADR-Verweis), die Anker
   dort erhalten und **alle** Referenzen dorthin repointen. Das verfeinert dessen §2c
   für den Bestandsfall: „geschlossen → in den Planungs-Register als *resolved*"
   statt „ersatzlos löschen" — die Provenienz-Redundanz ist der Preis dafür, das
   Immutabilitäts-gebundene ADR-Referenz-Web nicht zu brechen. (Alternative: nur offene
   umziehen + ADR-Refs auf die je auflösende ADR umbiegen — mehr Einzel-Repoints,
   fragiler. Beim Aktivieren final entscheiden.)
2. **Ziel-Home.** Ein dedizierter Planungs-Register (`docs/plan/planning/`; z. B.
   `open/architecture-open-points.md` als Trigger-Watch-Register, im `open/README`
   indexiert) hält `GG-AR-OPEN-*` mit Status. Die *offenen* Punkte sind damit
   Trigger-Watch (konform zu [`ADR 0081`](../../adr/0081-open-points-belong-in-planning.md));
   die *geschlossenen* dienen als Anker + Provenienz-
   Pointer auf die auflösende ADR.
3. **ADR-Immutabilität.** Referenz-Repoints in den ~15 ADRs sind **Pfad-/Anker-
   Maintenance** per [`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md)
   (Ziel inhaltsgleich, nur verschoben) — **keine** ADR-Prosa ändern.

## Umfang / Erwartete Lieferung

1. **Planungs-Register anlegen** mit `GG-AR-OPEN-*` (001–010; Status + ADR-Verweis je
   geschlossenem Punkt), im `open/README` indexiert.
2. **§19 aus `architecture.md` entfernen** (Header-Sprung §17→§20 wird §17→…; sauber
   um §18/§20 herum schneiden — §19 ist die einzige zu entfernende Sektion).
3. **Repoint** aller `GG-AR-OPEN-*`-Referenzen (ADRs per [`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md), `traceability.md`
   §27.1-Intro, `roadmap.md`, `open/README`, `CHANGELOG`, `code-review.md`) auf das
   Register.
4. **`.d-check.yml`:** `matrix.exclude-sections`-Eintrag „19. Offene architektonische
   Punkte" entfernen; `ids`-`GG-AR-OPEN`-Ziel (heute `architecture.md`) auf den
   Register-Pfad umbiegen (Muster-Priorität wie bei der PRINC/CC-Regel in 083).
5. **`traceability.md` §27.1-Intro** (nennt `GG-AR-OPEN-*` als architecture.md-Familie)
   nachziehen.

## Verifikationspfad

- `make docs-check` + `make gates` grün; `spec/` enthält **kein** `GG-AR-OPEN` mehr;
  jede der ~15 ADR-Referenzen + übrigen Refs resolvt auf den Register-Anker.
- **Adversarialer Review vor Commit** (wie 083): Referenz-Vollständigkeit + korrekte
  [`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md)-Abgrenzung (nur Links, keine Prosa) + kein gebrochenes Anker-Web.

## DoD

- `architecture.md` frei von „Offene Punkte" (§19 weg); `GG-AR-OPEN-*` im Planungs-
  Register; alle Referenzen repointet; docs-check + gates grün.
- **Release-Entscheidung: nein.** Doku/Config-only → `[Unreleased]`.

## Wandert nach

- `in-progress/` bei Aktivierung, dann `done/` mit Closure-Notiz.

## Bezug

- [`ADR 0081`](../../adr/0081-open-points-belong-in-planning.md) (Prinzip, §4),
  [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) (Soll-Schichten),
  [`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md) (Link-Maintenance).
- Präzedenz Spec-Cut + Repoint: [`083`](../done/083-spezifikation-layer-discipline-core-move.md).
- [`spec/architecture.md`](../../../../spec/architecture.md) §19,
  [`roadmap.md`](../in-progress/roadmap.md).
