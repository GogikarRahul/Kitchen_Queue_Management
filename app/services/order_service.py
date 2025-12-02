# app/services/order_service.py

from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User
from app.utils.email_sender import send_email
from app.models.order import (
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
)
from app.models.menu import MenuItem,MenuCategory
from app.models.restaurant import Restaurant

from app.websocket.events import (
    push_new_order,
    push_status_update,
    push_order_canceled,
    push_order_delayed,
)


# ============================================================
# 🔐 VALIDATION HELPERS
# ============================================================

async def _validate_restaurant(db: AsyncSession, restaurant_id: int):
    """Ensure restaurant exists."""
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(404, "Restaurant not found")
    return restaurant


async def _validate_order_belongs_to_restaurant(order: Order, restaurant_id: int):
    if order.restaurant_id != restaurant_id:
        raise HTTPException(403, "Not allowed: order belongs to another restaurant")


# ============================================================
# 🔥 CUSTOMER CREATES ORDER
# ============================================================
async def create_customer_order(
    db: AsyncSession,
    payload,
    current_customer,
    background_tasks: BackgroundTasks,
):
    # ==============================================================
    # 1️⃣ RESTAURANT PRIORITY → ID > NAME
    # ==============================================================
    restaurant = None

    if payload.restaurant_id:  
        # ID has top priority
        restaurant = await _validate_restaurant(db, payload.restaurant_id)

    elif payload.restaurant_name:  
        # Search by name only if ID not provided
        stmt = select(Restaurant).where(Restaurant.name.ilike(f"%{payload.restaurant_name}%"))
        res = await db.execute(stmt)
        restaurant = res.scalar_one_or_none()

        if not restaurant:
            return None, "Restaurant not found by name"

        payload.restaurant_id = restaurant.id  # assign ID internally

    else:
        return None, "You must provide restaurant_id or restaurant_name"

    # ==============================================================
    # 2️⃣ ITEMS VALIDATION
    # ==============================================================
    if not payload.items:
        return None, "Order must contain at least one item"

    # Extract IDs for fast lookup
    item_ids = [item.item_id for item in payload.items if item.item_id]

    # Fetch items by ID first
    stmt = select(MenuItem).where(MenuItem.id.in_(item_ids))
    result = await db.execute(stmt)
    menu_items = {m.id: m for m in result.scalars().all()}

    # ==============================================================
    # 3️⃣ ITEM PRIORITY → ID > NAME
    # ==============================================================
    for item in payload.items:

        # If item_id exists → use ID (highest priority)
        if item.item_id:
            if item.item_id not in menu_items:
                return None, f"Menu item {item.item_id} not found"
            continue

        # Else use item_name if provided
        if item.item_name:
            item_stmt = (
                select(MenuItem)
                .join(MenuCategory)
                .where(MenuItem.name.ilike(f"%{item.item_name}%"))
                .where(MenuCategory.restaurant_id == payload.restaurant_id)
            )
            item_res = await db.execute(item_stmt)
            found_item = item_res.scalar_one_or_none()

            if not found_item:
                return None, f"Menu item '{item.item_name}' not found in this restaurant"

            # Assign found ID so existing logic works
            item.item_id = found_item.id
            menu_items[found_item.id] = found_item

        else:
            return None, "Each item must include item_id or item_name"

    # ==================================================================
    # 4️⃣ EXISTING ORDER CREATION LOGIC (UNCHANGED)
    # ==================================================================

    order_items = []
    total_amount = Decimal("0.00")

    for item in payload.items:
        menu = menu_items.get(item.item_id)
        price = Decimal(str(menu.price))
        line_total = price * item.quantity
        total_amount += line_total

        order_items.append(
            OrderItem(
                menu_item_id=menu.id,
                quantity=item.quantity,
                unit_price=price,
                total_price=line_total,
                food_type=menu.food_type,
            )
        )

    now = datetime.now()
    order = Order(
        restaurant_id=payload.restaurant_id,
        customer_name=current_customer.name,
        mode=payload.mode,
        table_number=payload.table_number,
        status=OrderStatus.pending,
        total_amount=total_amount,
        created_at=now,
        updated_at=now,
    )

    for oi in order_items:
        order.items.append(oi)

    db.add(order)
    await db.flush()

    # Save history
    db.add(
        OrderStatusHistory(
            order_id=order.id,
            previous_status=None,
            new_status=OrderStatus.pending,
            timestamp=now,
            changed_by_chef_id=None,
        )
    )

    await db.commit()
    await db.refresh(order)

    # Send WebSocket push
    await push_new_order(order)

    # ==========================================================
    # 📩 EMAILS (same as before)
    # ==========================================================

    owner_res = await db.execute(select(User).where(User.id == restaurant.owner_id))
    owner = owner_res.scalar_one_or_none()

    if current_customer.email:
        background_tasks.add_task(
            send_email,
            subject="Order Placed Successfully 🎉",
            recipients=[current_customer.email],
            body=f"""
                <h3>Hello {current_customer.name},</h3>
                <p>Your order <b>#{order.id}</b> has been placed successfully!</p>
                <p>Total Amount: <b>{order.total_amount}</b></p>
                <p>Thank you for using our service! 🍽</p>
            """
        )

    if owner and owner.email:
        background_tasks.add_task(
            send_email,
            subject="New Order Received 🍽",
            recipients=[owner.email],
            body=f"""
                <h3>Hello {owner.name},</h3>
                <p>You have received a new order.</p>
                <p>Order ID: <b>{order.id}</b></p>
                <p>Customer Name: <b>{current_customer.name}</b></p>
                <p>Total Amount: <b>{order.total_amount}</b></p>
                <p>Please take action in your dashboard.</p>
            """
        )

    return order, None


# ============================================================
# 🔥 LIST CUSTOMER ORDERS (secure version)
# ============================================================
async def list_customer_orders(db: AsyncSession, customer_name: str):
    stmt = (
        select(Order)
        .where(Order.customer_name == customer_name)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )

    result = await db.execute(stmt)
    return result.scalars().all()


# ============================================================
# 🔥 GET CUSTOMER ORDER (secure)
# ============================================================

async def get_customer_order(db: AsyncSession, customer_name: str, order_id: int):
    stmt = (
        select(Order)
        .where(
            Order.id == order_id,
            Order.customer_name == customer_name  # FIXED
        )
        .options(selectinload(Order.items))
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ============================================================
# 🔥 CHEF GET ORDERS FOR RESTAURANT
# ============================================================

async def get_orders_for_restaurant(
    db: AsyncSession,
    restaurant_id: int,
    status: Optional[OrderStatus],
    current_chef,
):
    if current_chef.restaurant_id != restaurant_id:
        raise HTTPException(403, "Not allowed")

    stmt = select(Order).where(Order.restaurant_id == restaurant_id)

    if status:
        stmt = stmt.where(Order.status == status)

    stmt = stmt.order_by(Order.priority.desc(), Order.created_at.asc())
    result = await db.execute(stmt)

    return result.scalars().all()


# ============================================================
# 🔥 STATUS TRANSITION RULES
# ============================================================

ALLOWED_TRANSITIONS = {
    OrderStatus.pending: [OrderStatus.accepted, OrderStatus.canceled, OrderStatus.rejected],
    OrderStatus.accepted: [OrderStatus.cooking, OrderStatus.canceled],
    OrderStatus.cooking: [OrderStatus.ready, OrderStatus.canceled],
    OrderStatus.ready:   [OrderStatus.completed],
    OrderStatus.completed: [],
    OrderStatus.canceled: [],
    OrderStatus.rejected: [],
}

def can_transition(old: OrderStatus, new: OrderStatus):
    return new in ALLOWED_TRANSITIONS.get(old, [])


# ============================================================
# 🔥 CHANGE ORDER STATUS (secure, fixed version)
# ============================================================

async def change_status(
    db: AsyncSession,
    order_id: int,
    new_status: OrderStatus,
    current_chef,
):
    stmt = select(Order).where(Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(404, "Order not found")

    # Restaurant ownership check
    await _validate_order_belongs_to_restaurant(order, current_chef.restaurant_id)

    old_status = order.status

    if not can_transition(old_status, new_status):
        raise HTTPException(
            400,
            f"Cannot change status from {old_status.value} to {new_status.value}"
        )

    now = datetime.now()

    timestamp_map = {
        OrderStatus.accepted: "accepted_at",
        OrderStatus.cooking: "cooking_at",
        OrderStatus.ready: "ready_at",
        OrderStatus.completed: "completed_at",
    }

    if new_status in timestamp_map:
        setattr(order, timestamp_map[new_status], now)

    order.status = new_status
    order.assigned_chef_id = current_chef.id
    order.updated_at = now

    db.add(
        OrderStatusHistory(
            order_id=order.id,
            previous_status=old_status,
            new_status=new_status,
            timestamp=now,
            changed_by_chef_id=current_chef.id,
        )
    )

    await db.commit()
    await db.refresh(order)

    if new_status == OrderStatus.canceled:
        await push_order_canceled(order)
    else:
        await push_status_update(order)

    return order



async def cancel_order_by_customer(
    db: AsyncSession, order_id: int, current_customer
):
    # Fetch order belonging to this customer
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.customer_name == current_customer.name
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        return None, "Order not found"

    # Allowed cancellation states
    allowed = [OrderStatus.pending, OrderStatus.accepted]

    if order.status not in allowed:
        return None, f"Cannot cancel order in '{order.status}' state"

    # Update status
    order.status = OrderStatus.canceled
    order.updated_at = datetime.now()

    await db.commit()
    await db.refresh(order)

    return order, None
