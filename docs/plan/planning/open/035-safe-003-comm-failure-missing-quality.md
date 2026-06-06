# 035 — `GG-SAFE-003` Adapter-Kommunikationsausfall → `MISSING`/`STALE` + Alarm (partial Lücke)

**Status:** Open — partial Substanz-Lücke aus M6-Welle-5a-Audit
**Datum:** 2026-06-06
**Quelle:** M6-Welle-5a-C2 (Quality-Pipeline-Audit; siehe
`docs/user/safe-001-004-quality-pipeline.md`).

---

## Lastenheft-Akzeptanz

`GG-SAFE-003` MUSS (Lastenheft Z. 1365-1371):

> Kommunikationsausfaelle MUESSEN erkannt werden.
>
> Akzeptanz: Kommunikationsausfaelle erzeugen einen
> dokumentierten Fehlerstatus, betroffene Telemetrie wird als
> `missing` oder `stale` markiert und ein Alarm mit Ziel,
> Startzeit und Ursache wird erzeugt.

## Substanz-Stand (Welle-5a-Audit 2026-06-06)

**Teil-produktiv** (decken nur Sub-Faelle, nicht den vollen
Akzeptanz-Umfang):

- **`SmartMeterDevice` emittiert `Quality.MISSING`** wenn
  Source-Devices noch nicht via `attach_sources(...)`-Hook
  attached sind (`hexagon/core/devices/smart_meter/model.py:202`
  + ADR 0018 §2.3). Das ist **Konfigurations-Pre-Attach-
  Zustand**, NICHT „Kommunikationsausfall" im Sinne von
  Adapter-Lesefehler.
- **Protocol-Adapter (`protocol_opcua`/`protocol_iec61850`)
  emittieren `Quality.INVALID`** fuer Lese-String-Faelle
  (`protocol_opcua/_port.py:312`, `protocol_iec61850/_port.
  py:368`). Das deckt Schema-/Typ-Fehler, **NICHT**
  Verbindungs-Verlust.

**Fehlend**:

- **Real-Kommunikations-Ausfall-Erkennung**: kein Adapter hat
  Substanz fuer „Verbindung verloren mid-flight" mit Quality-
  Emission `MISSING` (oder `STALE`).
- **Alarm mit Ziel/Startzeit/Ursache**: weder das `SmartMeter`-
  noch die Protocol-Adapter-Pfade emittieren bei
  Quality.MISSING/INVALID einen typisierten Alarm-Datensatz
  via `AlarmStreamPort`. Acceptance-Pflicht „Alarm mit Ziel,
  Startzeit und Ursache" ist nicht abgedeckt.

Welle-5a-C2-Smoke-Test (`tests/integration/test_m6_welle_5a_
safe_001_004_smoke.py::test_safe_003_comm_failure_emits_
missing_or_stale`) ist deshalb `pytest.skip` mit Pointer auf
diesen Trigger; ein Sub-Smoke verifiziert nur die existierende
Teil-Substanz (SmartMeter-pre-attach).

## Erwartete Lieferung

Eigener Slice (M6-Welle-5a-Folge oder spaeter):

1. **Adapter-Lifecycle-Hook fuer Verbindungs-Verlust**: pro
   Protocol-Adapter (`protocol_opcua`, `protocol_iec61850`,
   `protocol_modbus`, `protocol_dnp3`, `protocol_mqtt`) wird
   ein Hook in `start()`/`stop()`/`read()`-Pfaden hinzugefuegt,
   der bei Verbindungsverlust den Status emittiert.
2. **Quality-Emission `MISSING` oder `STALE`** fuer alle
   Telemetrie-Points eines betroffenen Adapter-Targets nach
   Verbindungsverlust. Konkrete Wahl pro Adapter-Type begruendet
   in einer Welle-Decision-Liste.
3. **Alarm-Emission ueber `AlarmStreamPort`**: bei Verbindungs-
   Verlust wird ein typisierter `Alarm` mit `code="adapter_
   communication_lost"`, `severity="warning"` (oder hoher per
   Adapter-Typ), `target=<device_id>`, `simulation_time_ms`-
   Startzeit und `message=<Ursache>` emittiert.
4. **NEU Smoke-Tests pro Adapter-Familie**: end-to-end-
   Verifikation pro Protocol-Adapter (vorhandene Test-
   Sibling-Infra in `tests/integration/`).
5. **Doku-Update** in `docs/user/safe-001-004-quality-
   pipeline.md` (Status-Spalte fuer SAFE-003 von „partial
   Lücke" auf „produktiv").

## Aktivierung

Aktivierung erfolgt bei einer der folgenden Bedingungen:

1. **Reale-Compose-Demo-Pfad** mit Protocol-Adapter aktiviert
   (heute `--extra iec61850` nur Test-Sibling; aber
   Maintainer-Druck koennte das Demo-relevant machen).
2. **M6-Welle-6-Deploy-Hardening**-Material falls IEC-Smoke-
   Pfad-B aktiviert wird (Trigger 009-Erbschaft).
3. **Compliance-/Stakeholder-Druck** auf vollstaendige
   Adapter-Lifecycle-Quality-Substanz.
4. **M6-Welle-7-Closure-Sweep**-Material falls bis dahin
   nicht aufgeloest.

## Konsequenz wenn ungeloest

- `GG-SAFE-003`-Akzeptanz bleibt **partial erfuellt**
  (SmartMeter-pre-attach + Protocol-Adapter-String-Reads;
  echte Kommunikationsausfall-Detection fehlt).
- M6-Welle-5a `tests/integration/test_safe_003_*` Smoke bleibt
  `pytest.skip` fuer den vollen Umfang; Sub-Smoke fuer
  Teil-Substanz bleibt aktiv.
- `docs/user/safe-001-004-quality-pipeline.md` zeigt SAFE-003
  als „partial Lücke" mit Pointer auf diesen Trigger.
- M6-Closure-DoD (`make gates`/`make fullbuild`) bleibt
  unbeeinflusst.

## Bezuege

- [`../in-progress/M6-welle-5a.md`](../in-progress/M6-welle-5a.md)
  §3 Welle-5a-D-3 (Hybrid-Strategie: substantielle Lücken →
  `open/`-Trigger).
- [`../../../user/safe-001-004-quality-pipeline.md`](../../../user/safe-001-004-quality-pipeline.md)
  Audit-Tabelle mit Status-Spalte „partial Lücke" fuer SAFE-
  003.
- [`../../../../spec/lastenheft.md §20 GG-SAFE-003`](../../../../spec/lastenheft.md)
  — Lastenheft-Akzeptanz-Quelle.
- [`../../adr/0018-smart-meter-device-pattern.md`](../../adr/0018-smart-meter-device-pattern.md)
  §2.3 SmartMeter-pre-attach-MISSING-Substanz (Teil-produktiv).
- [`../../adr/0024-observability-port-trio.md`](../../adr/0024-observability-port-trio.md)
  + [`../../adr/0040-alarm-aggregation-and-stream-port.md`](../../adr/0040-alarm-aggregation-and-stream-port.md)
  — Alarm-Emission-Vorbild via `AlarmStreamPort`.
