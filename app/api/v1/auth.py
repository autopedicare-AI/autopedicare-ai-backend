from fastapi import APIRouter, Request, HTTPException, Depends, status
from jose import JWTError
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.services.auth.google_auth import verify_google_token
from app.services.auth.apple_auth import verify_apple_token
from app.models.user import User
from app.models.audit import UserLoginHistory
from app.api.dependencies import get_db
from app.schemas.auth import (
    GoogleLoginRequest,
    AppleLoginRequest,
    AuthResponse,
    RefreshRequest,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["Authentication"])

limiter = Limiter(key_func=get_remote_address)


security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    try:
        payload = verify_token(token)
        if not payload:
            logger.error("Auth failure: invalid token provided")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("sub")
        if not user_id:
            logger.error("Auth failure: token missing 'sub' claim")
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error("Auth failure: user not found", user_id=user_id)
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError as exc:
        logger.error("Auth failure: JWTError while validating token", error=str(exc))
        raise credentials_exception


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
    if not user:
        user = User(
            email=google_user["email"],
            provider="google",
            provider_id=google_user["sub"],
            is_verified=google_user["email_verified"],
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    audit_log = UserLoginHistory(
        user_id=user.id,
        ip_address=context["ip"],
        device=context["device"],
        os=context["os"],
        browser=context["browser"],
        latitude=context["location"]["latitude"],
        longitude=context["location"]["longitude"],
        country=context["location"]["country"],
        city=context["location"]["city"],
        provider="google",
        user_agent=context["user_agent"],
    )
    db.add(audit_log)
    db.commit()

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

    # verify the token and extract user info
    apple_user = await verify_apple_token(token)
    if not apple_user:
        raise HTTPException(status_code=401, detail="Invalid Apple token")

    # find or create user in DB
    user = db.query(User).filter(User.provider_id == apple_user["sub"]).first()
    if not user:
        user = User(
            email=apple_user["email"],
            provider="apple",
            provider_id=apple_user["sub"],
            is_verified=apple_user["email_verified"],
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    audit_log = UserLoginHistory(
        user_id=user.id,
        ip_address=context["ip"],
        device=context["device"],
        os=context["os"],
        browser=context["browser"],
        latitude=context["location"]["latitude"],
        longitude=context["location"]["longitude"],
        country=context["location"]["country"],
        city=context["location"]["city"],
        provider="apple",
        user_agent=context["user_agent"],
    )
    db.add(audit_log)
    db.commit()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"email": user.email},
    }


@limiter.limit("5/minute")
@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(payload: RefreshRequest):
    token = verify_token(payload.refresh_token)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if token.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = token.get("sub")
    new_access_token = create_access_token({"sub": user_id})
    new_refresh_token = create_refresh_token({"sub": user_id})

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": {},  # Refresh might not have full user data in token
    }
