# syntax=docker/dockerfile:1.7
#
# grid-gym multi-stage Dockerfile.
#
# Spike-0-Pfad fuer ADR 0002 (`Provisional` gemaess ADR 0006):
# Stages implementieren die Spike-0-Gates aus ADR 0002 (Auflage A-1)
# und ADR 0005 (Type-Check): Lint, Format, Typecheck, Architektur-Imports,
# Architektur-Custom (AST), Tests, Coverage-Gate, Runtime. Jeder Stage
# ist ein eigenstaendiges Build-Ziel und wird vom Makefile per `--target`
# einzeln gebaut. Aggregierte CI-Lauefe ueber `make ci` / `make gates`.
# Bis zur Acceptance von ADR 0002 und ADR 0005 bleibt diese Datei der
# validierte Spike-0-Pfad — kein verbindlicher Stack-Beschluss.
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
RUN uv sync --frozen --no-install-project --all-groups

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
RUN uv sync --frozen --all-groups

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
RUN uv run pytest tests/unit/ \
        --cov=src/grid_gym/hexagon/core/simulation \
        --cov=src/grid_gym/hexagon/core/devices/battery \
        --cov=src/grid_gym/hexagon/core/scenario \
        --cov=src/grid_gym/hexagon/core/replay \
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
# Die App muss importierbar sein; bis der API-Slice von Spike-0 dort
# Code liefert, faellt dieser Stage bewusst rot — er ist Teil des
# Spike-0-Pflichtnachweises analog `lint`/`arch-check`.
# ---------------------------------------------------------------------------
FROM source AS openapi-validate
RUN mkdir -p /src/artifacts \
 && uv run python -c "import json; from grid_gym.adapters.driving.http_api import app; \
print(json.dumps(app.openapi(), sort_keys=True, indent=2))" \
        > /src/artifacts/openapi.json \
 && uv run openapi-spec-validator /src/artifacts/openapi.json

# ---------------------------------------------------------------------------
# build-app: produktive Artefakte. `uv sync --frozen --no-dev` baut ein
# .venv ohne Test-/Lint-Dependencies; das wird in das Runtime-Image
# kopiert. Kein Wheel-Build noetig — der Code liegt unter src/ und wird
# editable installiert.
# ---------------------------------------------------------------------------
FROM source AS build-app
RUN uv sync --frozen --no-dev

# ---------------------------------------------------------------------------
# runtime: minimales Image fuer den Produktivlauf. Non-root, /health-
# Healthcheck, Port 8080. Enthaelt NUR die Runtime-Dependencies
# (`--no-dev`), nicht die Test-Toolchain.
#
# Bezug: GG-DEPLOY-001/003/006, GG-API-001 (/runs), GG-API-002 (/ws).
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/app/.venv/bin:$PATH \
    GRID_GYM_HOST=0.0.0.0 \
    GRID_GYM_PORT=8080 \
    GRID_GYM_ENV=production

# curl fuer den HEALTHCHECK. Kein build-essential im Runtime-Image —
# alle nativen Wheels werden im build-app-Stage aufgeloest und
# kopiert.
RUN apt-get update \
 && apt-get install --yes --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 1001 --shell /usr/sbin/nologin grid-gym

WORKDIR /app
COPY --from=build-app --chown=grid-gym:grid-gym /src/.venv /app/.venv
COPY --from=build-app --chown=grid-gym:grid-gym /src/src /app/src
COPY --from=build-app --chown=grid-gym:grid-gym /src/pyproject.toml /app/pyproject.toml

USER grid-gym:grid-gym
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD curl --fail --silent --show-error http://localhost:8080/health || exit 1
ENTRYPOINT ["python", "-m", "grid_gym.adapters.driving.http_api"]

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
