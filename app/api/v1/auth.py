import uuid

from fastapi import APIRouter, Request, HTTPException, Depends, status
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, verify_token
from app.services.auth.google_auth import verify_google_token
from app.services.auth.apple_auth import verify_apple_token
from app.models.user import User
from app.models.audit import UserLoginHistory
from app.db.session import get_db
from app.schemas.auth import (
    GoogleLoginRequest,
    AppleLoginRequest,
    AuthResponse,
    RefreshRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

limiter = Limiter(key_func=get_remote_address)


@limiter.limit("5/minute")
@router.post("/google", response_model=AuthResponse)
async def google_auth(
    request: Request, payload: GoogleLoginRequest, db: Session = Depends(get_db)
):
    context = request.state.context

    id_token = payload.token

    if not id_token:
        raise HTTPException(status_code=400, detail="ID token missing")

    google_user = await verify_google_token(id_token)

    user = db.query(User).filter(User.provider_id == google_user["sub"]).first()

    try:

        if not user:
            user = User(
                email=google_user["email"],
                provider="google",
                provider_id=google_user["sub"],
                is_verified=google_user["email_verified"],
            )
            db.add(user)
            db.commit()

        audit_log = UserLoginHistory(
            user_id=user.id,
            ip_address=context["ip"],
            device=context["device"],
            os=context["os"],
            browser=context["browser"],
            latitude=(
                context.get("location", {}).get("latitude")
                if context.get("location")
                else None
            ),
            longitude=(
                context.get("location", {}).get("longitude")
                if context.get("location")
                else None
            ),
            country=(
                context.get("location", {}).get("country")
                if context.get("location")
                else None
            ),
            city=(
                context.get("location", {}).get("city")
                if context.get("location")
                else None
            ),
            provider="google",
            user_agent=context["user_agent"],
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        logger.error("Google auth transaction failed: {error}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"email": user.email},
    }


@limiter.limit("5/minute")
@router.post("/apple", response_model=AuthResponse)
async def apple_login(
    payload: AppleLoginRequest, request: Request, db: Session = Depends(get_db)
):
    context = request.state.context
    token = payload.token
    if not token:
        raise HTTPException(status_code=400, detail="Identity token missing")

    apple_user = await verify_apple_token(token)
    if not apple_user:
        raise HTTPException(status_code=401, detail="Invalid Apple token")

    user = db.query(User).filter(User.provider_id == apple_user["sub"]).first()

    try:
        if not user:
            user = User(
                email=apple_user["email"],
                provider="apple",
                provider_id=apple_user["sub"],
                is_verified=apple_user["email_verified"],
            )
            db.add(user)
            db.commit()

        audit_log = UserLoginHistory(
            user_id=user.id,
            ip_address=context["ip"],
            device=context["device"],
            os=context["os"],
            browser=context["browser"],
            latitude=(
                context.get("location", {}).get("latitude")
                if context.get("location")
                else None
            ),
            longitude=(
                context.get("location", {}).get("longitude")
                if context.get("location")
                else None
            ),
            country=(
                context.get("location", {}).get("country")
                if context.get("location")
                else None
            ),
            city=(
                context.get("location", {}).get("city")
                if context.get("location")
                else None
            ),
            provider="apple",
            user_agent=context["user_agent"],
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        logger.error("Apple auth transaction failed: {error}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"email": user.email},
    }


@limiter.limit("5/minute")
@router.post("/refresh")
async def refresh_token(
    request: Request, payload: RefreshRequest, db: Session = Depends(get_db)
):
    token = verify_token(payload.refresh_token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = token.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing user identity.",
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identity in token.",
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    token_data = {"sub": str(user.id)}

    new_access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token(data=token_data)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }
