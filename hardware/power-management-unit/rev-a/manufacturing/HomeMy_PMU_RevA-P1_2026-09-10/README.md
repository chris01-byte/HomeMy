# HomeMy PMU RevA-P1 — prototype order package

**Engineering prototype – not production qualified**

This version is orderable as a **bare PCB or populated PCB engineering prototype**
to the enclosed requirements. `fabrication_release` and `assembly_release`
apply only to that scope. Production, a validated 50 A operating rating,
firmware, external system integration and permission to energize are excluded.
No physical board has been ordered, built or tested by this release process.

Package version: RevA-P1, dated 2026-09-10. PCB SHA-256: `13fcae0f58c9a6ac5f85eb721c24b44169a65f628baad6586bcd6002f4c17cfe`.
Use PACKAGE_MANIFEST.json and SHA256SUMS.txt to verify this exact delivery.
Source release: RELEASE.json. An altered file invalidates this version.
Further source references in copied documents use immutable repository links;
internet access is required for those supporting references. Manufacturing
drawings and order data are enclosed locally.

| Delivery | Files |
|---|---|
| Bare PCB | gerbers/: 11 X2 layers + job; drill/: separate PTH/NPTH Excellon + maps |
| Complete PCB BOM | bom/REV_A_BOM.csv + JSON; 356 positions, 352 populated, 4 DNP |
| Placement | assembly/: all, SMD and manual positions; units/origin/rotation in EXPORT_README.md |
| DNP | assembly/DNP.md and separate DNP position file |
| Stackup and bores | fabrication/PCB_STACKUP_PRESSFIT.md, PRESSFIT_HOLES.csv (48 holes), FABRICATION_NOTES.md |
| Copper hardware | mechanical/: BB1-BB7 drawings, combined 1:1 drawing, BUSBAR_DIMENSIONS.json, clamp BOM and build sequence |
| Assembly and polarity | assembly/: front/back Fab drawings, ASSEMBLY_ORIENTATION.svg, POLARITY.svg and connector pinout |
| Open external positions | integration/OPEN_ORDER_ITEMS.md: 0 before PCB order; 9 before energization |
| Verification | evidence/: native ERC/DRC, process exits/hashes, exact parity and high-current/neck review |

## Order and assembly conditions

The supplier must accept the specified finished press-fit holes and plating,
1.60-1.70 mm board thickness, finished 70/35/35/70 um copper, laminate and ENIG.
Order representative process coupons with the prototype; confirm their
quantity and insertion/clamp process in the quote. If these requirements cannot
be met, stop and revise the design/package; do not substitute a standard stackup.

The BOM quantities cover one PCB without placement waste or spares. Stocks are
unverified. Use exact selected PCB parts and only explicitly approved packaging
aliases. Pick-and-place coordinates are footprint anchors in the top-view
board frame; the assembler maps its machine origin, centroid and rotation.
Manual/THT and press-fit operations are separate. Complete soldering and
cleaning before pressing J1-J6; do not reflow the press-fit connections.

Seven underside busbars, eight top star bridges, contact shims and specified
insulation/clamp hardware are required for the designed high-current assembly.
They must never bypass shunts or FET banks. External fuse, converters, cables,
lugs, support/guards and permission circuit may be finalized later only within
the frozen interfaces. All nine external integration items and the staged
bring-up gates must be closed before their respective powered use.

## Recorded final native checks

Both checks used all severities; DRC used all-track-errors and full schematic
parity. Zero findings, zero open connections and zero parity differences.
Processes ended normally in the user's installed KiCad 10.0.6 session:

- ERC: exit 0, SHA-256 `38a01195bd9bfedae926026ad02f03b66581b02f8acda143ae8389dbc3256a1c`.
- DRC: exit 0, SHA-256 `41209f2f29faef8b89e8dab513edf4540d547d1aa666cb81b91bd1e35df13c75`.

The old timeout-124 reports remain historical evidence in the source repository.
Their status is not reused as a passing result. The separate geometric audits
and 247 power-pad paths do not replace current-sharing, contact, thermal, SOA,
transient or real press-fit measurements. See integration/REV_B_VALIDATION.md.
