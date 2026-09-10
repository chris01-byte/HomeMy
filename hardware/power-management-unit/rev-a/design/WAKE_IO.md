# Revision A wake, controller and low-voltage I/O

`rev_a_engineering_prototype: true`  
`rev_b_production: false`  
Date: 2026-09-10. Design status: implementable pin/net definition, subject to integrated ERC/DRC and motorless bench validation. This document does not claim measured hardware performance.

The machine-readable source is [wake-io-parts.json](wake-io-parts.json). Every populated IC includes physical pin numbers, pin names, electrical types, package and manufacturer source. The generated schematic must preserve these connections and the normally unpopulated CAN termination option.

## Always-on supply and off-domain separation

U15 is LT3014BIS5#TRPBF, an 80 V regulator used only for the hardware wake domain. Two 4.99 kohm, 0.75 W resistors limit its input current. The regulator pins are IN=1, GND=2, NC=3, ADJ=4, OUT=5. R202/R203 are 174 kohm/100 kohm, both 1%. The resulting AON rail is nominally 3.343 V; using the full 1.18–1.26 V reference limits and resistor tolerance gives 3.193–3.499 V, including maximum positive bias contribution at the upper bound. This remains above the worst supervisor release level and below the TMUX1511 3.6 V off-state input limit. These bounds already include the regulator's specified line/load envelope and must not be replaced by a typical-only 1.22 V calculation. [LT3014B datasheet, pp. 2–4, 7–8](https://www.analog.com/media/en/technical-documentation/data-sheets/3014bfb.pdf)

At a hard short after the feed resistors, 65 V produces 6.51 mA, 0.423 W total and 0.212 W per resistor. At 42 V, the corresponding resistor losses are 0.088 W each. The AON supply is not a general-purpose auxiliary supply.

A preliminary 0.60 mA AON input budget leaves more than 21 V at the regulator at minimum battery voltage. It represents an engineering allowance for timer, logic, pullups and regulator current, not a measured standby specification. At 0.60 mA the allowance is 14.4 mAh/day or 432 mAh/30 days, excluding the battery BMS and other unswitched main circuitry. Measure the complete battery OFF current in Revision A. Only the regulator, wake timing/latches/supervisors and LM shutdown domain stay powered. V5V and V3V3 supply the ESP32, CAN, LED, INA228 and normal logic only after the main path turns on.

U17 TPS3839G33DBZR supervises the AON rail; U26 is the same part on switched V3V3. Pin 1 is GND, pin 2 is push-pull RESET_N and pin 3 is VDD. Threshold is 3.08 V nominal, with 3.003–3.126 V limits; reset-release delay is 120–350 ms. A 100 nF bypass is placed at each part. Their outputs must never be wired together. [TPS3839 datasheet, pp. 4–8](https://www.ti.com/lit/ds/symlink/tps3839.pdf)

## One button, release-to-arm and hold transfer

U16 is LTC2954ITS8-1#TRPBF: active-high open-drain enable variant. Pin map: VIN=1, PB=2, ONT=3, GND=4, INT=5, EN=6, PDT=7, KILL=8. The raw physical button closes J20 pin 1 to J20 pin 2/LOGIC_GND. A 1 kohm series resistor, 100 kohm AON pullup, 10 nF capacitor and two Schmitt inverters produce complementary clean PB_PRESSED/PB_RELEASED signals.

U18/U19 form the release-to-arm interlock. The asynchronous clear of U18 follows AON_RESET_N. Its asynchronous preset is asserted only when AON_RESET_N and PB_RELEASED are both high. Thus a button already held during battery reconnection cannot start the robot: the button must first be released after a valid AON supply. The second NAND presents a low PB to the LTC2954 only when BUTTON_ARMED and PB_PRESSED are both true. Asynchronous clear and preset are never intentionally asserted together. [SN74LVC1G74 pin/truth tables](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf), [dual NAND pin/truth tables](https://www.ti.com/lit/ds/symlink/sn74lvc2g00.pdf)

U16 EN feeds WAKE_EN_OD through its 47 kohm pullup and 1 Mohm pulldown. U64 is its only logic load and buffers it into WAKE_RAW_EN. This buffer is required: a heavily loaded open-drain enable would not reliably meet the one-shot's 0.7 VCC trigger threshold. WAKE_RAW_EN fans out to latches, the timer and enable logic.

The ONT capacitor is 22 nF C0G, 5%, for approximately 174 ms total turn-on qualification. While running, INT asserts after the internal 26–41 ms debounce; a short press changes no hardware enable directly. The LTC2954's native KILL blanking interval is only 400–650 ms, insufficient as an assumed ESP32 plus unknown-converter boot deadline. [LTC2954 electrical/timing and application sections, pp. 3–12](https://www.analog.com/media/en/technical-documentation/data-sheets/2954fb.pdf)

U21 LTC6993IS6-1#TRPBF supplies a separate nonretriggerable start grant. Pins are TRIG=1, GND=2, SET=3, DIV=4, V+=5, OUT=6. TRIG is WAKE_RAW_EN. RSET=120 kohm and DIVCODE=7, selected by 1 Mohm above DIV and 887 kohm below it. Therefore:

```
Ndiv = 2^21
t_start = 2^21 × (120000 / 50000) × 1 microsecond
        = 5.0331648 seconds
```

The full-temperature timer accuracy is ±3.0%, not the ±2.3% room-temperature headline. Including 1% resistor tolerance and a conservative additional ±0.65% resistor temperature change gives approximately 4.80–5.27 s. Use 4.7 s as the latest allowed firmware hold assertion and 5.4 s as the failed-start bench acceptance ceiling. The timer is physically nonretriggerable and has no firmware trigger connection. [LTC6993 Rev. F, pp. 1–5, 12–17](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc6993-6993-1-6993-2-6993-3-6993-4.pdf)

U22 ORs STARTUP_GRANT with ESP_MAIN_HOLD_AON; its output reaches KILL through 10 kohm. The ESP signal crosses through 10 kohm and has explicit pulldowns, so an unpowered or reset GPIO cannot preserve hold. Startup grant expiry with hold absent shuts the main path off. A reset after grant expiry also shuts it off. Assertion of hold is permission to keep low-voltage power while checks continue; it is never motion authority.

The 1 uF PDT capacitor gives a nominal forced-off time near 6.48 s. Its effective capacitance must be qualified at the timer's actual voltage and temperature. With 0.80–1.10 uF effective capacitance plus timer/current tolerance, reserve an engineering acceptance window of 4.1–9.5 s; this is a board guard band requiring measurement, not a manufacturer guarantee for the assembled circuit. Capacitor substitution changes the customer-facing long-press time. Forcing off is independent of ESP32/Linux because the LTC2954 releases EN even while KILL remains high. The initial start press is subject to the LTC2954 start/release sequence; after startup, release then press-and-hold supplies the forced-off action.

Suggested firmware parameters are Linux boot deadline 120 s, controlled shutdown grace 90 s, Linux heartbeat interval 100 ms and stale deadline 500 ms. They are configurable Revision-A parameters, not implemented firmware in this artifact.

## Main latch, startup mask and power recovery

U23 is an AON asynchronous main-fault latch. MAIN_FAULT_LATCHED immediately disables U25's final main-enable AND and Q20 sinks LTC KILL. WAKE_RAW_EN returning low is the only latch clear. The underlying LTC2954 remains off until a fresh button action; recovery of a fault does not raise its enable. Q20 and Q21 are BSS138BK,215 with a 2.5 V gate-drive resistance specification; a generic 2N7002 is not an approved substitution for these low-voltage control functions. [BSS138BK datasheet](https://assets.nexperia.com/documents/data-sheet/BSS138BK.pdf)

The manufacturer does not define FLT as unconditionally high while LM74930 EN is low. Accordingly U62/U63 qualify main FLT capture briefly after a raw-enable edge. R262=4.7 kohm and C254=1 uF drive a Schmitt buffer; the conservative effective-capacitance and input-threshold bracket is about 1–5.5 ms. U63 also gates this delayed signal with undelayed WAKE_RAW_EN and AON_RESET_N, so shutdown clears the latch without simultaneous preset/clear. Native LM74930 protection remains active throughout this small capture mask. Native latched OC/SCP faults persist beyond it; sustained UV/OV is captured at its end. There is no multi-second main-fault mask.

U55 records that switched V3V3 has reached its supervisor-good state. Once that has happened, any subsequent SW_RESET_N low sets the main latch through U56/U57/U58. This prevents the five-second startup grant from automatically restarting a converter/ESP brownout. Before V3V3 first becomes good, the bounded one-shot allows startup. Recovery after AON collapse is governed by the release-to-arm interlock.

Final LM enable is:

```
AON_WAKE_EN = WAKE_RAW_EN AND MAIN_LATCH_OK AND AON_RESET_N
```

Verify FLT capture-mask timing, native fault retention through that mask, brownout pulse response and reset ordering with the real controller before increasing the bench supply current. Faults shorter than the supervisor's detection capability are not claimed to be detected by this latch; GPIO hold release and the independent motion watchdog provide additional responses.

## Motion permission, external latch and watchdog

U27 is a switched-rail D flip-flop used as the motion authorization latch. D and PRE_N are tied high, Q starts cleared, and only a rising ESP_MOTION_RESET edge can set Q after all interlocks are healthy. Boot firmware must keep that GPIO low until an explicit commissioning/mission decision. U28/U29/U50 asynchronously clear it for any motion current fault, motion thermal fault, chopper fault, missing watchdog, ESP hardware reset, lost external permission, or main enable off. U54 requires both Q and ESP_MOTION_REQUEST as well as AON_WAKE_EN. Both request and reset have 100 kohm pulldowns.

```
MOTION_CLEAR_N =
    MOTION_FLT_N AND MOTION_TEMP_FLT_N AND CHOP_FAULT_N
    AND ESP_CHIP_EN AND ESP_WDO_N AND MOTION_PERMIT AND AON_WAKE_EN
MOTION_GATE_EN = ESP_MOTION_REQUEST AND MOTION_ARMED AND AON_WAKE_EN
```

TPS48110 thermal protection can retry internally; this external latch keeps its INP low after recovery. Native EN/UVLO also auto-recovers and does not assert its overcurrent or thermal flags. Therefore the power sheet adds U5 TLV3011BIDBVR, whose independent SYS voltage comparator pulls the shared open-drain MOTION_FLT_N low on a system-bus undervoltage. Its 224 kohm/10 kohm divider targets 29.06 V nominal, with a conservative lower trip estimate near 27.9 V, above the highest native falling UVLO threshold of about 26.79 V. The exact tolerance calculation belongs to POWER_STAGE.md. No input capacitor intentionally delays that comparator; shallow or very short dips still require bench response verification. SYS recovering cannot re-arm motion. A fault deassertion alone never sets MOTION_ARMED. [TLV3011B reference, open-drain output and integrated hysteresis](https://www.ti.com/lit/ds/symlink/tlv3011b.pdf)

J22 is a three-pin low-voltage commissioning interface: pin 1 V3V3 loop supply, pin 2 permission return, pin 3 LOGIC_GND. An external **deenergized-open relay contact** may connect pins 1 and 2. Alternatively pin 2 may receive an external 3.3 V ±5% active permission referenced to pin 3. It is not a 24 V input. U61 supplies Schmitt cleanup; the return has 100 kohm to ground and 10 nF local filtering. Open/disconnected/unpowered-low input clears motion. No permanently installed shorting jumper is authorized for actuator tests. This single-channel interface is a Revision-A commissioning gate, not an accepted final emergency-stop architecture.

U51 TPS3431SDRBR is always enabled while V3V3 exists. Its CWD pin is intentionally NC and SET1 high, selecting 1.6 s nominal watchdog timing, bounded 1.36–1.84 s; WDO is an active-low open-drain pulse that clears U27. WDO recovery cannot re-arm motion. Firmware toggles ESP_WDI only from the supervised main loop after validating a fresh Linux heartbeat; a free-running PWM output must not feed it. The hardware independently detects a frozen ESP32. It cannot independently decide whether a still-running but incorrect program is reporting a truthful Linux heartbeat. [TPS3431 datasheet, pp. 3–7, 9–12](https://www.ti.com/lit/ds/symlink/tps3431.pdf)

## ESP32, power, CAN and LED

U65 provides two additional TMUX1511 channels for the UART service signals. Its powered-off isolation and two 100 kohm MCU-side pulldowns prevent a connected programmer from keeping the ESP32 powered through signal pins. Use only 3.3 V UART levels (3.6 V maximum while PMU is off). GPIO0 and EN service contacts remain dry switches, with no externally driven reset supply.

U10 is ESP32-S3-WROOM-1-N8: PCB antenna, 8 MB quad flash, no PSRAM. The service header is UART only and has no external power feed; GPIO0 and EN are available for dry-switch recovery. GPIO3/45/46 strapping pins are unused. Pins 1, 40 and exposed pad 41 go to LOGIC_GND; pin 2 is switched V3V3. Exact GPIO assignments are in the JSON and generated pin table. Place the module at the board edge with its antenna beyond the ground/copper region where possible; otherwise enforce the manufacturer's antenna keep-out on all layers, including busbars and mounting hardware. [Espressif module datasheet](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)

U12 TLV1117LV33DCYR provides 3.3 V, 1 A capability. Its SOT-223 tab is OUTPUT, not ground. At a 0.5 A continuous engineering allowance, dissipation is 0.85 W. The datasheet 62.9 °C/W reference-board figure corresponds to approximately 53.5 °C rise, so this is suitable only with an intentional output-tab copper area and measured temperature. At 70 °C ambient the estimate approaches 124 °C junction; do not infer a 1 A continuous board rating from the IC current rating. Normal external 5 V must remain within 4.75–5.25 V, and never exceed the LDO 5.5 V recommended maximum. [TLV1117LV datasheet, pp. 3–5](https://www.ti.com/lit/ds/symlink/tlv1117lv.pdf)

U13 TCAN1042HGVDRQ1 uses VCC=V5V and VIO=V3V3. It defaults to standby through a 10 kohm STB pullup; TXD defaults recessive. Its bus pins are high impedance when unpowered. D40 ESD2CAN24DBZRQ1 is placed at the connector with a short return. This 24 V TVS protects transients; the populated network does **not** claim survival of a continuous 42 V battery-to-CAN miswire, even though the transceiver itself has a higher bus fault rating. [TCAN1042H-Q1 datasheet](https://www.ti.com/lit/ds/symlink/tcan1042h-q1.pdf), [ESD2CAN24-Q1 Rev. D](https://www.ti.com/lit/ds/symlink/esd2can24-q1.pdf)

Use a continuous CAN_H/CAN_L backbone, short PMU stub and exactly two end terminations. Two 60.4 ohm series resistors and the midpoint capacitor form the optional local 120.8 ohm split termination; all three are DNP unless PMU is a physical end. A 1 Mohm bleed and 1 nF/1 kV capacitor couple CHASSIS to LOGIC_GND; shield current is not routed through an actuator-return path.

For twelve joints at 100 Hz with one command and one response each, a conservative 160-bit stuffed extended classical CAN frame gives 2400 × 160 = 384000 bit/s, or 38.4% at 1 Mbit/s. Eighty PMU frames/s add 1.28%. Error/retry traffic, final protocol framing and synchronization remain measured Revision-B inputs; the 50% target is not proven by this arithmetic.

U14 SN74AHCT1G125DBVR translates LED data to V5V. Its OE_N pullup disables it until Q21 sees switched supervisor-good. Data uses a 330 ohm series resistor and 100 kohm output pulldown. A 1000 uF/10 V Panasonic FR capacitor is at the strip output. The LED strip shares the specified external 5 V/5 A supply; no software brightness limit is credited as branch protection. [AHCT125 datasheet](https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf)

## Measurement and powered-off isolation

INA228 U11 uses its own pair of matched 10 ohm series resistors and 100 nF differential capacitor on MAIN_KELVIN_P/N. Their RC corner is approximately 79.6 kHz. Do not share these resistors or filtered nodes with the LM protection amplifier. VBUS senses BATT_SENSED_P through 10 ohm with a 10 nF/100 V capacitor. Address pins A0/A1 are ground for 0x40. I2C has 4.7 kohm pullups and ALERT 10 kohm, all to switched V3V3. Range initially remains ±163.84 mV. [INA228 datasheet](https://www.ti.com/lit/ds/symlink/ina228.pdf)

U60 TMUX1511PWR isolates four potentially live sources from the unpowered ESP32: system-bus divider, motion-bus divider, motion IMON and AON main fault. All selects follow switched supervisor-good. Its signal sources must remain within 0–3.6 V when the chip is unpowered. Main fault has a 3.499 V worst-case AON bound. Bus dividers use 200 kohm high side and 10 kohm low side: their isolated-side input reaches at most about 3.16 V at a 65 V transient including 1% resistors. ADC-side 100 kohm pulldowns limit 2 uA worst-case off leakage to 0.2 V. [TMUX1511 datasheet, pp. 3–7](https://www.ti.com/lit/ds/symlink/tmux1511.pdf)

With U60 on, each voltage divider's ADC pulldown changes the nominal gain to 1/23: 42 V gives 1.826 V, 46 V gives 2.000 V and 65 V gives 2.826 V. Calibrate this full network, including ADC characteristics. The motion sheet supplies IMON's resistor network; the extra 100 kohm ADC pulldown changes its calibration slightly and must be included. It is diagnostic telemetry, not the motion trip-setting path.

TH20/TH21 are Murata NCP18XH103F03RB, 10 kohm at 25 °C, 1%, with 10 kohm bias and 100 nF ADC reservoirs. Place each by its own hottest MOSFET bank on electrically isolated logic copper. Their B25/50 nominal value is 3380 K; a single-beta extrapolation is not a guaranteed high-temperature conversion. Firmware must use the manufacturer resistance-temperature data plus board calibration. Provisional software thresholds are 70 °C warning, 85 °C motion off and 95 °C main off; this pair of NTCs is not credited as an independent hardware thermal cutoff. [Murata exact-part page](https://pim.murata.com/en-us/pim/details/?partNum=NCP18XH103F03RB)

## Footprint audit

TI DGS0010A for INA228 matches the 3 × 3 mm, 0.5 mm pitch MSOP-10 footprint naming in KiCad (the manufacturer calls this VSSOP). U51 requires the specific DRB0008A land pattern: pin centers at x=±1.4 mm, y=±0.975/±0.325 mm, each land 0.6 × 0.31 mm, and a 1.5 × 1.75 mm central ground pad. A generic 1.65 × 2.4 mm exposed-pad footprint is not equivalent. Exact pad geometry is included in JSON, and the manufacturer's land-pattern pages are retained as evidence/ina228-land.png and evidence/tps3431-land.png.

## Bring-up evidence and limits

The initial [placement-wake.json](placement-wake.json) assigns all 168 references. INA228 and its independent Kelvin filters sit beside the main shunt. AON logic occupies the reserved lower-left region; motion latches and analog isolation are grouped by function. ESP32 is at (325, 280) mm, rotated 180 degrees, with the antenna directed toward the bottom edge. The module's stepped courtyard includes its antenna exclusion area; its rectangular bounding box is not a valid overlap test. Thirty-six local bypass capacitors use physical KiCad supply-pad coordinates, with conservative copper-edge separation no greater than 1.55 mm. The own-component courtyard check reports zero overlaps. These checks do not replace the combined-board clearance, routing, thermal, mounting or antenna reviews. Thermistors use the main/motion MOSFET placement coordinates supplied by the power-stage design.

Required motorless checks are held-button battery attachment, deliberate momentary start, no-hold timeout, normal short press, forced long press with stuck-high hold, ESP reset, switched-rail loss during and after startup grant, main fault during/after capture mask, all motion-fault inputs, SYS-only undervoltage with V3V3 maintained, removed permission, watchdog timeout and fault-recovery-without-reset. Scope raw/qualified main EN, KILL, startup grant, switched supervisor, motion latch Q and actual gate controller INP together. Confirm OFF leakage with CAN attached and residual SYS/MOTION bus voltage, and measure the assembled capacitor timings over the approved prototype temperature range.

The evidence record distinguishes Boolean/state arithmetic from transistor behavior, propagation races, EMI, ERC/DRC and physical measurements. Native main/motion protection, the external fuse, reachable disconnect and current-limited initial supply remain mandatory. No assembly, purchase, actuator enable or real-hardware test is authorized by this design note.
