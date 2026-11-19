"""World and plant model of the HomeMy test stand. Simulation only.

Ported from the Amadeus test stand (roboter_ws branch
claude/blissful-pasteur-s1eivj, commit 940a748, tools/simulation/ap06_world.py
and sh_robustheit_welt.py: World, GrundrissWelt, antrieb_schritt) and changed
for HomeMy:

- the robot outline, wheel separation, and LiDAR pose come from
  homemy_description/config/geometry.yaml instead of Amadeus constants;
- the LiDAR sits in the base at 164 mm and sees the struts and slot webs of
  its own body (self-returns), instead of a single cropped mast sector;
- VL53 near-field sensors, low obstacles, and the Amadeus evaluation helpers
  are left out (HomeMy has no VL53 and no obstacles below the scan plane in
  the laboratory);
- the world is a floor plan: rooms, door openings, and furniture as
  axis-aligned rectangles, as in GrundrissWelt.

The world never publishes a map; the product only receives sensor data.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

Box = Tuple[float, float, float, float]  # x0, x1, y0, y1


def rectangle(x0: float, x1: float, y0: float, y1: float) -> np.ndarray:
    return np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], dtype=float)


def subtract_box(box: Box, opening: Box) -> List[Box]:
    """Axis-aligned box without the opening; the remaining pieces."""

    x0, x1, y0, y1 = box
    ox0, ox1, oy0, oy1 = opening
    if ox0 >= x1 or ox1 <= x0 or oy0 >= y1 or oy1 <= y0:
        return [tuple(box)]
    pieces = [
        (x0, min(x1, ox0), y0, y1),
        (max(x0, ox1), x1, y0, y1),
        (max(x0, ox0), min(x1, ox1), y0, min(y1, oy0)),
        (max(x0, ox0), min(x1, ox1), max(y0, oy1), y1),
    ]
    return [p for p in pieces if p[1] - p[0] > 1e-9 and p[3] - p[2] > 1e-9]


@dataclass(frozen=True)
class RobotGeometry:
    """The parts of geometry.yaml the test stand needs (base_link, metres)."""

    x_min: float
    x_max: float
    y_half: float
    wheel_separation: float
    lidar_xy: Tuple[float, float]
    self_occluders: Tuple[Box, ...]  # struts and slot webs, robot-fixed

    @staticmethod
    def from_yaml_dict(geometry: dict, web_thickness_m: float = 0.006) -> "RobotGeometry":
        outline = geometry["base_outline"]
        struts = geometry["struts"]
        occluders: List[Box] = []
        for sign in (1.0, -1.0):
            y_a, y_b = sign * struts["y_inner"], sign * struts["y_outer"]
            occluders.append((struts["x_min"], struts["x_max"], min(y_a, y_b), max(y_a, y_b)))
        half = web_thickness_m / 2
        for x0, x1, y0, y1 in geometry["slot_webs"].values():
            if x0 == x1:  # web in the front or rear wall
                occluders.append((x0 - half, x0 + half, y0, y1))
            else:  # web in a side wall
                occluders.append((x0, x1, y0 - half, y0 + half))
        return RobotGeometry(
            x_min=float(outline["x_min"]),
            x_max=float(outline["x_max"]),
            y_half=float(outline["y_half"]),
            wheel_separation=float(geometry["drive_wheels"]["separation"]),
            lidar_xy=(float(geometry["lidar"]["x"]), float(geometry["lidar"]["y"])),
            self_occluders=tuple(tuple(float(v) for v in box) for box in occluders),
        )


def body(pose: Sequence[float], geometry: RobotGeometry, padding: float = 0.0) -> np.ndarray:
    """Corners of the (padded) rectangular body in the world.

    The rounded corners are left out on purpose: the test stand counts a
    collision conservatively.
    """

    x, y, yaw = pose
    c, s = math.cos(yaw), math.sin(yaw)
    corners = (
        (geometry.x_min - padding, -geometry.y_half - padding),
        (geometry.x_max + padding, -geometry.y_half - padding),
        (geometry.x_max + padding, geometry.y_half + padding),
        (geometry.x_min - padding, geometry.y_half + padding),
    )
    return np.array([(x + c * a - s * b, y + s * a + c * b) for a, b in corners])


def body_clearance(pose: Sequence[float], obstacles: Sequence[np.ndarray], geometry: RobotGeometry,
                   padding: float) -> float:
    """Distance between the padded body and the nearest obstacle; 0 on contact.

    Vectorised separating-axis test plus exact edge distances (Amadeus
    ``chassis_clearance``).
    """

    if len(obstacles) == 0:
        return math.inf
    shape, objects = body(pose, geometry, padding), np.asarray(obstacles)
    c, s = math.cos(pose[2]), math.sin(pose[2])
    axes = np.array([(1.0, 0.0), (0.0, 1.0), (c, s), (-s, c)])
    a, b = shape @ axes.T, objects @ axes.T
    separated = ((b.max(axis=1) < a.min(axis=0)) | (a.max(axis=0) < b.min(axis=1))).any(axis=1)
    distances = np.full(len(objects), math.inf)
    for points, edges in (
        (np.broadcast_to(shape, objects.shape), objects),
        (objects, np.broadcast_to(shape, objects.shape)),
    ):
        start, vector = edges, np.roll(edges, -1, axis=1) - edges
        delta = points[:, None, :, :] - start[:, :, None, :]
        fraction = np.clip(
            (delta * vector[:, :, None, :]).sum(axis=-1) / (vector * vector).sum(axis=-1)[:, :, None],
            0.0,
            1.0,
        )
        distance = np.linalg.norm(delta - fraction[..., None] * vector[:, :, None, :], axis=-1).min(axis=(1, 2))
        distances = np.minimum(distances, distance)
    return float(np.where(separated, distances, 0.0).min())


def raycast(boxes: Sequence[np.ndarray], origin: Sequence[float], angles: np.ndarray,
            maximum: float) -> np.ndarray:
    """First hit along each ray against axis-aligned boxes (slab method)."""

    directions = np.array([np.cos(angles), np.sin(angles)]).T
    result = np.full(len(directions), maximum)
    origin = np.asarray(origin, dtype=float)
    for box in boxes:
        low, high = box.min(axis=0), box.max(axis=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            t0, t1 = (low - origin) / directions, (high - origin) / directions
        parallel = abs(directions) < 1e-12
        outside = ((origin < low) | (origin > high)) & parallel
        lower = np.where(parallel, -np.inf, np.minimum(t0, t1)).max(axis=1)
        upper = np.where(parallel, np.inf, np.maximum(t0, t1)).min(axis=1)
        hit = (upper >= np.maximum(0.0, lower)) & ~outside.any(axis=1)
        result = np.minimum(result, np.where(hit, np.maximum(0.0, lower), maximum))
    return result


def drive_step(velocity: Sequence[float], target: Sequence[float], dt: float, tau_up_s: float,
               tau_down_s: float, wheel_separation: float) -> np.ndarray:
    """One time step of the two wheel drives with start and brake ramps.

    Amadeus ``antrieb_schritt``: each wheel is a first-order lag, slow when
    speeding up (``tau_up_s``) and quick when slowing down or reversing
    (``tau_down_s``). The HomeMy ramps are commissioning values.
    """

    v, w = float(velocity[0]), float(velocity[1])
    tv, tw = float(target[0]), float(target[1])
    half = wheel_separation / 2
    wheels = [v - w * half, v + w * half]
    goals = [tv - tw * half, tv + tw * half]
    new = []
    for current, goal in zip(wheels, goals):
        faster = abs(goal) > abs(current) and current * goal >= 0.0
        tau = tau_up_s if faster else tau_down_s
        new.append(current + (goal - current) * (1.0 - math.exp(-dt / tau)))
    return np.array([(new[0] + new[1]) / 2, (new[1] - new[0]) / wheel_separation])


class FloorPlanWorld:
    """A home made of rooms, door openings, and furniture, plus the robot in it.

    ``rooms``: name -> interior (x0, x1, y0, y1). ``doors``: free boxes through
    the walls. Walls are strips of ``WALL_M`` around each room, minus rooms and
    doors. ``furniture``: full-height boxes; the LiDAR sees them. Table legs are
    modelled as small boxes, because the scan plane passes under the top.
    """

    WALL_M = 0.05

    def __init__(
        self,
        geometry: RobotGeometry,
        start: Sequence[float],
        rooms: Dict[str, Box],
        doors: Iterable[Box] = (),
        furniture: Iterable[Box] = (),
        tau_up_s: float = 0.15,
        tau_down_s: float = 0.15,
        padding_m: float = 0.02,
    ) -> None:
        if not rooms:
            raise ValueError("a floor plan needs at least one room")
        if not (0.0 < tau_down_s <= tau_up_s <= 10.0):
            raise ValueError("expected 0 < tau_down_s <= tau_up_s <= 10")
        self.geometry = geometry
        self.rooms = {str(name): tuple(float(v) for v in box) for name, box in rooms.items()}
        self.doors = [tuple(float(v) for v in d) for d in doors]
        t = self.WALL_M
        strips: List[Box] = []
        for x0, x1, y0, y1 in self.rooms.values():
            strips += [
                (x0 - t, x0, y0 - t, y1 + t),
                (x1, x1 + t, y0 - t, y1 + t),
                (x0 - t, x1 + t, y0 - t, y0),
                (x0 - t, x1 + t, y1, y1 + t),
            ]
        for opening in list(self.rooms.values()) + self.doors:
            strips = [piece for wall in strips for piece in subtract_box(wall, opening)]
        self.obstacles = [rectangle(*wall) for wall in strips]
        self.obstacles += [rectangle(*(float(v) for v in item)) for item in furniture]
        self.tau_up_s = float(tau_up_s)
        self.tau_down_s = float(tau_down_s)
        self.padding_m = float(padding_m)
        self.start = np.asarray(start, dtype=float)
        self.pose = self.start.copy()
        self.velocity = np.zeros(2)
        self.wheel_angles = np.zeros(2)
        self.travel = 0.0
        self.minimum_clearance = math.inf
        self.collision = False
        self.checked_pose: Optional[tuple] = None
        if self.room_of(self.start[:2]) is None:
            raise ValueError("the start pose lies in no room")
        if body_clearance(self.pose, self.obstacles, geometry, 0.0) <= 0.0:
            raise ValueError("the robot touches an obstacle at the start pose")

    @staticmethod
    def from_file(path: str, geometry: RobotGeometry) -> "FloorPlanWorld":
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        plan = data["floor_plan"]
        drive = data.get("drive", {})
        return FloorPlanWorld(
            geometry,
            start=data["start"],
            rooms=plan["rooms"],
            doors=plan.get("doors", ()),
            furniture=plan.get("furniture", ()),
            tau_up_s=drive.get("tau_up_s", 0.15),
            tau_down_s=drive.get("tau_down_s", 0.15),
        )

    def room_of(self, point: Sequence[float]) -> Optional[str]:
        x, y = float(point[0]), float(point[1])
        for name, (x0, x1, y0, y1) in self.rooms.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                return name
        return None

    def integrate(self, command: Sequence[float], dt: float) -> None:
        """Advance the robot by ``dt`` seconds towards the commanded (v, w)."""

        if not 0.0 < dt <= 0.03:
            raise ValueError("a missed plant tick must be split, not extrapolated")
        if not all(math.isfinite(float(c)) for c in command):
            raise ValueError("non-finite command")
        if (
            not np.any(command)
            and not np.any(self.velocity)
            and self.checked_pose == tuple(self.pose)
        ):
            return
        self.velocity = drive_step(
            self.velocity, command, dt, self.tau_up_s, self.tau_down_s, self.geometry.wheel_separation
        )
        v, w = self.velocity
        x, y, yaw = self.pose
        if abs(w) > 1e-9:
            x += v / w * (math.sin(yaw + w * dt) - math.sin(yaw))
            y -= v / w * (math.cos(yaw + w * dt) - math.cos(yaw))
        else:
            x += v * dt * math.cos(yaw)
            y += v * dt * math.sin(yaw)
        new_yaw = yaw + w * dt
        self.pose[:] = x, y, math.atan2(math.sin(new_yaw), math.cos(new_yaw))
        self.travel += abs(v) * dt
        half = self.geometry.wheel_separation / 2
        self.wheel_angles += np.array([v - w * half, v + w * half]) * dt  # metres per wheel
        pose = tuple(self.pose)
        if pose != self.checked_pose:
            self.minimum_clearance = min(
                self.minimum_clearance,
                body_clearance(self.pose, self.obstacles, self.geometry, self.padding_m),
            )
            self.collision |= self.minimum_clearance <= 0.0
            self.checked_pose = pose

    def integrate_span(self, command: Sequence[float], span: float, max_step: float = 0.01) -> None:
        """Split a late timer tick into steps of at most ``max_step`` seconds."""

        if span <= 0.0:
            return
        steps = max(1, int(math.ceil(span / max_step)))
        for _ in range(steps):
            self.integrate(command, span / steps)

    def lidar_origin(self) -> np.ndarray:
        x, y, yaw = self.pose
        lx, ly = self.geometry.lidar_xy
        return np.array([x + math.cos(yaw) * lx - math.sin(yaw) * ly, y + math.sin(yaw) * lx + math.cos(yaw) * ly])

    def self_returns(self, angles: np.ndarray, maximum: float) -> np.ndarray:
        """Ranges to the robot's own struts and webs, in the LiDAR frame."""

        boxes = [rectangle(*box) for box in self.geometry.self_occluders]
        return raycast(boxes, self.geometry.lidar_xy, angles, maximum)

    def laser(self, beams: int = 720, maximum: float = 25.0, noise_m: float = 0.0,
              rng: Optional[np.random.Generator] = None) -> Tuple[np.ndarray, np.ndarray]:
        """One scan in the LiDAR frame: angles from -pi, counter-clockwise.

        Returns the angles and the ranges. Rays that hit nothing return
        ``maximum``; the robot's own struts and webs return short ranges.
        """

        angles = -math.pi + np.arange(beams) * 2 * math.pi / beams
        world = raycast(self.obstacles, self.lidar_origin(), angles + self.pose[2], maximum)
        own = self.self_returns(angles, maximum)
        ranges = np.minimum(world, own)
        if noise_m > 0.0:
            rng = rng or np.random.default_rng(0)
            hit = ranges < maximum
            ranges = np.where(hit, ranges + rng.normal(0.0, noise_m, len(ranges)), ranges)
        return angles, ranges

    def _nearest_on_obstacles(self, points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Distance of each point to the nearest obstacle (0 inside) and that nearest point."""

        distance = np.full(len(points), math.inf)
        nearest = points.copy()
        for obstacle in self.obstacles:
            low, high = obstacle.min(axis=0), obstacle.max(axis=0)
            inside = (points >= low).all(axis=1) & (points <= high).all(axis=1)
            distance[inside] = 0.0
            nearest[inside] = points[inside]
            for start, end in zip(obstacle, np.roll(obstacle, -1, axis=0)):
                vector = end - start
                fraction = np.clip((points - start) @ vector / (vector @ vector), 0.0, 1.0)
                candidate = start + fraction[:, None] * vector
                d = np.linalg.norm(points - candidate, axis=1)
                better = d < distance
                distance[better] = d[better]
                nearest[better] = candidate[better]
        return distance, nearest

    def map_error(self, occupancy: np.ndarray, resolution: float, origin: Sequence[float],
                  map_to_world: Sequence[float], align_iterations: int = 15) -> dict:
        """Compare a SLAM map with the world (after Amadeus ``map_oracle``).

        ``map_to_world`` is the pose of the map frame in the world, normally the
        start pose of the mapping run. Occupied cells (>= 65) are measured
        against the nearest obstacle edge, first as placed by ``map_to_world``
        and then after a best rigid fit (point-to-edge ICP). The fit separates
        a small rotation of the whole map, which grows with distance but does
        not hurt navigation in the robot's own map, from errors in its shape.
        """

        grid = np.asarray(occupancy)
        rows, cols = np.nonzero(grid >= 65)
        local = np.stack((origin[0] + (cols + 0.5) * resolution, origin[1] + (rows + 0.5) * resolution), axis=1)
        mx, my, myaw = map_to_world
        c, s = math.cos(myaw), math.sin(myaw)
        points = local @ np.array([[c, s], [-s, c]]) + np.array([mx, my])
        raw, _ = self._nearest_on_obstacles(points)

        fitted = points.copy()
        total_rotation, total_shift = 0.0, np.zeros(2)
        for _ in range(align_iterations if len(points) >= 3 else 0):
            distance, target = self._nearest_on_obstacles(fitted)
            use = distance <= 0.3  # ignore gross outliers in the fit
            if use.sum() < 3:
                break
            a, b = fitted[use], target[use]
            ca, cb = a.mean(axis=0), b.mean(axis=0)
            h = (a - ca).T @ (b - cb)
            angle = math.atan2(h[0, 1] - h[1, 0], h[0, 0] + h[1, 1])
            rotation = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
            fitted = (fitted - ca) @ rotation.T + cb
            total_rotation += angle
            total_shift = (total_shift - ca) @ rotation.T + cb
        aligned, _ = self._nearest_on_obstacles(fitted)

        free = 0
        free_known = 0
        for name, (x0, x1, y0, y1) in self.rooms.items():
            xs = np.arange(x0 + resolution / 2, x1, resolution)
            ys = np.arange(y0 + resolution / 2, y1, resolution)
            gx, gy = np.meshgrid(xs, ys)
            world_points = np.stack((gx.ravel(), gy.ravel()), axis=1)
            inside_furniture = np.zeros(len(world_points), dtype=bool)
            for obstacle in self.obstacles:
                low, high = obstacle.min(axis=0), obstacle.max(axis=0)
                inside_furniture |= (world_points >= low).all(axis=1) & (world_points <= high).all(axis=1)
            world_points = world_points[~inside_furniture]
            shifted = world_points - np.array([mx, my])
            map_points = shifted @ np.array([[c, -s], [s, c]])
            idx = np.floor((map_points - np.asarray(origin[:2])) / resolution).astype(int)
            in_grid = (idx[:, 0] >= 0) & (idx[:, 0] < grid.shape[1]) & (idx[:, 1] >= 0) & (idx[:, 1] < grid.shape[0])
            free += len(world_points)
            known = np.zeros(len(world_points), dtype=bool)
            known[in_grid] = grid[idx[in_grid, 1], idx[in_grid, 0]] == 0
            free_known += int(known.sum())

        def stats(d):
            return (float(d.max()), float(np.percentile(d, 95))) if len(d) else (None, None)

        raw_max, raw_p95 = stats(raw)
        fit_max, fit_p95 = stats(aligned)
        return {
            "occupied_cells": int(len(points)),
            "max_occupied_error_m": raw_max,
            "p95_occupied_error_m": raw_p95,
            "aligned_max_error_m": fit_max,
            "aligned_p95_error_m": fit_p95,
            "alignment_rotation_deg": math.degrees(total_rotation),
            "free_fraction_known": free_known / free if free else None,
        }
