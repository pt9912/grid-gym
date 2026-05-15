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
