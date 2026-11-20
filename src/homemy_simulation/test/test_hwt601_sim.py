"""Tests of the simulated HWT601 (no ROS), including the real HomeMy reader over a pseudo-terminal."""

import math

import pytest

from homemy_simulation.ess23_sim import PtyBusServer, with_crc
from homemy_simulation.hwt601_sim import Hwt601Bus, motion_registers, to_register
from homemy_state_estimation.hwt601_protocol import (
    build_read_holding_registers,
    decode_motion_registers,
    parse_read_holding_response,
)
from homemy_state_estimation.hwt601_transport import Hwt601SerialTransport, Hwt601TransportError

STILL = ((0.0, 0.0, 9.80665), (0.0, 0.0, 0.0))


def test_registers_use_the_sensors_scales():
    assert to_register(1.0, 4.0) == 8192
    assert to_register(-1.0, 4.0) == 0x10000 - 8192
    assert to_register(99.0, 4.0) == 32767          # clipped, never wrapped
    assert to_register(-99.0, 4.0) == 0x8000
    registers = motion_registers((0.0, 0.0, 9.80665), (0.0, 0.0, math.radians(100.0)))
    assert registers == (0, 0, 8192, 0, 0, 8192)


def test_bus_answers_the_readers_request_and_the_reader_decodes_it():
    bus = Hwt601Bus(lambda: ((0.0, 0.0, 9.80665), (0.01, -0.02, 0.5)))
    reply = bus.feed(build_read_holding_registers(0x50, 0x34, 6))
    sample = decode_motion_registers(parse_read_holding_response(reply, 0x50, 6))
    assert sample.linear_acceleration_mps2 == pytest.approx((0.0, 0.0, 9.80665), abs=0.002)
    assert sample.angular_velocity_radps == pytest.approx((0.01, -0.02, 0.5), abs=0.0003)
    assert bus.requests == 1 and bus.non_read_requests == 0


def test_writes_and_foreign_requests_are_refused_and_counted():
    bus = Hwt601Bus(lambda: STILL)
    write = with_crc(bytes((0x50, 0x06, 0x00, 0x69, 0xB5, 0x88)))  # an unlock command of this sensor family
    assert bus.feed(write) == with_crc(bytes((0x50, 0x86, 0x01)))
    assert bus.non_read_requests == 1
    assert bus.feed(build_read_holding_registers(0x01, 0x34, 6)) == b""       # a motor's address
    assert bus.feed(build_read_holding_registers(0x50, 0x00, 6)) == with_crc(bytes((0x50, 0x83, 0x02)))
    assert bus.feed(b"\x50\x03\x00\x34\x00\x06\x00\x00") == b""                # broken checksum
    assert bus.crc_errors >= 1


def test_faults_silent_and_corrupt():
    bus = Hwt601Bus(lambda: STILL)
    request = build_read_holding_registers(0x50, 0x34, 6)
    bus.silent = True
    assert bus.feed(request) == b""
    bus.silent = False
    bus.corrupt = True
    with pytest.raises(ValueError, match="CRC"):
        parse_read_holding_response(bus.feed(request), 0x50, 6)


def test_real_reader_over_a_pseudo_terminal(tmp_path):
    rate = [0.25]
    bus = Hwt601Bus(lambda: ((0.0, 0.0, 9.80665), (0.0, 0.0, rate[0])))
    link = str(tmp_path / "imu")
    server = PtyBusServer(bus, link)
    try:
        with Hwt601SerialTransport(link, 115200, 0.2, 0x50) as transport:
            for expected in (0.25, -0.4):
                rate[0] = expected
                sample = decode_motion_registers(transport.read_motion_registers())
                assert sample.angular_velocity_radps[2] == pytest.approx(expected, abs=0.0003)
            bus.silent = True
            with pytest.raises(Hwt601TransportError) as error:
                transport.read_motion_registers()
            assert error.value.kind == "response_deadline"
            bus.silent = False
            assert decode_motion_registers(transport.read_motion_registers()).angular_velocity_radps[2] == \
                pytest.approx(-0.4, abs=0.0003)
        assert bus.non_read_requests == 0
        assert bus.requests >= 3
    finally:
        server.close()
