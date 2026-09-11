# PMU Rev A.1 – Abschluss 280 × 220 mm

**Nicht fertiggestellt, nicht bestellbar. Der Auftrag ist wegen zwei aufeinanderfolgenden Zyklen ohne zulässigen Fortschritt beendet.**

Engineering prototype – not production qualified. `cad_complete`, `fabrication_release`, `assembly_release`, `production_release` und `orderable` sind `false`.

Branch: `codex/pmu-rev-a1-280x220-finish`. Ausgangscommit: `05e1a9ea9912712718387f560061f0f4fdd2d42e`, enthält `fc9d8e3c430a53018270b0b3bed357042d69690f`. Einzige geometrische Grundlage war die unveränderte 275×210-Platine, SHA-256 `1fed03fee50306971e381b0a862e38ba01ba24395e59430c27f37d2513381daa`.

Beginn: `2026-09-11T14:48:00+00:00`. Routing-/Reparaturstopp: `2026-09-11T15:27:35+00:00`. Dokumentabschluss: `2026-09-11T15:30:56.161294+00:00`; bis dahin **42.94 Minuten** einschließlich Vorbereitung und Dokumentation. Commit/Push folgen dieser Zeitmarke; die Abschlussantwort nennt die Gesamtzeit. **4/6 vollständige Zyklen, 0/4 Autorouter-Aufrufe.** Phase A zählt als Zyklus 1. Fünf native ERC- und fünf DRC-Aufrufe einschließlich eines ungültigen Prüfpaars in Zyklus 4; dessen Konfiguration wurde identisch wiederhergestellt und die Verifikation wiederholt. Kein nativer Timeout oder Prozessabsturz. Die 180-Minuten-Grenze wurde nicht erreicht.

## Maßgeblicher Endstand

Wiederhergestellt wurde ausschließlich der validierte **Zyklus 2**. Alle 70 geprüften Eingaben stimmen bytegenau mit dessen Prüfmanifest überein. Die vollständigen finalen ERC-/DRC-Dateien sind bytegleiche Kopien dieser gültigen Berichte. Die darin geprüfte Platine war nach Zonenfüllung gespeichert und für die Geometrieprüfung neu geladen worden; nach Wiederherstellung wurde ihre Identität erneut geprüft.

- PCB: [HomeMy_PMU_RevA_280x220.kicad_pcb](kicad/HomeMy_PMU_RevA_280x220.kicad_pcb), SHA-256 `d6c44c6fb3233af09af3c62d060077a1e0b0a8a34e0e81eeabf495157b3843bc`.
- Abmessung: **280,000 × 220,000 mm**, gemessen an den Edge.Cuts-Mittellinien. Die KiCad-Anzeigebox enthält zusätzlich 0,05 mm Strichbreite.
- ERC: **0 Befunde, regulärer Exit 0**. DRC: **5 `connection_width`-Fehler, 8 `track_dangling`- und 9 `via_dangling`-Warnungen, regulärer Exit 5**. Dazu **126 offene Verbindungen auf 28 Netzen**. Kein bestandener DRC.
- Vollständige Schaltplanparität: **0 Abweichungen**; `--schematic-parity`, `--all-track-errors` und alle Schweregrade waren aktiviert.
- Pflichtpfade: **244/247**; kritische explizite Pfade: **46/46**.
- 425 unveränderte Bauteil-/Footprint-/Padidentitäten, vier Montagebohrungen, 40 Testpunkte, 48 unveränderte Press-fit-Löcher, vier Kupferlagen und ursprüngliche Regeln/Netzklassen/Stackup. Platzierungs-, Probe-, 2D-Anschluss- und Antennen-Keepout-Prüfung bestanden.
- Die beiden U11-LOGIC_GND-Stitches bleiben im Endstand nur an F.Cu angebunden. In Zyklus 3/4 korrigierte Rückleiter und Stitches wurden zusammen mit den verworfenen Versuchen zurückgenommen.

## Erhaltener Fortschritt

Die Außenkontur wurde nach rechts um 5 mm und nach unten um 10 mm erweitert. Kein Footprint, Anschluss oder Montagepunkt wurde verschoben. Der bestehende ESP32-Keepout auf allen vier Kupferlagen reicht bis Y=224,15 mm und bleibt vollständig kupfer- und bauteilfrei bis über den neuen Rand.

40 kontrolliert festgelegte 0,20-mm-Signalabschnitte und 15 Durchkontaktierungen mit 0,60/0,30 mm stellen die drei MAIN_KELVIN_P-Pfade, den zugehörigen Testpunkt und die sechs MAIN_HGATE-/MAIN_DGATE-Verbindungen her. Alle vorhandenen Leiterbahnen und Leistungsvias bleiben im maßgeblichen Endstand erhalten. Dadurch sinkt die offene Verbindungsliste von 136 auf 126; die kritischen Pfade steigen von 37 auf 46.

Die positive Kelvin-Führung folgt der vorhandenen negativen Führung auf In2.Cu; der INA-Abzweig verläuft getrennt auf In1.Cu. Die Gate-Verteilung nutzt getrennte kontrollierte Lagen. Die Haupt-Gatewege bleiben wegen der übernommenen Platzierung relativ lang: HGATE etwa 36–86 mm, DGATE etwa 83–133 mm. Die vollständigen Leitungslängen und Lagen stehen in der Pfadliste; eine EM-/Stromteilungs- oder Hardwarequalifikation ist damit nicht verbunden.

## Zyklen und Abbruch

| Zyklus | Offen | Breitenfehler | Zonenüberschneidungen | Dangling Tracks / Vias | Pflichtpfade | Kritische Pfade | Disposition |
|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 136 | 5 | 0 | 8 / 9 | 244/247 | 37/46 | bestätigt |
| 2 | 126 | 5 | 0 | 8 / 9 | 244/247 | 46/46 | bestätigt |
| 3 | 122 | 9 | 27 | 8 / 7 | 246/247 | 46/46 | verworfen |
| 4 | 122 | 3 | 0 | 8 / 7 | 246/247 | 46/46 | verworfen |

1. Unveränderte 275-Geometrie auf feste 280×220-Kontur übernommen, gefüllt und nativ geprüft.
2. Die neun fehlenden kritischen Pfade einschließlich separater Kelvin-Abzweige ergänzt; als bester validierter Stand gesichert.
3. Zwei DC/DC-Rückleiter, DRIVE auf F.Cu, LIFT auf In1.Cu und LOGIC_5V_N auf B.Cu ergänzt; 20 BATT_N-Vias lokal bei unveränderter Anzahl und Geometrie versetzt. Elf kreuzende Signale erhielten gezielte Lagenübergänge. Zwei U11-Stitches sowie mehrere Engstellen wurden bearbeitet. Der Versuch erzeugte 27 Überschneidungsbefunde zwischen neuen gleichnamigen Flächen und verlor den vorher bestandenen LIFT-Pfad auf In2.Cu. Nicht als Beststand akzeptiert.
4. Neue gleichnamige Flächen zu geometrisch gleichen Vereinigungen zusammengeführt; V3V3-Übergang auf B.Cu an ein vorhandenes Via zurückgeführt; CHOP_DRIVE_H-Via weiter vom Engpass versetzt. Die Prüfung mit unveränderten Originalregeln zeigt 3 Breitenfehler und 122 offene Verbindungen. Der LIFT-In2-Pfad bleibt jedoch unterbrochen. Die neue MOTION_GATE_EN-Durchkontaktierung bei (175,1488; 156,0) schneidet den verbleibenden oberen Kupferdurchgang ab. Die nachträglich lesend vorgeschlagene weitere Korrektur wurde wegen der Abbruchgrenze **nicht ausgeführt**.

Ein höherer Gesamtzähler von 246/247 genügt nicht: Zyklus 3/4 gewinnen die drei vorher fehlenden Pfade, verlieren aber einen vorher bestandenen Pflichtpfad. Das verletzt ausdrücklich die Fortschrittsbedingung. Zwei solche Zyklen lösen den Stopp aus; Zyklus 2 wurde wiederhergestellt.

In Zyklus 4 verursachte das Laden einer Scratch-PCB ohne benachbarte Projektdatei eine automatische Speicherung von KiCad-Standardeinstellungen in die aktive `.kicad_pro`. Der erste ERC-/DRC-Satz dieses Zyklus ist deshalb **ungültige Abnahme-Evidenz** und bleibt gekennzeichnet erhalten. Die exakt ursprüngliche Projektdatei wurde anhand SHA-256 wiederhergestellt; nach erneutem Füllen erfolgte die gültige Verifikation `cycle-04-verified`. Es wurden keine geänderten Regeln zur Freigabe oder Fortschrittsbewertung verwendet. Die Check-Hilfe prüft seither den gebundenen Projekt-Hash vor jedem nativen Aufruf.

## Offene Pflichtpfade und Blockaden des Endstands

- `DRIVE_N`: J7.2 → NT3.1 auf **F.Cu** fehlt. Der vorhandene B.Cu-Rückleiter ersetzt diese Prüfung nicht.
- `LIFT_N`: J8.2 → NT4.1 auf **In1.Cu** fehlt; sein ursprünglicher In2-Pfad bleibt im wiederhergestellten Endstand erhalten.
- `LOGIC_5V_N`: J18.3 → J11.2 auf **B.Cu** fehlt.
- U11.1/U11.2: lokale LOGIC_GND-Vias (23,9; 22,0) und (22,9; 21,5) nur an F.Cu.
- Weitere Leistungs-/Referenzabzweige, eFuse-Zuleitungen/-Ausgänge und Rückleiter sowie Steuerleitungen bleiben offen. Via-Felder und dicht geführte Signale begrenzen die verfügbaren Leistungskorridore. Die vollständige Endliste enthält 126 Verbindungen auf den folgenden 28 Netzen.

| Netz | Offene Verbindungen |
|---|---:|
| `BATT_N` | 34 |
| `BATT_SENSED_P` | 3 |
| `BUTTON_ARM_SET_N` | 1 |
| `CAN_RX` | 1 |
| `CHOPPER_N` | 4 |
| `CHOP_DRAIN` | 2 |
| `CHOP_GND` | 5 |
| `CHOP_NTC` | 1 |
| `ESP_UART_TX` | 1 |
| `ESP_WDI` | 1 |
| `LED_DATA_3V3` | 2 |
| `LOGIC_5V_N` | 3 |
| `LOGIC_BUCK_IN_P` | 5 |
| `LOGIC_BUCK_N` | 1 |
| `LOGIC_GND` | 3 |
| `MAIN_CAPTURE_DELAYED` | 1 |
| `MAIN_COMMON` | 2 |
| `MAIN_FAULT_SET_N` | 1 |
| `MAIN_LATCH_OK` | 1 |
| `MOTION_BUS_P` | 10 |
| `MOTION_COMMON` | 2 |
| `MOTION_IMON_ADC` | 1 |
| `PC_BUCK_IN_P` | 5 |
| `PC_N` | 1 |
| `SYS_BUS_P` | 21 |
| `V3V3` | 2 |
| `V5V` | 11 |
| `WAKE_PDT` | 1 |

Die 17 Dangling-Warnungen werden **nicht akzeptiert oder ausgeblendet**. Jede steht mit UUID, Position, Netz und Schweregrad im vollständigen DRC-Bericht. Die fünf End-Breitenbefunde sind ebenfalls dort einzeln dokumentiert. Weitere nur lesend entworfene SYS-/eFuse-Routen wurden nicht angewendet und besitzen keine native Freigabe.

## Nachweise und Grenzen

- [Vollständiger nativer ERC](finish-280x220/final-erc.json): SHA-256 `9c92d1b3c2d9b97bb464a1590da761566acf38ec296ede8d698a17b8c7d95865`.
- [Vollständiger nativer DRC](finish-280x220/final-drc.json): SHA-256 `e987142dc3269835758c3569ee6fff07f22f52dae8577b7739ebd6f353dbd616`.
- [Alle 247 Pflichtpfade](finish-280x220/final-required-paths.json), [alle 46 kritischen Pfade](finish-280x220/final-critical-paths.json).
- [Alle 70 geprüften Eingabehashes](finish-280x220/final-input-sha256.json), [Geometrie, Via-Zahlen, Kupferfenster und mechanische Prüfungen](finish-280x220/final-geometry.json), [Endstatus](finish-280x220/final-state.json), [vollständiges Zyklusjournal](finish-280x220/ledger.json).
- Die frühen Geometrieausgaben lasen für die Referenzstitches versehentlich eine nicht mehr im kompakten Quellbericht enthaltene Langliste und meldeten ausdrücklich 0 geprüfte Stitches. Das war kein Anbindungsnachweis. Die separate abschließende Prüfung der beiden geforderten U11-Stitches ist jetzt im Endbericht enthalten.
- Querschnitte sind lokale Abtastungen, Busbar-Kontaktabstände sind keine fertigen Busbar-Zeichnungen. Die 2D-Prüfung ersetzt keine räumliche Gehäuse-/Werkzeug-/Kabelprüfung. Keine thermische Qualifikation, Fertigung, Bestellung, Bestückung, Bestromung oder Aktorprüfung.

Keine Gerber-, Bohr-, BOM- oder Positionsdateien für diesen unfertigen CAD-Stand erzeugt. Die ursprünglichen Varianten und ihre historischen Berichte bleiben unverändert. Parallel im lokalen Rev-A-Schaltplanverzeichnis entstandene Fremdänderungen und deren Restore-Backup gehören nicht zu diesem Auftrag; sie wurden weder zurückgesetzt noch in diesen Commit aufgenommen.
