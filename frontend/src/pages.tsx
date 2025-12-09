import React, { useState, useEffect } from 'react'
import { setupInterview, getResults, connectWebSocket } from './services'
import { useWebSocket } from './hooks'
import { useTimer } from './hooks'
import { VideoPlayer, Timer, Transcription, Results } from './components'

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
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/interview/setup`, {
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
      <h1>🎬 AI Interview Portal</h1>

      <div className="form-group">
        <label>Job Description</label>
        <textarea
          value={jobDesc}
          onChange={(e) => setJobDesc(e.target.value)}
          placeholder="Paste the job description or role details..."
        />
      </div>

      <div className="form-group">
        <label>Your Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter your full name"
        />
      </div>

      <div className="form-group">
        <label>Interview Duration</label>
        <select value={duration} onChange={(e) => setDuration(Number(e.target.value))}>
          <option value={5}>5 minutes</option>
          <option value={10}>10 minutes</option>
          <option value={15}>15 minutes</option>
        </select>
      </div>

      {error && <div style={{ color: 'red', marginBottom: '15px' }}>{error}</div>}

      <button onClick={handleStart} disabled={loading || !jobDesc || !name}>
        {loading ? '⏳ Starting...' : '▶️ Start Interview'}
      </button>
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
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [timer, setTimer] = useState(300) // 5 minutes default

  useEffect(() => {
    // Connect to WebSocket
    const socket = new WebSocket(`${WS_URL}/ws/interview/${sessionId}`)

    socket.onopen = () => {
      setWs(socket)
      socket.send(JSON.stringify({ type: 'ready' }))
    }

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data)

      if (message.type === 'greeting_video' || message.type === 'question_video') {
        setVideoUrl(message.video_url)
        setEvaluation(null)
        setTranscription('')
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

    // Timer interval
    const timerInterval = setInterval(() => {
      setTimer((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)

    return () => {
      clearInterval(timerInterval)
      if (socket.readyState === WebSocket.OPEN) {
        socket.close()
      }
    }
  }, [sessionId, WS_URL])

  const handleVideoEnd = () => {
    setIsListening(true)
    ws?.send(JSON.stringify({ type: 'listening_start' }))

    // Start capturing audio
    startAudioCapture()
  }

  const startAudioCapture = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const mediaStreamAudioSource = audioContext.createMediaStreamSource(stream)
      const processor = audioContext.createScriptProcessor(4096, 1, 1)

      mediaStreamAudioSource.connect(processor)
      processor.connect(audioContext.destination)

      let recordedChunks: Uint8Array[] = []

      processor.onaudioprocess = (event) => {
        const data = event.inputData[0]
        const chunk = new Uint8Array(data.buffer)
        recordedChunks.push(chunk)

        // Send chunk to WebSocket
        ws?.send(
          JSON.stringify({
            type: 'audio_chunk',
            data: btoa(String.fromCharCode(...chunk)),
          })
        )
      }

      // Stop after 30 seconds or when user stops
      setTimeout(() => {
        processor.disconnect()
        mediaStreamAudioSource.disconnect()
        stream.getTracks().forEach((track) => track.stop())
        setIsListening(false)
        ws?.send(JSON.stringify({ type: 'audio_end' }))
      }, 30000)
    } catch (err) {
      console.error('Microphone error:', err)
      alert('Please allow microphone access to continue')
    }
  }

  return (
    <div className="interview-container">
      <Timer remaining={timer} total={300} />

      {evaluation && (
        <div className="evaluation">
          <h3>Score: {evaluation.score}/10</h3>
          <p>{evaluation.feedback}</p>
        </div>
      )}

      {videoUrl && <VideoPlayer src={videoUrl} onEnded={handleVideoEnd} />}

      {isListening && (
        <>
          <Transcription text={transcription} />
          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <div
              style={{
                display: 'inline-block',
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: '#f44336',
                animation: 'pulse 1s infinite',
              }}
            />
            <p style={{ marginTop: '10px', color: '#666' }}>Listening... Speak now</p>
          </div>
        </>
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
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/api/interview/${sessionId}/results`
        )
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
    return <div className="results-container"><p>Loading results...</p></div>
  }

  if (!results) {
    return <div className="results-container"><p>No results found</p></div>
  }

  return <Results data={results} />
}
