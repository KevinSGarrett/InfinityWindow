from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.ingestion.docs_ingestor import ingest_text_document

router = APIRouter(
    tags=["docs"],
)


class DocumentCreateText(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    text: str


class DocumentRead(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentIngestResponse(BaseModel):
    document: DocumentRead
    num_chunks: int


@router.post("/docs/text", response_model=DocumentIngestResponse)
def create_text_document(
    payload: DocumentCreateText,
    db: Session = Depends(get_db),
):
    """
    Ingest a plain text document into a project.

    - Creates a Document row.
    - Chunks the text.
    - Embeds and indexes chunks in Chroma.
    """
    try:
        document, num_chunks = ingest_text_document(
            db=db,
            project_id=payload.project_id,
            name=payload.name,
            text=payload.text,
            description=payload.description,
        )
    except ValueError as e:
        # For example, project not found
        raise HTTPException(status_code=400, detail=str(e))

    return DocumentIngestResponse(
        document=document,
        num_chunks=num_chunks,
    )


@router.get("/projects/{project_id}/docs", response_model=List[DocumentRead])
def list_project_documents(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    List all documents attached to a given project.
    """
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    docs = (
        db.query(models.Document)
        .filter(models.Document.project_id == project_id)
        .order_by(models.Document.id)
        .all()
    )
    return docs
