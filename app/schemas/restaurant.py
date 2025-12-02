# app/schemas/restaurant.py

from typing import Optional, Annotated
from pydantic import BaseModel, StringConstraints, Field, field_validator


# -----------------------------------------
# STRING TYPES
# -----------------------------------------

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=150)]
AddressStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=300)]
PhoneStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=15)]


# -----------------------------------------
# BASE MODEL
# -----------------------------------------

class RestaurantBase(BaseModel):
    name: NameStr
    address: AddressStr
    phone: Optional[PhoneStr] = None

    @field_validator("phone")
    def validate_phone_digits(cls, v):
        if v is not None and not v.isdigit():
            raise ValueError("Phone number must contain digits only")
        return v


# -----------------------------------------
# CREATE MODEL
# -----------------------------------------

class RestaurantCreate(RestaurantBase):
    owner_id: int   # admin / owner user ID


# -----------------------------------------
# UPDATE MODEL
# -----------------------------------------

class RestaurantUpdate(BaseModel):
    name: Optional[NameStr] = None
    address: Optional[AddressStr] = None
    phone: Optional[PhoneStr] = None
    is_open: Optional[bool] = None

    @field_validator("phone")
    def validate_phone_digits(cls, v):
        if v is not None and not v.isdigit():
            raise ValueError("Phone number must contain digits only")
        return v


# -----------------------------------------
# RESPONSE MODEL
# -----------------------------------------

class RestaurantResponse(RestaurantBase):
    id: int
    is_open: bool

    class Config:
        from_attributes = True


# -----------------------------------------
# SETTINGS BASE
# -----------------------------------------

class RestaurantSettingsBase(BaseModel):
    auto_accept_orders: bool = False
    max_active_orders: int = Field(10, ge=1, le=200)  # must be between 1–200


# -----------------------------------------
# SETTINGS UPDATE
# -----------------------------------------

class RestaurantSettingsUpdate(BaseModel):
    auto_accept_orders: Optional[bool] = None
    max_active_orders: Optional[int] = Field(None, ge=1, le=200)


# -----------------------------------------
# SETTINGS RESPONSE
# -----------------------------------------

class RestaurantSettingsResponse(RestaurantSettingsBase):
    id: int
    restaurant_id: int

    class Config:
        from_attributes = True
