#!/usr/bin/env python3
"""Stand-in for the lifecycle manager. Simulation only.

Publishes the lifecycle state as text, latched and once per second. The state
can be changed at runtime, for example to test a fault:

    ros2 param set /homemy_lifecycle_stub state FAULT
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

LATCHED = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class LifecycleStub(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("homemy_lifecycle_stub", **node_options)
        self.declare_parameter("state_topic", "/homemy/lifecycle/state")
        self.declare_parameter("state", "READY")
        self.declare_parameter("period_s", 1.0)
        self.publisher = self.create_publisher(
            String, self.get_parameter("state_topic").value, LATCHED
        )
        self.create_timer(float(self.get_parameter("period_s").value), self._publish)
        self.get_logger().warning("SIMULATION: Lebenszyklus-Zustand ist vorgegeben.")
        self._publish()

    def _publish(self) -> None:
        self.publisher.publish(String(data=str(self.get_parameter("state").value)))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = LifecycleStub()
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
