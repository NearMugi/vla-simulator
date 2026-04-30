import { useState, useEffect } from 'react';
import { useRos } from './hooks/useRos';
import { SimulatorScene } from './components/SimulatorScene';

// Euler角(ラジアン)からクォータニオンへの変換関数
function eulerToQuaternion(roll: number, pitch: number, yaw: number) {
  const cy = Math.cos(yaw * 0.5);
  const sy = Math.sin(yaw * 0.5);
  const cp = Math.cos(pitch * 0.5);
  const sp = Math.sin(pitch * 0.5);
  const cr = Math.cos(roll * 0.5);
  const sr = Math.sin(roll * 0.5);

  return {
    w: cr * cp * cy + sr * sp * sy,
    x: sr * cp * cy - cr * sp * sy,
    y: cr * sp * cy + sr * cp * sy,
    z: cr * cp * sy - sr * sp * cy
  };
}

function App() {
  const { isConnected, sendTargetPose, sendGripperCmd, jointStates } = useRos();

  const [targetPos, setTargetPos] = useState({ x: 0.0, y: 0.5, z: 0.0, gripperPercent: 0 });
  // 初期姿勢: 下向き(X軸で180度回転)をRoll=180として設定
  const [targetRPY, setTargetRPY] = useState({ r: 180, p: 0, y: 0 });

  // 200msのデバウンス処理
  useEffect(() => {
    if (!isConnected) return;
    const handler = setTimeout(() => {
      // 度数法(degree)から弧度法(radian)に変換
      const rollRad = targetRPY.r * (Math.PI / 180);
      const pitchRad = targetRPY.p * (Math.PI / 180);
      const yawRad = targetRPY.y * (Math.PI / 180);

      const q = eulerToQuaternion(rollRad, pitchRad, yawRad);
      sendTargetPose(targetPos.x, targetPos.y, targetPos.z, q);
      
      // グリッパーの状態も同期送信
      sendGripperCmd(0.04 * (targetPos.gripperPercent / 100));
    }, 200);
    return () => clearTimeout(handler);
  }, [targetPos, targetRPY, isConnected]);

  const handlePosChange = (axis: 'x' | 'y' | 'z', value: string) => {
    setTargetPos(prev => ({ ...prev, [axis]: parseFloat(value) }));
  };

  const handleRPYChange = (axis: 'r' | 'p' | 'y', value: string) => {
    setTargetRPY(prev => ({ ...prev, [axis]: parseFloat(value) }));
  };

  const handleRunInference = async () => {
    if (!isConnected) return;

    // 1. シミュレータのCanvasを取得して画像化
    // react-three-fiberのCanvasはデフォルトで preserveDrawingBuffer: false なので、
    // タイミングによっては真っ暗になる可能性がありますが、まずはこの方法で試行
    const canvas = document.querySelector('canvas');
    if (!canvas) {
      alert('Canvas not found');
      return;
    }

    canvas.toBlob(async (blob) => {
      if (!blob) return;

      // 2. バックエンドへ送信
      const formData = new FormData();
      formData.append('image', blob, 'screenshot.png');

      try {
        const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/predict`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) throw new Error('Backend error');

        const data = await response.json();
        console.log('VLA Prediction:', data);

        // 3. 推論結果をUI状態に反映（自動的にデバウンス経由でROSへ送信される）
        setTargetPos({
          x: data.x,
          y: data.y,
          z: data.z,
          gripperPercent: data.gripper
        });
        setTargetRPY({
          r: data.roll,
          p: data.pitch,
          y: data.yaw
        });

      } catch (error) {
        console.error('Inference failed:', error);
        alert('推論に失敗しました');
      }
    }, 'image/png');
  };

  return (
    <>
      {/* 3Dシミュレータ画面（全画面） */}
      <SimulatorScene jointStates={jointStates} />

      {/* コントロールUI（オーバーレイ） */}
      <div className="ui-overlay">
        <div className="app-container">
          <h1>VLA Simulator Control</h1>

          <div className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '● Connected to ROS 2' : '○ Disconnected'}
          </div>

          <button 
            onClick={handleRunInference} 
            disabled={!isConnected}
            style={{ 
              marginBottom: '20px', 
              backgroundColor: '#8b5cf6', // 紫色で区別
              fontSize: '1.1rem' 
            }}
          >
            Run VLA Inference
          </button>

          <div style={{ marginTop: '20px' }}>
            <h3>Target Position (m)</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <label>
                X: {targetPos.x.toFixed(2)}
                <input type="range" min="-0.8" max="0.8" step="0.05" value={targetPos.x} onChange={e => handlePosChange('x', e.target.value)} style={{ width: '100%', marginLeft: '10px' }} />
              </label>
              <label>
                Y: {targetPos.y.toFixed(2)}
                <input type="range" min="0.0" max="0.9" step="0.05" value={targetPos.y} onChange={e => handlePosChange('y', e.target.value)} style={{ width: '100%', marginLeft: '10px' }} />
              </label>
              <label>
                Z: {targetPos.z.toFixed(2)}
                <input type="range" min="-0.8" max="0.8" step="0.05" value={targetPos.z} onChange={e => handlePosChange('z', e.target.value)} style={{ width: '100%', marginLeft: '10px' }} />
              </label>
            </div>
          </div>

          <div style={{ marginTop: '20px' }}>
            <h3>Target Orientation (deg)</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <label>
                Roll (X): {targetRPY.r.toFixed(0)}°
                <input type="range" min="-180" max="180" step="5" value={targetRPY.r} onChange={e => handleRPYChange('r', e.target.value)} style={{ width: '100%', marginLeft: '10px' }} />
              </label>
              <label>
                Pitch (Y): {targetRPY.p.toFixed(0)}°
                <input type="range" min="-180" max="180" step="5" value={targetRPY.p} onChange={e => handleRPYChange('p', e.target.value)} style={{ width: '100%', marginLeft: '10px' }} />
              </label>
              <label>
                Yaw (Z): {targetRPY.y.toFixed(0)}°
                <input type="range" min="-180" max="180" step="5" value={targetRPY.y} onChange={e => handleRPYChange('y', e.target.value)} style={{ width: '100%', marginLeft: '10px' }} />
              </label>
            </div>
          </div>

          <div style={{ marginTop: '20px' }}>
            <h3>Gripper Control</h3>
            <label>
              Grip: {((targetPos as any).gripperPercent || 0)}%
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={(targetPos as any).gripperPercent || 0}
                onChange={e => {
                  const percent = parseInt(e.target.value);
                  setTargetPos(prev => ({ ...prev, gripperPercent: percent }));
                  // 0.04 (Closed) * percent / 100
                  sendGripperCmd(0.04 * (percent / 100));
                }}
                style={{ width: '100%', marginLeft: '10px' }}
              />
            </label>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
