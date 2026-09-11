# PMU Rev A.1 — 280 × 220 mm rebuild: Abschluss

**WIP — nicht bestellbar. Engineering prototype – not production qualified.**

Branch: `codex/pmu-rev-a1-280x220-rebuild`. Nach 6 vollständigen Zyklen wurde die harte Zyklusgrenze erreicht. Bester übernommener Stand: Zyklus 6. Weitere CAD-Änderungen sind gesperrt.

**293 offene Verbindungen in 112 Netzen.** Native ERC: Exit 0; DRC: Exit 5. Schaltplanparität: 0 Befunde. Die Prozesse endeten regulär, ohne Timeout.

Platzierungsprüfung: True; 247/247 ursprüngliche Leistungspfad-Paare und 46/46 kritische Pfade. Eingefrorene Regeln und Tap-Provenienz: True (362 übernommen, 130 verworfen, zusammen 492).

## Native DRC-Befunde

| Befund | Anzahl |
| --- | ---: |
| warning:silk_over_copper | 119 |
| warning:silk_overlap | 76 |
| warning:track_dangling | 23 |
| warning:via_dangling | 35 |

**Zusätzlicher offener Befund:** Derselbe Eingabesatz meldete in Zyklus 6 eine BATT_N-Verbindungsbreite von 0,2012 mm am Via (184; 106,4 mm), im abschließenden Nur-Lese-Lauf dagegen keinen Breitenfehler. Dieser Unterschied ist nicht geklärt. Der Befund bleibt offen; keine Ausnahme und kein Wiederholen bis zu einem sauberen Ergebnis. [Vergleich und exakte UUIDs](reports/final-native-consistency.json).

Die DRC-Offenliste ist vollständig und stimmt mit der nach dem Speichern neu geladenen KiCad-Konnektivität überein. Ein bestandener Teilnachweis ersetzt keine vollständige DRC- oder Fertigungsfreigabe.

## Versuchsgrenzen und Verlauf

| Zyklus | Übernommen | Offen | Leistung | Kritisch | Notiz |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | True | 1021 | 18/247 | 0/46 | Mechanical placement gate passed; pure new layout, 1021 unrouted connections. Native parity and ERC pass; silkscreen warnings remain for assembly annotation. |
| 2 | False | 708 | 219/247 | 20/46 | 219 power and 20 critical paths established, but 28 via-hole clearance findings at net-tie copper graphics require one targeted correction. Candidate retained separately; validated placement checkpoint unchanged. |
| 3 | True | 456 | 247/247 | 38/46 | 247/247 original force pairs and 38/46 critical paths; 456 opens. Native hole-clearance conflicts removed, no shorts or clearance violations. Three connection-width errors remain explicitly unresolved; ERC/parity pass. |
| 4 | True | 442 | 247/247 | 46/46 | All247 force and46 critical paths; nativeERC/parity clean, no native error findings. 442 opens and298 warnings remain. TP6 and redundant return-via necks corrected without rule changes. |
| 5 | True | 305 | 247/247 | 46/46 | 305 opens, all247 force/46 critical paths, placement and frozen-rule/tap audits pass. No shorts/clearance violations. Exactly10 localized connection-width errors (temporary maximum allowed by inherited task) require next-cycle correction; nativeERC/parity pass. |
| 6 | True | 293 | 247/247 | 46/46 | 293 opens, all247 force and46 critical paths retained. Frozen rules/taps and placement pass. NativeERC0 and parity0; width errors reduced10 to1, dangling vias38 to35, no shorts/clearance violations. Unsafe10V tree withdrawn and22 vias restored. Single digital router stopped after more than30 stagnant passes; no import. Six-cycle boundary reached: stop all CAD work. |

Autorouter-Aufrufe: 1 von maximal 4. Pro Lauf maximal 250 Durchgänge und 600 Sekunden insgesamt, Optimierer aus. Zeitfenster: 2026-09-11T16:27:00+00:00 bis spätestens 19:27 UTC; CAD-Stopp spätestens 19:07 UTC. Tatsächlicher Abschluss: 2026-09-11T18:07:44.870138+00:00.

## Bekannte Grenzen und ausgeführte Korrekturen

- Vollständig neue Platzierung aus dem ursprünglichen 360×300-mm-Rev-A-Entwurf. Kein kompaktes WIP-Kupfer als Quelle. 280 × 220 mm entsprechen 61.600 mm² und 42,96 % weniger Fläche.
- Alle 425 Footprints, 40 Testpunkte, 48 Press-fit-Bohrungen, vier Befestigungen und der vollständige ESP32-Keepout bleiben geprüft. Kabelzugang und Montage werden geometrisch in 2D geprüft; ein gemessener 3D-Kabel-/Presswerkzeugaufbau fehlt.
- Neue breite Leistungsflächen, kürzere Busbar-Kontaktabstände je dokumentierter Teilstrecke, lokale MOSFET-/Shunt-Bereiche und gezielte Kelvin-/Gate-Bäume. Die einzelnen Busbar-Abstände können auch größer geworden sein; der Geometriebericht enthält Alt/Neu je Kontaktpaar.
- Zu dichte neue BATT_N-Viafelder blockierten die SYS-Zuleitung. Ein begrenzter Innenlagenkorridor wurde freigestellt; nur neue redundante Vias wurden entfernt. Originale Tap-Elemente bleiben geometrisch eingefroren.
- Die eFuse-Ausgangsflächen erreichten die feinen Pins zunächst nicht. Reguläre lokale Fanouts schließen die Ausgangspins; J10 erhält einen separaten Innenlagenübergang ohne Auftrennen seiner äußeren Rückleitung.
- Chopper-H-Gate-Escape, Feedback-/Entladungszweige und CHOP_SENSE wurden gezielt geführt. Der längere CHOP_GATE-Abgriff zu R305 und Q42 benötigt eine dynamische Kopplungsprüfung.
- Ein erster AON-Flächenvorschlag unterbrach NT8→BC15 und wurde nur im Speicher verworfen. Der übernommene Vorschlag spart vorhandene Batterierückwege um 0,6 mm erweitert aus.
- Der neue CHOP_10V-Baum auf B.Cu unterbrach sechs BATT_N-Pfade: nach frischem Fill nur 241/247. Der gesamte neue 10-V-Teilbaum wurde zurückgenommen und seine 22 entfernten Rückleiter-Vias exakt wiederhergestellt. Die neue CHOP_REF2V5-Führung auf In2 bleibt. Eine bloße Verringerung offener Verbindungen rechtfertigt keinen unterbrochenen Hochstromrückweg.
- Neue Logikversorgungen und CAN-Bäume wurden explizit angelegt. Restliche Versorgung, analoge Schwellen, Schutzsignale, Warnungen und Verbindungen stehen in den folgenden Listen; ihre Vollständigkeit wird nicht aus den 247/46-Pfadprüfungen abgeleitet.
- Der einzige digitale Autorouterlauf wurde nach mehr als 30 aufeinanderfolgenden Durchgängen ohne weitere Verbesserung vorzeitig beendet. Kein SES wurde importiert. Die letzten lokalen Korrekturen wurden anschließend nativ geprüft; die interne Router-Offenzahl ist keine native KiCad-Offenzahl.
- Zusätzliche mechanische Prüfung: H4 hat nur 0,405 mm Courtyard-Abstand zu C245. Zwei J1-Pressfit-Lochabstände zum flachen Testpad TP1 unterschreiten konservativ 3 mm. Die Behandlung von TP1 durch das Presswerkzeug bleibt offen; keine stillschweigende Ausnahme. Siehe [mechanical-review.md](reports/mechanical-review.md).
- Die dokumentierten Querschnitte sind Messstellen im tatsächlichen gefüllten Kupfer. Sie ersetzen weder eine globale Engstellenprüfung noch Stromaufteilungs-, Erwärmungs-, Schutztransienten- oder EMV-Messungen.
- Keine Gerber, Bohr- oder Bestückungsfreigabedaten für diesen unvollständigen Stand erzeugt. Alte Rev-A-Fertigungsdaten passen nicht zu diesem Umriss. Keine Bestellung oder Bestromung erfolgt.

## Offene Netze

| Gruppe | Netz | Offene Verbindungen |
| --- | --- | ---: |
| Leistung / Versorgung | `AON_3V3` | 4 |
| Leistung / Versorgung | `AON_FEED_MID` | 1 |
| Leistung / Versorgung | `AON_LDO_IN` | 1 |
| Leistung / Versorgung | `BATT_FUSED_P` | 1 |
| Leistung / Versorgung | `BATT_SENSED_P` | 2 |
| Leistung / Versorgung | `CHOPPER_N` | 4 |
| Leistung / Versorgung | `CHOP_10V` | 18 |
| Leistung / Versorgung | `CHOP_DRAIN` | 2 |
| Leistung / Versorgung | `MAIN_COMMON` | 2 |
| Leistung / Versorgung | `MOTION_BUS_P` | 8 |
| Leistung / Versorgung | `MOTION_COMMON` | 1 |
| Leistung / Versorgung | `SYS_BUS_P` | 9 |
| Leistung / Versorgung | `V5V` | 11 |
| Masse / Rueckleiter | `BATT_N` | 3 |
| Masse / Rueckleiter | `CHASSIS` | 3 |
| Masse / Rueckleiter | `CHOP_GND` | 4 |
| Masse / Rueckleiter | `LIFT_24V_N` | 1 |
| Masse / Rueckleiter | `LOGIC_5V_N` | 1 |
| Masse / Rueckleiter | `LOGIC_GND` | 3 |
| Messung / analoge Schwellen | `CHOP_HYS_MID` | 1 |
| Messung / analoge Schwellen | `CHOP_HYS_MID2` | 1 |
| Messung / analoge Schwellen | `CHOP_NTC` | 4 |
| Messung / analoge Schwellen | `CHOP_OV_OK` | 2 |
| Messung / analoge Schwellen | `CHOP_OV_SENSE` | 3 |
| Messung / analoge Schwellen | `CHOP_REF_READY` | 2 |
| Messung / analoge Schwellen | `CHOP_REF_SENSE` | 2 |
| Messung / analoge Schwellen | `CHOP_TEMP_ADC` | 3 |
| Messung / analoge Schwellen | `LOGIC_PGTH` | 2 |
| Messung / analoge Schwellen | `MOTION_ARMED_SENSE` | 1 |
| Messung / analoge Schwellen | `MOTION_BUS_ADC` | 3 |
| Messung / analoge Schwellen | `MOTION_IMON_ADC` | 3 |
| Messung / analoge Schwellen | `MOTION_IMON_INPUT` | 4 |
| Messung / analoge Schwellen | `MOTION_IMON_RAW` | 2 |
| Messung / analoge Schwellen | `MOTION_UV_REF` | 2 |
| Messung / analoge Schwellen | `PC_PGTH` | 2 |
| Messung / analoge Schwellen | `SYS_BUS_ADC` | 3 |
| Messung / analoge Schwellen | `TEMP_MAIN_ADC` | 3 |
| Messung / analoge Schwellen | `TEMP_MOTION_ADC` | 3 |
| Steuerung / Kommunikation | `AON_RESET_N` | 4 |
| Steuerung / Kommunikation | `AON_WAKE_EN` | 7 |
| Steuerung / Kommunikation | `BUTTON_ARMED` | 1 |
| Steuerung / Kommunikation | `BUTTON_ARM_SET_N` | 1 |
| Steuerung / Kommunikation | `BUTTON_INT_N` | 2 |
| Steuerung / Kommunikation | `CAN_RX` | 2 |
| Steuerung / Kommunikation | `CAN_STB` | 2 |
| Steuerung / Kommunikation | `CAN_TX` | 3 |
| Steuerung / Kommunikation | `CHOP_ACTIVE_N` | 3 |
| Steuerung / Kommunikation | `CHOP_DISABLE` | 2 |
| Steuerung / Kommunikation | `CHOP_FAULT_N` | 4 |
| Steuerung / Kommunikation | `CHOP_QUALIFY_BASE` | 2 |
| Steuerung / Kommunikation | `CHOP_QUALIFY_N` | 3 |
| Steuerung / Kommunikation | `CHOP_REQUEST` | 2 |
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
| Steuerung / Kommunikation | `LIFT_24V_SAMPLE` | 1 |
| Steuerung / Kommunikation | `LOGIC_EFUSE_FAULT_N` | 1 |
| Steuerung / Kommunikation | `LOGIC_EFUSE_PGOOD` | 1 |
| Steuerung / Kommunikation | `MAIN_CAPTURE_DELAYED` | 1 |
| Steuerung / Kommunikation | `MAIN_CAPTURE_EN` | 1 |
| Steuerung / Kommunikation | `MAIN_FAULT_ANY` | 1 |
| Steuerung / Kommunikation | `MAIN_FAULT_ASSERTED` | 1 |
| Steuerung / Kommunikation | `MAIN_FAULT_GPIO_N` | 2 |
| Steuerung / Kommunikation | `MAIN_FAULT_N` | 4 |
| Steuerung / Kommunikation | `MAIN_FAULT_SET_N` | 1 |
| Steuerung / Kommunikation | `MAIN_LATCH_OK` | 1 |
| Steuerung / Kommunikation | `MAIN_TMR` | 3 |
| Steuerung / Kommunikation | `MOTION_ARMED` | 2 |
| Steuerung / Kommunikation | `MOTION_CLEAR_N` | 1 |
| Steuerung / Kommunikation | `MOTION_FAULTS_OK` | 1 |
| Steuerung / Kommunikation | `MOTION_FLT_N` | 5 |
| Steuerung / Kommunikation | `MOTION_GATE_EN` | 4 |
| Steuerung / Kommunikation | `MOTION_LOCAL_OK` | 1 |
| Steuerung / Kommunikation | `MOTION_PERMIT` | 1 |
| Steuerung / Kommunikation | `MOTION_PERMIT_CONNECTOR` | 1 |
| Steuerung / Kommunikation | `MOTION_PERMIT_RAW` | 3 |
| Steuerung / Kommunikation | `MOTION_TEMP_DIODE` | 3 |
| Steuerung / Kommunikation | `MOTION_TEMP_FLT_N` | 4 |
| Steuerung / Kommunikation | `MOTION_TMR` | 3 |
| Steuerung / Kommunikation | `PB_CONNECTOR` | 1 |
| Steuerung / Kommunikation | `PB_LTC_N` | 1 |
| Steuerung / Kommunikation | `PB_PRESSED` | 2 |
| Steuerung / Kommunikation | `PB_RELEASED` | 1 |
| Steuerung / Kommunikation | `PC_EFUSE_FAULT_N` | 1 |
| Steuerung / Kommunikation | `PC_EFUSE_PGOOD` | 1 |
| Steuerung / Kommunikation | `PC_SHDN` | 2 |
| Steuerung / Kommunikation | `Q4_G` | 1 |
| Steuerung / Kommunikation | `Q9_G` | 1 |
| Steuerung / Kommunikation | `STARTUP_GRANT` | 1 |
| Steuerung / Kommunikation | `SW_BROWNOUT` | 1 |
| Steuerung / Kommunikation | `SW_POWER_SEEN` | 1 |
| Steuerung / Kommunikation | `SW_RESET_ASSERTED` | 1 |
| Steuerung / Kommunikation | `SW_RESET_N` | 11 |
| Steuerung / Kommunikation | `UART_RX_CONNECTOR` | 1 |
| Steuerung / Kommunikation | `UART_TX_CONNECTOR` | 1 |
| Steuerung / Kommunikation | `WAKE_EN_OD` | 3 |
| Steuerung / Kommunikation | `WAKE_KILL` | 3 |
| Steuerung / Kommunikation | `WAKE_RAW_EN` | 6 |

Exakte Endpunkte und UUIDs: [final-open-nets.json](reports/final-open-nets.json).

## Dateien und Nachweise

- [KiCad-Projekt](kicad/HomeMy_PMU_RevA1_Rebuild_280x220.kicad_pro) und [Platine](kicad/HomeMy_PMU_RevA1_Rebuild_280x220.kicad_pcb).
- [Native Prozesscodes und alle Eingabehashes](reports/final-native.json).
- [Geometrie: Zugriff, Press-fit, Antenne, Querschnitte, Flächen, Busbars und Pfade](reports/final-geometry.json).
- Native Kupfervorschauen: [Oberseite](reports/WIP-top.svg), [Unterseite](reports/WIP-bottom.svg); [Platzierungsübersicht](reports/placement-review.png). Nur Sichtprüfung, keine Fertigungsdaten.
- [Ergänzte ursprüngliche lokale Pfadlängen](reports/source-path-length-addendum.json); historische Nullwerte werden erklärt, nicht als Messung ausgegeben.
- [Regel-/Quellen-/Tap-Prüfung](reports/final-invariants.json), [Ausführungsledger](ledger.json) und [Freigabestatus](release.json).

| Datei | SHA-256 |
| --- | --- |
| PCB | `9f329b44bf0fece059550d2f4a07b94af8fb52cfec7d26c4796aeed230193f99` |
| Ursprüngliche Rev-A-PCB | `13fcae0f58c9a6ac5f85eb721c24b44169a65f628baad6586bcd6002f4c17cfe` |
| final-erc.json | `44ccdbd4553467b32eeb4517c07f426c27d723ab8e9c1bb45e622655bbce74d9` |
| final-drc.json | `2ad038337a0f3d9f8d68579c0a04c5b56bb7f5f5a48dddd0274a52edd8656c62` |
| final-native.json | `ccc1ea5da7e219eb534bcd442ca2df38e3e244e93d285fe1f1c53e0792ae42ab` |
| final-geometry.json | `ab5d1b6ecad5fc12ac4636a0a89301380279682f0f2e60934e9a9c181c72953e` |
| final-invariants.json | `42341067220cdcc3c05b0e177587ed387b900bcdaa22643ba290a3de7683d405` |
| final-open-nets.json | `3168da3b58de1762aa603063f149ae43344e817c5dcf954c7830653bdd67a486` |

Der ursprüngliche Rev-A-Stand und die früheren Versuchszweige werden nicht überschrieben. Rückfallweg: ursprünglicher Rev-A-P1-CAD-Stand unter `../rev-a/`. Der neue Stand bleibt ausschließlich auf dem separaten Rebuild-Branch.
