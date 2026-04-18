import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial

class CmdVelToSerial(Node):
    def __init__(self):
        super().__init__('cmd_vel_to_serial')

        # declared params
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baud', 115200)
        self.declare_parameter('wheel_separation', 0.135) 
        self.declare_parameter('min_pwm', 200) # required threshold to overcome heavy robot weight
        self.declare_parameter('max_pwm', 255)
        # If one motor is naturally faster, use trim 
        self.declare_parameter('left_trim', 1.0)
        self.declare_parameter('right_trim', 1.0) 

        self.declare_parameter('timer_interval', 0.02)
        self.declare_parameter('timeout_duration', 0.1)

        port = self.get_parameter('port').value
        baud = self.get_parameter('baud').value
        timer_interval = self.get_parameter('timer_interval').value

        self.timeout_duration = self.get_parameter('timeout_duration').value
        self.time_sent = None
        self.sent_vel_cmd = False
        
        #connecing to esp32
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            self.get_logger().info(f"Connected to ESP32 on {port}")
        except Exception as e:
            self.get_logger().error(f"Failed to connect: {e}")

        # subscribe to cmd_vel
        self.sub_cmd_vel = self.create_subscription(
            Twist, 'cmd_vel', self.listener_callback, 10)

        # timer to send pwm cmds to esp if cmd_vel msg comes
        self.create_timer(timer_interval, self.timer_callback)

    def timer_callback(self):
    # Check if we have sent a command recently and if the timeout has passed
        if self.sent_vel_cmd and self.time_sent is not None:
            duration = (self.get_clock().now() - self.time_sent).nanoseconds / 1e9

            if duration > self.timeout_duration:
                self.ser.write(b"0,0\n") # serial msg format compatible for esp32 code
                self.sent_vel_cmd = False
                self.get_logger().info("Timeout: Sending stop command (0,0)")

    def map_to_pwm(self, val):
        min_p = self.get_parameter('min_pwm').value
        max_p = self.get_parameter('max_pwm').value
        if abs(val) < 0.01:
            return 0

        # Scaling formula: maps speed 0.0-1.0 to min_pwm-max_pwm
        pwm = int(min_p + (abs(val) * (max_p - min_p)))
        # Ensure we don't exceed max_pwm
        pwm = min(pwm, max_p)
        return pwm if val > 0 else -pwm

    def listener_callback(self, msg):
        linear = msg.linear.x
        angular = msg.angular.z

        sep = self.get_parameter('wheel_separation').value
        #simple diff drive robot kinematics
        left_speed = linear - (angular * sep / 2.0) 
        right_speed = linear + (angular * sep / 2.0)

        # apply mapping
        l_pwm = self.map_to_pwm(left_speed)
        r_pwm = self.map_to_pwm(right_speed)

        # Apply trims
        l_pwm = int(l_pwm * self.get_parameter('left_trim').value)
        r_pwm = int(r_pwm * self.get_parameter('right_trim').value)

        # Final Formatting & Send
        packet = f"{l_pwm},{r_pwm}\n"
        try:
            self.ser.write(packet.encode('utf-8'))
            self.time_sent = self.get_clock().now()
            self.sent_vel_cmd = True
            self.get_logger().info(f"Sent: {packet.strip()}")
        except Exception as e:
            self.get_logger().error(f"Serial write failed: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = CmdVelToSerial()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()










