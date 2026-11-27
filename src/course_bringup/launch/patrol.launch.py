"""
ПР05: turtlesim + patrol + pose_relay + pose_subscriber в одном пространстве имён.

Пример: ros2 launch course_bringup patrol.launch.py namespace:=robot_a
subscriber_reliability:=reliable record:=false
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, GroupAction, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description() -> LaunchDescription:
    """Собрать систему; record управляет recorder через IfCondition."""
    namespace = LaunchConfiguration('namespace')
    record = LaunchConfiguration('record')
    bag_dir = LaunchConfiguration('bag_dir')
    reliability = LaunchConfiguration('subscriber_reliability')

    args = [
        DeclareLaunchArgument('namespace', default_value='robot_a',
                              description='пространство имён системы робота'),
        DeclareLaunchArgument('record', default_value='false',
                              description='true — записать <namespace>/sensor_pose в MCAP'),
        DeclareLaunchArgument('bag_dir', default_value='bags/robot_a',
                              description='каталог новой записи (не должен существовать)'),
        DeclareLaunchArgument('subscriber_reliability', default_value='best_effort',
                              choices=['reliable', 'best_effort'],
                              description='надёжность QoS подписчика pose_subscriber'),
    ]

    # Один turtlesim глобально: топики /turtle1/pose и /turtle1/cmd_vel без namespace.
    simulator = Node(package='turtlesim', executable='turtlesim_node',
                     name='turtlesim', output='screen')

    robot = GroupAction([
        PushRosNamespace(namespace),
        Node(package='patrol', executable='patrol', name='patrol', output='screen',
             remappings=[('turtle1/pose', '/turtle1/pose'),
                         ('cmd_vel', '/turtle1/cmd_vel')]),
        Node(package='patrol', executable='pose_relay', name='pose_relay', output='screen',
             remappings=[('pose', '/turtle1/pose')]),
        Node(package='patrol', executable='pose_subscriber', name='pose_subscriber',
             output='screen', parameters=[{'reliability': reliability}]),
    ])

    recorder = ExecuteProcess(
        cmd=['ros2', 'bag', 'record', '-s', 'mcap', '-o', bag_dir,
             '--topics', PathJoinSubstitution(['/', namespace, 'sensor_pose'])],
        output='screen',
        condition=IfCondition(record),
    )

    return LaunchDescription(args + [
        LogInfo(msg=['namespace=', namespace, ' subscriber_reliability=', reliability,
                     ' record=', record]),
        simulator,
        robot,
        recorder,
    ])
