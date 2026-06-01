# Vendored Static-Assets — M5 Welle 2

Dieses Verzeichnis enthaelt vendored Static-Assets, die das
UI-Driving-Adapter (`adapters/driving/ui/`) zur Laufzeit
unter `/static/*` ausliefert.

**Quelle pattern:** Vendoring statt CDN gemaess
[ADR 0036 §2.1](../../../../../../docs/plan/adr/0036-ui-stack-choice.md)
(„Bundle-Auslieferungs-Pattern: vendored Static-Asset, kein
CDN") + Welle-0-Decision 8 (siehe
[`done/M5-welle-0.md §3`](../../../../../../docs/plan/planning/done/M5-welle-0.md)).
Begruendung: Offline-Reproduzierbarkeit fuer
`GG-DEMO-001..008`, keine externe Network-Dependency in
`docker compose up`, deterministischer Bundle-Hash fuer
Reproduzierbarkeits-Belege.

## Pflege

Aktualisieren erfolgt ausserhalb des Docker-only-Buildpfads
als **einmalige Pflegeaktion** des Maintainers (siehe
Memory `feedback_docker_only`: lokale Network-Calls sind
fuer Build/Test verboten, eine Pflege-Operation wie das
Vendoring ist davon ausgenommen). Pflegeaktion umfasst:

1. Datei via `curl -fsSL <url> -o <pfad>` herunterladen.
2. SHA256-Hash via `sha256sum <pfad>` berechnen und mit
   der hier dokumentierten Reference vergleichen.
3. `pyproject.toml`-Kommentar im UI-Block-Bereich falls
   Major-Version-Wechsel.
4. Tests `make test-unit` + `make test-integration`
   gegen die neue Version laufen lassen.
5. Diesen Eintrag mit neuer Version + SHA256 + Datum +
   Upstream-URL aktualisieren; gepflegt-am-Datum unten
   im Footer schreiben.

## Pinned Assets

### htmx.min.js — HTMX 2.0.9

- **Version:** 2.0.9 (latest stable 2.x; 4.0.0-beta ist
  noch Beta-Linie und nicht produktiv-reif).
- **Upstream:** https://github.com/bigskysoftware/htmx/releases/tag/v2.0.9
- **CDN-Source:** https://cdn.jsdelivr.net/npm/htmx.org@2.0.9/dist/htmx.min.js
- **Lizenz:** MIT (Zero-Clause-BSD-aequivalent; vereinbar
  mit grid-gym-MIT-Lizenz).
- **Size:** 51,332 Bytes.
- **SHA256:** `57d9191515339922bd1356d7b2d80b1ee3b29f1b3a2c65a078bb8b2e8fd9ae5f`
- **Verwendung:** als Script-Include in `templates/base.html`
  (Defer-Load) — liefert das HTMX-Runtime fuer alle
  `hx-*`-Attribute (z. B. `hx-get`, `hx-post`,
  `hx-target`, `hx-swap`).

### chart.umd.min.js — Chart.js 4.5.1

- **Version:** 4.5.1 (latest stable 4.x).
- **Upstream:** https://github.com/chartjs/Chart.js/releases/tag/v4.5.1
- **CDN-Source:** https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js
- **Lizenz:** MIT.
- **Size:** 208,522 Bytes.
- **SHA256:** `48444a82d4edcb5bec0f1965faacdde18d9c17db3063d042abada2f705c9f54a`
- **Verwendung:** als Script-Include in `templates/base.html`
  (Defer-Load). **Welle-2-Anti-Scope:** Chart.js wird in
  Welle 2 nur vendored, aber nicht produktiv im Code
  benutzt — echte Time-Series-Charts kommen mit Welle 3
  (Live-Telemetry-Dashboard).
- **Build-Variante:** UMD (Universal-Module-Definition;
  `chart.umd.min.js` ist die Browser-globale Standard-
  Variante mit Window-`Chart`-Symbol; passt zu HTMX-
  Pattern ohne separaten Bundler).

## Sicherheits-Audit-Pfad

Bei einer M6-CVE-Triage gegen die vendored Assets kann das
SHA256-Hash-Paar oben direkt gegen ein CVE-Advisory
gestellt werden:

```
$ sha256sum src/grid_gym/adapters/driving/ui/static/*.js
```

Bei Drift: Pflegeaktion (oben) durchziehen.

## Gepflegt

- 2026-06-01 — M5-Welle-2-C2 (HTMX 2.0.9 + Chart.js 4.5.1).
