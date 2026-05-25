from sqlalchemy import String, Float, Integer, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from app.core.database import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=True)
    github_url: Mapped[str] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[str] = mapped_column(String(500), nullable=True)
    experience_years: Mapped[float] = mapped_column(Float, default=0.0)
    resume_path: Mapped[str] = mapped_column(String(500), nullable=True)
    resume_text: Mapped[str] = mapped_column(Text, nullable=True)
    ats_score: Mapped[float] = mapped_column(Float, default=0.0)
    parsed_data: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="candidate_profile")
    skills: Mapped[list["CandidateSkill"]] = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="candidate")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    proficiency_level: Mapped[str] = mapped_column(String(50), default="intermediate")
    years_of_experience: Mapped[float] = mapped_column(Float, default=0.0)

    candidate: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="skills")
    skill: Mapped["Skill"] = relationship("Skill")
