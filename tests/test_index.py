import pytest

from src.models import Chunk
from src.rag.index import VectorIndex


def make_chunk(name: str, ordinal: int) -> Chunk:
    return Chunk(
        id=str(ordinal),
        source=name,
        location="document",
        text=name,
        ordinal=ordinal,
    )


def test_vector_search_returns_most_similar_first():
    index = VectorIndex()
    chunks = [make_chunk("vacation", 0), make_chunk("expenses", 1), make_chunk("security", 2)]
    embeddings = [[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]]
    index.build(chunks, embeddings)
    results = index.search([0.9, 0.1], top_k=2)
    assert results[0].chunk.source == "vacation"
    assert len(results) == 2


def test_empty_index_returns_no_results():
    assert VectorIndex().search([1.0, 0.0]) == []


def test_index_rejects_mismatched_embedding_count():
    index = VectorIndex()
    with pytest.raises(ValueError):
        index.build([make_chunk("one", 0)], [])


def test_query_dimension_must_match():
    index = VectorIndex()
    index.build([make_chunk("one", 0)], [[1.0, 0.0]])
    with pytest.raises(ValueError):
        index.search([1.0, 0.0, 0.0])
