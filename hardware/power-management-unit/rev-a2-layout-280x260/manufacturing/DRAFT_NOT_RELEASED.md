# DRAFT / NOT RELEASED – PMU A2 280 × 260 mm

**NICHT BESTELLBAR. Keine Fertigungs-, Bestückungs-, Bestromungs- oder Produktionsfreigabe.** Alle nativen CAD-Prüfungen sind fehlerfrei; grafische Abschlusskontrolle, unabhängige Prüfung und physische Qualifikation bleiben offen. Siehe [FINAL_REPORT.md](../FINAL_REPORT.md) und [release-status.json](../release-status.json).

[DRAFT_NOT_RELEASED/DRAFT_MANIFEST.json](DRAFT_NOT_RELEASED/DRAFT_MANIFEST.json) bindet Gerber, Bohrungen und Bestückungspositionen sowie die lokale BOM über SHA-256 an die geprüfte PCB `2742638d03b884b8b6ac7bf7064ef98b2bd6c5a95377b7617b72999eb2e83bc2`. Alle drei nativen Exportprozesse endeten regulär mit Exit 0 und veränderten die Platine nicht.

- Elf Gerber-Dateien: vier Kupferlagen, beidseitig Lötstopp, Paste und Bestückungsdruck sowie Edge.Cuts. Native X2-Attribute und Jobdatei sind erhalten.
- **Fertiges Fräsprofil exakt 280 × 260 mm entlang der Edge.Cuts-Mittellinien.** Die native Jobangabe 280,05 × 260,05 mm umfasst die 0,05-mm-Zeichenstrichbreite und ist kein Fertigmaß.
- Getrennte Excellon-PTH/NPTH-Dateien: 1950 metallisierte und vier unmetallisierte Bohrungen; alle 48 Press-fit-Bohrungen bleiben **1,475 mm fertig**. Der Rohbohrer 1,60 mm ist eine separat freizugebende Prozessanforderung und darf nicht anstelle der fertigen Lochgröße in diese Dateien eingesetzt werden.
- 327 SMD-Positionen, beide Seiten, mm, absoluter Ursprung. X nach rechts, exportiertes Y negativ zur nach unten laufenden nativen PCB-Y-Achse, KiCad-Winkel. DNP und nativ aus Positionsdateien ausgeschlossene Footprints sind ausgelassen. THT-/Press-fit-/Busbar-Arbeiten stehen in BOM und Schnittstelle.
- Die lokale BOM enthält unveränderte Rev-A-Bauteilwerte und DNP: 356 Einkaufspositionen, 352 bestückt, vier DNP, 124 gruppierte Zeilen und 31 externe Zeilen. `REV_A_BOM_MANIFEST.json` dokumentiert den ursprünglichen Generator, die begrenzten Pfad-/Statusanpassungen und sämtliche Ein-/Ausgabehashes.

`busbar-pcb-interface.json` beschreibt die aktuelle A2-Geometrie. Historische `../rev-a/`-Verweise liefern Bauteil-, Material- und Montagequellen; deren frühere Platinenabmessungen und Positionen gelten nicht für A2. Der Dateiname `REV_A_BOM` bleibt wegen der unveränderten elektrischen Quelle erhalten.

Vier Kupferlagen mit 70/35/35/70 µm, ENIG und die unveränderten Spezifikationen aus [PCB_STACKUP_PRESSFIT.md](../../rev-a/manufacturing/PCB_STACKUP_PRESSFIT.md) gelten zusammen mit den vollständigen KiCad-Regeln. Der generische Gerber-Job-Regelauszug ersetzt keine Hochstrom- oder netzspezifische Regel. Fertiger Lochdurchmesser, Rohbohrer, Metallisierung, Laminat und Pressverfahren müssen gemeinsam vom Lieferanten angenommen werden. Die endgültige Produktionsqualifikation ist in [production-readiness.json](../reports/production-readiness.json) weiterhin offen.
