# ADR 0011 — Schaerfung durch parallele ADR ohne Supersedes

**Status:** Accepted — kein Validierungs-Spike erforderlich.
Direkter `Proposed → Accepted`-Sprung per `ADR 0006 §2`-Klausel
(„ADR ohne Validierungsbedarf").
**Datum:** 2026-05-17
**Status geaendert am:** 2026-05-17 — `Proposed → Accepted`.
**Bezug:**
[`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
§3 (Aenderungsregeln, schaerft diese ADR als reine Erweiterung).
Bisherige implizite Anwender:
[`ADR 0008`](0008-enum-as-domain-frozen-form.md) (erweitert
ADR 0002 §A-1), [`ADR 0009`](0009-randomport-snapshot-schema-rng-version.md)
(erweitert ADR 0007 §5.2),
[`ADR 0010`](0010-randomport-snapshot-as-mapping.md) (erweitert
ADR 0007 §5.1 + ADR 0009).

---

## 1. Kontext

`ADR 0006 §3` regelt Aenderungen an akzeptierten ADRs:

> Nach `Accepted` ist der Entscheidungstext immutable. Fachliche
> Aenderungen kommen als neue ADR, die die bestehende ADR
> abloest.
>
> Zulaessig bleiben nur Metadaten-Aenderungen an der alten ADR:
> Statuswechsel auf `Superseded`, `Status geaendert am`,
> `Superseded by`, ein kurzer Hinweis im Header, dass die ADR
> historisch ist.

Der Wortlaut beschreibt **Ablösung** (Supersedes-Form) als
einzigen explizit genannten Aenderungspfad. Im laufenden M1-
Slice (Welle 1..4) sind aber drei ADRs (`0008`, `0009`, `0010`)
als **reine Erweiterungen** angelegt — sie schaerfen einen Teil
einer aelteren `Accepted`-ADR (z. B. eine Tabellenzeile, ein
Code-Snippet im §5.2), ohne die alte ADR komplett zu ueberschreiben.
Das ist ein semantisch sauberes Muster, aber `ADR 0006 §3` nennt
es nicht namentlich.

Der externe Welle-4-Review hat das als **Doku-Drift-Risiko**
markiert: ADR 0010 zitiert „ADR 0006 §3 (Erweiterung ohne
Supersedes)", aber diese Wendung steht nirgends in §3.

Diese ADR schliesst die Luecke explizit.

---

## 2. Entscheidung

Neben dem in `ADR 0006 §3` beschriebenen **Supersedes-Pfad** ist
eine zweite ADR-Folge-Form zulaessig: die **Schaerfung durch
parallele ADR ohne Supersedes**.

Eine Schaerfungs-ADR `B` zu einer akzeptierten ADR `A`:

1. Wird selbst als regulaere ADR mit eigenem Header geschrieben
   (`Status`, `Datum`, `Status geaendert am`, `Bezug:` mit
   Verweis auf `A`).
2. **Schaerft, schraenkt ein oder ergaenzt** einen klar
   abgegrenzten Teil von `A` (eine Tabellenzeile, ein Code-
   Snippet, eine Protocol-Methode), **ohne** den uebrigen
   `A`-Entscheidungstext zu beruehren.
3. **Setzt `A` NICHT auf `Superseded`** — `A` bleibt `Accepted`
   und in Kraft. `B` liegt strukturell neben `A`, beide gelten
   gemeinsam.
4. **Trägt im Header keinen `Superseded by`-Verweis** an `A`,
   sondern `B`-Bezug-Zeile referenziert `A`.
5. Wird im ADR-Index (`docs/plan/adr/README.md`) in der
   „Schaerfungen / Folge-ADRs"-Spalte der `A`-Zeile eingetragen.

Wenn `B` `A` **vollstaendig** ersetzt oder einen Kern-Teil
**zurueckdreht**, ist Supersedes per `ADR 0006 §3` weiterhin
Pflicht — Schaerfung ist nicht das Universal-Vehikel fuer
fachliche Aenderungen, sondern explizit fuer **additive**
Erweiterungen.

---

## 3. Begruendung

- **Etablierte Praxis sichtbar machen:** Drei ADRs (`0008`,
  `0009`, `0010`) nutzen die Form bereits. ADR 0011 codifiziert,
  was im Repo passiert ist.
- **Audit-Pfad sauber:** Reviewer und kuenftige Architekten
  sehen im ADR-Index sofort, welche Stellen einer alten ADR
  durch eine Folge-ADR geschaerft wurden, ohne dass die alte
  ADR als „Superseded" gilt (was sie nicht ist — sie bleibt
  in Kraft).
- **Audrueckliche Untermenge:** Supersedes bleibt der richtige
  Pfad fuer (a) komplette Ablösung, (b) Zurueckdrehen einer
  Kernentscheidung, (c) inkompatible Schema-Aenderung. Schaerfung
  ist explizit nur fuer additive Faelle.
- **Selbst-bootstrap:** Diese ADR ist selbst eine Schaerfung
  ohne Supersedes von `ADR 0006 §3`. Das ist beabsichtigt — der
  Bootstrap macht die Regel anwendbar auf sich selbst.

---

## 4. Reichweite

- `ADR 0006 §3` bleibt textlich unveraendert (Accepted-
  Immutability per `ADR 0006 §3` selbst).
- ADR 0011 liegt parallel und wird in `ADR 0006`-Zeile des
  ADR-Index als „Schaerfung" eingetragen.
- Bestehende Schaerfungs-ADRs (`0008`, `0009`, `0010`) bekommen
  nachtraeglich `ADR 0011` als Bezug-Anker — der Index-Eintrag
  zeigt die Verwandtschaft.

---

## 5. Operative Artefakte

- `docs/plan/adr/README.md` ADR-Index: ADR-0006-Zeile traegt
  „Schaerfung-ohne-Supersedes-Pattern via ADR 0011".
- Kuenftige Schaerfungs-ADRs zitieren in ihrer `Bezug:`-Zeile
  zusaetzlich zu `ADR 0006 §3` auch `ADR 0011` als
  Erlaubnis-Anker.

---

## 6. Konsequenzen

- **Positiv:** Doku-Drift-Risiko aus Welle-4-Review geschlossen.
  ADR-Lifecycle-Mechanik ist vollstaendig dokumentiert.
- **Positiv:** Self-bootstrap demonstriert die Regel direkt.
- **Neutral:** Eine ADR mehr im Index.
- **Neutral:** Aeltere Schaerfungs-ADRs (0008/0009/0010) bleiben
  textlich unveraendert; ihre `Bezug:`-Zeilen werden nicht
  nachtraeglich editiert (per ADR 0006 §3 + ADR 0011 §4 —
  Accepted-Text-Immutability gilt fuer beide). Der ADR-Index
  als Lese-Schicht zeigt die Verwandtschaft.

---

## 7. Nicht Gegenstand dieser ADR

- Reformulierung von `ADR 0006 §3` selbst — bleibt textlich
  unveraendert.
- Migration bestehender Schaerfungs-ADRs auf einen einheitlichen
  „Schaerfung ohne Supersedes"-Header-Block — wuerde Accepted-
  Texte aendern. Bei Bedarf neue Schaerfungs-ADRs schreiben.
- Policy fuer „wann Schaerfung, wann Supersedes" jenseits des
  „additive vs. ersetzende"-Tests aus §2. Bei Grenzfaellen:
  im Zweifel Supersedes (sicherere Lifecycle-Position).
