# Only an Emergency Stop or a Hardware Fault Latches; Everything Else Heals

Status: accepted by the project owner. No implementation and no validation yet.
Date: 2026-11-17.

## Context

Amadeus enforced safety in the planning layer: a move was allowed only when every precondition was proven, and a failed proof usually ended the mission. Its October 2026 review counted 76 different abort and stale reasons, and the whole-mission result was 0 of 3. On 2026-10-15 the owner decided for Amadeus that a customer robot must heal itself and may stop the overall process only in exceptions.

The HomeMy contracts were written in August and September, before that lesson. Several of them say that motion never continues by itself after a stop.

On 2026-11-17 the owner decided the rule for HomeMy.

## Decision

**Exactly two causes may latch the robot, meaning that a person must reset it deliberately:**

1. an emergency stop;
2. a hardware fault.

**In every other case self-healing must bring the robot back to normal operation by itself.**

### What Latches

- Emergency stop or motor halt.
- A protection trip of the PMU: overcurrent, short circuit, undervoltage, overvoltage, or overtemperature.
- A drive, lift, arm joint, or gripper that reports a fault, or that still does not answer after its bounded reconnect attempts.

Latching is used where continuing by itself could cause harm or damage. A sensor that stays silent does not need a latch: without its data nothing that depends on it may move, the connection is retried, and operation continues when the data returns.

### What Heals

A stop is a pause, not the end of the mission. Examples:

| Situation | Healing |
| --- | --- |
| Obstacle in a protected volume | stand still; continue when the volume is clear again |
| Missing or stale sensor data | stand still and wait; reconnect the source |
| Position on the map uncertain or lost | search for the position again while standing |
| Route blocked | wait, plan again, try another route |
| Object not found, grasp failed | look again, try another grasp, within fixed limits |
| Unexpected contact | stop at once, then back off slowly along the path just travelled |
| External AI server unreachable | wait and retry; missions that need it wait or end with a clear message |
| App disconnected | no effect on the robot |
| A software process fails | restart it; the robot returns to READY |

Rules for healing:

- Every healing step is bounded in time, count, and distance.
- Every healing step starts from a confirmed standstill.
- Motion continues only after the cause has been gone for a defined clear time. The value is a commissioning result.
- When a mission cannot be completed, it ends with a clear result and the robot is in normal operation again, ready for the next command, without a reset.
- "Help needed" in the app is information and an offer to continue. It is not a lock.
- An object in the gripper is never dropped. The robot puts it down at the nearest reachable drop place, or holds it and reports.

### What Stays As It Was

- Power-on, restart, and READY never start motion by themselves. Motion needs an active mission or operating mode.
- Missing or stale data never permits motion.
- Perception, AI, and the app never grant motion authority.
- The emergency stop and the PMU protection are independent of the software.
- Whether a mission that was interrupted by a software restart continues by itself is not part of this decision. Until decided, it ends as interrupted and the robot returns to READY.

### Not Selected

- Requiring a confirmation in the app after every protection stop.
- Ending a mission because a proof, a time budget, or a freshness check failed once.
- Latching on lost localization, on a blocked route, or on an unreachable AI server.

## Evidence

- Amadeus self-healing concept (`docs/wohnungserkundung/KONZEPT_SELBSTHEILUNG.md`, roboter_ws branch `claude/blissful-pasteur-s1eivj`): 76 abort and stale reasons, whole missions 0 of 3 under the earlier approach; owner decision of 2026-10-15; healing ladder H0 to H5.
- Owner statement of 2026-11-17 for HomeMy.
- No HomeMy measurement exists.

## Impact

Changed with this decision:

- `contracts/hardware/obstacle-protection.md`: a protection event is a pause; motion continues by itself when inputs are healthy and the volume is clear.
- `contracts/hardware/navigation-commissioning.md`: a closed movement path during an active mission is a pause.
- `docs/decisions/2026-08-31-semantic-perception-and-grasping.md`: after a failed or uncertain grasp the robot observes again and retries by itself within fixed limits.
- `CURRENT_STATE.md` and the draft software concept.

Still to be written: the bounds of each healing step, the clear time before motion continues, and the tests that prove both. They belong to the manual-drive, navigation, and manipulation contracts.

## Validation

None. The healing behavior must be proven in simulation with injected disturbances before any real motion, as Amadeus did with its robustness scenarios.

## Risks and Rollback

Risks: the robot starts moving again without a person confirming it, for example when someone steps out of its way; an unbounded or badly bounded healing loop; healing that hides a real defect.

These risks are limited by the clear time, by the bounds on every healing step, by the two latching causes, and by logging every healing event.

Rollback: revert this decision and the contract changes listed above. The stricter earlier rule then applies again.
