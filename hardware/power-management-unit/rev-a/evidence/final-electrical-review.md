# Final source electrical review

`rev_a_engineering_prototype: true`  
`rev_b_production: false`  
Date: 2026-09-10. Scope: four source part records, schematic/integration generators and critical hardware paths. No PCB changes or physical tests. [Machine-readable audit](final-electrical-review.json) records source hashes and 55 passing checks across 430 integrated components, refreshed after the integration owner added BC1–BC15.

| Finding | Correction and disposition |
| --- | --- |
| F01 — CAN termination population lost | R243/R244/C244 specified `population=DNP`, but the generator originally read only `dnp`. Added explicit booleans to wake parts; parent also normalized the loader. Exactly those three components plus J13 are now DNP. Regeneration must preserve that selection into schematic/PCB/BOM. |
| F02 — Chopper reference test point omitted | Integration requested absent `CHOP_REF_2V5` and skipped TP28. Correct source net is `CHOP_REF2V5`; parent corrected the generator. Audit confirms the actual reference test point. |
| F03 — Default-low leakage margin insufficient | Changed R216, R217 and R237 from100kΩ to10kΩ, same0805 footprint. On AON_WAKE_EN, a conservative30.36µA aggregate partial-power-down leakage could raise the old100kΩ∥1MΩ network to2.76V. The new10kΩ∥1MΩ, including1% resistance tolerance, bounds it near0.304V, below LM74930's0.41V guaranteed falling threshold. Reset and motion-enable nodes also gain low-state margin. Added load occurs when their signals are high; timing/power-ramp measurements remain required. |
| F04 — LED current crossed logic star | J18 return originally used LOGIC_GND while J11 used LOGIC_5V_N, forcing strip current through NT9. Chopper owner changed J18.3; this review changed C246.2 to LOGIC_5V_N. The buffer keeps the quiet logic reference. Route LED power and capacitor return broadly/directly to J11/NT8. |
| F05 — Optocoupler collector ERC type | Chopper owner changed U34/U35 collector pin4 from passive to open_collector. Nets/pad maps remain unchanged. |

The [LVC AND gate leakage table](https://www.ti.com/lit/ds/symlink/sn74lvc1g11.pdf) and [LM74930 enable thresholds](https://www.ti.com/lit/ds/symlink/lm74930-q1.pdf) support F03's conservative static bound. This bound does not claim behavior during arbitrary rail ramps.

The ten intended return net ties have the expected source/destination pairs; NT9 is the logic star, and NT10 joins the chopper's local analog reference to its power return. The footprint generator declares actual net-tie pad groups and a copper bridge. Physical bar segmentation and return routing still need PCB review.

The nine power flags correspond only to explicit external sources, resistor/shunt/FET transfer paths or intentional ground ties. No blanket flag was added to every power-input pin, and no critical logic input was converted to passive to suppress ERC. A flag permits ERC to model a controlled path; it does not prove that the switch is on or that its copper exists.

Critical checks include LM exposed pad floating, current-sense polarity, CAN pinout, switched supplies, FF Q/Q-bar and asynchronous controls, LTC enable/KILL, start grant, main brownout memory, motion current/thermal/UV/chopper/watchdog/permission paths and continued analog chopper operation after motion latch-off. TI [flip-flop](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf), [dual NAND](https://www.ti.com/lit/ds/symlink/sn74lvc2g00.pdf) and [watchdog](https://www.ti.com/lit/ds/symlink/tps3431.pdf) pin tables were rechecked.512 stable-state motion-interlock combinations match the required AND/clear behavior.

No unresolved **source-level** failure remains in the checked set. This is not an unrestricted electrical release: partial-power ramps/propagation races, actual Kelvin/copper implementation, shared-shunt component-failure independence, hot SOA/full940µF startup, leakage/timing and thermal/EMC behavior retain the documented review/test gates. Regenerate CAD/BOM and run native checks after the corrected source snapshot.
