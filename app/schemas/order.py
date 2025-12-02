from typing import Annotated, Optional, List
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, PositiveInt

from app.models.order import OrderStatus   # keep your DB Enum


# -----------------------------------------
# ORDER MODE ENUM
# -----------------------------------------

class OrderMode(str, Enum):
    dine_in = "dinein"
    delivery = "delivery"
    pickup = "pickup"


# -----------------------------------------
# PRIORITY ENUM
# -----------------------------------------

class OrderPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


# -----------------------------------------
# ORDER ITEM (CUSTOMER INPUT)
# -----------------------------------------

class OrderItemBase(BaseModel):
    item_id: int
    quantity: PositiveInt   # quantity must be > 0


# -----------------------------------------
# ORDER ITEM RESPONSE
# -----------------------------------------

class OrderItemResponse(BaseModel):
    id: int
    item_id: int
    quantity: int
    price: int   # SQL model uses INTEGER → stays int

    class Config:
        from_attributes = True


# -----------------------------------------
# ORDER CREATE (CUSTOMER)
# -----------------------------------------

class OrderCreate(BaseModel):
    restaurant_id: int
    items: List[OrderItemBase]
    customer_name: Optional[str] = None
    mode: OrderMode
    table_number: Optional[int] = Field(None, ge=1)   # must be positive if provided

    @field_validator("customer_name")
    def validate_customer_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Customer name cannot be empty or whitespace")
        return v


# -----------------------------------------
# FULL ORDER RESPONSE
# -----------------------------------------

class OrderResponse(BaseModel):
    id: int
    restaurant_id: int
    customer_name: Optional[str]
    mode: OrderMode
    table_number: Optional[int]
    status: OrderStatus
    priority: OrderPriority
    total_amount: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------
# CUSTOMER LIST ITEM
# -----------------------------------------

class CustomerOrderListItem(BaseModel):
    id: int
    status: OrderStatus
    total_price: int
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------
# STATUS UPDATE
# -----------------------------------------

class OrderStatusUpdate(BaseModel):
    new_status: OrderStatus


# -----------------------------------------
# CHEF ORDER SUMMARY
# -----------------------------------------

class OrderSummary(BaseModel):
    id: int
    status: OrderStatus
    total_price: int
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------
# CHEF ORDER STATS
# -----------------------------------------

class ChefOrderStats(BaseModel):
    pending: int
    accepted: int
    cooking: int
    ready: int
    completed: int
