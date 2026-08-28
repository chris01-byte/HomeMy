# HomeMy

HomeMy is a ROS 2 platform for a household robot. It is initialized as a safe, modular foundation: simulation first, explicit contracts, and controlled transfers from roboter_ws.

## Start Here

1. Read [AGENTS.md](AGENTS.md) for safety and work rules.
2. Read [CURRENT_STATE.md](CURRENT_STATE.md) for the active project state.
3. Choose one focused context area in [context/index.json](context/index.json).
4. In a local checkout, run python tools/context/brief.py --area architecture or another matching area.

## Appliance Startup

HomeMy will use one on-board Linux computer for customer operation. Developer mode retains the normal Ubuntu login and desktop. Customer mode will start the HomeMy systemd target automatically, with no customer Ubuntu login, terminal, or manual ROS command.

The customer-facing display reports boot, self-test, ready, limited-ready, or fault states with a stable error code and clear next action. The external AI server is optional for local boot: an AI outage produces limited capability, not an unsafe or blocked local startup. Power-on and ready state never authorize motion by themselves.

The current decision and contracts are [the appliance architecture decision](docs/decisions/2026-08-28-appliance-startup.md), [the system lifecycle](contracts/ros/system-lifecycle.md), [customer power-on](contracts/hardware/customer-power-on.md), and [external AI health](contracts/api/ai-server-health.md).

## Structure

| Path | Purpose |
| --- | --- |
| [src/](src/README.md) | HomeMy-owned ROS 2 packages |
| [contracts/](contracts/README.md) | Stable ROS, hardware, API, and data boundaries |
| [simulation/](simulation/README.md) | Synthetic fixtures and deterministic scenarios |
| [deployment/systemd/](deployment/systemd/README.md) | Versioned systemd target and unit templates, not yet enabled |
| [integration/roboter_ws/](integration/roboter_ws/TRANSFER_MANIFEST.md) | Controlled transfers from roboter_ws |
| [docs/](docs/README.md) | Decisions, transfers, runbooks, and archived evidence |
| [context/](context/index.json) | Token-bounded context routing for agents |
| [tools/context/](tools/context/brief.py) | Context packet generator and validator |

## Transfer Policy

HomeMy does not start as a copy of roboter_ws. Every capability transfer names an immutable source commit, target contract, dependencies, validation, risk, and rollback path before code is ported.

## Safety and Privacy

The default is simulation or motorless validation. No actor is enabled without explicit human approval. Secrets, home maps, camera data, ROS bags, and deployment-specific configuration stay outside version control.
