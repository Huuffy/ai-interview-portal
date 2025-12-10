import React, { useState, useEffect, useRef } from 'react'

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

      // Debug log to verify backend response shape
      console.log('setup response', data)

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

      {error && <div className="error-message">{error}</div>}

      <div className="form-group">
        <label htmlFor="jobDesc">Job Description *</label>
        <textarea
          id="jobDesc"
          placeholder="Paste the job description or describe the role..."
          value={jobDesc}
          onChange={(e) => setJobDesc(e.target.value)}
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="name">Your Name *</label>
        <input
          id="name"
          type="text"
          placeholder="Enter your full name..."
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="duration">Interview Duration (minutes)</label>
        <select
          id="duration"
          value={duration}
          onChange={(e) => setDuration(parseInt(e.target.value))}
          disabled={loading}
        >
          <option value={5}>5 minutes</option>
          <option value={10}>10 minutes</option>
          <option value={15}>15 minutes</option>
          <option value={20}>20 minutes</option>
        </select>
      </div>

      <button
        onClick={handleStart}
        disabled={loading || !jobDesc.trim() || !name.trim()}
        className="btn-primary"
      >
        {loading ? 'Starting...' : 'Start Interview'}
      </button>
    </div>
  )
}

// ===== INTERVIEW PAGE =====
export const InterviewPage: React.FC<{
  interviewId: string
  candidateName: string
  onComplete: (results: any) => void
}> = ({ interviewId, candidateName, onComplete }) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const [currentQuestion, setCurrentQuestion] = useState<string>('')
  const [timeRemaining, setTimeRemaining] = useState<number>(300)
  const [isListening, setIsListening] = useState<boolean>(false)
  const [transcription, setTranscription] = useState<string>('')
  const [evaluation, setEvaluation] = useState<string>('')
  const [status, setStatus] = useState<
    'waiting' | 'generating' | 'analysing' | 'evaluating' | 'playing'
  >('waiting')
  const [error, setError] = useState<string>('')
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [interviewStarted, setInterviewStarted] = useState<boolean>(false)
  const [questionCount, setQuestionCount] = useState<number>(0)
  const [totalQuestions, setTotalQuestions] = useState<number>(5)
  const [showWelcome, setShowWelcome] = useState<boolean>(true)

  // NEW: AI interviewer video URL (MuseTalk output)
  const [aiVideoUrl, setAiVideoUrl] = useState<string | null>(null)

  // Request camera & audio permissions on mount
  useEffect(() => {
    if (!interviewId) {
      setError('No interview ID provided. Please restart the interview.')
      return
    }

    const requestPermissions = async () => {
      try {
        setStatus('waiting')
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: { echoCancellation: true, noiseSuppression: true }
        })
        setStream(mediaStream)

        // Display camera feed
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream
          videoRef.current.play()
        }

        // Initialize MediaRecorder
        const mediaRecorder = new MediaRecorder(mediaStream, {
          mimeType: 'audio/webm;codecs=opus'
        })
        mediaRecorderRef.current = mediaRecorder

        mediaRecorder.ondataavailable = (event) => {
          audioChunksRef.current.push(event.data)
        }

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
          audioChunksRef.current = []
          await submitAnswer(audioBlob)
        }

        // Start first question after 2 seconds (show welcome)
        setTimeout(() => {
          setShowWelcome(false)
          fetchFirstQuestion()
        }, 2000)
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to access camera/microphone. Please check permissions.'
        )
      }
    }

    requestPermissions()

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop())
      }
    }
  }, [interviewId])

  // Fetch first or next question
  const fetchFirstQuestion = async () => {
    if (!interviewId) return

    setStatus('generating')
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/interview/${interviewId}/question`,
        { method: 'GET' }
      )
      if (!response.ok) throw new Error('Failed to fetch question')
      const data = await response.json()

      setCurrentQuestion(data.question)
      setQuestionCount((prev) => prev + 1)

      // total questions from API (if available)
      if (data.total_questions) {
        setTotalQuestions(data.total_questions)
      }

      // AI interviewer video (MuseTalk) — backend should return this
      if (data.video_url) {
        setAiVideoUrl(data.video_url)
      }

      setStatus('playing')

      // Optional: keep audio path if you still use it
      if (data.audio_url) {
        if (audioRef.current) {
          audioRef.current.src = data.audio_url
          audioRef.current.onended = () => {
            setStatus('waiting')
            startListening()
          }
          audioRef.current.play()
        }
      } else {
        // Fallback: TTS (you can remove this if everything is video)
        await playTextToSpeech(data.question)
        setStatus('waiting')
        startListening()
      }

      setInterviewStarted(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load question')
      setStatus('waiting')
    }
  }

  // Text-to-speech fallback
  const playTextToSpeech = async (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1
      utterance.pitch = 1
      window.speechSynthesis.speak(utterance)

      return new Promise<void>((resolve) => {
        utterance.onend = () => resolve()
      })
    }
  }

  // Start recording user answer
  const startListening = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'inactive') {
      audioChunksRef.current = []
      mediaRecorderRef.current.start()
      setIsListening(true)
      setStatus('waiting')
    }
  }

  // Stop recording and submit answer
  const stopListening = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
      setIsListening(false)
    }
  }

  // Submit audio answer
  const submitAnswer = async (audioBlob: Blob) => {
    setStatus('analysing')
    setTranscription('')
    setEvaluation('')

    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'answer.webm')

      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/interview/${interviewId}/answer`,
        {
          method: 'POST',
          body: formData
        }
      )

      if (!response.ok) throw new Error('Failed to submit answer')
      const data = await response.json()

      setTranscription(data.transcription || '')
      setEvaluation(data.evaluation || '')
      setStatus('evaluating')

      // Wait 2 seconds then fetch next question or complete
      setTimeout(() => {
        if (data.next_question && questionCount < totalQuestions) {
          fetchFirstQuestion()
        } else {
          // Interview complete, fetch final results
          fetchResults()
        }
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process answer')
      setStatus('waiting')
    }
  }

  // Fetch final results
  const fetchResults = async () => {
    setStatus('analysing')
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/interview/${interviewId}/results`
      )
      if (!response.ok) throw new Error('Failed to fetch results')
      const results = await response.json()
      onComplete(results)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results')
      setStatus('waiting')
    }
  }

  // Timer effect
  useEffect(() => {
    if (!interviewStarted || timeRemaining <= 0) return

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          stopListening()
          fetchResults()
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [interviewStarted, timeRemaining])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="interview-container">
      <audio ref={audioRef} />

      <div className="interview-header">
        <div className="interview-title">
          <h2>Interview in Progress</h2>
          <p>
            Question {questionCount} of {totalQuestions} • Candidate: {candidateName}
          </p>
        </div>
        <div className="timer">
          <span className="timer-text">⏱ {formatTime(timeRemaining)}</span>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${(timeRemaining / 300) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Welcome message with candidate name */}
      {showWelcome && (
        <div style={{ textAlign: 'center', padding: '40px 20px', margin: '20px 0' }}>
          <h2 style={{ color: '#f5f5f5', marginBottom: '12px' }}>Welcome, {candidateName}! 👋</h2>
          <p style={{ color: '#cbd5e1' }}>Get ready for your AI interview...</p>
          <div className="spinner" style={{ margin: '20px auto 0' }} />
        </div>
      )}

      {/* Status indicator */}
      {!showWelcome && status !== 'waiting' && (
        <div style={{ textAlign: 'center', padding: '20px', margin: '20px 0' }}>
          {status === 'generating' && (
            <div>
              <div className="spinner" style={{ margin: '0 auto' }} />
              <p style={{ color: '#cbd5e1', marginTop: '12px' }}>Generating question...</p>
            </div>
          )}
          {status === 'playing' && (
            <div>
              <div className="pulse" style={{ display: 'inline-block' }} />
              <p style={{ color: '#cbd5e1', marginTop: '12px' }}>AI is speaking...</p>
            </div>
          )}
          {status === 'analysing' && (
            <div>
              <div className="spinner" style={{ margin: '0 auto' }} />
              <p style={{ color: '#cbd5e1', marginTop: '12px' }}>Analysing your answer...</p>
            </div>
          )}
          {status === 'evaluating' && (
            <div>
              <div className="spinner" style={{ margin: '0 auto' }} />
              <p style={{ color: '#cbd5e1', marginTop: '12px' }}>Evaluating response...</p>
            </div>
          )}
        </div>
      )}

      {/* Two video screens: AI interviewer + user */}
      {!showWelcome && (
        <div
          className="video-section"
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}
        >
          {/* AI interviewer (MuseTalk video) */}
          <video
            className="video-player"
            src={aiVideoUrl || undefined}
            autoPlay
            playsInline
            muted
            loop
            style={{ background: '#000' }}
          />

          {/* User webcam */}
          <video
            ref={videoRef}
            className="video-player"
            autoPlay
            playsInline
            muted
            style={{
              transform: 'scaleX(-1)',
              background: '#000'
            }}
          />
        </div>
      )}

      {/* Current question */}
      {!showWelcome && currentQuestion && (
        <div className="transcription">
          <strong>Current Question</strong>
          <p>{currentQuestion}</p>
        </div>
      )}

      {/* Listening indicator */}
      {isListening && (
        <div className="listening-indicator">
          <div className="pulse" />
          <p className="listening-text">Listening... Speak now</p>
          <button
            onClick={stopListening}
            style={{
              marginTop: '12px',
              padding: '10px 20px',
              background: '#ef4444',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Stop & Submit
          </button>
        </div>
      )}

      {/* Transcription */}
      {transcription && (
        <div className="transcription">
          <strong>Your Answer</strong>
          <p>{transcription}</p>
        </div>
      )}

      {/* Evaluation */}
      {evaluation && (
        <div className="evaluation">
          <h3>Feedback</h3>
          <p>{evaluation}</p>
        </div>
      )}

      {/* Manual next button for testing */}
      {!isListening && transcription && questionCount < totalQuestions && (
        <button onClick={fetchFirstQuestion} className="btn-primary">
          Next Question
        </button>
      )}

      {/* Complete interview button */}
      {!isListening && transcription && questionCount >= totalQuestions && (
        <button onClick={fetchResults} className="btn-primary">
          Complete Interview
        </button>
      )}
    </div>
  )
}

// ===== RESULTS PAGE =====
export const ResultsPage: React.FC<{ interviewId: string; results: any }> = ({
  interviewId,
  results
}) => {
  const [loading, setLoading] = useState(!results)

  useEffect(() => {
    if (!results) {
      fetchResults()
    }
  }, [interviewId, results])

  const fetchResults = async () => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/interview/${interviewId}/results`
      )
      if (!response.ok) throw new Error('Failed to fetch results')
      setLoading(false)
    } catch (err) {
      console.error('Failed to load results:', err)
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>Loading results...</p>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="results-container">
        <h1>No results found</h1>
      </div>
    )
  }

  return (
    <div className="results-container">
      <h1>Interview Results</h1>

      <div className="score-card">
        <div className="score-label">Overall Score</div>
        <div className="score-value">{results.overall_score || 0}/100</div>
        <div className="recommendation">{results.recommendation || 'Great effort!'}</div>
      </div>

      {results.breakdown && (
        <div className="breakdown">
          <h3>Performance Breakdown</h3>
          {Object.entries(results.breakdown).map(([key, value]: [string, any]) => (
            <div key={key} className="breakdown-item">
              <strong>{key}</strong>
              <p>{value}</p>
            </div>
          ))}
        </div>
      )}

      {results.strengths && results.weaknesses && (
        <div className="strengths-weaknesses">
          <div className="strength-card">
            <h3>Strengths</h3>
            <ul>
              {results.strengths.map((strength: string, idx: number) => (
                <li key={idx}>{strength}</li>
              ))}
            </ul>
          </div>
          <div className="weakness-card">
            <h3>Areas to Improve</h3>
            <ul>
              {results.weaknesses.map((weakness: string, idx: number) => (
                <li key={idx}>{weakness}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <button
        onClick={() => {
          window.location.reload()
        }}
        className="download-btn"
      >
        Start New Interview
      </button>
    </div>
  )
}

// ===== MAIN APP COMPONENT =====
export default function App() {
  const [page, setPage] = useState<'setup' | 'interview' | 'results'>('setup')
  const [interviewData, setInterviewData] = useState<any>(null)

  const handleSetupComplete = (data: any) => {
    // Defensive mapping to avoid undefined interviewId
    const interviewId = data.interview_id || data.id || data.interviewId
    const candidateName = data.candidate_name || data.name

    if (!interviewId) {
      console.error('Missing interview_id in setup response', data)
      alert('Setup API did not return an interview_id. Check backend response.')
      return
    }

    const normalized = {
      ...data,
      interview_id: interviewId,
      candidate_name: candidateName
    }

    setInterviewData(normalized)
    setPage('interview')
  }

  const handleInterviewComplete = (results: any) => {
    setInterviewData((prev: any) => ({
      ...prev,
      results
    }))
    setPage('results')
  }

  return (
    <div className="app">
      {page === 'setup' && <SetupPage onStart={handleSetupComplete} />}
      {page === 'interview' && interviewData && (
        <InterviewPage
          interviewId={interviewData.interview_id}
          candidateName={interviewData.candidate_name}
          onComplete={handleInterviewComplete}
        />
      )}
      {page === 'results' && (
        <ResultsPage interviewId={interviewData.interview_id} results={interviewData.results} />
      )}
    </div>
  )
}
