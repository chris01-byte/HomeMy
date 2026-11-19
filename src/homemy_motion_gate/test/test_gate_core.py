"""Tests of the motion gate decision logic (no ROS)."""

import math

import pytest

from homemy_motion_gate.gate_core import (
    MODE_CONFLICT,
    MODE_MAPPING,
    MODE_MISSION,
    MODE_OFF,
    GateConfig,
    GateInputs,
    ModeLimits,
    MotionGate,
    Stamped,
)

NOW = 100.0
CONFIG = GateConfig(
    mapping_limits=ModeLimits(0.20, 0.70),
    mission_limits=ModeLimits(0.25, 0.60),
    clear_time_s=0.5,
)


def clear(v, w):
    return True, "clear"


def blocked(v, w):
    return False, "obstacle"


def mapping_inputs(command=(0.12, 0.0), now=NOW):
    return GateInputs(
        mapping_active=Stamped(True, now - 0.2),
        mission_drive_active=Stamped(False, now - 0.2),
        lifecycle_state=Stamped("READY", now - 0.5),
        estop_pressed=Stamped(False, now - 0.1),
        teleop_command=Stamped(command, now - 0.05),
        scan_received_at=now - 0.1,
    )


def mission_inputs(command=(0.2, 0.1), now=NOW):
    return GateInputs(
        mapping_active=Stamped(False, now - 0.2),
        mission_drive_active=Stamped(True, now - 0.2),
        lifecycle_state=Stamped("OPERATING", now - 0.5),
        estop_pressed=Stamped(False, now - 0.1),
        localization_ready=Stamped(True, now - 0.2),
        nav_command=Stamped(command, now - 0.05),
        scan_received_at=now - 0.1,
    )


def step(inputs, protection=clear, gate=None, now=NOW):
    gate = gate or MotionGate(CONFIG)
    return gate.step(inputs, now, protection)


def test_mapping_mode_passes_controller_commands():
    decision = step(mapping_inputs())
    assert decision.mode == MODE_MAPPING
    assert decision.open
    assert decision.command == (0.12, 0.0)


def test_mission_mode_passes_navigation_commands():
    decision = step(mission_inputs())
    assert decision.mode == MODE_MISSION
    assert decision.open
    assert decision.command == (0.2, 0.1)


def test_nothing_known_means_closed():
    decision = step(GateInputs())
    assert not decision.open
    assert decision.command == (0.0, 0.0)
    assert "mode_off" in decision.reasons
    assert "lifecycle_missing" in decision.reasons
    assert "estop_missing" in decision.reasons
    assert "scan_stale" in decision.reasons


def test_both_modes_active_is_a_conflict():
    inputs = mapping_inputs()
    inputs.mission_drive_active = Stamped(True, NOW - 0.1)
    decision = step(inputs)
    assert decision.mode == MODE_CONFLICT
    assert not decision.open


def test_stale_mode_signal_closes():
    inputs = mapping_inputs()
    inputs.mapping_active = Stamped(True, NOW - 5.0)
    decision = step(inputs)
    assert decision.mode == MODE_OFF
    assert not decision.open


def test_mapping_ignores_navigation_commands():
    inputs = mapping_inputs()
    inputs.teleop_command = None
    inputs.nav_command = Stamped((0.2, 0.0), NOW - 0.01)
    decision = step(inputs)
    assert not decision.open
    assert "command_stale" in decision.reasons


def test_mission_ignores_controller_commands():
    inputs = mission_inputs()
    inputs.nav_command = None
    inputs.teleop_command = Stamped((0.2, 0.0), NOW - 0.01)
    decision = step(inputs)
    assert not decision.open
    assert "command_stale" in decision.reasons


@pytest.mark.parametrize("state", ["BOOTING", "SELF_TEST", "FAULT", "SHUTTING_DOWN", "OFF", "nonsense"])
def test_lifecycle_states_that_close(state):
    inputs = mapping_inputs()
    inputs.lifecycle_state = Stamped(state, NOW - 0.1)
    decision = step(inputs)
    assert not decision.open
    assert "lifecycle_not_ready" in decision.reasons


@pytest.mark.parametrize("state", ["READY", "READY_LIMITED", "OPERATING"])
def test_lifecycle_states_that_allow(state):
    inputs = mapping_inputs()
    inputs.lifecycle_state = Stamped(state, NOW - 0.1)
    assert step(inputs).open


def test_stale_lifecycle_closes():
    inputs = mapping_inputs()
    inputs.lifecycle_state = Stamped("READY", NOW - 3.5)
    assert "lifecycle_stale" in step(inputs).reasons


def test_emergency_stop_pressed_missing_or_stale_closes():
    for estop, reason in (
        (Stamped(True, NOW - 0.1), "estop_pressed"),
        (None, "estop_missing"),
        (Stamped(False, NOW - 2.0), "estop_stale"),
    ):
        inputs = mapping_inputs()
        inputs.estop_pressed = estop
        decision = step(inputs)
        assert not decision.open
        assert reason in decision.reasons


def test_released_direction_pad_stops():
    # Released: teleop sends zero, and the gate passes the zero.
    decision = step(mapping_inputs((0.0, 0.0)))
    assert decision.open
    assert decision.command == (0.0, 0.0)


def test_silent_controller_stops():
    # No controller messages at all: the last command goes stale.
    inputs = mapping_inputs((0.2, 0.0))
    inputs.teleop_command = Stamped((0.2, 0.0), NOW - 0.3)
    decision = step(inputs)
    assert not decision.open
    assert decision.command == (0.0, 0.0)
    assert "command_stale" in decision.reasons


def test_stale_command_closes():
    inputs = mapping_inputs()
    inputs.teleop_command = Stamped((0.1, 0.0), NOW - 0.3)
    assert "command_stale" in step(inputs).reasons


def test_mission_needs_localization():
    inputs = mission_inputs()
    inputs.localization_ready = Stamped(False, NOW - 0.1)
    assert "localization_not_ready" in step(inputs).reasons
    inputs.localization_ready = None
    assert "localization_not_ready" in step(inputs).reasons


def test_mapping_does_not_need_localization():
    inputs = mapping_inputs()
    inputs.localization_ready = None
    assert step(inputs).open


def test_stale_scan_closes():
    inputs = mapping_inputs()
    inputs.scan_received_at = NOW - 0.5
    assert "scan_stale" in step(inputs).reasons


def test_commands_are_clamped_to_the_mode_limits():
    decision = step(mapping_inputs((1.0, -3.0)))
    assert decision.command == (0.20, -0.70)
    decision = step(mission_inputs((-1.0, 3.0)))
    assert decision.command == (-0.25, 0.60)


@pytest.mark.parametrize("bad", [(math.nan, 0.0), (0.0, math.inf)])
def test_non_finite_commands_close(bad):
    decision = step(mapping_inputs(bad))
    assert not decision.open
    assert "command_invalid" in decision.reasons


def test_protection_sees_the_clamped_command():
    seen = []

    def protection(v, w):
        seen.append((v, w))
        return True, "clear"

    step(mapping_inputs((5.0, 0.0)), protection=protection)
    assert seen == [(0.20, 0.0)]


def test_obstacle_blocks_and_heals_after_the_clear_time():
    gate = MotionGate(CONFIG)
    inputs = mapping_inputs((0.12, 0.0), now=NOW)
    assert step(inputs, blocked, gate, NOW).reasons == ("obstacle",)

    later = NOW + 0.2
    inputs = mapping_inputs((0.12, 0.0), now=later)
    decision = step(inputs, clear, gate, later)
    assert not decision.open
    assert decision.reasons == ("obstacle_clear_wait",)

    healed = NOW + 0.6
    inputs = mapping_inputs((0.12, 0.0), now=healed)
    decision = step(inputs, clear, gate, healed)
    assert decision.open
    assert decision.command == (0.12, 0.0)


def test_standstill_during_clear_time_is_open_with_zero():
    gate = MotionGate(CONFIG)
    step(mapping_inputs((0.12, 0.0)), blocked, gate, NOW)
    later = NOW + 0.1
    decision = step(mapping_inputs((0.0, 0.0), now=later), clear, gate, later)
    assert decision.open
    assert decision.command == (0.0, 0.0)


def test_closed_gate_never_latches():
    gate = MotionGate(CONFIG)
    inputs = mapping_inputs()
    inputs.lifecycle_state = Stamped("FAULT", NOW - 0.1)
    assert not step(inputs, clear, gate, NOW).open
    later = NOW + 1.0
    assert step(mapping_inputs(now=later), clear, gate, later).open


def test_invalid_configuration_is_refused():
    with pytest.raises(ValueError):
        GateConfig(mapping_limits=ModeLimits(0.2, 0.7), mission_limits=ModeLimits(0.2, 0.7), command_timeout_s=0.0)
    with pytest.raises(ValueError):
        ModeLimits(-0.1, 0.5)
