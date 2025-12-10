import React, { useState, useEffect } from 'react'

// ===== SETUP PAGE =====
export const SetupPage: React.FC<{ onStart: (data: any) => void }> = ({ onStart }) => {
  const [jobDesc, setJobDesc] = useState('')
  const [name, setName] = useState('')
  const [duration, setDuration] = useState(5)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleStart = async () => {
    if (!jobDesc.trim() || !name.trim()) {
      setError('Please fill in all fields')
      return
    }

    setLoading(true)
    setError('')

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/interview/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_description: jobDesc,
          candidate_name: name,
          duration_minutes: duration,
          avatar_image_url: null
        })
      })

      if (!response.ok) throw new Error('Failed to start interview')

      const data = await response.json()
      onStart(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setLoading(false)
    }
  }

  return (
    <div className="setup-container">
      <div className="setup-header">
        <h1>🎬 AI Interview Portal</h1>
        <p>Practice interviews with AI guidance</p>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); handleStart(); }}>
        <div className="form-group">
          <label htmlFor="jobDesc">Job Description *</label>
          <textarea
            id="jobDesc"
            value={jobDesc}
            onChange={(e) => setJobDesc(e.target.value)}
            placeholder="Paste the job description or role details you're interviewing for..."
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="name">Your Name *</label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your full name"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="duration">Interview Duration</label>
          <select 
            id="duration"
            value={duration} 
            onChange={(e) => setDuration(Number(e.target.value))}
          >
            <option value={5}>5 minutes</option>
            <option value={10}>10 minutes</option>
            <option value={15}>15 minutes</option>
          </select>
        </div>

        {error && <div className="error-message">{error}</div>}

        <button 
          type="submit" 
          disabled={loading || !jobDesc.trim() || !name.trim()}
          className="btn-primary"
        >
          {loading ? '⏳ Starting...' : '▶️ Start Interview'}
        </button>
      </form>
    </div>
  )
}

// ===== INTERVIEW PAGE =====
export const InterviewPage: React.FC<{ sessionId: string; onComplete: () => void }> = ({
  sessionId,
  onComplete,
}) => {
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const WS_URL = API_URL.replace('http', 'ws')

  const [videoUrl, setVideoUrl] = useState('')
  const [transcription, setTranscription] = useState('')
  const [evaluation, setEvaluation] = useState<any>(null)
  const [isListening, setIsListening] = useState(false)
  const [timer, setTimer] = useState(300)
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [totalQuestions, setTotalQuestions] = useState(0)

  useEffect(() => {
    const socket = new WebSocket(`${WS_URL}/ws/interview/${sessionId}`)

    socket.onopen = () => {
      console.log('WebSocket connected')
      socket.send(JSON.stringify({ type: 'ready' }))
    }

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data)
      console.log('WebSocket message:', message.type)

      if (message.type === 'greeting_video' || message.type === 'question_video') {
        setVideoUrl(message.video_url)
        setEvaluation(null)
        setTranscription('')
        setIsListening(false)
        if (message.question_number) {
          setCurrentQuestion(message.question_number)
          setTotalQuestions(message.total_questions)
        }
      } else if (message.type === 'transcription_partial') {
        setTranscription(message.text)
      } else if (message.type === 'evaluation') {
        setEvaluation(message)
      } else if (message.type === 'results') {
        onComplete()
      }
    }

    socket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    socket.onclose = () => {
      console.log('WebSocket closed')
    }

    const timerInterval = setInterval(() => {
      setTimer((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)

    return () => {
      clearInterval(timerInterval)
      if (socket.readyState === WebSocket.OPEN) {
        socket.close()
      }
    }
  }, [sessionId, WS_URL, onComplete])

  const handleVideoEnd = () => {
    setIsListening(true)
    setTimeout(() => {
      startAudioCapture()
    }, 500)
  }

  const startAudioCapture = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const source = audioContext.createMediaStreamSource(stream)
      const processor = audioContext.createScriptProcessor(4096, 1, 1)

      source.connect(processor)
      processor.connect(audioContext.destination)

      processor.onaudioprocess = (event: AudioProcessingEvent) => {
        // FIXED: Use getChannelData() instead of inputData
        const channelData = event.inputBuffer.getChannelData(0)
        const chunk = new Uint8Array(channelData.length)
        for (let i = 0; i < channelData.length; i++) {
          chunk[i] = Math.floor((channelData[i] + 1) * 128)
        }
        console.log('Audio chunk captured:', chunk.length)
      }

      setTimeout(() => {
        processor.disconnect()
        source.disconnect()
        stream.getTracks().forEach((track) => track.stop())
        setIsListening(false)
      }, 30000)
    } catch (err) {
      console.error('Microphone error:', err)
      alert('Please allow microphone access')
      setIsListening(false)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const progress = ((300 - timer) / 300) * 100

  return (
    <div className="interview-container">
      <div className="interview-header">
        <div className="interview-title">
          <h2>Interview in Progress</h2>
          <p>Question {currentQuestion} of {totalQuestions || '...'}</p>
        </div>
        <div className="timer">
          <span className="timer-text">⏱️ {formatTime(timer)}</span>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>
      </div>

      {evaluation && (
        <div className="evaluation">
          <h3>Score: {evaluation.score}/10</h3>
          <p>{evaluation.feedback}</p>
        </div>
      )}

      {videoUrl && (
        <div className="video-section">
          <video
            src={videoUrl}
            autoPlay
            onEnded={handleVideoEnd}
            className="video-player"
          />
        </div>
      )}

      {isListening && (
        <div className="listening-indicator">
          <div className="pulse" />
          <p className="listening-text">🎤 Listening... Speak now</p>
          <p style={{ fontSize: '12px', color: '#888' }}>You have 30 seconds</p>
        </div>
      )}

      {transcription && (
        <div className="transcription">
          <strong>📝 Your Response:</strong>
          <p>{transcription}</p>
        </div>
      )}
    </div>
  )
}

// ===== RESULTS PAGE =====
export const ResultsPage: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const [results, setResults] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
        const response = await fetch(`${apiUrl}/api/interview/${sessionId}/results`)
        const data = await response.json()
        setResults(data)
      } catch (err) {
        console.error('Failed to fetch results:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [sessionId])

  if (loading) {
    return (
      <div className="results-container">
        <div className="loading">
          <div className="spinner" />
          <p>Loading results...</p>
        </div>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="results-container">
        <p>No results found</p>
      </div>
    )
  }

  return (
    <div className="results-container">
      <h1>Interview Results</h1>

      <div className="score-card">
        <div className="score-value">{Math.round(results.overall_score || 0)}</div>
        <div className="score-label">Overall Score</div>
        <div className="recommendation">
          {results.recommendation || 'Good Performance'}
        </div>
      </div>

      <div className="breakdown">
        <h3>📊 Q&A Breakdown</h3>
        {results.breakdown?.map((item: any, idx: number) => (
          <div key={idx} className="breakdown-item">
            <strong>Q{idx + 1}: {item.question}</strong>
            <p>Score: {item.marks}</p>
            <p>{item.feedback}</p>
          </div>
        ))}
      </div>

      <div className="strengths-weaknesses">
        <div className="strength-card">
          <h3>💪 Strengths</h3>
          <ul>
            {results.strengths?.map((s: string, idx: number) => (
              <li key={idx}>{s}</li>
            ))}
          </ul>
        </div>
        <div className="weakness-card">
          <h3>📈 Areas to Improve</h3>
          <ul>
            {results.weaknesses?.map((w: string, idx: number) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      </div>

      <button 
        className="download-btn"
        onClick={() => window.location.reload()}
      >
        🔄 Start Another Interview
      </button>
    </div>
  )
}