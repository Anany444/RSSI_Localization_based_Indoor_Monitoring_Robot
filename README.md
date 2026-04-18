# RSSI Localization based Indoor Monitoring Robot
A differential drive robot capable of localizing itself using wifi signal strength fingerprinting and monitor the indoor environment showcasing various features including teleop, fog computing, lidar odometry, 2d slam and autonomous navigation

<p align="center">
  <img src="https://github.com/user-attachments/assets/9b42a66e-3c8e-4bbe-bc0a-5d54e3c73606" width="32%" />
  <img src="https://github.com/user-attachments/assets/e57b71be-bc09-4ab0-a2ca-6cafdfde8cab" width="32%" />
  <img src="https://github.com/user-attachments/assets/2a8b6a3e-d282-4039-a773-316b56935f66" width="32%" />
</p>

##🛠️ Hardware & Components

**Edge Compute & Control**
* **Raspberry Pi 5:** Running Ubuntu 24.04 and ROS2 Jazzy, acts as the primary onboard edge node. It handles data preprocessing, and bridges communication to the fog node via DDS and runs slam_toolbox and nav2.
* **ESP32 Microcontroller:** Serves as the low-level hardware interface. It receives velocity commands from the Pi and translates them into real-time PWM signals.

**Sensors**
* **RPLIDAR A1 2d LiDAR:** Scans the environment to provide raw laser scan data for LiDAR odometry and SLAM mapping.
* **OV5647 Camera Module:** Captures the live visual feed used by the fog node for YOLOv8n human detection and visual servoing.
  
**Actuators & Power**
* **DC Motors:** Provides movement for the differential-drive chassis.
* **L298N Motor Driver:** Translates the PWM signals from the ESP32 into raw power for the DC motors.
* **3S Li-ion Battery:** Supplies high-current power specifically for the motors and motor driver.
* **Power Bank:** Provides isolated, stable power delivery directly to the Raspberry Pi.

* **Fog Compute**
* **Base Station Laptop:** Running Ubuntu 24.04 and ROS2 Jazz, acts as the fog node to offload heavy computations. It runs the zone predictor KNN model, YOLO inference, and Foxglove visualization.

## 🚀 Key Features
* **Teleoperation:** Manual keyboard control mode that allows for remote operation.
* **Fog-Edge Distributed Computing:** Optimizes performance by offloading heavy computations like YOLO inference to a Fog Node (Laptop) while maintaining real-time hardware control on the Edge Node (Raspberry Pi)
* **Multi-Modal State Estimation (LO + RSSI):** Uses LiDAR Odometry (LO) as primary odometry source with the Wi-Fi signal strength (RSSI) based indoor localization as fallback mechanism.
  <img width="1920" height="1067" alt="Screenshot from 2026-04-19 00-04-19" src="https://github.com/user-attachments/assets/d9cfa5d4-bc15-40ad-9228-1c3d4ae40419" />
  <img width="1920" height="1067" alt="image" src="https://github.com/user-attachments/assets/143d4cc2-ee1d-4a5f-94d7-b71db2b1bf6f" />
  Note: The filtered prediction doesnt work because of improper tuning.
  
* **Human Following:** Implements real-time visual servoing using YOLOv8n and a proportional controller to track and follow detected persons based on bounding box area .
  






  
* **2D SLAM & Mapping:** Utilizes the SLAM Toolbox for asynchronous mapping and pose-graph optimization to minimize odometry drift in feature-rich environments.
* **Machine Learning Zone Prediction:** Employs a K-Nearest Neighbors (KNN) classifier to accurately predict robot location zones based on processed RSSI data patterns.


## System Architecture

The system follows a modular ROS 2 pipeline covering mapping, localization, perception, navigation, control, and visualisation.

### 1. Mapping and Localization
- The `ros2_laser_scan_matcher` package provides LiDAR-based odometry using scan matching (ICP).
- The `ekf_node` fuses wheel odometry, IMU data, and LiDAR odometry into a robust filtered odometry, publishes transform `odom → base_footprint` for local estimation.
- The `slam_toolbox` package performs real-time 2D SLAM to generate an occupancy grid map of the environment and continuously corrects the odometry drift, publishes transform `map → odom` for global localization.

### 2. Rack Detection
- The `rack_detector` node processes the occupancy grid map to identify rack candidates based on geometric features and visualizes the detections using Matplotlib.
- Detected racks are published to a topic using the custom `warehouse_msgs` interfaces (`Rack` and `RackArray`).

### 3. Mission Control
- The `warehouse_mission_control` package coordinates the overall autonomous workflow.
- The `mission_executor` node manages high-level task execution by sending navigation goals via Nav2 and controlling the camera joint for vertical scanning.
- It controls the transitions between navigation and perception states based on mission logic.
  
### 4. QR Code Detection
- The `qr_pipeline` node processes the camera stream to detect QR codes using a YOLO-based model (`models/qr_model.pt`).
- The detected region is then preprocessed and decoded to extract the shelf content information.
  
### 5. Control
- The robot is controlled using `ros2_control`, with the `gz_ros2_control` plugin interfacing the controllers with the Gazebo simulation.
- A `diff_drive_controller` based controller is used for planar (x–y and yaw) motion of the robot base, a `joint_trajectory_controller` based camera joint controller is used for vertical camera movement while a `joint_state_broadcaster` based controller publishes joint states for feedback and visualization.
  
### 6. Visualisation
- RViz visualizes the map, robot pose, planned path, and live QR detection feed.

---

## Repository Structure
```text
├── edge_packages
│   └── src
│       ├── camera_ros
│       ├── laser_scan_matcher
│       │   ├── csm
│       │   └── ros2_laser_scan_matcher
│       ├── rplidar_ros
│       └── rssi
│           ├── config
│           │   ├── nav2.yaml
│           │   └── slam.yaml
│           ├── launch
│           │   ├── cam.launch.py
│           │   ├── nav2.launch.py
│           │   └── slam.launch.py
│           ├── rssi
│           │   ├── broadcaster_qos.py
│           │   ├── data_zone_serv.py
│           │   ├── rssi_logger.py
│           │   └── velocity_relay.py
├── fog_packages
│   └── src
│       └── rssi
│           ├── launch
│           │   ├── human_follower.launch.py
│           │   └── rssi_localization.launch.py
│           ├── models
│           │   ├── knnRaw_model.pkl
│           │   └── yolov8n.pt
│           ├── rssi
│           │   ├── human_follower.py
│           │   ├── velocity_relay.py
│           │   ├── visualize_prediction.py
│           │   └── zone_predictor.py
├── cyclonedds.xml
├── LICENSE
└── README.md
```
---

## Installation

```bash
# Create workspace
mkdir -p ~/warehouse_ws/src
cd ~/warehouse_ws/src

# Clone repository
git clone https://github.com/Anany444/Autonomous_Warehouse_Inventory_Scanning_Robot.git

# Move to workspace root
cd ~/warehouse_ws

# Source ROS 2
source /opt/ros/humble/setup.bash

# Install ROS dependencies
rosdep install --from-paths src --ignore-src -r -y

# Build the workspace
colcon build --symlink-install
source install/setup.bash
```

### Python Dependencies
```bash
pip install ultralytics opencv-python zxing-cpp matplotlib
```
---

## Usage
### 1. Launch the Full System
This launch starts the Gazebo simulation, robot state publisher, ekf, SLAM,  Nav2, the rack detector, the QR pipeline, the mission executor, and RViz.

```bash
# Source the workspace
source ~/warehouse_ws/install/setup.bash

#Launch everything
ros2 launch warehouse_robot_bringup final.launch.py
```

### 2. Mission Management
The mission executor uses `/racks_found` and `/start_navigation`  services to manage tasks during runtime.

1. **Map the environment and detect racks**  
   Use teleoperation to explore the warehouse and build the map. Ensure that racks are detected in the `rack_detector` Matplotlib window:

  ```bash
  ros2 run teleop_twist_keyboard teleop_twist_keyboard
  ```
2. **Store detected rack locations**
Once all racks are detected, call the `/racks_found` service to store their center coordinates:

```bash
ros2 service call /racks_found std_srvs/srv/Trigger
```
3. **Start Autonomous mission**
Move the robot to the warehouse entry point and call the `/start_navigation` service to begin mission execution:

```bash
ros2 service call /start_navigation std_srvs/srv/Trigger
```
4. **Monitor QR decoding output**
The robot navigates to each rack and scans the QR codes. The decoded data can be monitored via:

```bash
# In a new terminal, source the workspace
source ~/warehouse_ws/install/setup.bash

# Echo decoded qr output string
ros2 topic echo /qr_model/output_string
```
---
