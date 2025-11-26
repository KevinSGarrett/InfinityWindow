from __future__ import annotations

from typing import List

from app.llm.openai_client import get_client


DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def get_embedding(
    text: str,
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> List[float]:
    """
    Get a single embedding vector for the given text using OpenAI.

    Uses text-embedding-3-small by default.
    """
    client = get_client()
    response = client.embeddings.create(
        model=model,
        input=text,
    )
    # response.data is a list; we asked for one input so we take index 0
    return response.data[0].embedding


def get_embeddings(
    texts: List[str],
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> List[List[float]]:
    """
    Get embeddings for a list of texts.
    """
    client = get_client()
    response = client.embeddings.create(
        model=model,
        input=texts,
    )
    return [item.embedding for item in response.data]
