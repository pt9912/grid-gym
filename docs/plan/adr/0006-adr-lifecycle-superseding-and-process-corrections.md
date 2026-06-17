# ADR 0006 — ADR-Lifecycle: Superseding und Prozesskorrekturen

**Status:** Accepted
**Datum:** 2026-05-14
**Bezug:** [ADR 0001](0001-documentation-and-planning-structure.md),
`ADR 0003` (abgeloest, legitime Supersede-Lineage; Inline-Code statt Link,
da das `matrix`-Modul keinen Lineage-Carve-out kennt),
[ADR 0004](0004-identifier-based-cross-references.md),
[Lastenheft](../../../spec/lastenheft.md),
[Architektur](../../../spec/architecture.md)
**Aenderungstyp:** Supersedes `ADR 0003`. Praezisiert die
Retrofit-Regel aus `ADR 0004` fuer Lifecycle-Metadaten.

---

## 1. Kontext

`ADR 0003` hat den ADR-Lifecycle eingefuehrt. Danach wurde deutlich,
dass drei Punkte praeziser geregelt werden muessen:

- Eine akzeptierte ADR muss spaeter als `Superseded` markierbar sein,
  ohne ihren Entscheidungstext inhaltlich umzuschreiben.
- Vor `Accepted` koennen operative Spike-Artefakte (`Makefile`,
  `Dockerfile`, CI-Jobs, Tool-Konfiguration) noetig sein, duerfen aber
  keinen verbindlichen Beschluss vortaeuschen.
- `Rejected` und `Withdrawn` brauchen unterschiedliche Bedeutung:
  bewusste Negativentscheidung vs. Rueckzug ohne Negativentscheidung.

`ADR 0004` verbietet Sammel-Umschreibungen akzeptierter ADRs und
fordert kennungsbasierte Querverweise. Deshalb wird `ADR 0003` nicht
weiter inhaltlich fortgeschrieben. Diese ADR ersetzt ihn als neue
Lifecycle-Quelle.

---

## 2. Entscheidung

ADRs in `docs/plan/adr/` durchlaufen den folgenden Lebenszyklus:

| Status        | Bedeutung | Wirkung |
| ------------- | --------- | ------- |
| `Proposed`    | Empfehlung formuliert, **kein** Beschluss. Optionen und Bewertungskriterien sind dokumentiert. | Keine normative Wirkung. Abhaengige Dokumente duerfen hoechstens als Entwurf auf die ADR verweisen. |
| `Provisional` | Projektowner traegt die Empfehlung mit; ein begrenzter Validierungs-Spike laeuft, dessen Vertrag in der ADR steht. | Eingeschraenkte Wirkung. Abhaengige Dokumente duerfen auf den laufenden Spike verweisen, aber keine `GG-AR-OPEN-*`- oder Lastenheft-Anforderung als geschlossen markieren. |
| `Accepted`    | Beschluss steht. Falls die ADR einen Validierungs-Spike enthielt, ist dieser nachweisbar gruen abgeschlossen. | Volle Wirkung. Abhaengige Dokumente werden gepflegt; offene Punkte duerfen als geschlossen markiert werden. |
| `Rejected`    | ADR wird nach Review, Spike oder Owner-Entscheid bewusst nicht uebernommen. Die Negativentscheidung und ihre Begruendung bleiben dauerhaft in der ADR. | Normative Schluss-Verweise werden entfernt; Folge-ADRs duerfen die Ablehnungsgruende referenzieren. |
| `Withdrawn`   | Autor oder Owner zieht den Vorschlag vor Beschluss zurueck. Es liegt keine Negativentscheidung vor. | Laufende Hinweis-Verweise werden entfernt; der Vorschlag bleibt historisch sichtbar, bindet aber nicht. |
| `Superseded`  | ADR war akzeptiert, ist aber durch eine spaetere ADR abgeloest. | Historisch. Die alte ADR bindet nicht mehr; abhaengige Dokumente und operative Artefakte verweisen auf die Nachfolge-ADR. |

Erlaubte Uebergaenge:

```text
                Proposed
                  │  │
        ┌─────────┘  └─────────┐
        ▼                      ▼
    Provisional             Rejected / Withdrawn
        │
        ├──▶ Accepted ──▶ Superseded
        │
        └──▶ Rejected / Withdrawn
```

`Provisional` ist optional. Eine ADR ohne Validierungsbedarf darf
direkt `Proposed → Accepted` springen.

---

## 3. Aenderungsregeln

Nach `Accepted` ist der Entscheidungstext immutable. Fachliche
Aenderungen kommen als neue ADR, die die bestehende ADR abloest.

Zulaessig bleiben nur Metadaten-Aenderungen an der alten ADR:

- Statuswechsel auf `Superseded`,
- `Status geaendert am`,
- `Superseded by`,
- ein kurzer Hinweis im Header, dass die ADR historisch ist.

Keine zulaessige Metadaten-Aenderung sind neue Begruendungen,
neue Regeln, erweiterte Scope-Definitionen oder korrigierte
Konsequenzen. Solche Inhalte gehoeren in die Nachfolge-ADR.

---

## 4. Header-Schema

Jede ADR fuehrt im Header:

- `Status`: Lifecycle-Status, optional mit kurzem Klartext-Zusatz.
- `Datum`: Erstellungsdatum der ADR.
- `Status geaendert am`: Pflicht bei jedem Statuswechsel nach der
  Erstellung.
- `Letzte inhaltliche Aenderung`: Pflicht bei inhaltlichen
  Aenderungen vor `Accepted`; nach `Accepted` nur in der
  Nachfolge-ADR, nicht im abgeloesten Entscheidungstext.
- `Superseded by`: Pflicht bei Status `Superseded`.

Das Feld `Letzte inhaltliche Aenderung` ist kein Freibrief fuer
post-Acceptance-Korrekturen. Es dokumentiert nur erlaubte
Pre-Acceptance-Schaerfungen oder die Entstehung dieser ADR selbst.

---

## 5. Operative Artefakte

Die Status-Wirkung in dieser ADR gilt fuer normative Dokumente
(`spec/lastenheft.md`, `spec/architecture.md`) und fuer operative
Artefakte.

- Bei `Proposed` sind Code, `Makefile`, `Dockerfile`, CI-Jobs oder
  Tool-Konfiguration nur als Spike-/Prototyp-Artefakte erlaubt. Sie
  MUESSEN als `Spike` oder `Prototyp` mit ADR-Verweis markiert sein
  und duerfen keinen beschlossenen Stack oder Prozess behaupten.
- Bei `Provisional` duerfen solche Artefakte den validierten Pfad des
  Spike-Vertrags bilden. Sie bleiben vorlaeufig und MUESSEN bei
  `Rejected` oder `Withdrawn` entfernt, archiviert oder auf den
  Folgepfad umgestellt werden.
- Bei `Accepted` werden die Artefakte verbindliche
  Projektkonvention.
- Bei `Superseded` MUESSEN betroffene Artefakte auf die Nachfolge-ADR
  umgestellt oder als historisch/obsolete markiert werden. Sie duerfen
  nicht weiter eine abgeloeste ADR als aktive Grundlage ausgeben.

---

## 6. Bezug zu ADR 0004

Die Retrofit-Regel aus `ADR 0004` wird fuer Lifecycle-Aenderungen so
gelesen:

- Akzeptierte ADRs werden nicht inhaltlich auf neue Querverweis- oder
  Lifecycle-Konventionen umgeschrieben.
- Metadaten fuer `Superseded` sind erlaubt, weil ohne diese
  Statusmarkierung keine Superseded-Kette sichtbar waere.
- Neue Lifecycle-Regeln werden in neuen ADRs dokumentiert. Genau
  deshalb ersetzt diese ADR `ADR 0003`, statt dessen
  Entscheidungstext erneut zu erweitern.
- Neue oder beruehrte Dokumente verwenden weiterhin Kennungen als
  primaere Referenz (`ADR 0003`, `ADR 0004`, `ADR 0006`,
  `GG-AR-OPEN-*`), nicht positionsabhaengige Abschnittsverweise.

---

## 7. Konsequenzen

- `ADR 0003` wird auf `Superseded` gesetzt und verweist auf diese ADR.
- Kuenftige Lifecycle-Fragen referenzieren `ADR 0006`, nicht `ADR 0003`.
- Laufende `Provisional`-ADRs wie `ADR 0002` und `ADR 0005` behalten
  ihren Status-Pfad; bei spaeterer Acceptance oder Ablehnung gelten
  die Regeln dieser ADR.
- Operative Spike-Artefakte muessen ihren Status klar ausweisen und
  bei `Accepted`, `Rejected`, `Withdrawn` oder `Superseded`
  nachgezogen werden.

---

## 8. Nicht Gegenstand dieser ADR

- Review-Freigabeprozess fuer Statuswechsel.
- Automatisiertes Linting von ADR-Headern.
- Inhaltliche Entscheidung ueber den Sprach-/Build-Stack.
