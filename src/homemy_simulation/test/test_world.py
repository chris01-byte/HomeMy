"""Tests of the test-stand world (no ROS)."""

import json
import math
import pathlib

import numpy as np
import pytest
import yaml

from homemy_simulation.world import (
    FloorPlanWorld,
    RobotGeometry,
    body_clearance,
    drive_step,
    raycast,
    rectangle,
    subtract_box,
)

SRC = pathlib.Path(__file__).resolve().parents[2]
GEOMETRY = yaml.safe_load((SRC / "homemy_description" / "config" / "geometry.yaml").read_text())
WORLD_FILE = SRC / "homemy_simulation" / "worlds" / "testwohnung.json"


@pytest.fixture(scope="module")
def robot():
    return RobotGeometry.from_yaml_dict(GEOMETRY)


@pytest.fixture
def world(robot):
    return FloorPlanWorld.from_file(str(WORLD_FILE), robot)


def test_subtract_box_cuts_a_door():
    pieces = subtract_box((0.0, 0.1, 0.0, 4.0), (0.0, 0.1, 1.0, 1.85))
    assert sorted(pieces) == [(0.0, 0.1, 0.0, 1.0), (0.0, 0.1, 1.85, 4.0)]


def test_raycast_hits_the_near_face():
    box = rectangle(2.0, 2.5, -1.0, 1.0)
    ranges = raycast([box], (0.0, 0.0), np.array([0.0, math.pi]), maximum=10.0)
    assert ranges[0] == pytest.approx(2.0)
    assert ranges[1] == 10.0


def test_drive_model_reproduces_the_amadeus_pulse_measurement():
    # Amadeus: a 1.0 s pulse at 0.12 m/s with the slow ramp gave 0.0439 m.
    velocity = np.zeros(2)
    distance = 0.0
    dt = 0.01
    for step in range(300):
        target = (0.12, 0.0) if step < 100 else (0.0, 0.0)
        velocity = drive_step(velocity, target, dt, 1.3, 0.15, 0.3845)
        distance += velocity[0] * dt
    assert distance == pytest.approx(0.0439, rel=0.06)


def test_geometry_comes_from_the_robot_model(robot):
    assert robot.wheel_separation == pytest.approx(0.3994)
    assert robot.lidar_xy == pytest.approx((0.0694, 0.0))
    assert len(robot.self_occluders) == 2 + 6


def test_start_pose_is_free_and_in_the_living_room(world):
    assert world.room_of(world.pose[:2]) == "wohnzimmer"
    assert body_clearance(world.pose, world.obstacles, world.geometry, 0.0) > 0.2


def test_doors_are_open_and_walls_closed(world):
    # From the living room towards the hall door at y 3.03, and next to it.
    door = raycast(world.obstacles, (4.2, 3.03), np.array([0.0]), 20.0)[0]
    wall = raycast(world.obstacles, (4.2, 2.2), np.array([0.0]), 20.0)[0]
    assert door > 1.5
    assert wall == pytest.approx(0.4, abs=1e-6)


def test_driving_into_a_wall_counts_as_collision(world):
    world.pose[:] = (4.0, 1.0, 0.0)
    world.checked_pose = None
    for _ in range(600):
        world.integrate((0.2, 0.0), 0.01)
    assert world.collision


def test_turning_on_the_spot_keeps_position(world):
    x, y, _ = world.pose
    for _ in range(300):
        world.integrate((0.0, 0.7), 0.01)
    assert world.pose[0] == pytest.approx(x, abs=1e-9)
    assert world.pose[1] == pytest.approx(y, abs=1e-9)
    assert world.travel == pytest.approx(0.0, abs=1e-9)


def test_late_ticks_are_split(world):
    world.integrate_span((0.1, 0.0), 0.095)
    assert world.travel > 0.0
    with pytest.raises(ValueError):
        world.integrate((0.1, 0.0), 0.05)


def test_scan_contains_self_returns_from_struts_and_webs(world):
    angles, ranges = world.laser(beams=2160, maximum=25.0)
    short = ranges < 0.40
    bearings = np.degrees(angles[short])
    # The robot's own parts appear only at the sides and the rear quarters.
    assert short.any()
    assert np.all(np.abs(bearings) > 70.0)
    assert np.any(np.abs(bearings) > 155.0)  # rear webs


def test_self_returns_lie_inside_the_mask_sectors(world):
    mask = yaml.safe_load((SRC / "homemy_lidar_bringup" / "config" / "scan_mask.yaml").read_text())
    params = mask["scan_mask"]["ros__parameters"]
    margin = params["margin_deg"]
    sectors = list(zip(params["sector_start_deg"], params["sector_end_deg"]))
    angles = -math.pi + np.arange(4320) * 2 * math.pi / 4320
    own = world.self_returns(angles, 25.0)
    for bearing in np.degrees(angles[own < 25.0]):
        assert any(start - margin <= bearing <= end + margin for start, end in sectors), bearing


def test_mapping_route_is_drivable(world, robot):
    """Every leg keeps 5 cm to obstacles; every turn has room to rotate."""

    data = json.loads(WORLD_FILE.read_text())
    points = [tuple(world.start[:2])] + [tuple(p) for p in data["mapping_route"]["waypoints"]]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        heading = math.atan2(y1 - y0, x1 - x0)
        for f in np.linspace(0.0, 1.0, 40):
            pose = (x0 + f * (x1 - x0), y0 + f * (y1 - y0), heading)
            assert body_clearance(pose, world.obstacles, robot, 0.05) > 0.0, (x0, y0, x1, y1, f)
    for x, y in points:
        for yaw in np.linspace(-math.pi, math.pi, 36):
            assert body_clearance((x, y, yaw), world.obstacles, robot, 0.04) > 0.0, (x, y, yaw)
    assert {world.room_of(p) for p in points} == set(world.rooms)


def perfect_grid(world, resolution=0.05, origin=(-0.5, -1.2), size=(220, 130)):
    width, height = size
    grid = np.full((height, width), -1, dtype=int)
    ys, xs = np.mgrid[0:height, 0:width]
    centres = np.stack(
        (origin[0] + (xs.ravel() + 0.5) * resolution, origin[1] + (ys.ravel() + 0.5) * resolution), axis=1
    )
    inside = np.zeros(len(centres), dtype=bool)
    for obstacle in world.obstacles:
        low, high = obstacle.min(axis=0), obstacle.max(axis=0)
        inside |= (centres >= low).all(axis=1) & (centres <= high).all(axis=1)
    in_room = np.array([world.room_of(c) is not None for c in centres])
    grid.ravel()[in_room & ~inside] = 0
    grid.ravel()[inside] = 100
    return grid


def surface_only(grid):
    """Keep only occupied cells next to free space, as a LiDAR map has them."""

    free = grid == 0
    near_free = np.zeros_like(free)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        near_free |= np.roll(np.roll(free, dy, axis=0), dx, axis=1)
    result = grid.copy()
    result[(grid == 100) & ~near_free] = -1
    return result


def test_alignment_separates_a_rotated_map_from_a_wrong_one(world):
    grid = surface_only(perfect_grid(world))
    # The same perfect map, but placed 1.5 degrees rotated about the world origin.
    result = world.map_error(grid, 0.05, (-0.5, -1.2), (0.0, 0.0, math.radians(1.5)))
    assert result["max_occupied_error_m"] > 0.15
    assert result["aligned_p95_error_m"] <= 0.04
    assert abs(abs(result["alignment_rotation_deg"]) - 1.5) < 0.3


def test_map_error_of_a_perfect_map_is_small(world):
    resolution = 0.05
    origin = (-0.5, -1.2)
    width, height = 220, 130
    grid = np.full((height, width), -1, dtype=int)
    ys, xs = np.mgrid[0:height, 0:width]
    centres = np.stack(
        (origin[0] + (xs.ravel() + 0.5) * resolution, origin[1] + (ys.ravel() + 0.5) * resolution), axis=1
    )
    inside = np.zeros(len(centres), dtype=bool)
    for obstacle in world.obstacles:
        low, high = obstacle.min(axis=0), obstacle.max(axis=0)
        inside |= (centres >= low).all(axis=1) & (centres <= high).all(axis=1)
    in_room = np.array([world.room_of(c) is not None for c in centres])
    grid.ravel()[in_room & ~inside] = 0
    grid.ravel()[inside] = 100
    result = world.map_error(grid, resolution, origin, (0.0, 0.0, 0.0))
    assert result["max_occupied_error_m"] <= resolution
    assert result["free_fraction_known"] > 0.9


def test_invalid_worlds_are_refused(robot):
    with pytest.raises(ValueError):
        FloorPlanWorld(robot, (10.0, 10.0, 0.0), {"a": (0.0, 2.0, 0.0, 2.0)})
    with pytest.raises(ValueError):
        FloorPlanWorld(robot, (1.0, 1.0, 0.0), {})
    with pytest.raises(ValueError):
        FloorPlanWorld(robot, (0.1, 1.0, 0.0), {"a": (0.0, 2.0, 0.0, 2.0)})
