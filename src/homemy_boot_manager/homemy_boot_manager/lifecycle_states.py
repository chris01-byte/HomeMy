"""The lifecycle states of contracts/ros/system-lifecycle.md. No ROS."""

from __future__ import annotations

LIFECYCLE_STATES = (
    "OFF",
    "BOOTING",
    "SELF_TEST",
    "READY",
    "READY_LIMITED",
    "OPERATING",
    "FAULT",
    "SHUTTING_DOWN",
)

# What the bridge may be set to by hand. OFF and BOOTING describe a robot
# whose software is not running, so the bridge cannot report them.
BRIDGE_STATES = ("SELF_TEST", "READY", "READY_LIMITED", "OPERATING", "FAULT", "SHUTTING_DOWN")


def normalise_state(value: object) -> str:
    """Upper-case state name, or ValueError for anything the bridge may not report."""

    if not isinstance(value, str):
        raise ValueError("the lifecycle state must be text")
    state = value.strip().upper()
    if state not in BRIDGE_STATES:
        raise ValueError(
            f"unknown lifecycle state {value!r}; allowed: {', '.join(BRIDGE_STATES)}"
        )
    return state
