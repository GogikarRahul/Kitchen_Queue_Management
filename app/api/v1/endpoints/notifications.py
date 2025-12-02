from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import chef_required

from app.schemas.notification import NotificationOut
from app.models.notification import ChefNotification

from app.services.notification_service import (
    list_notifications,
    mark_notification_read,
    mark_all_read,
)

router = APIRouter(prefix="/chef", tags=["Chef - Notifications"])


# -------------------------------------------------------
# Helper: ensure chef belongs to restaurant
# -------------------------------------------------------
def ensure_same_restaurant(current_chef, restaurant_id: int):
    if current_chef.restaurant_id != restaurant_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access notifications for another restaurant.",
        )


# -------------------------------------------------------
# 1️⃣ LIST ALL NOTIFICATIONS (GLOBAL + PERSONAL)
# -------------------------------------------------------
@router.get("/restaurants/{restaurant_id}/notifications", response_model=list[NotificationOut])
async def get_notifications(
    restaurant_id: int,
    chef_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    ensure_same_restaurant(current_chef, restaurant_id)

    return await list_notifications(
        db=db,
        restaurant_id=restaurant_id,
        chef_id=chef_id,
        current_restaurant_id=current_chef.restaurant_id,
    )


# -------------------------------------------------------
# 2️⃣ GET ONLY GLOBAL NOTIFICATIONS
# -------------------------------------------------------
@router.get("/restaurants/{restaurant_id}/notifications/global", response_model=list[NotificationOut])
async def get_global_notifications(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):

    ensure_same_restaurant(current_chef, restaurant_id)

    stmt = (
        select(ChefNotification)
        .where(ChefNotification.restaurant_id == restaurant_id)
        .where(ChefNotification.chef_id.is_(None))  # GLOBAL ONLY
        .order_by(ChefNotification.created_at.desc())
    )

    result = await db.execute(stmt)
    return result.scalars().all()


# -------------------------------------------------------
# 3️⃣ GET ONLY PERSONAL NOTIFICATIONS (chef-specific)
# -------------------------------------------------------
@router.get("/restaurants/{restaurant_id}/notifications/personal", response_model=list[NotificationOut])
async def get_personal_notifications(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):

    ensure_same_restaurant(current_chef, restaurant_id)

    stmt = (
        select(ChefNotification)
        .where(ChefNotification.restaurant_id == restaurant_id)
        .where(ChefNotification.chef_id == current_chef.id)  # PERSONAL ONLY
        .order_by(ChefNotification.created_at.desc())
    )

    result = await db.execute(stmt)
    return result.scalars().all()


# -------------------------------------------------------
# MARK SINGLE NOTIFICATION READ
# -------------------------------------------------------
@router.patch("/notifications/{notification_id}/read")
async def read_one(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):

    stmt = select(ChefNotification).where(ChefNotification.id == notification_id)
    notif = (await db.execute(stmt)).scalar_one_or_none()

    if not notif:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")

    if notif.restaurant_id != current_chef.restaurant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    if notif.chef_id not in (None, current_chef.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This notification is not for you")

    return await mark_notification_read(
        db=db,
        notification_id=notification_id,
        current_chef_id=current_chef.id,
        current_restaurant_id=current_chef.restaurant_id,
    )


# -------------------------------------------------------
# MARK ALL NOTIFICATIONS READ
# -------------------------------------------------------
@router.patch("/restaurants/{restaurant_id}/notifications/read-all")
async def read_all(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):

    ensure_same_restaurant(current_chef, restaurant_id)

    return await mark_all_read(
        db=db,
        restaurant_id=restaurant_id,
        current_chef_id=current_chef.id,
        current_restaurant_id=current_chef.restaurant_id,
    )
