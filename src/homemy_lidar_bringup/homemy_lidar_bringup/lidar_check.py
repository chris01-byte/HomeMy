"""Check tool for LiDAR commissioning. It only listens; it sends nothing.

    ros2 run homemy_lidar_bringup lidar_check stats   --topic /scan_raw
    ros2 run homemy_lidar_bringup lidar_check target  --topic /scan_unconfirmed
    ros2 run homemy_lidar_bringup lidar_check sectors --topic /scan_unconfirmed

stats    beam counts, rate, and age of the scans (contract steps L1, L2)
target   bearing of the nearest object, once per second (step L3)
sectors  the robot's own parts in the scan, compared with the mask (step L4)
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path
from typing import List, Optional

import numpy as np
import rclpy
import yaml
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

from homemy_lidar_bringup import lidar_check_core as core
from homemy_lidar_bringup.scan_mask_core import build_sectors


def default_mask_file() -> Optional[Path]:
    try:
        from ament_index_python.packages import get_package_share_directory

        return Path(get_package_share_directory("homemy_lidar_bringup")) / "config" / "scan_mask.yaml"
    except Exception:
        return None


def load_mask(path: Path):
    values = yaml.safe_load(Path(path).read_text())["scan_mask"]["ros__parameters"]
    return build_sectors(values["sector_start_deg"], values["sector_end_deg"], float(values["margin_deg"]))


class Collector(Node):
    def __init__(self, topic: str) -> None:
        super().__init__("lidar_check")
        self.scans: List[LaserScan] = []
        self.ages: List[float] = []
        self.create_subscription(LaserScan, topic, self._on_scan, qos_profile_sensor_data)

    def _on_scan(self, message: LaserScan) -> None:
        stamp = message.header.stamp.sec + message.header.stamp.nanosec * 1e-9
        self.ages.append(self.get_clock().now().nanoseconds * 1e-9 - stamp)
        self.scans.append(message)

    def collect(self, count: int, timeout_s: float) -> List[LaserScan]:
        self.scans.clear()
        self.ages.clear()
        end = time.monotonic() + timeout_s
        while len(self.scans) < count and time.monotonic() < end and rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
        return list(self.scans)


def angles_deg(scan: LaserScan) -> np.ndarray:
    return np.degrees(scan.angle_min + np.arange(len(scan.ranges)) * scan.angle_increment)


def print_stats(scans: List[LaserScan], ages: List[float]) -> None:
    summary = core.beam_count_summary([len(s.ranges) for s in scans])
    stamps = [s.header.stamp.sec + s.header.stamp.nanosec * 1e-9 for s in scans]
    rate = core.rate_hz(stamps)
    first = scans[0]
    valid = [
        float(np.mean(np.isfinite(np.asarray(s.ranges, dtype=float)))) for s in scans
    ]
    print(f"Scans ausgewertet       : {summary['scans']}")
    print(f"Frame                   : {first.header.frame_id}")
    print(f"Rate                    : {rate:.1f} Hz" if rate else "Rate                    : nicht bestimmbar")
    print(f"Strahlen je Scan        : {summary['min']} bis {summary['max']}, "
          f"{summary['distinct']} verschiedene Werte")
    print(f"häufigster Wert         : {summary['most_common']} "
          f"({summary['most_common_share'] * 100:.0f} % der Scans)")
    print(f"Winkelbereich           : {math.degrees(first.angle_min):.1f} bis "
          f"{math.degrees(first.angle_max):.1f} Grad")
    print(f"Messbereich laut Treiber: {first.range_min:.2f} bis {first.range_max:.1f} m")
    print(f"gültige Strahlen        : {min(valid) * 100:.0f} bis {max(valid) * 100:.0f} %")
    print(f"Alter beim Empfang      : im Mittel {np.mean(ages) * 1000:.0f} ms, "
          f"höchstens {np.max(ages) * 1000:.0f} ms")
    if summary["distinct"] > 1:
        print("\nDie Strahlenzahl schwankt. Das ist beim STL-27L normal; die Vereinheitlichung")
        print("(scan_normalize) macht daraus ein festes Raster.")


def same_grid(scans: List[LaserScan]) -> bool:
    first = scans[0]
    return all(
        len(s.ranges) == len(first.ranges) and s.angle_min == first.angle_min
        and s.angle_increment == first.angle_increment for s in scans
    )


def print_sectors(scans: List[LaserScan], mask_file: Optional[Path], near_limit: float = 0.6,
                  spread_limit: float = 0.02) -> int:
    if not same_grid(scans):
        print("Die Scans haben verschiedene Strahlenzahlen. Die eigenen Teile lassen sich nur im")
        print("vereinheitlichten Scan bestimmen: --topic /scan_unconfirmed (oder /scan).")
        return 2
    first = scans[0]
    angles = angles_deg(first)
    median, spread = core.beam_medians(np.array([s.ranges for s in scans]), first.range_min, first.range_max)
    found = core.sectors_of(angles, core.fixed_near_beams(median, spread, near_limit, spread_limit))
    print(f"Feste, nahe Reflexe (näher als {near_limit:.2f} m, Streuung unter {spread_limit * 100:.0f} cm) "
          f"in {len(scans)} Scans:")
    if not found:
        print("  keine. Entweder steht der Sensor völlig frei, oder der Scan ist bereits maskiert.")
        with np.errstate(invalid="ignore"):
            near = np.isfinite(median) & (median < near_limit)
        if near.any():
            print(f"  Es gibt aber {int(near.sum())} nahe Strahlen mit Streuung bis "
                  f"{float(np.nanmax(spread[near])) * 100:.0f} cm. Steht jemand am Roboter?")
    for start, end in found:
        inside = (angles >= start) & (angles <= end) if end <= 180.0 else (angles >= start) | (angles <= end - 360.0)
        distance = float(np.nanmedian(median[inside])) if inside.any() else float("nan")
        print(f"  {start:+7.1f} bis {end:+7.1f} Grad  (Breite {end - start:4.1f} Grad, Abstand etwa {distance:.2f} m)")
    if mask_file is None or not Path(mask_file).is_file():
        print("\nKeine Maskendatei gefunden; kein Vergleich.")
        return 0
    result = core.compare_with_mask(found, load_mask(mask_file))
    print(f"\nVergleich mit der Maske aus {mask_file}:")
    for entry in result["mask"]:
        text = "im Scan bestätigt" if entry["confirmed"] else "im Scan NICHT gefunden"
        print(f"  Maske {entry['start']:+7.1f} bis {entry['end']:+7.1f} Grad: {text}")
    open_sectors = [e for e in result["found"] if not e["masked"]]
    for entry in open_sectors:
        print(f"  NICHT maskiert: fester Reflex {entry['start']:+7.1f} bis {entry['end']:+7.1f} Grad")
    unconfirmed = [e for e in result["mask"] if not e["confirmed"]]
    if not open_sectors and not unconfirmed:
        print("\nErgebnis: Jeder feste Reflex liegt in der Maske, und jeder Maskensektor ist bestätigt.")
        return 0
    print("\nErgebnis: Maske und Scan passen NICHT zusammen. Erst Richtung und Drehsinn prüfen")
    print("(lidar_check target), dann die Sektoren in config/scan_mask.yaml anpassen.")
    return 1


def run_target(node: Collector, seconds: float, mask_file: Optional[Path]) -> int:
    print("Nächstes Objekt im Scan. Einen Karton 0,5 bis 1 m genau VOR den Roboter stellen:")
    print("Die Richtung muss nahe 0 Grad liegen. Dann den Karton nach LINKS tragen:")
    print("Die Richtung muss dabei steigen (links = +90 Grad).\n")
    sectors = load_mask(mask_file) if mask_file and Path(mask_file).is_file() else []
    from homemy_lidar_bringup.scan_mask_core import blind_mask

    end = time.monotonic() + seconds
    seen = False
    while time.monotonic() < end and rclpy.ok():
        scans = node.collect(5, 1.5)
        if not scans:
            print("kein Scan empfangen")
            continue
        if not same_grid(scans):
            print("Strahlenzahl schwankt: bitte den vereinheitlichten Scan verwenden (--topic /scan_unconfirmed).")
            return 2
        seen = True
        angles = angles_deg(scans[0])
        median, _ = core.beam_medians(np.array([s.ranges for s in scans]), scans[0].range_min,
                                      scans[0].range_max, presence=0.6)
        target = core.nearest_target(angles, median, ignore=blind_mask(np.radians(angles), sectors))
        if target is None:
            print("kein Objekt zwischen 0,15 und 3 m")
        else:
            side = "vorn" if abs(target[0]) < 20 else "links" if 20 <= target[0] < 160 else \
                "rechts" if -160 < target[0] <= -20 else "hinten"
            print(f"Richtung {target[0]:+7.1f} Grad ({side}), Abstand {target[1]:.2f} m")
    return 0 if seen else 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Prüfwerkzeug für den LiDAR. Hört nur zu.")
    parser.add_argument("mode", choices=["stats", "target", "sectors"])
    parser.add_argument("--topic", default="/scan_unconfirmed")
    parser.add_argument("--scans", type=int, default=40)
    parser.add_argument("--seconds", type=float, default=30.0, help="Dauer für target")
    parser.add_argument("--mask-file", type=Path, default=default_mask_file())
    parser.add_argument("--near-limit", type=float, default=0.6, help="m; näher gilt als eigenes Teil")
    parser.add_argument("--spread-limit", type=float, default=0.02, help="m; darunter gilt als unbeweglich")
    args = parser.parse_args(rclpy.utilities.remove_ros_args(argv if argv is not None else sys.argv)[1:])

    rclpy.init()
    node = Collector(args.topic)
    try:
        if args.mode == "target":
            return run_target(node, args.seconds, args.mask_file)
        print(f"Sammle {args.scans} Scans von {args.topic}. Den Roboter bitte nicht bewegen ...", flush=True)
        scans = node.collect(args.scans, max(20.0, args.scans * 0.5))
        if len(scans) < 5:
            print(f"Nur {len(scans)} Scans empfangen. Läuft der Treiber, stimmt das Topic?")
            return 2
        if args.mode == "stats":
            print_stats(scans, list(node.ages))
            return 0
        return print_sectors(scans, args.mask_file, args.near_limit, args.spread_limit)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    sys.exit(main())
