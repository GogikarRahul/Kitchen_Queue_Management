from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from app.models.notification import ChefNotificationRead
from app.models.notification import ChefNotification
from app.schemas.notification import (
    GlobalNotificationCreate,
    ChefNotificationCreate
)

# ---------------------------------------------------------
# INTERNAL HELPER
# ---------------------------------------------------------
async def _get_notification(db: AsyncSession, notification_id: int):
    result = await db.execute(
        select(ChefNotification).where(ChefNotification.id == notification_id)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------
# LIST NOTIFICATIONS
# ---------------------------------------------------------
async def list_notifications(
    db: AsyncSession,
    restaurant_id: int,
    chef_id: int | None,
    current_restaurant_id: int
):

    if restaurant_id != current_restaurant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed")

    stmt = select(ChefNotification).where(
        ChefNotification.restaurant_id == restaurant_id
    )

    if chef_id is not None:
        stmt = stmt.where(
            (ChefNotification.chef_id == chef_id) |
            (ChefNotification.chef_id.is_(None))
        )

    result = await db.execute(stmt.order_by(ChefNotification.created_at.desc()))
    return result.scalars().all()


# ---------------------------------------------------------
# MARK SINGLE NOTIFICATION READ
# ---------------------------------------------------------

async def mark_notification_read(
    db: AsyncSession,
    notification_id: int,
    current_chef_id: int,
    current_restaurant_id: int,
):

    notification = await _get_notification(db, notification_id)
    if not notification:
        raise HTTPException(404, "Notification not found")

    if notification.restaurant_id != current_restaurant_id:
        raise HTTPException(403, "Not allowed")

    if notification.chef_id not in (None, current_chef_id):
        raise HTTPException(403, "Not your notification")

    # Check if read receipt exists
    existing = await db.execute(
        select(ChefNotificationRead).where(
            ChefNotificationRead.notification_id == notification_id,
            ChefNotificationRead.chef_id == current_chef_id
        )
    )
    if not existing.scalar_one_or_none():
        read_entry = ChefNotificationRead(
            notification_id=notification_id,
            chef_id=current_chef_id
        )
        db.add(read_entry)

    # Also update old is_read flag for compatibility
    notification.is_read = True

    await db.commit()
    return {"message": "Notification marked as read"}
# ---------------------------------------------------------
# MARK ALL READ
# ---------------------------------------------------------
async def mark_all_read(
    db: AsyncSession,
    restaurant_id: int,
    current_chef_id: int,
    current_restaurant_id: int
):

    if restaurant_id != current_restaurant_id:
        raise HTTPException(403, "Not allowed")

    stmt = (
        update(ChefNotification)
        .where(ChefNotification.restaurant_id == restaurant_id)
        .where(
            (ChefNotification.chef_id == current_chef_id) |
            (ChefNotification.chef_id.is_(None))
        )
        .values(is_read=True)
    )

    await db.execute(stmt)
    await db.commit()

    return {"message": "All relevant notifications marked read"}


# ---------------------------------------------------------
# CREATE GLOBAL NOTIFICATION
# ---------------------------------------------------------
async def create_global_notification_service(
    db: AsyncSession, restaurant_id: int, payload: GlobalNotificationCreate
):
    notification = ChefNotification(
        restaurant_id=restaurant_id,
        chef_id=None,
        title=payload.title,
        message=payload.message
    )

    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


# ---------------------------------------------------------
# CREATE CHEF-SPECIFIC NOTIFICATION
# ---------------------------------------------------------
async def create_chef_notification_service(
    db: AsyncSession, restaurant_id: int, payload: ChefNotificationCreate
):
    notification = ChefNotification(
        restaurant_id=restaurant_id,
        chef_id=payload.chef_id,
        title=payload.title,
        message=payload.message
    )

    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification
