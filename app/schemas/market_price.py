from pydantic import BaseModel
from datetime import datetime
from typing import List

class MarketPriceCreate(BaseModel):
    product_name: str
    price_per_unit: float
    location: str
    market_date: datetime   # 👈 add this


class MarketPriceResponse(MarketPriceCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PriceEstimateResponse(BaseModel):
    product_name: str
    location: str

    average_price_qtl: float
    average_price_kg: float

    min_price_qtl: float
    min_price_kg: float

    max_price_qtl: float
    max_price_kg: float

    suggested_price_kg: float

    data_points: int


class NegotiationRequest(BaseModel):
    product_name: str
    location: str
    offered_price: float

class NegotiationResponse(BaseModel):
    market_average: float
    offered_price: float
    difference_percent: float
    advice: str
    suggested_counter_price: float
    confidence: float  # 👈 add (0–1 AI confidence)

    


class PricePoint(BaseModel):
    price: float
    recorded_at: datetime


class PriceTrendResponse(BaseModel):
    product_name: str
    location: str
    points: List[PricePoint]

class PriceAlertResponse(BaseModel):
    product_name: str
    location: str
    latest_price: float
    recent_average: float
    drop_percent: float
    alert: bool
    message: str
class ProfitRequest(BaseModel):
    product_name: str
    location: str
    cost_price_per_kg: float
    quantity_kg: float
class ProfitResponse(BaseModel):
    product_name: str
    location: str

    suggested_price_per_kg: float
    expected_profit_per_kg: float
    total_expected_profit: float
    market_average_per_kg: float

    risk_level: str        # 🆕 LOW / MEDIUM / HIGH
    message: str           # 🆕 Advice for vendor
