#!/usr/bin/env python3

"""
drive_controller.py

Main driving node for Subteam 2.

What this node does:
- Starts a ROS2 node called drive_controller
- Subscribes to /cmd_vel (receives Twist messages from test_pattern.py)
- Clamps incoming velocity values to safe limits
- Forwards the safe commands to /raspbot/cmd_vel (the actual Raspbot hardware topic)
- Logs all motion and stop events
- Provides stop/reset via services (handled by stop_reset_service.py)
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from subteam2_driving.motion_helpers import clamp_value, is_stop_command, format_motion_command


class DriveController(Node):
    """
    Main ROS2 node for robot driving.
    Bridges /cmd_vel (planning side) -> /raspbot/cmd_vel (hardware side).
    """

    def __init__(self):
        super().__init__('drive_controller')

        # ----------------------------------------------------------
        # Parameters
        # ----------------------------------------------------------
        self.declare_parameter('max_linear_speed', 1.0)
        self.declare_parameter('max_angular_speed', 1.0)

        self.max_linear_speed = self.get_parameter('max_linear_speed').value
        self.max_angular_speed = self.get_parameter('max_angular_speed').value

        self.get_logger().info(f'max_linear_speed: {self.max_linear_speed}')
        self.get_logger().info(f'max_angular_speed: {self.max_angular_speed}')

        # ----------------------------------------------------------
        # Publisher -> sends commands TO the real Raspbot hardware
        # ----------------------------------------------------------
        # NOTE: /raspbot/cmd_vel is the topic the Raspbot V2 driver listens on.
        # If your robot doesn't move, run `ros2 topic list` while the robot
        # driver is running and find the correct motor command topic.
        # Then replace '/raspbot/cmd_vel' below with that topic name.
        self.motor_publisher = self.create_publisher(
            Twist,
            '/raspbot/cmd_vel',
            10
        )

        # ----------------------------------------------------------
        # Subscriber -> receives commands FROM test_pattern.py (or any planner)
        # ----------------------------------------------------------
        self.cmd_vel_subscriber = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.get_logger().info('Drive Controller node has started.')
        self.get_logger().info('Subscribing to: /cmd_vel')
        self.get_logger().info('Publishing to:  /raspbot/cmd_vel')

    def cmd_vel_callback(self, msg):
        """
        Runs every time a Twist message is received on /cmd_vel.

        Steps:
        1. Read raw linear/angular values from the incoming message
        2. Clamp them to safe limits
        3. Forward the safe command to the Raspbot hardware topic
        4. Log what happened
        """

        # Step 1: Read raw values
        raw_linear_x = msg.linear.x
        raw_linear_y = msg.linear.y   # Raspbot V2 is holonomic, so we also handle Y
        raw_angular_z = msg.angular.z

        # Step 2: Clamp to safe limits
        safe_linear_x = clamp_value(raw_linear_x, -self.max_linear_speed, self.max_linear_speed)
        safe_linear_y = clamp_value(raw_linear_y, -self.max_linear_speed, self.max_linear_speed)
        safe_angular_z = clamp_value(raw_angular_z, -self.max_angular_speed, self.max_angular_speed)

        # Step 3: Build and publish the outgoing Twist message to the robot
        out_msg = Twist()
        out_msg.linear.x = safe_linear_x
        out_msg.linear.y = safe_linear_y
        out_msg.angular.z = safe_angular_z
        self.motor_publisher.publish(out_msg)

        # Step 4: Log what we sent
        self.get_logger().info(
            f'Forwarding cmd_vel -> '
            f'linear.x: {safe_linear_x:.2f}, '
            f'linear.y: {safe_linear_y:.2f}, '
            f'angular.z: {safe_angular_z:.2f}'
        )

        if is_stop_command(safe_linear_x, safe_angular_z) and abs(safe_linear_y) < 1e-3:
            self.get_logger().info('Robot STOPPING.')
        else:
            self.get_logger().info('Robot MOVING.')

    def stop_robot(self):
        """
        Publishes a zero-velocity command to immediately stop the robot.
        Called on shutdown or by external services.
        """
        stop_msg = Twist()
        stop_msg.linear.x = 0.0
        stop_msg.linear.y = 0.0
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
        drive_controller.stop_robot()   # Make sure robot halts on Ctrl+C
    finally:
        drive_controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

