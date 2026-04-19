



# RSSI Localization based Indoor Monitoring Robot
A differential drive robot capable of localizing itself using Wi-Fi signal strength fingerprinting and monitoring the indoor environment.

<p align="center">
  <img src="https://github.com/user-attachments/assets/9b42a66e-3c8e-4bbe-bc0a-5d54e3c73606" width="32%" />
  <img src="https://github.com/user-attachments/assets/e57b71be-bc09-4ab0-a2ca-6cafdfde8cab" width="32%" />
  <img src="https://github.com/user-attachments/assets/2a8b6a3e-d282-4039-a773-316b56935f66" width="32%" />
</p>

---

## 📖 Overview
This project showcases a complete autonomous mobile robot software and hardware stack. By leveraging a distributed Fog-Edge computing architecture, the system maintains real-time, low-level hardware control using a [Raspberry Pi and ESP32] (Edge) while offloading computationally heavy tasks—such as YOLOv8n visual servoing and KNN-based Wi-Fi RSSI prediction—to a base station laptop (Fog). Core capabilities include LO-backed 2D SLAM, autonomous Nav2 goal reaching, and dynamic human following.

---
## 📑 Table of Contents
- [Hardware & Components](#hardware)
- [Key Features](#features)
- [System Architecture](#architecture)
- [Repository Structure](#structure)
- [Installation & Setup](#setup)
- [Using Different Features](#usage)
---
  
##  <a id="hardware"></a>🛠️ Hardware & Components

**1. Edge Compute & Control**
* **Raspberry Pi 5:** Running Ubuntu 24.04 and ROS2 Jazzy, acts as the primary onboard edge node. It handles data preprocessing, and bridges communication to the fog node via DDS and runs slam_toolbox and nav2.
* **ESP32 Microcontroller:** Serves as the low-level hardware interface. It receives velocity commands from the Pi and translates them into real-time PWM signals.

**2. Sensors**
* **RPLIDAR A1 2d LiDAR:** Scans the environment to provide raw laser scan data for LiDAR odometry and SLAM mapping.
* **OV5647 Camera Module:** Captures the live visual feed used by the fog node for YOLOv8n human detection and visual servoing.
  
**3. Actuators & Power**
* **DC Motors:** Provides movement for the differential-drive chassis.
* **L298N Motor Driver:** Translates the PWM signals from the ESP32 into raw power for the DC motors.
* **3S Li-ion Battery:** Supplies high-current power specifically for the motors and motor driver.
* **Power Bank:** Provides isolated, stable power delivery directly to the Raspberry Pi.

**4. Fog Compute**
* **Base Station Laptop:** Running Ubuntu 24.04 and ROS2 Jazz, acts as the fog node to offload heavy computations. It runs the zone predictor KNN model, YOLO inference, and Foxglove visualization.

---

## <a id="features"></a>🚀 Key Features
* **Teleoperation:** Manual keyboard control mode that allows for remote operation.
* **Fog-Edge Distributed Computing:** Optimizes performance by offloading heavy computations like YOLO inference to a Fog Node (Laptop) while maintaining real-time hardware control on the Edge Node (Raspberry Pi)
* **Multi-Modal State Estimation (LO + RSSI):** Uses LiDAR Odometry (LO) as primary odometry source with the Wi-Fi signal strength (RSSI) based indoor localization as fallback mechanism.
<img width="1920" height="1080" alt="Untitled design(2)" src="https://github.com/user-attachments/assets/0a0ee26d-e00c-4525-9333-413388ff6489" />

  Note: The blue filtered prediction doesnt predict correctly because of improper tuning.
  
* **Human Following:** Implements real-time visual servoing using YOLOv8n and a proportional controller to track and follow detected persons based on bounding box area .
  
https://github.com/user-attachments/assets/4ba3d4bb-5c2a-47c7-9eb5-8d6db647731f


* **2D SLAM & Mapping:** Utilizes the SLAM Toolbox for asynchronous mapping localization.
 <p align="center">
  <video src="https://github.com/user-attachments/assets/06881c47-0c20-4130-a2e5-f8573be80656" width="600" controls></video>
</p>


**Autonomous Navigation:** Uses Nav2 stack to perform autonomous navigation by processing costmaps using give goal pose in foxglove/rviz.
 
  <img width="859" height="726" alt="Screenshot from 2026-04-18 20-08-34" src="https://github.com/user-attachments/assets/683366c5-1ceb-4549-a270-69fc57631e9e" />

## <a id="architecture"></a>🏗️ System Architecture

The project utilizes a distributed **Fog-Edge** computing model designed for autonomous monitoring. Real-time hardware interfacing and raw sensor acquisition occur at the **Edge** (Raspberry Pi 5), while high-level perception and computationally expensive tasks are offloaded to the **Fog** (Laptop Base Station) via a high-performance **Eclipse Cyclone DDS** bridge.

### 1. Edge Node (Raspberry Pi 5 & Esp32)
The Edge layer manages raw data and low-level actuation:
* **Sensing:** Interfaces with the **2D-LiDAR** (via USB-Serial) and the **OV5647-Cam-Module** (via CSI).
* **RSSI Acquisition:** A custom `rssi_logger_node` polls the internal Wi-Fi module for signal strength metrics used in localization.
* **Broadcast_data:** Broadcasts image topics to fog node via dds peer to peer communication with configured QOS profiles for better latency.
* **LiDAR Odometry:** Implements the `laser_scan_matcher` locally to provide ICP-based LiDAR odometry.
* **SLAM :** Implements **SLAM Toolbox** for asynchronous 2D mapping using pose-graph optimization and scan matching to minimize odometry drift.
* **Navigation:** Used **Nav2** stack for autonomous navigation using goal posed given in foxglove/rviz.
* **Hardware Bridge:** Receives/generates velocity commands (`/cmd_vel`) and relays them to an **ESP32** via USB.
* **Motion Control:** The ESP32 generates real-time **PWM signals** for the motor driver to control the differential-drive base using DC motors.
* 
### 2. Communication Layer (DDS)
DDS peep to peer communication for seamless topic discovery across edge and fog:
* **Middleware:** Implemented using **Cyclone DDS** for decentralized, peer-to-peer communication.Uses a custom defined xml file for network discovery and unicast transmission between edge and fog node both of which are on same `ros_domain_id`  

### 3. Fog Node (Laptop Base Station)
The Fog layer handles heavy AI and mapping workloads:
* **Human Detection:** Runs **YOLOv8n** inference on compressed image streams to identify persons (Class 0) in real-time.
* **Human Follower (Visual Servoing):** Implements a **Proportional Controller** that calculates error based on bounding box area (for distance) and bounding box center (for yaw) to follow targets.
* **Zone Prediction:** A `Zone Predictor Node` integrates **K-Nearest Neighbors (KNN)** model—trained on raw data with to classify the robot's location based on RSSI fingerprints.
* **Teleoperation:** Supports remote manual control via a dedicated `Teleop Node`.
* **Live Telemetry:** Utilizes **Foxglove Studio** and **RViz** for real-time visualization of the occupancy grid, robot pose, and detection bounding boxes.
<img width="1920" height="1067" alt="image" src="https://github.com/user-attachments/assets/58101354-e311-4f77-8c4e-ed768f89eeb2" />

---

## <a id="structure"></a>📂Repository Structure
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

## <a id="setup"></a>⚙️ Installation & Setup

Since this project utilizes a distributed architecture, you must build the specific workspaces on their respective machines.

### 1. Edge Node Setup (Raspberry Pi 5)
Run these commands on the Pi.

```bash
# Clone the repository
git clone https://github.com/Anany444/RSSI_Localization_based_Indoor_Monitoring_Robot.git
cd ~/RSSI_Localization_based_Indoor_Monitoring_Robot/edge_packages

# Source ROS 2 (Jazzy)
source /opt/ros/jazzy/setup.bash

# Install ROS dependencies
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# Build the Edge workspace
colcon build --symlink-install
source install/setup.bash
```

### 2. Fog Node Setup (Laptop)
Run these commands on the laptop.
```bash
# Clone the repository
git clone https://github.com/Anany444/RSSI_Localization_based_Indoor_Monitoring_Robot.git
cd ~/RSSI_Localization_based_Indoor_Monitoring_Robot/fog_packages

#Create a Python virtual environment named 'fog_venv'
python3 -m venv fog_venv

# Activate the virtual environment
source fog_venv/bin/activate

# Install Python ML dependencies inside the venv
pip install ultralytics scikit-learn torch opencv-python matplotlib pyserial joblib

# Source ROS 2 (Jazzy)
source /opt/ros/jazzy/setup.bash

# Install Python ML dependencies inside a venv sourced envirnment
pip3 install ultralytics scikit-learn torch 

# Install ROS dependencies
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# Build the Fog workspace
colcon build --symlink-install
source install/setup.bash
```
### 3. DDS Configuration (Raspberry Pi and Laptop)
Run these commands on both Pi and Laptop to configure your DDS for peer to peer communication
```bash
#Install CycloneDDS rmw implementation
sudo apt install ros-jazzy-rmw-cyclonedds-cpp

# Because this is a distributed system, you must export your custom Cyclone DDS configuration on **both** the Raspberry Pi and the Laptop in *every* new terminal before running ROS 2 command or better add these to the end of bashrc of both
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///path/to/your/cyclonedds.xml

```
---
## <a id="usage"></a>🚀 Using different features
### 1.Teleoperation:
```bash
# On the Raspberry Pi
cd ~/RSSI_Localization_based_Indoor_Monitoring_Robot/edge_packages
source install/setup.bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
### 2.Human_follower
```bash
# On the Raspberry Pi
cd ~/RSSI_Localization_based_Indoor_Monitoring_Robot/edge_packages
source install/setup.bash
# launch camera 
ros2 launch rssi cam.launch.py
# on another sourced terminal
ros2 run rssi broadcaster
# on another sourced terminal
ros2 run rssi velocity_relay

# On the laptop
cd ~/RSSI_Localization_based_Indoor_Monitoring_Robot/fog_packages
source install/setup.bash
#launch human follower
ros2 launch rssi human_follower.launch.py
# Visualize in foxglove studio by adding the /debug/.. topics
```
### 3.RSSI localization
```bash
# On the Raspberry Pi
cd ~/RSSI_Localization_based_Indoor_Monitoring_Robot/edge_packages
source install/setup.bash
# Run teleop to move around 
ros2 run teleop_twist_keyboard teleop_twist_keyboard
# On another sourced terminal run velocity relay node
ros2 run rssi velocity_relay
# On another sourced terminal run RSSI logger node
ros2 run rssi rssi_logger

# On the laptop
cd ~/RSSI_Localization_based_Indoor_Monitoring_Robot/fog_packages
source install/setup.bash
# launch RSSI localization
ros2 launch rssi rssi_localization.launch.py
```

### 4. SLAM and Navigation
```bash
# On the Raspberry Pi
cd ~/RSSI_Localization_based_Indoor_Monitoring_Robot/edge_packages
source install/setup.bash
# Run teleop to move around if manual SLAM
ros2 run teleop_twist_keyboard teleop_twist_keyboard
# On another sourced terminal run velocity relay node
ros2 run rssi velocity_relay
# On another sourced terminal launch SLAM
ros2 launch rssi slam.launch.py
# On another sourced terminal launch nav2
ros2 launch rssi nav2.launch.py
# Optionally, on another sourced terminals launch camera and broadcaster for visual feed
ros2 launch rssi cam.launch.py
ros2 run rssi broadcaster
# Visualize in foxglove studio by adding the costmap, plan topics
```
---
