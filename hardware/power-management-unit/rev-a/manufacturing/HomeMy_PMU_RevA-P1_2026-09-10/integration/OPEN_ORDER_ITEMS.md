# Open external order positions — Rev A-P1

## Required before PCB ordering

None of the nine unresolved external BOM rows requires a PCB footprint change under the frozen interfaces below. Supplier acceptance of special PCB fabrication requirements is still required.

## Required before energization

| Item | Frozen PCB/external boundary | Evidence required before use |
|---|---|---|
| EXT_AL_PANELS | Two independent external 305 x 305 x 3.2 mm resistor heat-spreader panels; no attachment holes are added to the PCB. | Select alloy, transfer actual RH100 hole pattern, guards, fasteners and thermal sensor attachment; assemble and inspect before a resistor-bank pulse. |
| EXT_LUG_BATT | M5 horizontal faces on installed Wurth 7461103 at J1/J2; 6 mm2 battery conductors. | Select compatible lug, conductor and crimp tool; verify thread engagement, cable clearance, resistance and torque no greater than 2.2 Nm. |
| EXT_LUG_ARMS | M5 horizontal faces at J3-J6; 4 mm2 arm conductors. | Select compatible lugs and crimp system; keep separate ARM_L_N/ARM_R_N returns; verify fit, restraint and current/temperature envelope. |
| EXT_CABLES | Use the already selected PCB headers and their specified mating plugs. Harness, ferrules and restraints are external; no PCB holes or connector changes. | Release cable lengths, wire grades, pin-to-pin list, coding, polarity and crimp/terminal acceptance; resolve branch-specific cross-sections against design loads and routing. |
| EXT_COVERS | Independent enclosure-mounted insulating support and guards; use the existing four PCB mounting holes. At least 15 mm below PCB and planned 25 mm axial M5 tool access; preserve antenna keepout. | Dimension external guards/support to the fixed PCB and busbars, inspect live-part coverage, clearances and cable-force restraint before power. |
| EXT_BUTTON | Normally-open dry contact via existing J20 connector and matching cable; inject no external voltage. | Select switch/mating harness, confirm pinout and power-button/rearm behavior with a current-limited motorless fixture. |
| EXT_PERMISSION | Existing J22 3.3 V permission loop; deenergized contact must be open. No 24 V injection or permanent bypass jumper. | Select and accept external emergency-stop/permission circuit and harness; verify open/unpowered fault forces Motion OFF before actuator enable. |
| EXT_FUSE | External 60 A battery fuse and holder upstream of J1; neither mounts on the PCB. | Select exact DC-rated fuse/holder, interruption rating and time-current curve for the pack/wiring; verify before battery attachment. |
| EXT_CONVERTERS | External PC input at J9, logic converter input at J10 and regulated 5 V return at J11; lift input at J8. Use fixed Phoenix headers/mates. No converter module footprint exists on this PCB. | Select actual modules, including China-sourced modules if desired; verify wiring, 27.5-42 V operating input, transients, input capacitance/inrush, 5 V output and isolation/return behavior against POWER_STAGE and bring-up limits before connecting them. |

A nonconforming external selection is rejected or requires a new CAD/package revision. These open items do not authorize bypasses, permanent permission jumpers, connector substitution or battery connection.
