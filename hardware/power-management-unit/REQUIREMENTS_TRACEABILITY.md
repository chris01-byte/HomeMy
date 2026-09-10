# PMU Revision A requirement traceability

`rev_a_engineering_prototype: true`  
`rev_b_production: false`  
Date: 2026-09-10. This cross-reference separates implemented CAD from owner review and physical validation. The [final review](rev-a/evidence/FINAL_REVIEW.md) records native ERC/DRC reports with zero findings, zero open connections and zero schematic-parity differences; it also records the failed process exits after report completion. Assembly and hardware validation remain unperformed.

[requirements.yaml](requirements.yaml) remains authoritative. Every numbered requirement, including every `LOCKED` item, appears below. “Defined” means that a circuit, external interface or documented operating contract exists; it does not mean the implementation has been independently verified. A software requirement mapped to a GPIO/contract is **not implemented firmware**.

Evidence abbreviations: **P** = [power-stage design](rev-a/design/POWER_STAGE.md), [component nets](rev-a/design/power-parts.json), [calculations](rev-a/evidence/power/calculated.json); **W** = [wake/I/O design](rev-a/design/WAKE_IO.md), [component nets](rev-a/design/wake-io-parts.json), [logic/tolerance checks](rev-a/evidence/wake-io-calculations-and-checks.json); **C** = [chopper/mechanics design](rev-a/design/CHOPPER_MECHANICS.md), [component nets](rev-a/design/chopper-parts.json), [calculations](rev-a/design/chopper-calculations.json). Their manufacturer records are source evidence, not HomeMy measurements. **D0–D7/E0–E2/T0–T8** refer to [design review and bring-up](DESIGN_REVIEW_AND_BRINGUP.md); **B01–B14** refer to [Revision-B validation](REV_B_VALIDATION.md). Adjustable choices are in [Revision-A assumptions](REV_A_ASSUMPTIONS.md).

## Battery and power topology

| ID | Required status | Circuit/interface and evidence | Verification or remaining gate |
| --- | --- | --- | --- |
| BAT-001 | LOCKED | 10S7P, 27.5–42 V, 17.5 Ah/630 Wh source contract; J1/J2, `BATT_FUSED_P/BATT_N`; P voltage/thermal calculations. | Verify actual pack identity, polarity and separate ports at E0; no new pack test claimed. |
| BAT-002 | LOCKED | 50 A continuous source ceiling; normal policy 45 A. RSH1/RSH2 and Q1–Q10 pulse calculations address the advertised 150 A/1–3 s case. | 150 A is a survival case, never an operating setpoint. Full hot-system pulse survival and BMS curve remain B01/B07. |
| BAT-003 | LOCKED | U1 LM74930 reverse blocking, opposing Q1–Q6 banks; chopper across downstream `MOTION_BUS_P`. No charge-port connection. | D1 polarity/body-diode audit, T3 reverse-block test; measured regenerative battery current B03. |
| BAT-004 | REV_A_ENERGIZATION_GATE | External 60 A fuse ahead of J1; no PCB substitute. | **E0 open:** exact part, ≥42 V DC rating (prefer ≥60 V), interrupt rating and time-current curve required before battery power. |
| TOP-001 | LOCKED | J1 → RSH1 → `BATT_SENSED_P` → Q1–Q6/U1 → `SYS_BUS_P`; P. | D1/D4 netlist and physical-current-path review. |
| TOP-002 | LOCKED | SYS branches U3 PC TPS26631, U4 logic TPS26631, RSH2/U2 common motion gate; P. | D1 continuity and T4 branch isolation. |
| TOP-003 | LOCKED | Passive J3/J4 left arm, J5/J6 right arm, J7 drive, J8 lift-buck input and J12/Q40 chopper on motion bus; C. | D1 connector/polarity audit, T4 output continuity; B04/B06 load behavior. |
| TOP-004 | LOCKED | No populated precharge. U1/U2 gate slew parts remain configurable; installed chopper bulk is 940 µF. | T2 main fixture excludes that bulk with motion OFF. Full-system inrush/no-precharge decision remains B01; a resistor estimate is not SOA proof. |
| TOP-005 | LOCKED | External battery fuse only; U3/U4 and common motion protection are electronic. No arm/lift/chopper melting fuses. | D1 BOM/netlist audit; B07 actual protection coordination. |
| TOP-006 | LOCKED | Branch negative nets meet BATT_N at explicit star; LOGIC_GND stays outside load-current paths. J16/J17 straight CAN backbone. | D4 routed current-return and shield review; B06/B11 temperature and signal integrity. |

## Measurement and main/motion switches

| ID | Required status | Circuit/interface and evidence | Verification or remaining gate |
| --- | --- | --- | --- |
| MON-001 | LOCKED | U11 INA228AIDGSR, switched V3V3, high-side RSH1 after fuse; `MAIN_KELVIN_P/N`; W. | D2 package/polarity, T1 OFF leakage, T3 calibration. |
| MON-002 | REV_A_DESIGN | RSH1 Bourns CSS4J-4026R-L500F, 0.5 mΩ/10 W, four separate force/sense pads; P/C custom geometry. 150 A/3 s = 33.75 J; manufacturer's 50 W/5 s overload qualification = 250 J under its conditions. | Qualification is not an arbitrary-pulse energy rating. D2/D4 Kelvin geometry; T3 drift; B02/B07 hot pulse evidence. |
| MON-003 | PROVISIONAL | INA initial ±163.84 mV gives ±327.68 A nominal; I2C address 0x40, `INA_ALERT_N`; W. | Firmware register configuration and reference calibration T3/B02; no accuracy inferred from full scale. |
| MON-004 | REV_A_DESIGN | Shared RSH1 candidate: independent U1 filters and W R223/R224 = 10 Ω plus C241 = 100 nF differential filter. Common-mode/polarity and nominal thresholds documented in P/W. | **Partial design assurance:** independent traces do not prove IC-failure independence. D3 requires explicit failure review/conservative disposition before order; T3 sense-fault tests/B02. |
| MAIN-001 | LOCKED | U1 LM74930QRGERQ1, Q1–Q3 and Q4–Q6 opposing banks, six 100 V parts. AON U23 latch/Q20/U25 and LTC2954 require a new button cycle after hard fault. | D1 truth/polarity audit; T1/T3 fault recovery, brownout and no automatic restart. |
| MAIN-002 | REV_A_DESIGN | Q1–Q6 PSMN1R0-100ASFJ: 0.99 mΩ maximum at 25 °C and 2.3 mΩ at 175 °C with 10 V gate; Qg/SOA/thermal sources in P. | **Partial design assurance:** U1 DGATE minimum 9.2 V does not guarantee the 10 V resistance table. 3.2 mΩ fallback and cold bounded fixture are assumptions. D3 disposition and B01 hot SOA/gate/current-sharing evidence required. |
| MAIN-003 | PROVISIONAL | P configurable UV/OV/OCP/SCP networks: UV 29.03 V nominal, recovery 31.67 V, OV 44.52 V, OC 65.09 A equation, SCP 120.30 A. C3 film/100 kΩ TMR produces ~0.457 s FLT action. | **Documented deviations:** native fast UV, not 0.5 s; OV/recovery windows are wider than nominal request; no guaranteed 65 A error interval. T3 sweeps, B07 selectivity; see A02–A04. |
| MOT-001 | LOCKED | U2 TPS48110AQDGXRQ1, Q7/Q8 and Q9/Q10, four 100 V parts; U27/U28/U29/U50/U54 external latch; `MOTION_GATE_EN` default low. U5 UV comparator joins `MOTION_FLT_N`. | T1/T3 verify only explicit `ESP_MOTION_RESET` edge re-arms, including native thermal/UV recovery and chopper OV. |
| MOT-002 | REV_A_DESIGN | Q7–Q10 same exact 100 V FET; ≥11 V normal charge-pump enable basis, C9/C29 boost reservoir, individual gate resistors; P. | Boost bias curve and gate slew are conditional models. D3/T2 startup waveform and B01/B06 hot SOA/sharing; installed 940 µF adds ~0.995 J maximum initial capacitor energy at 42 V. |
| MOT-003 | REV_A_DESIGN | RSH2 CSS4J-4026R-L500F, 0.5 mΩ/10 W exceeds 5 W requirement; dedicated Kelvin nets to U2; P. | D2/D4 force/sense isolation; T3 calibration and thermal drift. |
| MOT-004 | REV_A_DESIGN | P 59.95 A nominal OC, 57.13–64.41 A table-derived corner; SCP ~100 A, 85.74–114.91 A modeled. C10 33 µF film/100 kΩ timer: FLT action 0.350–0.675 s under stated leakage/temperature assumptions. | T3 measure thresholds/delay/leakage; B07 coordinate motor pulses with main/fuse/BMS. Nominal 60/65 A ordering is not selectivity. |
| MOT-005 | LOCKED | J3–J6 passive arm outputs after common gate; no per-arm IC/FET/shunt; C. | D1 BOM/path audit; B06 enforce each 25 A planning envelope externally. |

## Software, chopper and converters

| ID | Required status | Circuit/interface and evidence | Verification or remaining gate |
| --- | --- | --- | --- |
| SW-001 | PROVISIONAL | INA total current supports 45 A normal ceiling, >45 A/1 s warn/derate and >50 A/2 s controlled motion stop; `ESP_MOTION_REQUEST`. | Policy configuration is not delivered firmware. T7 simulated lifecycle/load records; B09 measured execution and B07 coordination. |
| SW-002 | PROVISIONAL | INA/bus ADCs support 33 V/10 s warning, 31.5 V/5 s task rejection, 30.5 V/5 s shutdown. | T7 firmware configuration and fault-injection; B09 low-battery behavior. Native UV may act earlier at its upper corner. |
| SW-003 | LOCKED | AON main latch and motion authorization FF require deliberate new actions; READY is not motion permission. | T1/T7 every reset/recovery path; B09/B14 end-to-end fault injection. |
| CHOP-001 | PROVISIONAL | U30/U31/U32/U33 analog circuit, Q40 and J12, powered from motor-side `MOTION_BUS_P`; no branch fuse/ESP dependency; C. | T5 independent source, MCU absent, isolated bus hold-up and continued dissipation after motion latch-off. |
| CHOP-002 | REV_A_ASSUMPTION | Two external RH10010R00FE01, 10 Ω/100 W parallel; 5 Ω, 8.6 A/369.8 W at 43 V. Separate 305 × 305 × 3.2 mm Al plates; manufacturer short-overload evidence supports the proposed 500 J total-bank cold test under the A06 limits. | A06/T5 staged energy limit; repetitive duty, actual energy and chassis transfer remain B03. No repetitive pulse curve invented. |
| CHOP-003 | REV_A_DESIGN | Q40 IPT015N10N5ATMA1, U30 TPS7A4001DGNR, U31 REF5025IDR, U32 LM339BIPWR, U33 UCC27511DBVR, U36 supervisor, two independent NTCLE100E3103GB0 sensors; C. | D2 physical pad maps, T5 startup/thermal/open/short and switching capture; B03 losses/SOA. |
| CHOP-004 | PROVISIONAL | R303/feedback string set 43.000/42.402 V; independent divider ~46 V faults motion via U34. W ADC supports software 43.5 V warning/45 V controlled stop. | Modeled ranges 42.683–43.316 V on, 42.072–42.733 V off, 45.663–46.339 V hardware fault. T5 trim/latency; B03 dynamic margin; software actions T7. |
| CHOP-005 | PROVISIONAL | J13 DNP `LIFT_24V_SAMPLE/LIFT_24V_N`; no local 24 V clamp populated. | T6 check probe interface; B04 lowering/deceleration overshoot decides clamp addition. |
| PC-001 | LOCKED | U3 TPS26631, J9 `PC_BUCK_IN_P/PC_N`, external planned 12 V buck with claimed 8–55 V input; no dedicated PC current sensor. | A09 external module pinout/ratings are assumptions; T6/B05 characterize actual module. |
| PC-002 | LOCKED | 65 W battery-side Linux/BIOS policy, measured-source baseline ~25 W basic Ubuntu retained as prior context only. | T7/B09 repeat baseline and enforce budget with actual ROS/USB loads; this design did not remeasure it. |
| PC-003 | PROVISIONAL | U3 ILIM 6.04 kΩ → 2.980 A nominal; MODE floating latch-off, SHDN follows SYS, 22 nF slew. | T4/T6 overload pulse behavior and harness stress; not a precision 65 W clamp. |
| PC-004 | REV_B_VALIDATION | External module at J9; P interface/eFuse model. | B05 startup, current limit, efficiency, heat, low-battery and transient records. |
| LOGIC-001 | LOCKED | U4 TPS26631 → J10 external 5 V buck input; J11 regulated 5 V/≥5 A return; no software current limiting credited. | T4/T6 physical full-load test; B05 module validation. |
| LOGIC-002 | REV_A_ASSUMPTION | J10 pins input+/return, J11 pins regulated 5 V+/return; U12 TLV1117LV33DCYR creates V3V3; W/C. | A09 exact converter model remains unresolved. Verify module terminals before connection; T6/B05 all required tests. |
| LOGIC-003 | PROVISIONAL | U14 SN74AHCT1G125DBVR, R248 = 330 Ω, C246 = 1000 µF/10 V; J18 external WS2812B/SK6812-class strip. | T6/T7 signal level, default disabled output, local reservoir and full-load voltage/temperature. |
| LIFT-001 | LOCKED | J8 motion-bus input to external preferred 20–60 V → 24 V module, 10 A label target, planned 4–5 A output for two ESS17 drives. | Input connector current is not output current. A09 and T6 verify actual module; B04/B05 loaded performance. |
| LIFT-002 | LOCKED | Passive J8; internal converter OCP plus U2 common motion gate, no lift eFuse. | D1/T4 topology; B04 actual internal OCP/reverse-output behavior. |
| LIFT-003 | REV_A_ASSUMPTION | C explicit J8 input polarity and J13 DNP output sampling; externally replaceable module. | Exact converter model/pinout remains unknown; verify against its own documentation before connection, then B04/B05. |

## Controller, communications and layout

| ID | Required status | Circuit/interface and evidence | Verification or remaining gate |
| --- | --- | --- | --- |
| CTRL-001 | REV_A_DESIGN | U10 ESP32-S3-WROOM-1-N8: 8 MB flash, no PSRAM, PCB antenna; J21 UART recovery via U65 powered-off isolation; W. | D2 pin/strap/antenna review, T1 programmer backpower, T7 firmware/recovery. |
| CTRL-002 | LOCKED | LT3014B/LTC2954/AON logic alone remain supplied beside BMS/main shutdown domain. U3/U4, V5V/V3V3, ESP, PC, strip and INA switch off. | T1 measure complete battery OFF current with attached CAN/UART and residual buses. 0.60 mA AON allowance is not a measurement. |
| CTRL-003 | REV_A_DESIGN | U16 button controller, U18 release-to-arm, U21 fixed ~5 s one-shot, ESP hold OR, U23 fault latch, U55 switched-power-seen latch; `WAKE_RAW_EN/AON_WAKE_EN/WAKE_KILL`; W. | T1 complete timing/fault matrix; ~174 ms start, hold by 4.7 s, no-hold off ≤5.4 s, long-press board window 4.1–9.5 s requiring measurement. |
| CTRL-004 | LOCKED | J18 LED strip is customer indicator; development HDMI remains on external Linux PC. No onboard permanent display. | D1 BOM audit; T7 all lifecycle LED states and loss of stale READY. |
| CTRL-005 | LOCKED | J22 low-voltage external permission; R238 pulldown/U61 Schmitt and U27 asynchronous clear. Open/unpowered/low disables motion. No customer master switch. | T1 disconnect and power-sequence test; E2 physical service disconnect for actuator tests; final stop architecture B14. |
| COM-001 | LOCKED | U10 TWAI/classical CAN via U13; 1 Mbit/s, 12 joints + PMU, 100 Hz contract. W arithmetic ~38.4% joint frames plus ~1.28% example PMU traffic. | Arithmetic assumes frame sizes/rates; T7 fixture and B11 measured ≤50% utilization with errors/retries. |
| COM-002 | LOCKED | J16/J17 linear backbone; R243/R244 60.4 Ω halves and C244 DNP, populated only at physical end. External isolated USB-CAN retained. | D1/T6 exactly two end terminations, no star, short PMU stub. |
| COM-003 | REV_A_DESIGN | U13 TCAN1042HGVDRQ1, D40 ESD2CAN24DBZRQ1, shield RC R245/C245; W/C. | D2/T6 ESD/standby/no backpower; B11 EMC. 24 V TVS network does not claim continuous 42 V CAN miswire survival. |
| COM-004 | LOCKED | No onboard RS485; two external isolated USB-RS485 buses remain drive/lift system interfaces. | D1 BOM audit and T7/B09 integration. |
| PCB-001 | PROVISIONAL | Four layers, minimum finished 70 µm outer / 35 µm inner copper; 1.60–1.70 mm between outer copper faces, excluding masks. Baseline Tg 125–135 and ENIG; [fabrication process](rev-a/manufacturing/PCB_STACKUP_PRESSFIT.md). | D4/D6 compare the native stackup with the final fabricator stack and pressfit coupon; higher Tg requires separate pre-evaluation. No fabrication qualification is inferred from the CAD stack. |
| PCB-002 | LOCKED | Seven shaped 2 mm Cu-ETP underside bars BB1–BB7, fifteen Ø8 mm PCB contacts BC1–BC15, eight 20 × 10 × 2 mm top star bridges NB1–NB8, insulating film, contact shims and specified M3 spring clamps; [exact geometry](rev-a/manufacturing/busbar-pcb-interface.json), [calculations](rev-a/manufacturing/busbar-calculations.json), [assembly](rev-a/manufacturing/MECHANICAL_BUILD.md). [Current via-field-counts.json](rev-a/design/via-field-counts.json) is authoritative for generated counts. | The earlier 160-via calculation was conditional. The [filled-copper review](rev-a/evidence/filled-power-copper-review.md) uses the actual field counts and examines local shunt, FET and star paths. Counts do not prove local current sharing. D6 tests coupon force and contact resistance; B06 qualifies current and temperature. No 50 A assembly rating is inferred from bar cross-section. |
| PCB-003 | LOCKED | J1–J6 Würth 7461103 M5 press-fit 160 A class, battery 6 mm², arms 4 mm²; C. No final XT connector. | D6 plating/press-fit/torque/cover and harness review; B06 temperature/retention. Terminal rating does not rate the board. |
| PCB-004 | REV_A_ASSUMPTION | 360 × 300 mm bench board; four mount positions including H3 at (292, 292) mm outside the ESP corner; actual bar and fastener coordinates in the [1:1 drawing](rev-a/manufacturing/BUSBAR_TOP_VIEW_1to1.svg), [catalogue hardware](rev-a/manufacturing/MECHANICAL_CATALOG_BOM.json), [connector/enclosure assembly](rev-a/manufacturing/CONNECTOR_ASSEMBLY.md). Separate 305 × 305 × 3.2 mm resistor plates; at least 15 mm under the PCB and capacitor vent clearance defined. | A12 and the mechanical source specify a reproducible prototype proposal. D4/D6 must compare the final PCB, tool and cable envelopes, insulated carrier and support, stack tolerances and coupon results; B12 qualifies the final enclosure and airflow. No finished enclosure or mechanical test is claimed. |
| PCB-005 | REV_A_DESIGN | Right-angle Würth 7461103 M5 threaded terminals with horizontal screw and lug access, selected for J3–J6; 25 A per arm planning envelope. | P/C part evidence; D6 lug/crimp, counterhold and cable access; B06 current, temperature and derating. The terminal rating does not rate the PCB, cable or assembly. |
| PCB-006 | REV_A_DESIGN | J12 Phoenix 1776508/1777989 12 A class, 1.5 mm² high-temperature twisted pair for ~9.3 A worst pulse; neither pin is ground. | C manufacturer interface evidence avoids an unproved Micro-Fit pulse exception; T5/B03 connector temperature at approved duty. |

## Non-numbered completion and release requirements

| Requirement entry | Implementation/evidence and remaining disposition |
| --- | --- |
| Exact TPS26631 limits/retry | P U3/U4 latch-off MODE, 2.980/1.980 A nominal limits, 22 nF slew; T4/T6 must observe overload pulses and deliberate main-cycle recovery. |
| TVS/transient coordination | P D1/D2 PTVS1-043C-H; C D60/D61 SMCJ43A on 100 V motion domain only. D3 tolerance/lead-inductance audit and T3/T5 captures; B08 full installation. |
| Conservative external converter pinouts | C J8/J9/J10 are converter inputs; J11 regulated 5 V return; J13 DNP 24 V output sample. A09/T6 retains exact module unknowns. |
| Provisional mechanics and reinforcement | [Mechanical fabrication package](rev-a/manufacturing/MECHANICAL_BUILD.md), exact bar/contact JSON, 1:1 SVG, catalogue spring clamps, documented press-fit process, C calculations and A12. D4/D6 comparison with the final PCB and unpowered coupon checks remain required; no DRC, current or mechanical qualification is implied. |
| Initial current-limited supply | E1/T0–T2; ≤1 A initial main fixture, motion OFF, ≤100 µF direct SYS capacitance. This is distinct from the installed 940 µF motion bank. |
| Reachable service disconnect | E2 prerequisite for any separately authorized actuator test. |
| Rev-A CAD/fabrication/order review | Captured/routed connectivity, native reports, reviewed rules and assembly outputs are recorded in the [final review](rev-a/evidence/FINAL_REVIEW.md). D0–D7 retain the independent owner/component/SOA/assembly dispositions, and owner review precedes any order. A clean report does not waive those dispositions or the recorded native-process failure. |
| All Rev-B production gates | B01–B14 preserve inrush, regeneration, lift, converters, arm current, selectivity, final mechanics/harness and stop-architecture measurements. Production remains false. |

Open primary-data proof gaps, notably shared-shunt failure independence, main hot resistance at minimum gate drive, full installed-capacitance SOA and repetitive braking duty, are visible design-review dispositions. They must not be relabelled as measured passes or silently waived by an ERC/DRC result.
