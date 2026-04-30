import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import { Physics, RigidBody } from '@react-three/rapier';
import { RobotArm } from './RobotArm';

export function SimulatorScene({ jointStates }: { jointStates: Record<string, number> }) {
  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Canvas camera={{ position: [1.5, 1.5, 1.5], fov: 50 }}>
        <color attach="background" args={['#1a1a1a']} />

        {/* 照明設定 */}
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1.5} castShadow />

        {/* グリッド表示（床） */}
        <Grid
          infiniteGrid
          fadeDistance={10}
          fadeStrength={5}
          cellColor="#6f6f6f"
          sectionColor="#9d4b4b"
        />

        <OrbitControls makeDefault />

        {/* 物理空間とロボットの描画 */}
        <Physics>
          {/* 床の物理判定（可視化） */}
          <RigidBody type="fixed">
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
              <planeGeometry args={[10, 10]} />
              <meshStandardMaterial color="#334155" /> {/* ダークグレーの床 */}
            </mesh>
          </RigidBody>

          <RigidBody position={[-0.2, 0.0, 0.25]} colliders="cuboid" friction={2.0} restitution={0.0}>
            <mesh castShadow receiveShadow>
              <boxGeometry args={[0.06, 0.05, 0.06]} />
              <meshStandardMaterial color="#ef4444" />
            </mesh>
          </RigidBody>

          {/* 2. 円柱 - 右側に配置 */}
          <RigidBody position={[0.2, 0.0, 0.35]} colliders="hull" friction={2.0} restitution={0.0}>
            <mesh castShadow receiveShadow>
              <cylinderGeometry args={[0.035, 0.035, 0.05, 16]} />
              <meshStandardMaterial color="#3b82f6" />
            </mesh>
          </RigidBody>

          {/* 3. 六角柱 */}
          <RigidBody position={[0.0, 0.0, 0.45]} colliders="hull" friction={2.0} restitution={0.0}>
            <mesh castShadow receiveShadow>
              {/* 六角柱は cylinderGeometry の分割数を 6 にすることで表現 */}
              <cylinderGeometry args={[0.04, 0.04, 0.05, 6]} />
              <meshStandardMaterial color="#10b981" /> {/* 緑 */}
            </mesh>
          </RigidBody>

          {/* 運ぶ先のケース (Tray) */}
          <RigidBody type="fixed">
            <group position={[0.0, 0.02, -0.4]}>
              {/* 底面 */}
              <mesh position={[0, -0.01, 0]} receiveShadow castShadow>
                <boxGeometry args={[0.3, 0.02, 0.3]} />
                <meshStandardMaterial color="#14b8a6" transparent opacity={0.5} />
              </mesh>
              {/* 壁 */}
              <mesh position={[-0.14, 0.05, 0]} receiveShadow castShadow>
                <boxGeometry args={[0.02, 0.12, 0.3]} />
                <meshStandardMaterial color="#14b8a6" transparent opacity={0.5} />
              </mesh>
              <mesh position={[0.14, 0.05, 0]} receiveShadow castShadow>
                <boxGeometry args={[0.02, 0.12, 0.3]} />
                <meshStandardMaterial color="#14b8a6" transparent opacity={0.5} />
              </mesh>
              <mesh position={[0, 0.05, -0.14]} receiveShadow castShadow>
                <boxGeometry args={[0.3, 0.12, 0.02]} />
                <meshStandardMaterial color="#14b8a6" transparent opacity={0.5} />
              </mesh>
              <mesh position={[0, 0.05, 0.14]} receiveShadow castShadow>
                <boxGeometry args={[0.3, 0.12, 0.02]} />
                <meshStandardMaterial color="#14b8a6" transparent opacity={0.5} />
              </mesh>
            </group>
          </RigidBody>

          <RobotArm jointStates={jointStates} />
        </Physics>
      </Canvas>
    </div>
  );
}
