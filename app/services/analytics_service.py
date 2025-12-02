from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.order import Order, OrderStatus
from app.models.order import OrderItem
from app.models.menu import MenuItem
from app.schemas.analytics import (
    OrderCountAnalytics,
    VegVsNonVegAnalytics,
    PreparationTimeAnalytics,
    PeriodReport,
)


async def get_order_counts(db: AsyncSession, restaurant_id: int) -> OrderCountAnalytics:
    result = await db.execute(
        select(Order.status, func.count())
        .where(Order.restaurant_id == restaurant_id)
        .group_by(Order.status)
    )
    counts = {row[0]: row[1] for row in result.all()}
    total = sum(counts.values())
    def c(s: OrderStatus): return counts.get(s, 0)

    return OrderCountAnalytics(
        total_orders=total,
        pending=c(OrderStatus.pending),
        accepted=c(OrderStatus.accepted),
        cooking=c(OrderStatus.cooking),
        ready=c(OrderStatus.ready),
        completed=c(OrderStatus.completed),
        canceled=c(OrderStatus.canceled),
        rejected=c(OrderStatus.rejected),
    )


async def get_veg_vs_nonveg(db: AsyncSession, restaurant_id: int) -> VegVsNonVegAnalytics:
    # join Order -> OrderItem -> MenuItem
    stmt = (
        select(MenuItem.food_type, func.count(), func.sum(OrderItem.total_price))
        .join(OrderItem, OrderItem.id == MenuItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.restaurant_id == restaurant_id)
        .group_by(MenuItem.food_type)
    )
    result = await db.execute(stmt)
    rows = result.all()

    veg_orders_count = non_veg_orders_count = 0
    veg_revenue = non_veg_revenue = 0

    for food_type, count, revenue in rows:
        revenue = revenue or 0
        if food_type == "veg":
            veg_orders_count += count
            veg_revenue += revenue
        else:
            non_veg_orders_count += count
            non_veg_revenue += revenue

    return VegVsNonVegAnalytics(
        veg_orders_count=veg_orders_count,
        non_veg_orders_count=non_veg_orders_count,
        veg_revenue=veg_revenue,
        non_veg_revenue=non_veg_revenue,
    )


async def get_preparation_time_stats(db: AsyncSession, restaurant_id: int) -> PreparationTimeAnalytics:
    # completed orders with accepted_at & completed_at
    stmt = (
        select(
            Order.id,
            func.extract("epoch", Order.completed_at - Order.accepted_at),
        )
        .where(
            Order.restaurant_id == restaurant_id,
            Order.status == OrderStatus.completed,
            Order.completed_at.isnot(None),
            Order.accepted_at.isnot(None),
        )
    )
    result = await db.execute(stmt)
    times = [row[1] for row in result.all() if row[1] is not None]

    if not times:
        return PreparationTimeAnalytics(
            avg_preparation_time_seconds=None,
            fastest_time_seconds=None,
            slowest_time_seconds=None,
            time_per_item={},
        )

    avg_time = sum(times) / len(times)
    fastest = min(times)
    slowest = max(times)

    # time per item (simple: average over all completed orders per item)
    stmt_items = (
        select(
            OrderItem.id,
            func.avg(func.extract("epoch", Order.completed_at - Order.accepted_at)),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.restaurant_id == restaurant_id,
            Order.status == OrderStatus.completed,
            Order.completed_at.isnot(None),
            Order.accepted_at.isnot(None),
        )
        .group_by(OrderItem.id)
    )
    result_items = await db.execute(stmt_items)
    time_per_item = {
        row[0]: float(row[1]) for row in result_items.all() if row[1] is not None
    }

    return PreparationTimeAnalytics(
        avg_preparation_time_seconds=float(avg_time),
        fastest_time_seconds=float(fastest),
        slowest_time_seconds=float(slowest),
        time_per_item=time_per_item,
    )


async def _period_bounds(period: str) -> tuple[datetime, datetime]:
    now = datetime.now()
    if period == "daily":
        start = datetime(now.year, now.month, now.day)
        end = start + timedelta(days=1)
    elif period == "weekly":
        start = now - timedelta(days=now.weekday())
        start = datetime(start.year, start.month, start.day)
        end = start + timedelta(days=7)
    elif period == "monthly":
        start = datetime(now.year, now.month, 1)
        if now.month == 12:
            end = datetime(now.year + 1, 1, 1)
        else:
            end = datetime(now.year, now.month + 1, 1)
    else:
        raise ValueError("Invalid period")
    return start, end


async def get_period_report(db: AsyncSession, restaurant_id: int, period: str) -> PeriodReport:
    start, end = await _period_bounds(period)

    stmt_orders = (
        select(Order)
        .where(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start,
            Order.created_at < end,
        )
    )
    result = await db.execute(stmt_orders)
    orders = result.scalars().all()

    total_orders = len(orders)
    completed_orders = sum(1 for o in orders if o.status == OrderStatus.completed)
    canceled_orders = sum(1 for o in orders if o.status == OrderStatus.canceled)
    pending_orders = sum(1 for o in orders if o.status == OrderStatus.pending)

    total_revenue = sum(o.total_amount for o in orders)

    # veg/nonveg stats
    stmt_items = (
        select(MenuItem.food_type, func.sum(OrderItem.total_price))
        .join(OrderItem, OrderItem.id == MenuItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start,
            Order.created_at < end,
        )
        .group_by(MenuItem.food_type)
    )
    result_items = await db.execute(stmt_items)
    veg_orders = non_veg_orders = 0
    veg_revenue = non_veg_revenue = 0

    for food_type, revenue in result_items.all():
        revenue = revenue or 0
        if food_type == "veg":
            veg_revenue += revenue
            veg_orders += 1
        else:
            non_veg_revenue += revenue
            non_veg_orders += 1

    # avg preparation time
    stmt_time = (
        select(
            func.avg(
                func.extract("epoch", Order.completed_at - Order.accepted_at)
            )
        )
        .where(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start,
            Order.created_at < end,
            Order.status == OrderStatus.completed,
            Order.completed_at.isnot(None),
            Order.accepted_at.isnot(None),
        )
    )
    avg_time_result = await db.execute(stmt_time)
    avg_time = avg_time_result.scalar_one_or_none()
    avg_time_f = float(avg_time) if avg_time is not None else None

    return PeriodReport(
        start_date=start,
        end_date=end,
        total_orders=total_orders,
        completed_orders=completed_orders,
        canceled_orders=canceled_orders,
        pending_orders=pending_orders,
        veg_orders=veg_orders,
        non_veg_orders=non_veg_orders,
        total_revenue=total_revenue,
        veg_revenue=veg_revenue,
        non_veg_revenue=non_veg_revenue,
        avg_preparation_time_seconds=avg_time_f,
    )
