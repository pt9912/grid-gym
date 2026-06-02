# syntax=docker/dockerfile:1.7
#
# grid-gym multi-stage Dockerfile.
#
# Verbindlicher Stack gemaess ADR 0002 (Accepted 2026-05-15) und
# ADR 0005 (Accepted 2026-05-15). Stages implementieren die A-1-
# Pflicht-Gates aus ADR 0002 und das Type-Check-Gate aus ADR 0005:
# Lint, Format, Typecheck, Architektur-Imports, Architektur-Custom
# (AST), Tests, Coverage-Gate, Runtime. Jeder Stage ist ein
# eigenstaendiges Build-Ziel und wird vom Makefile per `--target`
# einzeln gebaut. Aggregierte CI-Lauefe ueber `make gates` (Spike-0-
# Abschluss-Gate) bzw. `make ci` / `make fullbuild` (M1-Abnahme).
#
# Bezug:
# - GG-AR-OPEN-001 / ADR 0002 (Sprach-Stack: Python 3.13+ Floor,
#   3.14 Referenz-Runtime, uv-basiert).
# - GG-CICD-001/002/003/005, GG-QG-001/002 (Build, Tests, Quality
#   Gates).
# - GG-DEPLOY-001/002/003/006/011 (Container, offline-faehig, Linux,
#   Healthcheck).
# - GG-ARCHTEST-001..005 (Architekturtests als Pflicht-Gate).

ARG PYTHON_VERSION=3.14
ARG UV_VERSION=0.5.31
ARG COVERAGE_THRESHOLD=90
ARG COVERAGE_BRANCH_THRESHOLD=85
ARG CRITICAL_COVERAGE_THRESHOLD=90

# ---------------------------------------------------------------------------
# base: Schlanke Python-Basis mit uv und gemeinsamen ENV-Variablen.
# uv wird per offiziellem Distroless-Image bezogen und ueber COPY in die
# Basis kopiert (vermeidet curl|sh in der Build-Kette).
# ---------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-binary

FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1
COPY --from=uv-binary /uv /usr/local/bin/uv
WORKDIR /src

# ---------------------------------------------------------------------------
# deps: Aufloesung der Abhaengigkeiten aus uv.lock (lockfile-first).
# `uv sync --frozen --no-install-project` baut nur das .venv mit
# Abhaengigkeiten — Projektcode kommt erst in spaeteren Stages.
# `--frozen` bricht ab, sobald uv.lock und pyproject.toml driften
# (Supply-Chain-Defense, analog `--locked-mode` bei NuGet in bess-ems).
# ---------------------------------------------------------------------------
FROM base AS deps
COPY pyproject.toml uv.lock .python-version ./
# M4-Welle-5b — `--extra iec61850` zieht `pyiec61850-ng` (GPLv3,
# optional Extra; ADR 0035 Decision I-f). CI/Tests muessen die
# Library explizit installieren, weil der Default-Install MIT-
# sauber bleibt (kein automatisches Pull von GPL-Dependencies).
RUN uv sync --frozen --no-install-project --all-groups --extra iec61850

# ---------------------------------------------------------------------------
# source: Projektcode dazu, dann editable-install via `uv sync` ohne
# Lockfile-Auflösung. Dieser Stage ist die gemeinsame Basis fuer alle
# Lint-/Test-Gates.
# ---------------------------------------------------------------------------
FROM deps AS source
COPY src/ src/
COPY tests/ tests/
COPY tools/ tools/
COPY spec/ spec/
# `docs/` wird vom `tools/check_refs.py`-Markdown-Link-Validator
# (Welle-7-Audit-Erbe, Trigger 002) gebraucht — er aufloest
# relative Pfade zwischen spec/ und docs/. `deploy/`, `Makefile`,
# `Dockerfile` und `CHANGELOG.md` werden ebenfalls per Markdown-
# Ref aus `docs/` referenziert (Slice-Plan + Trigger-Notes); die
# `docs-check`-Stage braucht sie im Build-Kontext, damit
# relative-Pfad-Aufloesung gegen reale Targets prueft. `AGENTS.md`
# und `harness/` gehoeren seit der Harness-Schaerfung ebenfalls zum
# docs-check-Scope, weil sie kanonische Quellen verlinken.
COPY docs/ docs/
COPY harness/ harness/
COPY deploy/ deploy/
COPY .github/workflows/ .github/workflows/
COPY Makefile Dockerfile CHANGELOG.md ./
COPY AGENTS.md ./
# `alembic.ini` zeigt auf das Postgres-Adapter-Migrations-
# Verzeichnis (`src/grid_gym/adapters/driven/persistence_postgres/
# migrations`) und wird vom Integration-Test-Runner programmatisch
# geladen (M1 Welle 6c).
COPY alembic.ini ./
# LICENSE und README.md sind in pyproject.toml ([project].license,
# [project].readme) referenziert — hatchling braucht beide fuer den
# editable Install im naechsten `uv sync`.
COPY LICENSE README.md README.de.md CONTRIBUTING.md ./
RUN uv sync --frozen --all-groups --extra iec61850

# ---------------------------------------------------------------------------
# lint: ruff check mit A-1-Regelgruppen (BLE, TRY, DTZ, S, TID, B904 +
# flake8-tidy-imports.banned-api / banned-module-level-imports).
# Deckt AC-NO-TIME (DTZ), AC-NO-RAND (TID), AC-TYPED-ERRORS (BLE/TRY/
# B904), Security-Subset (S). Per-File-Ignores in pyproject.toml.
# ---------------------------------------------------------------------------
FROM source AS lint
RUN uv run ruff check --no-cache .

# ---------------------------------------------------------------------------
# format-check: ruff format --check (kein Auto-Fix in CI).
# ---------------------------------------------------------------------------
FROM source AS format-check
RUN uv run ruff format --check .

# ---------------------------------------------------------------------------
# typecheck: mypy --strict (ADR 0005).
# Deckt GG-PRINC-004 (LSP via Variance), GG-PRINC-005 (ISP via Protocol-
# Konformitaet), GG-QG-005 (Static-Analysis-Gate). Konfiguration in
# pyproject.toml unter [tool.mypy] mit `strict = true` plus erweiterten
# error codes. Wird zwischen format-check und arch-check im Aggregator
# `gates` eingehaengt.
#
# Pfade kommen ausschliesslich aus der `files`-Direktive in
# [tool.mypy] (Single-Source-of-Truth fuer den Scope-Vertrag, ADR 0005
# §5.1). Kommandozeilen-Pfade wuerden die `files`-Direktive
# ueberlagern und sind deshalb hier bewusst nicht gesetzt.
# ---------------------------------------------------------------------------
FROM source AS typecheck
RUN uv run mypy --config-file pyproject.toml

# ---------------------------------------------------------------------------
# arch-check-imports: import-linter mit den Layer-/Forbidden-Contracts
# aus A-1. Deckt AC-CORE-NO-ADAPTERS, AC-CORE-NO-DRIVING, AC-PORTS-NO-OUT,
# AC-PORTS-NO-FW, AC-ADAPTER-PURE, AC-NO-FW, AC-NO-IO-MOD.
# Konfiguration in pyproject.toml unter [tool.importlinter].
# ---------------------------------------------------------------------------
FROM source AS arch-check-imports
RUN uv run lint-imports

# ---------------------------------------------------------------------------
# arch-check-custom: tools/arch_check.py (AST + grimp-SCC) deckt
# AC-NO-CYCLES, AC-NO-TIME (Aufruf-Site), AC-NO-RAND (Aufruf-Site),
# AC-NO-JSON, AC-DOMAIN-FROZEN, AC-NO-GOD-UTILS, AC-TYPED-ERRORS
# (Aufruf-Site / Vererbungs-Check), AC-ADAPTER-LIGHTWEIGHT. Whitelists
# liest das Skript aus [tool.grid_gym.arch_check] in pyproject.toml.
# ---------------------------------------------------------------------------
FROM source AS arch-check-custom
RUN uv run python tools/arch_check.py

# ---------------------------------------------------------------------------
# arch-check: Aggregator-Stage. Erst Imports, dann Custom — beide
# muessen gruen sein, sonst bricht der Stage.
# ---------------------------------------------------------------------------
FROM source AS arch-check
RUN uv run lint-imports \
 && uv run python tools/arch_check.py

# ---------------------------------------------------------------------------
# docs-check: Markdown-Link-Validator (Trigger 002 Welle 7).
# Scant docs/, spec/, harness/ und AGENTS.md nach relativen
# `[text](path)`-Links und meldet nicht aufloesbare Pfade. Faengt
# Audit-Lecks wie post-Move-Drift (z. B. `in-progress/ → done/`)
# automatisiert ab.
# ---------------------------------------------------------------------------
FROM source AS docs-check
RUN uv run python tools/check_refs.py

# ---------------------------------------------------------------------------
# spdx-check: tools/check_spdx.py — SPDX-License-Identifier-Lint fuer die
# IEC-61850-GPL-Boundary (Welle-5b Decision I-f, ADR 0035; Welle-6b C1).
# Verifiziert, dass alle Dateien unter protocol_iec61850/ + tests/.../iec61850/
# + tests/integration/test_iec61850_*.py + tests/integration/fixtures/iec61850/
# einen `SPDX-License-Identifier: GPL-3.0-only`-Header tragen.
# Lint-Failure bei fehlendem oder falschem Identifier; in `make gates`
# integriert.
# ---------------------------------------------------------------------------
FROM source AS spdx-check
RUN uv run python tools/check_spdx.py

# ---------------------------------------------------------------------------
# noqa-check: tools/check_noqa.py — `# noqa`-Marker-Reporter (Slice 027).
# Standardmodus: Report mit Exit-Code 0. Vor dem Plan-§4-Scharfschalten
# nuetzlich fuer einen aktuellen Bestands-Lauf.
# ---------------------------------------------------------------------------
FROM source AS noqa-check
RUN uv run python tools/check_noqa.py

# ---------------------------------------------------------------------------
# noqa-gate: tools/check_noqa.py --fail-on-noqa — Hard-Gate (Slice 027).
# Per `--build-arg NOQA_FILES="..."` paketweise auf einen Scope eingrenzbar;
# Default (leerer ARG) prueft das gesamte Repo (`src tests tools`).
# Plan §3.0: paketweise Hard-Stufe nach jedem Paket; Plan §4: Final-Scharf-
# schaltung in `make gates` nach Slice-Abschluss.
#
# `$NOQA_FILES` ist absichtlich unquoted — Shell-Word-Splitting laesst
# uns mehrere Pfade per Whitespace getrennt uebergeben
# (`NOQA_FILES="src/a.py src/b.py"`). Pfade mit Whitespace im Namen
# werden nicht unterstuetzt; das Repo hat keine.
# ---------------------------------------------------------------------------
FROM source AS noqa-gate
ARG NOQA_FILES=""
RUN uv run python tools/check_noqa.py --fail-on-noqa $NOQA_FILES

# ---------------------------------------------------------------------------
# test-unit: pytest auf tests/unit/. Schliesst hypothesis-Property-Tests
# fuer Determinismus (`GG-SIM-001..004`) und kanonische Serialisierung
# (A-2 / `GG-DATA-005`) ein.
# ---------------------------------------------------------------------------
FROM source AS test-unit
RUN uv run pytest tests/unit/ -v

# ---------------------------------------------------------------------------
# test-determinism: pytest-Marker-Filter fuer Determinismus-Property-
# Tests. Eigener Stage, damit `make test-determinism` schnell laufbar
# ist; in `make ci` ueber `test-unit` mit abgedeckt.
# ---------------------------------------------------------------------------
FROM source AS test-determinism
RUN uv run pytest -m determinism tests/ -v

# ---------------------------------------------------------------------------
# test-replay: Replay-Diff- und Golden-File-Tests (`GG-REPLAY-007`,
# `GG-SIM-001`). Eigener Stage analog test-determinism.
# ---------------------------------------------------------------------------
FROM source AS test-replay
RUN uv run pytest -m replay tests/ -v

# ---------------------------------------------------------------------------
# test-fault: Fault-Injection-Tests (`GG-FAULT-001..010`).
# ---------------------------------------------------------------------------
FROM source AS test-fault
RUN uv run pytest -m fault tests/ -v

# ---------------------------------------------------------------------------
# coverage-gate: Gesamt-Coverage gegen `src/grid_gym` (`GG-COV-001`
# Line-Coverage SOLLTE 90%, `GG-COV-002` Branch-Coverage SOLLTE 85%).
# `--cov-branch` aktiviert Branch-Erfassung; pytest-cov erzwingt den
# Line-Schwellwert ueber `--cov-fail-under`, die Branch-Schwelle wird
# anschliessend aus `coverage.xml` (Attribut `branch-rate`) gelesen.
# Integration-Tests laufen via testcontainers ausserhalb dieses Stages
# (siehe Makefile-Ziel `test-integration`).
# ---------------------------------------------------------------------------
FROM source AS coverage-gate
ARG COVERAGE_THRESHOLD
ARG COVERAGE_BRANCH_THRESHOLD
RUN uv run pytest tests/unit/ \
        --cov=src/grid_gym \
        --cov-branch \
        --cov-report=term-missing \
        --cov-report=xml:/src/coverage/coverage.xml \
        --cov-fail-under="${COVERAGE_THRESHOLD}" \
 && uv run python - <<EOF
import sys
import xml.etree.ElementTree as ET
threshold = float("${COVERAGE_BRANCH_THRESHOLD}")
root = ET.parse("/src/coverage/coverage.xml").getroot()
branch_rate = float(root.get("branch-rate", "0")) * 100
print(f"[coverage-gate] branch coverage: {branch_rate:.2f}% (threshold: {threshold:.2f}%)")
if branch_rate < threshold:
    print(
        f"error: branch coverage below threshold: "
        f"{branch_rate:.2f}% < {threshold:.2f}%",
        file=sys.stderr,
    )
    sys.exit(1)
EOF

# ---------------------------------------------------------------------------
# coverage-gate-critical: `GG-COV-003` MUSS — kritische Domaenenlogik
# (Simulationskern, Scheduler, Replay-Diff, Szenario-Validierung,
# Batteriemodell) erreicht mindestens 90 Prozent Line- und Branch-
# Coverage. Eigener Stage, weil der Gesamt-Schwellwert aus
# `coverage-gate` Adapter und IO-Pfade verwaessern wuerde.
# Zielwert fuer spaetere Releases ist 95 Prozent (GG-COV-003).
# ---------------------------------------------------------------------------
FROM source AS coverage-gate-critical
ARG CRITICAL_COVERAGE_THRESHOLD
# CRITICAL_COV_TARGETS: leerzeichengetrennte Pfade, die als `--cov=`-
# Argumente an pytest gehen. Default ist die volle kritische Domain
# (GG-COV-003: Simulation, Battery, Scenario, Replay). Wellen, die
# nur einen Teilbereich implementieren, ueberschreiben das per
# `--build-arg`. Beispiel (Welle 2, A-2 Custom-Emitter):
#   make coverage-gate-critical \
#        CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization
# M3-Welle-1 (ADR 0022 §6): `core/faults` ist Welle-2-anticipatory
# — Welle 1 liefert nur Protocol-Stubs (FaultInjectableDevice),
# echte Implementer kommen mit Welle 2. Gate ist heute strukturell
# bei 100 % Branch-Rate (keine Branches in Protocol-Stubs).
# M3-Welle-3 (ADR 0023 §2.6 + §6): `core/agents` ist Welle-3-
# Foundation — Protocol + Bus + Snapshot-Codec. Welle-3-Test-Pfade
# decken Protocol-Adherence + Bus-Determinismus + Snapshot-
# Roundtrip; konkrete Agent-Implementer (`RuleBasedAgent`) kommen
# mit Welle 4 unter dem gleichen Paket-Pfad und sind damit
# automatisch von der Default-Schwelle erfasst.
ARG CRITICAL_COV_TARGETS="src/grid_gym/hexagon/core/simulation src/grid_gym/hexagon/core/devices/battery src/grid_gym/hexagon/core/devices/pv src/grid_gym/hexagon/core/devices/load src/grid_gym/hexagon/core/devices/grid_connection src/grid_gym/hexagon/core/devices/smart_meter src/grid_gym/hexagon/core/grid_model src/grid_gym/hexagon/core/scenario src/grid_gym/hexagon/core/replay src/grid_gym/hexagon/core/faults src/grid_gym/hexagon/core/agents src/grid_gym/adapters/driven/telemetry_otlp src/grid_gym/adapters/driven/protocol_mqtt src/grid_gym/adapters/driven/protocol_modbus src/grid_gym/adapters/driven/protocol_opcua src/grid_gym/adapters/driven/protocol_dnp3 src/grid_gym/adapters/driven/protocol_iec61850"
RUN set -eu; \
    for target in ${CRITICAL_COV_TARGETS}; do \
        if [ ! -d "${target}" ]; then \
            echo "[coverage-gate-critical] target dir missing: ${target}" >&2; \
            echo "[coverage-gate-critical] override via --build-arg CRITICAL_COV_TARGETS=<paths>" >&2; \
            echo "[coverage-gate-critical] Spike-0-Stand: make gates CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization (siehe docs/plan/planning/done/spike-0.md)" >&2; \
            exit 1; \
        fi; \
    done; \
    cov_args=""; \
    for target in ${CRITICAL_COV_TARGETS}; do \
        cov_args="${cov_args} --cov=${target}"; \
    done; \
    uv run pytest tests/unit/ \
        ${cov_args} \
        --cov-branch \
        --cov-report=term-missing \
        --cov-report=xml:/src/coverage/coverage-critical.xml \
        --cov-fail-under="${CRITICAL_COVERAGE_THRESHOLD}" \
 && uv run python - <<EOF
import sys
import xml.etree.ElementTree as ET
threshold = float("${CRITICAL_COVERAGE_THRESHOLD}")
root = ET.parse("/src/coverage/coverage-critical.xml").getroot()
branch_rate = float(root.get("branch-rate", "0")) * 100
print(f"[coverage-gate-critical] branch coverage: {branch_rate:.2f}% (threshold: {threshold:.2f}%)")
if branch_rate < threshold:
    print(
        f"error: critical-domain branch coverage below threshold: "
        f"{branch_rate:.2f}% < {threshold:.2f}%",
        file=sys.stderr,
    )
    sys.exit(1)
EOF

# ---------------------------------------------------------------------------
# dep-audit: `GG-QG-002` Security-Severity-Gate + `GG-QA-005` Dep-Scan.
# `pip-audit` prueft die per `uv export` materialisierte Lockfile gegen
# die PyPA Advisory Database (osv.dev + GitHub Advisory). `--strict`
# bricht bereits bei einer einzigen High-/Critical-Vulnerability ab.
# Ausnahmen werden ueber `.pip-audit.toml` mit Datum, Begruendung und
# Fix-ETA dokumentiert (entspricht GG-QG-002 „dokumentierte Ausnahme").
# pip-audit ist in der `audit`-dependency-group geladen.
# ---------------------------------------------------------------------------
FROM source AS dep-audit
RUN uv export --frozen --no-emit-project --no-hashes \
        --format requirements-txt > /tmp/requirements-audit.txt \
 && uv run pip-audit --strict --requirement /tmp/requirements-audit.txt

# ---------------------------------------------------------------------------
# openapi-validate: `GG-QG-006` — OpenAPI-Spezifikation, Request- und
# Response-Schemas werden in CI validiert. Stage exportiert die von
# FastAPI generierte OpenAPI-Definition (`/openapi.json`-Equivalent
# ueber den `app.openapi()`-Helper) und prueft sie mit
# `openapi-spec-validator`. Spec wird zusaetzlich als Artefakt unter
# `/src/artifacts/openapi.json` abgelegt.
# Die App muss importierbar sein; bis der API-Slice (M1) Code liefert,
# faellt dieser Stage bewusst rot. Teil des `make ci`-Aggregator-
# Vertrags (M1-Abnahmebedingung), NICHT des Spike-0-Abschluss-Gates
# `make gates`.
# ---------------------------------------------------------------------------
FROM source AS openapi-validate
RUN mkdir -p /src/artifacts \
 && uv run python -c "import json; from grid_gym.adapters.driving.http_api import app; \
print(json.dumps(app.openapi(), sort_keys=True, indent=2))" \
        > /src/artifacts/openapi.json \
 && uv run openapi-spec-validator /src/artifacts/openapi.json

# ---------------------------------------------------------------------------
# build-app: produktive Artefakte. `uv sync --frozen --no-dev
# --no-editable` baut ein .venv ohne Test-/Lint-Dependencies und
# installiert das Projekt als Wheel direkt in site-packages (kein
# editable-Link auf /src/src/). Damit zeigt der Runtime-PYTHONPATH
# nicht mehr auf den Build-Pfad und shebangs koennen sauber gerewritet
# werden.
# Trigger 015 (M2 Welle 0b): `--no-editable` ersetzt den Welle-6d-
# `PYTHONPATH=/app/src`-Workaround.
#
# Welle-5b-C2-Review-Folge 2026-06-01: `--extra iec61850` propagiert
# auch in den build-app-Stage. Ohne diesen Flag hatte der Runtime-
# venv **kein** `pyiec61850-ng` (deps/source-Stages installieren das
# Extra, aber build-app ueberschrieb das mit `--frozen --no-dev
# --no-editable`). Ein produktiver Scenario mit `type: iec61850`
# crashte erst zur Laufzeit mit `Iec61850PortLibraryNotInstalledError`.
# Mit `--extra iec61850` ist die Library im Runtime-venv enthalten.
# **Achtung Distribution-Implication** (Decision I-f): Docker-Images,
# die so gebaut werden, enthalten produktiv pyiec61850-ng/libiec61850
# unter GPLv3 — der distribuierende Operator muss Source-Availability-
# Pflichten beachten (siehe LICENSE-Hinweis + README-Sektion).
# ---------------------------------------------------------------------------
FROM source AS build-app
RUN uv sync --frozen --no-dev --no-editable --extra iec61850

# ---------------------------------------------------------------------------
# runtime: minimales Image fuer den Produktivlauf. Non-root, /health-
# Healthcheck, Port 8080. Enthaelt NUR die Runtime-Dependencies
# (`--no-dev`), nicht die Test-Toolchain.
#
# Bezug: GG-DEPLOY-001/003/006, GG-API-001 (/runs), GG-API-002 (/ws).
#
# Base-Image-Patch-Strategie (Trigger 015, M2 Welle 0b):
# `python:${PYTHON_VERSION}-slim` lag bei Welle-0b-Verifikation
# Debian-Sicherheitspatches hinterher (libcap2 CVE-2026-4878,
# libsystemd0/libudev1 CVE-2026-29111). Reines `make rebase-base`
# allein behebt das nicht — Docker Hub veroeffentlicht den slim-Tag
# nicht mit jedem Debian-Security-Update neu. Welle 0b bleibt
# deshalb bewusst beim `apt-get upgrade -y`-Pattern aus Welle 6d,
# erklaert es aber jetzt als die *gewaehlte* Strategie (Option A
# aus Trigger 015): in-image-Patching ueber `apt-get upgrade`, plus
# `make rebase-base` zum Refresh des Base-Image-Layers fuer den
# uv-Cache. Wechsel auf ein eigenes `grid-gym-base:debian-13-patched`
# (Option B aus Trigger 015) ist M6-Material (Security-Haertung).
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/app/.venv/bin:$PATH \
    GRID_GYM_HOST=0.0.0.0 \
    GRID_GYM_PORT=8080 \
    GRID_GYM_ENV=production
# `PYTHONPATH=/app/src` (Welle-6d-Workaround) ist hier entfallen,
# weil `uv sync --no-editable` im build-app-Stage das Projekt direkt
# als Wheel in `/src/.venv/lib/.../site-packages/` installiert.

# curl fuer den HEALTHCHECK. Kein build-essential im Runtime-Image —
# alle nativen Wheels werden im build-app-Stage aufgeloest und
# kopiert. `apt-get upgrade -y` zieht Debian-Sicherheitspatches
# fuer Base-Image-Pakete (libcap2, libsystemd0, libudev1) — siehe
# Base-Image-Patch-Strategie oben. `make image-audit` (trivy mit
# `--ignore-unfixed`) bleibt das verbindliche Gate.
RUN apt-get update \
 && apt-get upgrade --yes \
 && apt-get install --yes --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 1001 --shell /usr/sbin/nologin grid-gym

WORKDIR /app
COPY --from=build-app --chown=grid-gym:grid-gym /src/.venv /app/.venv
COPY --from=build-app --chown=grid-gym:grid-gym /src/pyproject.toml /app/pyproject.toml

# Shebang-Rewrite (Trigger 015, M2 Welle 0b):
# venv-Binaries (`uvicorn`, `alembic`, console_scripts etc.) wurden
# im build-app-Stage mit Shebangs auf `/src/.venv/bin/python` gebaut.
# Im Runtime-Image liegt der Interpreter unter `/app/.venv/bin/python`
# — ohne Rewrite wuerden direkte Binary-Aufrufe mit
# `exec: no such file or directory` fehlschlagen (Welle-6d-Grund fuer
# `python -m uvicorn`-Indirection in `deploy/compose.yml`).
# `pyvenv.cfg` traegt ebenfalls den Build-Pfad und wird mitgerewritet.
#
# Welle-0b-Review M-6: `find` filtert `python*`- und `*.so`-Dateien
# heraus, damit `sed` keinen Binary-Launcher anfasst, sollte ein
# zukuenftiges uv-Release solche generieren.
#
# Welle-0b-Review L-13: der `sed`-Pattern `^#!/src/\.venv/bin/python`
# ist **bewusst praefix-matching** (kein `$`-Anker). Damit greift
# der Rewrite gleichermassen fuer
#   `#!/src/.venv/bin/python`,
#   `#!/src/.venv/bin/python3`,
#   `#!/src/.venv/bin/python3.14`
# (uv-Konsolen-Skripte koennen jede dieser Varianten emittieren).
# Non-matchende Erstzeilen lassen sed -i die Datei byte-identisch.
RUN find /app/.venv/bin -type f ! -name 'python*' ! -name '*.so' \
        -exec sed -i '1s|^#!/src/\.venv/bin/python|#!/app/.venv/bin/python|' {} + \
 && sed -i 's|/src/\.venv|/app/.venv|g' /app/.venv/pyvenv.cfg

USER grid-gym:grid-gym
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD curl --fail --silent --show-error http://localhost:8080/health || exit 1
# ENTRYPOINT laeuft `uvicorn` als direkte Binary (Shebang ist
# gerewritet, kein `python -m`-Indirection mehr noetig).
# Shell-Form mit `exec` sorgt fuer Signal-Forwarding (SIGTERM aus
# `docker stop` erreicht uvicorn direkt, nicht den /bin/sh-Wrapper).
# `GRID_GYM_HOST` und `GRID_GYM_PORT` aus der ENV-Sektion werden hier
# konsumiert (Welle-0b-Review H-1: Welle-0b-Erst-Wurf hatte sie zwar
# in ENV gesetzt, aber per exec-form-ENTRYPOINT ignoriert; das war
# ein dokumentations-naher Lie und ist hier behoben).
ENTRYPOINT exec uvicorn grid_gym.adapters.driving.http_api:app --host "$GRID_GYM_HOST" --port "$GRID_GYM_PORT"

# ---------------------------------------------------------------------------
# Image-Audit (`GG-QG-002` SOLLTE) laeuft AUSSERHALB des Dockerfile —
# trivy braucht das gebaute Runtime-Image als Eingabe. Makefile-Target:
# `make image-audit` (haengt von `make build` ab).
#
# Future stages (Folgewellen):
#   FROM source AS test-integration-postgres  -- testcontainers via Docker
#                                                socket im Makefile-Ziel.
#   FROM source AS test-e2e-demo              -- Compose-basierte Demo
#                                                (GG-DEMO-001..008).
#   FROM source AS sbom                       -- syft/cyclonedx-bom fuer
#                                                Release-Assets.
# ---------------------------------------------------------------------------
