"""Tests of the radio-link watchdog core (no ROS, no hardware)."""

import pytest

from homemy_manual_drive.controller_link import (
    EV_SYN,
    EVENT_SIZE,
    EventDecoder,
    InputDevice,
    LinkMonitor,
    SYN_REPORT,
    ambiguous_motion_devices,
    encode_event,
    find_motion_device,
    list_input_devices,
)

EV_ABS = 0x03
EV_MSC = 0x04
MSC_TIMESTAMP = 0x05


def motion_report(timestamp_us):
    return (
        encode_event(EV_ABS, 0x00, 12)
        + encode_event(EV_MSC, MSC_TIMESTAMP, timestamp_us)
        + encode_event(EV_SYN, SYN_REPORT, 0)
    )


def make_sysfs(tmp_path, names):
    root = tmp_path / "sys" / "class" / "input"
    for index, name in enumerate(names):
        device = root / f"event{index}" / "device"
        device.mkdir(parents=True)
        (device / "name").write_text(name + "\n")
    return root


def test_lists_devices_with_names(tmp_path):
    root = make_sysfs(
        tmp_path,
        ["Wireless Controller", "Wireless Controller Motion Sensors", "Wireless Controller Touchpad"],
    )
    devices = list_input_devices(str(root), "/dev/input")
    assert devices[1] == InputDevice("/dev/input/event1", "Wireless Controller Motion Sensors")


def test_missing_sysfs_gives_no_devices(tmp_path):
    assert list_input_devices(str(tmp_path / "nothing")) == []


def test_finds_only_the_motion_sensor_device():
    devices = [
        InputDevice("/dev/input/event3", "Wireless Controller"),
        InputDevice("/dev/input/event4", "Wireless Controller Touchpad"),
        InputDevice("/dev/input/event5", "Wireless Controller Motion Sensors"),
    ]
    assert find_motion_device(devices).event_path == "/dev/input/event5"
    assert find_motion_device(devices[:2]) is None


def test_usb_name_with_vendor_prefix_also_matches():
    devices = [InputDevice("/dev/input/event9", "Sony Interactive Entertainment Wireless Controller Motion Sensors")]
    assert find_motion_device(devices) is not None


def test_two_controllers_are_ambiguous():
    devices = [
        InputDevice("/dev/input/event5", "Wireless Controller Motion Sensors"),
        InputDevice("/dev/input/event8", "Wireless Controller Motion Sensors"),
    ]
    assert ambiguous_motion_devices(devices)
    assert not ambiguous_motion_devices(devices[:1])


def test_decoder_counts_reports_across_split_reads():
    decoder = EventDecoder()
    data = motion_report(1000) + motion_report(5000)
    assert len(data) == 6 * EVENT_SIZE
    assert decoder.feed(data[:10]) == 0
    assert decoder.feed(data[10 : 3 * EVENT_SIZE]) == 1
    assert decoder.feed(data[3 * EVENT_SIZE :]) == 1


def test_decoder_ignores_events_without_report_end():
    decoder = EventDecoder()
    assert decoder.feed(encode_event(EV_ABS, 0, 5) + encode_event(EV_MSC, MSC_TIMESTAMP, 9)) == 0


def test_link_is_down_before_any_report():
    monitor = LinkMonitor(0.15)
    assert not monitor.link_up(10.0)
    assert monitor.age(10.0) is None


def test_link_follows_report_age():
    monitor = LinkMonitor(0.15)
    monitor.note_reports(1, 10.0)
    assert monitor.link_up(10.10)
    assert monitor.link_up(10.149)
    assert not monitor.link_up(10.16)


def test_zero_reports_do_not_refresh_the_link():
    monitor = LinkMonitor(0.15)
    monitor.note_reports(1, 10.0)
    monitor.note_reports(0, 10.2)
    assert not monitor.link_up(10.2)


def test_device_loss_drops_the_link_at_once():
    monitor = LinkMonitor(0.15)
    monitor.note_reports(3, 10.0)
    monitor.device_lost()
    assert not monitor.link_up(10.01)


def test_clock_going_backwards_counts_as_down():
    monitor = LinkMonitor(0.15)
    monitor.note_reports(1, 10.0)
    assert not monitor.link_up(9.0)


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_timeout_is_refused(bad):
    with pytest.raises(ValueError):
        LinkMonitor(bad)
