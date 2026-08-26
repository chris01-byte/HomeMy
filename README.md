# HomeMy

HomeMy is a ROS 2 platform for a household robot. It is initialized as a safe, modular foundation: simulation first, explicit contracts, and controlled transfers from roboter_ws.

## Start Here

1. Read [AGENTS.md](AGENTS.md) for safety and work rules.
2. Read [CURRENT_STATE.md](CURRENT_STATE.md) for the active project state.
3. Choose one focused context area in [context/index.json](context/index.json).
4. In a local checkout, run `python tools/context/brief.py --area architecture` or another matching area.

## Structure

| Path | Purpose |
| --- | --- |
| [src/](src/README.md) | HomeMy-owned ROS 2 packages |
| [contracts/](contracts/README.md) | Stable ROS, hardware, API, and data boundaries |
| [simulation/](simulation/README.md) | Synthetic fixtures and deterministic scenarios |
| [integration/roboter_ws/](integration/roboter_ws/TRANSFER_MANIFEST.md) | Controlled transfers from roboter_ws |
| [docs/](docs/README.md) | Decisions, transfers, runbooks, and archived evidence |
| [context/](context/index.json) | Token-bounded context routing for agents |
| [tools/context/](tools/context/brief.py) | Context packet generator and validator |

## Transfer Policy

HomeMy does not start as a copy of roboter_ws. Every capability transfer names an immutable source commit, target contract, dependencies, validation, risk, and rollback path before code is ported.

## Safety and Privacy

The default is simulation or motorless validation. No actor is enabled without explicit human approval. Secrets, home maps, camera data, ROS bags, and deployment-specific configuration stay outside version control.
