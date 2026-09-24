"""Small in-memory cosine-similarity vector index."""

from __future__ import annotations

import numpy as np

from src.models import Chunk, SearchResult


class VectorIndex:
    """An intentionally transparent vector store for portfolio-scale documents."""

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._matrix: np.ndarray | None = None

    @property
    def chunks(self) -> tuple[Chunk, ...]:
        return tuple(self._chunks)

    @property
    def size(self) -> int:
        return len(self._chunks)

    def build(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Each chunk must have exactly one embedding.")
        if not chunks:
            self._chunks = []
            self._matrix = None
            return

        matrix = np.asarray(embeddings, dtype=np.float32)
        if matrix.ndim != 2:
            raise ValueError("Embeddings must form a two-dimensional matrix.")

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._matrix = matrix / norms
        self._chunks = list(chunks)

    def search(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 6,
        min_score: float = -1.0,
    ) -> list[SearchResult]:
        if self._matrix is None or not self._chunks:
            return []

        query = np.asarray(query_embedding, dtype=np.float32)
        if query.ndim != 1 or query.shape[0] != self._matrix.shape[1]:
            raise ValueError("Query embedding dimensionality does not match the index.")

        norm = np.linalg.norm(query)
        if norm == 0:
            return []
        query = query / norm

        scores = self._matrix @ query
        candidate_indices = np.argsort(scores)[::-1][: max(top_k, 0)]
        results = [
            SearchResult(chunk=self._chunks[index], score=float(scores[index]))
            for index in candidate_indices
            if float(scores[index]) >= min_score
        ]
        return results
