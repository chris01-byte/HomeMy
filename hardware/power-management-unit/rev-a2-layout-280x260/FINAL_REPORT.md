# HomeMy PMU Rev A2 – 280 × 260 mm

**WIP – NICHT BESTELLBAR. Alle nativen CAD-Prüfungen bestanden; die vorgeschriebene grafische Schließen-/Öffnen-Kontrolle und die Produktionsqualifikation sind noch offen.**

- Branch: `codex/pmu-rev-a2-280x260-layout`
- Fortsetzung von Commit: `eb2261104dbb95eb9bb6226e4644d3709d0f3eae`
- PCB: `kicad/HomeMy_PMU_RevA.kicad_pcb`
- PCB-SHA-256: `2742638d03b884b8b6ac7bf7064ef98b2bd6c5a95377b7617b72999eb2e83bc2`
- Eingangshash: `d4a9420958a3cee69e000600df9e1787f2b3d719b167e1c4359ce758362bd0a6`

Die letzten drei Netze **CAN_STB, I2C_SDA und TEMP_MOTION_ADC sind vollständig verbunden**. Alle sieben bisherigen Dangling-Befunde und alle 17 Beschriftungsbefunde sind beseitigt. Es bleiben **keine bekannten Routing-, Kurzschluss-, Kupferregel- oder nominellen 2D-Mechanikbefunde**. Das unveränderte Ergebnis besteht zwei vollständige native Prüfserien.

`native_cad_checks_complete` ist true. `cad_complete` bleibt wegen der nicht ausgeführten grafischen Abschlusskontrolle false. `orderable`, `fabrication_release`, `assembly_release`, `production_release` und `energization_release` bleiben ebenfalls false. Es wurde weder bestellt noch eine Bestromung oder Fertigung freigegeben. Maßgeblich ist ausschließlich [release-status.json](release-status.json); ältere Freigaben der ursprünglichen Rev A werden nicht auf A2 übertragen.

## Endprüfung

| Prüfung | `finish-final1` | `finish-final2` |
|---|---:|---:|
| Native ERC, alle Schweregrade | Exit 0, null Befunde | identisch |
| Native DRC, alle Trackfehler und Schaltplanparität | Exit 0, null Befunde | identisch |
| Offene Verbindungen / freie Tracks / freie Vias | 0 / 0 / 0 | 0 / 0 / 0 |
| Kurzschluss-/Abstands-/Beschriftungsbefunde | 0 | 0 |
| Native Schaltplan-/PCB-Paritätsbefunde | 0 | 0 |
| Vollständiger Quellen-/BOM-/Pad-Audit | Exit 0 | Exit 0 |
| Leistungspfad-Paare | **247/247** | **247/247** |
| Explizite kritische Pfade | **46/46** | **46/46** |
| Vollständiger Padgraph gegenüber dem Eingang | keine Regression | identisch |
| Kupferherkunft, Geometrie, nominelle Mechanik, Antennenkupfer | bestanden | identisch |
| Gefüllte Leistungsquerschnitte gegenüber dem Eingang | erhalten | identisch |

KiCad 10.0.6 füllte alle Zonen erneut und speicherte die Platine; bereits dieser Lauf endete mit DRC Exit 0 und unveränderten CAD-Hashes. Jeder finale Prüfprozess lud den gespeicherten Stand frisch und endete regulär. **24/24 finale Prozesse endeten mit Exit 0**, ohne Timeout, Absturz oder fehlenden Bericht. Alle 70 CAD-Eingaben blieben unverändert. Der vollständige Ergebnisvergleich stimmt überein; nur Zeitstempel und Laufzeiten sind davon ausgenommen. Vorläufige Prüfserien vor der letzten Status-/BOM-Aktualisierung sind ersetzt.

Die **grafische** Kontrolle dieses endgültigen PCB-Hashes konnte nicht stattfinden: Beide Bedienversuche meldeten einen gesperrten Mac, der sich nicht automatisch entsperren ließ. Eine manuelle Entsperrung wurde angefragt; sie liegt bis zur Berichtserstellung nicht bestätigt vor. Weder eine grafische Sichtkontrolle noch das vollständige Beenden und erneute Öffnen dieses Endstands wird als bestanden ausgegeben. Frühere GUI-Nachweise mit anderem PCB-Hash gelten dafür nicht.

[verification-processes.json](reports/verification-processes.json) dokumentiert Befehle, Prozesscodes, Berichts- und Prüferhashes, Wiederholungsvergleich und diese Einschränkung. [input-hashes.json](reports/input-hashes.json) enthält sämtliche CAD-Eingabehashes. Die leeren Restnetz- und Dangling-Listen stehen in [open-connections.json](reports/open-connections.json).

## Erhaltene Identität und ausgeführte Änderungen

Elektrische Quelle bleibt die ursprüngliche `../rev-a/`, Referenzhash `13fcae0f58c9a6ac5f85eb721c24b44169a65f628baad6586bcd6002f4c17cfe`. Die zuvor eigenständig aufgebaute 280×260-Revision wurde in ihrem isolierten Worktree fortgesetzt. Keine ältere Revision wurde geändert. Die spätere ausdrückliche 280×260-Anweisung des Nutzers bestimmt die Geometrie dieses Auftrags.

Die Edge-Cuts-Mittellinien bilden exakt `(0,0)–(280,0)–(280,260)–(0,260)` mm. Erhalten sind **425 Footprints, 1377 physische Pads einschließlich Montagepads, vier Kupferlagen, 40 Testpunkte, 48 Press-fit-Bohrungen und vier Befestigungen**. Werte, DNP, Pad-/Footprint-UUIDs, Netzidentitäten, Schutzfunktionen, Stackup, Netzklassen, Gate-/Kelvin- und Net-Tie-Konzept bleiben erhalten. DNP: `C244`, `J13`, `R243`, `R244`. **69/69 Nicht-PCB-CAD-Dateien sind byteidentisch zur ursprünglichen Rev A.** Keine Regel wurde abgeschwächt oder neu ausgenommen.

Die drei letzten Netze wurden mit gezielten lokalen Leiterzügen und Lagenwechseln geschlossen. CAN erhielt einen lokalen In1-Übergang, der die LOGIC_5V_N-Rückleitung erhält. TEMP umgeht den V5V-Querschnitt mit einem lokalen B.Cu-Übergang; sein Sensorabschnitt wurde aus dem Rand des Motion-Kupfers verlegt. Ausschließlich nach nativer Prüfung der vollständigen Padverbindungen wurden überflüssige Kupferäste entfernt. Die Bauteile selbst blieben an ihren bisherigen Positionen und Orientierungen. Nach Abschluss der Verbindungen wurden 14 Referenzbeschriftungen bei unveränderter Schriftgröße versetzt und der Platinenhinweis auf `DRAFT - NOT RELEASED` geändert.

Die Herkunftsprüfung erfasst **5595 Kupferobjekte: 4379 übernommene und 1216 neue**, mit vollständigem nativem Geometrieabgleich und 973 Padankern. Es gibt keine unbelegte Kupfer-UUID. Der zusätzliche UUID-Vergleich zum Eingang bestätigt 5436 unveränderte bestehende Kupferobjekte, 159 neue Objekte ausschließlich auf den drei geschlossenen Netzen und neun entfernte unbenutzte Signaläste; kein erhaltenes Kupferobjekt wurde geometrisch verändert. Entfernte Quellobjekte und manuelle Änderungen sind einzeln in [copper-provenance.json](reports/copper-provenance.json) erfasst. **Kein neuer Autorouter-Aufruf**; die zwei historischen Aufrufe bleiben das Gesamtmaximum.

## Gefülltes Kupfer und Fertigungsentwurf

Zwei frische Auswertungen untersuchten das tatsächlich gespeicherte gefüllte Kupfer einschließlich Pads, Leiterbahnen und eigener Bohrungsabzüge in 18 definierten Bereichen. Raster: 0,01 mm; native Polygonisierung: 0,005 mm. Gegenüber dem gesicherten Eingang entsteht kein neuer Nullquerschnitt und keine relevante Verringerung; maximale numerische Rundungsabweichung unter 0,0000011 mm.

Beispiele: DRIVE-F-Stamm 8,0995 mm, LIFT-In1 6,1995 mm, CHOPPER-N-Hauptengstelle 4,7656 mm, Motion-In2 am HYS-Übergang 4,5995 mm und am QUALIFY-Übergang 7,2995 mm. SYS-F hat am Lochquerschnitt 4,0003 mm **als Summe getrennter Intervalle**, davon maximal 3,0002 mm in einem Intervall; der horizontale Stamm ist 4,4 mm breit. Diese Stichproben ersetzen keinen globalen allwinkligen Engstellen- oder thermischen Belastungsnachweis. [filled-copper-review.json](reports/filled-copper-review.json) enthält Messbereiche, Intervalle, Vergleichswerte und Grenzen.

Der [DRAFT-Fertigungsprüfsatz](manufacturing/DRAFT_NOT_RELEASED.md) enthält elf native Gerber-Lagen, den Gerber-Job, getrennte PTH-/NPTH-Bohrdateien, 327 SMD-Positionen und die unveränderte elektrische BOM. **1950 metallisierte und vier nicht metallisierte Bohrungen**, darunter sämtliche 48 Press-fit-Bohrungen mit 1,475 mm, wurden vollständig gegen die nativen Koordinaten geprüft. Die maximale Excellon-Koordinatenquantisierung beträgt 0,0005 mm. Das Gerber-Fräsprofil ist exakt 280×260 mm. Der native Job nennt 280,05×260,05 mm als grafische Strichhülle; diese Hülle ist ausdrücklich kein Fräsmaß.

Die BOM umfasst 356 Einkaufspositionen, davon 352 bestückt und vier DNP, 124 gruppierte Zeilen und 31 externe Zeilen. Eingabe-/Ausgabehashes und Herkunftsaudit bestehen. Press-fit, THT, Busbars und sonstige manuelle Arbeiten werden über BOM und aktuelle [mechanische Schnittstelle](manufacturing/busbar-pcb-interface.json) beschrieben; die SMD-Positionsdatei ist kein Auftrag für diese Arbeitsgänge.

## Noch offene Abnahme und begrenzter nächster Schritt

Die nominellen Courtyard-, Werkzeug-, Anschluss-, Press-fit- und Busbar-Abstände bestehen. Im Antennen-Keepout liegt auf keiner der vier Kupferlagen tatsächliches Kupfer. **Eine tolerierte Montage- und Produktionsqualifikation ist damit nicht nachgewiesen.** Offen bleiben insbesondere:

- Shim-/Folienstapel mit nur 0,01 mm Reserve vor Ebenheit und Verformung; reale Kontaktkraft-/Widerstands-/Thermozyklus-Coupons fehlen.
- Press-fit-Los-, Bohr-/Metallisierungs-, Kraft-Weg- und Ausdrücknachweise; genaue Kabelschuhe, Werkzeuge, Kabelradien und endgültige Träger-/Gehäusestapel fehlen.
- Reale Einschalt-, Rückspeise-, Chopper-, Temperatur-, Kalibrier-, Selektivitäts- und Schutztests sowie abschließende Firmware-/System-/Sicherheitsvalidierung fehlen.

[production-readiness.json](reports/production-readiness.json) führt die neun Produktionskategorien, B01–B14 und die konkreten mechanischen Reserven auf. Es wurden keine Messwerte erfunden oder offene Gates durch CAD-Ergebnisse geschlossen.

Dieser Durchlauf begann am 13.09.2026 um 21:21:45 UTC nach `git fetch origin` und Lesen des Pflichtkontexts. Grenze: vier Stunden, höchstens zwölf CAD-Zyklen, höchstens zwei Versuche je unveränderter Ursache, Stopp nach zwei erfolglosen Zyklen. **Sieben CAD-Zyklen, davon fünf angenommen und zwei gezielt korrigierte Ablehnungen**; kein globales Rip-up, kein zusätzlicher Router und keine Bauteilverschiebung. Nur der Lead schrieb Dateien; in diesem Durchlauf wurden keine neuen Prüferagenten eingesetzt. Sobald Zyklus 7 nativ vollständig fehlerfrei war, wurden CAD-Änderungen eingestellt. Zwei erfolglose Hilfsprozesse vor dem Speichern sind dokumentiert und wurden nicht als bestandene Prüfungen gezählt.

**Nächster eng begrenzter Schritt:** Nach manueller Entsperrung genau diesen PCB-Hash grafisch öffnen, KiCad vollständig schließen und frisch erneut öffnen. Unveränderte Eingabehashes prüfen und die native Endprüfung zweimal wiederholen. Wenn sie erneut vollständig besteht, `cad_complete=true` und `cad_complete_pending_independent_review` setzen; sämtliche Bestell-, Fertigungs-, Bestückungs-, Bestromungs- und Produktionsflags bleiben bis zur jeweiligen belegten Freigabe false. Für bekannte Routingbefunde ist keine weitere CAD-Reparatur nötig. Danach folgen die unabhängige Prüfung des exakten Entwurfssatzes und die tatsächlich erforderliche physische Qualifikation.
