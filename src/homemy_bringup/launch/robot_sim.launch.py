#!/usr/bin/env python3
"""The real robot profile against simulated devices. Simulation only.

robot.launch.py runs unchanged. Only the three devices and the person with
the controller are simulated: ESS23-RS motors, an STL-27L, and an HWT601,
each on its own pseudo-terminal, where the real drive driver, the unchanged
vendor LiDAR driver, and the real IMU reader find them.

    ros2 launch homemy_bringup robot_sim.launch.py
    ros2 launch homemy_bringup robot_sim.launch.py commissioned:=true

Without commissioned:=true the robot profile has its delivered, locked
configuration. With it, the simulated robot's local values are used
(homemy_simulation/config/sim_robot_local.yaml).

Needs the vendor LiDAR driver built and sourced.
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
    sim_id = LaunchConfiguration("sim_id")
    drive_port = ["/tmp/homemy_sim_drive_", sim_id]
    lidar_port = ["/tmp/homemy_sim_lidar_", sim_id]
    imu_port = ["/tmp/homemy_sim_imu_", sim_id]
    local = PythonExpression([
        "'", share("homemy_simulation", "config", "sim_robot_local.yaml"), "' if '",
        LaunchConfiguration("commissioned"), "'.lower() == 'true' else '",
        LaunchConfiguration("locked_params_file"), "'",
    ])
    return LaunchDescription(
        [
            DeclareLaunchArgument("sim_id", default_value="0"),
            DeclareLaunchArgument("bridge_address", default_value="127.0.0.1"),
            DeclareLaunchArgument("bridge_port", default_value="9090"),
            DeclareLaunchArgument("storage_root", default_value="~/.local/share/homemy-sim"),
            DeclareLaunchArgument("use_imu_fusion", default_value="false"),
            DeclareLaunchArgument(
                "commissioned",
                default_value="false",
                description="true: use the simulated robot's local values, which unlock drive and LiDAR.",
            ),
            DeclareLaunchArgument(
                "locked_params_file",
                default_value=share("homemy_bringup", "config", "robot_overlay_none.yaml"),
                description="The local file used while commissioned is false.",
            ),
            DeclareLaunchArgument(
                "world_file", default_value=share("homemy_simulation", "worlds", "testwohnung.json")
            ),
            DeclareLaunchArgument(
                "operator_drives",
                default_value="true",
                description="The simulated person holds the direction pad forward.",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(share("homemy_bringup", "launch", "robot.launch.py")),
                launch_arguments={
                    "bridge_address": LaunchConfiguration("bridge_address"),
                    "bridge_port": LaunchConfiguration("bridge_port"),
                    "storage_root": LaunchConfiguration("storage_root"),
                    "use_imu_fusion": LaunchConfiguration("use_imu_fusion"),
                    "robot_params_file": local,
                    "drive_port": drive_port,
                    "lidar_port": lidar_port,
                    "imu_port": imu_port,
                    # The joystick driver is the one part replaced on the robot's side.
                    "start_joy_driver": "false",
                }.items(),
            ),
            Node(
                package="homemy_simulation",
                executable="sim_base",
                name="homemy_sim_base",
                output="screen",
                parameters=[
                    share("homemy_simulation", "config", "sim_lidar.yaml"),
                    share("homemy_simulation", "config", "sim_imu.yaml"),
                    {
                        "world_file": LaunchConfiguration("world_file"),
                        "geometry_file": share("homemy_description", "config", "geometry.yaml"),
                        "drive_interface": "modbus",
                        "modbus_port_link": drive_port,
                        "lidar_interface": "serial",
                        "lidar_port_link": lidar_port,
                        "imu_interface": "modbus",
                        "imu_port_link": imu_port,
                    },
                ],
            ),
            # The simulated person holds the direction pad forward.
            Node(
                package="homemy_simulation",
                executable="sim_controller",
                name="homemy_sim_controller",
                output="screen",
                parameters=[{"driving": ParameterValue(LaunchConfiguration("operator_drives"), value_type=bool)}],
            ),
        ]
    )
