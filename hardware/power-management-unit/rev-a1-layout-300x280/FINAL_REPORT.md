# HomeMy PMU Rev A1 – 300 × 280 mm

**WIP – NICHT BESTELLBAR. Kein fertig geroutetes Layout, keine Fertigungsfreigabe.**

Branch: `codex/pmu-rev-a1-300x280-layout`
PCB: `kicad/HomeMy_PMU_RevA.kicad_pcb`
PCB-SHA-256: `c8012eb2cb2495787e9562bbb6dd09944f823c233d16349e7fc7fd0f62e81972`

Gesichert ist der vollständig geprüfte Zwischenstand aus Zyklus 9. Nach elf Editier-/Prüfzyklen wurde die CAD-Bearbeitung am 13.09.2026 um 14:13:15 UTC beendet. Die zwei anschließenden Versorgungskandidaten bestanden die Bedingung gegen Prüfungsverschlechterungen nicht. Es gab keinen Autorouter-Aufruf. Alle Freigabeflags einschließlich `cad_complete` bleiben `false`; siehe [release-status.json](release-status.json). Ein Fertigungsprüfsatz wurde für diesen unvollständigen Stand nicht erzeugt. Keine Bestellung wurde ausgelöst.

## Wiederholte Abschlussprüfung

| Prüfung | Lauf 1 | Lauf 2 |
|---|---:|---:|
| Native ERC | Exit 0, keine Befunde | identisch |
| Native DRC | Exit 5, nicht bestanden | identisch |
| Kurzschlüsse | 0 | 0 |
| Unverbundene Leiterbahnenden / Vias | 0 / 0 | 0 / 0 |
| DRC-Beschriftungswarnungen | 13: 8 Überlappungen, 5 über Kupfer | identisch |
| Offene Verbindungen, ungekappter nativer Zähler | **806** | **806** |
| Netze mit getrennten Kupfergruppen | 188 | 188 |
| Schaltplan-/PCB-Paritätsbefunde | 0 | 0 |
| Erforderliche Leistungspaare | **246/247** | **246/247** |
| Explizite kritische Pfade | **0/46** | **0/46** |
| Nominaler mechanischer 2D-Screen | bestanden | identisch |
| Vollständige mechanische Abnahme | nicht erreicht | nicht erreicht |

Nach der Wiederherstellung wurden sämtliche Zonen nativ neu gefüllt und gespeichert. Beide anschließenden Prüfserien lasen diese unveränderte Datei jeweils in neuen KiCad-CLI-/pcbnew-Prozessen. Alle Prüfprozesse endeten regulär, ohne Timeout oder fehlenden Bericht. Die DRC-/ERC-Berichte sind bis auf den Zeitstempel identisch; Konnektivität, Leistungspaare, kritische Pfade und 2D-Ergebnisse stimmen überein. KiCad-Version: **10.0.6**. Exit 0 des geometrischen Leistungsprüfers bedeutet reguläre Auswertung, keine bestandene 247/247-Abnahme. Der kritische Prüfer endete regulär mit Exit 2 wegen fehlender Pfade.

Das zusätzliche interaktive Öffnen konnte nicht verifiziert werden: Das Computer-Use-Werkzeug meldete einen gesperrten Mac und erfolgloses automatisches Entsperren. Der dafür gestartete PCB-Editor wurde ohne CAD-Änderung beendet. Ein erfolgreicher GUI-Neulade-/3D-Abnahmelauf wird ausdrücklich nicht behauptet.

Die native DRC-JSON enthält hier nur **499** offene Einträge. Die vollständige Dokumentation verwendet deshalb native Kupferkomponenten einschließlich gespeicherter Zonen: 2.387 netzbehaftete Pad-/Track-/Viaobjekte bilden 1.063 disjunkte Komponenten in 257 Netzen. Die Summe `Komponenten je Netz − 1` beträgt exakt **806**, gleich dem ungekapp­ten nativen Zähler. Es gibt keine padlose Komponente. [open-connections.json](reports/open-connections.json) enthält sämtliche offenen Netze, ihre Komponenten, Padendpunkte mit UUIDs und Positionen sowie Track-/Via-UUIDs. Die zusätzliche Verbindungsliste ist ein erläuternder Spannbaum, keine als native Ratsnest-Ausgabe ausgegebene Routerlösung.

## Unveränderte elektrische Quelle und neue Geometrie

Die elektrische Quelle ist ausschließlich `../rev-a/`, PCB-SHA-256 `13fcae0f58c9a6ac5f85eb721c24b44169a65f628baad6586bcd6002f4c17cfe`. Die 280×220-Geometrie wurde nicht als Ausgangsplatine verwendet. Die ursprünglichen 425 Footprints wurden anhand der neuen Funktionsinseln platziert; globale Leiterbahnen, Zonen und der alte Umriss wurden nicht übernommen. Geschlossene Edge.Cuts-Kontur: **(0,0) bis (300,280) mm**, exakt 300 × 280 mm.

Erhalten und erneut geprüft: 425 Footprints, 1.377 physische Pads, 40 Testpunkte, 48 Press-fit-Bohrungen, vier Ø3,2-mm-Befestigungsbohrungen, vier Kupferlagen sowie sämtliche Footprint-/Pad-/Netzidentitäten, Werte und DNP-Festlegungen. DNP: C244, J13, R243, R244. Die 421 elektrischen Bauteile und 1.297 benannten physischen Padinstanzen stimmen mit Bauteilquelle und Rev-A-Netzexport überein. Stackup, Layer-Tabelle und allgemeine Platinenparameter sind strukturell identisch. Alle 69 mitkopierten Projekt-, Schaltplan- und Bibliotheksdateien einschließlich `.kicad_pro` und `.kicad_dru` sind byteidentisch. Es wurden keine Regeln abgeschwächt und keine neuen pauschalen Ausnahmen hinzugefügt.

Der gespeicherte Stand enthält 1.087 Vias, drei Leiterbahnsegmente und 30 Zonen. 915 Kupferobjekte wurden als begrenzte lokale Rev-A-Geometrie übernommen; 205 wurden neu gezeichnet. Alle 1.120 Objekte sind mit Quell-/Ziel-UUID, Netz, Layer und Geometrie vollständig abgeglichen. Keine der 492 ursprünglichen Hochstrom-Tap-Ausnahmen wurde übernommen. Die zwei ursprünglichen CHOPPER_N-Referenzsegmente sind von der Leistungspfadprüfung ausgeschlossen.

Eine Quellschnittstelle ist ausdrücklich **nicht** als starr verbundener Padanker übernommen: TP1.1, UUID `51096776-0c24-43af-ab7f-83d9e221eaec`. Die Quellzone hätte TP1 nach Translation bei (29,56) mm erwartet; der mechanisch neu platzierte TP1 liegt bei (11,61) mm und bleibt offen. Der geprüfte Kraftpfad J1–RSH1 ist davon getrennt. Die Zuordnung steht in [copper-provenance.json](reports/copper-provenance.json).

Die vorhandenen Revisionen wurden nicht verändert. Arbeitsbeginn: 13:15:57 UTC; `git fetch origin` erfolgte vor der Bearbeitung. Ausgangspunkt des isolierten Worktrees ist Commit `55d8cc4` des vorhandenen Canonical-Branches. Geltende AGENTS.md, CURRENT_STATE.md, Rev-A-Dokumentation und die historischen 280×220-Abschlussberichte aus Commit `6a83998` wurden berücksichtigt. Nur der Lead schrieb KiCad-Dateien; drei weitere Prüfer arbeiteten ausschließlich lesend.

## Technischer Stand und Blocker

Batterie-, Hauptschalter-, Motion-/Arm-, Drive-/Lift- und Chopper-Kraftkupfer sind vorhanden. Der einzige fehlende Eintrag der 247-Paar-Liste ist **LOGIC_5V_N auf B.Cu: J18.3 → J11.2**. Die 46 expliziten Gate-/Kelvin-/Analogpfade sind noch nicht vorhanden. Versorgung, Rückführungen der Steuer-ICs, Schutzsteuerung, Analogmessung, CAN und übrige Signale sind insgesamt unvollständig. **246 bestandene Kraftpaare belegen weder eine betriebsfähige Schaltung noch funktionsfähige Schutzfunktionen.**

Der Versorgungskandidat aus Zyklus 10 ergänzte unter anderem den SYS-Zulauf zu U3/U4, erzeugte jedoch einen **0,1970-mm-Kontakt bei TP6** gegen die unveränderte 1-mm-Regel und einen Bohrungsabstandsfehler bei NT9. Zyklus 11 beseitigte diese konkreten Stellen, hinterließ aber einen **0,5172-mm-Zonenhals** im neuen SYS-Zulauf. Die rohe Befundzahl sank von 15 auf 14; gegenüber dem akzeptierten Zyklus 9 blieb die DRC dennoch verschlechtert. Daher wurde keiner der beiden Kandidaten übernommen. Ihre Diagnosen und exakten Zulaufpolygone sind kompakt in [cycle-and-stop-record.json](reports/cycle-and-stop-record.json) enthalten; die verworfenen Platinen werden nicht mitgeliefert.

Die Beschriftung ist nicht fertigungsreif. Alle 13 verbleibenden Warnungen mit betroffenen Elementen und UUIDs stehen im [nativen DRC-Bericht](reports/native-drc.json).

Nominal sind Press-fit-, Stecker-, Werkzeug-, NB-Brücken- und Antennenbereiche frei. Konservativer kleinster Press-fit-Abstand bei maximalem Fertigloch Ø1,525 mm: 4,6325 mm zu fremden Courtyards. Die ESP-Sperre wirkt auf allen vier Kupferlagen; keine fremden Pads, Tracks, Vias, Füllungen oder Busbars schneiden sie. Die vollständige mechanische Abnahme bleibt jedoch offen: **Die Ø8-mm-Kontaktfläche NT5.2 berührt BB7-Außenkante x27 ohne Toleranzreserve.** Stellenweise verbleiben nur 2,3 mm nominale Bar-Ligamente an Ausschnitten. Unter BB6/BB7 verlaufen fremde Kupfernetze; die spezifizierte durchgängige Polyimidisolation bleibt erforderlich. Tolerierte 3D-Nachweise für Pressauflage, Kabelschuhe, Biegeradien, Werkzeuge und Gehäuse fehlen. Der vor Routing bestandene Platzierungsscreen war ein nominaler 2D-Nachweis, keine vollständige tolerierte Montagefreigabe.

Am tatsächlich gefüllten Kupfer wurden lokale Querschnitte geprüft: BATT_N unter NT2 6,5–7 mm; Drive 8 mm; Lift unter Kondensatoren 24,3 mm und am rechten THT-Schenkel 6,7 + 2,7 mm; Chopper-Rücksteg 10 mm; Drain-Anschlussarm 7 mm. Angeschlossene CHOP_DRAIN-Füllfläche: 1.001,89 mm². Diese Stichproben ersetzen keinen vollständigen Engstellen-/Stromtragfähigkeitsnachweis. Die Drain-Fläche bis y193 umschließt Regler-/Analogpads; Routing- und Störverträglichkeit bleiben zu prüfen.

## Begrenzter nächster Arbeitsschritt

In einem separaten, erneut begrenzten Durchlauf ausschließlich den **SYS-Zulauf zu U3/U4** bearbeiten: den dokumentierten 0,1970-/0,5172-mm-Befund reproduzieren, den tatsächlichen Hals in der Füllgeometrie lokalisieren und einen regelkonformen lokalen Zulauf ausarbeiten. U3/U4 bleiben unverändert platziert. Die sechs originalen `PWR_SYS_BRANCH_SPINE`- und sechs `PWR_SYS_BRANCH_FANOUT`-Segmente können mit vollständiger Quellgruppen-/UUID-Zuordnung bei Nulltransformation erneut geprüft werden. Anschlussports: (38;165,5) und (87,3;165,5) mm; zugehörige Pads U3/U4.1/.2/.5. Die alten 0,8-/1,25-mm-Spines und 0,25-mm-Fanouts gelten ausschließlich für die vorgesehenen 3-A-/2-A-eFuse-Abzweige; keine neue dünne Verbindung und keine zusätzliche Regelausnahme daraus ableiten. Danach Zonenfüllung, native DRC und Regression aller bereits bestandenen Kraftpaare. Keine globale Neuoptimierung.

[verification-processes.json](reports/verification-processes.json) dokumentiert die Eingaben, Prozess-Exit-Codes und Wiederholungsvergleiche; [input-hashes.json](reports/input-hashes.json) enthält alle CAD-Eingabehashes. Ergänzende Ergebnisse stehen in [power-and-critical.json](reports/power-and-critical.json) und [identity-and-mechanics.json](reports/identity-and-mechanics.json).
