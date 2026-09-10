# Anschluss- und Gehäusemontage Rev A

Diese Unterlage ergänzt die exakten Pin-Netze in `../design/chopper-parts.json` und die Herstellerquellen in `../evidence/chopper/source_manifest.json`. Die Leiterplatte ist ein Engineering-Prototyp. Montage- und Kabelartikel, die als Auswahlpunkt gekennzeichnet sind, dürfen nicht ohne passende mechanische Prüfung als bereits beschafft oder qualifiziert gelten.

Die verbindlichen Bauteilrichtungen, Gate-/Pin-1-Koordinaten und M5-Anschlussflächen sind in [ASSEMBLY_ORIENTATION.md](ASSEMBLY_ORIENTATION.md) mit einer vergrößerten Padansicht dokumentiert.

## Hochstrom J1..J6

Alle sechs Anschlüsse: Würth7461103, rechtwinkliger Pressfit-Anschluss,9×9 mm Grundfläche und14 mm oberhalbPCB. Der M5-Anschluss sitzt an einer **senkrechten** Anschlussfläche; Schraubachse und Kabelschuhzugang sind horizontal. Es handelt sich nicht um einen senkrechten M5-Stehbolzen. Herstellerzeichnung Seite1 legt die Flansch-/Gewindegeometrie fest;5.0±0.2 mm Materialstärke an der Gewindezone. Generische Blindloch-Hinweise im Datenblatt dürfen nicht mit einer M5-Stehbolzen-Geometrie verwechselt werden.

| Ref | Netz | Leitungsansatz für Prototyp | Montageziel |
|---|---|---|---|
| J1 | BATT_FUSED_P |6 mm² Cu; externe Sicherung vorPCB | positiver Batterieeingang |
| J2 | BATT_N |6 mm² Cu | gemeinsamer Batterierückleiter |
| J3 | MOTION_BUS_P |4 mm² Cu | linker Arm positiv |
| J4 | ARM_L_N |4 mm² Cu | linker Arm getrennt zumNT1 |
| J5 | MOTION_BUS_P |4 mm² Cu | rechter Arm positiv |
| J6 | ARM_R_N |4 mm² Cu | rechter Arm getrennt zumNT2 |

Passende M5-Ringkabelschuhe sind für genau den jeweiligen Leiteraufbau/Querschnitt zu wählen; Herstellerartikel, Crimpwerkzeug, Matrize, Abisoliermaß und Crimphöhe sind noch zu bestimmen. Querschnitt allein belegt keine50-A-Leitungsauslegung: Länge, Isolationsklasse, Bündelung, Umgebung, Kontakt- und Sicherungstemperatur sind in der Installation zu berücksichtigen. Zum prüfbaren Muster gehören Kabel-Längenliste und gemessener Widerstand jeder fertigen Leitung. Keine verzinnten Litzen in Schraubklemmen; keine mehreren Kabelschuhe auf einem Anschluss ohne eigene Stack-up-Prüfung.

Ringkabelschuh flach auf die verzinnte Anschlussfläche legen. Geeignete glatte Unterlegscheibe und Schraubenlänge passend zur tatsächlichen Gewindetiefe auswählen; vollständiger Eingriff ohne Aufsetzen am Anschlag oder Kollision hinter dem Gewindeflansch. M5-Befestigungsdrehmoment **höchstens2.2 Nm** nach Hersteller; Zielwert durch die gewählte Schrauben-/Ringkabelschuh-Kombination festlegen. Rechtwinkligen Anschluss während des Anziehens mechanisch gegenhalten, damit das Drehmoment nicht über Pressfit-Pins in die Platine gelangt. Keinen Stromtragfähigkeitsnachweis aus dem160-A-Datenblattwert@20°C ableiten: Hersteller nennt ausdrücklich PCB, Kabelschuh und Kabelquerschnitt als begrenzende Einflüsse.

Für die Gehäuseanordnung je M5-Fläche zunächst mindestens 25 mm freien axialen Schraub-/Werkzeugzugang und einen Kabelbiegeraum nach dem ausgewählten Kabeldatenblatt vorsehen. Diese 25 mm sind Montageplanungsreserve, keine verifizierte Werkzeughülle. Die Richtungstabelle in ASSEMBLY_ORIENTATION.md ist am realen Muster mit Gehäuse und Werkzeug abzugleichen. Die 9 × 9 mm Körperkontur allein beschreibt keine Kabelhülle. Separate Kabelklemmen am Träger oder Gehäuse so anordnen, dass Zug, Biegung und Servicekräfte nicht vom Terminal aufgenommen werden.

## Schraubklemmverbinder und Pinfolge

J7..J15: PCB-Header Phoenix1776508, zweiPole5.08 mm, Gegenstück1777989. Acht Gegenstücke bestückt, ein weiteres nur beiDNP-OptionJ13. J18: Header1776511, dreiPole5.08 mm, Gegenstück1777992. Die Schraubflansche des Gegenstücks sichern die Paarung; keine bloß ähnliche ungeflanschte Kontur als Austausch annehmen. Header-Footprint1.4-mm-PTH und2.08×3.6-mm-Lands sind aus der dokumentierten Bibliothekszuordnung übernommen; fertige Gehäuse/Flansche gegen Herstellerzeichnung und Muster kontrollieren.

| Ref | Pin1 | Pin2 | Pin3 | Leitungsansatz |
|---|---|---|---|---|
| J7 | MOTION_BUS_P | DRIVE_N |—|1.5 mm²,8-A-Zweig |
| J8 | MOTION_BUS_P | LIFT_N |—|1.0 mm², externer24-V-Wandler |
| J9 | PC_BUCK_IN_P | PC_N |—|1.0 mm² |
| J10 | LOGIC_BUCK_IN_P | LOGIC_BUCK_N |—|1.0 mm² |
| J11 | +5V | LOGIC_5V_N |—|1.0 mm²,5-V-Wandlerausgang |
| J12 | MOTION_BUS_P | CHOP_DRAIN |—|1.5 mm², verdrilltes Paar zur5-Ω-Bank |
| J13 | LIFT_24V_SAMPLE | LIFT_24V_N |—|DNP optional; separater externer24-V-Abgriff |
| J14 | CHOP_NTC | CHOP_GND |—|0.25 mm², eigener analoger NTC |
| J15 | CHOP_TEMP_ADC | LOGIC_GND |—|0.25 mm², unabhängiger Telemetrie-NTC |
| J18 | +5V | LED_DATA_OUT | LOGIC_5V_N |1.0 mm² Versorgung/Rückleiter,0.25 mm² Daten |

Die Tabelle ist eine Montagehilfe, keine alternative Netzquelle. Vor Konfektion alle Pin-Netze mit dem versionierten JSON vergleichen. Gleiche Steckgesichter für verschiedene Spannungen verlangen feste Kennzeichnung und eine mechanische Fehlsteckvermeidung im Kabelbaum/Gehäuse. Besonders J10(Batteriebus-Wandlereingang) und J11(5-V-Ausgang) dürfen nicht vertauschbar frei nebenliegen. Abisolierlänge, Aderendhülse, Schraubmoment und zulässiger Leiterbereich ausschließlich vom konkret bestellten Gegenstück übernehmen; diese Daten werden nicht aus einem ähnlichen Phoenix-Stecker interpoliert.

J18-Rückstrom undC246 gehen aufLOGIC_5V_N unmittelbar zumJ11.2/NT8. Die gemeinsame Datenreferenz entsteht am Stern; LED-Leistungsstrom darf nicht durch die kleineLOGIC_GND-VerbindungNT9 fließen. Rückleiteranschluss als eigener Leistungsleiter führen, LED-Datenleitung daneben, keine Rückstromführung über CAN-Schirm oder USB.

## CAN und externe Bremseinheit

J16/J17: JSTBM04B-GHS-TBT(LF)(SN), GegenstückeGHR-04V-S×2, KontakteSSHL-002T-P0.2×8 plus Reserve. Pin1CAN_H,2CAN_L,3LOGIC_GND,4CHASSIS. CAN_H/CAN_L verdrillen; Pin4 ist Schirm/Chassis, kein Versorgungsrückleiter. Passendes JST-Crimpwerkzeug und zugehörigen Leiter-/Isolationsbereich beim Konfektionierer festlegen. Abschlüsse gemäß Gesamtnetz, nicht automatisch beide Boardanschlüsse terminieren.

Externe Bremseinheit: zweiRH10010R00FE01 parallel, je10 Ω/100 W, jede auf eigener305×305×3.2-mm-Aluminiumplatte. Diese Montagebasis entspricht gerundet der Herstellerplatte12×12×0.125 Zoll je Widerstand; die Wärmeabgabe hängt weiterhin von Luftführung/Einbau ab. Befestigungslochbild und Anschlussgewinde nach derRH100-Zeichnung im archiviertenVishay30201-Datenblatt verwenden, nicht aus einemRH050-Gehäuse übertragen. Die konkret gebohrte Widerstandsplatte ist noch kein Teil dieser Busbar-Fräszeichnung; Lochbildübernahme und Artikelprüfung des angeliefertenRH100 bleiben Fertigungsarbeitspunkte.

Beide NTCs elektrisch getrennt nahe der thermisch ungünstigen Widerstands-Gehäusestelle befestigen. Fixierung/Isolierung müssen den ausgewählten NTC und die Gehäusetemperatur vertragen; ein lose in der Luft hängender NTC erfüllt die analoge Abschaltfunktion nicht. Die genaue Wärmeübergangszeit vom Heizkörper zum Sensor ist zu messen. LeistungspaarJ12 kurz und gemeinsam führen, Schleifenfläche begrenzen, Abstand zu CAN/NTC. Externe Widerstandsanschlüsse gegen Berührung und Kurzschluss abdecken, Kabel am Plattenträger zugentlasten.

Die dokumentierte Hersteller-Überlastprüfung5×Nennleistung für5 s ist eine Bauteil-Prüfbedingung. Der500-J-Bankversuch bleibt ein kalter, beaufsichtigter Prototypversuch mit stufenweisem Energieaufbau gemäßBringup-Unterlagen; keine Freigabe für wiederholtes Abbremsen oder einen Motorbetrieb. Kühlplatten, Sensormontage und Anschlussimpedanz sind Teil dieser Prüfung.

## Gehäusehöhen und erste Montagekontrolle

UnterPCB mindestens15 mm Raum für isolierte Schienen/Schrauben/Abdeckung. OberhalbC312/C313 mindestens36.5 mm Körperhöhe plus5 mm freie Ventilzone; keine Querschiene oder Kabel direkt über den Elektrolytkondensator-Ventilen. Die3D-Höhe aller Filmkondensatoren, Schraubflansche, Kabelschuhe und Stecker am realen Muster kontrollieren. Kein Metallträger im ESP-Antennenfreiraum; H3-Zielposition292,292 ist außerhalb der bisher beanstandeten Ecke.

Montageprotokoll: Fotos aller Pressfit-Pins, Kabelschuh-/Schraubenartikel und Kräfte, Crimpprotokoll, Klemmkraft derM3-Bar-Verbindungen, Vierleiter-Kontaktwiderstände, Durchgang jedes Netzes, ungewollte Brückenfreiheit vor Einsetzen optionalerNB-/Bar-Teile soweit prüfbar, Kabel-/Gehäusefreigängigkeit und Isolationsfolienlage. Es liegt noch kein solches Musterprotokoll vor.
