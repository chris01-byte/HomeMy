# PMU Rev A2 – 280 × 260 mm (aktuelle Leiterplatte)

**CAD vollständig – Entwurf – nicht bestellbar.** Maßgeblicher Status: [release-status.json](release-status.json); alle Freigaben sind `false`.

- KiCad-Projekt (KiCad 10): `kicad/HomeMy_PMU_RevA.kicad_pro`, Schaltplan mit 15 Unterblättern, vierlagige Leiterplatte 70/35/35/70 µm, 425 Footprints.
- PCB-SHA-256: `2742638d03b884b8b6ac7bf7064ef98b2bd6c5a95377b7617b72999eb2e83bc2`.
- Stückliste und Fertigungsentwurf: `manufacturing/` (Entwurf, siehe [DRAFT_NOT_RELEASED.md](manufacturing/DRAFT_NOT_RELEASED.md)).
- Abschlussbericht des Layouts: [FINAL_REPORT.md](FINAL_REPORT.md).
- Schaltungsauslegung, Berechnungen und Datenblätter: [`../rev-a/`](../rev-a/README.md).

## Offene Befunde

Die Gegenprüfung vom 2026-11-16 hat 25 Befunde ergeben (GP-01 bis GP-25) und empfiehlt, diesen Stand **nicht zu bestellen**: [`../reviews/2026-11-16-rev-a2-gegenpruefung/`](../reviews/2026-11-16-rev-a2-gegenpruefung/README.md). Die wichtigsten: Anbindung der Schutzdioden (GP-01), einzige Masseverbindung NT9 (GP-02), Fremdnetz-Vias unter den Kupferschienen (GP-03), Einschaltstrom des Motion-Gates (GP-04), Überspannungsschwelle der eFuses (GP-05).

## Hinweise zu den Nachweisen

- Die Dateien unter `reports/` sind Momentaufnahmen des Commits `d37c7f7` und wurden beim Aufräumen nicht verändert. Hashes und Pfade darin beziehen sich auf diesen Commit. Dort genannte Vergleichsdateien der früheren 360 × 300-Platine (`../rev-a/kicad/` und weitere) wurden am 2026-11-16 entfernt und sind in der Git-Historie abrufbar.
- „247/247" und „46/46" sind reine Verbindungsprüfungen ohne Breiten-, Strom- oder Temperaturkriterium (Befund GP-22).
- Einige Berichte enthalten absolute Pfade des erzeugenden Rechners (Befund GP-25).
- Schriftfeld und Bestückungsdruck der Leiterplatte tragen Entwurfsvermerke. Jede Freigabe erfordert eine PCB-Änderung, damit einen neuen Hash und neue Nachweise.
- Für die Kupferschienen und Sternbrücken gibt es für A2 nur `manufacturing/busbar-pcb-interface.json`, keine Zeichnungen (Befund GP-24). Die Gegenprüfung empfiehlt, die Schienen zu streichen (GP-03).

## Prüfungen wiederholen

```bash
cd ../reviews/2026-11-16-rev-a2-gegenpruefung/werkzeuge
```

```bash
/usr/bin/python3 drc_experiments.py
```

```bash
/usr/bin/python3 pcb_checks.py
```
