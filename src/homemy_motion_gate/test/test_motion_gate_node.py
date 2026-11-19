"""ROS-level test of the motion gate node with simulated inputs."""

import json
import math
import os
import pathlib
import time

import pytest
import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from rclpy.executors import SingleThreadedExecutor
from rclpy.parameter import Parameter
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String
from tf2_ros import StaticTransformBroadcaster

from homemy_motion_gate.motion_gate_node import MotionGateNode

GEOMETRY = (
    pathlib.Path(__file__).resolve().parents[2] / "homemy_description" / "config" / "geometry.yaml"
)
LATCHED = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)


@pytest.fixture
def harness():
    context = rclpy.Context()
    rclpy.init(context=context, domain_id=int(os.environ.get("ROS_DOMAIN_ID", "77")) % 100 + 110)
    gate = MotionGateNode(
        context=context,
        parameter_overrides=[
            Parameter("geometry_file", value=str(GEOMETRY)),
            Parameter("clear_time_s", value=0.3),
        ],
    )
    driver = rclpy.create_node("gate_test_driver", context=context)
    executor = SingleThreadedExecutor(context=context)
    executor.add_node(gate)
    executor.add_node(driver)

    broadcaster = StaticTransformBroadcaster(driver)
    transform = TransformStamped()
    transform.header.frame_id = "base_link"
    transform.child_frame_id = "lidar_link"
    transform.transform.translation.x = 0.0694
    transform.transform.translation.z = 0.1638
    transform.transform.rotation.w = 1.0
    broadcaster.sendTransform(transform)

    h = type("Harness", (), {})()
    h.out = []
    h.status = []
    driver.create_subscription(Twist, "/cmd_vel", lambda m: h.out.append((m.linear.x, m.angular.z)), 10)
    driver.create_subscription(String, "/homemy/motion_gate/status_json", lambda m: h.status.append(json.loads(m.data)), LATCHED)
    pubs = {
        "mapping": driver.create_publisher(Bool, "/homemy/mapping_mode/active", LATCHED),
        "mission": driver.create_publisher(Bool, "/homemy/mission/drive_active", LATCHED),
        "lifecycle": driver.create_publisher(String, "/homemy/lifecycle/state", LATCHED),
        "estop": driver.create_publisher(Bool, "/homemy/safety/estop", 10),
        "teleop": driver.create_publisher(Twist, "/homemy/cmd_vel/teleop", 10),
        "scan": driver.create_publisher(LaserScan, "/scan_masked", qos_profile_sensor_data),
    }
    h.wall_at = None
    h.silent = False
    h.command = (0.15, 0.0)

    def publish_inputs():
        pubs["mapping"].publish(Bool(data=True))
        pubs["mission"].publish(Bool(data=False))
        pubs["lifecycle"].publish(String(data="READY"))
        pubs["estop"].publish(Bool(data=False))
        if not h.silent:
            twist = Twist()
            twist.linear.x, twist.angular.z = h.command
            pubs["teleop"].publish(twist)
        scan = LaserScan()
        scan.header.frame_id = "lidar_link"
        scan.angle_min = -math.pi
        scan.angle_increment = 2 * math.pi / 360
        scan.angle_max = math.pi - scan.angle_increment
        scan.range_min = 0.05
        scan.range_max = 10.0
        ranges = [5.0] * 360
        if h.wall_at is not None:
            for i in range(170, 191):  # straight ahead, +-10 degrees
                ranges[i] = h.wall_at
        scan.ranges = ranges
        pubs["scan"].publish(scan)

    def run(seconds):
        end = time.monotonic() + seconds
        next_inputs = 0.0
        while time.monotonic() < end:
            if time.monotonic() >= next_inputs:
                publish_inputs()
                next_inputs = time.monotonic() + 0.05
            executor.spin_once(timeout_sec=0.01)

    h.run = run
    yield h
    executor.shutdown()
    gate.destroy_node()
    driver.destroy_node()
    rclpy.shutdown(context=context)


def test_mapping_command_passes_and_stops_on_release_silence_and_obstacle(harness):
    harness.run(1.5)
    assert harness.out[-1] == pytest.approx((0.15, 0.0))
    assert harness.status[-1]["open"] is True
    assert harness.status[-1]["mode"] == "mapping"

    # Released direction pad: teleop sends zero, the robot stops.
    harness.command = (0.0, 0.0)
    harness.run(0.4)
    assert harness.out[-1] == (0.0, 0.0)

    # No controller messages at all: the last command goes stale, the gate closes.
    harness.command = (0.15, 0.0)
    harness.run(0.4)
    assert harness.out[-1] == pytest.approx((0.15, 0.0))
    harness.silent = True
    harness.run(0.6)
    assert harness.out[-1] == (0.0, 0.0)
    assert "command_stale" in harness.status[-1]["reasons"]

    # Messages return: driving continues by itself.
    harness.silent = False
    harness.run(0.6)
    assert harness.out[-1] == pytest.approx((0.15, 0.0))

    # A wall 20 cm ahead of the LiDAR: forward is blocked, reverse is allowed.
    harness.wall_at = 0.20
    harness.run(0.6)
    assert harness.out[-1] == (0.0, 0.0)
    assert harness.status[-1]["reasons"] in (["obstacle"], ["obstacle_clear_wait"])
    harness.command = (-0.1, 0.0)
    harness.run(0.8)
    assert harness.out[-1] == pytest.approx((-0.1, 0.0))


def test_output_is_zero_at_a_fixed_rate_without_inputs():
    context = rclpy.Context()
    rclpy.init(context=context, domain_id=int(os.environ.get("ROS_DOMAIN_ID", "77")) % 100 + 111)
    gate = MotionGateNode(context=context, parameter_overrides=[Parameter("geometry_file", value=str(GEOMETRY))])
    listener = rclpy.create_node("zero_listener", context=context)
    received = []
    listener.create_subscription(Twist, "/cmd_vel", lambda m: received.append((m.linear.x, m.angular.z)), 10)
    executor = SingleThreadedExecutor(context=context)
    executor.add_node(gate)
    executor.add_node(listener)
    try:
        end = time.monotonic() + 1.2
        while time.monotonic() < end:
            executor.spin_once(timeout_sec=0.01)
        assert len(received) >= 10
        assert set(received) == {(0.0, 0.0)}
    finally:
        executor.shutdown()
        gate.destroy_node()
        listener.destroy_node()
        rclpy.shutdown(context=context)


def test_missing_geometry_is_refused():
    context = rclpy.Context()
    rclpy.init(context=context, domain_id=int(os.environ.get("ROS_DOMAIN_ID", "77")) % 100 + 112)
    try:
        with pytest.raises(ValueError):
            MotionGateNode(context=context)
    finally:
        rclpy.shutdown(context=context)
