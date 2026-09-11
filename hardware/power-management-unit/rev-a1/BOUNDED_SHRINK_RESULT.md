# PMU Rev A.1 – Ergebnis der begrenzten Verkleinerung

**Abbruch: Im erlaubten Suchraum wurde keine freigabefähige Verkleinerung erreicht. Kein Stand ist bestellbar.**

Engineering prototype – not production qualified. Fertigungs-, Bestückungs- und Produktionsfreigabe bleiben `false`. Rev A und der eingefrorene WIP-Branch wurden nicht verändert. Dies ist das Ergebnis dieses begrenzten Versuchs, kein allgemeiner Unmöglichkeitsnachweis für diese Abmessungen.

Arbeitsbranch: `codex/pmu-rev-a1-bounded-shrink`. Basis: `d1f97ba64da8717becdcc40eeb3f6bda842252e4`. WIP-Quelle: `014632dd9d8c65689d6f62036c11b4d191d49fb4`.

Arbeitszeit bis zum dokumentierten Abschluss: 79.61 Minuten, einschließlich Branch-/Kontextvorbereitung ab 2026-09-11T11:52:00+00:00. 3/5 Bearbeitungszyklen und 6/8 native DRC-Aufrufe. Grenzen: 150 Minuten insgesamt, ab Minute 140 nur Sicherung/Dokumentation; keine Registry-Änderung. Kein nativer ERC-/DRC-Absturz oder Timeout in diesem Auftrag.

| Größe | Fläche | Zyklen genutzt/erlaubt | Offene Verbindungen / betroffene Netze | DRC-Fehler | Dangling Tracks / Vias | ERC-Fehler | Parität | ERC-/DRC-Exit |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 250 × 200 mm | 50,000 mm² | 1/1 | 176 / 36 | ≥199 | 26 / 101 | 0 | 0 | 0 / 5 |
| 275 × 210 mm | 57,750 mm² | 1/2 | 136 / 31 | 5 | 8 / 9 | 0 | 0 | 0 / 5 |
| 300 × 220 mm | 66,000 mm² | 1/2 | 166 / 57 | 6 | 7 / 15 | 0 | 0 | 0 / 5 |

Alle finalen ERC-Prüfungen endeten regulär mit Exit 0; alle finalen DRC-Prüfungen regulär mit Exit 5 wegen Befunden. Vollständige Schaltplanparität und `--all-track-errors` waren aktiviert. Keine bestandene DRC-Prüfung und keine CAD-Freigabe.

## Ausgangsdaten, Fortschritt und genaue Nachweise

### 250 × 200 mm

Quelle: `reports/routing-round-003/HomeMy_PMU_RevA.kicad_pcb`, SHA-256 `6ed645fb3d2c6d22e68b48f5c53482f9391e65429ced608e0dd31965875e9267`.
Finale PCB-SHA-256: `3a024a0694d4cfc61e70dd1ee07d4525a2091103733d9e3769c8e3eb09bd310e`. Kompakter [Ergebnisbericht](results/HomeMy_PMU_RevA_250x200.json) einschließlich Quellhashes, Netzliste, DRC-Typen, Prüfhashes und Geometrie.

Fortschritt: 52 → 176 offene Verbindungen; DRC-Fehler mindestens 375 → mindestens 199. Fortschrittskriterium: **nicht erfüllt**. Kein weiterer Zyklus dieser Größe.
Geometrie: 425 Footprints, 40 Testpunkte; Platzierung, 2D-Anschluss-/Probezugang, Press-fit-Geometrie und vierlagiger Antennen-Keepout bestanden. 246/247 ursprüngliche lagenbezogene Leistungspaarprüfungen bestanden; zusätzlicher DRIVE-Rückleiter auf B.Cu: bestanden. 44/46 explizite kritische Leiterpfade gefunden.

Endgültige DRC-Typen: `connection_width` (error): 199, `track_dangling` (warning): 26, `via_dangling` (warning): 101. Kurzschluss-, Clearance-, Leiterbahnbreiten-, Via-/Bohrungs- und Paritätsbefunde: 0, soweit nicht ausdrücklich oben aufgeführt.

Offene Netze (Verbindungszahl): `AON_3V3` 1, `BATT_FUSED_P` 1, `BATT_N` 51, `BATT_SENSED_P` 8, `CHOP_ACTIVE_N` 1, `CHOP_GND` 1, `ESP_MOTION_REQUEST` 1, `KILL_HOLD_OR` 1, `LED_DATA_3V3` 1, `LOGIC_DVDT` 1, `LOGIC_EFUSE_FAULT_N` 1, `LOGIC_GND` 10, `MAIN_COMMON` 8, `MAIN_FAULT_GPIO_N` 1, `MAIN_FAULT_LATCHED` 1, `MAIN_FAULT_N` 1, `MOTION_BUS_ADC` 1, `MOTION_BUS_DIV` 1, `MOTION_BUS_P` 24, `MOTION_CLEAR_N` 1, `MOTION_COMMON` 8, `MOTION_FAULTS_OK` 1, `MOTION_GATE_EN` 1, `MOTION_IMON_ADC` 1, `MOTION_IMON_INPUT` 1, `MOTION_LOCAL_OK` 1, `MOTION_TEMP_FLT_N` 2, `PC_EFUSE_FAULT_N` 1, `PC_EFUSE_PGOOD` 1, `PC_ILIM` 1, `SW_RESET_N` 1, `SYS_BUS_ADC` 1, `SYS_BUS_P` 37, `SYS_DIV_MID` 1, `V3V3` 1, `WAKE_RAW_EN` 1.

Finale native Berichthashes:

- DRC: `9ebe498e8211b93746bb804e1086105daf23c8f8791242e09557235cf8eb9430` (Exit 5).
- ERC: `f0e028a32fccd0a340f5cd26f7ca464e39fd5e95bfedb47feabeb4744049dc5c` (Exit 0).

### 275 × 210 mm

Quelle: `study/250x200-straight/HomeMy_PMU_RevA.kicad_pcb`, SHA-256 `cac5bf1e37a504dadda31bff436361f5529e7eef9ce997f584c9bb9849cf5db2`.
Finale PCB-SHA-256: `1fed03fee50306971e381b0a862e38ba01ba24395e59430c27f37d2513381daa`. Kompakter [Ergebnisbericht](results/HomeMy_PMU_RevA_275x210.json) einschließlich Quellhashes, Netzliste, DRC-Typen, Prüfhashes und Geometrie.

Fortschritt: mindestens 499 → 136 offene Verbindungen; DRC-Fehler 0 → 5. Fortschrittskriterium: **nicht erfüllt**. Kein weiterer Zyklus dieser Größe.
Geometrie: 425 Footprints, 40 Testpunkte; Platzierung, 2D-Anschluss-/Probezugang, Press-fit-Geometrie und vierlagiger Antennen-Keepout bestanden. 244/247 ursprüngliche lagenbezogene Leistungspaarprüfungen bestanden; zusätzlicher DRIVE-Rückleiter auf B.Cu: bestanden. 37/46 explizite kritische Leiterpfade gefunden.

Endgültige DRC-Typen: `connection_width` (error): 5, `track_dangling` (warning): 8, `via_dangling` (warning): 9. Kurzschluss-, Clearance-, Leiterbahnbreiten-, Via-/Bohrungs- und Paritätsbefunde: 0, soweit nicht ausdrücklich oben aufgeführt.

Offene Netze (Verbindungszahl): `BATT_N` 34, `BATT_SENSED_P` 3, `BUTTON_ARM_SET_N` 1, `CAN_RX` 1, `CHOPPER_N` 4, `CHOP_DRAIN` 2, `CHOP_GND` 5, `CHOP_NTC` 1, `ESP_UART_TX` 1, `ESP_WDI` 1, `LED_DATA_3V3` 2, `LOGIC_5V_N` 3, `LOGIC_BUCK_IN_P` 5, `LOGIC_BUCK_N` 1, `LOGIC_GND` 3, `MAIN_CAPTURE_DELAYED` 1, `MAIN_COMMON` 2, `MAIN_DGATE` 3, `MAIN_FAULT_SET_N` 1, `MAIN_HGATE` 3, `MAIN_KELVIN_P` 4, `MAIN_LATCH_OK` 1, `MOTION_BUS_P` 10, `MOTION_COMMON` 2, `MOTION_IMON_ADC` 1, `PC_BUCK_IN_P` 5, `PC_N` 1, `SYS_BUS_P` 21, `V3V3` 2, `V5V` 11, `WAKE_PDT` 1.

Finale native Berichthashes:

- ERC: `fa045c772717b478f678d8506c1c942dcfa72620706f7f7ca4f039ff74c00ecc` (Exit 0).
- DRC: `9c9c04863e775befd57dbbdeca217bc5db407326bf9b1b6546bd4769b2a6d2f1` (Exit 5).

### 300 × 220 mm

Quelle: `study/250x200-straight/HomeMy_PMU_RevA.kicad_pcb`, SHA-256 `cac5bf1e37a504dadda31bff436361f5529e7eef9ce997f584c9bb9849cf5db2`.
Finale PCB-SHA-256: `330e5b6f61c7e8effd4c65c17f9873c81276f9dfbbdbe08d8d7accd35acf5f0a`. Kompakter [Ergebnisbericht](results/HomeMy_PMU_RevA_300x220.json) einschließlich Quellhashes, Netzliste, DRC-Typen, Prüfhashes und Geometrie.

Fortschritt: 809 → 166 offene Verbindungen; DRC-Fehler 0 → 6. Fortschrittskriterium: **nicht erfüllt**. Kein weiterer Zyklus dieser Größe.
Geometrie: 425 Footprints, 40 Testpunkte; Platzierung, 2D-Anschluss-/Probezugang, Press-fit-Geometrie und vierlagiger Antennen-Keepout bestanden. 246/247 ursprüngliche lagenbezogene Leistungspaarprüfungen bestanden; zusätzlicher DRIVE-Rückleiter auf B.Cu: bestanden. 37/46 explizite kritische Leiterpfade gefunden.

Endgültige DRC-Typen: `connection_width` (error): 6, `track_dangling` (warning): 7, `via_dangling` (warning): 15. Kurzschluss-, Clearance-, Leiterbahnbreiten-, Via-/Bohrungs- und Paritätsbefunde: 0, soweit nicht ausdrücklich oben aufgeführt.

Offene Netze (Verbindungszahl): `AON_3V3` 3, `BATT_N` 34, `BATT_SENSED_P` 3, `CAN_RX` 1, `CHOPPER_N` 4, `CHOP_10V` 1, `CHOP_DRAIN` 2, `CHOP_DRIVE_L` 1, `CHOP_GND` 2, `CHOP_NTC` 3, `CHOP_OV_SENSE` 1, `CHOP_REF2V5` 1, `CHOP_REF_SENSE` 1, `CHOP_TEMP_LOW` 1, `ESP_CHIP_EN` 3, `ESP_MOTION_REQUEST` 1, `ESP_UART_TX` 1, `I2C_SCL` 2, `I2C_SDA` 1, `LIFT_24V_N` 1, `LOGIC_5V_N` 1, `LOGIC_BUCK_N` 1, `LOGIC_EFUSE_FAULT_N` 1, `LOGIC_GND` 9, `LOGIC_ILIM` 1, `MAIN_COMMON` 2, `MAIN_DGATE` 3, `MAIN_FAULT_GPIO_N` 2, `MAIN_FAULT_SET_N` 1, `MAIN_HGATE` 3, `MAIN_KELVIN_P` 4, `MOTION_ARMED` 1, `MOTION_ARMED_SENSE` 1, `MOTION_BUS_DIV` 1, `MOTION_BUS_P` 10, `MOTION_CLEAR_N` 1, `MOTION_COMMON` 2, `MOTION_FLT_N` 1, `MOTION_GATE_EN` 2, `MOTION_PERMIT_RAW` 1, `MOTION_TEMP_FLT_N` 1, `MOT_DIV_MID` 1, `PB_LTC_N` 1, `PB_RAW_N` 1, `PC_BUCK_IN_P` 3, `PC_EFUSE_FAULT_N` 1, `PC_ILIM` 1, `PC_N` 1, `PC_PGTH` 1, `SW_POWER_SEEN` 1, `SW_RESET_N` 1, `SYS_BUS_P` 17, `SYS_DIV_MID` 1, `TEMP_MOTION_ADC` 1, `V3V3` 8, `V5V` 9, `WAKE_RAW_EN` 2.

Finale native Berichthashes:

- ERC: `10e629b439bad39be1d46eae5142341e9507a490b7fad11cc6ec01c072f934c0` (Exit 0).
- DRC: `6516f547650dc90e128acd6a6fc0e4ed4167186c995f66f932c2b6c1d767f3f0` (Exit 5).

## Technische Blockaden und Grenzen

- 250 mm: unzulässig übernommene dünne Leistungskupferstücke entfernt; nur original nachgewiesene Abgriffgeometrie zugelassen. Der einzelne lokale Routingpass schloss keine zusätzliche Verbindung. Das regelkonforme Entfernen dieser Stücke vergrößerte die offene Verbindungsliste; mindestens 199 Kupferengstellen bleiben.
- 275 mm: ein globaler Routingkandidat, anschließend native Prüfung. Fünf neue Engstellen sowie unterbrochene LIFT-/5-V-Rückleiter verhindern einen zweiten Zyklus. Das ursprüngliche DRIVE-F.Cu-Paar bleibt separat als fehlend erfasst; der neue B.Cu-Rückleiter ersetzt diesen historischen Lagenvergleich nicht stillschweigend.
- 300 mm: R40 und R56 einmalig versetzt; dadurch alle zwölf originalen eFuse-Eingangsfächer/-spinen übernommen. Geschützte breite DRIVE-/LIFT-Rückleiter, zwei DC/DC-Ausgangsnetze und LED-Verteilung ergänzt. Ein globaler Routingkandidat; keine Wiederholung mit geringfügig geänderten Einstellungen.
- Die geplante 4-mm-SYS-Zuleitung bei X=110 kreuzt 45 vorhandene BATT_N-Leistungsvias. Die geplanten PC-/Logic-Rückleiter treffen weitere Via-Felder; der Logic-Rückleiter überlappt zusätzlich einen originalen SYS-Abgriff um etwa 0,125 mm. Diese Vorschläge wurden verworfen; die Via-Felder wurden dafür nicht ausgedünnt.
- Beim 300-mm-Stand waren 162/492 ursprüngliche Abgriffstücke übernehmbar. 301 Stücke über mehrere unterschiedlich verschobene Bauteile besitzen keine gemeinsame starre Abbildung; 29 weitere kollidieren mit Testpunkten, Logikpads oder Arm-Sternkontakten. Kein neuer dünner Leiter wurde deshalb als Ausnahme deklariert.
- Geometrieberichte enthalten feste Kupferquerschnitte, Via-Anzahlen, 40-mm-FET-Kupferfenster und Busbar-Kontaktabstände. Diese sind keine globale Minimum-Cut-, Stromteilungs- oder Ampazitätsqualifikation. Kontaktabstände sind keine freigegebenen Busbar-Zeichnungen. Räumlicher Kabelbaum, Presswerkzeug, Gehäuse und Wärmeabfuhr bleiben physisch zu validieren.
- Keine thermische Hardwarevalidierung, Bestromung, Batterie-, Motor- oder Aktorprüfung. Keine Fertigungsdaten oder Bestellpakete erzeugt. Alle 425 Bauteil-/Footprintidentitäten, 40 Testpunkte, Schaltung, Netzklassen, Regeln, Stackup und Press-fit-Abmessungen bleiben erhalten.

Die zusätzliche Prüfung der neu gesetzten Referenzvias bestätigt beim 300-mm-Endstand 125/127 lokale Verbindungen zu mindestens zwei Kupferlagen. Die beiden INA228-GND-Stitches an U11.1/U11.2 erreichen nur F.Cu; ihre innere Referenzanbindung bleibt unbewiesen. Native Masseunterbrechungen bleiben ausdrücklich offen.

## Evidenz und Reproduzierbarkeit

KiCad 10.0.6 wurde nativ ausgeführt. Der Router lief je größerer Größe einmal, mit einem Worker, höchstens 200 internen Pässen und 480 Sekunden. Seine internen Fehler/Verbindungszahlen wurden nicht als KiCad-Ergebnis ausgegeben. Nur `latest.ses` wurde je Lauf einmal importiert, nach Prüfung der Quellhashes; Seed-Kupfer, geschützte UUIDs/Gruppen, Pads, Platzierung und Flächen mussten erhalten bleiben.

KiCad begrenzt lange Befundlisten (hier 199 je Fehlertyp beziehungsweise 499 offene Einträge). Solche Zahlen sind als Untergrenzen gekennzeichnet; beim 300-mm-Ausgangsstand lieferte der frisch geladene native Ratsnest-Zähler 809 Verbindungen. Endzahlen offener Verbindungen stammen aus frisch geladenen finalen PCBs und stimmen mit den nicht begrenzten Verbindungslisten der nativen Endberichte überein. Der erste 250-mm-ERC-Lauf meldete wegen eines falschen lokalen Symbolbibliothekspfads Warnungen; nach dessen Korrektur wurde ERC regulär mit Exit 0 wiederholt.

Die Rohberichte und Routerlaufdateien bleiben lokal unter `tools-local/bounded-shrink-native`; im Repository verbleiben je Größe eine aktive PCB-Datei und ein kompakter Ergebnisbericht. Keine DSN-/SES-Dateien, .class-Dateien, Python-Caches, .kicad_prl-Dateien oder Routerlogs werden übernommen. `bounded-ledger.json` beendet weitere automatische Bearbeitung.
