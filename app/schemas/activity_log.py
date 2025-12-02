from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChefActivityLogOut(BaseModel):
    id: int
    restaurant_id: int
    chef_id: Optional[int]
    order_id: Optional[int]
    action: str
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
