"""The LiDAR chain with the unchanged vendor driver against a simulated STL-27L.

Commissioning steps L0 to L5 in simulation (contracts/hardware/lidar-commissioning.md):
the vendor driver reads the device's serial packets from a pseudo-terminal;
scan normalisation and blind-sector mask follow.

Needs the vendor driver ldlidar_stl_ros2 built and sourced. Without it the
tests are skipped; the same chain without the vendor driver is covered by
test_drive_sim_e2e.py.

Everything is simulated: no hardware.
"""

from __future__ import annotations

import math
import pathlib
import random
import time

import numpy as np
import pytest
import yaml
from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

from e2e_support import launched_plain, set_parameter
from homemy_lidar_bringup import lidar_check_core as core
from homemy_lidar_bringup.scan_mask_core import blind_mask, build_sectors

try:
    get_package_share_directory("ldlidar_stl_ros2")
    VENDOR_DRIVER = True
except PackageNotFoundError:
    VENDOR_DRIVER = False

pytestmark = pytest.mark.skipif(not VENDOR_DRIVER, reason="vendor driver ldlidar_stl_ros2 is not built here")

TOPICS = ("/scan_raw", "/scan", "/scan_unconfirmed", "/scan_masked")


def mask_sectors():
    path = pathlib.Path(get_package_share_directory("homemy_lidar_bringup")) / "config" / "scan_mask.yaml"
    values = yaml.safe_load(path.read_text())["scan_mask"]["ros__parameters"]
    return build_sectors(values["sector_start_deg"], values["sector_end_deg"], float(values["margin_deg"]))


class Bench:
    def __init__(self, stack) -> None:
        self.stack = stack
        self.node = stack["node"]
        self.executor = SingleThreadedExecutor(context=stack["context"])
        self.executor.add_node(self.node)
        self.scans = {topic: [] for topic in TOPICS}
        for topic in TOPICS:
            self.node.create_subscription(LaserScan, topic, self.scans[topic].append, qos_profile_sensor_data)

    def spin(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.executor.spin_once(timeout_sec=0.02)

    def collect(self, topic, count, timeout):
        self.scans[topic].clear()
        end = time.monotonic() + timeout
        while len(self.scans[topic]) < count and time.monotonic() < end:
            self.executor.spin_once(timeout_sec=0.02)
        assert len(self.scans[topic]) >= count, (
            f"only {len(self.scans[topic])} of {count} scans on {topic}:\n" + open(self.stack["log"]).read()[-3000:]
        )
        return list(self.scans[topic][:count])

    def close(self):
        self.executor.remove_node(self.node)
        self.executor.shutdown()


def arguments(confirmed: bool):
    return [f"confirmed:={'true' if confirmed else 'false'}", f"sim_id:=test_{random.randint(0, 10**9)}"]


def angles_deg(scan):
    return np.degrees(scan.angle_min + np.arange(len(scan.ranges)) * scan.angle_increment)


def test_delivered_lock_keeps_the_scan_from_every_consumer():
    with launched_plain("lidar_sim.launch.py", arguments(False)) as stack:
        bench = Bench(stack)
        try:
            for_checking = bench.collect("/scan_unconfirmed", 10, 40)
            assert {len(scan.ranges) for scan in for_checking} == {2160}
            bench.spin(1.0)
            assert bench.scans["/scan"] == []
            assert bench.scans["/scan_masked"] == []
        finally:
            bench.close()


def test_vendor_driver_normalisation_and_mask_give_an_aligned_scan():
    with launched_plain("lidar_sim.launch.py", arguments(True)) as stack:
        bench = Bench(stack)
        try:
            # L1: what the vendor driver sends.
            raw = bench.collect("/scan_raw", 40, 60)
            counts = [len(scan.ranges) for scan in raw]
            assert len(set(counts)) >= 3, f"beam count does not vary: {set(counts)}"
            assert 2100 < min(counts) and max(counts) < 2220
            for scan in raw:
                assert scan.header.frame_id == "lidar_raw"
                assert scan.angle_min == 0.0
                assert scan.angle_max == pytest.approx(2.0 * math.pi)
                assert scan.angle_increment == pytest.approx(2.0 * math.pi / (len(scan.ranges) - 1), rel=1e-5)
            # The device turns ten times per second. The driver hands on at most
            # one scan per turn; on a busy test machine it can miss some, but it
            # can never deliver more.
            stamps = [s.header.stamp.sec + s.header.stamp.nanosec * 1e-9 for s in raw]
            assert 4.0 < core.rate_hz(stamps) < 11.5

            # L2: a fixed grid in the robot's frame.
            scans = bench.collect("/scan", 40, 30)
            for scan in scans:
                assert len(scan.ranges) == 2160
                assert scan.header.frame_id == "lidar_link"
                assert scan.angle_min == pytest.approx(-math.pi)
            angles = angles_deg(scans[0])
            median, spread = core.beam_medians(
                np.array([s.ranges for s in scans]), scans[0].range_min, scans[0].range_max)

            # L3: direction and rotation sense. The test apartment's start has a
            # wall 0.7 m to the right, 3.3 m to the left, and about 2.9 m ahead.
            def towards(bearing):
                return float(np.nanmedian(median[np.abs((angles - bearing + 180.0) % 360.0 - 180.0) < 1.5]))

            assert towards(-90.0) == pytest.approx(0.70, abs=0.05)
            assert towards(90.0) == pytest.approx(3.30, abs=0.08)
            assert towards(0.0) == pytest.approx(2.93, abs=0.08)

            # L4: the robot's own struts and webs lie exactly in the mask. The
            # simulated noise of 1 cm is coarser than the real sensor's.
            sectors = mask_sectors()
            found = core.sectors_of(angles, core.fixed_near_beams(median, spread, spread_limit_m=0.06))
            result = core.compare_with_mask(found, sectors)
            assert len(found) == 6, found
            assert all(entry["masked"] for entry in result["found"]), result
            assert all(entry["confirmed"] for entry in result["mask"]), result

            masked = bench.collect("/scan_masked", 10, 20)
            hidden = blind_mask(np.radians(angles), sectors)
            for scan in masked:
                ranges = np.array(scan.ranges)
                assert np.isnan(ranges[hidden]).all()
                visible = ranges[~hidden]
                assert np.isfinite(visible).mean() > 0.9
                # Nothing of the robot itself is left outside the mask.
                assert (visible[np.isfinite(visible)] < 0.45).mean() < 0.002

            # L5: cable pulled, then plugged in again.
            set_parameter(stack, "homemy_sim_base", "lidar_silent", True)
            bench.spin(1.5)
            bench.scans["/scan_masked"].clear()
            bench.spin(2.0)
            assert bench.scans["/scan_masked"] == []
            set_parameter(stack, "homemy_sim_base", "lidar_silent", False)
            back = bench.collect("/scan_masked", 10, 30)
            assert {len(scan.ranges) for scan in back} == {2160}
        finally:
            bench.close()
