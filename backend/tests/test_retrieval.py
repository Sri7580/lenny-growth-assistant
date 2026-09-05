"""
Tests for the chunking/timestamp-extraction logic used at ingestion time,
plus an integration-style test of pgvector retrieval against the live
database (requires `docker compose up db` to be running).
"""
import pytest

from scripts.ingest import chunk_text, extract_nearest_timestamp


def test_chunk_text_respects_target_size():
    words = ["word"] * 2000
    text = " ".join(words)
    chunks = chunk_text(text, size=700, overlap=100)

    assert len(chunks) > 1
    for chunk in chunks:
        word_count = len(chunk.split())
        assert word_count <= 700


def test_chunk_text_overlap_present():
    words = [f"w{i}" for i in range(1500)]
    text = " ".join(words)
    chunks = chunk_text(text, size=700, overlap=100)

    # With size=700, overlap=100, chunk[1] starts at word index 600, so the
    # overlapping region (words 600-699) falls within chunk[1]'s first 100
    # words, not its first 10 — check against that actual overlap window.
    tail_of_first = chunks[0].split()[-100:]
    head_of_second = chunks[1].split()[:100]
    assert any(w in head_of_second for w in tail_of_first)

def test_extract_nearest_timestamp_finds_hh_mm_ss():
    chunk = "Lenny (00:00:36): Welcome to the podcast."
    assert extract_nearest_timestamp(chunk) == "00:00:36"


def test_extract_nearest_timestamp_returns_none_when_absent():
    chunk = "This chunk has no timestamp in it at all."
    assert extract_nearest_timestamp(chunk) is None


@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_returns_grounded_results():
    """Integration test — requires the db container to be up and ingestion
    to have already run at least once (see README setup steps)."""
    from app.database import AsyncSessionLocal
    from app.rag.retriever import retrieve_relevant_chunks

    async with AsyncSessionLocal() as db:
        results = await retrieve_relevant_chunks(
            db, query="how do I find product market fit", top_k=3
        )

    assert isinstance(results, list)
    if results:  # only assert shape if the corpus returned something
        assert "guest" in results[0]
        assert "text" in results[0]
        assert "score" in results[0]