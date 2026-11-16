# Befunde der Gegenprüfung PMU Rev A2 (280 × 260 mm)

Geprüfter Stand: Branch `codex/pmu-rev-a2-280x260-layout`, Commit `d37c7f70536507b69d8bcac9a166c7d541a8984e`, PCB-SHA-256 `2742638d03b884b8b6ac7bf7064ef98b2bd6c5a95377b7617b72999eb2e83bc2`. Datum: 2026-11-16.

Alle Befunde sind **offen**. Keiner wurde in CAD oder Schaltung umgesetzt; die Leiterplatte ist unverändert. Koordinaten in mm, Ursprung linke obere Platinenecke, x nach rechts, y nach unten. Rechenwege stehen in [BERECHNUNGEN.md](BERECHNUNGEN.md), Rohdaten in `daten/`, die maschinenlesbare Liste in [findings.json](findings.json).

Spalte „Geprüft durch": **selbst** = von der Hauptprüfung mit eigenen Skripten/Rechnungen belegt; **Teilprüfung + Stichprobe** = von einer der drei Teilprüfungen gefunden und in der Kernaussage nachgeprüft; **Teilprüfung** = nur dort belegt (siehe `teilberichte/`).

Einstufung: **hoch** = vor einer Leiterplattenbestellung beheben; **mittel** = vor Bestellung beheben oder bewusst entscheiden; **niedrig** = bei der nächsten Layoutrunde mitnehmen.

## A. Layout und Schaltung

### GP-01 Schutzdioden sind nur über 0,2-mm-Leiterbahnen angebunden — hoch — selbst
- D1 (PTVS1-043C-H, Eingang, 1 kA 8/20 µs) bei (35, 70). Pad 1 (`BATT_FUSED_P`): 0,2 mm auf F.Cu (2,8 + 1,3 + 0,9 mm), Via 0,6/0,3 bei (32,9/74,8), 0,2 mm auf In1.Cu (13,6 + 0,7 mm, 35 µm Kupfer), Via 0,6/0,3 bei (32,4/60,7), erst dann die Fläche. Pad 2 (`BATT_N`): 0,2 mm × 2,8 mm und ein Via.
- D2 (Systembus): Pad 1 liegt in der `SYS_BUS_P`-Fläche, Pad 2 (`BATT_N`) hängt an 0,2 mm × 2,8 mm und einem Via. D60/D61 (SMCJ43A): `CHOPPER_N`-Pads über 0,2-mm-Stiche (0,5–2,9 mm) und Vias.
- Serienwiderstand D1 rund 45 mΩ. Schmelzgrenze der Innenlagenbahn rund 4–5 A²s. Eine Kurzschlussabschaltung des Hauptschalters kommutiert geschätzt 300–500 A für 45–70 µs in D1 (1,5–6 A²s). Bei 300 A kommen rund 14 V zur Klemmspannung hinzu; damit liegt der Knoten an der 70-V-Grenze des LM74930. Fällt D1 aus, gehen Q1–Q3 oberhalb ihres Avalanche-Nennstroms (117 A) in den Durchbruch.
- DRC ist sauber, weil diese Bahnen Mitglieder der Ausnahmegruppe `PWR_TAP_CONTROL` sind (435 Elemente). Alle anderen Mitglieder sind tatsächlich Signalabgriffe (`daten/power_continuity.json`).
- Die +42-V-Flächen enden an der Gehäusekante: `BATT_SENSED_P` bei D1 ab x = 38,01 (Gehäusekante 38,0), `SYS_BUS_P` bei D2 bis x = 105,03 (Kante 105,0). Laut Herstellerzeichnung liegen dort freiliegende Stege des großen Anschlusses (Masse). Trennung dann nur Lötstopplack. (Geometrie selbst geprüft, Steghöhe nur aus der Zeichnung.)
- Abhilfe: beide Pads von D1/D2/D60/D61 breit und kurz in die Flächen legen, mehrere Vias 0,8/0,4, Fremdkupfer mindestens 0,5 mm vom Gehäuseumriss fernhalten, Bahnen aus der Ausnahmegruppe nehmen.
- Belege: `daten/pcb_checks.json` (`pad_connection`, `tvs_d1_net_BATT_FUSED_P`, `tap_groups`, `tvs_body_edge`), `daten/bilder/F_Cu_D1_eingangsschutzdiode.png`.

### GP-02 Logik- und Leistungsmasse sind nur an einer Stelle verbunden — hoch — selbst
- `LOGIC_GND` (152 Anschlüsse) und `BATT_N` treffen sich ausschließlich an NT9 bei (108, 149): Netzbrücke `NetTie_Logic_2`, zwei Pads 1 × 1 mm, Kupferbrücke 2 × 1 mm. Logikseitig 1,29 mm Leiterbahn 0,2 mm und ein Via 0,6/0,3 bei (107,8/150,6). (`daten/netzliste/massebruecken.txt`, `daten/pcb_checks.json` → `ground_tie_NT9`.)
- Über diese Stelle fließt der gesamte Rückstrom der 3,3-V/5-V-Logik (ESP32, CAN, Latches): `LOGIC_GND` → NT9 → `BATT_N` → NT8 → `LOGIC_5V_N` → J11.2.
- Die Freigabe-Eingänge sind auf `LOGIC_GND` bezogen: `AON_WAKE_EN` (LM74930 EN/MODE) mit R216 10 kΩ nach `LOGIC_GND` und R29 1 MΩ nach `BATT_N`; `MOTION_GATE_EN` (TPS48110 INP) mit R237 10 kΩ nach `LOGIC_GND` und R39 100 kΩ nach `BATT_N`.
- Öffnet NT9 oder das Via, drückt die Always-on-Speisung (42 V über 10 kΩ) und die 5-V-Versorgung `LOGIC_GND` auf geschätzt +3,5 bis +5,6 V gegenüber `BATT_N`. EN (Schwelle max. 1,05 V) und INP (max. 2 V) lesen dann „ein": Hauptschalter bleibt oder geht an, Motion-Gate schaltet durch, die Hardware-Abschaltung per langem Tastendruck wirkt nicht.
- Auslöser können sein: Fertigungs-/Alterungsfehler des einen Vias, oder ein Fehlerstrom über die Logikmasse (Kurzschluss eines 42-V-Netzes auf `LOGIC_GND`, siehe GP-03 und GP-08; Armrückstrom über eine extern aufgelegte CAN-Masse).
- Abhilfe: Verbindung breit und mehrfach ausführen (≥ 2 mm, ≥ 4 Vias, zweite Brücke bei U1/U2); antiparallele Schottky-Dioden `LOGIC_GND`↔`BATT_N` an zwei Stellen; Pull-downs an EN/INP niederohmig gegen `BATT_N`. NT10 (`CHOP_GND`↔`CHOPPER_N`, über die der Gate-Rückstrom des UCC27511 fließt) gleich mit verbreitern.

### GP-03 Kupferschienen: Fremdnetz-Vias darunter, überwiegend wirkungslos — hoch — Teilprüfung + Stichprobe
- Vias fremder Netze unter den Schienen (Umrisse aus `rev-a2-layout-280x260/manufacturing/busbar-pcb-interface.json`, selbst nachgerechnet, `daten/pcb_checks.json` → `busbar_foreign_vias`):
  - BB1 (`BATT_SENSED_P`, ungeschaltetes Batterieplus): `V3V3` (44,19/60,09); `LOGIC_GND` (44,19/75,73), (42,94/80,23); `MAIN_KELVIN_N` (42,0/75,9).
  - BB2 (`MAIN_COMMON`): `LOGIC_GND` (71,71/74,66), (73,02/60,24), (71,96/54,36); `TEMP_MAIN_ADC` (74,71/60,34).
  - BB5 (`MOTION_COMMON`): `LOGIC_GND` ×2, `BATT_N` (174,0/77,93), `MOTION_TEMP_DIODE`, `TEMP_MOTION_ADC` ×2.
  - BB6 (`MOTION_BUS_P`): `LOGIC_GND` (199,91/92,25), (196,91/83,66). BB3, BB4: keine.
  - BB7 (`BATT_N`): `ARM_R_N` ×4, `MAIN_FAULT_N`, `AON_WAKE_EN` ×2, `MOTION_IMON_INPUT` ×3.
- Vias sind beidseitig abgedeckt, aber nicht verschlossen. Isolation nur Lötstopplack plus vier lose Kapton-Lagen unter 200–400 N Klemmkraft. Ein Folienfehler an BB1 ist ein Kurzschluss vor jeder elektronischen Schutzstufe (nur Sicherung/BMS); über `LOGIC_GND` trifft er zusätzlich GP-02.
- Die projekteigene Mechanikprüfung testet nur gebohrte Footprint-Pads gegen die Schienenumrisse, keine Vias, Bahnen oder Flächen.
- Flächenstrom-Rechnung der Teilprüfung bei 50 A (±20 %): Leiterverluste 6,3 W ohne und 4,5 W mit allen Schienen. BB7 spart 1,7 W, BB6 0,12 W, BB1–BB5 zusammen 0,014 W (sie verlaufen quer zur Stromrichtung, 1–4 A je Kontakt). Eigene Überschlagsrechnung stimmt damit überein.
- Die dokumentierte Reserve Kontaktscheibe/Folie von 0,01 mm wird rechnerisch ≤ 0, sobald Lack ≥ 10 µm unter der Folie mitgezählt wird (Lackdicke angenommen).
- Die aufgeschraubten Sternbrücken NB1–NB8 sind redundant: Die NT-Pads (10 × 10 mm) stoßen auf allen vier Lagen aneinander, F.Cu hat zusätzlich eine 20 × 10 mm Brücke. Die Aussage in `MECHANICAL_BUILD.md`, erst die NB-Brücke verbinde die Pads, stimmt nicht.
- Empfehlung: BB1–BB6 und NB1–NB8 streichen (entfernt über 20 Schraubverbindungen); den `BATT_N`-Korridor im Layout öffnen (GP-11), dann entfällt auch BB7. Bleibt eine Schiene: kein Fremdkupfer darunter (Sperrfläche), Kontaktscheibe ≥ 0,1 mm überstehend, Folie auf die Schiene geklebt.

### GP-04 Motion-Gate ohne definierte Einschaltstrombegrenzung — hoch — selbst
- Gate-Beschaltung: PU → R34 180 kΩ → Gate, PD direkt, je FET 10 Ω und 10 MΩ. Es gibt keinen Gate-Kondensator gegen Masse (TI TPS4811-Q1 Abschnitt 8.3.2.1: R1, C1, R2) und keinen Bestückplatz dafür. TI rät bei parallelen FETs von reiner Gate-Flankensteuerung ab (8.3.2.2).
- Q7–Q10 sind PSMN1R0-100ASF („NextPower", Schalt-FET). SOA bei 25 °C und 42 V, aus Datenblatt Fig. 3 abgelesen: 100 µs etwa 260 A, 1 ms etwa 22 A, 10 ms etwa 8 A, 100 ms etwa 3,4 A. Die Variante PSMN1R0-100ASE (ASFET für Hot-Swap, gleicher Footprint, 1,04 mΩ) liegt bei etwa 80 A / 40 A / 12 A.
- Simulation (`werkzeuge/inrush_sim.py`, `daten/inrush_sim.json`), konservativ mit einem FET: 940 µF → 21 A Spitze (15–33 A über die Crss-Streuung), Rampe 3–9 ms, 0,83 J, etwa halbe SOA-Grenze. 2000 µF → an der Grenze. 4000 µF → 1,7-fach darüber, 61 A. 8000 µF → 3-fach, 98 A, nahe der Kurzschlussschwelle (min. 86 A).
- Die Eingangskapazität der zwölf Gelenkantriebe, der zwei ESS23 und des 24-V-Wandlers steht in keiner Unterlage.
- Abhilfe: Q7/Q8 (besser Q7–Q10) als ASE bestücken; Bestückplatz C1 + R2 von `MOTION_GATE_DRIVE` nach `BATT_N` (100 V), z. B. 47 nF für etwa 50 ms Rampe; maximale externe Kapazität messen und festschreiben.

### GP-05 Überspannungsschwelle der eFuses überlappt die Motion-Abschaltung — hoch — selbst
- U3/U4 (TPS26631): R43/R53 374 kΩ zu 10 kΩ ergibt 46,08 V Abschaltung (45,0–47,2 V) und 43,08 V Wiedereinschalten (41,9–44,2 V).
- Motion-Latch (Chopper-Komparator U32): 46,00 V (45,66–46,34 V). Software-Stopp: 45,0 V.
- Bei eingeschaltetem Motion-Gate steigt `SYS_BUS_P` mit `MOTION_BUS_P` (Gate leitet in beide Richtungen, der LM74930 sperrt nur zur Batterie).
- Bleibt der Bus im Band 45,1–46,3 V (z. B. während des kontrollierten Stopps), trennen die eFuses PC- und 5-V-Wandler. Dauert das länger als deren Stützzeit, löst der Brownout-Latch aus und schaltet alles hart ab. Das schnelle Wiedereinschalten (58–225 µs) gilt nur, solange der eFuse-Ausgang über 22,6 V bleibt.
- Abhilfe: R43 und R53 auf 392–407 kΩ (48,2–50,0 V nominal), unter der 55-V-Angabe des PC-Wandlers.

### GP-06 Hardware-Fehlerleitungen liegen direkt am ESP32 — mittel bis hoch — selbst
- `MOTION_FLT_N` (IO36), `MOTION_TEMP_FLT_N` (IO37), `CHOP_FAULT_N` (IO38) ohne Serienwiderstand; `MAIN_FAULT_N` über U60 an IO35.
- Ein versehentlich als Ausgang „high" gesetzter Pin überstimmt den Optokoppler (`CHOP_FAULT_N`) sicher, die Open-Drain-Ausgänge des TPS48110 (54–90 Ω) weitgehend, den LM74930-FLT grenzwertig (etwa 1,1 V am Schmitt-Eingang U53).
- Abhilfe: je 10–47 kΩ in Serie zum GPIO (wie bereits R240 bei `MOTION_ARMED_SENSE`).

### GP-07 5-V-Eingang ohne Überspannungsschutz — mittel bis hoch — selbst
- An J11/`V5V` gibt es weder TVS noch Abschaltung (auf der Platine sind nur D1, D2, D40, D60–D66 Dioden). Legiert der externe 5-V-Wandler durch, liegen bis 42 V an U12, U13, U14, LED-Streifen und über den Regler an ESP32 und Latches; begrenzt nur durch U4 (2 A, 4 A für 25 ms, dann Abschaltung).
- Abhilfe: Überspannungsschalter oder Crowbar am 5-V-Eingang.

### GP-08 Abstände zwischen 42-V-Netzen und Logik nicht geregelt — mittel — selbst
- Alle Netzklassen haben 0,2 mm Abstand; es gibt keine spannungsabhängige Regel.
- Testregel „42-V-Netze zu allen anderen ≥ 0,6 mm" (`werkzeuge/drc_experiments.py hv`, `daten/hv_clearance.json`): 499 Stellen, Minimum 0,20 mm. Der Großteil sind Vias/Bahnen gegen Flächen auf Innenlagen bei 0,30 mm (nach IPC-2221B für Innenlagen zulässig).
- 27 Stellen auf Außenlagen mit Pad-Beteiligung liegen bei 0,20–0,39 mm (im Chatbericht mit 28 genannt; die archivierte Auswertung zählt 27). IPC-2221B verlangt für unbeschichtete Bauteilanschlüsse bei 31–50 V 0,4 mm, mit Schutzlack 0,13 mm. Beispiele: `SYS_BUS_P`-Pad R45 ↔ `PC_SHDN` 0,203 mm bei (23,0/185,4); `INA_VBUS` ↔ `V3V3`-Pad C206 0,205 mm bei (34,6/83,1); `LOGIC_BUCK_IN_P`-Pad C27 ↔ `LOGIC_EFUSE_PGOOD` 0,216 mm.
- Die Spannungsteiler sind hochohmig (523 kΩ, 732 kΩ, 226 kΩ, 374 kΩ, 1 MΩ, 2,69 MΩ). Ein Leckpfad von 10 MΩ über R27 verschiebt die Überspannungsschwelle um etwa −7 %.
- Abhilfe: Abstandsregel für die 42-V-Netze (≥ 0,5 mm an Pads) und Schutzlack für die bestückte Platine festlegen.

### GP-09 Keine Diode gegen negative Spannungsspitzen — mittel — selbst
- `SYS_BUS_P` hat nur D2 (bidirektional, klemmt negativ erst bei −48 V) und 3 × 100 nF. LM74930 Pin C verträgt −1 V, TPS26631 OUT −0,3 V. TI empfiehlt bei LM74930 (8.4.1), TPS4811 (9.5) und TPS2663 (9.5.1) eine Schottky-Diode vom Ausgang nach Masse.
- Die eFuse-Ausgänge `PC_BUCK_IN_P` und `LOGIC_BUCK_IN_P` (Kabel zu externen Wandlern) haben nur 1 µF.
- Abhilfe: je eine Schottky-Diode (≥ 60 V) an `SYS_BUS_P`, J9 und J10.

### GP-10 Batterieanschluss nicht gegen Verpolung und Werkzeugkurzschluss gesichert — mittel — selbst / Teilprüfung
- J1 (+) bei (20, 50) und J2 (−) bei (20, 112) sind identische M5-Einpressklemmen ohne Kodierung. Die Unterlagen sprechen von „keyed positive-polarity wiring"; mit Ringkabelschuhen ist das nicht gegeben.
- Die Schaltung ist ausdrücklich nicht verpolfest: LM74930 VS, CS+, CS−, ISCP (−1 V) und der INA228 (−0,3 V, nur 10 Ω davor) liegen direkt an der Batterieseite. Bei Verpolung werden U1 und U11 zerstört, die 10-Ω-Widerstände führen rund 4 A; die 60-A-Sicherung löst nicht aus.
- Teilprüfung: In A2 fehlen die Ausrichtungstexte der Klemmen; die Schraubachse von J2 zeigt auf den blanken J1-Block. 2,2 Nm ohne Gegenhalter belasten eine Stiftreihe mit etwa 289 N gegen 4 × 30 N garantierte Haltekraft.
- Abhilfe: unterschiedliche Bolzengrößen oder kodierter Batteriestecker, J2 um 180° drehen, Ausrichtung aufdrucken, Isolierkappen, Gegenhalter festlegen.

### GP-11 Rückleiter in A2 schmaler als in Rev A, in keinem Bericht erwähnt — mittel — Teilprüfung + Stichprobe
- `ARM_R_N`: Streifen x 250–256, y 88–120, also 6,0 mm auf F.Cu und B.Cu. `ARM_L_N`: 12 mm. Rev A: 12,5 mm.
- `BATT_N` bei x = 207–219 (Kreuzung mit dem `ARM_L_N`-Korridor): F.Cu 0 mm, B.Cu 2,05 mm bei x = 207 (durch eine `MOTION_GATE_EN`-Bahn eingeschnürt) bzw. 10,5 mm bei x = 210–215, In2.Cu 33–43 mm (35 µm). Beide Arm-Sternpunkte (NT1.2 bei x = 223, NT2.2 bei x = 253) liegen rechts davon. Der Armrückstrom hängt dort an Innenlage und BB7.
- `BATT_N`-Leistungsvias: 723 in Rev A, 130 in A2 (Teilprüfung).
- J1 → RSH1 läuft praktisch nur auf F.Cu; im Umkreis von 3 mm um Shunt-Kraftpads und FET-Fahnen liegt kein Via; In1/In2 sind an J1, J3–J6 nicht angeschlossen (Teilprüfung).
- Rechnerisch tragfähig (etwa 7 K je Lage, rund 15 K gesamt bei 25 A im 6-mm-Streifen), aber unsymmetrisch und undokumentiert.
- Abhilfe: `ARM_R_N` auf 12 mm, `BATT_N` auf F.Cu/B.Cu bei x 206–220 durchgängig führen, Vias an Shunts und FET-Fahnen ergänzen.
- Belege: `daten/pcb_checks.json` → `cross_sections`.

### GP-12 Padabstände und Bestückmerkmale für 70-µm-Kupfer — mittel — Teilprüfung + Stichprobe
- Positiv: Alle geprüften Pin-Zuordnungen, Pin-1-Lagen und Polaritäten stimmen (Q1–Q10, RSH1/2, J1–J6, U1–U4, D1/D2, Q40, D63, U10, U11, U12, U51, Optokoppler, Elkos, TVS).
- 0,15 mm Padabstand an U11 (Pads 1,5 × 0,35 mm; Pad 8 `INA_VBUS` neben Pad 7 `LOGIC_GND`), U30, U16, U18, U19, U23, U24, U27, U55. Die KiCad-Bibliothekspads sind 0,05 mm breiter als die Hersteller-Landmuster; mit diesen ergäben sich 0,20 mm. Üblich sind bei 70 µm mindestens 0,20 mm; eine Fertigerzusage liegt nicht vor. `.kicad_dru` erlaubt 0,15 mm für alle U-Pads.
- U3/U4: Abstand Pad zu Massefläche 0,20 mm bei 42 V (TI 0,27 mm).
- Keine Pin-1-Marke auf irgendeiner Lage bei D1, D2, U2, U51; nur Fab-Marken ohne Bestückungsdruck bei Q1–Q10, U1, RSH1/2, J1–J6. Ein um 180° gedrehtes D1/D2 ist ein harter Kurzschluss.
- CCPAK1212: Paste 100 % auf der Grundfläche statt sechs Öffnungen (etwa 75 %) nach Nexperia; U1-Massefläche ebenfalls 100 % (TI 77 %); offene Vias in den Masseflächen von U3/U4.
- U51: eine `V3V3`-Bahn läuft unter den freiliegenden Masse-Stegen bei (211,2–213,9/240,43).
- D63: Bohrung 1,1 mm bei maximal 1,09 mm Anschlussdiagonale.
- U12 (3,3-V-Regler): Ausgangsfahne nur über 0,2-mm-Bahnen angeschlossen, keine Kühlfläche; `WAKE_IO.md` setzt eine voraus.
- U10: IO35–IO37 sind nur bei der Variante N8 frei; Module mit Oktal-PSRAM dürfen nicht ersetzt werden.

### GP-13 Befestigung und mechanische Abstützung — mittel — Teilprüfung
- Nur vier M3-Punkte: H1 (9, 9), H2 (271, 9), H3 (202, 251), H4 (64, 251). J2 liegt 104 mm vom nächsten Loch.
- Abschätzung der Teilprüfung: Eigenfrequenz 17–24 Hz mit Schienen (35 Hz ohne); 10 N an J2 ergeben 1,65 mm Durchbiegung. Für einen fahrenden Roboter ist das weich; auf der Platine gibt es keine Aufnahme für den geforderten Träger.
- Montagebohrungen sind unbeschichtet und netzlos, aber Innenlagenkupfer reicht bis 0,25 mm an die Lochwand (`LOGIC_GND` an allen vier, `BATT_N` an H1/H2, `V3V3` an H4).
- `MOTION_BUS_P` läuft auf 191 mm Länge 0,95 mm vom rechten Platinenrand.
- D63 (TO-220 mit spannungsführender Fahne) und C312/C313 (35 mm hoch) stehen ungestützt.

### GP-14 Kleinere Schaltungspunkte — niedrig — selbst
- Taster-Eingang J20 (kundenseitig): nur 1 kΩ + 10 nF, keine ESD-Diode. Gleiches gilt für J22, J14/J15 und die LED-Datenleitung.
- J22 Pin 1 führt `V3V3` ohne Serienwiderstand; ein Kurzschluss nach Masse löst den Brownout-Latch aus. Schleifenstrom nur 33 µA (für übliche Not-Halt-Kontakte zu wenig).
- `MAIN_FAULT_GPIO_N`: High-Pegel 2,27 V (R215 47 kΩ gegen R259 100 kΩ), garantierte Schwelle des ESP32 2,475 V. R259 auf 1 MΩ.
- eFuse-Statusausgänge (`*_EFUSE_FAULT_N`, `*_EFUSE_PGOOD`) liegen nur auf Testpunkten.
- eFuse-SHDN-Teiler 1 MΩ/68 kΩ: unter etwa 29,5 V Busspannung ist der garantierte Einschaltpegel von 2 V nicht mehr erreicht.
- Fernfühl-Diode Q11: 45 mm Einzelleitung ohne geführten Rückleiter.

## B. Dimensionierung und Schutzkoordination

### GP-15 Unterspannungsabschaltung ungefiltert — mittel — selbst
- Hauptschalter: 29,03 V fallend (27,97–30,41 V), Filter C6 1 nF (rund 10 µs). Anforderung MAIN-003 nennt 0,5 s; die Abweichung ist dokumentiert, aber nicht von Ihnen abgenommen.
- Motion (U5): 29,31 V (27,89–30,73 V), ungefiltert.
- Software-Abschaltung 30,5 V nach 5 s liegt innerhalb der Hardware-Toleranz.
- Bei 60–100 mΩ Quell- und Leitungswiderstand bedeuten 45 A einen Einbruch von 2,7–4,5 V. Ein Lastsprung schaltet dann schon bei 33–35 V Leerlaufspannung hart ab, bevor Linux herunterfahren kann.
- Abhilfe: C6 auf 1 µF (rund 10 ms) oder größer, Schwelle Richtung 28 V, Software-Schwellen mit Abstand zur oberen Hardware-Grenze.

### GP-16 Haupt- und Motion-Überstrom nicht selektiv — mittel — selbst
- Motion: 59,95 A (57,1–64,4 A, vom Datenblatt direkt spezifiziert). Hauptschalter: 65,09 A nominal; aus Komparatorschwelle (1,08–1,32 V), Offset (±2,1 mV bei 32,5 mV) und Verstärkungsstreuung ergeben sich etwa 48–80 A (Summe) bzw. 54–76 A (quadratisch).
- Beide Zeitglieder liegen bei rund 0,46 s (0,33–0,77 s bzw. 0,35–0,68 s). Der Hauptschalter kann also vor dem Motion-Gate auslösen und nimmt dann PC und Logik mit.
- Abhilfe: Hauptschalter auf etwa 80 A (R22 + R64 zusammen 15 kΩ), Motion-Zeitglied kürzer (C10 15–22 µF).

### GP-17 Chopper-Schwellen knapp über dem Ladeschluss — mittel — selbst
- Ein 43,00 V (42,68–43,32 V), Aus 42,40 V (42,07–42,73 V), Batterie voll 42,0 V.
- Mit angeschlossenem Ladegerät in der Konstantspannungsphase (42,0–42,4 V, je nach Gerät mehr) kann ein einmal ausgelöster Chopper eingeschaltet bleiben: rund 355 W in der Widerstandsbank, bis der NTC bei 84 °C abschaltet.
- Abhilfe: beide Schwellen um etwa 1 V anheben (R303/R331 sind dafür vorgesehen) oder mit dem realen Ladegerät verifizieren.

### GP-18 Chopper-Überwachung nicht ausfallsicher und nicht prüfbar — mittel — selbst
- Chopper und 46-V-Abschaltung teilen sich Regler U30, Referenz U31 und Komparator U32.
- `CHOP_FAULT_N` wird nur im Fehlerfall aktiv getrieben (Optokoppler-LED an). Eine ausgefallene Chopper-Versorgung sieht aus wie „kein Fehler".
- Die Funktion lässt sich im Betrieb nicht testen.
- Abhilfe: zusätzliches Bereit-Signal nach dem Ruhestromprinzip (z. B. aus U36), Firmware-Plausibilität „Bus über 43,5 V und Chopper nicht aktiv".

## C. Konzept und gesperrte Anforderungen

### GP-19 Dünne Abzweige ohne Überlastschutz — hoch für das Produkt — selbst
- J7 (Drive, 1,5 mm²), J8 (Lift-Wandler, 1,0 mm²) und die Gelenkzuleitungen (1–2,5 mm²) hängen nur am gemeinsamen Motion-Gate: 60 A über 0,5 s, 100 A Kurzschluss.
- Ein harter Kurzschluss wird erkannt. Ein hochohmiger Fehler mit 30–55 A bleibt unbegrenzt bestehen.
- Ursache sind die gesperrten Anforderungen TOP-005, MOT-005 und LIFT-002. Empfehlung: Abzweigsicherungen oder eFuse-Kanäle je Abgang, dimensioniert auf den dünnsten Leiter. PC- (2,98 A) und Logikzweig (1,98 A) sind dagegen passend geschützt.
- Hinweis: 6 mm² Batterieleitung an einer 60-A-Sicherung setzt Hochtemperatur-Isolation voraus.

### GP-20 Motion-Stopp einkanalig — mittel jetzt, hoch vor Aktortests — selbst
- Ein Kurzschluss Drain–Source in Q7 oder Q8 versorgt `MOTION_BUS_P` über die Body-Dioden von Q9/Q10 weiter. Es gibt keine Hardware-Erkennung; nur die Firmware könnte über `MOTION_BUS_ADC` den Hauptschalter öffnen.
- Der Freigabe-Eingang J22 ist einkanalig mit 3,3-V-Pegel.
- Die Armgelenke sind rücktreibbar und fallen bei jeder Abschaltung. Ein verzögerter Stopp (erst bremsen, dann trennen) ist nicht vorgesehen.

### GP-21 Jeder ESP32-Reset schaltet den PC hart ab — niedrig — selbst
- Fällt `ESP_MAIN_HOLD`, trennt der LTC2954 nach Ablauf des 5-s-Startfensters den Hauptschalter. Das gilt auch für Firmware-Updates und für jeden 3,3-V-Einbruch (Brownout-Latch).
- Flashen geht nur mit externer 5-V-Speisung an J11 oder gehaltenem TP33. Eine Prozedur fehlt.
- Hinweis zu BAT-003: Die Rückstromsperre spricht bei −10,5 mV an; bei 0,33 mΩ sind das etwa 32 A (16–61 A) für unter 1 µs. „Kein Rückstrom" gilt also statisch.

## D. Nachweise, Dokumentation, Repository

### GP-22 „247/247" und „46/46" sind Verbindungsprüfungen — mittel — Teilprüfung + Stichprobe
- Ein Leistungspaar gilt als bestanden, wenn beide Pads auf derselben Lage in derselben Kupferinsel liegen. Es gibt kein Breiten-, Strom- oder Temperaturkriterium.
- 18 der 247 Paare vergleichen ein Pad mit sich selbst, 3 sind doppelt; es bleiben 226 Paare in 24 Kupferinseln. Die Abgänge J7, J8, J12, C312/C313 und alle Zweignetze fehlen.
- Der unfertige A1-Stand mit 806 offenen Verbindungen erreichte mit demselben Prüfer 246/247 (selbst nachgestellt).
- „46/46" prüft für 46 benannte Pin-Paare nur, dass ein Pfad existiert. „18 Bereiche bestanden" heißt unverändert gegenüber einer früheren Aufnahme; zwei Fenster enthalten kein Kupfer.
- Das Engstellen-Audit der Rev A wurde für A2 nicht wiederholt; seine Kriterien ergäben 350 Abweichungen.
- Der Prüfercode liegt nur als Text in `retest-methods.json` mit absoluten macOS-Pfaden; die Originale sind verloren (494 gegen 492 Abgriff-Objekte).

### GP-23 Altes 360 × 300-Paket war als freigegeben markiert — hoch — Teilprüfung + Stichprobe — **durch Aufräumen erledigt**
- `rev-a/release.json` hatte `fabrication_release` und `assembly_release` auf `true` (Commit 26c7b05, Autor „Codex", ohne dokumentierte Freigabe). Die alte Platine hatte dieselben Schwächen wie GP-01 und GP-02.
- Beim Aufräumen am 2026-11-16 wurden die alte Platine, das Bestellpaket und `release.json` entfernt.

### GP-24 Veraltete und fehlende Unterlagen — mittel — Teilprüfung + Stichprobe — **teilweise erledigt**
- Erledigt beim Aufräumen: `CURRENT_STATE.md`, `context/index.json`, PMU-`README.md`, PMU-`AGENTS.md` und `rev-a/README.md` nennen jetzt A2 280 × 260 mm.
- Offen: Für A2 gibt es keine Zeichnungen für Schienen, Brücken, Scheiben und Folie (nur JSON). `MECHANICAL_BUILD.md` beschreibt Koordinaten der 360 × 300-Platine. Die Ausrichtung der M5-Klemmen ist für A2 nicht dokumentiert.
- Offen: Die 48 Einpressbohrungen sind in den Bohrdaten nicht als Presspassung gekennzeichnet, eine `PRESSFIT_HOLES.csv` für A2 fehlt; die Werkzeuge 1,400 und 1,475 mm liegen direkt nebeneinander. Die Bohrklassen 0,3 mm (683) und 0,2 mm (18) fehlten in der Prozessbeschreibung.
- Offen: Schriftfeld der PCB („WIP / NOT RELEASED", 2026-09-13) und Bestückungsdruck („DRAFT - NOT RELEASED"). Jede Freigabe braucht eine PCB-Änderung, damit einen neuen Hash und neue Nachweise.
- Offen: Die Umstellung auf 280 × 260 mm stützt sich auf eine Anweisung, die nicht im Repository stand; sie ist jetzt in `docs/decisions/2026-11-16-pmu-rev-a2-canonical.md` festgehalten.

### GP-25 Lokale Kontonamen und Altlasten im öffentlichen Repository — niedrig — Teilprüfung + Stichprobe — **teilweise erledigt**
- Vor dem Aufräumen: 13 Dateien mit `/Users/…`-Pfaden (207 Treffer) und 25 Dateien mit `C:\Users\…`-Pfaden; dazu Routerdateien, Duplikate und ein ZIP.
- Erledigt: Routerdateien, Duplikate, ZIP und alle Berichte der alten Stände sind entfernt.
- Offen: Die A2-Berichte unter `rev-a2-layout-280x260/reports/` und zwei Manifeste enthalten weiterhin `/Users/…`-Pfade. Sie wurden nicht verändert, weil sie über Hashes miteinander verkettet sind. In der Git-Historie bleiben alle Pfade ohnehin erhalten; vollständig entfernen ließe sich das nur durch Umschreiben der Historie.

## Bestätigt (ohne Befund)

- Commit und PCB-Hash; ERC und DRC mit Schaltplanparität bei KiCad 10.0.8, auch mit neu gefüllten Zonen: je 0 Befunde (`daten/native_checks.json`).
- Pinbelegung, Pin-1-Lage und Polarität aller geprüften Bauteile gegen Datenblätter. Kleinsignal-Transistoren, die Analog-Devices-Bausteine und die Phoenix-Stecker nur aus Sekundärquellen.
- Massefläche des LM74930 potentialfrei (keine Vias, kein Netz); Antennen-Sperrfläche x 220–268, y 238,8–259,8 auf allen Lagen kupferfrei.
- Alle Schwellen und Zeitglieder ergeben nachgerechnet die dokumentierten Werte (Tabelle in `BERECHNUNGEN.md`).
- Wake-, Hauptfehler- und Motion-Latch-Logik entspricht `WAKE_IO.md`; Motion ist standardmäßig aus, kein automatischer Wiederanlauf.
- Q1–Q10, Shunt-Kraftpads, J1–J6, BC1–15 und NT1–8 bleiben auch ohne alle dünnen Leiterbahnen über Flächen verbunden.
- Fertigungsentwurf lässt sich identisch regenerieren; Stückliste gleich Netzliste (421 Bauteile, 257 Netze); alle Zählwerte stimmen.
- Verluste bei 50 A: rund 7 W in FETs und Shunts, rund 6 W im Kupfer.

## Grenzen der Prüfung

- Keine Messungen, keine Hardware.
- Batterie-Innenwiderstand (60–100 mΩ), Zuleitungsinduktivität (2 µH) und Antriebskapazität sind Annahmen.
- SOA-Werte sind aus Diagrammen abgelesen; die Einschaltsimulation ist ein vereinfachtes Modell.
- Die Teilprüfungen zu Footprints, Nachweisen und Mechanik sind in den Kernaussagen nachgeprüft, nicht in jedem Einzelwert (Flächenstrom-Rechnung, Eigenfrequenz, Lackdicken).
- Firmware existiert noch nicht und war nicht Gegenstand.
- Diese Prüfung ersetzt weder die Prüfung durch eine Fachperson noch die physische Qualifikation (B01–B14).
