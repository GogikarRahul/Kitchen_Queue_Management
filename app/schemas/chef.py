from typing import Optional, Annotated
from pydantic import BaseModel, StringConstraints, field_validator, Field
from app.models.order import OrderPriority

# -----------------------------------------
# SHARED VALIDATION UTILITIES
# -----------------------------------------

PhoneStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=10, max_length=15)
]

NameStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=100)
]

PasswordStr = Annotated[
    str,
    StringConstraints(min_length=6, max_length=100)
]


# -----------------------------------------
# BASE CHEF SCHEMA
# -----------------------------------------

class ChefBase(BaseModel):
    name: NameStr
    phone_number: PhoneStr   # ✅ FIXED

    @field_validator("phone_number")
    def validate_phone_digits(cls, v):
        if not v.isdigit():
            raise ValueError("Phone number must contain digits only")
        return v


# -----------------------------------------
# CREATE CHEF
# -----------------------------------------

class ChefCreate(ChefBase):
    password: PasswordStr
    


# -----------------------------------------
# UPDATE CHEF
# -----------------------------------------

class ChefUpdate(BaseModel):
    name: Optional[NameStr] = None
    phone_number: Optional[PhoneStr] = None  # ✅ FIXED
    password: Optional[PasswordStr] = None
    status: Optional[str] = None

    @field_validator("phone_number")
    def validate_phone_digits(cls, v):
        if v is not None and not v.isdigit():
            raise ValueError("Phone number must contain digits only")
        return v


# -----------------------------------------
# RESPONSE MODEL
# -----------------------------------------

class ChefOut(ChefBase):
    id: int
    restaurant_id: int
    status: str

    class Config:
        from_attributes = True


# -----------------------------------------
# LOGIN
# -----------------------------------------

class ChefLogin(BaseModel):
    phone_number: PhoneStr   # ✅ FIXED
    password: PasswordStr

    @field_validator("phone_number")
    def validate_phone_digits(cls, v):
        if not v.isdigit():
            raise ValueError("Phone number must contain digits only")
        return v


# -----------------------------------------
# NOTE UPDATE
# -----------------------------------------

class ChefNoteUpdate(BaseModel):
    note: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]

    @field_validator("note")
    def validate_note(cls, v):
        if not v.strip():
            raise ValueError("Note cannot be empty or whitespace")
        return v


# -----------------------------------------
# PRIORITY UPDATE
# -----------------------------------------

class ChefPriorityUpdate(BaseModel):
    priority: OrderPriority


# -----------------------------------------
# DELAY REASON UPDATE
# -----------------------------------------

class ChefDelayUpdate(BaseModel):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=300)]

    @field_validator("reason")
    def validate_reason(cls, v):
        if not v.strip():
            raise ValueError("Reason cannot be empty or whitespace")
        return v
