#!/usr/bin/env python3

"""
drive_controller.py

Main driving node for Subteam 2.

What this node does right now:
- Starts a ROS2 node called drive_controller
- Subscribes to the /cmd_vel topic
- Receives Twist messages
- Uses helper functions to keep commands safe and readable
- Prints whether the robot should move or stop

What this node will do later:
- Convert commands into real Raspbot motor commands
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from subteam2_driving.motion_helpers import clamp_value, is_stop_command, format_motion_command


class DriveController(Node):
    """
    Main ROS2 node for robot driving.
    """

    def __init__(self):
        super().__init__('drive_controller')

        # These are simple safety limits for now.
        # You can adjust them later after testing the robot.
        self.max_linear_speed = 1.0
        # Declare parameters (default values)
        self.declare_parameter('max_linear_speed', 1.0)
        self.declare_parameter('max_angular_speed', 1.0)

        # Load parameter values
        self.max_linear_speed = self.get_parameter(
            'max_linear_speed').value

        self.max_angular_speed = self.get_parameter(
            'max_angular_speed').value
            
        # Print loaded values
        self.get_logger().info(f'max_linear_speed: {self.max_linear_speed}')
        self.get_logger().info(f'max_angular_speed: {self.max_angular_speed}')
        
        self.max_angular_speed = 1.0

        self.cmd_vel_subscriber = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.get_logger().info('Drive Controller node has started.')
        self.get_logger().info('Listening for velocity commands on /cmd_vel')

    def cmd_vel_callback(self, msg):
        """
        Runs every time a Twist message is received.
        """

        # Get the raw values from the incoming message
        raw_linear = msg.linear.x
        raw_angular = msg.angular.z

        # Clamp the values so they stay inside safe limits
        safe_linear = clamp_value(raw_linear, -self.max_linear_speed, self.max_linear_speed)
        safe_angular = clamp_value(raw_angular, -self.max_angular_speed, self.max_angular_speed)

        # Print the cleaned-up command
        self.get_logger().info(
            f'Received cmd_vel -> {format_motion_command(safe_linear, safe_angular)}'
        )

        # Decide whether this means "stop" or "move"
        if is_stop_command(safe_linear, safe_angular):
            self.get_logger().info('Robot should STOP.')
        else:
            self.get_logger().info('Robot should MOVE.')

        # Later, the real robot control code will go here.


def main(args=None):
    rclpy.init(args=args)

    drive_controller = DriveController()

    try:
        rclpy.spin(drive_controller)
    except KeyboardInterrupt:
        drive_controller.get_logger().info('Drive Controller node stopped by user.')
    finally:
        drive_controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
