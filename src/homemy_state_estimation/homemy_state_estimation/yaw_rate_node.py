"""ROS node: the chassis yaw rate from the gyro, for the odometry.

In:  /imu/data_raw (sensor_msgs/Imu, sensor axes), wheel odometry (nav_msgs/Odometry)
Out: /imu/yaw_rate (sensor_msgs/Imu in base_link; only angular_velocity.z is meaningful)
     /homemy/imu/yaw_rate_status_json (std_msgs/String)

The node never commands anything. Without a learned bias, or with stale or
invalid input, it publishes no yaw rate at all.
"""

from __future__ import annotations

import json
import math

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu
from std_msgs.msg import String

from homemy_state_estimation.yaw_rate_core import YawRateAid, YawRateConfig


def stamp_seconds(stamp) -> float:
    return stamp.sec + stamp.nanosec * 1e-9


class YawRateNode(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("yaw_rate", **node_options)
        defaults = YawRateConfig()
        self.declare_parameter("imu_topic", "/imu/data_raw")
        self.declare_parameter("wheel_odom_topic", "/odom")
        self.declare_parameter("output_topic", "/imu/yaw_rate")
        self.declare_parameter("status_topic", "/homemy/imu/yaw_rate_status_json")
        self.declare_parameter("expected_imu_frame", "imu_link")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("yaw_rate_variance", 0.0004)
        names = [field for field in defaults.__dataclass_fields__]
        for name in names:
            self.declare_parameter(name, getattr(defaults, name))
        self.aid = YawRateAid(YawRateConfig(**{name: self.get_parameter(name).value for name in names}))
        self.expected_frame = str(self.get_parameter("expected_imu_frame").value)
        self.base_frame = str(self.get_parameter("base_frame").value)
        self.variance = float(self.get_parameter("yaw_rate_variance").value)
        if not (math.isfinite(self.variance) and self.variance > 0.0):
            raise ValueError("yaw_rate_variance must be positive and finite")
        self.published = 0
        self.wrong_frame = 0

        self.publisher = self.create_publisher(
            Imu, str(self.get_parameter("output_topic").value), qos_profile_sensor_data)
        self.status_pub = self.create_publisher(String, str(self.get_parameter("status_topic").value), 10)
        self.create_subscription(
            Imu, str(self.get_parameter("imu_topic").value), self._on_imu, qos_profile_sensor_data)
        self.create_subscription(
            Odometry, str(self.get_parameter("wheel_odom_topic").value), self._on_wheel, 20)
        self.create_timer(0.5, self._publish_status)
        self.get_logger().info(
            f"Yaw rate from sensor axis {self.aid.config.yaw_axis} with sign {self.aid.config.yaw_sign:+.0f}; "
            "no output until the bias is learned at standstill."
        )

    def _on_wheel(self, message: Odometry) -> None:
        self.aid.on_wheel(
            stamp_seconds(message.header.stamp), message.twist.twist.linear.x, message.twist.twist.angular.z)

    def _on_imu(self, message: Imu) -> None:
        if message.header.frame_id != self.expected_frame:
            self.wrong_frame += 1
            return
        rate = self.aid.on_imu(
            stamp_seconds(message.header.stamp),
            (message.angular_velocity.x, message.angular_velocity.y, message.angular_velocity.z),
        )
        if rate is None:
            return
        out = Imu()
        out.header.stamp = message.header.stamp
        out.header.frame_id = self.base_frame
        out.orientation.w = 1.0
        out.orientation_covariance[0] = -1.0  # no heading: the sensor has no absolute reference
        out.angular_velocity.z = rate
        out.angular_velocity_covariance[0] = 1e6  # roll and pitch rate are not provided
        out.angular_velocity_covariance[4] = 1e6
        out.angular_velocity_covariance[8] = self.variance
        out.linear_acceleration_covariance[0] = -1.0
        self.publisher.publish(out)
        self.published += 1

    def _publish_status(self) -> None:
        now = self.get_clock().now().nanoseconds * 1e-9
        payload = dict(self.aid.status(now), schema_version=1, published=self.published,
                       wrong_frame=self.wrong_frame, actuator_output=False)
        self.status_pub.publish(String(data=json.dumps(payload, allow_nan=False)))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = YawRateNode()
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
