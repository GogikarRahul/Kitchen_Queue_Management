from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base


class ChefNotification(Base):
    __tablename__ = "chef_notifications"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    chef_id = Column(Integer, ForeignKey("chefs.id"), nullable=True)  # optional
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    title = Column(String, nullable=False)
    message = Column(String, nullable=False)

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    chef = relationship("Chef")
    order = relationship("Order")
    restaurant = relationship("Restaurant")


class ChefNotificationRead(Base):
    __tablename__ = "chef_notification_reads"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("chef_notifications.id"), nullable=False)
    chef_id = Column(Integer, ForeignKey("chefs.id"), nullable=False)
    read_at = Column(DateTime, default=datetime.utcnow)

    notification = relationship("ChefNotification", backref="read_receipts")
    chef = relationship("Chef")