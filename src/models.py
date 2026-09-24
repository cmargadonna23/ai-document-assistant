"""Shared domain models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DocumentSection:
    """A source-aligned text section extracted from a document."""

    source: str
    location: str
    text: str


@dataclass(frozen=True)
class Chunk:
    """A retrievable unit derived from a document section."""

    id: str
    source: str
    location: str
    text: str
    ordinal: int

    @property
    def citation_label(self) -> str:
        return f"{self.source} — {self.location}"


@dataclass(frozen=True)
class SearchResult:
    """A chunk plus its vector similarity score."""

    chunk: Chunk
    score: float


@dataclass
class DocumentRecord:
    """Metadata shown in the document library."""

    name: str
    extension: str
    size_bytes: int
    section_count: int
    chunk_count: int

    @property
    def size_label(self) -> str:
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        if self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        return f"{self.size_bytes / (1024 * 1024):.1f} MB"


@dataclass
class AssistantAnswer:
    """Answer text and the evidence retrieved for it."""

    text: str
    sources: list[SearchResult] = field(default_factory=list)
