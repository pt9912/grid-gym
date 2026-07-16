# 065 — OTel-Collector CVE-2026-39822: Temp-Deferral bis go1.26.5-Stable

**Status:** Open — vulnignore-Temp-Deferral aktiv, wartet auf Upstream-Fix
(zuletzt re-geprueft **2026-07-14**, weiter blockiert — siehe Re-Checks)
**Datum:** 2026-07-11
**Quelle:** Fullbuild-CI rot (`make image-audit`) auf `c11ca51`; CVE-Drift analog
[`033`](../done/033-otel-collector-go-stdlib-cve-bump.md).

---

## Befund

`make image-audit` (Fullbuild-Gate, [`GG-QG-002`](../../../../spec/spezifikation.md#gg-qg-002))
meldet im gepinnten `OTEL_COLLECTOR_IMAGE` (`otel/opentelemetry-collector-contrib:0.154.0`,
`Makefile` Z.35 / `deploy/compose.yml`):

```
otelcol-contrib (gobinary)
Total: 1 (HIGH: 1, CRITICAL: 0)
CVE-2026-39822  stdlib  go1.26.4  fixed in 1.26.5  — os.Root Symlink-Following / dir-traversal
```

Kein gepatchtes Collector-Image verfuegbar: die neueste Stable `0.156.0` ist
ebenfalls gegen go1.26.4 gebaut (getestet), `0.157.0` existiert bislang nur als
nightly. Ein Versions-Bump loest es aktuell NICHT. grid-gyms eigenes
Runtime-Image ist nicht betroffen (Python, nicht Go).

## Temp-Deferral (angewandt)

`deploy/security/vulnignore.yaml`-Eintrag `CVE-2026-39822`
(`scope: otel-collector`, `expires: 2026-10-09` = +90 Tage,
[`ADR 0044`](../../adr/0044-generated-trivyignore-permit.md)-Max). Begruendung:
os.Root-Traversal in einem Compose-internen Telemetrie-Sidecar ohne
untrusted-Filesystem-Pfad = begrenzte Exploitierbarkeit; befristet bis
Upstream-Fix. Pflicht-Begleit-Trigger dieses Eintrags
([`ADR 0043`](../../adr/0043-image-audit-strategy.md) §2.2 /
[`ADR 0044`](../../adr/0044-generated-trivyignore-permit.md) §2.1).

**Invarianten-Vorbehalt (Review-N3):** Die Nicht-Exploitierbarkeit gilt, SOLANGE
die Collector-Config **network-ingress + static-path-output** bleibt (`deploy/
otel-collector-config.yaml`: `receivers: [otlp]`, `file`-Exporter mit statischem
Pfad). Wird vor `expires` ein pfad-aus-Payload-Komponente ergaenzt (`filelog`-
Receiver, `filestorage`-Extension, path-templated Exporter), ist die Traversal
u. U. erreichbar → dann Deferral SOFORT neu bewerten, nicht bis `expires` warten.

## Aufloesung (Wandert nach `done/`)

Bump `OTEL_COLLECTOR_IMAGE` (`Makefile` + `deploy/compose.yml`) auf die erste
Collector-Stable, deren gobinary gegen **go1.26.5+** gebaut ist (`0.157.0+`
erwartet), Trivy-Re-Scan 0 HIGH/CRITICAL, vulnignore-Eintrag entfernt — analog
[`033`](../done/033-otel-collector-go-stdlib-cve-bump.md). Vor `expires`
(2026-10-09) erneuern ODER aufloesen, sonst bricht `make render-trivyignore`.

## Aktivierungs-Kriterium

Verfuegbarkeit einer OTel-Collector-Stable mit go1.26.5+ ODER `expires`-Ablauf.

## Re-Checks

- **2026-07-14** (Trigger-Bearbeitung): Aktivierungs-Kriterium weiter NICHT
  erfuellt. Neueste Stable `0.156.0` (2026-07-07) ist gobinary-verifiziert gegen
  `go1.26.4` gebaut → CVE-2026-39822 unveraendert HIGH (containerisierter
  Trivy-`0.71.1`-Scan, `--severity HIGH,CRITICAL --ignore-unfixed`; Trivy nennt
  `1.25.12, 1.26.5, 1.27.0-rc.2` als Fixed-Versions). Ein Bump auf 0.156.0 loest
  es NICHT; `0.157.0` weiter nur nightly. **Deferral-Invariant (Review-N3)
  re-bestaetigt:** `deploy/otel-collector-config.yaml` ist unveraendert reiner
  OTLP-gRPC-Ingress (`receivers: [otlp]`) + statischer `file`-Exporter (kein
  `filelog`-Receiver, keine `filestorage`-Extension, kein path-templated
  Exporter) → kein os.Root-/Traversal-Pfad erreichbar; Deferral bleibt sachlich
  gueltig, `expires 2026-10-09` unkritisch (~3 Monate). **Forecast (belastbar):**
  `0.157.0-nightly.5db62cf` ist gobinary-verifiziert gegen `go1.26.5` gebaut und
  Trivy-clean (0 HIGH/CRITICAL) → sobald 0.157.0 **stable** erscheint, ist die
  Aufloesung ein sauberer 1:1-Bump analog
  [`033`](../done/033-otel-collector-go-stdlib-cve-bump.md).
