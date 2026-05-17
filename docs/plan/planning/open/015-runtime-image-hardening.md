# 015 — Production-Image-Hardening (M2/M6)

**Status:** Open — Trigger-Watch. Welle-6d-Erbe.
**Datum:** 2026-05-17
**Quelle:** M1 Welle 6d (Commit `b5243fe`). Drei pragmatische
Runtime-Fixes haben `make fullbuild` gruen bekommen — die
sauberen Loesungen brauchen einen eigenen Slice.
**Verlinkt:** [`Dockerfile`](../../../../Dockerfile)
`runtime`-Stage, [`deploy/compose.yml`](../../../../deploy/compose.yml),
M1-Slice-Plan
[`M1-tick-loop-spine.md`](../in-progress/M1-tick-loop-spine.md)
§3 Welle 6d.

---

## Trigger

Welle 6d hatte drei Runtime-Hacks noetig, die `make fullbuild`
bei der ersten Iteration brachen:

1. **venv-shebangs zeigen auf den Build-Pfad** `/src/.venv/bin/
   python`. Der `runtime`-Stage kopiert das venv nach
   `/app/.venv/`, aber die `.pth`-Editable-Install-Datei und die
   Binary-Shebangs (`uvicorn`, `alembic`, etc.) zeigen weiter
   auf `/src/`. `python -m <modul>` umgeht das, aber:
   - direkter `uvicorn`-Aufruf in `deploy/compose.yml` failed
     mit `exec /app/.venv/bin/uvicorn: no such file or directory`.
   - `alembic upgrade head` aus dem Runtime-Image waere genauso
     betroffen, sobald ein Migrations-Schritt produktiv laeuft.
2. **`PYTHONPATH=/app/src` als Workaround** fuer den editable-
   install. Das ist eine ENV-Setzung, kein echter Install — bei
   `uv sync --no-editable` haette uv die wheels direkt installiert
   und der Pfad waere nicht noetig.
3. **`apt-get upgrade -y`** im Runtime-Stage faengt Base-Image-
   CVEs (libcap2, libsystemd0) ein, aber jedes neue Image braucht
   den Schritt erneut. Ein `python:3.14-slim` mit aktuellem Patch-
   Level oder ein selbst gebautes Base-Image waere idiomatischer.

## Erwartete Lieferung

- **`uv sync --no-editable`** im `build-app`-Stage statt
  editable-Install. Site-packages sind dann direkt unter
  `/src/.venv/lib/.../grid_gym/`, der `PYTHONPATH`-Workaround
  entfaellt. Folgepruefung: `hatch build` + `pip install`-aequivalenter
  Pfad.
- **Shebang-Rewrite oder Pip-Relocate**: nach dem `COPY` ins
  Runtime-Image die shebangs in `.venv/bin/*` auf
  `/app/.venv/bin/python` umstellen. Ein-/Zweizeiler `sed`-Loop
  oder `pip install --target /app/.venv` als Alternative.
  Danach: `uvicorn` und `alembic` als direkte Binaries in
  `deploy/compose.yml`.
- **Base-Image-Patch-Strategie**: entweder
  - eigenes Base-Image (`grid-gym-base:debian-13-patched`), das
    `apt-get upgrade` einmal pro CI-Lauf macht und cacheable
    bleibt, ODER
  - `python:3.14-slim` per
    `--pull always` + regelmaessige `make rebase-base`-Routine.
- **Dockerfile-Doku** im `runtime`-Stage entfernt die
  Welle-7-Closure-Items und ersetzt sie durch eine fixe
  Architektur-Notiz.

## Aktivierungs-Kriterium

Mit M6 (Security/CI-Haertung, Roadmap §3) — spaetestens vor der
ersten produktiven Lastpruefung. Bei drueckendem
Sicherheits-Audit-Befund kann es vorgezogen werden.

## Wandert nach

- `next/`, sobald M6 oder ein Sicherheits-Slice das Pattern
  aktiviert,
- `in-progress/`, wenn der Refactor-Slice geplant ist.
