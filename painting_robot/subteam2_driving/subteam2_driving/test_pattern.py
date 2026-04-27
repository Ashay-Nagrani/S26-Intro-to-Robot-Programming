#!/usr/bin/env python3
 
"""
test_pattern.py
 
This node sends a serpentine grid movement pattern to /cmd_vel_raw (drive_controller forwards this to /cmd_vel)
for an omnidirectional Raspbot V2.
 
What this file does:
- Creates a square grid path (3x3, 4x4, 5x5, etc.)
- Moves one square at a time
- Stops briefly at each square
- Uses the robot's omnidirectional movement
- Computes movement time from square size and speed
 
Important assumptions:
- The Raspbot V2 accepts holonomic Twist motion commands
- linear.x controls forward/back (grid Y axis, up/down columns)
- linear.y controls sideways (grid X axis, left/right between columns)
- angular.z controls rotation (unused here)
 
Team note:
You may need to flip signs on linear.x or linear.y depending on
how your robot is physically oriented relative to the painting grid.

==================================================================
BUGS FIXED (vs original):
1. generate_grid_path: was row-major (snaking across rows).
   Fixed to column-major (snaking up/down columns), matching the
   diagram which shows vertical serpentine movement.

2. publish_move_to_next_cell: the dx==-1 case was sending
   +cell_speed instead of -cell_speed (copy-paste bug).

3. driving_params.yaml timer_period was 0.5s — far too coarse for
   small cells (causes massive overshoot). Recommended: 0.05s.
   Update your YAML: timer_period: 0.05
==================================================================
"""
 
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
 
 
class TestPatternPublisher(Node):
    """
    Publishes a grid-based serpentine motion pattern.
    Snakes column by column (up one column, step right, down next column, etc.)
    matching the diagram with Y=up, X=right axes.
    """
 
    def __init__(self):
        super().__init__('test_pattern_publisher')
 
        # Publisher to the robot velocity topic
        self.publisher = self.create_publisher(Twist, '/cmd_vel_raw', 10)
 
        # ==========================================================
        # USER SETTINGS
        # ==========================================================
 
        # Declare parameters (default fallback values)
        self.declare_parameter('grid_size', 3)
        self.declare_parameter('canvas_size', 0.9)
        self.declare_parameter('cell_speed', 0.15)
        self.declare_parameter('stop_duration', 1.0)
        self.declare_parameter('timer_period', 0.05)  # FIX #3: was 0.1 default, YAML had 0.5 (way too coarse)

        # Load parameter values from YAML
        self.grid_size = self.get_parameter('grid_size').value
        self.canvas_size = self.get_parameter('canvas_size').value
        self.cell_speed = self.get_parameter('cell_speed').value
        self.stop_duration = self.get_parameter('stop_duration').value
        self.timer_period = self.get_parameter('timer_period').value
 
        # ==========================================================
        # COMPUTED VALUES
        # ==========================================================
 
        # Size of one square cell
        self.cell_size = self.canvas_size / self.grid_size
 
        # Time needed to move one cell
        self.move_duration = self.cell_size / self.cell_speed
 
        # Number of timer ticks needed for one movement
        self.move_ticks = max(1, int(round(self.move_duration / self.timer_period)))
 
        # Number of timer ticks needed for one stop
        self.stop_ticks = max(1, int(round(self.stop_duration / self.timer_period)))
 
        # Generate the serpentine path (column-major to match diagram)
        self.path = self.generate_grid_path(self.grid_size)
 
        # Current position in the path list
        self.current_index = 0
 
        # Current phase: "move" or "stop"
        self.phase = 'move'
        self.phase_ticks = 0
 
        # Create repeating timer
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
 
        # Startup logs
        self.get_logger().info('Test Pattern Publisher started.')
        self.get_logger().info(f'Grid size: {self.grid_size}x{self.grid_size}')
        self.get_logger().info(f'Canvas size: {self.canvas_size:.2f} m')
        self.get_logger().info(f'Cell size: {self.cell_size:.3f} m')
        self.get_logger().info(f'Cell speed: {self.cell_speed:.3f} m/s')
        self.get_logger().info(f'Move duration per cell: {self.move_duration:.2f} s')
        self.get_logger().info(f'Move ticks per cell: {self.move_ticks}')
        self.get_logger().info(f'Stop duration: {self.stop_duration:.2f} s')
        self.get_logger().info(f'Timer period: {self.timer_period:.3f} s')
        self.get_logger().info(f'Generated path: {self.path}')
 
    def generate_grid_path(self, n):
        """
        FIX #1: Generate a column-major serpentine path through an n x n grid.

        Matches the diagram: snake UP one column, step RIGHT, snake DOWN, step RIGHT, etc.

        Coordinates: (col, row) where col=X (right), row=Y (up)

        Example for n=3:
          col 0: (0,0)->(0,1)->(0,2)   [going up]
          step:  (0,2)->(1,2)           [step right]
          col 1: (1,2)->(1,1)->(1,0)   [going down]
          step:  (1,0)->(2,0)           [step right]
          col 2: (2,0)->(2,1)->(2,2)   [going up]

        Full path: [(0,0),(0,1),(0,2),(1,2),(1,1),(1,0),(2,0),(2,1),(2,2)]
        """
        path = []

        for col in range(n):
            if col % 2 == 0:
                # Even columns: go UP (increasing row/Y)
                for row in range(n):
                    path.append((col, row))
            else:
                # Odd columns: go DOWN (decreasing row/Y)
                for row in range(n - 1, -1, -1):
                    path.append((col, row))

        return path
 
    def publish_stop(self):
        """
        Send a stop command to the robot.
        """
        msg = Twist()
        msg.linear.x = 0.0
        msg.linear.y = 0.0
        msg.angular.z = 0.0
        self.publisher.publish(msg)
 
    def publish_move_to_next_cell(self, current_point, next_point):
        """
        Publish a motion command to move exactly one grid cell directionally.

        Grid coordinate system: (col, row) = (X, Y)
          - dcol (+1) = step RIGHT  -> robot linear.y positive
          - dcol (-1) = step LEFT   -> robot linear.y negative  [FIX #2]
          - drow (+1) = step UP     -> robot linear.x positive
          - drow (-1) = step DOWN   -> robot linear.x negative

        If your robot moves in the wrong direction on the floor, flip the
        sign of linear.x or linear.y here.
        """
        dcol = next_point[0] - current_point[0]  # change in X (column)
        drow = next_point[1] - current_point[1]  # change in Y (row)
 
        msg = Twist()
        msg.angular.z = 0.0
        msg.linear.x = 0.0
        msg.linear.y = 0.0
 
        if dcol == 0 and drow == 1:
            # Moving UP a column (increasing Y)
            msg.linear.x = self.cell_speed
            self.get_logger().info(f'Moving UP (+Y): {current_point} -> {next_point}')
 
        elif dcol == 0 and drow == -1:
            # Moving DOWN a column (decreasing Y)
            msg.linear.x = -self.cell_speed
            self.get_logger().info(f'Moving DOWN (-Y): {current_point} -> {next_point}')
 
        elif dcol == 1 and drow == 0:
            # Stepping RIGHT to next column (+X)
            msg.linear.y = self.cell_speed
            self.get_logger().info(f'Stepping RIGHT (+X): {current_point} -> {next_point}')
 
        elif dcol == -1 and drow == 0:
            # FIX #2: was `msg.linear.y = self.cell_speed` (positive! wrong!)
            # Stepping LEFT to previous column (-X)
            msg.linear.y = -self.cell_speed
            self.get_logger().info(f'Stepping LEFT (-X): {current_point} -> {next_point}')
 
        else:
            self.get_logger().warn(
                f'Unexpected move from {current_point} to {next_point}. Sending STOP.'
            )
 
        self.publisher.publish(msg)
 
    def timer_callback(self):
        """
        Main timer loop.
 
        Alternates between:
        - moving one cell (holds velocity for move_ticks)
        - stopping briefly (holds zero for stop_ticks)
        """
 
        # If we are at the last point, finish
        if self.current_index >= len(self.path) - 1:
            self.publish_stop()
            self.get_logger().info('Test pattern finished.')
            self.timer.cancel()
            self.destroy_node()
            rclpy.shutdown()
            return
 
        current_point = self.path[self.current_index]
        next_point = self.path[self.current_index + 1]
 
        # MOVE PHASE: publish velocity command only on tick 0, hold for move_ticks
        if self.phase == 'move':
            if self.phase_ticks == 0:
                self.publish_move_to_next_cell(current_point, next_point)
 
            self.phase_ticks += 1
 
            if self.phase_ticks >= self.move_ticks:
                self.phase = 'stop'
                self.phase_ticks = 0
 
        # STOP PHASE: publish stop only on tick 0, hold for stop_ticks
        elif self.phase == 'stop':
            if self.phase_ticks == 0:
                self.publish_stop()
                self.get_logger().info(f'Stopping at {next_point}')
 
            self.phase_ticks += 1
 
            if self.phase_ticks >= self.stop_ticks:
                self.current_index += 1
                self.phase = 'move'
                self.phase_ticks = 0
 
 
def main(args=None):
    rclpy.init(args=args)
 
    node = TestPatternPublisher()
    rclpy.spin(node)
 
 
if __name__ == '__main__':
    main()
