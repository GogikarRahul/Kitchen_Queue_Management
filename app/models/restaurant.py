from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    is_open = Column(Boolean, default=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    settings = relationship("RestaurantSettings", uselist=False, back_populates="restaurant")
    chefs = relationship("Chef", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant", cascade="all, delete-orphan")



class RestaurantSettings(Base):
    __tablename__ = "restaurant_settings"

    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))

    auto_accept_orders = Column(Boolean, default=False)
    max_active_orders = Column(Integer, default=10)

    restaurant = relationship("Restaurant", back_populates="settings")
