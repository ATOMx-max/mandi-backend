from pydantic import BaseModel
from datetime import datetime
from typing import List

class PurchaseCreate(BaseModel):
    vendor_id: int
    product_name: str
    quantity: float
    price_per_unit: float
    seller_name: str | None = None


class PurchaseResponse(PurchaseCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
        
class PurchaseAnalysisItem(BaseModel):
    product_name: str
    purchase_price: float
    market_average_price: float
    difference_percent: float
    insight: str


class PurchaseAnalysisResponse(BaseModel):
    vendor_id: int
    analysis: List[PurchaseAnalysisItem]


class SupplierRankItem(BaseModel):
    seller_name: str
    avg_price: float
    total_purchases: int
    performance: str


class SupplierRankingResponse(BaseModel):
    vendor_id: int
    suppliers: List[SupplierRankItem]
