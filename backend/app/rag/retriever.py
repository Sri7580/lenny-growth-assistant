from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.db_models import TranscriptChunk
from app.rag.embeddings import embed_text


async def retrieve_relevant_chunks(
    db: AsyncSession,
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.35,
) -> list[dict]:
    """Cosine similarity search over transcript_chunks using pgvector.
    pgvector's <=> operator returns cosine *distance*; similarity = 1 - distance."""
    query_vector = embed_text(query)

    stmt = (
        select(
            TranscriptChunk.guest_name,
            TranscriptChunk.episode_title,
            TranscriptChunk.video_id,
            TranscriptChunk.youtube_url,
            TranscriptChunk.timestamp_ref,
            TranscriptChunk.chunk_text,
            (1 - TranscriptChunk.embedding.cosine_distance(query_vector)).label("score"),
        )
        .order_by(TranscriptChunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "guest": r.guest_name,
            "episode": r.episode_title,
            "video_id": r.video_id,
            "youtube_url": r.youtube_url,
            "timestamp": r.timestamp_ref,
            "text": r.chunk_text,
            "score": float(r.score),
        }
        for r in rows
        if r.score >= similarity_threshold
    ]
