from typing import Optional, List, Annotated
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, StringConstraints, Field, field_validator


# -----------------------------------------
# ENUM
# -----------------------------------------
class FoodType(str, Enum):
    veg = "veg"
    nonveg = "nonveg"


# -----------------------------------------
# CATEGORY SCHEMAS
# -----------------------------------------

class MenuCategoryBase(BaseModel):
    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=150)
    ]

    @field_validator("name")
    def ensure_valid_name(cls, v: str):
        if not v.strip():
            raise ValueError("Category name cannot be empty or whitespace")
        return v


class MenuCategoryCreate(MenuCategoryBase):
    restaurant_id: int


class MenuCategoryUpdate(BaseModel):
    name: Optional[
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
    ] = None

    @field_validator("name")
    def ensure_valid_name(cls, v: Optional[str]):
        if v is not None and not v.strip():
            raise ValueError("Category name cannot be empty or whitespace")
        return v


class MenuCategoryResponse(MenuCategoryBase):
    id: int
    category_number: int 
    restaurant_id: int

    class Config:
        from_attributes = True


# -----------------------------------------
# MENU ITEM SCHEMAS
# -----------------------------------------

class MenuItemBase(BaseModel):
    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=150)
    ]

    description: Optional[
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
    ] = None

    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)

    food_type: FoodType

    @field_validator("name")
    def validate_item_name(cls, v: str):
        if not v.strip():
            raise ValueError("Item name cannot be empty or whitespace")
        return v


class MenuItemCreate(MenuItemBase):
    category_id: int


class MenuItemUpdate(BaseModel):
    name: Optional[
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
    ] = None

    description: Optional[
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
    ] = None

    price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)

    food_type: Optional[FoodType] = None

    @field_validator("name")
    def validate_name(cls, v: Optional[str]):
        if v is not None and not v.strip():
            raise ValueError("Item name cannot be empty or whitespace")
        return v


class MenuItemResponse(MenuItemBase):
    id: int
    category_id: int

    class Config:
        from_attributes = True


# -----------------------------------------
# AVAILABILITY SCHEMA
# -----------------------------------------

class AvailabilityUpdate(BaseModel):
    is_available: bool


# -----------------------------------------
# SEARCH ITEM RESULT SCHEMA
# -----------------------------------------

class MenuItemWithRestaurant(BaseModel):
    id: int
    name: str
    price: float
    description: str | None

    restaurant_name: str
    restaurant_location: str

    class Config:
        from_attributes = True

