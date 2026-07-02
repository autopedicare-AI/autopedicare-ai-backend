import uuid
from fastapi import APIRouter, Request, HTTPException, Depends, status
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import create_access_token, create_refresh_token, verify_token
from app.services.auth.google_auth import verify_google_token
from app.services.auth.apple_auth import verify_apple_token
from app.models.user import User
from app.services.auth.session_service import SessionService
from app.db.session import get_db
from app.core.config import settings
from app.services.auth.auth_service import get_or_create_oauth_user, create_login_audit
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
    request: Request, payload: GoogleLoginRequest, db: AsyncSession = Depends(get_db)
):
    context = getattr(request.state, "context", {})

    id_token = payload.token

    if not id_token:
        raise HTTPException(status_code=400, detail="ID token missing")

    google_user = await verify_google_token(id_token)

    if not google_user:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    try:
        user = await get_or_create_oauth_user(
            db=db,
            email=google_user["email"],
            provider="google",
            provider_id=google_user["sub"],
            is_verified=google_user["email_verified"],
        )

        audit_log = await create_login_audit(
            db=db,
            user=user,
            context=context,
            provider="google",
        )
        db.add(audit_log)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error("Google auth transaction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    refresh_payload = verify_token(refresh_token)
    
    try:
        await SessionService.store_refresh_token(
            user_id=user.id,
            jti=refresh_payload.get("jti"),
            expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )
    except Exception as e:
        logger.error("Failed to store refresh token")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"email": user.email},
    }


@limiter.limit("5/minute")
@router.post("/apple", response_model=AuthResponse)
async def apple_login(
    payload: AppleLoginRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    context = request.state.context
    token = payload.token
    if not token:
        raise HTTPException(status_code=400, detail="Identity token missing")

    apple_user = await verify_apple_token(token)
    if not apple_user:
        raise HTTPException(status_code=401, detail="Invalid Apple token")

    try:
        user = await get_or_create_oauth_user(
            db=db,
            email=apple_user["email"],
            provider="apple",
            provider_id=apple_user["sub"],
            is_verified=apple_user["email_verified"],
        )

        await create_login_audit(
            db=db,
            user=user,
            context=context,
            provider="apple",
        )

        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error("Apple auth transaction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    refresh_payload = verify_token(refresh_token)
    
    try:
        await SessionService.store_refresh_token(
            user_id=user.id,
            jti=refresh_payload.get("jti"),
            expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )
    except Exception as e:
        logger.error("Failed to store refresh token")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"email": user.email},
    }


@limiter.limit("5/minute")
@router.post("/refresh")
async def refresh_token(
    request: Request, payload: RefreshRequest, db: AsyncSession = Depends(get_db)
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

    jti = token.get("jti")

    if not jti:
        raise HTTPException(
            status_code=401,
            detail="Missing token ID",
        )
    
    stored_session = await SessionService.validate_refresh_token(
        jti=jti
    )
    
    if not stored_session:
        raise HTTPException(
            status_code=401,
            detail="Refresh token has been revoked",
        )
    
    await SessionService.revoke_refresh_token(
        jti=jti
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

    stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    
    refresh_payload = verify_token(new_refresh_token)

    await SessionService.store_refresh_token(
        user_id=user_id,
        jti=refresh_payload["jti"],
        expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    payload: RefreshRequest,
):
    token_payload = verify_token(
        payload.refresh_token
    )

    if not token_payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    await SessionService.revoke_refresh_token(
        jti=token_payload["jti"]
    )

    return {
        "message": "Logged out successfully"
    }