# Anwenderhandbuch: grid-gym

Handbuch-Version: 1.0
Software-Version: v0.2.0
Stand: 2026-07-01
Verantwortlich: grid-gym-Maintainer
Gültigkeitsbereich: lokale Demo-/Validierungsplattform grid-gym (Docker-Compose-Betrieb)

> **Sicherheitshinweis — bitte zuerst lesen.**
> grid-gym ist eine **reine Simulations- und Validierungsplattform**.
> Sie ist **nicht** für die Steuerung realer Anlagen oder Stromnetze
> freigegeben ([`GG-SAFE-007`](../../spec/lastenheft.md#gg-safe-007),
> [`GG-NONGOAL-001`](../../spec/lastenheft.md#gg-nongoal-001)). Alle
> Geräte, Netzmodelle und Protokoll-Adapter arbeiten gegen simulierte
> oder Test-Systeme. Verbinden Sie grid-gym niemals mit produktiven
> Feldgeräten.

---

## Inhalt

1. [Einleitung](#1-einleitung)
2. [Installation und Zugriff](#2-installation-und-zugriff)
3. [Erste Schritte](#3-erste-schritte)
4. [Aufgaben ausführen](#4-aufgaben-ausführen)
5. [Konfiguration](#5-konfiguration)
6. [Rollen und Rechte](#6-rollen-und-rechte)
7. [Fehlerbehebung](#7-fehlerbehebung)
8. [FAQ](#8-faq)
9. [Glossar](#9-glossar)
10. [Anhang](#10-anhang)
11. [Support und Kontakt](#11-support-und-kontakt)
12. [Änderungshistorie](#12-änderungshistorie)

---

## 1. Einleitung

### Zweck der Software

Mit grid-gym führen Sie **deterministische Simulationen** von
elektrischen Energiesystemen aus — Batteriespeicher (BESS),
Photovoltaik, Lasten, Netzanschluss, Smart Meter sowie weitere Geräte
und ein Netzbilanzmodell. Sie können damit:

- Steuerungs- und Betriebsstrategien lokal und offline durchspielen,
- das Verhalten bei geplanten Fehlern (Fault Injection) beobachten,
- Live-Telemetrie und Alarme in einer Web-Oberfläche verfolgen,
- Läufe **bit-genau reproduzieren** (gleicher Seed + gleiches Szenario
  → gleiches Ergebnis) und
- eine maschinenlesbare Abnahmeprüfung ausführen.

grid-gym läuft vollständig lokal in Docker-Containern. Es braucht
keine Cloud, kein Internet zur Laufzeit und keine realen Geräte.

### Zielgruppe dieses Handbuchs

Dieses Handbuch richtet sich an **Anwender, die grid-gym betreiben und
auswerten** — Fach- und Testingenieure, Integratoren sowie
QA-/Abnahme-Personal. Vorausgesetzt werden Grundkenntnisse in
Kommandozeile und Docker. Kenntnisse des grid-gym-Quellcodes sind
**nicht** nötig.

Wenn Sie grid-gym weiterentwickeln möchten, sind stattdessen die
Entwickler-Dokumente (`AGENTS.md`, `spec/`, `docs/plan/`) die richtige
Quelle.

### Voraussetzungen

- Ein Rechner mit **Docker** (inkl. `docker compose`) und **make**.
- Für Demo-Betrieb und Weboberfläche ist **kein lokales Python und
  kein `uv`** nötig — dieser Teil ist **Docker-only**. Nur die
  Abnahme `make accept`
  ([Abschnitt 4.9](#49-abnahme-und-deterministisches-replay-prüfen))
  braucht zusätzlich eine lokale `uv`-Installation.
- Ca. 2 GB freier Speicher für Images und das Postgres-Datenvolume.
- Beim ersten Start Internetzugang zum Laden der Container-Images
  (danach läuft die Demo offline).

---

## 2. Installation und Zugriff

### Systemanforderungen

| Komponente | Anforderung |
| --- | --- |
| Betriebssystem | Linux, macOS oder Windows mit Docker-Unterstützung |
| Docker | aktuelle Version mit `docker compose` |
| make | vorhanden (Standard auf Linux/macOS) |
| Freier Port | `8000` auf `127.0.0.1` (lokal) |

### Installation

grid-gym wird **nicht installiert**, sondern als Container-Stack
gestartet. Wechseln Sie in das Projektverzeichnis (das die Datei
`Makefile` enthält).

### Zugriff / Start

1. Öffnen Sie ein Terminal im Projektverzeichnis.
2. Starten Sie den Demo-Stack:

   ```bash
   make demo
   ```

3. Warten Sie, bis die Meldung erscheint:
   `[demo] /health ok; UI verfuegbar unter http://localhost:8000`
   (der erste Start kann bei kaltem Cache ~70 s dauern, weil Postgres-
   und OpenTelemetry-Images geladen werden).
4. Öffnen Sie im Browser **http://localhost:8000**.

**Ergebnis:** Die grid-gym-Weboberfläche ist erreichbar und das
Demo-Szenario ([`deploy/scenarios/gg-demo.yaml`](../../deploy/scenarios/gg-demo.yaml))
ist geladen.

### Demo stoppen

```bash
make demo-stop
```

> **Achtung:** `make demo-stop` entfernt die Postgres-Datenvolumes
> (Demo-Standard). Persistierte Läufe der aktuellen Sitzung gehen
> dabei verloren.

### Netzwerk-Bindung

Der Stack bindet die UI standardmäßig nur an `127.0.0.1` (nur der
lokale Rechner). Für eine Lab-/Remote-Demo können Sie die Bindung über
die Umgebungsvariable `GRID_GYM_DEMO_HOST_BIND` ändern (siehe
[Abschnitt 5](#5-konfiguration)). Öffnen Sie die UI **nicht**
unbeaufsichtigt im Netz — es gibt keine Anmeldung (siehe
[Abschnitt 6](#6-rollen-und-rechte)).

---

## 3. Erste Schritte

### Überblick über die Oberfläche

Am oberen Rand jeder Seite finden Sie das Navigationsmenü. Es enthält
in dieser Reihenfolge:

| Menüpunkt | Was Sie dort tun |
| --- | --- |
| **Demo** | Startseite mit einer kleinen Funktionsprobe |
| **Health** | schneller Lebt-der-Dienst-Status |
| **Dashboard** | Live-Telemetrie als Tabelle und Diagramm |
| **Control** | einen Lauf pausieren, fortsetzen, stoppen |
| **Alarms** | Alarm-Historie und Live-Alarme |
| **Faults** | einen Fehler (Fault) an einem Gerät anfragen |
| **Devices** | aktuelle Gerätezustände als Tabelle |
| **System** | Lauf- und Dienststatus im Überblick |

Auf jeder Seite steht oben ein Hinweisbanner:
„Simulation only — not approved for production grid control."

> **Hinweis:** Die Menüpunkte verweisen fest auf den Demo-Lauf mit der
> Kennung `demo-run-0001`. Für eigene Läufe verwenden Sie die
> HTTP-Schnittstelle (siehe [Abschnitt 4.8](#48-einen-lauf-über-die-api-anlegen-und-starten)).

### Schneller Einstieg (5 Minuten)

1. `make demo` ausführen und **http://localhost:8000** öffnen.
2. Auf **Dashboard** klicken — nach kurzer Zeit erscheinen
   Telemetrie-Zeilen und das Zeitreihen-Diagramm füllt sich.
3. Auf **Devices** wechseln — die Gerätetabelle aktualisiert sich
   jede Sekunde.
4. Auf **Alarms** wechseln — ab Simulationszeit 600 s erscheint ein
   Last-Alarm (der Demo-Lauf löst ihn bewusst aus).
5. Fertig — Sie sehen einen laufenden, deterministischen
   Simulationslauf.

### Wichtigste Bedienkonzepte

- **Tick:** Ein Simulationsschritt. Im Demo-Szenario ist ein Tick
  1000 ms Simulationszeit lang.
- **Szenario:** Eine YAML-Datei, die Geräte, Netzmodell, Fehler und
  Agenten beschreibt (siehe [Abschnitt 5](#5-konfiguration)).
- **Lauf (Run):** Die Ausführung eines Szenarios mit einem festen
  Seed. Jeder Lauf hat eine `run_id`.
- **Determinismus:** Gleicher Seed + gleiches Szenario ergeben
  dasselbe Ergebnis. Das ist die Grundlage für das Replay.
- **Quality-Status:** Jeder Telemetriewert trägt eine Qualität
  (z. B. `GOOD`, `STALE`, `MISSING`, `LIMITED`).

---

## 4. Aufgaben ausführen

Die folgenden Anleitungen sind nach Ihren Zielen geordnet. Jede hat
Voraussetzung, Vorgehen, Ergebnis und Hinweise.

### 4.1 Live-Telemetrie ansehen (Dashboard)

**Voraussetzung:** Der Demo-Stack läuft (`make demo`), die UI ist
geöffnet.

**Vorgehen:**

1. Klicken Sie im Menü auf **Dashboard**.
2. Beobachten Sie die Tabelle **Telemetry feed** mit den Spalten
   *Device, Metric, Value, Unit, Sim time (ms), Quality, Sequence*.
3. Sehen Sie sich unter **Time series** das Diagramm an
   (Batterie-Leistung, Batterie-Ladestand, Netz-Leistung).

**Ergebnis:** Die Telemetrie aktualisiert sich live über eine
WebSocket-Verbindung; die Tabelle zeigt die letzten Werte, das
Diagramm die Zeitreihe.

**Hinweise:**

- Solange noch keine Daten fließen, steht dort „Waiting for live
  data…". Prüfen Sie in diesem Fall, ob ein Lauf aktiv ist (siehe
  [Fehlerbehebung](#7-fehlerbehebung)).
- Die Tabelle zeigt maximal die letzten 16 Zeilen, das Diagramm die
  letzten 200 Punkte.

### 4.2 Gerätezustände prüfen (Devices)

**Voraussetzung:** Ein Lauf ist aktiv.

**Vorgehen:**

1. Klicken Sie im Menü auf **Devices**.
2. Lesen Sie die Tabelle mit den Spalten *ID, Type, State, Quality*.

**Ergebnis:** Für jedes Gerät sehen Sie den wichtigsten Zustand und
den zusammengefassten Qualitätsstatus. Die Tabelle aktualisiert sich
jede Sekunde.

**Hinweise:**

- Angezeigte Zustandsgrößen je Gerätetyp: Batterie zeigt Ladestand
  und Leistung, Netzanschluss zeigt Leistung und Spannung, usw.
- Steht dort „No devices registered for this run.", läuft aktuell
  kein Lauf zu dieser `run_id`.

### 4.3 Alarme beobachten (Alarms)

**Voraussetzung:** Ein Lauf ist aktiv.

**Vorgehen:**

1. Klicken Sie im Menü auf **Alarms**.
2. Beim Öffnen wird die Alarm-Historie einmalig geladen; danach
   kommen neue Alarme live hinzu.
3. Lesen Sie die Tabelle mit den Spalten *Zeit (ms), Ziel,
   Schweregrad, Code, Nachricht, Status*.

**Ergebnis:** Sie sehen vergangene und neue Alarme, neueste zuerst.
Der Schweregrad ist `info`, `warning` oder `critical`.

**Hinweise:**

- Im Demo-Szenario erscheint ab Simulationszeit 600 s ein
  `LIMITED`-Last-Alarm (das Szenario überlagert die Last mit einem
  Lastereignis über der Nennleistung).
- „No alarms yet." bedeutet, dass bisher kein Alarm ausgelöst wurde.

### 4.4 System- und Dienststatus prüfen (System, Health)

**Voraussetzung:** Der Stack läuft.

**Vorgehen:**

1. Klicken Sie auf **System**.
2. Unter **Run Status** sehen Sie Zustand, Simulationszeit und
   Tick-Zähler des Laufs (Aktualisierung jede Sekunde).
3. Unter **Service Health** sehen Sie den Dienststatus (Aktualisierung
   alle 5 Sekunden), z. B. „Service: OK".
4. Für eine reine Lebt-der-Dienst-Anzeige klicken Sie auf **Health**.

**Ergebnis:** Sie erkennen auf einen Blick, ob der Lauf fortschreitet
und der Dienst antwortet.

### 4.5 Einen Lauf steuern (Control)

**Voraussetzung:** Ein aktiver Lauf mit laufendem Tick-Loop.

**Vorgehen:**

1. Klicken Sie im Menü auf **Control**.
2. Der Block **Status** zeigt fortlaufend Zustand, Simulationszeit und
   Tick-Zahl.
3. Nutzen Sie im Block **Actions** die Schaltflächen:
   - **Pause** — den Lauf anhalten.
   - **Resume** — einen pausierten Lauf fortsetzen.
   - **Stop** — den Lauf beenden.

**Ergebnis:** Der Lauf wechselt in den gewünschten Zustand; unter dem
Status-Block erscheint eine Bestätigung.

**Hinweise:**

- Es gibt in der Oberfläche **keinen Start-Knopf**. Das Starten eines
  Laufs erfolgt über die HTTP-Schnittstelle (siehe
  [Abschnitt 4.8](#48-einen-lauf-über-die-api-anlegen-und-starten)).
- Ein unerlaubter Übergang (z. B. **Pause** bei bereits gestopptem
  Lauf) wird mit einer Meldung abgelehnt (siehe
  [Fehlerbehebung](#7-fehlerbehebung)).

### 4.6 Einen Fehler (Fault) über die Oberfläche anfragen (Faults)

**Voraussetzung:** Ein aktiver Lauf mit registriertem Tick-Loop; Sie
kennen die Geräte-ID des Zielgeräts (z. B. `battery-1`).

**Vorgehen:**

1. Klicken Sie im Menü auf **Faults**.
2. Füllen Sie das Formular aus:
   - **Fault Type** — wählen Sie einen Fehlertyp
     (`cell_failure (Battery)` oder `voltage_drop (GridConnection)`).
   - **Target Device ID** — die Geräte-ID, z. B. `battery-1` oder
     `grid-connection-1`.
   - **Start at Tick** — ab welchem Tick der Fehler gelten soll
     (Standard 0).
   - **Duration (Ticks)** — Dauer in Ticks (Standard 10; `0` = bis zur
     Recovery).
   - **Recovery** — `auto-recover-after-N-ticks` oder
     `manual-via-command`.
3. Klicken Sie auf **Submit**.

**Ergebnis:** Bei gültiger Eingabe erscheint
„Fault registered: <Fault-ID> (accepted=true)."

**Hinweise:**

- Das Formular bietet nur die zwei Fehlertypen an, die zu den
  Demo-Geräten passen. Weitere Fehlertypen
  (`connection_loss`, `winding_fault`, `genset_fault`) sind nur für
  die entsprechenden Geräte gültig und werden im YAML-Szenario oder
  über die API genutzt.
- Der Fehlertyp muss zum Gerätetyp passen. Passt er nicht, erhalten
  Sie „Validation error: fault_invalid_type_for_target …".
- **Wichtig:** Über die Oberfläche wird der Fehler **validiert und
  quittiert**, aber nicht dynamisch in den laufenden Tick-Loop
  eingespeist. Reproduzierbare Demo-Fehler definieren Sie im
  YAML-Szenario (siehe [Abschnitt 4.7](#47-ein-eigenes-szenario-konfigurieren)).

### 4.7 Ein eigenes Szenario konfigurieren

**Voraussetzung:** Ein Texteditor; Grundverständnis von YAML.

**Vorgehen:**

1. Kopieren Sie das Demo-Szenario
   [`deploy/scenarios/gg-demo.yaml`](../../deploy/scenarios/gg-demo.yaml)
   als Vorlage.
2. Passen Sie die Abschnitte an (Details in
   [Abschnitt 5](#5-konfiguration)):
   - `simulation` — `tick_ms`, `duration_s`, `seed`.
   - `devices` — Liste der Geräte mit `id`, `type`, `params`.
   - `grid_model` — Netzbilanz-Parameter.
   - optional `faults`, `load_events`, `load_profiles`, `agents`,
     `commands`.
3. Notieren Sie **Dezimal-Felder** (Geräte-Parameter, Leistungen) als
   **Zeichenketten** (z. B. `"50"`), damit die Zahl exakt übernommen
   wird. **Ganzzahlige Steuerfelder** (`tick_ms`, `duration_s`,
   `seed`, Fault-Zeiten) notieren Sie als **echte Zahlen ohne
   Anführungszeichen** — genau wie im Demo-Szenario.
4. Legen Sie Ihre Datei in `deploy/scenarios/` ab (dieses Verzeichnis
   wird in den Container eingebunden). Am einfachsten **bearbeiten oder
   ersetzen Sie [`deploy/scenarios/gg-demo.yaml`](../../deploy/scenarios/gg-demo.yaml)**,
   da der `make demo`-Stack fest auf diese Datei zeigt. Für einen
   anderen Dateinamen passen Sie zusätzlich
   `GRID_GYM_DEMO_SCENARIO_PATH` in
   [`deploy/compose.yml`](../../deploy/compose.yml) an. Starten Sie den
   Stack anschließend neu (`make demo-stop` und `make demo`).

**Ergebnis:** Ihr Szenario wird beim Start geladen und ausgeführt.

**Hinweise:**

- Ein fester `seed` macht den Lauf reproduzierbar. Gleicher Seed +
  gleiches Szenario ergeben dasselbe Ergebnis.
- Weitere Beispielszenarien (auch für EV-Charger, Transformer, Wind
  und Diesel) liegen unter
  [`tests/integration/scenarios/`](../../tests/integration/scenarios/).

### 4.8 Einen Lauf über die API anlegen und starten

Dieser Ablauf richtet sich an **Integratoren**. Die Oberfläche bietet
kein Formular zum Anlegen von Läufen; nutzen Sie dafür die
HTTP-Schnittstelle. Eine interaktive API-Übersicht finden Sie unter
**http://localhost:8000/docs** (Swagger-UI).

**Voraussetzung:** Der Stack läuft; Sie haben ein kanonisiertes
Szenario samt `scenario_hash` (SHA-256).

**Vorgehen (Reihenfolge einhalten):**

1. **Szenario ablegen** — `POST /scenarios` mit `scenario_hash` und
   dem Szenario-Objekt (Dezimalfelder als Zeichenketten).
2. **Lauf anlegen** — `POST /runs` mit `scenario_hash`, `seed` und
   `tick_ms`. Sie erhalten die `run_id`.
3. **Lauf starten** — `POST /runs/{run_id}/start` (kein Body). Antwort
   `202` mit `status="accepted"`; der Lauf wechselt beim ersten Tick
   von `pending` nach `running`.
4. **Live verfolgen** — öffnen Sie das Dashboard mit Ihrer `run_id`
   oder abonnieren Sie den WebSocket `WS /runs/{run_id}/telemetry`.

**Ergebnis:** Ihr eigener Lauf läuft und liefert Live-Telemetrie.

**Hinweise:**

- Für ein Replay legen Sie einen zweiten Lauf mit `replay_of` =
  `run_id` des Referenzlaufs an.
- Die vollständige Endpunkt- und Fehlerliste steht im
  [Anhang](#104-http-api-referenz-auszug).

### 4.9 Abnahme und deterministisches Replay prüfen

**Voraussetzung:** ein **laufender Demo-Stack** (`make demo`), eine
lokale **`uv`-Installation** und `make`. Anders als der übrige
Demo-Betrieb ruft `make accept` `uv` auf dem Host auf und prüft den
laufenden Stack (Details in [`docs/user/abnahme-cli.md`](abnahme-cli.md)).

**Vorgehen:**

```bash
make demo      # falls der Stack noch nicht läuft
make accept
```

**Ergebnis:** grid-gym führt die Abnahme aus (Szenario-Validierung →
zwei deterministische Läufe mit Diff → Healthcheck) und gibt einen
maschinenlesbaren `AbnahmeReport` als JSON aus. Der Exit-Code ist
`0` (bestanden), `1` oder `2` (Abweichung/Fehler).

**Hinweise:**

- Details: [`docs/user/abnahme-cli.md`](abnahme-cli.md)
  ([`GG-MVP-003`](../../spec/lastenheft.md#gg-mvp-003)).
- Die manuelle Demo-Abnahme (Schritt-für-Schritt in der UI) ist in
  [`docs/user/gg-demo-008-abnahme.md`](gg-demo-008-abnahme.md)
  beschrieben.

---

## 5. Konfiguration

### 5.1 Umgebungsvariablen

| Variable | Zweck | Beispiel / Standard |
| --- | --- | --- |
| `GRID_GYM_DEMO_SCENARIO_PATH` | Pfad zum Szenario, das beim Start geladen wird | `/app/deploy/scenarios/gg-demo.yaml` |
| `GRID_GYM_DEMO_HOST_BIND` | Host-Adresse, an die die UI gebunden wird | `127.0.0.1` (nur lokal) |
| `GRID_GYM_PORT` | interner Port des Dienstes im Container | `8080` |
| `GRID_GYM_DATABASE_URL` | Postgres-Verbindung für die Persistenz | (im Compose-Stack gesetzt) |

Die Zuordnung Host-Port `8000` → Container-Port `8080` ist in
[`deploy/compose.yml`](../../deploy/compose.yml) festgelegt.

### 5.2 Szenario-Datei (YAML)

Ein Szenario beginnt mit `schema_version: "grid-gym.scenario.v1"` und
enthält:

| Abschnitt | Inhalt |
| --- | --- |
| `metadata` | `id`, `name` des Szenarios |
| `simulation` | `tick_ms` (Tick-Länge), `duration_s` (Dauer), `seed` |
| `devices` | Liste von Geräten mit `id`, `type`, `params` |
| `grid_model` | Netzbilanz (Frequenz-/Spannungs-Parameter) |
| `load_events` | zeitlich begrenzte Lastspitzen |
| `load_profiles` | Tages-/Zeitprofile je Gerät |
| `faults` | geplante Fehler (Zeitpunkt, Dauer, Typ, Ziel) |
| `agents` | regelbasierte Steuerung (z. B. BESS-Regler) |
| `commands` | tick-genau geplante Steuerbefehle an Geräte |

**Dezimal-Felder als Zeichenketten** notieren (z. B. Geräte-Parameter
und Leistungen: `"50"`, nicht `50.0`) — so bleibt die Zahl exakt.
**Ganzzahlige Felder als echte Zahlen** (ohne Anführungszeichen):
`simulation.tick_ms`, `simulation.duration_s`, `simulation.seed`, die
Fault-Zeiten (`start_simulation_time`, `duration_ms`) sowie das
`tick_ms` in `load_profiles`. Als Vorlage dient
[`deploy/scenarios/gg-demo.yaml`](../../deploy/scenarios/gg-demo.yaml).

### 5.3 Verfügbare Gerätetypen

| `type` | Bedeutung | Wichtige `params` (Beispiel) |
| --- | --- | --- |
| `battery` | Batteriespeicher (BESS) | `capacity_kwh`, `initial_soc_pct`, `max_charge_kw`, `max_discharge_kw`, `ramp_kw_per_s` |
| `pv` | Photovoltaik | `rated_power_kw` |
| `load` | Verbraucher/Last | `rated_power_kw` |
| `grid_connection` | Netzanschluss | `nominal_voltage_v`, `max_import_kw`, `max_export_kw` |
| `smart_meter` | Zähler (aggregiert) | `aggregate_device_ids`, `aggregate_metric_name` |
| `ev_charger` | Ladepunkt (E-Fahrzeug) | siehe Beispielszenario |
| `transformer` | Transformator | siehe Beispielszenario |
| `wind_turbine` | Windkraftanlage | siehe Beispielszenario |
| `diesel_generator` | Dieselgenerator | siehe Beispielszenario |

Vollständige Parameter der neueren Gerätetypen entnehmen Sie den
Beispielszenarien in
[`tests/integration/scenarios/`](../../tests/integration/scenarios/).

### 5.4 Verfügbare Fehlertypen (Faults)

| `type` | Gültig für Gerätetyp | Wirkung (Kurz) |
| --- | --- | --- |
| `cell_failure` | `battery` | reduziert die effektive Entladeleistung |
| `voltage_drop` | `grid_connection` | senkt die Spannung als Telemetrie-Effekt |
| `connection_loss` | `ev_charger` | Verbindungsverlust am Ladepunkt |
| `winding_fault` | `transformer` | Wicklungsfehler / Schutzauslösung |
| `genset_fault` | `diesel_generator` | Genset gestoppt, Leistung `0` |

Ein Fehler wird nur akzeptiert, wenn der Typ zum Gerätetyp des Ziels
passt.

### 5.5 Schnittstellen

- **Weboberfläche** — HTMX-basiert, unter `http://localhost:8000`.
- **REST-API** — Läufe, Szenarien, Steuerung, Fehler (siehe
  [Anhang](#104-http-api-referenz-auszug)).
- **WebSocket** — Live-Telemetrie (`WS /runs/{run_id}/telemetry`) und
  Live-Alarme (`WS /runs/{run_id}/alarms-stream`).
- **OpenAPI** — Maschinen-Schema unter `/openapi.json`, interaktiv
  unter `/docs`.
- **Observability** — strukturierte Logs, Metriken und Traces über
  einen OTLP-Adapter (siehe
  [`docs/user/observability.md`](observability.md)).

### 5.6 Import und Export

- **Szenario-Import:** YAML-Datei über `GRID_GYM_DEMO_SCENARIO_PATH`
  oder `POST /scenarios`.
- **Telemetrie-Persistenz:** Zeitreihen werden in Postgres
  gespeichert.
- **Replay-Export:** Ein Lauf lässt sich als Referenz für ein
  deterministisches Replay verwenden (`replay_of`), das per
  `replay_diff_status` ein Urteil liefert
  ([`GG-SAFE-006`](../../spec/lastenheft.md#gg-safe-006); Details in
  [`docs/user/replay-determinism-e2e.md`](replay-determinism-e2e.md)).
- **Release-Artefakte:** Ein offizielles Release liefert zusätzlich
  SBOM, Testberichte, Coverage und OpenAPI-Spezifikation (siehe
  Releases-Seite des Projekts).

---

## 6. Rollen und Rechte

grid-gym ist eine **lokale Einzelplatz-Demo**. Deshalb gilt:

- **Es gibt keine Anmeldung, keine Benutzerkonten und keine
  Rollen.** Alle Seiten und Endpunkte — inklusive `/docs`, der
  Steuer- und Fault-Endpunkte — sind ohne Authentifizierung
  erreichbar.
- Der Zugriff wird ausschließlich über die **Netzwerk-Bindung**
  geschützt: standardmäßig `127.0.0.1` (nur der lokale Rechner).
- Geben Sie die Oberfläche **nicht** ungeschützt in einem Netzwerk
  frei. Wenn Sie `GRID_GYM_DEMO_HOST_BIND` weiten, sichern Sie den
  Zugang mit einem vorgelagerten Reverse-Proxy oder einer Firewall
  ab.

Fachliche Schutzgrenze: grid-gym steuert **keine** realen Anlagen
([`GG-SAFE-007`](../../spec/lastenheft.md#gg-safe-007)); es entstehen
keine Betriebsrisiken an echten Geräten.

---

## 7. Fehlerbehebung

### Fehler: `make demo` startet nicht

**Ursache:** Docker läuft nicht oder `docker compose` fehlt.

**Lösung:**

1. Prüfen Sie mit `docker version`, ob der Docker-Daemon läuft.
2. Prüfen Sie, ob `docker compose version` funktioniert.
3. Starten Sie `make demo` erneut.

### Fehler: „UI verfuegbar unter http://localhost:8000", aber Seite nicht erreichbar

**Ursache:** Der Host-Port `8000` ist belegt, oder die Bindung liegt
auf `127.0.0.1` und Sie greifen von einem anderen Rechner zu.

**Lösung:**

1. Prüfen Sie, ob ein anderer Prozess Port `8000` belegt.
2. Für Remote-Zugriff setzen Sie `GRID_GYM_DEMO_HOST_BIND` (siehe
   [Abschnitt 5.1](#51-umgebungsvariablen)) und sichern den Zugang ab.

### Dashboard zeigt dauerhaft „Waiting for live data…"

**Ursache:** Es läuft kein aktiver Tick-Loop zur angezeigten `run_id`.

**Lösung:**

1. Prüfen Sie auf der **System**-Seite den *Run Status*.
2. Starten Sie den Lauf über
   [Abschnitt 4.8](#48-einen-lauf-über-die-api-anlegen-und-starten),
   falls er `pending`/`stopped` ist.

### Meldung: „Validation error: fault_invalid_type_for_target …"

**Ursache:** Der gewählte Fehlertyp passt nicht zum Gerätetyp des
Ziels (z. B. `cell_failure` auf einem Netzanschluss).

**Lösung:** Wählen Sie einen passenden Fehlertyp (siehe
[Abschnitt 5.4](#54-verfügbare-fehlertypen-faults)) oder ein passendes
Zielgerät.

### Meldung: „fault_unknown_target"

**Ursache:** Die eingegebene Geräte-ID gehört nicht zum aktiven Lauf.

**Lösung:** Verwenden Sie eine ID aus der **Devices**-Tabelle
(z. B. `battery-1`).

### Steuerung wird abgelehnt (`invalid_transition`)

**Ursache:** Der angeforderte Zustandswechsel ist nicht erlaubt
(z. B. **Pause** auf einem bereits gestoppten Lauf).

**Lösung:** Prüfen Sie den aktuellen Zustand im Status-Block und
wählen Sie eine gültige Aktion.

### Steuerung/Fault meldet `tick_loop_not_active` (HTTP 503)

**Ursache:** Der Lauf ist zwar angelegt, aber es läuft kein aktiver
Tick-Loop.

**Lösung:** Starten Sie den Lauf zuerst
([Abschnitt 4.8](#48-einen-lauf-über-die-api-anlegen-und-starten)).

### `POST /scenarios` meldet `scenario_hash_mismatch` (HTTP 422)

**Ursache:** Der mitgeschickte `scenario_hash` stimmt nicht mit dem
server-seitig berechneten Hash des Szenarios überein — meist weil
Dezimalfelder als Zahl statt als Zeichenkette notiert wurden.

**Lösung:** Notieren Sie alle Dezimalwerte als Zeichenketten und
berechnen Sie den SHA-256-Hash über das kanonisierte Szenario neu.

### `POST /runs/{id}/start` meldet `run_already_terminal` (HTTP 409)

**Ursache:** Der Lauf ist bereits `stopped` oder `completed` und kann
nicht neu gestartet werden.

**Lösung:** Legen Sie einen neuen Lauf an (`POST /runs`) und starten
Sie diesen.

### `POST /runs/{id}/start` meldet `run_concurrency_limit` (HTTP 429)

**Ursache:** Es laufen bereits so viele Läufe, wie die Registry
gleichzeitig zulässt.

**Lösung:** Beenden Sie einen laufenden Lauf über **Control → Stop**
und starten Sie erneut.

---

## 8. FAQ

**Brauche ich Python oder eine Datenbank-Installation?**
Für Demo-Betrieb und Weboberfläche nein — der Host braucht nur
`docker` und `make` (Postgres läuft im Compose-Stack). Nur die
Abnahme `make accept` braucht zusätzlich eine lokale
`uv`-Installation.

**Steuert grid-gym reale Anlagen?**
Nein. grid-gym ist ausschließlich Simulation
([`GG-SAFE-007`](../../spec/lastenheft.md#gg-safe-007),
[`GG-NONGOAL-001`](../../spec/lastenheft.md#gg-nongoal-001)).

**Warum sehe ich keinen Start-Knopf in der Oberfläche?**
Das Starten eines Laufs ist bewusst der API vorbehalten
([Abschnitt 4.8](#48-einen-lauf-über-die-api-anlegen-und-starten)).
Die Oberfläche bietet Pause, Resume und Stop.

**Wie mache ich einen Lauf reproduzierbar?**
Verwenden Sie denselben `seed` und dasselbe Szenario. Zur Prüfung
dient `make accept` und das Replay über `replay_of`.

**Gibt es eine Anmeldung?**
Nein. Schützen Sie den Zugang über die Netzwerk-Bindung
([Abschnitt 6](#6-rollen-und-rechte)).

**Wo finde ich eine maschinenlesbare API-Beschreibung?**
Unter `/openapi.json`; interaktiv unter `/docs`.

---

## 9. Glossar

| Begriff | Bedeutung |
| --- | --- |
| **Tick** | Ein Simulationsschritt fester Länge (`tick_ms`). |
| **Tick-Loop** | Der deterministische Kern, der Ticks nacheinander ausführt. |
| **Szenario** | YAML-Beschreibung von Geräten, Netzmodell, Fehlern und Agenten. |
| **Lauf (Run)** | Eine Ausführung eines Szenarios; identifiziert durch `run_id`. |
| **Seed** | Startwert des Zufallsgenerators; sichert Reproduzierbarkeit. |
| **Determinismus** | Gleicher Seed + gleiches Szenario ⇒ gleiches Ergebnis. |
| **Snapshot** | Zustandsabbild des Laufs zu einem Zeitpunkt. |
| **Replay** | Erneutes Ausführen gegen einen Referenzlauf mit Diff-Urteil. |
| **Quality-Status** | Güte eines Messwerts (z. B. `GOOD`, `STALE`, `MISSING`, `LIMITED`). |
| **Fault Injection** | Bewusstes Einspeisen eines Fehlers zu Testzwecken. |
| **Alarm** | Ereignis mit Schweregrad (`info`/`warning`/`critical`). |
| **Agent** | Regelbasierte Steuerung eines Geräts im Szenario. |
| **BESS** | Battery Energy Storage System (Batteriespeicher). |
| **SoC** | State of Charge — Ladestand der Batterie. |
| **PV** | Photovoltaik. |
| **Smart Meter** | Zähler, der Netzanschluss-Telemetrie aggregiert. |
| **OTLP** | OpenTelemetry-Protokoll für Logs/Metriken/Traces. |

---

## 10. Anhang

### 10.1 make-Befehle (Auswahl)

| Befehl | Wirkung |
| --- | --- |
| `make help` | alle verfügbaren Befehle anzeigen |
| `make demo` | Demo-Stack starten (UI auf `http://localhost:8000`) |
| `make demo-stop` | Demo-Stack stoppen (entfernt Datenvolumes) |
| `make accept` | maschinenlesbare Abnahmeprüfung ausführen |

### 10.2 Gerätetypen

Siehe [Abschnitt 5.3](#53-verfügbare-gerätetypen): `battery`, `pv`,
`load`, `grid_connection`, `smart_meter`, `ev_charger`, `transformer`,
`wind_turbine`, `diesel_generator`.

### 10.3 Fehlertypen

Siehe [Abschnitt 5.4](#54-verfügbare-fehlertypen-faults):
`cell_failure`, `voltage_drop`, `connection_loss`, `winding_fault`,
`genset_fault`.

### 10.4 HTTP-API-Referenz (Auszug)

| Methode + Pfad | Zweck | Wichtige Fehler |
| --- | --- | --- |
| `GET /health` | Liveness (immer `ok`) | — |
| `GET /ready` | Bereitschaft (`healthy`/`degraded`/`unhealthy`) | `503` bei `unhealthy` |
| `POST /scenarios` | Szenario ablegen | `422 scenario_hash_mismatch`, `422 invalid_scenario` |
| `POST /runs` | Lauf anlegen | `422 reference_run_not_found` |
| `GET /runs/{id}` | Lauf-Detail | `404 run_not_found` |
| `GET /runs/{id}/status` | Lauf-Status | `404 run_not_found` |
| `GET /runs/{id}/devices/state` | Gerätezustände (JSON) | `404 run_not_found` |
| `GET /runs/{id}/alarms-history` | Alarm-Historie | `404 run_not_found` |
| `POST /runs/{id}/start` | Lauf starten | `409 run_already_terminal`, `422 scenario_content_not_found`, `422 scenario_build_failed`, `429 run_concurrency_limit` |
| `POST /runs/{id}/control` | Pause/Resume/Stop | `409 invalid_transition`, `503 tick_loop_not_active` |
| `POST /runs/{id}/faults` | Fehler anfragen | `422 fault_unknown_target`, `422 fault_type_unknown`, `422 fault_invalid_type_for_target`, `503 tick_loop_not_active` |
| `WS /runs/{id}/telemetry` | Live-Telemetrie | Close `1008` (Lauf unbekannt) |
| `WS /runs/{id}/alarms-stream` | Live-Alarme | Close `1008` (Lauf unbekannt) |

Alle Fehlerantworten haben die Felder `code`, `message` und optional
`details`.

### 10.5 Grenzwerte

- `seed`: `0 … 2^32-1`.
- `scenario_hash`: exakt 64 Zeichen (SHA-256).
- `alarms-history`-`limit`: `0 … 200` (Standard 50).
- Dashboard-Tabelle: max. 16 Zeilen; Diagramm: max. 200 Punkte.

---

## 11. Support und Kontakt

- Fehler und Fragen: über die Issues des grid-gym-Repositorys.
- Weiterführende Anwender-Dokumente:
  - [`docs/user/abnahme-cli.md`](abnahme-cli.md) — Abnahme per `make accept`.
  - [`docs/user/gg-demo-008-abnahme.md`](gg-demo-008-abnahme.md) — manuelle Demo-Abnahme.
  - [`docs/user/safe-001-004-quality-pipeline.md`](safe-001-004-quality-pipeline.md) — Quality-Status.
  - [`docs/user/replay-determinism-e2e.md`](replay-determinism-e2e.md) — Replay/Determinismus.
  - [`docs/user/observability.md`](observability.md) — Logs, Metriken, Traces.

---

## 12. Änderungshistorie

| Handbuch-Version | Datum | Software-Version | Änderung |
| --- | --- | --- | --- |
| 1.0 | 2026-07-01 | v0.2.0 | Erstfassung nach [`benutzerhandbuch-standard.md`](benutzerhandbuch-standard.md); deckt Weboberfläche, REST-/WebSocket-API, Szenario-Konfiguration, Fehlerbehebung und Abnahme ab. |
