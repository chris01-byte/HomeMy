"""The real robot profile (robot.launch.py) against simulated devices.

robot.launch.py is what runs on HomeMy. Here it runs unchanged; only the
motors, the LiDAR, the IMU, and the person with the controller are
simulated. The real drive driver, the unchanged vendor LiDAR driver, and the
real IMU reader each talk to their device through a pseudo-terminal.

Two questions:

1. As delivered, can the profile move anything or use a real scan? It must not.
2. With the local values of commissioning, does the whole chain drive?

Needs the vendor driver ldlidar_stl_ros2 built and sourced; without it the
tests are skipped.

Everything is simulated: no hardware.
"""

from __future__ import annotations

import json
import pathlib
import random
import time

import pytest
import yaml
from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String

from e2e_support import WebSocketClient, launched, set_parameter
from test_drive_sim_e2e import MODE_COMMAND, MODE_STATUS, Probe, mode_command

try:
    get_package_share_directory("ldlidar_stl_ros2")
    VENDOR_DRIVER = True
except PackageNotFoundError:
    VENDOR_DRIVER = False

pytestmark = pytest.mark.skipif(not VENDOR_DRIVER, reason="vendor driver ldlidar_stl_ros2 is not built here")

TEMPLATE = pathlib.Path(get_package_share_directory("homemy_bringup")) / "config" / "robot_local.example.yaml"


class RobotProbe(Probe):
    def __init__(self, stack) -> None:
        super().__init__(stack)
        self.drive = None
        self.imu = None
        self.yaw = None
        self.scans = {"/scan": 0, "/scan_unconfirmed": 0, "/scan_masked": 0}
        node = self.node
        node.create_subscription(String, "/homemy/drivebase/state_json", self._setter("drive"), 10)
        node.create_subscription(String, "/homemy/imu/status_json", self._setter("imu"), 10)
        node.create_subscription(String, "/homemy/imu/yaw_rate_status_json", self._setter("yaw"), 10)
        for topic in self.scans:
            node.create_subscription(LaserScan, topic, self._counter(topic), qos_profile_sensor_data)

    def _counter(self, topic):
        def callback(_message):
            self.scans[topic] += 1
        return callback


def connect(stack):
    control = WebSocketClient(stack["port"])
    control.send({"op": "advertise", "topic": MODE_COMMAND, "type": "std_msgs/String"})
    control.send({"op": "subscribe", "topic": MODE_STATUS, "type": "std_msgs/String"})
    return control


def enable_mapping(control):
    """Switch mapping mode on as the app does: only once the robot offers it.

    The app shows the switch only while the status carries no block reason
    (controller connected, robot ready). Sending the command earlier would be
    refused, and rightly so.
    """

    control.wait_status(
        MODE_STATUS,
        lambda s: s["mapping_mode"]["controller_connected"] and s["mapping_mode"]["enable_block_reason"] is None,
        timeout=40,
    )
    return mode_command(control, "enable", "ios-mode-1")


def sim_id():
    return f"sim_id:=test_{random.randint(0, 10**9)}"


def test_template_of_local_values_unlocks_nothing():
    """Copying the template must change nothing: every value in it is a comment."""

    template = yaml.safe_load(TEMPLATE.read_text())
    for node, section in template.items():
        assert list(section["ros__parameters"]) == ["note"], node
    text = TEMPLATE.read_text()
    for key in ("dry_run: false", "allow_rs485: true", "alignment_confirmed: true"):
        assert f"# {key}" in text and f"\n    {key}" not in text


def test_delivered_profile_moves_nothing_and_uses_no_scan():
    """The robot profile with the untouched template as its local file."""

    with launched("robot_sim.launch.py", [sim_id(), f"locked_params_file:={TEMPLATE}"], ready_timeout=90.0) as stack:
        control = connect(stack)
        probe = RobotProbe(stack)
        try:
            probe.spin_until(
                lambda: None not in (probe.sim, probe.gate, probe.drive, probe.imu), 60, "robot profile running")
            enabled = enable_mapping(control)
            assert enabled["ok"] and enabled["mapping_mode"]["state"] == "active", enabled["message"]

            # Mapping mode is on and the person holds the direction pad forward.
            probe.spin_until(lambda: probe.scans["/scan_unconfirmed"] >= 20, 40, "vendor driver delivers")
            probe.spin(5.0)
            assert probe.travel() == 0.0
            assert probe.sim["bus_requests"] == 0  # not a single byte to the motors
            assert probe.drive["dry_run"] is True and probe.drive["allow_rs485"] is False
            assert probe.scans["/scan"] == 0 and probe.scans["/scan_masked"] == 0
            assert probe.gate["open"] is False
            assert "scan_stale" in probe.gate["reasons"]
            assert probe.map is None  # no scan, no map

            # The IMU is read, and only read.
            assert probe.imu["ready"] is True
            assert probe.sim["imu_non_read_requests"] == 0
        finally:
            probe.close()
            control.close()


def test_commissioned_profile_drives_through_all_three_real_drivers():
    with launched("robot_sim.launch.py", [sim_id(), "commissioned:=true", "operator_drives:=false"],
                  ready_timeout=90.0) as stack:
        control = connect(stack)
        probe = RobotProbe(stack)
        try:
            probe.spin_until(
                lambda: None not in (probe.sim, probe.gate, probe.drive, probe.imu), 60, "robot profile running")
            probe.spin_until(lambda: probe.scans["/scan_masked"] >= 20, 40, "scan reaches the consumers")
            # Standing still: the gyro bias is learned.
            probe.spin_until(lambda: probe.yaw is not None and probe.yaw["ready"], 30, "gyro bias learned")
            assert probe.travel() == 0.0

            enabled = enable_mapping(control)
            assert enabled["ok"] and enabled["mapping_mode"]["state"] == "active", enabled["message"]
            probe.spin(1.0)
            assert probe.travel() == 0.0  # mapping mode on, direction pad not pressed

            set_parameter(stack, "homemy_sim_controller", "driving", True)
            probe.spin_until(lambda: probe.travel() > 0.5, 40, "robot drives forward")
            assert probe.gate["open"] and probe.gate["mode"] == "mapping"
            assert probe.drive["rs485_ready"] is True
            probe.spin_until(lambda: probe.map is not None, 30, "map from the real LiDAR chain")

            set_parameter(stack, "homemy_sim_controller", "driving", False)
            probe.spin(1.0)
            released_at = time.monotonic()
            probe.spin(1.0)
            assert probe.moved_since(released_at) < 0.005

            # Straight ahead: the gyro and the wheels agree that the robot did not turn.
            assert abs(probe.yaw["gyro_minus_wheel_yaw_deg"]) < 2.0
            assert probe.sim["collision"] is False
            assert probe.sim["imu_non_read_requests"] == 0

            disabled = mode_command(control, "disable", "ios-mode-2")
            assert disabled["ok"], json.dumps(disabled)
        finally:
            probe.close()
            control.close()
