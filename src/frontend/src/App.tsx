import { useRos } from './hooks/useRos';
import { SimulatorScene } from './components/SimulatorScene';

function App() {
  const { isConnected, sendDummyPose, sendGripperCmd, jointStates } = useRos();

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
            onClick={sendDummyPose} 
            disabled={!isConnected}
          >
            Send Dummy Target Pose
          </button>

          <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
            <button 
              onClick={() => sendGripperCmd(0.0)} 
              disabled={!isConnected}
            >
              Open Gripper
            </button>
            <button 
              onClick={() => sendGripperCmd(0.04)} 
              disabled={!isConnected}
            >
              Close Gripper
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
