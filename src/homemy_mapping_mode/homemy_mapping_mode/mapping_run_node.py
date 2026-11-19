"""Coordinates slam_toolbox with mapping mode.

- When mapping mode begins (its active flag rises), the map is reset and
  slam_toolbox takes measurements: every mapping run starts a new map.
- While mapping mode is off, slam_toolbox is paused. The last map stays
  published on /map, so the app can show and save it.
- When the mapping-mode signal is missing, slam_toolbox is paused too: no
  map changes without a known mapping run.

The coordinator only switches mapping on and off. It commands no motion.
The current pause state is read from slam_toolbox's parameter
``paused_new_measurements`` before every toggle, because the pause service
toggles instead of setting.
"""

from __future__ import annotations

import json
import time
from typing import Optional

import rclpy
from rcl_interfaces.srv import GetParameters
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from slam_toolbox.srv import Pause, Reset
from std_msgs.msg import Bool, String

LATCHED = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)


class MappingRunCoordinator(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("mapping_run_coordinator", **node_options)
        self.declare_parameter("active_topic", "/homemy/mapping_mode/active")
        self.declare_parameter("status_topic", "/homemy/mapping_run/status_json")
        self.declare_parameter("slam_node", "/slam_toolbox")
        self.declare_parameter("active_timeout_s", 2.0)
        self.declare_parameter("period_s", 0.5)
        slam = str(self.get_parameter("slam_node").value).rstrip("/")
        self.active_timeout_s = float(self.get_parameter("active_timeout_s").value)

        self.reset_client = self.create_client(Reset, f"{slam}/reset")
        self.pause_client = self.create_client(Pause, f"{slam}/pause_new_measurements")
        self.params_client = self.create_client(GetParameters, f"{slam}/get_parameters")
        self.status_pub = self.create_publisher(String, str(self.get_parameter("status_topic").value), LATCHED)
        self.create_subscription(Bool, str(self.get_parameter("active_topic").value), self._on_active, LATCHED)
        self.create_timer(float(self.get_parameter("period_s").value), self._reconcile)

        self.active: Optional[bool] = None
        self.active_at: Optional[float] = None
        self.new_run_pending = False
        self.busy = False
        self.paused: Optional[bool] = None
        self.runs_started = 0
        self.last_status = None

    def _on_active(self, message: Bool) -> None:
        now = time.monotonic()
        value = bool(message.data)
        if value and self.active is False:
            self.new_run_pending = True
        self.active = value
        self.active_at = now

    def _wanted_measuring(self) -> bool:
        fresh = self.active_at is not None and time.monotonic() - self.active_at <= self.active_timeout_s
        return bool(fresh and self.active)

    def _reconcile(self) -> None:
        self._publish_status()
        if self.busy:
            return
        if not (self.reset_client.service_is_ready() and self.pause_client.service_is_ready()
                and self.params_client.service_is_ready()):
            self.paused = None
            return
        if self.new_run_pending and self._wanted_measuring():
            self.new_run_pending = False
            self.busy = True
            request = Reset.Request()
            request.pause_new_measurements = False
            self.reset_client.call_async(request).add_done_callback(self._after_reset)
            return
        self.busy = True
        request = GetParameters.Request()
        request.names = ["paused_new_measurements"]
        self.params_client.call_async(request).add_done_callback(self._after_read)

    def _after_reset(self, future) -> None:
        self.busy = False
        if future.result() is None:
            self.get_logger().error("slam_toolbox reset failed; trying again.")
            self.new_run_pending = True
            return
        self.runs_started += 1
        self.paused = False
        self.get_logger().info(f"Mapping run {self.runs_started}: new map, measuring.")

    def _after_read(self, future) -> None:
        response = future.result()
        if response is None or not response.values:
            self.busy = False
            self.paused = None
            return
        self.paused = bool(response.values[0].bool_value)
        wanted = self._wanted_measuring()
        if wanted == (not self.paused):
            self.busy = False
            return
        self.pause_client.call_async(Pause.Request()).add_done_callback(self._after_toggle)

    def _after_toggle(self, future) -> None:
        self.busy = False
        if future.result() is None:
            self.get_logger().error("slam_toolbox pause toggle failed.")
            return
        self.paused = not self.paused if self.paused is not None else None
        self.get_logger().info("slam_toolbox paused." if self.paused else "slam_toolbox measuring.")

    def _publish_status(self) -> None:
        status = {
            "slam_available": self.paused is not None,
            "measuring": self.paused is False,
            "mapping_mode_active": self._wanted_measuring(),
            "runs_started": self.runs_started,
        }
        if status != self.last_status:
            self.last_status = status
            self.status_pub.publish(String(data=json.dumps(status)))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MappingRunCoordinator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
