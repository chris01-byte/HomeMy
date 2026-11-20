#!/usr/bin/env python3
"""The IMU chain against a simulated HWT601, with the drive driver at simulated motors.

The real IMU reader reads a simulated sensor over a simulated RS485 line; the
yaw-rate aid learns the bias at standstill. Nothing else of the robot runs.

    ros2 launch homemy_bringup imu_sim.launch.py
    ros2 launch homemy_bringup imu_sim.launch.py use_imu_fusion:=true

Without fusion the gyro is only compared with the wheels (shadow mode). With
fusion an EKF publishes /odom from wheel speed and gyro yaw rate.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def share(package, *parts):
    return os.path.join(get_package_share_directory(package), *parts)


def generate_launch_description():
    drive_port = ["/tmp/homemy_sim_drive_", LaunchConfiguration("sim_id")]
    imu_port = ["/tmp/homemy_sim_imu_", LaunchConfiguration("sim_id")]
    fusion = LaunchConfiguration("use_imu_fusion")
    fused = PythonExpression(["'", fusion, "'.lower() == 'true'"])
    return LaunchDescription(
        [
            DeclareLaunchArgument("sim_id", default_value="0"),
            DeclareLaunchArgument("use_imu_fusion", default_value="false"),
            DeclareLaunchArgument(
                "world_file", default_value=share("homemy_simulation", "worlds", "testwohnung.json")
            ),
            Node(
                package="homemy_simulation",
                executable="sim_base",
                name="homemy_sim_base",
                output="screen",
                parameters=[
                    share("homemy_simulation", "config", "sim_imu.yaml"),
                    {
                        "world_file": LaunchConfiguration("world_file"),
                        "geometry_file": share("homemy_description", "config", "geometry.yaml"),
                        "drive_interface": "modbus",
                        "modbus_port_link": drive_port,
                        "imu_port_link": imu_port,
                    },
                ],
            ),
            # The real drive driver, unlocked only against the simulated motors.
            # With fusion the EKF owns /odom and the transform.
            Node(
                package="homemy_drivebase",
                executable="drivebase",
                name="drivebase",
                output="screen",
                parameters=[
                    share("homemy_drivebase", "config", "homemy_drivebase.yaml"),
                    share("homemy_simulation", "config", "sim_drivebase.yaml"),
                    {
                        "rs485_port": drive_port,
                        "odom_topic": PythonExpression(["'/wheel/odom' if ", fused, " else '/odom'"]),
                        "publish_tf": ParameterValue(PythonExpression(["not ", fused]), value_type=bool),
                    },
                ],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(share("homemy_state_estimation", "launch", "imu.launch.py")),
                launch_arguments={
                    "imu_port": imu_port,
                    "use_imu_fusion": fusion,
                    "imu_overlay_params_file": share("homemy_simulation", "config", "sim_imu.yaml"),
                }.items(),
            ),
        ]
    )
