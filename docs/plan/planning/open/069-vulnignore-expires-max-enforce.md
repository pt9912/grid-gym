# 069 — render_trivyignore.py: +90-Tage-`expires`-Maximum erzwingen

**Status:** Open — Härtungs-Befund aus dem Session-Review (2026-07-11)
**Quelle:** Security-Review des vulnignore-Deferrals ([`065`](065-otel-collector-go-1265-cve.md)) —
adversarialer Befund N3(a).

---

## Befund

[`ADR 0044`](../../adr/0044-generated-trivyignore-permit.md) §2.2 definiert
`expires` als **max. +90 Tage**. `tools/render_trivyignore.py` erzwingt in
`_validate_entry` aber nur die **Untergrenze** (`expires >= heute`, sonst Exit 1)
— **nicht** die Obergrenze. Ein künftiger Eintrag könnte `expires` beliebig weit
in die Zukunft setzen; der Renderer würde ihn klaglos ausgeben. Der `+90`-Cap ist
derzeit reine Human-/ADR-Disziplin. (Der aktuelle CVE-2026-39822-Eintrag liegt
exakt am Cap — hier kein Defekt, nur fehlende Durchsetzung.)

## Erwartete Lieferung

- `_validate_entry` erzwingt zusätzlich `expires <= referenz + 90 Tage` (Exit 1
  sonst). **Design-Frage:** woher kommt die Referenz? Der Eintrag kennt heute nur
  `expires`. Optionen: (a) neues Pflichtfeld `created: YYYY-MM-DD` je Eintrag
  (dann `created <= expires <= created+90`), oder (b) git-blame/-log-Anker der
  Eintrags-Zeile. **(a)** ist hermetisch und schema-treu (bevorzugt).
- Schema-Doku in `vulnignore.yaml` + [`ADR 0044`](../../adr/0044-generated-trivyignore-permit.md)
  §2.2 nachziehen; Test in `tools/`-Test-Suite.

## Aktivierungs-Kriterium

Nächster Security-/Tooling-Slice; spätestens wenn ein zweiter vulnignore-Eintrag
dazukommt (dann ist die fehlende Cap-Durchsetzung real riskant).

## Wandert nach

`done/`, sobald der Renderer den +90-Tage-Cap fail-closed erzwingt und ein Test
das absichert.
