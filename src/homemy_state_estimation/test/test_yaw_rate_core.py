"""Tests of the yaw-rate aid (no ROS)."""

import math
import pathlib
import random

import pytest
import yaml

from homemy_state_estimation.yaw_rate_core import YawRateAid, YawRateConfig

RATE_HZ = 100.0


class Bench:
    """Feeds wheel odometry at 50 Hz and gyro samples at 100 Hz."""

    def __init__(self, bias=0.004, noise=0.002, **config):
        self.aid = YawRateAid(YawRateConfig(**config))
        self.bias = bias
        self.noise = noise
        self.rng = random.Random(4)
        self.now = 100.0
        self.out = []

    def run(self, seconds, wheel=(0.0, 0.0), true_rate=None, axis_values=None, wheel_silent=False):
        """true_rate defaults to what the wheels report."""

        true_rate = wheel[1] if true_rate is None else true_rate
        steps = int(round(seconds * RATE_HZ))
        produced = []
        for step in range(steps):
            self.now += 1.0 / RATE_HZ
            if step % 2 == 0 and not wheel_silent:
                self.aid.on_wheel(self.now, wheel[0], wheel[1])
            measured = true_rate + self.bias + self.rng.gauss(0.0, self.noise)
            values = axis_values(measured) if axis_values else (0.0, 0.0, measured)
            rate = self.aid.on_imu(self.now, values)
            if rate is not None:
                produced.append(rate)
        self.out.extend(produced)
        return produced


def test_no_output_before_the_bias_is_learned():
    bench = Bench()
    assert bench.run(3.0) == []
    assert bench.aid.status(bench.now)["ready"] is False
    assert bench.aid.status(bench.now)["reason"] == "learning_bias"


def test_bias_is_learned_at_standstill_and_removed():
    bench = Bench(bias=0.004)
    bench.run(7.0)
    assert bench.aid.bias == pytest.approx(0.004, abs=0.0005)
    turning = bench.run(4.0, wheel=(0.0, 0.5))
    assert sum(turning) / len(turning) == pytest.approx(0.5, abs=0.001)
    assert bench.aid.status(bench.now)["ready"] is True


def test_driving_at_start_gives_no_bias_and_no_output():
    bench = Bench()
    assert bench.run(10.0, wheel=(0.2, 0.3)) == []
    assert bench.aid.bias is None
    assert bench.aid.status(bench.now)["reason"] == "waiting_for_standstill"


def test_motion_is_never_learned_as_bias():
    bench = Bench(bias=0.004)
    bench.run(7.0)
    learned = bench.aid.bias
    bench.run(60.0, wheel=(0.1, 0.4))
    assert bench.aid.bias == learned


def test_bias_follows_a_slow_drift_while_standing():
    bench = Bench(bias=0.004)
    bench.run(7.0)
    bench.bias = 0.010
    bench.run(120.0)
    assert bench.aid.bias == pytest.approx(0.010, abs=0.001)


def test_turned_by_hand_while_the_wheels_stand_is_not_learned_but_is_reported():
    """Someone turns the standing robot: the wheels see nothing, the gyro does."""

    bench = Bench(bias=0.004)
    bench.run(7.0)
    learned = bench.aid.bias
    rates = bench.run(4.0, true_rate=0.4)
    assert bench.aid.bias == pytest.approx(learned, abs=1e-6)
    assert sum(rates) / len(rates) == pytest.approx(0.4, abs=0.002)
    status = bench.aid.status(bench.now)
    assert status["gyro_minus_wheel_yaw_deg"] == pytest.approx(math.degrees(1.6), abs=1.0)


def test_unsteady_window_is_rejected_and_tried_again():
    bench = Bench(bias=0.004)
    bench.run(6.5, true_rate=0.3)  # wheels still, but the robot is being turned
    assert bench.aid.bias is None
    assert bench.aid.rejected_windows == 1
    assert bench.aid.status(bench.now)["reason"] == "bias_implausibly_large"
    # The window that still holds the end of the turn is rejected too; the next one is clean.
    bench.run(12.0)
    assert bench.aid.rejected_windows == 2
    assert bench.aid.bias == pytest.approx(0.004, abs=0.0005)


def test_implausibly_large_offset_is_not_accepted_as_bias():
    bench = Bench(bias=0.2)
    assert bench.run(12.0) == []
    assert bench.aid.bias is None
    assert bench.aid.rejected_windows >= 1
    assert bench.aid.status(bench.now)["reason"] == "bias_implausibly_large"


def test_shaky_standstill_is_not_accepted_as_bias():
    bench = Bench(bias=0.004, noise=0.05)
    assert bench.run(12.0) == []
    assert bench.aid.status(bench.now)["reason"] == "bias_window_unsteady"


def test_missing_wheel_odometry_means_no_standstill():
    bench = Bench()
    assert bench.run(10.0, wheel_silent=True) == []
    assert bench.aid.standing(bench.now) is False


def test_stale_wheel_odometry_stops_bias_learning():
    bench = Bench(bias=0.004)
    bench.run(7.0)
    learned = bench.aid.bias
    bench.bias = 0.02
    bench.run(30.0, wheel_silent=True)
    # Only the 0.3 s until the wheel data counts as stale can still be learned from.
    assert bench.aid.bias == pytest.approx(learned, abs=0.0005)


@pytest.mark.parametrize(
    "axis,sign,layout",
    [
        ("z", 1.0, lambda rate: (0.0, 0.0, rate)),
        ("z", -1.0, lambda rate: (0.0, 0.0, -rate)),
        ("x", 1.0, lambda rate: (rate, 0.0, 0.0)),
        ("y", -1.0, lambda rate: (0.0, -rate, 0.0)),
    ],
)
def test_mounting_axis_and_sign(axis, sign, layout):
    bench = Bench(bias=0.0, yaw_axis=axis, yaw_sign=sign)
    bench.run(7.0, axis_values=layout)
    turning = bench.run(2.0, wheel=(0.0, 0.3), axis_values=layout)
    assert sum(turning) / len(turning) == pytest.approx(0.3, abs=0.002)


def test_totals_compare_gyro_and_wheels_since_the_bias():
    """A slipping wheel: the wheels report 10 % more turn than the chassis makes."""

    bench = Bench(bias=0.004)
    bench.run(7.0)
    bench.run(10.0, wheel=(0.0, 0.33), true_rate=0.30)
    status = bench.aid.status(bench.now)
    assert status["gyro_yaw_deg"] == pytest.approx(math.degrees(3.0), abs=1.0)
    assert status["wheel_yaw_deg"] == pytest.approx(math.degrees(3.3), abs=1.0)
    assert status["gyro_minus_wheel_yaw_deg"] == pytest.approx(math.degrees(-0.3), abs=1.0)


def test_invalid_and_backward_samples_give_nothing():
    bench = Bench()
    bench.run(7.0)
    assert bench.aid.on_imu(bench.now + 0.01, (0.0, 0.0, float("nan"))) is None
    assert bench.aid.on_imu(bench.now + 0.02, (0.0, 0.0)) is None
    assert bench.aid.on_imu(bench.now - 1.0, (0.0, 0.0, 0.1)) is None
    assert bench.aid.status(bench.now)["reason"] == "imu_time_not_increasing"
    assert bench.aid.on_imu(bench.now + 0.03, (0.0, 0.0, 0.1)) is not None


def test_gap_in_the_gyro_data_is_not_integrated():
    bench = Bench(bias=0.0, noise=0.0)
    bench.run(7.0)
    bench.run(1.0, wheel=(0.0, 0.5))
    before = bench.aid.gyro_yaw
    bench.now += 5.0  # five seconds without samples
    bench.aid.on_wheel(bench.now, 0.0, 0.5)
    bench.aid.on_imu(bench.now, (0.0, 0.0, 0.5))
    assert bench.aid.gyro_yaw == pytest.approx(before, abs=1e-9)


def test_stale_gyro_is_not_ready():
    bench = Bench()
    bench.run(7.0)
    assert bench.aid.status(bench.now)["ready"] is True
    status = bench.aid.status(bench.now + 1.0)
    assert status["ready"] is False and status["reason"] == "imu_stale"


@pytest.mark.parametrize(
    "config",
    [
        {"yaw_axis": "up"},
        {"yaw_sign": 0.5},
        {"bias_window_s": 0.0},
        {"input_timeout_s": float("nan")},
        {"bias_max_abs_radps": -1.0},
    ],
)
def test_invalid_configuration_is_rejected(config):
    with pytest.raises(ValueError):
        YawRateAid(YawRateConfig(**config))


def test_delivered_configuration_is_valid_and_marked_unmeasured():
    path = pathlib.Path(__file__).resolve().parents[1] / "config" / "hwt601.yaml"
    text = path.read_text()
    config = yaml.safe_load(text)
    yaw = config["yaw_rate"]["ros__parameters"]
    fields = YawRateConfig.__dataclass_fields__
    YawRateAid(YawRateConfig(**{name: value for name, value in yaw.items() if name in fields}))
    assert "NOT MEASURED" in text
    reader = config["hwt601_imu"]["ros__parameters"]
    assert reader["port"] == "/dev/homemy_imu"
    assert reader["frame_id"] == yaw["expected_imu_frame"] == "imu_link"
    assert reader["imu_topic"] == yaw["imu_topic"]


def test_fusion_profile_takes_only_yaw_rate_from_the_gyro():
    path = pathlib.Path(__file__).resolve().parents[1] / "config" / "ekf_yaw_rate.yaml"
    ekf = yaml.safe_load(path.read_text())["odometry_ekf"]["ros__parameters"]
    assert ekf["two_d_mode"] is True
    assert ekf["imu0"] == "/imu/yaw_rate"
    assert [i for i, used in enumerate(ekf["imu0_config"]) if used] == [11]   # yaw rate only
    assert [i for i, used in enumerate(ekf["odom0_config"]) if used] == [6, 11]  # forward speed, yaw rate
    assert ekf["odom0"] == "/wheel/odom"
    assert len(ekf["process_noise_covariance"]) == 225
