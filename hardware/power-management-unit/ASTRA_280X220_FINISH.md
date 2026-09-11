# Astra-Auftrag: HomeMy PMU Rev A.1 auf 280 × 220 mm fertigstellen

Status: verbindlicher, zeitlich begrenzter Layout-Abschlussauftrag
Datum: 2026-09-11
Ausgangsbranch: `codex/pmu-rev-a1-bounded-shrink`
Mindestens enthaltener Ausgangscommit: `fc9d8e3c430a53018270b0b3bed357042d69690f`
Zielbranch: `codex/pmu-rev-a1-280x220-finish`

## 1. Verbindliches Ziel

Erstelle aus dem vorhandenen 275 × 210-mm-Zwischenstand eine vollständig geroutete und elektrisch geprüfte **280,0 × 220,0-mm-Platine** als Engineering-Prototyp.

Die Größe 280,0 × 220,0 mm ist endgültig festgelegt. Keine weiteren Größenvergleiche, Verkleinerungsstudien oder Änderungen der Außenmaße durchführen. Das Ziel ist ein tatsächlich fertiggestellter PCB-Stand. Die harten Zeit- und Iterationsgrenzen dieses Auftrags bleiben trotzdem verbindlich.

## 2. Pflichtkontext und Arbeitsbranch

Vor jeder Änderung vollständig lesen:

- `AGENTS.md`
- `CURRENT_STATE.md`
- `hardware/power-management-unit/AGENTS.md`
- `hardware/power-management-unit/ASTRA_PCB_HANDOFF.md`
- `hardware/power-management-unit/rev-a/README.md`
- `hardware/power-management-unit/rev-a/design/HIGH_CURRENT_RULES.md`
- `hardware/power-management-unit/rev-a/manufacturing/PCB_STACKUP_PRESSFIT.md`
- `hardware/power-management-unit/DESIGN_REVIEW_AND_BRINGUP.md`
- `hardware/power-management-unit/REV_A_ASSUMPTIONS.md`
- `hardware/power-management-unit/rev-a1/BOUNDED_SHRINK_RESULT.md`
- `hardware/power-management-unit/rev-a1/results/HomeMy_PMU_RevA_275x210.json`

Repository aktualisieren, prüfen, dass der Ausgangscommit im Verlauf enthalten ist, und den neuen Branch `codex/pmu-rev-a1-280x220-finish` anlegen. Den Ausgangsbranch, Rev A und die eingefrorenen 250×200-/300×220-Ergebnisse nicht verändern.

## 3. Einzige Ausgangsplatine

Nur diese PCB-Datei als geometrische und routingtechnische Grundlage verwenden:

`hardware/power-management-unit/rev-a1/kicad/HomeMy_PMU_RevA_275x210.kicad_pcb`

Nicht vom 250×200- oder 300×220-Stand neu beginnen. Die brauchbare Platzierung und das vorhandene Routing des 275×210-Standes müssen soweit möglich erhalten bleiben.

Eigenständige 280×220-Projektdateien erzeugen:

- `HomeMy_PMU_RevA_280x220.kicad_pcb`
- `HomeMy_PMU_RevA_280x220.kicad_sch`
- `HomeMy_PMU_RevA_280x220.kicad_pro`
- `HomeMy_PMU_RevA_280x220.kicad_dru`

Vorhandene Varianten nicht überschreiben.

## 4. Geometrische Umstellung

- Platinenumriss exakt auf 280,0 × 220,0 mm erweitern.
- Bestehende Platzierung, Kupferstrukturen und bereits gültige Routen bewahren.
- Bauteile, Montagebohrungen und Randsteckverbinder nur verschieben, wenn Platinenrand, Zugänglichkeit oder Routing es erfordern.
- Steckverbinderzugang, vier Montagebohrungen, 40 Testpunkte und ESP32-Antennen-Keep-out erneut prüfen.
- Keine elektrische Topologie, Bauteilwerte, Footprints, Pinbelegungen, Netznamen, Schutzfunktionen, Layer oder verbindlichen Netzklassen verändern.
- DRC-Regeln niemals abschwächen, deaktivieren, herabstufen oder durch pauschale Ausnahmen umgehen.

## 5. Bekannter Ausgangszustand

Der 275×210-Stand besitzt ungefähr:

- 136 offene Verbindungen auf 31 Netzen,
- 5 `connection_width`-Fehler,
- 8 offene Leiterbahnenden,
- 9 nicht vollständig angebundene Vias,
- 244 von 247 bestandene Pflichtpfade,
- 37 von 46 bestandene kritische Pfade.

Bekannte kritische Aufgaben:

- `RSH1.2 → R21.1` auf `MAIN_KELVIN_P`,
- `RSH1.2 → R23.1` für die Kurzschlusserfassung,
- `RSH1.2 → R223.1` für die INA228-Kelvinführung,
- drei `MAIN_HGATE`-Verbindungen,
- drei `MAIN_DGATE`-Verbindungen,
- vorgeschriebener `DRIVE_N`-Pfad auf F.Cu,
- vorgeschriebener `LIFT_N`-Pfad auf In1.Cu,
- vorgeschriebener `LOGIC_5V_N`-Pfad auf B.Cu,
- zwei unvollständig angebundene `LOGIC_GND`-Stitching-Vias an U11.

Diese Anforderungen nicht entfernen, umbenennen oder durch geänderte Prüfregeln lösen.

## 6. Verbindliche Bearbeitungsreihenfolge

### Phase A – Sichere Übernahme

1. 280×220-Projekt aus dem 275×210-Stand erzeugen.
2. Schaltplanparität, Stack-up, Netzklassen, Footprints und mechanische Platzierung prüfen.
3. Kupferzonen neu füllen.
4. Native ERC-/DRC-Ausgangsprüfung durchführen und Berichte samt PCB-SHA-256 speichern.

### Phase B – Kritische Pfade

In dieser Reihenfolge bearbeiten:

1. Kelvin- und Strommessleitungen,
2. MAIN_HGATE und MAIN_DGATE,
3. Shunt-, MOSFET- und Busbar-Anbindungen,
4. Batterie-, SYS-, Motion-, Arm-, Lift- und DC/DC-Leistungspfade,
5. die drei fehlgeschlagenen Pflichtpfade,
6. die beiden U11-Masse-Stitching-Vias,
7. die fünf vorhandenen `connection_width`-Fehler.

Die reale Kupfergeometrie korrigieren; keine Ausnahme oder schwächere Regel anlegen.

### Phase C – Restliches Routing

Danach die übrigen Netze priorisiert routen:

1. Versorgung und Rückleiter,
2. Schutz-, Abschalt- und Fehlersignale,
3. CAN, I²C, UART und weitere Kommunikationsnetze,
4. allgemeine Steuer- und Statussignale.

Kurze nachvollziehbare Verbindungen, zusammenhängende Rückstrompfade und möglichst wenige Vias verwenden. Keine Sackgassen, Kupferinseln oder unzulässigen Engstellen erzeugen. Globale Autorouter nur für unkritische Signale verwenden; Leistung, Gate, Kelvin und Messpfade gezielt kontrollieren.

## 7. Korrigierte Fortschrittslogik

Einen Zwischenstand nicht allein deshalb verwerfen, weil gegenüber einem ungerouteten Ausgangsboard wenige lokale `connection_width`-Fehler entstanden sind.

Zwischenzeitlich sind höchstens zehn eindeutig lokalisierte `connection_width`-Fehler zulässig, wenn gleichzeitig:

- keine Kurzschlüsse oder Clearance-Verstöße entstehen,
- keine Regeln oder Netzklassen abgeschwächt werden,
- keine bestandenen kritischen oder vorgeschriebenen Pfade verloren gehen,
- die offenen Verbindungen messbar sinken,
- die Breitenfehler im folgenden Zyklus gezielt bearbeitet werden.

Ein Zyklus gilt als Fortschritt, wenn mindestens eines zutrifft:

- mindestens fünf offene Verbindungen geschlossen,
- offene Verbindungen um mindestens fünf Prozent reduziert,
- mindestens ein kritischer Pfad hergestellt,
- mindestens ein Pflichtpfad hergestellt,
- DRC-Fehler oder dangling Tracks/Vias reduziert,

und dabei keine sicherheitskritische Verschlechterung entsteht.

Nach jedem erfolgreichen Zyklus einen validierten besten Zwischenstand sichern. Ein schlechterer Versuch darf ihn nicht überschreiben. Zwei aufeinanderfolgende Zyklen ohne messbaren Fortschritt lösen den Abbruch aus.

## 8. Harte Grenzen

Ab Beginn dieses Auftrags gelten:

- maximal 180 Minuten gesamte Bearbeitungszeit,
- maximal sechs vollständige Bearbeitungs- und Prüfzyklen,
- maximal vier Autorouter-Aufrufe,
- maximal zehn Minuten beziehungsweise 250 Durchgänge je Autorouter-Aufruf,
- maximal zwei gezielte Reparaturversuche für denselben unveränderten Fehler,
- maximal zwei aufeinanderfolgende Zyklen ohne messbaren Fortschritt,
- maximal zwei Neustarts eines identisch abgestürzten KiCad- oder Prüfprozesses.

Bei Erreichen einer Grenze sofort:

1. weitere Routing- und Reparaturversuche stoppen,
2. den besten validierten Stand wiederherstellen,
3. verbleibende Fehler exakt dokumentieren,
4. den Stand als nicht bestellbaren WIP kennzeichnen,
5. committen und pushen,
6. Arbeit beenden.

Nicht auf andere Größen ausweichen. Wenn alle Abnahmekriterien früher erfüllt sind, sofort Abschlussprüfung, Dokumentation, Commit und Push durchführen; keine kosmetischen Zusatzschleifen.

## 9. Abnahmekriterien

Der CAD-Stand gilt nur dann als vollständig, wenn alle Bedingungen erfüllt sind:

- Platinenabmessung exakt 280,0 × 220,0 mm,
- vollständige Schaltplanparität,
- nativer ERC ohne Fehler und Exit-Code 0,
- nativer DRC ohne Fehler und Exit-Code 0,
- keine Kurzschlüsse oder offenen Verbindungen,
- keine dangling Tracks oder Vias,
- 247 von 247 Pflichtpfaden bestanden,
- 46 von 46 kritischen Pfaden bestanden,
- keine unerlaubten Kupferengstellen,
- alle Hochstrompfade erfüllen die unveränderten Netzklassen,
- Kelvin- und Messpfade nachvollziehbar von Leistungsstrompfaden getrennt,
- nach finalem Zonenfüllen gespeicherte Platine neu geladen und erneut geprüft,
- Footprints, Montagebohrungen, Steckverbinder, Testpunkte und Freiräume geprüft.

Warnungen nicht stillschweigend ignorieren. Jede unvermeidbare Warnung einzeln begründen. Offene Verbindungen, dangling Elemente oder fehlende native Prüfungen dürfen niemals freigegeben werden.

## 10. Abschlussunterlagen und Freigabe

Erzeugen oder aktualisieren:

- `FINAL_280x220_REPORT.md`,
- vollständige ERC-/DRC-Berichte,
- Liste aller kritischen und vorgeschriebenen Pfade,
- SHA-256 der geprüften KiCad-Eingaben,
- kompakte Änderungshistorie je Zyklus,
- `release.json` mit eindeutigem CAD- und WIP-Status.

Nur bei vollständig bestandenen CAD-Kriterien dürfen Gerber-, Bohr-, BOM- und Positionsdaten für die spätere Prüfung erzeugt werden. `fabrication_release`, `assembly_release` und `production_release` bleiben `false`, bis der Nutzer einen separaten Freigabeauftrag erteilt. Keine Bestellung, Fertigung oder reale Bestromung durchführen.

## 11. Agenteneinsatz

Subagenten dürfen parallel nur lesend für Analyse, DRC-Auswertung, Netzpriorisierung und Dokumentationsprüfung arbeiten. Genau ein leitender Agent besitzt die Schreibverantwortung für die maßgebliche `.kicad_pcb`-Datei. Keine parallelen PCB-Schreibzugriffe oder Zusammenführung konkurrierender Layoutstände.

## 12. Commit, Push und Abschlussantwort

Alle relevanten Ergebnisse auf `codex/pmu-rev-a1-280x220-finish` committen und pushen.

Die Abschlussantwort enthält ausschließlich:

- Branchname und Commit-SHA,
- tatsächliche Bearbeitungszeit,
- verwendete Zyklen und Autorouter-Aufrufe,
- endgültiges ERC-/DRC-/Paritätsergebnis,
- Zahl offener Verbindungen,
- Ergebnis der Pflicht- und kritischen Pfade,
- Freigabestatus,
- Link zum Abschlussbericht,
- gegebenenfalls kompakte Liste verbleibender Blocker.

Niemals behaupten, die Platine sei fertig oder bestellbar, wenn ein Abnahmekriterium fehlt. Vor Beginn und nach jedem Zyklus die Abbruchgrenzen erneut prüfen.
