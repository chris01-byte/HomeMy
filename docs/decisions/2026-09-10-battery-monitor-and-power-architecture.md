# HomeMy Power Management Unit (PMU) Architecture

Status: accepted architecture; complete Revision-A measurement prototype authorized; Revision-B production validation pending.  
Date: 2026-09-10.

## Context

This decision records the agreed battery, power-path, monitoring, regeneration-protection, customer power-button, status-indicator, compute-power, actuator, and communication assumptions for the HomeMy prototype. The resulting central subsystem is named the HomeMy Power Management Unit (PMU). It is the current design memory for later schematic, firmware, Linux, and commissioning work.

Values marked **initial** are accepted starting points for commissioning, not measured final limits. No real-hardware protection test has yet validated this architecture.

## Prototype-first development decision

The PMU will be developed in two explicit revisions to avoid a circular dependency between PCB design and measurements:

- **Revision A** is a complete, functional engineering prototype used to obtain the missing electrical and thermal evidence. Astra is expected to finish its schematic, exact prototype-component selection, PCB layout, calculations, BOM, test points, and fabrication package.
- Unknowns that are normal component-design work are selected by Astra from primary manufacturer data. Unknowns caused by missing production mechanics or load measurements receive conservative, documented, configurable Revision-A assumptions.
- Only conditions necessary to energize the prototype safely, such as a suitably DC-rated external main fuse and a current-limited bring-up setup, remain gates before power is applied. They do not block completing the PCB.
- **Revision B** is the later production-oriented redesign. Revision-A measurements decide its final protection settings, connectors, copper reinforcement, thermal design, converter acceptance, mechanics, precharge decision, and chopper energy rating.

Revision A is not approved for customer use, unattended operation, or unrestricted motion. Its fabrication package may be generated and, after project-owner design review, ordered for controlled bring-up and measurements.

## Decision

## Battery

The selected battery is the LERIAN POWER 36 V, 17.5 Ah lithium-ion pack sold as article 36175:

- 10S7P, 18650 cells;
- 36 V nominal, 42 V charge voltage;
- 17.5 Ah and 630 Wh;
- 27.5 V BMS cut-off;
- 50 A maximum continuous discharge;
- 150 A advertised peak discharge for 1-3 s;
- separate charge and discharge ports;
- supplied discharge cable with 60 A fuse;
- 290 x 118 x 70 mm and approximately 3.8 kg;
- not approved by the supplier for regenerative charging, series connection, or parallel connection.

The design therefore treats 50 A as the maximum continuous battery current. The 150 A value is a short fault/acceleration survival case, not a normal operating target. The 60 A fuse and its final time-current characteristic must be coordinated with the electronic limits before motion tests.

Source: <https://www.akkushop-24.de/Lithium-Ionen-Akkupack-36V-175Ah-50A-inkl-50A-BMS-fuer-Scooter-Pedelec-Roller>

## Actuator and Load Assumptions

The current prototype plan is:

- two ESS23-RS20 integrated RS485 closed-loop stepper motors for the differential drive, operated directly from the 27.5-42 V battery bus;
- a tested 10:1 mechanical reduction on the drive, with sufficient self-locking for the current prototype;
- two arms with six joints each;
- RobStride RS02 planned for J1-J4 on each arm, eight total;
- RobStride RS00 planned for J5-J6 on each arm, four total;
- an additional reduction planned for J2 and J3; joint selection and reduction remain under test;
- one 24 V ESS17-RS07 for each arm's vertical tower lift, two total, supplied through a dedicated 24 V converter;
- both vertical lifts may operate simultaneously;
- each lift uses a mechanically self-locking trapezoidal screw;
- no arm brake or counterweight is planned. On complete power loss the arms may hang or fall vertically when the lift is high enough; this is an accepted prototype limitation, not a safety guarantee;
- drive, lifts, arms, compute, and sensors may be active simultaneously.

The onboard Linux-computer budget is based on the discussed i5-9600K system without a discrete GPU. The measured basic Ubuntu and sensor load was approximately 25 W at the battery side before the DC/DC converter, without ROS nodes. The complete compute/sensor branch is to be limited to approximately 65 W at the battery side. This limit is enforced through the final Linux/BIOS CPU-power configuration and verified under the final ROS workload. The branch has no dedicated current sensor; the central INA228 still measures the complete robot.

The existing adjustable Chinese 8-55 V to 1-36 V buck converter is planned for the 12 V computer branch. Its seller ratings are not accepted as proof of continuous capability; it requires load, thermal, transient, and low-battery testing. A separate 24 V converter is planned for the two ESS17 lift motors and also requires testing.

## Power-Path Topology

The planned discharge path is:

1. battery discharge port;
2. supplied 60 A main fuse;
3. 0.5 mOhm four-terminal shunt;
4. LM74930-Q1 controller with external back-to-back N-channel MOSFET banks;
5. protected HomeMy DC bus;
6. resettable electronically protected small-load branches and a separately controlled motion gate.

The charge port remains separate and is used only with the supplied 42 V charger.

The LM74930-Q1 is the selected design direction for:

- electronic main power-path ON/OFF control;
- reverse-current blocking from the robot bus toward the battery;
- hardware undervoltage, overcurrent, and short-circuit response;
- low-current shutdown without a user-facing mechanical master switch.

The Gigavac GXL14 latching contactor was evaluated and rejected because its 350 A class, approximately 500 g mass, physical size, and cost are disproportionate for HomeMy.

The initial MOSFET concept uses two opposing banks with three parallel 100 V N-channel MOSFETs per bank, six MOSFETs total. The desired individual device class is no more than approximately 1.5 mOhm at 25 degrees C in a power package suitable for chassis heat spreading. Using a conservative 2.5 mOhm hot resistance per device gives approximately 1.67 mOhm for the complete two-bank path:

| Total current | Approximate hot path loss |
| ---: | ---: |
| 25 A | 1.0 W |
| 50 A | 4.2 W |
| 60 A | 6.0 W |
| 150 A | 37.5 W |

This is a sizing hypothesis. The final MOSFET must be selected using maximum hot RDS(on), package current, transient thermal impedance, safe operating area, gate charge, and availability. The 150 A/1-3 s case must be verified thermally.

No separate precharge circuit is planned initially because the observed/expected inrush is considered manageable. Commissioning must still measure peak current, pulse duration, battery sag, MOSFET temperature, and reliable startup. A later revision remains a fallback if these tests fail.

The updated branch-protection direction is intentionally simple and resettable:

- the supplied 60 A battery fuse is the only melting fuse and remains the last-resort protection;
- a common TPS48110-Q1 motion gate protects two passive arm outputs, the common ESS23 drive output, and the external 24 V lift-converter input;
- no per-arm eFuse, MOSFET, shunt, or temperature sensor is planned;
- TPS26631 eFuses protect the external computer-converter input and the external 5 V converter input;
- the external 24 V lift converter relies on its verified internal protection plus the common motion gate;
- electronic hard faults latch and do not autonomously repeat retries.

The initial motion-stage concept uses a separate 0.5 mOhm, at least 5 W four-terminal shunt and two parallel 100 V N-channel MOSFETs in each opposing bank, four total. Initial motion thresholds are approximately 60 A overcurrent and 100 A fast short circuit. The requested approximately 0.5 s overcurrent timing is not final until the TPS48110 timing range, capacitor leakage/tolerance, and protection selectivity are calculated from the current datasheet.

## Measurement

The central monitor uses:

- INA228, 85 V, 20-bit, bidirectional current/power/energy/charge monitor;
- 0.5 mOhm four-terminal shunt;
- preferred shunt rating of at least 10 W with documented pulse capability of at least approximately 34 J;
- high-side placement immediately after the 60 A main fuse;
- ESP32-S3-DevKitC-1 / ESP32-S3-WROOM-1-N8 for the prototype controller.

Expected shunt values are:

| Current | Shunt voltage | Shunt power |
| ---: | ---: | ---: |
| 45 A | 22.5 mV | 1.01 W |
| 50 A | 25 mV | 1.25 W |
| 60 A | 30 mV | 1.80 W |
| 120 A | 60 mV | 7.20 W |
| 150 A | 75 mV | 11.25 W |

The INA228 range of plus/minus 163.84 mV corresponds to approximately plus/minus 327.7 A with this shunt. INA228 measurements are diagnostic and supervisory; the fuse, BMS, and independent hardware path provide final fault protection.

Sharing this shunt with the LM74930-Q1 current-sense inputs is a candidate to avoid a second high-current loss. It is not accepted until the final schematic validates common-mode range, polarity, thresholds, filtering, Kelvin routing, and fault independence.

State of charge will ultimately combine coulomb counting with voltage plausibility and learned/internal-resistance compensation. A simple linear voltage-to-percent conversion is not considered adequate for the final system.

## Initial Protection Thresholds

### Battery voltage

| Condition | Initial response |
| --- | --- |
| Above 33.0 V | Normal operation |
| Below 33.0 V for 10 s | Warning; status LED amber |
| Below 31.5 V for 5 s | Reject new work and request return to charging location |
| Below 30.5 V for 5 s | End motion and request controlled Linux shutdown |
| Below 29.0 V for 0.5 s | Hardware power-path latch-off |
| 27.5 V | Battery BMS last-resort cut-off |

Short motor-induced voltage dips must be filtered or compensated. After a hardware undervoltage cut-off there is no automatic restart. A deliberate button press and a recovered voltage of approximately 32 V or higher are required.

### Battery current

| Condition | Initial response |
| --- | --- |
| Up to 45 A | Normal operation |
| Above 45 A for more than 1 s | Warning and commanded torque/power reduction |
| Above 50 A for more than 2 s | Stop motion and record a fault |
| Motion current around 60 A | Common motion-gate hardware latch-off; delay remains to be validated |
| Total battery current around 65 A for approximately 0.5 s | Main-path hardware latch-off |
| Above approximately 120 A | Fast short-circuit latch-off |

The LM74930-Q1 default 20 mV short-circuit threshold would equal 40 A with a 0.5 mOhm shunt and must therefore be programmed for the intended approximately 60 mV/120 A starting point. All current thresholds remain subject to tolerance analysis, fuse-curve coordination, measured motor transients, and supervised fault injection.

## Regeneration and Bus Overvoltage

Because the battery is not approved for regeneration, normal operation must not send generated energy into the battery. The LM74930-Q1 reverse-current function isolates the battery. A brake chopper on the protected motor bus absorbs generated energy.

The updated chopper concept is:

- two external 10 ohm/100 W aluminium-housed resistors in parallel, 5 ohm effective;
- at least 500 J documented pulse-energy capability for the complete bank and verified duty cycle;
- 100 V low-side MOSFET with suitable gate driver;
- independent analogue comparator and hysteresis, not ESP32-only control;
- temperature sensing on the resistor;
- no melting branch fuse; current, temperature, and main/motion electronic protection handle a stuck-on fault;
- installation on a metal heat spreader away from the printed polymer enclosure.

At 43 V, 5 ohm draws 8.6 A and dissipates approximately 370 W while active, about 185 W per resistor. The 100 W nameplate is not a continuous rating at this operating point. Exact pulse curves, chassis thermal resistance, repetition rate, and measured regenerative energy must prove this choice; otherwise the resistor technology or rating must increase.

Initial motor-bus thresholds are:

| Bus voltage | Initial response |
| ---: | --- |
| Below 42.4 V | Chopper off |
| 43.0 V | Chopper on |
| 43.5 V | Log overvoltage warning |
| 45.0 V | Reduce regenerative braking and command controlled motor stop |
| 46.0 V | Remove hardware motor enable |

TVS devices are transient clamps only and must not absorb normal braking energy. Exact resistor, MOSFET, comparator, gate driver, thermal cut-out, TVS, and energy limits remain open until arm mass, speed, simultaneous-axis cases, and measured bus waveforms are available.

The chopper controller must be powered from and connected across the protected motor bus so it can continue dissipating stored/regenerated energy after the battery path opens. A chopper-open fault causes motor inhibition. A stuck-on chopper causes battery-path shutdown after diagnostics and requires an independent thermal fallback.

## Customer Power Button and Shutdown

HomeMy has one customer-facing Power button and no customer-facing mechanical master switch.

Accepted behavior:

1. A deliberate press asserts the hardware enable/start path.
2. The electronic power path starts the ESP32, status LED, and onboard Linux computer.
3. The ESP32 takes over electrical self-hold after successful startup checks.
4. The motion gate remains closed throughout boot and self-test.
5. Customer Linux boots through `homemy.target` without an Ubuntu desktop, login, terminal, or manual ROS command.
6. A short press while running is a controlled shutdown request, not an immediate power cut.
7. HomeMy rejects new work, closes and verifies the motion gate, records final state, requests OS shutdown, and only then releases the electronic main path.
8. A long press provides a forced-shutdown fallback. Exact debounce, long-press duration, grace timeout, and hardware implementation remain to be selected and tested.
9. Hardware undervoltage, overcurrent, short circuit, or critical thermal faults may override Linux and remove power.
10. No fault or power recovery automatically authorizes motion or automatically restarts the robot.

Linux heartbeat loss must first close the independent motion gate. The ESP32 then records the available fault information and follows the defined timeout/fallback path. The BMS and fuse remain the last protection layer if controller electronics fail.

## Customer Status and Diagnostics

HomeMy has no permanently installed graphical display. A short addressable 5 V LED strip controlled by the ESP32 provides the customer-visible coarse state independently of Linux:

| State | LED behavior |
| --- | --- |
| OFF | Dark |
| BOOTING | Pulsing blue |
| SELF_TEST | Moving yellow |
| READY | Steady green |
| READY_LIMITED | Amber |
| OPERATING | Cyan activity pattern |
| FAULT | Flashing red |
| SHUTTING_DOWN | Pulsing violet |

The initial interface uses a WS2812B- or SK6812-class 5 V strip, a 74AHCT125-class 3.3-to-5 V data-level shifter, approximately 220-330 ohm series data resistance, and approximately 1000 uF of local bulk capacitance rated for at least 10 V. The external 5 V converter is to be sized for at least 5 A continuous. No software current or brightness limit is credited as electrical protection; animation brightness remains an aesthetic and thermal setting. Exact LED count remains open.

Detailed voltage, signed current, power, energy, state of charge, remaining time, temperatures, faults, and time plots are shown through the Linux diagnostic application. An HDMI monitor is attached only for development; normal customer operation does not start the Ubuntu GUI. The same records are stored locally and later exposed through ROS 2, including `sensor_msgs/BatteryState` where appropriate.

## Communication Assumptions

- The twelve RobStride joint actuators and the ESP32 battery/power controller share a planned 1 Mbit/s classical CAN network.
- Joint command/feedback update is planned at 100 Hz. The preliminary worst-case estimate remains below approximately 50 percent bus use, including conservative frame overhead; this requires measurement with the final protocol.
- The physical CAN network is a continuous backbone with one 120 ohm termination at each physical end. The USB-CAN adapter connects through a short unterminated stub.
- Linux uses native SocketCAN through a galvanically isolated USB-CAN adapter; the exact production adapter remains a procurement/validation item.
- The ESS motors remain on RS485, not CAN.
- Two existing isolated Waveshare USB-to-RS485/422 converters based on FT232RL/SP485EEN are available: one bus for the two ESS23 drive motors and one bus for the two ESS17 lift motors.
- The OAK camera remains directly connected by USB 3. Lower-bandwidth CAN/RS485 adapters may use a suitable powered USB 2 hub.

## Evidence

- The selected battery supplier publishes 36 V nominal, 42 V charge voltage, 17.5 Ah, 50 A continuous discharge, 150 A for 1-3 s, 27.5 V cut-off, separate charge/discharge ports, a 60 A fused cable, and an explicit prohibition on regeneration.
- The compute/sensor branch measured approximately 25 W at the battery side in basic Ubuntu without ROS workload.
- The drive 10:1 reduction and its self-locking behavior were physically tested by the project owner.
- TI specifies the LM74930-Q1 for a 4-65 V input, external back-to-back N-channel MOSFET control, reverse-current blocking, adjustable overcurrent/short-circuit protection, undervoltage/overvoltage handling, and low-current shutdown.
- StepperOnline specifies ESS23-RS20 for 24-48 V DC and ESS17-RS07 for 24 V DC.
- All loss, shunt, and chopper numbers in this record are engineering calculations from the stated initial component values; they are not measurements of completed HomeMy hardware.

## Impact

The decision changes the customer power-on contract, lifecycle/status behavior, PMU requirements, actuator-bus protection, Linux diagnostics, ESP32 firmware scope, CAN/RS485 planning, and the order of commissioning. It removes the permanent customer display and oversized latching contactor from the design direction while retaining independent visible state and low-current electronic shutdown.

## Revision-B production validation

The following evidence is obtained with Revision A before any accepted value becomes a Revision-B production limit. Its absence does not prevent completing the Revision-A design:

1. Full branch power budget with all actuators, compute, and sensors active.
2. Exact resettable eFuse settings, wire gauges, connectors, return paths, grounding, and isolation; verify the battery fuse as the only melting fuse.
3. MOSFET selection and hot/transient thermal verification.
4. Main-path inrush test; add precharge if the measured result fails limits.
5. DC/DC converter load, efficiency, thermal, transient, and undervoltage tests.
6. Brake-chopper energy calculation from actual arm masses and speeds, followed by regenerative bus tests.
7. Fuse/BMS/electronic-trip coordination and fault-injection tests.
8. Battery, shunt, MOSFET, chopper, and converter temperature-sensor selection and placement.
9. ESP32 state machine, watchdog, fault latch, non-volatile event log, and CAN interface.
10. Linux service, dashboard, ROS 2 interface, and `homemy.target` implementation.
11. Cold start, failed boot, heartbeat loss, controlled shutdown, forced shutdown, brownout, short circuit, chopper fault, CAN/RS485 loss, and recovery tests.

## Risks and Rollback

Principal risks are undocumented motor regeneration, unknown final arm energy, unverified Chinese DC/DC converter capability, MOSFET linear/transient stress, fuse/BMS mismatch, shunt-sense interaction, thermal concentration, and loss of diagnostic power during a hard trip.

Until the complete electronic path is built and validated, retain the developer-controlled supply and shutdown procedure. Real actuators remain disconnected or independently inhibited during controller commissioning. Reverting this decision means removing the LM74930/chopper assumptions from the power contract without weakening the independent fuse, BMS, or motion gate.

## PMU Handoff

The consolidated schematic/layout input, machine-readable two-stage requirement status, release gates, Astra start prompt, and staged evidence plan are maintained in:

- `hardware/power-management-unit/ASTRA_PCB_HANDOFF.md`;
- `hardware/power-management-unit/interfaces-and-layout.md`;
- `hardware/power-management-unit/requirements.yaml`;
- `hardware/power-management-unit/verification-plan.md`;
- `hardware/power-management-unit/ASTRA_START_PROMPT.md`.

Those files capture later detail and take precedence for the PCB implementation where they explicitly refine this architectural record.
