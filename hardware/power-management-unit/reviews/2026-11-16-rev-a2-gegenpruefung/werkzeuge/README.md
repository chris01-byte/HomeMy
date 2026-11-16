# Prüfskripte der Gegenprüfung

Voraussetzung: KiCad 10 (`kicad-cli` und das Python-Modul `pcbnew`). Unter Linux hat meist `/usr/bin/python3` das Modul. Alle Skripte lesen die A2-Leiterplatte unter `../../../rev-a2-layout-280x260/kicad/`; Experimente arbeiten auf einer temporären Kopie. Mit `PMU_PCB=<pfad>` lässt sich eine andere `.kicad_pcb` prüfen, mit `PMU_OUT=<verzeichnis>` ein anderes Ausgabeverzeichnis wählen (Standard `../daten`).

| Aufruf | Ergebnis |
|---|---|
| `/usr/bin/python3 drc_experiments.py native` | ERC, DRC, DRC mit neu gefüllten Zonen → `daten/native_checks.json` |
| `/usr/bin/python3 drc_experiments.py hv` | Abstände 42-V-Netze zu allen anderen unter 0,6 mm → `daten/hv_clearance.json` |
| `/usr/bin/python3 drc_experiments.py power` | Was nur an dünnen Leiterbahnen hängt → `daten/power_continuity.json` |
| `/usr/bin/python3 pcb_checks.py` | Anbindung D1/D2, Ausnahmegruppen, NT9, Querschnitte, Vias unter Schienen, Padabstände, Antenne → `daten/pcb_checks.json` |
| `python3 netlist_tools.py` | Netzliste je Schaltplanblatt, alle Netze, Massebrücken → `daten/netzliste/` |
| `python3 inrush_sim.py` | Einschaltsimulation Motion-Gate gegen SOA → `daten/inrush_sim.json` |
| `node svg2png.cjs <svg> <png> <breite> [x,y,b,h]` | Lagenbild aus `kicad-cli pcb export svg` rastern (braucht Playwright) |

Nach einer Layoutänderung dieselben Aufrufe wiederholen und die Ergebnisse mit `daten/` vergleichen. Die Zahlen in `BEFUNDE.md` stammen aus genau diesen Läufen am 2026-11-16 mit KiCad 10.0.8.

`teilpruefungen/` enthält die Skripte der drei Teilprüfungen so, wie sie gelaufen sind. Sie verweisen mit `<SITZUNG>` auf Verzeichnisse der damaligen Prüfsitzung und laufen erst nach Anpassen dieser Pfade. Ihre Ergebnisse stehen in `../teilberichte/`.
