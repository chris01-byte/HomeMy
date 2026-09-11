# Additional mechanical review — WIP

Read-only native geometry review on 2026-09-11. PCB SHA-256:
`9f329b44bf0fece059550d2f4a07b94af8fb52cfec7d26c4796aeed230193f99`.
The measured snapshot was not changed by the aborted digital router.

| Mount | Centre, mm | Hole edge to PCB edge, mm | Courtyard gap to nearest neighbour, mm |
| --- | --- | ---: | --- |
| H1 | 8, 8 | 6.40 | 16.694 to U11 |
| H2 | 272, 8 | 6.40 | 7.055 to J5 |
| H3 | 218, 214 | 4.40 | 1.002 to R222 |
| H4 | 20, 215 | 3.40 | 0.405 to C245 |

All four mounting holes are 3.20 mm diameter. Their 6.90-mm-diameter native
courtyards do not overlap neighbouring component courtyards. The small H4 gap
requires an explicit selected screw/washer/tool envelope; this is not a measured
3D assembly or tool-clearance qualification.

Across all 48 press-fit holes, the minimum hole-edge-to-board-edge distance is
7.4525 mm nominal, or 7.4275 mm at the largest permitted 1.525-mm finished hole.

The conservative 3-mm distance check against *all* foreign courtyards finds:

- J1 pad 1 to TP1: 1.96164 mm.
- J1 pad 2 to TP1: 2.77096 mm.

TP1 at (8, 53) is an unpopulated, flat 2-mm test pad with no hole. Excluding test
pad courtyards, the minimum distance to another mechanical/electrical footprint
is 6.88708 mm from J3 pad 8 to C312. The finished-hole upper tolerance reduces
hole-edge distances by another 0.025 mm.

This distinction does **not** waive a manufacturing requirement. TP1's treatment
in the actual press support/stamp design remains open. Likewise, actual harness
bend radii, selected cable lugs, busbar shapes/insulation and press-tool support
must be reviewed in 3D before a future fabrication release.

**WIP — not orderable. No mechanical or manufacturing release.**
