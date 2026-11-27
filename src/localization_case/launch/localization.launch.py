"""
ПР08: map_server, amcl и lifecycle_manager_localization одной командой.

Пример: ros2 launch localization_case localization.launch.py
params_file:=$PWD/src/localization_case/config/amcl.yaml
map:=$PWD/.course-kit/v1/fixtures/pr08/map.yaml
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    """Все ноды на времени симуляции; имена совпадают с ключами YAML."""
    params_file = LaunchConfiguration('params_file')
    map_yaml = LaunchConfiguration('map')
    sim_time = {'use_sim_time': True}
    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution(
                [FindPackageShare('localization_case'), 'config', 'amcl.yaml']),
            description='профиль AMCL / map_server / lifecycle manager'),
        DeclareLaunchArgument('map', description='абсолютный путь к map.yaml'),
        Node(package='nav2_map_server', executable='map_server', name='map_server',
             output='screen', parameters=[params_file, {'yaml_filename': map_yaml}, sim_time]),
        Node(package='nav2_amcl', executable='amcl', name='amcl', output='screen',
             parameters=[params_file, sim_time]),
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_localization', output='screen',
             parameters=[params_file, sim_time]),
    ])
