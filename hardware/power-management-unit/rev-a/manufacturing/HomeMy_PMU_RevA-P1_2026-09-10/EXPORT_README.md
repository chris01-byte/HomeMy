# RevA-P1 native PCB export

Engineering prototype – not production qualified.

These files are native KiCad exports of the board identified by SHA-256 in EXPORT_MANIFEST.json. They do not certify that the board is routed, DRC-clean, thermally qualified or safe to energize. `rev_a_engineering_prototype: true`; `rev_b_production: false`.

Gerbers contain the four actual copper layers, both masks, both silkscreens, both paste layers and Edge.Cuts. Excellon holes are metric, decimal, unmirrored, absolute board origin (0,0), with PTH/NPTH in separate files. KiCad converts its screen-coordinate Y direction in its native Gerber/Excellon writer. No holes, copper, zones, apertures or drill tolerances are invented by this exporter. The Gerber job describes the loaded board stack.

Placement CSVs use the KiCad footprint anchor, millimetres, absolute board origin, X right and Y down. Rotation is GetOrientationDegrees() from the loaded footprint; bottom placements remain in the same unmirrored board coordinates. The assembler must translate origin, rotation-zero, handedness and body centroid for its own equipment before use. SMD/manual subsets partition all populated purchased BOM references; DNP positions and PCB features are separate review lists. Press-fit terminals are manual through-hole operations, not reflow placements.

All required layer files are present even when a layer intentionally has no image primitives. Coverage validation means files/BOM/board identities reconcile; it is independent of manufacturing release. Review errors and board_state in EXPORT_MANIFEST.json. The copied BOM includes external parts and unselected hardware; stock is unverified. Only the output paths listed in the manifest belong to this export. Re-run build_bom.py after final source/CAD generation, then run this script with KiCad Python through scripts/run_tool.py. The exporter never saves the source board.
