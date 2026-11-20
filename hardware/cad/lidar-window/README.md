# LiDAR Window Ring "freie Sicht für Lidar"

Status: CAD body built from `../homemy.step` (V2) and the slot/web values of the
2026-11-16 LiDAR slot decision. Not built, not measured, not checked with a live scan.

## Why This Exists

The STL-27L cannot see through the infrared acrylic ring between the ABS base
frame and the upper shell. The accepted fix is an open slot at scan height with
six webs that keep the ring load-bearing. The values come from
`docs/decisions/2026-11-16-lidar-slot-and-support-webs.md` (commit `e883e7b`,
branch `claude/eager-shannon-yfyfpf`, not yet on `main`).

The acrylic ring itself is not in `homemy.step` V2: the components
`KEEP_CLEAR_optical_window_Z23.00_to_33.00_scan_Z27.00` and
`Structural_base_ring_load_path_above_IR_window` are exported without geometry,
and no body is named "freie Sicht für Lidar". The ring was therefore modelled
from the parts around it and then slotted. `homemy.step` is unchanged.

## Files

| File | Content |
| --- | --- |
| `freie_sicht_fuer_lidar.step` | Slotted ring as one solid named "freie Sicht für Lidar", AP214, mm, in the coordinates of `homemy.step`. Insert it at the origin without moving it. |
| `freie_sicht_fuer_lidar_abwicklung.dxf` | Flat development 1:1 in mm. Layers `KONTUR`, `SCHLITZE`, `BIEGEZONEN`, `TEXT`. |
| `freie_sicht_fuer_lidar.png` | Drawing sheet: top view at the scan plane, dimensions, blind sectors, development. |
| `freie_sicht_fuer_lidar.json` | All values and check results produced by the generator. |

Regenerate with `tools/cad/lidar_window_ring.py --model hardware/cad/homemy.step --out hardware/cad/lidar-window`
(needs `cadquery-ocp`, `ezdxf`, `matplotlib`, and the STEP from Git LFS).

## Geometry

Model frame: X to the robot's right, Y forward, Z up, Z 0 = top of the aluminium
base plate, floor at about Z -41.8. The decision record uses X forward, Y left.

| Item | Value | Source |
| --- | --- | --- |
| Outline | outer 500 x 400 mm, corner radius 100 (inner 494 x 394, R97) | ABS frame below Z 89 and shell above Z 189 are both 500 x 400 |
| Sheet | 3 mm | ABS frame has a 3 mm rebate; record assumed 3 mm |
| Height | Z 89 to Z 189 (100 mm) | rebate step Z 89, frame top Z 99, shell underside Z 189 |
| Scan plane | Z 122 (about 164 mm above the floor) | LiDAR component `scan_Z27.00`, component Z 0 = model Z 95 |
| Slot | Z 102 to 142, 40 mm, 13 to 53 mm above the ring's lower edge | record: 40 mm centred on the scan plane |
| Slot corners | R3 (6 mm end mill) | record risk: unrounded milled corners crack |

The lower 10 mm of the ring overlap the frame rebate, so 3 mm of acrylic remain
visible between the frame top and the slot. The upper land is 47 mm.

### Webs

| Web | Model coordinates | How to mark it on the ring | Width |
| --- | --- | --- | --- |
| front left / right | front wall, X -150..-130 and +130..+150 | 130 to 150 mm left/right of the centre line | 20 mm |
| side left / right | side walls, Y -110..-30 | 230 to 310 mm behind the front face; the last 10 mm lie in the rear corner bend | 80 mm |
| rear left / right | rear wall, X -150..-130 and +130..+150 | 130 to 150 mm left/right of the centre line | 20 mm |

### Development

Measured on the sheet mid-surface (corner radius 98.5 mm), outside face visible,
lower edge (rebate side) at the bottom. Length 1618.9 mm, height 100 mm. The
strip starts in the middle of the left side web and runs counter-clockwise seen
from above (rear first). The start point is only a drawing reference.

| Slot | From (mm) | To (mm) | Length (mm) | Between webs |
| --- | ---: | ---: | ---: | --- |
| 1 | 40.0 | 184.7 | 144.7 | side left, rear left |
| 2 | 204.7 | 464.7 | 260.0 | rear left, rear right |
| 3 | 484.7 | 629.4 | 144.7 | rear right, side right |
| 4 | 709.5 | 994.2 | 284.7 | side right, front right |
| 5 | 1014.2 | 1274.2 | 260.0 | front right, front left |
| 6 | 1294.2 | 1578.9 | 284.7 | front left, side left |

Bend zones: rear left 30.0 to 184.7, rear right 484.7 to 639.5, front right
839.5 to 994.2, front left 1294.2 to 1448.9. Rear centre at 334.7, front centre
at 1144.2.

## Checks

Run by the generator; it stops if one fails.

- The result is one valid solid; volume 320,345 mm3 (about 381 g of PMMA).
  The slot removes 165,323 mm3.
- Web sectors at the scan plane, from the LiDAR axis (0 deg ahead, positive to
  the left): front +-72.9 to +-76.1 (3.2 deg), rear +-157.2 to +-160.1 (2.9 deg).
  These match the decision record within 0.1 deg.
- Side webs: +-127.2 to +-137.6 at the scan plane and +-127.0 to +-137.8 next
  to the slot edges. Both lie inside the strut shadows of +-126.9 to +-137.9,
  so they add no blind angle.
- At slot height, only the two struts and the LiDAR head cut the scan plane.
- The ring overlaps no solid of `homemy.step` (0 mm3 with frame and shell).
- Re-importing the STEP gives one valid solid named "freie Sicht für Lidar".

## Limits

- CAD prediction only. Mask sectors must still be confirmed with live scans
  (LiDAR contract, stages L3 and L4).
- The ring is assumed flush with the 500 x 400 outline, 3 mm thick, seated on
  the frame rebate and ending at the shell underside. A different sheet or
  joint changes the ring, not the web positions. A 5 mm sheet widens the
  front sectors by about 0.7 deg.
- No clearances or manufacturing tolerances are modelled.
- The development uses the mid-surface. A flat strip bent afterwards can
  differ by the real bend allowance in the four corners. Webs and slot ends
  on straight walls are not affected.
- The side web boundary at Y -110 is a plane across the rear corner bend. It
  meets the sheet about 6 deg off square, so the slot end on the inner face
  sits about 0.3 mm from the one on the outer face.
- The open slot lets dust and small objects into the base.

## Rollback

Delete this folder and `tools/cad/lidar_window_ring.py`. `homemy.step` was not
modified. If the built ring differs, change the constants in the generator,
regenerate, and repeat the LiDAR L4 mask check.
