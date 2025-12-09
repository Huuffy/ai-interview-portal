import React from 'react'

// ===== VIDEO PLAYER =====
export const VideoPlayer: React.FC<{ src: string; onEnded: () => void }> = ({ src, onEnded }) => {
  return (
    <div className="video-player">
      <video
        src={src}
        autoPlay
        onEnded={onEnded}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  )
}

// ===== TIMER =====
export const Timer: React.FC<{ remaining: number; total: number }> = ({ remaining, total }) => {
  const minutes = Math.floor(remaining / 60)
  const seconds = remaining % 60
  const percentage = (remaining / total) * 100

  return (
    <div className="timer">
      <div className="timer-text">
        ⏱️ Time Remaining: {minutes}:{seconds.toString().padStart(2, '0')}
      </div>
      <div className="progress-bar" style={{ width: '200px' }}>
        <div className="progress-fill" style={{ width: `${percentage}%` }} />
      </div>
    </div>
  )
}

// ===== TRANSCRIPTION =====
export const Transcription: React.FC<{ text: string }> = ({ text }) => {
  return (
    <div className="transcription">
      <strong>📝 Your Response:</strong>
      <p>{text || 'Listening for your response...'}</p>
    </div>
  )
}

// ===== RESULTS =====
export const Results: React.FC<{ data: any }> = ({ data }) => {
  return (
    <div className="results-container">
      <h1>Interview Results</h1>

      <div className="score">
        <h2>{data.overall_score}/10</h2>
        <p className="recommendation">{data.recommendation}</p>
      </div>

      <div className="breakdown">
        <h3>📊 Q&A Breakdown</h3>
        {data.breakdown?.map((item: any, idx: number) => (
          <div key={idx} className="breakdown-item">
            <p>
              <strong>Q{idx + 1}: {item.question}</strong>
            </p>
            <p>Score: {item.marks}</p>
            <p>{item.feedback}</p>
          </div>
        ))}
      </div>

      <div className="strengths-weaknesses">
        <div className="strengths">
          <h3>💪 Strengths</h3>
          <ul>
            {data.strengths?.map((s: string, idx: number) => (
              <li key={idx}>{s}</li>
            ))}
          </ul>
        </div>
        <div className="weaknesses">
          <h3>📈 Areas to Improve</h3>
          <ul>
            {data.weaknesses?.map((w: string, idx: number) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      </div>

      <button
        onClick={() => {
          window.location.href = `${import.meta.env.VITE_API_URL}/api/interview/download-report`
        }}
      >
        📥 Download Report
      </button>
    </div>
  )
}

// ===== LOADING SPINNER =====
export const Loading: React.FC = () => {
  return (
    <div style={{ textAlign: 'center', padding: '40px' }}>
      <div
        style={{
          display: 'inline-block',
          width: '40px',
          height: '40px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #667eea',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }}
      />
      <p style={{ marginTop: '20px', color: '#666' }}>Loading...</p>
    </div>
  )
}

// ===== ERROR DISPLAY =====
export const Error: React.FC<{ message: string }> = ({ message }) => {
  return (
    <div
      style={{
        background: '#ffebee',
        border: '2px solid #f44336',
        padding: '15px',
        borderRadius: '8px',
        color: '#c62828',
      }}
    >
      ❌ {message}
    </div>
  )
}
