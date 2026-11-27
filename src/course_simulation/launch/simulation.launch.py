"""
ПР07: Gazebo (headless) + robot_state_publisher + один мост ros_gz + два адаптера.

Пример: ros2 launch course_simulation simulation.launch.py world:=<sdf>
bridge_config:=<yaml> headless:=true namespace:=sim
"""

from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess, GroupAction,
                            SetEnvironmentVariable)
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import (Command, EnvironmentVariable, LaunchConfiguration,
                                  PathJoinSubstitution)
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    """Сервер Gazebo, мост и адаптеры; ROS-ноды на времени симуляции."""
    sim_share = FindPackageShare('course_simulation')
    desc_share = FindPackageShare('course_description')
    world = LaunchConfiguration('world')
    bridge_config = LaunchConfiguration('bridge_config')
    headless = LaunchConfiguration('headless')
    namespace = LaunchConfiguration('namespace')
    sim_time = {'use_sim_time': True}
    robot_description = ParameterValue(
        Command(['xacro ', PathJoinSubstitution([desc_share, 'urdf', 'vehicle.urdf.xacro'])]),
        value_type=str)

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value=PathJoinSubstitution(
            [sim_share, 'worlds', 'mcity-minimal.sdf'])),
        DeclareLaunchArgument('bridge_config', default_value=PathJoinSubstitution(
            [sim_share, 'config', 'bridge.yaml'])),
        DeclareLaunchArgument('headless', default_value='true',
                              description='true — сервер без окна с EGL-рендерингом сенсоров'),
        DeclareLaunchArgument('namespace', default_value='sim',
                              description='пространство имён ROS-нод (не меняет топики моста)'),
        # model://course_ackermann ищется по GZ_SIM_RESOURCE_PATH; прежнее значение сохраняется.
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', [
            PathJoinSubstitution([sim_share, 'models']), ':',
            EnvironmentVariable('GZ_SIM_RESOURCE_PATH', default_value='')]),
        ExecuteProcess(cmd=['gz', 'sim', '-s', '-r', '--headless-rendering', world],
                       output='screen', condition=IfCondition(headless)),
        ExecuteProcess(cmd=['gz', 'sim', '-r', world],
                       output='screen', condition=UnlessCondition(headless)),
        GroupAction([
            PushRosNamespace(namespace),
            Node(package='robot_state_publisher', executable='robot_state_publisher',
                 name='robot_state_publisher', output='screen',
                 parameters=[{'robot_description': robot_description}, sim_time]),
            Node(package='ros_gz_bridge', executable='parameter_bridge', name='bridge',
                 output='screen',
                 parameters=[{'config_file': bridge_config}, sim_time]),
            Node(package='course_simulation', executable='drive_adapter',
                 name='drive_adapter', output='screen', parameters=[sim_time]),
            Node(package='course_simulation', executable='odom_adapter',
                 name='odom_adapter', output='screen', parameters=[sim_time]),
        ]),
    ])
