"""Start the mission manager with the recovery-free navigation tree."""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bt_xml = PathJoinSubstitution(
        [FindPackageShare("homemy_navigation"), "config", "navigate_to_pose_no_recovery.xml"]
    )
    return LaunchDescription(
        [
            Node(
                package="homemy_mission",
                executable="mission_manager",
                name="mission_manager",
                output="screen",
                parameters=[{"bt_xml": bt_xml}],
            ),
        ]
    )
