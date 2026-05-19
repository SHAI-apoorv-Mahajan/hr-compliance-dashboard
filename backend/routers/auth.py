"""Auth router — login + me. FR-001."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import AppUser
from routers.deps import get_current_user
from schemas.auth import LoginRequest, TokenResponse, UserResponse
from utils.auth_utils import create_access_token, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(AppUser).filter(AppUser.email == payload.email).first()
    # Same response shape whether email missing or password wrong (FR-001 verbatim).
    if (
        not user
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token(subject=user.email, extra={"role": user.role})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current: AppUser = Depends(get_current_user)) -> AppUser:
    return current
