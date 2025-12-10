import React, { useState, useEffect, useRef } from 'react';

// ===== SETUP PAGE =====
export const SetupPage: React.FC<{ onStart: (data: any) => void }> = ({ onStart }) => {
  const [jobDesc, setJobDesc] = useState('');
  const [name, setName] = useState('');
  const [duration, setDuration] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!jobDesc.trim() || !name.trim()) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/interview/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_description: jobDesc,
          candidate_name: name,
          duration_minutes: duration,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start interview');
      }

      const data = await response.json();
      onStart(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="setup-container">
      <div className="setup-card">
        <h1>AI Interview Practice</h1>
        <p>Prepare for your interview with AI guidance</p>

        <form onSubmit={handleStart}>
          <div className="form-group">
            <label>Your Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., John Doe"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>Job Description</label>
            <textarea
              value={jobDesc}
              onChange={(e) => setJobDesc(e.target.value)}
              placeholder="e.g., Senior Frontend Engineer..."
              rows={4}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>Interview Duration (minutes)</label>
            <select
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value))}
              disabled={loading}
            >
              {[3, 5, 10, 15].map((min) => (
                <option key={min} value={min}>
                  {min} minutes
                </option>
              ))}
            </select>
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Starting Interview...' : 'Start Interview'}
          </button>
        </form>
      </div>
    </div>
  );
};

// ===== CAMERA PERMISSION PAGE =====
export const CameraPermissionPage: React.FC<{ onApprove: () => void }> = ({ onApprove }) => {
  const [cameraReady, setCameraReady] = useState(false);
  const [micReady, setMicReady] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const requestPermissions = async () => {
      try {
        // Request both camera and microphone
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: { echoCancellation: true, noiseSuppression: true },
        });

        // Display camera preview
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setCameraReady(true);
          setMicReady(true);
        }
      } catch (err) {
        console.error('Permission denied:', err);
      }
    };

    requestPermissions();
  }, []);

  const handleApprove = () => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      // Stop preview stream
      stream.getTracks().forEach((track) => track.stop());
    }
    onApprove();
  };

  return (
    <div className="permission-container">
      <div className="permission-card">
        <h2>Camera & Microphone Permission</h2>
        <p>We need access to your camera and microphone for the interview.</p>

        <div className="preview-box">
          {cameraReady && micReady ? (
            <>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="preview-video"
              />
              <div className="status-indicators">
                <div className="status-item">
                  <span className="status-icon" style={{ color: 'green' }}>●</span>
                  Camera Ready
                </div>
                <div className="status-item">
                  <span className="status-icon" style={{ color: 'green' }}>●</span>
                  Microphone Ready
                </div>
              </div>
            </>
          ) : (
            <div className="status-waiting">
              <div className="spinner"></div>
              <p>Requesting permissions...</p>
            </div>
          )}
        </div>

        <button
          onClick={handleApprove}
          disabled={!cameraReady || !micReady}
          className="btn-primary"
        >
          Continue to Interview
        </button>
      </div>
    </div>
  );
};

// ===== INTERVIEW PAGE =====
export const InterviewPage: React.FC<{ sessionId: string; socket: WebSocket }> = ({
  sessionId,
  socket,
}) => {
  const [currentQuestion, setCurrentQuestion] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [aiVideoUrl, setAiVideoUrl] = useState('');
  const [userVideoStream, setUserVideoStream] = useState<MediaStream | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [evaluation, setEvaluation] = useState('');
  const [feedback, setFeedback] = useState('');
  const [phase, setPhase] = useState<'greeting' | 'question' | 'listening' | 'evaluation' | 'results'>('greeting');

  const userVideoRef = useRef<HTMLVideoElement>(null);
  const aiVideoRef = useRef<HTMLVideoElement>(null);
  const audioRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Setup user camera
  useEffect(() => {
    const setupCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: false, // Will capture audio separately
        });
        setUserVideoStream(stream);
        if (userVideoRef.current) {
          userVideoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error('Camera error:', err);
      }
    };

    setupCamera();

    return () => {
      if (userVideoStream) {
        userVideoStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // Setup WebSocket message handler
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      const message = JSON.parse(event.data);
      console.log('[Interview] WebSocket message:', message.type);

      switch (message.type) {
        case 'greeting_video':
          setPhase('greeting');
          setAiVideoUrl(message.video_url);
          break;

        case 'question_video':
          setPhase('question');
          setCurrentQuestion(message.question_index);
          setTotalQuestions(message.total_questions);
          setAiVideoUrl(message.video_url);
          break;

        case 'transcription_partial':
          setTranscription(message.text);
          break;

        case 'evaluation':
          setPhase('evaluation');
          setEvaluation(message.marks);
          setFeedback(message.feedback);
          break;

        case 'results':
          setPhase('results');
          // Store results for display
          console.log('Final results:', message);
          break;

        case 'error':
          console.error('Server error:', message.message);
          break;
      }
    };

    socket.addEventListener('message', handleMessage);
    return () => socket.removeEventListener('message', handleMessage);
  }, [socket]);

  // Start listening and recording audio
  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          // Send audio chunk to backend
          const reader = new FileReader();
          reader.onload = () => {
            socket.send(
              JSON.stringify({
                type: 'audio_chunk',
                data: reader.result,
              })
            );
          };
          reader.readAsArrayBuffer(event.data);
        }
      };

      mediaRecorder.start(100); // Send chunk every 100ms
      audioRecorderRef.current = mediaRecorder;
      setIsListening(true);
      setPhase('listening');

      // Notify backend we're listening
      socket.send(JSON.stringify({ type: 'listening_start' }));
    } catch (err) {
      console.error('Audio error:', err);
    }
  };

  const stopListening = () => {
    if (audioRecorderRef.current) {
      audioRecorderRef.current.stop();
      const stream = audioRecorderRef.current.stream;
      stream.getTracks().forEach((track: MediaStreamTrack) => track.stop());
      setIsListening(false);

      // Notify backend audio ended
      socket.send(JSON.stringify({ type: 'audio_end' }));
    }
  };

  const handleVideoEnd = () => {
    if (phase === 'greeting') {
      socket.send(JSON.stringify({ type: 'greeting_complete' }));
    } else if (phase === 'question') {
      startListening();
    } else if (phase === 'evaluation') {
      // Wait for next question
    }
  };

  return (
    <div className="interview-container">
      {/* AI Interviewer Video (left) */}
      <div className="video-section ai-video">
        <h3>AI Interviewer</h3>
        <video
          ref={aiVideoRef}
          src={aiVideoUrl}
          autoPlay
          onEnded={handleVideoEnd}
          className="video-player"
        />
      </div>

      {/* User Camera Video (right) */}
      <div className="video-section user-video">
        <h3>You</h3>
        <video
          ref={userVideoRef}
          autoPlay
          playsInline
          muted
          className="video-player"
        />
      </div>

      {/* Bottom Panel */}
      <div className="interview-panel">
        <div className="question-counter">
          Question {currentQuestion} of {totalQuestions}
        </div>

        {phase === 'question' && (
          <div className="transcription-area">
            <h4>Your Response:</h4>
            <p>{transcription || 'Listening...'}</p>
          </div>
        )}

        {phase === 'evaluation' && (
          <div className="evaluation-area">
            <div className="score">{evaluation}</div>
            <div className="feedback">{feedback}</div>
          </div>
        )}

        {phase === 'listening' && (
          <div className="listening-controls">
            <button onClick={stopListening} className="btn-stop">
              Stop Speaking
            </button>
            <div className="timer">30 seconds max</div>
          </div>
        )}

        {phase === 'results' && (
          <div className="results-summary">
            <h2>Interview Complete!</h2>
            <p>Check your results above.</p>
          </div>
        )}
      </div>
    </div>
  );
};

// ===== RESULTS PAGE =====
export const ResultsPage: React.FC<{ results: any }> = ({ results }) => {
  return (
    <div className="results-container">
      <div className="results-card">
        <h1>Interview Results</h1>

        <div className="score-display">
          <div className="overall-score">{results.overall_score}/10</div>
          <div className="recommendation">{results.recommendation}</div>
        </div>

        <div className="breakdown">
          <h3>Question Breakdown</h3>
          {results.breakdown?.map((item: any, idx: number) => (
            <div key={idx} className="result-item">
              <span>Question {idx + 1}:</span>
              <span className="marks">{item.marks}</span>
              <p>{item.feedback}</p>
            </div>
          ))}
        </div>

        <div className="strengths-weaknesses">
          <div className="strengths">
            <h4>Strengths</h4>
            <ul>
              {results.strengths?.map((s: string, i: number) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>

          <div className="weaknesses">
            <h4>Areas to Improve</h4>
            <ul>
              {results.weaknesses?.map((w: string, i: number) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        </div>

        <button className="btn-primary" onClick={() => window.location.reload()}>
          Practice Again
        </button>
      </div>
    </div>
  );
};
