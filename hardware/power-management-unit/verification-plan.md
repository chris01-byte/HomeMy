# HomeMy Power Management Unit (PMU) Verification Plan

Status: Revision-A bring-up and Revision-B production evidence plan; no hardware tests have been performed.  
Date: 2026-09-10.

## Purpose

This plan is the verification counterpart to `ASTRA_PCB_HANDOFF.md` and `requirements.yaml`. Revision A exists specifically to break the measurement/design dependency: V0 calculations and reviews gate its prototype order; V1-V6 measurements made with Revision A gate only the later Revision-B production design. Passing ERC/DRC alone is insufficient for either gate. Every test result must record board revision, schematic commit, firmware commit, equipment, setup, ambient temperature, raw data location, pass/fail result, and approver.

Real actuators remain disconnected or independently inhibited until a person present at the robot explicitly authorizes the bounded test. Start with simulation, circuit analysis, current-limited supplies, and passive loads.

## Evidence levels

| Level | Permitted setup | Purpose |
| --- | --- | --- |
| V0 | calculations, datasheets, SPICE, ERC/DRC | complete and review the Rev-A prototype before ordering |
| V1 | unpowered Rev-A PCB inspection and continuity | assembly and isolation checks |
| V2 | current-limited bench supply, no battery, no motors | controller and protection bring-up |
| V3 | battery simulator or protected battery, passive/electronic loads | current, inrush, thermal, and chopper tests |
| V4 | connected converters and Linux, motion gate physically inhibited | lifecycle and load validation |
| V5 | supervised single-actuator tests | bounded transient and regeneration evidence |
| V6 | supervised integrated robot tests | final coordination and duty-cycle evidence |

No level may be skipped during physical bring-up because a lower-level test appears likely to pass. Measurements unavailable before hardware shall be recorded as Revision-B validation items, not used as a reason to leave Revision A incomplete.

## V0: Revision-A design review before ordering

### Schematic and component evidence

- Cross-reference every ID in `requirements.yaml` to a schematic sheet, part, net, test point, calculation, documented Revision-A assumption, or Revision-B measurement.
- Check controller absolute maximum ratings for battery hot-plug, chopper operation, cable inductance, gate transients, reverse polarity, and ground offsets.
- Verify exact packages, pin numbers, exposed pads, thermal vias, no-connect pins, default pull states, and power sequencing from manufacturer datasheets.
- Verify every fault/enable line has a defined state while the ESP32 is unpowered, resetting, booting, or disconnected.
- Prove that the motion gate defaults off independently of firmware.
- Prove that an open, unpowered, or disconnected external motion-inhibit input keeps the motion gate off.
- Prove that the wake latch can start from the unpowered state and cannot automatically restart after a latched fault or battery reconnection.
- Verify I2C/CAN/ADC logic levels and that no signal back-powers an unpowered domain.
- Verify that the chopper analogue control remains powered from the isolated motor-side energy after main/motion switch opening.

### Electrical calculations

- Calculate main and motion MOSFET conduction, switching/turn-off, pulse, SOA, and thermal behavior with maximum hot RDS(on), not typical room-temperature values.
- Include 25 A, 45 A, 50 A, 60 A, 100/120 A short transient, and 150 A for 1-3 s where the stage can experience it.
- Calculate paralleled-FET gate charge, drive time, individual gate resistors, current sharing, and layout imbalance sensitivity.
- Calculate both shunts at DC and pulse conditions, including terminal/PCB heating and sense error from copper and input-filter bias/leakage.
- Run a worst-case tolerance analysis for undervoltage, overvoltage, overcurrent, short circuit, chopper thresholds, hysteresis, and ADC divider limits.
- Plot coordination among motor limits, software actions, TPS48110 trip, LM74930 trip, 60 A fuse curve, and BMS behavior.
- Demonstrate a realizable TPS48110 timing solution; do not accept an impractically large/leakage-sensitive timing capacitor.
- Calculate conservative, adjustable Revision-A PC and 5 V TPS26631 limits, startup blanking, thermal foldback, and retry/latch behavior from the documented provisional load envelopes. Validate and, if necessary, revise them after measuring the selected converters.
- Calculate a conservative Revision-A chopper envelope from bounded kinetic and gravitational assumptions, not only resistor nameplate power. Replace this estimate with measured energy before Revision-B release.
- Check CAN termination, stub length, common-mode range, ESD current path, and shield/chassis connection.

### Layout review

- Confirm fabricator-approved four-layer stack-up and current-carrying copper/busbar construction.
- Review high-current loop area, FET symmetry, shunt Kelvin paths, star return, creepage/clearance, via current/thermal density, connector temperature rise, and chassis heat flow.
- Review separation of chopper/gate-drive nodes from INA228, ESP32 ADC, CAN, oscillator, antenna, and Power-button nets.
- Confirm all required test points remain accessible after assembly and installation.
- Confirm the ESP32 antenna keep-out against enclosure metal, busbars, battery, and harnesses.
- Obtain project-owner review of the Revision-A schematic, BOM, layout, calculations, and assumptions list before ordering; a second qualified review is strongly preferred.

## V1: incoming PCB and unpowered assembly

- Photograph and identify board revision, assembly revision, shunts, MOSFETs, controllers, connectors, polarity markings, and fuse interface.
- Inspect polarity, solder voiding, exposed pads, press-fit/stud installation, busbars, isolation slots, and thermal-interface material.
- Measure resistance/continuity for every power path with converters and loads disconnected.
- Confirm no short between positive buses, returns, shield/chassis, gates, sense lines, and logic rails.
- Verify Kelvin sense traces terminate only at dedicated shunt terminals.
- Verify motion enable is electrically inactive with the ESP32/module absent.
- Check programmed resistor values independently against the calculation sheet.

## V2: current-limited motorless bring-up

Use a current-limited supply with an explicit energy limit. Start below nominal battery voltage and at a current insufficient to damage the board.

1. Verify off-state current and that ESP32, LED, Linux branches, and motion bus are off.
2. Exercise the Power button and observe the hardware wake interval before fitting/enabling the ESP32.
3. Verify 5 V and 3.3 V sequencing, brownout behavior, reset behavior, and hold transfer.
4. Verify short press produces only a shutdown request.
5. Verify the hardware long-press fallback with no firmware response.
6. Verify power removal and reconnection do not cause automatic restart.
7. Verify every fault input closes the motion gate and latches as designed.
8. Open and disconnect the hardware motion-inhibit input and verify that motion power cannot enable.
9. Verify CAN transmit/receive and termination selection using a controlled bus fixture.
10. Verify LED states with a short test strip; software brightness is not credited as overcurrent protection.

## V3: measurement, eFuse, switch, and chopper tests

### INA228 and shunts

- Calibrate voltage, signed current, power, energy, and charge at zero and at multiple positive/negative current points.
- Compare against a traceable reference at approximately 1 A, 5 A, 25 A, 45 A, and the highest safe bench point.
- Measure offset after thermal soak and after high-current pulses.
- Inject sense-open/sense-short faults where safe and verify diagnostic behavior.

### Main and motion switches

- Measure path resistance and temperature distribution across every parallel MOSFET.
- Capture gate, drain-source voltage, shunt voltage, supply voltage, and fault outputs during enable, disable, overload, and short tests.
- Validate UV/OV thresholds on rising and falling voltage, including delay and hysteresis.
- Validate overcurrent and short thresholds with worst-case resistor tolerances.
- Verify hard trips latch and require the intended deliberate reset.
- Verify motion faults do not require the external main fuse to open.
- Increase load only after each lower-current result passes and is reviewed.

### Inrush and no-precharge decision

- Test with the final external 12 V, 24 V, and 5 V converters and representative output capacitance.
- Capture peak current, duration, battery/simulator sag, gate waveform, connector behavior, and FET temperature.
- Repeat at 27.5 V, 36 V, and 42 V and across expected temperature extremes.
- Keep the no-precharge decision only if all limits and reliable starts pass with margin.

### Brake chopper

- Use a controlled regenerative-energy emulator or programmable source before any motor test.
- Verify off/on thresholds, hysteresis, analogue independence from ESP32, status output, overtemperature response, and hardware motion-off at the upper threshold.
- Capture resistor current sharing and both resistor temperatures.
- Apply the calculated worst approved pulse and repetition pattern; remain below manufacturer pulse curves and chassis temperature limits.
- Test chopper open, MOSFET/gate stuck off, and a controlled stuck-on simulation.
- Verify a chopper fault cannot drive current into the battery.
- Treat any TVS conduction during normal chopper cycling as a failure.

### Small branches and external converters

- Characterize the PC converter and 5 V converter separately at 27.5 V, 36 V, and 42 V.
- Measure efficiency, startup current, current limit, short response, thermal equilibrium, output ripple, input transients, and recovery.
- Demonstrate the PC eFuse allows normal startup while protecting its harness. Confirm the 65 W policy separately in Linux/BIOS; do not infer it from the eFuse setting.
- Demonstrate the 5 V converter supports the maximum physical LED/logic load without relying on a software current limit.
- Characterize the 24 V lift converter with two electronic loads up to the planned 4-5 A continuous total and its labelled 10 A claim only within safe test limits.

## V4: Linux lifecycle with motion inhibited

- Boot basic Ubuntu and repeat the existing approximately 25 W battery-side baseline measurement.
- Run the intended ROS nodes, sensors, logging, CAN/RS485 adapters, and realistic CPU load.
- Configure and verify the approximately 65 W battery-side computer/sensor budget using BIOS/RAPL or the final Linux mechanism.
- Verify `homemy.target` boots without a GUI/login and `graphical.target` remains available for development.
- Verify heartbeat, power telemetry, dashboard, logs, button events, and every LED lifecycle state.
- Verify a short press closes the motion gate, logs final state, shuts Linux down, and only then releases main self-hold.
- Verify failed boot, lost heartbeat, frozen user space, lost CAN, and missing shutdown acknowledgement.
- Verify hard hardware trips protect the battery even if Linux and ESP32 software are non-responsive.

## V5: bounded actuator evidence

Requires an attending person's explicit authorization, physical restraints/stands, a reachable emergency stop or service disconnect, cleared workspace, and a written single-test limit.

- Test one ESS23 drive channel at a time, then the pair, while capturing supply current and regenerative bus voltage.
- Test one ESS17 lift at a time without payload, then both, while capturing 24 V output overshoot during commanded lowering/deceleration and forced stop.
- Decide whether the DNP local 24 V clamp becomes necessary from the measured output.
- Test one RobStride joint at a time with conservative torque/speed limits; measure battery and arm-branch current.
- Build an enforceable per-arm current envelope and validate the selected connector/contact/wire temperature.
- Characterize stop/deceleration settings that limit regeneration without weakening commanded stop behavior.

## V6: integrated coordination

- Exercise representative simultaneous drive, lift, arm, compute, sensor, and LED loads while keeping normal battery current no greater than 45 A.
- Demonstrate warn/derate above 45 A, controlled motion stop above 50 A, and independent hardware protection without opening the 60 A fuse during expected recoverable faults.
- Test low-battery warning, task rejection, controlled shutdown, hardware undervoltage latch, and deliberate restart after voltage recovery.
- Verify the full CAN traffic target at 1 Mbit/s and 100 Hz joint updates remains below 50 percent measured utilization with adequate error margin.
- Measure worst-case enclosure and chassis temperatures at the approved duty cycle and ambient range.
- Repeat regenerative scenarios using the maximum approved simultaneous axes and payload.
- Confirm no protection recovery automatically grants motion.

## Release records

### Revision-A prototype order record

The Revision-A fabrication package may be ordered after all of the following are recorded:

- every `REV_A_DESIGN` requirement has an exact circuit/part/footprint or a documented safe alternative;
- every `REV_A_ASSUMPTION` has a conservative value, adjustment method, test point, and linked Revision-B measurement;
- all `REV_A_ENERGIZATION_GATE` items are either closed or explicitly labelled as required before battery power;
- schematic, BOM, layout, calculations, and assumption record have project-owner review;
- ERC/DRC and manufacturing-rule reports have no unreviewed exclusions;
- initial bring-up procedure uses a current-limited supply, disconnected actuators, and an accessible service disconnect.

This record authorizes only a functional engineering prototype. It is not a claim of product safety, production readiness, or unrestricted actuator operation.

### Revision-B production record

Production release additionally requires:

- all `rev_b_production_validation_gates` from `requirements.yaml` closed;
- reproducible calculation files updated with measured values;
- oscilloscope captures and thermal images for inrush, trips, switching, regeneration, and chopper tests;
- calibrated INA228 results and converter reports;
- connector/harness temperature and pull/retention evidence;
- firmware/Linux versions and fault-injection results;
- final mechanics, motion-safety architecture, deviations, residual risks, and rollback instructions.

Until the Revision-B record exists, Revision A remains a prototype for controlled motorless or explicitly supervised tests.
