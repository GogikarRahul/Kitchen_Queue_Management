# app/api/v1/endpoints/analytics.py

import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import admin_required
from app.models.restaurant import Restaurant

from app.schemas.analytics import (
    OrderCountAnalytics,
    VegVsNonVegAnalytics,
    PreparationTimeAnalytics,
    PeriodReport,
)

from app.services.analytics_service import (
    get_order_counts,
    get_veg_vs_nonveg,
    get_preparation_time_stats,
    get_period_report,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin - Analytics & Reports"],
)


# -----------------------------------------------------------
# Helper: Validate admin owns restaurant
# -----------------------------------------------------------

async def ensure_admin_owns_restaurant(
    db: AsyncSession,
    restaurant_id: int,
    admin_user
):
    result = await db.execute(
        select(Restaurant).where(Restaurant.id == restaurant_id)
    )
    restaurant = result.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(404, "Restaurant not found")

    if restaurant.owner_id != admin_user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not own this restaurant."
        )

    return restaurant


# -----------------------------------------------------------
# ORDER COUNT ANALYTICS
# -----------------------------------------------------------

@router.get("/restaurants/{restaurant_id}/analytics/orders/count",
            response_model=OrderCountAnalytics)
async def orders_count(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    await ensure_admin_owns_restaurant(db, restaurant_id, current_admin)
    return await get_order_counts(db, restaurant_id)


# -----------------------------------------------------------
# VEG VS NON-VEG ANALYTICS
# -----------------------------------------------------------

@router.get("/restaurants/{restaurant_id}/analytics/veg-vs-nonveg",
            response_model=VegVsNonVegAnalytics)
async def veg_vs_nonveg(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    await ensure_admin_owns_restaurant(db, restaurant_id, current_admin)
    return await get_veg_vs_nonveg(db, restaurant_id)


# -----------------------------------------------------------
# PREPARATION TIME ANALYTICS
# -----------------------------------------------------------

@router.get("/restaurants/{restaurant_id}/analytics/preparation-time",
            response_model=PreparationTimeAnalytics)
async def prep_time(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    await ensure_admin_owns_restaurant(db, restaurant_id, current_admin)
    return await get_preparation_time_stats(db, restaurant_id)


# -----------------------------------------------------------
# DAILY REPORT
# -----------------------------------------------------------

@router.get("/restaurants/{restaurant_id}/reports/daily",
            response_model=PeriodReport)
async def daily_report(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    await ensure_admin_owns_restaurant(db, restaurant_id, current_admin)
    return await get_period_report(db, restaurant_id, "daily")


# -----------------------------------------------------------
# WEEKLY REPORT
# -----------------------------------------------------------

@router.get("/restaurants/{restaurant_id}/reports/weekly",
            response_model=PeriodReport)
async def weekly_report(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    await ensure_admin_owns_restaurant(db, restaurant_id, current_admin)
    return await get_period_report(db, restaurant_id, "weekly")


# -----------------------------------------------------------
# MONTHLY REPORT
# -----------------------------------------------------------

@router.get("/restaurants/{restaurant_id}/reports/monthly",
            response_model=PeriodReport)
async def monthly_report(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    await ensure_admin_owns_restaurant(db, restaurant_id, current_admin)
    return await get_period_report(db, restaurant_id, "monthly")


# -----------------------------------------------------------
# DOWNLOAD REPORT (CSV)
# -----------------------------------------------------------

@router.get("/restaurants/{restaurant_id}/reports/{period}/download")
async def download_report_csv(
    restaurant_id: int,
    period: str,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    await ensure_admin_owns_restaurant(db, restaurant_id, current_admin)

    if period not in ("daily", "weekly", "monthly"):
        raise HTTPException(400, "Invalid report period")

    report = await get_period_report(db, restaurant_id, period)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "start_date",
        "end_date",
        "total_orders",
        "completed_orders",
        "canceled_orders",
        "pending_orders",
        "veg_orders",
        "non_veg_orders",
        "total_revenue",
        "veg_revenue",
        "non_veg_revenue",
        "avg_preparation_time_seconds",
    ])

    writer.writerow([
        report.start_date,
        report.end_date,
        report.total_orders,
        report.completed_orders,
        report.canceled_orders,
        report.pending_orders,
        report.veg_orders,
        report.non_veg_orders,
        report.total_revenue,
        report.veg_revenue,
        report.non_veg_revenue,
        report.avg_preparation_time_seconds,
    ])

    output.seek(0)

    filename = f"{period}_report_restaurant_{restaurant_id}.csv"

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
