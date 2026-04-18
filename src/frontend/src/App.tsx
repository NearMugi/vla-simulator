import { useRos } from './hooks/useRos';
import { SimulatorScene } from './components/SimulatorScene';

function App() {
  const { isConnected, sendDummyPose } = useRos();

  return (
    <>
      {/* 3Dシミュレータ画面（全画面） */}
      <SimulatorScene />

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
        </div>
      </div>
    </>
  );
}

export default App;
