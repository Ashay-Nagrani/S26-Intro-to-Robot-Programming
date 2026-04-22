from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():

    config_file = os.path.join(
        FindPackageShare('subteam2_driving').find('subteam2_driving'),
        'config',
        'driving_params.yaml'
    )

    return LaunchDescription([

        Node(
            package='subteam2_driving',
            executable='drive_controller',
            name='drive_controller',
            parameters=[config_file],
            output='screen'
        ),

        Node(
            package='subteam2_driving',
            executable='stop_reset_service',
            name='stop_reset_service',
            output='screen'
        ),
        
        Node(
            package='subteam2_driving',
            executable='test_pattern',
            name='test_pattern_publisher',
            parameters=[config_file],
            output='screen'
        ),

    ])
