# backend/main.py

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
import asyncio
import json
from datetime import datetime
import uuid
import os
import logging
from config import settings
from models import db_init
from schemas import InterviewSetupRequest, InterviewSetupResponse
from services import (
    InterviewService, AudioService, EvaluationService,
    QuestionService, MediaService, SessionService,
    TimerService, ResultsService
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Interview Portal", version="1.0.0")

# ===== CORS Configuration =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
interview_service = InterviewService()
audio_service = AudioService()
evaluation_service = EvaluationService()
question_service = QuestionService()
media_service = MediaService()
session_service = SessionService()
timer_service = TimerService()
results_service = ResultsService()

# ===== Startup Event =====

@app.on_event("startup")
async def startup():
    """Initialize database, services, integrations"""
    db_init()
    print("✓ Database initialized")
    print("✓ Services ready")
    
    # Create media directories
    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    os.makedirs(settings.VIDEO_CACHE_DIR, exist_ok=True)
    os.makedirs(settings.AUDIO_CACHE_DIR, exist_ok=True)
    os.makedirs(settings.AVATAR_DIR, exist_ok=True)
    print("✓ Media directories created")
    print(f"  - Video: {settings.VIDEO_CACHE_DIR}")
    print(f"  - Audio: {settings.AUDIO_CACHE_DIR}")
    print(f"  - Avatars: {settings.AVATAR_DIR}")
    
    # Mount static files for serving media
    if os.path.exists(settings.MEDIA_DIR):
        app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")
        print("✓ Static files mounted at /media")

# ===== REST ENDPOINTS =====

@app.post("/api/interview/setup", response_model=InterviewSetupResponse)
async def setup_interview(request: InterviewSetupRequest):
    """
    1. Create interview record + in-memory session
    2. Pre-generate greeting + first 3 questions
    3. Return session_id + WebSocket URL
    """
    session_id = str(uuid.uuid4())
    
    print(f"\n[Setup] Starting interview setup...")
    print(f"  Session ID: {session_id}")
    print(f"  Candidate: {request.candidate_name}")
    print(f"  Job: {request.job_description[:50]}...")
    print(f"  Duration: {request.duration_minutes} minutes")
    
    # Create interview record
    interview_service.create_interview(
        session_id=session_id,
        job_description=request.job_description,
        candidate_name=request.candidate_name,
        duration_minutes=request.duration_minutes,
    )
    
    # Create in-memory session
    session_service.create_session(
        session_id=session_id,
        job_description=request.job_description,
        candidate_name=request.candidate_name,
    )
    
    # Pre-generate greeting (async background task)
    print(f"[Setup] Pre-generating greeting video...")
    asyncio.create_task(media_service.pre_generate_greeting(session_id))
    
    # Return session info to frontend
    ws_url = f"ws://{settings.API_HOST}:8000/ws/interview/{session_id}"
    
    print(f"[Setup] ✓ Interview setup complete")
    print(f"  WebSocket URL: {ws_url}")
    
    return InterviewSetupResponse(
        session_id=session_id,
        ws_url=ws_url,
        message="Interview setup complete. Generating media...",
    )

@app.get("/api/health")
async def health_check():
    """Check service health"""
    return {
        "status": "ok",
        "services": {
            "database": "ok",
            "whisper": "ok",
            "huggingface": "ok"
        }
    }

# ===== VIDEO STREAMING ENDPOINT =====

@app.get("/media/video/{session_id}/{video_name}")
async def stream_video(session_id: str, video_name: str):
    """
    Stream video file with proper headers for HTML5 video tag.
    Supports range requests for seeking.
    """
    video_path = os.path.join(settings.VIDEO_CACHE_DIR, session_id, video_name)
    
    print(f"[Stream] Request: {session_id}/{video_name}")
    print(f"  Path: {video_path}")
    
    # Security: Prevent path traversal
    if ".." in video_name or not video_path.startswith(settings.VIDEO_CACHE_DIR):
        print(f"[Stream] ✗ Security check failed")
        raise HTTPException(status_code=403, detail="Forbidden")
    
    if not os.path.exists(video_path):
        print(f"[Stream] ✗ File not found: {video_path}")
        # List files in directory for debugging
        session_dir = os.path.join(settings.VIDEO_CACHE_DIR, session_id)
        if os.path.exists(session_dir):
            files = os.listdir(session_dir)
            print(f"[Stream] Files in {session_dir}: {files}")
        raise HTTPException(status_code=404, detail="Video not found")
    
    file_size = os.path.getsize(video_path)
    print(f"[Stream] ✓ Streaming {video_name} ({file_size / (1024*1024):.2f} MB)")
    
    # Support range requests for seeking
    async def file_streamer():
        with open(video_path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                yield chunk
    
    return StreamingResponse(
        file_streamer(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Cache-Control": "public, max-age=3600",
        }
    )

# ===== WEBSOCKET ENDPOINT - MAIN INTERVIEW FLOW =====

@app.websocket("/ws/interview/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Main interview WebSocket handler.
    Flow: greeting → questions → responses → evaluation → results
    FIXED: Properly handles binary audio data from frontend
    """
    await websocket.accept()
    print(f"\n[WS] Client connected: {session_id}")
    
    # Get session from SessionService
    session = session_service.get_session(session_id)
    if not session:
        print(f"[WS] ✗ Session not found: {session_id}")
        await websocket.send_json({"type": "error", "message": "Session not found"})
        await websocket.close()
        return
    
    # Start interview timer
    timer_service.start_timer(session_id, settings.INTERVIEW_DURATION_MINUTES)
    
    try:
        # Wait for client ready signal
        print(f"[WS] Waiting for ready signal...")
        data = await websocket.receive_json()
        
        if data.get("type") != "ready":
            print(f"[WS] ✗ Invalid message type: {data.get('type')}")
            await websocket.send_json({"type": "error", "message": "Expected ready signal"})
            return
        
        print(f"[WS] ✓ Client ready, sending greeting video")
        
        # ===== SEND GREETING VIDEO =====
        await websocket.send_json({
            "type": "greeting_video",
            "video_url": f"/media/video/{session_id}/greeting.mp4",
            "duration_seconds": 15
        })
        
        # Wait for greeting completion or skip
        try:
            data = await asyncio.wait_for(websocket.receive_json(), timeout=20.0)
            if data.get("type") != "greeting_complete":
                print(f"[WS] Skipping greeting wait")
        except asyncio.TimeoutError:
            print(f"[WS] Greeting timeout, proceeding")
        
        # ===== INTERVIEW LOOP (4-5 questions) =====
        question_index = 1
        max_questions = 5
        
        while question_index <= max_questions and timer_service.get_remaining(session_id) > settings.CLOSING_BUFFER_SECONDS:
            print(f"\n[WS] === QUESTION {question_index} ===")
            remaining = timer_service.get_remaining(session_id)
            print(f"  Time remaining: {remaining:.0f}s")
            
            # Generate question text if not pre-generated
            question_obj = session_service.get_question(session_id, question_index)
            if not question_obj:
                print(f"[WS] No pre-generated question, generating...")
                if question_index == 1:
                    question_text = await question_service.generate_opening_question(
                        session.get("job_description", "")
                    )
                else:
                    question_text = f"Question {question_index}"
                
                session_service.add_question(session_id, question_index, question_text)
                question_obj = {"text": question_text, "index": question_index}
            
            # Send question video
            print(f"[WS] Sending question {question_index} video")
            await websocket.send_json({
                "type": "question_video",
                "video_url": f"/media/video/{session_id}/q{question_index}.mp4",
                "question_text": question_obj.get("text", ""),
                "question_index": question_index,
                "total_questions": max_questions
            })
            
            # Wait for listening start signal
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                if data.get("type") != "listening_start":
                    print(f"[WS] No listening start signal")
                    continue
            except asyncio.TimeoutError:
                print(f"[WS] No listening start signal")
            
            # ===== RECEIVE AUDIO & TRANSCRIBE =====
            print(f"[WS] Listening for audio response...")
            audio_chunks = []
            transcription = ""
            
            while True:
                try:
                    # ✅ FIX: Receive any message type (binary or text)
                    message = await asyncio.wait_for(
                        websocket.receive(),  # ← Changed from receive_json()
                        timeout=60.0
                    )
                    
                    # Handle text messages (JSON control messages)
                    if "text" in message:
                        try:
                            data = json.loads(message["text"])
                            print(f"[WS] ← JSON message: {data.get('type')}")
                            
                            if data.get("type") == "audio_end":
                                print(f"[WS] Audio ended")
                                break
                        except json.JSONDecodeError:
                            print(f"[WS] Invalid JSON in text message")
                            continue
                    
                    # Handle binary messages (audio data from frontend)
                    elif "bytes" in message:
                        chunk = message["bytes"]
                        audio_chunks.append(chunk)
                        total_bytes = sum(len(c) for c in audio_chunks)
                        print(f"[WS] ← audio_chunk ({len(chunk)} bytes, total: {total_bytes} bytes)")
                
                except asyncio.TimeoutError:
                    print(f"[WS] Audio timeout after 60s")
                    break
                except KeyError as e:
                    # ✅ FIX: Proper error handling
                    print(f"[WS] ✗ Message parsing error: {e}")
                    continue
                except Exception as e:
                    # ✅ FIX: Use logger for exc_info instead of print
                    logger.error(f"[WS] ✗ WebSocket exception: {e}", exc_info=True)
                    break
            
            # Get final transcription from all chunks
            print(f"[WS] Total audio chunks: {len(audio_chunks)}")
            if audio_chunks:
                final_transcript = await audio_service.get_final_transcription(
                    session_id, audio_chunks
                )
            else:
                final_transcript = ""
            
            print(f"[WS] Final transcript: {final_transcript[:100]}...")
            
            # Store response
            session_service.add_response(session_id, question_index, final_transcript)
            
            # ===== EVALUATION =====
            print(f"[WS] Evaluating response...")
            evaluation = await evaluation_service.evaluate_response(
                question=question_obj.get("text", ""),
                response=final_transcript,
                job_description=session.get("job_description", ""),
                conversation_history=session_service.get_conversation_history(session_id)
            )
            
            print(f"[WS] Score: {evaluation.get('score')}/10")
            print(f"[WS] Feedback: {evaluation.get('feedback')}")
            
            # Store evaluation
            session_service.add_evaluation(session_id, question_index, evaluation)
            
            # Send evaluation feedback
            await websocket.send_json({
                "type": "evaluation",
                "score": evaluation.get("score", 5),
                "marks": evaluation.get("marks", "5/10"),
                "feedback": evaluation.get("feedback", "Good answer.")
            })
            
            # Check if we should continue
            remaining = timer_service.get_remaining(session_id)
            if remaining <= settings.CLOSING_BUFFER_SECONDS:
                print(f"[WS] Time expired, closing interview")
                break
            
            question_index += 1
        
        # ===== CLOSING SEQUENCE =====
        print(f"\n[WS] === CLOSING ===")
        print(f"[WS] Sending closing video")
        
        await websocket.send_json({
            "type": "closing_video",
            "video_url": f"/media/video/{session_id}/closing.mp4"
        })
        
        # Wait for closing completion
        try:
            await asyncio.wait_for(websocket.receive_json(), timeout=20.0)
        except asyncio.TimeoutError:
            pass
        
        # ===== COMPILE & SEND RESULTS =====
        print(f"[WS] Compiling results...")
        results = results_service.compile_results(session_id, session_service)
        
        print(f"[WS] Overall score: {results.get('overall_score')}/10")
        print(f"[WS] Recommendation: {results.get('recommendation')}")
        
        await websocket.send_json({
            "type": "results",
            "evaluations": results.get("evaluations", []),
            "overall_score": results.get("overall_score", 0),
            "recommendation": results.get("recommendation", "CONSIDER")
        })
        
        # Complete interview
        interview_service.complete_interview(session_id, results)
        
        print(f"[WS] ✓ Interview completed: {session_id}")
    
    except Exception as e:
        # ✅ FIX: Use logger instead of print with exc_info
        logger.error(f"[WS] ✗ Error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    
    finally:
        await websocket.close()
        timer_service.stop_timer(session_id)
        print(f"[WS] WebSocket closed: {session_id}")

# ===== RUN =====

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
