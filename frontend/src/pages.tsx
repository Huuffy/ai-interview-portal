import React, { useState, useEffect, useRef } from 'react';

// ===== SETUP PAGE =====
export const SetupPage: React.FC<{
  onStart: (data: any) => void;
}> = ({ onStart }) => {
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

      if (!response.ok) throw new Error('Failed to start interview');

      const data = await response.json();
      console.log('[Setup] Response:', data);
      onStart(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
      console.error('[Setup] Error:', err);
    } finally {
      setLoading(false);
    }
  };

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
          <h1 style={{
            fontSize: '24px',
            fontWeight: '600',
            margin: '0 0 8px 0',
            color: 'var(--color-text)'
          }}>🎯 Interview Setup</h1>
          <p style={{
            fontSize: '14px',
            color: 'var(--color-text-secondary)',
            margin: 0
          }}>Prepare for your interview with AI guidance</p>
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
            ⚠️ {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleStart} style={{ padding: '24px' }}>
          {/* Job Description */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontWeight: '550',
              fontSize: '12px',
              color: 'var(--color-text)'
            }}>Job Description</label>
            <textarea
              value={jobDesc}
              onChange={(e) => setJobDesc(e.target.value)}
              placeholder="Describe the job role..."
              rows={4}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid var(--color-border)',
                borderRadius: '8px',
                fontFamily: 'inherit',
                fontSize: '14px',
                color: 'var(--color-text)',
                backgroundColor: 'var(--color-surface)',
                resize: 'vertical'
              }}
              required
            />
          </div>

          {/* Name */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontWeight: '550',
              fontSize: '12px',
              color: 'var(--color-text)'
            }}>Your Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your full name"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid var(--color-border)',
                borderRadius: '8px',
                fontFamily: 'inherit',
                fontSize: '14px',
                color: 'var(--color-text)',
                backgroundColor: 'var(--color-surface)',
                boxSizing: 'border-box'
              }}
              required
            />
          </div>

          {/* Duration */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontWeight: '550',
              fontSize: '12px',
              color: 'var(--color-text)'
            }}>Interview Duration (minutes)</label>
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value))}
              min="1"
              max="30"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid var(--color-border)',
                borderRadius: '8px',
                fontFamily: 'inherit',
                fontSize: '14px',
                color: 'var(--color-text)',
                backgroundColor: 'var(--color-surface)',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px 24px',
              backgroundColor: loading ? 'rgba(50, 184, 198, 0.5)' : 'var(--color-primary)',
              color: 'var(--color-btn-primary-text)',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 150ms ease',
              opacity: loading ? 0.6 : 1
            }}
          >
            {loading ? '⏳ Starting...' : '▶️ Start Interview'}
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
  const [error, setError] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [aiVideoUrl, setAiVideoUrl] = useState('');
  const [aiVideoError, setAiVideoError] = useState(false);
  
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

  // WebSocket connection
  useEffect(() => {
    let fixedUrl = wsUrl.replace('0.0.0.0', 'localhost');
    if (!fixedUrl.includes(':8000')) {
      fixedUrl = fixedUrl.replace('ws://localhost/', 'ws://localhost:8000/');
    }
    
    console.log('[Interview] Connecting to WebSocket:', fixedUrl);
    setConnectionStatus('Connecting...');

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
            const fullUrl = getFullVideoUrl(message.video_url);
            console.log('[Interview] Setting greeting video:', fullUrl);
            setAiVideoUrl(fullUrl);
            setQuestionText('Welcome! Let\'s begin the interview.');
          } else if (message.type === 'question_video') {
            const fullUrl = getFullVideoUrl(message.video_url);
            console.log('[Interview] Setting question video:', fullUrl);
            setAiVideoUrl(fullUrl);
            setCurrentQuestion(message.question_index || 1);
            setQuestionText(message.question_text || `Question ${message.question_index}`);
            setTranscription('');
          } else if (message.type === 'transcription_partial') {
            setTranscription(message.text || '');
          } else if (message.type === 'results') {
            console.log('[Interview] Results received');
            if (onComplete) onComplete(message);
          } else if (message.type === 'error') {
            setError(message.message || 'Server error');
          }
        } catch (e) {
          console.error('[Interview] Message parse error:', e);
        }
      };

      socket.onerror = (err) => {
        console.error('[Interview] WebSocket error:', err);
        setError('WebSocket connection failed');
        setConnectionStatus('Error ❌');
      };

      socket.onclose = () => {
        console.log('[Interview] WebSocket closed');
        socketRef.current = null;
        setConnectionStatus('Disconnected');
      };

      return () => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
          socketRef.current.close();
        }
      };
    } catch (e) {
      console.error('[Interview] Connection error:', e);
      setError('Failed to connect');
      setConnectionStatus('Error ❌');
    }
  }, [wsUrl, onComplete]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        if (socketRef.current?.readyState === WebSocket.OPEN) {
          socketRef.current.send(audioBlob);
        }
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      console.log('[Interview] Recording started');
    } catch (e) {
      console.error('[Interview] Recording error:', e);
      setError('Could not start recording');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      console.log('[Interview] Recording stopped');
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
                style={{
                  padding: '12px 24px',
                  backgroundColor: 'var(--color-primary)',
                  color: 'var(--color-btn-primary-text)',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'all 150ms ease'
                }}
              >
                🎤 Start Recording
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

  const totalScore = results.evaluations.reduce((sum: number, item: any) => sum + (item.marks || 0), 0);
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
