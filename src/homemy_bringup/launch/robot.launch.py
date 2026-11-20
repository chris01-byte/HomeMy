#!/usr/bin/env python3
"""HomeMy on the real robot.

As delivered, this profile can move nothing and uses no real sensor value:

- the drive driver runs dry (it opens no bus and sends nothing);
- the LiDAR scan goes only to /scan_unconfirmed, so mapping, localization,
  and the motion gate receive none;
- the IMU is only read and compared with the wheels.

Each of these opens only through values in a local file of this robot,
entered step by step during commissioning (config/robot_local.example.yaml,
docs/runbooks/first-bring-up.md):

    ros2 launch homemy_bringup robot.launch.py
    ros2 launch homemy_bringup robot.launch.py robot_params_file:=$HOME/.config/homemy/robot_local.yaml

The app bridge listens on the loopback interface unless bridge_address is
given. It has no authentication; open it only in the laboratory network
(owner decision for the prototype):

    ros2 launch homemy_bringup robot.launch.py bridge_address:=0.0.0.0

Device names of the included parts can be given here as well: lidar_port,
imu_port.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def share(package, *parts):
    return os.path.join(get_package_share_directory(package), *parts)


def include(package, launch_file, arguments=None):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(share(package, "launch", launch_file)),
        launch_arguments=(arguments or {}).items(),
    )


def generate_launch_description():
    local = LaunchConfiguration("robot_params_file")
    fusion = LaunchConfiguration("use_imu_fusion")
    fused = PythonExpression(["'", fusion, "'.lower() == 'true'"])
    return LaunchDescription(
        [
            DeclareLaunchArgument("bridge_address", default_value="127.0.0.1"),
            DeclareLaunchArgument("bridge_port", default_value="9090"),
            DeclareLaunchArgument("storage_root", default_value="~/.local/share/homemy"),
            DeclareLaunchArgument("auto_end_timeout_s", default_value="300.0"),
            DeclareLaunchArgument(
                "robot_params_file",
                default_value=share("homemy_bringup", "config", "robot_overlay_none.yaml"),
                description="Local values of this robot from commissioning. Default: none, everything locked.",
            ),
            DeclareLaunchArgument(
                "drive_port",
                default_value="/dev/homemy_drive",
                description="Serial device of the drive's RS485 adapter; the stable udev alias.",
            ),
            DeclareLaunchArgument(
                "use_imu_fusion",
                default_value="false",
                description="true: the odometry uses the gyro's yaw rate. Only after IMU steps I2 to I4.",
            ),
            DeclareLaunchArgument("use_lidar", default_value="true", description="false leaves out the LiDAR."),
            DeclareLaunchArgument("use_imu", default_value="true", description="false leaves out the IMU."),
            DeclareLaunchArgument(
                "use_controller", default_value="true", description="false leaves out controller driving."
            ),
            # ------------------------------------------------ app, model, state
            include(
                "homemy_bringup",
                "app_backend.launch.py",
                {
                    "bridge_address": LaunchConfiguration("bridge_address"),
                    "bridge_port": LaunchConfiguration("bridge_port"),
                    "storage_root": LaunchConfiguration("storage_root"),
                    "auto_end_timeout_s": LaunchConfiguration("auto_end_timeout_s"),
                },
            ),
            include("homemy_description", "description.launch.py"),
            # The lifecycle state and the emergency-stop signal are bridged with
            # fixed values while the PMU does not exist (homemy_boot_manager).
            # The hardware emergency-stop switch works without software.
            Node(
                package="homemy_boot_manager",
                executable="lifecycle_bridge",
                name="lifecycle_bridge",
                output="screen",
            ),
            # ------------------------------------------------------------ drive
            # With fusion the EKF owns /odom and the transform.
            Node(
                package="homemy_drivebase",
                executable="drivebase",
                name="drivebase",
                output="screen",
                parameters=[
                    share("homemy_drivebase", "config", "homemy_drivebase.yaml"),
                    local,
                    {
                        "rs485_port": LaunchConfiguration("drive_port"),
                        "odom_topic": PythonExpression(["'/wheel/odom' if ", fused, " else '/odom'"]),
                        "publish_tf": ParameterValue(PythonExpression(["not ", fused]), value_type=bool),
                    },
                ],
            ),
            # ------------------------------------------------------------ LiDAR
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(share("homemy_lidar_bringup", "launch", "stl27l.launch.py")),
                launch_arguments={"lidar_overlay_params_file": local}.items(),
                condition=IfCondition(LaunchConfiguration("use_lidar")),
            ),
            include("homemy_lidar_bringup", "scan_mask.launch.py", {"scan_mask_overlay_params_file": local}),
            # -------------------------------------------------------------- IMU
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(share("homemy_state_estimation", "launch", "imu.launch.py")),
                launch_arguments={"imu_overlay_params_file": local, "use_imu_fusion": fusion}.items(),
                condition=IfCondition(LaunchConfiguration("use_imu")),
            ),
            # ---------------------------------------------- driving and missions
            include("homemy_motion_gate", "motion_gate.launch.py"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(share("homemy_manual_drive", "launch", "manual_drive.launch.py")),
                condition=IfCondition(LaunchConfiguration("use_controller")),
            ),
            include("homemy_navigation", "slam.launch.py"),
            include("homemy_navigation", "navigation.launch.py", {"storage_root": LaunchConfiguration("storage_root")}),
            include("homemy_mission", "mission.launch.py"),
        ]
    )
