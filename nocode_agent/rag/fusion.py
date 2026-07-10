from __future__ import annotations

from collections.abc import Sequence

from nocode_agent.rag.types import Chunk, ScoredChunk


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[ScoredChunk]], k: int = 60, weights: Sequence[float] | None = None
) -> list[ScoredChunk]:
    if weights is not None and len(weights) != len(rankings):
        raise ValueError("weights must have one entry per ranking")
    scores: dict[str, float] = {}
    chunks: dict[str, Chunk] = {}
    for ranking_index, ranking in enumerate(rankings):
        weight = 1.0 if weights is None else weights[ranking_index]
        for rank, hit in enumerate(ranking, start=1):
            scores[hit.chunk.id] = scores.get(hit.chunk.id, 0.0) + weight / (k + rank)
            chunks.setdefault(hit.chunk.id, hit.chunk)
    ordered = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))
    return [ScoredChunk(chunks[chunk_id], scores[chunk_id]) for chunk_id in ordered]
