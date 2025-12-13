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
        # Mount frontend build
    if os.path.exists(settings.FRONTEND_DIR):
        app.mount("/", StaticFiles(directory=settings.FRONTEND_DIR, html=True), name="frontend")
        print("✓ Frontend mounted at /")
    else:
        print("⚠ Frontend build not found at:", settings.FRONTEND_DIR)

    # Mount static files for serving media
    if os.path.exists(settings.MEDIA_DIR):
        app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")
        print("✓ Static files mounted at /media")

# ===== REST ENDPOINTS =====

@app.post("/api/interview/setup", response_model=InterviewSetupResponse)
async def setup_interview(request: InterviewSetupRequest):
    """
    1. Create interview record + in-memory session
    2. Pre-generate greeting + interview questions
    3. Return session_id + WebSocket URL
    """
    session_id = str(uuid.uuid4())
    
    print(f"\n[Setup] Starting interview setup...")
    print(f"  Session ID: {session_id}")
    print(f"  Candidate: {request.candidate_name}")
    print(f"  Job: {request.job_description[:50]}...")
    print(f"  Questions: {request.question_count}")
    
    # Create interview record
    interview_service.create_interview(
        session_id=session_id,
        job_description=request.job_description,
        candidate_name=request.candidate_name,
        question_count=request.question_count,
    )
    
    # Create in-memory session
    session_service.create_session(
        session_id=session_id,
        job_description=request.job_description,
        candidate_name=request.candidate_name,
        question_count=request.question_count
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
    await websocket.accept()
    print(f"\n[WS] Client connected: {session_id}")
    
    session = session_service.get_session(session_id)
    if not session:
        await websocket.close()
        return
    
    timer_service.start_timer(session_id, 30)
    
    try:
        # 1. Ready Signal
        data = await websocket.receive_json()
        if data.get("type") != "ready":
            return
            
        # 2. Pre-generate a generic "Listening" video (nodding) if it doesn't exist
        # We will use this loop whenever the candidate is speaking
        listening_video_url = f"/media/video/{session_id}/listening.mp4"
        if f"{session_id}_listening" not in media_service.video_cache:
            print(f"[WS] Generating listening video loop...")
            await media_service.generate_listening_video(session_id, 3.0, "listening")

        # 3. Send Greeting
        greeting_path = os.path.join(settings.VIDEO_CACHE_DIR, session_id, "greeting.mp4")
        greeting_url = f"/media/video/{session_id}/greeting.mp4"
        
        print(f"[WS] Waiting for greeting video at: {greeting_path}")
        
        # Poll for file existence (Timeout after 60 seconds)
        video_ready = False
        for _ in range(60):
            if os.path.exists(greeting_path) and os.path.getsize(greeting_path) > 1000:
                video_ready = True
                break
            await asyncio.sleep(1) # Wait 1 second and check again
            
        if not video_ready:
            print(f"[WS] ✗ Timeout: Greeting video was not generated.")
            # Fallback: Send just text if video fails
            await websocket.send_json({
                "type": "greeting_video",
                "video_url": "", # Frontend should handle empty URL
                "text": "Welcome to your AI Interview. (Video unavailable)"
            })
        else:
            print(f"[WS] ✓ Greeting video ready. Sending to client.")
            await websocket.send_json({
                "type": "greeting_video",
                "video_url": greeting_url,
                "text": "Welcome to your AI Interview."
            })
        
        # Wait for greeting to finish
        try:
            msg = await asyncio.wait_for(websocket.receive(), timeout=30.0)
            if msg["type"] == "websocket.disconnect": return
        except asyncio.TimeoutError:
            pass

        # ===== START INTERVIEW LOOP =====
        question_index = 1
        max_questions = session.get("question_count", settings.DEFAULT_QUESTION_COUNT)
        previous_evaluation = None
        
        while question_index <= max_questions:
            print(f"\n[WS] === QUESTION {question_index} ===")
            
            # --- STEP A: GENERATE QUESTION CONTENT ---
            question_text = ""
            spoken_text = "" # What the avatar actually says (Feedback + Question)

            if question_index == 1:
                # First question (No feedback needed)
                question_text = await question_service.generate_opening_question(session.get("job_description", ""))
                spoken_text = question_text
            else:
                # Adaptive Question (Includes Feedback from previous Q)
                prev_index = question_index - 1
                
                # Get context
                hist = session_service.get_conversation_history(session_id)
                prev_resp = next((r["text"] for r in hist["responses"] if r["question_index"] == prev_index), "")
                
                # Generate Q
                question_text = await question_service.generate_adaptive_question(
                    previous_question=session_service.get_question(session_id, prev_index)["text"],
                    response=prev_resp,
                    evaluation=previous_evaluation or {},
                    job_description=session.get("job_description", ""),
                    conversation_history=hist
                )
                
                # Construct smooth transition: Feedback -> Transition -> New Question
                feedback_short = previous_evaluation.get("feedback", "Thank you.")
                spoken_text = f"{feedback_short} Now, {question_text}"

            # Save Question
            session_service.add_question(session_id, question_index, question_text)

            # --- STEP B: GENERATE VIDEO (Feedback + Question) ---
            print(f"[WS] Generating video for Question {question_index}...")
            # We generate video for 'spoken_text' but display 'question_text' on screen
            audio_path = await media_service.text_to_speech(spoken_text, session_id, f"q{question_index}")
            await media_service.generate_video(session_id, audio_path, f"q{question_index}")

            # --- STEP C: PLAY VIDEO ---
            await websocket.send_json({
                "type": "question_video",
                "video_url": f"/media/video/{session_id}/q{question_index}.mp4",
                "question_text": question_text, # Display text
                "question_index": question_index,
                "total_questions": max_questions
            })

            # Wait for video to finish
            try:
                msg = await asyncio.wait_for(websocket.receive(), timeout=60.0) # Wait for playback
                if msg["type"] == "websocket.disconnect": return
            except asyncio.TimeoutError:
                pass

            # --- STEP D: LISTENING MODE ---
            # Tell frontend to switch to "Listening" video and start mic
            print(f"[WS] Switching to listening mode...")
            await websocket.send_json({
                "type": "start_listening",
                "video_url": listening_video_url # Loop this while user speaks
            })

            # --- STEP E: RECEIVE AUDIO ---
            audio_chunks = []
            while True:
                try:
                    msg = await asyncio.wait_for(websocket.receive(), timeout=60.0)
                    
                    if "text" in msg:
                        data = json.loads(msg["text"])
                        if data.get("type") == "audio_end": break
                    elif "bytes" in msg:
                        audio_chunks.append(msg["bytes"])
                        
                except asyncio.TimeoutError:
                    break
            
            # --- STEP F: PROCESS RESPONSE ---
            print(f"[WS] Processing response...")
            final_transcript = await audio_service.get_final_transcription(session_id, audio_chunks)
            session_service.add_response(session_id, question_index, final_transcript)
            
            await websocket.send_json({
                "type": "transcription",
                "text": final_transcript
            })
            # --- STEP G: EVALUATE (In background for next loop) ---
            previous_evaluation = await evaluation_service.evaluate_response(
                question=question_text,
                response=final_transcript,
                job_description=session.get("job_description", ""),
                conversation_history=session_service.get_conversation_history(session_id)
            )
            session_service.add_evaluation(session_id, question_index, previous_evaluation)
            
            # Send interim score to frontend (optional, keeps UI updated)
            await websocket.send_json({
                "type": "interim_result",
                "score": previous_evaluation.get("score"),
                "feedback": previous_evaluation.get("feedback")
            })

            question_index += 1

        # ===== CLOSING =====
        results = results_service.compile_results(session_id, session_service)
        interview_service.complete_interview(session_id, results)
        
        await websocket.send_json({
            "type": "results",
            "overall_score": results.get("overall_score"),
            "recommendation": results.get("recommendation"),
            "evaluations": results.get("evaluations")
        })

    except Exception as e:
        logger.error(f"[WS] Error: {e}", exc_info=True)
    finally:
        await websocket.close()

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
