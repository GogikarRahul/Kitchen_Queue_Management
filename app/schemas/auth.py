from typing import Annotated
from pydantic import BaseModel, EmailStr, StringConstraints, field_validator
from app.models.user import UserRole


# -----------------------------------------
# SIGNUP SCHEMA
# -----------------------------------------

class SignupSchema(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=6, max_length=100)]
    role: UserRole  # required for role guards

    @field_validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


# -----------------------------------------
# LOGIN SCHEMA
# -----------------------------------------

class LoginSchema(BaseModel):
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=1)]


# -----------------------------------------
# CHEF LOGIN SCHEMA
# -----------------------------------------

class ChefLoginRequest(BaseModel):
    phone: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=15)]
    password: Annotated[str, StringConstraints(min_length=1)]

    @field_validator("phone")
    def validate_phone(cls, v):
        if not v.isdigit():
            raise ValueError("Phone number must contain digits only")
        return v
