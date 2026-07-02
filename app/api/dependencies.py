from loguru import logger
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from uuid import UUID

from app.core.security import verify_token
from app.models.user import User
from app.db.session import get_db

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        user_id = payload.get("sub")
        if not user_id:
            logger.error("Auth failure: token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )

        try:
            user_uuid = UUID(user_id)
        except ValueError:
            logger.error(
                "Auth failure: token sub claim is not a valid UUID", sub=user_id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )

        stmt = select(User).where(User.id == user_uuid)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error("Auth failure: user not found", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return user
    except JWTError as exc:
        logger.error("Auth failure: JWTError while validating token", error=str(exc))
        raise credentials_exception
    

async def _require_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        logger.warning("Unauthorized access attempt by non-admin user", user_id=str(user.id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
    return user