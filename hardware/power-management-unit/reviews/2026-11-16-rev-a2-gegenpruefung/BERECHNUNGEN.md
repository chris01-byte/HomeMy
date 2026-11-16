# Rechenwege der Gegenprüfung PMU Rev A2

Stand 2026-11-16. Alle Werte sind Rechnungen aus Datenblattangaben und der exportierten Netzliste, keine Messungen. Datenblätter liegen unter `../../rev-a/evidence/`. Bauteilwerte stammen aus `daten/netzliste/`.

## 1. Nachgerechnete Schwellen und Zeitglieder

Alle Werte stimmen mit `rev-a/design/POWER_STAGE.md`, `WAKE_IO.md` und `CHOPPER_MECHANICS.md` überein.

| Funktion | Bauteile | Formel (Datenblatt) | Nominal | Grenzen |
|---|---|---|---|---|
| Haupt-UV fallend | R25 523 kΩ / R26 10,1 kΩ | 0,55 V × 52,78 | 29,03 V | 27,97–30,41 V |
| Haupt-UV steigend | wie oben | 0,60 V × 52,78 | 31,67 V | 30,71–33,42 V |
| Haupt-OV steigend / fallend | R27 732 kΩ / R28 10 kΩ | 0,60 V bzw. 0,55 V × 74,2 | 44,52 / 40,81 V | 43,17–46,98 V |
| Haupt-Überstrom | R21 49,9 Ω, R22+R64 18,4 kΩ, 0,5 mΩ | I = 12 × RSET / (RILIM × RSNS) | 65,09 A | siehe 7 |
| Haupt-Kurzschluss | R23 3,65 kΩ | (20 mV + 11 µA × RISCP) / RSNS | 120,3 A | 102–134 A |
| Haupt-Zeitglied | C3 33 µF ‖ R24 100 kΩ | t = −RC ln(1 − V/(I R)), 85 µA, 1,2 V | 0,50 s | 0,35–0,91 s |
| Motion-Überstrom | R30 100 Ω, R31 39,7 kΩ | RIWRN = 11,9 × RSET / (RSNS × IOC) | 59,95 A | 57,1–64,4 A |
| Motion-Kurzschluss | R32 2,74 kΩ | RISCP = ISC × RSNS / 15,6 µA − 464 Ω | 99,96 A | 85,7–114,9 A |
| Motion-Zeitglied | C10 33 µF ‖ R33 100 kΩ | wie oben, 82 µA | 0,52 s | 0,38–0,74 s |
| Motion-UVLO (TPS48110) | R35 226 kΩ / R36 10 kΩ | 1,18 V / 1,11 V × 23,6 | 27,85 / 26,20 V | — |
| Motion-UV-Latch (U5) | R62 226 kΩ / R63 10 kΩ | 1,242 V × 23,6 | 29,31 V | 27,89–30,73 V |
| eFuse-Strombegrenzung | R40 6,04 kΩ / R50 9,09 kΩ | 18 / R[kΩ] | 2,98 / 1,98 A | ±10 % |
| eFuse-UVLO | 191 kΩ / 10 kΩ | 1,2 V × 20,1 | 24,12 V | 23,6–24,7 V |
| eFuse-OVP steigend | R43, R53 374 kΩ / 10 kΩ | 1,2 V × 38,4 | 46,08 V | 45,0–47,2 V |
| eFuse-OVP fallend | wie oben | 1,122 V × 38,4 | 43,08 V | 41,9–44,2 V |
| eFuse-Rampe | C20, C25 22 nF | 42 V / (25 × 2 µA / C) | 18,5 ms | 15–23 ms |
| Chopper ein / aus | R302+R303 161,4 kΩ, R304 10 kΩ, Rückkopplung 2,69 MΩ vom Gate | Knotengleichung am Komparator, Uref 2,5 V | 43,00 / 42,40 V | 42,68–43,32 / 42,07–42,73 V |
| Motion-OV-Latch | R308 174 kΩ / R309 10 kΩ | 2,5 V × 18,4 | 46,00 V | 45,66–46,34 V |
| NTC-Fenster Chopper | R312/R313, R314/R315 | 0,2478 V und 2,475 V an 10 kΩ NTC | 1,1 kΩ ≙ etwa 84 °C; offen > 1 MΩ | — |
| Referenzüberwachung U36 | R325 117 kΩ / R326 24,9 kΩ | 0,405 V × 5,70 | 2,308 V | — |
| Always-on-Spannung | R202 174 kΩ / R203 100 kΩ | 1,22 V × 2,74 | 3,343 V | 3,19–3,50 V |
| Startfenster U21 | R208 120 kΩ, Teilercode 7 | 2²¹ × (120 k/50 k) × 1 µs | 5,03 s | 4,80–5,27 s |
| Einschaltentprellung U16 | C203 22 nF | 32 ms + 6,7 s/µF × C | 0,18 s | — |
| Zwangsabschaltung U16 | C204 1 µF | 64 ms + 6,7 s/µF × C | 6,5–6,8 s | 4,1–9,5 s (Projektangabe) |
| Watchdog U51 | CWD offen, SET1 high | fest | 1,6 s | 1,36–1,84 s |

## 2. Spannungs- und Stromleiter

Bus steigend (Rückspeisung):

| Spannung | Wirkung |
|---|---|
| 42,0 V | Batterie voll (Ladegerät je nach Toleranz bis etwa 42,4 V) |
| 42,07–42,73 V | Chopper aus |
| 42,68–43,32 V | Chopper ein |
| 43,5 V | Software-Warnung |
| 43,17–46,98 V | Haupt-OV (misst nur die Batterieseite) |
| 45,0 V | Software: kontrollierter Stopp |
| 45,0–47,2 V | eFuses trennen PC und 5-V-Wandler (Wiedereinschalten unter 41,9–44,2 V) |
| 45,66–46,34 V | Motion-Latch |
| 47,8–52,8 V | Durchbruch SMCJ43A (Motion-Bus); 48–53 V PTVS1-043C (Eingang, Systembus) |
| 55 / 60 / 65–70 / 100 V | PC-Wandler / Gelenkantriebe / ICs / FETs |

Bus fallend: Software 33,0 V (10 s), 31,5 V (5 s), 30,5 V (5 s); Motion-Latch 27,89–30,73 V sofort; Hauptschalter 27,97–30,41 V nach rund 10 µs; BMS 27,5 V; TPS48110 26,2 V; eFuses 22,6 V.

Strom: Software 45 A (1 s) und 50 A (2 s); Hauptschalter etwa 48–80 A (0,33–0,77 s); Motion 57–64 A (0,35–0,68 s); Sicherung 60 A; Motion-Kurzschluss 86–115 A; Haupt-Kurzschluss 102–134 A; Batterie-Spitze 150 A für 1–3 s.

## 3. Anbindung der Eingangsschutzdiode D1 (GP-01)

- Geometrie: F.Cu 0,2 mm × 70 µm über 5,0 mm; In1.Cu 0,2 mm × 35 µm über 14,3 mm; zwei Vias 0,3 mm; Masseseite 0,2 mm × 2,8 mm und ein Via.
- Widerstand (ρ = 1,72·10⁻⁸ Ωm): F.Cu 1,23 mΩ/mm × 5,0 mm = 6 mΩ; In1 2,46 mΩ/mm × 14,3 mm = 35 mΩ; Via je 1,2 mΩ (Hülse π × 0,3 mm × 25 µm, 1,6 mm lang); Masseseite 3,4 mΩ + 1,2 mΩ. Summe rund 45 mΩ.
- Schmelzgrenze der Innenlagenbahn nach Onderdonk: A = 0,007 mm² = 13,8 Kreismil; I²t = A² × log₁₀((1083 − 25)/(234 + 25) + 1) / 33 = 190 × 0,706 / 33 = 4,1 A²s.
- Kurzschlussfall (Annahmen: Quelle plus Leitung 70 mΩ, 2 µH; Kurzschlussstrom asymptotisch 42 V / 70 mΩ = 600 A, τ = L/R = 29 µs):
  - Schwelle 120 A nach 6,5 µs. Reaktionszeit: Komparator 3,5–5,5 µs, RC-Filter 3,65 kΩ × 1 nF = 3,7 µs, Gate-Entladung 3 × 539 nC / 128 mA = 12,6 µs, zusammen rund 15–20 µs.
  - Strom beim Abschalten: 600 A × (1 − e^(−21,5/29)) = 314 A; ungünstig bis etwa 500 A.
  - Kommutierung in D1: t = L × I / (U_klemm − U_batt) = 2 µH × 314 A / 14 V = 45 µs; Energie 0,5 × 56 V × 314 A × 45 µs = 0,4 J; ∫i²dt = I² t / 3 = 1,5 A²s. Bei 500 A: 71 µs, 1,0 J, 5,9 A²s.
  - Zusatzspannung über die Anbindung: 300 A × 45 mΩ = 13,5 V; mit 56 V Klemmspannung rund 70 V am Knoten (Grenzwert LM74930 70 V), induktiver Anteil noch nicht gerechnet.
- Die Projektrechnung (`POWER_STAGE.md`) setzt 120 A × 25 µs an (0,126 J und 0,0144 J). Sie berücksichtigt den Stromanstieg während der Reaktionszeit nicht.

## 4. Einzige Masseverbindung NT9 (GP-02)

- Netzlistenabfrage: Nur NT9 verbindet `LOGIC_GND` und `BATT_N` (`daten/netzliste/massebruecken.txt`).
- Rückstrompfad der Logik: `V5V` (J11.1) → U12 → `V3V3` → Lasten → `LOGIC_GND` → NT9 → `BATT_N` → NT8 → `LOGIC_5V_N` → J11.2. Nur der LED-Streifen fließt direkt über `LOGIC_5V_N`.
- Bei offenem NT9: Die Always-on-Domäne (LT3014B aus `BATT_SENSED_P` über 2 × 4,99 kΩ, rund 0,3 mA) und die Logikversorgung speisen Strom in `LOGIC_GND`, der nur über parasitäre Pfade nach `BATT_N` zurückkann: R29 1 MΩ, R237 + R39 110 kΩ, Schutzdiode des ESP32-Pins IO5 über U60 und R61 10 kΩ. Abschätzung: 0,6 V + 0,3 mA × 10 kΩ ≈ 3,6 V; Obergrenze durch die Schutzdioden der Logik-ICs gegen `V5V` bei etwa 5,6 V.
- Pegel an den Empfängern: EN des LM74930 = U(`LOGIC_GND`) × 1 MΩ / 1,01 MΩ ≈ 3,5 V (Schwelle 0,8–1,05 V). INP des TPS48110 = U × 100 kΩ / 110 kΩ ≈ 3,3 V (Schwelle 1,6–2 V). Beide lesen „ein", unabhängig vom Zustand der Latches.

## 5. Einschalten des Motion-Gates (GP-04)

- Modell (`werkzeuge/inrush_sim.py`): Sourcefolger. Gatestrom I_g = (12 V − U_GS) / 180 kΩ − U_GS / 2,5 MΩ lädt C_GS (4 × 24 nF + 10 nF) und die Miller-Kapazität der beiden Eingangs-FETs Q7/Q8. Kennlinie I_D = K × (U_GS − 3 V)² mit K = 14,8 A/V² je FET (25 A bei 4,3 V). Crss(U): 5 nF unter 8 V, darüber × (8/U)^2,1; ergibt Crss(42 V) = 177 pF und 82 nC bis 50 V (Datenblatt: 123 pF typisch bei 50 V, QGD 69,5 nC typisch).
- SOA PSMN1R0-100ASF bei 25 °C, aus Fig. 3 abgelesen und als Geraden im doppelt logarithmischen Maßstab angenähert:
  - 100 µs: 11 kW konstant (110 A bei 100 V).
  - 1 ms: 440 A bei 10 V bis 3,5 A bei 100 V, Steigung −2,1.
  - 10 ms: 440 A bei 4,2 V bis 1,7 A bei 100 V, Steigung −1,75.
  - 100 ms: 580 A bei 1,3 V bis 0,95 A bei 100 V, Steigung −1,48.

| U_DS | 100 µs | 1 ms | 10 ms | 100 ms |
|---|---|---|---|---|
| 20 V | 550 A | 103 A | 28,5 A | 10,2 A |
| 30 V | 367 A | 43,8 A | 14,0 A | 5,6 A |
| 42 V | 262 A | 21,6 A | 7,8 A | 3,4 A |

  PSMN1R0-100ASE bei 42 V (aus dessen Fig. 3, gröber abgelesen): 1 ms etwa 80 A, 10 ms etwa 40 A, 100 ms etwa 12 A; bei 125 °C etwa 55 / 22 / 8 A.
- Ergebnis (ein FET trägt den gesamten Strom, 25 °C):

| Lastkapazität | Spitzenstrom | Rampe | Energie in den FETs | Verhältnis zur SOA |
|---|---|---|---|---|
| 752 µF | 18 A | 4,1 ms | 0,66 J | 0,42 |
| 940 µF | 21 A | 4,2 ms | 0,83 J | 0,50 |
| 1128 µF | 24 A | 4,3 ms | 0,99 J | 0,59 |
| 2000 µF | 37 A | 4,8 ms | 1,76 J | 0,96 |
| 4000 µF | 61 A | 5,6 ms | 3,53 J | 1,71 |
| 8000 µF | 98 A | 6,8 ms | 7,06 J | 3,02 |

  Streuung bei 940 µF: Crss(50 V) 12 pF → 33 A in 2,7 ms; 321 pF → 15 A in 9,3 ms; Schwellspannung 2 V / 4 V → 23 A / 19 A. Vor der Rampe vergehen 3,6–8 ms Totzeit.
- Die Energie in den FETs ist immer ½ C U². R34 lässt sich wegen der 4 × 10 MΩ Gate-Widerstände nur bis etwa 1 MΩ vergrößern (U_GS dann 8,6 V).
- Vorschlag mit Gate-Kondensator nach TI Gleichung 3: dU/dt = 0,63 × 12 V / (R1 × C1). Mit 180 kΩ und 47 nF: 0,89 V/ms, 42 V in 47 ms, 3,6 A bei 4000 µF. Bedingung C_BST > Q_g,ges + 10 × C1 ist mit 9,4 µF (wirksam rund 3,9 µF) erfüllt.

## 6. eFuse-Überspannung (GP-05)

- TPS26631: Abschaltverzögerung 8,5–14 µs. Wiedereinschalten schnell (58–225 µs), solange der Ausgang über der PGOOD-Schwelle liegt (R47/R48: 1,123 V × 20,1 = 22,6 V); sonst mit voller Rampe (18,5 ms ab 0 V).
- Stützbedarf bei voller Rampe: PC mit 65 W über 18 ms braucht 1,17 J, das sind rund 1400 µF zwischen 42 V und 10 V. Die 5-V-Seite hat mit C246 1000 µF zwischen 5,0 V und 3,9 V nur 4,9 mJ, also etwa 2 ms bei 2,5 W.
- Vorschlag: R43/R53 392 kΩ → 48,24 V (47,3–49,2 V); 407 kΩ → 50,04 V (49,0–51,0 V).

## 7. Genauigkeit des Haupt-Überstroms (GP-16)

- LM74930: Komparatorschwelle 1,08 / 1,22 / 1,32 V (−11,5 % / +8,2 %); Eingangsoffset ±2,1 mV bei 32,5 mV Messspannung (±6,5 %); Verstärkung des Stromspiegels 82 / 90 / 97 (−8,9 % / +7,8 %, für IMON spezifiziert, für ILIM als gleich angenommen).
- Summe: 65 A × (1 − 0,27) bis × (1 + 0,22) = 47,5–79,5 A. Quadratisch: etwa 54–76 A.
- TPS48110 zum Vergleich: 29,2 / 30,6 / 31,5 mV direkt spezifiziert, also 57,1–64,4 A einschließlich Widerständen.
- Für 80 A nominal: RILIM = 12 × 49,9 / (80 × 0,0005) = 15,0 kΩ.

## 8. Spannungseinbruch und Unterspannung (GP-15)

- Annahme Quellwiderstand: 10S7P mit 20–35 mΩ je Zelle ergibt rund 40 mΩ; BMS, Verbinder, Sicherung und 2 × 1 m mit 6 mm² rund 25–40 mΩ; zusammen 60–100 mΩ.
- Einbruch bei 45 A: 2,7–4,5 V; bei 50 A: 3,0–5,0 V.
- Filter am UVLO-Pin: (523 kΩ ‖ 10,1 kΩ) × 1 nF = 9,9 µs. Mit 1 µF: 9,9 ms.

## 9. Chopper (GP-17, GP-18)

- Strom bei 43 V an 5 Ω: 8,6 A, 370 W; bei 42 V: 8,4 A, 353 W.
- Dauerhaft ein bleibt der Chopper, wenn die Busspannung unter Last über seiner Ausschaltschwelle bleibt: U_Quelle − 8,4 A × R_Quelle > 42,07–42,73 V. Mit Batterie allein (70 mΩ, Einbruch 0,59 V) wären dafür über 42,66 V Leerlaufspannung nötig. Mit einem Ladegerät, das 42,4–42,7 V hält und einen Teil des Stroms liefert, ist die Bedingung bei Exemplaren am unteren Toleranzrand erfüllt.
- Versorgung der Analogschaltung: Last am 10-V-Regler rund 8–10 mA; Verlust (46 V − 10 V) × 10 mA = 0,36 W.
- Fehlersignal: LED-Strom (10 V − 1,2 V − 0,6 V − 0,3 V) / 4,7 kΩ = 1,7 mA; Optokoppler mit mindestens 100 % Übertragung gegen 10 kΩ Pull-up.

## 10. Rückstromschwelle (GP-21)

- Schnelle Rückstromerkennung des LM74930: −10,5 mV (−16 bis −5 mV), Abschaltung in 0,5–0,95 µs. Drei parallele FETs: 0,33 mΩ bei 25 °C (typisch 0,26 mΩ). Rückstrom bis zum Ansprechen: 10,5 mV / 0,33 mΩ = 32 A; Grenzen 16–61 A.
- Unter 32 A Vorwärtsstrom regelt der Baustein den Spannungsabfall auf 10,5 mV; die FETs sind dann nur teilweise aufgesteuert.

## 11. Verluste und Kupferquerschnitte (GP-11)

- Halbleiter und Shunts bei 25 °C (Maximalwerte): Hauptschalter 0,33 + 0,33 mΩ, Motion 0,5 + 0,5 mΩ, zwei Shunts je 0,5 mΩ, zusammen 2,66 mΩ; bei 50 A 6,7 W.
- Kupfer ohne Schienen laut Flächenstrom-Rechnung der Teilprüfung 6,3 W bei 50 A (je Abschnitt 96–195 µΩ, `BATT_N` 891 µΩ, Armrückleiter rund 1,0–1,2 mΩ).
- `ARM_R_N`: 6,0 mm × 70 µm × 2 Lagen = 0,84 mm²; 32 mm lang; 0,66 mΩ; bei 25 A 0,41 W und 30 A/mm². Erwärmung nach IPC-2221 (I = 0,048 × ΔT^0,44 × A^0,725, A in mil²) je Lage mit 12,5 A und 651 mil²: ΔT = 7,1 K; beide Lagen zusammen grob 15 K.
- `BATT_N` bei x = 207–219: Innenlage 33 mm × 35 µm × 12 mm Länge = 0,18 mΩ; bei 50 A 0,45 W und rund 43 A/mm².
- Flächenwiderstand 70 µm: 0,246 mΩ je Quadrat, zwei Lagen parallel 0,123 mΩ.
- Shunt-Pad: 50 A / (5,6 mm × 70 µm) = 127 A/mm² an der Padkante, über wenige Zehntelmillimeter.

## 12. Ruhestrom (Schätzung)

- Teiler am Hauptschalter: 42 V / 533 kΩ + 42 V / 742 kΩ = 136 µA. LM74930 abgeschaltet 2,5–5 µA.
- Always-on-Domäne: R206 47 kΩ (70 µA im Aus-Zustand), R215 47 kΩ (70 µA, falls FLT im Aus-Zustand low ist), LTC6993 rund 90 µA, Rückkopplung 12 µA, LT3014B 7 µA.
- Summe rund 0,4 mA (Projektbudget 0,6 mA). Bei 17,5 Ah sind das mehrere Jahre; der Wert ist zu messen.

## 13. Abstände und Leckempfindlichkeit (GP-08)

- IPC-2221B Tabelle 6-1, Mindestabstände in mm:

| Spannung | Innenlage | Außen, mit Lötstopplack | Bauteilanschluss unbeschichtet | mit Schutzlack |
|---|---|---|---|---|
| 31–50 V | 0,1 | 0,13 | 0,4 | 0,13 |
| 51–100 V | 0,1 | 0,13 | 0,5 | 0,13 |

- Ergebnis der Testregel: 499 Stellen unter 0,6 mm, davon 371 gegen Flächen auf Innenlagen bei 0,30 mm; 27 mit Pad-Beteiligung auf Außenlagen unter 0,4 mm.
- Leckempfindlichkeit: 10 MΩ parallel zu R27 (732 kΩ) senkt die OV-Schwelle um 6,8 %; parallel zu R25 (523 kΩ) senkt die UV-Schwelle um 5 %; 100 kΩ parallel zu R45 (1 MΩ) hebt `PC_SHDN` auf rund 18 V (Grenzwert 5,5 V).

## 14. Sonstige Einzelwerte

- `MAIN_FAULT_GPIO_N`: 3,343 V × 100 kΩ / 147 kΩ = 2,27 V; garantierte High-Schwelle des ESP32 0,75 × 3,3 V = 2,475 V.
- Messbereich der Busspannungsteiler: (10 kΩ ‖ 100 kΩ) / (200 kΩ + 10 kΩ ‖ 100 kΩ) = 1/23; 42 V → 1,83 V, 65 V → 2,83 V.
- Ladungspumpe LM74930: Freigabeverzögerung 175 µs + 1 µF × 6,6 V / 2,7 mA = 2,6 ms (bis 5,1 ms bei 1,3 mA); die Fehlermaske der Wake-Schaltung beträgt 1–5,5 ms.
- TPS48110-Bootstrap: 9,4 µF × 7,6 V / 100 µA = 0,71 s bis zur Treiberfreigabe.
- Kelvin-Leitungen: 146 / 143 mm (Hauptshunt) und 124 / 122 mm (Motion) mit 0,2 mm, überwiegend Innenlage; rund 0,3–0,36 Ω je Leitung; Fehler unter 0,2 %.
- 3,3-V-Regler U12: 0,5 A × 1,7 V = 0,85 W; ohne Kühlfläche über 100 K/W, also nur für die tatsächlichen 0,1–0,2 A geeignet.
- Leiterschutz: 1 mm² an einem Fehler mit 50 A und 0,7 Ω setzt 1,75 kW an der Fehlerstelle um, ohne dass 60 A / 0,5 s oder 100 A erreicht werden.
