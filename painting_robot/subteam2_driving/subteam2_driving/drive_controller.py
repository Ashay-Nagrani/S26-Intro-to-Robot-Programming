#!/usr/bin/env python3
 
"""
drive_controller.py
 
Main driving node for Subteam 2.
 
What this node does:
- Subscribes to /cmd_vel_raw  (receives raw commands from test_pattern.py)
- Clamps values to safe speed limits
- Publishes safe commands to /cmd_vel  (the Yahboom robot hardware topic)
- Sends a stop command when shut down with Ctrl+C
 
Topic flow:
    test_pattern --> /cmd_vel_raw --> drive_controller --> /cmd_vel --> robot motors
"""
 
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
 
from subteam2_driving.motion_helpers import clamp_value, is_stop_command, format_motion_command
 
 
class DriveController(Node):
 
    def __init__(self):
        super().__init__('drive_controller')
 
        # ----------------------------------------------------------
        # Parameters - loaded from YAML or use defaults
        # ----------------------------------------------------------
        self.declare_parameter('max_linear_speed', 1.0)
        self.declare_parameter('max_angular_speed', 1.0)
 
        self.max_linear_speed = self.get_parameter('max_linear_speed').value
        self.max_angular_speed = self.get_parameter('max_angular_speed').value
 
        self.get_logger().info(f'max_linear_speed: {self.max_linear_speed}')
        self.get_logger().info(f'max_angular_speed: {self.max_angular_speed}')
 
        # ----------------------------------------------------------
        # Publisher -> sends safe commands TO the robot hardware
        # /cmd_vel is the topic the Yahboom driver listens on
        # ----------------------------------------------------------
        self.motor_publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )
 
        # ----------------------------------------------------------
        # Subscriber -> receives raw commands FROM test_pattern.py
        # /cmd_vel_raw is separate from the hardware topic to avoid loops
        # ----------------------------------------------------------
        self.cmd_vel_subscriber = self.create_subscription(
            Twist,
            '/cmd_vel_raw',
            self.cmd_vel_callback,
            10
        )
 
        self.get_logger().info('Drive Controller node has started.')
        self.get_logger().info('Subscribing to: /cmd_vel_raw')
        self.get_logger().info('Publishing to:  /cmd_vel')
 
    def cmd_vel_callback(self, msg):
        """
        Called every time test_pattern.py sends a velocity command.
        Clamps the values to safe limits then forwards to the robot.
        """
 
        # Read raw values from test_pattern
        raw_linear_x = msg.linear.x
        raw_linear_y = msg.linear.y
        raw_angular_z = msg.angular.z
 
        # Clamp to safe limits
        safe_linear_x  = clamp_value(raw_linear_x,  -self.max_linear_speed,  self.max_linear_speed)
        safe_linear_y  = clamp_value(raw_linear_y,  -self.max_linear_speed,  self.max_linear_speed)
        safe_angular_z = clamp_value(raw_angular_z, -self.max_angular_speed, self.max_angular_speed)
 
        # Build the outgoing message
        out_msg = Twist()
        out_msg.linear.x  = safe_linear_x
        out_msg.linear.y  = safe_linear_y
        out_msg.angular.z = safe_angular_z
 
        # Send to robot hardware
        self.motor_publisher.publish(out_msg)
 
        # Log what was sent
        self.get_logger().info(
            f'CMD -> linear.x: {safe_linear_x:.2f}  '
            f'linear.y: {safe_linear_y:.2f}  '
            f'angular.z: {safe_angular_z:.2f}'
        )
 
        if is_stop_command(safe_linear_x, safe_angular_z) and abs(safe_linear_y) < 1e-3:
            self.get_logger().info('Robot STOPPING.')
        else:
            self.get_logger().info('Robot MOVING.')
 
    def stop_robot(self):
        """Send a zero velocity command to stop the robot immediately."""
        stop_msg = Twist()
        stop_msg.linear.x  = 0.0
        stop_msg.linear.y  = 0.0
        stop_msg.angular.z = 0.0
        self.motor_publisher.publish(stop_msg)
        self.get_logger().info('Stop command sent to robot.')
 
 
def main(args=None):
    rclpy.init(args=args)
    drive_controller = DriveController()
 
    try:
        rclpy.spin(drive_controller)
    except KeyboardInterrupt:
        drive_controller.get_logger().info('Drive Controller stopped by user.')
        drive_controller.stop_robot()
    finally:
        drive_controller.destroy_node()
        rclpy.shutdown()
 
 
if __name__ == '__main__':
    main()
