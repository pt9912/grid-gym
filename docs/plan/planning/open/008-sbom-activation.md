# 008 — SBOM scharfschalten

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-15
**Quelle:** [`Makefile`](../../../../Makefile) Target `sbom`
(Kommentar bei `SYFT_IMAGE`); `GG-CICD-007` (Artefakt-Veroeffentlichung)

---

## Trigger

`make sbom` ist heute eingerichtet, aber als kommentierte
Folgearbeit markiert:

> SBOM-Erzeugung als Release-Asset. Wird in spaeterer Welle scharf
> geschaltet, sobald `GG-CICD-007` (Artefakt-Veroeffentlichung)
> aktiv wird.

Aktivierung ergibt erst Sinn, wenn `GG-CICD-007` (Release-Pipeline
mit Artefakt-Publikation) ein konkretes Release-Vehikel hat.

## Erwartete Lieferung

- `make sbom VERSION=v0.1.0` laeuft in CI als Pflicht-Schritt fuer
  Release-Tags und produziert `artifacts/sbom-vN.cdx.json`.
- Release-Workflow lade das SBOM-Asset zur Release-Veroeffentlichung
  hoch.
- Pruefung: SBOM enthaelt alle Runtime-Dependencies aus `uv.lock`
  und das Container-Image.

## Aktivierungs-Kriterium

Mit der ersten Release-Veroeffentlichung (Tag, GitHub Release oder
Container-Registry-Push).

## Wandert nach

- `next/`, sobald Release-Pipeline skizziert ist,
- `in-progress/`, wenn aktiver Release-Slice geplant ist.

## M5-Welle-0-C2-Triage 2026-06-01

Verbleibt in `open/`. M5-Closure liefert keine produktive
Release-Pipeline (M5 ist UI + Demo, kein Release-Workflow).
M5-Welle-7-Closure koennte allerdings SBOM-Aktivierung
mitnehmen falls ein Demo-Release-Tag erwogen wird —
optional, kein DoD-Pflicht-Punkt. Realistischer
Aktivierungs-Pfad bleibt M6 (`GG-CICD-007` Release-
Workflow als Pflicht-Lieferung).
