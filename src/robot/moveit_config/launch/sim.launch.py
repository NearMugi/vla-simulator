import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    # パス設定
    urdf_path = '/app/urdf/dummy_arm.urdf'
    srdf_path = '/app/moveit_config/config/dummy_arm.srdf'
    kinematics_yaml_path = '/app/moveit_config/config/kinematics.yaml'

    with open(urdf_path, 'r') as f:
        robot_description_content = f.read()

    with open(srdf_path, 'r') as f:
        robot_description_semantic_content = f.read()

    robot_description = {'robot_description': robot_description_content}
    robot_description_semantic = {'robot_description_semantic': robot_description_semantic_content}
    
    kinematics_yaml = {'robot_description_kinematics': {}}
    import yaml
    with open(kinematics_yaml_path, 'r') as f:
        kinematics_yaml = {'robot_description_kinematics': yaml.safe_load(f)}

    # MoveGroup Node
    move_group_node = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            {'publish_robot_description_semantic': True},
            {'use_sim_time': False},
        ],
    )

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='both',
        parameters=[robot_description],
    )

    # Rosbridge WebSocket
    rosbridge_node = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        output='screen',
        parameters=[{'address': '0.0.0.0'}]
    )

    # IK Node (直接スクリプトを実行)
    from launch.actions import ExecuteProcess
    ik_node = ExecuteProcess(
        cmd=['python3', '/app/moveit_config/scripts/ik_node.py'],
        output='screen'
    )

    # Joint State Publisher
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{'source_list': ['/joint_states']}] # /joint_states から入力を受け取る
    )

    return LaunchDescription([
        robot_state_publisher,
        joint_state_publisher,
        move_group_node,
        rosbridge_node,
        ik_node
    ])
