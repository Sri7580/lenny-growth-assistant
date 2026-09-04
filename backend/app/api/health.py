import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.models.schemas import HealthOut

router = APIRouter()


@router.get("/api/health", response_model=HealthOut)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "ok"
    vector_status = "ok"
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        try:
            await db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
        except Exception:
            vector_status = "missing_extension"
    except Exception as e:
        db_status = f"error: {e}"

    ollama_status = "ok"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code != 200:
                ollama_status = f"unreachable ({resp.status_code})"
    except Exception:
        ollama_status = "unreachable"

    overall = "ok" if db_status == "ok" else "degraded"

    return HealthOut(
        status=overall,
        database=db_status,
        ollama=ollama_status,
        vector_index=vector_status,
    )
