# Protection and measurement routing review

Revision A engineering review; no hardware measurements or order release. The
native PCB remains the authority. `scripts/review_critical_routing.py` loads it
read-only and writes `reports/critical-routing-geometry.json`, including the board
SHA-256, individual segments, pad coordinates, shortest explicit-track paths and
layer transitions. This is separate from native ERC/DRC and from schematic net
identity checks.

The final main-board snapshot reviewed at 2026-09-10 18:17:04 UTC has SHA-256
`70bb8eb588f2fc7200f718df0e11659aad3c40c7e9d5652228eb7a58d232065f`.
All 46 requested explicit paths are present. The check of all 125 locked analog
track/via objects finds zero internal different-net copper collisions. The
review script wrote no PCB. These geometry results do not replace the final
native ERC/DRC reports or the independent source-to-board parity audit.

## Finding and deterministic correction

The first complete autoroute had electrically connected, widely separated sense
branches. In particular, C4 reached U1 CS+ through 19.55 mm of routed copper and
two vias; its CS− connection was 25.72 mm. The original C241 negative connection
to the INA228 took 6.31 mm. These geometries did not implement a small local
differential filter loop merely because their assigned nets were correct.

`scripts/analog_routing_corrections.py` is the reproducible placement/routing
overlay. Its API `apply_analog_routing_corrections(board)` modifies the supplied
in-memory board, preserves pre-existing locked copper, and never saves the main
PCB itself. It changes no net, component value, MPN or pin mapping. It refuses
pre-existing locked copper on its own ten nets to prevent accidental duplicate
application. The caller must reroute displaced foreign signal nets, refill zones,
place reference text and perform native DRC before retaining a final board.

The overlay uses separate local pickups at each physical main shunt sense pad
for the controller and INA branches. It puts the controller trunks on In2.Cu
and the INA branch on In1.Cu. Most paired trunks have 0.65 mm center spacing and
0.20 mm trace width; divergence at the 8.05 mm-spaced shunt pads, IC fanout and
separate threshold resistor branches is explicit. The main controller corridor
is at x = 30.5/31.15 mm between the x ≤ 28 mm input force region and x ≥ 33 mm
sensed force region. The motion corridor is at x = 119.5/120.15 mm between the
system and motion sensed force regions. Both pass below the transfer-via fields
before turning toward their controllers, and stay above the y = 109–133 mm
high-current return strip. Their layer choice does not claim a continuous
ground shield or a calculated electromagnetic coupling limit.

The final native board retains the corrected filter connections and paired
trunks, with the following measured geometries. The JSON hash identifies the
actual saved board rather than an isolated overlay test.

| Path | First route, mm | Final board, mm | Final path layers / transitions |
| --- | ---: | ---: | --- |
| C4 pin 1 → U1 CS+ | 19.552 | 2.490 | F.Cu, no via |
| C4 pin 2 → U1 CS− | 25.723 | 2.490 | F.Cu, no via |
| C5 pin 1 → U1 ISCP | 16.650 | 2.564 | F.Cu, no via |
| C11 pin 1 → U2 CS+ | 6.575 | 2.833 | F.Cu, no via |
| C11 pin 2 → U2 CS− | 8.682 | 3.297 | F.Cu, no via |
| C12 pin 1 → U2 ISCP | 17.064 | 4.431 | F.Cu, no via |
| C241 pin 1 → U11 IN+ | 2.962 | 3.625 | F.Cu, no via |
| C241 pin 2 → U11 IN− | 6.315 | 3.045 | F.Cu, no via |
| RSH1 sense+ → R21 input | 97.042 | 88.573 | F.Cu / In2.Cu, 2 vias |
| RSH1 sense− → U1 CS− | 88.049 | 94.024 | F.Cu / In2.Cu, 2 vias |
| RSH2 sense+ → R30 input | 93.096 | 114.029 | F.Cu / In2.Cu, 2 vias |
| RSH2 sense− → U2 CS− | 102.802 | 113.640 | F.Cu / In2.Cu, 2 vias |

The longer motion route deliberately follows the other sense leg in a clear
corridor. Absolute trace length and matching are not evidence of selectivity,
threshold precision or universal immunity to fast differential interference.
The local capacitor connections and paired route area are the relevant concrete
improvements. Input resistor branches remain independent; no filter resistor is
shared between the INA228, CS+ and ISCP functions.

The INA228 shunt-to-filter branches are 39.663 mm positive and 43.812 mm negative,
each with two physical via transitions using F.Cu and In1.Cu. From R223/R224 to
the INA228 inputs the paths are 6.692 mm and 10.185 mm, entirely on F.Cu. The
independent ISCP input branches measure 102.041 mm from RSH1 to R23 and
120.147 mm from RSH2 to R32. These are branch lengths; paths ending at different
filter resistors are not directly comparable as a matched differential pair.

An isolated native DRC diagnostic found collisions with pre-existing foreign
signal routes and relocated reference text. After those foreign routes were
removed, the integrated native check exposed an additional CS-feed via crossing
the motion-negative inner trace. The via was moved from (169, 91.5) to
(170, 91.5) mm. The helper now independently checks every new track/via pair on
each shared copper layer: this check detects the former intersection and finds
zero internal new-copper collisions for the corrected coordinates. It prevents
a crowded multi-net short report from being mistaken for an exhaustive pair
list. Native DRC still owns pads, zones, hole spacing and the final integrated
board. The temporary diagnostic's library lookup warnings arise from its
separate test-project location, and must not replace the actual project-library
check.

## Gate and bootstrap observations

The frozen routing002 session and reviewed local completion repairs are now
integrated into the main board. `reports/final-routing-integration.json` records
the integration and preservation of all 1,959 previously protected copper
objects. The independent final geometry measurements below refer to the main
board hash at the beginning of this document.

The preceding temporary candidate had exact source/XML/physical-pad parity and
a native DRC JSON reporting zero violations and zero unconnected items. Its
portable CLI emitted registry errors and required timeout cleanup after writing
that report. `reports/routing002-completion-review.json` records these distinct
outcomes and the frozen session, repair plan and candidate-board hashes. That
candidate evidence is separate from the final main-board native checks.

`scripts/final_routing_repairs.py` and `FINAL_ROUTING_REPAIRS.json` finish six
connections left by that frozen session. They provide U2's SRC escape and
common-source return, connect the INA supply decoupler, ground the J16/U19/U53
local nodes, and connect U4's grounded exposed pad to BATT_N with a thermal via
and a route around the converter feed. Small PU, FLT_T and AON supply doglegs
move to permit the escapes. All electrical nets and all 1,959 pre-existing locked
copper items remain intact. Twenty-two duplicate dangling-stub segments and
nine replaced local segments are identified by exact net/layer/geometry rather
than import-dependent UUIDs; native DRC confirms that their removal leaves no
missing connection in the completed candidate.

The final controller-to-individual-gate-resistor paths are:

| Gate resistor input | Main/motion path, mm | Physical via transitions | Copper layers |
| --- | ---: | ---: | --- |
| R1 | 80.227 | 3 | F.Cu, In1.Cu, In2.Cu |
| R2 | 57.371 | 3 | F.Cu, In1.Cu, In2.Cu |
| R3 | 35.256 | 3 | F.Cu, In1.Cu, In2.Cu |
| R4 | 99.253 | 3 | F.Cu, In1.Cu, In2.Cu |
| R5 | 73.931 | 3 | F.Cu, In1.Cu, In2.Cu |
| R6 | 47.056 | 3 | F.Cu, In1.Cu, In2.Cu |
| R7 | 87.150 | 3 | F.Cu, In1.Cu, In2.Cu |
| R8 | 123.582 | 4 | F.Cu, In1.Cu, In2.Cu |
| R9 | 84.169 | 2 | F.Cu, In1.Cu |
| R10 | 49.612 | 2 | F.Cu, In1.Cu |

The individual 10 Ω resistor-to-gate paths are 6.088 mm for Q1/Q2/Q3/Q7/Q8
and 7.913 mm for Q4/Q5/Q6/Q9/Q10, all on F.Cu with no via. The longer R8 trunk
must be included in individual-device VGS measurements. These lengths establish
physical geometry; they are not a measured gate-loop inductance, guaranteed
damping ratio or turn-off time.

| Local supply/drive path | Final length, mm | Physical via transitions | Copper layers |
| --- | ---: | ---: | --- |
| C9 pin 1 → U2 BST | 6.843 | 0 | F.Cu |
| C29 pin 1 → U2 BST | 10.843 | 0 | F.Cu |
| U2 SRC → C9 pin 2 | 16.316 | 2 | F.Cu, B.Cu |
| U2 SRC → C29 pin 2 | 20.035 | 3 | F.Cu, B.Cu, In1.Cu |
| C206 pin 1 → U11 VS | 7.481 | 2 | F.Cu, B.Cu |
| C2 pin 1 → U1 CAP | 10.089 | 0 | F.Cu |
| U2 PU → R34 pin 1 | 14.868 | 0 | F.Cu |
| U2 PD → R34 pin 2 | 17.454 | 2 | F.Cu, In1.Cu |

The SRC-return paths are explicitly measured through the repaired source escape.
Their filled-copper surroundings and the common gate/source return structure
still require an electromagnetic or physical assessment to establish loop area,
impedance and waveform behavior. The two positive bootstrap paths alone would
not describe the complete BST/SRC loop. The INA supply-decoupler route and main
charge-pump route also remain explicit bring-up observation points.

During the bounded motorless bring-up specified in `POWER_STAGE.md`, measure
VGS at the individual MOSFET gate/source terminals, BST−SRC at U2, both shunt
inputs at the controllers, and their differential error during current steps
and commanded/forced turn-off. Confirm that the controller-filter voltages do
not create nuisance trips and that gate peaks/ringing stay inside the actual
device limits. Do not substitute a waveform sampled only at the controller gate
pin for the remote MOSFET terminal waveform. This is a physical validation item,
not an assertion that an unmeasured gate waveform is already acceptable.

## Primary layout basis and measurement limits

The local archived [LM74930 datasheet](../evidence/power/lm74930-q1.pdf), section
8.5.1, calls for Kelvin sense connections and short controller/gate/source
connections. The [TPS4811 datasheet](../evidence/power/tps4811-q1.pdf), sections
8.3 and 9.6.1, places the differential suppression capacitors close to the device,
uses Kelvin shunt connections, and calls for a short BST/SRC loop. These
manufacturer instructions support the layout correction; they do not specify an
arbitrary maximum permissible trace length for this board.

The script's graph splits straight tracks at explicit junctions, connects vias
on their actual copper layers, and attaches pads only where a track endpoint is
inside the native pad shape. It measures copper centerlines plus short straight
pad-center leads and excludes vertical via barrel length. It rejects arcs rather
than silently estimating them. It does not analyze zone continuity, impedance,
field coupling or temperature. Use native connectivity and DRC for copper
continuity and spacing, then the physical test plan for transient behavior.
