import rclpy
from rclpy.node import Node
from example_interfaces.srv import SetBool
import csv
import time
import os
import subprocess
import re

class KalmanFilter:
    def __init__(self, process_variance=1e-5, measurement_variance=1e-1):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.estimated_value = -100.0  # Initial guess for RSSI
        self.error_covariance = 1.0

    def update(self, measurement):
        # Prediction update
        prior_error_covariance = self.error_covariance + self.process_variance

        # Measurement update 
        kalman_gain = prior_error_covariance / (prior_error_covariance + self.measurement_variance)
        self.estimated_value = self.estimated_value + kalman_gain * (measurement - self.estimated_value)
        self.error_covariance = (1 - kalman_gain) * prior_error_covariance
        
        return self.estimated_value

class RSSILogger(Node):
    def __init__(self):
        super().__init__('rssi_pi_scanner')

        self.filename = 'wifi_fingerprint_dataset.csv'
        self.interface = 'wlan0' 
        
        # Targeted BSSIDs 
        self.target_bssids = [
            'ea:b0:c5:11:92:25', # AP0
            'f2:0b:9b:04:2f:7e', # AP1
            '76:09:6d:d7:74:0f', # AP2
            '8a:21:1a:1b:f8:8a'  # AP3
        ]

        # Initialize Filters
        self.filters = [KalmanFilter() for _ in range(4)]
        
        # --- STATE ---
        self.current_zone = "None"
        self.is_logging = False
        self.point_count = 0

        # --- SERVICE & PARAMETERS ---
        self.declare_parameter('zone_name', 'Room1')
        self.srv = self.create_service(SetBool, 'log_control', self.service_callback)

        # Scanner loop 
        self.timer = self.create_timer(0.1, self.scan_and_log)

    def service_callback(self, request, response):
        if request.data:
            self.current_zone = self.get_parameter('zone_name').get_parameter_value().string_value
            self.is_logging = True
            self.point_count = 0
            response.success = True
            response.message = f"STARTED logging zone: {self.current_zone}"
        else:
            self.is_logging = False
            response.success = True
            response.message = f"STOPPED. Total points for {self.current_zone}: {self.point_count}"
        return response

    def get_rssi_data(self):
        # Run iwlist scan
        try:
            cmd = ["sudo", "iwlist", self.interface, "scan"]
            result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8')
        except Exception as e:
            self.get_logger().error(f"Scan failed: {e}")
            return None

        # Dictionary to hold found signals
        found_signals = {bssid: -100 for bssid in self.target_bssids} # Default -100 

        # Regex to find BSSID and Signal Level
        cells = result.split('Cell ')
        for cell in cells:
            # Extract MAC
            mac_match = re.search(r"Address: ([\dA-F:]{17})", cell, re.I)
            # Extract RSSI 
            rssi_match = re.search(r"Signal level=(-?\d+) dBm", cell)
            
            if mac_match and rssi_match:
                mac = mac_match.group(1).lower()
                rssi = int(rssi_match.group(1))
                if mac in found_signals:
                    found_signals[mac] = rssi

        return [found_signals[b] for b in self.target_bssids]

    def scan_and_log(self):
        if not self.is_logging:
            return

        raw_rssis = self.get_rssi_data()
        if raw_rssis is None:
            return

        filtered_rssis = [self.filters[i].update(raw_rssis[i]) for i in range(4)]
        
        # Format: timestamp, zone, raw0, filt0, raw1, filt1, raw2, filt2, raw3, filt3
        timestamp = time.time()
        row = [timestamp, self.current_zone]
        for r, f in zip(raw_rssis, filtered_rssis):
            row.extend([r, round(f, 2)])

        # Save to CSV
        file_exists = os.path.isfile(self.filename)
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists or os.stat(self.filename).st_size == 0:
                writer.writerow(['time', 'zone', 
                                 'ap0_raw', 'ap0_filt', 
                                 'ap1_raw', 'ap1_filt', 
                                 'ap2_raw', 'ap2_filt', 
                                 'ap3_raw', 'ap3_filt'])
            writer.writerow(row)

        self.point_count += 1
        
        # Console Output: Current points and the list of 4 filtered RSSIs
        display_list = [round(f, 1) for f in filtered_rssis]
        self.get_logger().info(f"Zone: {self.current_zone} | Count: {self.point_count} | RSSI: {display_list}")

def main(args=None):
    rclpy.init(args=args)
    node = RSSILogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
