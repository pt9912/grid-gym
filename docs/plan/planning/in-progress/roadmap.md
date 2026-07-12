# Roadmap — grid-gym

**Status:** Slice-getrieben
([`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md)). **M1..M8
abgeschlossen** — die MUSS-/SOLLTE-Roadmap ist geliefert, **v0.2.0 released**
(MVP-Linie); aktuelles Release **v0.5.0** (2026-07-12, Field-Server-Surface).
**Aktiver Slice:**
[`075`](075-field-server-inbound-write-command.md) (Field-Server
Inbound-Write→`Command`). Zuletzt abgeschlossen 074/073 (Field-Server, v0.5.0),
davor:
[`072`](../done/072-gg-fault-002-stale-data.md) (dedizierter `stale_data`-
Quality-Fault →
[`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002) erfuellt;
[`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) §2.3,
Slice B = Last-Value-Cache + opt-in Snapshot; released **v0.4.0**),
[`071`](../done/071-gg-fault-003-nan-injection.md) (metrik-adressierter
`nan_injection`-Quality-Fault →
[`GG-FAULT-003`](../../../../spec/lastenheft.md#gg-fault-003) erfuellt;
[`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) `Accepted`,
Slice A = Foundation + NaN; released **v0.4.0**) und
[`070`](../done/070-gg-fault-004-frequency-drop.md) (dedizierter
`frequency_drop`-Fault →
[`GG-FAULT-004`](../../../../spec/lastenheft.md#gg-fault-004) erfuellt;
released **v0.4.0**).
**Aktiver Arc:** die **Field-Server-Surface**
([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md),
`Accepted`, released **v0.5.0**; zwei Schwester-Ports in der Kompositions-Schicht,
nach zwei adversarialen Reviews revidiert) — schliesst die Asymmetrie „alle
Protokolladapter sind Client/Master"
([`ADR 0030`](../../adr/0030-device-protocol-port-surface.md)) und macht ein
externes EMS (`bess-ems`) als System-under-Test anbindbar
([`GG-TEST-004`](../../../../spec/lastenheft.md#gg-test-004) HIL-Konkretisierung,
keine eigene `GG-*`-ID). **Beide Schwester-Ports done + review-gehaertet
(2026-07-12):** Push-Seite
[`073`](../done/073-field-server-mqtt-publish-bridge.md) (`FieldPublishPort`/MQTT)
+ Pull-Seite [`074`](../done/074-field-server-modbus-server-adapter.md)
(`DeviceServerPort`/Modbus-Server Read-Serving + geteilte Current-Value-
Projektion) → [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
**`Accepted`**, released als **v0.5.0** (2026-07-12). **Aktiver Slice:
[`075`](075-field-server-inbound-write-command.md)**
(Inbound-Write→Command, ausgegliedert). Offene Trigger (OTel-Bump, Vorwaerts-
Traceability, `a-check`) sind noch nicht als Slice geschnitten.
**Stand:** 2026-07-12

**Bezug:** [Lastenheft](../../../../spec/lastenheft.md),
[Architektur](../../../../spec/architecture.md),
[`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) (Planungsmodell),
[`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md) (Doku-/
Planungsstruktur), [`carveouts.md`](carveouts.md).

---

## 1. Zweck

Diese Roadmap fuehrt (a) die **gelieferte Historie** (Meilensteine M1..M8, jetzt
eingefroren) als Nachschlag-Index und (b) die **aktive/geplante Slice-Arbeit**.

Seit [`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) ist das
Planungsmodell **slice-getrieben**: Wellen/Slices sind die oberste Einheit, es
werden **keine neuen Meilensteine (`M{N}`)** mehr eroeffnet, und die
Release-Entscheidung faellt **pro Slice** (§5).

**`M{N}`-Marker sind historisch.** Die bestehenden `M{N}`-Statusmarker in
`spec/protocol_profiles.md` (Adapter-Provenienz) und in
`spec/persistence-schema.yaml` bleiben als Aufzeichnung eingefroren; neue
Anforderungs-Erfuellung wird per **Slice-Referenz** (bzw. Release-Version)
eingetragen. Die frueher `M{N}`-markierte
[`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Implementierungs-Matrix
(§27.2 in `docs/plan/traceability.md`, seit Slice 063 dort) wurde in Slice 066
entfernt und an `make doc-trace` delegiert.

---

## 2. Konvention

- Neue Arbeit = **Slice** (`NNN-slug.md`, repo-weit fortlaufende dreistellige
  Nummer; Muster `041`/`045`/`051`/`053`), grosse Slices sub-gesliced als
  `NNN-a`/`NNN-b`.
- Lifecycle: `open → next → in-progress → done`
  ([`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md)).
- Jeder Slice-Plan traegt Akzeptanzkriterien, einen Verifikationspfad und ein
  **Release-Feld** (§5).
- Abgeschlossene Slices wandern per Self-Move nach [`../done/`](../done/) mit
  Closure-Notiz.

---

## 3. Gelieferte Historie (M1..M8, eingefroren)

Die Meilenstein-Ebene ist Historie; das vollstaendige Detail (Wellen,
Abnahme-Belege, ADR-Sweeps) lebt in den `M{N}-results.md`-Closure-Docs unter
[`../done/`](../done/). Diese Tabelle ist der Nachschlag-Index.

| Meilenstein | Lieferziel | Abschluss | Closure-Doc |
| ----------- | ---------- | --------- | ----------- |
| M1 | Tick-Loop-Spine | 2026-05-17 | [`M1-tick-loop-results.md`](../done/M1-tick-loop-results.md) |
| M2 | Geraetemodelle | 2026-05-20 | [`M2-devices-results.md`](../done/M2-devices-results.md) |
| M3 | Faults + Multi-Agent + Observability | 2026-05-25 | [`M3-results.md`](../done/M3-results.md) |
| M4 | Protokolladapter (MQTT/Modbus/OPC-UA/DNP3/IEC-61850) | 2026-06-01 | [`M4-results.md`](../done/M4-results.md) |
| M5 | UI + Demo | 2026-06-04 | [`M5-results.md`](../done/M5-results.md) |
| M6 | Performance + Security + CI/CD-Haertung | 2026-06-08 | [`M6-results.md`](../done/M6-results.md) |
| M7 | MVP-Abschluss → **v0.1.0** | 2026-06-12 | [`M7-results.md`](../done/M7-results.md) |
| M8 | SOLLTE-Geraete & Netz → **v0.2.0** | 2026-07-01 | [`M8-results.md`](../done/M8-results.md) |

Der MVP-Abnahmescope und die architektonischen Vorbedingungen sind mit
M7/M8 erfuellt; Detail in [`M7-results.md`](../done/M7-results.md) bzw.
[`M8-results.md`](../done/M8-results.md).

---

## 4. Aktive / geplante Slices

**Aktiver Slice:** [`075`](075-field-server-inbound-write-command.md)
(Field-Server Inbound-Write→`Command`, S0 = dedizierte Folge-ADR). Zuletzt
abgeschlossen (2026-07-12) die Field-Server-Pull-/Push-Seite
[`074`](../done/074-field-server-modbus-server-adapter.md)/[`073`](../done/073-field-server-mqtt-publish-bridge.md)
(→ **v0.5.0**), davor:
[`072`](../done/072-gg-fault-002-stale-data.md) (dedizierter `stale_data`-
Quality-Fault →
[`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002) „Stale Data"
erfuellt: der `QualityFaultRuntime` fuehrt einen per-`(Ziel, Metrik)`-Last-
Value-Cache und liefert aktiv den letzten gueltigen Wert weiter, bis `max_age`
ueberschritten ist → `quality=stale` — **kein** Alarm; der Cache ueberlebt den
Snapshot opt-in (byte-identisch ohne Vorwert);
[`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) §2.3
(Slice B, obenauf der Slice-071-Foundation); released **v0.4.0**); davor
[`071`](../done/071-gg-fault-003-nan-injection.md) (metrik-adressierter
`nan_injection`-Quality-Fault →
[`GG-FAULT-003`](../../../../spec/lastenheft.md#gg-fault-003) „NaN-Injection"
erfuellt: spine-interner `QualityFaultRuntime` + `_apply_quality_fault_stage`
markiert matchende `(Ziel, Metrik)`-Punkte mit Sentinel `Decimal("0")` +
`quality=nan` + einmaligem `quality_fault_nan_injection`-Alarm — kein
numerischer NaN, Geraet unberuehrt;
[`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) `Accepted`
(Slice A = Foundation + NaN; Last-Value-Cache + `stale_data`/[`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002) =
Slice B); opt-in, byte-identisch fuer Szenarien ohne den Fault; released
**v0.4.0**) +
[`070`](../done/070-gg-fault-004-frequency-drop.md) (dedizierter
`frequency_drop`-Fault auf dem `grid_connection`-Geraet →
[`GG-FAULT-004`](../../../../spec/lastenheft.md#gg-fault-004) „Frequenzabfaelle"
erfuellt: Payload `frequency_hz`/`delta_hz`, opt-in Grid-Telemetrie + Alarm,
byte-identisch fuer Szenarien ohne den Fault; released **v0.4.0**) +
[`066`](../done/066-traceability-recut-delegate-27-2.md) (traceability.md-Re-Cut —
§27.2 „Anforderung→Implementierung" inkl. Status-Matrix entfernt und an
`make doc-trace` delegiert; [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Amendment; §27.1/§27.3 bleiben kuratiert) +
[`064`](../done/064-rtm-titel-html-anker.md) (RTM-Titel via HTML-Anker —
`make doc-trace`-Titel-Spalte gefuellt, ohne bestehende `#gg-...`-Verweise oder
Accepted-ADRs zu brechen; advisory, kein Release) +
[`063`](../done/063-traceability-doc-auslagern.md) (§27-Traceability aus
`lastenheft.md` nach `docs/plan/traceability.md` ausgelagert — Vertrag jetzt
abwaerts-verweis-frei; Trace-MUSS-Anforderung amendiert, §27-`exclude-sections`
raus) +
[`060`](../done/060-lastenheft-traceability-resync.md) (Lastenheft §27.2-Status-
Re-Sweep: 36 stale `🔲` → `✓`; 2 MUSS-Luecken aufgedeckt → Trigger
[`061`](../open/061-replay-time-multipliers.md)/[`062`](../open/062-run-deletion-operation.md)) +
[`059`](../done/059-hygiene-bundle-adr-index-app-version.md) (Hygiene-Buendel
056+057: ADR-Index-Status-Sync + App-/Tool-Version-Single-Source; Runtime-Delta
→ Release **v0.3.1**) +
[`058`](../done/058-marker-sensor-drift-guard.md) (Sensor-Marker-Drift-Guard
Meta-Test, Follow-up zu 054, Test-only) +
[`054`](../done/054-pytest-marker-drift-sensor-targets.md)
(pytest-Marker-Sweep `determinism`/`fault`, Test-only); davor
[`055`](../done/055-profile-preflight-e2e-sensor.md) (E2E-Sensor
produktiver Profil-Pfad → Replay-Preflight; Slice-038-Review-INFO-
Aufloesung, Test-only, Release **nein**) und
[`038`](../done/038-gg-term-002-003-full-equality-matrix.md) (volle
[`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/003-Equality-Matrix,
[`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) `Accepted` →
Release **v0.3.0**, 2026-07-03 — erster Release-Zyklus des
slice-getriebenen Modells); davor
[`053`](../done/053-planungsmodell-slices-ohne-meilensteine.md) (slice-first-
Umstellung, [`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md)).

**Aktiver Arc** (2026-07-12): **Field-Server-Surface** (drei Slices auf
[`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md),
`Accepted`, Design-first) —
[`073`](../done/073-field-server-mqtt-publish-bridge.md) (`FieldPublishPort`,
Push + Kompositions-Schicht-Naht + grid-gym↔`bess-ems`-Integrationsgeschirr) und
[`074`](../done/074-field-server-modbus-server-adapter.md)
(`DeviceServerPort`, Modbus-Server Read-Serving + geteilte Current-Value-
Projektion) sind **done + review-gehaertet → [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) `Accepted`**,
**released als v0.5.0** (2026-07-12); **aktiv** ist jetzt
[`075`](075-field-server-inbound-write-command.md) (Inbound-Write→Command,
**ausgegliedert** samt Folge-ADR, weil Live-Writes das geschlossene Self-Replay
brechen). Der Entwurf wurde nach zwei adversarialen Reviews von einem geteilten
Kern-`TickLoop`-Port auf **zwei Schwester-Ports in der Kompositions-Schicht**
revidiert (Fan-out lebt im API-Prozess-Driver, nicht im Kern-Loop,
[`ADR 0012`](../../adr/0012-api-simulation-two-processes.md)). Motivation ist die
HIL/SUT-Anbindung ([`GG-TEST-004`](../../../../spec/lastenheft.md#gg-test-004)).
**Anforderungs-Verankerung entschieden (2026-07-12):** HIL-Konkretisierung von
[`GG-TEST-004`](../../../../spec/lastenheft.md#gg-test-004) (keine eigene
`GG-*`-ID; [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
§7) — die Slices liegen aktivierungsbereit in `next/`. Die
GG-FAULT-Konsolidierung (002/003/004) ist mit
[`070`](../done/070-gg-fault-004-frequency-drop.md)/[`071`](../done/071-gg-fault-003-nan-injection.md)/[`072`](../done/072-gg-fault-002-stale-data.md)
vollstaendig geliefert; [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md)
ist beidseitig (Slice A + B) eingeloest. Offene Trigger (OTel-Collector-Bump,
Vorwaerts-Traceability, neues `a-check`-Tool) sind notiert, aber noch nicht als
Slice geschnitten.

**Vorheriger Kandidat erledigt:** das Hygiene-Buendel der Slice-038-Session
([`054`](../done/054-pytest-marker-drift-sensor-targets.md)/[`058`](../done/058-marker-sensor-drift-guard.md)
+ [`059`](../done/059-hygiene-bundle-adr-index-app-version.md) = 056+057) ist
komplett geliefert (057-Runtime-Delta → **Release v0.3.1**).

Weitere trigger-getriebene Folgearbeit + Aktivierungs-Bedingungen:
[`../open/`](../open/) (Trigger-Watch). Cross-Slice-Carveouts
(Anti-Scope + Erbschaft): [`carveouts.md`](carveouts.md).

---

## 5. Release-Modell (pro Slice)

Seit [`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) faellt
die Release-Entscheidung **pro Slice**: jeder Slice-Plan traegt ein DoD-Feld
„Release-Entscheidung: ja/nein (+ SemVer-Ziel)".

- **`nein`** → das Delta sammelt unter [`CHANGELOG.md`](../../../../CHANGELOG.md)
  `[Unreleased]`.
- **`ja`** → der Abschluss-Commit schneidet den Tag (`pyproject`-Bump +
  CHANGELOG-Finalisierung + `v*.*.*`-Tag → `release.yml`), gebunden an die Regel
  „kein Doku-only-Release" (Runtime-Delta-Pflicht) + `make fullbuild` vor dem
  Tag. SemVer folgt dem Delta (Minor bei additiven Features, Patch bei Fixes).

Aktuelles Release: **v0.5.0** (2026-07-12, Field-Server-Surface —
Slices 073/074 auf [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)).
