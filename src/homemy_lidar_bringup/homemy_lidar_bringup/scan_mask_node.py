"""ROS node: republishes the scan with the blind sectors set to NaN.

The sector bearings are given at the LiDAR axis in the robot-aligned
direction. This node assumes that the scan's frame is aligned that way
(lidar_link of homemy_description). The driver's own zero direction and
rotation sense are fixed in commissioning step L3; until then the real
scan must not be used for motion.
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

from homemy_lidar_bringup.scan_mask_core import apply_mask, blind_degrees, build_sectors


class ScanMask(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("scan_mask", **node_options)
        self.declare_parameter("input_topic", "/scan")
        self.declare_parameter("output_topic", "/scan_masked")
        self.declare_parameter("sector_start_deg", [0.0])
        self.declare_parameter("sector_end_deg", [0.0])
        self.declare_parameter("margin_deg", 1.5)
        starts = list(self.get_parameter("sector_start_deg").value)
        ends = list(self.get_parameter("sector_end_deg").value)
        self.sectors = build_sectors(starts, ends, float(self.get_parameter("margin_deg").value))
        self.publisher = self.create_publisher(
            LaserScan, str(self.get_parameter("output_topic").value), qos_profile_sensor_data
        )
        self.create_subscription(
            LaserScan, str(self.get_parameter("input_topic").value), self._on_scan, qos_profile_sensor_data
        )
        self.get_logger().info(
            f"Masking {len(self.sectors)} blind sectors, {blind_degrees(self.sectors):.1f} degrees in total."
        )

    def _on_scan(self, message: LaserScan) -> None:
        masked = apply_mask(message.ranges, message.angle_min, message.angle_increment, self.sectors)
        out = LaserScan()
        out.header = message.header
        out.angle_min = message.angle_min
        out.angle_max = message.angle_max
        out.angle_increment = message.angle_increment
        out.time_increment = message.time_increment
        out.scan_time = message.scan_time
        out.range_min = message.range_min
        out.range_max = message.range_max
        out.ranges = masked.tolist()
        out.intensities = list(message.intensities)
        self.publisher.publish(out)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ScanMask()
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
