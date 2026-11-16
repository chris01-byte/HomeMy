# Footprint review — HomeMy PMU Rev A2 (`HomeMy_PMU_RevA.kicad_pcb`)

**Result:** no BLOCKER. Every pad-number → physical-pin mapping, pin-1 corner, counting direction and polarity I checked is correct, and nothing is mirrored. I found 2 MAJOR issues in my slice, 1 MAJOR incidental issue outside it, and several MINOR ones.

Base facts:
- All 425 board footprints have pads identical to their library files, and all parts are on F.Cu (`python3 $A/cmp_lib.py`).
- Web was partly reachable: TI, Infineon, Espressif, JST and Panasonic downloaded. Nexperia (403), Analog Devices (503 / empty reply) and Phoenix (403) were not.
- The project's `footprint-pin-audit.json` only compares pin-number sets; it does not check geometry or pin position.

`$A` = `<SITZUNG>/agents/footprints`; `$E` = `$W/hardware/power-management-unit/rev-a/evidence`. All dimensions in mm, footprint-local coordinates (y down).

## 1. Footprint table

| Ref / footprint | Verdict | PCB vs datasheet | Evidence |
|---|---|---|---|
| Q1–Q10 `CCPAK1212_SOT8000A` | DEVIATION (mapping OK) | Pad 1 (G) at (−5.0, +5.65); 2–6 (S) same row to +5.0; 7–12 (D) opposite row +5 → −5; 13 (mb) centred. Matches Nexperia top view and "pad 1". Lead lands 1.20×1.90 (4.70…6.60) vs 1.30×1.65 (4.85…6.50); pitch 2.0 = 2.0. Mb 10.8×7.25 vs 10.8×7.26 (exposed pad 10.65–10.95 × 7.10–7.40). Lead-land → mb gap 1.075 vs 1.22. Toe 0.53–0.68 (Nexperia 0.43–0.58), heel 0.23–0.78, side 0.04–0.14 per side (lead width 0.93–1.12). | `$E/power/psmn1r0-100asf.pdf` p2, p10 Fig 18, p11 Fig 19 |
| RSH1/2 `CSS4J_4026_Kelvin` | OK | Force 2.55×5.60, sense 2.55×0.80, force–sense gap 0.90, overall 10.60×7.30, inner 5.50: identical to Bourns layout. Pads 2/3 are the sense lands, each on the side of its own force pad. Only 0.2 mm Kelvin tracks attach; no force copper within 0.3 mm. | `$E/power/css4j-4026.pdf` p2 |
| J1–J6 `Wurth_7461103` | OK | 8 holes at x ±3.81, y ±1.27 / ±3.81 (7.62×7.62, pitch 2.54) = drawing. Finished Ø1.475 = 1.475 ±0.05 (chemical surface; drill 1.60 −0.03, Cu 25–60 µm). Pad Ø2.10 gives 0.25 ring on the drill (≥0.10 required). Body 9×9, courtyard ±5.5. M5 axis parallel to the 4-pin rows = drawing. F.Cu under body is own net only. Board 1.6 mm equals the datasheet minimum. | `$E/chopper/7461103.pdf` p1 |
| U2 `VSSOP_DGX19…Missing16` | OK | 19 × 1.45×0.30, rows ±2.2, pitch 0.5; 1–10 left top→bottom, 11–20 right bottom→top; position 16 (+2.2, −0.25) empty. Identical to TI DGX0019A. | `$E/power/tps4811-q1.pdf` p5, p47, p48 |
| U1 `VQFN_RGE24…EP_FLOAT` | OK | 24 × 0.60×0.25 at ±1.9, EP 2.1×2.1, counter-clockwise from top-left: identical to TI RGE0024T. EP net unconnected; no via, track or zone on F.Cu at the EP (nearest copper 0.22 mm, an AON_WAKE_EN track). | `$E/power/lm74930-q1.pdf` p3, p4 (RTN), p39–40 |
| U3/U4 `Texas_RGE0024H…` | OK (minor dev.) | 0.825×0.25 at ±1.9625 (1.55…2.375) vs TI 0.58×0.24 at ±1.9125. EP 2.7 = 2.7. Pad–EP gap 0.20 vs 0.27. | `$E/power/tps2663.pdf` p3, p52–53 |
| D1/D2 `PTVS1_DFN8x6` | Land OK; see F2, F6 | 1.19×4.93 (x −3.465…−2.275) and 5.04×4.93 (−1.575…+3.465), gap 0.70: identical to Bourns. Small pad is on the pin-1-dot side. | `$E/power/ptvs1.pdf` p4 |
| Q40 `Infineon_PG-HSOF-8-1` | OK | Gate pad 1 at (−5.25, −4.2) = pin 1. Seven source fingers y −3.0…+4.2, pitch 1.2 = 1.20, = pins 2–8. Drain land x −1.35…+6.65 vs package pad end −1.26. Netlist 1 = G, 2 = S, 3 = D. | Infineon IPT015N10N5 Rev 2.4 p1, p10 (`$A/dl/infineon/`) |
| D63 `TO-220-2_Vertical` | OK | Pad 1 = K = MOTION_BUS_P, pad 2 = A = CHOP_DRAIN. Vishay: pin 1 tied to case, so cathode = pin 1 = tab; the tab is live at MOTION_BUS_P. Pitch 5.08 (4.95–5.20). | `$E/chopper/mbr10100.pdf` p1, p3 |
| Q11, Q44, Q20, Q21, Q41, Q42, Q43 `SOT-23` | NOT VERIFIED (primary) | Netlist uses 1 = B/G, 2 = E/S, 3 = C/D throughout (Q11: B+C = MOTION_TEMP_DIODE, E = BATT_N; Q43: S = CHOP_10V). This matches the standard Nexperia SOT23 pinouts as I know them. | — |
| D40, U17/U26 `SOT-23` | OK | ESD2CAN24 DBZ: 1, 2 = IO, 3 = GND. TPS3839 DBZ: 1 GND, 2 RESET, 3 VDD. | TI esd2can24-q1 p3; tps3839 p5 |
| U10 `ESP32-S3-WROOM-1` | OK | 40 × 1.5×0.9, x ±8.75, pitch 1.27, pad 1 at 7.49 from antenna end, EPAD centre 7.5 / 10.29 from left / bottom: = Espressif Fig 11-1. Pins 1–41 = Fig 3-1. | Espressif datasheet v1.8 p10, p45 |
| U12 `SOT-223-3_TabPin2` | OK | 1 GND, 2 + tab OUT (both on V3V3), 3 IN = TI. Lands 2.0×1.5 and tab 2.0×3.8 at ±3.15 vs TI 2.15×0.95 and 2.15×3.25 at ±2.9. | TI tlv1117lv p3, p23 |
| U51 `TI_DRB0008A…` | OK; see F5 | 8 × 0.60×0.31 at ±1.4, pitch 0.65, EP 1.5×1.75 = TI. TI's land also has four 0.23-wide tie-bar fingers, absent here. | `$E/tps3431.pdf` p3, p28–29 |
| U11 `MSOP-10_3x3mm_P0.5mm` | DEVIATION (F1) | 1.50×0.35 at ±2.1 vs TI DGS0010A 1.45×0.30 at ±2.2. Gap 0.15 vs 0.20. | `$E/ina228.pdf` p3, p45–46 |
| U30 `Texas_DGN0008B…` | DEVIATION (F1) | 1.45×0.50 vs TI 1.40×0.45. Gap 0.15 vs 0.20. EP copper 2.0×3.0, mask 1.88×1.98, vias as TI. Pin map and EP = GND correct. | `$E/chopper/tps7a4001.pdf` p3, p21–22 |
| U18, U19, U23, U24, U27, U55 `VSSOP-8_2.3x2mm` | DEVIATION (F1) | 1.25×0.35 at ±1.4 vs TI DCU0008A 0.85×0.30 at ±1.55. Gap 0.15 vs 0.20. | TI sn74lvc1g74 p22–23 |
| U34/U35 `SSOP-4` | OK | 1 A, 2 K, 3 E, 4 C = Vishay. Lands 1.65×0.60, inner 4.6 / outer 7.9, vs Vishay 1.25×0.90, 5.0 / 7.5. | `$E/chopper/vos618a.pdf` p1, p7 |
| U32, U60, U65 `TSSOP-14`; U13, U31 `SOIC-8`; SOT-23-5 / -6 | OK | TSSOP 1.475×0.40 vs TI 1.5×0.45 (gap 0.25). SOIC and DBV lands compatible with TI. Pin functions of U5, U14, U20, U22, U25, U31, U33, U36, U61 (and same-type parts) match the TI pin tables. | lm339b p51, tps3808 p4, tlv3011 p3, ucc27511 p5, ref50 p4, TI logic datasheets p3 |
| U16 `TSOT-23-8`, U21 `TSOT-23-6`, U15 `SOT-23-5` | NOT VERIFIED (land) | KiCad standard footprints. U16: 1.325×0.50 at 0.65 pitch, gap 0.15. U16 and U15 pinouts confirmed only from secondary datasheet copies. | — |
| C3/C10 | OK | Pitch 27.5; drill 1.1 for Ø0.8 lead; body 31.5×13. | `$E/power/wima-mks4.pdf` |
| C312/C313 | OK | Ø12.5, pitch 5.0, drill 1.2 for Ø0.6 lead. Pad 1 (+) = MOTION_BUS_P. | `$E/chopper/kyc.pdf` p1 |
| C246 | OK | EEU-FR1A102 is Ø10×16, pitch 5.0, lead Ø0.6; drill 1.0. Pad 1 (+) = V5V. | Panasonic FR p4 |
| J16/J17 JST GH | OK | 4 × 0.6×1.7 at 1.25; MP 1.0×2.8; pin-1 centre to MP edge 1.35. Matches JST layout; pin-1 side consistent. | JST eGH p2 |
| J7–J15, J18 MSTB | NOT VERIFIED | KiCad generic footprint for order numbers 1776508 / 1776511: pitch 5.08, drill 1.4. | — |
| D60/61, D62, D64–66 | Polarity OK | Pad 1 = K. D60: K MOTION_BUS_P. D61: K CHOP_DRAIN. D62: K CHOP_GATE. D64: K MOTION_BUS_P, A CHOP_10V. | netlist |

Intrinsic copper gaps (item 12), from `python3 $A/gaps.py` and `gaps2.py`:

| Ref | Smallest gap | Pads / nets |
|---|---|---|
| U1 | 0.25 | 13 (GND) ↔ 14 (HGATE), 15 (OUT) ↔ 16 (OVCLAMP = BATT_N); EP ↔ pads 0.55 |
| U2 | 0.20 | Only between pins within about 12 V of each other; 17 ↔ 15 is 0.70 |
| U3/U4 | 0.20 | IN / OUT pads ↔ GND EP; 0.25 for 5 (SYS_BUS_P) ↔ 6 (UVLO) |
| U11 | 0.15 | 7 (LOGIC_GND) ↔ 8 (INA_VBUS, battery voltage) |
| U30 | 0.15 | 5 / 8 (MOTION_BUS_P) ↔ NC 6 / 7; HV ↔ EP 0.475 |
| U51 | 0.34 | Low voltage only |
| U60 | 0.25 | Low voltage only |
| U15 | 0.35 | 1 (AON_LDO_IN) ↔ 2 (GND) |

## 2. Findings

**BLOCKER:** none.

**MAJOR**

- **F1 — 0.15 mm pad gaps on 70 µm copper, including battery voltage on U11.**
  - Refs: U11, U30, U16, U18, U19, U23, U24, U27, U55.
  - Cause: KiCad-library pads are 0.05 wider than the manufacturer lands (0.35 vs 0.30; 0.50 vs 0.45). See `Package_SO.pretty/MSOP-10_3x3mm_P0.5mm.kicad_mod:242`, `VSSOP-8…:206`, `Texas_DGN0008B…:289`, `Package_TO_SOT_SMD.pretty/TSOT-23-8.kicad_mod:242`.
  - The project DRC waives this to 0.15 for all U* pads (`HomeMy_PMU_RevA.kicad_dru` lines 3–143). The repo has no fabricator capability statement.
  - Why it matters: 0.15 mm in 2 oz copper is below the usual ≥0.20 mm fabricator limit, and no mask dam is possible. On U11, pad 8 is BATT_SENSED_P through R225 (10 Ω), upstream of the main switch; a bridge to pad 7 puts 42 V across R225 (4.2 A, about 176 W in an 0805).
  - Fix: use the TI lands (DGS 1.45×0.30, DCU 0.85×0.30, DGN 1.40×0.45), which give 0.20.
  - Confidence: high on the numbers, medium on the fab limit (fab-specific).

- **F2 — D1/D2: opposite-polarity pour under the package edge where BATT_N tie-bar stubs are exposed.**
  - The Bourns side views (p4) show cut tie-bar stubs in the lowest ~0.2 mm of the side walls: 3 per long side and 3 on the short side for the large terminal.
  - D2: the SYS_BUS_P pour edge is at local |y| = 2.965 on both long sides and x = +3.965 on the short side. The package edge is 3.0 / 4.0 ±0.05, so the pour is 0.035 inside the outline.
  - D1: the BATT_SENSED_P pour edge is at local y = +3.00 along the whole long side.
  - Separation is solder mask plus roughly 0.1–0.2 mm vertical at 42 V (clamp events about 56 V and above). IPC-2221B guidance for uncoated terminations at 31–50 V is 0.4 mm (quoted from memory).
  - Fix: keep foreign-net copper at least 0.5 mm outside the body outline, i.e. about 1.2 mm clearance from pad 2, or add a keep-out in the footprint.
  - Confidence: high on the copper geometry, medium on stub height (taken from the drawing only).
  - Re-verify: `/usr/bin/python3 $A/scan.py D2 x:-1.22:-3.6:3.6 y:0:3.3:4.6` and `… D1 x:3.03:-3.6:3.6`.

- **F3 — incidental, outside my slice: the bus TVS diodes are connected through 0.20 mm "tap" tracks.**
  - D1 pad 1 (BATT_FUSED_P): 2.55 mm of F.Cu 0.2 mm, a 0.6/0.3 via, 14.35 mm of In1 0.2 mm × 35 µm, then another via. That is about 40 mΩ and fuses at about 4 A²s (roughly 500 A at 8/20 µs). The part is rated 1 kA with a 56 V clamp.
  - D1 pad 2 and D2 pad 2 (BATT_N): 2.4 mm and 1.0 mm of 0.2 mm track, then a single 0.3 mm via into the 35 µm In2 plane.
  - Effect: about +8 V at 200 A on D1, against the LM74930 absolute maximum of 70 V.
  - These tracks are members of the DRC exemption group `PWR_TAP_CONTROL` (435 items; `.kicad_dru` line 189), which is why DRC is clean.
  - D60 pad 2 and D61 pad 2 are similar (about 3 mm of 0.2 mm track plus one via) but adequate for a 21.6 A SMCJ.
  - Confidence: high.
  - Re-verify: `/usr/bin/python3 $A/trace.py D1 1 14`, `$A/padconn.py D1 D2 D60 D61`, `$A/groups.py`.

**MINOR**

- **F4 — CCPAK land and paste differ from Nexperia Fig 19.** Lands are 0.10 narrower and 0.25 longer. Paste is 100 % on the 10.8×7.25 base; Nexperia specifies six 3.16×3.10 apertures (about 75 %) with a 0.15 mm stencil, and lead paste 1.15×1.5. Risks are tilt, voids and beading on ten 50 A FETs.
- **F5 — U51: a V3V3 track runs under the exposed GND tie bars.** The track from (211.175, 240.432) to (213.943, 240.432), 0.2 wide, crosses under both bottom-edge tie bars (x 213 ±0.325, package edge y 240.5). Only solder mask separates V3V3 from GND. TI's land puts GND copper there. Re-verify: `/usr/bin/python3 $A/nearbox.py U51 211.45 237.45 214.55 240.55`.
- **F6 — missing orientation marks.** D1/D2, U2 and U51 have no pin-1 mark on any layer. Q1–Q10, U1, RSH1/2 and J1–J6 have Fab marks but no silkscreen mark. Consequences of a 180° placement:
  - D1/D2: the 5.04 mm terminal bridges both pads, a hard short of BATT_FUSED_P / SYS_BUS_P to BATT_N.
  - RSH1/2: the sense pad is shorted to the force terminal, with no functional symptom.
  - Q1–Q10: drain and source are tied together.
- **F7 — paste and vias in exposed pads.** U1 EP has 100 % paste (TI: 77 %). U3 and U4 each have an open via in the EP centre (0.4 and 0.3 mm). The U10 and U30 footprints add eighteen 0.2 mm drills, a class not listed in `PCB_STACKUP_PRESSFIT.md`.
- **F8 — U3/U4: pad-to-EP gap is 0.20 (TI 0.27)** with 42 V between IN/OUT and the GND EP. The TI land (0.58×0.24 at 3.825 spacing) recovers the margin.
- **F9 — D63 drill 1.1 mm** against a maximum lead diagonal of 1.09 (0.94×0.56). There is no margin at maximum material; 1.3 would be safe.

**INFO**

- U1: a tented BATT_N via (0.6/0.3) sits partly under the package corner, 2.045 / 1.922 from centre.
- U34/U35: the input–output pad gap is 4.6 against Vishay's 5.0.
- U10: IO35–37 are used, which works on the N8 variant only.
- NT9/NT10 `NetTie_Logic_2` pads carry F.Paste.
- U12 (outside slice): the OUT tab pad has no pour, only 0.2 mm tracks and one 0.3 mm via, so the 62.9 °C/W assumed in `WAKE_IO.md` will not be reached.
- CCPAK mid-side tie bars sit at leadframe level; F.Cu there is the drain pour on all ten FETs.

## 3. Not verified

- Nexperia SOT23 and SOD123F pinouts and lands (BSS138BK, 2N7002, BSS84, MMBT3904, BZT52H).
- Analog Devices TS8, S6 and S5 land drawings (LTC2954, LTC6993, LT3014B).
- Phoenix 1776508 / 1776511 hole pattern.
- SMC and SOD-323 lands; Samtec TSW; 0603 NTC.
- PTVS1 stub height and the potential of the CCPAK side tie bars (both from drawings only).
- Paste and mask Gerbers and pick-and-place rotations; I read the board file only.
- Fabricator limits for 70 µm copper.

Housekeeping: `$A/dl/{2n7002,bss138bk,bss84,bzt52h,mmbt3904,1n4148ws}/*.pdf` are HTML error pages from the blocked downloads, not datasheets. I tried to delete them and the command was blocked, so they are still there.

## 4. Re-verification

```
export HOME=<SITZUNG>/kihome
A=<SITZUNG>/agents/footprints
python3 $A/dump.py Q1 PMU_RevA.pretty/CCPAK1212_SOT8000A.kicad_mod   # pads in local coordinates
python3 $A/cmp_nets.py U11 D1 Q40                                    # pad -> net vs netlist pin function
python3 $A/gaps.py; python3 $A/gaps2.py U11 U30 U3                   # intrinsic gaps
/usr/bin/python3 $A/near.py U1 25 0                                  # copper at the U1 EP, all layers
```

Sources for the secondary pinout confirmations (U16, U15):
- [LTC2954 product page](https://www.analog.com/en/products/ltc2954)
- [LTC2954 datasheet copy](https://cdn.components.ru/media/PDF/1445781.pdf)
- [LT3014B product page](https://www.analog.com/en/products/lt3014b.html)
- [LT3014B datasheet copy](https://html.alldatasheet.com/html-pdf/192052/LINER/LT3014BES5/948/6/LT3014BES5.html)