# ADR 0003 — ADR-Lifecycle (Ergaenzung zu ADR 0001)

**Status:** Accepted
**Datum:** 2026-05-14
**Letzte inhaltliche Aenderung:** 2026-05-14 — Review-Fix:
Metadaten-Ausnahme fuer `Superseded`, Artefakt-Scope, Header-Schema,
Abgrenzung `Rejected`/`Withdrawn`.
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
Build-Stack) startete als Entscheidungsvorschlag und benoetigt einen
Pre-Acceptance-Spike (Spike-0), bevor die Wahl verbindlich wird.
Das ist eine vorgesehene, strukturierte Entscheidungsfindung —
nicht eine „laufende Diskussion". ADR 0001 hatte fuer diesen Fall
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
| `Rejected`    | ADR wird nach Review, Spike oder Owner-Entscheid bewusst nicht uebernommen. Die Negativentscheidung und ihre Begruendung bleiben dauerhaft in der ADR. | Normative Schluss-Verweise werden entfernt; Folge-ADRs duerfen die Ablehnungsgruende referenzieren.                              |
| `Superseded`  | ADR war akzeptiert, ist aber durch eine spaetere ADR abgeloest. Die alte ADR erhaelt einen Nachfolger-Verweis.       | Historisch: bleibt erhalten, aber bindet nicht mehr; abhaengige Dokumente verweisen auf die Nachfolge-ADR.                       |
| `Withdrawn`   | ADR-Autor zieht den Vorschlag vor Beschluss zurueck. Spike (falls vorhanden) wird beendet; es liegt keine Negativentscheidung vor. | Laufende Hinweis-Verweise werden entfernt; der Vorschlag bleibt historisch sichtbar, bindet aber nicht.                          |

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

### 2.1 Operative Artefakte vor `Accepted`

Die Status-Wirkung oben gilt fuer normative Dokumente
(`spec/lastenheft.md`, `spec/architecture.md`) und fuer das
Schliessen von `GG-AR-OPEN-*`-Punkten. Operative Artefakte
ausserhalb dieser Spezifikationsdokumente duerfen eine ADR vor
`Accepted` nur unter klarer Kennzeichnung umsetzen:

- Bei `Proposed` sind Code, `Makefile`, `Dockerfile`, CI-Jobs oder
  Tool-Konfiguration nur als Spike-/Prototyp-Artefakte erlaubt. Sie
  MUESSEN im Kommentar oder in der Beschreibung als
  `Spike`/`Prototyp` mit ADR-Verweis markiert sein und duerfen keine
  geschlossene Architekturentscheidung behaupten.
- Bei `Provisional` duerfen solche Artefakte den validierten Pfad des
  Spike-Vertrags bilden. Sie bleiben vorlaeufig und MUESSEN bei
  `Rejected` oder `Withdrawn` entfernt, archiviert oder auf den
  Folgepfad umgestellt werden.
- Erst bei `Accepted` werden operative Artefakte als verbindliche
  Projektkonvention behandelt und duerfen ohne Spike-Kennzeichnung
  auf die ADR als beschlossenen Stack, Prozess oder Vertrag
  verweisen.

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
  strikt fuer den Entscheidungstext: jede fachliche Aenderung kommt
  als neue ADR, die die vorhandene ADR abloest (`Superseded`).
  Zulassig bleiben ausschliesslich Metadaten-Aenderungen an der alten
  ADR: Statuswechsel auf `Superseded`, Datum des Statuswechsels,
  Nachfolger-Verweis und ein kurzer Superseded-Hinweis. Der
  urspruengliche Entscheidungstext bleibt unveraendert.

---

## 4. Pflege-Regeln

- Jede ADR fuehrt im Header den aktuellen Status. Header-Felder sind:
  - `Status`: aktueller Lifecycle-Status, optional mit kurzem
    Klartext-Zusatz.
  - `Datum`: Erstellungsdatum der ADR.
  - `Letzte inhaltliche Aenderung`: Pflicht, sobald eine ADR vor
    `Accepted` inhaltlich geschaerft wurde oder eine akzeptierte ADR
    ausnahmsweise durch eine Prozesskorrektur aktualisiert wird.
  - `Status geaendert am`: Pflicht bei jedem Statuswechsel nach der
    Erstellung.
  - `Superseded by`: Pflicht bei Status `Superseded`.
- Der Status ist das erste Aenderbare; jeder Statuswechsel wird durch
  `Status geaendert am` und, falls noetig, einen kurzen Hinweis im
  Header begleitet.
- Eine ADR mit `Provisional`-Status MUSS einen
  Validierungs-Spike-Vertrag enthalten (Akzeptanzkriterien, Dauer,
  Erfolgs-/Misserfolgs-Definition).
- `architecture.md §19` und Lastenheft-Verweise nutzen folgende
  Formelhilfe:
  - bei `Proposed`: kein Eintrag, hoechstens „Entwurf in ADR XXXX".
  - bei `Provisional`: „Vorgeschlagen, Spike laufend, siehe ADR XXXX".
  - bei `Accepted`: „Geschlossen mit ADR XXXX".
  - bei `Rejected`: schliessenden Eintrag entfernen; falls die
    Ablehnung fuer Folgeentscheidungen relevant ist, darf ein
    historischer Hinweis auf die Ablehnungsgruende bleiben.
  - bei `Withdrawn`: laufenden Hinweis entfernen.
  - bei `Superseded`: Verweis auf Nachfolge-ADR.

---

## 5. Konsequenzen

- ADR 0002 nutzt den hier definierten Status-Pfad. Seine
  Pre-Acceptance-Spike-Phase ist mit dieser Lifecycle-Definition
  formal kompatibel.
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
