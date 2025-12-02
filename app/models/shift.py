from sqlalchemy import Column, Integer, DateTime, ForeignKey
from datetime import datetime
from app.db.base import Base


class ChefShift(Base):
    __tablename__ = "chef_shifts"

    id = Column(Integer, primary_key=True)
    chef_id = Column(Integer, ForeignKey("users.id"))

    shift_start = Column(DateTime, default=datetime.utcnow)
    shift_end = Column(DateTime, nullable=True)
