from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.limiter import limiter
from app.middleware.access_control import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserProfileUpdate, UserResponse
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    update_user_profile,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register(request: Request, data: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, data.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    if get_user_by_email(db, data.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return create_user(db, data)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    payload = {"sub": str(user.id), "role": user.role}
    return TokenResponse(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_refresh_token(data.refresh_token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user = get_user_by_id(db, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    token_payload = {"sub": str(user.id), "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=create_refresh_token(token_payload),
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(_: User = Depends(get_current_user)):
    return {"message": "Logged out successfully. Discard your tokens on the client."}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.email and data.email != current_user.email:
        if get_user_by_email(db, data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    updated_user, error = update_user_profile(db, current_user, data)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return updated_user
