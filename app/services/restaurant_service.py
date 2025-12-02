# app/services/restaurant_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from typing import List, Optional

from app.models.restaurant import Restaurant, RestaurantSettings
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantSettingsBase,
    RestaurantSettingsUpdate,
)


# ============================================================
# INTERNAL HELPERS
# ============================================================

async def _get_restaurant(db: AsyncSession, restaurant_id: int) -> Optional[Restaurant]:
    result = await db.execute(
        select(Restaurant).where(Restaurant.id == restaurant_id)
    )
    return result.scalar_one_or_none()


async def _get_settings(db: AsyncSession, restaurant_id: int) -> Optional[RestaurantSettings]:
    result = await db.execute(
        select(RestaurantSettings).where(RestaurantSettings.restaurant_id == restaurant_id)
    )
    return result.scalar_one_or_none()


async def _ensure_owner(restaurant: Restaurant, current_owner_id: int):
    if restaurant.owner_id != current_owner_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "You are not allowed to manage this restaurant."
        )


# ============================================================
# CREATE RESTAURANT
# ============================================================

async def create_restaurant(
    db: AsyncSession,
    payload: RestaurantCreate,
    current_owner_id: int
) -> Restaurant:

    # Prevent duplicates on name + phone
    existing = await db.execute(
        select(Restaurant).where(
            (Restaurant.name.ilike(payload.name)) |
            (Restaurant.phone == payload.phone)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "A restaurant with this name or phone already exists")

    restaurant = Restaurant(
        name=payload.name.strip(),
        address=payload.address.strip(),
        phone=payload.phone,
        owner_id=current_owner_id,
        is_open=True,
    )

    db.add(restaurant)

    try:
        await db.flush()

        # Auto-create settings row
        settings = RestaurantSettings(
            restaurant_id=restaurant.id,
            auto_accept_orders=False,
            max_active_orders=10,
        )
        db.add(settings)

        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Error while creating restaurant")

    await db.refresh(restaurant)
    return restaurant


# ============================================================
# GET RESTAURANT
# ============================================================

async def get_restaurant(db: AsyncSession, restaurant_id: int) -> Optional[Restaurant]:
    return await _get_restaurant(db, restaurant_id)


# ============================================================
# LIST RESTAURANTS
# ============================================================

async def list_restaurants(db: AsyncSession) -> List[Restaurant]:
    result = await db.execute(select(Restaurant))
    return result.scalars().all()


# ============================================================
# UPDATE RESTAURANT
# ============================================================

async def update_restaurant(
    db: AsyncSession,
    restaurant_id: int,
    payload: RestaurantUpdate,
    current_owner_id: int
) -> Restaurant:

    restaurant = await _get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(404, "Restaurant not found")

    # Ownership validation
    _ensure_owner(restaurant, current_owner_id)

    # Apply sanitized updates
    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(400, "Name cannot be empty")
        restaurant.name = name

    if payload.address is not None:
        address = payload.address.strip()
        if not address:
            raise HTTPException(400, "Address cannot be empty")
        restaurant.address = address

    if payload.phone is not None:
        restaurant.phone = payload.phone

    if payload.is_open is not None:
        restaurant.is_open = payload.is_open

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Error updating restaurant")

    await db.refresh(restaurant)
    return restaurant


# ============================================================
# OPEN / CLOSE RESTAURANT
# ============================================================

async def toggle_restaurant_open_status(
    db: AsyncSession,
    restaurant_id: int,
    is_open: bool,
    current_owner_id: int
):
    restaurant = await _get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(404, "Restaurant not found")

    _ensure_owner(restaurant, current_owner_id)

    restaurant.is_open = is_open

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(500, "Error updating restaurant status")

    await db.refresh(restaurant)
    return restaurant


# ============================================================
# SETTINGS
# ============================================================

async def get_restaurant_settings(
    db: AsyncSession,
    restaurant_id: int
) -> Optional[RestaurantSettings]:
    return await _get_settings(db, restaurant_id)


async def create_or_update_settings(
    db: AsyncSession,
    restaurant_id: int,
    payload: RestaurantSettingsUpdate | RestaurantSettingsBase,
    current_owner_id: int
) -> RestaurantSettings:

    restaurant = await _get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(404, "Restaurant not found")

    _ensure_owner(restaurant, current_owner_id)

    settings = await _get_settings(db, restaurant_id)

    if settings is None:
        settings = RestaurantSettings(
            restaurant_id=restaurant_id,
            auto_accept_orders=(
                payload.auto_accept_orders if payload.auto_accept_orders is not None else False
            ),
            max_active_orders=(
                payload.max_active_orders if payload.max_active_orders is not None else 10
            ),
        )
        db.add(settings)

    else:
        if payload.auto_accept_orders is not None:
            settings.auto_accept_orders = payload.auto_accept_orders

        if payload.max_active_orders is not None:
            if payload.max_active_orders < 1:
                raise HTTPException(400, "max_active_orders must be ≥ 1")
            settings.max_active_orders = payload.max_active_orders

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(500, "Error updating restaurant settings")

    await db.refresh(settings)
    return settings
