# HomeMy – App für iPhone

Native SwiftUI-App für HomeMy. Sie schaltet den Kartiermodus, zeigt die Karte, speichert sie, verwaltet die Räume und schickt den Roboter in einen Raum. Die Schnittstelle zum Roboter steht in [`contracts/api/app-bridge.md`](../../contracts/api/app-bridge.md).

Die App beruht auf der Amadeus-App (`ios/Robotersteuerung` in roboter_ws, Commit `05439c7`).

**Stand:** Die App ist gegen den mitgelieferten Mock und gegen die Roboterseite in der Simulation getestet. Am echten Roboter lief sie noch nie.

## Was die App kann

- Verbindung zum Roboter über rosbridge (WebSocket).
- Kartiermodus ein- und ausschalten. Gefahren wird danach mit dem Controller am Roboter, nicht mit der App.
- Stopp-Knopf: hält den Roboter an, beendet den Kartiermodus und bricht einen laufenden Auftrag ab.
- Anzeige: Controller verbunden oder nicht, Zeit bis zum automatischen Ende, Grund des letzten Endes.
- Live-Karte mit Zoom, Verschieben und Drehen.
- Karte speichern, sobald der Kartiermodus beendet ist.
- Räume als Flächen einzeichnen, benennen, optional mit Fahrziel und Blickrichtung, und wieder löschen.
- Zu einem Raum fahren lassen: „Hinfahren“ am gewählten Raum mit Fahrziel. Die Auftragskarte im Tab **Roboter** zeigt Ziel, Fortschritt und Ergebnis und bietet „Auftrag abbrechen“. Ist eine Fahrt nicht möglich, nennt sie den Grund, zum Beispiel dass der Roboter seine Position in der Karte noch sucht.

## Was die App nicht kann

- Sie sendet keine Fahrbefehle. Eine Fahrt ist ein Auftrag an den Roboter; ob er fährt, entscheidet seine Bewegungsfreigabe.
- Eine zweite Karte speichern, nachdem schon Räume zu einer Karte gehören.
- Die Roboterposition auf der Karte anzeigen.
- Den Controller koppeln.
- Zugriffsschutz: Die Verbindung ist unverschlüsselt und ohne Anmeldung. Nur in einem vertrauenswürdigen Labornetz verwenden.

## Voraussetzungen

- iPhone mit iOS 16 oder neuer.
- Xcode auf einem Mac.
- iPhone und Roboter (oder der Mock) im selben WLAN.

## Auf dem iPhone installieren

Das geht nur mit Xcode auf einem Mac. Das iPhone ist per Kabel verbunden, und der Entwicklermodus ist eingeschaltet (Einstellungen → Datenschutz & Sicherheit → Entwicklermodus).

1. Den Stand mit der App auf den Mac holen. Solange er nicht auf `main` liegt, ist das der Arbeits-Branch:

   ```bash
   git clone https://github.com/chris01-byte/HomeMy.git
   ```

   ```bash
   cd HomeMy && git checkout claude/eager-shannon-yfyfpf
   ```

   Ist das Repository schon da, genügt im Ordner `HomeMy`:

   ```bash
   git fetch origin && git checkout claude/eager-shannon-yfyfpf && git pull
   ```

2. Einmalig die eigene Signatur eintragen. Dazu die Vorlage kopieren:

   ```bash
   cp ios/HomeMy/Config/Local.xcconfig.example ios/HomeMy/Config/Local.xcconfig
   ```

   In `Local.xcconfig` zwei Werte eintragen:
   - `DEVELOPMENT_TEAM`: die zehnstellige Team-ID des eigenen Apple-Kontos. Es ist dieselbe wie bei der Amadeus-App. Aus deren Projekt lässt sie sich auslesen (Pfad anpassen):

     ```bash
     grep -m1 -o 'DEVELOPMENT_TEAM = [A-Z0-9]*' ~/Roboter_ws/ios/Robotersteuerung/Robotersteuerung.xcodeproj/project.pbxproj
     ```

   - `PRODUCT_BUNDLE_IDENTIFIER`: eine eigene, eindeutige Kennung, zum Beispiel `de.deinname.HomeMy`.

   Die Datei bleibt auf dem Mac; Git ignoriert sie. Spätere Updates aus dem Repository überschreiben sie nicht.

3. `ios/HomeMy/HomeMy.xcodeproj` in Xcode öffnen, oben das iPhone als Ziel wählen und **Run** (▶) drücken.
4. Beim ersten Start am iPhone, falls verlangt, dem Entwickler vertrauen (Einstellungen → Allgemein → VPN & Geräteverwaltung) und den Dialog für das lokale Netzwerk mit **Erlauben** bestätigen.
5. In der App die Adresse der Gegenstelle eintragen (siehe unten).

Wer lieber klickt: Statt Schritt 2 lässt sich das Team auch in Xcode wählen (Target **HomeMy** → **Signing & Capabilities** → **Team**). Das ändert aber die Projektdatei auf dem Mac und kann sich mit späteren Updates beißen.

Mit einem kostenlosen Apple-Konto läuft die App sieben Tage und muss dann mit **Run** neu aufgespielt werden.

Die zuletzt erfolgreich verwendete Adresse wird nur lokal in den App-Einstellungen gespeichert.

## Mit dem iPhone testen, ohne Roboter

Der Mock läuft auf dem Mac und braucht nur Python 3. Mac und iPhone sind im selben WLAN.

```bash
python3 ios/HomeMy/Tools/mock_rosbridge.py --host 0.0.0.0
```

Die Adresse des Mac im WLAN:

```bash
ipconfig getifaddr en0
```

In der App dann `ws://<Adresse des Mac>:9090/` eintragen, zum Beispiel `ws://192.168.1.23:9090/`. Fragt die Firewall des Mac, ob Python Verbindungen annehmen darf: erlauben. Der Ablauf zum Durchspielen steht unter „Ohne ROS ausprobieren“.

## Gegen die Roboterseite in der Simulation

Die echte Roboterseite läuft ohne Hardware mit ROS 2 Jazzy (siehe `src/homemy_bringup/README.md`):

```bash
ros2 launch homemy_bringup app_sim.launch.py
```

Danach in der App `ws://127.0.0.1:9090/` eintragen. Der Ablauf ist derselbe wie beim Mock unten.

## Ohne ROS ausprobieren

Der Mock braucht weder ROS noch zusätzliche Python-Pakete und verwendet nur künstliche Daten.

```bash
python3 Tools/mock_rosbridge.py
```

Danach die App im iOS-Simulator starten und `ws://127.0.0.1:9090/` eintragen.

Ablauf zum Durchspielen:

1. Im Tab **Kartieren** den Kartiermodus einschalten.
2. In den Tab **Karte** wechseln: Die Testwohnung wächst, als würde der Roboter gefahren.
3. Kartiermodus beenden oder **STOPP** drücken.
4. Im Tab **Karte** die Karte speichern und Räume mit Fahrziel einzeichnen.
5. Einen Raum wählen und **Hinfahren** drücken. Der Mock meldet zwölf Sekunden lang die Fahrt und dann „erreicht“.

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
| `http://127.0.0.1:9091/mission-block?reason=not_localized` | „Hinfahren“ wird abgelehnt, mit Grund |
| `http://127.0.0.1:9091/mission-unblock` | „Hinfahren“ wieder möglich |
| `http://127.0.0.1:9091/mission-fail` | Der laufende Auftrag scheitert |
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

`HomeMyTests/BackendFixtureTests.swift` liest Antworten, die die Ende-zu-Ende-Tests von der echten Roboterseite aufgezeichnet haben (`HomeMyTests/Fixtures/backend/`). Damit ist geprüft, dass die App diese Antworten versteht, denselben Karten-Fingerabdruck berechnet, die Raumbearbeitung freigibt und die Auftragsmeldungen richtig deutet: angenommen, unterwegs, erreicht, abgebrochen, abgelehnt mit Grund.

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
| Missionen: Raum anfahren | neu gebaut nach dem HomeMy-Vertrag, mit Abbrechen und Gründen für Ablehnungen |
| Missionen Greifen und Bringen, Erkunden, KI-Anzeige | entfernt |
| Entwickler-Team, Bundle-ID, Standard-Hostname | entfernt und durch neutrale Platzhalter ersetzt |
