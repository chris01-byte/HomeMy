# AGENTS.md

## Zweck

HomeMy ist ein ROS-2-Projekt fuer einen Haushaltsroboter. Der Standardzustand ist Simulation oder motorloser Test. Reale Hardware kann physische Wirkung haben.

## Sicherheitsregeln

1. Keine Aktoren, Motoren oder Endeffektoren ohne ausdrueckliche Freigabe einer anwesenden Person.
2. Erst Offline-, Simulations- oder motorlose Pruefung; danach nur ein begrenzter beaufsichtigter Realtest.
3. Keine Tokens, Schluessel, Zugangsdaten, Wohnungsdaten, Kamerabilder, Karten oder ROS-Bags committen.
4. Sicherheits-, Sensor-, Netzwerk- und Kalibrierungsaenderungen bleiben je Aenderung getrennt und brauchen einen Rueckfallweg.
5. Keine unbekannten Hardware- oder Konfigurationsdateien ueberschreiben.

## Kontext mit kleinem Budget

1. Zuerst `CURRENT_STATE.md` lesen.
2. Danach in `context/index.json` genau den Bereich der Aufgabe waehlen.
3. Nur die dort genannten Dateien und den betroffenen Vertrag laden; nicht pauschal `docs/` oder alle Transfers lesen.
4. Historische Evidenz nur bei einer konkreten Frage laden.
5. Nach einer Entscheidung nur die passende Status-, ADR- oder Transferdatei aktualisieren.

Der aktive Agentenkontext soll klein, aktuell und nach Themen getrennt bleiben. Lange Logs gehoeren nach `docs/archive/`, nicht in den Standardkontext.

## Transfers aus roboter_ws

- Nie ganze Pakete oder Verzeichnisse blind kopieren.
- Jeder Transfer beginnt mit Quelle, Commit, Ziel, Schnittstellenvertrag, Tests und Rueckfallweg in `integration/roboter_ws/TRANSFER_MANIFEST.md`.
- Erst die Schnittstelle stabilisieren, dann Implementierung uebernehmen.
- Echte Umgebungsdaten bleiben lokal; das Repository enthaelt nur anonymisierte oder synthetische Fixtures.

## Arbeitsweise

- Eine Branch-Aenderung hat ein fachliches Thema.
- Vor Parameteraenderungen messen oder einen klaren Test formulieren.
- Tests, bekannte Grenzen und Rueckfallweg in der passenden Dokumentation festhalten.
- `main` bleibt ein nachvollziehbar getesteter Stand.
