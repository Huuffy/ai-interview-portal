import React, { useState, useEffect, useRef } from 'react';

// ===== SETUP PAGE =====
export const SetupPage: React.FC<{
  onStart: (data: any) => void;
}> = ({ onStart }) => {
  const [jobDesc, setJobDesc] = useState('');
  const [name, setName] = useState('');
  // --- FIX 1: Rename state variable ---
  const [questionCount, setQuestionCount] = useState(5); 
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
          // --- FIX 2: Send correct key and variable ---
          question_count: questionCount, 
        }),
      });

      if (!response.ok) throw new Error('Failed to start interview');

      const data = await response.json();
      onStart(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ /* ... container styles ... */ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--color-background)' }}>
      <div style={{ /* ... card styles ... */ maxWidth: '600px', width: '100%', backgroundColor: 'var(--color-surface)', padding: '24px', borderRadius: '12px' }}>
        <h1 style={{ textAlign: 'center', color: 'var(--color-text)' }}>🎯 Interview Setup</h1>
        
        {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}

        <form onSubmit={handleStart}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', color: 'var(--color-text)' }}>Job Description</label>
            <textarea
              value={jobDesc}
              onChange={(e) => setJobDesc(e.target.value)}
              style={{ width: '100%', padding: '12px', borderRadius: '8px' }}
              required
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', color: 'var(--color-text)' }}>Your Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ width: '100%', padding: '12px', borderRadius: '8px' }}
              required
            />
          </div>

          {/* --- FIX 3: Updated Input Label and Value binding --- */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', color: 'var(--color-text)' }}>Number of Questions</label>
            <input
              type="number"
              value={questionCount}
              onChange={(e) => setQuestionCount(parseInt(e.target.value))}
              min="1"
              max="10"
              style={{ width: '100%', padding: '12px', borderRadius: '8px' }}
            />
          </div>

          <button type="submit" disabled={loading} style={{ width: '100%', padding: '12px', backgroundColor: 'var(--color-primary)', color: 'white', borderRadius: '8px', border: 'none' }}>
            {loading ? 'Starting...' : 'Start Interview'}
          </button>
        </form>
      </div>
    </div>
  );
};

// ===== CAMERA PERMISSION PAGE =====
export const CameraPermissionPage: React.FC<{
  onApprove: () => void;
}> = ({ onApprove }) => {
  const [cameraReady, setCameraReady] = useState(false);
  const [micReady, setMicReady] = useState(false);
  const [error, setError] = useState('');
  const [permissionDenied, setPermissionDenied] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    console.log('[Permission] Checking permissions...');
    
    const checkPermissions = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: true,
        });

        console.log('[Permission] Stream acquired successfully');

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(e => console.log('[Permission] Autoplay:', e));
        }

        setCameraReady(true);
        setMicReady(true);
        setError('');
        setPermissionDenied(false);

      } catch (err: any) {
        const errorName = err.name;
        const errorMsg = err.message;

        console.error('[Permission] Error:', errorName, errorMsg);

        if (errorName === 'NotAllowedError' || errorName === 'PermissionDeniedError') {
          setError('❌ Camera/microphone permission denied');
          setPermissionDenied(true);
        } else if (errorName === 'NotFoundError') {
          setError('❌ No camera/microphone found');
        } else if (errorName === 'NotReadableError') {
          setError('❌ Camera/microphone already in use');
        } else if (errorName === 'SecurityError') {
          setError('❌ Secure context required');
        } else {
          setError(`❌ Error: ${errorMsg}`);
        }

        setCameraReady(false);
        setMicReady(false);
      }
    };

    checkPermissions();

    return () => {
      if (videoRef.current?.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      backgroundColor: 'var(--color-background)'
    }}>
      <div style={{
        maxWidth: '600px',
        width: '100%',
        backgroundColor: 'var(--color-surface)',
        borderRadius: '12px',
        border: '1px solid var(--color-card-border)',
        boxShadow: 'var(--shadow-sm)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '24px',
          borderBottom: '1px solid var(--color-card-border-inner)',
          textAlign: 'center'
        }}>
          <h2 style={{
            fontSize: '20px',
            fontWeight: '600',
            margin: '0 0 8px 0',
            color: 'var(--color-text)'
          }}>📷 Camera & Microphone Required</h2>
          <p style={{
            fontSize: '14px',
            color: 'var(--color-text-secondary)',
            margin: 0
          }}>We need access to your camera and microphone</p>
        </div>

        {/* Error Banner */}
        {error && (
          <div style={{
            margin: '20px',
            padding: '12px 16px',
            backgroundColor: 'rgba(255, 84, 89, 0.15)',
            color: 'var(--color-error)',
            borderRadius: '8px',
            border: '1px solid rgba(255, 84, 89, 0.25)',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        {/* Content */}
        <div style={{ padding: '24px' }}>
          {/* Video Preview */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{
              width: '100%',
              borderRadius: '8px',
              backgroundColor: 'var(--color-charcoal-700)',
              marginBottom: '20px',
              aspectRatio: '16 / 9'
            }}
          />

          {/* Status */}
          <div style={{
            display: 'flex',
            gap: '16px',
            marginBottom: '24px',
            padding: '16px',
            backgroundColor: 'rgba(50, 184, 198, 0.1)',
            borderRadius: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
              <span style={{ fontSize: '20px' }}>{cameraReady ? '✅' : '⏳'}</span>
              <span style={{ fontSize: '14px', color: 'var(--color-text)' }}>
                Camera: {cameraReady ? 'Ready' : 'Checking...'}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
              <span style={{ fontSize: '20px' }}>{micReady ? '✅' : '⏳'}</span>
              <span style={{ fontSize: '14px', color: 'var(--color-text)' }}>
                Microphone: {micReady ? 'Ready' : 'Checking...'}
              </span>
            </div>
          </div>

          {/* Continue Button */}
          <button
            onClick={onApprove}
            disabled={!cameraReady || !micReady}
            style={{
              width: '100%',
              padding: '12px 24px',
              backgroundColor: !cameraReady || !micReady ? 'rgba(50, 184, 198, 0.5)' : 'var(--color-primary)',
              color: 'var(--color-btn-primary-text)',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: !cameraReady || !micReady ? 'not-allowed' : 'pointer',
              transition: 'all 150ms ease',
              opacity: !cameraReady || !micReady ? 0.5 : 1,
              marginBottom: '16px'
            }}
          >
            {cameraReady && micReady ? '✓ Continue to Interview' : 'Waiting for permissions...'}
          </button>

          {/* Help Text */}
          {permissionDenied && (
            <div style={{
              marginTop: '16px',
              padding: '12px 16px',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderRadius: '8px',
              fontSize: '12px',
              color: 'var(--color-text)'
            }}>
              <strong>How to fix:</strong>
              <ol style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                <li>Refresh this page (Ctrl+R)</li>
                <li>When browser asks, click "Allow"</li>
                <li>Check browser settings if blocked</li>
              </ol>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ===== INTERVIEW PAGE =====
export const InterviewPage: React.FC<{
  sessionId: string;
  wsUrl: string;
  onComplete?: (results: any) => void;
}> = ({ sessionId, wsUrl, onComplete }) => {
  const [currentQuestion, setCurrentQuestion] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [questionText, setQuestionText] = useState('Waiting for question...');
  const [transcription, setTranscription] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isInputAllowed, setIsInputAllowed] = useState(false);
  const [error, setError] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [aiVideoUrl, setAiVideoUrl] = useState('');
  const [aiVideoError, setAiVideoError] = useState(false);
  const isConnecting = useRef(false);
  const socketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const userVideoRef = useRef<HTMLVideoElement>(null);
  const aiVideoRef = useRef<HTMLVideoElement>(null);
  const userStreamRef = useRef<MediaStream | null>(null);

  const getFullVideoUrl = (relativePath: string): string => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const baseUrl = new URL(apiUrl).origin;
    
    if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
      return relativePath;
    }
    
    return `${baseUrl}${relativePath}`;
  };

  // Setup user video
  useEffect(() => {
    const setupUserVideo = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { width: { ideal: 1280 }, height: { ideal: 720 } }, 
          audio: false 
        });
        
        if (userVideoRef.current) {
          userVideoRef.current.srcObject = stream;
          userVideoRef.current.play().catch(e => console.log('[Interview] Autoplay:', e));
        }
        userStreamRef.current = stream;
      } catch (err) {
        console.error('[Interview] User video error:', err);
      }
    };

    setupUserVideo();

    return () => {
      if (userStreamRef.current) {
        userStreamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  //WebSocket connection
  useEffect(() => {
    // [NEW] CHECK: If already connecting, STOP immediately
    if (isConnecting.current) {
        console.log('[Interview] Skipping double connection attempt');
        return;
    }

    let fixedUrl = wsUrl.replace('0.0.0.0', 'localhost');
    if (!fixedUrl.includes(':8000')) {
      fixedUrl = fixedUrl.replace('ws://localhost/', 'ws://localhost:8000/');
    }
    
    console.log('[Interview] Connecting to WebSocket:', fixedUrl);
    setConnectionStatus('Connecting...');
    
    // [NEW] LOCK: Set connecting to true
    isConnecting.current = true;

    try {
      const socket = new WebSocket(fixedUrl);

      socket.onopen = () => {
        console.log('[Interview] WebSocket connected');
        socketRef.current = socket;
        setConnectionStatus('Connected ✅');
        setError('');
        socket.send(JSON.stringify({ type: 'ready' }));
      };

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('[Interview] Message:', message.type);

          if (message.type === 'greeting_video') {
            setAiVideoUrl(getFullVideoUrl(message.video_url));
            setQuestionText('Welcome! Let\'s begin.');
            } 
          else if (message.type === 'question_video') {
            setAiVideoUrl(getFullVideoUrl(message.video_url));
            setCurrentQuestion(message.question_index);
            setQuestionText(message.question_text);
            setIsInputAllowed(false);
            if (isRecording) stopRecording();
          } 
          else if (message.type === 'start_listening') {
             console.log('[Interview] AI is listening...');
             if (message.video_url) {
                setAiVideoUrl(getFullVideoUrl(message.video_url));
                if (aiVideoRef.current) aiVideoRef.current.loop = true;
            }
            setIsInputAllowed(true);
          }
          else if (message.type === 'results') {
             if (onComplete) onComplete(message);
          }
          
        } catch (e) {
          console.error('[Interview] Error:', e);
        }
      };

      socket.onerror = (err) => {
        console.error('[Interview] WebSocket error:', err);
        setError('WebSocket connection failed');
        setConnectionStatus('Error ❌');
        isConnecting.current = false; // Reset lock on error
      };

      socket.onclose = () => {
        console.log('[Interview] WebSocket closed');
        socketRef.current = null;
        setConnectionStatus('Disconnected');
        isConnecting.current = false; // Reset lock on close
      };

    } catch (e) {
      console.error('[Interview] Connection error:', e);
      setError('Failed to connect');
      setConnectionStatus('Error ❌');
      isConnecting.current = false;
    }

    // Cleanup
    return () => {
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.close();
      }
      isConnecting.current = false;
    };
  }, [wsUrl, onComplete]);

  const startRecording = async () => {
    if (!isInputAllowed) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Create blob from collected chunks
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        
        console.log(`[Interview] Sending audio: ${audioBlob.size} bytes`); // Debug log
        
        if (socketRef.current?.readyState === WebSocket.OPEN) {
          // Send the Blob directly
          socketRef.current.send(audioBlob);
          // Send the 'audio_end' signal strictly AFTER the blob
          setTimeout(() => {
             socketRef.current?.send(JSON.stringify({ type: 'audio_end' }));
          }, 100);
        }
        stream.getTracks().forEach(track => track.stop());
      };

      // Request data every 1 second to ensure chunks are captured
      mediaRecorder.start(1000); 
      setIsRecording(true);
      console.log('[Interview] Recording started');
    } catch (e) {
      console.error('[Interview] Recording error:', e);
      setError('Could not start recording');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsInputAllowed(false);
      // Removed the manual 'audio_end' sending here because we moved it to onstop
      // to ensure it happens after the data is sent.
      
      if (aiVideoRef.current) aiVideoRef.current.loop = false;
    }
  };
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--color-background)',
      padding: '20px',
      color: 'var(--color-text)'
    }}>
      {/* Status Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        padding: '12px 20px',
        backgroundColor: 'var(--color-surface)',
        borderRadius: '8px',
        fontSize: '14px'
      }}>
        <span>Status: <strong>{connectionStatus}</strong></span>
        {error && <span style={{ color: 'var(--color-error)' }}>⚠️ {error}</span>}
      </div>

      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Video Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '20px',
          marginBottom: '24px'
        }}>
          {/* AI Interviewer */}
          <div>
            <div style={{ fontSize: '12px', fontWeight: '550', marginBottom: '8px' }}>AI Interviewer</div>
            <div style={{
              width: '100%',
              aspectRatio: '16 / 9',
              backgroundColor: 'var(--color-charcoal-700)',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              {aiVideoError ? (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  background: 'rgba(50, 184, 198, 0.1)',
                  flexDirection: 'column',
                  gap: '16px'
                }}>
                  <div style={{ fontSize: '24px' }}>⚠️ Video Error</div>
                  <div style={{ fontSize: '12px', color: 'rgba(245, 245, 245, 0.7)' }}>
                    {aiVideoUrl || 'No video URL'}
                  </div>
                </div>
              ) : aiVideoUrl ? (
                <video
                  ref={aiVideoRef}
                  src={aiVideoUrl}
                  controls
                  autoPlay
                  onError={() => {
                    console.error('[Interview] Video error:', aiVideoUrl);
                    setAiVideoError(true);
                  }}
                  onLoadedData={() => {
                    console.log('[Interview] Video loaded');
                    setAiVideoError(false);
                  }}
                  style={{
                    width: '100%',
                    height: '100%'
                  }}
                />
              ) : (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%'
                }}>
                  <div style={{ color: 'rgba(245, 245, 245, 0.5)' }}>
                    🎬 Loading video...
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* User Camera */}
          <div>
            <div style={{ fontSize: '12px', fontWeight: '550', marginBottom: '8px' }}>You</div>
            <div style={{
              width: '100%',
              aspectRatio: '16 / 9',
              backgroundColor: 'var(--color-charcoal-700)',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <video
                ref={userVideoRef}
                autoPlay
                playsInline
                muted
                style={{
                  width: '100%',
                  height: '100%',
                  transform: 'scaleX(-1)'
                }}
              />
            </div>
          </div>
        </div>

        {/* Question Section */}
        <div style={{
          backgroundColor: 'var(--color-surface)',
          borderRadius: '12px',
          border: '1px solid var(--color-card-border)',
          padding: '24px'
        }}>
          {/* Question Header */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '20px',
            paddingBottom: '12px',
            borderBottom: '1px solid var(--color-border)'
          }}>
            <span style={{ fontSize: '12px', fontWeight: '550' }}>
              Question {currentQuestion} of {totalQuestions}
            </span>
            <span style={{ display: 'flex', gap: '4px' }}>
              {Array(totalQuestions).fill(0).map((_, i) => (
                <span
                  key={i}
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: i < currentQuestion ? 'var(--color-primary)' : 'var(--color-gray-300)',
                    transition: 'all 150ms ease'
                  }}
                />
              ))}
            </span>
          </div>

          {/* Question Text */}
          <div style={{
            backgroundColor: 'var(--color-secondary)',
            padding: '20px',
            borderRadius: '8px',
            marginBottom: '20px',
            border: '1px solid var(--color-border)'
          }}>
            <p style={{
              fontSize: '16px',
              margin: 0,
              lineHeight: '1.5',
              color: 'var(--color-text)'
            }}>{questionText}</p>
          </div>

          {/* Transcription */}
          {transcription && (
            <div style={{
              backgroundColor: 'rgba(50, 184, 198, 0.1)',
              padding: '16px',
              borderRadius: '8px',
              marginBottom: '20px',
              border: '1px solid rgba(50, 184, 198, 0.25)'
            }}>
              <strong style={{ color: 'var(--color-success)' }}>Your Response:</strong>
              <p style={{
                fontSize: '14px',
                margin: '8px 0 0 0',
                color: 'var(--color-text-secondary)',
                lineHeight: '1.5'
              }}>{transcription}</p>
            </div>
          )}

          {/* Controls */}
          <div style={{ display: 'flex', gap: '12px' }}>
            {!isRecording ? (
              <button
                onClick={startRecording}
                disabled={!isInputAllowed}
                style={{
                  padding: '12px 24px',
                  backgroundColor: isInputAllowed ? 'var(--color-primary)' : 'var(--color-gray-300)',
                  color: 'var(--color-btn-primary-text)',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: isInputAllowed ? 'pointer' : 'not-allowed',
                  transition: 'all 150ms ease',
                  opacity: isInputAllowed ? 1 : 0.6
                }}
              >
                {isInputAllowed ? '🎤 Speak' : '✋ wait'}
              </button>
            ) : (
              <button
                onClick={stopRecording}
                style={{
                  padding: '12px 24px',
                  backgroundColor: 'var(--color-error)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'all 150ms ease'
                }}
              >
                ⏹️ Stop Recording
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// ===== RESULTS PAGE =====
export const ResultsPage: React.FC<{
  results: any;
}> = ({ results }) => {
  if (!results || !results.evaluations) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        backgroundColor: 'var(--color-background)'
      }}>
        <div style={{
          maxWidth: '600px',
          width: '100%',
          backgroundColor: 'var(--color-surface)',
          borderRadius: '12px',
          border: '1px solid var(--color-card-border)',
          padding: '24px',
          textAlign: 'center'
        }}>
          <h2 style={{ color: 'var(--color-text)' }}>📊 Interview Results</h2>
          <p style={{ color: 'var(--color-text-secondary)' }}>No results found</p>
        </div>
      </div>
    );
  }

  const totalScore = results.evaluations.reduce((sum: number, item: any) => sum + (item.score || 0), 0);
  const avgScore = (totalScore / results.evaluations.length).toFixed(1);

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--color-background)',
      padding: '20px',
      color: 'var(--color-text)'
    }}>
      <div style={{ maxWidth: '600px', margin: '0 auto' }}>
        <div style={{
          backgroundColor: 'var(--color-surface)',
          borderRadius: '12px',
          border: '1px solid var(--color-card-border)',
          overflow: 'hidden'
        }}>
          {/* Header */}
          <div style={{
            padding: '24px',
            borderBottom: '1px solid var(--color-card-border-inner)',
            textAlign: 'center'
          }}>
            <h2 style={{
              fontSize: '20px',
              fontWeight: '600',
              margin: '0 0 16px 0',
              color: 'var(--color-text)'
            }}>📊 Your Interview Results</h2>
            <div style={{
              fontSize: '12px',
              color: 'var(--color-text-secondary)',
              marginBottom: '8px'
            }}>Overall Score:</div>
            <div style={{
              fontSize: '30px',
              fontWeight: '600',
              color: 'var(--color-primary)'
            }}>{avgScore}/10</div>
          </div>

          {/* Results List */}
          <div style={{ padding: '24px' }}>
            {results.evaluations.map((item: any, index: number) => (
              <div
                key={index}
                style={{
                  padding: '16px',
                  backgroundColor: 'var(--color-secondary)',
                  borderRadius: '8px',
                  marginBottom: index < results.evaluations.length - 1 ? '16px' : 0,
                  border: '1px solid var(--color-border)'
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px'
                }}>
                  <span style={{ fontSize: '12px', fontWeight: '550' }}>
                    Question {index + 1}
                  </span>
                  <span
                    style={{
                      padding: '4px 12px',
                      borderRadius: '6px',
                      color: 'white',
                      fontSize: '12px',
                      fontWeight: '550',
                      background: item.marks >= 7 ? 'var(--color-primary)' : 
                                  item.marks >= 5 ? 'var(--color-warning)' : 
                                  'var(--color-error)'
                    }}
                  >
                    {item.marks}/10
                  </span>
                </div>
                <p style={{
                  fontSize: '12px',
                  color: 'var(--color-text-secondary)',
                  margin: 0,
                  lineHeight: '1.5'
                }}>
                  {item.feedback}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
