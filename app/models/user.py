from sqlalchemy import Column, Integer, String, Boolean, Enum
from app.db.base import Base
import enum


class UserRole(enum.Enum):
    customer = "customer"
    admin = "admin"
    chef = "chef"
    


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False,default="Customer")
    is_active = Column(Boolean, default=True)
