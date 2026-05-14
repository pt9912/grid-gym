# grid-gym Makefile.
#
# Spike-0-Pfad fuer ADR 0002 (`Provisional` per ADR 0003 §2.1):
# Targets entsprechen den Stages aus Dockerfile (ADR 0002 Auflage A-1
# plus ADR 0005 typecheck). Aggregierte Gates ueber `gates` und `ci`;
# Closure-Lauf ueber `fullbuild`. Bis zur Acceptance von ADR 0002 und
# ADR 0005 bleibt dies der validierte Spike-0-Pfad — kein verbindlicher
# Stack-Beschluss.
#
# Bezug:
# - GG-AR-OPEN-001 / ADR 0002 (Python-Stack)
# - GG-CICD-001..007 (Build, Tests, Quality Gates, Security/Dep-Scan)
# - GG-DEPLOY-001/002/006/011 (Container, offline, Healthcheck)
# - GG-COV-001..005, GG-QG-001..007 (Coverage und Quality Gates)

DOCKER ?= docker
DOCKERFILE ?= Dockerfile
BUILD_CONTEXT ?= .
IMAGE_PREFIX ?= grid-gym
PYTHON_VERSION ?= 3.14
UV_VERSION ?= 0.5.31
COVERAGE_THRESHOLD ?= 90
COVERAGE_BRANCH_THRESHOLD ?= 85
CRITICAL_COVERAGE_THRESHOLD ?= 90
TRIVY_IMAGE ?= aquasec/trivy:0.58.0
TRIVY_SEVERITY ?= HIGH,CRITICAL
DOCKER_BUILD_ARGS ?=
COMPOSE_FILE ?= deploy/compose.yml

DOCKER_BUILD = $(DOCKER) build $(BUILD_CONTEXT) \
	-f $(DOCKERFILE) \
	--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
	--build-arg UV_VERSION=$(UV_VERSION) \
	--build-arg COVERAGE_THRESHOLD=$(COVERAGE_THRESHOLD) \
	--build-arg COVERAGE_BRANCH_THRESHOLD=$(COVERAGE_BRANCH_THRESHOLD) \
	--build-arg CRITICAL_COVERAGE_THRESHOLD=$(CRITICAL_COVERAGE_THRESHOLD) \
	$(DOCKER_BUILD_ARGS)

.DEFAULT_GOAL := help

.PHONY: help \
	lint format-check typecheck \
	arch-check arch-check-imports arch-check-custom \
	test test-unit test-determinism test-replay test-fault \
	test-integration \
	coverage-gate coverage-gate-critical \
	dep-audit image-audit openapi-validate \
	gates ci fullbuild \
	build runtime test-container \
	lock-refresh \
	sbom \
	clean

help:
	@echo "grid-gym Makefile"
	@echo ""
	@echo "Override variables (defaults shown):"
	@echo "  DOCKER=$(DOCKER)"
	@echo "  DOCKERFILE=$(DOCKERFILE)"
	@echo "  BUILD_CONTEXT=$(BUILD_CONTEXT)"
	@echo "  IMAGE_PREFIX=$(IMAGE_PREFIX)"
	@echo "  PYTHON_VERSION=$(PYTHON_VERSION)"
	@echo "  UV_VERSION=$(UV_VERSION)"
	@echo "  COVERAGE_THRESHOLD=$(COVERAGE_THRESHOLD)"
	@echo "  COVERAGE_BRANCH_THRESHOLD=$(COVERAGE_BRANCH_THRESHOLD)"
	@echo "  CRITICAL_COVERAGE_THRESHOLD=$(CRITICAL_COVERAGE_THRESHOLD)"
	@echo "  TRIVY_IMAGE=$(TRIVY_IMAGE)"
	@echo "  TRIVY_SEVERITY=$(TRIVY_SEVERITY)"
	@echo "  COMPOSE_FILE=$(COMPOSE_FILE)"
	@echo ""
	@echo "Spike-0 / A-1 (ADR 0002):"
	@echo "  make lint              ruff check (BLE/TRY/B/DTZ/S/TID/C901/PLR*/N/RET/SIM/ARG/RUF + banned-api)"
	@echo "  make format-check      ruff format --check (kein Auto-Fix)"
	@echo "  make typecheck         mypy --strict (ADR 0005, GG-QG-005, GG-PRINC-004/005 LSP/ISP)"
	@echo "  make arch-check        import-linter + tools/arch_check.py (15 A-1-Contracts)"
	@echo "  make arch-check-imports  Nur import-linter (Layer-/Forbidden-Contracts)"
	@echo "  make arch-check-custom   Nur AST + grimp-SCC (Aufruf-Sites, Immutability, ...)"
	@echo ""
	@echo "Tests:"
	@echo "  make test-unit         pytest tests/unit/"
	@echo "  make test-determinism  pytest -m determinism (GG-SIM-001..004, GG-DATA-005)"
	@echo "  make test-replay       pytest -m replay (GG-REPLAY-007, GG-SAFE-006)"
	@echo "  make test-fault        pytest -m fault (GG-FAULT-001..010)"
	@echo "  make test              Alle Test-Marker im selben Stage"
	@echo "  make test-integration  Compose-basierte Integration-Tests (Postgres etc.)"
	@echo "  make coverage-gate            GG-COV-001/002 — \$$COVERAGE_THRESHOLD% Line + \$$COVERAGE_BRANCH_THRESHOLD% Branch (gesamt)"
	@echo "  make coverage-gate-critical   GG-COV-003 MUSS — \$$CRITICAL_COVERAGE_THRESHOLD% auf kritischer Domain (simulation/devices/battery/scenario/replay)"
	@echo ""
	@echo "Security & Spec-Gates:"
	@echo "  make dep-audit         GG-QG-002/GG-QA-005 — pip-audit gegen Lockfile (High/Critical bricht Build)"
	@echo "  make image-audit       GG-QG-002 SOLLTE — trivy image scan (haengt von make build ab)"
	@echo "  make openapi-validate  GG-QG-006 — OpenAPI-Spec aus FastAPI exportieren und validieren"
	@echo ""
	@echo "Aggregator:"
	@echo "  make gates             lint + format-check + typecheck + arch-check + test-unit + coverage-gate + coverage-gate-critical + dep-audit"
	@echo "  make ci                gates + test-integration + openapi-validate + image-audit"
	@echo "  make fullbuild         ci + build + runtime"
	@echo ""
	@echo "Runtime:"
	@echo "  make build             Multi-stage Runtime-Image (non-root, /health HEALTHCHECK)"
	@echo "  make runtime           docker compose up + /health-Probe + down"
	@echo "  make test-container    Alias fuer runtime"
	@echo ""
	@echo "Maintenance:"
	@echo "  make lock-refresh      uv lock refresh (commit uv.lock alongside pyproject.toml)"
	@echo "  make sbom              CycloneDX SBOM (Release-Asset; aktiviert in spaeterer Welle)"
	@echo "  make clean             Lokale Build-Artefakte loeschen"

# --- Spike-0 / A-1-Gates ---------------------------------------------------

lint:
	$(DOCKER_BUILD) --target lint -t $(IMAGE_PREFIX)-lint:latest

format-check:
	$(DOCKER_BUILD) --target format-check -t $(IMAGE_PREFIX)-format-check:latest

# mypy --strict gegen src/grid_gym + tools/. Configuration in
# pyproject.toml [tool.mypy] (siehe ADR 0005).
typecheck:
	$(DOCKER_BUILD) --target typecheck -t $(IMAGE_PREFIX)-typecheck:latest

arch-check:
	$(DOCKER_BUILD) --target arch-check -t $(IMAGE_PREFIX)-arch-check:latest

arch-check-imports:
	$(DOCKER_BUILD) --target arch-check-imports -t $(IMAGE_PREFIX)-arch-check-imports:latest

arch-check-custom:
	$(DOCKER_BUILD) --target arch-check-custom -t $(IMAGE_PREFIX)-arch-check-custom:latest

# --- Tests -----------------------------------------------------------------

test-unit:
	$(DOCKER_BUILD) --target test-unit -t $(IMAGE_PREFIX)-test-unit:latest

test-determinism:
	$(DOCKER_BUILD) --target test-determinism -t $(IMAGE_PREFIX)-test-determinism:latest

test-replay:
	$(DOCKER_BUILD) --target test-replay -t $(IMAGE_PREFIX)-test-replay:latest

test-fault:
	$(DOCKER_BUILD) --target test-fault -t $(IMAGE_PREFIX)-test-fault:latest

test: test-unit test-determinism test-replay test-fault
	@echo "[test] all marker stages green"

# Integration-Tests laufen mit testcontainers gegen echte Service-
# Container (Postgres, ggf. Influx). Der Docker-Daemon ist im
# Build-Stage nicht ansprechbar; deshalb laeuft pytest via Compose
# im Host-Netz und gibt testcontainers Zugriff auf /var/run/docker.sock.
# Voraussetzung: ein `tests/integration/compose.yml`, das einen
# `test-runner`-Service mit Docker-Socket-Mount definiert.
test-integration:
	@if [ ! -f tests/integration/compose.yml ]; then \
		echo "[test-integration] tests/integration/compose.yml fehlt — wird in Welle 2 angelegt"; \
		exit 0; \
	fi
	$(DOCKER) compose -f tests/integration/compose.yml up --build --abort-on-container-exit --exit-code-from test-runner; \
	exit_code=$$?; \
	$(DOCKER) compose -f tests/integration/compose.yml down -v --remove-orphans >/dev/null 2>&1; \
	exit $$exit_code

coverage-gate:
	$(DOCKER_BUILD) --target coverage-gate \
		--build-arg COVERAGE_THRESHOLD=$(COVERAGE_THRESHOLD) \
		--build-arg COVERAGE_BRANCH_THRESHOLD=$(COVERAGE_BRANCH_THRESHOLD) \
		-t $(IMAGE_PREFIX)-coverage-gate:latest

coverage-gate-critical:
	$(DOCKER_BUILD) --target coverage-gate-critical \
		--build-arg CRITICAL_COVERAGE_THRESHOLD=$(CRITICAL_COVERAGE_THRESHOLD) \
		-t $(IMAGE_PREFIX)-coverage-gate-critical:latest

# --- Security & Spec-Gates -------------------------------------------------

# GG-QG-002 / GG-QA-005: pip-audit gegen die per `uv export`
# materialisierte Lockfile. `pip-audit` ist in der `audit`-dependency-group
# verankert; --strict bricht bei einer einzigen High/Critical-CVE.
# Ausnahmen werden ueber `.pip-audit.toml` (Datum, Begruendung, Fix-ETA)
# dokumentiert — entspricht GG-QG-002 "dokumentierte Ausnahme".
dep-audit:
	$(DOCKER_BUILD) --target dep-audit -t $(IMAGE_PREFIX)-dep-audit:latest

# GG-QG-002 SOLLTE: Container-Image-Scan ueber trivy. Laeuft AUSSERHALB
# des Dockerfile, weil trivy das gebaute Image braucht. `--exit-code 1`
# bricht den Build bei jeder HIGH/CRITICAL-Vulnerability, `--ignore-unfixed`
# verschont Befunde ohne verfuegbaren Fix (alternative: explizit als
# Ausnahme dokumentieren).
image-audit: build
	$(DOCKER) run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v "$$HOME/.cache/trivy:/root/.cache/" \
		$(TRIVY_IMAGE) image \
			--exit-code 1 \
			--severity $(TRIVY_SEVERITY) \
			--ignore-unfixed \
			$(IMAGE_PREFIX)-runtime:latest

# GG-QG-006: OpenAPI-Spec aus FastAPI exportieren und mit
# openapi-spec-validator pruefen. Stage faellt rot, solange der
# API-Slice den Endpunkt nicht liefert — das ist beabsichtigt.
openapi-validate:
	$(DOCKER_BUILD) --target openapi-validate -t $(IMAGE_PREFIX)-openapi-validate:latest

# --- Aggregierte Gates -----------------------------------------------------

gates: lint format-check typecheck arch-check test-unit coverage-gate coverage-gate-critical dep-audit
	@echo "[gates] mandatory Spike-0/A-1 gates green: lint, format-check, typecheck (mypy --strict, ADR 0005), arch-check (15 contracts), test-unit, coverage-gate ($(COVERAGE_THRESHOLD)% line / $(COVERAGE_BRANCH_THRESHOLD)% branch), coverage-gate-critical ($(CRITICAL_COVERAGE_THRESHOLD)% critical domain), dep-audit"

ci: gates test-integration openapi-validate image-audit
	@echo "[ci] mandatory gates green + test-integration + openapi-validate + image-audit"

fullbuild: ci build runtime
	@echo "[fullbuild] full closure: ci + runtime image + compose smoke green"

# --- Runtime ---------------------------------------------------------------

build:
	$(DOCKER_BUILD) --target runtime -t $(IMAGE_PREFIX)-runtime:latest

# Compose-Smoke: produktiv-shaped Stack hoch, /health pollen, down.
# Voraussetzung: `make build` (bereits Bestandteil dieses Targets via
# dependency) und ein `deploy/compose.yml`, das api, postgres und ui
# definiert.
runtime: build
	@if [ ! -f $(COMPOSE_FILE) ]; then \
		echo "[runtime] $(COMPOSE_FILE) fehlt — wird mit der Deploy-Slice angelegt"; \
		exit 1; \
	fi
	$(DOCKER) compose -f $(COMPOSE_FILE) up -d --wait --wait-timeout 60
	@echo "[runtime] stack is up; probing /health"
	$(DOCKER) compose -f $(COMPOSE_FILE) exec -T api curl --fail --silent --show-error http://localhost:8080/health
	@echo "[runtime] /health ok; tearing down"
	$(DOCKER) compose -f $(COMPOSE_FILE) down -v --remove-orphans

test-container: runtime
	@echo "[test-container] runtime smoke green"

# --- Maintenance -----------------------------------------------------------

# Lock-Refresh: nach Aenderung von pyproject.toml-Dependencies neu
# aufloesen. uv.lock MUSS gemeinsam mit der pyproject.toml-Aenderung
# committet werden, damit `--frozen`-Builds gruen bleiben (Supply-Chain-
# Defense, analog `packages.lock.json` in bess-ems).
lock-refresh:
	$(DOCKER) run --rm -v "$$(pwd)":/src -w /src \
		ghcr.io/astral-sh/uv:$(UV_VERSION) \
		uv lock

# SBOM-Erzeugung als Release-Asset. Wird in spaeterer Welle scharf
# geschaltet, sobald GG-CICD-007 (Artefakt-Veroeffentlichung) aktiv
# wird. Aufruf: `make sbom VERSION=v0.1.0`.
SYFT_IMAGE ?= anchore/syft:v1.17.0
sbom:
	@if [ -z "$(VERSION)" ]; then \
		echo "[sbom] VERSION ist erforderlich, z. B. make sbom VERSION=v0.1.0" >&2; \
		exit 1; \
	fi
	$(DOCKER) run --rm \
		-v "$$(pwd)":/src \
		$(SYFT_IMAGE) \
		dir:/src -o cyclonedx-json=/src/artifacts/sbom-$(VERSION).cdx.json

clean:
	@rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov coverage \
		.venv build dist *.egg-info
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@find . -type f -name '*.pyc' -delete
	@echo "[clean] local build artefacts removed"
