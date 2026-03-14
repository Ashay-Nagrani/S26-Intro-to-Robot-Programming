from action_msgs.msg import GoalStatus
from turtle_interfaces.action import MakeSquare

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.msg import ParameterDescriptor

class TurtleSquareClient(Node):
    def __init__(self):
        super().__init__('square_client')
        self._action_client = ActionClient(self,MakeSquare,'make_square')
        descriptor = ParameterDescriptor(description='Size of the square')
        self.declare_parameter('square_size', 50.0, descriptor)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            return

        self.get_logger().info('Goal accepted')

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)


    def feedback_callback(self,feedback):
        self.get_logger().info('Received feedback: {0}'.format(feedback.feedback.current_pose))


    def get_result_callback(self,future):
        result = future.result().result
        status = future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('Goal succeeded! Result: {0}'.format(result.final_pose))
        else:
            self.get_logger().info('Goal failed with status: {0}'.format(status))
        rclpy.shutdown()


    def send_goal(self):
        self.get_logger().info('Waiting for action server...')
        self._action_client.wait_for_server()

        goal_msg = MakeSquare.Goal()
        goal_msg.square_size = self.get_parameter('square_size').get_parameter_value().double_value

        self.get_logger().info('Sending goal request...')

        self._send_goal_future = self._action_client.send_goal_async(goal_msg, feedback_callback=self.feedback_callback)

        self._send_goal_future.add_done_callback(self.goal_response_callback)


def main(args=None):
    rclpy.init(args=args)
    action_client = TurtleSquareClient()
    action_client.send_goal()
    rclpy.spin(action_client)

if __name__ == '__main__':
    main()

