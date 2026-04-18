from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share = get_package_share_directory('rssi')

    zone_pred = Node(
            package='rssi',
            executable='zone_predictor',
            name='zone_predictor',
        )
    
    zone_viz = Node(
            package='rssi',
            executable='visualize_prediction',
            name='visualize_prediction',
        )

    return LaunchDescription([
        zone_pred,
        zone_viz
    ])
