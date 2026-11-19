"""The global search in the synthetic test apartment (no ROS).

A LiDAR-like map of the apartment is built from the world file, scans are
simulated at several poses with the test stand's own LiDAR model (noise,
self-returns, blind-sector mask), and the search must find each pose again.
"""

import math
import pathlib

import numpy as np
import pytest
import yaml

from homemy_lidar_bringup.scan_mask_core import apply_mask, build_sectors
from homemy_navigation.global_scan_matcher import MapScorer, search_global_pose
from homemy_navigation.relocalization_core import SearchConfig, SearchPlanner
from homemy_simulation.world import FloorPlanWorld, RobotGeometry

SRC = pathlib.Path(__file__).resolve().parents[2]
RESOLUTION = 0.05
ORIGIN = (-0.5, -1.2)


@pytest.fixture(scope="module")
def geometry():
    data = yaml.safe_load((SRC / "homemy_description" / "config" / "geometry.yaml").read_text())
    return RobotGeometry.from_yaml_dict(data)


@pytest.fixture(scope="module")
def world(geometry):
    return FloorPlanWorld.from_file(str(SRC / "homemy_simulation" / "worlds" / "testwohnung.json"), geometry)


@pytest.fixture(scope="module")
def sectors():
    params = yaml.safe_load((SRC / "homemy_lidar_bringup" / "config" / "scan_mask.yaml").read_text())[
        "scan_mask"]["ros__parameters"]
    return build_sectors(params["sector_start_deg"], params["sector_end_deg"], params["margin_deg"])


def lidar_like_map(world, size=(220, 130)):
    """Free inside rooms and doors, occupied only where a wall borders free space."""

    width, height = size
    grid = np.full((height, width), -1, dtype=np.int16)
    ys, xs = np.mgrid[0:height, 0:width]
    centres = np.stack(
        (ORIGIN[0] + (xs.ravel() + 0.5) * RESOLUTION, ORIGIN[1] + (ys.ravel() + 0.5) * RESOLUTION), axis=1)
    solid = np.zeros(len(centres), dtype=bool)
    for obstacle in world.obstacles:
        low, high = obstacle.min(axis=0), obstacle.max(axis=0)
        solid |= (centres >= low).all(axis=1) & (centres <= high).all(axis=1)
    open_space = np.array([world.room_of(c) is not None for c in centres])
    for x0, x1, y0, y1 in world.doors:
        open_space |= (centres[:, 0] >= x0) & (centres[:, 0] <= x1) & (centres[:, 1] >= y0) & (centres[:, 1] <= y1)
    flat = grid.ravel()
    flat[open_space & ~solid] = 0
    flat[solid] = 100
    free = grid == 0
    beside_free = np.zeros_like(free)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        beside_free |= np.roll(np.roll(free, dy, axis=0), dx, axis=1)
    grid[(grid == 100) & ~beside_free] = -1
    return grid


def scan_points(world, sectors, pose, rng, beams=720):
    world.pose[:] = pose
    angles, ranges = world.laser(beams, 25.0, 0.01, rng)
    ranges = apply_mask(ranges, float(angles[0]), 2 * math.pi / beams, sectors)
    valid = np.isfinite(ranges) & (ranges > 0.1) & (ranges < 12.0)
    return np.stack((ranges[valid] * np.cos(angles[valid]), ranges[valid] * np.sin(angles[valid])), axis=1)


@pytest.fixture(scope="module")
def scorer(world):
    return MapScorer(lidar_like_map(world), RESOLUTION, ORIGIN[0], ORIGIN[1])


def search(scorer, geometry, points):
    return search_global_pose(
        scorer, points,
        laser_translation_x=geometry.lidar_xy[0], laser_translation_y=geometry.lidar_xy[1], laser_yaw_rad=0.0)


@pytest.mark.parametrize(
    "pose",
    [
        (6.2, 0.6, 0.0),      # kitchen: nearly symmetric under a half turn
        (7.0, 0.9, 2.5),      # kitchen, the hardest of the tried poses
        (0.6, 0.5, 2.0),      # corner of the living room
        (5.4, 3.0, 1.2),      # hall
        (8.3, 2.2, 0.0),      # bedroom
    ],
)
def test_search_finds_the_pose_and_two_scans_agree(world, geometry, sectors, scorer, pose):
    rng = np.random.default_rng(11)
    planner = SearchPlanner(SearchConfig())
    found = None
    now = 0.0
    for _ in range(2):
        points = scan_points(world, sectors, pose, rng)
        assert planner.may_start(now, None, True, len(points))
        planner.note_started()
        found = planner.note_result(now + 3.0, search(scorer, geometry, points))
        now += 6.0
    assert found is not None, planner.last_reason
    assert math.hypot(found.x_m - pose[0], found.y_m - pose[1]) <= 0.08
    yaw_error = math.atan2(math.sin(found.yaw_rad - pose[2]), math.cos(found.yaw_rad - pose[2]))
    assert abs(math.degrees(yaw_error)) <= 3.0


def test_a_fully_symmetric_room_is_refused(geometry):
    # A closed rectangular room: a pose and the same pose turned by half a
    # turn about the room's centre explain the scan equally well.
    room = FloorPlanWorld(geometry, (1.2, 1.0, 0.4), {"room": (0.0, 3.0, 0.0, 2.4)})
    scorer = MapScorer(lidar_like_map(room, size=(90, 80)), RESOLUTION, ORIGIN[0], ORIGIN[1])
    rng = np.random.default_rng(5)
    planner = SearchPlanner(SearchConfig())
    sectors = build_sectors([], [], 0.0)
    for attempt in range(3):
        points = scan_points(room, sectors, (1.2, 1.0, 0.4), rng)
        planner.note_started()
        assert planner.note_result(float(attempt), search(scorer, geometry, points)) is None
    assert planner.last_reason.startswith("not_unique_or_weak")


def test_robot_close_to_a_wall_is_a_candidate(world, scorer):
    # base_link is only 0.11 m behind the front edge: a robot facing a wall
    # 5 cm away has base_link 0.16 m from it. Amadeus' 0.40 m would exclude it.
    xs, ys = scorer.candidate_positions()
    wall_x = 4.6  # east wall of the living room
    near_wall = (np.abs(xs - (wall_x - 0.17)) <= 0.06) & (ys > 0.5) & (ys < 2.0)
    assert near_wall.any()
