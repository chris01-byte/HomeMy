"""Tests of the simulated STL-27L serial stream (no ROS)."""

import math
import os
import time

import numpy as np
import pytest

from homemy_simulation import stl27l_sim as sim

# Checksum table of the vendor driver (lipkg.cpp), first and last entries.
VENDOR_TABLE_START = [0x00, 0x4D, 0x9A, 0xD7, 0x79, 0x34, 0xE3, 0xAE, 0xF2, 0xBF, 0x68, 0x25]
VENDOR_TABLE_END = [0x7F, 0x32, 0xE5, 0xA8]


def room(angles):
    """A wall 2 m away everywhere, and a target 0.5 m away at 90 degrees counter-clockwise."""

    degrees = np.degrees(np.asarray(angles)) % 360.0
    return np.where(np.abs(degrees - 90.0) < 3.0, 0.5, 2.0)


def test_checksum_table_matches_the_vendor_driver():
    assert sim._CRC_TABLE[:12] == VENDOR_TABLE_START
    assert sim._CRC_TABLE[-4:] == VENDOR_TABLE_END
    assert sim.crc8(b"") == 0


def test_packet_layout_and_round_trip():
    packet = sim.encode_packet(3600, 35900, range(100, 112), [200] * 12, 35900 + 183, 4242)
    assert len(packet) == sim.PACKET_SIZE == 47
    assert packet[0] == 0x54 and packet[1] == 0x2C
    decoded = sim.decode_packet(packet)
    assert decoded["speed_dps"] == 3600
    assert decoded["distances_mm"] == list(range(100, 112))
    assert decoded["intensities"] == [200] * 12
    assert decoded["timestamp_ms"] == 4242
    # Across the seam: 359.00 degrees on, ending at 0.83 degrees.
    assert decoded["angles_deg"][0] == pytest.approx(359.0)
    assert decoded["angles_deg"][-1] == pytest.approx(0.76, abs=0.1)


def test_damaged_packet_is_rejected():
    packet = bytearray(sim.encode_packet(3600, 0, [1000] * 12, [200] * 12, 183, 1))
    packet[10] ^= 0x01
    assert sim.decode_packet(bytes(packet)) is None
    assert sim.decode_packet(b"\x54\x2c") is None
    with pytest.raises(ValueError):
        sim.encode_packet(3600, 0, [1000] * 11, [200] * 11, 183, 1)


def read_points(device, packets):
    data = device.packets(packets)
    assert len(data) == packets * sim.PACKET_SIZE
    angles, distances = [], []
    for start in range(0, len(data), sim.PACKET_SIZE):
        decoded = sim.decode_packet(data[start:start + sim.PACKET_SIZE])
        assert decoded is not None
        angles.extend(decoded["angles_deg"])
        distances.extend(decoded["distances_mm"])
    return np.array(angles), np.array(distances)


def test_device_counts_clockwise_and_measures_in_millimetres():
    device = sim.Stl27lDevice(room, speed_wander_dps=0.0)
    angles, distances = read_points(device, 180)  # one revolution
    assert angles[0] == pytest.approx(0.0)
    steps = np.diff(angles)
    assert np.all((steps > 0.15) & (steps < 0.18))  # rising = clockwise for this device
    # The target at 90 degrees counter-clockwise is at 270 degrees for the device.
    near = angles[distances < 1000]
    assert near.min() == pytest.approx(267.0, abs=0.3)
    assert near.max() == pytest.approx(273.0, abs=0.3)
    assert set(np.unique(distances)) == {500, 2000}


def test_points_per_revolution_change_with_the_turning_speed():
    device = sim.Stl27lDevice(room, speed_wander_dps=25.0, seed=3)
    angles, _ = read_points(device, 180 * 30)
    turns = np.flatnonzero(np.diff(angles) < -180.0)
    counts = np.diff(turns)
    assert len(counts) >= 25
    assert len(set(counts.tolist())) > 3
    assert 2100 < counts.min() and counts.max() < 2220
    assert sim.points_per_revolution(3600.0) == pytest.approx(2160.0)


def test_nothing_measured_is_sent_as_zero():
    device = sim.Stl27lDevice(lambda angles: np.full(len(angles), np.nan), speed_wander_dps=0.0)
    data = device.packets(1)
    decoded = sim.decode_packet(data)
    assert decoded["distances_mm"] == [0] * 12
    assert decoded["intensities"] == [0] * 12


def test_stream_sends_in_real_time_through_the_pseudo_terminal(tmp_path):
    link = str(tmp_path / "lidar")
    stream = sim.PtyStream(sim.Stl27lDevice(room), link)
    try:
        assert os.path.islink(link)
        reader = os.open(link, os.O_RDONLY | os.O_NONBLOCK)
        received = bytearray()
        start = time.monotonic()
        while time.monotonic() - start < 1.0:
            try:
                received += os.read(reader, 65536)
            except BlockingIOError:
                time.sleep(0.005)
        os.close(reader)
        packets = [received[i:i + 47] for i in range(0, len(received) - 46, 47)]
        valid = sum(sim.decode_packet(bytes(p)) is not None for p in packets)
        # 1800 packets per second; allow for a slow test machine.
        assert 0.6 * sim.expected_packet_rate() < valid <= 1.1 * sim.expected_packet_rate()

        stream.silent = True
        time.sleep(0.2)
        reader = os.open(link, os.O_RDONLY | os.O_NONBLOCK)
        try:
            os.read(reader, 65536)
        except BlockingIOError:
            pass
        time.sleep(0.3)
        try:
            late = os.read(reader, 65536)
        except BlockingIOError:
            late = b""
        os.close(reader)
        assert late == b""
    finally:
        stream.close()
    assert not os.path.exists(link)
