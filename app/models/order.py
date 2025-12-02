from datetime import datetime
from decimal import Decimal
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Boolean,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


# ---------------- ENUMS ----------------

class OrderStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    cooking = "cooking"
    ready = "ready"
    completed = "completed"
    canceled = "canceled"
    rejected = "rejected"


class OrderMode(str, enum.Enum):
    dine_in = "dinein"
    delivery = "delivery"
    pickup = "pickup"


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    card = "card"
    upi = "upi"


class OrderPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


# ---------------- ORDER MODEL ----------------

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)

    customer_name = Column(String, nullable=True)

    mode = Column(
        SAEnum(OrderMode, name="order_mode_enum"),
        nullable=False,
    )

    table_number = Column(Integer, nullable=True)

    status = Column(
        SAEnum(OrderStatus, name="order_status_enum"),
        nullable=False,
        default=OrderStatus.pending,
    )

    priority = Column(
        SAEnum(OrderPriority, name="order_priority_enum"),
        nullable=False,
        default=OrderPriority.normal,
    )

    total_amount = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    created_at = Column(DateTime, default=datetime.now(), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now(), nullable=False)

    is_delayed = Column(Boolean, default=False)
    delay_reason = Column(String, nullable=True)

    chef_note = Column(String, nullable=True)

    accepted_at = Column(DateTime, nullable=True)
    cooking_at = Column(DateTime, nullable=True)
    ready_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # NEW FIXED FOREIGN KEY → VERY IMPORTANT
    assigned_chef_id = Column(Integer, ForeignKey("chefs.id"), nullable=True)

    # RELATIONSHIPS
    restaurant = relationship("Restaurant", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    assigned_chef_id = Column(Integer, ForeignKey("chefs.id"))
    assigned_chef = relationship("Chef", back_populates="assigned_orders")

    status_history = relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.timestamp.asc()",
    )

# ---------------- ORDER ITEM MODEL ----------------

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)

    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

    # Snapshot of food type at the time of order ("veg", "nonveg")
    food_type = Column(String, nullable=True)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")
   

# ---------------- ORDER STATUS HISTORY MODEL ----------------

class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    previous_status = Column(SAEnum(OrderStatus, name="order_status_enum"), nullable=True)
    new_status = Column(SAEnum(OrderStatus, name="order_status_enum"), nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    changed_by_chef_id = Column(Integer, ForeignKey("chefs.id"), nullable=True)

    order = relationship("Order", back_populates="status_history")
    changed_by_chef = relationship("Chef")
