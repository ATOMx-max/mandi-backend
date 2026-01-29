from pydantic import BaseModel
from datetime import datetime

class InventoryItem(BaseModel):
    product_name: str
    quantity_available: float
    minimum_threshold: float
    last_updated: datetime

    class Config:
        from_attributes = True
