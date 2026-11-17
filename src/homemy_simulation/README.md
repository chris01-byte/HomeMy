# homemy_simulation

Ersatzteile für die Simulation. **Nie auf dem Roboter starten.** Jeder Knoten meldet beim Start eine Warnung, dass er simuliert.

| Knoten | Ersetzt | Verhalten |
| --- | --- | --- |
| `synthetic_map` | SLAM | Veröffentlicht `/map` erst nach dem ersten Einschalten des Kartiermodus. Jede neue Kartierfahrt beginnt klein und mit neuem Fingerabdruck. Solange der Controller „fährt“, wird jede Sekunde mehr von der Testwohnung sichtbar. Nach der Fahrt bleibt die letzte Karte veröffentlicht. |
| `sim_controller` | Funk-Controller und `joy_node` | Sendet `/joy` mit 20 Hz. Bei `driving` meldet das Steuerkreuz „vorwärts“ (Achse 7, wie beim DualShock von Amadeus). |
| `lifecycle_stub` | Lebenszyklus-Manager | Sendet den Zustand, Standard `READY`, latched und jede Sekunde. |

Die Testwohnung ist dieselbe wie im Mock der App: 48 × 36 Zellen zu 10 cm. Sie ist erfunden und keine echte Wohnung.

## Zur Laufzeit umschalten

```bash
ros2 param set /homemy_sim_controller driving false
ros2 param set /homemy_sim_controller connected false
ros2 param set /homemy_lifecycle_stub state FAULT
```

Gestartet werden die Knoten über `homemy_bringup/launch/app_sim.launch.py`.
