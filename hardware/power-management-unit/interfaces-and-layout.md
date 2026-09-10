# HomeMy Power Management Unit (PMU) Interfaces and Layout

Status: Revision-A engineering-prototype layout and fabrication package authorized after human design review; production release is false.  
Date: 2026-09-10.

## 1. Prototype-first rule

Revision A must be a complete, functional measurement prototype. Missing values that can only be measured on hardware do not block its schematic, layout, BOM, or fabrication-package generation. Astra shall instead:

- select exact electronic parts and footprints from current manufacturer data;
- use conservative, configurable values and accessible test points;
- use a generous bench-prototype outline with provisional mounting and connector placement;
- prefer replaceable external modules, terminal blocks, resistor banks, option resistors, DNP positions, and rework access where uncertainty remains;
- record every assumption and the measurement that will confirm or change it.

The owner reviews the complete Revision-A package before ordering. Revision-B production release remains false until the measurements in `verification-plan.md` are complete.

## 2. Connector and harness plan

Identifiers below are functional names; Astra assigns reference designators and exact Revision-A orderable parts. Exact production suffixes and enclosure integration may change in Revision B.

| Function | Revision-A interface basis | Pins / current basis | Status |
| --- | --- | --- | --- |
| Battery positive/negative | covered M5 ring-lug studs or >=70 A DC terminal class | 6 mm2; at least 70 A design class | `REV_A_DESIGN` |
| Left arm | Mega-Fit candidate or higher-current locking terminal | +/return; 4 mm2; provisional 25 A continuous | `REV_A_DESIGN`; validate in Rev B |
| Right arm | Mega-Fit candidate or higher-current locking terminal | +/return; 4 mm2; provisional 25 A continuous | `REV_A_DESIGN`; validate in Rev B |
| Two ESS23 drive motors | Micro-Fit 3.0 2-pin candidate | +/return; common feed about 8 A peak setting; 1.5 mm2 trunk | `REV_A_DESIGN` |
| External 24 V lift buck input | Micro-Fit 3.0 2-pin candidate | motion +/return; expected 4-5 A input; 1 mm2 | `REV_A_ASSUMPTION` |
| Optional 24 V clamp sense | DNP 2-pin service connector | 24 V output/return | `PROVISIONAL` |
| External PC buck input | Micro-Fit 3.0 2-pin candidate | protected system +/return; about 3 A allowed; 0.75 mm2 | `REV_A_ASSUMPTION` |
| External 5 V buck input | Micro-Fit 3.0 2-pin candidate | protected system +/return | `REV_A_ASSUMPTION` |
| Regulated 5 V return to PCB | Micro-Fit 3.0 2-pin candidate | +5V/return; up to 5 A; 1 mm2 | `REV_A_ASSUMPTION` |
| Chopper resistor | locking terminal rated above the 8.6 A pulse case | resistor high/low; 1.5 mm2 high-temperature wire | `REV_A_DESIGN`; validate in Rev B |
| LED strip | locking 3-pin | +5V, DATA, GND | `REV_A_DESIGN` |
| Power button | locking 2- or 3-pin | switch and return; optional shield | `REV_A_DESIGN` |
| Hardware motion inhibit | locking 2-pin commissioning input | open/unpowered/disconnected forces motion off | `LOCKED` behavior; exact circuit is `REV_A_DESIGN` |
| CAN | JST-GH 4-pin candidate | CAN_H, CAN_L, CAN_GND, shield/NC | `REV_A_DESIGN` |
| NTCs / service signals | locking small-signal multi-pin | 0.14-0.25 mm2 | `REV_A_DESIGN` |

The previously considered Würth `7466003R` 50 A SMT part is not acceptable for the battery path because it lacks margin. Do not use XT-series connectors in the final product. They may be used only in a clearly labelled Revision-A bench harness outside the PCB when this improves safe reconfiguration.

Individual RobStride wire after the arm distribution is expected in the 1-2.5 mm2 range and remains part of the arm harness, not this board.

## 3. PCB partition and layout constraints

Starting stack-up is four layers, 2 oz outer copper and 1 oz inner copper, subject to the chosen prototype fabricator's confirmed capabilities.

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
- apply the selected ESP32 module's antenna keep-out at a board edge;
- keep brake-resistor connector and chopper FET at a board edge and away from the ESP32;
- place temperature sensors at the predicted hot spots of shunts and MOSFET banks;
- use 100 V-rated semiconductors and appropriately derated passives in battery/motion domains unless a lower-voltage protected domain is proven;
- provide labelled test points for battery voltage, shunt Kelvin nodes, SYS bus, motion bus, 24 V sample, 5 V, 3.3 V, all enables, all fault lines, chopper gate, CAN TX/RX, and ground references;
- provide programming/recovery access without energizing motion outputs;
- use net ties or explicit star-point symbols where grounds intentionally meet.

### Revision-A mechanical assumption

Astra shall choose a generous rectangular bench-prototype outline sized around the completed circuitry, thermal copper, safe clearances, connector access, four mounting holes, and an unobstructed antenna edge. Connector directions, mounting coordinates, component-height envelope, airflow, busbar geometry, and chassis heat-spreader contact shall be documented as provisional dimensions. These missing final-enclosure inputs do not justify leaving the PCB unrouted. Revision B adapts the proven circuit to the final enclosure.

## 4. Revision-A component ownership

| Function | Required class | Revision-A action |
| --- | --- | --- |
| Main controller | LM74930-Q1 | select package/order code and calculate all support parts |
| Main monitor | INA228 | select package/order code and input/filter parts |
| Motion controller | TPS48110-Q1 | implement a realizable configurable timer and retry behavior |
| Small branch eFuses | two TPS26631 channels | select package, ILIM, timer, and retry/latch networks |
| Main FETs | 100 V NMOS, 3 per bank | select exact active part and prove hot loss, SOA, gate drive, and transient margin |
| Motion FETs | 100 V NMOS, 2 per bank | select exact active part and prove hot loss, SOA, gate drive, and transient margin |
| Chopper FET | 100 V low-side NMOS | select exact active part with pulse-SOA and thermal margin |
| Chopper control | independent analogue | select comparator, reference, driver, hysteresis, and hardware overtemperature path |
| Main shunt | 0.5 mOhm 4-terminal, >=10 W, pulse-rated | select exact part and footprint |
| Motion shunt | 0.5 mOhm 4-terminal, >=5 W | select exact part and footprint |
| MCU module | ESP32-S3-WROOM-1 class | select exact module variant and antenna keep-out |
| CAN transceiver | 3.3 V logic, 1 Mbit/s, high bus-fault tolerance | select transceiver, ESD, common-mode, shield, and termination parts |
| LED level shifter | 74AHCT125 class | select exact part |
| Always-on supply/latch | >=60 V input, low-Iq hardware domain | design exact wake/self-hold/forced-off circuit |
| Logic 3.3 V regulator | from regulated 5 V | select exact part and decoupling |
| TVS/ESD | coordinated below controller absolute maximum ratings | select from calculated Rev-A environment; confirm with Rev-A waveforms |

All exact parts must be active and orderable when selected and must be justified from manufacturer datasheets. Marketplace pages may define purchased module expectations, but they do not replace component datasheets, pulse curves, or thermal calculations.

## 5. Required Astra deliverables

Astra shall return the following on a dedicated branch or commit series:

1. a complete KiCad project with hierarchical schematic and routed four-layer Revision-A PCB;
2. a requirements cross-reference mapping every `requirements.yaml` ID to a sheet, reference, net, test point, calculation, assumption, or Revision-B measurement;
3. a BOM with manufacturer part number, package, rating, lifecycle status, supplier evidence, and at least one compatible alternative for each critical part;
4. main and motion FET loss/SOA/gate-drive calculations at 25 A, 45 A, 50 A, 60 A, 120 A transient, and the applicable 150 A/1-3 s survival case;
5. shunt dissipation, pulse-energy, Kelvin-error, and threshold-tolerance calculations;
6. preliminary motion/main/fuse/BMS selectivity analysis including worst-case component tolerances;
7. chopper threshold, hysteresis, power, pulse, MOSFET-SOA, connector, and preliminary thermal calculations;
8. eFuse ILIM/timer/retry calculations for PC, 5 V, and motion paths;
9. complete connector pin table and provisional harness-current record;
10. power-off/start/hold/short-press/long-press/shutdown timing diagram;
11. ERC and DRC reports with no unreviewed exclusions;
12. assembly drawings, Gerbers, drill files, position files, and BOM as a clearly labelled Revision-A prototype package;
13. `REV_A_ASSUMPTIONS.md` with every provisional choice, adjustment range, test point, and safe initial setting;
14. `REV_B_VALIDATION.md` mapping each post-build measurement to the affected production decision;
15. release metadata stating `rev_a_engineering_prototype: true` and `rev_b_production: false`.

## 6. Release gates

### Complete before Revision-A ordering

- all exact PCB-mounted parts, footprints, pinouts, default states, adjustment ranges, and test points selected;
- a complete schematic and routed layout with reviewed ERC/DRC exceptions only;
- calculations demonstrate a plausible safe Revision-A operating envelope;
- provisional board mechanics and external-module connector pinouts are explicit;
- external 60 A fuse exact DC rating and time-current curve are identified before battery power is applied;
- hardware motion-inhibit input is present and motion defaults off;
- first bring-up uses a current-limited supply, with actuators disconnected;
- project-owner review of schematic, BOM, layout, calculations, and assumptions is recorded.

### Measure with Revision A before Revision-B production release

- main-path inrush and the no-precharge decision;
- regenerative energy, chopper pulse/repetition/thermal margin, and 24 V lift-bus behavior;
- 12 V PC, 5 V, and 24 V external-converter startup, limit, efficiency, ripple, transient, and thermal behavior;
- actual arm, drive, lift, compute, and simultaneous-system current envelopes;
- connector, cable, shunt, MOSFET, resistor, PCB, and enclosure temperatures;
- fuse/BMS/main/motion protection selectivity and fault behavior;
- final board outline, mounting, airflow, busbar, enclosure, service access, and chassis heat spreader;
- final product emergency-stop/motion-safety architecture and harness qualification.

These Revision-B measurements may change component ratings, settings, connector series, copper reinforcement, thermal design, or mechanics. They do not prevent construction of the Revision-A measurement prototype.
