# Gegenprüfung PMU Rev A2 (280 × 260 mm) vom 2026-11-16

KI-gestützte Gegenprüfung des gesamten PMU-Konzepts: Schaltung, Leiterplatte, Schutzkoordination, Mechanik, Nachweise und Unterlagen. Sie ersetzt weder die Prüfung durch eine Fachperson noch die physische Qualifikation. Es wurde nichts an CAD oder Schaltung geändert; alle Freigaben bleiben `false`.

- Geprüfter Stand: Commit `d37c7f70536507b69d8bcac9a166c7d541a8984e`, PCB-SHA-256 `2742638d03b884b8b6ac7bf7064ef98b2bd6c5a95377b7617b72999eb2e83bc2`.
- Werkzeug: KiCad 10.0.8 (Projekt wurde mit 10.0.6 erstellt).

## Ergebnis

Die CAD-Angaben stimmen und die Schaltung ist im Kern richtig ausgelegt. **Diesen Stand nicht bestellen.** Es gibt 25 Befunde, die ERC, DRC und die Zähler „247/247" und „46/46" nicht erfassen können. Nötig sind eine Layoutrunde, einige geänderte Bestückungswerte und zwei Konzeptentscheidungen.

## Befunde im Überblick

Details mit Koordinaten und Abhilfe: [BEFUNDE.md](BEFUNDE.md). Rechenwege: [BERECHNUNGEN.md](BERECHNUNGEN.md). Maschinenlesbar: [findings.json](findings.json).

| Nr. | Befund | Einstufung |
|---|---|---|
| GP-01 | Schutzdioden D1/D2/D60/D61 hängen an 0,2-mm-Leiterbahnen; +42-V-Fläche an der Gehäusekante | hoch |
| GP-02 | Logik- und Leistungsmasse nur an NT9 verbunden; bei Unterbrechung lesen Haupt- und Motion-Schalter „ein" | hoch |
| GP-03 | Fremdnetz-Vias unter den Kupferschienen; BB1–BB5 elektrisch wirkungslos | hoch |
| GP-04 | Motion-Gate ohne definierte Einschaltstrombegrenzung; FET-Typ mit schwacher SOA | hoch |
| GP-05 | eFuse-Überspannung überlappt Motion-Abschaltung und Software-Stopp | hoch |
| GP-06 | Hardware-Fehlerleitungen ohne Serienwiderstand am ESP32 | mittel–hoch |
| GP-07 | 5-V-Eingang ohne Überspannungsschutz | mittel–hoch |
| GP-08 | Abstände 42 V zu Logik nicht geregelt; hochohmige Teiler; kein Schutzlack | mittel |
| GP-09 | Keine Diode gegen negative Spitzen an Systembus und eFuse-Ausgängen | mittel |
| GP-10 | Batterieklemmen nicht kodiert, Schaltung nicht verpolfest | mittel |
| GP-11 | Rückleiter schmaler als in Rev A (rechter Arm 6 mm, `BATT_N` eingeschnürt) | mittel |
| GP-12 | 0,15 mm Padabstand bei 70 µm Kupfer; fehlende Pin-1-Marken; Pasten-/Bohrdetails | mittel |
| GP-13 | Nur vier M3-Befestigungen, keine Abstützung an den Klemmen | mittel |
| GP-14 | Kleinere Schaltungspunkte (ESD, Pegel, Statusleitungen) | niedrig |
| GP-15 | Unterspannungsabschaltung ungefiltert | mittel |
| GP-16 | Haupt- und Motion-Überstrom nicht selektiv | mittel |
| GP-17 | Chopper-Schwellen knapp über dem Ladeschluss | mittel |
| GP-18 | Chopper-Überwachung nicht ausfallsicher, nicht prüfbar | mittel |
| GP-19 | Dünne Abzweige ohne Überlastschutz (gesperrte Anforderungen TOP-005, MOT-005, LIFT-002) | hoch für das Produkt |
| GP-20 | Motion-Stopp einkanalig; Arme fallen bei Abschaltung | mittel, hoch vor Aktortests |
| GP-21 | ESP32-Reset schaltet den PC hart ab; Flash-Prozedur fehlt | niedrig |
| GP-22 | „247/247" und „46/46" sind reine Verbindungsprüfungen | mittel |
| GP-23 | Altes 360 × 300-Paket war als freigegeben markiert | erledigt (entfernt) |
| GP-24 | Veraltete Unterlagen; A2-Mechanikzeichnungen und Bohrkennzeichnung fehlen | teilweise erledigt |
| GP-25 | Lokale Kontonamen in Berichtspfaden; Altlasten | teilweise erledigt |

## Bestätigt

ERC, DRC und Schaltplanparität je 0 Befunde (auch mit neu gefüllten Zonen); Pinbelegung und Polarität aller geprüften Bauteile; alle Schwellen und Zeitglieder; Wake- und Latch-Logik; Fertigungsentwurf, Stückliste und Zählwerte.

## Empfohlene Reihenfolge

1. Layoutrunde für GP-01 bis GP-04 und GP-06 bis GP-13.
2. Bestückungswerte nach GP-05 und GP-15 bis GP-17 anpassen.
3. Über GP-19 und GP-20 entscheiden (betrifft gesperrte Anforderungen).
4. Prüfskripte in `werkzeuge/` erneut laufen lassen und mit `daten/` vergleichen.
5. Danach Prüfung durch eine Fachperson und Rückfrage beim Fertiger zu 70 µm Kupfer, 0,20 mm Abständen und Presspassung.

## Inhalt dieses Verzeichnisses

| Pfad | Inhalt |
|---|---|
| `BEFUNDE.md` | Alle 25 Befunde mit Belegen, Koordinaten, Folgen und Abhilfe; Liste des Bestätigten; Grenzen |
| `BERECHNUNGEN.md` | Nachgerechnete Schwellen, Schutzleitern, D1-Anbindung, Masseverbindung, Einschaltsimulation, Toleranzen, Querschnitte |
| `findings.json` | Befundliste zum Nachverfolgen (Status je Befund) |
| `teilberichte/` | Wortlaut der drei Teilprüfungen: Footprints, Nachweise und Fertigungsdaten, Mechanik (englisch) |
| `werkzeuge/` | Lauffähige Prüfskripte und die Skripte der Teilprüfungen |
| `daten/` | Ergebnisse der Läufe vom 2026-11-16: native Prüfungen, Abstands- und Leistungspfad-Experiment, PCB-Geometrie, Simulation, Netzliste je Blatt, Lagenbilder |

## Grenzen

Keine Messungen. Batterie-Innenwiderstand, Zuleitungsinduktivität und Antriebskapazität sind Annahmen. SOA-Werte sind aus Diagrammen abgelesen. Die Teilprüfungen sind in den Kernaussagen nachgeprüft, nicht in jedem Einzelwert.
