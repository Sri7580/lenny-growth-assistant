from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.db_models import Session as SessionModel, Message
from app.models.schemas import SessionCreate, SessionOut, MessageOut

router = APIRouter()


@router.post("/api/sessions", response_model=SessionOut)
async def create_session(payload: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = SessionModel(title=payload.title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/api/sessions/{session_id}", response_model=list[MessageOut])
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    result = await db.execute(stmt)
    messages = result.scalars().all()
    if not messages:
        exists = await db.get(SessionModel, session_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Session not found")
    return messages
