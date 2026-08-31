# Semantic Perception and Grasping Pipeline

Status: proposed for HomeMy; no perception, manipulation, or source runtime code has been copied.

## Context

HomeMy needs a future perception path that can find a requested household object, derive usable local 3D geometry, propose a grasp, and reject unsafe or uncertain execution. The path must remain compatible with the existing rule that local obstacle protection, the movement gate, and the independent emergency stop are separate from semantic perception.

A fixed serial chain of YOLO, Grounding DINO, SAM2, depth, and a grasp model would add latency and compound uncertainty. The components have different purposes and should be selected only when their result is needed.

## Decision

HomeMy will use an event-driven, locally validated perception-and-grasping pipeline:

1. Acquire fresh, time-bounded local RGB-D data and a valid camera-to-base_link transform.
2. Select an object detector for the request:
   - use YOLO for known, trained object classes and efficient scene observation;
   - use Grounding DINO for open-vocabulary or language-described objects;
   - use both only when cross-checking materially improves confidence for a specific manipulation request.
3. Pass the chosen detection prompt or bounding box to SAM2 when a precise object mask or temporal tracking is required.
4. Combine the accepted mask with local OAK depth to derive a filtered object cloud, pose estimate, visible support surface, and uncertainty bounds.
5. Give the geometry to the grasp model. The model proposes ranked grasp candidates; it does not authorize motion.
6. Validate the selected candidate deterministically before execution: fresh data, valid transform, reachable pose, collision-free approach and retreat, workspace limits, object confidence, protected environment, and explicit movement authorization.

The pipeline is conditional, not a mandatory per-frame sequence. Detection runs on a request, scene change, tracking loss, or confidence loss. SAM2 tracks an already selected candidate where useful instead of repeatedly redetecting it. Grounding DINO is not a required precondition for a known YOLO class.

## Component Roles

| Component | Intended role | Not an authority for |
| --- | --- | --- |
| YOLO | Fast closed-set object candidates | Motion authorization, obstacle safety, or final grasp approval |
| Grounding DINO | Open-vocabulary candidates from a text description | Continuous mandatory detection or safety response |
| SAM2 | Object mask refinement and tracking from a selected candidate | Object identity by itself or depth validity |
| Local OAK depth | Local 3D geometry, pose support, visible free space, and data-age checks | Semantic object identity or independent emergency stop |
| Grasp model | Ranked grasp-pose proposals from valid object geometry | Trajectory safety, actuator enablement, or automatic recovery |
| Execution validator | Deterministic rejection of invalid, stale, unreachable, or colliding proposals | Semantic recognition or remote inference |

## Safety and Availability Boundary

Semantic perception and manipulation are not the primary obstacle-protection path. STL-27L floor and near-field coverage, the local OAK 4D protection role, the movement gate, and the independent emergency stop remain governed by the obstacle-protection and navigation contracts.

A semantic result must never delay, suppress, or veto an immediate local protection response. Remote AI, network availability, image relays, LLM planning, and off-board inference are not required for an immediate stop or for the basic validity checks before a local grasp.

A detected label such as "cup" does not permit an arm or drivebase move. A valid depth image does not permit a move either. Each movement remains blocked until the independent execution validator and movement gate both accept the request.

## Minimum Validity Checks

Before a grasp candidate can be considered, HomeMy must reject it when any applicable condition is false:

- RGB and depth data are fresh and sufficiently synchronized for the requested operation.
- Camera calibration and camera-to-base_link transform are valid and current.
- The object mask has sufficient support in depth and does not merge target and background.
- The visible object geometry, grasp point, approach vector, and support surface are plausible.
- The target is inside the measured working envelope and outside excluded zones.
- The proposed approach, grasp, lift, retreat, and any base movement are collision-checked against the current local geometry.
- The active OAK/STL protection inputs, movement gate, and required hardware safety path are healthy.
- An explicit operator or higher-level policy has authorized the bounded action.

Failure, ambiguity, stale input, tracking loss, insufficient depth, or disagreement between required checks means no grasp execution. Recovery starts with renewed observation; it never resumes motion automatically.

## Delivery Order

1. P0: build synthetic RGB-D fixtures and verify timestamps, transform rejection, mask-to-depth extraction, and zero-motion behavior.
2. P1: commission local OAK RGB-D frames and measure camera mount, latency, depth limits, and calibration without motion.
3. P2: validate SAM2 mask-to-depth geometry on static household-object fixtures; record failure cases such as reflective, transparent, thin, and occluded objects.
4. P3: add simple deterministic grasp heuristics for a small set of robust objects and validate collision rejection in simulation or motorless mode.
5. P4: add a grasp model as a candidate generator and compare its output with the deterministic validator on recorded synthetic or approved test fixtures.
6. P5: add YOLO for selected known classes. Add Grounding DINO only for explicit open-vocabulary or language-driven tasks.
7. P6: after separate human approval, perform low-speed supervised physical tests with bounded travel, fault injection, and a proven stop path.

## Evidence

This is an architecture decision based on the distinct responsibilities and failure modes of the proposed models. No HomeMy inference benchmark, calibration result, model evaluation, physical manipulation test, or source-code transfer has been performed yet.

## Impact

This decision affects future local OAK bring-up, semantic perception, manipulation, navigation integration, and the eventual movement-gate interface. It does not select a specific YOLO version, Grounding DINO checkpoint, SAM2 checkpoint, grasp model, accelerator, ROS message contract, or external AI service.

The external AI server, network transport, relay, inference backend, LLM planner, and deployment remain explicitly deferred and must not be modified by work under this decision.

## Validation

Required evidence before any physical grasping includes synthetic unit tests, transform and stale-data fault injection, depth-quality characterization, target-mask verification, collision-check tests, workspace-limit tests, stop-path verification, and bounded supervised physical trials. Results must distinguish simulation, motorless validation, and approved physical motion.

## Risks and Rollback

Risks include detector confusion, language ambiguity, segmentation leakage, depth holes, reflective or transparent surfaces, calibration drift, motion latency, grasp-model hallucinated affordances, and false confidence caused by correlated model errors.

Rollback is to remove the semantic-grasp service from customer composition, keep the movement gate closed for manipulation, and retain local obstacle protection. Do not substitute cached RGB-D data, remote AI availability, source calibration, or source grasp parameters for missing HomeMy validation.
