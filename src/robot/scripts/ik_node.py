#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState
from moveit_msgs.srv import GetPositionIK
from moveit_msgs.msg import PositionIKRequest, MoveItErrorCodes

class IKNode(Node):
    def __init__(self):
        super().__init__('ik_node')
        
        # 現在の関節角度を保持
        self.current_joint_state = JointState()
        self.current_joint_state.name = [
            'joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6'
        ]
        self.current_joint_state.position = [0.0] * 6

        # IKサービスクライアントの設定
        self.ik_client = self.create_client(GetPositionIK, '/compute_ik')
        while not self.ik_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /compute_ik service...')
            
        # サブスクライバ: フロントエンドからの目標座標
        self.subscription = self.create_subscription(
            PoseStamped,
            '/vla/target_pose',
            self.target_pose_callback,
            10
        )
        
        # パブリッシャ: 計算された関節角度
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
        
        self.get_logger().info('IK Node started. Subscribing to /vla/target_pose')

    def target_pose_callback(self, msg):
        self.get_logger().info(f'Received target pose: {msg.pose.position.x}, {msg.pose.position.y}, {msg.pose.position.z}')
        
        # IKリクエストの作成
        request = GetPositionIK.Request()
        ik_request = PositionIKRequest()
        ik_request.group_name = 'arm'
        ik_request.pose_stamped = msg
        ik_request.avoid_collisions = True
        
        # 現在の状態をシードとして与える
        ik_request.robot_state.joint_state = self.current_joint_state
        
        request.ik_request = ik_request
        
        # サービスの呼び出し
        future = self.ik_client.call_async(request)
        future.add_done_callback(self.ik_response_callback)

    def ik_response_callback(self, future):
        try:
            response = future.result()
            if response.error_code.val == MoveItErrorCodes.SUCCESS:
                self.get_logger().info(f'IK solution found! Joints: {response.solution.joint_state.name}')
                
                # 状態を更新
                self.current_joint_state = response.solution.joint_state
                
                # JointStateメッセージをパブリッシュ（フロントエンド同期用）
                self.joint_pub.publish(self.current_joint_state)
            else:
                self.get_logger().warn(f'IK failed with error code: {response.error_code.val}')
        except Exception as e:
            self.get_logger().error(f'Service call failed: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = IKNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
