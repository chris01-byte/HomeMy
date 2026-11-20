"""Tests of the simulated ESS23-RS motors, including the real Modbus client."""

import os

import pytest

from homemy_simulation.ess23_sim import (
    COMMAND_START,
    COMMAND_STOP,
    REG_COMMAND,
    REG_POSITION,
    REG_SETPOINT,
    Ess23Bus,
    Ess23Motor,
    PtyBusServer,
    crc16,
    with_crc,
)


def request(motor_id, function, address, value):
    return with_crc(bytes((motor_id, function, address >> 8, address & 0xFF, value >> 8, value & 0xFF)))


def test_crc_matches_the_modbus_reference_vector():
    # Read 10 registers from address 0 of device 1: CRC bytes C5 CD.
    frame = bytes((0x01, 0x03, 0x00, 0x00, 0x00, 0x0A))
    assert with_crc(frame)[-2:] == bytes((0xC5, 0xCD))
    assert crc16(with_crc(frame)) == 0


def test_setpoint_start_and_stop():
    bus = Ess23Bus([Ess23Motor(1), Ess23Motor(2)])
    motor = bus.motors[1]
    assert bus.feed(request(1, 0x06, REG_SETPOINT, (-120) & 0xFFFF)) == request(1, 0x06, REG_SETPOINT, (-120) & 0xFFFF)
    assert motor.setpoint_rpm == -120
    assert motor.target_rpm() == 0.0  # no start impulse yet
    bus.feed(request(1, 0x06, REG_COMMAND, COMMAND_START))
    assert motor.target_rpm() == -120.0
    bus.feed(request(1, 0x06, REG_SETPOINT, 60))
    assert motor.target_rpm() == 60.0  # a running motor follows a new setpoint
    bus.feed(request(1, 0x06, REG_COMMAND, COMMAND_STOP))
    assert motor.target_rpm() == 0.0
    assert bus.motors[2].target_rpm() == 0.0


def test_position_block_follows_the_word_order():
    high_first = Ess23Motor(1, high_word_first=True, position_counts=-2, speed_rpm=-30.0)
    low_first = Ess23Motor(2, high_word_first=False, position_counts=0x00012345, speed_rpm=30.0)
    bus = Ess23Bus([high_first, low_first])
    reply = bus.feed(request(1, 0x03, REG_POSITION, 3))
    assert reply[:3] == bytes((1, 3, 6))
    assert reply[3:9] == bytes((0xFF, 0xFF, 0xFF, 0xFE, 0xFF, 0xE2))  # -2 as uint32, -30 rpm
    reply = bus.feed(request(2, 0x03, REG_POSITION, 3))
    assert reply[3:9] == bytes((0x23, 0x45, 0x00, 0x01, 0x00, 0x1E))


def test_unknown_register_function_and_address():
    bus = Ess23Bus([Ess23Motor(1)])
    assert bus.feed(request(1, 0x03, 0x0300, 1))[:3] == bytes((1, 0x83, 0x02))
    assert bus.feed(request(1, 0x06, 0x0300, 1))[:3] == bytes((1, 0x86, 0x02))
    assert bus.feed(request(1, 0x10, 0x0000, 1))[:3] == bytes((1, 0x90, 0x01))
    assert bus.feed(request(9, 0x03, REG_POSITION, 1)) == b""  # not our device: silence


def test_garbage_and_split_frames_are_survived():
    bus = Ess23Bus([Ess23Motor(1)])
    frame = request(1, 0x03, REG_POSITION, 3)
    assert bus.feed(b"\x00\xff" + frame[:3]) == b""
    reply = bus.feed(frame[3:])
    assert reply[:2] == bytes((1, 3))
    assert bus.crc_errors >= 1


def test_real_modbus_client_over_the_pseudo_terminal(tmp_path):
    pymodbus = pytest.importorskip("pymodbus")
    from pymodbus.client import ModbusSerialClient

    motors = [Ess23Motor(1), Ess23Motor(2, position_counts=123456)]
    link = str(tmp_path / "drive")
    server = PtyBusServer(Ess23Bus(motors), link)
    client = ModbusSerialClient(port=link, baudrate=115200, bytesize=8, parity="N", stopbits=1, timeout=0.2, retries=0)
    try:
        assert os.path.islink(link)
        assert client.connect()
        keyword = "device_id" if tuple(int(p) for p in pymodbus.__version__.split(".")[:2]) >= (3, 10) else "slave"
        result = client.read_holding_registers(REG_POSITION, count=3, **{keyword: 2})
        assert not result.isError()
        assert (result.registers[0] << 16 | result.registers[1]) == 123456
        assert not client.write_register(REG_SETPOINT, 200, **{keyword: 1}).isError()
        assert not client.write_register(REG_COMMAND, COMMAND_START, **{keyword: 1}).isError()
        assert motors[0].target_rpm() == 200.0
        assert client.read_holding_registers(0x0300, count=1, **{keyword: 1}).isError()
    finally:
        client.close()
        server.close()
    assert not os.path.exists(link)
