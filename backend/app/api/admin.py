from fastapi import APIRouter, Depends
from app.api.deps import require_admin
from app.models.user_store import user_db
from app.models.schemas import UserOut
from app.services.session_manager import session_manager
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserOut])
def list_users(admin: dict = Depends(require_admin)):
    """List all registered users (admin only)."""
    return [
        UserOut(
            id=u["id"],
            username=u["username"],
            email=u["email"],
            role=u["role"],
            created_at=u["created_at"],
        )
        for u in user_db.list_users()
    ]


@router.get("/sessions/active")
def active_sessions(admin: dict = Depends(require_admin)):
    """Get count of active chat sessions."""
    return {"active_sessions": session_manager.active_sessions()}
