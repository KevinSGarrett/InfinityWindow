from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

from app.llm.openai_client import get_client

load_dotenv()


# Default to text-embedding-3-small, which matches the 1536‑dimensional
# Chroma collections you've already created.
_DEFAULT_EMBED_MODEL = "text-embedding-3-small"


def _get_embedding_model_name() -> str:
    """
    Resolve which embedding model to use.

    Environment variable OPENAI_EMBEDDING_MODEL (if set) wins,
    otherwise we fall back to a safe default.
    """
    return os.getenv("OPENAI_EMBEDDING_MODEL", _DEFAULT_EMBED_MODEL)


def get_embedding(text: str) -> List[float]:
    """
    Get an embedding vector for the given text using the configured
    OpenAI embedding model.
    """
    client = get_client()
    model = _get_embedding_model_name()

    response = client.embeddings.create(
        model=model,
        input=text,
    )

    return response.data[0].embedding


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Helper used by the document ingestor.

    Takes a list of texts and returns a list of embedding vectors,
    one per text. This calls the embeddings API once with a batch
    of inputs instead of one call per text.
    """
    if not texts:
        return []

    client = get_client()
    model = _get_embedding_model_name()

    response = client.embeddings.create(
        model=model,
        input=texts,
    )

    return [item.embedding for item in response.data]
