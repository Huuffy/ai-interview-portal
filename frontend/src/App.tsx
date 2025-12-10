import React, { useState } from 'react';
import { SetupPage, CameraPermissionPage, InterviewPage, ResultsPage } from './pages';

type AppPhase = 'setup' | 'permission' | 'interview' | 'results';

interface InterviewData {
  session_id: string;
  ws_url: string;
  message?: string;
}

function App() {
  const [phase, setPhase] = useState<AppPhase>('setup');
  const [sessionData, setSessionData] = useState<InterviewData | null>(null);
  const [results, setResults] = useState<any>(null);

  const handleSetupStart = (data: InterviewData) => {
    console.log('[App] Setup started:', data);
    setSessionData(data);
    setPhase('permission');
  };

  const handlePermissionApprove = () => {
    console.log('[App] Camera permission approved');
    if (sessionData) {
      // FIX: Ensure port 8000 is included in WebSocket URL
      let wsUrl = sessionData.ws_url;
      
      // Replace 0.0.0.0 with localhost
      wsUrl = wsUrl.replace('0.0.0.0', 'localhost');
      
      // Add port 8000 if missing
      if (!wsUrl.includes(':8000')) {
        wsUrl = wsUrl.replace('ws://localhost/', 'ws://localhost:8000/');
      }
      
      console.log('[App] WebSocket URL:', wsUrl);
      setSessionData({ ...sessionData, ws_url: wsUrl });
      setPhase('interview');
    }
  };

  const handleInterviewComplete = (finalResults: any) => {
    console.log('[App] Interview complete:', finalResults);
    setResults(finalResults);
    setPhase('results');
  };

  return (
    <div>
      {phase === 'setup' && <SetupPage onStart={handleSetupStart} />}
      
      {phase === 'permission' && (
        <CameraPermissionPage onApprove={handlePermissionApprove} />
      )}
      
      {phase === 'interview' && sessionData && (
        <InterviewPage
          sessionId={sessionData.session_id}
          wsUrl={sessionData.ws_url}
          onComplete={handleInterviewComplete}
        />
      )}
      
      {phase === 'results' && results && (
        <ResultsPage results={results} />
      )}
    </div>
  );
}

export default App;
