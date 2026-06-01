# grid-gym Makefile.
#
# Verbindliche Build-/Test-/Gate-Schicht gemaess ADR 0002
# (Accepted 2026-05-15) und ADR 0005 (Accepted 2026-05-15). Targets
# entsprechen den Stages aus Dockerfile (ADR 0002 Auflage A-1 plus
# ADR 0005 typecheck). Aggregierte Gates ueber `gates` (Spike-0-
# Abschluss-Gate) und `ci`; Closure-Lauf ueber `fullbuild`
# (M1-Abnahmebedingung).
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
# M3-Welle-6-C2: OTLP-Collector-Sibling fuer telemetry_otlp-Adapter.
# Wird in deploy/compose.yml als `${OTEL_COLLECTOR_IMAGE:-...}`
# interpoliert. `export` macht den Wert fuer das compose-Recipe
# sichtbar; gleichzeitig deckt der `:-default`-Fallback im Compose-
# YAML Aufrufe ohne Makefile (`docker compose -f deploy/compose.yml
# up`) ab.
OTEL_COLLECTOR_IMAGE ?= otel/opentelemetry-collector-contrib:0.152.1
export OTEL_COLLECTOR_IMAGE

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
	arch-check arch-check-imports arch-check-custom docs-check spdx-check \
	test test-unit test-determinism test-replay test-fault \
	test-integration \
	coverage-gate coverage-gate-critical \
	dep-audit image-audit openapi-validate \
	gates ci fullbuild \
	build runtime test-container \
	lock-refresh rebase-base \
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
	@echo "  OTEL_COLLECTOR_IMAGE=$(OTEL_COLLECTOR_IMAGE)"
	@echo ""
	@echo "Spike-0 / A-1 (ADR 0002):"
	@echo "  make lint              ruff check (BLE/TRY/B/DTZ/S/TID/C901/PLR*/N/RET/SIM/ARG/RUF + banned-api)"
	@echo "  make format-check      ruff format --check (kein Auto-Fix)"
	@echo "  make typecheck         mypy --strict (ADR 0005, GG-QG-005, GG-PRINC-004/005 LSP/ISP)"
	@echo "  make arch-check        import-linter + tools/arch_check.py (19 A-1-Contracts: 6 import-linter + 13 arch_check)"
	@echo "  make arch-check-imports  Nur import-linter (Layer-/Forbidden-Contracts)"
	@echo "  make arch-check-custom   Nur AST + grimp-SCC (Aufruf-Sites, Immutability, ...)"
	@echo "  make docs-check        tools/check_refs.py — Markdown-Link-Validator (Trigger 002)"
	@echo "  make spdx-check        tools/check_spdx.py — SPDX-License-Identifier-Lint fuer IEC-61850-GPL-Boundary (ADR 0035, M4 Welle 6b)"
	@echo "  make noqa-check        tools/check_noqa.py — # noqa-Marker-Reporter (Slice 027, Exit 0)"
	@echo "  make noqa-gate         tools/check_noqa.py --fail-on-noqa (Plan §4 hart in 'make gates'; FILES=... fuer paketweise Scope-Eingrenzung)"
	@echo ""
	@echo "Tests:"
	@echo "  make test-unit         pytest tests/unit/"
	@echo "  make test-determinism  pytest -m determinism (GG-SIM-001..004, GG-DATA-005)"
	@echo "  make test-replay       pytest -m replay (GG-REPLAY-007, GG-SAFE-006)"
	@echo "  make test-fault        pytest -m fault (GG-FAULT-001..010)"
	@echo "  make test              Alle Test-Marker im selben Stage"
	@echo "  make test-integration  Compose-basierte Integration-Tests (Postgres etc.)"
	@echo "  make coverage-gate            GG-COV-001/002 — \$$COVERAGE_THRESHOLD% Line + \$$COVERAGE_BRANCH_THRESHOLD% Branch (gesamt)"
	@echo "  make coverage-report          Zeigt Total-Coverage frisch (--no-cache-filter coverage-gate; vorgelagerte Stages bleiben kalt)"
	@echo "  make coverage-gate-critical   GG-COV-003 MUSS — \$$CRITICAL_COVERAGE_THRESHOLD% auf kritischer Domain (simulation/devices/battery/scenario/replay)"
	@echo ""
	@echo "Security & Spec-Gates:"
	@echo "  make dep-audit         GG-QG-002/GG-QA-005 — pip-audit gegen Lockfile (High/Critical bricht Build)"
	@echo "  make image-audit       GG-QG-002 SOLLTE — trivy image scan (haengt von make build ab)"
	@echo "  make openapi-validate  GG-QG-006 — OpenAPI-Spec aus FastAPI exportieren und validieren"
	@echo ""
	@echo "Aggregator:"
	@echo "  make gates             lint + format-check + typecheck + arch-check + test-unit + coverage-gate + coverage-gate-critical + dep-audit + noqa-gate + spdx-check"
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
	@echo "  make rebase-base       docker pull python:\$$(PYTHON_VERSION)-slim + uv-image — Base-Image-Patch-Pull (Trigger 015)"
	@echo "  make sbom              CycloneDX SBOM (Release-Asset; aktiviert in spaeterer Welle)"
	@echo "  make clean             Lokale Build-Artefakte loeschen"

# --- Spike-0 / A-1-Gates ---------------------------------------------------

lint:
	$(DOCKER_BUILD) --target lint -t $(IMAGE_PREFIX)-lint:latest

format-check:
	$(DOCKER_BUILD) --target format-check -t $(IMAGE_PREFIX)-format-check:latest

# Wendet ruff format auf den Repo an (kein --check, sondern Auto-Fix).
# Laeuft im base-Stage als aktueller User; Cache geht nach /tmp.
format:
	$(DOCKER_BUILD) --target source -t $(IMAGE_PREFIX)-source:latest
	$(DOCKER) run --rm \
		--user "$$(id -u):$$(id -g)" \
		-e UV_CACHE_DIR=/tmp/uv-cache \
		-e UV_PROJECT_ENVIRONMENT=/tmp/uv-venv \
		-e RUFF_CACHE_DIR=/tmp/ruff-cache \
		-v "$$(pwd)":/src -w /src \
		$(IMAGE_PREFIX)-source:latest \
		uv run ruff format .

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

docs-check:
	$(DOCKER_BUILD) --target docs-check -t $(IMAGE_PREFIX)-docs-check:latest

# `tools/check_spdx.py` — SPDX-License-Identifier-Lint fuer die
# IEC-61850-GPL-Boundary (ADR 0035 Decision I-f, M4 Welle 6b C1).
# Lint-Failure bei fehlendem oder falschem Identifier; in `make gates`
# integriert.
spdx-check:
	$(DOCKER_BUILD) --target spdx-check -t $(IMAGE_PREFIX)-spdx-check:latest

# `tools/check_noqa.py` — `# noqa`-Marker-Reporter (Slice 027 Plan).
# Default-Modus ist Report-only (Exit 0); fuer einen Bestands-Lauf vor
# dem Slice-Start. Hard-Gate ist `make noqa-gate` (siehe darunter).
noqa-check:
	$(DOCKER_BUILD) --target noqa-check -t $(IMAGE_PREFIX)-noqa-check:latest

# `tools/check_noqa.py --fail-on-noqa` — Hard-Gate (Exit 1 bei Treffer).
# Paketweise verwendbar via `FILES`-Variable:
#   make noqa-gate FILES="src/grid_gym/adapters/driving/http_api/app.py"
# Ohne `FILES` prueft das gesamte Repo (`src tests tools`). Plan §3.0
# verlangt paketweise Hard-Stufen nach jedem A..E-Paket; Plan §4
# integriert das Gate final in `make gates` (kommt mit Slice-Final).
noqa-gate:
	$(DOCKER_BUILD) --target noqa-gate \
		--build-arg NOQA_FILES="$(FILES)" \
		-t $(IMAGE_PREFIX)-noqa-gate:latest

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

# Zeigt die aktuelle Total-Line- und Branch-Coverage, ohne den
# Cache der vorgelagerten `base`/`deps`/`source`-Stages zu kippen.
# `--no-cache-filter coverage-gate` (BuildKit) zwingt nur die
# coverage-gate-Stage zur Re-Ausfuehrung; pytest laeuft frisch,
# darunterliegende Layer bleiben kalt → typischer Lauf < 15s.
coverage-report:
	@$(DOCKER) build $(BUILD_CONTEXT) -f $(DOCKERFILE) $(DOCKER_BUILD_ARGS) \
		--target coverage-gate \
		--no-cache-filter coverage-gate \
		--build-arg COVERAGE_THRESHOLD=$(COVERAGE_THRESHOLD) \
		--build-arg COVERAGE_BRANCH_THRESHOLD=$(COVERAGE_BRANCH_THRESHOLD) \
		-t $(IMAGE_PREFIX)-coverage-gate:latest 2>&1 \
		| grep -E "^#[0-9]+ +[0-9.]+ +(TOTAL|Required test coverage|====.*passed)" \
		| sed 's/^#[0-9]* *[0-9.]* *//'

# Override CRITICAL_COV_TARGETS, um nur einen Teilbereich der kritischen
# Domain zu pruefen — bevor alle Pfade aus GG-COV-003 implementiert sind.
# Beispiel fuer Spike-0 Welle 2:
#   make coverage-gate-critical CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization
coverage-gate-critical:
	$(DOCKER_BUILD) --target coverage-gate-critical \
		--build-arg CRITICAL_COVERAGE_THRESHOLD=$(CRITICAL_COVERAGE_THRESHOLD) \
		$(if $(CRITICAL_COV_TARGETS),--build-arg CRITICAL_COV_TARGETS="$(CRITICAL_COV_TARGETS)",) \
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
#
# Welle-6-C2-Erweiterung: zweiter Trivy-Run gegen den gepinnten
# OTLP-Collector-Tag — der Collector ist Teil des Welle-6-Observability-
# Pfads (`deploy/compose.yml`-Sibling) und hat dieselbe DoD-Bindung wie
# das selbst-gebaute runtime-Image. `docker image inspect ... || pull`
# (Welle-6-Review-Folge M-5) ist rate-limit-freundlich gegenueber
# Docker-Hub: zieht den Tag nur dann, wenn er lokal noch nicht da
# ist; bei wiederholten Lauefen oder im offline-CI faellt der Pull
# weg.
image-audit: build
	$(DOCKER) run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v "$$HOME/.cache/trivy:/root/.cache/" \
		$(TRIVY_IMAGE) image \
			--exit-code 1 \
			--severity $(TRIVY_SEVERITY) \
			--ignore-unfixed \
			$(IMAGE_PREFIX)-runtime:latest
	$(DOCKER) image inspect $(OTEL_COLLECTOR_IMAGE) >/dev/null 2>&1 || $(DOCKER) pull $(OTEL_COLLECTOR_IMAGE)
	$(DOCKER) run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v "$$HOME/.cache/trivy:/root/.cache/" \
		$(TRIVY_IMAGE) image \
			--exit-code 1 \
			--severity $(TRIVY_SEVERITY) \
			--ignore-unfixed \
			$(OTEL_COLLECTOR_IMAGE)

# GG-QG-006: OpenAPI-Spec aus FastAPI exportieren und mit
# openapi-spec-validator pruefen. Stage faellt rot, solange der
# API-Slice den Endpunkt nicht liefert — das ist beabsichtigt.
openapi-validate:
	$(DOCKER_BUILD) --target openapi-validate -t $(IMAGE_PREFIX)-openapi-validate:latest

# --- Aggregierte Gates -----------------------------------------------------

gates: lint format-check typecheck arch-check test-unit coverage-gate coverage-gate-critical dep-audit noqa-gate spdx-check
	@echo "[gates] mandatory A-1 gates green: lint, format-check, typecheck (mypy --strict, ADR 0005), arch-check (19 contracts), test-unit, coverage-gate ($(COVERAGE_THRESHOLD)% line / $(COVERAGE_BRANCH_THRESHOLD)% branch), coverage-gate-critical ($(CRITICAL_COVERAGE_THRESHOLD)% critical domain), dep-audit, noqa-gate (Slice 027 — no # noqa marker), spdx-check (M4 Welle 6b — GPL-3.0-only-Header in IEC-61850-Boundary)"

# M1-Closure-Hinweis (2026-05-17): `ci` und `fullbuild` benoetigen
# heute ein explizites `CRITICAL_COV_TARGETS`-Override, weil der
# Default-Pfad das M2-`devices/battery`-Target enthaelt, das in M1
# nicht existiert. M2 schliesst die Default-Linie.
#
# Empfohlener Override (M1-Closure-Stand):
#   make fullbuild CRITICAL_COV_TARGETS="\
#       src/grid_gym/hexagon/core/domain \
#       src/grid_gym/hexagon/ports/driven \
#       src/grid_gym/adapters/driven/random_mt \
#       src/grid_gym/hexagon/core/simulation \
#       src/grid_gym/hexagon/core/scenario \
#       src/grid_gym/hexagon/core/replay \
#       src/grid_gym/adapters/driving/http_api"
#
# Bei `coverage-gate-critical`-Fail druckt der Aggregator den Hinweis
# noch einmal vor dem Exit, damit Neueinsteiger den Override-Pfad
# nicht uebersehen.

define M1_OVERRIDE_HINT
echo ""; \
echo "[ci] Hinweis (M1-Closure 2026-05-17): default CRITICAL_COV_TARGETS"; \
echo "[ci] enthaelt 'devices/battery' (M2-Verantwortung). M1-Closure"; \
echo "[ci] erwartet expliziten Override. Beispiel-Aufruf:"; \
echo "[ci]   make fullbuild CRITICAL_COV_TARGETS=\"src/grid_gym/hexagon/core/domain \\"; \
echo "[ci]       src/grid_gym/hexagon/ports/driven \\"; \
echo "[ci]       src/grid_gym/adapters/driven/random_mt \\"; \
echo "[ci]       src/grid_gym/hexagon/core/simulation \\"; \
echo "[ci]       src/grid_gym/hexagon/core/scenario \\"; \
echo "[ci]       src/grid_gym/hexagon/core/replay \\"; \
echo "[ci]       src/grid_gym/adapters/driving/http_api\""; \
echo "[ci] Volle Default-Gruen-Linie kommt mit M2-Geraetemodellen."
endef

ci: gates test-integration openapi-validate image-audit
	@echo "[ci] mandatory gates green + test-integration + openapi-validate + image-audit"

# `make fullbuild` ohne Override faellt heute ueber `coverage-gate-critical`.
# Der `|| (...; exit 1)`-Wrapper druckt den M1-Override-Hinweis nach dem
# Fail-Output, damit der Aggregator-Hint nicht vom Trivy-/Coverage-Output
# verdraengt wird.
fullbuild:
	@$(MAKE) ci || ( $(M1_OVERRIDE_HINT); exit 1 )
	@$(MAKE) build
	@$(MAKE) runtime
	@echo "[fullbuild] full closure: ci + runtime image + compose smoke green"

# --- Runtime ---------------------------------------------------------------

build:
	$(DOCKER_BUILD) --target runtime -t $(IMAGE_PREFIX)-runtime:latest

# Compose-Smoke: produktiv-shaped Stack hoch, /health pollen, down.
# Voraussetzung: `make build` (bereits Bestandteil dieses Targets via
# dependency) und ein `deploy/compose.yml`, das api, postgres und ui
# definiert.
#
# Welle-6-C2-Erweiterung: nach dem `/health`-Probe ein Bounded-Poll
# auf den OTLP-Collector-Health-Endpoint `http://otel-collector:13133/`
# aus dem `api`-Container heraus. Der Collector-Container ist
# distroless (`gcr.io/distroless/static-debian12:nonroot`) — kein
# eigener Healthcheck moeglich, weil weder wget noch nc noch shell
# vorhanden sind. Stattdessen pollt der API-Container die OTel-
# `health_check`-Extension via Python-stdlib (urllib).
runtime: build
	@if [ ! -f $(COMPOSE_FILE) ]; then \
		echo "[runtime] $(COMPOSE_FILE) fehlt — wird mit der Deploy-Slice angelegt"; \
		exit 1; \
	fi
	$(DOCKER) compose -f $(COMPOSE_FILE) up -d --wait --wait-timeout 60
	@echo "[runtime] stack is up; probing /health"
	$(DOCKER) compose -f $(COMPOSE_FILE) exec -T api curl --fail --silent --show-error http://localhost:8080/health
	@echo "[runtime] /health ok; probing otel-collector :13133"
	$(DOCKER) compose -f $(COMPOSE_FILE) cp tools/wait_otel_collector.py api:/tmp/wait_otel_collector.py
	$(DOCKER) compose -f $(COMPOSE_FILE) exec -T api python /tmp/wait_otel_collector.py
	@echo "[runtime] otel-collector ok; tearing down"
	$(DOCKER) compose -f $(COMPOSE_FILE) down -v --remove-orphans

test-container: runtime
	@echo "[test-container] runtime smoke green"

# --- Maintenance -----------------------------------------------------------

# Lock-Refresh: nach Aenderung von pyproject.toml-Dependencies neu
# aufloesen. uv.lock MUSS gemeinsam mit der pyproject.toml-Aenderung
# committet werden, damit `--frozen`-Builds gruen bleiben (Supply-Chain-
# Defense, analog `packages.lock.json` in bess-ems).
# Laeuft im projekteigenen `base`-Stage (python:$(PYTHON_VERSION)-slim
# + uv $(UV_VERSION) gepinnt) — gleiche Toolchain wie CI. Das
# distroless `ghcr.io/astral-sh/uv:$(UV_VERSION)`-Image taugt nicht
# fuer `uv lock`, weil dort weder Python noch eine Shell vorhanden ist.
lock-refresh:
	$(DOCKER_BUILD) --target base -t $(IMAGE_PREFIX)-base:latest
	$(DOCKER) run --rm \
		--user "$$(id -u):$$(id -g)" \
		-e UV_CACHE_DIR=/tmp/uv-cache \
		-v "$$(pwd)":/src -w /src \
		$(IMAGE_PREFIX)-base:latest \
		uv lock

# Base-Image-Patch-Pull (Trigger 015, M2 Welle 0b).
# Zieht das pinned `python:$(PYTHON_VERSION)-slim`-Base-Image und das
# `ghcr.io/astral-sh/uv:$(UV_VERSION)`-Image explizit aus der Registry.
# Ergaenzt das `apt-get upgrade -y` im runtime-Stage: `rebase-base`
# refresht den Base-Layer und macht damit `apt-get update` schneller
# (und gleichzeitig die uv-Toolchain aktuell). Bleibt `make
# image-audit` (trivy `--ignore-unfixed`) trotz `rebase-base` rot,
# eskaliert das auf einen Folge-Trigger fuer ein eigenes
# `grid-gym-base:debian-13-patched`-Image (Trigger 015 Option B, M6).
rebase-base:
	$(DOCKER) pull python:$(PYTHON_VERSION)-slim
	$(DOCKER) pull ghcr.io/astral-sh/uv:$(UV_VERSION)
	@echo "[rebase-base] base images refreshed — naechster docker build nutzt die aktuellen Layer."

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
