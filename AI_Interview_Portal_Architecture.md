# AI Interview Portal - Complete Architecture & Flow

## 1. PROJECT OVERVIEW

**Objective:** Build an AI-powered interview platform where candidates are interviewed by a realistic AI avatar with lip-synced responses, intelligent RAG-based question generation, and real-time response evaluation.

---

## 2. CORE COMPONENTS & TECH STACK

### 2.1 Frontend (User Interface)
- **Framework:** React or Vue.js
- **Video Streaming:** WebRTC (for local video capture)
- **State Management:** Redux/Vuex
- **UI Library:** Material-UI or Tailwind CSS
- **Video Display:** HTML5 Canvas or Video element

### 2.2 AI Avatar & Lip-Sync
- **Avatar Source:** 
  - Option A: Use HeyGen API (pre-built avatars with lip-sync)
  - Option B: Use Vozo AI SDK (custom video lip-sync)
  - Option C: Self-hosted Wav2Lip implementation (open-source)
- **Text-to-Speech:** Google Cloud TTS, Azure TTS, or Eleven Labs
- **Lip-Sync Engine:** 
  - HeyGen's proprietary lip-sync technology, OR
  - Wav2Lip open-source model

### 2.3 Audio Processing & Transcription
- **Audio Capture:** Web Audio API
- **Speech-to-Text (ASR):** 
  - Option A: Google Cloud Speech-to-Text (high accuracy ~97%)
  - Option B: Azure Speech Services (real-time streaming)
  - Option C: Picovoice Cheetah (low-latency on-device)
  - Option D: OpenAI Whisper API (good balance)
- **VAD (Voice Activity Detection):** Picovoice or WebRTC VAD
- **Audio Processing:** Web Audio API + FFmpeg.js for preprocessing

### 2.4 RAG-Based Question Generation
- **Vector Database:** Pinecone, Weaviate, or Milvus
- **Embedding Model:** OpenAI embeddings, Sentence Transformers
- **LLM for Generation:** 
  - Option A: OpenAI GPT-4
  - Option B: Anthropic Claude
  - Option C: Open-source Llama (via Ollama for local deployment)
- **RAG Framework:** LangChain or LlamaIndex
- **Document Processing:** PyPDF2, LangChain document loaders

### 2.5 Response Evaluation & Scoring
- **LLM Evaluation:** GPT-4 with custom evaluation prompts
- **Sentiment Analysis:** Transformers.js or Hugging Face API
- **Scoring Engine:** Custom logic with weighted criteria

### 2.6 Backend Infrastructure
- **API Server:** Node.js (Express) or Python (FastAPI/Flask)
- **Database:** PostgreSQL (structured data), MongoDB (flexible schema)
- **Session Management:** Redis
- **File Storage:** AWS S3 or Google Cloud Storage
- **Authentication:** JWT tokens, OAuth 2.0

### 2.7 DevOps & Deployment
- **Containerization:** Docker
- **Orchestration:** Kubernetes (optional)
- **CI/CD:** GitHub Actions, GitLab CI
- **Cloud Platform:** AWS, Google Cloud, Azure, or DigitalOcean

---

## 3. SYSTEM ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React/Vue)                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Interview UI    │  │  Avatar Display  │  │  Video Recorder  │  │
│  │  - Questions     │  │  (HeyGen/Vozo)   │  │  (WebRTC)        │  │
│  │  - Instructions  │  │  - Lip-synced    │  │  - Candidate cam │  │
│  │  - Timer         │  │  - Expressions   │  │  - Audio capture │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────┬─────────────────────────────────┬─────────────────────┘
              │                                 │
              ▼                                 ▼
        ┌─────────────┐              ┌──────────────────────┐
        │  Audio      │              │  Candidate Video     │
        │  Recorder   │              │  & Response Stream   │
        │  (Web Audio │              │                      │
        │   API)      │              │                      │
        └──────┬──────┘              └──────────┬───────────┘
               │                                │
               ▼                                ▼
        ┌────────────────────────────────────────────┐
        │     BACKEND API SERVER (Node/Python)      │
        ├────────────────────────────────────────────┤
        │  ┌──────────────────────────────────────┐  │
        │  │  1. Audio Processing Pipeline        │  │
        │  │     - VAD (Voice Activity Detection) │  │
        │  │     - Audio chunking (smart split)   │  │
        │  │     - Pre-processing (noise removal) │  │
        │  └──────────┬───────────────────────────┘  │
        │             ▼                               │
        │  ┌──────────────────────────────────────┐  │
        │  │  2. Speech-to-Text (ASR)             │  │
        │  │     - Real-time transcription        │  │
        │  │     - Accuracy: ~95-97% WER          │  │
        │  │     - Provider: Google/Azure/Whisper │  │
        │  └──────────┬───────────────────────────┘  │
        │             ▼                               │
        │  ┌──────────────────────────────────────┐  │
        │  │  3. Response Evaluation              │  │
        │  │     - Semantic analysis              │  │
        │  │     - Key skills detection           │  │
        │  │     - LLM-based scoring              │  │
        │  │     - Confidence metrics             │  │
        │  └──────────┬───────────────────────────┘  │
        │             ▼                               │
        │  ┌──────────────────────────────────────┐  │
        │  │  4. RAG Question Generator           │  │
        │  │     - Retrieve relevant context      │  │
        │  │     - Generate contextual questions  │  │
        │  │     - Maintain interview flow        │  │
        │  └──────────┬───────────────────────────┘  │
        │             ▼                               │
        │  ┌──────────────────────────────────────┐  │
        │  │  5. Text-to-Speech & Avatar          │  │
        │  │     - Convert question to speech     │  │
        │  │     - Generate avatar response       │  │
        │  │     - Lip-sync with audio            │  │
        │  └──────────────────────────────────────┘  │
        └────────┬─────────────────────┬────────────┘
                 │                     │
                 ▼                     ▼
        ┌────────────────────┐ ┌──────────────────────┐
        │   EXTERNAL APIs    │ │  DATA STORES         │
        ├────────────────────┤ ├──────────────────────┤
        │ • Google Cloud STT │ │ • PostgreSQL (users, │
        │ • OpenAI GPT-4     │ │   interviews, scores)│
        │ • Google TTS       │ │ • Redis (sessions)   │
        │ • HeyGen/Vozo API  │ │ • Vector DB          │
        │ • Pinecone/Weaviate│ │   (embeddings)       │
        │                    │ │ • S3/GCS (files,     │
        │                    │ │   videos)            │
        └────────────────────┘ └──────────────────────┘
```

---

## 4. DETAILED FLOW DIAGRAMS

### 4.1 Interview Initialization Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: Setup Phase                                                 │
└─────────────────────────────────────────────────────────────────────┘

1. User Login/Registration
   ├─ Authenticate via JWT/OAuth
   └─ Retrieve user profile

2. Create Interview Session
   ├─ Select interview type:
   │  ├─ Option A: Job Requirements Upload (PDF/DOCX)
   │  └─ Option B: Topic-based (manual text input)
   ├─ Parse/Extract requirements
   └─ Generate interview context

3. Initialize RAG Pipeline
   ├─ Load documents into vector database
   │  ├─ Split into chunks (semantic)
   │  ├─ Generate embeddings
   │  └─ Store in Pinecone/Weaviate
   ├─ Create system prompts with context
   └─ Initialize LLM for question generation

4. Load AI Avatar
   ├─ Select from avatar library (HeyGen/Vozo)
   ├─ Configure voice (tone, accent, language)
   ├─ Initialize video streaming
   └─ Test audio-video sync

5. Start Recording
   ├─ Initialize WebRTC video capture
   ├─ Get microphone permissions
   ├─ Initialize audio stream
   └─ Start session timer

6. Generate First Question
   ├─ Call RAG pipeline
   │  ├─ Retrieve relevant context from documents
   │  ├─ Generate question using LLM
   │  └─ Validate question quality
   ├─ Convert to speech (TTS)
   ├─ Generate avatar video with lip-sync
   └─ Stream to user
```

### 4.2 Interview Execution Flow (Per Question)

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Interview Loop (Repeats for each question)                  │
└─────────────────────────────────────────────────────────────────────┘

PHASE A: QUESTION DELIVERY
┌──────────────────────────────────────────────────────┐
│ 1. Avatar Asks Question                              │
│    ├─ Stream pre-generated video with lip-sync       │
│    ├─ Audio plays synchronized with avatar movement  │
│    └─ Show question text as subtitle (optional)      │
│                                                      │
│ 2. User Sees Visual Cues                             │
│    ├─ Avatar speaking animation                      │
│    ├─ Countdown timer (e.g., 3 minutes for answer)   │
│    ├─ "Your turn" indicator                          │
│    └─ Video recording starts after question ends     │
└──────────────────────────────────────────────────────┘

PHASE B: CANDIDATE RESPONSE CAPTURE
┌──────────────────────────────────────────────────────┐
│ 1. Audio Capture                                     │
│    ├─ Use Web Audio API                              │
│    ├─ Stream audio in chunks (e.g., 100ms)           │
│    ├─ Apply noise gate (VAD - Voice Activity Det.)   │
│    └─ Buffer audio for processing                    │
│                                                      │
│ 2. Real-time Display                                 │
│    ├─ Show candidate's video feed                    │
│    ├─ Display audio waveform (optional)              │
│    ├─ Show remaining time                            │
│    └─ Allow manual "next question" button            │
└──────────────────────────────────────────────────────┘

PHASE C: AUDIO PROCESSING & TRANSCRIPTION
┌──────────────────────────────────────────────────────┐
│ 1. VAD (Voice Activity Detection)                    │
│    ├─ Detect when candidate starts/stops speaking    │
│    ├─ Remove silence periods                         │
│    └─ Smart audio chunking (split at natural breaks) │
│                                                      │
│ 2. Speech-to-Text Conversion                         │
│    ├─ Send audio chunks to ASR service               │
│    │  └─ Options: Google STT, Azure, Whisper, etc.   │
│    ├─ Receive real-time transcription                │
│    ├─ Accuracy target: 95%+ (WER <5%)                │
│    └─ Post-processing:                               │
│        ├─ Fix capitalization                         │
│        ├─ Handle numbers/abbreviations               │
│        └─ Remove filler words (optional)             │
│                                                      │
│ 3. Store Transcription                               │
│    ├─ Save to database with timestamps               │
│    ├─ Link to interview session & question ID        │
│    └─ Store audio file (for review/audit)            │
└──────────────────────────────────────────────────────┘

PHASE D: RESPONSE EVALUATION
┌──────────────────────────────────────────────────────┐
│ 1. Prepare Evaluation Prompt                         │
│    ├─ Question asked                                 │
│    ├─ Candidate's transcribed response               │
│    ├─ Job requirements/topic context                 │
│    ├─ Evaluation criteria:                           │
│    │  ├─ Relevance to question                       │
│    │  ├─ Technical accuracy                          │
│    │  ├─ Completeness of answer                      │
│    │  ├─ Communication clarity                       │
│    │  └─ Confidence indicators                       │
│    └─ Rubric/scoring framework                       │
│                                                      │
│ 2. LLM-Based Evaluation                              │
│    ├─ Send prompt to GPT-4/Claude                    │
│    ├─ Receive structured evaluation:                 │
│    │  ├─ Score (0-100)                               │
│    │  ├─ Feedback/reasoning                          │
│    │  ├─ Key insights detected                       │
│    │  ├─ Skills demonstrated                         │
│    │  └─ Red flags (if any)                          │
│    └─ Store evaluation results                       │
│                                                      │
│ 3. Real-time Feedback (optional)                     │
│    ├─ Show candidate their score                     │
│    ├─ Display brief feedback                         │
│    └─ Maintain interview flow                        │
└──────────────────────────────────────────────────────┘

PHASE E: NEXT QUESTION GENERATION
┌──────────────────────────────────────────────────────┐
│ 1. Context-Aware Question Generation                 │
│    ├─ Use RAG pipeline:                              │
│    │  ├─ Query: "What should I ask next?"            │
│    │  ├─ Context: Previous questions & answers       │
│    │  ├─ Document context: Job requirements          │
│    │  └─ Retrieve top-K relevant passages            │
│    │                                                 │
│    ├─ LLM generates question based on:               │
│    │  ├─ Retrieved context                           │
│    │  ├─ Interview progression                       │
│    │  ├─ Skills not yet assessed                     │
│    │  └─ Follow-up to previous answer (if needed)    │
│    │                                                 │
│    ├─ Validation:                                    │
│    │  ├─ Not duplicate of previous questions         │
│    │  ├─ Appropriate difficulty level                │
│    │  ├─ Relevant to job requirements                │
│    │  └─ Natural conversation flow                   │
│    │                                                 │
│    └─ Store generated question                       │
│                                                      │
│ 2. Convert to Speech                                 │
│    ├─ Use TTS service (Google/Azure/ElevenLabs)      │
│    ├─ Apply natural prosody/pauses                   │
│    ├─ Generate audio file                            │
│    └─ Stream to video generation                     │
│                                                      │
│ 3. Generate Avatar Video with Lip-Sync               │
│    ├─ Option A: HeyGen API                           │
│    │  └─ Send: Avatar ID + TTS audio                 │
│    │  └─ Receive: Pre-generated video with lip-sync  │
│    │                                                 │
│    ├─ Option B: Vozo AI                              │
│    │  └─ Send: Avatar video + audio                  │
│    │  └─ Receive: Lip-synced video                   │
│    │                                                 │
│    └─ Option C: Self-hosted Wav2Lip                  │
│       └─ Local processing (requires GPU)             │
│                                                      │
│ 4. Cache & Serve                                     │
│    ├─ Store generated video in S3/CDN                │
│    ├─ Optimize for streaming (MP4, WebM)             │
│    └─ Ready for next question delivery               │
└──────────────────────────────────────────────────────┘

PHASE F: LOOP DECISION
┌──────────────────────────────────────────────────────┐
│ Check continuation criteria:                         │
│ ├─ Questions asked: N out of MAX (e.g., 8/8)?       │
│ ├─ Time elapsed: Within limit?                      │
│ ├─ Interview quality: Met minimum standards?        │
│ │                                                   │
│ └─ Decision:                                         │
│    ├─ If YES → Go to STEP 3 (End Interview)         │
│    └─ If NO → Repeat PHASE A (Ask next question)    │
└──────────────────────────────────────────────────────┘
```

### 4.3 Interview Termination Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: Interview Conclusion & Report Generation                    │
└─────────────────────────────────────────────────────────────────────┘

PHASE A: DATA AGGREGATION
┌──────────────────────────────────────────────────────┐
│ 1. Collect All Responses                             │
│    ├─ Retrieve all questions asked                   │
│    ├─ Retrieve all transcriptions                    │
│    ├─ Retrieve all evaluation scores                 │
│    ├─ Retrieve all audio/video files                 │
│    └─ Retrieve timing data                           │
│                                                      │
│ 2. Calculate Overall Score                           │
│    ├─ Average question scores                        │
│    ├─ Apply weighting (if applicable):               │
│    │  ├─ Technical questions: 40%                    │
│    │  ├─ Behavioral questions: 30%                   │
│    │  ├─ Communication: 20%                          │
│    │  └─ Overall fit: 10%                            │
│    │                                                 │
│    └─ Final Score Calculation:                       │
│       └─ Overall Score = Σ(Score_i × Weight_i)      │
│                                                      │
│ 3. Aggregate Feedback                                │
│    ├─ Compile all LLM evaluations                    │
│    ├─ Extract key themes:                            │
│    │  ├─ Strengths demonstrated                      │
│    │  ├─ Areas for improvement                       │
│    │  ├─ Technical skills assessment                 │
│    │  └─ Soft skills assessment                      │
│    └─ Generate executive summary                     │
└──────────────────────────────────────────────────────┘

PHASE B: REPORT GENERATION
┌──────────────────────────────────────────────────────┐
│ 1. Create Comprehensive Report                       │
│    ├─ Header:                                        │
│    │  ├─ Candidate name & ID                         │
│    │  ├─ Job position applied for                    │
│    │  ├─ Interview date & duration                   │
│    │  └─ Overall recommendation (Hire/No hire)       │
│    │                                                 │
│    ├─ Scoring Section:                               │
│    │  ├─ Question-by-question scores                 │
│    │  ├─ Category breakdowns                         │
│    │  ├─ Visual charts (bar/radar)                   │
│    │  └─ Comparative benchmarks                      │
│    │                                                 │
│    ├─ Detailed Feedback:                             │
│    │  ├─ Transcribed responses                       │
│    │  ├─ Evaluator comments                          │
│    │  ├─ Highlighted strengths                       │
│    │  └─ Improvement areas                           │
│    │                                                 │
│    ├─ Video Review Section:                          │
│    │  ├─ Playback of each Q&A                        │
│    │  ├─ Transcript with timestamps                  │
│    │  ├─ Score annotations                           │
│    │  └─ Searchable by question/topic                │
│    │                                                 │
│    └─ Metadata:                                      │
│       ├─ Interview session ID                        │
│       ├─ Timestamps for all events                   │
│       └─ Technical notes (ASR accuracy, etc.)        │
│                                                      │
│ 2. Store Report                                      │
│    ├─ Save to database                               │
│    ├─ Generate PDF export                            │
│    ├─ Create downloadable archive (all files)        │
│    └─ Enable secure sharing link                     │
└──────────────────────────────────────────────────────┘

PHASE C: NOTIFICATIONS & NEXT STEPS
┌──────────────────────────────────────────────────────┐
│ 1. Notify Candidate                                  │
│    ├─ Send email/dashboard notification              │
│    ├─ Provide access to interview report             │
│    ├─ Optional: Feedback message from recruiter      │
│    └─ Next steps information                         │
│                                                      │
│ 2. Notify Recruiter/Hiring Manager                   │
│    ├─ Send report to dashboard                       │
│    ├─ Alert for low/high performers                  │
│    ├─ Enable quick hire/reject decision              │
│    ├─ Provide bulk comparison (if multiple)          │
│    └─ Export options (PDF, Excel, etc.)              │
│                                                      │
│ 3. Archive & Cleanup                                 │
│    ├─ Store all data for compliance (GDPR, etc.)     │
│    ├─ Compress old video files                       │
│    ├─ Move to cold storage (optional)                │
│    └─ Set retention policies                         │
└──────────────────────────────────────────────────────┘

PHASE D: ANALYTICS & INSIGHTS
┌──────────────────────────────────────────────────────┐
│ 1. Candidate Analytics                               │
│    ├─ Track candidate progression through pipeline    │
│    ├─ Analyze score distributions                    │
│    ├─ Identify patterns (weak areas, trends)         │
│    └─ Benchmark against previous candidates          │
│                                                      │
│ 2. Interview Quality Metrics                         │
│    ├─ ASR accuracy per session                       │
│    ├─ Avatar lip-sync quality feedback               │
│    ├─ User experience metrics (completion rate)      │
│    ├─ Average interview duration                     │
│    └─ Question quality metrics                       │
│                                                      │
│ 3. Hiring Metrics                                    │
│    ├─ Time-to-hire improvement                       │
│    ├─ Hire rate by position                          │
│    ├─ Predicted job performance correlation          │
│    └─ Cost per hire savings                          │
└──────────────────────────────────────────────────────┘
```

---

## 5. DETAILED TECHNICAL COMPONENTS

### 5.1 RAG Pipeline Implementation

```
┌─────────────────────────────────────────────────────────────────────┐
│ RAG-BASED QUESTION GENERATION SYSTEM                                │
└─────────────────────────────────────────────────────────────────────┘

PHASE 1: DOCUMENT INGESTION & INDEXING
┌──────────────────────────────────────────────────────┐
│ 1. Upload Documents                                  │
│    ├─ Formats: PDF, DOCX, TXT, JSON                  │
│    ├─ Content: Job requirements, JD, role info       │
│    └─ Size limit: ~50MB per document                 │
│                                                      │
│ 2. Extract Text Content                              │
│    ├─ Use PyPDF2 or pdfplumber for PDFs              │
│    ├─ Use python-docx for Word documents             │
│    ├─ Parse JSON structures                          │
│    └─ Handle OCR for scanned documents               │
│                                                      │
│ 3. Text Cleaning & Preprocessing                     │
│    ├─ Remove headers/footers                         │
│    ├─ Standardize formatting                         │
│    ├─ Remove duplicate content                       │
│    ├─ Normalize whitespace                           │
│    └─ Detect language & encoding                     │
│                                                      │
│ 4. Semantic Chunking                                 │
│    ├─ Strategy: Split by paragraph/section           │
│    ├─ Size: 500-1000 tokens per chunk                │
│    ├─ Overlap: 50-100 tokens between chunks          │
│    ├─ Maintain context boundaries                    │
│    └─ Tools: LangChain RecursiveCharacterSplitter    │
│                                                      │
│ 5. Generate Embeddings                               │
│    ├─ Model: OpenAI text-embedding-3-small           │
│    │  └─ Dimension: 1536                             │
│    │  └─ Cost: ~$0.02 per 1M tokens                  │
│    │                                                 │
│    ├─ Alternative: Sentence-Transformers             │
│    │  └─ "all-mpnet-base-v2" (local, free)           │
│    │                                                 │
│    ├─ Batch processing:                              │
│    │  ├─ Process in chunks of 100 documents          │
│    │  ├─ Add retry logic for failures                │
│    │  └─ Cache embeddings                            │
│    │                                                 │
│    └─ Vector representation:                         │
│       └─ Each chunk → Dense vector (1536 dim)        │
│                                                      │
│ 6. Store in Vector Database                          │
│    ├─ Database options:                              │
│    │  ├─ Pinecone (cloud, managed)                   │
│    │  │  └─ Free tier: 1GB storage                   │
│    │  ├─ Weaviate (self-hosted, open-source)         │
│    │  ├─ Milvus (self-hosted, high performance)      │
│    │  └─ Qdrant (modern, open-source)                │
│    │                                                 │
│    ├─ Metadata stored per chunk:                     │
│    │  ├─ Source document ID                          │
│    │  ├─ Chunk index                                 │
│    │  ├─ Original text                               │
│    │  ├─ Timestamp                                   │
│    │  └─ Section/category tags                       │
│    │                                                 │
│    └─ Indexing strategy:                             │
│       ├─ Create namespace per interview              │
│       ├─ Build hybrid index (dense + sparse)         │
│       └─ Enable metadata filtering                   │
└──────────────────────────────────────────────────────┘

PHASE 2: QUESTION GENERATION
┌──────────────────────────────────────────────────────┐
│ 1. Build Query Context                               │
│    ├─ Current state:                                 │
│    │  ├─ Questions already asked (list)              │
│    │  ├─ Candidate responses (summaries)              │
│    │  ├─ Skills already assessed                     │
│    │  └─ Time elapsed                                │
│    │                                                 │
│    ├─ Target state:                                  │
│    │  ├─ Skills still to assess                      │
│    │  ├─ Required competencies (from JD)             │
│    │  ├─ Difficulty progression                      │
│    │  └─ Interview depth needed                      │
│    │                                                 │
│    └─ Build query string:                            │
│       └─ "Generate a [difficulty] question about    │
│          [topic/skill] that tests [competency]       │
│          for a [job role]. Skip [already asked]"    │
│                                                      │
│ 2. Retrieve Relevant Context (RAG Retrieval)         │
│    ├─ Embed the query string                         │
│    ├─ Search vector database:                        │
│    │  ├─ Similarity metric: Cosine similarity         │
│    │  ├─ Top-K results: 5-10 chunks                  │
│    │  ├─ Min similarity threshold: 0.6               │
│    │  └─ Metadata filter: Relevant sections only     │
│    │                                                 │
│    ├─ Retrieved results contain:                     │
│    │  ├─ Relevant job requirements                   │
│    │  ├─ Skill descriptions                          │
│    │  ├─ Example competencies                        │
│    │  └─ Context for follow-ups                      │
│    │                                                 │
│    └─ Re-rank results (optional):                    │
│       ├─ Use cross-encoder model                     │
│       ├─ Improve relevance ordering                  │
│       └─ Filter noise                                │
│                                                      │
│ 3. Build LLM Prompt (Few-Shot)                       │
│    ├─ System message:                                │
│    │  └─ "You are an expert technical interviewer    │
│    │     for [job role]. Generate natural,           │
│    │     engaging questions that assess              │
│    │     candidate skills based on job               │
│    │     requirements. Ensure questions are          │
│    │     open-ended and encourage detailed           │
│    │     responses."                                 │
│    │                                                 │
│    ├─ Context window:                                │
│    │  ├─ Retrieved chunks (3-5 top ones)             │
│    │  ├─ Previous Q&A pairs (for follow-ups)         │
│    │  └─ Evaluation feedback (implicit)              │
│    │                                                 │
│    ├─ Few-shot examples:                             │
│    │  ├─ Example 1: Good question for [skill 1]      │
│    │  ├─ Example 2: Good question for [skill 2]      │
│    │  └─ Example 3: Good follow-up question          │
│    │                                                 │
│    ├─ User prompt:                                   │
│    │  ├─ Next question type (follow-up/new topic)    │
│    │  ├─ Skills to assess next                       │
│    │  ├─ Difficulty level adjustment                 │
│    │  └─ Special instructions                        │
│    │                                                 │
│    └─ Parameters:                                    │
│       ├─ Model: GPT-4 or Claude 3                    │
│       ├─ Temperature: 0.7 (creative but coherent)    │
│       ├─ Max tokens: 150                             │
│       ├─ Top-p: 0.9                                  │
│       └─ Stop sequences: ["\n\n", "---"]             │
│                                                      │
│ 4. LLM Question Generation                           │
│    ├─ Call OpenAI API / Claude API                   │
│    ├─ Receive generated question                     │
│    ├─ Validate output:                               │
│    │  ├─ Length check: 20-300 characters             │
│    │  ├─ Relevance check: Matches topic              │
│    │  ├─ Uniqueness: Not duplicate                   │
│    │  ├─ Grammar check: No obvious errors            │
│    │  └─ LLM judgment: Makes sense                   │
│    │                                                 │
│    ├─ If validation fails:                           │
│    │  ├─ Retry with adjusted prompt (max 2)          │
│    │  └─ Fall back to template-based Q if needed     │
│    │                                                 │
│    └─ Store generated question:                      │
│       ├─ Question text                               │
│       ├─ Topic/category                              │
│       ├─ Difficulty level                            │
│       ├─ Expected skills                             │
│       └─ Retrieval context (chunks used)             │
│                                                      │
│ 5. Quality Assurance                                 │
│    ├─ Semantic similarity check:                     │
│    │  └─ Ensure not too similar to previous Q        │
│    │                                                 │
│    ├─ Keyword check:                                 │
│    │  └─ Ensure covers topic/skill                   │
│    │                                                 │
│    ├─ Tone check:                                    │
│    │  └─ Ensure professional and respectful          │
│    │                                                 │
│    └─ Final approval:                                │
│       └─ Question ready for TTS conversion           │
└──────────────────────────────────────────────────────┘

PHASE 3: IMPLEMENTATION DETAILS

Tech Stack Recommendations:

┌─ Framework & Libraries ─┐
│ • LangChain 0.1+        │  (Orchestration)
│ • LlamaIndex (optional) │  (Alternative to LangChain)
│ • OpenAI Python SDK     │  (API calls)
│ • Anthropic SDK         │  (Claude API)
│                         │
├─ Vector Database ──────┤
│ • Pinecone SDK          │  (Cloud)
│ • Weaviate Client       │  (Self-hosted)
│ • LangChain integrations│
│                         │
├─ Embedding Models ─────┤
│ • OpenAI embeddings     │  (Cloud, high quality)
│ • SentenceTransformers  │  (Local, free)
│ • HuggingFace Hub       │  (Wide variety)
│                         │
├─ Document Processing ──┤
│ • LangChain loaders     │  (Unified interface)
│ • PyPDF2 / pdfplumber   │  (PDF extraction)
│ • python-docx           │  (DOCX parsing)
│ • Unstructured lib      │  (Multi-format)
│                         │
├─ Validation & QA ──────┤
│ • LLM-as-judge         │  (GPT-4 validation)
│ • similarity_measures   │  (Cosine/Euclidean)
│ • spaCy / NLTK          │  (NLP checks)
│                         │
└─ Caching & Optimization─
  • Redis cache           │  (Store embeddings)
  • Local SQLite          │  (Dev environment)
  • Query result cache    │
└─────────────────────────┘
```

### 5.2 Audio Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ REAL-TIME AUDIO PROCESSING & TRANSCRIPTION SYSTEM                  │
└─────────────────────────────────────────────────────────────────────┘

STEP 1: AUDIO CAPTURE (Browser - WebRTC/Web Audio API)
┌──────────────────────────────────────────────────────┐
│ // Get user's microphone access                      │
│ navigator.mediaDevices.getUserMedia({audio: true})   │
│   .then(stream => {                                  │
│     const audioContext = new AudioContext()          │
│     const source = audioContext.createMediaStreamAudioSourceNode(stream)
│     const processor = audioContext.createScriptProcessor(4096)
│                                                      │
│     // Audio Parameters:                             │
│     - Sample rate: 16,000 Hz (44,100 Hz capture)     │
│     - Buffer size: 4,096 samples                     │
│     - Channel: Mono                                  │
│     - Bit depth: 16-bit PCM                          │
│     - Format: WAV or WebM (Opus codec)               │
│                                                      │
│     processor.onaudioprocess = (event) => {          │
│       const audioData = event.inputBuffer            │
│       // Collect audio chunks every 100ms            │
│       if (audioBuffer.length > 1600) {               │
│         sendAudioChunk(audioBuffer)                  │
│         audioBuffer = []                             │
│       }                                              │
│     }                                                │
│   })                                                 │
└──────────────────────────────────────────────────────┘

STEP 2: CLIENT-SIDE PRE-PROCESSING
┌──────────────────────────────────────────────────────┐
│ 1. Voice Activity Detection (VAD)                    │
│    ├─ Detect silence vs speech                       │
│    ├─ Tools:                                         │
│    │  ├─ Silero VAD (lightweight, open-source)       │
│    │  ├─ Picovoice Porcupine (on-device)             │
│    │  └─ WebRTC VAD (basic)                          │
│    │                                                 │
│    ├─ Parameters:                                    │
│    │  ├─ Threshold: 0.5 (speech probability)         │
│    │  ├─ Min speech duration: 500ms                  │
│    │  ├─ Min silence duration: 300ms                 │
│    │  └─ Speech buffer: Extend 50ms before/after     │
│    │                                                 │
│    └─ Output: Segments of actual speech only         │
│                                                      │
│ 2. Noise Gate & Normalization                        │
│    ├─ Discard audio below threshold (-40dB)          │
│    ├─ Normalize volume:                              │
│    │  └─ Target RMS: -20dB                           │
│    └─ Prevent clipping                               │
│                                                      │
│ 3. Downsampling (if needed)                          │
│    ├─ Resample to 16 kHz (most ASR services)         │
│    ├─ Apply low-pass filter                          │
│    └─ Method: FFmpeg.js or Web Audio API             │
│                                                      │
│ 4. Smart Audio Chunking                              │
│    ├─ Strategy: Split at natural pauses              │
│    │  ├─ Detect silence (> 300ms)                    │
│    │  ├─ Don't split mid-sentence                    │
│    │  ├─ Max chunk: 5 seconds                        │
│    │  └─ Min chunk: 500ms                            │
│    │                                                 │
│    └─ Result: Coherent audio chunks ready for STT    │
└──────────────────────────────────────────────────────┘

STEP 3: SEND TO SERVER
┌──────────────────────────────────────────────────────┐
│ // WebSocket connection for streaming                │
│ const ws = new WebSocket('wss://api.server.com/...')│
│                                                      │
│ ws.send(JSON.stringify({                             │
│   type: 'audio_chunk',                               │
│   data: audioBuffer,          // Raw PCM             │
│   format: 'wav',              // Format              │
│   sample_rate: 16000,         // Hz                  │
│   duration: 1.5,              // Seconds             │
│   timestamp: Date.now(),      // For sync            │
│   session_id: sessionId,      // Interview ID        │
│   sequence: chunkIndex        // For ordering        │
│ }))                                                  │
│                                                      │
│ // Compression (optional):                           │
│ ├─ Opus codec: ~6-8 kbps                             │
│ ├─ AAC codec: ~16-24 kbps                            │
│ └─ Reduces bandwidth by ~80%                         │
└──────────────────────────────────────────────────────┘

STEP 4: SERVER-SIDE PROCESSING
┌──────────────────────────────────────────────────────┐
│ 1. Receive & Buffer Audio                            │
│    ├─ Queue audio chunks                             │
│    ├─ Monitor queue size (max 10 chunks)             │
│    └─ Handle retransmissions                         │
│                                                      │
│ 2. Real-Time Transcription Options                   │
│    │                                                 │
│    ├─ Option A: Google Cloud Speech-to-Text         │
│    │  └─ API Endpoint: speech.googleapis.com         │
│    │  └─ Models:                                     │
│    │     ├─ default: General purpose (good)          │
│    │     ├─ numbers_and_commands: Better for tech    │
│    │     ├─ phone_call: For audio quality            │
│    │     └─ video: For video content                 │
│    │  └─ Streaming parameters:                       │
│    │     ├─ Sample rate: 16,000 Hz                   │
│    │     ├─ Encoding: LINEAR16 (WAV) or OPUS        │
│    │     ├─ Language: en-US (or target)              │
│    │     └─ Interim results: true (for real-time)    │
│    │  └─ Accuracy: 94-97% WER                        │
│    │  └─ Latency: 200-500ms (real-time)              │
│    │  └─ Cost: ~$0.024 per 15-sec block              │
│    │                                                 │
│    ├─ Option B: Azure Cognitive Services             │
│    │  └─ Real-time speech recognition                │
│    │  └─ Accuracy: 93-96% WER                        │
│    │  └─ Latency: 100-400ms                          │
│    │  └─ Cost: ~$1 per audio hour                    │
│    │                                                 │
│    ├─ Option C: OpenAI Whisper API                   │
│    │  └─ Batch/offline only (not streaming)          │
│    │  └─ Accuracy: 95%+ WER (best)                   │
│    │  └─ Latency: 5-30 seconds                       │
│    │  └─ Cost: ~$0.36 per audio hour                 │
│    │  └─ Supports 99 languages                       │
│    │                                                 │
│    └─ Option D: Picovoice Cheetah (On-Device)        │
│       └─ Local processing (no internet needed)       │
│       └─ Accuracy: 94% WER                           │
│       └─ Latency: <100ms                             │
│       └─ Cost: One-time $99/year per dev             │
│       └─ Privacy: All on-device                      │
│                                                      │
│ 3. Recommended Stack for Interview Portal:           │
│    ├─ Primary: Google Cloud Speech-to-Text           │
│    │  └─ Best balance of accuracy, cost, latency     │
│    │  └─ Streaming support for real-time            │
│    │  └─ Good language support                       │
│    │                                                 │
│    ├─ Alternative: Whisper (batch processing)        │
│    │  └─ Higher accuracy but offline only            │
│    │  └─ Use for final transcription                 │
│    │                                                 │
│    └─ Fallback: Local Silero VAD + basic model       │
│       └─ If API fails or offline                     │
└──────────────────────────────────────────────────────┘

STEP 5: REAL-TIME TRANSCRIPTION PROCESSING
┌──────────────────────────────────────────────────────┐
│ // Python pseudocode (FastAPI backend)               │
│                                                      │
│ @app.websocket("/stream_transcribe")                 │
│ async def transcribe_stream(websocket):              │
│   async with google_speech_client.streaming_recognize(
│     config=speech_config,                            │
│     requests=request_generator()                     │
│   ) as responses:                                    │
│                                                      │
│     for response in responses:                       │
│       if response.results:                           │
│         result = response.results[0]                 │
│                                                      │
│         # Interim results (partial transcription)    │
│         if not result.is_final:                      │
│           transcript = result.alternatives[0].transcript
│           confidence = result.alternatives[0].confidence
│           print(f"Interim: {transcript} ({confidence:.2%})")
│                                                      │
│           # Send to frontend in real-time            │
│           await websocket.send_json({                │
│             "type": "interim_transcript",            │
│             "text": transcript,                      │
│             "confidence": confidence,                │
│             "is_final": False                        │
│           })                                         │
│                                                      │
│         # Final result (when speech ends)            │
│         else:                                        │
│           final_transcript = result.alternatives[0].transcript
│           final_confidence = result.alternatives[0].confidence
│           print(f"Final: {final_transcript}")        │
│                                                      │
│           # Post-process final transcription         │
│           cleaned_text = post_process_transcript(    │
│             final_transcript                         │
│           )                                          │
│                                                      │
│           # Send final result                        │
│           await websocket.send_json({                │
│             "type": "final_transcript",              │
│             "text": cleaned_text,                    │
│             "confidence": final_confidence,          │
│             "is_final": True,                        │
│             "end_time": datetime.now()               │
│           })                                         │
│                                                      │
│           # Save to database                         │
│           save_transcription(                        │
│             session_id, cleaned_text, final_confidence
│           )                                          │
│                                                      │
│           # Proceed to response evaluation           │
│           await evaluate_response(cleaned_text)     │
└──────────────────────────────────────────────────────┘

STEP 6: POST-PROCESSING & CLEANUP
┌──────────────────────────────────────────────────────┐
│ 1. Text Normalization                                │
│    ├─ Fix capitalization (first word, proper nouns)  │
│    ├─ Expand contractions (can't → cannot)           │
│    ├─ Standardize numbers (1,000 → thousand)         │
│    ├─ Remove filler words (um, uh, like - optional)  │
│    └─ Fix punctuation                                │
│                                                      │
│ 2. Quality Metrics                                   │
│    ├─ Confidence score (ASR model confidence)        │
│    ├─ Word error rate (if reference available)       │
│    ├─ Audio quality metrics                          │
│    └─ Flag low-confidence segments                   │
│                                                      │
│ 3. Storage & Indexing                                │
│    ├─ Store final transcript in database             │
│    ├─ Link to question ID                            │
│    ├─ Store audio file reference                     │
│    ├─ Timestamp for entire response                  │
│    └─ Make searchable (full-text index)              │
└──────────────────────────────────────────────────────┘

PERFORMANCE TARGETS
┌──────────────────────────────────────────────────────┐
│ • ASR Accuracy (WER): < 5%                           │
│ • Transcription Latency: < 500ms (real-time)         │
│ • End-to-end Delay: < 2 seconds                      │
│ • Uptime: 99.9% (for API calls)                      │
│ • Concurrent Interviews: 100+ (architecture-dependent)
└──────────────────────────────────────────────────────┘
```

### 5.3 Avatar & Lip-Sync Generation

```
┌─────────────────────────────────────────────────────────────────────┐
│ AI AVATAR & LIP-SYNC VIDEO GENERATION SYSTEM                       │
└─────────────────────────────────────────────────────────────────────┘

ARCHITECTURE OPTIONS

OPTION 1: HeyGen API (Recommended for Production)
┌──────────────────────────────────────────────────────┐
│ Advantages:                                          │
│ ✓ 100+ pre-built realistic avatars                   │
│ ✓ Best-in-class lip-sync accuracy                    │
│ ✓ Multi-language support (40+ languages)             │
│ ✓ Expressions & natural gestures                     │
│ ✓ Fast generation (30-60 seconds per video)          │
│ ✓ Webhook support for async processing               │
│ ✓ CDN delivery                                       │
│                                                      │
│ Disadvantages:                                       │
│ ✗ API cost ($0.05-0.1 per video)                     │
│ ✗ Rate limits (needs queuing)                        │
│ ✗ Requires internet connection                       │
│                                                      │
│ Implementation:                                      │
│                                                      │
│ 1. Initialize HeyGen Client                          │
│    import requests                                   │
│    api_key = "your_heygen_api_key"                   │
│                                                      │
│ 2. Select Avatar                                     │
│    # Option A: Pre-built avatar                      │
│    avatar_id = "Avatar_18"  # ID from HeyGen library │
│                                                      │
│    # Option B: Custom avatar (upload video)          │
│    avatar_id = "custom_avatar_123"                   │
│                                                      │
│ 3. Generate Video                                    │
│    payload = {                                       │
│      "avatar_id": avatar_id,                         │
│      "voice": {                                      │
│        "voice_id": "google-en-US-Neural2-C",         │
│        "input_text": "Your question here",           │
│        "speed": 1.0                                  │
│      },                                              │
│      "video_encoding": "H264"                        │
│    }                                                 │
│                                                      │
│    response = requests.post(                         │
│      "https://api.heygen.com/v1/video_generate",    │
│      headers={"X-API-Key": api_key},                 │
│      json=payload                                    │
│    )                                                 │
│    video_id = response.json()["data"]["video_id"]    │
│                                                      │
│ 4. Poll for Completion                               │
│    # Poll every 5 seconds                            │
│    while True:                                       │
│      status_response = requests.get(                 │
│        f"https://api.heygen.com/v1/video/{video_id}",
│        headers={"X-API-Key": api_key}                │
│      )                                               │
│      status = status_response.json()["data"]["status"]
│                                                      │
│      if status == "completed":                       │
│        video_url = status_response.json()[           │
│          "data"]["video_url"                         │
│        ]                                             │
│        break                                         │
│      elif status == "failed":                        │
│        raise Exception("Video generation failed")    │
│      time.sleep(5)                                   │
│                                                      │
│ 5. Cache & Stream                                    │
│    # Download and cache video                        │
│    video_content = requests.get(video_url).content   │
│    s3.put_object(                                    │
│      Bucket=bucket,                                  │
│      Key=f"videos/{video_id}.mp4",                   │
│      Body=video_content                              │
│    )                                                 │
│                                                      │
│    # Return streaming URL                            │
│    return f"https://cdn.server.com/videos/{video_id}.mp4"
│                                                      │
│ Cost Estimate:                                       │
│ • $0.06 per 60-second video                          │
│ • 10 questions per interview                         │
│ • $0.60 per interview                                │
│ • 1000 interviews/month = $600/month                 │
└──────────────────────────────────────────────────────┘

OPTION 2: Vozo AI Lip-Sync (Alternative)
┌──────────────────────────────────────────────────────┐
│ Advantages:                                          │
│ ✓ High-quality lip-sync (next-gen generative AI)     │
│ ✓ Works with custom videos                           │
│ ✓ Multi-speaker support                              │
│ ✓ Non-frontal face support                           │
│ ✓ Can use pre-recorded avatar videos                 │
│                                                      │
│ Disadvantages:                                       │
│ ✗ Need custom avatar video source                    │
│ ✗ Longer processing time                             │
│ ✗ API less mature than HeyGen                        │
│                                                      │
│ Implementation:                                      │
│ Similar to HeyGen but with your custom video         │
│ as the source.                                       │
└──────────────────────────────────────────────────────┘

OPTION 3: Self-Hosted Wav2Lip (Cost-Saving)
┌──────────────────────────────────────────────────────┐
│ Advantages:                                          │
│ ✓ Open-source (free)                                 │
│ ✓ Full control over process                          │
│ ✓ No recurring API costs                             │
│ ✓ Works offline                                      │
│                                                      │
│ Disadvantages:                                       │
│ ✗ Requires GPU (high compute)                        │
│ ✗ Lower quality lip-sync than HeyGen                 │
│ ✗ Needs custom avatar video                          │
│ ✗ Complex setup & maintenance                        │
│                                                      │
│ Implementation:                                      │
│                                                      │
│ 1. Setup Wav2Lip                                     │
│    git clone https://github.com/Rudrabha/Wav2Lip.git
│    pip install -r requirements.txt                   │
│    # Download pre-trained model                      │
│                                                      │
│ 2. Prepare Avatar Video                              │
│    # Capture 5-10 seconds of someone speaking        │
│    avatar.mp4 (720p, 25fps, clear face)              │
│                                                      │
│ 3. Generate Speech                                   │
│    # Use TTS to create audio                         │
│    audio.wav (44.1 kHz, mono)                        │
│                                                      │
│ 4. Run Wav2Lip                                       │
│    python inference.py \\                            │
│      --checkpoint_path checkpoints/wav2lip.pth \\   │
│      --face avatar.mp4 \\                            │
│      --audio audio.wav \\                            │
│      --outfile output.mp4                            │
│                                                      │
│ 5. Post-process                                      │
│    # Re-encode for streaming                         │
│    ffmpeg -i output.mp4 -c:v libx264 \              │
│      -preset fast -crf 23 final_video.mp4            │
│                                                      │
│ Performance:                                         │
│ • Processing time: 2-5 minutes per 60s video         │
│ • GPU required: NVIDIA A100/V100 recommended         │
│ • Quality: Good but not as polished as HeyGen        │
│                                                      │
│ Cost Analysis:                                       │
│ • GPU instance: $1-3/hour (AWS g4dn.xlarge)          │
│ • 10 questions/interview × 1 min = 10 min            │
│ • Cost per interview: ~$0.50                         │
│ • 1000 interviews/month = $500 (vs $600 HeyGen)      │
│ BUT requires infrastructure management               │
└──────────────────────────────────────────────────────┘

RECOMMENDED IMPLEMENTATION: Hybrid Approach
┌──────────────────────────────────────────────────────┐
│ Use HeyGen for Production (Best Quality)             │
│                                                      │
│ Flow:                                                │
│ 1. Question generated by RAG pipeline                │
│ 2. Convert to speech (Google TTS)                    │
│ 3. Call HeyGen API to generate video                 │
│ 4. Cache video in S3                                 │
│ 5. Stream to user via CDN                            │
│                                                      │
│ Optimization:                                        │
│ • Batch requests during off-peak (10x cheaper)       │
│ • Cache frequently asked questions                   │
│ • Use webhooks for async processing                  │
│ • Implement request queue (max N concurrent)         │
│                                                      │
│ Architecture:                                        │
│                                                      │
│      Question           TTS Audio                     │
│         │                   │                         │
│         └───────┬───────────┘                         │
│                 ▼                                     │
│          HeyGen API                                   │
│          (Video Gen)                                  │
│                 │                                     │
│                 ▼                                     │
│          S3 Cache Store                               │
│          (MP4 Video)                                  │
│                 │                                     │
│                 ▼                                     │
│          CDN Distribution                             │
│          (Stream to User)                             │
│                 │                                     │
│                 ▼                                     │
│          HTML5 Video Player                           │
│          (WebRTC display)                             │
└──────────────────────────────────────────────────────┘

TEXT-TO-SPEECH CONFIGURATION
┌──────────────────────────────────────────────────────┐
│ Recommended: Google Cloud Text-to-Speech             │
│                                                      │
│ Configuration:                                       │
│ {                                                    │
│   "voice": {                                         │
│     "language_code": "en-US",                        │
│     "name": "en-US-Neural2-C",  // Professional     │
│     "ssml_gender": "MALE"                            │
│   },                                                 │
│   "audio_config": {                                  │
│     "audio_encoding": "LINEAR16",                    │
│     "pitch": 0.0,                 // Neutral         │
│     "speaking_rate": 1.0          // Normal speed    │
│   },                                                 │
│   "text": "Your interview question here..."          │
│ }                                                    │
│                                                      │
│ Cost: ~$16 per 1M characters                         │
│ • Average question: 200 characters                   │
│ • 10 questions/interview: 2,000 chars                │
│ • Cost per interview: $0.032                         │
└──────────────────────────────────────────────────────┘

VIDEO DELIVERY & OPTIMIZATION
┌──────────────────────────────────────────────────────┐
│ 1. Format & Encoding                                 │
│    ├─ Container: MP4 (H.264)                         │
│    ├─ Resolution: 1080p (1920x1080)                  │
│    ├─ FPS: 24/25                                     │
│    ├─ Bitrate: 2-4 Mbps                              │
│    └─ File size: ~30-40 MB per minute                │
│                                                      │
│ 2. Streaming Protocol                                │
│    ├─ HLS (HTTP Live Streaming) - Safari friendly    │
│    ├─ DASH (Dynamic Adaptive Streaming)              │
│    └─ Progressive download (for simplicity)          │
│                                                      │
│ 3. CDN Configuration                                 │
│    ├─ CloudFront / Cloudflare / Akamai               │
│    ├─ Edge caching: 24-48 hours                      │
│    ├─ Geo-replication                                │
│    └─ DDoS protection                                │
│                                                      │
│ 4. Bandwidth Optimization                            │
│    ├─ Adaptive bitrate streaming                     │
│    ├─ Range requests (pause/resume)                  │
│    └─ Preload next question video                    │
└──────────────────────────────────────────────────────┘
```

### 5.4 Response Evaluation Engine

```
┌─────────────────────────────────────────────────────────────────────┐
│ RESPONSE EVALUATION & SCORING SYSTEM                               │
└─────────────────────────────────────────────────────────────────────┘

EVALUATION FRAMEWORK

Input Data:
├─ Transcribed response (text)
├─ Question asked (text)
├─ Job requirements context (from RAG)
├─ Candidate metadata (experience level, etc.)
└─ Interview context (previous Q&A)

PHASE 1: LLM-BASED SEMANTIC EVALUATION
┌──────────────────────────────────────────────────────┐
│ 1. Build Evaluation Prompt                           │
│                                                      │
│    system_prompt = """                               │
│    You are an expert technical interviewer and       │
│    evaluator. Your task is to evaluate a candidate's │
│    response to an interview question based on:       │
│                                                      │
│    1. Relevance: Does it answer the question?        │
│    2. Accuracy: Is the technical content correct?    │
│    3. Completeness: Does it cover key points?        │
│    4. Clarity: Is it well-explained?                 │
│    5. Confidence: Does the candidate sound          │
│       confident and knowledgeable?                   │
│    6. Depth: Does it show expertise or just          │
│       surface knowledge?                             │
│    7. Soft Skills: Communication, professionalism    │
│                                                      │
│    Provide a structured evaluation with scores       │
│    and specific feedback.                            │
│    """                                               │
│                                                      │
│ 2. Construct Context Window                          │
│                                                      │
│    context = {                                       │
│      "job_requirements": job_jd_summary,             │
│      "question": "What is your experience with...", │
│      "response": "The candidate's transcribed...",   │
│      "previous_qa": [previous_questions_and_scores], │
│      "candidate_profile": {                          │
│        "years_of_experience": 5,                     │
│        "role_level": "mid-level",                    │
│        "location": "..."                             │
│      }                                               │
│    }                                                 │
│                                                      │
│ 3. Create Few-Shot Examples                          │
│                                                      │
│    examples = [                                      │
│      {                                               │
│        "question": "Example Q1",                     │
│        "response": "Good example response",          │
│        "evaluation": {                               │
│          "relevance_score": 9,                       │
│          "accuracy_score": 9,                        │
│          "completeness_score": 8,                    │
│          ...                                         │
│          "overall_score": 8.5,                       │
│          "feedback": "Strong answer, covered..."     │
│        }                                             │
│      },                                              │
│      ...                                             │
│    ]                                                 │
│                                                      │
│ 4. Format Final Prompt                               │
│                                                      │
│    prompt = f"""                                     │
│    Job Role: {context['job_requirements']}          │
│                                                      │
│    Question: {context['question']}                  │
│    Candidate's Response: {context['response']}      │
│                                                      │
│    Please evaluate this response on the             │
│    following criteria (1-10 scale):                 │
│                                                      │
│    1. Relevance (does it address the question?)     │
│    2. Technical Accuracy                             │
│    3. Completeness of answer                        │
│    4. Clarity and Communication                     │
│    5. Confidence and Professionalism                │
│    6. Depth of Knowledge                            │
│    7. Problem-Solving Approach (if applicable)      │
│                                                      │
│    Provide your evaluation in JSON format.          │
│    """                                               │
│                                                      │
│ 5. Call LLM (GPT-4 / Claude 3)                       │
│                                                      │
│    response = openai.ChatCompletion.create(          │
│      model="gpt-4",                                  │
│      messages=[                                      │
│        {"role": "system", "content": system_prompt}, │
│        {"role": "user", "content": prompt}           │
│      ],                                              │
│      temperature=0.3,  // Consistent, factual        │
│      response_format="json_object"                   │
│    )                                                 │
│                                                      │
│ 6. Parse LLM Response                                │
│                                                      │
│    evaluation = json.loads(response.content)        │
│    {                                                 │
│      "relevance": 8,                                 │
│      "accuracy": 9,                                  │
│      "completeness": 7,                              │
│      "clarity": 8,                                   │
│      "confidence": 8,                                │
│      "depth": 7,                                     │
│      "problem_solving": 8,                           │
│      "overall_score": 7.9,                           │
│      "strengths": ["Good understanding of...", "..."],
│      "improvements": ["Could have mentioned...", "..."],
│      "red_flags": [],  // Or list any concerns       │
│      "hire_recommendation": "STRONG_YES"             │
│    }                                                 │
└──────────────────────────────────────────────────────┘

PHASE 2: ADDITIONAL EVALUATION METRICS
┌──────────────────────────────────────────────────────┐
│ 1. Response Length Analysis                          │
│    ├─ Word count                                    │
│    ├─ Speaking duration                              │
│    ├─ Normalized score based on question type        │
│    │  ├─ Short Q (yes/no): Expected 30-60 secs       │
│    │  ├─ Medium Q (explain): Expected 1-2 mins       │
│    │  └─ Long Q (problem-solving): Expected 3+ mins  │
│    └─ Alert if too short (possibly weak answer)      │
│                                                      │
│ 2. Sentiment & Tone Analysis                         │
│    ├─ Use HuggingFace transformers                   │
│    ├─ Detect sentiment: positive/negative/neutral    │
│    ├─ Confidence level (high/medium/low)             │
│    ├─ Professionalism score                          │
│    └─ Flag if negative sentiment (anxiety?)          │
│                                                      │
│ 3. Keyword Matching                                  │
│    ├─ Extract expected keywords from job desc        │
│    ├─ Search for them in candidate response          │
│    ├─ Calculate keyword density                      │
│    ├─ Score: % of important keywords mentioned       │
│    └─ Penalize if key terms missing                  │
│                                                      │
│ 4. Communication Quality                             │
│    ├─ Filler words detection (um, uh, like)          │
│    ├─ Sentence structure complexity                  │
│    ├─ Use of technical jargon (if appropriate)       │
│    ├─ Clarity score (easier for non-experts)         │
│    └─ Professionalism indicators                     │
│                                                      │
│ 5. Skill Pattern Recognition                         │
│    ├─ Extract mentioned skills from response         │
│    ├─ Match against job requirements                 │
│    ├─ Classify as: Required / Nice-to-have / Extra   │
│    ├─ Experience level inference                     │
│    └─ Consistency with previous answers              │
└──────────────────────────────────────────────────────┘

PHASE 3: SCORING CALCULATION
┌──────────────────────────────────────────────────────┐
│ Weighted Scoring Model:                              │
│                                                      │
│ final_score = Σ(score_i × weight_i)                 │
│                                                      │
│ Components:                                          │
│ ├─ LLM Overall Score: 50% (main evaluation)          │
│ ├─ Technical Accuracy: 20%                           │
│ ├─ Communication Quality: 15%                        │
│ ├─ Keyword Matching: 10%                             │
│ └─ Response Length Appropriateness: 5%               │
│                                                      │
│ Example Calculation:                                 │
│ LLM score: 8.5 × 0.50 = 4.25                        │
│ Technical: 9.0 × 0.20 = 1.80                        │
│ Communication: 8.0 × 0.15 = 1.20                    │
│ Keywords: 7.5 × 0.10 = 0.75                         │
│ Response Length: 8.0 × 0.05 = 0.40                  │
│                                                      │
│ FINAL SCORE = 4.25 + 1.80 + 1.20 + 0.75 + 0.40      │
│             = 8.40 / 10                              │
│                                                      │
│ Scale Interpretation:                                │
│ 9-10: Exceptional (Strong Hire)                      │
│ 8-9:  Very Good (Hire)                               │
│ 7-8:  Good (Consider)                                │
│ 6-7:  Fair (Maybe)                                   │
│ 5-6:  Poor (Unlikely)                                │
│ <5:   Very Poor (No Hire)                            │
└──────────────────────────────────────────────────────┘

PHASE 4: INTERVIEW-LEVEL SCORING
┌──────────────────────────────────────────────────────┐
│ Overall Interview Score:                             │
│                                                      │
│ interview_score = Σ(question_score_i) / num_questions
│                                                      │
│ With optional weighting by question difficulty:      │
│                                                      │
│ weighted_score = Σ(score_i × difficulty_weight_i)    │
│                  / Σ(difficulty_weight_i)             │
│                                                      │
│ Example (8 questions):                               │
│ Q1 (Easy): 8.0 × 1.0 = 8.0                          │
│ Q2 (Medium): 7.5 × 1.2 = 9.0                        │
│ Q3 (Easy): 8.5 × 1.0 = 8.5                          │
│ Q4 (Hard): 6.0 × 1.5 = 9.0                          │
│ Q5 (Medium): 7.0 × 1.2 = 8.4                        │
│ Q6 (Medium): 8.0 × 1.2 = 9.6                        │
│ Q7 (Hard): 7.5 × 1.5 = 11.25                        │
│ Q8 (Easy): 8.5 × 1.0 = 8.5                          │
│                                                      │
│ Total weighted: 71.85                                │
│ Total weights: 9.4                                   │
│ FINAL INTERVIEW SCORE: 71.85 / 9.4 = 7.64 / 10     │
│ Recommendation: GOOD (Consider for next round)       │
└──────────────────────────────────────────────────────┘

PHASE 5: RED FLAG DETECTION
┌──────────────────────────────────────────────────────┐
│ Automatic alerts for:                                │
│                                                      │
│ ├─ Missing key competencies (0% keyword match)       │
│ ├─ Inconsistent answers (contradiction with Q2+)     │
│ ├─ Potential plagiarism (exact phrase matches online)│
│ ├─ Very low confidence on core skills                │
│ ├─ No previous experience in required areas          │
│ ├─ Negative sentiment (anger, frustration)           │
│ ├─ Technical inaccuracies in core skills             │
│ └─ Communication barriers (language, clarity)        │
│                                                      │
│ Actions:                                             │
│ ├─ Flag for recruiter review                         │
│ ├─ Request additional clarification Q&A              │
│ ├─ Schedule follow-up interview                      │
│ └─ Notify candidate of concerns                      │
└──────────────────────────────────────────────────────┘

STORAGE & REPORTING
┌──────────────────────────────────────────────────────┐
│ Store evaluation results:                            │
│                                                      │
│ {                                                    │
│   "interview_id": "int_12345",                       │
│   "question_id": "q_789",                            │
│   "timestamp": "2024-01-15T10:30:00Z",               │
│   "transcription": "Candidate's full response...",   │
│   "evaluation": {                                    │
│     "llm_scores": {...},                             │
│     "sentiment": {...},                              │
│     "keywords": {...},                               │
│     "communication": {...},                          │
│     "final_score": 8.4,                              │
│     "recommendation": "HIRE"                         │
│   },                                                 │
│   "metadata": {                                      │
│     "asr_confidence": 0.95,                          │
│     "evaluation_model": "gpt-4",                     │
│     "processing_time_ms": 3500,                      │
│     "llm_tokens_used": 1200                          │
│   }                                                  │
│ }                                                    │
│                                                      │
│ Query for reports:                                   │
│ ├─ Get all scores for a candidate                    │
│ ├─ Filter by score range                             │
│ ├─ Identify common weak areas                        │
│ ├─ Generate hiring recommendations                   │
│ └─ Compare against benchmarks                        │
└──────────────────────────────────────────────────────┘
```

---

## 6. DATABASE SCHEMA

```sql
-- Users Table
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  role ENUM('candidate', 'recruiter', 'admin'),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interview Sessions
CREATE TABLE interview_sessions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  job_id VARCHAR(100),
  job_title VARCHAR(255),
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  total_duration_seconds INT,
  status ENUM('in_progress', 'completed', 'abandoned'),
  interview_type ENUM('job_requirements', 'topic_based'),
  context_content TEXT,  -- Uploaded JD or topic
  overall_score DECIMAL(3,2),
  recommendation ENUM('strong_yes', 'yes', 'maybe', 'no', 'strong_no'),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Questions
CREATE TABLE questions (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES interview_sessions(id),
  question_text TEXT NOT NULL,
  question_type ENUM('technical', 'behavioral', 'system_design'),
  difficulty ENUM('easy', 'medium', 'hard'),
  category VARCHAR(100),
  order_in_interview INT,
  generated_by ENUM('rag_llm', 'template', 'custom'),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Responses
CREATE TABLE responses (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES interview_sessions(id),
  question_id UUID REFERENCES questions(id),
  raw_transcription TEXT,
  cleaned_transcription TEXT,
  asr_confidence DECIMAL(3,2),
  audio_file_path VARCHAR(500),
  video_file_path VARCHAR(500),
  response_duration_seconds INT,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Evaluations
CREATE TABLE evaluations (
  id UUID PRIMARY KEY,
  response_id UUID REFERENCES responses(id),
  session_id UUID REFERENCES interview_sessions(id),
  question_id UUID REFERENCES questions(id),
  relevance_score DECIMAL(3,2),
  accuracy_score DECIMAL(3,2),
  completeness_score DECIMAL(3,2),
  clarity_score DECIMAL(3,2),
  confidence_score DECIMAL(3,2),
  depth_score DECIMAL(3,2),
  communication_score DECIMAL(3,2),
  overall_score DECIMAL(3,2),
  feedback_text TEXT,
  strengths JSON,
  improvements JSON,
  red_flags JSON,
  sentiment VARCHAR(50),
  keywords_found JSON,
  evaluation_model VARCHAR(50),  -- gpt-4, claude-3, etc.
  llm_tokens_used INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RAG Documents (for knowledge base)
CREATE TABLE rag_documents (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES interview_sessions(id),
  document_name VARCHAR(255),
  document_type ENUM('pdf', 'docx', 'txt', 'json'),
  original_file_path VARCHAR(500),
  content TEXT,
  chunk_count INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RAG Chunks (for vector DB references)
CREATE TABLE rag_chunks (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES rag_documents(id),
  chunk_index INT,
  chunk_text TEXT,
  embedding_id VARCHAR(255),  -- Reference to vector DB
  chunk_tokens INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Avatar Cache (for generated videos)
CREATE TABLE avatar_videos (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES interview_sessions(id),
  question_id UUID REFERENCES questions(id),
  question_text TEXT,
  audio_file_path VARCHAR(500),
  video_file_path VARCHAR(500),
  video_duration_seconds INT,
  avatar_id VARCHAR(100),
  lip_sync_quality DECIMAL(3,2),
  generation_time_seconds INT,
  provider ENUM('heygen', 'vozo', 'wav2lip'),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expiry_date TIMESTAMP
);

-- Indices for performance
CREATE INDEX idx_sessions_user ON interview_sessions(user_id);
CREATE INDEX idx_responses_session ON responses(session_id);
CREATE INDEX idx_evaluations_response ON evaluations(response_id);
CREATE INDEX idx_questions_session ON questions(session_id);
CREATE INDEX idx_rag_documents_session ON rag_documents(session_id);
CREATE INDEX idx_avatar_videos_session ON avatar_videos(session_id);
```

---

## 7. API ENDPOINTS

```
# Interview Management
POST /api/interviews/create
  - Create new interview session
  - Input: job_title, interview_type (job_req | topic)
  - Return: session_id, interview_token

POST /api/interviews/:session_id/start
  - Initialize interview (load avatar, prepare questions)
  - Return: first_question, avatar_video_url

GET /api/interviews/:session_id/status
  - Get current interview state
  - Return: current_question, time_elapsed, responses_count

POST /api/interviews/:session_id/end
  - Conclude interview, generate report
  - Return: final_score, report_url

# Document Management
POST /api/documents/upload
  - Upload job requirements or topic
  - Input: file, session_id
  - Return: document_id, chunks_count

POST /api/documents/process
  - Process document, create embeddings, index in RAG
  - Input: document_id
  - Return: status, chunks_indexed, ready_for_questions

# Question Generation
GET /api/questions/generate
  - Generate next interview question
  - Input: session_id, previous_responses_summary
  - Return: question_text, question_id, category

# Audio Processing
POST /api/audio/transcribe
  - Real-time transcription (WebSocket)
  - Input: audio_stream (WebSocket)
  - Return: interim_transcript, final_transcript, confidence

# Response Evaluation
POST /api/responses/evaluate
  - Evaluate candidate response
  - Input: question_id, transcription, audio_duration
  - Return: score, feedback, red_flags

# Reporting
GET /api/reports/interview/:session_id
  - Get comprehensive interview report
  - Return: scores_by_question, overall_score, recommendation, video_clips

GET /api/reports/candidate/:user_id
  - Get all interview reports for candidate
  - Return: list of interviews, scores, progression

POST /api/reports/export
  - Export report as PDF/Excel
  - Input: session_id, format
  - Return: download_url

# Analytics
GET /api/analytics/dashboard
  - Hiring team dashboard
  - Return: top_candidates, common_weak_areas, hiring_metrics

GET /api/analytics/benchmarks
  - Compare candidate against benchmarks
  - Input: role, experience_level
  - Return: comparative_scores, percentile
```

---

## 8. DEPLOYMENT ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────────┐
│ PRODUCTION DEPLOYMENT STACK                                      │
└──────────────────────────────────────────────────────────────────┘

Frontend:
├─ React/Vue SPA hosted on Vercel/Netlify
├─ CDN: Cloudflare for static assets
├─ Video streaming via CDN

Backend:
├─ Containerized with Docker
├─ API: FastAPI (Python) or Express.js (Node)
├─ Deployment: AWS ECS, Google Cloud Run, or Kubernetes
├─ Load Balancer: Application Load Balancer

Databases:
├─ PostgreSQL (RDS) for relational data
├─ Redis (ElastiCache) for sessions
├─ Pinecone / Weaviate for vectors
├─ MongoDB (optional) for flexible schemas

External Services:
├─ HeyGen API (avatar & lip-sync)
├─ Google Cloud Speech-to-Text (transcription)
├─ OpenAI GPT-4 (question generation & evaluation)
├─ Google Cloud Text-to-Speech (TTS)
├─ AWS S3 / GCS (file storage)

Monitoring:
├─ DataDog / New Relic for APM
├─ CloudWatch for logs
├─ Sentry for error tracking
└─ Custom metrics for business KPIs

CI/CD:
├─ GitHub Actions for deployments
├─ Automated testing on push
├─ Staging environment for QA
└─ Blue-green deployments
```

---

## 9. IMPLEMENTATION TIMELINE

**Phase 1 (Weeks 1-2): Foundation**
- [ ] Set up project structure & repositories
- [ ] Design database schema
- [ ] Implement user auth (JWT/OAuth)
- [ ] Build basic React UI

**Phase 2 (Weeks 3-4): Core Features**
- [ ] Document upload & RAG indexing
- [ ] WebRTC video capture setup
- [ ] Web Audio API for recording
- [ ] Basic question generation (template-based)

**Phase 3 (Weeks 5-6): AI Integration**
- [ ] Integrate Google STT for transcription
- [ ] Integrate HeyGen API for avatars
- [ ] TTS integration (Google/ElevenLabs)
- [ ] RAG-based question generation (LangChain)

**Phase 4 (Weeks 7-8): Evaluation**
- [ ] LLM-based evaluation pipeline
- [ ] Scoring calculation engine
- [ ] Report generation
- [ ] Testing & optimization

**Phase 5 (Week 9): Polish & Deploy**
- [ ] Frontend refinement
- [ ] Performance optimization
- [ ] Security audit
- [ ] Production deployment

---

## 10. COST ESTIMATION (Monthly)

```
API Calls:
├─ Speech-to-Text (Google): $0.03/15-sec block
│  └─ 1000 interviews × 10 min avg = $2,400
├─ GPT-4 API (questions + evaluation): $0.05/1K tokens
│  └─ 1000 interviews × 50K tokens = $2,500
├─ Text-to-Speech: $0.016 per 1M characters
│  └─ 1000 interviews × 2K chars = $32
└─ HeyGen (avatar videos): $0.06 per video
   └─ 1000 interviews × 8-10 videos = $4,800-6,000

Infrastructure:
├─ Backend (AWS EC2): $500-1,000
├─ Database (RDS): $300-500
├─ Redis: $100
├─ S3 Storage: $100-200
├─ CDN (Cloudflare): $0-200
└─ Vector DB (Pinecone): $200-500

Total: $10,000-$15,000/month (for 1000 interviews)

Optimizations:
├─ Batch API calls (10x cheaper)
├─ Cache frequently generated videos
├─ Compress old videos (cold storage)
└─ Use open-source alternatives where possible
```

---

## 11. TECH STACK SUMMARY

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React 18 + TypeScript | Rich ecosystem, great for real-time UI |
| **Backend** | FastAPI (Python) | Async support, easy integration with ML/AI |
| **Database** | PostgreSQL + Redis | Reliable, scalable, great for interviews |
| **Vector DB** | Pinecone | Managed, easy to scale, good accuracy |
| **LLM Orchestration** | LangChain | Abstracts API complexity, supports RAG |
| **Speech-to-Text** | Google Cloud STT | Best accuracy-cost balance |
| **Text-to-Speech** | Google Cloud TTS | Natural voices, supports multiple languages |
| **Avatar & Lip-Sync** | HeyGen API | Best-in-class quality, reliable |
| **LLM Backend** | GPT-4 / Claude 3 | Best for evaluation & generation |
| **Deployment** | Docker + Kubernetes | Scalable, industry standard |
| **CI/CD** | GitHub Actions | Native GitHub integration |
| **Monitoring** | DataDog | Comprehensive APM & logging |

---

## 12. KEY CHALLENGES & SOLUTIONS

| Challenge | Solution |
|-----------|----------|
| **ASR Accuracy in noisy environments** | Implement VAD + noise gate, use high-quality models (Google STT) |
| **Lip-sync latency** | Pre-generate videos, cache frequently asked Q, use CDN |
| **Cost at scale** | Batch API calls, implement smart caching, consider hybrid on-prem/cloud |
| **Avatar not looking realistic** | Use HeyGen (professional avatars), not self-hosted Wav2Lip |
| **LLM hallucinations in evaluation** | Fine-tune prompts, implement validation, use GPT-4 (more accurate) |
| **RAG question relevance** | Use semantic chunking, hybrid BM25 + dense retrieval, human review |
| **Interview flow naturalness** | Implement context awareness, follow-up questions, adaptive difficulty |
| **Data privacy/compliance** | Encrypt data at rest & in transit, implement GDPR policies, audit trails |

---

## CONCLUSION

This architecture provides a scalable, production-ready foundation for your AI interview portal. The combination of:

1. **HeyGen for realistic avatars** with perfect lip-sync
2. **RAG pipeline** for intelligent, contextual question generation
3. **High-accuracy transcription** (Google STT) with real-time processing
4. **LLM-based evaluation** for fair, consistent scoring
5. **Comprehensive reporting** for hiring teams

...creates a compelling alternative to traditional interviews while maintaining authenticity and fairness.

**Start with Phase 1-2 (core infrastructure), then incrementally add AI layers. This allows for iterative improvement and cost optimization.**
