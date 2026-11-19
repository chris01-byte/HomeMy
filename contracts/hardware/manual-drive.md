# Manual-Drive Contract

Status: proposed. Implemented and tested in simulation (`src/homemy_manual_drive`, `src/homemy_motion_gate`, the S2 test stand); nothing has run with the real controller or on the robot.
Owner: HomeMy platform.

## Scope

Driving HomeMy with the wireless controller during mapping mode, so that a technician or the customer can map the home once (`docs/decisions/2026-11-16-manual-mapping-and-app-room-management.md`). The app switches mapping mode on and off (`contracts/api/app-bridge.md`); the motion gate decides whether a command reaches the drive (`contracts/ros/motion-gate.md`).

Out of scope: driving outside mapping mode, driving from the app, and driving the arms.

## Controller

- Sony DualShock 4, model CUH-ZCT2E, over Bluetooth, the same model as on Amadeus. It is delivered paired with the robot.
- Assignment kept from Amadeus by owner decision: direction pad up/down drives, left/right turns, R1 held selects the faster speed. There is no dead-man button (owner decision 2026-11-16).
- The direction pad is digital, so there is no creeping from stick drift. Each press asks for the full speed of its level; the drive ramps smooth it.

| Level | Linear | Turning |
| --- | --- | --- |
| normal | 0.12 m/s | 0.40 rad/s |
| faster (R1) | 0.20 m/s | 0.70 rad/s |

These are the Amadeus values and proposals for HomeMy. The motion gate additionally clamps every mapping command to 0.20 m/s and 0.70 rad/s.

## Command Path

```
DualShock 4 --Bluetooth--> joy_node --/joy--> teleop_twist_joy --/homemy/cmd_vel/teleop-->
    motion gate --/cmd_vel--> drive
```

- `joy_node`: dead zone 0.20, repeats the last state at 20 Hz while Linux has the device (`autorepeat_rate`).
- `teleop_twist_joy` publishes only to `/homemy/cmd_vel/teleop`. No HomeMy profile may send controller commands to `/cmd_vel` or to the drive directly. The Amadeus paths around the gate (`cmd_topic:=/cmd_vel`, the "befreien" profile) are not ported.
- The configuration is `src/homemy_manual_drive/config/manual_drive.yaml`.

## Radio Link

### The problem

The software never sees the radio link itself:

- The Linux gamepad interface reports only changes.
- `joy_node` repeats the last known state while the input device exists. It stops only when Linux removes the device (checked in the Jazzy source of `joy` 3.3.0).
- If the radio link breaks silently (out of range, interference, a flat battery that does not send a disconnect), Linux keeps the device until the Bluetooth link supervision timeout has passed. The Bluetooth specification's default is 20 s; the value on the HomeMy computer is to be measured.
- During that time `joy_node` keeps repeating, for example "forward". Repeated `/joy` messages are therefore no proof that the controller is still there.
- On Amadeus (Humble), `joy_node` did not even notice a removed controller and had to be restarted (roboter_ws commit `f3a9094`). A disconnect with a direction held was never tested.

### The solution

- While its radio link is up, the DualShock 4 streams input reports continuously, also when nothing is pressed. The Linux driver (`hid-playstation`, or `hid-sony` in older kernels) exposes the gyroscope and accelerometer as a separate input device, "… Wireless Controller Motion Sensors". It emits one report per received radio packet, because the sensor timestamp changes in every packet.
- The node `controller_link` reads that device and publishes `/homemy/controller/link` (`std_msgs/Bool`) at 20 Hz. It reports true only if a motion report arrived within the last 0.15 s.
- The motion gate drives in mapping mode only while `/homemy/controller/link` is true and at most 0.2 s old.
- The mapping-mode manager shows the controller as connected from the same signal (`contracts/api/app-bridge.md`).
- If two controllers are paired and both show a motion device, the node cannot tell them apart and reports the link down.

The report rate, the 0.15 s timeout, and the existence of the motion device under Bluetooth are assumptions until step M1.

## Required Behavior

- **Mapping mode off:** controller input moves nothing.
- **Controller link down, frozen, or stale:** the robot stands still. Mapping mode stays active (owner decision). When the link returns, driving continues without any other action.
- **App disconnected:** no effect on driving or on mapping mode.
- **Emergency stop pressed, lifecycle not ready, scan stale:** the robot stands still; all of these heal, except that the emergency stop itself latches in hardware.
- **Obstacle:** the reactive protection of the motion gate blocks motion towards an obstacle and allows motion away from it. Backing out of a protection stop with the direction pad therefore works without a special profile.
- **No input for 300 s:** mapping mode ends by itself (`contracts/api/app-bridge.md`).

## Commissioning

| Step | Content | Motors |
| --- | --- | --- |
| M0 | Simulation: the S2 end-to-end test drives the mapping route through the real teleop profile and motion gate; frozen link, emergency stop, and obstacle cases. Done 2026-11-19 in simulation. | none |
| M1 | On the HomeMy computer: input devices and names, the motion device under Bluetooth, report interval while idle and while pressing, axis and button numbers, `joy_node` repeat, permissions (`input` group). | none |
| M2 | Radio loss without motors: switch off, walk out of range, shield the controller in a metal box. Measure the time to `link` false and to device removal, and check that the gate closes. Two paired controllers. | none |
| M3 | Wheels raised, a person present: hold forward, then shield the controller. Measure the time to a zero command and to wheel standstill. | raised wheels |
| M4 | On the floor at low speed, supervised: stopping distance on radio loss with a direction held, at both speed levels; obstacle stop and backing out. | floor, supervised |
| M5 | Record the accepted values: link timeout, speeds, stopping distances, clear time. | none |

Every step needs the explicit approval of a person present at the robot once motors are involved (`AGENTS.md`). A failed step keeps manual driving disabled.

## Validation So Far

Simulation only, 2026-11-19:

- unit tests of the link watchdog: device discovery, report decoding across split reads, timeout, device loss, two controllers;
- a ROS test with a FIFO standing in for the motion device: link up with reports, down when they stop (frozen link), up again, down when the device closes;
- static tests of the profile: commands only to the gate, direction pad, no dead-man button, speeds inside the gate limits, link timeout tighter than the gate's;
- the S2 end-to-end test (`src/homemy_bringup/test/test_drive_sim_e2e.py`): nothing moves with mapping mode off; with the link frozen while `/joy` keeps repeating, the robot stops within 1 s and less than 0.15 m and stands still; driving resumes when the link returns; the emergency stop stops and releases; the full mapping route ends without contact.

Simulation results are not robot acceptance.

## Open Points

- Report rate and timeout on the real controller (M1, M2).
- Re-pairing procedure for the customer, if the delivered pairing is lost.
- Speeds and drive ramps for HomeMy (M4).

## Rollback

Remove `manual_drive.launch.py` from the robot composition. Without teleop commands and a link signal the motion gate stays closed in mapping mode; mapping is then impossible, but nothing can move.
