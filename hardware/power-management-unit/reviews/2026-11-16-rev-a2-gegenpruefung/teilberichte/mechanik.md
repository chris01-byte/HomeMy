# PMU Rev A2 — electromechanical concept review (busbars, star bridges, press-fit)

**Verdict:** the busbar concept as drawn has one release-blocking insulation defect, and five of the seven bars do no electrical work. Only BB7 carries meaningful current, and the layout forces that dependence.

**Basis:** the A2 PCB (sha256 2742638d…, untouched) read with pcbnew 10.0.8 on a private copy. I rasterised all four copper layers to net maps (0.05 mm) and took bar outlines from the A2 `manufacturing/busbar-pcb-interface.json`. I ran a 2-D sheet-resistance solve per main-path net (0.2 mm grid, 20 °C, vias and barrels modelled, equal FET currents) and a plate FE for the mounting. Geometry is exact to 0.05 mm; solver absolutes are about ±20 %, relative conclusions are firm. No physical tests.

Scripts and images are in `<SITZUNG>/agents/mech/` (`underbar.py`, `run_sheet.py`, `plate.py`, `pressfit.py`, `ov_B.png`).

## BLOCKER

**B1 — Positive bars sit on other nets' vias; BB1 is on the unswitched battery node.**
- **BB1** (BATT_SENSED_P, x 42–54, y 19–91): LOGIC_GND vias at (44.19, 75.73) and (42.94, 80.23), V3V3 at (44.19, 60.09), MAIN_KELVIN_N at (42.00, 75.90) on the bar edge.
- **BB2**: LOGIC_GND ×3 at (71.71, 74.66), (73.02, 60.24), (71.96, 54.36); TEMP_MAIN_ADC at (74.71, 60.34).
- **BB5**: BATT_N at (174.00, 77.93), LOGIC_GND ×2, TEMP_MOTION_ADC ×2, MOTION_TEMP_DIODE.
- **BB6**: LOGIC_GND ×2. **BB3/BB4**: none.
- **BB7** (BATT_N): 10 foreign vias (ARM_R_N ×4, MOTION_IMON_INPUT ×3, AON_WAKE_EN ×2, MAIN_FAULT_N) plus ARM_L_N / ARM_R_N / LOGIC_BUCK_N pours of 205 / 224 / 64 mm². No positive net lies under BB7.
- All are Ø0.6/0.3 mm vias, tented both sides but not plugged; the B.Mask Gerber has pad openings only. Insulation is solder mask plus four loose Kapton sheets, in or beside the M3 clamp zone (LOGIC_GND vias 5.5–5.8 mm from the BC2/BC4 screw axes).
- **Why it matters:** a BB1 short to LOGIC_GND (via NT9's 1 mm neck to BATT_N) or to V3V3 is upstream of Q1–Q6. Only the external 60 A fuse/BMS is in the path. The via barrel (0.022 mm² Cu) would open at roughly 200 A in about 1 ms under the clamped bar; a V3V3 hit puts 42 V on the logic rail. BB2/BB5/BB6 shorts rely on short-circuit protection alone.
- **Why the project missed it:** `mechanics.py` (in `reports/retest-methods.json`) tests only drilled footprint pads against bar outlines, never vias, tracks or zones.
- **Confidence:** high. **Re-verify:** loop over `PCB_VIA` positions against the JSON outlines, or view B.Cu at the coordinates.

## MAJOR

**M1 — BB1–BB5 are electrically inert.** They run perpendicular to the current and touch their own pour at two near-equipotential points.

| Segment (50 A; arms 25 A) | PCB only µΩ / W | With bar, 0 / 100 µΩ contacts | Current per bar contact |
|---|---|---|---|
| J1 → RSH1 (no bar) | 118 / 0.30 | — | — |
| BATT_SENSED_P (BB1) | 172 / 0.43 | 172 / 172 µΩ | 1.1–1.8 A |
| MAIN_COMMON (BB2) | 96 / 0.24 | 93 / 94 µΩ | 2.9–4.3 A |
| SYS_BUS_P (BB3) | 195 / 0.49 | 193 / 195 µΩ | 1.3–3.0 A |
| MOTION_SENSED_P (BB4) | 188 / 0.47 | 187 / 188 µΩ | 0.6–1.2 A |
| MOTION_COMMON (BB5) | 134 / 0.33 | 131 / 133 µΩ | 1.6–3.4 A |
| MOTION_BUS_P (BB6) | 176 / 0.44 | 102 / 126 µΩ | 6–18 A |
| ARM_L_N / ARM_R_N (no bars) | 1195 / 0.75, 1031 / 0.64 | — | — |
| BATT_N (BB7) | 891 / 2.23 | 150 / 223 µΩ (0.37 / 0.56 W) | NT1.2, NT2.2 19–23 A; BC15 19–30 A |

- Total conductor loss is 6.3 W PCB-only against 4.5 W with all bars. BB7 saves 1.7 W, BB6 0.12 W, BB1–BB5 together 0.014 W. For scale, the shunts dissipate 2.5 W and the FETs about 4.2 W.
- The pours are already 50–75 mm wide on two 70 µm layers.
- `HIGH_CURRENT_RULES.md` calls the bars "zwingend" (mandatory); for BB1–BB5 this does not hold.
- Deleting BB1–BB6 removes 14 bolted joints and B1 entirely.
- **Confidence:** high on the conclusion, medium on absolutes.

**M2 — Shim/film reserve is not real once solder mask is counted.** This affects 23 contacts.
- **Assumptions:** shim 0.25 ± 0.02 on ENIG (+0.004); film 0.16–0.22 on mask of 15–40 µm over the 70 µm pour. The project's own stackup declares 10 µm mask.
- **Vertical:** reserve is +0.03 mm nominal and −0.03 mm worst case. The documented "+0.01" (`MECHANICAL_BUILD.md:40`, `production-readiness.json`) becomes ≤ 0 with any mask ≥ 10 µm.
- **Load path:** the film window (Ø8.5) lies inside the clamp cone (about Ø11.5 at the PCB face). With negative reserve the preload goes into film and mask, at about 4 MPa, and the shim is unloaded.
- **Lateral:** shim Ø8 equals land Ø8, in a Ø8.2 mask opening. M3 play (shim hole 3.4, PTH 3.1–3.3) allows up to about 0.47 mm offset, so the shim rides the mask rim at the 15 BC lands. The film is located only by those floating shims and can be pinched.
- **Not an issue:** bar thickness tolerance and board bow. Bow gives ≤ 0.09 mm over 58 mm, flattened by about 2 N.
- **Confidence:** medium-high; mask thickness is assumed.

**M3 — J1 (+) and J2 (−) are in line, 53 mm apart, and A2 no longer defines which way they face.**
- J1 is at (20, 50), J2 at (20, 112); the corridor between them is empty.
- Rev A carried "Jx M5 FACE ±Y" texts; the A2 PCB has only "M5 AXIS" double arrows. `ASSEMBLY_ORIENTATION.md:47-54` lists old coordinates and J4/J6 at 0° (now 90°).
- The only A2 statement is implicit in `mechanics.py`: J1/J2/J3/J5 face −Y, J4/J6 face +X. That points J2's screw and tool axis straight at the bare J1 block.
- A tool on J2 touching J1 is a battery short with only the 60 A fuse in the path. There is no barrier, boot or polarity keying, and a wrongly pressed terminal cannot be reworked.
- 2.2 Nm without counter-hold loads a pin row with about 289 N against 4 × 30 N guaranteed retention. An 84 N sideways cable pull at 10.9 mm height reaches the same limit. No counter-hold feature or tool is defined.
- **Fix:** J2 facing +Y, markers restored, insulating covers.
- **Confidence:** high on geometry.

**M4 — The A2 mechanical package is JSON only.**
- There is no drawing for bars, NB bridges, shims, backing washers or film. Rev A had 1:1 SVGs; the BOM says "fabricate to HomeMy drawing".
- `MECHANICAL_BUILD.md:21-34` (the binding assembly text) still gives 360×300 coordinates and cut-outs under J2–J6 that no longer exist.
- The A2 JSON says "PET/polyimide" where the film spec is Kapton HN, labels the J2 cut-out "foreign" although J2 is BATT_N, and gives no inner radius for BB6.
- There is no assembly fixture concept for roughly 275 loose parts, including 93 disc springs that must be stacked in threes the same way round.

**M5 — Mounting: four M3 points only.** H1 (9, 9), H2 (271, 9), H3 (202, 251), H4 (64, 251).
- Bars plus hardware weigh about 300 g (BB7 106 g, BB6 31 g, BB1–BB5 65 g, NB bridges 29 g, hardware about 70 g). Board with parts is about 410 g.
- Fundamental frequency is 17–24 Hz with bars (35 Hz without); 1 g sag is 0.6–1.0 mm.
- A 10 N vertical force deflects the board 1.65 mm at J2, 1.3 mm at J6 and 0.6 mm at J1. J2 is 104 mm from the nearest hole.
- The documents require an independent carrier and strain relief, but the PCB has no interface for one. This is weak for a mobile robot.
- **Confidence:** medium (bar stiffness ignored, parts masses estimated).

**M6 — NB bridges and pad-1 hardware are redundant, and NB7 sits 0.80 mm from +42 V copper.**
- The NT pads (10×10, on all copper layers) abut. The In1/In2 Gerbers flash both pads, and F.Cu has a 20×10 fill. The built-in tie is therefore 10 mm wide on four layers (2.1 mm²) with zero length.
- A missing or loose NB bridge changes nothing: about 82 µΩ on the PCB against 9 µΩ plus two contacts. `MECHANICAL_BUILD.md:34` ("only the NB bridge connects…") is wrong.
- NB7's edge (x = 118) is 0.80 mm from the 4.4 mm SYS_BUS_P feed (zone edge x = 117.2). The positional stack is up to 0.77 mm, so separation there is mask only.
- Each NB bridge is 20×10 in a 20.2×10.2 mask opening, so it sits on the mask rim.
- Deleting NB1–NB8 and the pad-1 stacks removes 8 more joints.

## MINOR

- **m1 — True bottlenecks are untouched by the bars.**
  - No stitching via lies within 3 mm of any shunt force pad (nearest 4.7–7.1 mm) or any of the ten FET tabs.
  - J1 → RSH1 runs 48.5 of 50 A in F.Cu alone, at a 99th-percentile 75 A/mm² (peak about 150). The B.Cu pour at J1 is a dead end with two signal vias.
  - In1/In2 are not connected to the J1, J3–J6 pins.
  - Würth's rule of thumb (I/0.3 µm total copper) asks for about 167 µm at 50 A and 200 µm at 60 A.
- **m2 — Clamp stack.**
  - Three nested discs go flat at about 375 N, so the "200–400 N" window is inconsistent. 200 N is at 0.10 mm, 312 N at 0.1875 mm, leaving about 0.09 mm settling reserve.
  - The top Ø9 washer sits on the Ø8.2 mask rim (about 29 MPa on mask).
  - The nut bears on the spring's inner edge at the nut chamfer.
  - There is no method to set or verify preload: no torque spec, single-use Precote.
  - Contact pressure is 4.9–7.6 MPa on bare copper, at the low end of busbar practice.
  - The ten-cycle coupon test does not cover FR-4 or mask creep.
- **m3 — Mounting holes.**
  - NPTH, no net. Copper comes to 0.25 mm from the hole wall: LOGIC_GND on In1 (all four), BATT_N on In2 (H1, H2), V3V3 on In2 (H4), and LOGIC_GND on B.Cu (H3, H4).
  - Standoffs at H3/H4 therefore sit on mask-covered LOGIC_GND.
- **m4 — Press-fit data.**
  - The 48 holes are not flagged press-fit in the drill file; they are separable only as T8 1.475.
  - The annular ring is 0.25 mm from the 1.6 drill; `PCB_STACKUP_PRESSFIT.md:33` computes 0.3125 from the finished hole.
  - In1 LOGIC_GND and In2 BATT_N planes are 0.30 mm from J1's pads (0.55 mm from the drilled wall) on the unprotected node.
- **m5 — ARM_R_N neck.** 6.0 mm wide for about 30 mm (x 250–256, y 89–119, both outer layers), 30 A/mm² at 25 A. The documents quote 12.5 mm. Roughly 11 K rise by IPC-2221, so acceptable but at the rule minimum.
- **m6 — B.Cu BATT_N band under NT1.** Cut to 2.0 mm at x = 206.5 by a MOTION_GATE_EN track. The PCB-only return then rests on In2 (35 µm).
- **m7 — BB7 bolted rigidly at nine points.** A 20 K bar-to-board difference gives about 38 µm slip at the end joints (fretting on bare Cu/ENIG).
- **m8 — Unsupported parts.** D63 is a free-standing two-lead TO-220 with live tab; C312/C313 stand 35 mm on a 5 mm pitch.
- **m9 — Edge trunk.** MOTION_BUS_P runs 0.95 mm from the right board edge for 191 mm (x 275–279).

## INFO

- PCB copper alone can carry 50 A; the layout, not the copper budget, makes BB7 necessary. Opening the F/B BATT_N corridor at x 206–220, or taking the arm returns to an external star stud, would remove it.
- If any bar stays: no foreign copper beneath it (enforce with a rule area), shim proud by at least 0.1 mm or embossed bosses, film bonded to the bar, plated contacts.
- Würth permits pressing REDCUBE directly into solid copper bar (Ø1.45 ± 0.05); vertical-stud terminals would react lug torque in-plane.
- Würth's datasheet gives 160 A at 20 °C with no PCB conditions. The rule of thumb is from their 2023 presentation: https://www.we-online.com/files/pdf1/redcube-high-power-terminals.pdf

## Verified OK

- All 15 BC and 16 NT hole coordinates and nets in the A2 JSON match the PCB pads exactly; hole edge distances are ≥ 4.75 mm.
- No bar collides with THT pads, press-fit pins, mounting holes, the board edge (≥ 19 mm) or another bar (gaps 16–36 mm). There are no bottom-side components.
- Nearest bar-to-pin gaps: BB7–J2 1.14 mm and BB6–J3/J5 2.64 mm (same net); BB6–J4 4.14 mm (MOTION_BUS_P against ARM_L_N).
- Press-fit keep-outs hold: nearest courtyard 2.97 mm (TP1, a bare pad), edge ≥ 13 mm, 25 mm M5 corridors free.
- Arithmetic in `MECHANICAL_BUILD.md` is correct (10.7325 mm stack, spring figures, T = KFd, bar resistances). The 1.07 mm is protrusion beyond the nut, so engagement is full; with the ISO minimum length of 11.65 mm it is 0.92 mm.

## Not verified

- Actual mask and ENIG thickness, and fab capability for 38–60 µm hole copper.
- 3-D heights and tool envelopes (no 3-D models).
- Real contact resistance and FET current sharing.
- Precote build-up against the Ø3.1 mm minimum PTH.
- The enclosure.