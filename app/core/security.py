import uuid
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from loguru import logger
from datetime import datetime, timedelta, timezone
from app.core.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def generate_token(
    *,
    data: dict,
    token_type: str,
    expires_delta: timedelta,
):
    now = datetime.now(timezone.utc)

    payload = data.copy()

    payload.update(
        {
            "jti": str(uuid.uuid4()),
            "type": token_type,
            "iat": now,
            "nbf": now,
            "exp": now + expires_delta,
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
        }
    )

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_access_token(data: dict):
    return generate_token(
        data=data,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(data: dict):
    return generate_token(
        data=data,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def verify_token(token: str):
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
    except ExpiredSignatureError:
        logger.error("JWT expired")
        return None
    except JWTClaimsError:
        logger.error("JWT claims validation failed")
        return None
    except JWTError:
        logger.error("JWT validation failed")
        return None
