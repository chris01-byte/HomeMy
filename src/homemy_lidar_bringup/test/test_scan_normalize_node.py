"""ROS-level test of the scan normalisation with raw scans like the vendor driver's."""

import math
import os
import time

import numpy as np
import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

from homemy_lidar_bringup.scan_normalize_node import ScanNormalize

FULL_TURN = 2.0 * math.pi


def raw_scan(beams, target_deg=None, stamp_s=12.5, blind=(236.0, 304.0)):
    """A scan as ldlidar_stl_ros2 sends it: 0..360 degrees, (N - 1) * increment = 360."""

    scan = LaserScan()
    scan.header.frame_id = "lidar_raw"
    scan.header.stamp.sec = int(stamp_s)
    scan.header.stamp.nanosec = int((stamp_s % 1.0) * 1e9)
    scan.angle_min = 0.0
    scan.angle_max = FULL_TURN
    scan.angle_increment = FULL_TURN / (beams - 1)
    scan.scan_time = 0.1
    scan.time_increment = 0.1 / (beams - 1)
    scan.range_min = 0.02
    scan.range_max = 25.0
    degrees = np.degrees(np.arange(beams) * scan.angle_increment)
    ranges = np.full(beams, 3.0)
    if blind is not None:
        ranges[(degrees >= blind[0]) & (degrees <= blind[1])] = np.nan
    if target_deg is not None:
        ranges[np.abs(degrees - target_deg) <= 1.0] = 0.8
    scan.ranges = ranges.tolist()
    scan.intensities = np.where(np.isnan(ranges), np.nan, 180.0).tolist()
    return scan


class Harness:
    def __init__(self, **parameters):
        self.context = rclpy.Context()
        rclpy.init(context=self.context, domain_id=int(os.environ.get("ROS_DOMAIN_ID", "77")) % 100 + 115)
        self.node = ScanNormalize(
            context=self.context,
            parameter_overrides=[Parameter(name, value=value) for name, value in parameters.items()],
        )
        self.driver = rclpy.create_node("normalize_test_driver", context=self.context)
        self.executor = SingleThreadedExecutor(context=self.context)
        self.executor.add_node(self.node)
        self.executor.add_node(self.driver)
        self.out = {"/scan": [], "/scan_unconfirmed": []}
        for topic, store in self.out.items():
            self.driver.create_subscription(LaserScan, topic, store.append, qos_profile_sensor_data)
        self.raw = self.driver.create_publisher(LaserScan, "/scan_raw", qos_profile_sensor_data)
        self.spin(0.5)

    def spin(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.executor.spin_once(timeout_sec=0.02)

    def send(self, scans, topic="/scan"):
        before = len(self.out[topic])
        for scan in scans:
            self.raw.publish(scan)
            self.spin(0.08)
        self.spin(0.3)
        return self.out[topic][before:]

    def close(self):
        self.executor.shutdown()
        self.node.destroy_node()
        self.driver.destroy_node()
        rclpy.shutdown(context=self.context)


@pytest.fixture
def harness():
    created = []

    def make(**parameters):
        created.append(Harness(**parameters))
        return created[-1]

    yield make
    for item in created:
        item.close()


def test_varying_beam_counts_become_one_fixed_grid(harness):
    h = harness(alignment_confirmed=True)
    counts = [2146, 2160, 2153, 2176, 2171, 2149]
    out = h.send([raw_scan(count) for count in counts])
    assert len(out) == len(counts)
    for scan in out:
        assert len(scan.ranges) == 2160
        assert len(scan.intensities) == 2160
        assert scan.header.frame_id == "lidar_link"
        assert scan.angle_min == pytest.approx(-math.pi)
        assert scan.angle_increment == pytest.approx(FULL_TURN / 2160)
        assert scan.angle_max == pytest.approx(math.pi - FULL_TURN / 2160)
        assert scan.time_increment == 0.0
        assert (scan.header.stamp.sec, scan.header.stamp.nanosec) == (12, 500000000)
        assert (scan.range_min, scan.range_max) == (pytest.approx(0.02), 25.0)
    assert len({(s.angle_min, s.angle_increment, s.angle_max) for s in out}) == 1


def test_driver_nan_stays_nan_and_nothing_is_invented(harness):
    h = harness(alignment_confirmed=True)
    out = h.send([raw_scan(2172)])[0]
    ranges = np.array(out.ranges)
    degrees = np.degrees(out.angle_min + np.arange(2160) * out.angle_increment)
    blind = degrees[np.isnan(ranges)]
    # The device's 236..304 degrees are -124..-56 degrees for the robot.
    assert blind.min() == pytest.approx(-124.0, abs=0.3)
    assert blind.max() == pytest.approx(-56.0, abs=0.3)
    assert set(np.unique(ranges[np.isfinite(ranges)])) == {3.0}
    assert np.all(np.array(out.intensities)[np.isnan(ranges)] != 180.0)


@pytest.mark.parametrize("yaw_deg", [0.0, 90.0, -37.04])
def test_yaw_offset_puts_a_target_at_its_bearing_in_the_robot_frame(harness, yaw_deg):
    h = harness(alignment_confirmed=True, yaw_offset_deg=yaw_deg)
    out = h.send([raw_scan(2158, target_deg=30.0, blind=None)])[0]
    ranges = np.array(out.ranges)
    degrees = np.degrees(out.angle_min + np.arange(2160) * out.angle_increment)
    seen = float(np.mean(degrees[ranges < 1.0]))
    assert seen == pytest.approx(30.0 + yaw_deg, abs=0.2)


def test_unconfirmed_alignment_reaches_no_consumer(harness):
    """The delivered default: the scan is only published for checking."""

    h = harness()
    for_checking = h.send([raw_scan(2160), raw_scan(2150)], topic="/scan_unconfirmed")
    assert len(for_checking) == 2
    assert h.out["/scan"] == []
    assert h.node.output_topic == "/scan_unconfirmed"


def test_unusable_scans_are_dropped_and_good_ones_continue(harness):
    h = harness(alignment_confirmed=True)
    empty = raw_scan(2160)
    empty.ranges = []
    empty.intensities = []
    mirrored = raw_scan(2160)
    mirrored.angle_increment = -mirrored.angle_increment
    broken = raw_scan(2160)
    broken.angle_increment = float("nan")
    assert h.send([empty, mirrored, broken]) == []
    assert len(h.send([raw_scan(2160)])) == 1
    assert h.node.seen == 4 and h.node.published == 1


def test_invalid_parameters_stop_the_start():
    context = rclpy.Context()
    rclpy.init(context=context, domain_id=int(os.environ.get("ROS_DOMAIN_ID", "77")) % 100 + 115)
    try:
        for name, value in (("beams", 1), ("yaw_offset_deg", 400.0), ("yaw_offset_deg", float("nan"))):
            with pytest.raises(ValueError):
                ScanNormalize(context=context, parameter_overrides=[Parameter(name, value=value)])
    finally:
        rclpy.shutdown(context=context)
