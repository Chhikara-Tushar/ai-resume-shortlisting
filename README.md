# AI-Powered Resume Shortlisting System

A full-stack AI-powered platform for resume shortlisting with three roles: **Admin**, **Recruiter**, and **Candidate**.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 + Tailwind CSS |
| Backend | FastAPI (Python 3.11) |
| Database | PostgreSQL 15 |
| Vector DB | FAISS (in-process) |
| AI/NLP | Sentence Transformers + OpenAI GPT-4o-mini |
| Auth | JWT (access + refresh tokens) |
| Deployment | Docker + Nginx |

## Quick Start

### 1. Configure environment
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Start with Docker
```bash
docker compose up --build
```

The app will be available at **http://localhost**

- Frontend: http://localhost
- API docs: http://localhost/docs
- Backend API: http://localhost/api

### 3. Create first admin user
After startup, register a user via the UI and then manually set their role to `admin` in the DB:
```sql
UPDATE users SET role = 'admin' WHERE email = 'your@email.com';
```

## Local Development (without Docker)

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
# Set DATABASE_URL to your local PostgreSQL
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install --legacy-peer-deps
NEXT_PUBLIC_API_URL=http://localhost:8000/api npm run dev
```

## Features

### Admin Panel
- User & recruiter management
- Real-time analytics dashboard
- Activity trend charts
- System settings configuration

### Recruiter Panel  
- Job creation with skill requirements
- AI-powered candidate ranking
- Semantic skill matching
- Candidate shortlisting/rejection
- LLM-generated hiring insights
- Side-by-side candidate comparison

### Candidate Panel
- Resume upload (PDF/DOCX)
- AI resume parsing & analysis
- ATS score with breakdown
- Skill gap analysis
- AI job recommendations
- Application tracking
- AI chatbot assistant

## AI Engine

| Component | Description |
|---|---|
| Resume Parser | pdfplumber + spaCy NER |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| Vector Search | FAISS IndexFlatIP |
| Ranking | Weighted: 40% semantic + 25% skills + 20% experience + 15% ATS |
| Insights | OpenAI GPT-4o-mini (with mock fallback if no key) |
| Chatbot | RAG-based with chat history |

## Project Structure

```
├── backend/           FastAPI application
│   ├── app/
│   │   ├── api/v1/    Route handlers
│   │   ├── ai/        AI engine modules
│   │   ├── models/    SQLAlchemy models
│   │   ├── schemas/   Pydantic schemas
│   │   └── services/  Business logic
│   └── Dockerfile
├── frontend/          Next.js 14 application
│   └── src/
│       ├── app/       Pages (App Router)
│       ├── components/ Reusable UI
│       ├── lib/       API client
│       └── store/     Zustand state
├── nginx/             Reverse proxy config
├── docker-compose.yml
└── .env.example
```

## Environment Variables

See `.env.example` for all required variables. The system works **without** an OpenAI API key (uses fallback mock responses). To enable full AI features, set `OPENAI_API_KEY`.
