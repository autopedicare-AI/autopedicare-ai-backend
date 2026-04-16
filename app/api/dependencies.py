from loguru import logger
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from uuid import UUID
from app.core.security import verify_token
from app.models.user import User
from app.db.session import get_db

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
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

        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            logger.error("Auth failure: user not found", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return user
    except JWTError as exc:
        logger.error("Auth failure: JWTError while validating token", error=str(exc))
        raise credentials_exception