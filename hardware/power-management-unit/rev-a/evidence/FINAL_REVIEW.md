# PMU Revision A-P1 — prototype order release

`rev_a_engineering_prototype: true`  
`rev_b_production: false`  
Review date: 2026-09-10. PCB SHA-256:
`13fcae0f58c9a6ac5f85eb721c24b44169a65f628baad6586bcd6002f4c17cfe`.

**Engineering prototype – not production qualified.**

The [versioned delivery](../manufacturing/HomeMy_PMU_RevA-P1_2026-09-10/README.md)
is ready for ordering a bare or populated Rev-A engineering prototype to its
specified fabrication and assembly conditions. `fabrication_release` and
`assembly_release` apply only to that scope. No hardware has been ordered,
assembled or energized by this work. Firmware, a validated 50 A rating and
series production are outside this release.

## Final checks

| Check | Result and evidence |
| --- | --- |
| Native KiCad 10.0.6 ERC | **Exit 0; 0 findings.** [Report](../reports/erc-final.json). |
| Native DRC | **Exit 0; 0 findings, 0 open connections, 0 schematic-parity differences.** All severities, all track errors and full parity explicitly requested. [Report](../reports/drc-final.json). |
| Native process provenance | Actual CLI commands, times, report SHA-256 and current CAD input hashes in [native-checks-both.json](../reports/native-checks-both.json). Normal exits came from the installed KiCad session; old timeout results are archived separately. |
| Electrical identity | **0 errors.** 430 captured symbols, 421 physical schematic parts, 425 PCB footprints including four mounting holes, 1,373 pad instances, all 63 intentional no-connect identities and 55 requirements reconcile. [Strict parity](../reports/electrical-parity-audit.json). |
| Power rules | Four dedicated classes with 4/6 mm enforced track minima, 0.8/0.4 mm vias and scoped neck rules. Exact exceptions cover 492 captured tap copper items, with no power assignment to Kelvin nets or item-level DRC exclusions. [Rules and constrictions](../design/HIGH_CURRENT_RULES.md), [audit](high-current-audit.json). |
| Actual power copper | **247/247 power-pad paths continuous**, excluding tap tracks/vias from the connected-copper union; 85 section samples. Q40 connected drain copper exceeds the 600 mm² geometric target. [Filled geometry](filled-power-copper-review.md). |
| Critical analog routes | **46/46 paths**, 125 protected copper items, no foreign-net collisions in the audited paths. [Routing geometry](../reports/critical-routing-geometry.json). |
| Placement and access | 40 test points; no critical findings. Centered 3 mm probe: minimum modeled body-clearance reserve 0.366 mm. Antenna keepout and courtyards checked. Physical cable bends/tool access remain assembly checks. [Placement record](placement-access-review.json). |
| BOM and fabrication | **0 errors**; 356 PCB positions, 352 populated, four DNP, 124 grouped PCB rows and 31 external rows. Eleven Gerber layers, PTH/NPTH drills/maps, placement subsets and all requested mechanical/assembly documents. [Package manifest](../manufacturing/HomeMy_PMU_RevA-P1_2026-09-10/PACKAGE_MANIFEST.json). |
| Artifact consistency | The [final audit](FINAL_REVIEW.json) verifies native process success, current source/output hashes, every delivery file and ZIP contents. [Metadata scope](release-metadata-scope.json) retains prototype/production flags without changing native-format schemas. |

ERC SHA-256: `38a01195bd9bfedae926026ad02f03b66581b02f8acda143ae8389dbc3256a1c`.
DRC SHA-256: `41209f2f29faef8b89e8dab513edf4540d547d1aa666cb81b91bd1e35df13c75`.

The 360 × 300 mm board uses 70/35/35/70 µm copper, 48 zones and 2,232 through
vias. Twenty-five power zones now have 1.2 mm minimum fill thickness and remove
isolated islands. Widening BATT_N's lower extent from Y133 to Y137 mm restored
two return connections exposed by the stricter fill. Footprints and connector
interfaces were preserved. Seven 2 mm underside bars, fifteen BC contacts and
eight top star bridges remain required parts of the high-current assembly.
The 1 mm connection-width rule detects slivers; it is not a full-current rating.

A separate negative control inserts an undersized Motion track and via into a
temporary PCB copy. Native DRC detects both deliberate rule violations. That
diagnostic process timed out in the agent environment; its result is retained
in [power-rule-negative-control.json](../reports/power-rule-negative-control.json)
and is not substituted for the final board's normal exit-0 checks.

## Drawings and open procurement items

The delivery contains 48 press-fit hole coordinates/tolerances, seven separate
1:1 busbar drawings plus the combined drawing, stackup requirements, clamp BOM,
front/back assembly, component orientation, a polarity sheet and connector
pinout. DNP positions are C244, J13, R243 and R244. Thirteen SVG-derived review
views were rendered; the new polarity sheet, BB7 drawing and revised top copper
were visually inspected. [Source/image hashes](../reports/rendered-review-manifest.json)
identify these views. Visual review does not certify every manufacturing feature.

All nine unselected external positions are explicitly classified: **zero before
PCB ordering; nine before energization**. Their fixed interfaces and closure
evidence are specified in [OPEN_ORDER_ITEMS.md](../manufacturing/HomeMy_PMU_RevA-P1_2026-09-10/integration/OPEN_ORDER_ITEMS.md).
Converter, fuse, lug and cable selection may remain open only without changing
PCB footprints. The manufacturer must separately accept the prescribed stackup,
finished press-fit bores/plating and representative coupons as order conditions.

## Physical qualification remains open

Follow the [staged design review and bring-up](../../DESIGN_REVIEW_AND_BRINGUP.md).
Initial main-path work uses a current-limited motorless fixture at no more than
1 A, motion OFF and no more than 100 µF directly on SYS. The 940 µF motion/chopper
bank needs its separately defined controlled charging arrangement. Close the
external fuse, insulation, mounting and integration gates before battery use.

Real contact resistance, insertion/clamp behavior, hot FET/SOA/current sharing,
shunt drift, inrush, repetitive chopper energy, converter behavior, cable/arm
heating, fuse/BMS coordination, EMI/CAN and system stopping remain
[Revision-B validation](../../REV_B_VALIDATION.md). Geometry and clean ERC/DRC
do not turn any of these physical checks into a measured pass.
