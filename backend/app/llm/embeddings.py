from __future__ import annotations

import os
from typing import List, Optional

from dotenv import load_dotenv

from app.llm.openai_client import get_client

load_dotenv()


# Default to text-embedding-3-small, which matches the 1536‑dimensional
# Chroma collections you've already created.
_DEFAULT_EMBED_MODEL = "text-embedding-3-small"
_DEFAULT_MAX_TOKENS_PER_BATCH = 50000
_DEFAULT_MAX_ITEMS_PER_BATCH = 256


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


def _estimated_token_count(text: str) -> int:
    """
    Rough token estimator based on character count.

    The heuristic (len / 4) is intentionally simple; it just ensures we don't
    try to stuff hundreds of thousands of characters into a single embeddings
    call.
    """
    if not text:
        return 1
    return max(1, len(text) // 4 + 1)


def _resolve_batch_limit(env_key: str, default_value: int) -> int:
    raw = os.getenv(env_key)
    if raw is None:
        return default_value
    try:
        parsed = int(raw)
    except ValueError:
        return default_value
    return max(1, parsed)


def embed_texts_batched(
    texts: List[str],
    *,
    max_tokens_per_batch: Optional[int] = None,
    max_items_per_batch: Optional[int] = None,
    model: Optional[str] = None,
) -> List[List[float]]:
    """
    Embed a list of texts by splitting them into smaller batches that satisfy
    both token-count and item-count limits. This prevents gigantic ingestion
    jobs from exceeding OpenAI's per-request caps.
    """
    if not texts:
        return []

    tokens_cap = max_tokens_per_batch or _resolve_batch_limit(
        "MAX_EMBED_TOKENS_PER_BATCH", _DEFAULT_MAX_TOKENS_PER_BATCH
    )
    items_cap = max_items_per_batch or _resolve_batch_limit(
        "MAX_EMBED_ITEMS_PER_BATCH", _DEFAULT_MAX_ITEMS_PER_BATCH
    )

    client = get_client()
    model_name = model or _get_embedding_model_name()

    # Pre-allocate results to preserve ordering even though we process batches.
    results: List[Optional[List[float]]] = [None] * len(texts)
    batch_inputs: List[str] = []
    batch_indices: List[int] = []
    batch_tokens = 0

    def flush_batch() -> None:
        nonlocal batch_inputs, batch_indices, batch_tokens
        if not batch_inputs:
            return
        response = client.embeddings.create(
            model=model_name,
            input=batch_inputs,
        )
        embeddings = [item.embedding for item in response.data]
        for idx, embedding in zip(batch_indices, embeddings):
            results[idx] = embedding
        batch_inputs = []
        batch_indices = []
        batch_tokens = 0

    for idx, text in enumerate(texts):
        est_tokens = _estimated_token_count(text)
        if est_tokens > tokens_cap:
            # If a single chunk is enormous, flush current batch and send it alone.
            flush_batch()
            batch_inputs = [text]
            batch_indices = [idx]
            batch_tokens = est_tokens
            flush_batch()
            continue

        if (
            batch_inputs
            and (
                len(batch_inputs) >= items_cap
                or batch_tokens + est_tokens > tokens_cap
            )
        ):
            flush_batch()

        batch_inputs.append(text)
        batch_indices.append(idx)
        batch_tokens += est_tokens

    flush_batch()

    # Every entry should be filled; guard against unexpected None.
    return [embedding or [] for embedding in results]
