# HomeMy PMU Rev A2 – 280 × 260 mm

**CAD VOLLSTÄNDIG – DRAFT / NOT RELEASED – NICHT BESTELLBAR.** Die grafische Abschlusskontrolle und zwei frische Prüfserien sind am 16.11.2026 bestanden. Status: `cad_complete_pending_independent_review`. Unabhängige Prüfung und physische Produktionsqualifikation bleiben offen.

- Branch: `codex/pmu-rev-a2-280x260-layout`
- Basis dieser Wiederholungsprüfung: `0ca837e387a45cfac2556d204b3a2c90102ba566`
- PCB: `kicad/HomeMy_PMU_RevA.kicad_pcb`
- PCB-SHA-256: `2742638d03b884b8b6ac7bf7064ef98b2bd6c5a95377b7617b72999eb2e83bc2`
- PCB-Eingang und Ausgang dieser Wiederholungsprüfung sind byteidentisch.

Die bereits geschlossenen Netze CAN_STB, I2C_SDA und TEMP_MOTION_ADC sind weiterhin vollständig verbunden. Es bleiben **keine bekannten Routing-, Kurzschluss-, Kupferregel-, Beschriftungs- oder nominellen 2D-Mechanikbefunde**. Für diese Wiederholungsprüfung wurden keine Leiterbahnen, Bauteile oder Regeln geändert.

`native_cad_checks_complete`, `gui_close_reopen_verified` und `cad_complete` sind true. `orderable`, `fabrication_release`, `assembly_release`, `production_release` und `energization_release` bleiben false. Es wurde weder bestellt noch eine Bestromung oder Fertigung freigegeben. Maßgeblich ist [release-status.json](release-status.json); ältere Freigaben der ursprünglichen Rev A werden nicht auf A2 übertragen.

## Endprüfung am 16.11.2026

| Prüfung | Lauf 1 | Lauf 2 |
|---|---:|---:|
| Native ERC, alle Schweregrade | Exit 0, null Befunde | identisch |
| Native DRC, alle Trackfehler und Schaltplanparität | Exit 0, null Befunde | identisch |
| Offene Verbindungen / freie Tracks / freie Vias | 0 / 0 / 0 | 0 / 0 / 0 |
| Kurzschluss-/Abstands-/Beschriftungsbefunde | 0 | 0 |
| Native Schaltplan-/PCB-Paritätsbefunde | 0 | 0 |
| Vollständiger Quellen-/BOM-/Pad-Audit | Exit 0 | Exit 0 |
| Leistungspfad-Paare | **247/247** | **247/247** |
| Explizite kritische Pfade | **46/46** | **46/46** |
| Vollständiger nativer Konnektivitätsgraph | bestanden | identisch |
| Nominelle Mechanik und tatsächliches Antennenkupfer | bestanden | identisch |
| 18 Bereiche tatsächlich gefüllten Kupfers | unverändert bestanden | identisch |

KiCad 10.0.6 füllte alle Zonen erneut und speicherte die Platine in einer vollständigen, bytegenauen Kopie des versionierten Projekts; dieser Lauf endete mit DRC Exit 0. Alle 70 CAD-Eingaben blieben unverändert. Die Kopie schützte die bereits vor Arbeitsbeginn lokal abweichend serialisierte Projektdatei. Diese Benutzerdatei und die vorhandenen lokalen Einstellungen blieben erhalten und gehören nicht zu diesem Commit.

Die zuvor blockierte **grafische Kontrolle ist abgeschlossen**: Die exakte A2-Datei wurde zweimal frisch im PCB-Editor geöffnet, am vollständigen Pfad, Fenstertitel und Platinenhinweis identifiziert und angezeigt. Beide Male wurde KiCad vollständig beendet und das Prozessende geprüft. Die Anzeige bestätigte 1377 Pads, 1807 Vias, 3711 Leiterbahnsegmente, 257 Netze und null offene Verbindungen. Der PCB-Hash blieb unverändert.

Anschließend endeten **16/16 finale Prozesse regulär mit Exit 0**: je zweimal ERC, DRC, Leistungsprüfung, kritische Pfadprüfung, Mechanik/Konnektivität, Netzlistenexport, Quellen-/Exportaudit und elektrische Parität. In diesen finalen Serien gab es keinen Timeout, Absturz oder fehlenden Bericht. Der vollständige Ergebnisvergleich stimmt nach den dokumentierten Normalisierungen überein: generierte Zeitstempel sowie Pfad/Hash der frischen Netzliste; deren gesamter XML-Inhalt wurde zusätzlich bis auf `design/date` identisch verglichen. Vorläufige Hilfsprobleme bei der Prüferskriptrekonstruktion und der Einordnung einer neu erzeugten lokalen Einstellungsdatei sind dokumentiert und wurden nicht als bestandene Prüfungen gezählt.

[retest-2026-11-16.json](reports/retest-2026-11-16.json) enthält Ergebnisse, Grenzen und Eingabehashes; [verification-processes.json](reports/verification-processes.json) die Prozessnachweise. Die wiederherstellbaren Prüferquellen stehen in [retest-methods.json](reports/retest-methods.json). [input-hashes.json](reports/input-hashes.json) beschreibt den versionierten CAD-Stand. Die Restnetz- und Dangling-Listen in [open-connections.json](reports/open-connections.json) sind leer. Der frische native Graph umfasst 6815 konkrete Pad-/Track-/Via-Objekte, 257 Netze und genau 257 Komponenten ohne padlose Teilkomponenten.

## Elektrische und geometrische Identität

Elektrische Quelle bleibt die ursprüngliche `../rev-a/`, Referenzhash `13fcae0f58c9a6ac5f85eb721c24b44169a65f628baad6586bcd6002f4c17cfe`. Die eigenständig aufgebaute 280×260-Revision wurde im isolierten Worktree geprüft. Keine ältere Revision wurde geändert. Die spätere ausdrückliche 280×260-Anweisung des Nutzers bestimmt die Geometrie dieses Auftrags.

Die Edge-Cuts-Mittellinien bilden exakt `(0,0)–(280,0)–(280,260)–(0,260)` mm. Erhalten sind **425 Footprints, 1377 physische Pads einschließlich Montagepads, vier Kupferlagen, 40 Testpunkte, 48 Press-fit-Bohrungen und vier Befestigungen**. Werte, DNP, Pad-/Footprint-UUIDs, Netzidentitäten, Schutzfunktionen, Stackup, Netzklassen, Gate-/Kelvin- und Net-Tie-Konzept bleiben erhalten. DNP: `C244`, `J13`, `R243`, `R244`.

Im versionierten Stand sind **69/69 Nicht-PCB-CAD-Dateien byteidentisch zur ursprünglichen Rev A**. Im vorhandenen Worktree sind es 68/69; die vorbestehende `.kicad_pro` unterscheidet sich ausschließlich durch Zeilenenden und die Reihenfolge inhaltsgleicher benannter Netzklassen. Klasseninhalte, Prioritäten und alle übrigen JSON-Werte sind gleich. Keine Regel wurde abgeschwächt oder neu ausgenommen.

Der unveränderte historische Kupferherkunftsnachweis erfasst 5595 Kupferobjekte: 4379 übernommene und 1216 neue, mit Geometrieabgleich und 973 Padankern. Es gibt keine unbelegte Kupfer-UUID. Einzelheiten stehen in [copper-provenance.json](reports/copper-provenance.json); die damaligen lokalen Reparaturen sind im Basiscommit vollständig dokumentiert. Dieser Durchlauf enthält **null CAD-Editierzyklen und null Autorouter-Aufrufe**. Der historische Stand bleibt bei sieben Fortsetzungszyklen und insgesamt zwei Autorouter-Aufrufen.

## Gefülltes Kupfer und Fertigungsentwurf

Zwei frische Auswertungen untersuchten tatsächlich gefülltes Kupfer einschließlich Pads, Leiterbahnen und Bohrungsabzügen in 18 definierten Bereichen. Raster: 0,01 mm; native Polygonisierung: 0,005 mm. Alle Messwerte entsprechen dem vorherigen Prüfstand. Der historische Ausschlussbestand umfasst 494 Tap-UUIDs; davon sind aktuell 447 Objekte vorhanden. Die 47 bereits entfernten Objekte werden nicht als vorhandenes Kupfer gezählt.

Beispiele: DRIVE-F-Stamm 8,0995 mm, LIFT-In1 6,1995 mm, CHOPPER-N-Hauptengstelle 4,7656 mm, Motion-In2 am HYS-Übergang 4,5995 mm. SYS-F hat am Lochquerschnitt 4,0003 mm **als Summe getrennter Intervalle**, davon maximal 3,0002 mm in einem Intervall; der horizontale Stamm ist 4,4 mm breit. Diese Stichproben ersetzen keinen globalen allwinkligen Engstellen- oder thermischen Belastungsnachweis. [filled-copper-review.json](reports/filled-copper-review.json) enthält Messbereiche, Intervalle und Grenzen.

Der [DRAFT-Fertigungsprüfsatz](manufacturing/DRAFT_NOT_RELEASED.md) enthält elf native Gerber-Lagen, Gerber-Job, getrennte PTH-/NPTH-Bohrdateien, 327 SMD-Positionen und die unveränderte elektrische BOM. Seine Exportdateien wurden erneut gegen Hashes und native Geometrie geprüft und bleiben byteidentisch. Aktualisiert wurden ausschließlich Status-/Prüfmetadaten und die zugehörigen Manifesthashes.

Alle **1950 metallisierten und vier nicht metallisierten Bohrungen**, darunter 48 Press-fit-Bohrungen mit 1,475 mm, stimmen mit den nativen Koordinaten überein; maximale Excellon-Quantisierung 0,0005 mm. Das Gerber-Fräsprofil ist exakt 280×260 mm. Die native Jobangabe 280,05×260,05 mm ist die grafische Strichhülle, kein Fräsmaß. Die BOM umfasst 356 Einkaufspositionen, davon 352 bestückt und vier DNP, 124 gruppierte Zeilen und 31 externe Zeilen. Press-fit-, THT- und Busbar-Arbeiten sind in BOM und [mechanischer Schnittstelle](manufacturing/busbar-pcb-interface.json) beschrieben.

## Offene Abnahme und begrenzter nächster Schritt

Die nominellen Courtyard-, Werkzeug-, Anschluss-, Press-fit- und Busbar-Abstände bestehen. Im Antennen-Keepout liegt auf keiner der vier Kupferlagen tatsächliches Kupfer. Eine tolerierte Montage- und Produktionsqualifikation ist damit nicht nachgewiesen. Offen bleiben insbesondere:

- Unabhängige fachliche Prüfung des exakten CAD-/Entwurfssatzes.
- Shim-/Folienstapel mit nur 0,01 mm Reserve vor Ebenheit und Verformung; reale Kontaktkraft-/Widerstands-/Thermozyklus-Coupons fehlen.
- Press-fit-Los-, Bohr-/Metallisierungs-, Kraft-Weg- und Ausdrücknachweise; genaue Kabelschuhe, Werkzeuge, Kabelradien und endgültige Träger-/Gehäusestapel fehlen.
- Reale Einschalt-, Rückspeise-, Chopper-, Temperatur-, Kalibrier-, Selektivitäts- und Schutztests sowie Firmware-/System-/Sicherheitsvalidierung fehlen.

[production-readiness.json](reports/production-readiness.json) führt die neun Produktionskategorien, B01–B14 und konkreten mechanischen Reserven auf. Es wurden keine physischen Tests durchgeführt und keine offenen Produktionsbedingungen durch CAD-Ergebnisse geschlossen. Parallel beauftragte Agenten arbeiteten ausschließlich lesend; nach deren Nutzungslimit übernahm der Lead die Prüferkontrolle und finalen regulären Prüfläufe. Das ersetzt keine unabhängige menschliche Prüfung.

**Nächster begrenzter Schritt:** Unabhängige Prüfung dieses exakten Entwurfssatzes, beginnend mit Press-fit-Prozess und Busbar-/Shim-Toleranzkette; anschließend die zutreffenden physischen Nachweise aus B01–B14 mit versionierten Rohdaten und überprüften Annahmekriterien erbringen. Für bekannte Routingbefunde ist keine weitere CAD-Reparatur nötig. Sämtliche Freigabeflags bleiben bis zur jeweils belegten Freigabe false.
