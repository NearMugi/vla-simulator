import React, { useEffect, useState } from 'react';
import URDFLoader from 'urdf-loader';

export function RobotArm({ jointStates }: { jointStates: Record<string, number> }) {
  const [robot, setRobot] = useState<any>(null);

  useEffect(() => {
    const loader = new URDFLoader();
    loader.load('/urdf/dummy_arm.urdf', (result) => {
      result.rotation.x = -Math.PI / 2;
      setRobot(result);
    });
  }, []);

  useEffect(() => {
    if (robot && jointStates) {
      Object.keys(jointStates).forEach((name) => {
        if (robot.joints[name]) {
          robot.joints[name].setJointValue(jointStates[name]);
        }
      });
    }
  }, [robot, jointStates]);

  if (!robot) return null;

  return <primitive object={robot} />;
}
