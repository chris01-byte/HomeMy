"""Tests of the mission logic (no ROS)."""

import json

import pytest

from homemy_mission.mission_core import (
    STATE_CANCELED,
    STATE_FAILED,
    STATE_RUNNING,
    STATE_SUCCEEDED,
    CommandError,
    Mission,
    MissionPolicy,
    Preconditions,
    parse_command,
    start_block_reason,
)

FP = "a" * 64


def text(**payload):
    return json.dumps(payload)


def test_parse_go_to_room_by_id_or_name():
    command = parse_command(text(command="go_to_room", request_id="ios-1", room_id="room-1"))
    assert (command.command, command.room_id, command.room_name) == ("go_to_room", "room-1", None)
    command = parse_command(text(command="go_to_room", request_id="ios-2", room="Küche"))
    assert command.room_name == "Küche"


def test_parse_cancel():
    assert parse_command(text(command="cancel", request_id="ios-3")).command == "cancel"


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "[]",
        text(command="go_to_room", room_id="r"),
        text(command="go_to_room", request_id="bad id!", room_id="r"),
        text(command="go_to_room", request_id="ios-1"),
        text(command="go_to_room", request_id="ios-1", room_id=""),
        text(command="go_to_room", request_id="ios-1", room_id=3),
        text(command="go_to_room", request_id="ios-1", room_id="r", speed=2),
        text(command="cancel", request_id="ios-1", room_id="r"),
        text(command="explore", request_id="ios-1"),
        "x" * 5000,
    ],
)
def test_invalid_commands_are_refused(payload):
    with pytest.raises(CommandError):
        parse_command(payload)


def test_refusal_keeps_the_request_id_when_known():
    with pytest.raises(CommandError) as error:
        parse_command(text(command="explore", request_id="ios-9"))
    assert error.value.request_id == "ios-9"


def ready(**changes):
    values = dict(mapping_active=False, lifecycle_ready=True, localization_ready=True,
                  localization_map_fingerprint=FP, rooms_map_fingerprint=FP, navigation_available=True)
    values.update(changes)
    return Preconditions(**values)


def test_start_needs_every_precondition():
    assert start_block_reason(False, ready()) is None
    assert start_block_reason(True, ready()) == "busy"
    assert start_block_reason(False, ready(mapping_active=True)) == "mapping_active"
    assert start_block_reason(False, ready(lifecycle_ready=False)) == "not_ready"
    assert start_block_reason(False, ready(localization_map_fingerprint=None)) == "no_map"
    assert start_block_reason(False, ready(rooms_map_fingerprint="b" * 64)) == "rooms_not_bound"
    assert start_block_reason(False, ready(rooms_map_fingerprint=None)) == "rooms_not_bound"
    assert start_block_reason(False, ready(localization_ready=False)) == "not_localized"
    assert start_block_reason(False, ready(navigation_available=False)) == "navigation_unavailable"


def mission(**policy):
    return Mission("room-1", "Küche", (1.0, 2.0, 0.0), MissionPolicy(**policy), started_at=100.0)


def test_successful_drive():
    m = mission()
    m.driving(101.0)
    m.arrived(130.0)
    assert m.state == STATE_SUCCEEDED and not m.running


def test_failed_drive_waits_and_retries_then_ends():
    m = mission(max_attempts=2, retry_wait_s=3.0)
    m.driving(101.0)
    m.drive_failed(120.0, "aborted")
    assert m.state == STATE_RUNNING and m.attempt == 2
    assert not m.retry_due(122.0)
    assert m.retry_due(123.0)
    m.driving(123.0)
    m.drive_failed(140.0, "aborted")
    assert m.state == STATE_FAILED and m.result == "aborted"


def test_lost_position_waits_a_bounded_time():
    m = mission(localization_grace_s=10.0)
    assert not m.localization(False, 101.0)
    assert not m.localization(False, 110.0)
    assert not m.localization(True, 111.0)  # back in time: the run continues
    assert not m.localization(False, 112.0)
    assert m.localization(False, 122.5)


def test_cancel_ends_the_mission():
    m = mission()
    m.cancel(105.0, "app_cancel")
    assert m.state == STATE_CANCELED and m.result == "app_cancel"


def test_status_shape():
    status = mission().as_dict()
    assert set(status) == {"state", "command", "room_id", "room_name", "phase", "attempt",
                           "max_attempts", "distance_remaining_m", "result"}


def test_invalid_policy_is_refused():
    with pytest.raises(ValueError):
        MissionPolicy(max_attempts=0)
    with pytest.raises(ValueError):
        MissionPolicy(retry_wait_s=float("nan"))
