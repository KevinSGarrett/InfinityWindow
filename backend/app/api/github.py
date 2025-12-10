from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.ingestion.github_ingestor import ingest_local_repo

router = APIRouter(
    prefix="/github",
    tags=["github"],
)


class LocalRepoIngestRequest(BaseModel):
    project_id: int
    root_path: str
    name_prefix: Optional[str] = None
    include_globs: Optional[List[str]] = None


class LocalRepoIngestResponse(BaseModel):
    project_id: int
    root_path: str
    num_files: int
    num_documents: int
    num_chunks: int


@router.post("/ingest_local_repo", response_model=LocalRepoIngestResponse)
def ingest_local_repo_endpoint(
    payload: LocalRepoIngestRequest,
    db: Session = Depends(get_db),
):
    """
    Ingest a local Git repo (or any folder of code/text files) into a project.

    This expects:
      - project_id: which InfinityWindow project to attach documents to.
      - root_path: local filesystem path to the repo root.
      - name_prefix: optional prefix for Document.name (e.g. 'MyRepo/').
      - include_globs: optional file patterns (default covers common text/code).

    For each matching file:
      - Reads it as UTF-8 text (ignore errors).
      - Creates a Document.
      - Chunks, embeds, and indexes it in Chroma.
    """
    # Make sure the project exists
    project = db.get(models.Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    try:
        result = ingest_local_repo(
            db=db,
            project_id=payload.project_id,
            root_path=payload.root_path,
            name_prefix=payload.name_prefix,
            include_globs=payload.include_globs,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return LocalRepoIngestResponse(**result)
