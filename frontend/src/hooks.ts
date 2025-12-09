import { useState, useEffect, useRef } from 'react'
import { connectWebSocket } from './services'

export const useWebSocket = (url: string) => {
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    const socket = new WebSocket(url)

    socket.onopen = () => {
      setWs(socket)
      setIsConnected(true)
    }

    socket.onerror = () => {
      setIsConnected(false)
    }

    socket.onclose = () => {
      setIsConnected(false)
    }

    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close()
      }
    }
  }, [url])

  return ws
}

export const useTimer = (initialSeconds: number) => {
  const [remaining, setRemaining] = useState(initialSeconds)

  useEffect(() => {
    const interval = setInterval(() => {
      setRemaining((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  return { remaining, total: initialSeconds }
}

export const useAudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false)
  const [audioData, setAudioData] = useState<Uint8Array[]>([])
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)

      const chunks: BlobPart[] = []

      mediaRecorder.ondataavailable = (event) => {
        chunks.push(event.data)
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/wav' })
        const reader = new FileReader()
        reader.onloadend = () => {
          const uint8Array = new Uint8Array(reader.result as ArrayBuffer)
          setAudioData((prev) => [...prev, uint8Array])
        }
        reader.readAsArrayBuffer(blob)
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start()
      setIsRecording(true)
    } catch (err) {
      console.error('Microphone error:', err)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop())
      setIsRecording(false)
    }
  }

  return { isRecording, audioData, startRecording, stopRecording }
}

export const useInterview = (sessionId: string) => {
  const [state, setState] = useState<'setup' | 'interview' | 'results'>('setup')
  const [data, setData] = useState<any>(null)

  return { state, setState, data, setData }
}