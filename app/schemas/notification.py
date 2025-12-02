from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChefNotificationCreate(BaseModel):
    chef_id: int
    title: str
    message: str


class GlobalNotificationCreate(BaseModel):
    title: str
    message: str

class NotificationOut(BaseModel):
    id: int
    restaurant_id: int
    chef_id: Optional[int]
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True
