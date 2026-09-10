# HomeMy Power-Control Board Interfaces and Layout

Status: companion to `ASTRA_PCB_HANDOFF.md`; **not released for fabrication**.  
Date: 2026-09-10.

## 1. Connector and harness plan

Identifiers below are functional names; Astra may assign reference designators. Exact orderable suffixes, contact plating, temperature rise, mating cycles, keying, and locking must be verified.

| Function | Proposed interface | Pins / current basis | Status |
| --- | --- | --- | --- |
| Battery positive/negative | covered M5 ring-lug studs or REDCUBE press-fit class | 6 mm2; at least 70 A design class | `BLOCKER` exact part and mechanics |
| Left arm | Molex Mega-Fit 2-pin candidate | +/return; 4 mm2; target <=25 A continuous pending proof | `BLOCKER` derating/current envelope |
| Right arm | Molex Mega-Fit 2-pin candidate | +/return; 4 mm2; target <=25 A continuous pending proof | `BLOCKER` derating/current envelope |
| Two ESS23 drive motors | Micro-Fit 3.0 2-pin candidate | +/return; common feed about 8 A peak setting; 1.5 mm2 trunk | `PROVISIONAL` exact suffix |
| External 24 V lift buck input | Micro-Fit 3.0 2-pin candidate | motion +/return; expected 4-5 A input; 1 mm2 | `PROVISIONAL` |
| Optional 24 V clamp sense | DNP 2-pin service connector | 24 V output/return | `PROVISIONAL` |
| External PC buck input | Micro-Fit 3.0 2-pin candidate | protected system +/return; about 3 A allowed; 0.75 mm2 | `PROVISIONAL` |
| External 5 V buck input | Micro-Fit 3.0 2-pin candidate | protected system +/return | `PROVISIONAL` |
| Regulated 5 V return to PCB | Micro-Fit 3.0 2-pin candidate | +5V/return; up to 5 A; 1 mm2 | `PROVISIONAL` |
| Chopper resistor | Micro-Fit 3.0 2-pin only if pulse derating passes | resistor high/low; 8.6 A pulse; 1.5 mm2 high-temperature | `BLOCKER` connector pulse/temperature proof |
| LED strip | locking 3-pin | +5V, DATA, GND | `PROVISIONAL` |
| Power button | locking 2- or 3-pin | switch and return; optional shield | `OPEN` |
| CAN | JST-GH 4-pin candidate | CAN_H, CAN_L, CAN_GND, shield/NC | `PROVISIONAL` exact pinout |
| NTCs / service signals | locking small-signal multi-pin | 0.14-0.25 mm2 | `OPEN` |

The previously considered Würth `7466003R` 50 A SMT part is not acceptable for the battery path because it lacks margin. Do not use XT-series connectors in the final product design; they may remain prototype harness parts outside the released PCB.

Individual RobStride wire after the arm distribution is expected in the 1-2.5 mm2 range and remains part of the arm harness, not this board.

## 2. PCB partition and layout constraints

Starting stack-up is four layers, 2 oz outer copper and 1 oz inner copper, pending fabricator confirmation.

Suggested hierarchical sheets:

1. `00_top_power_tree`;
2. `01_battery_input_main_shunt`;
3. `02_main_switch_lm74930`;
4. `03_motion_gate_tps48110`;
5. `04_brake_chopper`;
6. `05_pc_and_5v_efuses`;
7. `06_esp32_wake_button`;
8. `07_ina228_analog`;
9. `08_can_led_io`;
10. `09_connectors_testpoints`.

Layout rules:

- separate the battery/main-FET, motion-FET, chopper, sensitive analogue, and digital/RF regions;
- place main FETs, motion FETs, shunts, and high-current terminals to minimize commutation loops;
- do not carry the 45-60 A path in ordinary PCB traces alone; use calculated broad pours on both outer layers plus dense via arrays and a specified copper-strip/busbar solution;
- make parallel-FET copper electrically and thermally symmetrical;
- route every shunt sense input as a matched Kelvin pair from dedicated shunt terminals; no load current may share these traces or vias;
- keep switch-node/gate-drive loops short and away from INA228, ADC dividers, CAN, crystal, antenna, and button nets;
- provide continuous signal reference under CAN and digital traces; do not split the logic return with high-current slots;
- provide an ESP32 antenna edge keep-out with no copper, components, chassis metal, or harness crossing, according to the selected module datasheet;
- keep brake-resistor connector and chopper FET at a board edge and away from the ESP32;
- place MOSFET and shunt temperature sensors at measured hot spots, not at convenient digital locations;
- use 100 V-rated semiconductors and appropriately derated passives in battery/motion domains unless a lower-voltage protected domain is proven;
- provide labelled test points for battery voltage, shunt Kelvin nodes, SYS bus, motion bus, 24 V sample, 5 V, 3.3 V, all enables, all fault lines, chopper gate, CAN TX/RX, and ground references;
- provide programming/recovery access without energizing motion outputs;
- use net ties or explicit star-point symbols where grounds intentionally meet; do not rely on hidden copper coincidence.

Board outline, mounting holes, keep-outs, enclosure airflow, allowed component height, connector exit directions, chassis heat-spreader contact, busbar geometry, and service access are all `BLOCKER` inputs. Astra may make an unrouted placement study before they are supplied, but not a final layout.

## 3. Provisional component classes

| Function | Selected class | Exact part status |
| --- | --- | --- |
| Main controller | LM74930-Q1 | controller locked; package/order code and passives to verify |
| Main monitor | INA228 | controller locked; package/order code provisional |
| Motion eFuse controller | TPS48110-Q1 | controller direction locked; exact implementation/timer open |
| Small branch eFuse | TPS26631, two channels | class locked; settings/package/order code open |
| Main FETs | 100 V NMOS, 3 per bank | `BLOCKER` |
| Motion FETs | 100 V NMOS, 2 per bank | `BLOCKER` |
| Chopper FET | 100 V low-side NMOS with pulse SOA | `BLOCKER` |
| Chopper comparator/reference/driver | independent analogue | `BLOCKER` |
| Main shunt | 0.5 mOhm 4-terminal, >=10 W, pulse-rated | `BLOCKER` exact part/footprint |
| Motion shunt | 0.5 mOhm 4-terminal, >=5 W | `BLOCKER` exact part/footprint |
| MCU module | ESP32-S3-WROOM-1 class | `BLOCKER` exact variant |
| CAN transceiver | 3.3 V logic, 1 Mbit/s, high bus-fault tolerance | `OPEN` |
| LED level shifter | 74AHCT125 class | `PROVISIONAL` |
| Always-on supply/latch | >=60 V input, low-Iq hardware domain | `BLOCKER` |
| Logic 3.3 V regulator | from regulated 5 V | `OPEN` |
| TVS/ESD | selected from measured environment and controller absolute limits | `BLOCKER` |

All exact parts must be active, orderable, and sourced from manufacturer datasheets. Marketplace product pages may define purchased module expectations, but they do not replace component datasheets, pulse curves, or thermal calculations.

## 4. Required Astra deliverables

Astra shall return the following on a dedicated branch or commit series:

1. a KiCad project with hierarchical schematic and preliminary four-layer PCB;
2. a requirements cross-reference mapping every `requirements.yaml` ID to sheet/reference/test point;
3. a BOM with manufacturer part number, package, voltage/current/temperature rating, lifecycle status, and at least one compatible alternative for every critical part;
4. main and motion FET loss/SOA/gate-drive calculations at 25 A, 45 A, 50 A, 60 A, 120 A transient, and 150 A/1-3 s survival case where applicable;
5. shunt dissipation, pulse-energy, Kelvin-error, and threshold-tolerance calculations;
6. motion/main/fuse/BMS selectivity analysis including worst-case component tolerances;
7. chopper voltage, hysteresis, power, pulse energy, repetition, MOSFET SOA, connector, and chassis thermal calculations;
8. eFuse ILIM/timer/retry calculations for PC, 5 V, and motion paths;
9. complete connector pin table and harness-current/temperature derating record;
10. power-off/start/hold/short-press/long-press/shutdown timing diagram;
11. ERC and DRC reports with no unreviewed exclusions;
12. an `OPEN_ITEMS.md` listing every unresolved blocker and any assumption Astra had to make;
13. a fabrication-release field that remains `false` until the project owner approves all blockers and the verification plan has evidence.

## 5. Fabrication-release blockers

At minimum, the following must be resolved before ordering a PCB:

- board envelope, mounting, connector orientation, maximum height, busbar, and chassis thermal interface;
- exact main/motion/chopper MOSFETs and their SOA/thermal/gate-drive proof;
- exact main and motion shunts, pulse ratings, and footprints;
- exact >=70 A battery terminals and final arm/chopper connector derating;
- external 60 A fuse DC rating and time-current curve;
- exact always-on wake/self-hold/forced-off circuit and timings;
- exact ESP32-S3 module and antenna arrangement;
- exact CAN transceiver, ESD, termination, and shield strategy;
- exact TPS26631 settings and external-converter startup/inrush envelopes;
- valid TPS48110 timer and selectivity implementation;
- measured main inrush supporting the no-precharge decision;
- measured regenerative energy and 24 V lift-bus behavior supporting the chopper choice;
- TVS/transient coordination below controller absolute maximum ratings;
- measured or bounded per-arm current supporting the final connector;
- explicit electrical and mechanical emergency-stop/motion-inhibit interface, which is not yet fully defined in the project.

Until these are closed, the output is an engineering prototype design for review and motorless testing only.
