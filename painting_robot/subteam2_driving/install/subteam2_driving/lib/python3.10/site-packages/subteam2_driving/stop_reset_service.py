#!/usr/bin/env python3

"""
stop_reset_service.py

This node provides simple ROS2 services for:
- stopping robot motion
- resetting robot motion state

Why this file exists:
- Gives other nodes a clean way to request stop/reset
- Keeps service logic separate from drive_controller.py
- Makes the package easier for the team to understand

Right now:
- the services only log messages
- later, they can be connected to real robot control logic
"""

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class StopResetService(Node):
    """
    A ROS2 node that provides stop and reset services.
    """

    def __init__(self):
        super().__init__('stop_reset_service')

        # Create a service called /stop_robot
        self.stop_service = self.create_service(
            Trigger,
            '/stop_robot',
            self.handle_stop_request
        )

        # Create a service called /reset_robot
        self.reset_service = self.create_service(
            Trigger,
            '/reset_robot',
            self.handle_reset_request
        )

        self.get_logger().info('Stop/Reset Service node has started.')
        self.get_logger().info('Services available:')
        self.get_logger().info('  /stop_robot')
        self.get_logger().info('  /reset_robot')

    def handle_stop_request(self, request, response):
        """
        Runs when someone calls /stop_robot.

        Right now:
        - logs that a stop was requested
        - sends back a success response
        """
        self.get_logger().info('STOP service was called.')

        response.success = True
        response.message = 'Robot stop request received.'
        return response

    def handle_reset_request(self, request, response):
        """
        Runs when someone calls /reset_robot.

        Right now:
        - logs that a reset was requested
        - sends back a success response
        """
        self.get_logger().info('RESET service was called.')

        response.success = True
        response.message = 'Robot reset request received.'
        return response


def main(args=None):
    """
    Standard ROS2 Python node startup.
    """
    rclpy.init(args=args)

    node = StopResetService()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Stop/Reset Service node stopped by user.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
