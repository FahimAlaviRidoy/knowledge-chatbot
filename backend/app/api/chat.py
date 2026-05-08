import time
from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, SourceDocument
from app.services.vector_store import get_vector_store
from app.services.session_manager import session_manager
from app.services.llm_service import generate_answer
from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.logger import log

router = APIRouter(prefix="/chat", tags=["Chat"])
settings = get_settings()


@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Main chat endpoint.
    - Retrieves relevant context from the knowledge base via semantic search.
    - Passes context + conversation history to the LLM.
    - Handles out-of-scope questions gracefully.
    """
    start = time.time()

    # 1. Session / memory
    session_id = session_manager.get_or_create(body.session_id)
    history = session_manager.get_history(session_id)

    # 2. Semantic retrieval
    vs = get_vector_store()
    hits = vs.search(body.message, top_k=settings.top_k_results)
    in_kb = len(hits) > 0

    context_texts = [h["full_text"] for h in hits]
    sources = [
        SourceDocument(
            doc_id=h["doc_id"],
            filename=h["filename"],
            chunk_index=h["chunk_index"],
            similarity_score=h["similarity_score"],
            excerpt=h["excerpt"],
        )
        for h in hits
    ]

    # 3. LLM answer generation
    answer = generate_answer(
        question=body.message,
        context_chunks=context_texts,
        history=history,
        in_knowledge_base=in_kb,
    )

    # 4. Save turn to session memory
    session_manager.add_turn(session_id, body.message, answer)

    elapsed = round((time.time() - start) * 1000, 1)
    log.info(
        f"Chat | user={current_user['username']} | session={session_id[:8]} | "
        f"in_kb={in_kb} | sources={len(sources)} | {elapsed}ms"
    )

    return ChatResponse(
        answer=answer,
        session_id=session_id,
        sources=sources,
        in_knowledge_base=in_kb,
        response_time_ms=elapsed,
    )


@router.delete("/session/{session_id}")
def clear_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Clear conversation history for a session."""
    session_manager.clear_session(session_id)
    return {"message": "Session cleared", "session_id": session_id}
