from typing import Annotated
from pydantic import BaseModel, EmailStr, StringConstraints, field_validator
from app.models.user import UserRole


# -----------------------------------------
# TYPE ALIASES FOR CLEAN VALIDATION
# -----------------------------------------

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
PasswordStr = Annotated[str, StringConstraints(min_length=6, max_length=100)]


# -----------------------------------------
# BASE USER MODEL
# -----------------------------------------

class UserBase(BaseModel):
    name: NameStr
    email: EmailStr

    @field_validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v


# -----------------------------------------
# USER CREATE (Signup)
# -----------------------------------------

class UserCreate(UserBase):
    password: PasswordStr
    role: UserRole

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


# -----------------------------------------
# USER RESPONSE
# -----------------------------------------

class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True
