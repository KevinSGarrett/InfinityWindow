from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.ingestion.docs_ingestor import ingest_text_document

router = APIRouter(
    tags=["docs"],
)


# ---------- Pydantic models ----------


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


# ---------- Endpoints ----------


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


@router.post("/docs/upload_text_file", response_model=DocumentIngestResponse)
async def upload_text_document(
    project_id: int = Form(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Ingest a text file (txt / md / log) into a project.

    Request is multipart/form-data with fields:
      - project_id (int, required)
      - name (optional, defaults to file.filename)
      - description (optional)
      - file (UploadFile, required)

    The file content is treated as UTF-8 text and passed through the same
    ingestion pipeline as /docs/text.
    """

    # Basic content-type check (not strict; we just avoid obviously non-text)
    if file.content_type not in ("text/plain", "text/markdown", "application/octet-stream"):
        # We'll still *allow* unknown types but warn via description; if you want
        # strict rejection, you can uncomment the HTTPException below.
        #
        # raise HTTPException(
        #     status_code=400,
        #     detail=f"Unsupported content-type: {file.content_type}",
        # )
        pass

    raw_bytes = await file.read()
    try:
        text = raw_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to decode file as UTF-8 text: {e}",
        )

    doc_name = name or (file.filename or "uploaded_document.txt")

    try:
        document, num_chunks = ingest_text_document(
            db=db,
            project_id=project_id,
            name=doc_name,
            text=text,
            description=description,
        )
    except ValueError as e:
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
