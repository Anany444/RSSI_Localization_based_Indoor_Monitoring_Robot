from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='camera_ros',
            executable='camera_node',
            name='camera',
            parameters=[
                {'width': 640},
                {'height': 480},
                # Force 15 FPS via Frame Duration 
                {'FrameDurationLimits': [66666, 66666]},
               # {'role': 'video'}, # default mode works fine for us
            ]
        )
    ])
