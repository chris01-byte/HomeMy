"""Localization and path planning for driving to rooms.

- map_server and AMCL are lifecycle nodes owned by the localization manager,
  which switches between mapping (slam_toolbox, see slam.launch.py) and
  navigation on the saved map;
- planner, controller, velocity smoother, and bt_navigator run all the time
  under Nav2's lifecycle manager. Their commands leave through the smoother
  to the motion gate (/homemy/cmd_vel/nav), never to the drive.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    share = FindPackageShare("homemy_navigation")
    params = LaunchConfiguration("nav2_params_file")
    storage_root = LaunchConfiguration("storage_root")
    bt_xml = PathJoinSubstitution([share, "config", "navigate_to_pose_no_recovery.xml"])
    managed = ["controller_server", "planner_server", "velocity_smoother", "bt_navigator"]
    return LaunchDescription(
        [
            DeclareLaunchArgument("nav2_params_file", default_value=PathJoinSubstitution([share, "config", "nav2.yaml"])),
            DeclareLaunchArgument("storage_root", default_value="~/.local/share/homemy"),
            Node(package="nav2_map_server", executable="map_server", name="map_server",
                 output="screen", parameters=[params]),
            Node(package="nav2_amcl", executable="amcl", name="amcl", output="screen", parameters=[params]),
            Node(package="nav2_planner", executable="planner_server", name="planner_server",
                 output="screen", parameters=[params]),
            Node(package="nav2_controller", executable="controller_server", name="controller_server",
                 output="screen", parameters=[params], remappings=[("cmd_vel", "cmd_vel_nav_raw")]),
            Node(package="nav2_velocity_smoother", executable="velocity_smoother", name="velocity_smoother",
                 output="screen", parameters=[params],
                 remappings=[("cmd_vel", "cmd_vel_nav_raw"), ("cmd_vel_smoothed", "/homemy/cmd_vel/nav")]),
            Node(package="nav2_bt_navigator", executable="bt_navigator", name="bt_navigator",
                 output="screen", parameters=[params, {"default_nav_to_pose_bt_xml": bt_xml}]),
            Node(package="nav2_lifecycle_manager", executable="lifecycle_manager",
                 name="lifecycle_manager_navigation", output="screen",
                 parameters=[{"autostart": True, "node_names": managed, "bond_timeout": 4.0}]),
            Node(package="homemy_navigation", executable="localization_manager", name="localization_manager",
                 output="screen",
                 parameters=[{"maps_root": [storage_root, "/maps"],
                              "last_pose_file": [storage_root, "/localization/last_pose.json"]}]),
        ]
    )
