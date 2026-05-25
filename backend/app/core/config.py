from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "AI Resume Shortlisting System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database — Railway provides postgresql://, we need postgresql+asyncpg://
    DATABASE_URL: str = "postgresql+asyncpg://resume_user:resume_pass@localhost:5432/resume_db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        if v.startswith("postgres://") and "+asyncpg" not in v:
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v

    # Auth
    SECRET_KEY: str = secrets.token_hex(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    HF_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # File storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "doc"]

    # FAISS
    FAISS_INDEX_DIR: str = "./data/faiss_index"

    # CORS — set to * or comma-separated URLs via env var
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost", "http://localhost:80"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",")]
        return v


settings = Settings()
