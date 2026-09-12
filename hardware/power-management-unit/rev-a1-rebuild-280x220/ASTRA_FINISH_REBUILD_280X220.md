# ASTRA-Auftrag: PMU-Rebuild 280 × 220 mm fertigstellen

## Auftrag und verbindlicher Startpunkt

Der Nutzer autorisiert am 2026-09-12 genau einen neuen, begrenzten
Fertigstellungslauf für die bereits aufgebaute PMU Rev A.1 auf
280 × 220 mm.

Arbeitsbranch:

- codex/pmu-rev-a1-280x220-rebuild

Einzige CAD-Ausgangsbasis:

- Commit vor diesem Auftragscommit:
  0dd4a3b4a81ef42925506c995fb0fcbda171ecb0
- PCB:
  kicad/HomeMy_PMU_RevA1_Rebuild_280x220.kicad_pcb
- erwarteter PCB-SHA-256 am Start:
  9f329b44bf0fece059550d2f4a07b94af8fb52cfec7d26c4796aeed230193f99

Der abgeschlossene Rebuild ist die Grundlage. Kein Neubeginn, kein Wechsel auf
die 250-, 275-, 300- oder 360-mm-Geometrie und keine erneute globale
Platzierung. Die bisherige Sperre in FINAL_REPORT.md wird ausschließlich für
diesen neuen, begrenzten Abschlusslauf aufgehoben. Alte Versuchszähler werden
nicht fortgesetzt; die unten genannten neuen Grenzen gelten ausschließlich für
diesen Lauf.

Vor jeder CAD-Änderung vollständig lesen:

1. dieses Dokument,
2. RUN_PLAN.md,
3. FINAL_REPORT.md,
4. release.json,
5. reports/final-open-nets.json,
6. reports/final-native-consistency.json,
7. reports/mechanical-review.md,
8. die übergeordneten AGENTS.md-Dateien und den dort genannten Rev-A-Pflichtkontext.

## Ziel

Die bestehende Platine bis zu einem vollständig gerouteten, nativ geprüften
CAD-Stand fertigstellen. Der Schwerpunkt liegt auf den noch offenen
Versorgungs-, Masse-, Mess-, Steuer- und Kommunikationsnetzen sowie auf den
verbliebenen DRC- und Mechanikbefunden.

Aktueller Ausgangsstand:

- 293 offene Verbindungen in 112 Netzen,
- 247/247 erforderliche Leistungspfad-Paare,
- 46/46 kritische Pfade,
- ERC Exit 0 und Schaltplanparität ohne Befund,
- DRC Exit 5,
- 23 dangling tracks und 35 dangling vias,
- 119 silk_over_copper- und 76 silk_overlap-Warnungen,
- ungeklärte, nicht deterministische BATT_N-connection_width-Meldung,
- offene mechanische Punkte H4/C245 sowie J1/TP1.

## Unveränderliche Randbedingungen

- Platinenaußenmaß exakt 280 × 220 mm.
- Vierlagiger Stackup, 425 Footprints, alle Pad- und Netzidentitäten,
  Bauteilwerte, DNP-Entscheidungen, 40 Testpunkte, 48 Press-fit-Bohrungen,
  vier Befestigungsbohrungen und der vollständige ESP32-Antennen-Keepout
  bleiben erhalten.
- Topologie, Schutzfunktionen, Netzklassen, Designregeln, minimale
  Leiterbahnbreiten, Via-Geometrien, Abstände, Kelvin-/Gate-Konzept,
  Net-Ties, Busbar- und Press-fit-Schnittstellen dürfen nicht abgeschwächt,
  umgangen oder pauschal ausgenommen werden.
- Die bestehenden 247/247 Leistungspfade und 46/46 kritischen Pfade sind
  geschützte Invarianten. Ein Kandidat, der auch nur einen davon verliert,
  wird verworfen.
- Vorhandenes validiertes Hochstromkupfer, Shunt-, MOSFET-, Net-Tie-,
  Kelvin-, Gate-, Busbar-, Press-fit-, Anschluss- und Keepout-Layout bleibt
  standardmäßig gesperrt.
- Keine globale Neuplatzierung und kein globales Rip-up.
- Nur der Lead-Agent schreibt KiCad-Dateien. Subagenten dürfen ausschließlich
  lesend Netze, Engstellen und Prüfergebnisse analysieren.
- Keine reale Bestromung, Batterie-, Motor- oder Aktorprüfung.

Nur wenn ein noch offenes Signal nach zwei nachvollziehbaren lokalen
Routingversuchen geometrisch blockiert bleibt, darf der Lead-Agent einzelne
reine Kleinleistungs-/Signalbauteile innerhalb derselben Funktionsinsel
verschieben. Jede solche Bewegung braucht Vorher-/Nachher-Koordinaten,
Begründung und eine erneute vollständige Prüfung. Leistungsbauteile,
Anschlüsse, Shunts, MOSFETs, Net-Ties, Testpunkte mit Presswerkzeugbezug,
Befestigungen und Keepouts dürfen nicht verschoben werden. Wenn die Lösung eine
Änderung dieser gesperrten Elemente erfordert, Arbeit stoppen und den konkreten
Blocker dokumentieren.

## Arbeitsreihenfolge

### Phase 0 – reproduzierbare Basis

Vor der ersten Änderung:

1. Projekt mit den korrekten benachbarten .kicad_pro- und .kicad_dru-Dateien
   laden.
2. PCB-Start-Hash bestätigen.
3. Zonen neu füllen, speichern, KiCad schließen beziehungsweise Datei frisch
   laden und ERC, DRC, Parität, offene Verbindungen, Dangling-Elemente,
   247 Leistungspfade und 46 kritische Pfade erneut erfassen.
4. Die BATT_N-connection_width-Meldung am Via bei ungefähr
   (184 mm; 106,4 mm) zweimal aus einem jeweils frisch geladenen,
   unveränderten Eingabesatz prüfen.
5. Wenn die beiden Läufe voneinander abweichen, zunächst Ursache in
   Projektkonfiguration, Zonenfüllung, Cache oder Prüfaufruf bestimmen. Nicht
   durch Wiederholen bis zu einem zufälligen Pass kaschieren.

Die Referenzwerte dieses neuen Basislaufs sind im neuen Abschlussledger
festzuhalten. Bei nicht reproduzierbarer nativer Prüfung darf später kein
CAD-complete-Status gesetzt werden.

### Phase 1 – Versorgung und Rückleiter

Zuerst ausschließlich die noch offenen Leistungs-, Versorgungs- und
Massennetze schließen. Priorität:

1. BATT_N und BATT_FUSED_P/BATT_SENSED_P,
2. SYS_BUS_P, MOTION_BUS_P und zugehörige COMMON-/Rückleiternetze,
3. CHOPPER_N, CHOP_DRAIN, CHOP_GND und CHOP_10V,
4. V5V, AON_3V3, LOGIC_GND, LOGIC_5V_N und verbleibende Zweigversorgungen.

Jede Änderung muss die Netzklasse und reale gefüllte Kupfergeometrie erfüllen.
Eine geringere Ratsnest-Zahl ist kein Fortschritt, wenn dadurch ein
Leistungspfad, eine Engstelle, eine Clearance, ein Net-Tie oder eine
Schutzfunktion verschlechtert wird.

### Phase 2 – Messung und analoge Schwellen

Danach die INA228-, Temperatur-, Strom-, Busspannungs-, Chopper- und
Schwellwertnetze lokal und kurz führen. Analoge Messpfade von schaltenden
Gate-, Chopper-, CAN- und Hochstrombereichen fernhalten. Kelvinbezüge und
zugehörige Masseführung unverändert respektieren.

### Phase 3 – Steuerung und Kommunikation

Danach in Funktionsinseln arbeiten:

1. Main-/Motion-Fault-, Permit-, Latch- und Timer-Netze,
2. Power-Taster-, Wake-, Reset- und Watchdog-Netze,
3. CAN mit konsistentem Paarverlauf und ohne unnötige Stubs,
4. I2C, UART, LED und verbleibende GPIO-Signale,
5. alle übrigen Niedrigstromnetze.

Pro Teilabschnitt eine feste Netzliste verwenden. Nicht gleichzeitig
unabhängige Inseln global umsortieren.

### Phase 4 – Bereinigung und Mechanik

Erst nach vollständiger Konnektivität:

- sämtliche dangling tracks und vias entfernen oder korrekt anbinden,
- Silkscreen-Kollisionen ohne Verschieben elektrischer Funktionsgruppen
  beseitigen,
- H4/C245-Abstand regelkonform lösen,
- J1/TP1-Presswerkzeugabstand regelkonform lösen oder, falls er nur durch
  Veränderung eines gesperrten Elements lösbar wäre, als konkreten
  mechanischen Freigabeblocker stoppen,
- Montage-, Kabelzugangs-, Press-fit-, Busbar- und Antennenprüfungen
  wiederholen.

## Routingmethode

- Vor jedem Editierzyklus eine konkrete, begrenzte Netzliste und das erwartete
  Ergebnis nennen.
- Lokales, deterministisches Routing bevorzugen.
- Kein zufälliges Brute Force, keine unbeschränkte Reparaturschleife und kein
  wiederholtes Umschreiben des Routers für dieselbe Ursache.
- Bestehende Hilfsskripte dürfen verwendet werden. Für dieselbe technische
  Ursache ist höchstens eine Skriptkorrektur zulässig; scheitert sie zweimal,
  wird nicht weiter daran iteriert.
- Höchstens ein selektiver Autorouter-Aufruf im gesamten Lauf. Er darf nur
  ausdrücklich aufgelistete Niedrigstrom-Signalnetze bearbeiten, maximal
  300 Sekunden und maximal 100 Durchgänge laufen. Kein globaler Autorouter.
  Ein Ergebnis wird nur importiert, wenn es weniger offene Verbindungen hat
  und alle Invarianten sowie DRC-Parität bestehen.
- Keine Zeit für kosmetische Renderings oder 3D-Ansichten verwenden, bevor
  Konnektivität und elektrische DRC-Befunde geschlossen sind.
- Sobald alle Annahmekriterien erfüllt sind, sofort aufhören. Keine weitere
  ästhetische Optimierung.

## Harte Laufgrenzen

Dieser Auftrag erlaubt maximal:

- 180 Minuten gesamte Bearbeitungszeit,
- davon mindestens die letzten 25 Minuten ausschließlich für Endprüfung,
  Bericht, Commit und Push,
- acht vollständige Editieren/Speichern/Neu-Laden/Prüfen-Zyklen,
- einen selektiven Autorouter-Aufruf,
- zwei Korrekturversuche je unveränderter technischer Ursache,
- zwei Neustarts desselben abgestürzten nativen Prozesses.

Nach jedem vollständigen Zyklus muss der aktuelle Kandidat mit dem bisher
besten validierten Kandidaten verglichen werden. Fortschritt bedeutet:

- bei mehr als 100 offenen Verbindungen: mindestens 15 weniger,
- bei 20 bis 100 offenen Verbindungen: mindestens fünf weniger,
- bei weniger als 20 offenen Verbindungen: mindestens eine weniger oder ein
  beseitigter DRC-/Dangling-/Mechanikbefund,
- und gleichzeitig keine Regression bei 247/247, 46/46, Parität, Clearance,
  Short-, Width-, Regel- oder Mechanikprüfungen.

Zwei aufeinanderfolgende Zyklen ohne diesen Fortschritt beenden den Lauf.
Dasselbe gilt sofort bei einer notwendigen Sicherheits-, Topologie-,
Stackup-, Größen- oder Regeländerung. Ein regressiver Kandidat wird verworfen;
der letzte bessere, vollständig geprüfte Kandidat wird wiederhergestellt.
Nicht weiterprobieren, nur um die Zyklus- oder Zeitgrenze auszuschöpfen.

## Vollständige Annahmekriterien

Ein CAD-complete-Ergebnis liegt nur vor, wenn nach Zonenfüllung, Speichern und
frischem Neu-Laden gleichzeitig nachgewiesen sind:

- Außenmaß exakt 280 × 220 mm,
- Schaltplan-/PCB-Parität ohne Befund,
- ERC regulär beendet mit Exit 0 und ohne Befunde,
- DRC regulär beendet mit Exit 0 und ohne Fehler oder Warnungen,
- null offene Verbindungen,
- null dangling tracks und null dangling vias,
- 247/247 erforderliche Leistungspfade,
- 46/46 kritische Pfade,
- alle eingefrorenen Regeln und Tap-Provenienzen bestanden,
- keine Shorts, Clearance-, Width- oder Zonenfehler,
- Montage-, Press-fit-, Busbar-, Kabelzugangs- und Antennenprüfung bestanden,
- BATT_N-Prüfergebnis reproduzierbar,
- alle finalen Berichte referenzieren exakt denselben PCB-Hash.

Teilprüfungen oder interne Routerwerte ersetzen keine native KiCad-Prüfung.

Wenn sämtliche Kriterien erfüllt sind:

1. cad_complete in release.json auf true setzen,
2. orderable, fabrication_release, assembly_release und production_release
   weiterhin false lassen,
3. den Zustand als cad_complete_pending_independent_review kennzeichnen,
4. einen als DRAFT / NOT RELEASED markierten Gerber-, Bohr-, BOM- und
   Pick-and-Place-Prüfsatz erzeugen,
5. keine Bestellung auslösen,
6. FINISH_REPORT.md mit Hashes und reproduzierbaren Exit-Codes erstellen.

Die eigentliche Fertigungsfreigabe bleibt ein separater Nutzerauftrag.

## Abbruch- und Abschlussverhalten

Wenn die Platine innerhalb der Grenzen nicht vollständig fertig wird:

- den besten validierten Kandidaten wiederherstellen,
- keine zufälligen weiteren Versuche starten,
- alle Freigabeflags false und WIP true lassen,
- FINISH_REPORT.md mit Restnetzliste, exakten Endpunkten/UUIDs,
  DRC-Befunden, gescheiterten Ursachen und einem konkreten nächsten
  Ingenieurschritt erstellen,
- klar schreiben: WIP – NICHT BESTELLBAR.

In beiden Fällen:

- kompakte Zyklusmetriken und die finalen nativen Berichte speichern,
- keine Caches, Backups, temporären Routerdateien, redundanten
  Zwischenplatinen oder massenhaften Zwischenrenderings committen,
- nur den final ausgewählten Kandidaten und die erforderliche Evidenz
  committen,
- auf codex/pmu-rev-a1-280x220-rebuild pushen,
- abschließend ausschließlich Branch, Commit-SHA, PCB-Hash, Ergebnisstatus,
  Prüftabelle und gegebenenfalls verbleibende Blocker nennen.
