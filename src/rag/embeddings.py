"""Embedding provider abstraction and OpenAI implementation."""

from __future__ import annotations

from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class OpenAIEmbeddingProvider:
    """Generate embeddings through the OpenAI Embeddings API."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "text-embedding-3-small",
        batch_size: int = 64,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the openai package with `pip install -r requirements.txt`.") from exc
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.batch_size = batch_size

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            response = self.client.embeddings.create(
                model=self.model,
                input=batch,
                encoding_format="float",
            )
            ordered = sorted(response.data, key=lambda item: item.index)
            embeddings.extend(item.embedding for item in ordered)
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=[text],
            encoding_format="float",
        )
        return response.data[0].embedding
