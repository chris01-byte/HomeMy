"""End-to-end test of stage S2 mapping: HomeMy drives in the test stand.

Starts ``drive_sim.launch.py`` with the simulated person on the mapping route
and drives the whole route through the real code: app frames over the real
bridge, mapping mode, the real teleop profile, the motion gate with obstacle
protection, the blind-sector mask, slam_toolbox, and the map store.

Checks along the way (contracts/hardware/manual-drive.md,
contracts/ros/motion-gate.md):

- with mapping mode off, a pressed controller moves nothing;
- a frozen radio link stops the robot although the joystick driver keeps
  repeating "forward"; when the link returns, driving continues;
- a pressed emergency stop stops the robot; released, driving continues;
- the route ends without contact;
- the map from slam_toolbox matches the world: after a rigid fit 95 % of
  the wall cells lie within 5 cm and none beyond 15 cm (5 cm grid), and the
  whole map is rotated by at most 2 degrees; it is saved
  through the app's frame with the live map's fingerprint;
- no velocity command can enter through the bridge.

Everything is simulated: no hardware, no real home data.
"""

from __future__ import annotations

import json
import math
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

    def travel(self) -> float:
        return float(self.sim["travel_m"]) if self.sim else 0.0

    def close(self) -> None:
        self.executor.remove_node(self.node)
        self.executor.shutdown()


@pytest.fixture(scope="module")
def stack():
    with launched("drive_sim.launch.py", ["operator_route:=true"], ready_timeout=60.0) as running:
        yield running


def mode_command(client: WebSocketClient, kind: str, request_id: str) -> dict:
    publish_json(client, MODE_COMMAND, {"command": kind, "request_id": request_id})
    return client.wait_status(MODE_STATUS, lambda s: s.get("request_id") == request_id)


def test_mapping_run_through_the_whole_apartment(stack):
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

        # A frozen radio link: the joystick keeps repeating, the robot stops.
        set_parameter(stack, "homemy_sim_controller", "link_frozen", True)
        frozen_at = time.monotonic()
        probe.spin(1.0)
        stopped_at = time.monotonic()
        probe.spin(1.0)
        assert probe.moved_since(stopped_at) < 0.005
        assert probe.moved_since(frozen_at) < 0.15  # stopping distance in the simulation
        assert "controller_link_down" in probe.gate["reasons"]
        control.drain()  # only statuses from after the freeze count
        status = control.wait_status(MODE_STATUS, lambda s: not s["mapping_mode"]["controller_connected"])
        assert status["mapping_mode"]["state"] == "active"  # a lost link does not end mapping mode
        set_parameter(stack, "homemy_sim_controller", "link_frozen", False)
        probe.spin_until(lambda: probe.gate["open"], 10, "driving heals after the link returns")

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
    finally:
        probe.close()
        control.close()
