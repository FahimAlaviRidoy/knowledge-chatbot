from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import List
from datetime import datetime

from app.models.schemas import (
    DocumentUploadResponse,
    DocumentInfo,
    KnowledgeBaseStats,
    URLIngestRequest,
    DeleteDocumentResponse,
)
from app.services.vector_store import get_vector_store
from app.services.document_parser import ingest_file, ingest_url, SUPPORTED_EXTENSIONS
from app.api.deps import get_current_user, require_admin
from app.core.logger import log

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

MAX_FILE_SIZE_MB = 50


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    admin: dict = Depends(require_admin),
):
    """Upload and ingest a document into the knowledge base (admin only)."""
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    try:
        doc_id, chunks, meta = ingest_file(file.filename, content)
    except ValueError as e:
        raise HTTPException(422, str(e))

    vs = get_vector_store()
    vs.add_document(doc_id, chunks, meta)

    log.info(f"Admin '{admin['username']}' uploaded '{file.filename}' → {len(chunks)} chunks")
    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=file.filename,
        chunks_created=len(chunks),
        status="success",
        message=f"Successfully ingested {len(chunks)} chunks from '{file.filename}'",
    )


@router.post("/ingest-url", response_model=DocumentUploadResponse, status_code=201)
def ingest_from_url(
    body: URLIngestRequest,
    admin: dict = Depends(require_admin),
):
    """Scrape and ingest a web page into the knowledge base (admin only)."""
    try:
        doc_id, chunks, meta = ingest_url(body.url, body.title)
    except Exception as e:
        raise HTTPException(422, f"Failed to fetch URL: {e}")

    vs = get_vector_store()
    vs.add_document(doc_id, chunks, meta)

    log.info(f"Admin '{admin['username']}' ingested URL '{body.url}' → {len(chunks)} chunks")
    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=meta["filename"],
        chunks_created=len(chunks),
        status="success",
        message=f"Successfully ingested {len(chunks)} chunks from URL",
    )


@router.get("/documents", response_model=List[DocumentInfo])
def list_documents(current_user: dict = Depends(get_current_user)):
    """List all documents in the knowledge base."""
    vs = get_vector_store()
    raw = vs.list_documents()
    docs = []
    for d in raw:
        try:
            uploaded_at = datetime.fromisoformat(d["uploaded_at"]) if d["uploaded_at"] else datetime.utcnow()
        except Exception:
            uploaded_at = datetime.utcnow()
        docs.append(
            DocumentInfo(
                doc_id=d["doc_id"],
                filename=d["filename"],
                file_type=d["file_type"],
                chunks=d["chunks"],
                uploaded_at=uploaded_at,
                size_bytes=d["size_bytes"],
            )
        )
    return docs


@router.delete("/documents/{doc_id}", response_model=DeleteDocumentResponse)
def delete_document(
    doc_id: str,
    admin: dict = Depends(require_admin),
):
    """Delete a document and all its chunks (admin only)."""
    vs = get_vector_store()
    deleted = vs.delete_document(doc_id)
    if deleted == 0:
        raise HTTPException(404, "Document not found")
    log.info(f"Admin '{admin['username']}' deleted doc_id={doc_id} ({deleted} chunks)")
    return DeleteDocumentResponse(
        doc_id=doc_id,
        deleted_chunks=deleted,
        message=f"Deleted {deleted} chunks for document {doc_id}",
    )


@router.get("/stats", response_model=KnowledgeBaseStats)
def get_stats(current_user: dict = Depends(get_current_user)):
    """Get knowledge base statistics."""
    vs = get_vector_store()
    raw = vs.stats()
    last_updated = None
    if raw["last_updated"]:
        try:
            last_updated = datetime.fromisoformat(raw["last_updated"])
        except Exception:
            pass
    return KnowledgeBaseStats(
        total_documents=raw["total_documents"],
        total_chunks=raw["total_chunks"],
        supported_formats=raw["supported_formats"],
        last_updated=last_updated,
    )
