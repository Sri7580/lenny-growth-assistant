"""
Ingest Lenny's Podcast transcripts into pgvector.

Usage:
    python -m scripts.ingest --limit 30
"""
import argparse
import asyncio
import re
import sys
from pathlib import Path

import frontmatter

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import AsyncSessionLocal, init_db
from app.models.db_models import TranscriptChunk
from app.rag.embeddings import embed_batch

TRANSCRIPTS_DIR = Path(__file__).resolve().parents[1] / "data" / "lennys-transcripts" / "episodes"

CHUNK_SIZE = 700       # target tokens (approximated by words)
CHUNK_OVERLAP = 100

TIMESTAMP_PATTERN = re.compile(r"\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?")


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += size - overlap
    return chunks


def extract_nearest_timestamp(chunk: str) -> str | None:
    match = TIMESTAMP_PATTERN.search(chunk)
    return match.group(1) if match else None


def load_episodes(limit: int | None = None) -> list[dict]:
    episodes = []
    folders = sorted(TRANSCRIPTS_DIR.iterdir())
    if limit:
        folders = folders[:limit]

    for folder in folders:
        transcript_file = folder / "transcript.md"
        if not transcript_file.exists():
            continue
        post = frontmatter.load(transcript_file)
        episodes.append({
            "guest": post.get("guest", folder.name),
            "title": post.get("title", "Untitled episode"),
            "video_id": post.get("video_id"),
            "youtube_url": post.get("youtube_url"),
            "publish_date": str(post.get("publish_date", "")),
            "body": post.content,
        })
    return episodes


async def ingest(limit: int | None):
    print(f"Initializing database schema...")
    await init_db()

    episodes = load_episodes(limit=limit)
    print(f"Loaded {len(episodes)} episodes from {TRANSCRIPTS_DIR}")

    async with AsyncSessionLocal() as db:
        for ep in episodes:
            chunks = chunk_text(ep["body"])
            if not chunks:
                continue

            print(f"  {ep['guest']} — {len(chunks)} chunks")
            vectors = embed_batch(chunks)

            for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
                db.add(TranscriptChunk(
                    guest_name=ep["guest"],
                    episode_title=ep["title"],
                    video_id=ep["video_id"],
                    youtube_url=ep["youtube_url"],
                    publish_date=ep["publish_date"],
                    timestamp_ref=extract_nearest_timestamp(chunk),
                    chunk_index=idx,
                    chunk_text=chunk,
                    embedding=vector,
                ))
            await db.commit()

    print("Ingestion complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30, help="Number of episodes to ingest")
    args = parser.parse_args()
    asyncio.run(ingest(args.limit))
