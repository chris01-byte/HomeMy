"""ROS node of the motion gate.

Subscribes to every input of contracts/ros/motion-gate.md, decides with
gate_core and protection_core, and publishes the drive command on
``/cmd_vel`` at a fixed rate: the gated command when open, zero otherwise.
The fixed rate keeps the drive watchdog fed with an explicit zero.
"""

from __future__ import annotations

import json
import math
import time
from typing import Optional, Tuple

import numpy as np
import rclpy
import yaml
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_sensor_data,
)
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String
from tf2_ros import Buffer, TransformException, TransformListener

from homemy_motion_gate.gate_core import (
    GateConfig,
    GateInputs,
    ModeLimits,
    MotionGate,
    Stamped,
)
from homemy_motion_gate.protection_core import FootprintGuard, Outline, scan_to_points

LATCHED = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


def load_outline(geometry_file: str) -> Outline:
    with open(geometry_file, encoding="utf-8") as handle:
        geometry = yaml.safe_load(handle)
    outline = geometry["base_outline"]
    return Outline(
        x_min=float(outline["x_min"]),
        x_max=float(outline["x_max"]),
        y_half=float(outline["y_half"]),
        corner_radius=float(outline["corner_radius"]),
    )


class MotionGateNode(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("motion_gate", **node_options)
        declare = self.declare_parameter
        declare("geometry_file", "")
        declare("base_frame", "base_link")
        declare("output_topic", "/cmd_vel")
        declare("status_topic", "/homemy/motion_gate/status_json")
        declare("teleop_topic", "/homemy/cmd_vel/teleop")
        declare("nav_topic", "/homemy/cmd_vel/nav")
        declare("mapping_active_topic", "/homemy/mapping_mode/active")
        declare("mission_drive_active_topic", "/homemy/mission/drive_active")
        declare("lifecycle_state_topic", "/homemy/lifecycle/state")
        declare("estop_topic", "/homemy/safety/estop")
        declare("localization_ready_topic", "/homemy/localization/ready")
        declare("scan_topic", "/scan_masked")
        declare("publish_rate_hz", 20.0)
        declare("status_period_s", 0.5)
        declare("mapping_max_linear_mps", 0.20)
        declare("mapping_max_angular_rps", 0.70)
        declare("mission_max_linear_mps", 0.25)
        declare("mission_max_angular_rps", 0.60)
        declare("mode_timeout_s", 1.5)
        declare("lifecycle_timeout_s", 3.0)
        declare("estop_timeout_s", 1.0)
        declare("command_timeout_s", 0.25)
        declare("localization_timeout_s", 1.0)
        declare("scan_timeout_s", 0.3)
        declare("clear_time_s", 0.5)
        declare("protection_margin_m", 0.05)
        declare("protection_horizon_s", 1.0)
        declare("protection_min_lookahead_m", 0.05)

        def value(name):
            return self.get_parameter(name).value

        geometry_file = str(value("geometry_file"))
        if not geometry_file:
            raise ValueError("geometry_file is required: the outline comes from the robot model")
        self.guard = FootprintGuard(
            load_outline(geometry_file),
            margin_m=float(value("protection_margin_m")),
            horizon_s=float(value("protection_horizon_s")),
            min_lookahead_m=float(value("protection_min_lookahead_m")),
        )
        self.gate = MotionGate(
            GateConfig(
                mapping_limits=ModeLimits(
                    float(value("mapping_max_linear_mps")), float(value("mapping_max_angular_rps"))
                ),
                mission_limits=ModeLimits(
                    float(value("mission_max_linear_mps")), float(value("mission_max_angular_rps"))
                ),
                mode_timeout_s=float(value("mode_timeout_s")),
                lifecycle_timeout_s=float(value("lifecycle_timeout_s")),
                estop_timeout_s=float(value("estop_timeout_s")),
                command_timeout_s=float(value("command_timeout_s")),
                localization_timeout_s=float(value("localization_timeout_s")),
                scan_timeout_s=float(value("scan_timeout_s")),
                clear_time_s=float(value("clear_time_s")),
            )
        )
        self.base_frame = str(value("base_frame"))
        self.inputs = GateInputs()
        self.points = np.empty((0, 2))
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.sensor_pose: Optional[Tuple[str, float, float, float]] = None
        self.last_summary = None
        self.last_status_at = 0.0
        self.status_period_s = float(value("status_period_s"))

        self.output = self.create_publisher(Twist, str(value("output_topic")), 10)
        self.status = self.create_publisher(String, str(value("status_topic")), LATCHED)

        self.create_subscription(Twist, str(value("teleop_topic")), self._on_teleop, 10)
        self.create_subscription(Twist, str(value("nav_topic")), self._on_nav, 10)
        self.create_subscription(Bool, str(value("mapping_active_topic")), self._setter("mapping_active"), LATCHED)
        self.create_subscription(
            Bool, str(value("mission_drive_active_topic")), self._setter("mission_drive_active"), LATCHED
        )
        self.create_subscription(String, str(value("lifecycle_state_topic")), self._on_lifecycle, LATCHED)
        self.create_subscription(Bool, str(value("estop_topic")), self._setter("estop_pressed"), 10)
        self.create_subscription(
            Bool, str(value("localization_ready_topic")), self._setter("localization_ready"), 10
        )
        self.create_subscription(LaserScan, str(value("scan_topic")), self._on_scan, qos_profile_sensor_data)

        rate = float(value("publish_rate_hz"))
        if not (math.isfinite(rate) and rate > 0):
            raise ValueError("publish_rate_hz must be positive")
        self.create_timer(1.0 / rate, self._tick)

    @staticmethod
    def _now() -> float:
        return time.monotonic()

    def _setter(self, field_name):
        def callback(message: Bool) -> None:
            setattr(self.inputs, field_name, Stamped(bool(message.data), self._now()))

        return callback

    def _on_lifecycle(self, message: String) -> None:
        self.inputs.lifecycle_state = Stamped(str(message.data).strip(), self._now())

    def _on_teleop(self, message: Twist) -> None:
        self.inputs.teleop_command = Stamped((message.linear.x, message.angular.z), self._now())

    def _on_nav(self, message: Twist) -> None:
        self.inputs.nav_command = Stamped((message.linear.x, message.angular.z), self._now())

    def _sensor_pose(self, frame: str) -> Optional[Tuple[float, float, float]]:
        if self.sensor_pose is not None and self.sensor_pose[0] == frame:
            return self.sensor_pose[1:]
        try:
            transform = self.tf_buffer.lookup_transform(self.base_frame, frame, rclpy.time.Time())
        except TransformException:
            return None
        t = transform.transform.translation
        q = transform.transform.rotation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self.sensor_pose = (frame, t.x, t.y, yaw)
        return self.sensor_pose[1:]

    def _on_scan(self, message: LaserScan) -> None:
        pose = self._sensor_pose(message.header.frame_id)
        if pose is None:
            # Without the sensor transform the scan cannot be used: treat as missing.
            return
        self.points = scan_to_points(
            np.asarray(message.ranges, dtype=float),
            message.angle_min,
            message.angle_increment,
            message.range_min,
            message.range_max,
            (pose[0], pose[1]),
            pose[2],
        )
        self.inputs.scan_received_at = self._now()

    def _protection(self, v: float, w: float):
        result = self.guard.check(v, w, self.points)
        return result.allowed, result.reason

    def _tick(self) -> None:
        now = self._now()
        decision = self.gate.step(self.inputs, now, self._protection)
        twist = Twist()
        twist.linear.x = float(decision.command[0])
        twist.angular.z = float(decision.command[1])
        self.output.publish(twist)

        summary = (decision.mode, decision.open, decision.reasons)
        if summary != self.last_summary or now - self.last_status_at >= self.status_period_s:
            if summary != self.last_summary:
                state = "open" if decision.open else "closed: " + ", ".join(decision.reasons)
                self.get_logger().info(f"Motion gate {decision.mode}, {state}.")
            self.last_summary = summary
            self.last_status_at = now
            payload = {
                "schema_version": 1,
                "mode": decision.mode,
                "open": decision.open,
                "reasons": list(decision.reasons),
                "command": {"linear_mps": decision.command[0], "angular_rps": decision.command[1]},
                "time": time.time(),
            }
            self.status.publish(String(data=json.dumps(payload, allow_nan=False)))

    def stop(self) -> None:
        """Publish one explicit zero, e.g. before shutdown."""

        if rclpy.ok(context=self.context):
            try:
                self.output.publish(Twist())
            except Exception:  # noqa: BLE001 - shutdown race; the drive watchdog stops anyway
                pass


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MotionGateNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
