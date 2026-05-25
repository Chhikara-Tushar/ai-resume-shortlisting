import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.chat import ChatSession, ChatMessage


async def get_or_create_session(user_id: str, session_id: Optional[str], db: AsyncSession) -> ChatSession:
    if session_id:
        result = await db.execute(select(ChatSession).where(ChatSession.session_id == session_id, ChatSession.user_id == user_id))
        session = result.scalar_one_or_none()
        if session:
            return session

    session = ChatSession(user_id=user_id, session_id=str(uuid.uuid4()))
    db.add(session)
    await db.flush()
    return session


async def get_history(session: ChatSession, db: AsyncSession, limit: int = 10) -> list:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in reversed(messages)]


async def chat(user_id: str, session_id: Optional[str], message: str, role: str, db: AsyncSession) -> dict:
    session = await get_or_create_session(user_id, session_id, db)
    history = await get_history(session, db)

    # Save user message
    db.add(ChatMessage(session_id=session.id, role="user", content=message))
    await db.flush()

    reply = await _generate_reply(message, history, role)

    db.add(ChatMessage(session_id=session.id, role="assistant", content=reply))
    await db.commit()

    return {"reply": reply, "session_id": session.session_id}


async def _generate_reply(message: str, history: list, role: str) -> str:
    if not settings.OPENAI_API_KEY:
        return _mock_reply(message, role)

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    system_prompts = {
        "candidate": "You are a helpful AI career assistant for job seekers. Help with resume advice, job search, skill development, and application tips.",
        "recruiter": "You are a helpful AI assistant for recruiters. Help with candidate evaluation, job description writing, interview questions, and hiring decisions.",
        "admin": "You are a helpful AI assistant for system administrators. Help with platform management, analytics, and user support.",
    }
    system_prompt = system_prompts.get(role, system_prompts["candidate"])

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": message})

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        max_tokens=500,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def _mock_reply(message: str, role: str) -> str:
    msg = message.lower()
    if "resume" in msg:
        return "To improve your resume, focus on: 1) Adding quantifiable achievements, 2) Including a clear skills section, 3) Using action verbs, 4) Tailoring it to each job description."
    if "skill" in msg:
        return "Based on current market trends, I recommend learning: Python, Cloud platforms (AWS/Azure), Docker/Kubernetes, and SQL. These are highly sought after by employers."
    if "interview" in msg:
        return "For interview prep: research the company, prepare STAR stories for behavioral questions, practice technical questions in your domain, and prepare thoughtful questions to ask the interviewer."
    if "salary" in msg:
        return "Salary negotiation tip: research market rates on Glassdoor/LinkedIn, know your value, and don't be afraid to negotiate. Most employers expect it."
    return "I'm here to help with your career journey! You can ask me about resume improvement, skill recommendations, interview preparation, job search strategies, and more."
