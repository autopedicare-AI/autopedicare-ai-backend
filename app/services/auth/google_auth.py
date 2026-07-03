from loguru import logger
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi.concurrency import run_in_threadpool
from fastapi import HTTPException, status
from app.core.config import settings


async def verify_google_token(token: str):
    try:
        id_info = await run_in_threadpool(
            id_token.verify_oauth2_token,
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

        if id_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Invalid issuer")

        return {
            "sub": id_info["sub"],
            "email": id_info.get("email"),
            "email_verified": id_info.get("email_verified"),
        }
    except Exception as e:
        logger.exception("Google token verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google token verification failed",
        )
