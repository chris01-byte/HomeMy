#!/usr/bin/env python3
"""Stand-in for SLAM: a synthetic map that grows while mapping mode is active.

Simulation only. On the robot, SLAM publishes ``/map`` instead.

* Before the first mapping run nothing is published, as on a new robot.
* Each new mapping run starts a new, small map with a new fingerprint.
* While mapping mode is active and the controller is being used, more of the
  apartment becomes known every ``growth_period_s``.
* After the run the last map stays published, so that it can be saved.
"""

from __future__ import annotations

import time
from typing import Optional

from nav_msgs.msg import OccupancyGrid
import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_sensor_data,
)
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool

from homemy_simulation import test_apartment

LATCHED = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class SyntheticMap(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("homemy_synthetic_map", **node_options)
        self.declare_parameter("map_topic", "/map")
        self.declare_parameter("active_topic", "/homemy/mapping_mode/active")
        self.declare_parameter("joy_topic", "/joy")
        self.declare_parameter("frame_id", "map")
        self.declare_parameter("start_columns", 14)
        self.declare_parameter("growth_columns", 4)
        self.declare_parameter("growth_period_s", 1.0)
        self.declare_parameter("input_timeout_s", 1.0)
        self.declare_parameter("republish_period_s", 2.0)
        self.declare_parameter("initial_map", False)

        value = lambda name: self.get_parameter(name).value  # noqa: E731
        self.frame_id = str(value("frame_id"))
        self.start_columns = int(value("start_columns"))
        self.growth_columns = int(value("growth_columns"))
        self.growth_period_s = float(value("growth_period_s"))
        self.input_timeout_s = float(value("input_timeout_s"))
        self.republish_period_s = float(value("republish_period_s"))

        self.active = False
        self.revision = 0
        self.reveal_columns: Optional[int] = None
        self.have_map = bool(value("initial_map"))
        self.last_input_at = 0.0
        self.last_growth_at = 0.0
        self.last_publish_at = 0.0
        self.load_time = self.get_clock().now().to_msg()

        self.map_publisher = self.create_publisher(OccupancyGrid, value("map_topic"), LATCHED)
        self.create_subscription(Bool, value("active_topic"), self._on_active, LATCHED)
        self.create_subscription(Joy, value("joy_topic"), self._on_joy, qos_profile_sensor_data)
        self.create_timer(0.1, self._on_tick)
        self.get_logger().warning("SIMULATION: synthetische Karte, keine echten Sensordaten.")
        if self.have_map:
            self._publish()

    def _on_active(self, message: Bool) -> None:
        if message.data and not self.active:
            self.revision += 1
            self.reveal_columns = self.start_columns
            self.have_map = True
            self.load_time = self.get_clock().now().to_msg()
            self.last_growth_at = time.monotonic()
            self.get_logger().info(f"Neue Kartierfahrt {self.revision} beginnt.")
            self.active = True
            self._publish()
        elif not message.data and self.active:
            self.active = False
            self.get_logger().info("Kartierfahrt beendet; letzte Karte bleibt veröffentlicht.")
            self._publish()

    def _on_joy(self, message: Joy) -> None:
        if any(abs(axis) > 0.2 for axis in message.axes) or any(message.buttons):
            self.last_input_at = time.monotonic()

    def _on_tick(self) -> None:
        now = time.monotonic()
        driving = now - self.last_input_at <= self.input_timeout_s
        if (
            self.active
            and driving
            and self.reveal_columns is not None
            and now - self.last_growth_at >= self.growth_period_s
        ):
            self.last_growth_at = now
            self.reveal_columns += self.growth_columns
            if self.reveal_columns >= test_apartment.WIDTH:
                self.reveal_columns = None
            self._publish()
        elif self.have_map and now - self.last_publish_at >= self.republish_period_s:
            self._publish()

    def _publish(self) -> None:
        if not self.have_map:
            return
        message = OccupancyGrid()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self.frame_id
        message.info.map_load_time = self.load_time
        message.info.resolution = test_apartment.RESOLUTION
        message.info.width = test_apartment.WIDTH
        message.info.height = test_apartment.HEIGHT
        message.info.origin.position.x = test_apartment.ORIGIN[0]
        message.info.origin.position.y = test_apartment.ORIGIN[1]
        message.info.origin.position.z = test_apartment.ORIGIN[2]
        message.info.origin.orientation.w = 1.0
        message.data = test_apartment.build_cells(self.revision, self.reveal_columns)
        self.map_publisher.publish(message)
        self.last_publish_at = time.monotonic()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = SyntheticMap()
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
