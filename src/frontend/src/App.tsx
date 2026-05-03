import { useState, useEffect, useRef } from 'react';
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
  const [targetRPY, setTargetRPY] = useState({ r: 180, p: 0, y: 0 });

  // 200msのデバウンス処理
  useEffect(() => {
    if (!isConnected) return;
    const handler = setTimeout(() => {
      const rollRad = targetRPY.r * (Math.PI / 180);
      const pitchRad = targetRPY.p * (Math.PI / 180);
      const yawRad = targetRPY.y * (Math.PI / 180);

      const q = eulerToQuaternion(rollRad, pitchRad, yawRad);
      sendTargetPose(targetPos.x, targetPos.y, targetPos.z, q);
      sendGripperCmd(0.04 * (1 - targetPos.gripperPercent / 100));
    }, 200);
    return () => clearTimeout(handler);
  }, [targetPos, targetRPY, isConnected]);

  const handlePosChange = (axis: 'x' | 'y' | 'z', value: string) => {
    setTargetPos(prev => ({ ...prev, [axis]: parseFloat(value) }));
  };

  const handleRPYChange = (axis: 'r' | 'p' | 'y', value: string) => {
    setTargetRPY(prev => ({ ...prev, [axis]: parseFloat(value) }));
  };

  const [cameraPos, setCameraPos] = useState<[number, number, number] | undefined>(undefined);
  const [isInferring, setIsInferring] = useState(false);
  const [isAutonomous, setIsAutonomous] = useState(false); 
  const [lastCaptureUrl, setLastCaptureUrl] = useState<string | null>(null);
  const [inferenceResult, setInferenceResult] = useState<any>(null);
  const [instruction, setInstruction] = useState("pick up the blue block");

  // 自律モードの最新状態を保持するためのRef（クロージャ・非同期対策）
  const isAutoRef = useRef(false);

  useEffect(() => {
    isAutoRef.current = isAutonomous;
    if (isAutonomous && !isInferring) {
      handleRunInference();
    }
  }, [isAutonomous]);

  const handleRunInference = async () => {
    if (!isConnected || isInferring) return;
    
    setIsInferring(true);
    setInferenceResult(null);

    // 推論時は定点カメラに固定
    setCameraPos([1.2, 0.8, 1.2]); 
    await new Promise(resolve => setTimeout(resolve, 500));

    const canvas = document.querySelector('canvas');
    if (!canvas) {
      setIsInferring(false);
      setIsAutonomous(false);
      isAutoRef.current = false;
      return;
    }

    canvas.toBlob(async (blob) => {
      if (!blob) {
        setIsInferring(false);
        setIsAutonomous(false);
        isAutoRef.current = false;
        return;
      }

      // 自律モード中に停止ボタンが押された場合のみ中断
      if (isAutonomous && !isAutoRef.current) {
        setIsInferring(false);
        return;
      }

      const formData = new FormData();
      formData.append('image', blob, 'screenshot.png');
      formData.append('instruction', instruction);
      formData.append('current_x', targetPos.x.toString());
      formData.append('current_y', targetPos.y.toString());
      formData.append('current_z', targetPos.z.toString());
      formData.append('current_roll', targetRPY.r.toString());
      formData.append('current_pitch', targetRPY.p.toString());
      formData.append('current_yaw', targetRPY.y.toString());
      formData.append('current_gripper', (targetPos.gripperPercent / 100).toString());

      try {
        const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/predict`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) throw new Error('Backend error');

        const data = await response.json();
        
        // 通信待ちの間に停止されていないかチェック（自律モード時のみ）
        if (isAutonomous && !isAutoRef.current) {
           setIsInferring(false);
           return;
        }

        setInferenceResult(data);
        setTargetPos({
          x: data.x,
          y: data.y,
          z: data.z,
          gripperPercent: data.gripper * 100
        });
        setTargetRPY({
          r: data.roll,
          p: data.pitch,
          y: data.yaw
        });

        // 移動待機
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const finalCanvas = document.querySelector('canvas');
        if (finalCanvas) {
          setLastCaptureUrl(finalCanvas.toDataURL('image/png'));
        }

        // 自律モード継続中ならループ
        if (isAutoRef.current) {
          setTimeout(handleRunInference, 100);
        }

      } catch (error) {
        console.error('Inference failed:', error);
        setIsAutonomous(false);
        isAutoRef.current = false;
        alert('推論に失敗しました');
      } finally {
        setIsInferring(false);
      }
    }, 'image/png');
  };

  return (
    <>
      <SimulatorScene jointStates={jointStates} cameraPosition={cameraPos} />

      <div className="ui-overlay" style={{ maxHeight: '100vh', overflowY: 'auto' }}>
        <div className="app-container">
          <h1>VLA Simulator Control</h1>

          <div className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '● Connected to ROS 2' : '○ Disconnected'}
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ fontSize: '0.9rem', color: '#a78bfa', display: 'block', marginBottom: '5px' }}>Instruction</label>
            <input 
              type="text" 
              value={instruction} 
              onChange={e => setInstruction(e.target.value)}
              placeholder="e.g. pick up the blue block"
              style={{ 
                width: '100%', 
                padding: '8px', 
                borderRadius: '4px', 
                border: '1px solid #4b5563', 
                backgroundColor: '#1f2937', 
                color: 'white' 
              }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '10px' }}>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button 
                onClick={handleRunInference} 
                disabled={!isConnected || isInferring || isAutonomous}
                style={{ 
                  flex: 2, 
                  backgroundColor: (isInferring || isAutonomous) ? '#4b5563' : '#8b5cf6', 
                  fontSize: '1.1rem'
                }}
              >
                {isInferring ? 'Inferring...' : 'Run Single Inference'}
              </button>
              <button 
                onClick={() => setIsAutonomous(!isAutonomous)}
                disabled={!isConnected}
                style={{ 
                  flex: 2, 
                  backgroundColor: isAutonomous ? '#ef4444' : '#10b981', 
                  fontSize: '1.1rem',
                  fontWeight: 'bold'
                }}
              >
                {isAutonomous ? 'STOP AUTO' : 'START AUTO'}
              </button>
            </div>
            
            <button 
              onClick={() => setCameraPos([1.2, 0.8, 1.2])}
              style={{ backgroundColor: '#4b5563', fontSize: '0.9rem' }}
            >
              Reset Camera View
            </button>

            {(lastCaptureUrl || inferenceResult) && (
              <div style={{ 
                display: 'flex', 
                gap: '15px', 
                backgroundColor: 'rgba(0,0,0,0.3)', 
                padding: '10px', 
                borderRadius: '8px',
                border: '1px solid rgba(255,255,255,0.1)'
              }}>
                {lastCaptureUrl && (
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '0.7rem', margin: '0 0 5px 0', opacity: 0.7 }}>Last Capture</p>
                    <img src={lastCaptureUrl} alt="Last capture" style={{ width: '100%', borderRadius: '4px' }} />
                  </div>
                )}
                {inferenceResult && (
                  <div style={{ flex: 1, fontSize: '0.8rem' }}>
                    <p style={{ fontSize: '0.7rem', margin: '0 0 5px 0', opacity: 0.7 }}>Prediction</p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px' }}>
                      <span>X: {inferenceResult.x.toFixed(2)}</span>
                      <span>R: {inferenceResult.roll.toFixed(0)}</span>
                      <span>Y: {inferenceResult.y.toFixed(2)}</span>
                      <span>P: {inferenceResult.pitch.toFixed(0)}</span>
                      <span>Z: {inferenceResult.z.toFixed(2)}</span>
                      <span>Y: {inferenceResult.yaw.toFixed(0)}</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div style={{ marginTop: '20px' }}>
            <h3>Target Position (m)</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <label>
                X: {targetPos.x.toFixed(2)}
                <input type="range" min="-0.8" max="0.8" step="0.05" value={targetPos.x} onChange={e => handlePosChange('x', e.target.value)} style={{ width: '100%', marginLeft: '10px' }} disabled={isAutonomous} />
              </label>
              <label>
                Y: {targetPos.y.toFixed(2)}
                <input type="range" min="0.0" max="0.9" step="0.05" value={targetPos.y} onChange={e => handlePosChange('y', e.target.value)} style={{ width: '100%', marginLeft: '10px' }} disabled={isAutonomous} />
              </label>
              <label>
                Z: {targetPos.z.toFixed(2)}
                <input type="range" min="-0.8" max="0.8" step="0.05" value={targetPos.z} onChange={e => handlePosChange('z', e.target.value)} style={{ width: '100%', marginLeft: '10px' }} disabled={isAutonomous} />
              </label>
            </div>
          </div>

          <div style={{ marginTop: '20px' }}>
            <h3>Target Orientation (deg)</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <label>
                Roll (X): {targetRPY.r.toFixed(0)}°
                <input type="range" min="-180" max="180" step="5" value={targetRPY.r} onChange={e => handleRPYChange('r', e.target.value)} style={{ width: '100%', marginLeft: '10px' }} disabled={isAutonomous} />
              </label>
              <label>
                Pitch (Y): {targetRPY.p.toFixed(0)}°
                <input type="range" min="-180" max="180" step="5" value={targetRPY.p} onChange={e => handleRPYChange('p', e.target.value)} style={{ width: '100%', marginLeft: '10px' }} disabled={isAutonomous} />
              </label>
              <label>
                Yaw (Z): {targetRPY.y.toFixed(0)}°
                <input type="range" min="-180" max="180" step="5" value={targetRPY.y} onChange={e => handleRPYChange('y', e.target.value)} style={{ width: '100%', marginLeft: '10px' }} disabled={isAutonomous} />
              </label>
            </div>
          </div>

          <div style={{ marginTop: '20px' }}>
            <h3>Gripper Control (Octo Spec)</h3>
            <label>
              Status: {targetPos.gripperPercent <= 10 ? 'CLOSED' : targetPos.gripperPercent >= 90 ? 'OPEN' : `${targetPos.gripperPercent.toFixed(0)}%`}
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={targetPos.gripperPercent}
                onChange={e => {
                  const percent = parseInt(e.target.value);
                  setTargetPos(prev => ({ ...prev, gripperPercent: percent }));
                  // Octo spec: 0% = 閉(物理0.04), 100% = 開(物理0.0)
                  sendGripperCmd(0.04 * (1 - percent / 100));
                }}
                disabled={isAutonomous}
                style={{ width: '100%', marginLeft: '10px' }}
              />
              <span style={{ fontSize: '0.7rem', opacity: 0.6 }}>0%: 閉 (Closed) / 100%: 開 (Open)</span>
            </label>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
