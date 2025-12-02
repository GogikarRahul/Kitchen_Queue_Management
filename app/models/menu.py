from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum





class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    category_number = Column(Integer, nullable=False) 
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    items = relationship("MenuItem", back_populates="category")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("menu_categories.id"))

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Integer, nullable=False)
    food_type = Column(
    Enum("veg", "nonveg", name="food_type"),
    nullable=False
              )

    is_available = Column(Boolean, default=True)
    
    category = relationship("MenuCategory", back_populates="items")
    order_items = relationship("OrderItem", back_populates="menu_item")
   
