"""Seed initial data: admin user + skill master list."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://resume_user:resume_pass@localhost:5432/resume_db")

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.core.database import Base
from app.core.security import hash_password
from app.models.user import User
from app.models.skill import Skill
import app.models  # noqa

SKILLS = [
    ("Python", "Programming"), ("Java", "Programming"), ("JavaScript", "Programming"),
    ("TypeScript", "Programming"), ("Go", "Programming"), ("Rust", "Programming"),
    ("C++", "Programming"), ("C#", "Programming"), ("Ruby", "Programming"), ("PHP", "Programming"),
    ("React", "Frontend"), ("Next.js", "Frontend"), ("Vue.js", "Frontend"), ("Angular", "Frontend"),
    ("HTML", "Frontend"), ("CSS", "Frontend"), ("Tailwind CSS", "Frontend"),
    ("Node.js", "Backend"), ("FastAPI", "Backend"), ("Django", "Backend"), ("Flask", "Backend"),
    ("Spring Boot", "Backend"), ("Express.js", "Backend"), ("REST API", "Backend"), ("GraphQL", "Backend"),
    ("PostgreSQL", "Database"), ("MySQL", "Database"), ("MongoDB", "Database"),
    ("Redis", "Database"), ("Elasticsearch", "Database"), ("SQLite", "Database"),
    ("Docker", "DevOps"), ("Kubernetes", "DevOps"), ("AWS", "DevOps"),
    ("Azure", "DevOps"), ("GCP", "DevOps"), ("CI/CD", "DevOps"), ("Terraform", "DevOps"),
    ("Git", "Tools"), ("Linux", "Tools"), ("Nginx", "Tools"), ("Jenkins", "Tools"),
    ("Machine Learning", "AI/ML"), ("Deep Learning", "AI/ML"), ("NLP", "AI/ML"),
    ("TensorFlow", "AI/ML"), ("PyTorch", "AI/ML"), ("Scikit-learn", "AI/ML"),
    ("Pandas", "Data"), ("NumPy", "Data"), ("SQL", "Data"), ("Tableau", "Data"), ("Power BI", "Data"),
    ("Agile", "Soft Skills"), ("Scrum", "Soft Skills"), ("Jira", "Soft Skills"),
    ("Communication", "Soft Skills"), ("Leadership", "Soft Skills"),
    ("Microservices", "Architecture"), ("System Design", "Architecture"),
    ("Data Structures", "CS Fundamentals"), ("Algorithms", "CS Fundamentals"),
    ("FAISS", "AI/ML"), ("LangChain", "AI/ML"), ("OpenAI API", "AI/ML"),
]


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        # Admin user
        existing = await db.execute(select(User).where(User.email == "admin@resume.ai"))
        if not existing.scalar_one_or_none():
            db.add(User(email="admin@resume.ai", password_hash=hash_password("Admin@1234"), full_name="System Admin", role="admin"))
            print("Created admin: admin@resume.ai / Admin@1234")

        # Skills
        for name, category in SKILLS:
            normalized = name.lower().strip()
            existing = await db.execute(select(Skill).where(Skill.normalized_name == normalized))
            if not existing.scalar_one_or_none():
                db.add(Skill(name=name, normalized_name=normalized, category=category))

        await db.commit()
        print(f"Seeded {len(SKILLS)} skills")

    await engine.dispose()
    print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
