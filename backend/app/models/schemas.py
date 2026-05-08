from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime
import uuid


# ─── Auth Models ─────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: Literal["user", "admin"] = "user"


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    role: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


# ─── Chat Models ─────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    stream: bool = False


class SourceDocument(BaseModel):
    doc_id: str
    filename: str
    chunk_index: int
    similarity_score: float
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: List[SourceDocument] = []
    in_knowledge_base: bool
    response_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─── Knowledge Base Models ────────────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    chunks_created: int
    status: str
    message: str


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    file_type: str
    chunks: int
    uploaded_at: datetime
    size_bytes: int


class KnowledgeBaseStats(BaseModel):
    total_documents: int
    total_chunks: int
    supported_formats: List[str]
    last_updated: Optional[datetime]


class URLIngestRequest(BaseModel):
    url: str
    title: Optional[str] = None


class DeleteDocumentResponse(BaseModel):
    doc_id: str
    deleted_chunks: int
    message: str
