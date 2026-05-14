# ADR 0003 — ADR-Lifecycle (Ergaenzung zu ADR 0001)

**Status:** Superseded
**Datum:** 2026-05-14
**Status geaendert am:** 2026-05-14 — abgeloest durch ADR 0006.
**Superseded by:** [ADR 0006](0006-adr-lifecycle-superseding-and-process-corrections.md)
**Bezug:** [ADR 0001](0001-documentation-and-planning-structure.md),
[Lastenheft](../../../spec/lastenheft.md),
[Architektur](../../../spec/architecture.md)
**Aenderungstyp:** Ergaenzung — `ADR 0001` bleibt inhaltlich
gueltig; diese ADR fuegt einen Lebenszyklus fuer ADR-Statuswerte
hinzu, der in ADR 0001 nicht spezifiziert war.

---

## 1. Kontext

ADR 0001 legt die Dokumentations- und Planungsstruktur fest und
sagt (`§3` und `§4`):

> ADRs dokumentieren **Entscheidungen**, nicht laufende
> Diskussionen.
> ADRs werden nach Erstellung nicht inhaltlich ueberschrieben;
> spaetere Aenderungen kommen als neue ADR.

Daraus folgt ein impliziter Konflikt: ADR 0002 (Sprach- und
Build-Stack) traegt den Status `Proposed` und benoetigt einen
Pre-Acceptance-Spike (Spike-0), bevor die Wahl verbindlich wird.
Das ist eine vorgesehene, strukturierte Entscheidungsfindung —
nicht eine „laufende Diskussion". ADR 0001 hat fuer diesen Fall
keine eigene Lifecycle-Stufe.

Diese ADR schliesst die Luecke, ohne ADR 0001 inhaltlich
umzuschreiben. Sie fuehrt einen expliziten ADR-Lifecycle ein und
klaert, was „Entscheidung" in ADR 0001 fuer welchen Status
bedeutet.

---

## 2. Entscheidung

ADRs in `docs/plan/adr/` durchlaufen den folgenden Lebenszyklus:

| Status        | Bedeutung                                                                                                          | Wirkung auf abhaengige Dokumente                                                                                                  |
| ------------- | ------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| `Proposed`    | Empfehlung formuliert, **kein** Beschluss. Optionen und Bewertungskriterien sind dokumentiert.                       | KEINE. Lastenheft und `architecture.md` duerfen NICHT auf die Empfehlung verweisen, ausser als Hinweis auf den laufenden Vorschlag. |
| `Provisional` | Projektowner traegt die Empfehlung mit; ein begrenzter Validierungs-Spike laeuft, dessen Vertrag in der ADR steht.   | Eingeschraenkt: abhaengige Dokumente duerfen auf die ADR verweisen, aber keine `GG-AR-OPEN-*`/Lastenheft-Anforderung als geschlossen markieren. |
| `Accepted`    | Beschluss steht. Falls die ADR einen Validierungs-Spike enthielt, ist dieser nachweisbar gruen abgeschlossen.        | Voll: abhaengige Dokumente werden gepflegt (z. B. `architecture.md §19` schliesst den referenzierten `GG-AR-OPEN-*`).             |
| `Rejected`    | ADR wird nicht uebernommen. Begruendung in der ADR selbst.                                                          | KEINE. Verweise aus abhaengigen Dokumenten werden entfernt.                                                                       |
| `Superseded`  | ADR ist durch eine spaetere ADR abgeloest. Verweis auf Nachfolger in der ADR.                                       | Historisch: bleibt erhalten, aber bindet nicht mehr.                                                                              |
| `Withdrawn`   | ADR-Autor zieht den Vorschlag vor Beschluss zurueck. Spike (falls vorhanden) wird beendet.                          | KEINE.                                                                                                                            |

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

## 3. Verhaeltnis zu ADR 0001

- ADR 0001 §3 („ADRs dokumentieren **Entscheidungen**, nicht
  laufende Diskussionen") wird so gelesen: **eine ADR im Status
  `Proposed` dokumentiert einen Entscheidungsvorschlag mit
  vollstaendigem Bewertungsrahmen und nimmt den Beschluss vorweg,
  ohne ihn zu treffen.** Sie ist keine offene Diskussion, sondern
  ein vorbereiteter Beschluss. Laufende Diskussionen, die noch
  keinen Vorschlag erlauben, gehoeren weiterhin nach
  `docs/plan/planning/open/`, nicht in `adr/`.
- ADR 0001 §4 („ADRs werden nach Erstellung nicht inhaltlich
  ueberschrieben") gilt fuer **akzeptierte** Inhalte. Der
  Status-Wechsel `Proposed → Provisional → Accepted` ist kein
  Inhaltsuebergriff. Inhaltliche Verschaerfungen oder Korrekturen
  vor `Accepted` (z. B. ein verschaerfter Auflagenvertrag in einer
  Review-Runde) sind zulaessig; sie werden im Datums- und
  Status-Header der ADR durch einen kurzen „Letzte inhaltliche
  Aenderung"-Eintrag dokumentiert.
- Nach `Accepted` gilt das Aenderungsverbot aus ADR 0001 §4
  strikt: jede Aenderung kommt als neue ADR, die die vorhandene
  ablöst (`Superseded`).

---

## 4. Pflege-Regeln

- Jede ADR fuehrt im Frontmatter den aktuellen Status. Der Status
  ist das erste Aenderbare; jeder Statuswechsel wird durch einen
  kurzen Datums-Vermerk in der ADR begleitet.
- Eine ADR mit `Provisional`-Status MUSS einen
  Validierungs-Spike-Vertrag enthalten (Akzeptanzkriterien, Dauer,
  Erfolgs-/Misserfolgs-Definition).
- `architecture.md §19` und Lastenheft-Verweise nutzen folgende
  Formelhilfe:
  - bei `Proposed`: kein Eintrag, hoechstens „Entwurf in ADR XXXX".
  - bei `Provisional`: „Vorgeschlagen, Spike laufend, siehe ADR XXXX".
  - bei `Accepted`: „Geschlossen mit ADR XXXX".
  - bei `Rejected`/`Withdrawn`: Eintrag entfernen.
  - bei `Superseded`: Verweis auf Nachfolge-ADR.

---

## 5. Konsequenzen

- ADR 0002 bleibt `Proposed`. Sein Status-Pfad ist mit dieser
  Lifecycle-Definition jetzt formal kompatibel.
- ADR 0001 bleibt inhaltlich unveraendert; diese ADR ist
  Ergaenzung, nicht Ablöser.
- Kuenftige ADRs verwenden ausschliesslich die hier definierten
  Statuswerte.

---

## 6. Nicht Gegenstand dieser ADR

- Versionierung von ADR-Dateien (z. B. semantische Versionen) —
  ADRs werden ueber `Superseded`-Ketten versioniert, nicht ueber
  Dateinamen-Suffixe.
- Review-Prozess vor Statuswechsel — eigener Prozess-ADR bei
  Bedarf.
