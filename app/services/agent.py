from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Conversation, Message
from app.services.rag import retrieve

EMERGENCY_PATTERNS = (
    "chest pain",
    "cannot breathe",
    "can't breathe",
    "severe bleeding",
    "unconscious",
    "suicidal",
    "stroke",
)
MEDICAL_ADVICE_PATTERNS = ("diagnose", "what medicine", "dosage", "should i take")


@dataclass
class AgentResult:
    answer: str
    citations: list[dict]
    requires_human: bool = False
    emergency: bool = False


async def _llm_answer(question: str, context: str) -> str | None:
    s = get_settings()
    if not s.openai_api_key:
        return None
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=s.openai_api_key, base_url=s.openai_base_url)
    system = """You are a hospital administrative assistant. Help with appointments, departments, hours, and approved hospital policies. Never diagnose, prescribe, or claim emergency expertise. Use only supplied context for hospital facts. If context is insufficient, say so and offer a human handoff. Keep voice answers under 90 words."""
    r = await client.chat.completions.create(
        model=s.openai_model,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Context:\n{context}\n\nPatient: {question}"},
        ],
    )
    return r.choices[0].message.content


async def respond(
    session: AsyncSession, message: str, conversation_id: UUID | None, channel: str
) -> tuple[Conversation, str, AgentResult, int]:
    started = time.perf_counter()
    lower = message.lower()
    s = get_settings()
    turn_id = str(uuid.uuid4())
    conv = await session.get(Conversation, conversation_id) if conversation_id else None
    if not conv:
        conv = Conversation(channel=channel, state={})
        session.add(conv)
        await session.flush()
    session.add(Message(conversation_id=conv.id, role="user", content=message, turn_id=turn_id))
    if any(p in lower for p in EMERGENCY_PATTERNS):
        result = AgentResult(
            f"This may be an emergency. Please call {s.emergency_phone} now or go to the nearest emergency department. I can connect you to a human, but do not wait for this assistant.",
            [],
            True,
            True,
        )
    elif any(p in lower for p in MEDICAL_ADVICE_PATTERNS):
        result = AgentResult(
            "I can help with hospital services and appointments, but I cannot diagnose or recommend medication. Please speak with a qualified clinician. I can help arrange an appointment or human handoff.",
            [],
            True,
        )
    else:
        docs = await retrieve(session, message, 5)
        context = "\n\n".join(f"[{d['title']}] {d['content']}" for d in docs)
        answer = await _llm_answer(message, context)
        if not answer:
            if docs:
                answer = f"Here is the relevant hospital information: {docs[0]['content']}"
            else:
                answer = "I could not find an approved answer in the hospital knowledge base. I can help you contact the hospital team."
        citations = [
            {"title": d["title"], "source_url": d.get("source_url"), "document_id": d["id"]}
            for d in docs[:3]
        ]
        result = AgentResult(answer, citations, requires_human=not bool(docs))
    latency = int((time.perf_counter() - started) * 1000)
    session.add(
        Message(
            conversation_id=conv.id,
            role="assistant",
            content=result.answer,
            turn_id=turn_id,
            latency_ms=latency,
        )
    )
    await session.commit()
    return conv, turn_id, result, latency
