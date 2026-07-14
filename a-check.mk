# a-check.mk — Architektur-Gate via a-check, zum `include` in das
# Makefile des konsumierenden Repos. Erzeugt von `a-check --print-mk`.
#
# A_CHECK_IMAGE wird beim Release auf `@sha256:…` digest-gepinnt.
A_CHECK_IMAGE ?= ghcr.io/pt9912/a-check@sha256:203df7ab02ec68db5f77f77660fe12523dad9fd48a6c84b95aabb080ec30de24

.PHONY: a-check a-check-graph
a-check: ## Architektur: Hexagon-Regeln via a-check (netzlos, read-only).
	docker run --rm --network none -v "$(CURDIR)":/src:ro $(A_CHECK_IMAGE) /src

a-check-graph: ## Architektur-Graph (Mermaid) aus .a-check.yml auf stdout (read-only, kein Scan).
	docker run --rm --network none -v "$(CURDIR)":/src:ro $(A_CHECK_IMAGE) --print-graph /src
