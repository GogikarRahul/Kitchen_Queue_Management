# app/api/deps.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_token
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.chef import Chef

settings = get_settings()

# ONE OAUTH2 SCHEME FOR EVERYONE
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------
# GET CURRENT USER (Admin/User)
# ---------------------------------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:

    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(403, "Not a user token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "User not found")

    return user


# ---------------------------------------------------
# CHEF REQUIRED GUARD
# ---------------------------------------------------
async def chef_required(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Chef:

    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")

    chef_id = payload.get("chef_id")
    if not chef_id:
        raise HTTPException(403, "Not a chef token")

    result = await db.execute(select(Chef).where(Chef.id == chef_id))
    chef = result.scalar_one_or_none()

    if not chef:
        raise HTTPException(404, "Chef not found")

    return chef


# ---------------------------------------------------
# ROLE GUARDS
# ---------------------------------------------------
def admin_required(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(403, "Admin access required")
    return current_user


def customer_required(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.customer:
        raise HTTPException(403, "Customer access required")
    return current_user

def customer_required(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.customer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer access required",
        )
    return current_user


