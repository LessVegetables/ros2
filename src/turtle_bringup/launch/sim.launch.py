from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """Запустить одну ноду turtlesim_node из пакета turtlesim."""
    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            output='screen',
        ),
    ])
