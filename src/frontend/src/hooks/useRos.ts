import { useState, useEffect, useRef } from 'react';
import ROSLIB from 'roslib';

export function useRos() {
  const [isConnected, setIsConnected] = useState(false);
  const rosRef = useRef<ROSLIB.Ros | null>(null);

  useEffect(() => {
    const rosUrl = import.meta.env.VITE_ROSBRIDGE_URL || 'ws://localhost:9090';
    console.log('Connecting to ROS web socket:', rosUrl);

    const ros = new ROSLIB.Ros({
      url: rosUrl
    });

    ros.on('connection', () => {
      console.log('Connected to websocket server.');
      setIsConnected(true);
    });

    ros.on('error', (error) => {
      console.log('Error connecting to websocket server: ', error);
      setIsConnected(false);
    });

    ros.on('close', () => {
      console.log('Connection to websocket server closed.');
      setIsConnected(false);
    });

    rosRef.current = ros;

    return () => {
      ros.close();
    };
  }, []);

  const [jointStates, setJointStates] = useState<Record<string, number>>({});

  useEffect(() => {
    if (!rosRef.current || !isConnected) return;

    const jointStateTopic = new ROSLIB.Topic({
      ros: rosRef.current,
      name: '/joint_states',
      messageType: 'sensor_msgs/JointState'
    });

    jointStateTopic.subscribe((message: any) => {
      const newStates: Record<string, number> = {};
      message.name.forEach((name: string, index: number) => {
        newStates[name] = message.position[index];
      });
      setJointStates(newStates);
    });

    return () => {
      jointStateTopic.unsubscribe();
    };
  }, [isConnected]);

  const sendTargetPose = (x: number, y: number, z: number, q = { x: 1.0, y: 0.0, z: 0.0, w: 0.0 }) => {
    if (!rosRef.current || !isConnected) return;

    const topic = new ROSLIB.Topic({
      ros: rosRef.current,
      name: '/vla/target_pose',
      messageType: 'geometry_msgs/PoseStamped'
    });

    const message = new ROSLIB.Message({
      header: {
        stamp: {
          sec: Math.floor(Date.now() / 1000),
          nanosec: (Date.now() % 1000) * 1000000
        },
        frame_id: 'base_link'
      },
      pose: {
        position: { x, y, z },
        orientation: q
      }
    });

    topic.publish(message);
    console.log('Published target pose:', message.pose.position);
  };

  const sendGripperCmd = (width: number) => {
    if (!rosRef.current || !isConnected) return;

    const topic = new ROSLIB.Topic({
      ros: rosRef.current,
      name: '/vla/gripper_cmd',
      messageType: 'std_msgs/Float32'
    });

    const message = new ROSLIB.Message({
      data: width
    });

    topic.publish(message);
    console.log('Published gripper command:', width);
  };

  return { isConnected, sendTargetPose, sendGripperCmd, jointStates };
}
