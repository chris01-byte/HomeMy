# DRAFT / NOT RELEASED – PMU A2 280 × 260 mm

**WIP – NICHT BESTELLBAR.** Diese Dateien sind ein BOM-/Schnittstellen-Prüfsatz, keine Fertigungs- oder Bestellfreigabe. Drei Verbindungen und weitere DRC-/Montagebefunde bleiben offen; siehe [FINAL_REPORT.md](../FINAL_REPORT.md).

Die elektronischen Rev-A-Werte und DNP bleiben unverändert. `busbar-pcb-interface.json` beschreibt die aktuelle A2-Geometrie. Historische `../rev-a/`-Verweise liefern Material-, Bauteil- und Montagequellen; deren frühere Platinenpositionen gelten nicht für A2. Der Dateiname `REV_A_BOM` bleibt wegen des unveränderten elektrischen Quellenaudits erhalten.

Die lokale Stückliste wurde mit dem ursprünglichen BOM-Generator und dokumentierten Pfad-/Statusanpassungen erstellt. `REV_A_BOM_MANIFEST.json` enthält Quellen, Eingabe-/Ausgabehashes und Anpassungsbelege. Externe Dokumentpfade wurden auf `../rev-a/` qualifiziert; für NB-Brücken und Rückseiten-Unterlegscheiben verweist der Zusatztext ausdrücklich auf die aktuelle lokale Schnittstelle.

Es liegen keine Gerber-, Bohr- oder Pick-and-Place-Freigabedaten vor. Maßgeblich sind ausschließlich die durchgehend falschen Flags in [release-status.json](../release-status.json).
