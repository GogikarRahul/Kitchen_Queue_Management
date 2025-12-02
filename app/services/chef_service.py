# app/services/chef_service.py

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chef import Chef
from app.core.security import hash_password, verify_password
from app.schemas.chef import ChefUpdate


# -------------------------------------------------
# INTERNAL HELPER
# -------------------------------------------------
async def _get_chef(db: AsyncSession, chef_id: int) -> Chef:
    """Fetch chef or raise 404."""
    result = await db.execute(select(Chef).where(Chef.id == chef_id))
    chef = result.scalar_one_or_none()

    if not chef:
        raise HTTPException(status_code=404, detail="Chef not found")

    return chef


async def _ensure_unique_phone(db: AsyncSession, phone: str, exclude_id: int | None = None):
    """Ensure phone number is not already taken by another chef."""
    query = select(Chef).where(Chef.phone_number == phone)
    if exclude_id:
        query = query.where(Chef.id != exclude_id)

    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already in use",
        )


# -------------------------------------------------
# CREATE CHEF (ASYNC)
# -------------------------------------------------
async def create_chef_service(db: AsyncSession, restaurant_id: int, payload):
    # Check unique phone_number
    existing = await db.execute(
        select(Chef).where(Chef.phone_number == payload.phone_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Phone number already registered")

    chef = Chef(
        restaurant_id=restaurant_id,
        name=payload.name,
        phone_number=payload.phone_number,   # ✅ Correct field
        password=hash_password(payload.password),  # ✅ Correct field
    )

    db.add(chef)
    await db.commit()
    await db.refresh(chef)

    return chef

# -------------------------------------------------
# LIST CHEFS (ASYNC)
# -------------------------------------------------
async def list_chefs_service(db: AsyncSession, restaurant_id: int):
    stmt = select(Chef).where(Chef.restaurant_id == restaurant_id)
    result = await db.execute(stmt)
    return result.scalars().all()


# -------------------------------------------------
# UPDATE CHEF (ASYNC)
# -------------------------------------------------
async def update_chef_service(
    db: AsyncSession, chef_id: int, payload: ChefUpdate, current_restaurant_id: int | None = None
):
    chef = await _get_chef(db, chef_id)

    # Prevent cross-restaurant updates
    if current_restaurant_id is not None and chef.restaurant_id != current_restaurant_id:
        raise HTTPException(403, "You cannot update chefs from another restaurant")

    # Phone uniqueness check
    if payload.phone_number is not None:
        await _ensure_unique_phone(db, payload.phone_number, exclude_id=chef.id)

    # Safe updates
    if payload.name is not None:
        if not payload.name.strip():
            raise HTTPException(400, "Name cannot be empty")
        chef.name = payload.name.strip()

    if payload.phone_number is not None:
        chef.phone_number = payload.phone_number

    if payload.password is not None:
        if payload.password.strip() == "":
            raise HTTPException(400, "Password cannot be empty")
        chef.password = hash_password(payload.password)

    if payload.status is not None:
        if payload.status not in ["active", "inactive"]:
            raise HTTPException(400, "Invalid status value")
        chef.status = payload.status

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Database error while updating chef")

    await db.refresh(chef)
    return chef


# -------------------------------------------------
# DELETE CHEF (ASYNC)
# -------------------------------------------------
async def delete_chef_service(db: AsyncSession, chef_id: int, current_restaurant_id: int | None = None):
    chef = await _get_chef(db, chef_id)

    # Prevent deleting another restaurant's chef
    if current_restaurant_id is not None and chef.restaurant_id != current_restaurant_id:
        raise HTTPException(403, "You cannot delete chefs from another restaurant")

    try:
        await db.delete(chef)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            400,
            "Chef cannot be deleted because they are referenced by other records (orders, logs)"
        )

    return {"message": "Chef deleted successfully"}


# -------------------------------------------------
# CHEF LOGIN (ASYNC)
# -------------------------------------------------
async def chef_login_service(db: AsyncSession, phone: str, password: str):
    stmt = select(Chef).where(Chef.phone_number == phone)
    result = await db.execute(stmt)
    chef = result.scalar_one_or_none()

    if not chef:
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    # Chef must be active
    if chef.status != "active":
        raise HTTPException(status_code=403, detail="Chef account is disabled")

    if not verify_password(password, chef.password):
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    return chef
