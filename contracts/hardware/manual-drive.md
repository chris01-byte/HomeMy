# Manual-Drive Contract

Status: proposed. Implemented and tested in simulation (`src/homemy_manual_drive`, `src/homemy_motion_gate`, the S2 test stand); nothing has run with the real controller on HomeMy. The owner drove Amadeus with the same controller and the same profile.
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

- `joy_node`: dead zone 0.20, repeats the last state at 20 Hz (`autorepeat_rate`), so a held direction keeps driving.
- `teleop_twist_joy` publishes only to `/homemy/cmd_vel/teleop`. No HomeMy profile may send controller commands to `/cmd_vel` or to the drive directly. The Amadeus paths around the gate (`cmd_topic:=/cmd_vel`, the "befreien" profile) are not ported.
- The configuration is `src/homemy_manual_drive/config/manual_drive.yaml`.

## No Separate Supervision of the Radio Link

Owner decision of 2026-11-19, for the first prototype and the test laboratory: manual driving stays as simple as on Amadeus. Pressing the direction pad drives, releasing it stops. There is no separate supervision of the radio link.

What stops the robot:

- **Released direction pad:** the teleop command is zero.
- **No controller messages** (controller switched off and removed by Linux, joystick driver stopped): the last command is older than 0.25 s, and the motion gate sends zero.
- **Obstacle, emergency stop, mapping mode off, app stop:** as below.

Accepted for the laboratory: if the radio link breaks silently while a direction is held (out of range, interference), the joystick driver keeps repeating that direction until Linux removes the controller. During that time the robot keeps driving at mapping speed; the obstacle protection, the stop in the app, and the stop at the robot remain. The owner did not observe a problem with this on Amadeus. How long Linux takes on the HomeMy computer is measured once in step M2.

A watchdog that reads the controller's motion-sensor reports was built and tested in simulation on 2026-11-19 and removed again by this decision. It is in the repository history (last contained in commit `b372d69`: `src/homemy_manual_drive/homemy_manual_drive/controller_link.py` and the `controller_link` input of the motion gate) and can be restored if it is wanted before customer use.

## Required Behavior

- **Mapping mode off:** controller input moves nothing.
- **Direction pad released or controller messages missing:** the robot stands still. Mapping mode stays active (owner decision). When input returns, driving continues without any other action.
- **App disconnected:** no effect on driving or on mapping mode.
- **Emergency stop pressed, lifecycle not ready, scan stale:** the robot stands still; all of these heal, except that the emergency stop itself latches in hardware.
- **Obstacle:** the reactive protection of the motion gate blocks motion towards an obstacle and allows motion away from it. Backing out of a protection stop with the direction pad therefore works without a special profile.
- **No input for 300 s:** mapping mode ends by itself (`contracts/api/app-bridge.md`).

## Commissioning

| Step | Content | Motors |
| --- | --- | --- |
| M0 | Simulation: the S2 end-to-end test drives the mapping route through the real teleop profile and motion gate; release, controller off, emergency stop, and obstacle cases. Done 2026-11-19 in simulation. | none |
| M1 | On the HomeMy computer: axis and button numbers of the direction pad and R1, `joy_node` repeat, permissions (`input` group). | none |
| M2 | Wheels raised, a person present: press drives, release stops; faster level with R1. Hold forward and switch the controller off, then once walk out of range: note how long the wheels keep turning. | raised wheels |
| M3 | On the floor at low speed, supervised: stopping distance on release at both speed levels; obstacle stop and backing out. | floor, supervised |
| M4 | Record the accepted values: speeds, stopping distances, clear time, and the time from M2. | none |

Every step needs the explicit approval of a person present at the robot once motors are involved (`AGENTS.md`). A failed step keeps manual driving disabled.

## Validation So Far

Simulation only, 2026-11-19:

- static tests of the profile: commands only to the gate, direction pad, no dead-man button, speeds inside the gate limits, the joystick repeat faster than the gate's command timeout;
- unit and ROS tests of the motion gate: a released direction pad and missing controller messages both give a zero command, and driving continues when input returns;
- the S2 end-to-end test (`src/homemy_bringup/test/test_drive_sim_e2e.py`): nothing moves with mapping mode off; letting go stops the robot and pressing again drives on; a controller that is switched off stops the robot within 1 s and less than 0.15 m while mapping mode stays active; the emergency-stop signal stops and releases; the full mapping route ends without contact.

Simulation results are not robot acceptance.

## Open Points

- How long the robot keeps driving after a silent radio loss with a direction held (M2).
- Re-pairing procedure for the customer, if the delivered pairing is lost.
- Speeds and drive ramps for HomeMy (M3).

## Rollback

Remove `manual_drive.launch.py` from the robot composition. Without teleop commands the motion gate stays closed in mapping mode; mapping is then impossible, but nothing can move. To bring back the radio-link watchdog, restore it from commit `b372d69`.
