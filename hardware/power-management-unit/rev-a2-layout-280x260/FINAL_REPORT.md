# HomeMy PMU Rev A2 – 280 × 260 mm

**WIP – NICHT BESTELLBAR. Das Layout bleibt unvollständig; sämtliche Freigabeflags sind false.**

Branch: `codex/pmu-rev-a2-280x260-layout`
Fortsetzung von Commit: `fbfa7675531354aed1ec0358987397bb4b4bddf4`
PCB: `kicad/HomeMy_PMU_RevA.kicad_pcb`
PCB-SHA-256: `d4a9420958a3cee69e000600df9e1787f2b3d719b167e1c4359ce758362bd0a6`

Der ausgewählte, zweimal nativ geprüfte Fortsetzungsstand aus Zyklus 7 reduziert die offenen Verbindungen von **10 auf 3** und die Dangling-Befunde von **34 auf 7**. Der zusätzliche Motion-In2-Unterbruch ist geschlossen und seine HYS-Engstelle verbreitert. Reset, Haupttemperaturmessung, Taster, LED und I²C-SCL sind vollständig verbunden. Die revisionslokale BOM-Herkunftsprüfung besteht nun. **CAN_STB, I2C_SDA und TEMP_MOTION_ADC bleiben offen.** DRC ist nicht bestanden; `cad_complete`, `orderable`, `fabrication_release`, `assembly_release`, `production_release` und `energization_release` bleiben false. Keine Bestellung und kein Gerber-/Bohr-/Pick-and-Place-Fertigungsprüfsatz wurden ausgelöst.

## Endprüfungen am unveränderten Stand

| Prüfung | Lauf 1 | Lauf 2 |
|---|---:|---:|
| Native ERC | Exit 0, keine Befunde | gleich |
| Native DRC, alle Schweregrade | **Exit 5, nicht bestanden** | gleich |
| Offene Verbindungen | **3** | **3** |
| Kurzschluss-/Abstands-/Kupferregelbefunde | 0 | 0 |
| Freie Leiterbahnenden / einlagige Via | 6 / 1 | 6 / 1 |
| Beschriftungsüberlappung / über Kupfer | 9 / 8 | 9 / 8 |
| Native Schaltplan-/PCB-Paritätsbefunde | 0 | 0 |
| Vollständiger Quellen-/BOM-/Pad-Audit | Exit 0, keine Fehler | gleich |
| Erforderliche Leistungspfad-Paare | **247/247** | **247/247** |
| Explizite kritische Pfade | **46/46** | **46/46** |
| Vollständiger Padgraph gegen Fortsetzungseingang | keine Regression | gleich |
| Kupferidentität / Geometriebeleg / nominelle Mechanik | Exit 0 | Exit 0 |

KiCad 10.0.6 hat sämtliche Zonen nativ neu gefüllt und gespeichert. Der genaue Projektpfad wurde im grafischen PCB-Editor geöffnet, der Editor vollständig beendet, frisch gestartet und dieselbe Platine erneut geladen. Die PCB blieb dabei unverändert. Beim Schließen sortierte KiCad lediglich das Array der Netzklassen in `.kicad_pro` um; Namen, Prioritäten und Regelwerte blieben gleich. Nach vollständigem Editorende wurde die ursprüngliche Projektdatei byteidentisch wiederhergestellt. Ausschließlich die danach ausgeführten Serien `resume-proof1` und `resume-proof2` sind verbindlich; ein vorläufiger Lauf wurde ersetzt.

Alle finalen Prozesse endeten regulär, ohne Absturz, Timeout oder fehlenden Bericht. Alle 70 CAD-Eingabedateien blieben während beider Serien unverändert. Die vollständigen Graphen und sämtliche tatsächlichen DRC-Befunde stimmen überein. KiCad wählte beim offenen TEMP_MOTION_ADC-Ziel zwei unterschiedliche repräsentative Trackobjekte derselben unveränderten Komponente. Beide Rohzeugen sind dokumentiert; beide DRC-Läufe bleiben fehlgeschlagen. [verification-processes.json](reports/verification-processes.json) enthält Befehle, Exit-Codes, Hashbezüge und Wiederholungsvergleich; [input-hashes.json](reports/input-hashes.json) die Eingabehashes.

## Elektrische Identität und Änderungen

Elektrische Quelle bleibt ausschließlich die ursprüngliche `../rev-a/`, PCB-Referenzhash `13fcae0f58c9a6ac5f85eb721c24b44169a65f628baad6586bcd6002f4c17cfe`. Die neue 280×260-Geometrie aus dem vorherigen Auftrag wird fortgesetzt; keine ältere Revision wurde überschrieben. In diesem Durchlauf wurden keine Bauteile verschoben. Die Edge-Cuts-Mittellinien bleiben exakt `(0,0)–(280,0)–(280,260)–(0,260)` mm.

Erhalten sind 425 Footprints, 1377 physische Pads einschließlich Montagepads, vier Kupferlagen, 40 Testpunkte, 48 Pressfit-Bohrungen und vier Befestigungsbohrungen. Werte, Pad-/Footprint-UUIDs, Netzidentitäten, Stackup, Schutz-, Gate-/Kelvin- und Net-Tie-Konzept bleiben erhalten. DNP: `C244`, `J13`, `R243`, `R244`. **69/69 Nicht-PCB-CAD-Dateien sind byteidentisch zur ursprünglichen Rev A.** Keine Mindestbreite oder Via-Regel wurde abgesenkt; keine pauschale Ausnahme angelegt.

Die finale Kupferprüfung erfasst 5368 Track-/Viaobjekte und 77 Zonen: 4388 erhaltene Quellobjekte und 1057 neue Objekte, ohne unbelegte UUID. Sämtliche ausgewählten Quell-/Zielgeometrien und 973 Padanker stimmen mit dem nativen Stand überein. Entfernte Einzelobjekte aus ursprünglichen Power-Tap-Gruppen sind ausdrücklich als verworfen dokumentiert; diese Gruppen werden nicht pauschal als unverändert ausgegeben. [copper-provenance.json](reports/copper-provenance.json) enthält die vollständigen Zuordnungen.

Die zusätzliche Motion-In2-Verteilung wurde durch einen lokalen CHOP_QUALIFY_N-Lagenwechsel und die Verlagerung der neuen HYS-Via geschlossen. Die Reset-Verbindung erhielt einen gezielten B.Cu-Übergang, damit CHOP_GND nach dem Füllen zusammenhängend bleibt. Nur nach nativer Padgraph-Prüfung wurden vollständige unbenutzte Kupferäste entfernt oder bis zum tatsächlichen Anschluss gekürzt.

**Kein neuer Autorouter-Aufruf.** Die zwei historischen Aufrufe bleiben das Gesamtmaximum. 18 bereits erzeugte SCL-Kandidaten des zweiten historischen Laufs wurden selektiv übernommen; eine randnahe Via und zwei anschließende Endpunkte wurden lokal korrigiert. Frische UUIDs und Zuordnung zur historischen Geometrie sind dokumentiert. Die Übernahme senkte offene Verbindungen, ohne neue elektrische DRC-Befunde oder Verlust eines Leistungs-/kritischen Pfades. [autorouter-review.json](reports/autorouter-review.json) trennt historische Läufe und diese spätere Auswahl.

Die lokale BOM enthält unverändert 356 Einkaufspositionen, davon 352 bestückt und vier DNP, zusammengefasst in 124 Zeilen sowie 31 externe Zeilen. Alle 13 Eingabe- und vier Ausgabehashes bestehen. Elektrische Stücklisteninhalte wurden nicht geändert; Busbar- und Kontaktgeometrie stammen aus dieser Revision. Historische Material-/Montagequellen sind mit `../rev-a/` abgegrenzt. Die Dateien in [manufacturing](manufacturing/DRAFT_NOT_RELEASED.md) sind ausschließlich **DRAFT / NOT RELEASED**. Historische `source_release`-Felder im Paritätsbericht gelten nicht für diese Revision; maßgeblich ist [release-status.json](release-status.json).

## Verbleibende Verbindungen und Befunde

Der native Graph enthält 257 Netze, 260 Kupferkomponenten und keine padlose Komponente. Die ungekappte Summe der erforderlichen Zusammenführungen ist drei. [open-connections.json](reports/open-connections.json) enthält alle Padendpunkte, Footprint-/Pad-UUIDs, Koordinaten, Layer und Track-/Via-UUIDs der getrennten Komponenten.

| Netz | Repräsentative getrennte Padendpunkte | Konkrete verbleibende Ursache |
|---|---|---|
| CAN_STB | R242.2 → U10.34 | Der lokale Weg durch Wake-/ESP-Bereich ist nicht durchgehend frei: Quellenübergänge nahe RESET/BUTTON/GND sowie die Übergänge am UART-/Permit-Anschlussfeld kollidieren mit vorhandenen Leiterbahnen, Pads oder Vias. |
| I2C_SDA | R226.2 → J23.1 | Lokale Übergänge an INA_ALERT, CHOP_FAULT, MOTION_ARMED und GND-Vias bleiben ungeklärt. Die östlichen Via-Positionen müssen zusätzlich den 0,50-mm-Abstand der Motion-Leistungsfläche erhalten. |
| TEMP_MOTION_ADC | C253.1 → U10.38 | Sensor-/Westkanal ist nicht vollständig verbunden: vorhandener SYS-Abgriff, AON_RESET und CHIP_EN kreuzen den geplanten Stamm. Eine untersuchte Via bei (113.2,92.6) würde den SYS-F-Stamm von 4,4 auf 2,995 mm verengen und wurde verworfen. |

Die verbleibende einlagige TEMP_MOTION_ADC-Via liegt bei `(233.7913,234.9251)`, UUID `e90b1fe4-1210-4f7e-9e54-4e6badf1678c`. Sämtliche sechs freien Trackenden und 17 Beschriftungsbefunde stehen mit UUIDs im [nativen DRC-Bericht](reports/native-drc.json). Sie wurden weder ausgenommen noch verborgen. Nicht vollständig freigeprüfte Routingvorschläge wurden nicht in die PCB geschrieben. Beschriftungsoptimierung wurde entsprechend der vorgegebenen Reihenfolge zurückgestellt.

## Gefülltes Leistungskupfer und Montagegrenzen

Zwei unabhängige, frische Kupferauswertungen mit identischem 0,01-mm-Raster stimmen überein. Im zusätzlichen Motion-In2-Balken bleiben **null statt 78 Nullschnitte**; seine drei vorher getrennten Proben liegen nun in einem gemeinsamen Polygon. Das HYS-Minimum steigt von 3,6949 auf **4,5995 mm**, am QUALIFY-Übergang liegen mindestens **7,2995 mm** zusammenhängendes Kupfer vor.

Die untersuchten übrigen Querschnitte bleiben gegenüber dem Eingang unverändert: DRIVE-F-Stamm 8,0995 mm, LIFT-In1 6,1995 mm, CHOPPER-N-Hauptengstelle 4,7656 mm. SYS-F erreicht am Lochquerschnitt 4,0003 mm **als Summe getrennter Intervalle**; der horizontale Stamm hat 4,4 mm. CHOP_DRAIN-Fläche: 986,372884 mm². Summen sind keine einzelne zusammenhängende Leiterbreite. [filled-copper-review.json](reports/filled-copper-review.json) enthält Rasterbereiche, Bohrungsabzüge, Einzelintervalle, beide Prozesslaufzeiten und Grenzen. Kein globaler allwinkliger Engstellen-, Ampazitäts- oder Thermiknachweis wird behauptet.

Nominelle Courtyard-, Pressfit-, Busbar-, Werkzeug- und Anschlussabstände bestehen; im ESP-Antennen-Keepout liegt auf keiner der vier Lagen tatsächliches Kupfer. Eine tolerierte Montagefreigabe bleibt offen: Shim-/Folienüberstand nur **0,01 mm vor Ebenheit**, fehlende Klemmkraft-/Kontaktwiderstands-Coupons und Pressfit-Losnachweise sowie noch nicht vollständig bestimmte Kabelschuhe, Werkzeuge, Kabelradien und Träger. Aktuelle rechnerische Reserven: BB7/NT5 **0,45 mm**, BB6-Washer **1,2 mm** nach den angegebenen Kontur-/Lochtoleranzen. Diese Werte ersetzen kein geschlossenes Montagebudget. Details in [identity-and-mechanics.json](reports/identity-and-mechanics.json).

## Begrenzung und nächster Schritt

Fortsetzungsbeginn: 13.09.2026, 19:40:25 UTC. Vor Beginn wurden Origin aktualisiert und die geltenden AGENTS-, CURRENT_STATE-, Rev-A- und Rebuild-Dokumente gelesen. Nur der Lead schrieb Dateien; drei Prüfer arbeiteten ausschließlich lesend. Der isolierte Branch und Worktree wurden beibehalten.

Festgelegt waren höchstens zwölf Editier-/Prüfzyklen, zwei erfolglose Zyklen hintereinander als Stoppkriterium, begrenzte Versuche je unveränderter Ursache sowie vier Stunden einschließlich Abschlussfenster. **Sieben CAD-Zyklen wurden verwendet, fünf Stände angenommen; die zwei verworfenen Stände wurden jeweils gezielt korrigiert.** Kein Zeit- oder Zyklusmaximum wird als erreicht behauptet. Der Durchlauf endet wegen der ungelösten lokalen Routingengstellen nach den begrenzten Korridor- und Übergangsprüfungen; der vollständig geprüfte Zyklus 7 bleibt erhalten. Vorprüfungen ohne CAD-Schreibvorgang sind keine zusätzlichen abgeschlossenen CAD-Zyklen. [cycle-and-stop-record.json](reports/cycle-and-stop-record.json) dokumentiert Fortschritt und Stopp.

**Nächster eng begrenzter Schritt:** ausschließlich den Sensor-/Westkanal für TEMP_MOTION_ADC schließen. Vom bereits vorhandenen Sensor-Via `(170.9448,82.7809)` ausgehen, zunächst das Portal außerhalb des 4,4-mm-SYS-Stamms prüfen und danach die konkreten SYS-/AON_RESET-/CHIP_EN-Kreuzungen mit lokalen Lagenwechseln lösen. Keine weitere Südkorridor-Neuplanung; der bereits untersuchte südliche Anschluss ab `(113.2,251.3)` ist geometrisch frei. Maximal zwei vollständige Kandidaten, jeweils frisches Füllen, DRC, 247/46 und vollständiger Padgraph; bei keinem bestandenen Kandidaten stoppen. Die Platine bleibt bis zum vollständigen Abschluss und separater Freigabe nicht bestellbar.
