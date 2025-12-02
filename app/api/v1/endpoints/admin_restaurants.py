# app/api/v1/endpoints/admin_restaurants.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.notification import GlobalNotificationCreate,ChefNotificationCreate,NotificationOut
from app.services.notification_service import create_chef_notification_service,create_global_notification_service
from app.models.notification import ChefNotificationRead,ChefNotification
from app.api.deps import admin_required
from app.db.session import get_db
from sqlalchemy import select
from app.models.chef import Chef
# Schemas
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
    RestaurantSettingsBase,
    RestaurantSettingsUpdate,
    RestaurantSettingsResponse,
)

from app.schemas.chef import (
    ChefCreate,
    ChefOut,
    ChefUpdate,
)

# Services
from app.services.restaurant_service import (
    create_restaurant,
    list_restaurants,
    get_restaurant,
    update_restaurant,
    toggle_restaurant_open_status,
    create_or_update_settings,
    get_restaurant_settings,
)

from app.services.chef_service import (
    create_chef_service,
    list_chefs_service,
    update_chef_service,
    delete_chef_service,
)

router = APIRouter(
    prefix="/admin/restaurants",
    tags=["Admin - Restaurants"],
)


# ============================================================
# CREATE RESTAURANT (Owner = Admin)
# ============================================================

@router.post("/", response_model=RestaurantResponse)
async def create_restaurant_endpoint(
    payload: RestaurantCreate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    # Pass owner ID to service
    return await create_restaurant(db, payload, current_admin.id)


# ============================================================
# LIST RESTAURANTS (Super admins can see all)
# ============================================================

# @router.get("/", response_model=List[RestaurantResponse])
# async def list_restaurants_endpoint(
#     db: AsyncSession = Depends(get_db),
#     current_admin=Depends(admin_required),
# ):
#     return await list_restaurants(db)


# ============================================================
# GET RESTAURANT
# ============================================================

@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant_endpoint(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    restaurant = await get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")

    return restaurant


# ============================================================
# UPDATE RESTAURANT (Owner Only)
# ============================================================

@router.patch("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant_endpoint(
    restaurant_id: int,
    payload: RestaurantUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    restaurant = await update_restaurant(db, restaurant_id, payload, current_admin.id)

    if not restaurant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")

    return restaurant


# ============================================================
# CHANGE OPEN/CLOSE STATUS
# ============================================================

@router.patch("/{restaurant_id}/status", response_model=RestaurantResponse)
async def set_restaurant_status(
    restaurant_id: int,
    is_open: bool,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    restaurant = await toggle_restaurant_open_status(
        db, restaurant_id, is_open, current_admin.id
    )

    if not restaurant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")

    return restaurant


# ============================================================
# SETTINGS
# ============================================================

@router.put("/{restaurant_id}/settings", response_model=RestaurantSettingsResponse)
async def create_or_update_settings_endpoint(
    restaurant_id: int,
    payload: RestaurantSettingsBase | RestaurantSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    # Ensures restaurant exists
    restaurant = await get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")

    # Ownership validated inside service
    return await create_or_update_settings(
        db,
        restaurant_id,
        payload,
        current_admin.id
    )


@router.get("/{restaurant_id}/settings", response_model=RestaurantSettingsResponse)
async def get_settings_endpoint(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    settings = await get_restaurant_settings(db, restaurant_id)
    if not settings:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Settings not found")
    return settings


# ============================================================
# CHEF MANAGEMENT
# ============================================================

@router.post("/{restaurant_id}/chefs", response_model=ChefOut)
async def create_chef(
    restaurant_id: int,
    payload: ChefCreate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    # Ensure admin owns this restaurant
    restaurant = await get_restaurant(db, restaurant_id)
    if not restaurant or restaurant.owner_id != current_admin.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed")

    return await create_chef_service(db, restaurant_id, payload)


@router.get("/{restaurant_id}/chefs", response_model=List[ChefOut])
async def list_chefs(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    restaurant = await get_restaurant(db, restaurant_id)
    if not restaurant or restaurant.owner_id != current_admin.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed")

    return await list_chefs_service(db, restaurant_id)


@router.patch("/chefs/{chef_id}", response_model=ChefOut)
async def update_chef(
    chef_id: int,
    payload: ChefUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    return await update_chef_service(db, chef_id, payload, current_admin.id)


@router.delete("/chefs/{chef_id}")
async def delete_chef(
    chef_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    return await delete_chef_service(db, chef_id, current_admin.id)


# ---------------------------------------------------------
# 1️⃣ GLOBAL NOTIFICATION (Admin Only)
# ---------------------------------------------------------
@router.post("/{restaurant_id}/notifications/global")
async def send_global_notification(
    restaurant_id: int,
    payload: GlobalNotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(admin_required),   # <-- ADMIN GUARD
):
    return await create_global_notification_service(db, restaurant_id, payload)


# ---------------------------------------------------------
# 2️⃣ CHEF-SPECIFIC NOTIFICATION (Admin Only)
# ---------------------------------------------------------
@router.post("/{restaurant_id}/notifications/chef")
async def send_chef_notification(
    restaurant_id: int,
    payload: ChefNotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(admin_required),   # <-- ADMIN GUARD
):
    return await create_chef_notification_service(db, restaurant_id, payload)

@router.get("/notifications/{notification_id}/unread")
async def get_notification_unread(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(admin_required),
):
    # Load notification
    notif = await db.get(ChefNotification, notification_id)

    if not notif:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    # Get all chefs in same restaurant
    chefs_stmt = select(Chef.id).where(
        Chef.restaurant_id == notif.restaurant_id
    )
    chefs = (await db.execute(chefs_stmt)).scalars().all()

    # Get all chefs who read it
    reads_stmt = select(ChefNotificationRead.chef_id).where(
        ChefNotificationRead.notification_id == notification_id
    )
    read_chefs = (await db.execute(reads_stmt)).scalars().all()

    unread = [c for c in chefs if c not in read_chefs]

    return {"unread_chefs": unread}