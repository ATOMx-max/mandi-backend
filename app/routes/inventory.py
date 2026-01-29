from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import Inventory
from app.schemas.inventory import InventoryItem
from pydantic import BaseModel
from typing import List
router = APIRouter()


class LowStockItem(BaseModel):
    product_name: str
    quantity_available: float
    minimum_threshold: float
    shortage: float

@router.get("/alerts/{vendor_id}", response_model=List[LowStockItem])
def low_stock_alerts(vendor_id: int, db: Session = Depends(get_db)):

    items = db.query(Inventory).filter(Inventory.vendor_id == vendor_id).all()

    alerts = []

    for item in items:
        if item.quantity_available <= item.minimum_threshold:
            alerts.append({
                "product_name": item.product_name,
                "quantity_available": item.quantity_available,
                "minimum_threshold": item.minimum_threshold,
                "shortage": item.minimum_threshold - item.quantity_available
            })

    return alerts

@router.get("/{vendor_id}", response_model=list[InventoryItem])
def get_inventory(vendor_id: int, db: Session = Depends(get_db)):
    return db.query(Inventory).filter(Inventory.vendor_id == vendor_id).all()


