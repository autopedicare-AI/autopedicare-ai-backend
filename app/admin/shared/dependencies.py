from fastapi import Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.models.user import User
from app.permissions.permissions import Role, ROLE_PERMISSIONS, Permission


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )
    return current_user
