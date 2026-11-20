"""Simulated ESS23-RS drive motors on a simulated RS485 bus. Simulation only.

The real drive driver (homemy_drivebase) talks Modbus RTU through pymodbus and
a serial port. For the test stand that serial port is a pseudo-terminal: the
driver opens it like the USB adapter, and this module answers on the other
end as two motors would. So the driver's real code path runs unchanged, down
to the bytes on the bus.

Modelled, following the registers the Amadeus driver was proven with:

- FC03 (read holding registers) and FC06 (write single register), CRC-16;
- speed setpoint 0x001D (signed rpm), start impulse and stop on 0x0027,
  ramp registers 0x001E/0x001F/0x0020 (stored, not simulated);
- absolute position 0x000A/0x000B (32 bit, word order from 0x0019) and
  actual speed 0x000C, read as one block;
- segment 0x0011, word order 0x0019, encoder resolution 0x0101.

Like the real motors as far as known, a simulated motor has no watchdog: it
keeps its last setpoint until it is told to stop.
"""

from __future__ import annotations

import os
import select
import threading
import tty
from dataclasses import dataclass, field
from typing import Dict, List, Optional

REG_POSITION = 0x000A
REG_SPEED = 0x000C
REG_SEGMENT = 0x0011
REG_WORD_ORDER = 0x0019
REG_SETPOINT = 0x001D
REG_ACCEL = 0x001E
REG_DECEL = 0x001F
REG_START_SPEED = 0x0020
REG_COMMAND = 0x0027
REG_RESOLUTION = 0x0101
COMMAND_START = 0x0002
COMMAND_STOP = 0x0100

EXCEPTION_ILLEGAL_FUNCTION = 0x01
EXCEPTION_ILLEGAL_ADDRESS = 0x02


def crc16(data: bytes) -> int:
    """Modbus RTU CRC-16 (polynomial 0xA001, initial value 0xFFFF)."""

    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def with_crc(frame: bytes) -> bytes:
    crc = crc16(frame)
    return frame + bytes((crc & 0xFF, crc >> 8))


def signed16(word: int) -> int:
    return word - 0x10000 if word & 0x8000 else word


@dataclass
class Ess23Motor:
    """Registers and state of one simulated motor."""

    motor_id: int
    segment: int = 1000
    resolution: int = 4000
    high_word_first: bool = True
    setpoint_rpm: int = 0
    running: bool = False
    position_counts: int = 0  # signed, wraps as uint32 on the bus
    speed_rpm: float = 0.0
    stored: Dict[int, int] = field(default_factory=dict)
    writes: int = 0

    def target_rpm(self) -> float:
        return float(self.setpoint_rpm) if self.running else 0.0

    def read(self, address: int) -> Optional[int]:
        position = self.position_counts & 0xFFFFFFFF
        high, low = position >> 16, position & 0xFFFF
        if address == REG_POSITION:
            return high if self.high_word_first else low
        if address == REG_POSITION + 1:
            return low if self.high_word_first else high
        if address == REG_SPEED:
            return int(round(self.speed_rpm)) & 0xFFFF
        if address == REG_SEGMENT:
            return self.segment
        if address == REG_WORD_ORDER:
            return 0 if self.high_word_first else 1
        if address == REG_RESOLUTION:
            return self.resolution
        if address == REG_SETPOINT:
            return self.setpoint_rpm & 0xFFFF
        if address in (REG_ACCEL, REG_DECEL, REG_START_SPEED, REG_COMMAND):
            return self.stored.get(address, 0)
        return None

    def write(self, address: int, value: int) -> bool:
        self.writes += 1
        if address == REG_SETPOINT:
            self.setpoint_rpm = signed16(value)
            return True
        if address == REG_COMMAND:
            self.stored[address] = value
            if value == COMMAND_START:
                self.running = True
            elif value == COMMAND_STOP:
                self.running = False
            return True
        if address in (REG_ACCEL, REG_DECEL, REG_START_SPEED):
            self.stored[address] = value
            return True
        return False


class Ess23Bus:
    """Answers Modbus RTU requests for a set of motors. No I/O in this class."""

    def __init__(self, motors: List[Ess23Motor]) -> None:
        self.motors = {motor.motor_id: motor for motor in motors}
        self.lock = threading.Lock()
        self._buffer = b""
        self.requests = 0
        self.crc_errors = 0
        self.silent = False  # fault injection: the bus is cut, nothing answers

    def feed(self, data: bytes) -> bytes:
        """Add received bytes; return the bytes to send back."""

        if self.silent:
            self._buffer = b""
            return b""
        self._buffer += data
        out = b""
        while len(self._buffer) >= 8:
            frame = self._buffer[:8]
            if crc16(frame[:6]) != (frame[6] | frame[7] << 8):
                self.crc_errors += 1
                self._buffer = self._buffer[1:]  # resynchronise
                continue
            self._buffer = self._buffer[8:]
            out += self._handle(frame)
        return out

    def _handle(self, frame: bytes) -> bytes:
        motor_id, function = frame[0], frame[1]
        address = frame[2] << 8 | frame[3]
        value = frame[4] << 8 | frame[5]
        motor = self.motors.get(motor_id)
        if motor is None:
            return b""  # another device's address: stay silent, as on a real bus
        self.requests += 1
        with self.lock:
            if function == 0x03:
                if not 1 <= value <= 125:
                    return with_crc(bytes((motor_id, 0x83, EXCEPTION_ILLEGAL_ADDRESS)))
                words = [motor.read(address + offset) for offset in range(value)]
                if any(word is None for word in words):
                    return with_crc(bytes((motor_id, 0x83, EXCEPTION_ILLEGAL_ADDRESS)))
                payload = b"".join(bytes((word >> 8, word & 0xFF)) for word in words)
                return with_crc(bytes((motor_id, 0x03, len(payload))) + payload)
            if function == 0x06:
                if not motor.write(address, value):
                    return with_crc(bytes((motor_id, 0x86, EXCEPTION_ILLEGAL_ADDRESS)))
                return with_crc(frame[:6])
        return with_crc(bytes((motor_id, function | 0x80, EXCEPTION_ILLEGAL_FUNCTION)))


class PtyBusServer:
    """Serves an Ess23Bus on a pseudo-terminal and links it to a fixed path."""

    def __init__(self, bus: Ess23Bus, link_path: str) -> None:
        self.bus = bus
        self.link_path = link_path
        self.master_fd, self.slave_fd = os.openpty()
        tty.setraw(self.slave_fd)  # no echo, no line handling, like a serial adapter
        self.device = os.ttyname(self.slave_fd)
        if os.path.islink(link_path) or os.path.exists(link_path):
            os.unlink(link_path)
        os.symlink(self.device, link_path)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        while not self._stop.is_set():
            ready, _, _ = select.select([self.master_fd], [], [], 0.05)
            if not ready:
                continue
            try:
                data = os.read(self.master_fd, 256)
            except OSError:
                continue
            reply = self.bus.feed(data)
            if reply:
                os.write(self.master_fd, reply)

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
