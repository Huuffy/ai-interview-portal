import React, { useState } from 'react'
import { SetupPage } from './pages'
import { InterviewPage } from './pages'
import { ResultsPage } from './pages'
import './App.css'

type AppState = 'setup' | 'interview' | 'results'

function App() {
  const [state, setState] = useState<AppState>('setup')
  const [sessionId, setSessionId] = useState('')

  const handleSetupStart = (data: any) => {
    setSessionId(data.session_id)
    setState('interview')
  }

  const handleInterviewComplete = () => {
    setState('results')
  }

  return (
    <div className="app">
      {state === 'setup' && (
        <SetupPage onStart={handleSetupStart} />
      )}
      {state === 'interview' && (
        <InterviewPage sessionId={sessionId} onComplete={handleInterviewComplete} />
      )}
      {state === 'results' && (
        <ResultsPage sessionId={sessionId} />
      )}
    </div>
  )
}

export default App