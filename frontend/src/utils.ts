export const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export const formatScore = (score: number): string => {
  return `${score.toFixed(1)}/10`
}

export const getRecommendationColor = (recommendation: string): string => {
  switch (recommendation) {
    case 'STRONG HIRE':
      return '#4caf50'
    case 'HIRE':
      return '#2196f3'
    case 'CONSIDER':
      return '#ff9800'
    case 'HESITANT':
      return '#ff5722'
    case 'NO HIRE':
      return '#f44336'
    default:
      return '#999'
  }
}

export const API_ENDPOINTS = {
  SETUP: '/api/interview/setup',
  RESULTS: '/api/interview/:id/results',
  DOWNLOAD: '/api/interview/:id/download-report',
  HEALTH: '/api/health',
}

export const MESSAGE_TYPES = {
  READY: 'ready',
  AUDIO_CHUNK: 'audio_chunk',
  AUDIO_END: 'audio_end',
  GREETING_COMPLETE: 'greeting_complete',
  LISTENING_START: 'listening_start',
  GREETING_VIDEO: 'greeting_video',
  QUESTION_VIDEO: 'question_video',
  TRANSCRIPTION_PARTIAL: 'transcription_partial',
  EVALUATION: 'evaluation',
  CLOSING_VIDEO: 'closing_video',
  RESULTS: 'results',
  ERROR: 'error',
}
