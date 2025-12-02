# app/api/v1/endpoints/chef_orders.py

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import chef_required
from app.models.order import OrderStatus

from app.services.chef_order_services import (
    list_orders_for_kitchen,
    accept_order,
    start_cooking,
    mark_ready,
    complete_order,
    cancel_order,
    reject_order,
    assign_order,
    unassign_order,
    get_order_items_with_name

    
)

from app.schemas.chef import ChefNoteUpdate, ChefPriorityUpdate, ChefDelayUpdate

router = APIRouter(prefix="/chef", tags=["Chef - Orders"])


# ---------------------------------------------------------
# Helper – Enforce restaurant access
# ---------------------------------------------------------
def ensure_same_restaurant(current_chef, restaurant_id: int):
    if current_chef.restaurant_id != restaurant_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to manage orders for another restaurant."
        )


# ---------------------------------------------------------
# LIST ORDERS FOR RESTAURANT
# ---------------------------------------------------------

@router.get("/restaurants/{restaurant_id}/orders")
async def get_orders(
    restaurant_id: int,
    status: Optional[OrderStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    ensure_same_restaurant(current_chef, restaurant_id)
    return await list_orders_for_kitchen(db, restaurant_id, status, current_chef)


# ---------------------------------------------------------
# GET ORDER DETAILS
# ---------------------------------------------------------

@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    return await get_order_items_with_name(db, order_id, current_chef)

@router.get("/orders/{order_id}/items")
async def get_order_items(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    order = await get_order_items_with_name(db, order_id, current_chef)

    return order

# ---------------------------------------------------------
# STATUS TRANSITIONS
# ---------------------------------------------------------

@router.patch("/orders/{order_id}/accept")
async def accept(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    return await accept_order(db, order_id, current_chef)


@router.patch("/orders/{order_id}/start-cooking")
async def start_cook(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    return await start_cooking(db, order_id, current_chef)


@router.patch("/orders/{order_id}/mark-ready")
async def ready(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    return await mark_ready(db, order_id, current_chef)


@router.patch("/orders/{order_id}/complete")
async def complete(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    return await complete_order(db, order_id, current_chef)


@router.patch("/orders/{order_id}/cancel")
async def cancel(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    return await cancel_order(db, order_id, current_chef)


@router.patch("/orders/{order_id}/reject")
async def reject(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    return await reject_order(db, order_id, current_chef)


# ---------------------------------------------------------
# ASSIGNMENT
# ---------------------------------------------------------

@router.patch("/orders/{order_id}/assign")
async def assign(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    return await assign_order(db, order_id, current_chef)


@router.patch("/orders/{order_id}/unassign")
async def unassign(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_chef=Depends(chef_required),
):
    return await unassign_order(db, order_id, current_chef)


