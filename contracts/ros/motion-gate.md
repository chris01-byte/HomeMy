# Motion Gate Contract

Status: proposed. Implemented in `src/homemy_motion_gate` and tested in simulation; never run on the robot. The second, electrical motion gate in the PMU does not exist yet.
Owner: HomeMy platform and safety integration.

## Purpose

The motion gate is the one place in the HomeMy software that lets drive commands reach the drive (software concept, section 5.4). It decides afresh at every cycle whether the robot may move now. It never decides where to go.

It is a software function. It does not replace the emergency stop, the PMU motion gate, or any other hardware protection.

## Interfaces

Inputs:

| Topic | Type | Meaning | Freshness |
| --- | --- | --- | --- |
| `/homemy/mapping_mode/active` | `std_msgs/Bool`, latched | mapping mode active | 1.5 s |
| `/homemy/mission/drive_active` | `std_msgs/Bool`, latched | a drive mission is active | 1.5 s |
| `/homemy/lifecycle/state` | `std_msgs/String`, latched | lifecycle state | 3.0 s |
| `/homemy/safety/estop` | `std_msgs/Bool` | emergency stop pressed | 1.0 s |
| `/homemy/controller/link` | `std_msgs/Bool` | radio link of the controller up | 0.2 s |
| `/homemy/localization/ready` | `std_msgs/Bool` | position on the map is trusted | 1.0 s |
| `/homemy/cmd_vel/teleop` | `geometry_msgs/Twist` | commands from the controller | 0.25 s |
| `/homemy/cmd_vel/nav` | `geometry_msgs/Twist` | commands from navigation | 0.25 s |
| `/scan_masked` | `sensor_msgs/LaserScan` | LiDAR scan with blind sectors as NaN | 0.3 s |

Outputs:

| Topic | Type | Meaning |
| --- | --- | --- |
| `/cmd_vel` | `geometry_msgs/Twist` | command to the drive, 20 Hz: the gated command, or zero |
| `/homemy/motion_gate/status_json` | `std_msgs/String`, latched | mode, open or closed, reasons, command |

The gate is the only publisher of `/cmd_vel`. The app bridge refuses `/cmd_vel`, and no HomeMy profile may publish to it.

## Rules

1. **Exactly one mode drives.**

   | Mode | Condition | Commands from | Additionally required |
   | --- | --- | --- | --- |
   | mapping | mapping mode active | `/homemy/cmd_vel/teleop` | controller link up |
   | mission | drive mission active | `/homemy/cmd_vel/nav` | localization ready |

   Neither mode active means `mode_off`; both active means `mode_conflict`. Both keep the gate closed.
2. **The robot must be ready.** The lifecycle state must be READY, READY_LIMITED, or OPERATING, and the emergency stop must be reported released.
3. **Everything must be fresh.** A missing, stale, malformed, or non-finite input closes the gate. Nothing ever opens it by default.
4. **Speed limits.** Mapping: 0.20 m/s and 0.70 rad/s. Mission: 0.25 m/s and 0.60 rad/s. Commands are clamped, never scaled up.
5. **Reactive protection.** See below.
6. **Nothing latches here.** When the cause is gone, the gate opens again at the next cycle. Only the emergency stop and hardware faults latch, in hardware and in the lifecycle state (`docs/decisions/2026-11-17-self-healing-and-latching.md`).

When closed, the gate publishes an explicit zero at 20 Hz, so the drive's own watchdog is always fed with a known command.

## Reactive Protection

The gate checks every command against the latest masked scan:

- It moves the robot outline (the rounded 400 × 500 mm base from `homemy_description`) along the commanded motion for 1.0 s, or at least 5 cm.
- If any scan point would come closer to the outline than 5 cm **and** closer than it is now, the command is blocked. Motion away from an obstacle stays allowed, so the robot can back out of a stop.
- After a block, a command passes only when the protection has been clear for 0.5 s (clear time).
- Points in the blind sectors are NaN and ignored.

The values are simulation proposals. Margin, horizon, and clear time are commissioning results (`contracts/hardware/obstacle-protection.md`).

Known gaps:

- The protection remembers nothing. An obstacle that lies only in a blind sector, close to the struts, can be hit when the robot turns.
- Obstacles below the scan plane (164 mm) and at arm height are not seen. The owner accepted this for the laboratory and the prototype.
- OAK depth is not an input yet.
- The arms are not in the outline. They are assumed to stay inside the base while driving.

## Validation So Far

Simulation only, 2026-11-19:

- 32 unit tests of the decision logic: each mode, each missing or stale input, lifecycle states, emergency stop, frozen radio link, clamping, non-finite commands, block and clear time, no latching;
- 17 unit tests of the protection: outline distances, rounded corners, wall ahead with and without reverse, rotation near a rear obstacle, moving away from a touching point, creeping speed, invalid configuration;
- a ROS test of the node: command passes; link loss closes; link return heals; a wall stops forward and allows reverse; zero at a fixed rate without inputs; the outline file is required;
- the S2 end-to-end test (`src/homemy_bringup/test/test_drive_sim_e2e.py`), see the manual-drive contract.

## Open Points

- Arm side of the gate (drive or arms, measured standstill), software concept section 5.4.
- The PMU motion gate and its link to this node.
- A short obstacle memory for the blind sectors.
- Measured margins, speeds, and clear time.

## Rollback

Stop the motion gate. Nothing publishes `/cmd_vel` any more, and the drive's watchdog stops the robot. No other node may take over its role.
