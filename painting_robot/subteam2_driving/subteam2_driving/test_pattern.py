#!/usr/bin/env python3

"""
test_pattern.py

Serpentine grid movement for Raspbot V2 (omnidirectional).

Movement description:
- Robot faces NORTH the entire time (no rotation)
- linear.x positive = move NORTH (forward)
- linear.x negative = move SOUTH (backward)
- linear.y positive = shift RIGHT (sideways)
- linear.y negative = shift LEFT  (unused in standard pattern)

Serpentine sequence per column pair:
  1. Move north one cell, stop  [repeat grid_size times]
  2. Overshoot: move north one more cell (clears grid edge, no stop)
  3. Shift right one cell (no stop)
  4. Move south one cell, stop  [repeat grid_size times]
  5. Overshoot: move south one more cell (no stop)
  6. Shift right one cell (no stop)
  7. Repeat for next column pair

Number of columns = grid_size
Number of right-shifts = grid_size - 1 (no shift after the last column)
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


# Direction constants — (linear.x multiplier, linear.y multiplier)
NORTH       = ( 1,  0)   # linear.x = +speed  (forward)
SOUTH       = (-1,  0)   # linear.x = -speed  (backward)
SHIFT_RIGHT = ( 0,  1)   # linear.y = +speed  (sideways right)


class TestPatternPublisher(Node):

    def __init__(self):
        super().__init__('test_pattern_publisher')

        self.publisher = self.create_publisher(Twist, '/cmd_vel_raw', 10)

        # ----------------------------------------------------------
        # Parameters
        # ----------------------------------------------------------
        self.declare_parameter('grid_size',     5)
        self.declare_parameter('canvas_size',   0.35)
        self.declare_parameter('cell_speed',    0.15)
        self.declare_parameter('stop_duration', 1.0)
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

        # ----------------------------------------------------------
        # Build the explicit move sequence.
        # Each entry: (direction, do_stop_after)
        #   do_stop_after=True  -> pause for stop_duration after the move
        #   do_stop_after=False -> no pause (overshoot / sideways shift)
        # ----------------------------------------------------------
        self.sequence = self.build_sequence(self.grid_size)

        self.get_logger().info('Test Pattern Publisher started.')
        self.get_logger().info(f'Grid:        {self.grid_size}x{self.grid_size}')
        self.get_logger().info(f'Canvas:      {self.canvas_size:.2f} m')
        self.get_logger().info(f'Cell size:   {self.cell_size:.3f} m')
        self.get_logger().info(f'Speed:       {self.cell_speed:.3f} m/s')
        self.get_logger().info(f'Move time:   {self.move_duration:.3f} s  ({self.move_ticks} ticks)')
        self.get_logger().info(f'Stop time:   {self.stop_duration:.2f} s  ({self.stop_ticks} ticks)')
        self.get_logger().info(f'Total steps: {len(self.sequence)}')

        # State machine
        self.step_index  = 0
        self.phase       = 'move'
        self.phase_ticks = 0

        self.timer = self.create_timer(self.timer_period, self.timer_callback)

    # ----------------------------------------------------------
    def build_sequence(self, n):
        """
        Build the full explicit move+stop sequence.

        Example for n=3:
          north+stop, north+stop, north+stop,   <- up column 0
          north(no stop),                        <- overshoot top
          shift_right(no stop),                  <- slide to column 1
          south+stop, south+stop, south+stop,   <- down column 1
          south(no stop),                        <- overshoot bottom
          shift_right(no stop),                  <- slide to column 2
          north+stop, north+stop, north+stop    <- up column 2  (no overshoot/shift at end)
        """
        seq = []

        for col in range(n):
            going_north = (col % 2 == 0)
            direction   = NORTH if going_north else SOUTH

            # Travel the full column, pausing at each cell
            for _ in range(n):
                seq.append((direction, True))

            # Overshoot + shift right — only if there is a next column
            if col < n - 1:
                seq.append((direction,   False))   # overshoot past edge
                seq.append((SHIFT_RIGHT, False))   # slide to next column

        return seq

    # ----------------------------------------------------------
    def publish_velocity(self, direction, speed):
        msg = Twist()
        msg.linear.x  = direction[0] * speed
        msg.linear.y  = direction[1] * speed
        msg.angular.z = 0.0
        self.publisher.publish(msg)

    def publish_stop(self):
        msg = Twist()
        msg.linear.x  = 0.0
        msg.linear.y  = 0.0
        msg.angular.z = 0.0
        self.publisher.publish(msg)

    # ----------------------------------------------------------
    def timer_callback(self):

        # All steps done
        if self.step_index >= len(self.sequence):
            self.publish_stop()
            self.get_logger().info('Serpentine pattern COMPLETE. Shutting down.')
            self.timer.cancel()
            self.destroy_node()
            rclpy.shutdown()
            return

        direction, do_stop_after = self.sequence[self.step_index]

        # ---- MOVE phase ----
        if self.phase == 'move':

            if self.phase_ticks == 0:
                dir_name = {
                    NORTH:       'NORTH',
                    SOUTH:       'SOUTH',
                    SHIFT_RIGHT: 'SHIFT_RIGHT'
                }[direction]
                self.get_logger().info(
                    f'Step {self.step_index + 1}/{len(self.sequence)}: '
                    f'{dir_name}  pause_after={do_stop_after}'
                )
                self.publish_velocity(direction, self.cell_speed)

            self.phase_ticks += 1

            if self.phase_ticks >= self.move_ticks:
                self.phase_ticks = 0
                if do_stop_after:
                    self.phase = 'stop'
                else:
                    # No pause — stop motors briefly and move to next step immediately
                    self.publish_stop()
                    self.step_index += 1
                    self.phase = 'move'

        # ---- STOP / PAUSE phase ----
        elif self.phase == 'stop':

            if self.phase_ticks == 0:
                self.publish_stop()
                self.get_logger().info(f'  Pausing after step {self.step_index + 1}')

            self.phase_ticks += 1

            if self.phase_ticks >= self.stop_ticks:
                self.phase_ticks = 0
                self.step_index += 1
                self.phase = 'move'


# ----------------------------------------------------------
def main(args=None):
    rclpy.init(args=args)
    node = TestPatternPublisher()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
