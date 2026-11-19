# Runbook: HomeMy-App auf das iPhone bringen

Auftrag für einen Agenten, der **auf dem Mac** des Projektinhabers läuft. Das iPhone hängt per USB am Mac.

## Ziel

Die HomeMy-App aus `ios/HomeMy/` bauen, auf dem iPhone installieren und starten. Danach den Mock starten, damit die App ohne Roboter getestet werden kann.

## Grenzen

- Kein Roboter, keine Motoren. Hier wird nur die App installiert.
- Team-ID und Bundle-ID gehören nur in `ios/HomeMy/Config/Local.xcconfig`. Die Datei wird von Git ignoriert und darf nie committet werden. Die Projektdatei `HomeMy.xcodeproj/project.pbxproj` nicht für die Signatur ändern.
- Nichts committen oder pushen.
- Unklarheiten (Team-ID, Apple-Konto, Passwörter) beim Projektinhaber erfragen, nicht raten.

## Schritte

1. **Stand holen.** Im Repository-Ordner `HomeMy`:

   ```bash
   git fetch origin && git checkout claude/eager-shannon-yfyfpf && git pull
   ```

   Gibt es das Repository noch nicht, vorher klonen: `https://github.com/chris01-byte/HomeMy.git`.

2. **Werkzeuge prüfen.** `xcodebuild -version` muss Xcode 16 oder neuer melden. `xcrun devicectl list devices` muss das iPhone als verbunden zeigen. Fehlt es, den Projektinhaber bitten:
   - das iPhone zu entsperren und „Diesem Computer vertrauen“ zu bestätigen;
   - auf dem iPhone den Entwicklermodus einzuschalten (Einstellungen → Datenschutz & Sicherheit → Entwicklermodus).

3. **Signatur eintragen.**

   ```bash
   cp ios/HomeMy/Config/Local.xcconfig.example ios/HomeMy/Config/Local.xcconfig
   ```

   Darin zwei Werte setzen:
   - `DEVELOPMENT_TEAM`: die Team-ID der Amadeus-App. Sie steht in deren Projekt (Pfad suchen, zum Beispiel unter `~/Roboter_ws`):

     ```bash
     grep -m1 -o 'DEVELOPMENT_TEAM = [A-Z0-9]*' <Pfad>/ios/Robotersteuerung/Robotersteuerung.xcodeproj/project.pbxproj
     ```

     Ist dort keine zu finden, den Projektinhaber fragen.
   - `PRODUCT_BUNDLE_IDENTIFIER`: eine eigene, eindeutige ID, zum Beispiel `de.<name>.HomeMy`, nicht `com.example.HomeMy`.

4. **Bauen.** Mit der Geräte-ID aus Schritt 2:

   ```bash
   xcodebuild -project ios/HomeMy/HomeMy.xcodeproj -scheme HomeMy -configuration Debug \
     -destination 'platform=iOS,id=<GERÄTE-ID>' -derivedDataPath build/ios \
     -allowProvisioningUpdates build
   ```

   Scheitert die Signatur, weil kein Apple-Konto in Xcode angemeldet ist, den Projektinhaber bitten, es unter Xcode → Einstellungen → Accounts anzumelden. Danach erneut bauen.

5. **Installieren und starten.**

   ```bash
   xcrun devicectl device install app --device <GERÄTE-ID> build/ios/Build/Products/Debug-iphoneos/HomeMy.app
   ```

   ```bash
   xcrun devicectl device process launch --device <GERÄTE-ID> <PRODUCT_BUNDLE_IDENTIFIER aus Schritt 3>
   ```

   Wird der Start verweigert, muss der Projektinhaber auf dem iPhone dem Entwickler vertrauen (Einstellungen → Allgemein → VPN & Geräteverwaltung) und dann erneut starten.

6. **Mock starten** (läuft weiter, bis er beendet wird):

   ```bash
   python3 ios/HomeMy/Tools/mock_rosbridge.py --host 0.0.0.0
   ```

   Die WLAN-Adresse des Mac ermitteln:

   ```bash
   ipconfig getifaddr en0
   ```

   Fragt die macOS-Firewall nach eingehenden Verbindungen für Python, muss der Projektinhaber sie erlauben.

## Ergebnis an den Projektinhaber

Kurz melden:

- ob die App auf dem iPhone installiert ist und startet;
- die Adresse für die App: `ws://<WLAN-Adresse des Mac>:9090/`;
- dass iPhone und Mac im selben WLAN sein müssen und die App beim ersten Verbinden nach dem lokalen Netzwerk fragt (**Erlauben**);
- den Ablauf zum Durchspielen aus `ios/HomeMy/README.md`, Abschnitt „Ohne ROS ausprobieren“: Kartiermodus ein, Karte wächst, beenden, Karte speichern, Raum mit Fahrziel zeichnen, „Hinfahren“.

Mit einem kostenlosen Apple-Konto läuft die App sieben Tage. Danach Schritt 4 und 5 wiederholen.

## Aufräumen

- Den Mock mit Ctrl-C beenden, wenn der Test vorbei ist.
- `build/ios` kann gelöscht werden; `build/` wird von Git ignoriert.
- `Local.xcconfig` bleibt liegen, damit spätere Updates ohne neue Signatur gebaut werden können.
