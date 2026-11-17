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

import base64
import json
import math
import os
import random
import signal
import socket
import struct
import subprocess
import tempfile
import time

import pytest
import rclpy
from rcl_interfaces.msg import Parameter as ParameterMsg, ParameterType, ParameterValue
from rcl_interfaces.srv import SetParameters
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node

MODE_COMMAND = "/homemy/mapping_mode/command_json"
MODE_STATUS = "/homemy/mapping_mode/status_json"
MAP = "/map"
MAP_COMMAND = "/homemy/map_manager/command_json"
MAP_STATUS = "/homemy/map_manager/status_json"
ROOM_COMMAND = "/homemy/room_manager/command_json"
ROOM_STATUS = "/homemy/room_manager/status_json"
AUTO_END_S = 4.0

# With HOMEMY_RECORD_FIXTURES=<dir> the test writes the frames it received to
# that directory. The app's Swift tests read them from
# ios/HomeMy/HomeMyTests/Fixtures/backend/ to prove that the app decodes the
# real backend output. All recorded data is synthetic.
FIXTURE_DIR = os.environ.get("HOMEMY_RECORD_FIXTURES")


def record(name: str, frame: dict) -> None:
    if not FIXTURE_DIR:
        return
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    with open(os.path.join(FIXTURE_DIR, f"{name}.json"), "w", encoding="utf-8") as target:
        json.dump(frame, target, ensure_ascii=False, sort_keys=True, indent=1)
        target.write("\n")


# --------------------------------------------------------------------- client


class WebSocketClient:
    """Minimal RFC 6455 text client, enough to act like the app."""

    def __init__(self, port: int) -> None:
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        self.sock.sendall(
            (
                "GET / HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            ).encode("ascii")
        )
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(1024)
            if not chunk:
                raise AssertionError("handshake closed")
            response += chunk
        head, _, rest = response.partition(b"\r\n\r\n")
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise AssertionError(f"unexpected handshake: {head!r}")
        self.buffer = rest
        self.inbox: list[dict] = []

    def send(self, payload: dict) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        mask = os.urandom(4)
        header = bytearray([0x81])
        if len(data) < 126:
            header.append(0x80 | len(data))
        elif len(data) < 65536:
            header.append(0x80 | 126)
            header += struct.pack("!H", len(data))
        else:
            header.append(0x80 | 127)
            header += struct.pack("!Q", len(data))
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
        self.sock.sendall(bytes(header) + mask + masked)

    def _read_exact(self, size: int) -> bytes:
        while len(self.buffer) < size:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise AssertionError("socket closed")
            self.buffer += chunk
        data, self.buffer = self.buffer[:size], self.buffer[size:]
        return data

    def _receive_frame(self) -> dict | None:
        first, second = self._read_exact(2)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(8))[0]
        payload = self._read_exact(length)
        opcode = first & 0x0F
        if opcode != 0x1:
            return None
        return json.loads(payload.decode("utf-8"))

    def wait_for(self, predicate, timeout: float = 15.0) -> dict:
        """Return the first message (old or new) that matches the predicate."""

        for index, message in enumerate(self.inbox):
            if predicate(message):
                return self.inbox.pop(index)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.sock.settimeout(max(0.05, deadline - time.monotonic()))
            try:
                message = self._receive_frame()
            except socket.timeout:
                break
            if message is None:
                continue
            if predicate(message):
                return message
            self.inbox.append(message)
            del self.inbox[:-200]
        raise AssertionError("expected message not received")

    def wait_status(self, topic: str, predicate=lambda s: True, timeout: float = 15.0,
                    record_as: str | None = None) -> dict:
        def matches(message):
            if message.get("op") != "publish" or message.get("topic") != topic:
                return False
            return predicate(json.loads(message["msg"]["data"]))

        frame = self.wait_for(matches, timeout)
        if record_as:
            record(record_as, frame)
        return json.loads(frame["msg"]["data"])

    def drain(self) -> None:
        self.inbox.clear()

    def close(self) -> None:
        self.sock.close()


def publish_json(client: WebSocketClient, topic: str, payload: dict) -> None:
    """The app's StringPublishFrame: JSON text inside std_msgs/String."""

    client.send({"op": "publish", "topic": topic, "msg": {"data": json.dumps(payload)}})


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


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(scope="module")
def stack():
    domain = random.randint(101, 199)
    port = _free_port()
    storage = tempfile.TemporaryDirectory(prefix="homemy-e2e-")
    env = dict(os.environ, ROS_DOMAIN_ID=str(domain), ROS_AUTOMATIC_DISCOVERY_RANGE="LOCALHOST")
    env.pop("ROS_LOCALHOST_ONLY", None)
    log = tempfile.NamedTemporaryFile(prefix="homemy-e2e-launch-", suffix=".log", delete=False)
    process = subprocess.Popen(
        [
            "ros2", "launch", "homemy_bringup", "app_sim.launch.py",
            f"bridge_port:={port}",
            f"storage_root:={storage.name}",
            f"auto_end_timeout_s:={AUTO_END_S}",
        ],
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        try:
            socket.create_connection(("127.0.0.1", port), timeout=1).close()
            break
        except OSError:
            time.sleep(0.5)
    else:
        process.kill()
    if process.poll() is not None:
        log.seek(0)
        pytest.fail("launch ended early:\n" + open(log.name).read()[-4000:])

    context = rclpy.Context()
    rclpy.init(context=context, domain_id=domain)
    node = Node("homemy_e2e_probe", context=context)
    yield {"port": port, "node": node, "context": context, "log": log.name}

    node.destroy_node()
    rclpy.shutdown(context=context)
    os.killpg(process.pid, signal.SIGINT)
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
    storage.cleanup()


def set_parameter(stack, node_name: str, name: str, value) -> None:
    node: Node = stack["node"]
    client = node.create_client(SetParameters, f"/{node_name}/set_parameters")
    assert client.wait_for_service(timeout_sec=10), f"{node_name} has no parameter service"
    parameter_value = ParameterValue()
    if isinstance(value, bool):
        parameter_value.type = ParameterType.PARAMETER_BOOL
        parameter_value.bool_value = value
    else:
        parameter_value.type = ParameterType.PARAMETER_STRING
        parameter_value.string_value = str(value)
    request = SetParameters.Request(parameters=[ParameterMsg(name=name, value=parameter_value)])
    future = client.call_async(request)
    executor = SingleThreadedExecutor(context=stack["context"])
    executor.add_node(node)
    try:
        executor.spin_until_future_complete(future, timeout_sec=10)
    finally:
        executor.remove_node(node)
        executor.shutdown()
    result = future.result()
    assert result is not None and all(item.successful for item in result.results)
    node.destroy_client(client)


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
    node: Node = stack["node"]
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
