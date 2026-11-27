"""
ПР06: robot_state_publisher по развёрнутому Xacro и (по желанию) RViz.

Пример: ros2 launch course_description display.launch.py rviz:=true zero_joints:=false
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

WHEEL_JOINTS = (
    'front_left_steering_joint, front_right_steering_joint, front_left_wheel_joint, '
    'front_right_wheel_joint, rear_left_wheel_joint, rear_right_wheel_joint'
)


def generate_launch_description() -> LaunchDescription:
    """robot_state_publisher — единственный издатель /tf_static модели."""
    share = FindPackageShare('course_description')
    model = LaunchConfiguration('model')
    robot_description = ParameterValue(Command(['xacro ', model]), value_type=str)

    return LaunchDescription([
        DeclareLaunchArgument(
            'model', default_value=PathJoinSubstitution([share, 'urdf', 'vehicle.urdf.xacro']),
            description='путь к Xacro-модели'),
        DeclareLaunchArgument('rviz', default_value='true', description='запустить RViz'),
        DeclareLaunchArgument(
            'zero_joints', default_value='false',
            description='публиковать нулевые joint_states, чтобы колёса появились в /tf'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             name='robot_state_publisher', output='screen',
             parameters=[{'robot_description': robot_description}]),
        Node(package='rviz2', executable='rviz2', name='rviz2', output='log',
             arguments=['-d', PathJoinSubstitution([share, 'rviz', 'vehicle.rviz'])],
             condition=IfCondition(LaunchConfiguration('rviz'))),
        ExecuteProcess(
            cmd=['ros2', 'topic', 'pub', '-r', '10', '/joint_states',
                 'sensor_msgs/msg/JointState',
                 '{header: auto, name: [' + WHEEL_JOINTS + '], '
                 'position: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}'],
            output='log', condition=IfCondition(LaunchConfiguration('zero_joints'))),
    ])
