from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import XMLLaunchDescriptionSource
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share = get_package_share_directory('rssi')
    bridge_launch_dir = os.path.join(get_package_share_directory('foxglove_bridge'), 'launch')

    conf_threshold = LaunchConfiguration('conf_threshold', default='0.3')
    kp_linear = LaunchConfiguration('kp_linear', default='1.2')
    kp_angular = LaunchConfiguration('kp_angular', default='0.5')

    declare_conf_threshold = DeclareLaunchArgument(
        'conf_threshold',
        default_value='0.3',
        description='YOLO confidence threshold for human detection'
    )
    declare_kp_linear = DeclareLaunchArgument(
        'kp_linear',
        default_value='1.2',
        description='Linear proportional gain for controller'
    )
    declare_kp_angular = DeclareLaunchArgument(
        'kp_angular',
        default_value='0.5',
        description='Angular proportional gain for controller'
    )

    hum_foll = Node(
        package='rssi',
        executable='human_follower',
        name='human_follower',
        parameters=[{
            'conf_threshold': conf_threshold,
            'kp_linear': kp_linear,
            'kp_angular': kp_angular,
        }],
        output='screen',
    )
    
    fox_bridge = IncludeLaunchDescription(
        XMLLaunchDescriptionSource(os.path.join(bridge_launch_dir, 'foxglove_bridge_launch.xml'))
    )

    return LaunchDescription([
        declare_conf_threshold,
        declare_kp_linear,
        declare_kp_angular,
        hum_foll,
        fox_bridge
    ])
