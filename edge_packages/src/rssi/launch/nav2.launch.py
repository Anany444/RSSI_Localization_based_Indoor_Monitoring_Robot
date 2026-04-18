import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_name = 'rssi'
    pkg_share = get_package_share_directory(pkg_name)
    
    nav2_bringup_share = get_package_share_directory('nav2_bringup')
    nav2_launch_file = os.path.join(nav2_bringup_share, 'launch', 'navigation_launch.py')
    nav2_params_path = os.path.join(pkg_share, 'config', 'nav2.yaml')
    
    slam_launch_file = os.path.join(pkg_share, 'launch', 'slam.launch.py')

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch_file)
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_launch_file),
            launch_arguments={
                'params_file': nav2_params_path,
                'use_sim_time': 'false'
            }.items()
        )
    ])