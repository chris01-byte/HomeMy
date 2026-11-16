# HomeMy – App für iPhone

Native SwiftUI-App für HomeMy. Sie schaltet den Kartiermodus, zeigt die Karte, speichert sie und verwaltet die Räume. Die Schnittstelle zum Roboter steht in [`contracts/api/app-bridge.md`](../../contracts/api/app-bridge.md).

Die App beruht auf der Amadeus-App (`ios/Robotersteuerung` in roboter_ws, Commit `05439c7`).

**Stand:** Die App ist gegen den mitgelieferten Mock getestet. Auf der Roboterseite gibt es die Schnittstelle noch nicht.

## Was die App kann

- Verbindung zum Roboter über rosbridge (WebSocket).
- Kartiermodus ein- und ausschalten. Gefahren wird danach mit dem Controller am Roboter, nicht mit der App.
- Stopp-Knopf: hält den Roboter an und beendet den Kartiermodus.
- Anzeige: Controller verbunden oder nicht, Zeit bis zum automatischen Ende, Grund des letzten Endes.
- Live-Karte mit Zoom, Verschieben und Drehen.
- Karte speichern, sobald der Kartiermodus beendet ist.
- Räume als Flächen einzeichnen, benennen, optional mit Fahrziel und Blickrichtung, und wieder löschen.

## Was die App nicht kann

- Sie sendet keine Fahrbefehle.
- Einen Raum anfahren. Fahrziele werden nur gespeichert.
- Eine zweite Karte speichern, nachdem schon Räume zu einer Karte gehören.
- Die Roboterposition auf der Karte anzeigen.
- Den Controller koppeln.
- Zugriffsschutz: Die Verbindung ist unverschlüsselt und ohne Anmeldung. Nur in einem vertrauenswürdigen Labornetz verwenden.

## Voraussetzungen

- iPhone mit iOS 16 oder neuer.
- Xcode auf einem Mac.
- iPhone und Roboter (oder der Mock) im selben WLAN.

## Auf dem iPhone installieren

1. `HomeMy.xcodeproj` in Xcode öffnen.
2. Target **HomeMy** → **Signing & Capabilities** öffnen.
3. Bei **Team** das eigene Apple-Konto auswählen. Im Projekt ist bewusst kein Team hinterlegt.
4. Die Bundle-ID `com.example.HomeMy` durch eine eigene, eindeutige ID ersetzen.
5. iPhone verbinden, als Ziel wählen und **Run** drücken.
6. Beim ersten Verbinden den iOS-Dialog für das lokale Netzwerk mit **Erlauben** bestätigen.
7. In der App die Adresse des Roboters eintragen, zum Beispiel `ws://192.168.1.50:9090/`.

Die zuletzt erfolgreich verwendete Adresse wird nur lokal in den App-Einstellungen gespeichert.

## Ohne Roboter ausprobieren

Der Mock braucht weder ROS noch zusätzliche Python-Pakete und verwendet nur künstliche Daten.

```bash
python3 Tools/mock_rosbridge.py
```

Danach die App im iOS-Simulator starten und `ws://127.0.0.1:9090/` eintragen.

Ablauf zum Durchspielen:

1. Im Tab **Kartieren** den Kartiermodus einschalten.
2. In den Tab **Karte** wechseln: Die Testwohnung wächst, als würde der Roboter gefahren.
3. Kartiermodus beenden oder **STOPP** drücken.
4. Im Tab **Karte** die Karte speichern und Räume einzeichnen.

Der Mock lässt sich über einen zweiten Port steuern, um Sonderfälle zu prüfen:

| Adresse | Wirkung |
| --- | --- |
| `http://127.0.0.1:9091/controller-disconnect` | Controller getrennt |
| `http://127.0.0.1:9091/controller-connect` | Controller wieder verbunden |
| `http://127.0.0.1:9091/controller-idle` | Controller wird nicht benutzt; das automatische Ende zählt herunter |
| `http://127.0.0.1:9091/controller-drive` | Controller wird wieder benutzt |
| `http://127.0.0.1:9091/mapping-timeout?seconds=20` | Automatisches Ende nach 20 Sekunden |
| `http://127.0.0.1:9091/mapping-block?reason=not_ready` | Einschalten wird abgelehnt |
| `http://127.0.0.1:9091/mapping-unblock` | Einschalten wieder möglich |
| `http://127.0.0.1:9091/mapping-fault` | Kartiermodus endet mit einem Fehler |
| `http://127.0.0.1:9091/pause?seconds=8` | Status bleibt aus; die App zeigt „unbekannt“ |
| `http://127.0.0.1:9091/close` | Verbindung wird getrennt |
| `http://127.0.0.1:9091/reset` | Ausgangszustand |
| `http://127.0.0.1:9091/events` | Alle empfangenen Nachrichten |

## Bedien- und Sicherheitslogik

- Die App schaltet nur frei, was der Roboter frisch bestätigt. Ein Status, der älter als 2,5 Sekunden ist, gilt als unbekannt.
- Einschalten ist nur möglich, wenn der Roboter frisch „aus“ meldet und keinen Hinderungsgrund nennt.
- Der Stopp-Knopf ist verfügbar, sobald die Verbindung steht und der Kartiermodus aktiv oder unbekannt ist. Die App wiederholt den Stopp, bis der Roboter „aus“ bestätigt, höchstens vier Sekunden lang. Danach meldet sie, dass die Bestätigung fehlt.
- Die Karte lässt sich nur speichern, solange der Roboter frisch „aus“ meldet.
- Räume lassen sich nur bearbeiten, wenn Live-Karte, Kartenspeicher und Raumverwaltung denselben Fingerabdruck der Karte melden.
- Unbeantwortete Befehle werden gemeldet und nicht automatisch wiederholt. Einzige Ausnahme ist der Stopp.
- Karte und Steuerung laufen über zwei getrennte Verbindungen. Eine große Karte kann einen Stopp nicht aufhalten.
- iOS hält die Verbindung im Hintergrund oder bei gesperrtem Bildschirm nicht zuverlässig. Die App ist deshalb nie Teil der Sicherheitskette. Der Stopp in der App ist kein Not-Aus.

## Tests

Die Tests für Protokoll, Bedienregeln und Kartengeometrie laufen ohne Xcode und ohne Simulator, auf macOS und auf Linux:

```bash
swift test --package-path ios/HomeMy
```

Unter Linux ersetzt `Tools/LinuxShims/CryptoKit` Apples CryptoKit durch eine kleine SHA-256-Umsetzung. Die App selbst verwendet immer das CryptoKit des Systems.

Die Tests des Mocks, einschließlich eines Ablaufs über eine echte WebSocket-Verbindung:

```bash
python3 -m unittest discover -s ios/HomeMy/Tools -p 'test_mock_rosbridge.py' -v
```

Ein unsignierter App-Build für den Simulator:

```bash
xcodebuild \
  -project ios/HomeMy/HomeMy.xcodeproj \
  -scheme HomeMy \
  -configuration Debug \
  -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO \
  build
```

Alle drei Prüfungen laufen auch in GitHub Actions (`.github/workflows/app-checks.yml`).

## Was aus der Amadeus-App wurde

| Teil | HomeMy |
| --- | --- |
| Verbindung, Wiederverbinden, Log | übernommen |
| Kartenansicht, Karte speichern, Raumeditor | übernommen; Topics umbenannt, Speichern an den Kartiermodus gebunden |
| Kartiermodus ein/aus, Controller-Status, automatisches Ende | neu |
| Software-NOT-AUS mit Freigabe | ersetzt durch den Stopp-Knopf |
| Missionen (Raum, Greifen, Bringen), Erkunden, KI-Anzeige | entfernt |
| Entwickler-Team, Bundle-ID, Standard-Hostname | entfernt und durch neutrale Platzhalter ersetzt |
