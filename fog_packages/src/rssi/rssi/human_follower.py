#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from geometry_msgs.msg import Twist
from std_srvs.srv import SetBool
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import cv2
import numpy as np
import torch
from ultralytics import YOLO
from ament_index_python.packages import get_package_share_directory
import os

class HumanFollower(Node):
    def __init__(self):
        super().__init__('human_follower')
        
        # load yolo model
        try:
            package_share = get_package_share_directory('rssi')
            def_path = os.path.join(package_share, 'models', 'yolov8n.pt')
        except Exception as e:
            self.get_logger().error(f"Could not find package_share or model {e}")
            return

    
        self.declare_parameter('conf_threshold', 0.3) 
        
        # P Controller Parameters ---
        self.declare_parameter('kp_linear', 1.2)
        self.declare_parameter('kp_angular', 0.5)

        self.kp_v = self.get_parameter('kp_linear').value
        self.kp_w = self.get_parameter('kp_angular').value

        #  ROCm / PyTorch Setup 
        if torch.cuda.is_available():
            self.get_logger().info(f"AMD GPU Detected, Device: {torch.cuda.get_device_name(0)}")
            self.device = 'cuda'
        else:
            self.get_logger().warn("ROCm not detected")
            self.device = 'cpu'

        model_path = def_path
        self.get_logger().info("Loading native YOLOv8 PyTorch Model...")
        self.model = YOLO(model_path)
        self.model.to(self.device)

        # QoS Setup 
        wifi_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        #  Follower State Variables 
        self.is_following = False
        self.prev_err_v = 0.0 # was used for d part in pd controller but we switched to p only due to low fps 
        self.prev_err_w = 0.0
        self.last_control_time = self.get_clock().now()

        #  Base Variables
        self.is_processing = False
        self.target_fps = 15.0  
        self.last_pub_time = self.get_clock().now()
        self.conf_thresh = self.get_parameter('conf_threshold').value
        
        #  ROS 2 Interfaces
        self.sub = self.create_subscription(
            CompressedImage, '/broadcast/camera/image_raw/compressed', self.image_callback, wifi_qos)
            
        self.pub_debug = self.create_publisher(
            CompressedImage, '/debug/human_image/compressed', wifi_qos)
            
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.srv = self.create_service(SetBool, '/human_follower', self.follower_toggle_cb)

        self.get_logger().info(" YOLOv8 Node Running")

    def follower_toggle_cb(self, request, response):
        #Service callback to start/stop following logic
        self.is_following = request.data
        response.success = True
        state = "ENABLED" if self.is_following else "DISABLED"
        response.message = f"Visual Servoing Human Follower {state}"
        self.get_logger().info(response.message)
        
        # Stop the robot immediately when disabling
        if not self.is_following:
            self.publish_zero_velocity()
            
        return response

    def publish_zero_velocity(self):
        msg = Twist()
        self.cmd_pub.publish(msg)

    def image_callback(self, msg):
        if self.is_processing:
            return

        current_time = self.get_clock().now()
        time_diff = (current_time - self.last_pub_time).nanoseconds / 1e9
        
        if time_diff < (1.0 / self.target_fps):
            return 

        self.is_processing = True
        self.last_pub_time = current_time
        
        try:
            # 1. Decode Compressed Image
            np_arr = np.frombuffer(msg.data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return

            img_h, img_w = frame.shape[:2]

            # 2. Run Inference
            results = self.model(frame, conf=self.conf_thresh, classes=[0], verbose=False)
            annotated_frame = results[0].plot()

            # --- Visual Servoing Logic ---
            if self.is_following:
                # Extract bounding boxes (xyxy format)
                boxes = results[0].boxes.xyxy.cpu().numpy()
                
                if len(boxes) > 0:
                    best_box = None
                    best_score = -float('inf')
                    
                    # Target Selection Logic
                    for box in boxes:
                        x1, y1, x2, y2 = box
                        box_cx = (x1 + x2) / 2.0
                        box_h = y2 - y1
                        
                        # Score 1: Proximity to center (1.0 is dead center, 0.0 is edge)
                        center_score = 1.0 - (abs(box_cx - img_w / 2.0) / (img_w / 2.0))
                        
                        # Score 2: Height ratio (cap at 0.9 to prevent overly close tracking from skewing)
                        height_score = min(box_h / img_h, 0.9)
                        
                        # Combined Score (You can tune the weights here if needed)
                        score = center_score + height_score
                        
                        if score > best_score:
                            best_score = score
                            best_box = box

                    # Control Logic on the Best Box
                    if best_box is not None:
                        x1, y1, x2, y2 = best_box
                        box_cx = (x1 + x2) / 2.0
                        box_h_norm = (y2 - y1) / img_h
                        img_cx = img_w / 2.0

                        # Angular Error (Normalized between -0.5 and 0.5)
                        # Positive error means box is to the left -> turn left (+z)
                        e_w_raw = (img_cx - box_cx) / img_w
                        
                        # 10% Deadband for rotation
                        if abs(e_w_raw) < 0.10:
                            err_w = 0.0
                        else:
                            err_w = e_w_raw - (np.sign(e_w_raw) * 0.15)

                        # Linear Error (Vertical Length / Distance)
                        # 65% to 80% Deadband
                        if 0.65 <= box_h_norm <= 0.80:
                            err_v = 0.0
                        elif box_h_norm < 0.65:
                            err_v = 0.65 - box_h_norm  # Positive: move forward
                        else:  # box_h_norm > 0.80
                            err_v = 0.80 - box_h_norm  # Negative: move backward

                        # P Equations
                        cmd = Twist()
                        cmd.linear.x = (self.kp_v * err_v) 
                        cmd.angular.z = (self.kp_w * err_w) 

                        # clip to min and max speed
                        cmd.linear.x = float(np.clip(cmd.linear.x, -0.2, 0.2))
                        cmd.angular.z = float(np.clip(cmd.angular.z, -0.5, 0.5))

                        self.cmd_pub.publish(cmd)

                        # Draw a thick green box around the tracked target for debug viewing
                        cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
                        cv2.putText(annotated_frame, "TRACKING", (int(x1), int(y1)-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                else:
                    # Target lost
                    self.publish_zero_velocity()
            
            # 4. Compress and Publish to Foxglove
            _, debug_jpeg = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            debug_msg = CompressedImage()
            debug_msg.header = msg.header
            debug_msg.format = "jpeg"
            debug_msg.data = debug_jpeg.tobytes()
            self.pub_debug.publish(debug_msg)

        except Exception as e:
            self.get_logger().error(f"Inference error: {str(e)}")

        finally:
            self.is_processing = False

def main():
    rclpy.init()
    node = HumanFollower()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()