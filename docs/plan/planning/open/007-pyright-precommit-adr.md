# 007 — ADR fuer pyright als Pre-Commit-Hook

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-15
**Quelle:** [`ADR 0005`](../../adr/0005-type-check-gate.md) §6

---

## Trigger

[`ADR 0005`](../../adr/0005-type-check-gate.md) nennt:

> ADR fuer Pyright als optionales Pre-Commit-Hook fuer
> Entwickler-Maschinen (Trigger-basiert, sobald Editor-Parity-Druck
> entsteht).

Hintergrund: Pylance (pyright-basiert) ist im Editor restriktiver
als `mypy --strict`. Ein Pre-Commit-Hook auf pyright wuerde
Editor- und Lokal-Diagnose synchronisieren, ohne das CI-Gate zu
veraendern.

## Erwartete Lieferung

ADR-Skizze mit:

- Pre-Commit-Konfiguration (`.pre-commit-config.yaml`),
- pyright-Konfiguration in `pyproject.toml`,
- Verhaeltnis zu CI (`mypy --strict` bleibt das Gate, pyright nur
  Pre-Commit auf Entwickler-Maschinen),
- Opt-In oder Opt-Out fuer Entwickler.

## Aktivierungs-Kriterium

Sobald Editor-Parity-Druck auftritt: Beispiele aus dem Repository,
in denen Pylance lokal rot meldet, mypy in CI aber gruen — und das
zu wiederholten Debugging-Runden fuehrt.

## Wandert nach

- `next/`, sobald Editor-Parity-Druck dokumentiert ist,
- `in-progress/`, wenn ADR-Schreibarbeit beginnt.
