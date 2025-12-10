from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import json
from datetime import datetime
import uuid
import os

from config import settings
from models import db_init
from schemas import InterviewSetupRequest, InterviewSetupResponse
from services import (
    InterviewService, AudioService, EvaluationService,
    QuestionService, MediaService, SessionService,
    TimerService, ResultsService
)

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
    
    # Mount static files for serving media
    if os.path.exists(settings.MEDIA_DIR):
        app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")
        print("✓ Static files mounted")

# ===== REST ENDPOINTS =====

@app.post("/api/interview/setup", response_model=InterviewSetupResponse)
async def setup_interview(request: InterviewSetupRequest):
    """
    1. Create interview record + in-memory session
    2. Pre-generate greeting + first 3 questions
    3. Return session_id + WebSocket URL
    """
    session_id = str(uuid.uuid4())
    
    # Persist interview metadata
    interview_service.create_interview(
        session_id=session_id,
        job_description=request.job_description,
        candidate_name=request.candidate_name,
        duration_minutes=request.duration_minutes,
    )
    
    # CRITICAL: Create in-memory session used by WebSocket
    session_service.create_session(
        session_id=session_id,
        job_description=request.job_description,
        candidate_name=request.candidate_name,
    )
    
    # Pre-generate greeting (async background task)
    asyncio.create_task(
        media_service.pre_generate_greeting(session_id)
    )
    
    # Pre-generate first 3 questions (async background task)
    asyncio.create_task(
        question_service.pre_generate_opening_questions(
            session_id, request.job_description, 3
        )
    )
    
    # Return session info to frontend
    ws_url = f"ws://{settings.API_HOST}/ws/interview/{session_id}"
    
    return InterviewSetupResponse(
        session_id=session_id,
        ws_url=ws_url,
        message="Interview setup complete. Generating media...",
    )

@app.get("/api/interview/{interview_id}/results")
async def get_results(interview_id: str):
    """Get final interview results"""
    results = results_service.get_results(interview_id)
    if not results:
        raise HTTPException(status_code=404, detail="Interview not found")
    return results

@app.get("/api/interview/{interview_id}/download-report")
async def download_report(interview_id: str):
    """Download PDF report"""
    pdf_path = results_service.export_pdf(interview_id)
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(pdf_path, media_type="application/pdf")

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

# ===== WEBSOCKET ENDPOINT =====

@app.websocket("/ws/interview/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Main interview WebSocket handler
    Manages: greeting → questions → responses → evaluation → results
    """
    await websocket.accept()
    print(f"[WS] Client connected: {session_id}")
    
    # Get session from SessionService (in-memory)
    session = session_service.get_session(session_id)
    if not session:
        print(f"[WS] Session not found: {session_id}")
        await websocket.send_json({"type": "error", "message": "Session not found"})
        await websocket.close()
        return
    
    # Start timer
    timer_service.start_timer(session_id, settings.INTERVIEW_DURATION_MINUTES)
    
    try:
        # Wait for client ready signal
        print(f"[WS] Waiting for ready signal from {session_id}")
        data = await websocket.receive_json()
        if data.get("type") != "ready":
            print(f"[WS] Invalid message type: {data.get('type')}")
            await websocket.send_json({"type": "error", "message": "Expected ready signal"})
            return
        
        print(f"[WS] Client ready, sending greeting video")
        
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
                print(f"[WS] Skipping greeting wait: {data.get('type')}")
        except asyncio.TimeoutError:
            print(f"[WS] Greeting timeout, proceeding")
        
        # ===== INTERVIEW LOOP (4-5 questions) =====
        question_index = 1
        while timer_service.get_remaining(session_id) > settings.CLOSING_BUFFER_SECONDS:
            
            # ===== SEND QUESTION VIDEO =====
            question_obj = session_service.get_question(session_id, question_index)
            if not question_obj:
                print(f"[WS] No question at index {question_index}")
                break
            
            print(f"[WS] Sending question {question_index}")
            await websocket.send_json({
                "type": "question_video",
                "video_url": f"/media/video/{session_id}/q{question_index}.mp4",
                "question_text": question_obj.get("text", ""),
                "question_index": question_index,
                "total_questions": 5
            })
            
            # Wait for listening start signal
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                if data.get("type") != "listening_start":
                    print(f"[WS] Unexpected message: {data.get('type')}")
                    continue
            except asyncio.TimeoutError:
                print(f"[WS] No listening start signal, continuing")
            
            # ===== RECEIVE & PROCESS AUDIO =====
            audio_chunks = []
            transcription = ""
            print(f"[WS] Listening for audio from {session_id}")
            
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=60.0
                    )
                except asyncio.TimeoutError:
                    print(f"[WS] Audio timeout")
                    break
                
                if message.get("type") == "audio_chunk":
                    chunk = message.get("data")
                    audio_chunks.append(chunk)
                    
                    # Stream to Whisper (non-blocking)
                    partial = await audio_service.transcribe_chunk(session_id, chunk)
                    if partial:
                        transcription += partial + " "
                        await websocket.send_json({
                            "type": "transcription_partial",
                            "text": transcription.strip()
                        })
                
                elif message.get("type") == "audio_end":
                    print(f"[WS] Audio ended, processing final transcript")
                    break
            
            # Get final transcription
            final_transcript = await audio_service.get_final_transcription(session_id, audio_chunks)
            print(f"[WS] Final transcript: {final_transcript[:50]}...")
            
            # Store response
            session_service.add_response(
                session_id, question_index, final_transcript
            )
            
            # ===== EVALUATION =====
            evaluation = await evaluation_service.evaluate_response(
                question=question_obj.get("text", ""),
                response=final_transcript,
                job_description=session.get("job_description", ""),
                conversation_history=session_service.get_conversation_history(session_id)
            )
            
            # Store evaluation
            session_service.add_evaluation(session_id, question_index, evaluation)
            
            # Send evaluation feedback
            await websocket.send_json({
                "type": "evaluation",
                "score": evaluation.get("score", 5),
                "marks": evaluation.get("marks", "5/10"),
                "feedback": evaluation.get("feedback", "Good answer.")
            })
            
            # Check if we should continue or close
            if timer_service.get_remaining(session_id) <= settings.CLOSING_BUFFER_SECONDS:
                print(f"[WS] Time expired, closing interview")
                break
            
            # Generate next question (async)
            try:
                next_q_text = await asyncio.wait_for(
                    question_service.generate_adaptive_question(
                        previous_question=question_obj.get("text", ""),
                        response=final_transcript,
                        evaluation=evaluation,
                        job_description=session.get("job_description", ""),
                        conversation_history=session_service.get_conversation_history(session_id)
                    ),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                next_q_text = "Tell me more about this experience."
            
            # Generate TTS and video (async - happens in background)
            asyncio.create_task(
                media_service.generate_question_media(
                    session_id, question_index + 1, next_q_text
                )
            )
            
            # Save question to DB
            session_service.add_question(
                session_id, question_index + 1, next_q_text
            )
            
            question_index += 1
        
        # ===== CLOSING SEQUENCE =====
        print(f"[WS] Sending closing video")
        await websocket.send_json({
            "type": "closing_video",
            "video_url": f"/media/video/{session_id}/closing.mp4"
        })
        
        # Wait for closing completion
        try:
            data = await asyncio.wait_for(websocket.receive_json(), timeout=20.0)
        except asyncio.TimeoutError:
            pass
        
        # ===== COMPILE & SEND RESULTS =====
        print(f"[WS] Compiling results for {session_id}")
        results = results_service.compile_results(
            session_id, session_service, evaluation_service
        )
        
        await websocket.send_json({
            "type": "results",
            "overall_score": results.get("overall_score", 0),
            "recommendation": results.get("recommendation", "CONSIDER"),
            "breakdown": results.get("breakdown", []),
            "strengths": results.get("strengths", []),
            "weaknesses": results.get("weaknesses", [])
        })
        
        # Save interview to DB
        interview_service.complete_interview(session_id, results)
        print(f"[WS] Interview completed: {session_id}")
        
    except Exception as e:
        print(f"[WS] Error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
            print(f"[WS] WebSocket closed: {session_id}")
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=int(settings.API_PORT))
