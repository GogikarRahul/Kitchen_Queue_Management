from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base


class ChefActivityLog(Base):
    __tablename__ = "chef_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    chef_id = Column(Integer, ForeignKey("chefs.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    action = Column(String, nullable=False)  # e.g. "accept", "start_cooking"
    details = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    chef = relationship("Chef")
    order = relationship("Order")
    restaurant = relationship("Restaurant")
