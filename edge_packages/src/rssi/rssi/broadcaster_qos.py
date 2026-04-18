#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage, CameraInfo
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

class QoSRelayNode(Node):
    def __init__(self):
        super().__init__('qos_relay_node')

        # QOS profile for low latency
        wifi_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT, # BEST_EFFORT instead of RELIABLE for sending the most recent frame without waiting in long queues for previous msgs to reach
            history=HistoryPolicy.KEEP_LAST, # helps low memory usage and low processing overhead for subscribers
            depth=1
        )

        # Publishers under /broadcast namespace indicating configured before sending 
        self.pub_comp = self.create_publisher(CompressedImage, '/broadcast/camera/image_raw/compressed', wifi_qos)
        self.pub_info = self.create_publisher(CameraInfo, '/broadcast/camera/camera_info', wifi_qos)
        
        # Subscribers for camera info and images
        self.sub_comp = self.create_subscription(CompressedImage, '/camera/image_raw/compressed', self.comp_callback, 10)
        self.sub_info = self.create_subscription(CameraInfo, '/camera/camera_info', self.info_callback, 10)
        self.sub_raw = self.create_subscription(Image, '/camera/image_raw', self.raw_callback, 10)

        self.get_logger().info("Broadcaster activated")

    # callbacks publishing withoug processing
    def comp_callback(self, msg):
        self.pub_comp.publish(msg)

    def info_callback(self, msg):
        self.pub_info.publish(msg)

def main():
    rclpy.init()
    node = QoSRelayNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()