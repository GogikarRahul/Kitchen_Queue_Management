from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.chef_activity import ChefActivityLog


async def get_activity_logs_for_restaurant(db: AsyncSession, restaurant_id: int):
    result = await db.execute(
        select(ChefActivityLog)
        .where(ChefActivityLog.restaurant_id == restaurant_id)
        .order_by(ChefActivityLog.created_at.desc())
    )
    return result.scalars().all()


async def get_activity_logs_for_order(db: AsyncSession, order_id: int):
    result = await db.execute(
        select(ChefActivityLog)
        .where(ChefActivityLog.order_id == order_id)
        .order_by(ChefActivityLog.created_at.desc())
    )
    return result.scalars().all()
