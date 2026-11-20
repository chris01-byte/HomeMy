"""A simulated STL-27L on a serial line. Simulation only; pure Python, no ROS.

The device sends, without being asked, 47-byte packets of 12 measurements
each (format and checksum as read by the vendor driver ldlidar_stl_ros2,
``ldlidar_driver/src/dataprocess/lipkg.cpp``):

    0x54  0x2C  speed(u16, deg/s)  start_angle(u16, 0.01 deg)
    12 x [ distance(u16, mm)  intensity(u8) ]
    end_angle(u16, 0.01 deg)  timestamp(u16, ms)  crc8

All values little-endian. The device's angle counts clockwise seen from
above. It measures 21600 points per second and turns about ten times per
second; the turning speed wanders a little, which is why the number of
points per revolution changes from scan to scan.

``Stl27lDevice`` produces the packets, ``PtyStream`` sends them through a
pseudo-terminal that stands in for the USB adapter, so that the unchanged
vendor driver can read them.
"""

from __future__ import annotations

import math
import os
import select
import struct
import threading
import time
import tty
from typing import Callable, Dict, List, Optional

import numpy as np

HEADER = 0x54
VER_LEN = 0x2C
POINTS_PER_PACKET = 12
PACKET_SIZE = 47
POINT_RATE_HZ = 21600.0
_PACKET = struct.Struct("<BBHH" + "HB" * POINTS_PER_PACKET + "HH")


def _crc_table() -> List[int]:
    table = []
    for value in range(256):
        crc = value
        for _ in range(8):
            crc = ((crc << 1) ^ 0x4D) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
        table.append(crc)
    return table


_CRC_TABLE = _crc_table()


def crc8(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc = _CRC_TABLE[crc ^ byte]
    return crc


def encode_packet(speed_dps: int, start_centideg: int, distances_mm, intensities,
                  end_centideg: int, timestamp_ms: int) -> bytes:
    if len(distances_mm) != POINTS_PER_PACKET or len(intensities) != POINTS_PER_PACKET:
        raise ValueError("a packet holds exactly 12 points")
    points = []
    for distance, intensity in zip(distances_mm, intensities):
        points.extend((int(distance) & 0xFFFF, int(intensity) & 0xFF))
    body = _PACKET.pack(
        HEADER, VER_LEN, int(speed_dps) & 0xFFFF, int(start_centideg) % 36000, *points,
        int(end_centideg) % 36000, int(timestamp_ms) & 0xFFFF,
    )
    return body + bytes([crc8(body)])


def decode_packet(packet: bytes) -> Optional[Dict]:
    """The reading side, for tests: None if the packet is not valid."""

    if len(packet) != PACKET_SIZE or packet[0] != HEADER or packet[1] != VER_LEN:
        return None
    if crc8(packet[:-1]) != packet[-1]:
        return None
    fields = _PACKET.unpack(packet[:-1])
    span = (fields[-2] - fields[3]) % 36000
    step = span / (POINTS_PER_PACKET - 1) / 100.0
    return {
        "speed_dps": fields[2],
        "angles_deg": [(fields[3] / 100.0 + i * step) % 360.0 for i in range(POINTS_PER_PACKET)],
        "distances_mm": list(fields[4:-2:2]),
        "intensities": list(fields[5:-2:2]),
        "timestamp_ms": fields[-1],
    }


class Stl27lDevice:
    """Produces the device's packet stream.

    ``sample`` gets the measuring directions as angles in radians, counter-
    clockwise in the device's own frame, and returns the ranges in metres
    (NaN or inf: nothing measured).
    """

    def __init__(self, sample: Callable[[np.ndarray], np.ndarray], speed_dps: float = 3600.0,
                 speed_wander_dps: float = 25.0, seed: int = 11, intensity: int = 200) -> None:
        self.sample = sample
        self.nominal_speed = float(speed_dps)
        self.speed_wander = float(speed_wander_dps)
        self.speed = float(speed_dps)
        self.rng = np.random.default_rng(seed)
        self.intensity = int(intensity)
        self.angle_deg = 0.0  # clockwise, direction of the next measurement
        self.points_sent = 0

    def packets(self, count: int) -> bytes:
        """The next ``count`` packets; all their directions are sampled in one call."""

        if count <= 0:
            return b""
        starts = []
        angles = np.empty((count, POINTS_PER_PACKET))
        speeds = []
        for row in range(count):
            # The turning speed wanders slowly around its nominal value.
            self.speed += float(self.rng.normal(0.0, self.speed_wander * 0.02))
            self.speed += (self.nominal_speed - self.speed) * 0.002
            step = self.speed / POINT_RATE_HZ
            angles[row] = self.angle_deg + np.arange(POINTS_PER_PACKET) * step
            starts.append(self.angle_deg)
            speeds.append(self.speed)
            self.angle_deg = (self.angle_deg + POINTS_PER_PACKET * step) % 360.0
        ranges = np.asarray(self.sample(-np.radians(angles.ravel())), dtype=float).reshape(angles.shape)
        valid = np.isfinite(ranges) & (ranges > 0.0) & (ranges < 65.0)
        millimetres = np.where(valid, np.rint(np.where(valid, ranges, 0.0) * 1000.0), 0).astype(int)
        out = bytearray()
        for row in range(count):
            self.points_sent += POINTS_PER_PACKET
            out += encode_packet(
                int(round(speeds[row])),
                int(round(starts[row] * 100.0)),
                millimetres[row],
                np.where(valid[row], self.intensity, 0),
                int(round(angles[row, -1] * 100.0)),
                int(self.points_sent / POINT_RATE_HZ * 1000.0),
            )
        return bytes(out)


class PtyStream:
    """Sends a device's packets in real time through a pseudo-terminal linked to a fixed path."""

    def __init__(self, device: Stl27lDevice, link_path: str, period_s: float = 0.01) -> None:
        self.device = device
        self.link_path = link_path
        self.period = float(period_s)
        self.master_fd, self.slave_fd = os.openpty()
        tty.setraw(self.slave_fd)  # no echo, no line handling, like a serial adapter
        os.set_blocking(self.master_fd, False)
        self.device_path = os.ttyname(self.slave_fd)
        if os.path.islink(link_path) or os.path.exists(link_path):
            os.unlink(link_path)
        os.symlink(self.device_path, link_path)
        self.silent = False  # True: the cable is pulled, nothing is sent
        self.bytes_sent = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        packets_per_second = POINT_RATE_HZ / POINTS_PER_PACKET
        start = time.monotonic()
        sent = 0
        while not self._stop.wait(self.period):
            due = int((time.monotonic() - start) * packets_per_second) - sent
            if due <= 0:
                continue
            if due > 4 * packets_per_second * self.period + 20:
                # After a stall, do not send a burst of old measurements.
                sent += due
                continue
            sent += due
            if self.silent:
                continue
            data = self.device.packets(due)
            # Nobody reading: drop the data, as a cable without a listener would.
            _, writable, _ = select.select([], [self.master_fd], [], 0.0)
            if not writable:
                continue
            try:
                self.bytes_sent += os.write(self.master_fd, data)
            except (BlockingIOError, OSError):
                pass
            # Whatever the reader sends (nothing, for this device) is thrown away.
            try:
                while os.read(self.master_fd, 4096):
                    pass
            except (BlockingIOError, OSError):
                pass

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1.0)
        for descriptor in (self.master_fd, self.slave_fd):
            try:
                os.close(descriptor)
            except OSError:
                pass
        try:
            if os.path.islink(self.link_path):
                os.unlink(self.link_path)
        except OSError:
            pass


def points_per_revolution(speed_dps: float) -> float:
    return 360.0 / (speed_dps / POINT_RATE_HZ)


def expected_packet_rate() -> float:
    return POINT_RATE_HZ / POINTS_PER_PACKET


__all__ = [
    "PACKET_SIZE", "POINTS_PER_PACKET", "POINT_RATE_HZ", "PtyStream", "Stl27lDevice",
    "crc8", "decode_packet", "encode_packet", "expected_packet_rate", "points_per_revolution",
]
