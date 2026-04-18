import React, { useEffect, useState } from 'react';
import URDFLoader from 'urdf-loader';

export function RobotArm() {
  const [robot, setRobot] = useState<any>(null);

  useEffect(() => {
    // urdf-loader requires global THREE to be set sometimes depending on the version, 
    // but the newer versions accept a LoadingManager or just work.
    const loader = new URDFLoader();
    
    loader.load('/urdf/dummy_arm.urdf', (result) => {
      // Three.js設定 (Y-up) と URDF設定 (Z-up) を合わせるため、X軸まわりに -90 度回転させます。
      // （アームが床に寝てしまう問題をこれで解決します）
      result.rotation.x = -Math.PI / 2;
      setRobot(result);
    });
  }, []);

  if (!robot) return null;

  return <primitive object={robot} />;
}
