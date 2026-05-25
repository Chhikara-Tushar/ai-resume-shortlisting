from sqlalchemy import String, Float, Integer, ForeignKey, Text, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    recruiter_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("recruiter_profiles.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    job_type: Mapped[str] = mapped_column(SAEnum("full_time", "part_time", "contract", "internship", "remote", name="job_type"), default="full_time")
    experience_required: Mapped[float] = mapped_column(Float, default=0.0)
    salary_min: Mapped[float] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(SAEnum("draft", "active", "closed", name="job_status"), default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    recruiter: Mapped["RecruiterProfile"] = relationship("RecruiterProfile", back_populates="jobs")
    skills: Mapped[list["JobSkill"]] = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="job")
    ai_insights: Mapped[list["AIInsight"]] = relationship("AIInsight", back_populates="job", cascade="all, delete-orphan")


class JobSkill(Base):
    __tablename__ = "job_skills"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    importance: Mapped[str] = mapped_column(SAEnum("required", "preferred", name="skill_importance"), default="required")
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    job: Mapped["Job"] = relationship("Job", back_populates="skills")
    skill: Mapped["Skill"] = relationship("Skill")
