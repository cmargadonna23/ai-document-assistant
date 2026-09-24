from src.ingestion.chunking import chunk_sections
from src.models import DocumentSection


def test_chunking_preserves_source_metadata():
    sections = [DocumentSection("policy.txt", "document", "A " * 1500)]
    chunks = chunk_sections(sections, chunk_size=500, overlap=50)
    assert len(chunks) > 1
    assert all(chunk.source == "policy.txt" for chunk in chunks)
    assert all(chunk.location == "document" for chunk in chunks)


def test_chunk_ids_are_stable_for_same_input():
    sections = [DocumentSection("a.txt", "document", "hello world " * 100)]
    first = chunk_sections(sections, chunk_size=300, overlap=30)
    second = chunk_sections(sections, chunk_size=300, overlap=30)
    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]


def test_overlap_must_be_smaller_than_chunk_size():
    sections = [DocumentSection("a.txt", "document", "hello")]
    try:
        chunk_sections(sections, chunk_size=300, overlap=300)
    except ValueError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
