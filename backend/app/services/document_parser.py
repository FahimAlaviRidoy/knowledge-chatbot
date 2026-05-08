"""
Document parsing service.
Supports: PDF, DOCX, TXT, MD, HTML, web URL scraping.
"""
import re
import io
import uuid
import chardet
import requests
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

import pdfplumber
from docx import Document as DocxDocument
from bs4 import BeautifulSoup
from app.core.config import get_settings
from app.core.logger import log

settings = get_settings()

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".html", ".htm"}


def _clean_text(text: str) -> str:
    """Normalize whitespace and strip control chars."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split text into overlapping chunks at sentence/paragraph boundaries."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap
    return [c for c in chunks if len(c.strip()) > 50]


def parse_pdf(content: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text()
            if txt:
                text_parts.append(txt)
    return "\n\n".join(text_parts)


def parse_docx(content: bytes) -> str:
    doc = DocxDocument(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def parse_html(content: bytes) -> str:
    encoding = chardet.detect(content)["encoding"] or "utf-8"
    soup = BeautifulSoup(content.decode(encoding, errors="replace"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    return soup.get_text(separator="\n")


def parse_text(content: bytes) -> str:
    encoding = chardet.detect(content)["encoding"] or "utf-8"
    return content.decode(encoding, errors="replace")


def fetch_url(url: str) -> Tuple[str, str]:
    """Fetch and parse a web page. Returns (text, title)."""
    headers = {"User-Agent": "KnowledgeBot/1.0 (document ingestion)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    title = soup.title.string if soup.title else url
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    return _clean_text(text), title.strip()


def ingest_file(
    filename: str,
    content: bytes,
) -> Tuple[str, List[str], dict]:
    """
    Parse and chunk a document.
    Returns: (doc_id, chunks, metadata)
    """
    ext = Path(filename).suffix.lower()
    log.info(f"Ingesting file: {filename} ({len(content)} bytes, type={ext})")

    if ext == ".pdf":
        raw_text = parse_pdf(content)
    elif ext == ".docx":
        raw_text = parse_docx(content)
    elif ext in {".html", ".htm"}:
        raw_text = parse_html(content)
    elif ext in {".txt", ".md"}:
        raw_text = parse_text(content)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    clean = _clean_text(raw_text)
    if not clean:
        raise ValueError("No text could be extracted from the document.")

    chunks = _chunk_text(clean, settings.chunk_size, settings.chunk_overlap)
    doc_id = str(uuid.uuid4())

    metadata = {
        "doc_id": doc_id,
        "filename": filename,
        "file_type": ext,
        "chunks": len(chunks),
        "size_bytes": len(content),
        "uploaded_at": datetime.utcnow().isoformat(),
    }
    log.info(f"Parsed '{filename}' → {len(chunks)} chunks (doc_id={doc_id})")
    return doc_id, chunks, metadata


def ingest_url(url: str, custom_title: str = None) -> Tuple[str, List[str], dict]:
    """Fetch a URL and ingest its text content."""
    text, title = fetch_url(url)
    filename = custom_title or title or url
    chunks = _chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    doc_id = str(uuid.uuid4())
    metadata = {
        "doc_id": doc_id,
        "filename": filename,
        "file_type": "url",
        "source_url": url,
        "chunks": len(chunks),
        "size_bytes": len(text.encode()),
        "uploaded_at": datetime.utcnow().isoformat(),
    }
    log.info(f"Ingested URL '{url}' → {len(chunks)} chunks (doc_id={doc_id})")
    return doc_id, chunks, metadata
