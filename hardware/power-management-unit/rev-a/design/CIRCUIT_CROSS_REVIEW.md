# Independent circuit interconnection review

Date: 2026-09-10. Scope: component/net definitions in the power, wake/I/O, chopper and integration records. This is a peer review of intended connectivity and published device behavior; the generated CAD connectivity, ERC/DRC, timing waveforms and hardware remain separate evidence. The source hashes at review completion are in `../evidence/chopper/cross-review-sources.json`.

## Fault found and corrected

The original motion latch observed TPS48110 FLT_I and FLT_T but did not observe its native undervoltage turn-off. Those outputs indicate current/timer and temperature faults; a SYS-only voltage dip could turn the motion FETs off while leaving 3.3 V, MOTION_ARMED and INP high. Recovery could then restart motion. The main UV detector senses battery input and does not establish detection of every SYS-only dip. [TPS4811 pin table and UV behavior](https://www.ti.com/lit/ds/symlink/tps4811-q1.pdf).

The power author added U5 TLV3011B: SYS divider to IN+, its internal reference to IN−, V3V3 supply and an open-drain output directly on MOTION_FLT_N. I checked the physical pin map, polarity, shared pull-up and connection through U28/U50 to U27 asynchronous clear. Persistent SYS undervoltage now clears the external motion latch; voltage recovery does not supply a new rising clock. The independent threshold is above the native **falling** UV corner, which is the relevant comparison. Short-pulse coverage remains bounded by comparator overdrive/propagation and the latch's input requirements; the stated 4 µs delay applies only under its specified overdrive condition. See the latest POWER_STAGE table for the selected standard divider value and final numerical corners. [TLV3011B](https://www.ti.com/lit/ds/symlink/tlv3011.pdf).

## Other reviewed paths

| Invariant | Traced implementation | Review conclusion and limit |
| --- | --- | --- |
| Held-button battery attachment does not start | U17 AON reset clears U18; U19 presets only after reset-good and button release | Boolean connection is consistent. Debounce/supply sequencing remains a motorless test. |
| Failed boot loses main hold | Nonretriggerable U21 start grant ORs with ESP hold at U22; grant expiry and absent hold lower LTC2954 KILL | No direct GPIO path retriggers the timer. Physical timing/capacitance must meet the published bench bounds. |
| Main fault does not retry | U23 captures qualified fault, U25 removes main EN, Q20 sinks KILL; only raw wake EN low clears U23 | Normal fault deassertion cannot itself re-enable the path. Brief main startup capture mask is independently documented. |
| Switched brownout during startup does not loop | U55 records the first switched supervisor-good edge; U56/U57/U58 then latch its loss | Logical coverage extends through the remaining start-grant interval. Supervisor detection limits still apply. |
| Motion authority starts absent | U27 asynchronous clear includes ESP reset/watchdog/permission/main status; clock is explicit ESP_MOTION_RESET | Request alone cannot arm, and recovery alone cannot arm. Actual MCU boot pin behavior and pulse races still require verification. |
| Analog chopper fault removes motion | U34 collector drives CHOP_FAULT_N, pulled up on V3V3; U28 includes that input, then U50 clears U27 | OV and thermal fault reach hardware, not only the ESP input. |
| 46 V trip leaves braking available | U32 OV output enters U34 fault OR; U33 IN− depends on thermal/qualification, not OV | The motion gate can open while the bus-powered chopper continues. |
| Chopper startup does not create a deterministic false fault | U36 CT open qualifies reference; Q43 gates fault LED supply, Q44 completes Q41 return only when qualified | Startup comparator states cannot sink the optocoupler output before qualification. Initial motion must be stationary during reference establishment. |
| NTC short/open can inhibit without firmware | Independent analog divider/window controls Q41 and fault OR; telemetry uses another NTC element | Local sensor wiring is separate. All returns eventually share the system star, so this is not a claim of complete system galvanic isolation. |
| Switched MCU is not directly pulled up from 10 V | Chopper interfaces use optocouplers; U60/U65 isolate live bus/AON/service sources; LED buffer OE follows switched supervisor | The reviewed signal connections avoid a direct unswitched high-voltage pull-up into ESP pins. Off leakage and real ground bounce remain measured quantities. |
| Lower-voltage rails connect consistently | Schematic builder aliases +3V3→V3V3 and +5V→V5V | Raw source spelling differences are intentional and normalized at assembly. |
| Braking frequency has defined populated capacitance | C312/C313 total940µF nominal on MOTION_BUS; the main test keeps motion disabled | Capacitor ripple/frequency and separate motion inrush have explicit analytical bounds and bench conditions in CHOPPER_MECHANICS/POWER_STAGE. |

The review does not turn unbounded hot SOA, maximum clamp voltage, exact current selectivity, full-energy regenerative behavior, press-fit assembly or individual supplier stock into completed validations. No new deterministic startup, self-hold or fault-recovery error was found in the other paths above after the documented revisions. The generated board still needs its own integrated physical checks.
