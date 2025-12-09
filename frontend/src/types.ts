export interface InterviewSetupRequest {
  job_description: string
  candidate_name: string
  duration_minutes: number
  avatar_image_url?: string
}

export interface InterviewSetupResponse {
  session_id: string
  ws_url: string
  message: string
}

export interface EvaluationResult {
  score: number
  marks: string
  correctness: string
  relatedness: number
  depth: string
  next_question_type: string
  feedback: string
  confidence: number
}

export interface BreakdownItem {
  question: string
  score: number
  marks: string
  feedback: string
}

export interface InterviewResults {
  overall_score: number
  recommendation: string
  breakdown: BreakdownItem[]
  strengths: string[]
  weaknesses: string[]
}

export interface WebSocketMessage {
  type:
    | 'ready'
    | 'audio_chunk'
    | 'audio_end'
    | 'greeting_complete'
    | 'listening_start'
    | 'greeting_video'
    | 'question_video'
    | 'transcription_partial'
    | 'evaluation'
    | 'closing_video'
    | 'results'
    | 'error'
  [key: string]: any
}
