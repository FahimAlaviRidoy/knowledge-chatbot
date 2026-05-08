"""
Session/Conversation Memory Manager.
Stores short-term conversation history per session in memory.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid
from app.core.logger import log


SESSION_TTL_MINUTES = 60
MAX_HISTORY_PER_SESSION = 20


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, dict] = {}

    def _evict_expired(self):
        now = datetime.utcnow()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s["last_active"] > timedelta(minutes=SESSION_TTL_MINUTES)
        ]
        for sid in expired:
            del self._sessions[sid]
        if expired:
            log.debug(f"Evicted {len(expired)} expired sessions")

    def get_or_create(self, session_id: Optional[str] = None) -> str:
        self._evict_expired()
        if session_id and session_id in self._sessions:
            self._sessions[session_id]["last_active"] = datetime.utcnow()
            return session_id
        new_id = session_id or str(uuid.uuid4())
        self._sessions[new_id] = {
            "history": [],
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow(),
        }
        return new_id

    def get_history(self, session_id: str) -> List[dict]:
        s = self._sessions.get(session_id)
        return s["history"] if s else []

    def add_turn(self, session_id: str, user_msg: str, assistant_msg: str):
        if session_id not in self._sessions:
            self.get_or_create(session_id)
        history = self._sessions[session_id]["history"]
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": assistant_msg})
        # Keep only recent turns
        if len(history) > MAX_HISTORY_PER_SESSION * 2:
            self._sessions[session_id]["history"] = history[-(MAX_HISTORY_PER_SESSION * 2):]
        self._sessions[session_id]["last_active"] = datetime.utcnow()

    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

    def active_sessions(self) -> int:
        self._evict_expired()
        return len(self._sessions)


session_manager = SessionManager()
