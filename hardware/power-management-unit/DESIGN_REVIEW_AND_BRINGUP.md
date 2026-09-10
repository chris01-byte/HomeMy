# PMU Revision A design review and bring-up

`rev_a_engineering_prototype: true`  
`rev_b_production: false`  
Date: 2026-09-10. Review/test procedure only. No ordering, assembly, energization, actuator motion or completed CAD verification is recorded here.

Read [requirements traceability](REQUIREMENTS_TRACEABILITY.md), [assumptions](REV_A_ASSUMPTIONS.md), the [verification plan](verification-plan.md) and [Revision-B register](REV_B_VALIDATION.md) with the three circuit-design records. The project owner reviews the complete concrete package before ordering; work on the design and fabrication outputs can continue while measurement-only items remain open.

## Design review before order

Record a named reviewer, date, revision and disposition for each row. All rows are initially **unreviewed**. A manufacturer drawing or analytical bound is useful evidence; it does not replace the integrated netlist, layout or measured waveform.

| Gate | Review evidence required |
| --- | --- |
| D0 — Artifact consistency | Compare requirements, exact populated/DNP BOM, part JSON, hierarchical schematic, PCB, calculations, connector table and fabrication outputs. Confirm Revision-A metadata throughout. Record generated ERC/DRC reports and inspect every exclusion; **this document asserts no ERC/DRC pass**. |
| D1 — Locked topology/default state | Trace battery fuse→RSH1→main banks→SYS and all three SYS branches. Confirm common motion gate, passive arm outputs, no branch melting fuses/precharge, isolated lift sample and analog chopper downstream of motion gate. Verify MOSFET opposing orientation, reverse blocking, default motion OFF, deliberate main/motion reset and CAN backbone topology. |
| D2 — Exact physical pin/package audit | Compare each IC/FET/shunt/connector against its exact manufacturer drawing. Check U1 LM74930 exposed pad remains floating; U12 tab is3.3 V output; U11 DGS maps toMSOP10; U51 DRB0008A EP1.5×1.75 mm; U2 DGX missing physical pin16; Q1–Q10 CCPAK pad map; Q40 grouped HSOF map; D63 live cathode tab; four separate force/sense shunt contacts. Check all NC/DNC pins, ratings, passive order codes and DNP options. |
| D3 — Protection and proof gaps | Review threshold/timer corner models, native retry paths and external latches, AON startup blank and hold deadline. Explicitly disposition shared-shunt failure independence, main hot resistance at9.2 V gate, full940 µF motion-start SOA, boost-capacitor effective value, TVS peaks and resistor repetitive duty for the **specific proposed fixture**. Unsupported manufacturer guarantees must remain open or receive a conservative circuit/test restriction; do not silently label them Rev-B measurements. |
| D4 — Routed geometry and returns | Inspect true Kelvin pairs before pours, separate INA/U1 filters, equal FET force paths, short gate/commutation loops, local bypasses, dense vias, broad copper and segmented bars. No bar bridges a shunt/FET/protected bus. Follow all power returns to star; keep load/LED/shield currents outside logic/ADC necks. Check actual four mounting holes, clearances, ESP antenna exclusion on every layer and busbar/cover hardware. |
| D5 — Firmware/interface contract | Pin map matches eventual firmware; straps unused; recovery access cannot backpower the off ESP. All GPIO defaults/faults are defined. Heartbeat feed comes from the supervised loop; READY never arms motion. Current/voltage policy and LED/lifecycle requirements remain unimplemented until separately tested firmware exists. |
| D6 — Manufacture, assembly and procurement | Fabricator confirms4-layer70/35 µm stackup, drills/plating and Würth press-fit process. Check component heights, polarity, capacitor orientation, mounting/torque/heat spreading, exact cable mating parts/lugs/crimps, covers, labels and service access. Do not solder press-fit terminals by an unqualified process. Recheck lifecycle/availability and actual external converter terminals. |
| D7 — Order record | Owner reviews schematic, BOM, board, calculations, open assumptions, reviewed ERC/DRC and fabrication/assembly outputs. Record explicit disposition of open design proofs and future energization gates. Only then may the owner order the engineering prototype. No production or actuator authorization follows from this review. |

## Energization gates

| Gate | Mandatory evidence before its activity |
| --- | --- |
| E0 — Battery connection | Exact external60 A fuse, at least42 V DC (prefer≥60 V), suitable interrupt rating and source time-current curve; verified actual battery/BMS/port/polarity and external wiring. This remains open until documented. Do not attach a battery to substitute for a limited bench source. |
| E1 — Each initial bench fixture | Disconnected actuators; independently set source voltage/current/energy limits; measured capacitor population and stored voltage; correctly rated differential probes and loads; clear polarity/return diagram; reachable power removal. Close D3 for that fixture. Identify who reviews captured limits before advancing. |
| E2 — Any actuator test | Separate explicit authorization from an attending person, physical restraints/stands, clear workspace, reachable service disconnect/stop and one written current/speed/torque/energy/duration limit. J22 must not be permanently bypassed. Start with one unloaded axis after motorless stages pass. |

## Staged motorless tests

“Stop” means remove the fixture's energy source, wait and measure residual voltage, preserve the failure record, then review before any retry. The following stages are sequential approvals of evidence, not an instruction to run them now.

| Stage | Fixture, observations and pass condition |
| --- | --- |
| T0 — Unpowered inspection | With battery, converters, motor harnesses and resistor bank disconnected, inspect assembly/polarity, press-fit joints, shorts, isolation and power-star connections. Measure expected resistor/divider/shunt connectivity; compare every connector against its label. Check gate-source pulldowns and true Kelvin pads. Discharge capacitors and verify voltage before touching. |
| T1 — Logic/wake and fault-state fixture | Use current-limited AON/main input and a separately identified low-voltage bench fixture only where necessary to test5 V/3.3 V logic. Any deliberate external5 V injection at J11 invalidates a true OFF-current measurement until removed. Verify AON3.193–3.499 V modeled window, supervisor behavior and normal3.3 V. Run the button/fault table below with no actuators. Remove external5 V for final OFF/backpower checks. |
| T2 — Separate main and motion startup fixtures | **First main test:**20–30 °C starting assembly, ≤42 V/1 A supply, motion OFF, external converter inputs omitted until independently characterized, ≤100 µF total directly switched SYS capacitance. Capture VDS/gates/current; the reviewed cold SOA point covers only this bounded fixture and observed startup≤100 ms. **First chopper-bus preparation:** keep motion gate OFF and charge its populated940 µF bus through a separate current-limited fixture; do not treat it as≤100 µF. Connecting940 µF through the motion gate at1 A may cause native UV/OC interactions and is not promised to start. Full gate-powered motion startup requires its own source/energy/SOA disposition, observed waveforms and boost preparation; no full-battery start from an RC estimate. |
| T3 — Monitor/main/motion protection | Calibrate low current first, then approved higher points. Sweep UV/OV using an appropriate source with low available energy; record threshold, delay, both fault outputs and actual gate state. Inject controller fault indications using a reviewed low-voltage fixture before considering high-current faults. Verify native thermal retry and SYS-only UV recovery cannot re-arm U27. Do not create a battery short to “test120 A.” Full-current/short apparatus needs a separate reviewed plan. |
| T4 — Protected branch behavior | With electronic loads and characterized converter fixtures, measure U3/U4 ramp, current-limit, overload pulse, short/thermal response and main-cycle reset. Check that failure of one load cannot backfeed the off board. Confirm passive motion branches and absence of per-arm protection; current limiting remains necessary in the external fixture. |
| T5 — Analog chopper, isolated energy fixture | With stationary/disconnected motors and motion gate OFF, use a controlled source on the motion bus. Verify12–28 ms reference qualification, analog thresholds/hysteresis, independent46 V motion fault, continued dissipation after latch-off, NTC open/short/hot response and off-domain status isolation. Start with small energy pulses; record `integral(Vresistor×Iresistor dt)`, both resistor temperatures, gate/VDS/frequency and capacitor ripple. Only after those pass may the reviewed cold fixture approach500 J bank energy; repeat no sooner than60 s and only below40 °C on both cases. Stop for normal-cycle TVS conduction, excessive voltage/temperature or unbounded cycling. |
| T6 — Modules, CAN and LED | Independently validate actual external modules and their pinouts before joining them to the board: J8/J9/J10 input versus J11 regulated5 V return. Verify CAN end termination and short stub, unpowered/recessive behavior and bench traffic. Use a short strip first; prove5 V load capability electrically, without a software brightness limit. J13 remains DNP until a later24 V lift-output test. |
| T7 — Firmware/Linux with motion inhibited | Validate the eventual firmware and lifecycle implementation in simulation and a motorless fixture. Test all LED states, current/voltage policy, heartbeat, CAN loss, stopped services, boot deadline and controlled shutdown acknowledgement. Verify motion closes before recovery/shutdown, no stale green READY, and main hold is released only after acknowledgement or bounded fallback. Do not switch the development default away from graphical.target before homemy.target validation. |
| T8 — Integration decision | Review all raw captures and changed settings; reconcile actual capacitance/inrush, temperatures and protection interaction before combining fixtures or increasing load. Produce the separate bounded plan for B01–B14 work. E0 remains mandatory before battery; E2 before any actuator motion. |

The resistor bank is a current sink of only about8.6 A at43 V; source capability above it can raise bus voltage despite a working chopper. Capacitance and ESR set hysteretic frequency. The fitted940 µF bank stores up to approximately0.995 J at42 V initially; its bleed estimate of53.35 s to5 V is not permission to skip a voltage measurement.

## Button and fault acceptance table

| Stimulus | Signals and required observation |
| --- | --- |
| Battery/AON attachment with button already held | `BUTTON_ARMED` stays clear until physical release after AON good; no automatic main enable. Release then deliberately press to start. |
| Momentary start | ~174 ms nominal qualification raises WAKE_RAW_EN/AON_WAKE_EN; STARTUP_GRANT permits converter/ESP boot while motion stays OFF. |
| Hold transfer absent | `ESP_MAIN_HOLD` remains low; grant ends within its modeled4.80–5.27 s interval and actual main off meets the provisional≤5.4 s bench limit. |
| Successful hold transfer | Assert hold by4.7 s latest; grant expiry does not remove normal power. Hold alone never arms motion. |
| Short running press | `BUTTON_INT_N` requests controlled shutdown; it does not directly disable main hardware. Firmware first closes motion, obtains the stop/shutdown condition and then releases hold. |
| Long running press with hold stuck high | After release of the original start press, a new held press forces raw enable low without firmware. Measure the provisional4.1–9.5 s assembled-board window; do not call the nominal6.48 s a guaranteed limit. |
| Main fault and recovery | After~1–5.5 ms startup capture mask, MAIN_FAULT_N latches off; native U1 protection is active during mask. Sustained fault, short during mask, cleared fault and new press must follow reviewed controller/latch behavior. Recovery alone never starts main. |
| Switched3.3 V brownout | After SW_RESET_N has first gone high, its loss sets main latch even during startup grant. No automatic converter/ESP reboot from lingering grant. |
| ESP reset or missing watchdog | ESP_CHIP_EN low or ESP_WDO_N low clears motion latch. Later recovery does not arm it. Verify both during and after the startup interval. |
| Hardware permission removed | J22 open/low/unpowered clears MOTION_CLEAR_N and actual U2 INP; no new motion until healthy permission plus explicit reset edge and request. |
| Motion current/thermal/SYS UV/chopper fault | Each route clears U27. Include SYS dipping while3.3 V remains good; recovering native U2 UV/thermal must not restart. Very shallow/short dip coverage is measured, not guaranteed by a single comparator propagation value. |
| Chopper motion-off threshold | `CHOP_FAULT_N` clears motion; chopper keeps absorbing isolated bus energy until voltage drops or its independent thermal/supply protection intervenes. |

## Records and stop criteria

Each test record contains revision/options, source limit, load/capacitance, initial temperatures, instruments, calibration, waveform files, measured extrema and pass/fail disposition. Stop on any unexpected gate enable, automatic restart, input polarity issue, sense fault, overheating, abnormal TVS activity, supply collapse or exceeded component limit. Preserve evidence; change the circuit/fixture and repeat affected lower stages before advancing.

Successful motorless bring-up establishes only that tested envelope. The production measurements, final mechanical/harness work and final stop architecture remain in [REV_B_VALIDATION.md](REV_B_VALIDATION.md).

