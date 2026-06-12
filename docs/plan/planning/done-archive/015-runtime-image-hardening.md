# 015 — Production-Image-Hardening (M2/M6)

**Status:** Done — geschlossen 2026-05-18 in M2 Welle 0b
(Commit `ee37f36`). Welle 0b liefert die drei Production-
Image-Refactor-Items (uv-`--no-editable`, Shebang-Rewrite,
direkte Binaries); Option-A (in-image `apt-get upgrade`) bleibt
als gewaehlte Base-Image-Patch-Strategie. Option-B (eigenes
`grid-gym-base:debian-13-patched`) eskaliert auf M6, falls
trivy trotz `apt-get upgrade` + `make rebase-base` Highs/Criticals
weiter meldet.
**Datum:** 2026-05-17 — geoeffnet aus M1 Welle 6d (Commit
`b5243fe`).
**Verlinkt:** [`Dockerfile`](../../../../Dockerfile)
`runtime`-Stage, [`deploy/compose.yml`](../../../../deploy/compose.yml),
M1-Slice-Plan
[`M1-tick-loop-spine.md`](M1-tick-loop-spine.md)
§3 Welle 6d.

---

## Closure-Notiz (M2 Welle 0b, 2026-05-18)

**Lieferung im Repo:**

- `build-app`-Stage faehrt jetzt `uv sync --frozen --no-dev
  --no-editable`: das Projekt wird als Wheel direkt in
  `/src/.venv/lib/.../site-packages/` installiert, nicht mehr
  als editable Link auf `/src/src/`. Der Welle-6d-
  `PYTHONPATH=/app/src`-Workaround im runtime-Stage entfaellt.
- Shebang-Rewrite via `find /app/.venv/bin -type f -exec sed
  -i '1s|^#!/src/\.venv/bin/python|#!/app/.venv/bin/python|'`
  plus `sed -i 's|/src/\.venv|/app/.venv|g' /app/.venv/pyvenv.cfg`.
  `uvicorn` und `alembic` laufen jetzt als direkte Binaries —
  `python -m uvicorn`-Indirection und `entrypoint: []` aus
  `deploy/compose.yml::api` sind weg.
- Dockerfile-`ENTRYPOINT` umgestellt von dem nicht-aufrufbaren
  `python -m grid_gym.adapters.driving.http_api` (kein
  `__main__.py`) auf
  `exec uvicorn grid_gym.adapters.driving.http_api:app --host
  "$GRID_GYM_HOST" --port "$GRID_GYM_PORT"` (shell-form mit
  `exec` fuer Signal-Forwarding; ENV-Vars werden konsumiert,
  siehe Welle-0-Review H-1 in Commit `d490905`).
  `deploy/compose.yml::api` benutzt diesen ENTRYPOINT direkt.
- Neues `make rebase-base`-Target zieht
  `python:$(PYTHON_VERSION)-slim` und das uv-Image explizit aus
  der Registry; refresht den Base-Layer fuer den uv-Cache.

**Bewusst NICHT umgesetzt:**

- `apt-get upgrade -y` im `runtime`-Stage bleibt. Trivy-Lauf in
  Welle-0b zeigt, dass `python:3.14-slim` auf Docker Hub
  Debian-Security-Patches (libcap2 CVE-2026-4878,
  libsystemd0/libudev1 CVE-2026-29111) hinterherlaeuft —
  `make rebase-base` alleine raeumt diese Highs/Criticals nicht
  auf. Welle 0b waehlt deshalb explizit Trigger-015-Option-A
  (in-image-Patching) und dokumentiert das. Wechsel auf
  Trigger-015-Option-B (eigenes
  `grid-gym-base:debian-13-patched`) ist M6 (`GG-CICD`/
  Security-Haertung).
- `entrypoint: []` am `simulation`-Stub-Service in
  `deploy/compose.yml` bleibt — der Stub ist kein Webserver
  und ueberschreibt den Dockerfile-`uvicorn`-ENTRYPOINT bewusst
  mit `sleep infinity` (Welle-6c-Erbe; M2-Welle-6 ersetzt den
  Stub durch den Geraete-TickLoop-Runner). Welle-0b hat
  ausschliesslich den `entrypoint: []`-Override am `api`-Service
  entfernt.

**Abnahme-Belege:**

- `make fullbuild` cache-frei gruen mit M1-Override-Liste +
  `core/serialization`: ci + runtime image + compose smoke
  durchlaufen.
- `make image-audit` gruen (trivy `--ignore-unfixed`, mit
  `apt-get upgrade -y` im runtime-Stage).
- `make runtime`-Compose-Smoke: API-Container startet `uvicorn`
  via Dockerfile-ENTRYPOINT, `/health` antwortet mit
  `{"status":"ok"}`.
- 268 Unit-Tests gruen, keine M1-Tests verloren.

**Erbschaft fuer Folgewellen:**

- M2 Welle 1+ koennen das produktiv gehaertete Runtime-Image
  ohne weitere Compose-Overrides nutzen.
- M6-Folge-Trigger (Option B aus Trigger 015): eigenes
  `grid-gym-base:debian-13-patched`-Image, das `apt-get upgrade`
  einmal pro CI-Lauf macht und cacheable bleibt — eskaliert,
  wenn trivy persistente HIGHs/CRITICALs trotz `apt-get upgrade`
  zeigt.

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
