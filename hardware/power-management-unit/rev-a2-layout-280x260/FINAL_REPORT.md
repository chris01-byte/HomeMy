# HomeMy PMU Rev A2 – 280 × 260 mm

**WIP – NICHT BESTELLBAR. Das Layout ist nicht vollständig fertig. Alle Freigaben sind gesperrt.**

Branch: `codex/pmu-rev-a2-280x260-layout`

PCB: `kicad/HomeMy_PMU_RevA.kicad_pcb`

PCB-SHA-256: `d088591283675624ee5fc5b582c4f685d1b0a614aec517129990e586f1e82b43`

Gesichert wird der geprüfte Stand aus Zyklus 28: zehn offene Verbindungen in acht Netzen, 247/247 erforderliche Leistungspaare, 46/46 explizite kritische Pfade und keine elektrischen DRC-Fehler. DRC ist dennoch **nicht bestanden**: Exit 5, zusätzlich 32 unverbundene Leiterbahnenden, zwei einseitig angeschlossene Vias und 17 Beschriftungswarnungen. ERC endet mit Exit 0. `cad_complete`, `orderable`, `fabrication_release`, `assembly_release`, `production_release` und `energization_release` bleiben false. Es wurde kein Fertigungsprüfsatz und keine Bestellung erzeugt.

## Ausgewählter und zweimal geprüfter Stand

| Prüfung | Lauf 1 | Lauf 2 |
|---|---:|---:|
| Native ERC | Exit 0; 0 Befunde | gleich |
| Native DRC | Exit 5; nicht bestanden | gleich |
| Elektrische DRC-Fehler einschließlich Kurzschlüsse | 0 | 0 |
| Offene Verbindungen, ungekappter nativer Zähler | **10** | **10** |
| Unverbundene Leiterbahnenden / Vias | 32 / 2 | 32 / 2 |
| Beschriftung: Überlappung / über Kupfer | 9 / 8 | 9 / 8 |
| Native Schaltplan-/PCB-Paritätsbefunde | 0 | 0 |
| Leistungspfad-Paare | **247/247** | **247/247** |
| Explizite kritische Pfade | **46/46** | **46/46** |
| Nominaler mechanischer 2D-Screen | bestanden | gleich |
| Vollständige Montage-/Fertigungsabnahme | offen | offen |
| Kupfer-Netzidentität und Geometriebeleg | 0 Abweichungen | gleich |
| Vollständiger Padgraph gegen Zyklus 18 | 0 Regressionen | gleich |

Vor den beiden Serien wurden alle Zonen mit KiCad 10.0.6 nativ neu gefüllt und gespeichert. Die 70 CAD-Eingabedateien blieben dabei byteidentisch. Jede anschließende Prüfung las die unveränderten Dateien in einem neuen CLI-/pcbnew-Prozess. Alle finalen Prozesse wurden regulär beendet; keine Zeitüberschreitung, kein fehlender Bericht und kein CAD-Schreibvorgang während der Prüfung. Die geometrischen Leistungs-, Pfad-, Mechanik-, Kupfer- und Padprüfer endeten jeweils mit Exit 0. Die beiden vollständigen Quellen-/BOM-Audits endeten regulär mit Exit 2, ausschließlich wegen der unten genannten ursprünglichen BOM-Hash-Befunde.

Die Wiederholung bestätigt dieselben Kupferkomponenten, Pfade und Befunde. Die nativen DRC-Dateien sind **nicht byteidentisch**: KiCad wählt bei einer offenen SW_RESET_N-Verbindung andere repräsentative Track-/Viaobjekte. Die vollständige Komponententeilung einschließlich sämtlicher Pad-/Track-/Via-UUIDs ist identisch; die Anzahl offener Verbindungen und alle tatsächlichen DRC-Verstöße sind identisch. Beide Zeugen stehen in [verification-processes.json](reports/verification-processes.json). Diese Anzeigevariation wird nicht als erfolgreicher DRC-Lauf ausgegeben.

Der zusätzliche grafische Neuladetest konnte nicht abgeschlossen werden. Ein frischer PCB-Editor startete, doch der macOS-Dateidialog übernahm den vollständigen Pfad nicht zuverlässig; der Zwischenablagezugriff lief in einen Timeout. Der leere Editor wurde ohne CAD-Änderung geschlossen. Erfolgreiches grafisches Öffnen der Zielplatine und vollständiges Schließen/Neuöffnen aller KiCad-Oberflächen werden ausdrücklich **nicht** behauptet. Die frischen nativen CLI-/API-Ladevorgänge sind davon getrennt dokumentiert.

## Unveränderte elektrische Quelle

Elektrische Quelle ist ausschließlich `../rev-a/`, ursprünglicher PCB-Hash `13fcae0f58c9a6ac5f85eb721c24b44169a65f628baad6586bcd6002f4c17cfe`. Die unvollständige 280×220-Platine wurde nicht als geometrischer Ausgangspunkt verwendet. Neue geschlossene Edge.Cuts-Kontur: **(0,0) bis (280,260) mm**, exakt 280×260 mm. Die Footprints wurden nach mechanischen Schnittstellen und Funktionsinseln neu angeordnet; lokale geprüfte Rev-A-Kupfergruppen wurden anschließend mit dokumentierten Transformationen übernommen.

Erhalten: 425 Footprints, 1377 physische Pads einschließlich vier Montagepads, vier Kupferlagen, 40 Testpunkte, 48 Press-fit-Bohrungen, vier Befestigungsbohrungen, 257 benannte Netze einschließlich 63 separater NC-Netze. Werte, Footprint-/Pad-UUIDs, Netzidentitäten, Footprintbibliotheken, Padgeometrien, DNP, Stackup, Net-Ties, Schutzschaltung sowie Gate-/Kelvin-Topologie wurden nicht geändert. DNP bleibt `C244`, `J13`, `R243`, `R244`. Die 69 mitkopierten Schaltplan-, Projekt-, Regel- und Bibliotheksdateien sind byteidentisch zur Quelle, darunter `.kicad_pro`, `.kicad_dru`, 16 Schaltpläne und 48 Footprintdateien. Keine Regeln oder Mindestbreiten wurden abgesenkt, keine neuen pauschalen Ausnahmen angelegt.

Der Endstand enthält 5223 Leiterbahn-/Viaobjekte und 77 Zonen. 4424 übernommene und 876 neue Kupferobjekte sind mit Netz, Layer, UUID und Geometrie vollständig erfasst; 973 Padanker der lokalen Gruppen wurden erneut abgeglichen. Sämtliche übernommenen Quell- und Zielgeometrien stimmen mit ihren Belegen überein. Bei elf **neuen** Objekten enthielt der Erstellungsbeleg noch den Zustand vor dokumentierten geometrischen Änderungen. Diese elf Belegzeilen wurden anhand der ausgeführten Änderungsskripte und des frisch geladenen Endstands nachgeführt; die CAD-Datei wurde dabei nicht verändert. Vorher-/Nachherwerte bleiben im Bericht erhalten. Außerdem wurden im Routing 14 neue Vias mit unerwarteter nativer Netzzuordnung erkannt und entfernt; die finale vollständige Kupfer-Netzidentitätsprüfung findet keine Abweichung.

Die unabhängige elektrische Prüfung vergleicht Teilequellen, zusammengeführte Teileliste, frisch exportierte native Schaltplan-XML und tatsächliche PCB-Pads: **keine elektrischen Zuordnungsfehler**. Der umfassendere Originalaudit meldet jedoch drei veraltete BOM-Eingabehashes: `design/chopper-parts.json`, `design/power-parts.json` und `design/wake-io-parts.json`. Deshalb lautet dessen Gesamt-Exit-Code 2; eine vollständig bestandene BOM-Herkunftsprüfung wird nicht behauptet. Die ursprüngliche Revision und ihre BOM-Dateien bleiben unverändert. Siehe [electrical-parity.json](reports/electrical-parity.json). Dessen unverändert übernommenes Feld `source_release` beschreibt ausschließlich die ursprüngliche Rev A; darin enthaltene Freigaben gelten nicht für diese neue Revision. Für Rev A2 ist ausschließlich [release-status.json](release-status.json) maßgeblich, mit sämtlichen Freigaben auf false.

## Restverbindungen und konkrete Ursachen

Der native Graph enthält 257 Netze und 267 Kupferkomponenten; die Summe `Komponenten pro Netz−1` ergibt 10, identisch zum ungekappten KiCad-Zähler. Keine Komponente ist padlos. [open-connections.json](reports/open-connections.json) enthält sämtliche Padendpunkte mit Footprint-/Pad-UUIDs, Positionen, Layern und die Track-/Via-UUIDs jeder offenen Komponente. Die folgenden Paare sind erläuternde Spannbaum-Verbindungen zwischen getrennten Komponenten, keine fertigen Routenvorschläge.

| Netz | Fehlende Verbindungen | Repräsentative Padendpunkte |
|---|---:|---|
| BUTTON_INT_N | 1 | U10.23 → U16.5 |
| CAN_STB | 1 | R242.2 → U10.34 |
| I2C_SCL | 2 | J23.2 → R227.2; J23.2 → U11.5 |
| I2C_SDA | 1 | R226.2 → J23.1 |
| LED_DATA_3V3 | 1 | U14.2 → U10.11 |
| SW_RESET_N | 2 | R218.1 → U60.1; U56.2 → U65.4 |
| TEMP_MAIN_ADC | 1 | C252.1 → U10.39 |
| TEMP_MOTION_ADC | 1 | C253.1 → U10.38 |

Die verbleibenden Übergänge verbinden räumlich getrennte Analog-, Wake-/Reset- und ESP-Inseln. Direkte lange Verbindungen kollidieren mit vorhandenen Gate-/Kelvin-/Schutzbahnen oder schneiden Versorgungsflächen. TEMP_MAIN_ADC wurde beispielsweise einzeln geometrisch freigeprüft, kreuzte beim Zusammenführen aber die neue CHIP_EN-Verteilung; dieser Kandidat wurde vollständig verworfen. TEMP_MOTION_ADC benötigt mehrere lokale Lagenwechsel an den Motion-Fault-/Temperaturbahnen und am Chopper. Die CAN_STB-Variante wurde wegen Antennen-Keepout und geteilter V3V3-Fläche verworfen. Offene Schutz-/Reset-Signale sind trotz 46/46 expliziter geprüfter Pfade kein funktionsfähiges Gesamtschutzsystem.

Die zwei verbleibenden Via-Befunde sind `MOTION_BUS_P` bei (220.0871,214.755), UUID `3616401c-fa4a-4aa6-a59e-17cd9cbb196d`, und `TEMP_MOTION_ADC` bei (233.7913,234.9251), UUID `e90b1fe4-1210-4f7e-9e54-4e6badf1678c`. Alle 32 Leiterbahnenden und 17 Beschriftungsbefunde stehen mit UUIDs im [nativen DRC-Bericht](reports/native-drc.json). Eine pauschale Löschung dieser Elemente wäre falsch: einzelne als dangling gemeldete Segmente tragen Anschlüsse über innere T-Verbindungen. Entfernt wurden nur nachgewiesene unbenutzte Endstücke beziehungsweise gezielt gekürzte freie Enden.

## Gefülltes Leistungskupfer und Mechanik

247/247 bedeutet durchgängiges tatsächlich gefülltes Kupfer für die ausdrücklich aufgeführten gleichlagigen Padpaare. Dokumentierte dünne Mess-/Gate-Taps sind aus diesem Kraftpfadnachweis ausgeschlossen. 46/46 bedeutet explizite Leiterbahn-/Via-Verbindungen der festgelegten kritischen Pfade; es ist keine vollständige Schutzfunktions-, Stromtragfähigkeits- oder EMV-Freigabe.

Ein zusätzlicher **MOTION_BUS_P-Querbalken auf In 2 bleibt unterbrochen**. Bei x 230.8,231.05 und 231.5 mm liegt zwischen y 154 und 163 mm kein Motion-Kupfer. Linker Teil und rechter Randstamm bilden unterschiedliche Kupferpolygone. Ursache ist die CHOP_QUALIFY_N-Via `8109d2d4-f675-4b9e-93c9-c5d556155e6a` bei (231.05,156.0625) und der In 2-Track `3fc99fc7-dc43-4db6-b64d-540838df5886` bis (231.05,167.35). Dieser zusätzliche Querbalken ist **nicht Bestandteil der 247-Paar-Liste**. Allgemeine elektrische Erreichbarkeit über andere Lagen ersetzt seinen Breiten- und Stromnachweis nicht.

Am endgültigen Hash wurden orthogonale Querschnitte im 0.05-mm-Raster geprüft: DRIVE F vertikal 8.0995 mm zusammenhängend, horizontal 8.3990 mm als Summe zweier Teilintervalle; LIFT In 1 mindestens 6.1995 mm zusammenhängend; SYS F horizontal 4.4 mm, vertikal 4.0013 mm als Summe um eine Bohrung; CHOPPER_N B Hauptband 4.8255 mm zusammenhängend. CHOP_DRAIN besitzt 986.372884 mm² gefüllte Fläche. Summierte Teilbreiten sind keine einzelne zusammenhängende Leiterbreite. Die vollständigen Werte, Bohrungsabzüge, Grenzen und der Motion-Unterbruch stehen in [filled-copper-review.json](reports/filled-copper-review.json). Ein globaler diagonaler Engstellen-, Temperatur- und Stromtragfähigkeitsnachweis fehlt.

Der nominale 2D-Platzierungsnachweis besteht: keine fremden Courtyard-Überschneidungen, Stecker-/Kabelabgänge, Presswerkzeug-, Schraubwerkzeug-, Busbar- und Antennenbereiche wurden mit dokumentierten Konturen geprüft. Er ist keine tolerierte 3D-Montagefreigabe. Offene Punkte sind Pressauflage und Werkzeuggeometrie, Kabelschuhe/Biegeradien, Gehäuse, BB6-L-Kopf-Freiräume sowie das noch nicht qualifizierte Shim-/Ebenheitstoleranzbudget. Die konkrete Anordnung und Freiräume stehen in [mechanical-interface.json](reports/mechanical-interface.json) und [identity-and-mechanics.json](reports/identity-and-mechanics.json). Bestückungsbeschriftung ist wegen 17 Befunden noch nicht fertigungsreif.

## Begrenzter Durchlauf und nächster Schritt

Arbeitsbeginn 13.09.2026, 15:37:17 UTC; vor Beginn `git fetch origin`, geltende AGENTS.md, CURRENT_STATE.md, Rev-A-Dokumentation und 280×220-Abschlussberichte gelesen. Eigener Worktree auf Basis von `e1d8eb9903d0bd09de5a7c72c426c4c882161fd6`. Nur der Lead schrieb Dateien/CAD; drei weitere Prüfer arbeiteten ausschließlich lesend. Alle älteren Platinenrevisionen bleiben unverändert.

Der selbst festgelegte Prüfzyklus wurde einmal von 20 auf maximal 28 Zyklen erweitert, als weiterhin messbarer Fortschritt vorlag; diese Erweiterung blieb endlich. Letzter Designeingriff begann 19:07:08 UTC, vor dem vorgesehenen Änderungsstopp 19:07:17 UTC. Danach nur Auswahlprüfung, finale Neufüllung und unveränderte Wiederholungsprüfungen. Der Stopp erfolgt wegen der 28-Zyklus-Grenze und des reservierten Abschlussfensters, **nicht** wegen angeblicher vollständiger Fertigstellung oder zweier aufeinanderfolgender Zyklen ohne Fortschritt. Die vollständige kompakte Zyklenliste steht in [cycle-and-stop-record.json](reports/cycle-and-stop-record.json).

Genau zwei selektive Autorouter-Aufrufe wurden verwendet, jeweils mit 13 ausdrücklich aufgelisteten Niedrigstromnetzen, maximal 150 Durchgängen und 598 s Prozessobergrenze. Bestehendes Kupfer war gesperrt; Leistungs-, Gate-, Kelvin-, Analog- und Schutznetze waren ausgeschlossen. Vom ersten Kandidaten bleiben 61 Objekte; die abgelehnten I²C-/LED-Teile schnitten Versorgungsflächen. Im zweiten Routingmodell wurden deshalb 70 harte Leistungsflächen-Sperren hinzugefügt. Der zweite Lauf endete nach kooperativem Zeitstopp regulär nach 546.719 s; nur 20 I2C_SDA-Objekte wurden nach nativer Prüfung übernommen. 31 SCL-Objekte mit Randabstandsfehler sowie sieben unnötige Ergänzungen wurden verworfen. Beide nativen Annahmeprüfungen erhielten 247/247 und 46/46. [autorouter-review.json](reports/autorouter-review.json) enthält Eingabehashes, Exit-Codes, Auswahl und Grenzen.

**Nächster eng begrenzter Arbeitsschritt:** ausschließlich den CHOP_QUALIFY_N-Lagenwechsel am zusätzlichen Motion-In 2-Querbalken untersuchen. Den Unterbruch anhand der genannten UUIDs reproduzieren, einen lokalen Lagenwechsel ober-/unterhalb des 4-mm-Kraftkorridors vorprüfen und nach Übernahme die gefüllte gleichlagige Breite sowie alle 247/46-Pfade und den vollständigen Padgraphen erneut prüfen. Maximal zwei geometrische Varianten, kein globales Rip-up. Erst nach bestandenem Nachweis die zehn Restverbindungen netzweise in gesperrten Schutzkorridoren ergänzen. Beschriftung und tolerierte 3D-Montageprüfung folgen nach elektrischer Vollständigkeit; Fertigungsfreigabe bleibt ein separater Auftrag.
