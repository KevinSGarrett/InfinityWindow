from __future__ import annotations

import time
from typing import Optional, List, Tuple

from sqlalchemy.orm import Session

from app.db import models
from app.llm.embeddings import embed_texts_batched
from app.vectorstore.chroma_store import add_document_chunks


def _chunk_text(
    text: str,
    max_chars: int = 2000,
    overlap: int = 200,
) -> List[str]:
    """
    Simple character-based chunking with overlap.

    Later we can replace this with a smarter token/paragraph-based splitter,
    but this is a good starting point.
    """
    text = text.replace("\r\n", "\n")
    n = len(text)
    if n == 0:
        return []

    chunks: List[str] = []
    start = 0

    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == n:
            break
        # Slide window forward with overlap
        start = max(0, end - overlap)

    return chunks


def _flush_with_retry(db: Session, attempts: int = 6, base_delay: float = 0.3) -> None:
    """
    Flush pending objects with retries to tolerate SQLite locks.
    """
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            db.flush()
            return
        except Exception as exc:  # noqa: BLE001
            # SQLite lock errors surface as OperationalError -> generic here
            db.rollback()
            last_exc = exc
            if "locked" not in str(exc).lower():
                raise
            time.sleep(base_delay * (i + 1))
    if last_exc:
        raise last_exc


def _commit_with_retry(db: Session, attempts: int = 6, base_delay: float = 0.3) -> None:
    """
    Commit with retries to ride out transient SQLite locks.
    """
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            db.commit()
            return
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            last_exc = exc
            if "locked" not in str(exc).lower():
                raise
            time.sleep(base_delay * (i + 1))
    if last_exc:
        raise last_exc


def ingest_text_document(
    db: Session,
    project_id: int,
    name: str,
    text: str,
    description: Optional[str] = None,
    max_chars: int = 2000,
    overlap: int = 200,
) -> Tuple[models.Document, int]:
    """
    Ingest a plain text document into a project.

    Steps:
      1. Verify the project exists.
      2. Create a Document row.
      3. Create a single DocumentSection representing the whole doc.
      4. Chunk the text.
      5. Embed all chunks with OpenAI.
      6. Create DocumentChunk rows and index them in Chroma.

    Returns:
      (Document instance, number of chunks)
    """
    # 1) Verify project exists
    project = db.get(models.Project, project_id)
    if project is None:
        raise ValueError(f"Project {project_id} not found")

    # 2) Create the Document
    document = models.Document(
        project_id=project_id,
        name=name,
        description=description,
    )
    db.add(document)
    _flush_with_retry(db)  # document.id is now available

    # 3) Create a single section for the whole document
    section = models.DocumentSection(
        document_id=document.id,
        title=name,
        index=0,
        path=name,
    )
    db.add(section)
    _flush_with_retry(db)  # section.id is now available

    # 4) Chunk the text
    chunks: List[str] = _chunk_text(text, max_chars=max_chars, overlap=overlap)
    if not chunks:
        # No content; just commit the empty document + section
        _commit_with_retry(db)
        db.refresh(document)
        return document, 0

    # 5) Embed chunks in batches to respect token limits
    embeddings: List[List[float]] = embed_texts_batched(chunks)

    # 6) Create DocumentChunk rows and collect IDs
    chunk_ids: List[int] = []
    chunk_indexes: List[int] = list(range(len(chunks)))

    for idx, chunk_text in enumerate(chunks):
        chunk = models.DocumentChunk(
            document_id=document.id,
            section_id=section.id,
            index=idx,
            content=chunk_text,
        )
        db.add(chunk)
        _flush_with_retry(db)  # chunk.id is now available
        chunk_ids.append(chunk.id)

    # Index in Chroma using the batch helper
    add_document_chunks(
        document_id=document.id,
        project_id=project_id,
        chunk_ids=chunk_ids,
        chunk_indexes=chunk_indexes,
        contents=chunks,
        embeddings=embeddings,
    )

    # Final commit
    _commit_with_retry(db)
    db.refresh(document)

    return document, len(chunks)
