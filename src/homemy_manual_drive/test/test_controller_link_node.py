"""ROS-level test of the radio-link watchdog with a simulated input device.

A FIFO stands in for /dev/input/eventN. Writing motion reports into it keeps
the link up; stopping (a frozen radio link) or removing the device drops it.
"""

import os
import time

import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from std_msgs.msg import Bool

from homemy_manual_drive.controller_link import EV_SYN, SYN_REPORT, encode_event
from homemy_manual_drive.controller_link_node import ControllerLinkNode


@pytest.fixture
def ros_context():
    context = rclpy.Context()
    rclpy.init(context=context, domain_id=int(os.environ.get("ROS_DOMAIN_ID", "77")) % 100 + 100)
    yield context
    rclpy.shutdown(context=context)


def make_device(tmp_path):
    sys_root = tmp_path / "sys" / "class" / "input"
    (sys_root / "event7" / "device").mkdir(parents=True)
    (sys_root / "event7" / "device" / "name").write_text("Wireless Controller Motion Sensors\n")
    dev_root = tmp_path / "dev" / "input"
    dev_root.mkdir(parents=True)
    os.mkfifo(dev_root / "event7")
    return sys_root, dev_root


def test_link_follows_motion_reports(tmp_path, ros_context):
    sys_root, dev_root = make_device(tmp_path)
    node = ControllerLinkNode(
        context=ros_context,
        parameter_overrides=[
            rclpy.parameter.Parameter("sys_class_input", value=str(sys_root)),
            rclpy.parameter.Parameter("dev_input", value=str(dev_root)),
            rclpy.parameter.Parameter("link_timeout_s", value=0.15),
            rclpy.parameter.Parameter("rescan_period_s", value=0.1),
            rclpy.parameter.Parameter("link_topic", value="/test/controller/link"),
        ],
    )
    listener = rclpy.create_node("link_listener", context=ros_context)
    received = []
    listener.create_subscription(Bool, "/test/controller/link", lambda m: received.append((time.monotonic(), m.data)), 10)
    executor = SingleThreadedExecutor(context=ros_context)
    executor.add_node(node)
    executor.add_node(listener)

    def spin_for(seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            executor.spin_once(timeout_sec=0.01)

    def latest():
        return received[-1][1] if received else None

    writer = None
    try:
        spin_for(0.4)
        assert latest() is False  # nothing has arrived yet

        # Open the writer end: the node's reader now sees a live device.
        writer = os.open(dev_root / "event7", os.O_WRONLY)
        report = encode_event(0x03, 0, 1) + encode_event(EV_SYN, SYN_REPORT, 0)
        end = time.monotonic() + 0.6
        while time.monotonic() < end:
            os.write(writer, report)
            spin_for(0.01)
        assert latest() is True

        # Radio link freezes: the device stays, but reports stop.
        spin_for(0.4)
        assert latest() is False

        # Reports return: the link heals by itself.
        end = time.monotonic() + 0.4
        while time.monotonic() < end:
            os.write(writer, report)
            spin_for(0.01)
        assert latest() is True

        # The controller is switched off: the device disappears.
        os.close(writer)
        writer = None
        spin_for(0.3)
        assert latest() is False
    finally:
        if writer is not None:
            os.close(writer)
        executor.shutdown()
        node.destroy_node()
        listener.destroy_node()
