import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String
import joblib
import numpy as np
from ament_index_python.packages import get_package_share_directory
import os

class ZonePredictor(Node):
    def __init__(self):
        super().__init__('zone_predictor')
        model_path = os.path.join(get_package_share_directory('rssi'), 'models')

        try:
            self.model_raw = joblib.load(os.path.join(model_path, 'knnRaw_model.pkl'))
            self.model_filt = self.model_raw # using the same model 
            self.get_logger().info("Models loaded successfully")
        except Exception as e:
            self.get_logger().error(f" Model load failed: {e}")

        self.sub_raw = self.create_subscription(Float32MultiArray, '/rssi/raw', self.raw_callback, 10)
        self.sub_filt = self.create_subscription(Float32MultiArray, '/rssi/filtered', self.filt_callback, 10)
        self.pub_pred_raw = self.create_publisher(String, '/predict/raw', 1)
        self.pub_pred_filtered = self.create_publisher(String, '/predict/filtered', 1)

    def raw_callback(self, msg):
        prediction =self.predict_zone(msg.data, self.model_raw)
        self.get_logger().info(f"ZONE_RAW: {prediction}")
        pred_msg = String()
        pred_msg.data = str(prediction) 
        self.pub_pred_raw.publish(pred_msg)

    def filt_callback(self, msg):
        prediction = self.predict_zone(msg.data, self.model_filt)
        self.get_logger().info(f"ZONE_FILTERED: {prediction}")
        pred_msg = String()
        pred_msg.data = str(prediction)
        self.pub_pred_filtered.publish(pred_msg)
        
    def predict_zone(self, data, model):
        sample = np.array([data])
        pred = model.predict(sample)
        return pred[0]

def main():
    rclpy.init()
    node = ZonePredictor()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()