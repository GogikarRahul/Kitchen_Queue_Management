from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base

class Chef(Base):
    __tablename__ = "chefs"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)

    name = Column(String, nullable=False)

    phone_number = Column(String, unique=True, nullable=False)   # FIXED
    password = Column(String, nullable=False)

    status = Column(                                      # ✅ REQUIRED FIELD
        Enum("active", "inactive", name="chef_status_enum"),
        nullable=False,
        default="active",
    )

    restaurant = relationship("Restaurant", back_populates="chefs")

    assigned_orders = relationship(
        "Order",
        back_populates="assigned_chef",
        lazy="selectin"
    )
