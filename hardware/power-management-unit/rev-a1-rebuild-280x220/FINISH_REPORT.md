# PMU 280 × 220 mm — Abschluss des begrenzten Fertigstellungslaufs

**WIP – NICHT BESTELLBAR. Engineering prototype – not production qualified.**

Der neue Auftrag wurde in Phase 0 angehalten. ERC und DRC schreiben vollständige Berichte, beenden sich in dieser Agent-Umgebung aber nicht regulär. Der letzte DRC-Versuch mit direkter Dateiausgabe bestätigt einen bei Ablauf der 90 Sekunden noch laufenden nativen Prozess. Das ist kein bloßes Warten auf das Ende einer Ausgabepipe. Eine bestandene native Basis fehlt.

Branch: `codex/pmu-rev-a1-280x220-rebuild`. Auftragsstand: `0fdfd91ffdc3e5fd28f4c1715114b23c0d4dbe31`. Unveränderte CAD-Ausgangsbasis: `0dd4a3b4a81ef42925506c995fb0fcbda171ecb0`.

PCB-SHA-256: `9f329b44bf0fece059550d2f4a07b94af8fb52cfec7d26c4796aeed230193f99`.

**Keine Routing-, Platzierungs- oder Kupferänderung.** Drei native Phase-0-Fill/Save-Aufrufe haben exakt dieselben PCB-Bytes hinterlassen. Projekt, Regeln, Schaltpläne und eingebundene Bibliotheken stimmen vollständig mit dem historischen finalen Eingabehashsatz überein. Es gibt keinen neuen CAD-Kandidaten; der vorhandene WIP-Checkpoint bleibt erhalten.

Laufbeginn: `2026-09-13T11:36:00+00:00`; CAD-Stopp/Abschlussledger: `2026-09-13T12:01:12.646629+00:00`. 0 von 8 Editierzyklen, 0 von 1 Autorouter-Aufrufen. DRC: drei Versuche inklusive zweier Neustarts; ERC: ein Versuch. Die Schranken werden nicht ausgeschöpft, wenn die notwendige native Prüfung nicht ausführbar ist. Weitere CAD-Änderungen sind nach diesem Abschluss gesperrt.

## Prüfergebnis

| Prüfung | Ergebnis dieses Laufs |
| --- | --- |
| CAD-Identität | Start-, Vorher-/Nachher- und finaler PCB-Hash identisch; sämtliche erfassten CAD-Eingaben unverändert |
| ERC | JSON: 0 Befunde; Prozess nach 90 s beendet, kein regulärer Exit-Code — **nicht bestanden** |
| DRC | Alle drei Prozesse nach 90 s beendet; kein regulärer Exit-Code — **nicht bestanden** |
| Schaltplanparität | Alle drei DRC-JSONs: 0 Befunde; wegen Prozessabbruch kein vollständiger Pass |
| Offen | 293 Verbindungen in 112 Netzen in allen drei DRC-JSONs |
| Dangling | 23 Leiterbahnen und 35 Vias in allen drei DRC-JSONs |
| Silkscreen | 119 silk_over_copper + 76 silk_overlap in allen drei DRC-JSONs |
| BATT_N / connection_width | Schwankende Befunde; alle bleiben offen, siehe vollständige Liste unten |
| 247 Leistungspaare / 46 kritische Pfade | Historisch 247/247 und 46/46 auf byteidentischer PCB; **keine frisch abgeschlossene Pfadprüfung** |
| Regeln, Tap-Provenienz, 280 × 220 mm, vier Lagen, 425 Footprints, 40 TPs, 48 Press-fit-Bohrungen, vier Befestigungen, Antennen-Keepout | Unveränderte CAD-Bytes erhalten den früheren Nachweis; keine neue vollständige native Prüfung |
| Mechanik | H4/C245 und J1/TP1 bleiben offen; keine neue mechanische Freigabe |
| Fertigung / Bestückung / Produktion | Alle Flags false; kein DRAFT-Prüfsatz erzeugt, da cad_complete nicht erreicht |

## Native Versuche und Hashes

Die folgenden JSONs sind Diagnoseevidenz. `exit: null` und `timed_out: true` bedeuten ausdrücklich keinen nativen Exit 0 oder Exit 5. Ein eventueller Exit 0 des Python-Protokollierers ist kein KiCad-Prüfergebnis. Befehle, Beginn, Dauer, stdout/stderr und vollständige Vorher-/Nachher-Hashes stehen in den zugehörigen `-process.json` und `-receipt.json`.

| Bericht | Fehler connection_width | Zeit, s | SHA-256 |
| --- | ---: | ---: | --- |
| [basis-refill-drc.json](reports/finish/basis-refill-drc.json) | 4 | 90.111 | `15ab2a9969340e0eb98a8fb8aacd213473c30ae80e8008ec2df0b9ff8dd84a41` |
| [basis-refill-configured-drc.json](reports/finish/basis-refill-configured-drc.json) | 1 | 90.170 | `8835f9b1f163db7cbc45694b2507578c46529fb96c18db582264be761358fe38` |
| [basis-refill-direct-drc.json](reports/finish/basis-refill-direct-drc.json) | 2 | 90.157 | `85a57c5a2d31f5aba22fba9565367a5da2be809e79a7934a2522afc63e4047d9` |
| [basis-erc.json](reports/finish/basis-erc.json) | ERC: 0 Befunde | 90.237 | `b31d6d27be4332e068d601a411da5f1afe66c979347ada76f3ef5fb66c1f90e7` |

Alle DRC-Aufrufe verwenden `--schematic-parity --all-track-errors --severity-all --exit-code-violations --refill-zones --save-board` und die korrekten benachbarten .kicad_pro/.kicad_dru-Dateien. Zwischen Versuch 1 und 2 änderte sich die Fontconfig-Umgebung; zwischen Versuch 2 und 3 ausschließlich der Ausgabetransport und der Berichtsname. Diese Diagnoseschritte ersetzen nicht den verlangten reproduzierbaren, regulär beendeten Doppelcheck.

## Fehlgeschlagene Ursachenklärung

1. **Fontconfig:** Die Standardkonfiguration konnte Benutzerverzeichnisse und Cache nicht auflösen. Eine einzige lokale Konfigurationskorrektur verwendet dieselben Windows-Schriftverzeichnisse und einen beschreibbaren Workspace-Cache. Die Fontconfig-Fehler verschwinden; der native Timeout bleibt. [Konfigurationsnachweis](reports/finish/fontconfig-environment.json). Keine CAD- oder Regeländerung.
2. **Prozessabschluss:** Ein einmaliger Wechsel von Pipes auf direkte Workspace-Logdateien und `Popen.wait()` bestätigt den noch laufenden nativen DRC-Prozess am Timeout. Nur dieser eigene Kindprozess wurde danach beendet. Kein erzwungener Erfolgs-Exit, keine Dialog-/Prüfunterdrückung.
3. **Registry:** KiCad meldet verweigerten Zugriff auf `HKCU\Software\kicad-cli`. Das ist eine Beobachtung, keine bewiesene Ursache: der separat ausgeführte Versionsaufruf beendete sich trotz derselben Meldung regulär (10.0.6, Exit 0).
4. **Native Aufräumphase:** KiCad 10.0.6 wartet nach CLI-Arbeiten auf den Threadpool und räumt Kifaces/Einstellungen/gemeinsame Ressourcen auf. Eine Blockade in diesem nach CAD-Laden erweiterten Pfad ist plausibel, wurde jedoch nicht durch eine Stackaufnahme lokalisiert. [CLI-Quellcode](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/kicad/kicad_cli.cpp#L557).

## Offene Breitenprüfung

Der bekannte F.Cu-Befund nennt BATT_N-Via `3f25db10-a5fc-4042-be5f-f7b44be8e08f` bei (184; 106,4) mm und CHOP_SENSE-Pad R304.1 `e250d50b-0ffb-40d1-abb0-3ea6750e749b` bei (182; 104,9125) mm beziehungsweise dessen Leiterbahn `73040b97-7918-47e3-bdc0-d79745ef74e4`. Gemeldet: 0,2012 mm gegenüber 1,0000 mm.

Versuch 1 nennt zusätzlich 0,9180 mm auf B.Cu an LOGIC_GND-Via `83bd7ad9-613d-4faf-81a6-f2947d5b2cc0` und BATT_N-Zone `e90d672b-8c09-4079-ab7a-916c59c7d788`, sowie 0,2071 und 0,2000 mm auf F.Cu mit PC_DVDT-Leiterbahn `94b162b0-e155-49eb-b181-223818e67e7c` und U3.8 `cab1b7a3-2f47-4878-9002-8b91b183f7ec`. [Sämtliche Befunde je Versuch mit exakten Objekt-UUIDs](reports/finish/finish-width-findings.json).

Eine Quellcodeprüfung findet bei der Engstellenzuordnung eine ungeordnete Sammlung naher Kupferobjekte ohne Netzfilter und eine Regelauswertung anhand der ersten beiden Treffer. Das ist eine mögliche Erklärung der schwankenden Zuordnung, **kein bewiesener Fehlalarm an dieser Platine**. JSON enthält nur zwei zugeordnete Objekte und deren Positionen, nicht beide tatsächlichen Halsendpunkte. Zur Klärung sind Markerposition, geprüfte Polygon-Netz-ID, Halsenden und vollständige geordnete Treffer-/Regelpaarliste nötig. [Breitenprüfer](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/pcbnew/drc/drc_test_provider_connection_width.cpp#L359), [RTree-Ergebnismenge](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/pcbnew/drc/drc_rtree.h#L428), [JSON-Serialisierung](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/common/rc_item.cpp#L175).

Keine Breitenregel abgeschwächt, kein Befund ausgenommen, kein Via entfernt, um eine Meldung zum Verschwinden zu bringen. Auch zusätzliche Meldungen bleiben unaufgelöst.

## Lokale Routing- und Mechanikpunkte

- **U2.2/BATT_N:** Pad `e7d6e7d1-12be-470d-9006-5679037f532f` bei (153,8; 76,25) mm hat keinen angeschlossenen Fanout. Eine neue Verbindung nach allgemeinen Hochstrom-Mindestmaßen passt nicht direkt an das 1,45 × 0,30-mm-Pad bei 0,5-mm-Pitch. Der ursprünglich erfasste 0,2-mm-Tap `ad7b84ed-b805-401d-a6ce-68225593656f` ist derzeit als retired dokumentiert. Seine exakte Wiederübernahme mit ursprünglicher Gruppe und transformierter Geometrie (153,8; 76,25) → (152,0751; 76,25) mm ist ein lokaler Reparaturkandidat ohne neue Regelausnahme. Capture bleibt unverändert; Disposition und Padanker wären nachzuführen. Das einzelne Segment schließt noch keinen vollständigen Rückweg. Keine Umsetzung oder native Validierung in diesem Lauf.
- **Versorgungen:** Lesende lokale Prüfungen finden kurze Kandidaten in AON_3V3, V5V, CHOP_10V und CHOP_GND. Sie sind keine geprüften Routingfortschritte. AON-LDO-/Feed-Escapes und längere Chopper-Verbindungen kollidieren mit bestehenden Rückleitern, Feedback- oder Gate-Kupfer. Der historische CHOP_10V-B.Cu-Baum, der sechs BATT_N-Leistungspaare trennte, wurde nicht wiederholt. Die 247/46-Nachweise allein belegen nicht die Versorgung jedes Controllerpins.
- **Mechanik:** H4/C245: 0,405 mm Courtyard-Abstand; Schrauben-/Scheiben-/Werkzeugkontur fehlt. J1-Pad 1/2 zu TP1: 1,96164 / 2,77096 mm gegenüber konservativ 3 mm. TP1 ist ein flaches unbestücktes Testpad, aber seine Behandlung im Presswerkzeug ist nicht freigegeben. Montage, Kabelbiegeradien, Busbar-Isolation und Pressauflage benötigen weiter den tatsächlichen mechanischen Aufbau. [Unveränderte mechanische Evidenz](reports/mechanical-review.md).

**Die geometrische Unlösbarkeit von 280 × 220 mm oder die Notwendigkeit einer größeren Platine ist durch diesen Lauf nicht nachgewiesen.** Der unmittelbare Blocker ist die nicht regulär ausführbare native Phase 0. Mehr Routingzeit allein behebt ihn nicht.

## Konkreter nächster Ingenieurschritt

Den unveränderten vollständigen Eingabesatz mit KiCad 10.0.6 in einer normalen Windows-Sitzung prüfen; stdout/stderr direkt in Dateien schreiben und den tatsächlichen Prozessstatus separat erfassen. Falls der Prozess nach der Berichtsausgabe weiterläuft, eine Thread-Wait-Chain oder Stackaufnahme des eigenen Prüfprozesses sichern. Erst daraus eine gezielte Umgebungs- oder Herstellerkorrektur ableiten. Registry-Zugriff als Ursache nicht voraussetzen.

Danach zwei frisch geladene, identische native Eingabesätze mit regulärem Prozessabschluss vergleichen und die Breitenmarker mit Halsgeometrie/Regelzuordnung auflösen. Erst mit belastbarer Basis ist ein weiterer ausdrücklich begrenzter Routingauftrag sinnvoll. U2.2 samt nachgewiesenem Originaltap ist dann ein konkreter erster lokaler Kandidat; Regeln bleiben unverändert.

## Vollständige Restnetzliste

Alle 293 offenen Verbindungen mit beiden Beschreibungen, Koordinaten und UUIDs stehen in [finish-open-nets.json](reports/finish/finish-open-nets.json), direkt aus dem letzten nativen DRC-Bericht dieses Laufs. Funktionale Gruppierung wird aus dem früheren Bericht übernommen und gegen jede Netzanzahl geprüft. BATT_N bleibt auch in der Massegruppe ein Hochstromrückleiter.

| Gruppe | Netz | Offen |
| --- | --- | ---: |
| Leistung / Versorgung | `AON_3V3` | 4 |
| Leistung / Versorgung | `AON_FEED_MID` | 1 |
| Leistung / Versorgung | `AON_LDO_IN` | 1 |
| Steuerung / Kommunikation | `AON_RESET_N` | 4 |
| Steuerung / Kommunikation | `AON_WAKE_EN` | 7 |
| Leistung / Versorgung | `BATT_FUSED_P` | 1 |
| Masse / Rueckleiter | `BATT_N` | 3 |
| Leistung / Versorgung | `BATT_SENSED_P` | 2 |
| Steuerung / Kommunikation | `BUTTON_ARMED` | 1 |
| Steuerung / Kommunikation | `BUTTON_ARM_SET_N` | 1 |
| Steuerung / Kommunikation | `BUTTON_INT_N` | 2 |
| Steuerung / Kommunikation | `CAN_RX` | 2 |
| Steuerung / Kommunikation | `CAN_STB` | 2 |
| Steuerung / Kommunikation | `CAN_TX` | 3 |
| Masse / Rueckleiter | `CHASSIS` | 3 |
| Leistung / Versorgung | `CHOPPER_N` | 4 |
| Leistung / Versorgung | `CHOP_10V` | 18 |
| Steuerung / Kommunikation | `CHOP_ACTIVE_N` | 3 |
| Steuerung / Kommunikation | `CHOP_DISABLE` | 2 |
| Leistung / Versorgung | `CHOP_DRAIN` | 2 |
| Steuerung / Kommunikation | `CHOP_FAULT_N` | 4 |
| Masse / Rueckleiter | `CHOP_GND` | 4 |
| Messung / analoge Schwellen | `CHOP_HYS_MID` | 1 |
| Messung / analoge Schwellen | `CHOP_HYS_MID2` | 1 |
| Messung / analoge Schwellen | `CHOP_NTC` | 4 |
| Messung / analoge Schwellen | `CHOP_OV_OK` | 2 |
| Messung / analoge Schwellen | `CHOP_OV_SENSE` | 3 |
| Steuerung / Kommunikation | `CHOP_QUALIFY_BASE` | 2 |
| Steuerung / Kommunikation | `CHOP_QUALIFY_N` | 3 |
| Messung / analoge Schwellen | `CHOP_REF_READY` | 2 |
| Messung / analoge Schwellen | `CHOP_REF_SENSE` | 2 |
| Steuerung / Kommunikation | `CHOP_REQUEST` | 2 |
| Messung / analoge Schwellen | `CHOP_TEMP_ADC` | 3 |
| Steuerung / Kommunikation | `CHOP_TEMP_HIGH` | 2 |
| Steuerung / Kommunikation | `CHOP_THERMAL_OK` | 5 |
| Steuerung / Kommunikation | `ESP_BOOT_N` | 2 |
| Steuerung / Kommunikation | `ESP_CHIP_EN` | 4 |
| Steuerung / Kommunikation | `ESP_MAIN_HOLD` | 3 |
| Steuerung / Kommunikation | `ESP_MOTION_REQUEST` | 2 |
| Steuerung / Kommunikation | `ESP_MOTION_RESET` | 3 |
| Steuerung / Kommunikation | `ESP_UART_RX` | 2 |
| Steuerung / Kommunikation | `ESP_UART_TX` | 2 |
| Steuerung / Kommunikation | `ESP_WDI` | 2 |
| Steuerung / Kommunikation | `ESP_WDO_N` | 2 |
| Steuerung / Kommunikation | `I2C_SCL` | 3 |
| Steuerung / Kommunikation | `I2C_SDA` | 3 |
| Steuerung / Kommunikation | `INA_ALERT_N` | 2 |
| Steuerung / Kommunikation | `LED_DATA_3V3` | 2 |
| Steuerung / Kommunikation | `LED_DATA_OUT` | 2 |
| Steuerung / Kommunikation | `LED_OE_N` | 2 |
| Masse / Rueckleiter | `LIFT_24V_N` | 1 |
| Steuerung / Kommunikation | `LIFT_24V_SAMPLE` | 1 |
| Masse / Rueckleiter | `LOGIC_5V_N` | 1 |
| Steuerung / Kommunikation | `LOGIC_EFUSE_FAULT_N` | 1 |
| Steuerung / Kommunikation | `LOGIC_EFUSE_PGOOD` | 1 |
| Masse / Rueckleiter | `LOGIC_GND` | 3 |
| Messung / analoge Schwellen | `LOGIC_PGTH` | 2 |
| Steuerung / Kommunikation | `MAIN_CAPTURE_DELAYED` | 1 |
| Steuerung / Kommunikation | `MAIN_CAPTURE_EN` | 1 |
| Leistung / Versorgung | `MAIN_COMMON` | 2 |
| Steuerung / Kommunikation | `MAIN_FAULT_ANY` | 1 |
| Steuerung / Kommunikation | `MAIN_FAULT_ASSERTED` | 1 |
| Steuerung / Kommunikation | `MAIN_FAULT_GPIO_N` | 2 |
| Steuerung / Kommunikation | `MAIN_FAULT_N` | 4 |
| Steuerung / Kommunikation | `MAIN_FAULT_SET_N` | 1 |
| Steuerung / Kommunikation | `MAIN_LATCH_OK` | 1 |
| Steuerung / Kommunikation | `MAIN_TMR` | 3 |
| Steuerung / Kommunikation | `MOTION_ARMED` | 2 |
| Messung / analoge Schwellen | `MOTION_ARMED_SENSE` | 1 |
| Messung / analoge Schwellen | `MOTION_BUS_ADC` | 3 |
| Leistung / Versorgung | `MOTION_BUS_P` | 8 |
| Steuerung / Kommunikation | `MOTION_CLEAR_N` | 1 |
| Leistung / Versorgung | `MOTION_COMMON` | 1 |
| Steuerung / Kommunikation | `MOTION_FAULTS_OK` | 1 |
| Steuerung / Kommunikation | `MOTION_FLT_N` | 5 |
| Steuerung / Kommunikation | `MOTION_GATE_EN` | 4 |
| Messung / analoge Schwellen | `MOTION_IMON_ADC` | 3 |
| Messung / analoge Schwellen | `MOTION_IMON_INPUT` | 4 |
| Messung / analoge Schwellen | `MOTION_IMON_RAW` | 2 |
| Steuerung / Kommunikation | `MOTION_LOCAL_OK` | 1 |
| Steuerung / Kommunikation | `MOTION_PERMIT` | 1 |
| Steuerung / Kommunikation | `MOTION_PERMIT_CONNECTOR` | 1 |
| Steuerung / Kommunikation | `MOTION_PERMIT_RAW` | 3 |
| Steuerung / Kommunikation | `MOTION_TEMP_DIODE` | 3 |
| Steuerung / Kommunikation | `MOTION_TEMP_FLT_N` | 4 |
| Steuerung / Kommunikation | `MOTION_TMR` | 3 |
| Messung / analoge Schwellen | `MOTION_UV_REF` | 2 |
| Steuerung / Kommunikation | `PB_CONNECTOR` | 1 |
| Steuerung / Kommunikation | `PB_LTC_N` | 1 |
| Steuerung / Kommunikation | `PB_PRESSED` | 2 |
| Steuerung / Kommunikation | `PB_RELEASED` | 1 |
| Steuerung / Kommunikation | `PC_EFUSE_FAULT_N` | 1 |
| Steuerung / Kommunikation | `PC_EFUSE_PGOOD` | 1 |
| Messung / analoge Schwellen | `PC_PGTH` | 2 |
| Steuerung / Kommunikation | `PC_SHDN` | 2 |
| Steuerung / Kommunikation | `Q4_G` | 1 |
| Steuerung / Kommunikation | `Q9_G` | 1 |
| Steuerung / Kommunikation | `STARTUP_GRANT` | 1 |
| Steuerung / Kommunikation | `SW_BROWNOUT` | 1 |
| Steuerung / Kommunikation | `SW_POWER_SEEN` | 1 |
| Steuerung / Kommunikation | `SW_RESET_ASSERTED` | 1 |
| Steuerung / Kommunikation | `SW_RESET_N` | 11 |
| Messung / analoge Schwellen | `SYS_BUS_ADC` | 3 |
| Leistung / Versorgung | `SYS_BUS_P` | 9 |
| Messung / analoge Schwellen | `TEMP_MAIN_ADC` | 3 |
| Messung / analoge Schwellen | `TEMP_MOTION_ADC` | 3 |
| Steuerung / Kommunikation | `UART_RX_CONNECTOR` | 1 |
| Steuerung / Kommunikation | `UART_TX_CONNECTOR` | 1 |
| Leistung / Versorgung | `V5V` | 11 |
| Steuerung / Kommunikation | `WAKE_EN_OD` | 3 |
| Steuerung / Kommunikation | `WAKE_KILL` | 3 |
| Steuerung / Kommunikation | `WAKE_RAW_EN` | 6 |

## Nachweise und Rückfallweg

- [Kompakter Prüf-/Hashvergleich](reports/finish/finish-native-summary.json).
- [Abschlussledger](finish-ledger.json) und [Freigabestatus](release.json).
- [Historischer Rebuild-Abschluss](FINAL_REPORT.md) bleibt unverändert und ist keine frische Prüfung.
- `FINISH_SHA256SUMS` ist das neue vollständige Manifest dieses Verzeichnisses. Das ältere `SHA256SUMS` bleibt historische Evidenz des früheren Rebuild-Commits.
- Ursprüngliches Rev-A-CAD, RevA-P1-Paket und frühere Varianten bleiben unverändert. Dieser Lauf bleibt auf dem bestehenden separaten Rebuild-Branch. Keine Bestellung, Bestückung oder Bestromung.
