"""ROS node: puts the raw LiDAR scan on a fixed, robot-aligned angle grid.

After Amadeus ``scan_vereinheitlichen.py`` (Roboter_ws 05439c7).

Measured on Amadeus (424 scans, robot standing): the STL-27L delivers
between 2146 and 2176 beams per revolution, 19 different counts; the most
frequent one covers only a quarter of the scans. slam_toolbox drops every
scan whose count differs from the first one, without a warning in the ROS
log. This node therefore sits between the vendor driver and every consumer.
The vendor driver stays unchanged.

HomeMy: the output is in ``lidar_link``, 0 = straight ahead. The yaw offset
of the device is a commissioning result (LiDAR contract step L3) and is
coupled with the driver's ``laser_scan_dir``.
"""

from __future__ import annotations

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

from homemy_lidar_bringup.scan_grid import FULL_TURN, grid_indices, to_grid


class ScanNormalize(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("scan_normalize", **node_options)
        self.declare_parameter("input_topic", "/scan_raw")
        self.declare_parameter("output_topic", "/scan")
        self.declare_parameter("output_frame", "lidar_link")
        # 2160 lies inside the observed span 2146..2176 and close to the nominal
        # resolution of the STL-27L (360 / 0.167 = 2156).
        self.declare_parameter("beams", 2160)
        self.declare_parameter("yaw_offset_deg", 0.0)
        # Lock: an alignment nobody has checked must not reach the consumers.
        self.declare_parameter("alignment_confirmed", False)
        self.declare_parameter("report_interval_s", 30.0)

        self.beams = int(self.get_parameter("beams").value)
        if self.beams < 2:
            raise ValueError("beams must be at least 2")
        yaw_deg = float(self.get_parameter("yaw_offset_deg").value)
        if not (math.isfinite(yaw_deg) and -180.0 <= yaw_deg <= 180.0):
            raise ValueError("yaw_offset_deg must be between -180 and 180")
        self.yaw_offset = math.radians(yaw_deg)
        self.output_frame = str(self.get_parameter("output_frame").value)
        self.report_interval = float(self.get_parameter("report_interval_s").value)

        self.confirmed = bool(self.get_parameter("alignment_confirmed").value)
        output_topic = str(self.get_parameter("output_topic").value)
        if not self.confirmed:
            output_topic += "_unconfirmed"
        self.output_topic = output_topic
        self.publisher = self.create_publisher(LaserScan, output_topic, qos_profile_sensor_data)
        self.create_subscription(
            LaserScan, str(self.get_parameter("input_topic").value), self._on_scan, qos_profile_sensor_data
        )
        self._cache = {}
        self.seen = 0
        self.published = 0
        self.sizes = set()
        self._last_report = self.get_clock().now()
        self._last_warning = None
        self.get_logger().info(
            f"Normalising to {self.beams} beams in {self.output_frame}, yaw offset {yaw_deg:.2f} degrees, "
            f"output on {output_topic}."
        )
        if not self.confirmed:
            self.get_logger().warning(
                "The scan alignment is not confirmed (alignment_confirmed: false). The scan is published "
                "only for checking; mapping, localization, and driving receive nothing."
            )

    def _mapping(self, message: LaserScan):
        key = (len(message.ranges), message.angle_min, message.angle_increment)
        if key not in self._cache:
            if len(self._cache) > 64:
                self._cache.clear()
            self._cache[key] = grid_indices(
                len(message.ranges), message.angle_min, message.angle_increment, self.beams, self.yaw_offset
            )
        return self._cache[key]

    def _on_scan(self, message: LaserScan) -> None:
        self.seen += 1
        self.sizes.add(len(message.ranges))
        try:
            index, valid = self._mapping(message)
        except ValueError as error:
            self._warn(f"Scan dropped: {error}.")
            return

        out = LaserScan()
        out.header.stamp = message.header.stamp
        out.header.frame_id = self.output_frame
        out.angle_min = -math.pi
        out.angle_increment = FULL_TURN / self.beams
        out.angle_max = out.angle_min + (self.beams - 1) * out.angle_increment
        # After re-ordering, the beam index no longer follows the time of measurement.
        out.time_increment = 0.0
        out.scan_time = message.scan_time
        out.range_min = message.range_min
        out.range_max = message.range_max
        out.ranges = to_grid(message.ranges, index, valid).tolist()
        if len(message.intensities) == len(message.ranges):
            out.intensities = to_grid(message.intensities, index, valid, 0.0).tolist()
        self.publisher.publish(out)
        self.published += 1
        self._report()

    def _warn(self, text: str) -> None:
        now = self.get_clock().now()
        if self._last_warning is None or (now - self._last_warning).nanoseconds > 5e9:
            self._last_warning = now
            self.get_logger().warning(text)

    def _report(self) -> None:
        if self.report_interval <= 0.0:
            return
        now = self.get_clock().now()
        if (now - self._last_report).nanoseconds < self.report_interval * 1e9:
            return
        self._last_report = now
        self.get_logger().info(
            f"{self.published}/{self.seen} scans normalised; input had {len(self.sizes)} different "
            f"beam counts ({min(self.sizes)}..{max(self.sizes)}), output is fixed at {self.beams}."
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ScanNormalize()
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
