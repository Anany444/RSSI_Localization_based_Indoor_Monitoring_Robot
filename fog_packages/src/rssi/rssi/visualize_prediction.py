import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class ZoneVisualizerLite(Node):
    def __init__(self):
        super().__init__('zone_visualizer_lite')
        
        # Subscriptions
        self.create_subscription(Odometry, '/laser_odom', self.odom_callback, 10) 
        self.create_subscription(String, '/predict/raw', self.raw_zone_callback, 10)
        self.create_subscription(String, '/predict/filtered', self.filtered_zone_callback, 10)

        # Plot Setup (Centered at 0,0)
        self.width_m, self.height_m = 6.5, 8.0
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(6.5, 8))
        
        # State Variables
        self.bot_pos = [0.0, 0.0]
        self.raw_zone = "None"
        self.filtered_zone = "None"
        
        # zone mapping
        self.zones = {
            "zone0": [0.0, -4.0, 3.25, 4.0],    # 0 = Bottom Right
            "zone1": [0.0, 0.0, 3.25, 4.0],     # 1 = Top Right
            "zone2": [-3.25, 0.0, 3.25, 4.0],   # 2 = Top Left
            "zone3": [-3.25, -4.0, 3.25, 4.0]   # 3 = Bottom Left
        }

        self.timer = self.create_timer(0.1, self.update_plot)

    def odom_callback(self, msg):
        ros_x = msg.pose.pose.position.x
        ros_y = msg.pose.pose.position.y
        self.bot_pos = [-ros_y, ros_x] # ros default conventions to normal convention transform

    def raw_zone_callback(self, msg):
        self.raw_zone = msg.data.strip()

    def filtered_zone_callback(self, msg):
        self.filtered_zone = msg.data.strip()

    def update_plot(self):
        self.ax.clear()
        
        # Keep standard limits
        self.ax.set_xlim(-self.width_m/2, self.width_m/2)
        self.ax.set_ylim(-self.height_m/2, self.height_m/2)

        # 1. Draw Static Grid, Predictions, and Labels
        for name, rect in self.zones.items():
            # Draw empty borders for all zones
            border = patches.Rectangle((rect[0], rect[1]), rect[2], rect[3], 
                                       fill=False, edgecolor='gray', linestyle='--')
            self.ax.add_patch(border)

            # Draw Green patch for Raw Prediction
            if name == self.raw_zone:
                raw_patch = patches.Rectangle((rect[0], rect[1]), rect[2], rect[3], 
                                              color='green', alpha=0.4, label='Raw (Green)')
                self.ax.add_patch(raw_patch)

            # Draw Blue patch for Filtered Prediction
            if name == self.filtered_zone:
                filt_patch = patches.Rectangle((rect[0], rect[1]), rect[2], rect[3], 
                                               color='blue', alpha=0.4, label='Filtered (Blue)')
                self.ax.add_patch(filt_patch)

            # Add the text label in the center of each zone
            center_x = rect[0] + (rect[2] / 2.0)
            center_y = rect[1] + (rect[3] / 2.0)
            self.ax.text(center_x, center_y, name, 
                         fontsize=16, color='black', alpha=0.3, 
                         ha='center', va='center', fontweight='bold')

        # 2. Draw Crosshairs for Origin
        self.ax.axhline(0, color='black', linewidth=1)
        self.ax.axvline(0, color='black', linewidth=1)

        # 3. Draw Robot Position
        self.ax.plot(self.bot_pos[0], self.bot_pos[1], marker='o', color='black', 
                     markersize=12, markeredgecolor='white', markeredgewidth=2, label="Robot")
        
        # UI Updates
        plt.title(f"Raw: {self.raw_zone} | Filtered: {self.filtered_zone}")
        
        # Smart Legend 
        handles, labels = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        if by_label:
            self.ax.legend(by_label.values(), by_label.keys(), loc='upper right')

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

def main(args=None):
    rclpy.init(args=args)
    node = ZoneVisualizerLite()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        plt.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()