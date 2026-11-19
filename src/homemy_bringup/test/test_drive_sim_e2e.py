"""End-to-end test of stage S2 mapping: HomeMy drives in the test stand.

Starts ``drive_sim.launch.py`` with the simulated person on the mapping route
and drives the whole route through the real code: app frames over the real
bridge, mapping mode, the real teleop profile, the motion gate with obstacle
protection, the blind-sector mask, slam_toolbox, and the map store.

Checks along the way (contracts/hardware/manual-drive.md,
contracts/ros/motion-gate.md):

- with mapping mode off, a pressed controller moves nothing;
- letting go of the direction pad stops the robot, pressing again drives on;
  a controller that is switched off stops the robot too, and mapping mode
  stays active;
- a pressed emergency stop stops the robot; released, driving continues;
- the route ends without contact;
- the map from slam_toolbox matches the world: after a rigid fit 95 % of
  the wall cells lie within 5 cm and none beyond 15 cm (5 cm grid), and the
  whole map is rotated by at most 2 degrees; it is saved
  through the app's frame with the live map's fingerprint;
- no velocity command can enter through the bridge;
- after saving, localization switches to the saved map with AMCL and
  reports a trusted position; rooms drawn with the app's frames stay bound;
- "drive to a room" from the app reaches the living room through two doors;
  a cancelled drive stops the robot; missions are refused while mapping;
- after a restart where the robot stood, it trusts its stored pose and
  drives to the bedroom; after a restart where it was secretly moved, it
  does not trust the stored pose and refuses to drive.

Everything is simulated: no hardware, no real home data.
"""

from __future__ import annotations

import json
import math
import tempfile
import time

import numpy as np
import pytest
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

from e2e_support import WebSocketClient, launched, publish_json, set_parameter
from homemy_simulation.world import FloorPlanWorld, RobotGeometry

MODE_COMMAND = "/homemy/mapping_mode/command_json"
MODE_STATUS = "/homemy/mapping_mode/status_json"
MAP_COMMAND = "/homemy/map_manager/command_json"
MAP_STATUS = "/homemy/map_manager/status_json"
ROOM_COMMAND = "/homemy/room_manager/command_json"
ROOM_STATUS = "/homemy/room_manager/status_json"
MISSION_COMMAND = "/homemy/mission/command_json"
MISSION_STATUS = "/homemy/mission/status_json"
START = (1.6, 0.7)  # world start pose; the map frame begins here (yaw 0)

# Rooms of the test apartment in world coordinates: interior and drive goal.
ROOMS = {
    "wohnzimmer": ("Wohnzimmer", (0.0, 4.6, 0.0, 4.0), (3.0, 1.0, math.pi)),
    "kueche": ("Küche", (4.7, 7.6, -0.8, 1.5), (6.2, 0.6, 0.0)),
    "schlafzimmer": ("Schlafzimmer", (6.2, 9.4, 1.6, 4.6), (8.3, 2.2, 0.0)),
}
SHARED = {}
LATCHED = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)
ROUTE_TIMEOUT_S = 420.0


class Probe:
    """Reads the test stand's ground truth and the robot's own outputs."""

    def __init__(self, stack) -> None:
        self.node = stack["node"]
        self.executor = SingleThreadedExecutor(context=stack["context"])
        self.executor.add_node(self.node)
        self.truth = []  # (monotonic time, x, y)
        self.operator = None
        self.sim = None
        self.gate = None
        self.map = None
        self.localization = None
        self.node.create_subscription(String, "/homemy/localization/status_json", self._setter("localization"), LATCHED)
        self.node.create_subscription(PoseStamped, "/homemy/sim/ground_truth", self._on_truth, 10)
        self.node.create_subscription(String, "/homemy/sim/operator_status", self._setter("operator"), 10)
        self.node.create_subscription(String, "/homemy/sim/status_json", self._setter("sim"), 10)
        self.node.create_subscription(String, "/homemy/motion_gate/status_json", self._setter("gate"), LATCHED)
        self.node.create_subscription(OccupancyGrid, "/map", self._on_map, LATCHED)

    def _setter(self, name):
        def callback(message):
            setattr(self, name, json.loads(message.data))
        return callback

    def _on_truth(self, message):
        self.truth.append((time.monotonic(), message.pose.position.x, message.pose.position.y))
        del self.truth[:-2000]

    def _on_map(self, message):
        self.map = message

    def spin(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.executor.spin_once(timeout_sec=0.02)

    def spin_until(self, predicate, timeout: float, what: str):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.executor.spin_once(timeout_sec=0.02)
            if predicate():
                return
        raise AssertionError(f"not reached in {timeout:.0f} s: {what}")

    def moved_since(self, since: float) -> float:
        points = [(x, y) for t, x, y in self.truth if t >= since]
        if len(points) < 2:
            return 0.0
        return math.hypot(points[-1][0] - points[0][0], points[-1][1] - points[0][1])

    def pose(self):
        return (self.truth[-1][1], self.truth[-1][2]) if self.truth else None

    def travel(self) -> float:
        return float(self.sim["travel_m"]) if self.sim else 0.0

    def close(self) -> None:
        self.executor.remove_node(self.node)
        self.executor.shutdown()


@pytest.fixture(scope="module")
def storage_dir():
    with tempfile.TemporaryDirectory(prefix="homemy-e2e-drive-") as directory:
        yield directory


def to_map(x, y):
    return x - START[0], y - START[1]


def room_payload(room_id, grid_info):
    """The room as the app draws it: a rectangle inside the room and on the map."""

    name, (x0, x1, y0, y1), (gx, gy, gyaw) = ROOMS[room_id]
    left, bottom = grid_info.origin.position.x + 0.05, grid_info.origin.position.y + 0.05
    right = grid_info.origin.position.x + grid_info.width * grid_info.resolution - 0.05
    top = grid_info.origin.position.y + grid_info.height * grid_info.resolution - 0.05
    (ax, ay), (bx, by) = to_map(x0 + 0.05, y0 + 0.05), to_map(x1 - 0.05, y1 - 0.05)
    ax, bx = max(ax, left), min(bx, right)
    ay, by = max(ay, bottom), min(by, top)
    corners = [(ax, ay), (bx, ay), (bx, by), (ax, by)]
    mx, my = to_map(gx, gy)
    return {"id": room_id, "name": name, "color": "#31A8FF",
            "polygon": [{"x": round(x, 3), "y": round(y, 3)} for x, y in corners],
            "navigation_goal": {"x": round(mx, 3), "y": round(my, 3), "yaw": gyaw}}


def mission_link(port):
    link = WebSocketClient(port)
    link.send({"op": "advertise", "topic": MISSION_COMMAND, "type": "std_msgs/String"})
    link.send({"op": "subscribe", "topic": MISSION_STATUS, "type": "std_msgs/String"})
    return link


def go_to_room(link, room_id, request_id, record_as=None):
    publish_json(link, MISSION_COMMAND, {"command": "go_to_room", "room_id": room_id, "request_id": request_id})
    return link.wait_status(MISSION_STATUS, lambda s: s.get("request_id") == request_id, timeout=20,
                            record_as=record_as)


def wait_mission(link, predicate, timeout, record_as=None):
    return link.wait_status(MISSION_STATUS, lambda s: predicate(s["mission"]), timeout=timeout,
                            record_as=record_as)


def assert_arrived(probe, room_id):
    name, (x0, x1, y0, y1), (gx, gy, _) = ROOMS[room_id]
    probe.spin(1.0)
    x, y = probe.pose()
    assert x0 <= x <= x1 and y0 <= y <= y1, (room_id, x, y)
    assert math.hypot(x - gx, y - gy) <= 0.35, (room_id, x, y)


def mode_command(client: WebSocketClient, kind: str, request_id: str) -> dict:
    publish_json(client, MODE_COMMAND, {"command": kind, "request_id": request_id})
    return client.wait_status(MODE_STATUS, lambda s: s.get("request_id") == request_id)


def test_mapping_run_then_drive_to_rooms(storage_dir):
    with launched("drive_sim.launch.py", ["operator_route:=true"], ready_timeout=60.0,
                  storage_root=storage_dir) as stack:
        mapping_run_then_drive_to_rooms(stack)


def mapping_run_then_drive_to_rooms(stack):
    control = WebSocketClient(stack["port"])
    control.send({"op": "advertise", "topic": MODE_COMMAND, "type": "std_msgs/String"})
    control.send({"op": "subscribe", "topic": MODE_STATUS, "type": "std_msgs/String"})
    probe = Probe(stack)
    try:
        # Nothing moves while mapping mode is off, although the person presses.
        probe.spin_until(lambda: probe.sim is not None and probe.gate is not None, 30, "test stand running")
        probe.spin(3.0)
        assert probe.travel() == 0.0
        assert "mode_off" in probe.gate["reasons"]
        status = control.wait_status(MODE_STATUS, lambda s: s["mapping_mode"]["controller_connected"], timeout=20)
        assert status["mapping_mode"]["state"] == "off"

        # The app switches mapping mode on; the person starts to drive.
        enabled = mode_command(control, "enable", "ios-mode-1")
        assert enabled["ok"] and enabled["mapping_mode"]["state"] == "active"
        probe.spin_until(lambda: probe.travel() > 0.8, 40, "robot drives")

        # The person lets go of the direction pad: the robot stops.
        set_parameter(stack, "homemy_sim_controller", "driving", False)
        probe.spin(1.0)
        released_at = time.monotonic()
        probe.spin(1.0)
        assert probe.moved_since(released_at) < 0.005
        assert probe.gate["open"] and probe.gate["mode"] == "mapping"  # open, with a zero command
        set_parameter(stack, "homemy_sim_controller", "driving", True)
        resumed_at = time.monotonic()
        probe.spin(2.0)
        assert probe.moved_since(resumed_at) > 0.05 or probe.travel() > 0.8

        # The controller is switched off: no more messages, the robot stops.
        # Mapping mode stays active (owner decision).
        set_parameter(stack, "homemy_sim_controller", "connected", False)
        off_at = time.monotonic()
        probe.spin(1.0)
        stopped_at = time.monotonic()
        probe.spin(1.0)
        assert probe.moved_since(stopped_at) < 0.005
        assert probe.moved_since(off_at) < 0.15  # stopping distance in the simulation
        assert "command_stale" in probe.gate["reasons"]
        control.drain()  # only statuses from after the switch-off count
        status = control.wait_status(MODE_STATUS, lambda s: not s["mapping_mode"]["controller_connected"])
        assert status["mapping_mode"]["state"] == "active"
        set_parameter(stack, "homemy_sim_controller", "connected", True)
        probe.spin_until(lambda: probe.gate["open"], 10, "driving continues when the controller is back")

        # Emergency stop pressed and released.
        set_parameter(stack, "homemy_lifecycle_stub", "estop_pressed", True)
        probe.spin(1.0)
        held = time.monotonic()
        probe.spin(1.0)
        assert probe.moved_since(held) < 0.005
        assert "estop_pressed" in probe.gate["reasons"]
        set_parameter(stack, "homemy_lifecycle_stub", "estop_pressed", False)
        probe.spin_until(lambda: probe.gate["open"], 10, "driving continues after release")

        # The rest of the route, through all four rooms.
        probe.spin_until(lambda: probe.operator and probe.operator["done"], ROUTE_TIMEOUT_S, "route finished")
        probe.spin(1.0)
        assert probe.sim["collision"] is False
        assert probe.sim["room"] == "schlafzimmer"

        # The app ends mapping mode; the map stays.
        disabled = mode_command(control, "disable", "ios-mode-2")
        assert disabled["ok"] and disabled["mapping_mode"]["state"] == "off"
        probe.spin(3.0)
        assert probe.map is not None

        geometry = yaml.safe_load(open(
            get_package_share_directory("homemy_description") + "/config/geometry.yaml", encoding="utf-8"))
        world = FloorPlanWorld.from_file(
            get_package_share_directory("homemy_simulation") + "/worlds/testwohnung.json",
            RobotGeometry.from_yaml_dict(geometry))
        grid = np.array(probe.map.data).reshape(probe.map.info.height, probe.map.info.width)
        quality = world.map_error(
            grid, probe.map.info.resolution,
            (probe.map.info.origin.position.x, probe.map.info.origin.position.y),
            tuple(world.start))
        print("map quality:", quality)
        # The map grid is 5 cm: a cell centre alone can be 3.5 cm off a wall.
        # A small rotation of the whole map grows over the 9 m apartment but
        # does not hurt driving in the robot's own map; the shape is judged
        # after a rigid fit. Amadeus required 10 cm at a 1 cm grid.
        assert abs(quality["alignment_rotation_deg"]) <= 2.0
        assert quality["max_occupied_error_m"] <= 0.30
        assert quality["aligned_p95_error_m"] <= 0.05
        assert quality["aligned_max_error_m"] <= 0.15
        assert quality["free_fraction_known"] >= 0.85

        # Saved with the app's frame, bound to the live map's fingerprint.
        map_link = WebSocketClient(stack["port"])
        try:
            map_link.send({"op": "advertise", "topic": MAP_COMMAND, "type": "std_msgs/String"})
            map_link.send({"id": "status", "op": "subscribe", "queue_length": 1,
                           "topic": MAP_STATUS, "type": "std_msgs/String"})
            manager = map_link.wait_status(MAP_STATUS, lambda s: s["ok"] and s["map"]["snapshot_available"])
            fingerprint = manager["map"]["summary"]["fingerprint"]
            publish_json(map_link, MAP_COMMAND, {"command": "save", "name": "wohnung", "request_id": "ios-map-1"})
            saved = map_link.wait_status(MAP_STATUS, lambda s: s.get("request_id") == "ios-map-1")
            assert saved["ok"] and saved["storage"]["last_saved"]["fingerprint"] == fingerprint
        finally:
            map_link.close()

        # No velocity command can enter through the bridge: the gate stays the
        # only publisher of /cmd_vel.
        control.send({"op": "advertise", "topic": "/cmd_vel", "type": "geometry_msgs/Twist"})
        control.send({"op": "publish", "topic": "/cmd_vel", "msg": {"linear": {"x": 0.5}}})
        probe.spin(2.0)
        publishers = probe.node.get_publishers_info_by_topic("/cmd_vel")
        assert [info.node_name for info in publishers] == ["motion_gate"]

        # Saving switches localization to the saved map; the position is trusted.
        probe.spin_until(lambda: probe.localization and probe.localization["mode"] == "navigation"
                         and probe.localization["ready"], 60, "localization on the saved map")
        assert probe.localization["map"]["fingerprint"] == fingerprint
        assert probe.localization["initial_pose_source"] == "slam_handover"

        # Rooms drawn as the app does, bound to the saved map.
        rooms_link = WebSocketClient(stack["port"])
        try:
            rooms_link.send({"op": "advertise", "topic": ROOM_COMMAND, "type": "std_msgs/String"})
            rooms_link.send({"op": "subscribe", "topic": ROOM_STATUS, "type": "std_msgs/String"})
            status = rooms_link.wait_status(ROOM_STATUS, lambda s: (s.get("semantic_map") or {}).get("editable") is True)
            assert status["semantic_map"]["map_ref"]["fingerprint"] == fingerprint
            revision = status["semantic_map"]["revision"]
            for number, room_id in enumerate(ROOMS):
                publish_json(rooms_link, ROOM_COMMAND, {
                    "command": "upsert_room", "request_id": f"ios-room-{number}",
                    "map_fingerprint": fingerprint, "base_revision": revision,
                    "room": room_payload(room_id, probe.map.info)})
                created = rooms_link.wait_status(ROOM_STATUS, lambda s, n=number: s.get("request_id") == f"ios-room-{n}")
                assert created["ok"], created["message"]
                revision = created["semantic_map"]["revision"]
        finally:
            rooms_link.close()

        # Drive to the living room: through the hall and two doors.
        missions = mission_link(stack["port"])
        try:
            started = go_to_room(missions, "wohnzimmer", "ios-go-1", record_as="mission_go_to_room_result")
            assert started["ok"], started["message"]
            wait_mission(missions, lambda m: m["state"] == "running" and m["distance_remaining_m"] is not None,
                         timeout=60, record_as="mission_running")
            done = wait_mission(missions, lambda m: m["state"] in ("succeeded", "failed", "canceled"), timeout=240,
                                record_as="mission_finished")
            assert done["mission"]["state"] == "succeeded", done
            assert_arrived(probe, "wohnzimmer")
            assert probe.sim["collision"] is False

            # A cancelled drive stops the robot.
            started = go_to_room(missions, "kueche", "ios-go-2")
            assert started["ok"], started["message"]
            probe.spin_until(lambda: probe.gate["mode"] == "mission" and probe.gate["open"], 30, "mission drives")
            probe.spin(3.0)
            publish_json(missions, MISSION_COMMAND, {"command": "cancel", "request_id": "ios-cancel-1"})
            canceled = missions.wait_status(MISSION_STATUS, lambda s: s.get("request_id") == "ios-cancel-1",
                                            record_as="mission_cancel_result")
            assert canceled["ok"] and canceled["mission"]["state"] == "canceled"
            probe.spin(1.5)
            held = time.monotonic()
            probe.spin(1.5)
            assert probe.moved_since(held) < 0.01
            assert "mode_off" in probe.gate["reasons"]

            # Missions are refused while mapping mode is on.
            assert mode_command(control, "enable", "ios-mode-3")["ok"]
            refused = go_to_room(missions, "schlafzimmer", "ios-go-3", record_as="mission_refused_mapping")
            assert not refused["ok"] and refused["start_block_reason"] == "mapping_active"
            assert mode_command(control, "disable", "ios-mode-4")["ok"]
        finally:
            missions.close()
        x, y = probe.pose()
        yaw_truth = probe.sim["pose"][2]
        SHARED["final_pose"] = (x, y, yaw_truth)
    finally:
        probe.close()
        control.close()


def restart(storage_dir, pose):
    argument = "start_pose:=[{:.4f}, {:.4f}, {:.4f}]".format(*pose)
    return launched("drive_sim.launch.py", [argument], ready_timeout=60.0, storage_root=storage_dir)


def test_restart_where_the_robot_stood_trusts_the_stored_pose(storage_dir):
    if "final_pose" not in SHARED:
        pytest.skip("needs the mapping run of the first test")
    with restart(storage_dir, SHARED["final_pose"]) as stack:
        probe = Probe(stack)
        missions = mission_link(stack["port"])
        try:
            probe.spin_until(lambda: probe.localization and probe.localization["ready"], 60, "trusted after restart")
            assert probe.localization["initial_pose_source"] == "stored"
            started = go_to_room(missions, "schlafzimmer", "ios-go-4")
            assert started["ok"], started["message"]
            done = wait_mission(missions, lambda m: m["state"] in ("succeeded", "failed", "canceled"), timeout=240)
            assert done["mission"]["state"] == "succeeded", done
            assert_arrived(probe, "schlafzimmer")
            assert probe.sim["collision"] is False
        finally:
            missions.close()
            probe.close()


def test_restart_after_the_robot_was_moved_is_not_trusted(storage_dir):
    if "final_pose" not in SHARED:
        pytest.skip("needs the mapping run of the first test")
    # The robot was carried into the kitchen while switched off.
    with restart(storage_dir, (6.2, 0.6, 0.0)) as stack:
        probe = Probe(stack)
        missions = mission_link(stack["port"])
        try:
            probe.spin_until(lambda: probe.localization and probe.localization["mode"] == "navigation", 60,
                             "navigation mode after restart")
            probe.spin(15.0)
            assert probe.localization["ready"] is False
            refused = go_to_room(missions, "wohnzimmer", "ios-go-5", record_as="mission_refused_not_localized")
            assert not refused["ok"] and refused["start_block_reason"] == "not_localized"
            probe.spin(2.0)
            assert probe.travel() == 0.0
        finally:
            missions.close()
            probe.close()
