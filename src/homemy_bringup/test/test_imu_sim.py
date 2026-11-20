"""The IMU chain against a simulated HWT601, with the drive driver at simulated motors.

Commissioning steps I0 to I5 in simulation (contracts/hardware/imu-commissioning.md):
the real reader only reads; the yaw-rate aid learns the bias at standstill;
the gyro sees a turn of the chassis that the wheels cannot see; and the
fused odometry follows the gyro, with the wheels as fallback.

Everything is simulated: no hardware.
"""

from __future__ import annotations

import json
import math
import random
import time

from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu
from std_msgs.msg import String
from tf2_msgs.msg import TFMessage

from e2e_support import launched_plain, set_parameter


def yaw_of(orientation) -> float:
    return math.atan2(2.0 * orientation.w * orientation.z, 1.0 - 2.0 * orientation.z * orientation.z)


class Unwrapped:
    """A yaw angle followed over several turns."""

    def __init__(self) -> None:
        self.total = 0.0
        self._last = None

    def add(self, yaw: float) -> None:
        if self._last is not None:
            self.total += math.atan2(math.sin(yaw - self._last), math.cos(yaw - self._last))
        self._last = yaw


class Bench:
    def __init__(self, stack) -> None:
        self.stack = stack
        self.node = stack["node"]
        self.executor = SingleThreadedExecutor(context=stack["context"])
        self.executor.add_node(self.node)
        self.imu = None           # reader status
        self.yaw = None           # yaw-rate status
        self.sim = None
        self.raw = []             # (frame, z rate, z acceleration)
        self.rates = []           # corrected yaw rates
        self.truth = Unwrapped()
        self.odom = {"/odom": Unwrapped(), "/wheel/odom": Unwrapped()}
        self.odom_rate = {"/odom": 0.0, "/wheel/odom": 0.0}
        self.tf_authors = set()
        node = self.node
        node.create_subscription(String, "/homemy/imu/status_json", self._setter("imu"), 10)
        node.create_subscription(String, "/homemy/imu/yaw_rate_status_json", self._setter("yaw"), 10)
        node.create_subscription(String, "/homemy/sim/status_json", self._setter("sim"), 10)
        node.create_subscription(Imu, "/imu/data_raw", self._on_raw, qos_profile_sensor_data)
        node.create_subscription(
            Imu, "/imu/yaw_rate", lambda m: self.rates.append(m.angular_velocity.z), qos_profile_sensor_data)
        node.create_subscription(
            PoseStamped, "/homemy/sim/ground_truth", lambda m: self.truth.add(yaw_of(m.pose.orientation)), 50)
        for topic in self.odom:
            node.create_subscription(Odometry, topic, self._odom_callback(topic), 50)
        node.create_subscription(TFMessage, "/tf", self._on_tf, 50)
        self.commands = node.create_publisher(Twist, "/cmd_vel", 1)

    def _setter(self, name):
        def callback(message):
            setattr(self, name, json.loads(message.data))
        return callback

    def _on_raw(self, message):
        self.raw.append((message.header.frame_id, message.angular_velocity.z, message.linear_acceleration.z))
        del self.raw[:-2000]

    def _odom_callback(self, topic):
        def callback(message):
            self.odom[topic].add(yaw_of(message.pose.pose.orientation))
            self.odom_rate[topic] = message.twist.twist.angular.z
        return callback

    def _on_tf(self, message):
        for transform in message.transforms:
            if transform.header.frame_id == "odom" and transform.child_frame_id == "base_link":
                self.tf_authors.add("odom->base_link")

    def spin(self, seconds, command=None):
        end = time.monotonic() + seconds
        next_publish = 0.0
        while time.monotonic() < end:
            if command is not None and time.monotonic() >= next_publish:
                twist = Twist()
                twist.linear.x, twist.angular.z = command
                self.commands.publish(twist)
                next_publish = time.monotonic() + 0.05
            self.executor.spin_once(timeout_sec=0.01)

    def spin_until(self, predicate, timeout, what, command=None):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.spin(0.1, command)
            if predicate():
                return
        raise AssertionError(
            f"not reached in {timeout:.0f} s: {what}\nreader: {self.imu}\nyaw: {self.yaw}\n"
            + open(self.stack["log"]).read()[-3000:])

    def turn(self, radians, rate=0.5):
        """Turn in place by about ``radians`` (measured on the ground truth), then stand."""

        start = self.truth.total
        command = (0.0, math.copysign(rate, radians))
        self.spin_until(lambda: abs(self.truth.total - start) >= abs(radians) - 0.05, 60, "turn", command)
        self.spin(1.5)

    def close(self):
        self.executor.remove_node(self.node)
        self.executor.shutdown()


def arguments(fusion: bool):
    return [f"use_imu_fusion:={'true' if fusion else 'false'}", f"sim_id:=test_{random.randint(0, 10**9)}"]


def degrees(value: float) -> float:
    return math.degrees(value)


def test_reader_only_reads_and_the_gyro_sees_what_the_wheels_miss():
    with launched_plain("imu_sim.launch.py", arguments(False)) as stack:
        bench = Bench(stack)
        try:
            # I0, I1: the reader delivers raw data in the sensor's own axes.
            bench.spin_until(lambda: bench.imu is not None and bench.imu["ready"], 30, "reader ready")
            assert bench.imu["sensor_write_commands"] is False
            assert bench.imu["actuator_output"] is False
            bench.spin(1.0)
            assert bench.imu["observed_rate_hz"] > 60.0
            frame, _, acceleration_z = bench.raw[-1]
            assert frame == "imu_link"
            assert acceleration_z < -9.0  # the simulated sensor is mounted upside down

            # I2: no yaw rate before the bias is learned at standstill.
            assert bench.rates == []
            bench.spin_until(lambda: bench.yaw is not None and bench.yaw["ready"], 20, "bias learned")
            # The sensor's z axis points down: its offset of 0.004 rad/s appears with the robot's sign.
            assert abs(bench.yaw["bias_radps"] - 0.004) < 0.001

            # I3, I4: a full turn. The simulated chassis is 2 % wider and its
            # wheels 1 % smaller than the driver believes, so the wheels
            # overestimate the turn by about 3 %.
            bench.truth.total = 0.0
            bench.spin(0.6)
            start_gyro, start_wheel = bench.yaw["gyro_yaw_deg"], bench.yaw["wheel_yaw_deg"]
            bench.turn(2.0 * math.pi)
            bench.spin(0.6)
            truth = degrees(bench.truth.total)
            gyro = bench.yaw["gyro_yaw_deg"] - start_gyro
            wheel = bench.yaw["wheel_yaw_deg"] - start_wheel
            print(f"RESULT shadow: full turn truth {truth:.1f}, gyro {gyro:.1f}, wheels {wheel:.1f} degrees")
            assert abs(gyro - truth) < 2.0, (gyro, truth)
            assert 6.0 < wheel - truth < 16.0, (wheel, truth)

            # A tile joint: the chassis turns 5 degrees, the wheels do not.
            before = dict(bench.yaw)
            set_parameter(stack, "homemy_sim_base", "yaw_kick_deg", 5.0)
            bench.spin(3.0)
            assert abs((bench.yaw["gyro_yaw_deg"] - before["gyro_yaw_deg"]) - 5.0) < 0.6
            assert abs(bench.yaw["wheel_yaw_deg"] - before["wheel_yaw_deg"]) < 0.3
            learned = bench.yaw["bias_radps"]

            # Shadow mode: the drive driver alone owns the odometry.
            assert bench.odom["/wheel/odom"]._last is None
            assert bench.odom["/odom"]._last is not None

            # I1: cable pulled, then answers with a broken checksum.
            for fault in ("imu_silent", "imu_corrupt"):
                set_parameter(stack, "homemy_sim_base", fault, True)
                bench.spin_until(lambda: not bench.imu["ready"] and not bench.yaw["ready"], 10, f"{fault} noticed")
                bench.rates.clear()
                bench.spin(1.0)
                assert bench.rates == []
                set_parameter(stack, "homemy_sim_base", fault, False)
                bench.spin_until(lambda: bench.imu["ready"] and bench.yaw["ready"], 15, f"{fault} healed")
            assert abs(bench.yaw["bias_radps"] - learned) < 0.001  # kept, not learned anew

            # The reader never tried to write to the sensor.
            bench.spin(1.2)
            assert bench.sim["imu_non_read_requests"] == 0
            assert bench.sim["imu_requests"] > 1000
        finally:
            bench.close()


def test_fused_odometry_follows_the_gyro_and_falls_back_to_the_wheels():
    with launched_plain("imu_sim.launch.py", arguments(True)) as stack:
        bench = Bench(stack)
        try:
            bench.spin_until(lambda: bench.yaw is not None and bench.yaw["ready"], 40, "bias learned")
            bench.spin_until(lambda: bench.odom["/odom"]._last is not None, 20, "fused odometry")
            bench.spin(1.0)
            assert "odom->base_link" in bench.tf_authors

            for unwrapped in (bench.truth, bench.odom["/odom"], bench.odom["/wheel/odom"]):
                unwrapped.total = 0.0
            bench.turn(2.0 * math.pi)
            set_parameter(stack, "homemy_sim_base", "yaw_kick_deg", 5.0)
            bench.spin(3.0)
            truth = degrees(bench.truth.total)
            fused = degrees(bench.odom["/odom"].total)
            wheels = degrees(bench.odom["/wheel/odom"].total)
            print(f"RESULT fused: turn and kick truth {truth:.1f}, fused {fused:.1f}, wheels {wheels:.1f} degrees")
            assert abs(fused - truth) < 2.5, (fused, truth)
            assert abs(wheels - truth) > 5.0 * 0.4, (wheels, truth)
            assert abs(fused - truth) < abs(wheels - truth)

            # The gyro falls silent while turning: the odometry keeps turning with the wheels.
            set_parameter(stack, "homemy_sim_base", "imu_silent", True)
            bench.spin_until(lambda: not bench.yaw["ready"], 10, "gyro loss noticed", command=(0.0, 0.4))
            bench.spin(2.0, command=(0.0, 0.4))
            assert bench.odom_rate["/odom"] > 0.3, bench.odom_rate
            bench.spin(1.0)
            set_parameter(stack, "homemy_sim_base", "imu_silent", False)
            bench.spin_until(lambda: bench.yaw["ready"], 15, "gyro back")
        finally:
            bench.close()
