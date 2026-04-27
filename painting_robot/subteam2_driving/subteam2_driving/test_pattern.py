#!/usr/bin/env python3

"""
test_pattern.py

Moves the Raspbot V2 in a straight line through 5 grid spaces heading NORTH.
Pauses at each cell for a long-exposure camera shot.
Robot must be manually repositioned to the start before each run.

Topic flow:
    test_pattern --> /cmd_vel_raw --> drive_controller --> /cmd_vel --> motors
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class TestPatternPublisher(Node):

    def __init__(self):
        super().__init__('test_pattern_publisher')

        self.publisher = self.create_publisher(Twist, '/cmd_vel_raw', 10)

        # ----------------------------------------------------------
        # Parameters
        # ----------------------------------------------------------
        self.declare_parameter('grid_size',     5)      # number of cells to travel
        self.declare_parameter('canvas_size',   0.35)   # total distance in meters
        self.declare_parameter('cell_speed',    0.05)   # slow for long exposure
        self.declare_parameter('stop_duration', 3.0)    # long pause for camera
        self.declare_parameter('timer_period',  0.05)

        self.grid_size     = self.get_parameter('grid_size').value
        self.canvas_size   = self.get_parameter('canvas_size').value
        self.cell_speed    = self.get_parameter('cell_speed').value
        self.stop_duration = self.get_parameter('stop_duration').value
        self.timer_period  = self.get_parameter('timer_period').value

        # ----------------------------------------------------------
        # Derived timing
        # ----------------------------------------------------------
        self.cell_size     = self.canvas_size / self.grid_size
        self.move_duration = self.cell_size / self.cell_speed
        self.move_ticks    = max(1, int(round(self.move_duration / self.timer_period)))
        self.stop_ticks    = max(1, int(round(self.stop_duration / self.timer_period)))

        self.get_logger().info('Straight Line Test Pattern started.')
        self.get_logger().info(f'Cells:       {self.grid_size}')
        self.get_logger().info(f'Cell size:   {self.cell_size:.3f} m')
        self.get_logger().info(f'Speed:       {self.cell_speed:.3f} m/s')
        self.get_logger().info(f'Move time:   {self.move_duration:.3f} s  ({self.move_ticks} ticks)')
        self.get_logger().info(f'Stop time:   {self.stop_duration:.2f} s  ({self.stop_ticks} ticks)')

        # State machine
        self.current_cell = 0      # how many cells we have completed
        self.phase        = 'move'
        self.phase_ticks  = 0

        self.timer = self.create_timer(self.timer_period, self.timer_callback)

    def publish_north(self):
        msg = Twist()
        msg.linear.x  =  self.cell_speed   # forward = north
        msg.linear.y  =  0.0
        msg.angular.z =  0.0
        self.publisher.publish(msg)

    def publish_stop(self):
        msg = Twist()
        msg.linear.x  = 0.0
        msg.linear.y  = 0.0
        msg.angular.z = 0.0
        self.publisher.publish(msg)

    def timer_callback(self):

        # All cells done
        if self.current_cell >= self.grid_size:
            self.publish_stop()
            self.get_logger().info('Straight line complete. Shutting down.')
            self.timer.cancel()
            self.destroy_node()
            rclpy.shutdown()
            return

        # ---- MOVE phase ----
        if self.phase == 'move':
            if self.phase_ticks == 0:
                self.get_logger().info(
                    f'Moving to cell {self.current_cell + 1}/{self.grid_size}'
                )
                self.publish_north()

            self.phase_ticks += 1

            if self.phase_ticks >= self.move_ticks:
                self.phase_ticks = 0
                self.phase = 'stop'

        # ---- STOP / CAMERA phase ----
        elif self.phase == 'stop':
            if self.phase_ticks == 0:
                self.publish_stop()
                self.get_logger().info(
                    f'  >> Camera exposure at cell {self.current_cell + 1} '
                    f'({self.stop_duration:.1f}s pause)'
                )

            self.phase_ticks += 1

            if self.phase_ticks >= self.stop_ticks:
                self.phase_ticks  = 0
                self.current_cell += 1
                self.phase = 'move'


def main(args=None):
    rclpy.init(args=args)
    node = TestPatternPublisher()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
