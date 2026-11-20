"""A simulated HWT601-AGV-485 on an RS485 line. Simulation only; no ROS.

The sensor is a Modbus RTU device (factory address 0x50). The HomeMy reader
asks for six holding registers from 0x34 with function 0x03:

    AX AY AZ   acceleration, signed 16 bit, full scale 4 g
    GX GY GZ   angular rate, signed 16 bit, full scale 400 deg/s

``Hwt601Bus`` answers those requests like ``Ess23Bus`` answers the motors'
and is served through the same pseudo-terminal class. It counts every
request that is not a plain read, so that a test can prove that the reader
never tries to write to the sensor.
"""

from __future__ import annotations

import math
import threading
from typing import Callable, Sequence, Tuple

from homemy_simulation.ess23_sim import crc16, with_crc

DEVICE_ADDRESS = 0x50
MOTION_REGISTER_START = 0x34
MOTION_REGISTER_COUNT = 6
ACCELERATION_FULL_SCALE_G = 4.0
ANGULAR_FULL_SCALE_DPS = 400.0
GRAVITY = 9.80665
EXCEPTION_ILLEGAL_FUNCTION = 0x01
EXCEPTION_ILLEGAL_ADDRESS = 0x02

Vector = Tuple[float, float, float]


def to_register(value: float, full_scale: float) -> int:
    """A physical value as the sensor's signed 16-bit register, clipped at full scale."""

    raw = int(round(value / full_scale * 32768.0))
    raw = max(-32768, min(32767, raw))
    return raw & 0xFFFF


def motion_registers(acceleration_mps2: Sequence[float], angular_velocity_radps: Sequence[float]) -> Tuple[int, ...]:
    return tuple(
        [to_register(a / GRAVITY, ACCELERATION_FULL_SCALE_G) for a in acceleration_mps2]
        + [to_register(math.degrees(w), ANGULAR_FULL_SCALE_DPS) for w in angular_velocity_radps]
    )


class Hwt601Bus:
    """Answers Modbus RTU requests for one HWT601. No I/O in this class.

    ``sample`` returns the current acceleration (m/s^2) and angular rate
    (rad/s) in the sensor's own axes.
    """

    def __init__(self, sample: Callable[[], Tuple[Vector, Vector]], address: int = DEVICE_ADDRESS) -> None:
        self.sample = sample
        self.address = address
        self.lock = threading.Lock()
        self._buffer = b""
        self.requests = 0
        self.crc_errors = 0
        self.non_read_requests = 0  # anything but function 0x03: must stay 0
        self.silent = False         # fault: the cable is pulled, nothing answers
        self.corrupt = False        # fault: answers arrive with a broken checksum

    def feed(self, data: bytes) -> bytes:
        if self.silent:
            self._buffer = b""
            return b""
        self._buffer += data
        out = b""
        while len(self._buffer) >= 8:
            frame = self._buffer[:8]
            if crc16(frame[:6]) != (frame[6] | frame[7] << 8):
                self.crc_errors += 1
                self._buffer = self._buffer[1:]
                continue
            self._buffer = self._buffer[8:]
            out += self._handle(frame)
        return out

    def _handle(self, frame: bytes) -> bytes:
        address, function = frame[0], frame[1]
        start = frame[2] << 8 | frame[3]
        count = frame[4] << 8 | frame[5]
        if address != self.address:
            return b""  # another device's address: stay silent, as on a real bus
        self.requests += 1
        if function != 0x03:
            self.non_read_requests += 1
            return with_crc(bytes((address, function | 0x80, EXCEPTION_ILLEGAL_FUNCTION)))
        if start < MOTION_REGISTER_START or start + count > MOTION_REGISTER_START + MOTION_REGISTER_COUNT \
                or count < 1:
            return with_crc(bytes((address, 0x83, EXCEPTION_ILLEGAL_ADDRESS)))
        acceleration, angular = self.sample()
        words = motion_registers(acceleration, angular)[start - MOTION_REGISTER_START:][:count]
        payload = b"".join(bytes((word >> 8, word & 0xFF)) for word in words)
        reply = with_crc(bytes((address, 0x03, len(payload))) + payload)
        if self.corrupt:
            reply = reply[:-1] + bytes((reply[-1] ^ 0xFF,))
        return reply
