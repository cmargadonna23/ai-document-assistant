"""Application configuration and safe defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration for document ingestion and RAG."""

    text_model: str = os.getenv("OPENAI_TEXT_MODEL", "gpt-5.6-luna")
    embedding_model: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )
    chunk_size: int = 1_800
    chunk_overlap: int = 250
    retrieval_top_k: int = 6
    max_file_size_mb: int = 15
    max_summary_characters: int = 35_000
    max_compare_characters_per_document: int = 20_000


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".xlsx"}
