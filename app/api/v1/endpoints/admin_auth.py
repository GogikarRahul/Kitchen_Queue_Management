# app/api/v1/endpoints/auth.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)
from app.models.user import User, UserRole
from app.models.chef import Chef
from app.schemas.auth import SignupSchema

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================
# ADMIN SIGNUP (create Admin only)
# ============================================================

@router.post("/admin/signup")
async def admin_signup(
    payload: SignupSchema,
    db: AsyncSession = Depends(get_db),
):
    email = payload.email.strip().lower()

    if payload.role != UserRole.admin:
        raise HTTPException(403, "You can create only admin accounts")

    if not payload.name.strip():
        raise HTTPException(400, "Name cannot be empty")

    # Check duplicate
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(400, "Email already registered")

    user = User(
        name=payload.name.strip(),
        email=email,
        hashed_password=hash_password(payload.password),
        role=UserRole.admin,
        is_active=True,
    )

    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Error creating admin")

    await db.refresh(user)
    return {
        "message": "Admin created",
        "user_id": user.id,
        "role": user.role,
    }


# ============================================================
# USER SIGNUP (Customer signup)
# ============================================================

@router.post("/user/signup")
async def user_signup(
    payload: SignupSchema,
    db: AsyncSession = Depends(get_db)
):
    email = payload.email.strip().lower()

    if not payload.name.strip():
        raise HTTPException(400, "Name cannot be empty")

    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(400, "Email already registered")

    user = User(
        name=payload.name.strip(),
        email=email,
        hashed_password=hash_password(payload.password),
        role=UserRole.customer,
        is_active=True,
    )

    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Error creating user")

    await db.refresh(user)
    return {
        "message": "User registered",
        "user_id": user.id,
        "role": user.role,
    }


# ============================================================
# UNIFIED LOGIN (Admin/User ⇢ email, Chef ⇢ phone)
# ============================================================

@router.post("/login")
async def unified_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    username = form_data.username.strip().lower()
    password = form_data.password

    # -----------------------------------------
    # Admin/User Login (email)
    # -----------------------------------------
    result = await db.execute(select(User).where(User.email == username))
    user = result.scalar_one_or_none()

    if user and verify_password(password, user.hashed_password):
        token = create_access_token({
            "user_id": user.id,
            "role": user.role.value
        })
        return {
            "access_token": token,
            "token_type": "bearer",
            "type": "user"
        }

    # -----------------------------------------
    # Chef Login (phone_number)
    # -----------------------------------------
    result = await db.execute(select(Chef).where(Chef.phone_number == username))
    chef = result.scalar_one_or_none()

    if chef and verify_password(password, chef.password):
        token = create_access_token({"chef_id": chef.id})
        return {
            "access_token": token,
            "token_type": "bearer",
            "type": "chef"
        }

    # -----------------------------------------
    # Authentication Failed
    # -----------------------------------------
    raise HTTPException(401, "Invalid email/phone or password")
