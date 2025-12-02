from datetime import datetime
from typing import Optional, Iterable

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.order import Order, OrderStatus, OrderPriority,OrderItem
from app.models.menu import MenuItem
from app.models.chef import Chef
from app.models.chef_activity import ChefActivityLog
from app.schemas.chef import ChefNoteUpdate, ChefPriorityUpdate, ChefDelayUpdate


async def get_order_items_with_name(db: AsyncSession, order_id: int,chef:Chef):
    stmt = (
        select(
            OrderItem.id,
            OrderItem.menu_item_id,
            MenuItem.name.label("item_name"),
            OrderItem.quantity,
            OrderItem.unit_price,
            OrderItem.total_price,
            OrderItem.food_type,
        )
        .join(MenuItem, MenuItem.id == OrderItem.menu_item_id)
        .where(OrderItem.order_id == order_id)
    )

    result = await db.execute(stmt)
    return result.mappings().all()


# ---------------------------------------------------
# Internal helper: ensure status before action
# ---------------------------------------------------
def _ensure_status(
    order: Order,
    allowed_statuses: Iterable[OrderStatus],
    action_name: str,
) -> None:
    """
    Ensures the current order.status is within allowed_statuses.
    Raises HTTP 400 if not.

    Example:
    - Only pending orders can be accepted.
    """
    if order.status not in allowed_statuses:
        allowed_str = ", ".join(s.value for s in allowed_statuses)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order must be in one of [{allowed_str}] to {action_name}. "
                   f"Current status: {order.status.value}",
        )


# ---------------------------------------------------
# Internal helper: set status & timestamps
# ---------------------------------------------------
def _set_status_fields(order: Order, new_status: OrderStatus) -> None:
    """
    Updates the order status and the appropriate timestamp field.
    Corner cases:
    - Repeated transitions will overwrite timestamps (by design).
    """
    now = datetime.now()

    if new_status == OrderStatus.accepted:
        order.accepted_at = now
    elif new_status == OrderStatus.cooking:
        order.cooking_at = now
    elif new_status == OrderStatus.ready:
        order.ready_at = now
    elif new_status == OrderStatus.completed:
        order.completed_at = now

    order.status = new_status


# ---------------------------------------------------
# Internal helper: log chef actions
# ---------------------------------------------------
async def _log_action(
    db: AsyncSession,
    order: Order,
    chef: Chef,
    action: str,
    details: Optional[str] = None,
) -> None:
    """
    Logs an action performed by a chef on an order.
    Corner cases:
    - If logging fails due to DB constraints, caller may need try/except
      if you want to ignore log failures.
    """
    db.add(
        ChefActivityLog(
            restaurant_id=order.restaurant_id,
            chef_id=chef.id,
            order_id=order.id,
            action=action,
            details=details,
        )
    )
    await db.flush()  # stays within transaction


# ---------------------------------------------------
# Internal helper: change status & log, then assign chef
# ---------------------------------------------------
async def _change_status_and_log(
    db: AsyncSession,
    order: Order,
    chef: Chef,
    new_status: OrderStatus,
    action: str,
    details: Optional[str] = None,
) -> Order:
    """
    Applies a status change, assigns the chef, logs the action, commits, and refreshes.
    """
    _set_status_fields(order, new_status)
    order.chef_id = chef.id  # track which chef handled this step

    await _log_action(db, order, chef, action, details)
    await db.commit()
    await db.refresh(order)
    return order


# ---------------------------------------------------
# LIST ORDERS FOR KITCHEN
# ---------------------------------------------------
async def list_orders_for_kitchen(
    db: AsyncSession,
    restaurant_id: int,
    status_filter: Optional[OrderStatus],
    current_chef: Chef,
):
    """
    Lists orders for a particular restaurant, optionally filtered by status.

    Corner cases:
    - Chef belongs to another restaurant -> 403
    - status_filter is None -> return all statuses
    - Empty result -> returns [] (no error)
    """
    if current_chef.restaurant_id != restaurant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this restaurant")

    query = select(Order).where(Order.restaurant_id == restaurant_id)

    if status_filter:
        query = query.where(Order.status == status_filter)

    # Higher priority first, then earliest created
    query = query.order_by(Order.priority.desc(), Order.created_at.asc())

    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------
# ACCEPT ORDER
# ---------------------------------------------------
async def accept_order(db: AsyncSession, order_id: int, current_chef: Chef) -> Order:
    """
    Accept a pending order.
    Only orders in 'pending' can be accepted.
    """
    order = await get_order_items_with_name(db, order_id, current_chef)
    _ensure_status(order, [OrderStatus.pending], "accept")

    return await _change_status_and_log(
        db, order, current_chef, OrderStatus.accepted, "accept"
    )


# ---------------------------------------------------
# START COOKING
# ---------------------------------------------------
async def start_cooking(db: AsyncSession, order_id: int, current_chef: Chef) -> Order:
    """
    Move order from 'accepted' to 'cooking'.
    """
    order = await get_order_items_with_name(db, order_id, current_chef)
    _ensure_status(order, [OrderStatus.accepted], "start cooking")

    return await _change_status_and_log(
        db, order, current_chef, OrderStatus.cooking, "start_cooking"
    )


# ---------------------------------------------------
# MARK READY
# ---------------------------------------------------
async def mark_ready(db: AsyncSession, order_id: int, current_chef: Chef) -> Order:
    """
    Move order from 'cooking' to 'ready'.
    """
    order = await get_order_items_with_name(db, order_id, current_chef)
    _ensure_status(order, [OrderStatus.cooking], "mark ready")

    return await _change_status_and_log(
        db, order, current_chef, OrderStatus.ready, "mark_ready"
    )


# ---------------------------------------------------
# COMPLETE ORDER
# ---------------------------------------------------
async def complete_order(db: AsyncSession, order_id: int, current_chef: Chef) -> Order:
    """
    Move order from 'ready' to 'completed'.
    """
    order = await get_order_items_with_name(db, order_id, current_chef)
    _ensure_status(order, [OrderStatus.ready], "complete")

    return await _change_status_and_log(
        db, order, current_chef, OrderStatus.completed, "complete"
    )


# ---------------------------------------------------
# CANCEL ORDER
# ---------------------------------------------------
async def cancel_order(db: AsyncSession, order_id: int, current_chef: Chef) -> Order:
    """
    Cancel an order that is not already completed, canceled, or rejected.

    NOTE: You may want stricter rules:
    - e.g. only allow cancelling 'pending' or 'accepted' orders.
    """
    order = await get_order_items_with_name(db, order_id, current_chef)

    if order.status in [OrderStatus.completed, OrderStatus.canceled, OrderStatus.rejected]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel an order that is completed, canceled, or rejected",
        )

    order.status = OrderStatus.canceled
    await _log_action(db, order, current_chef, "cancel")

    await db.commit()
    await db.refresh(order)
    return order


# ---------------------------------------------------
# REJECT ORDER
# ---------------------------------------------------
async def reject_order(db: AsyncSession, order_id: int, current_chef: Chef) -> Order:
    """
    Reject an order only when it is in 'pending' state.
    """
    order = await get_order_items_with_name(db, order_id, current_chef)
    _ensure_status(order, [OrderStatus.pending], "reject")

    order.status = OrderStatus.rejected
    await _log_action(db, order, current_chef, "reject")

    await db.commit()
    await db.refresh(order)
    return order



async def assign_order(db: AsyncSession, order_id: int, current_chef: Chef):

    order = await get_order_items_with_name(db, order_id, current_chef)

    if order.assigned_chef_id and order.assigned_chef_id != current_chef.id:
        raise HTTPException(400, "Order already assigned to another chef")

    order.assigned_chef_id = current_chef.id

    await db.commit()
    await db.refresh(order)

    return order


async def unassign_order(db: AsyncSession, order_id: int, current_chef: Chef):

    order = await get_order_items_with_name(db, order_id, current_chef)

    if order.assigned_chef_id != current_chef.id:
        raise HTTPException(403, "You are not assigned to this order")

    order.assigned_chef_id = None

    await db.commit()
    await db.refresh(order)

    return order
