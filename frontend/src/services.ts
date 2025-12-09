
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const setupInterview = async (data: {
  job_description: string
  candidate_name: string
  duration_minutes: number
  avatar_image_url?: string
}) => {
  const response = await fetch(`${API_URL}/api/interview/setup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return response.json()
}

export const getResults = async (interviewId: string) => {
  const response = await fetch(`${API_URL}/api/interview/${interviewId}/results`)
  return response.json()
}

export const connectWebSocket = (sessionId: string) => {
  const wsURL = API_URL.replace('http', 'ws')
  return new WebSocket(`${wsURL}/ws/interview/${sessionId}`)
}

export const downloadReport = async (interviewId: string) => {
  const response = await fetch(`${API_URL}/api/interview/${interviewId}/download-report`)
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `interview-report-${interviewId}.pdf`
  a.click()
}

export const healthCheck = async () => {
  const response = await fetch(`${API_URL}/api/health`)
  return response.json()
}
