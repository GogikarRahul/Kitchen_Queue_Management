from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import chef_required
from app.schemas.activity_log import ChefActivityLogOut
from app.services.activity_log_service import (
    get_activity_logs_for_restaurant,
    get_activity_logs_for_order,
)

router = APIRouter(prefix="/chef", tags=["Chef - Activity Logs"])


@router.get("/restaurants/{restaurant_id}/activity-logs", response_model=list[ChefActivityLogOut])
async def restaurant_logs(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    return await get_activity_logs_for_restaurant(db, restaurant_id)


@router.get("/orders/{order_id}/activity-logs", response_model=list[ChefActivityLogOut])
async def order_logs(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    return await get_activity_logs_for_order(db, order_id)
