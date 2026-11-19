"""Tests for the ROS-free mapping-mode core (contracts/api/app-bridge.md)."""

import json
import math

import pytest

from homemy_mapping_mode.mapping_mode_core import (
    BLOCK_FAULT,
    BLOCK_NOT_READY,
    BLOCK_SHUTTING_DOWN,
    END_APP_DISABLE,
    END_APP_STOP,
    END_FAULT,
    END_INACTIVITY,
    END_SHUTDOWN,
    Command,
    CommandError,
    ControllerTracker,
    MappingMode,
    block_reason_for_lifecycle,
    build_status,
    encode_status,
    parse_command,
)

ENVELOPE_KEYS = {"schema_version", "event", "ok", "request_id", "message", "mapping_mode", "time"}
MODE_KEYS = {
    "state",
    "controller_connected",
    "auto_end_timeout_s",
    "auto_end_remaining_s",
    "last_end_reason",
    "enable_block_reason",
}


def app_accepts(status: dict) -> bool:
    """Mirror of MappingModeStatus.isValid in the iOS app (RobotModels.swift)."""

    mode = status["mapping_mode"]
    if status["schema_version"] != 1:
        return False
    if status["event"] not in {"status", "enable_result", "disable_result", "stop_result"}:
        return False
    if not status["message"] or not math.isfinite(status["time"]):
        return False
    if mode["state"] not in {"off", "active"}:
        return False
    timeout = mode["auto_end_timeout_s"]
    if not (math.isfinite(timeout) and timeout > 0):
        return False
    remaining = mode["auto_end_remaining_s"]
    if remaining is not None:
        if mode["state"] != "active" or not (0 <= remaining <= timeout):
            return False
    for key in ("last_end_reason", "enable_block_reason"):
        if mode[key] is not None and mode[key] == "":
            return False
    return isinstance(mode["controller_connected"], bool)


def status(mode, now=0.0, connected=True, block=None, **kwargs):
    result = build_status(
        mode,
        now=now,
        wall_time=1_731_790_000.0,
        controller_connected=connected,
        block_reason=block,
        **kwargs,
    )
    # Round-trip through the wire format to catch non-JSON values.
    return json.loads(encode_status(result))


def cmd(kind, request_id="ios-1"):
    return Command(kind=kind, request_id=request_id)


# ---------------------------------------------------------------- commands


@pytest.mark.parametrize("kind", ["enable", "disable", "stop"])
def test_parses_every_command(kind):
    command = parse_command(json.dumps({"command": kind, "request_id": "ios-mode-1"}))
    assert command == Command(kind=kind, request_id="ios-mode-1")


@pytest.mark.parametrize(
    "text, keeps_id",
    [
        ("{kaputt", False),
        ("[]", False),
        ('"enable"', False),
        ('{"command": "drive", "request_id": "ios-1"}', True),
        ('{"command": "enable"}', False),
        ('{"command": "enable", "request_id": "../unsafe"}', False),
        ('{"command": "enable", "request_id": "ios-1", "speed": 1}', True),
        ('{"command": "enable", "request_id": "' + "a" * 65 + '"}', False),
        ('{"command": "enable", "request_id": 7}', False),
    ],
)
def test_refuses_malformed_commands(text, keeps_id):
    with pytest.raises(CommandError) as error:
        parse_command(text)
    assert (error.value.request_id == "ios-1") is keeps_id


def test_refuses_oversized_command_before_parsing():
    with pytest.raises(CommandError):
        parse_command('{"command": "stop", "request_id": "a", "x": "' + "y" * 5000 + '"}')


def test_refuses_deeply_nested_json():
    with pytest.raises(CommandError):
        parse_command("[" * 2000 + "]" * 2000)


# ---------------------------------------------------------------- lifecycle


@pytest.mark.parametrize(
    "state, reason",
    [
        ("READY", None),
        ("READY_LIMITED", None),
        ("OPERATING", BLOCK_NOT_READY),
        ("BOOTING", BLOCK_NOT_READY),
        ("SELF_TEST", BLOCK_NOT_READY),
        (None, BLOCK_NOT_READY),
        ("UNKNOWN", BLOCK_NOT_READY),
        ("FAULT", BLOCK_FAULT),
        ("SHUTTING_DOWN", BLOCK_SHUTTING_DOWN),
    ],
)
def test_enable_is_allowed_only_in_ready_states(state, reason):
    assert block_reason_for_lifecycle(state) == reason


# ---------------------------------------------------------------- state machine


def test_starts_off_with_complete_status():
    mode = MappingMode(300)
    result = status(mode)
    assert set(result) == ENVELOPE_KEYS
    assert set(result["mapping_mode"]) == MODE_KEYS
    assert result["mapping_mode"]["state"] == "off"
    assert result["mapping_mode"]["auto_end_remaining_s"] is None
    assert result["mapping_mode"]["last_end_reason"] is None
    assert app_accepts(result)


def test_enable_then_disable():
    mode = MappingMode(300)
    ok, _ = mode.handle(cmd("enable"), now=10.0, block_reason=None)
    assert ok and mode.active
    result = status(mode, now=10.0, event="enable_result", request_id="ios-1")
    assert result["mapping_mode"]["auto_end_remaining_s"] == 300
    assert result["mapping_mode"]["enable_block_reason"] is None
    assert app_accepts(result)

    ok, _ = mode.handle(cmd("disable"), now=20.0, block_reason=None)
    assert ok and not mode.active
    assert mode.last_end_reason == END_APP_DISABLE
    assert app_accepts(status(mode, now=20.0, event="disable_result"))


def test_enable_is_refused_while_blocked_and_state_stays_off():
    mode = MappingMode(300)
    ok, message = mode.handle(cmd("enable"), now=0.0, block_reason=BLOCK_NOT_READY)
    assert not ok and not mode.active
    assert BLOCK_NOT_READY in message
    result = status(mode, block=BLOCK_NOT_READY, event="enable_result", ok=ok, message=message)
    assert result["mapping_mode"]["enable_block_reason"] == BLOCK_NOT_READY
    assert app_accepts(result)


def test_repeated_enable_and_disable_are_harmless():
    mode = MappingMode(300)
    assert mode.handle(cmd("disable"), 0.0, None) == (True, "Kartiermodus ist bereits aus.")
    mode.handle(cmd("enable"), 1.0, None)
    ok, _ = mode.handle(cmd("enable"), 2.0, BLOCK_FAULT)
    assert ok and mode.active


def test_stop_is_accepted_in_every_state_and_idempotent():
    mode = MappingMode(300)
    assert mode.handle(cmd("stop"), 0.0, BLOCK_FAULT)[0]
    assert mode.last_end_reason is None

    mode.handle(cmd("enable"), 1.0, None)
    assert mode.handle(cmd("stop"), 2.0, BLOCK_FAULT)[0]
    assert not mode.active and mode.last_end_reason == END_APP_STOP

    assert mode.handle(cmd("stop"), 3.0, None)[0]
    assert mode.last_end_reason == END_APP_STOP


def test_ends_by_itself_without_controller_input():
    mode = MappingMode(20)
    mode.handle(cmd("enable"), 100.0, None)
    assert mode.tick(110.0, "READY") is None
    assert mode.remaining(110.0) == pytest.approx(10.0)

    mode.note_input(115.0)
    assert mode.tick(130.0, "READY") is None
    assert mode.remaining(130.0) == pytest.approx(5.0)

    assert mode.tick(135.0, "READY") == END_INACTIVITY
    assert not mode.active
    result = status(mode, now=135.0)
    assert result["mapping_mode"]["last_end_reason"] == END_INACTIVITY
    assert result["mapping_mode"]["auto_end_remaining_s"] is None
    assert app_accepts(result)


def test_input_while_off_does_not_start_anything():
    mode = MappingMode(20)
    mode.note_input(5.0)
    assert not mode.active
    assert mode.tick(100.0, "READY") is None


@pytest.mark.parametrize("state, reason", [("FAULT", END_FAULT), ("SHUTTING_DOWN", END_SHUTDOWN)])
def test_fault_or_shutdown_ends_the_mode_at_once(state, reason):
    mode = MappingMode(300)
    mode.handle(cmd("enable"), 0.0, None)
    assert mode.tick(0.1, state) == reason
    assert not mode.active and mode.last_end_reason == reason


@pytest.mark.parametrize("state", [None, "OPERATING", "READY_LIMITED", "SELF_TEST"])
def test_other_lifecycle_states_do_not_end_an_active_mode(state):
    mode = MappingMode(300)
    mode.handle(cmd("enable"), 0.0, None)
    assert mode.tick(1.0, state) is None
    assert mode.active


def test_remaining_time_stays_within_the_timeout_even_if_the_clock_jumps_back():
    mode = MappingMode(300)
    mode.handle(cmd("enable"), 100.0, None)
    assert mode.remaining(50.0) == 300
    assert app_accepts(status(mode, now=50.0))


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_timeout_must_be_positive_and_finite(value):
    with pytest.raises(ValueError):
        MappingMode(value)


# ---------------------------------------------------------------- controller


def test_controller_connection_follows_the_radio_link():
    tracker = ControllerTracker(timeout_s=0.5, deadzone=0.2)
    assert not tracker.connected(0.0)
    tracker.update_link(True, now=10.0)
    assert tracker.connected(10.4)
    assert not tracker.connected(10.6)
    tracker.update_link(True, now=11.0)
    tracker.update_link(False, now=11.1)
    assert not tracker.connected(11.1)


def test_repeated_joy_messages_do_not_mean_connected():
    tracker = ControllerTracker(timeout_s=0.5, deadzone=0.2)
    tracker.update([0.0] * 8, [0] * 13, now=10.0)
    assert not tracker.connected(10.1)
    assert tracker.last_input_at is None


def test_controller_input_is_any_axis_beyond_deadzone_or_any_button():
    tracker = ControllerTracker(timeout_s=0.5, deadzone=0.2)
    assert not tracker.update([0.15, -0.19, 0.0], [0, 0], now=1.0)
    assert tracker.update([0.0, 0.0, 1.0], [0, 0], now=2.0)
    assert tracker.update([0.0], [0, 1], now=3.0)
    assert tracker.last_input_at == 3.0
    assert not tracker.update([float("nan")], [0], now=4.0)


@pytest.mark.parametrize("timeout, deadzone", [(0, 0.2), (0.5, 1.0), (0.5, -0.1), (float("nan"), 0.2)])
def test_controller_settings_are_checked(timeout, deadzone):
    with pytest.raises(ValueError):
        ControllerTracker(timeout, deadzone)


def test_status_never_contains_nan_or_infinity():
    mode = MappingMode(300)
    with pytest.raises(ValueError):
        encode_status(build_status(mode, now=0.0, wall_time=float("nan"),
                                   controller_connected=True, block_reason=None))
