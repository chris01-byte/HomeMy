"""The real drive driver against simulated ESS23-RS motors, on its own.

Commissioning step H5 in simulation (contracts/hardware/drivebase-commissioning.md):
the delivered configuration moves nothing; unlocked against the simulated
motors the driver drives, stops when commands stop, refuses invalid
commands, and survives a cut bus and a jump of the encoder counters.

Everything is simulated: no hardware.
"""

from __future__ import annotations

import json
import math
import random
import time

import pytest
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.executors import SingleThreadedExecutor
from std_msgs.msg import String

from e2e_support import launched_plain, set_parameter


class Bench:
    def __init__(self, stack) -> None:
        self.stack = stack
        self.node = stack["node"]
        self.executor = SingleThreadedExecutor(context=stack["context"])
        self.executor.add_node(self.node)
        self.drive_state = None
        self.sim = None
        self.truth = []  # (time, x, y, yaw)
        self.odom = None
        self.node.create_subscription(String, "/homemy/drivebase/state_json", self._setter("drive_state"), 10)
        self.node.create_subscription(String, "/homemy/sim/status_json", self._setter("sim"), 10)
        self.node.create_subscription(PoseStamped, "/homemy/sim/ground_truth", self._on_truth, 10)
        self.node.create_subscription(Odometry, "/odom", self._on_odom, 10)
        self.commands = self.node.create_publisher(Twist, "/cmd_vel", 1)

    def _setter(self, name):
        def callback(message):
            setattr(self, name, json.loads(message.data))
        return callback

    def _on_truth(self, message):
        q = message.pose.orientation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self.truth.append((time.monotonic(), message.pose.position.x, message.pose.position.y, yaw))
        del self.truth[:-3000]

    def _on_odom(self, message):
        self.odom = (message.pose.pose.position.x, message.pose.pose.position.y, message.twist.twist.linear.x)

    def spin(self, seconds, command=None):
        """Spin; with a command, publish it at 20 Hz like the motion gate."""

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
        raise AssertionError(f"not reached in {timeout:.0f} s: {what}; drive state: {self.drive_state}")

    def moved(self, seconds):
        """Distance and yaw change over the last ``seconds``."""

        now = time.monotonic()
        points = [p for p in self.truth if p[0] >= now - seconds]
        assert len(points) >= 2, "no ground truth"
        distance = math.hypot(points[-1][1] - points[0][1], points[-1][2] - points[0][2])
        yaw = math.atan2(math.sin(points[-1][3] - points[0][3]), math.cos(points[-1][3] - points[0][3]))
        return distance, yaw

    def close(self):
        self.executor.remove_node(self.node)
        self.executor.shutdown()


def launch_arguments(unlocked: bool):
    return [f"unlocked:={'true' if unlocked else 'false'}", f"sim_id:=test_{random.randint(0, 10**9)}"]


def test_delivered_configuration_sends_nothing_to_the_motors():
    with launched_plain("drivebase_sim.launch.py", launch_arguments(False)) as stack:
        bench = Bench(stack)
        try:
            bench.spin_until(lambda: bench.drive_state is not None and bench.sim is not None, 30, "driver and test stand up")
            assert bench.drive_state["dry_run"] is True
            assert bench.drive_state["allow_rs485"] is False
            bench.spin(3.0, command=(0.2, 0.3))
            bench.spin(1.0)
            assert bench.sim["travel_m"] == 0.0
            assert bench.sim["bus_requests"] == 0  # not a single byte on the bus
            assert bench.drive_state["rs485_ready"] is False
        finally:
            bench.close()


def test_unlocked_driver_drives_stops_and_survives_faults():
    with launched_plain("drivebase_sim.launch.py", launch_arguments(True)) as stack:
        bench = Bench(stack)
        try:
            bench.spin_until(
                lambda: bench.drive_state is not None and bench.drive_state["rs485_ready"]
                and bench.drive_state["encoder_feedback_ok"], 40, "driver connected to the simulated motors")

            # Straight ahead: the commanded speed arrives at the wheels.
            bench.spin(3.0, command=(0.20, 0.0))
            distance, yaw = bench.moved(1.0)
            assert 0.17 <= distance <= 0.22, distance
            assert abs(yaw) < 0.03
            assert bench.odom[2] == pytest.approx(0.20, abs=0.02)

            # No more commands: the driver's watchdog stops the motors.
            bench.spin(1.0)
            bench.spin(1.0)
            assert bench.moved(1.0)[0] < 0.005

            # Turning left on the spot: signs and geometry.
            bench.spin(3.0, command=(0.0, 0.5))
            distance, yaw = bench.moved(1.0)
            assert 0.40 <= yaw <= 0.55, yaw  # counter-clockwise, positive
            assert distance < 0.02
            bench.spin(1.5)

            # A command that is not a number is refused and stops the robot.
            bench.spin(1.0, command=(0.15, 0.0))
            bench.spin(1.5, command=(math.nan, 0.0))
            assert bench.moved(0.5)[0] < 0.005
            assert bench.drive_state["invalid_cmd_count"] >= 1

            # The bus is cut while driving. The driver notices and reports it.
            # It cannot reach the motors any more: they keep turning, which is
            # the known gap that the hardware emergency stop covers.
            bench.spin(1.5, command=(0.15, 0.0))
            set_parameter(stack, "homemy_sim_base", "bus_silent", True)
            bench.spin_until(lambda: not bench.drive_state["rs485_ready"] or not bench.drive_state["encoder_feedback_ok"],
                             5, "driver notices the cut bus", command=(0.15, 0.0))
            bench.spin(1.0)
            assert bench.moved(1.0)[0] > 0.05  # still rolling: nothing can stop it by software
            # The bus returns: the driver reconnects, and its first act is a stop.
            set_parameter(stack, "homemy_sim_base", "bus_silent", False)
            bench.spin_until(lambda: bench.drive_state["rs485_ready"] and bench.drive_state["encoder_feedback_ok"],
                             15, "driver reconnects")
            bench.spin(1.5)
            assert bench.moved(1.0)[0] < 0.005

            # The encoder counters jump, as after a reset of a motor controller.
            # The odometry must not jump with them.
            before = bench.odom[:2]
            set_parameter(stack, "homemy_sim_base", "encoder_jump_counts", 500000)
            bench.spin(3.0)
            after = bench.odom[:2]
            assert math.hypot(after[0] - before[0], after[1] - before[1]) < 0.02
            assert bench.drive_state["encoder_rejected_updates"] + bench.drive_state["encoder_rebases"] >= 1
            # And driving works again afterwards.
            bench.spin_until(lambda: bench.drive_state["encoder_feedback_ok"], 10, "encoder feedback healthy again")
            bench.spin(3.0, command=(0.20, 0.0))
            assert bench.moved(1.0)[0] >= 0.15
            assert bench.sim["bus_crc_errors"] == 0
        finally:
            bench.close()
