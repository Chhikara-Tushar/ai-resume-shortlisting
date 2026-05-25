from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import create_tables
from app.api.v1 import auth, admin, recruiter, candidate, jobs, ai_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.FAISS_INDEX_DIR, exist_ok=True)
    # Load FAISS indexes lazily — vector_store auto-loads on first use
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-Powered Resume Shortlisting System API",
    lifespan=lifespan,
)

_cors_origins = settings.get_cors_origins()
_allow_all = "*" in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else _cors_origins,
    allow_credentials=False if _allow_all else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(recruiter.router, prefix="/api/v1/recruiter", tags=["Recruiter"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(candidate.router, prefix="/api/v1/candidate", tags=["Candidate"])
app.include_router(ai_routes.router, prefix="/api/v1/ai", tags=["AI"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": settings.APP_NAME}
