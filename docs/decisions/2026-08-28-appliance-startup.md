# Appliance Startup Uses On-Board Linux and systemd

Status: accepted.
Date: 2026-08-28.

## Context

HomeMy must behave as a customer appliance. A customer must be able to use one physical power control without starting a Jetson, Windows host, Ubuntu desktop, terminal, or ROS process. Development still requires the normal Ubuntu desktop, login, VS Code, and diagnostic tools. An external AI server remains in use for now.

## Decision

HomeMy uses an on-board Linux computer as its only customer-required compute host. Its product services are started and supervised by systemd, not by an interactive desktop session.

Two deliberate boot modes exist:

- Developer mode uses graphical.target and retains the normal Ubuntu login and desktop.
- Customer mode uses homemy.target, starts HomeMy automatically, and does not show a customer Ubuntu login screen.

Customer mode enters BOOTING, SELF_TEST, READY, READY_LIMITED, or FAULT. A HomeMy status display, not systemd itself, presents the state, stable error code, plain-language explanation, and next action. Startup and restart keep the motion gate closed; ready state alone never authorizes motion.

The external AI server is checked with a bounded application-level health request. If local mandatory checks pass but the AI server is unavailable, HomeMy enters READY_LIMITED with E-AI-001. The Linux boot and local robot stack remain available; only explicitly AI-dependent capabilities are unavailable.

## Not Selected

- A Windows computer or manually started external computer in the customer startup path.
- A customer entering an Ubuntu password to run robot software.
- Desktop autologin as the supervisor for safety-relevant services.
- Treating an unavailable AI server as a local safety fault.
- Automatic actuator activation after power-on, restart, or successful health checks.

## Evidence

This decision follows the explicit customer requirement for one-button use and the developer requirement to keep a normal graphical Ubuntu environment. systemd starts before desktop login and can operate services without an interactive session, so it supports both needs through separate targets.

## Impact

Future packages include a boot manager, status display, and bring-up composition. The required contracts are customer-power-on, system-lifecycle, and ai-server-health. Simulation must cover cold boot, local fault, external AI outage, recovery, and controlled shutdown before hardware integration.

## Validation

Documentation and contract review only. No systemd units, runtime packages, display hardware, or power hardware have been implemented or tested.

## Risks and Rollback

Physical power control, independent safety hardware, customer display, disk encryption, and the final AI health protocol remain open designs. Until customer mode is proven, developer mode remains the default. Disabling homemy.target must restore graphical.target without enabling actuators or bypassing independent safety hardware.
