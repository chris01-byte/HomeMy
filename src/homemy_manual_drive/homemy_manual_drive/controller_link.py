"""Radio-link watchdog for the DualShock 4 controller.

Why this exists: the Linux gamepad interface reports only changes, and the
ROS joystick driver repeats the last known state at a fixed rate while the
input device exists. When the radio link breaks without a clean disconnect,
Linux keeps the device, and the driver keeps repeating a held direction,
until the Bluetooth link supervision timeout removes it. The repeated /joy
messages are therefore no proof that the controller is still there.

The DualShock 4 streams input reports continuously while its radio link is
up. The Linux driver (hid-playstation) exposes its gyroscope and
accelerometer as a separate input device, "... Wireless Controller Motion
Sensors", which emits one report per received radio packet because the
sensor timestamp changes in every packet. The time since the last motion
report is therefore a direct measure of the radio link.

This module holds the parts that need no ROS: device discovery, event
decoding, and the link decision. The report rate and the timeout must be
measured on the HomeMy computer (contracts/hardware/manual-drive.md, step M1).
"""

from __future__ import annotations

import os
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

# struct input_event on 64-bit Linux: struct timeval (two longs), u16 type,
# u16 code, s32 value.
EVENT_FORMAT = "llHHi"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)
EV_SYN = 0x00
SYN_REPORT = 0x00

DEFAULT_DEVICE_PATTERN = r"Wireless Controller Motion Sensors$"


@dataclass(frozen=True)
class InputDevice:
    event_path: str
    name: str


def list_input_devices(
    sys_class_input: str = "/sys/class/input", dev_input: str = "/dev/input"
) -> List[InputDevice]:
    """Return the event devices with their names, sorted by path."""

    devices = []
    root = Path(sys_class_input)
    if not root.is_dir():
        return devices
    for entry in sorted(root.glob("event*")):
        name_file = entry / "device" / "name"
        try:
            name = name_file.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        devices.append(InputDevice(event_path=f"{dev_input}/{entry.name}", name=name))
    return devices


def find_motion_device(
    devices: Iterable[InputDevice], pattern: str = DEFAULT_DEVICE_PATTERN
) -> Optional[InputDevice]:
    """The first device whose name matches the motion-sensor pattern.

    Returns None when no device matches. If more than one matches, the
    controllers cannot be told apart; the caller must refuse to report a
    link (see ambiguous_motion_devices).
    """

    regex = re.compile(pattern)
    for device in devices:
        if regex.search(device.name):
            return device
    return None


def ambiguous_motion_devices(
    devices: Iterable[InputDevice], pattern: str = DEFAULT_DEVICE_PATTERN
) -> bool:
    regex = re.compile(pattern)
    return sum(1 for device in devices if regex.search(device.name)) > 1


class EventDecoder:
    """Turns raw bytes from an event device into a count of finished reports."""

    def __init__(self) -> None:
        self._buffer = b""

    def feed(self, data: bytes) -> int:
        """Add bytes; return how many SYN_REPORT events completed."""

        self._buffer += data
        reports = 0
        while len(self._buffer) >= EVENT_SIZE:
            chunk, self._buffer = self._buffer[:EVENT_SIZE], self._buffer[EVENT_SIZE:]
            _sec, _usec, ev_type, code, _value = struct.unpack(EVENT_FORMAT, chunk)
            if ev_type == EV_SYN and code == SYN_REPORT:
                reports += 1
        return reports


def encode_event(ev_type: int, code: int, value: int, sec: int = 0, usec: int = 0) -> bytes:
    """Encode one input_event; used by tests and the simulated controller."""

    return struct.pack(EVENT_FORMAT, sec, usec, ev_type, code, value)


class LinkMonitor:
    """Decides whether the radio link is up from the time of the last report.

    The link is up only while reports keep arriving at least every
    ``timeout_s`` seconds. Before the first report, after a device loss, and
    when the clock goes backwards, the link is down. Times are monotonic
    seconds.
    """

    def __init__(self, timeout_s: float) -> None:
        if not (timeout_s > 0) or timeout_s != timeout_s or timeout_s == float("inf"):
            raise ValueError("timeout_s must be a positive finite number")
        self.timeout_s = timeout_s
        self.last_report_at: Optional[float] = None
        self.reports = 0

    def note_reports(self, count: int, now: float) -> None:
        if count > 0:
            self.last_report_at = now
            self.reports += count

    def device_lost(self) -> None:
        self.last_report_at = None

    def link_up(self, now: float) -> bool:
        if self.last_report_at is None:
            return False
        age = now - self.last_report_at
        return 0 <= age <= self.timeout_s

    def age(self, now: float) -> Optional[float]:
        if self.last_report_at is None:
            return None
        return now - self.last_report_at


def read_available(fd: int, max_bytes: int = EVENT_SIZE * 64) -> Iterator[bytes]:
    """Read what an O_NONBLOCK descriptor holds now; stops when it would block."""

    while True:
        try:
            data = os.read(fd, max_bytes)
        except BlockingIOError:
            return
        if not data:
            raise OSError("event device closed")
        yield data
