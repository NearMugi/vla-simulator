import { useRos } from './hooks/useRos';

function App() {
  const { isConnected, sendDummyPose } = useRos();

  return (
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
  );
}

export default App;
