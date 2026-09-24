"""Text chunking with overlap and source metadata preservation."""

from __future__ import annotations

import hashlib
import re

from src.models import Chunk, DocumentSection


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_sections(
    sections: list[DocumentSection],
    *,
    chunk_size: int = 1_800,
    overlap: int = 250,
) -> list[Chunk]:
    """Split sections into overlapping chunks suitable for retrieval."""

    if chunk_size < 200:
        raise ValueError("chunk_size must be at least 200 characters")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    chunks: list[Chunk] = []
    ordinal = 0

    for section in sections:
        text = _normalize_text(section.text)
        if not text:
            continue

        start = 0
        while start < len(text):
            target_end = min(start + chunk_size, len(text))
            end = target_end

            if target_end < len(text):
                minimum_break = start + int(chunk_size * 0.60)
                newline_break = text.rfind("\n", minimum_break, target_end)
                sentence_break = text.rfind(". ", minimum_break, target_end)
                space_break = text.rfind(" ", minimum_break, target_end)
                best_break = max(newline_break, sentence_break, space_break)
                if best_break > start:
                    end = best_break + (2 if best_break == sentence_break else 1)

            piece = text[start:end].strip()
            if piece:
                digest = hashlib.sha1(
                    f"{section.source}|{section.location}|{ordinal}|{piece[:120]}".encode(
                        "utf-8"
                    )
                ).hexdigest()[:12]
                chunks.append(
                    Chunk(
                        id=digest,
                        source=section.source,
                        location=section.location,
                        text=piece,
                        ordinal=ordinal,
                    )
                )
                ordinal += 1

            if end >= len(text):
                break
            start = max(end - overlap, start + 1)

    return chunks
