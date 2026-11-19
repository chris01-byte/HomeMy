"""Localization manager: mapping with slam_toolbox, or navigation on the saved map.

The one owner of slam_toolbox, map_server, and AMCL (all lifecycle nodes):

- mapping mode active: AMCL and map_server inactive, slam_toolbox active;
  every new mapping run resets the map;
- mapping ended: slam_toolbox paused, its map stays until it is saved;
- the SLAM map saved (the map store reports a saved version with the live
  map's fingerprint): slam_toolbox inactive, map_server loads that version,
  AMCL starts at the robot's last SLAM pose;
- start-up with a saved map: navigation on the newest saved version, starting
  at the last trusted pose stored for exactly that map;
- whenever the position is not trusted while the robot stands still, for
  example because it was carried elsewhere, the whole map is searched for
  the place where the current scan fits (global_scan_matcher, ported from
  Amadeus). Two searches on different scans must agree; then AMCL starts
  there. A search without a result is repeated after a pause; nothing
  latches.

It publishes ``/homemy/localization/ready`` (std_msgs/Bool, 5 Hz) only while
navigating, with AMCL confident and the scan agreeing with the map
(localization_core.ReadinessGuard). It commands no motion.
"""

from __future__ import annotations

import json
import math
import os
import time
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Deque, Optional, Tuple

import numpy as np
import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from lifecycle_msgs.msg import State, Transition
from lifecycle_msgs.srv import ChangeState, GetState
from nav2_msgs.srv import LoadMap
from nav_msgs.msg import OccupancyGrid, Odometry
from rcl_interfaces.srv import GetParameters
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from slam_toolbox.srv import Pause, Reset
from std_msgs.msg import Bool, String
from std_srvs.srv import Empty
from tf2_ros import Buffer, TransformException, TransformListener

from homemy_navigation.global_scan_matcher import MapScorer, SearchResult, search_global_pose
from homemy_navigation.relocalization_core import STATE_SEARCHING, SearchConfig, SearchPlanner
from homemy_navigation.localization_core import (
    MODE_IDLE,
    MODE_MAPPING,
    MODE_NAVIGATION,
    MODE_SLAM_HOLD,
    Check,
    OccupancyIndex,
    ReadinessConfig,
    ReadinessGuard,
    SavedMapRef,
    desired_mode,
    load_last_pose,
    save_last_pose,
    sigmas_from_covariance,
    yaw_from_quaternion,
)

LATCHED = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)


class StepFailed(Exception):
    pass


class LocalizationManager(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("localization_manager", **node_options)
        declare = self.declare_parameter
        declare("maps_root", "~/.local/share/homemy/maps")
        declare("map_name", "wohnung")
        declare("last_pose_file", "~/.local/share/homemy/localization/last_pose.json")
        declare("mapping_active_topic", "/homemy/mapping_mode/active")
        declare("map_status_topic", "/homemy/map_manager/status_json")
        declare("scan_topic", "/scan_masked")
        declare("map_topic", "/map")
        declare("amcl_pose_topic", "/amcl_pose")
        declare("initial_pose_topic", "/initialpose")
        declare("ready_topic", "/homemy/localization/ready")
        declare("status_topic", "/homemy/localization/status_json")
        declare("slam_node", "/slam_toolbox")
        declare("map_server_node", "/map_server")
        declare("amcl_node", "/amcl")
        declare("map_frame", "map")
        declare("base_frame", "base_link")
        declare("mapping_active_timeout_s", 2.0)
        declare("agreement_radius_m", 0.15)
        declare("check_period_s", 0.5)
        declare("handover_sigma_xy_m", 0.10)
        declare("handover_sigma_yaw_deg", 5.0)
        # A switched-off robot does not move; the stored pose is therefore
        # taken as precise. If someone moved it, the scan check rejects it.
        declare("stored_sigma_xy_m", 0.15)
        declare("stored_sigma_yaw_deg", 8.0)
        declare("save_pose_period_s", 2.0)
        declare("service_timeout_s", 5.0)
        # While standing, AMCL only updates when asked. After an initial pose
        # it is asked repeatedly, so that the scan confirms or rejects it.
        declare("nomotion_updates", 30)
        declare("nomotion_period_s", 0.5)
        # Global search (relocalization_core.SearchConfig).
        declare("odom_topic", "/odom")
        declare("search_start_after_s", 5.0)
        declare("search_minimum_scan_points", 200)
        declare("search_minimum_score", 0.85)
        declare("search_minimum_endpoint_ratio", 0.85)
        declare("search_minimum_score_ratio", 1.05)
        declare("search_pause_after_failure_s", 10.0)
        declare("search_sigma_xy_m", 0.15)
        declare("search_sigma_yaw_deg", 5.0)
        declare("search_max_range_m", 12.0)
        declare("standstill_linear_mps", 0.01)
        declare("standstill_angular_rps", 0.02)
        declare("standstill_time_s", 1.0)

        def value(name):
            return self.get_parameter(name).value

        self.maps_root = os.path.expanduser(str(value("maps_root")))
        self.map_name = str(value("map_name"))
        self.last_pose_file = os.path.expanduser(str(value("last_pose_file")))
        self.map_frame = str(value("map_frame"))
        self.base_frame = str(value("base_frame"))
        self.mapping_timeout_s = float(value("mapping_active_timeout_s"))
        self.agreement_radius_m = float(value("agreement_radius_m"))
        self.check_period_s = float(value("check_period_s"))
        self.handover_sigma = (float(value("handover_sigma_xy_m")), float(value("handover_sigma_yaw_deg")))
        self.stored_sigma = (float(value("stored_sigma_xy_m")), float(value("stored_sigma_yaw_deg")))
        self.save_pose_period_s = float(value("save_pose_period_s"))
        self.service_timeout_s = float(value("service_timeout_s"))
        self.nomotion_updates = int(value("nomotion_updates"))
        self.nomotion_period_s = float(value("nomotion_period_s"))
        self.nomotion_left = 0
        self.nomotion_at = 0.0
        self.planner = SearchPlanner(SearchConfig(
            start_after_s=float(value("search_start_after_s")),
            minimum_scan_points=int(value("search_minimum_scan_points")),
            minimum_score=float(value("search_minimum_score")),
            minimum_endpoint_ratio=float(value("search_minimum_endpoint_ratio")),
            minimum_score_ratio=float(value("search_minimum_score_ratio")),
            pause_after_failure_s=float(value("search_pause_after_failure_s")),
        ))
        self.search_sigma = (float(value("search_sigma_xy_m")), float(value("search_sigma_yaw_deg")))
        self.search_max_range_m = float(value("search_max_range_m"))
        self.standstill = (float(value("standstill_linear_mps")), float(value("standstill_angular_rps")),
                           float(value("standstill_time_s")))
        self.search_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="global_search")
        self.search_future: Optional[Future] = None
        self.search_scan_stamp: Optional[Tuple[int, int]] = None
        self.scorer: Optional[MapScorer] = None
        self.scorer_map: Optional[OccupancyGrid] = None
        self.latest_scan: Optional[LaserScan] = None
        self.latest_scan_at: Optional[float] = None
        self.odom_at: Optional[float] = None
        self.moving_at: Optional[float] = None
        self.not_trusted_since: Optional[float] = None
        self.searches_done = 0
        self.guard = ReadinessGuard(ReadinessConfig())

        slam = str(value("slam_node")).rstrip("/")
        self.lifecycle_clients = {}
        for key, name in (("slam", slam), ("map_server", str(value("map_server_node")).rstrip("/")),
                          ("amcl", str(value("amcl_node")).rstrip("/"))):
            self.lifecycle_clients[key] = (
                self.create_client(GetState, f"{name}/get_state"),
                self.create_client(ChangeState, f"{name}/change_state"),
            )
        self.slam_reset = self.create_client(Reset, f"{slam}/reset")
        self.slam_pause = self.create_client(Pause, f"{slam}/pause_new_measurements")
        self.slam_params = self.create_client(GetParameters, f"{slam}/get_parameters")
        self.load_map_client = self.create_client(LoadMap, f"{str(value('map_server_node')).rstrip('/')}/load_map")
        self.nomotion_client = self.create_client(
            Empty, f"{str(value('amcl_node')).rstrip('/')}/request_nomotion_update")

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Unknown until the first switch has run, so that start-up always
        # brings the three lifecycle nodes into a defined state.
        self.mode = "unknown"
        self.target: Optional[str] = None
        self.steps: Deque[Callable[[], Optional[rclpy.task.Future]]] = deque()
        self.pending: Optional[Tuple[rclpy.task.Future, Callable]] = None
        self.pending_since = 0.0
        self.last_error: Optional[str] = None
        self.retry_after = 0.0
        self.mapping_active: Optional[bool] = None
        self.mapping_active_at: Optional[float] = None
        self.new_run = False
        self.live_fingerprint: Optional[str] = None
        self.saved: Optional[SavedMapRef] = None
        self.saved_scanned_at = -math.inf
        self.loaded: Optional[SavedMapRef] = None
        self.initial_pose_source: Optional[str] = None
        self.initial_pose_sent_at: Optional[float] = None
        self.amcl_cov: Optional[Tuple[float, float, float]] = None  # time, sigma_xy, sigma_yaw
        self.latest_map: Optional[OccupancyGrid] = None
        self.index: Optional[OccupancyIndex] = None
        self.index_frame: Optional[str] = None
        self.last_check_at = 0.0
        self.last_pose_saved_at = 0.0
        self.last_status = None
        self.last_status_at = 0.0

        self.initial_pose_pub = self.create_publisher(PoseWithCovarianceStamped, str(value("initial_pose_topic")), 10)
        self.ready_pub = self.create_publisher(Bool, str(value("ready_topic")), 10)
        self.status_pub = self.create_publisher(String, str(value("status_topic")), LATCHED)
        self.create_subscription(Bool, str(value("mapping_active_topic")), self._on_mapping_active, LATCHED)
        self.create_subscription(String, str(value("map_status_topic")), self._on_map_status, LATCHED)
        self.create_subscription(OccupancyGrid, str(value("map_topic")), self._on_map, LATCHED)
        self.create_subscription(PoseWithCovarianceStamped, str(value("amcl_pose_topic")), self._on_amcl_pose, 10)
        self.create_subscription(LaserScan, str(value("scan_topic")), self._on_scan, qos_profile_sensor_data)
        self.create_subscription(Odometry, str(value("odom_topic")), self._on_odom, 10)
        self.create_timer(0.2, self._tick)

    # ------------------------------------------------------------ inputs

    def _on_mapping_active(self, message: Bool) -> None:
        active = bool(message.data)
        if active and self.mapping_active is False:
            self.new_run = True
        self.mapping_active = active
        self.mapping_active_at = time.monotonic()

    def _on_map_status(self, message: String) -> None:
        try:
            status = json.loads(message.data)
            summary = (status.get("map") or {}).get("summary") or {}
            fingerprint = summary.get("fingerprint")
            self.live_fingerprint = fingerprint if isinstance(fingerprint, str) else None
            last = (status.get("storage") or {}).get("last_saved")
            if isinstance(last, dict) and isinstance(last.get("fingerprint"), str) and isinstance(last.get("path"), str):
                if last.get("name") in (None, self.map_name):
                    self.saved = SavedMapRef(last["fingerprint"], os.path.join(last["path"], "map.yaml"),
                                             str(last.get("version", "")))
        except (ValueError, AttributeError, TypeError):
            pass

    def _on_map(self, message: OccupancyGrid) -> None:
        # Kept always; the index for the check is built when navigation uses it.
        self.latest_map = message
        self.index = None

    def _ensure_index(self) -> Optional[OccupancyIndex]:
        if self.index is None and self.latest_map is not None:
            info = self.latest_map.info
            try:
                self.index = OccupancyIndex(self.latest_map.data, info.width, info.height, info.resolution,
                                            (info.origin.position.x, info.origin.position.y), self.agreement_radius_m)
                self.index_frame = self.latest_map.header.frame_id or self.map_frame
            except ValueError as error:
                self.get_logger().error(f"Map unusable for the localization check: {error}")
                self.latest_map = None
        return self.index

    def _on_amcl_pose(self, message: PoseWithCovarianceStamped) -> None:
        sigma_xy, sigma_yaw = sigmas_from_covariance(message.pose.covariance)
        self.amcl_cov = (time.monotonic(), sigma_xy, sigma_yaw)

    def _on_odom(self, message: Odometry) -> None:
        now = time.monotonic()
        self.odom_at = now
        twist = message.twist.twist
        if (self.moving_at is None or abs(twist.linear.x) > self.standstill[0]
                or abs(twist.angular.z) > self.standstill[1]):
            self.moving_at = now

    def _standing_still(self, now: float) -> bool:
        if self.odom_at is None or self.moving_at is None or now - self.odom_at > 1.0:
            return False
        return now - self.moving_at >= self.standstill[2]

    def _on_scan(self, message: LaserScan) -> None:
        now = time.monotonic()
        self.latest_scan = message
        self.latest_scan_at = now
        if self.mode != MODE_NAVIGATION or self.target is not None or self._ensure_index() is None:
            return
        if now - self.last_check_at < self.check_period_s:
            return
        self.last_check_at = now
        if self.amcl_cov is None or self.initial_pose_sent_at is None or self.amcl_cov[0] < self.initial_pose_sent_at:
            return
        try:
            transform = self.tf_buffer.lookup_transform(self.index_frame, message.header.frame_id, rclpy.time.Time())
        except TransformException:
            self.guard.reset("no_transform")
            return
        t = transform.transform.translation
        q = transform.transform.rotation
        yaw = yaw_from_quaternion(q.x, q.y, q.z, q.w)
        ranges = np.asarray(message.ranges, dtype=float)
        angles = message.angle_min + np.arange(len(ranges)) * message.angle_increment + yaw
        valid = np.isfinite(ranges) & (ranges >= message.range_min) & (ranges <= message.range_max)
        points = np.stack((t.x + ranges[valid] * np.cos(angles[valid]), t.y + ranges[valid] * np.sin(angles[valid])), axis=1)
        agreement, count = self.index.agreement(points)
        _, sigma_xy, sigma_yaw = self.amcl_cov
        self.guard.update(Check(now, agreement, count, sigma_xy, sigma_yaw))

    # ------------------------------------------------------------ helpers

    def _mapping_wanted(self) -> bool:
        fresh = self.mapping_active_at is not None and time.monotonic() - self.mapping_active_at <= self.mapping_timeout_s
        return bool(fresh and self.mapping_active)

    def _newest_saved(self) -> Optional[SavedMapRef]:
        """The newest saved map version on disk, verified by the map store's own code."""

        try:
            from homemy_map_manager.map_core import MapRepository

            repository = MapRepository(Path(self.maps_root), default_name=self.map_name)
            records = repository.list_versions(name=self.map_name, limit=1)
        except Exception as error:  # noqa: BLE001 - storage problems mean "no saved map"
            self.get_logger().warning(f"Saved maps unreadable: {error}")
            return None
        if not records:
            return None
        record = records[0]
        return SavedMapRef(record.fingerprint, os.path.join(str(record.path), "map.yaml"), record.version)

    def _robot_pose(self) -> Optional[Tuple[float, float, float]]:
        try:
            transform = self.tf_buffer.lookup_transform(self.map_frame, self.base_frame, rclpy.time.Time())
        except TransformException:
            return None
        t = transform.transform.translation
        q = transform.transform.rotation
        return t.x, t.y, yaw_from_quaternion(q.x, q.y, q.z, q.w)

    # ------------------------------------------------------------ global search

    def _scan_points_in_laser_frame(self, message: LaserScan) -> np.ndarray:
        ranges = np.asarray(message.ranges, dtype=float)
        angles = message.angle_min + np.arange(len(ranges)) * message.angle_increment
        limit = min(message.range_max, self.search_max_range_m)
        valid = np.isfinite(ranges) & (ranges >= max(message.range_min, 0.1)) & (ranges <= limit)
        return np.stack((ranges[valid] * np.cos(angles[valid]), ranges[valid] * np.sin(angles[valid])), axis=1)

    def _ensure_scorer(self) -> Optional[MapScorer]:
        if self.latest_map is None:
            return None
        if self.scorer is None or self.scorer_map is not self.latest_map:
            info = self.latest_map.info
            q = info.origin.orientation
            try:
                grid = np.asarray(self.latest_map.data, dtype=np.int16).reshape(info.height, info.width)
                self.scorer = MapScorer(grid, info.resolution, info.origin.position.x, info.origin.position.y,
                                        yaw_from_quaternion(q.x, q.y, q.z, q.w))
                self.scorer_map = self.latest_map
            except ValueError as error:
                self.get_logger().error(f"Map unusable for the global search: {error}")
                self.scorer = None
                self.scorer_map = self.latest_map
        return self.scorer

    def _search_tick(self, now: float, ready: bool) -> None:
        """Start, or collect, a search of the whole map while the position is not trusted."""

        navigating = self.mode == MODE_NAVIGATION and self.target is None
        if not navigating or ready:
            self.not_trusted_since = None
            if self.planner.state != STATE_SEARCHING:
                self.planner.reset()
            if self.search_future is not None and self.search_future.done():
                self.search_future = None  # a late result for a situation that is over
            return
        if self.not_trusted_since is None:
            self.not_trusted_since = now

        if self.search_future is not None:
            if not self.search_future.done():
                return
            future, self.search_future = self.search_future, None
            self.searches_done += 1
            result: Optional[SearchResult] = None
            error: Optional[str] = None
            try:
                result = future.result()
            except Exception as exception:  # noqa: BLE001 - any failure of the search is "no result"
                error = f"search_failed: {exception}"
            found = self.planner.note_result(now, result, error)
            if result is not None:
                best = result.best
                self.get_logger().info(
                    f"Global search: best x={best.x_m:.2f} y={best.y_m:.2f} yaw={math.degrees(best.yaw_rad):.0f} deg, "
                    f"score {best.score:.3f}, wall share {best.endpoint_within_0_15_m_ratio:.2f}, "
                    f"margin {result.score_ratio:.2f}; {self.planner.last_reason}.")
            else:
                self.get_logger().warning(f"Global search without result: {error}.")
            if found is not None:
                self._send_initial_pose((found.x_m, found.y_m, found.yaw_rad), self.search_sigma, "global_search")
                self.not_trusted_since = now
            return

        scan = self.latest_scan
        if scan is None or self.latest_scan_at is None or now - self.latest_scan_at > 1.0:
            return
        stamp = (scan.header.stamp.sec, scan.header.stamp.nanosec)
        if stamp == self.search_scan_stamp:
            return  # every attempt needs a new scan
        scorer = self._ensure_scorer()
        if scorer is None:
            return
        try:
            transform = self.tf_buffer.lookup_transform(self.base_frame, scan.header.frame_id, rclpy.time.Time())
        except TransformException:
            return
        points = self._scan_points_in_laser_frame(scan)
        reference = self.not_trusted_since
        if self.initial_pose_sent_at is not None:
            reference = max(reference, self.initial_pose_sent_at)
        not_trusted_for = None if self.initial_pose_sent_at is None else now - reference
        if not self.planner.may_start(now, not_trusted_for, self._standing_still(now), len(points)):
            return
        t = transform.transform.translation
        q = transform.transform.rotation
        laser_yaw = yaw_from_quaternion(q.x, q.y, q.z, q.w)
        self.planner.note_started()
        self.search_scan_stamp = stamp
        self.get_logger().info(f"Position not trusted; searching the whole map (attempt {self.planner.attempts}).")
        self.search_future = self.search_pool.submit(
            search_global_pose, scorer, points,
            laser_translation_x=float(t.x), laser_translation_y=float(t.y), laser_yaw_rad=laser_yaw)

    # ------------------------------------------------------------ steps

    def _call(self, client, request, check: Callable[[object], bool], what: str) -> Callable:
        def step():
            if not client.service_is_ready():
                raise StepFailed(f"{what}: service not available")
            future = client.call_async(request)
            self.pending = (future, lambda response: check(response) or self._fail(what))
            self.pending_since = time.monotonic()
            return future
        return step

    def _fail(self, what: str) -> bool:
        raise StepFailed(what)

    def _ensure_state(self, key: str, active: bool) -> Callable:
        get_client, change_client = self.lifecycle_clients[key]

        def step():
            if not get_client.service_is_ready():
                raise StepFailed(f"{key}: lifecycle service not available")
            future = get_client.call_async(GetState.Request())

            def after(response):
                state = response.current_state.id
                plan = []
                if active:
                    if state == State.PRIMARY_STATE_UNCONFIGURED:
                        plan = [Transition.TRANSITION_CONFIGURE, Transition.TRANSITION_ACTIVATE]
                    elif state == State.PRIMARY_STATE_INACTIVE:
                        plan = [Transition.TRANSITION_ACTIVATE]
                    elif state != State.PRIMARY_STATE_ACTIVE:
                        raise StepFailed(f"{key}: unexpected lifecycle state {response.current_state.label}")
                elif state == State.PRIMARY_STATE_ACTIVE:
                    plan = [Transition.TRANSITION_DEACTIVATE]
                for transition in reversed(plan):
                    request = ChangeState.Request()
                    request.transition.id = transition
                    self.steps.appendleft(self._call(change_client, request, lambda r: bool(r.success),
                                                     f"{key}: transition {transition} failed"))
                return True

            self.pending = (future, after)
            self.pending_since = time.monotonic()
            return future
        return step

    def _slam_paused(self, paused: bool) -> Callable:
        def step():
            if not self.slam_params.service_is_ready():
                raise StepFailed("slam_toolbox parameters not available")
            request = GetParameters.Request()
            request.names = ["paused_new_measurements"]
            future = self.slam_params.call_async(request)

            def after(response):
                if not response.values:
                    raise StepFailed("slam_toolbox pause state unknown")
                if bool(response.values[0].bool_value) != paused:
                    self.steps.appendleft(self._call(self.slam_pause, Pause.Request(), lambda r: True,
                                                     "slam_toolbox pause toggle failed"))
                return True

            self.pending = (future, after)
            self.pending_since = time.monotonic()
            return future
        return step

    def _slam_reset(self) -> Callable:
        request = Reset.Request()
        request.pause_new_measurements = False
        return self._call(self.slam_reset, request, lambda r: True, "slam_toolbox reset failed")

    def _load_map(self, ref: SavedMapRef) -> Callable:
        request = LoadMap.Request()
        request.map_url = ref.yaml_path
        return self._call(self.load_map_client, request,
                          lambda r: r.result == LoadMap.Response.RESULT_SUCCESS, f"map_server could not load {ref.yaml_path}")

    def _immediate(self, action: Callable[[], None]) -> Callable:
        def step():
            action()
            return None
        return step

    def _plan(self, target: str) -> None:
        steps = []
        if target == MODE_MAPPING:
            steps = [self._ensure_state("amcl", False), self._ensure_state("map_server", False),
                     self._ensure_state("slam", True)]
            if self.new_run:
                self.new_run = False
                steps.append(self._slam_reset())
            steps.append(self._slam_paused(False))
        elif target in (MODE_SLAM_HOLD, MODE_IDLE):
            steps = [self._ensure_state("amcl", False), self._ensure_state("map_server", False),
                     self._ensure_state("slam", True), self._slam_paused(True)]
        elif target == MODE_NAVIGATION:
            ref = self.saved
            handover = self._robot_pose() if self.mode == MODE_SLAM_HOLD else None
            steps = [self._ensure_state("slam", False), self._ensure_state("map_server", True),
                     self._load_map(ref), self._ensure_state("amcl", True),
                     self._immediate(lambda: self._set_loaded(ref, handover))]
        self.target = target
        self.steps = deque(steps)
        self.guard.reset("switching")
        self.initial_pose_source = None
        self.initial_pose_sent_at = None
        self.get_logger().info(f"Localization: {self.mode} -> {target}.")

    def _set_loaded(self, ref: SavedMapRef, handover: Optional[Tuple[float, float, float]]) -> None:
        self.loaded = ref
        if handover is not None:
            self._send_initial_pose(handover, self.handover_sigma, "slam_handover")
            return
        stored = load_last_pose(self.last_pose_file, ref.fingerprint)
        if stored is not None:
            self._send_initial_pose(stored, self.stored_sigma, "stored")
        else:
            self.initial_pose_source = None
            self.initial_pose_sent_at = None
            self.get_logger().info("No pose known on the saved map; the whole map will be searched.")

    def _send_initial_pose(self, pose, sigmas, source: str) -> None:
        message = PoseWithCovarianceStamped()
        message.header.frame_id = self.map_frame
        message.header.stamp = self.get_clock().now().to_msg()
        message.pose.pose.position.x, message.pose.pose.position.y = float(pose[0]), float(pose[1])
        message.pose.pose.orientation.z = math.sin(pose[2] / 2.0)
        message.pose.pose.orientation.w = math.cos(pose[2] / 2.0)
        message.pose.covariance[0] = message.pose.covariance[7] = sigmas[0] ** 2
        message.pose.covariance[35] = math.radians(sigmas[1]) ** 2
        self.initial_pose_pub.publish(message)
        self.initial_pose_source = source
        self.initial_pose_sent_at = time.monotonic()
        self.nomotion_left = self.nomotion_updates
        self.guard.reset("initial_pose_set")
        self.get_logger().info(f"Initial pose from {source}: x={pose[0]:.2f} y={pose[1]:.2f} yaw={math.degrees(pose[2]):.1f} deg.")

    # ------------------------------------------------------------ main loop

    def _tick(self) -> None:
        now = time.monotonic()
        if self.saved is None and now - self.saved_scanned_at > 10.0:
            self.saved_scanned_at = now
            self.saved = self._newest_saved()

        self._run_steps(now)
        if self.target is None and now >= self.retry_after:
            wanted = desired_mode(self._mapping_wanted(), self.mode, self.saved, self.live_fingerprint)
            needs_plan = wanted != self.mode or (wanted == MODE_MAPPING and self.new_run)
            if wanted == MODE_NAVIGATION and self.mode == MODE_NAVIGATION and self.saved != self.loaded:
                needs_plan = True
            if needs_plan:
                self._plan(wanted)
                self._run_steps(now)

        ready = self.mode == MODE_NAVIGATION and self.target is None and self.guard.is_ready(now)
        if (not ready and self.mode == MODE_NAVIGATION and self.target is None and self.nomotion_left > 0
                and now - self.nomotion_at >= self.nomotion_period_s and self.nomotion_client.service_is_ready()):
            self.nomotion_left -= 1
            self.nomotion_at = now
            self.nomotion_client.call_async(Empty.Request())
        self.ready_pub.publish(Bool(data=bool(ready)))
        self._search_tick(now, ready)
        if ready and self.loaded is not None and now - self.last_pose_saved_at >= self.save_pose_period_s:
            pose = self._robot_pose()
            if pose is not None:
                try:
                    save_last_pose(self.last_pose_file, self.loaded.fingerprint, pose, time.time())
                    self.last_pose_saved_at = now
                except OSError as error:
                    self.get_logger().warning(f"Last pose not stored: {error}")
        self._publish_status(now, ready)

    def _run_steps(self, now: float) -> None:
        try:
            while True:
                if self.pending is not None:
                    future, after = self.pending
                    if not future.done():
                        if now - self.pending_since > self.service_timeout_s:
                            raise StepFailed("service call timed out")
                        return
                    self.pending = None
                    response = future.result()
                    if response is None:
                        raise StepFailed("service call failed")
                    after(response)
                if not self.steps:
                    if self.target is not None:
                        self.mode = self.target
                        self.target = None
                        self.last_error = None
                        self.get_logger().info(f"Localization mode: {self.mode}.")
                    return
                step = self.steps.popleft()
                step()
        except StepFailed as error:
            self.last_error = str(error)
            self.get_logger().warning(f"Localization switch to {self.target} failed: {error}; retrying.")
            self.steps.clear()
            self.pending = None
            self.target = None
            self.retry_after = now + 2.0

    def _status_pose(self) -> Optional[dict]:
        pose = self._robot_pose()
        if pose is None:
            return None
        return {"x": round(pose[0], 2), "y": round(pose[1], 2), "yaw": round(pose[2], 2)}

    def destroy_node(self):
        self.search_pool.shutdown(wait=False, cancel_futures=True)
        return super().destroy_node()

    def _publish_status(self, now: float, ready: bool) -> None:
        last = self.guard.last
        status = {
            "schema_version": 1,
            "mode": self.mode,
            "switching_to": self.target,
            "last_error": self.last_error,
            "ready": ready,
            "reason": "ok" if ready else (self.target and "switching") or (
                "not_navigating" if self.mode != MODE_NAVIGATION else
                ("no_initial_pose" if self.initial_pose_sent_at is None else self.guard.reason)),
            "map": None if self.loaded is None else {"fingerprint": self.loaded.fingerprint, "version": self.loaded.version},
            "initial_pose_source": self.initial_pose_source,
            "pose": self._status_pose() if ready else None,
            "search": {
                "state": self.planner.state,
                "attempt": self.planner.attempts,
                "rounds_without_result": self.planner.rounds_failed,
                "last_reason": self.planner.last_reason,
                "searches_done": self.searches_done,
            },
            "agreement": None if last is None else round(last.agreement, 3),
            "sigma_xy_m": None if last is None or not math.isfinite(last.sigma_xy_m) else round(last.sigma_xy_m, 3),
            "sigma_yaw_deg": None if last is None or not math.isfinite(last.sigma_yaw_deg) else round(last.sigma_yaw_deg, 2),
        }
        if status != self.last_status or now - self.last_status_at >= 1.0:
            self.last_status = status
            self.last_status_at = now
            payload = dict(status, time=time.time())
            self.status_pub.publish(String(data=json.dumps(payload, allow_nan=False)))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LocalizationManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
