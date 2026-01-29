from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database.db import get_db
from app.database.models import MarketPrice
from app.schemas.market_price import PriceTrendResponse, PricePoint

router = APIRouter()

@router.get("/price-trend", response_model=PriceTrendResponse)
def get_price_trend(
    product_name: str = Query(...),
    location: str = Query(...),
    days: int = Query(30),
    db: Session = Depends(get_db)
):
    start_date = datetime.today().date() - timedelta(days=days)

    records = (
        db.query(MarketPrice)
        .filter(
            MarketPrice.product_name == product_name.lower(),
            MarketPrice.location == location.lower(),
            MarketPrice.created_at >= start_date
        )
        .order_by(MarketPrice.date.asc())
        .all()
    )

    points = [
        PricePoint(price=r.price_per_unit, recorded_at=r.date)
        for r in records
    ]


    return PriceTrendResponse(
        product_name=product_name,
        location=location,
        points=points
    )
