# Placement and access review after analog changes

`rev_a_engineering_prototype: true`  
`rev_b_production: false`

Final stable placement snapshot. No PCB data was changed.
The [JSON evidence](placement-access-review.json) records actual native geometry. This review does not establish final routing connectivity or a 3D tool/harness envelope.

All 40 testpoints were checked against their source nets, front mask openings and reference visibility. The smallest test-pad edge to component-courtyard gap is **0.866 mm at TP1/RSH1**. A centered 3 mm probe nose has a minimum body-courtyard margin of **0.366 mm**. Negative margins are reported as access limitations, not silently accepted.

| Ref | Net | X | Y | Nearest body / pad-edge gap mm | 3 mm probe margin mm |
|---|---|---:|---:|---|---:|
| TP1 | BATT_FUSED_P | 24 | 51 | RSH1 / 0.866 | 0.366 |
| TP2 | BATT_SENSED_P | 53 | 85 | Q3 / 2.505 | 2.005 |
| TP3 | MAIN_KELVIN_P | 44 | 91 | R27 / 2.055 | 1.555 |
| TP4 | MAIN_KELVIN_N | 44 | 85.8 | BC2 / 2.305 | 1.805 |
| TP5 | MAIN_COMMON | 79 | 59 | Q5 / 1.505 | 1.005 |
| TP6 | SYS_BUS_P | 97 | 108 | NT8 / 7.505 | 7.005 |
| TP7 | MOTION_KELVIN_P | 150 | 91 | R35 / 1.325 | 0.825 |
| TP8 | MOTION_KELVIN_N | 146.5 | 85.5 | R35 / 1.555 | 1.055 |
| TP9 | MOTION_COMMON | 158 | 55 | BC10 / 2.543 | 2.043 |
| TP10 | MOTION_BUS_P | 281 | 52 | R331 / 4.295 | 3.795 |
| TP11 | PC_BUCK_IN_P | 40 | 169 | C21 / 2.305 | 1.805 |
| TP12 | LOGIC_BUCK_IN_P | 74 | 176 | R54 / 1.081 | 0.581 |
| TP13 | V5V | 134 | 262 | C246 / 1.771 | 1.271 |
| TP14 | V3V3 | 214 | 207 | R240 / 5.064 | 4.564 |
| TP15 | BATT_N | 102 | 133 | NT8 / 4.505 | 4.005 |
| TP16 | LOGIC_GND | 160 | 217 | Q20 / 21.533 | 21.033 |
| TP17 | AON_3V3 | 86 | 228 | C257 / 3.268 | 2.768 |
| TP18 | AON_WAKE_EN | 136 | 178 | R229 / 21.944 | 21.444 |
| TP19 | MAIN_FAULT_N | 152 | 177 | R229 / 8.504 | 8.004 |
| TP20 | MAIN_TMR | 59 | 108 | R22 / 2.072 | 1.572 |
| TP21 | MOTION_GATE_EN | 193 | 139 | NT1 / 5.677 | 5.177 |
| TP22 | MOTION_FLT_N | 200 | 168 | R235 / 20.424 | 19.924 |
| TP23 | MOTION_TEMP_FLT_N | 203 | 186 | R235 / 2.325 | 1.825 |
| TP24 | MOTION_TMR | 161 | 108 | C13 / 2.305 | 1.805 |
| TP25 | MOTION_IMON_INPUT | 184 | 133 | C10 / 2.887 | 2.387 |
| TP26 | CHOP_GATE | 293 | 39 | Q40 / 1.105 | 0.605 |
| TP27 | CHOP_10V | 290 | 67 | R302 / 2.055 | 1.555 |
| TP28 | CHOP_REF2V5 | 301 | 83 | R311 / 5.064 | 4.564 |
| TP29 | CHOP_FAULT_N | 226 | 188 | R237 / 1.055 | 0.555 |
| TP30 | CHOP_ACTIVE_N | 250 | 183 | C228 / 18.268 | 17.768 |
| TP31 | CAN_TX | 138 | 278 | J23 / 2.235 | 1.735 |
| TP32 | CAN_RX | 183 | 277 | C246 / 42.756 | 42.256 |
| TP33 | ESP_MAIN_HOLD | 246 | 256 | J22 / 16.747 | 16.247 |
| TP34 | ESP_MOTION_RESET | 245 | 221 | R233 / 13.055 | 12.555 |
| TP35 | LIFT_24V_SAMPLE | 16 | 241 | J13 / 1.505 | 1.005 |
| TP36 | LIFT_24V_N | 20 | 243 | J20 / 1.554 | 1.054 |
| TP37 | PC_EFUSE_FAULT_N | 35 | 175 | C20 / 1.305 | 0.805 |
| TP38 | PC_EFUSE_PGOOD | 39 | 181 | R40 / 1.081 | 0.581 |
| TP39 | LOGIC_EFUSE_FAULT_N | 85 | 175 | C25 / 1.305 | 0.805 |
| TP40 | LOGIC_EFUSE_PGOOD | 89 | 171 | U4 / 1.375 | 0.875 |

Native front-courtyard intersections: **0**. These use actual polygons, including the ESP32 stepped outline.

| ESP32 candidate | Intersection mm² | Actual courtyard gap mm |
|---|---:|---:|
| C205 / U10 | 0 | 0.210 |
| C239 / U10 | 0 | 3.060 |
| C240 / U10 | 0 | 3.560 |
| R219 / U10 | 0 | 2.310 |
| R220 / U10 | 0 | 1.580 |

The antenna check reads every native rule area, its prohibitions/layers, actual pad/track/via copper, saved filled polygons, foreign courtyards and the defined busbars. Copper curves are polygonized at 0.005 mm; this screen complements native DRC.
Bounds [301.0, 286.75, 349.0, 307.75] mm; layers ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']. Foreign courtyard hits []; busbar hits []; actual copper intersections 0. Mounting-hole courtyard gaps: {'H3': 5.555001000000004, 'H1': 400.9710254344193, 'H4': 289.555001, 'H2': 275.31881917246534}.

| Connector | Access basis | 20 mm projected courtyard hits | Top bridge hits |
|---|---|---|---|
| J1 | M5 face -Y from assembly specification; 9 mm wide projected 20 mm tool corridor | none | none |
| J2 | M5 face -Y from assembly specification; 9 mm wide projected 20 mm tool corridor | none | none |
| J3 | M5 face -Y from assembly specification; 9 mm wide projected 20 mm tool corridor | none | none |
| J4 | M5 face +Y from assembly specification; 9 mm wide projected 20 mm tool corridor | none | none |
| J5 | M5 face -Y from assembly specification; 9 mm wide projected 20 mm tool corridor | none | none |
| J6 | M5 face +Y from assembly specification; 9 mm wide projected 20 mm tool corridor | none | none |
| J7 | Right-edge horizontal mating | none | none |
| J8 | Right-edge horizontal mating | none | none |
| J9 | Left-edge horizontal mating | none | none |
| J10 | Left-edge horizontal mating | none | none |
| J11 | Left-edge horizontal mating | none | none |
| J12 | Right-edge horizontal mating | none | none |
| J13 | Left-edge horizontal mating | none | none |
| J14 | Right-edge horizontal mating | none | none |
| J15 | Right-edge horizontal mating | none | none |
| J16 | Vertical mating/top access; mated housing/grip volume absent | top access; no horizontal corridor modeled | none |
| J17 | Vertical mating/top access; mated housing/grip volume absent | top access; no horizontal corridor modeled | none |
| J18 | Bottom-edge horizontal mating | none | none |
| J20 | Vertical mating/top access; mated housing/grip volume absent | top access; no horizontal corridor modeled | none |
| J21 | Vertical mating/top access; mated housing/grip volume absent | top access; no horizontal corridor modeled | none |
| J22 | Vertical mating/top access; mated housing/grip volume absent | top access; no horizontal corridor modeled | none |
| J23 | Vertical mating/top access; mated housing/grip volume absent | top access; no horizontal corridor modeled | none |

M5 directions come from the assembly specification: J1/J2/J3/J5 face −Y; J4/J6 face +Y. A projected overlap is an unresolved 3D fixture check because screw-axis and nearby hardware heights are not modeled here. A clear projection also does not prove tool access. Confirm actual wrench, lug stack, counterhold and cable-bend clearance at the first article.

Critical geometric findings: none detected in this snapshot.
Limited 3 mm probe positions: none.
