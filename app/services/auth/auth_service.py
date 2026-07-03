from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.audit import UserLoginHistory
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


async def get_or_create_oauth_user(
    *,
    db: AsyncSession,
    email: str,
    provider: str,
    provider_id: str,
    is_verified: bool,
):
    stmt = select(User).where(
        User.provider_id == provider_id
    )

    result = await db.execute(stmt)

    user = result.scalar_one_or_none()

    if user:
        return user

    user = User(
        email=email,
        provider=provider,
        provider_id=provider_id,
        is_verified=is_verified,
    )

    db.add(user)

    try:
        await db.flush()

    except IntegrityError:
        await db.rollback()

        result = await db.execute(stmt)

        user = result.scalar_one()

    return user


async def create_login_audit(
    *,
    db: AsyncSession,
    user: User,
    context: dict,
    provider: str,
):
    audit_log = UserLoginHistory(
        user_id=user.id,
        ip_address=context.get("ip"),
        device=context.get("device"),
        os=context.get("os"),
        browser=context.get("browser"),
        latitude=context.get("location", {}).get("latitude"),
        longitude=context.get("location", {}).get("longitude"),
        country=context.get("location", {}).get("country"),
        city=context.get("location", {}).get("city"),
        provider=provider,
        user_agent=context.get("user_agent"),
    )

    db.add(audit_log)
    return audit_log