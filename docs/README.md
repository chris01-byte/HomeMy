# Documentation Map

## Active Context

- ../CURRENT_STATE.md: current project state and next safe step.
- ../AGENTS.md: work, safety, and context rules.
- ../context/index.json: task-to-context routing.

## Focused Records

- architecture/: the software concept, the German reference for what the robot software is to do and in which order it is built. A draft until the owner accepts it.
- decisions/: small evidence-backed design decisions with a rollback path.
- transfers/roboter_ws/: detailed records for individual source transfers.
- runbooks/: repeatable operational procedures once a component exists.
- archive/: superseded or long-form evidence, never a default reading target.

## Documentation Rule

Put current facts in CURRENT_STATE.md, a durable choice in decisions/, and a source migration in transfers/. Link instead of duplicating. Keep each active document short enough to be selected by the context router.
