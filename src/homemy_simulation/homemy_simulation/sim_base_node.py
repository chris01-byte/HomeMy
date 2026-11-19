#!/usr/bin/env python3
"""The HomeMy test stand: simulated drive, LiDAR, odometry, and IMU. Simulation only.

Replaces only the devices; everything behind them is the real HomeMy code.
Modelled on the Amadeus test stand (``Anlage`` in tools/simulation/
sh_robustheit.py, roboter_ws 940a748), changed for HomeMy:

- ``/cmd_vel`` (geometry_msgs/Twist) drives the robot, with the 0.25 s
  watchdog of the real drive: without a fresh command it brakes to zero;
- ``/scan`` (sensor_msgs/LaserScan, frame ``lidar_link``) at 10 Hz, 360
  degrees counter-clockwise from -pi, with self-returns from the struts and
  slot webs, max range as +inf, and optional noise;
- ``/odom`` and TF odom -> base_link at 50 Hz, with optional scale drift;
- ``/imu/data`` (sensor_msgs/Imu, frame ``imu_link``): yaw rate with bias and
  noise, like the HWT601 yaw-rate input; no orientation;
- ``/joint_states`` for the two wheel joints;
- for tests only: ``/homemy/sim/ground_truth`` (PoseStamped in frame
  ``world``) and ``/homemy/sim/status_json`` (collision, clearance, travel).

The physics runs in its own thread, apart from the ROS executor, so that no
sensor timer can starve it and it cannot starve the sensors (Amadeus lesson:
a starved sensor timer caused constant navigation restarts). Wall-clock
time; no /clock.
"""

from __future__ import annotations

import json
import math
import threading
import time

import numpy as np
import rclpy
import yaml
from geometry_msgs.msg import PoseStamped, TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu, JointState, LaserScan
from std_msgs.msg import String
from tf2_ros import TransformBroadcaster

from homemy_simulation.world import FloorPlanWorld, RobotGeometry


def yaw_to_quaternion(yaw: float):
    return 0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)


class SimBase(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("homemy_sim_base", **node_options)
        declare = self.declare_parameter
        declare("world_file", "")
        declare("geometry_file", "")
        declare("cmd_topic", "/cmd_vel")
        declare("cmd_timeout_s", 0.25)
        declare("physics_rate_hz", 100.0)
        declare("odom_rate_hz", 50.0)
        declare("scan_rate_hz", 10.0)
        declare("beams", 720)
        declare("range_max_m", 25.0)
        declare("lidar_noise_m", 0.01)
        declare("odom_yaw_scale_error", 0.02)
        declare("odom_length_scale_error", -0.01)
        declare("imu_bias_rps", 0.001)
        declare("imu_noise_rps", 0.002)
        declare("seed", 7)

        def value(name):
            return self.get_parameter(name).value

        world_file, geometry_file = str(value("world_file")), str(value("geometry_file"))
        if not world_file or not geometry_file:
            raise ValueError("world_file and geometry_file are required")
        with open(geometry_file, encoding="utf-8") as handle:
            geometry = yaml.safe_load(handle)
        self.geometry = RobotGeometry.from_yaml_dict(geometry)
        self.wheel_radius = float(geometry["drive_wheels"]["radius"])
        self.world = FloorPlanWorld.from_file(world_file, self.geometry)
        self.cmd_timeout_s = float(value("cmd_timeout_s"))
        self.beams = int(value("beams"))
        self.range_max = float(value("range_max_m"))
        self.lidar_noise = float(value("lidar_noise_m"))
        self.yaw_scale = 1.0 + float(value("odom_yaw_scale_error"))
        self.length_scale = 1.0 + float(value("odom_length_scale_error"))
        self.imu_bias = float(value("imu_bias_rps"))
        self.imu_noise = float(value("imu_noise_rps"))
        self.scan_period = 1.0 / float(value("scan_rate_hz"))
        self.rng = np.random.default_rng(int(value("seed")))

        self.lock = threading.Lock()
        self.command = (0.0, 0.0)
        self.command_at = None
        self.odom_pose = np.zeros(3)
        self.last_physics = time.monotonic()
        self.max_gap = 0.0

        self.physics_period = 1.0 / float(value("physics_rate_hz"))
        self.ticks = 0

        self.create_subscription(Twist, str(value("cmd_topic")), self._on_cmd, 10)
        self.scan_pub = self.create_publisher(LaserScan, "/scan", qos_profile_sensor_data)
        self.odom_pub = self.create_publisher(Odometry, "/odom", 10)
        self.imu_pub = self.create_publisher(Imu, "/imu/data", qos_profile_sensor_data)
        self.joint_pub = self.create_publisher(JointState, "/joint_states", 10)
        self.truth_pub = self.create_publisher(PoseStamped, "/homemy/sim/ground_truth", 10)
        self.status_pub = self.create_publisher(String, "/homemy/sim/status_json", 10)
        self.tf = TransformBroadcaster(self)

        self.create_timer(1.0 / float(value("odom_rate_hz")), self._odometry)
        self.create_timer(self.scan_period, self._scan)
        self.create_timer(0.5, self._status)
        self.running = True
        self.physics_thread = threading.Thread(target=self._physics_loop, daemon=True)
        self.physics_thread.start()
        self.get_logger().warning(
            f"SIMULATION: test stand with world {world_file}; start pose {list(self.world.start)}."
        )

    def _on_cmd(self, message: Twist) -> None:
        command = (float(message.linear.x), float(message.angular.z))
        if not all(math.isfinite(c) for c in command):
            self.get_logger().error("Non-finite drive command ignored.")
            return
        with self.lock:
            self.command = command
            self.command_at = time.monotonic()

    def _physics_loop(self) -> None:
        next_tick = time.monotonic()
        while self.running:
            next_tick += self.physics_period
            self._physics()
            delay = next_tick - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_tick = time.monotonic()

    def destroy_node(self):
        self.running = False
        if self.physics_thread.is_alive():
            self.physics_thread.join(timeout=1.0)
        return super().destroy_node()

    def _physics(self) -> None:
        now = time.monotonic()
        with self.lock:
            span = now - self.last_physics
            self.last_physics = now
            self.max_gap = max(self.max_gap, span)
            fresh = self.command_at is not None and now - self.command_at <= self.cmd_timeout_s
            command = self.command if fresh else (0.0, 0.0)
            before = self.world.pose.copy()
            self.world.integrate_span(command, min(span, 0.5))
            after = self.world.pose.copy()
            # Odometry: the same motion seen through scale errors of the encoders.
            dx, dy = after[0] - before[0], after[1] - before[1]
            c, s = math.cos(before[2]), math.sin(before[2])
            forward = (c * dx + s * dy) * self.length_scale
            dyaw = math.atan2(math.sin(after[2] - before[2]), math.cos(after[2] - before[2])) * self.yaw_scale
            ox, oy, oyaw = self.odom_pose
            mid = oyaw + dyaw / 2.0
            self.odom_pose[:] = (ox + forward * math.cos(mid), oy + forward * math.sin(mid),
                                 math.atan2(math.sin(oyaw + dyaw), math.cos(oyaw + dyaw)))

    def _odometry(self) -> None:
        stamp = self.get_clock().now().to_msg()
        with self.lock:
            x, y, yaw = self.odom_pose
            v, w = self.world.velocity
            truth = self.world.pose.copy()
            wheels = self.world.wheel_angles.copy()
        qx, qy, qz, qw = yaw_to_quaternion(yaw)
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x, odom.pose.pose.position.y = float(x), float(y)
        odom.pose.pose.orientation.z, odom.pose.pose.orientation.w = qz, qw
        odom.twist.twist.linear.x = float(v) * self.length_scale
        odom.twist.twist.angular.z = float(w) * self.yaw_scale
        for i, variance in zip((0, 7, 35), (1e-3, 1e-3, 3e-3)):
            odom.pose.covariance[i] = variance
            odom.twist.covariance[i] = variance
        self.odom_pub.publish(odom)

        transform = TransformStamped()
        transform.header = odom.header
        transform.child_frame_id = "base_link"
        transform.transform.translation.x, transform.transform.translation.y = float(x), float(y)
        transform.transform.rotation.z, transform.transform.rotation.w = qz, qw
        self.tf.sendTransform(transform)

        imu = Imu()
        imu.header.stamp = stamp
        imu.header.frame_id = "imu_link"
        imu.orientation_covariance[0] = -1.0  # the HWT601 yaw input carries no absolute heading
        imu.angular_velocity.z = float(w + self.imu_bias + self.rng.normal(0.0, self.imu_noise))
        imu.angular_velocity_covariance[8] = self.imu_noise ** 2
        imu.linear_acceleration.z = 9.81
        self.imu_pub.publish(imu)

        self.ticks += 1
        if self.ticks % 2:
            return  # wheel joints and ground truth at half the odometry rate

        joints = JointState()
        joints.header.stamp = stamp
        joints.name = ["left_wheel_joint", "right_wheel_joint"]
        joints.position = [float(wheels[0] / self.wheel_radius), float(wheels[1] / self.wheel_radius)]
        self.joint_pub.publish(joints)

        pose = PoseStamped()
        pose.header.stamp = stamp
        pose.header.frame_id = "world"
        pose.pose.position.x, pose.pose.position.y = float(truth[0]), float(truth[1])
        _, _, tz, tw = yaw_to_quaternion(truth[2])
        pose.pose.orientation.z, pose.pose.orientation.w = tz, tw
        self.truth_pub.publish(pose)

    def _scan(self) -> None:
        with self.lock:
            angles, ranges = self.world.laser(self.beams, self.range_max, self.lidar_noise, self.rng)
        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = "lidar_link"
        scan.angle_min = float(angles[0])
        scan.angle_increment = float(2 * math.pi / self.beams)
        scan.angle_max = float(angles[-1])
        scan.scan_time = self.scan_period
        scan.time_increment = self.scan_period / self.beams
        scan.range_min = 0.03
        scan.range_max = self.range_max
        ranges = np.where(ranges >= self.range_max, np.inf, ranges)
        scan.ranges = ranges.astype(float).tolist()
        self.scan_pub.publish(scan)

    def _status(self) -> None:
        with self.lock:
            payload = {
                "collision": bool(self.world.collision),
                "minimum_clearance_m": None if math.isinf(self.world.minimum_clearance)
                else round(float(self.world.minimum_clearance), 4),
                "travel_m": round(float(self.world.travel), 3),
                "pose": [round(float(v), 4) for v in self.world.pose],
                "room": self.world.room_of(self.world.pose[:2]),
                "max_physics_gap_s": round(self.max_gap, 4),
            }
        self.status_pub.publish(String(data=json.dumps(payload)))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = SimBase()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
