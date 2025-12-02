from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class OrderCountAnalytics(BaseModel):
    total_orders: int
    pending: int
    accepted: int
    cooking: int
    ready: int
    completed: int
    canceled: int
    rejected: int


class VegVsNonVegAnalytics(BaseModel):
    veg_orders_count: int
    non_veg_orders_count: int
    veg_revenue: int
    non_veg_revenue: int


class PreparationTimeAnalytics(BaseModel):
    avg_preparation_time_seconds: Optional[float]
    fastest_time_seconds: Optional[float]
    slowest_time_seconds: Optional[float]
    # time per item id → avg seconds
    time_per_item: Dict[int, float] = {}


class PeriodReport(BaseModel):
    start_date: datetime
    end_date: datetime

    total_orders: int
    completed_orders: int
    canceled_orders: int
    pending_orders: int

    veg_orders: int
    non_veg_orders: int

    total_revenue: int
    veg_revenue: int
    non_veg_revenue: int

    avg_preparation_time_seconds: Optional[float]
