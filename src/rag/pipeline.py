"""High-level document assistant orchestration."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from src.config import AppConfig
from src.ingestion.chunking import chunk_sections
from src.ingestion.parsers import parse_document
from src.models import AssistantAnswer, Chunk, DocumentRecord, SearchResult
from src.rag.embeddings import EmbeddingProvider, OpenAIEmbeddingProvider
from src.rag.index import VectorIndex
from src.services.openai_client import OpenAITextService


class DocumentAssistant:
    """Coordinates ingestion, embeddings, retrieval, and grounded generation."""

    def __init__(
        self,
        *,
        api_key: str,
        config: AppConfig | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        text_service: OpenAITextService | None = None,
    ) -> None:
        self.config = config or AppConfig()
        self.embedding_provider = embedding_provider or OpenAIEmbeddingProvider(
            api_key=api_key,
            model=self.config.embedding_model,
        )
        self.text_service = text_service or OpenAITextService(
            api_key=api_key,
            model=self.config.text_model,
        )
        self.index = VectorIndex()
        self.records: list[DocumentRecord] = []
        self._chunks_by_source: dict[str, list[Chunk]] = defaultdict(list)

    @property
    def chunks(self) -> tuple[Chunk, ...]:
        return self.index.chunks

    @property
    def document_names(self) -> list[str]:
        return [record.name for record in self.records]

    def index_documents(self, files: list[tuple[str, bytes]]) -> list[DocumentRecord]:
        all_chunks: list[Chunk] = []
        records: list[DocumentRecord] = []
        chunks_by_source: dict[str, list[Chunk]] = defaultdict(list)

        seen_names: set[str] = set()
        for name, data in files:
            normalized_name = name.casefold()
            if normalized_name in seen_names:
                raise ValueError(f"Duplicate file name '{name}'. Rename one of the files and try again.")
            seen_names.add(normalized_name)

            max_bytes = self.config.max_file_size_mb * 1024 * 1024
            if len(data) > max_bytes:
                raise ValueError(
                    f"'{name}' exceeds the {self.config.max_file_size_mb} MB file-size limit."
                )

            sections = parse_document(name, data)
            chunks = chunk_sections(
                sections,
                chunk_size=self.config.chunk_size,
                overlap=self.config.chunk_overlap,
            )
            all_chunks.extend(chunks)
            chunks_by_source[name].extend(chunks)
            records.append(
                DocumentRecord(
                    name=name,
                    extension=Path(name).suffix.lower(),
                    size_bytes=len(data),
                    section_count=len(sections),
                    chunk_count=len(chunks),
                )
            )

        if not all_chunks:
            raise ValueError("No searchable text was extracted from the uploaded documents.")

        embeddings = self.embedding_provider.embed_texts([chunk.text for chunk in all_chunks])
        self.index.build(all_chunks, embeddings)
        self.records = records
        self._chunks_by_source = chunks_by_source
        return list(records)

    def search(self, query: str, *, top_k: int | None = None) -> list[SearchResult]:
        query = query.strip()
        if not query:
            return []
        embedding = self.embedding_provider.embed_query(query)
        return self.index.search(
            embedding,
            top_k=top_k or self.config.retrieval_top_k,
        )

    def ask(
        self,
        question: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> AssistantAnswer:
        sources = self.search(question)
        answer = self.text_service.answer(
            question=question,
            sources=sources,
            history=history,
        )
        return AssistantAnswer(text=answer, sources=sources)

    def summarize(self, source_name: str) -> str:
        chunks = self._require_source(source_name)
        context = self._join_chunks(chunks, self.config.max_summary_characters)
        return self.text_service.summarize(source_name=source_name, context=context)

    def compare(self, first_name: str, second_name: str) -> str:
        if first_name == second_name:
            raise ValueError("Choose two different documents to compare.")
        first = self._join_chunks(
            self._require_source(first_name),
            self.config.max_compare_characters_per_document,
        )
        second = self._join_chunks(
            self._require_source(second_name),
            self.config.max_compare_characters_per_document,
        )
        return self.text_service.compare(
            first_name=first_name,
            first_context=first,
            second_name=second_name,
            second_context=second,
        )

    def _require_source(self, source_name: str) -> list[Chunk]:
        chunks = self._chunks_by_source.get(source_name, [])
        if not chunks:
            raise ValueError(f"Document '{source_name}' is not indexed.")
        return chunks

    @staticmethod
    def _join_chunks(chunks: list[Chunk], character_limit: int) -> str:
        parts: list[str] = []
        total = 0
        for chunk in chunks:
            block = f"[{chunk.location}]\n{chunk.text}\n"
            if total + len(block) > character_limit:
                remaining = character_limit - total
                if remaining > 200:
                    parts.append(block[:remaining])
                break
            parts.append(block)
            total += len(block)
        return "\n".join(parts)
