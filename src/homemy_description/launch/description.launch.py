"""Publish the HomeMy robot model with robot_state_publisher."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    oak_tilt_deg = LaunchConfiguration("oak_tilt_deg")
    use_sim_time = LaunchConfiguration("use_sim_time")
    model = PathJoinSubstitution(
        [FindPackageShare("homemy_description"), "urdf", "homemy.urdf.xacro"]
    )
    robot_description = ParameterValue(
        Command(["xacro ", model, " oak_tilt_deg:=", oak_tilt_deg]),
        value_type=str,
    )
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "oak_tilt_deg",
                default_value="0.0",
                description="OAK tilt from the calibration record, positive looks down.",
            ),
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                parameters=[
                    {
                        "robot_description": robot_description,
                        "use_sim_time": use_sim_time,
                    }
                ],
            ),
        ]
    )
