from launch import LaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    pkg_name = 'rssi'
    pkg_path = os.path.join(get_package_share_directory(pkg_name))
    slam_config_path = os.path.join(pkg_path, 'config', 'slam.yaml')
    slam_toolbox_share = get_package_share_directory('slam_toolbox')
    slam_launch_file = os.path.join(slam_toolbox_share, 'launch', 'online_async_launch.py')
    rplidar_pkg_share = get_package_share_directory('rplidar_ros')
    rplidar_launch_file = os.path.join(rplidar_pkg_share, 'launch', 'rplidar_a1_launch.py')

    return LaunchDescription([
        # 1. Static Transform Publisher: base_footprint -> laser
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_laser_broadcaster',
            arguments=[
                '--x', '0',
                '--y', '0',
                '--z', '0',
                '--yaw', '0',
                '--pitch', '0',
                '--roll', '0',
                '--frame-id', 'base_footprint',
                '--child-frame-id', 'laser'
            ],
            output='screen',
        ),

        IncludeLaunchDescription(
        PythonLaunchDescriptionSource(rplidar_launch_file),
        launch_arguments={
            'serial_port': '/dev/ttyUSB0'
            }.items()
        ),
        
        # 2. Laser Scan Matcher (Providing Odom -> base_footprint tf)
        Node(
            package='ros2_laser_scan_matcher',
            executable='laser_scan_matcher',
            name='laser_scan_matcher',
            output='screen'
        ),

        # 3. SLAM Toolbox Async
        IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_launch_file),
        launch_arguments={
            'slam_params_file': slam_config_path,
            'use_sim_time': 'false' 
        }.items()
        )
    ])