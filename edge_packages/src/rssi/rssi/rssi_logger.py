import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import subprocess
import re
import time

class KalmanFilter:
    def __init__(self, process_variance=1e-5, measurement_variance=1e-1):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.estimated_value = -90.0
        self.error_covariance = 1.0

    def update(self, measurement):
        prior_error_covariance = self.error_covariance + self.process_variance
        kalman_gain = prior_error_covariance / (prior_error_covariance + self.measurement_variance)
        self.estimated_value = self.estimated_value + kalman_gain * (measurement - self.estimated_value)
        self.error_covariance = (1 - kalman_gain) * prior_error_covariance
        return self.estimated_value

class RSSIPublisher(Node):
    def __init__(self):
        super().__init__('rssi_publisher')
        self.raw_pub = self.create_publisher(Float32MultiArray, '/rssi/raw', 10)
        self.filt_pub = self.create_publisher(Float32MultiArray, '/rssi/filtered', 10)
        
        self.interface = 'wlan0'
        self.target_bssids = [
            'ea:b0:c5:11:92:25', 'f2:0b:9b:04:2f:7e', 
            'ce:ec:70:ba:27:7e', '8a:21:1a:1b:f8:8a'
        ]
        self.filters = [KalmanFilter() for _ in range(4)]
        self.timer = self.create_timer(0.1, self.publish_rssi)

    def get_rssi_data(self):
        try:
            result = subprocess.check_output(["sudo", "iwlist", self.interface, "scan"], stderr=subprocess.DEVNULL).decode('utf-8')
            found = {bssid: -100.0 for bssid in self.target_bssids}
            cells = result.split('Cell ')
            for cell in cells:
                mac_match = re.search(r"Address: ([\dA-F:]{17})", cell, re.I)
                rssi_match = re.search(r"Signal level=(-?\d+) dBm", cell)
                if mac_match and rssi_match:
                    mac = mac_match.group(1).lower()
                    if mac in found:
                        found[mac] = float(rssi_match.group(1))
            return [found[b] for b in self.target_bssids]
        except:
            return None

    def publish_rssi(self):
        raw_vals = self.get_rssi_data()
        if raw_vals:
            # Publish Raw
            raw_msg = Float32MultiArray()
            raw_msg.data = raw_vals
            self.raw_pub.publish(raw_msg)

            # Filter and Publish Filtered
            filt_vals = [self.filters[i].update(raw_vals[i]) for i in range(4)]
            filt_msg = Float32MultiArray()
            filt_msg.data = filt_vals
            self.filt_pub.publish(filt_msg)

def main():
    rclpy.init()
    node = RSSIPublisher()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
