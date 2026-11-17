# HomeMy Uses the OAK-D-S2 Instead of the OAK 4D

Status: accepted by the project owner. No HomeMy camera has been mounted or tested.
Date: 2026-11-17.

## Context

The HomeMy documents planned an OAK 4D as the camera on top of the robot: complementary 3D depth for obstacle protection, and coarse object detection for grasping. The owner reports that the OAK 4D is not available.

## Decision

HomeMy uses the Luxonis OAK-D-S2, the same camera model as Amadeus.

Unchanged:

- its roles: complementary 3D depth for obstacle protection, and finding objects for grasping;
- the wrist camera, an Orbbec Gemini 305, which does the fine localization during the grasp;
- object detection on the external AI computer first (software concept, decision E5).

Still open, to be decided before stage S7 of the software concept: whether the camera is mounted fixed or tiltable.

## Consequences

- **Amadeus experience applies directly.** Amadeus ran this model in long tests and recorded fixes: the image size must be set through the ISP scale, rectification runs outside the DepthAI container, on-device RGB-depth synchronization stays off, raw images never go over WLAN, and silent stream losses need watchdogs.
- **Unit values still do not carry over.** Calibration, mounting position and tilt, depth thresholds, and device aliases of the Amadeus camera remain HomeMy measurements, as the contracts already require.
- **Autofocus.** If the unit has the autofocus colour camera, its focus is fixed at the lens position stored in the factory calibration, so that colour image and depth stay aligned. Depth comes from the fixed-focus stereo pair and is not affected.
- **On-camera compute.** The OAK 4D would have offered considerably more compute on the camera. With the OAK-D-S2, detection stays on the external AI computer, as already decided.

## Evidence

- Owner statement of 2026-11-17: the OAK 4D is not available.
- Amadeus OAK-D-S2 records in roboter_ws `docs/PROJECT_MEMORY.md` (entries of 2026-08-25 to 2026-08-28): 33 min 49 s continuous camera run after the fixes; a cup located relative to the robot with at most 7.2 mm spread over eleven measurements at standstill. Accuracy against a measured reference was never determined.
- Luxonis documentation: the autofocus and fixed-focus variants differ only in the colour camera; the alignment example fixes the colour focus at the calibrated lens position.

## Impact

Documents that named the OAK 4D now name the OAK-D-S2: `CURRENT_STATE.md`, `contracts/README.md`, `contracts/hardware/obstacle-protection.md`, `contracts/hardware/navigation-commissioning.md`, `integration/roboter_ws/TRANSFER_MANIFEST.md`, the semantic perception decision, the software concept, and the context index. The dated transfer record of 2026-08-28 keeps its text and carries an update note.

## Validation

None. Commissioning stages O0 to O5 of the obstacle-protection contract apply unchanged.

## Risks and Rollback

Risks: the narrower compute budget on the camera, and possible blur of an autofocus colour camera if its focus is not fixed.

Rollback: if an OAK 4D or another camera becomes available, record a new decision. The contracts describe the camera role, so only names and commissioning values change.
