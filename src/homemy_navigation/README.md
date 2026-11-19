# homemy_navigation

Standort und Wegplanung von HomeMy.

**Stand:** slam_toolbox für die Kartierfahrt ist eingerichtet und in der Simulation geprüft. Am Roboter nie gelaufen.

## Kartieren mit slam_toolbox

`launch/slam.launch.py` startet slam_toolbox (online, asynchron) mit `config/slam_toolbox.yaml` und schaltet den Lifecycle-Knoten auf aktiv. Ob er misst, entscheidet der Koordinator in `homemy_mapping_mode`: nur während des Kartiermodus.

Ausgangspunkt der Einstellungen ist Amadeus (`src/amadeus_lidar_bringup/config/slam_toolbox_amadeus.yaml`, Commit `05439c7`). Übernommen sind die strengeren Schwellen für Schleifenschlüsse, mit denen der Amadeus-Prüfstand falsche Schleifenschlüsse abstellte. Neu für HomeMy:

- Eingang ist `/scan_masked`, in dem die blinden Sektoren NaN sind;
- `base_link` liegt auf der Antriebsachse;
- 5 cm Raster in der Simulation, bei Amadeus waren es 3 cm.

Die Werte für den echten Roboter sind Ergebnisse der Inbetriebnahme. Ob HomeMy auf Fliesenfugen eine Scan-Sperre im Stillstand braucht wie auf dem Amadeus-Branch `feature/stationary-scan-gate`, wird am gebauten Fahrgestell gemessen.
