from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db.base import Base


class DailyAnalytics(Base):
    __tablename__ = "daily_analytics"

    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)

    # Date of the report
    report_date = Column(Date, nullable=False)

    # Orders
    total_orders = Column(Integer, default=0)
    completed_orders = Column(Integer, default=0)
    canceled_orders = Column(Integer, default=0)
    pending_orders = Column(Integer, default=0)

    # Veg vs Non-veg
    veg_orders = Column(Integer, default=0)
    non_veg_orders = Column(Integer, default=0)

    # Revenue
    total_revenue = Column(Float, default=0.0)
    veg_revenue = Column(Float, default=0.0)
    non_veg_revenue = Column(Float, default=0.0)

    # Preparation-time metrics (in minutes)
    avg_preparation_time = Column(Float, default=0.0)
    fastest_order_time = Column(Float, default=0.0)
    slowest_order_time = Column(Float, default=0.0)

    restaurant = relationship("Restaurant")


class MonthlyAnalytics(Base):
    __tablename__ = "monthly_analytics"

    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)

    # Month-year string: "2025-07"
    month = Column(String, nullable=False)

    # Totals
    total_orders = Column(Integer, default=0)
    completed_orders = Column(Integer, default=0)
    canceled_orders = Column(Integer, default=0)

    # Veg vs Non-veg
    veg_orders = Column(Integer, default=0)
    non_veg_orders = Column(Integer, default=0)

    # Revenue
    total_revenue = Column(Float, default=0.0)
    veg_revenue = Column(Float, default=0.0)
    non_veg_revenue = Column(Float, default=0.0)

    restaurant = relationship("Restaurant")

