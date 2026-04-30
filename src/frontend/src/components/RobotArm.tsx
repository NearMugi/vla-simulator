import React, { useEffect, useState, useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { RigidBody, RapierRigidBody } from '@react-three/rapier';
import * as THREE from 'three';
import URDFLoader from 'urdf-loader';

export function RobotArm({ jointStates }: { jointStates: Record<string, number> }) {
  const [robot, setRobot] = useState<any>(null);
  
  // 各リンクの RigidBody の参照を保持する辞書
  const rigidBodyRefs = useRef<Record<string, React.RefObject<RapierRigidBody>>>({});

  useEffect(() => {
    const loader = new URDFLoader();
    loader.load('/urdf/dummy_arm.urdf', (result) => {
      // 物理エンジンとの整合性のため、初期回転を適用 (Y-up化により削除)
      result.updateMatrixWorld(true);
      
      // RigidBody用のRefを事前生成
      const refs: Record<string, React.RefObject<RapierRigidBody>> = {};
      Object.keys(result.links).forEach(linkName => {
        refs[linkName] = React.createRef<RapierRigidBody>();
      });
      rigidBodyRefs.current = refs;
      
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

  // 毎フレーム、見た目のワールド座標を物理エンジン側のRigidBodyに同期
  useFrame(() => {
    if (!robot) return;
    
    // アーム全体のワールドマトリクスを最新化
    robot.updateMatrixWorld(true);

    const position = new THREE.Vector3();
    const quaternion = new THREE.Quaternion();
    const scale = new THREE.Vector3();

    Object.keys(robot.links).forEach(linkName => {
      const linkObj = robot.links[linkName];
      const rbRef = rigidBodyRefs.current[linkName];
      
      if (linkObj && rbRef && rbRef.current) {
        linkObj.matrixWorld.decompose(position, quaternion, scale);
        
        // RigidBody の位置と姿勢を強制更新 (Kinematic)
        // 値が上書きされないようにclone()を渡す
        rbRef.current.setNextKinematicTranslation(position.clone());
        rbRef.current.setNextKinematicRotation(quaternion.clone());
      }
    });
  });

  if (!robot) return null;

  return (
    <group>
      {/* 1. 見た目の描画 */}
      <primitive object={robot} />

      {/* 2. 物理判定用の透明なゴーストRigidBody群 */}
      {Object.keys(robot.links).map((linkName) => {
        const linkObj = robot.links[linkName];
        
        const meshes: THREE.Mesh[] = [];
        linkObj.traverse((child: any) => {
          if (child.isMesh) meshes.push(child);
        });

        if (meshes.length === 0) return null;

        return (
          <RigidBody 
            key={linkName} 
            ref={rigidBodyRefs.current[linkName]} 
            type="kinematicPosition" 
            colliders={linkName.includes('finger') ? "cuboid" : "hull"} 
            friction={2.0}
            restitution={0.0}
          >
            {meshes.map((mesh, idx) => (
              <mesh 
                key={idx} 
                geometry={mesh.geometry} 
                position={mesh.position} 
                rotation={mesh.rotation} 
                scale={mesh.scale}
              >
                {/* 物理エンジンに形状を認識させるため、visible={false} ではなく透明なマテリアルを適用 */}
                <meshBasicMaterial transparent opacity={0} />
              </mesh>
            ))}
          </RigidBody>
        );
      })}
    </group>
  );
}
