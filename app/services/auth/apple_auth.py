import httpx
from jose import jwt, jwk
from jose.utils import base64url_decode
from fastapi import HTTPException, status
from app.core.config import settings

APPLE_PUBLIC_KEYS_URL = "https://appleid.apple.com/auth/keys"


async def verify_apple_token(token: str):
    try:
        # fetch Apple's public keys
        async with httpx.AsyncClient() as client:
            response = await client.get(APPLE_PUBLIC_KEYS_URL)
            apple_keys = response.json().get("keys", [])

        # Get kid from token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # fine the matching key from apple's public keys
        key = next((k for k in apple_keys if k["kid"] == kid), None)
        if not key:
            raise HTTPException(
                status_code=401, detail="Invalid token: no matching key found"
            )

        # construct the public key and decode
        public_key = jwk.construct(key)
        payload = jwt.decode(
            token,
            public_key.to_dict(),
            algorithms=["RS256"],
            audience=settings.APPLE_CLIENT_ID,
            issuer="https://appleid.apple.com",
        )

        return {
            "sub": payload["sub"],
            "email": payload.get("email"),
            "email_verified": payload.get("email_verified"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Apple token verification failed: {str(e)}",
        )
