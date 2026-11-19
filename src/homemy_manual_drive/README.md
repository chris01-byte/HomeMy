# homemy_manual_drive

Fahren mit dem Funk-Controller DualShock 4 (CUH-ZCT2E) beim Kartieren. Der Vertrag steht in [`contracts/hardware/manual-drive.md`](../../contracts/hardware/manual-drive.md).

**Stand:** in der Simulation getestet. An HomeMy nie gelaufen; bei Amadeus fuhr der Projektinhaber mit demselben Controller und derselben Belegung.

## Gedrückt fährt, losgelassen steht

So einfach wie bei Amadeus (Entscheidung des Projektinhabers vom 19.11.2026, für den ersten Prototyp und das Testlabor): Steuerkreuz drücken fährt, loslassen hält an. Eine eigene Überwachung der Funkverbindung gibt es nicht.

Der Roboter hält auch an, wenn keine Controller-Nachrichten mehr kommen: Dann ist der letzte Befehl nach 0,25 s veraltet, und die Bewegungsfreigabe sendet null.

Bewusst in Kauf genommen: Reißt der Funk still ab, während eine Richtung gehalten wird, wiederholt der Joystick-Treiber diese Richtung, bis Linux den Controller abmeldet. So lange fährt der Roboter mit Kartiergeschwindigkeit weiter; es bleiben der Hindernisschutz, der Stopp in der App und der Halt am Roboter. Wie lange das am HomeMy-Rechner dauert, wird bei der Inbetriebnahme einmal gemessen (Schritt M2 im Vertrag).

## Controller-Profil

`launch/manual_drive.launch.py` startet `joy_node` und `teleop_twist_joy`. Die Befehle gehen an `/homemy/cmd_vel/teleop`, also an die Bewegungsfreigabe, nie direkt an den Antrieb.

| Taste | Wirkung |
| --- | --- |
| Steuerkreuz hoch/runter | vorwärts/rückwärts, 0,12 m/s |
| Steuerkreuz links/rechts | drehen, 0,40 rad/s |
| R1 gehalten | schneller: 0,20 m/s und 0,70 rad/s |

Übernommen aus Amadeus (`src/robot_bringup/config/teleop_joy.yaml`, Commit `05439c7`): Steuerkreuz statt Stick, Totzone 0,20, kein Totmann-Knopf (Entscheidung des Projektinhabers). Achsen- und Tastennummern werden in Schritt M1 am HomeMy-Rechner bestätigt.
