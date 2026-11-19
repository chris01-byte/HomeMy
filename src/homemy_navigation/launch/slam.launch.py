"""slam_toolbox for the manual mapping run.

slam_toolbox is a lifecycle node under Jazzy; it is configured and activated
here. It starts paused: the mapping-run coordinator of homemy_mapping_mode
resets it when mapping mode begins and pauses it when mapping mode ends.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, LogInfo, RegisterEventHandler
from launch.events import matches_action
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import LifecycleNode
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
from launch_ros.substitutions import FindPackageShare
from lifecycle_msgs.msg import Transition


def generate_launch_description():
    params = PathJoinSubstitution([FindPackageShare("homemy_navigation"), "config", "slam_toolbox.yaml"])
    slam = LifecycleNode(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        namespace="",
        output="screen",
        parameters=[LaunchConfiguration("slam_params_file"), {"use_lifecycle_manager": False}],
    )
    configure = EmitEvent(
        event=ChangeState(
            lifecycle_node_matcher=matches_action(slam),
            transition_id=Transition.TRANSITION_CONFIGURE,
        )
    )
    activate = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=slam,
            start_state="configuring",
            goal_state="inactive",
            entities=[
                LogInfo(msg="slam_toolbox configured; activating."),
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(slam),
                        transition_id=Transition.TRANSITION_ACTIVATE,
                    )
                ),
            ],
        )
    )
    return LaunchDescription(
        [
            DeclareLaunchArgument("slam_params_file", default_value=params),
            slam,
            configure,
            activate,
        ]
    )
