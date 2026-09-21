import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.db_models import Session as SessionModel, Message, Artifact
from app.models.schemas import ChatRequest
from app.agent.claude_agent import run_agent_turn
from app.skills.artifact_generator import extract_artifacts

logger = logging.getLogger("lenny-growth-assistant")
router = APIRouter()


@router.post("/api/chat")
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(SessionModel, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = Message(session_id=session.id, role="user", content=payload.message)
    db.add(user_msg)
    await db.commit()

    hist_stmt = select(Message).where(Message.session_id == session.id).order_by(Message.created_at)
    hist_result = await db.execute(hist_stmt)
    history = [
        {"role": m.role, "content": m.content}
        for m in hist_result.scalars().all()
        if m.role in ("user", "assistant")
    ][:-1]  # exclude the message we just added, agent re-adds it with context

    async def event_stream():
        full_response = ""
        sources = None
        try:
            agent_gen = run_agent_turn(db, payload.message, history, payload.provider)
            async for token in agent_gen:
                full_response += token
                yield token
        except Exception as e:
            logger.exception("Agent turn failed")
            yield f"\n[Error: {e}]"
            full_response += f"\n[Error: {e}]"

        cleaned_text, artifacts = extract_artifacts(full_response)

        assistant_msg = Message(
            session_id=session.id,
            role="assistant",
            content=cleaned_text or full_response,
            sources=sources,
        )
        db.add(assistant_msg)
        await db.commit()
        await db.refresh(assistant_msg)

        for art in artifacts:
            db.add(Artifact(
                message_id=assistant_msg.id,
                artifact_type=art["artifact_type"],
                title=art["title"],
                content=art["content"],
            ))
        await db.commit()

    return StreamingResponse(event_stream(), media_type="text/plain")
