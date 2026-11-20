# homemy_boot_manager

Hier entsteht später das Programm, das den Gesamtzustand des Roboters festlegt: startet, Selbsttest, bereit, eingeschränkt bereit, in Betrieb, Fehler, fährt herunter (`contracts/ros/system-lifecycle.md`). Es braucht die PMU.

**Solange die PMU fehlt, enthält das Paket nur eine Überbrückung** (Entscheidung des Projektinhabers vom 19.11.2026).

## `lifecycle_bridge`

Der Knoten meldet zwei feste Werte, auf die der Rest der Software wartet:

| Topic | Wert | Wer wartet darauf |
| --- | --- | --- |
| `/homemy/lifecycle/state` | `READY` | Kartiermodus, Bewegungsfreigabe, Auftragssteuerung |
| `/homemy/safety/estop` | `false`, also „Not-Halt nicht gedrückt“ | Bewegungsfreigabe |

Er prüft nichts: kein Selbsttest, keine Batterie, keine Hardware. Ohne PMU bekommt die Software auch kein Not-Halt-Signal. **Den Prototyp sichert ein externer, hardwareseitig eingebauter Not-Halt-Schalter** (Entscheidung des Projektinhabers vom 20.11.2026). Er wirkt ohne Software; die Software liest ihn nicht.

Fällt die Überbrückung aus, schließt die Bewegungsfreigabe von selbst, weil beide Werte veralten.

Von Hand lässt sich alles sperren oder ein Fehler nachstellen:

```bash
ros2 param set /lifecycle_bridge state FAULT
```

```bash
ros2 param set /lifecycle_bridge estop_pressed true
```

Derselbe Knoten läuft in der Simulation und später am Laborroboter:

```bash
ros2 launch homemy_boot_manager lifecycle_bridge.launch.py
```

## Rückbau

Sobald die PMU den Zustand und das Not-Halt-Signal liefert, entfällt die Überbrückung. Wird sie aus dem Start entfernt, ohne dass ein Ersatz läuft, bleibt die Bewegungsfreigabe geschlossen.
