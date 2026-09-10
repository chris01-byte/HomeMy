# Fab assembly annotation review

`rev_a_engineering_prototype: true`  
`rev_b_production: false`

The helper has now been applied to the stable main PCB and all four matching vendored library files, as recorded in [the application report](../reports/assembly-annotation-application.json). This read-only review verified that the current board hash exactly matches that report and the [final placement review](placement-access-review.json). Reapplying the pure annotation function would change neither the board nor any of the four libraries. The 19 affected footprints retain every pad, copper object, courtyard, position, existing UUID, and route. A structural comparison excludes only F.Fab graphic primitives, then requires all remaining s-expression data to match exactly. Every old UUID must remain, and duplicate UUIDs are rejected. Reapplying the helper produces no board changes.

| Target | Local F.Fab edits |
|---|---|
| Q1–Q10, CCPAK1212 | Replace the pad-envelope Fab rectangle with the 12×9.4 mm molded body, corners (−6,−4.7)/(6,4.7). Add pin-1 circle at (−5.3,4.05), gate/source/drain labels. Text rotates with each native footprint. |
| U1, LM74930 | Body rectangle (−2,−2)/(2,2); pin-1 diagonal (−1.95,−1.2) to (−1.2,−1.95), label 1, and internal “EP25 FLOAT / NO VIA” note. EP copper is untouched. |
| RSH1/RSH2, CSS4J | “SENSE 2 / 3” at (0,−1.2); separate left/right guides along y=−2.6 and x=±2.75, corresponding to the smaller north/−Y sense lands. “1 FORCE”/“4 FORCE” labels at (±3,1). |
| J1–J6, Würth M5 | Same generic local ±Y screw-axis graphic in library and embedded footprints. Board-only F.Fab flange/face arrows specify J1/J2/J3/J5 toward −Y, J4/J6 toward +Y. No terminal footprint rotates. |

The M5 board arrows run from 4.5 to 10 mm beyond the terminal center in the specified direction. A flange line spans x±3 mm at y±4.5 mm; labels sit at y±11.8 mm. They are orientation instructions, not proof of the three-dimensional screw/tool envelope. Manufacturer and mechanical basis remain in `manufacturing/assembly-orientation.json`, `CONNECTOR_ASSEMBLY.md`, and their source drawings.

During development, native KiCad 10.0.6 loaded and plotted an edited temporary board. That historical test report contains **zero geometric/library violations** and **325 unconnected items in its earlier routing-work snapshot**. Those unconnected counts do not describe the final main board; the historical native report is retained only as evidence for the annotation implementation. Final routing/ERC/DRC approval remains in the release checks. The CLI returned code 1 after denied Windows registry access; the saved native report and exported SVG were inspected independently. The retained four-panel native development Fab crop confirms readable pin-1/EP/sense/face markers without their earlier text overlaps.

The modified footprint generator produced all four annotated library definitions identically to applying the helper to fresh authoritative library copies (s-expression equality). Its existing pin audit passed all 421 footprints. The library and embedded-board additions use the same local geometry; UUID ownership differs deliberately per board instance.

## API and handoff

`scripts/annotate_assembly.py` depends only on Python's standard library and `scripts/sexpr.py`:

- `annotate_footprint_text(text, identifier=None) -> (text, summary)` is pure and is now called by `build_footprints.write_custom`.
- `annotate_board_text(text) -> (text, summary)` is pure, including per-reference M5 face graphics.
- `annotate_libraries(library_root) -> summaries` updates only the four target vendored files supplied by the caller.

The following is the repeatable post-build application command; its completed main-board run is linked above:

```powershell
python scripts/annotate_assembly.py --board kicad/HomeMy_PMU_RevA.kicad_pcb --in-place --library-root kicad/libraries --report reports/assembly-annotation-application.json
```

For isolated use, replace `--in-place` with `--output TEMP_BOARD` and supply copied libraries. The CLI checks preservation and idempotence before writing its board output. Subsequent generation of custom libraries preserves the new generic markers; run the annotation CLI after board creation to reproduce board-specific M5 face notes.

Evidence: [machine results](assembly-annotation-review.json), [native DRC snapshot](assembly-annotation-drc.json), and [native Fab detail crop](assembly-annotation-fab.png). End-to-end routing, torque/tool clearance, energization, and Rev B measurements remain outside this graphical change.
