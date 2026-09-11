# Astra-Auftrag: begrenzte Verkleinerung der HomeMy PMU Rev A.1

Status: verbindlicher Arbeitsauftrag für den kompakten Rev-A.1-Layoutversuch  
Datum: 2026-09-11  
Ausgangsbasis: Rev A, Commit d1f97ba64da8717becdcc40eeb3f6bda842252e4  
WIP-Referenz: Branch codex/pmu-rev-a1-250x200-wip, Commit 014632dd9d8c65689d6f62036c11b4d191d49fb4

## Ziel

Die HomeMy Power Management Unit soll nicht theoretisch maximal, sondern nur bis zur kleinsten innerhalb eines fest begrenzten Suchraums vollständig routbaren und regelkonformen Prototypplatine verkleinert werden.

Dieser Auftrag erlaubt keine unbeschränkten Routing-, Reparatur- oder Optimierungsschleifen.

## 1. Zuerst nur analysieren

Vor jeder Änderung vollständig lesen:

- Branch codex/pmu-rev-a1-250x200-wip
- Commit 014632dd9d8c65689d6f62036c11b4d191d49fb4
- rev-a1/WIP_ABSCHLUSS.md
- rev-a1/study/VARIANT_COMPARISON.md
- rev-a1/release.json
- die DRC-Berichte aus rev-a1/reports/routing-round-003/ und rev-a1/reports/local-routing-011/
- rev-a/design/HIGH_CURRENT_RULES.md
- rev-a/manufacturing/PCB_STACKUP_PRESSFIT.md
- DESIGN_REVIEW_AND_BRINGUP.md
- REV_A_ASSUMPTIONS.md

Alle relativen Pfade beziehen sich auf hardware/power-management-unit/.

Der WIP-Branch ist eingefrorene Evidenz und darf nicht verändert werden.

Der Kandidat mit 49 offenen Verbindungen ist nicht automatisch besser. Er besitzt 505 DRC-Meldungen gegenüber 470 beim Kandidaten mit 52 offenen Verbindungen. Er darf höchstens als Quelle für einzelne, nachweislich gültige Leitungsabschnitte dienen.

## 2. Arbeitsbranch und Repository-Hygiene

Ausschließlich auf Branch codex/pmu-rev-a1-bounded-shrink arbeiten.

Der Branch basiert auf dem geprüften Rev-A-Commit d1f97ba64da8717becdcc40eeb3f6bda842252e4. Weder diesen Basis-Branch noch den WIP-Branch verändern.

Aus dem WIP nur die tatsächlich benötigten KiCad-Quellen, die kompakte Platzierung, notwendige Skripte und abschließende Nachweise übernehmen. Den WIP-Commit nicht vollständig mergen oder cherry-picken.

Nicht übernehmen oder neu committen:

- .kicad_prl-Dateien
- Java-.class-Dateien
- Python-Caches
- temporäre DSN-/SES-Dateien
- vollständige Router-Logs
- redundante Zwischenplatinen
- redundante Renderings und Diagnosekopien

Pro untersuchter Größe höchstens eine aktive PCB-Datei und einen kompakten Ergebnisbericht behalten.

## 3. Unveränderliche Vorgaben

Nicht verändern:

- Schaltungstopologie, Netznamen und Funktionsumfang
- Bauteilidentitäten und Footprints
- alle 425 Footprints einschließlich vier Montagebohrungen
- alle 40 Testpunkte
- Steckverbinder, Press-fit-Pinbilder und externe Schnittstellen
- getrennte Kelvin-Paare
- Gate-Widerstände und Gate-/Kommutierungspfade
- Sternpunkte und getrennte Masse-/Arm-Rückleiter
- ESP32-Antennen-Keepout auf allen vier Kupferlagen
- vierlagiger Aufbau mit mindestens 70/35/35/70 µm fertigem Kupfer
- bestehende Hochstrom-Netzklassen
- mindestens 4 mm für Batterie-, SYS- und Motion-Hauptpfade
- mindestens 6 mm für Arm-Hauptpfade
- mindestens 0,8/0,4 mm für Leistungsvias
- Press-fit-, Bohrungs-, Busbar- und Kontaktgeometrien
- bestehende Sicherheits-, Default-OFF- und Diagnosefunktionen

Verboten sind:

- DRC-Regeln abschwächen, löschen oder zu Warnungen herabstufen
- neue pauschale DRC-Ausnahmen
- Leiterbahnen nur zur DRC-Beruhigung als Steuerabgriffe deklarieren
- schmale Steuerabgriffe als Bestandteil eines Hauptstrompfads anrechnen
- Footprints verkleinern oder durch andere Komponenten ersetzen
- Topologieänderungen ohne ausdrückliche Nutzerfreigabe
- 220 × 180 mm erneut untersuchen
- beliebige Zwischengrößen ausprobieren
- wiederholte globale Autorouterläufe mit nur geringfügig geänderten Einstellungen

Benötigt eine Größe eine verbotene Maßnahme, gilt sie als gescheitert.

## 4. Feste Größenleiter

Ausschließlich in dieser Reihenfolge untersuchen:

1. 250 × 200 mm
2. 275 × 210 mm
3. 300 × 220 mm

Die erste vollständig erfolgreiche Größe ist das Ergebnis. Danach sofort aufhören. Es wird nicht weiter nach einer theoretisch kleineren Variante gesucht.

### 250 × 200 mm

Genau ein weiterer vollständiger Rettungszyklus ist erlaubt.

Zuvor höchstens eine kurze, rein lesende Vorauswahl zwischen diesen Quellen durchführen:

- sauberer Platzierungsstand study/250x200-straight
- 52-Verbindungen-Stand aus reports/routing-round-003
- 49-Verbindungen-Stand aus reports/local-routing-011

Den sauberen Platzierungsstand oder den 52er-Stand bevorzugen. Der 49er-Stand darf nur gewählt werden, wenn eine reproduzierbare native Prüfung einen wirklichen Vorteil nach Fehlerarten und nicht nur nach der Ratsnest-Zahl nachweist.

Kein pauschales Weiterflicken des 49er-Kandidaten.

Besteht 250 × 200 mm nach dem einen Rettungszyklus nicht vollständig, Ergebnis dokumentieren und direkt zu 275 × 210 mm wechseln.

### 275 × 210 mm und 300 × 220 mm

Je Größe höchstens zwei vollständige Bearbeitungszyklen.

Größere Varianten aus der sauberen kompakten Platzierung ableiten. Nur nachweislich gültige Leistungs-, Kelvin-, Gate- und Referenzgeometrien übernehmen. Keine beschädigten Autorouter-Signalwege oder dangling Fragmente übernehmen.

## 5. Reihenfolge jedes Bearbeitungszyklus

1. Platzierung, Steckverbinder, Montagebohrungen, Testpunkte und Antennenfreiraum prüfen.
2. Hauptstromflächen, Shunts, MOSFET-Bänke, Busbar-Kontakte und tatsächliche Rückleiter bearbeiten.
3. Kelvin-, Gate-, Bias- und Referenzverbindungen herstellen.
4. Masseflächen und reale Via-Verbindungen kontrollieren. Eine nahe Fläche ohne tatsächliches Via gilt nicht als verbunden.
5. Steuer- und Messsignale routen.
6. Kupferflächen vollständig neu füllen.
7. Native ERC-, DRC- und Schaltplan-Paritätsprüfung ausführen.
8. Hochstrom-, Engstellen-, Via-, Anschluss-, Testpunkt-, Keepout- und Geometrieprüfungen ausführen.
9. Metriken zusammen mit PCB-SHA-256 dokumentieren.

Ein globaler Autorouterlauf darf nur einen Kandidaten erzeugen. Das Ergebnis muss fachlich geprüft werden. Wiederholte globale Autorouterläufe mit minimal veränderten Einstellungen sind nicht erlaubt.

## 6. Fortschrittskriterium

Nach jedem vollständigen Zyklus mindestens dokumentieren:

- offene Verbindungen insgesamt
- Anzahl betroffener Netze
- sämtliche DRC-Typen mit Anzahl und Schweregrad
- ERC-Ergebnis
- Schaltplan-Parität
- Kurzschluss- und Clearance-Fehler
- Breiten-, Bohrungs- und Viafehler
- dangling Tracks und Vias
- Hochstrom-Durchgängigkeit
- PCB-SHA-256

Ein weiterer Zyklus derselben Größe ist nur erlaubt, wenn:

- die offenen Verbindungen um mindestens 20 Prozent oder mindestens zehn Verbindungen sinken,
- die Gesamtzahl der DRC-Fehler nicht steigt,
- keine neuen Kurzschluss-, Clearance- oder Paritätsprobleme entstehen.

Wird dieses Fortschrittskriterium verfehlt, gilt die Größe sofort als gescheitert. Keine zusätzliche Reparaturvariante starten.

## 7. Erfolgskriterien

Eine Größe ist nur erfolgreich, wenn gleichzeitig erfüllt:

- 0 offene Verbindungen
- 0 ERC-Fehler
- 0 DRC-Fehler unter den bestehenden Regeln
- 0 Schaltplan-Paritätsabweichungen
- 0 Kurzschlüsse
- 0 Clearance-Verstöße
- 0 unzulässige Leiterbahn-, Verbindungs-, Bohrungs- oder Via-Abmessungen
- 0 dangling Tracks und Vias
- alle 425 Footprints gültig platziert
- alle 40 Testpunkte erreichbar
- alle externen Anschlusskorridore frei
- ESP32-Antennen-Keepout auf allen vier Kupferlagen intakt
- alle geprüften Leistungsendpunkte ohne Anrechnung schmaler Steuerabgriffe durchgängig
- Hochstromflächen, Engstellen, Busbar-Kontakte, Gate- und Kelvin-Verbindungen erneut geprüft
- Prüfergebnisse an den exakten finalen PCB-Hash gebunden
- native KiCad-Prozesse regulär mit Exit-Code 0 beendet

Eine niedrige Ratsnest-Zahl oder ein optisch vollständiges Board ist kein Erfolg.

## 8. Harte Abbruchgrenzen

- höchstens fünf Bearbeitungszyklen insgesamt:
  - einer bei 250 × 200 mm
  - zwei bei 275 × 210 mm
  - zwei bei 300 × 220 mm
- höchstens acht vollständige native DRC-Aufrufe
- höchstens 150 Minuten gesamte Bearbeitungszeit
- spätestens nach 140 Minuten nur noch sichern, dokumentieren, committen und pushen
- nach zwei identischen KiCad-CLI-Abstürzen oder Timeouts keine weiteren Umgebungsreparaturen versuchen
- keine Registry-Manipulationen
- keine endlosen Prozessneustarts

Wenn die native Prüfung in der Agentenumgebung zweimal identisch abstürzt, genau einen reproduzierbaren Einmalbefehl für die normale Benutzerumgebung erstellen. Danach Stand sichern und aufhören. Ohne regulären Exit-Code 0 keine Größe als erfolgreich bezeichnen.

Scheitert auch 300 × 220 mm, vollständig abbrechen. Dokumentieren, dass im erlaubten Suchraum keine freigabefähige Verkleinerung erreicht wurde. Keine weiteren Zwischengrößen oder automatischen Reparaturen starten.

## 9. Agenteneinsatz

Astra Ultra und Subagenten dürfen verwendet werden.

Dabei gilt:

- genau ein leitender Agent darf KiCad-Quelldateien verändern
- Subagenten prüfen DRC, Hochstrompfade, Geometrie und Repository-Hygiene nur lesend
- niemals mehrere Agenten gleichzeitig dieselbe PCB-, Schaltplan- oder Projektdatei bearbeiten lassen
- der leitende Agent entscheidet über jede Übernahme

## 10. Ergebnis und Dokumentation

BOUNDED_SHRINK_RESULT.md erstellen mit:

- untersuchten Größen
- jeweiliger Ausgangsdatei und SHA-256
- erlaubten und tatsächlich ausgeführten Zyklen
- Ergebnis jeder Fortschrittsprüfung
- vollständigen Endmetriken
- ausgewählter kleinster bestandener Größe oder eindeutigem Abbruchergebnis
- bekannten verbleibenden technischen Risiken
- Hinweis, dass keine thermische Hardwarevalidierung erfolgt ist

Falls eine Größe vollständig besteht:

- in release.json nur tatsächlich nachgewiesene CAD-Zustände aktualisieren
- fabrication_release, assembly_release und production_release bleiben false
- noch kein Bestell- oder Fertigungspaket erzeugen

Abschließenden Stand committen und pushen.

Die Abschlussantwort enthält nur:

- Branch
- Commit-SHA
- gewählte Platinengröße oder Abbruchergebnis
- ERC-/DRC-/Paritätsstatus
- Zahl offener Verbindungen
- ausgeführte Zyklen und Arbeitszeit
- verbleibende Blocker
- eindeutigen Hinweis, ob der Stand bestellbar ist

Vor Beginn und nach jedem Zyklus erneut prüfen, ob die Abbruchgrenzen erreicht sind.
