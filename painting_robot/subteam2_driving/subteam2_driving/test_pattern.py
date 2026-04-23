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
- linear.x controls one direction of translation
- linear.y controls sideways translation
- angular.z controls rotation (unused here for now)
 
Team note:
You may need to flip signs on linear.x or linear.y depending on
how your robot is physically oriented relative to the painting grid.
"""
 
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
 
 
class TestPatternPublisher(Node):
    """
    Publishes a grid-based serpentine motion pattern.
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
        self.declare_parameter('timer_period', 0.1)
 
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
 
        # Generate the serpentine path
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
        self.get_logger().info(f'Stop duration: {self.stop_duration:.2f} s')
        self.get_logger().info(f'Generated path: {self.path}')
 
    def generate_grid_path(self, n):
        """
        Generate a serpentine path through an n x n grid.
 
        Example for n=3:
        [(0,0), (0,1), (0,2), (1,2), (1,1), (1,0), (2,0), (2,1), (2,2)]
        """
        path = []
 
        for x in range(n):
            if x % 2 == 0:
                for y in range(n):
                    path.append((x, y))
            else:
                for y in range(n - 1, -1, -1):
                    path.append((x, y))
 
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
 
        Grid interpretation:
        - dy changes move along robot linear.x
        - dx changes move along robot linear.y
 
        IMPORTANT:
        Depending on your robot orientation on the floor, you may need to
        swap signs or axes after testing real movement.
        """
        dx = next_point[0] - current_point[0]
        dy = next_point[1] - current_point[1]
 
        msg = Twist()
        msg.angular.z = 0.0
 
        # Default to no motion
        msg.linear.x = 0.0
        msg.linear.y = 0.0
 
        if dx == 0 and dy == 1:
            # Move one cell in positive grid y direction
            msg.linear.x = self.cell_speed
            self.get_logger().info(f'Moving +grid_y: {current_point} -> {next_point}')
 
        elif dx == 0 and dy == -1:
            # Move one cell in negative grid y direction
            msg.linear.x = -self.cell_speed
            self.get_logger().info(f'Moving -grid_y: {current_point} -> {next_point}')
 
        elif dx == 1 and dy == 0:
            # Move one cell in positive grid x direction
            msg.linear.y = self.cell_speed
            self.get_logger().info(f'Moving +grid_x: {current_point} -> {next_point}')
 
        elif dx == -1 and dy == 0:
            # Move one cell in negative grid x direction
            msg.linear.y = -self.cell_speed
            self.get_logger().info(f'Moving -grid_x: {current_point} -> {next_point}')
 
        else:
            self.get_logger().warn(
                f'Unexpected move from {current_point} to {next_point}. Sending STOP.'
            )
 
        self.publisher.publish(msg)
 
    def timer_callback(self):
        """
        Main timer loop.
 
        Alternates between:
        - moving one cell
        - stopping briefly
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
 
        # MOVE PHASE
        if self.phase == 'move':
            if self.phase_ticks == 0:
                self.publish_move_to_next_cell(current_point, next_point)
 
            self.phase_ticks += 1
 
            if self.phase_ticks >= self.move_ticks:
                self.phase = 'stop'
                self.phase_ticks = 0
 
        # STOP PHASE
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
