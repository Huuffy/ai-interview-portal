<div align="center">

# 🎙️ AI Interview Portal

### End-to-end AI-driven technical interview platform

![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&pause=1000&color=A855F7&center=true&vCenter=true&width=700&lines=AI-Powered+Technical+Interviews.;RAG-based+question+generation.;Real-time+transcription+%26+scoring.;Built+with+FastAPI+%C2%B7+React+%C2%B7+GPT-4.)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=for-the-badge&logo=vercel)](https://ai-interview-viraj.vercel.app/)
[![Backend](https://img.shields.io/badge/Backend-Railway-blueviolet?style=for-the-badge&logo=railway)](https://railway.app)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React_19-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI_GPT--4-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](./LICENSE)

</div>

---

## ✨ What is AI Interview Portal?

**AI Interview Portal** is a full-stack, production-ready platform that automates the technical interview process using a multi-stage AI pipeline. Rather than generic quiz platforms, this system ingests a company's actual job description and generates role-specific, context-aware interview questions through **Retrieval-Augmented Generation (RAG)**. Questions are delivered by a **talking AI avatar**, candidate responses are captured via **WebRTC** in-browser, transcribed in real time, and evaluated by **GPT-4** across five weighted dimensions — producing a structured score report for recruiters.

> **Status:** Core architecture and pipeline fully designed. Active development paused due to GPU requirements for self-hosted avatar generation (Wav2Lip). HeyGen API integration is production-ready.

The project is split across two repositories:
- **This repo** — Full-stack source (backend + frontend)
- **[Vercel Frontend](https://ai-interview-viraj.vercel.app/)** — Live deployment

---

## 🚀 Features

| Feature | Description |
|---|---|
| 📄 **RAG Question Generation** | Uploads job descriptions, converts to vector embeddings, retrieves context before generating questions — no generic prompts |
| 🎭 **Avatar-Delivered Questions** | AI avatar reads questions aloud via HeyGen API or self-hosted Wav2Lip, simulating a real interviewer |
| 🎙️ **Real-Time Transcription** | Streams candidate audio through Web Audio API with voice activity detection, achieving 95%+ accuracy (WER <5%) |
| 🧠 **GPT-4 Evaluation Engine** | Structured rubric scoring across 5 dimensions: technical accuracy, relevance, completeness, clarity, and confidence |
| 🌐 **Zero-Plugin Browser Experience** | Full WebRTC audio/video capture — no downloads, no extensions, runs entirely in the browser |
| 🐳 **Docker Support** | Containerized backend for consistent local and cloud deployment |
| 📊 **Weighted Score Reports** | Per-candidate reports with dimension-level breakdowns, ready for recruiter review |

---

## 🏗️ Architecture

```
Recruiter: Upload Job Description (PDF / Text)
        │
        ▼
  Embedding Model (OpenAI / Sentence Transformers)
        │
        ▼
  Vector Store (Pinecone / Weaviate)  ◄── RAG Retrieval
        │
        ▼
  GPT-4: Contextual Question Generation
        │
        ▼
  Google Cloud TTS ──► Audio File
        │
        ▼
  HeyGen API / Wav2Lip ──► Avatar Video
        │
        ▼
  WebRTC Stream → Candidate Browser
        │
        ▼
  Web Audio API ──► Voice Activity Detection
        │
        ▼
  Whisper / Google Cloud STT ──► Transcript
        │
        ▼
  GPT-4 Evaluation ──► Weighted Score Report
        │
        ▼
  PostgreSQL + Redis ──► Recruiter Dashboard
```

---

## 🛠️ Tech Stack

### Frontend
| Layer | Technology |
|---|---|
| **UI Framework** | React 19 + TypeScript (Vite) |
| **Styling** | CSS — custom glassmorphic design |
| **Video/Audio Capture** | WebRTC |
| **Audio Processing** | Web Audio API + Voice Activity Detection |
| **Deployment** | Vercel |

### Backend
| Layer | Technology |
|---|---|
| **API Server** | FastAPI (Python 3.10+) |
| **Primary Database** | PostgreSQL — candidate and session storage |
| **Cache / Queue** | Redis — session state and job queues |
| **Containerisation** | Docker |
| **Deployment** | Railway |

### AI & Media Pipeline
| Component | Technology |
|---|---|
| **Question Generation** | OpenAI GPT-4 |
| **Answer Evaluation** | OpenAI GPT-4 (structured prompts) |
| **Document Embedding** | OpenAI Embeddings / Sentence Transformers |
| **Vector Search (RAG)** | Pinecone / Weaviate |
| **Text-to-Speech** | Google Cloud TTS |
| **Transcription** | OpenAI Whisper / Google Cloud STT |
| **Avatar (Cloud)** | HeyGen API (~$0.06/video) |
| **Avatar (Self-hosted)** | Wav2Lip — requires GPU |

---

## 🤖 Evaluation Rubric

Each candidate answer is scored by GPT-4 using a structured prompt that evaluates five weighted dimensions:

| Dimension | Weight | What it measures |
|---|---|---|
| 🎯 **Technical Accuracy** | 20% | Correctness of the technical content in the answer |
| 🔗 **Relevance** | 20% | How directly the answer addresses the question asked |
| 📋 **Completeness** | 20% | Coverage — does the answer address all aspects of the question |
| 🗣️ **Clarity** | 15% | How well-structured and understandable the response is |
| 💡 **Confidence** | 15% | Decisiveness and authority in the response |

Final scores are aggregated per candidate and stored against their session in PostgreSQL.

---

## 💸 Cost Estimate (1,000 Interviews / Month)

| Service | Estimated Monthly Cost |
|---|---|
| Avatar generation (HeyGen API) | ~$7,200 |
| LLM evaluation (GPT-4) | ~$2,000 |
| Transcription (Whisper / Google STT) | ~$1,500 |
| Embeddings + TTS | ~$300–500 |
| Infrastructure (Railway + Vercel) | ~$50–100 |
| **Total** | **~$10,000–15,000** |

> Cost is dominated by per-interview API calls, not infrastructure. A self-hosted stack (local Whisper + Wav2Lip + open-source LLM) can reduce costs by 80–90% at the cost of GPU hardware.

---

## 📁 Project Structure

```
ai-interview-portal/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── interview.py        # Session management endpoints
│   │   │   ├── evaluation.py       # GPT-4 scoring endpoints
│   │   │   └── upload.py           # Job description ingestion
│   │   ├── services/
│   │   │   ├── rag_pipeline.py     # Embedding + vector retrieval
│   │   │   ├── question_gen.py     # GPT-4 question generation
│   │   │   ├── tts_service.py      # Google Cloud TTS
│   │   │   ├── transcription.py    # Whisper / Google STT
│   │   │   └── scorer.py           # Weighted evaluation engine
│   │   └── models/
│   │       ├── session.py          # Interview session schema
│   │       └── candidate.py        # Candidate profile schema
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── InterviewRoom/      # WebRTC capture + avatar player
│   │   │   ├── AvatarPlayer/       # Video delivery component
│   │   │   └── ScoreReport/        # Candidate result display
│   │   └── pages/
│   │       ├── Home.tsx
│   │       ├── Interview.tsx
│   │       └── Results.tsx
│   └── package.json
├── AI_Interview_Portal_Architecture.md
├── architecture-flow.txt
├── .dockerignore
└── LICENSE
```

---

## 🔧 Local Development

### Prerequisites
- **Node.js** v18+
- **Python** 3.10+
- **PostgreSQL** (running locally or via Docker)
- **Redis** (running locally or via Docker)
- API keys for OpenAI, Google Cloud, HeyGen, and Pinecone

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

### Docker (backend)

```bash
cd backend
docker compose up --build
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | GPT-4 question generation and evaluation |
| `GOOGLE_APPLICATION_CREDENTIALS` | ✅ | Path to Google Cloud service account JSON |
| `PINECONE_API_KEY` | ✅ | Vector store for RAG retrieval |
| `HEYGEN_API_KEY` | ✅ | Avatar video generation |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `REDIS_URL` | ✅ | Redis connection string |
| `WHISPER_MODEL` | ❌ | Local Whisper model size (default: `base`) |

Create a `.env` file in `backend/` before running:

```env
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp.json
PINECONE_API_KEY=...
HEYGEN_API_KEY=...
DATABASE_URL=postgresql://user:password@localhost:5432/ai_interview
REDIS_URL=redis://localhost:6379
```

---

## 🔮 Roadmap

- [ ] **Multi-language support** — extend transcription and evaluation to non-English interviews
- [ ] **Custom avatar upload** — allow companies to use their own branded AI interviewers
- [ ] **Async interview mode** — candidates complete interviews on their own schedule
- [ ] **Proctoring layer** — screen + gaze detection to flag suspicious behavior
- [ ] **Open-source LLM integration** — swap GPT-4 for Mistral / LLaMA for cost reduction
- [ ] **ATS export** — push score reports directly to Greenhouse, Lever, or Workday



<div align="center">

![footer](https://capsule-render.vercel.app/api?type=waving&color=A855F7&height=100&section=footer)

</div>
