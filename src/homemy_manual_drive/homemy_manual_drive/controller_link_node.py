"""ROS node: publishes whether the controller's radio link is up.

Reads the motion-sensor input device of the DualShock 4 and publishes
``/homemy/controller/link`` (std_msgs/Bool) at a fixed rate. True means a
motion report arrived within ``link_timeout_s``. The motion gate treats a
missing or stale message as "link down".

The node needs read access to /dev/input/event* (group ``input``).
"""

from __future__ import annotations

import os
import select
import threading
import time
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool

from homemy_manual_drive.controller_link import (
    DEFAULT_DEVICE_PATTERN,
    EventDecoder,
    LinkMonitor,
    ambiguous_motion_devices,
    find_motion_device,
    list_input_devices,
    read_available,
)


class ControllerLinkNode(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("controller_link", **node_options)
        self.declare_parameter("link_topic", "/homemy/controller/link")
        self.declare_parameter("device_name_pattern", DEFAULT_DEVICE_PATTERN)
        self.declare_parameter("link_timeout_s", 0.15)
        self.declare_parameter("publish_period_s", 0.05)
        self.declare_parameter("rescan_period_s", 1.0)
        self.declare_parameter("sys_class_input", "/sys/class/input")
        self.declare_parameter("dev_input", "/dev/input")

        def value(name):
            return self.get_parameter(name).value

        self.pattern = str(value("device_name_pattern"))
        self.sys_class_input = str(value("sys_class_input"))
        self.dev_input = str(value("dev_input"))
        self.rescan_period_s = float(value("rescan_period_s"))
        self.monitor = LinkMonitor(float(value("link_timeout_s")))
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.device_path: Optional[str] = None
        self.last_reported: Optional[bool] = None

        self.publisher = self.create_publisher(Bool, str(value("link_topic")), 10)
        self.create_timer(float(value("publish_period_s")), self._publish)
        self.reader = threading.Thread(target=self._read_loop, daemon=True)
        self.reader.start()

    def _read_loop(self) -> None:
        while not self.stop_event.is_set():
            devices = list_input_devices(self.sys_class_input, self.dev_input)
            if ambiguous_motion_devices(devices, self.pattern):
                self.get_logger().error(
                    "More than one controller motion device found; link stays down."
                )
                self.stop_event.wait(self.rescan_period_s)
                continue
            device = find_motion_device(devices, self.pattern)
            if device is None:
                self.stop_event.wait(self.rescan_period_s)
                continue
            self._follow(device.event_path)

    def _follow(self, path: str) -> None:
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        except OSError as error:
            self.get_logger().warning(f"Cannot open {path}: {error}")
            self.stop_event.wait(self.rescan_period_s)
            return
        self.device_path = path
        self.get_logger().info(f"Watching controller motion reports on {path}.")
        decoder = EventDecoder()
        try:
            while not self.stop_event.is_set():
                ready, _, _ = select.select([fd], [], [], 0.05)
                if not ready:
                    continue
                for data in read_available(fd):
                    count = decoder.feed(data)
                    with self.lock:
                        self.monitor.note_reports(count, time.monotonic())
        except OSError as error:
            self.get_logger().warning(f"Controller motion device lost: {error}")
        finally:
            os.close(fd)
            with self.lock:
                self.monitor.device_lost()
            self.device_path = None
        self.stop_event.wait(self.rescan_period_s)

    def _publish(self) -> None:
        with self.lock:
            up = self.monitor.link_up(time.monotonic())
        self.publisher.publish(Bool(data=up))
        if up != self.last_reported:
            self.get_logger().info("Controller radio link up." if up else "Controller radio link down.")
            self.last_reported = up

    def destroy_node(self):
        self.stop_event.set()
        self.reader.join(timeout=1.0)
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ControllerLinkNode()
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
