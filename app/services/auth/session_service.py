from app.core.redis import redis_client


class SessionService:
    REFRESH_TOKEN_PREFIX = "refresh"

    @classmethod
    async def store_refresh_token(
        cls,
        *,
        user_id: str,
        jti: str,
        expires_in: int,
    ):
        key = f"{cls.REFRESH_TOKEN_PREFIX}:{jti}"
        return await redis_client.set(key, user_id, ex=expires_in * 24 * 3600)

    @classmethod
    async def validate_refresh_token(cls, jti: str):
        key = f"{cls.REFRESH_TOKEN_PREFIX}:{jti}"
        return await redis_client.get(key)

    @classmethod
    async def revoke_refresh_token(cls, jti: str):
        key = f"{cls.REFRESH_TOKEN_PREFIX}:{jti}"
        return await redis_client.delete(key)