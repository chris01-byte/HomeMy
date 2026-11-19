"""End-to-end test of the robot side of the app, over the real bridge.

Starts ``app_sim.launch.py`` as a separate process and talks to it over a
WebSocket with exactly the frames the iOS app sends (see
``ios/HomeMy/HomeMy/Services/RosbridgeProtocol.swift`` and
``MapRosbridgeProtocol.swift``). It covers contracts/api/app-bridge.md:
mapping mode, stop, the growing map, saving, rooms, the bridge allowlist,
the automatic end, and a lifecycle fault.

Everything is simulated. No hardware is used and nothing can move.
"""

from __future__ import annotations

import math
import time

import pytest

from e2e_support import WebSocketClient, launched, publish_json, record, set_parameter

MODE_COMMAND = "/homemy/mapping_mode/command_json"
MODE_STATUS = "/homemy/mapping_mode/status_json"
MAP = "/map"
MAP_COMMAND = "/homemy/map_manager/command_json"
MAP_STATUS = "/homemy/map_manager/status_json"
ROOM_COMMAND = "/homemy/room_manager/command_json"
ROOM_STATUS = "/homemy/room_manager/status_json"
AUTO_END_S = 4.0

def app_accepts_mode_status(status: dict) -> bool:
    """Mirror of MappingModeStatus.isValid in the iOS app."""

    mode = status["mapping_mode"]
    timeout = mode["auto_end_timeout_s"]
    remaining = mode["auto_end_remaining_s"]
    return (
        status["schema_version"] == 1
        and status["event"] in {"status", "enable_result", "disable_result", "stop_result"}
        and bool(status["message"])
        and math.isfinite(status["time"])
        and mode["state"] in {"off", "active"}
        and isinstance(mode["controller_connected"], bool)
        and math.isfinite(timeout)
        and timeout > 0
        and (remaining is None or (mode["state"] == "active" and 0 <= remaining <= timeout))
    )


# --------------------------------------------------------------------- stack


@pytest.fixture(scope="module")
def stack():
    with launched("app_sim.launch.py", [f"auto_end_timeout_s:={AUTO_END_S}"]) as running:
        yield running


@pytest.fixture
def control(stack):
    client = WebSocketClient(stack["port"])
    # RosbridgeProtocol.setupFrames() of the app.
    client.send({"op": "advertise", "topic": MODE_COMMAND, "type": "std_msgs/String"})
    client.send({"op": "subscribe", "topic": MODE_STATUS, "type": "std_msgs/String"})
    yield client
    client.close()


@pytest.fixture
def map_link(stack):
    client = WebSocketClient(stack["port"])
    # MapRosbridgeProtocol.connectionSetupFrames() of the app.
    client.send({"op": "advertise", "topic": MAP_COMMAND, "type": "std_msgs/String"})
    client.send({"op": "advertise", "topic": ROOM_COMMAND, "type": "std_msgs/String"})
    client.send({"id": "homemy-map", "op": "subscribe", "queue_length": 1,
                 "throttle_rate": 1000, "topic": MAP})
    client.send({"id": "homemy-map-manager-status", "op": "subscribe", "queue_length": 1,
                 "topic": MAP_STATUS, "type": "std_msgs/String"})
    client.send({"id": "homemy-room-manager-status", "op": "subscribe", "queue_length": 1,
                 "topic": ROOM_STATUS, "type": "std_msgs/String"})
    yield client
    client.close()


def command(client: WebSocketClient, kind: str, request_id: str,
            record_as: str | None = None) -> dict:
    publish_json(client, MODE_COMMAND, {"command": kind, "request_id": request_id})
    result = client.wait_status(
        MODE_STATUS, lambda s: s["request_id"] == request_id, record_as=record_as
    )
    assert app_accepts_mode_status(result)
    return result


def ensure_off(client: WebSocketClient, tag: str) -> None:
    result = command(client, "stop", f"ios-stop-reset-{tag}")
    assert result["mapping_mode"]["state"] == "off"


# --------------------------------------------------------------------- tests


def test_full_mapping_and_room_flow(control, map_link):
    # 1. The robot reports: mapping mode off, controller connected, enable allowed.
    ready = control.wait_status(
        MODE_STATUS,
        lambda s: s["mapping_mode"]["controller_connected"]
        and s["mapping_mode"]["enable_block_reason"] is None,
        timeout=20,
        record_as="mode_status_ready",
    )
    assert ready["mapping_mode"]["state"] == "off"
    assert app_accepts_mode_status(ready)

    # 2. Mapping run: the map appears and grows.
    enabled = command(control, "enable", "ios-mode-1", record_as="mode_enable_result")
    assert enabled["ok"] and enabled["event"] == "enable_result"
    assert enabled["mapping_mode"]["state"] == "active"
    assert enabled["mapping_mode"]["auto_end_remaining_s"] is not None

    def map_message(message):
        return message.get("op") == "publish" and message.get("topic") == MAP

    first = map_link.wait_for(map_message, timeout=20)["msg"]
    unknown_first = first["data"].count(-1)
    grown = map_link.wait_for(
        lambda m: map_message(m) and m["msg"]["data"].count(-1) < unknown_first, timeout=20
    )["msg"]
    assert grown["info"]["width"] == first["info"]["width"]

    # 3. End the run normally. Saving is offered only now.
    disabled = command(control, "disable", "ios-mode-2")
    assert disabled["mapping_mode"]["state"] == "off"
    assert disabled["mapping_mode"]["last_end_reason"] == "app_disable"

    # 4. Save the map as the app does; rooms become editable.
    map_link.drain()
    manager = map_link.wait_status(
        MAP_STATUS, lambda s: s["ok"] and s["map"]["snapshot_available"], timeout=15
    )
    fingerprint = manager["map"]["summary"]["fingerprint"]
    publish_json(map_link, MAP_COMMAND,
                 {"command": "save", "name": "wohnung", "request_id": "ios-map-1"})
    saved = map_link.wait_status(MAP_STATUS, lambda s: s.get("request_id") == "ios-map-1",
                                 record_as="map_manager_save_result")
    assert saved["ok"] and saved["event"] == "save_result"
    assert saved["storage"]["last_saved"]["fingerprint"] == fingerprint

    bound = map_link.wait_status(
        ROOM_STATUS,
        lambda s: (s.get("semantic_map") or {}).get("editable") is True,
        timeout=15,
        record_as="room_status_bound",
    )
    semantic = bound["semantic_map"]
    map_link.drain()
    saved_map = map_link.wait_for(map_message, timeout=15)
    record("map_saved", saved_map)
    assert semantic["map_ref"]["fingerprint"] == fingerprint
    revision = semantic["revision"]

    # 5. Draw a room with a navigation goal.
    room = {
        "id": "kueche",
        "name": "Küche",
        "color": "#31A8FF",
        "polygon": [
            {"x": -2.0, "y": -1.5},
            {"x": -0.5, "y": -1.5},
            {"x": -0.5, "y": 0.0},
            {"x": -2.0, "y": 0.0},
        ],
        "navigation_goal": {"x": -1.2, "y": -0.8, "yaw": 0.0},
    }
    publish_json(map_link, ROOM_COMMAND, {
        "command": "upsert_room",
        "request_id": "ios-room-1",
        "map_fingerprint": fingerprint,
        "base_revision": revision,
        "room": room,
    })
    created = map_link.wait_status(ROOM_STATUS, lambda s: s.get("request_id") == "ios-room-1",
                                   record_as="room_status_created")
    assert created["ok"], created["message"]
    assert created["semantic_map"]["revision"] > revision
    assert [r["id"] for r in created["semantic_map"]["rooms"]] == ["kueche"]

    # 6. A second run ends with the stop button; stop is idempotent.
    assert command(control, "enable", "ios-mode-3")["mapping_mode"]["state"] == "active"
    stopped = command(control, "stop", "ios-stop-1", record_as="mode_stop_result")
    assert stopped["ok"] and stopped["event"] == "stop_result"
    assert stopped["mapping_mode"]["state"] == "off"
    assert stopped["mapping_mode"]["last_end_reason"] == "app_stop"
    again = command(control, "stop", "ios-stop-1")
    assert again["ok"] and again["mapping_mode"]["state"] == "off"


def test_bridge_refuses_topics_outside_the_app_contract(stack, control):
    node = stack["node"]
    control.send({"op": "advertise", "topic": "/cmd_vel", "type": "geometry_msgs/Twist"})
    control.send({"op": "publish", "topic": "/cmd_vel",
                  "msg": {"linear": {"x": 0.5, "y": 0.0, "z": 0.0},
                          "angular": {"x": 0.0, "y": 0.0, "z": 0.0}}})
    control.send({"op": "subscribe", "topic": "/rosout", "type": "rcl_interfaces/Log"})
    control.send({"op": "call_service", "service": "/homemy_sim_controller/set_parameters",
                  "args": {}})
    time.sleep(2.0)

    topics = dict(node.get_topic_names_and_types())
    assert "/cmd_vel" not in topics
    assert not any(
        m.get("topic") == "/rosout" and m.get("op") == "publish" for m in control.inbox
    )
    # The allowed status topic still works on the same connection.
    assert app_accepts_mode_status(control.wait_status(MODE_STATUS))


def test_mapping_mode_ends_by_itself_without_controller_input(stack, control):
    ensure_off(control, "auto")
    set_parameter(stack, "homemy_sim_controller", "driving", False)
    try:
        assert command(control, "enable", "ios-mode-auto")["mapping_mode"]["state"] == "active"
        ended = control.wait_status(
            MODE_STATUS,
            lambda s: s["mapping_mode"]["state"] == "off",
            timeout=AUTO_END_S + 6,
            record_as="mode_status_inactivity_ended",
        )
        assert ended["mapping_mode"]["last_end_reason"] == "inactivity_timeout"
        assert app_accepts_mode_status(ended)
    finally:
        set_parameter(stack, "homemy_sim_controller", "driving", True)


def test_disconnected_controller_is_reported(stack, control):
    set_parameter(stack, "homemy_sim_controller", "connected", False)
    try:
        lost = control.wait_status(
            MODE_STATUS, lambda s: s["mapping_mode"]["controller_connected"] is False
        )
        assert app_accepts_mode_status(lost)
    finally:
        set_parameter(stack, "homemy_sim_controller", "connected", True)
    control.wait_status(MODE_STATUS, lambda s: s["mapping_mode"]["controller_connected"])


def test_lifecycle_fault_blocks_and_ends_mapping_mode(stack, control):
    ensure_off(control, "fault")
    assert command(control, "enable", "ios-mode-fault")["mapping_mode"]["state"] == "active"
    set_parameter(stack, "homemy_lifecycle_stub", "state", "FAULT")
    try:
        ended = control.wait_status(
            MODE_STATUS, lambda s: s["mapping_mode"]["last_end_reason"] == "fault"
        )
        assert ended["mapping_mode"]["state"] == "off"
        refused = command(control, "enable", "ios-mode-fault-2", record_as="mode_enable_refused")
        assert refused["ok"] is False
        assert refused["mapping_mode"]["enable_block_reason"] == "fault"
    finally:
        set_parameter(stack, "homemy_lifecycle_stub", "state", "READY")
    control.wait_status(MODE_STATUS, lambda s: s["mapping_mode"]["enable_block_reason"] is None)
