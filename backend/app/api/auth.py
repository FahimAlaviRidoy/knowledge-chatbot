from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import UserRegister, UserLogin, Token, TokenRefresh, UserOut
from app.models.user_store import user_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.logger import log
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: UserRegister):
    """Register a new user account."""
    try:
        user = user_db.create(body.username, body.email, body.password, body.role)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return UserOut(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["role"],
        created_at=user["created_at"],
    )


@router.post("/login", response_model=Token)
def login(body: UserLogin):
    """Login and receive JWT tokens."""
    user = user_db.get_by_username(body.username)
    if not user or not verify_password(body.password, user["hashed_password"]):
        log.warning(f"Failed login attempt for username='{body.username}'")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access = create_access_token({"sub": user["id"], "role": user["role"]})
    refresh = create_refresh_token({"sub": user["id"]})
    log.info(f"User '{body.username}' logged in")
    return Token(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=Token)
def refresh_token(body: TokenRefresh):
    """Refresh access token using refresh token."""
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user = user_db.get_by_id(payload.get("sub", ""))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_access_token({"sub": user["id"], "role": user["role"]})
    new_refresh = create_refresh_token({"sub": user["id"]})
    return Token(access_token=access, refresh_token=new_refresh)


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    """Get the currently authenticated user."""
    return UserOut(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        created_at=current_user["created_at"],
    )
