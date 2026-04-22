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

          {/* 学習ターゲット用オブジェクト（アームのリーチに合わせて少し遠くに配置） */}
          {/* グリッパーの最大開口幅は約9cm（0.09m）なので、幅は6〜7cm程度に抑えつつ高さを出します */}
          
          {/* 1. 四角柱 (直方体) - 目標 */}
          <RigidBody position={[0.2, 0.2, 0.5]} colliders="cuboid">
            <mesh castShadow receiveShadow>
              {/* 幅6cm、高さ15cm、奥行き6cm */}
              <boxGeometry args={[0.06, 0.15, 0.06]} />
              <meshStandardMaterial color="#ef4444" /> {/* 赤 */}
            </mesh>
          </RigidBody>

          {/* 2. 円柱 */}
          <RigidBody position={[-0.1, 0.2, 0.5]} colliders="hull">
            <mesh castShadow receiveShadow>
              {/* 半径3.5cm (直径7cm)、高さ15cm */}
              <cylinderGeometry args={[0.035, 0.035, 0.15, 16]} />
              <meshStandardMaterial color="#3b82f6" /> {/* 青 */}
            </mesh>
          </RigidBody>

          {/* 3. 円錐 */}
          <RigidBody position={[0.0, 0.2, 0.6]} colliders="hull">
            <mesh castShadow receiveShadow>
              {/* 底面半径4cm (直径8cm)、高さ14cm */}
              <coneGeometry args={[0.04, 0.14, 16]} />
              <meshStandardMaterial color="#eab308" /> {/* 黄 */}
            </mesh>
          </RigidBody>

          {/* 運ぶ先の箱 (Tray) - 円錐の真反対(180度裏側)に配置 */}
          {/* オブジェクトが大きくなったので、箱も少し大きく(30cm四方)、壁を高く(12cm)します */}
          <RigidBody type="fixed">
            <group position={[0.0, 0.02, -0.6]}>
              {/* 底面 */}
              <mesh position={[0, -0.01, 0]} receiveShadow castShadow>
                <boxGeometry args={[0.3, 0.02, 0.3]} />
                <meshStandardMaterial color="#14b8a6" transparent opacity={0.5} />
              </mesh>
              {/* 左の壁 */}
              <mesh position={[-0.14, 0.05, 0]} receiveShadow castShadow>
                <boxGeometry args={[0.02, 0.12, 0.3]} />
                <meshStandardMaterial color="#14b8a6" transparent opacity={0.5} />
              </mesh>
              {/* 右の壁 */}
              <mesh position={[0.14, 0.05, 0]} receiveShadow castShadow>
                <boxGeometry args={[0.02, 0.12, 0.3]} />
                <meshStandardMaterial color="#14b8a6" transparent opacity={0.5} />
              </mesh>
              {/* 奥の壁 */}
              <mesh position={[0, 0.05, -0.14]} receiveShadow castShadow>
                <boxGeometry args={[0.3, 0.12, 0.02]} />
                <meshStandardMaterial color="#14b8a6" transparent opacity={0.5} />
              </mesh>
              {/* 手前の壁 */}
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
