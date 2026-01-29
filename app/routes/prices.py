from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import MarketPrice
from app.schemas.market_price import MarketPriceCreate, MarketPriceResponse,PriceEstimateResponse,NegotiationRequest, NegotiationResponse,PriceAlertResponse
from app.schemas.market_price import PriceTrendResponse, PricePoint
from app.ml.predict import predict_next_price
from app.schemas.market_price import ProfitRequest, ProfitResponse
from sqlalchemy import func
from fastapi import HTTPException
import csv
from fastapi.responses import StreamingResponse
from io import StringIO

import time

CACHE = {}
CACHE_TTL = 300  # seconds (5 minutes)
router = APIRouter()

#MARKET PRICE
@router.post("/market-prices/", response_model=MarketPriceResponse)
def create_market_price(
    data: MarketPriceCreate,
    db: Session = Depends(get_db)
):
    new_price = MarketPrice(**data.dict())
    db.add(new_price)
    db.commit()
    db.refresh(new_price)
    return new_price

#ESTIMATE
@router.get("/estimate/{product_name}", response_model=PriceEstimateResponse)
def estimate_price(product_name: str, location: str, db: Session = Depends(get_db)):
    cache_key = f"{product_name.lower()}_{location.lower()}"

    # ⚡ Return cached result if valid
    if cache_key in CACHE:
        data, timestamp = CACHE[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return data
    prices = (
        db.query(MarketPrice.price_per_unit)
        .filter(
            MarketPrice.product_name.ilike(f"%{product_name.lower()}%"),
            MarketPrice.location.ilike(f"%{location.lower()}%")
        )
        .order_by(MarketPrice.created_at.desc())
        .limit(20)
        .all()
    )

    if not prices:
        return {
            "product_name": product_name,
            "location": location,
            "average_price": 0,
            "min_price": 0,
            "max_price": 0,
            "suggested_price": 0,
            "data_points": 0
        }

    price_list = [p[0] for p in prices]

    avg_price = sum(price_list) / len(price_list)
    min_price = min(price_list)
    max_price = max(price_list)

    # Simple intelligence: suggest slightly below average for negotiation
    suggested_price = round(avg_price * 0.97, 2)

    result = {
        "product_name": product_name,
        "location": location,

        "average_price_qtl": round(avg_price, 2),
        "average_price_kg": round(avg_price / 100, 2),

        "min_price_qtl": min_price,
        "min_price_kg": round(min_price / 100, 2),

        "max_price_qtl": max_price,
        "max_price_kg": round(max_price / 100, 2),

        "suggested_price_kg": round(suggested_price / 100, 2),

        "data_points": len(price_list)
    }

    CACHE[cache_key] = (result, time.time())

    return result


#NEGOTIATE
@router.post("/negotiate", response_model=NegotiationResponse)
def negotiate_price(data: NegotiationRequest, db: Session = Depends(get_db)):

    prices = (
        db.query(MarketPrice.price_per_unit)
        .filter(
            MarketPrice.product_name.ilike(f"%{data.product_name.lower()}%"),
            MarketPrice.location.ilike(f"%{data.location.lower()}%")
        )
        .order_by(MarketPrice.created_at.desc())
        .limit(20)
        .all()
    )

    if not prices:
        return {
            "market_average": 0,
            "offered_price": data.offered_price,
            "difference_percent": 0,
            "advice": "Not enough market data to give advice.",
            "suggested_counter_price": 0
        }

    price_list = [p[0] for p in prices]
    avg_price = sum(price_list) / len(price_list)

    difference_percent = ((data.offered_price - avg_price) / avg_price) * 100

    if difference_percent > 10:
        advice = "This offer is too high. You should negotiate strongly."
        counter_price = round(avg_price * 0.97, 2)
    elif difference_percent > 3:
        advice = "This offer is slightly high. Try negotiating a bit."
        counter_price = round(avg_price * 0.98, 2)
    elif difference_percent < -5:
        advice = "Great deal! This price is below market average."
        counter_price = data.offered_price
    else:
        advice = "This is a fair market price."
        counter_price = round(avg_price, 2)

    return {
        "market_average": round(avg_price, 2),
        "offered_price": data.offered_price,
        "difference_percent": round(difference_percent, 2),
        "advice": advice,
        "suggested_counter_price": counter_price
    }

@router.get("/trend/{product_name}", response_model=PriceTrendResponse)
def price_trend(
    product_name: str,
    location: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    # Safety limit to prevent huge queries
    limit = min(limit, 200)

    records = (
        db.query(MarketPrice.price_per_unit, MarketPrice.created_at)
        .filter(
            MarketPrice.product_name.ilike(f"%{product_name.lower()}%"),
            MarketPrice.location.ilike(f"%{location.lower()}%")
        )
        .order_by(MarketPrice.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    points = [
        {"price": r[0], "recorded_at": r[1]}
        for r in records
    ]

    return {
        "product_name": product_name,
        "location": location,
        "points": points
    }


#PRISE DROP ALART
@router.get("/alerts/{product_name}", response_model=PriceAlertResponse)
def price_drop_alert(product_name: str, location: str, db: Session = Depends(get_db)):

    records = (
        db.query(MarketPrice.price_per_unit)
        .filter(
            MarketPrice.product_name.ilike(f"%{product_name.lower()}%"),
            MarketPrice.location.ilike(f"%{location.lower()}%")

        )
        .order_by(MarketPrice.created_at.desc())
        .limit(10)
        .all()
    )

    if len(records) < 2:
        return {
            "product_name": product_name,
            "location": location,
            "latest_price": 0,
            "recent_average": 0,
            "drop_percent": 0,
            "alert": False,
            "message": "Not enough data to determine price trend."
        }

    prices = [r[0] for r in records]
    latest_price = prices[0]
    recent_average = sum(prices[1:]) / (len(prices) - 1)

    drop_percent = ((recent_average - latest_price) / recent_average) * 100

    if drop_percent > 5:
        message = "Price dropped significantly. Good time to buy!"
        alert = True
    else:
        message = "No significant price drop detected."
        alert = False

    return {
        "product_name": product_name,
        "location": location,
        "latest_price": latest_price,
        "recent_average": round(recent_average, 2),
        "drop_percent": round(drop_percent, 2),
        "alert": alert,
        "message": message
    }

@router.get("/predict/{product_name}")
def predict_price(product_name: str, location: str, db: Session = Depends(get_db)):

    prices = (
        db.query(MarketPrice.price_per_unit)
        .filter(
            MarketPrice.product_name.ilike(f"%{product_name.lower()}%"),
            MarketPrice.location.ilike(f"%{location.lower()}%")
        )
        .order_by(MarketPrice.created_at.asc())
        .all()
    )

    if len(prices) < 5:
        return {"message": "Not enough data for prediction"}

    price_list = [p[0] for p in prices]

    predicted_price = predict_next_price(len(price_list))

    if predicted_price is None:
        return {
            "message": "Prediction model not trained yet. Collecting more data."
        }

    return {
        "product_name": product_name,
        "location": location,
        "predicted_price": round(predicted_price, 2)
    }

@router.post("/profit-estimate", response_model=ProfitResponse)
def calculate_profit(data: ProfitRequest, db: Session = Depends(get_db)):
    avg_price_qtl = (
        db.query(func.avg(MarketPrice.price_per_unit))
        .filter(
            MarketPrice.product_name == data.product_name.lower(),
            MarketPrice.location == data.location.lower()
        )
        .scalar()
    )

    if not avg_price_qtl:
        raise HTTPException(status_code=404, detail="No market data found")

    market_avg_per_kg = avg_price_qtl / 100
    suggested_price = market_avg_per_kg * 0.98

    expected_profit_per_kg = suggested_price - data.cost_price_per_kg
    total_expected_profit = expected_profit_per_kg * data.quantity_kg

    # 🧠 Risk Logic
    if expected_profit_per_kg < 0:
        risk = "HIGH"
        msg = "You are likely to incur a loss at this price."
    elif expected_profit_per_kg < market_avg_per_kg * 0.05:
        risk = "MEDIUM"
        msg = "Profit margin is very low. Consider negotiating a better price."
    else:
        risk = "LOW"
        msg = "Good profit margin based on current market conditions."

    return ProfitResponse(
        product_name=data.product_name,
        location=data.location,
        suggested_price_per_kg=round(suggested_price, 2),
        expected_profit_per_kg=round(expected_profit_per_kg, 2),
        total_expected_profit=round(total_expected_profit, 2),
        market_average_per_kg=round(market_avg_per_kg, 2),
        risk_level=risk,
        message=msg
    )

# 📊 DATA SUMMARY ENDPOINT
@router.get("/data-summary")
def data_summary(db: Session = Depends(get_db)):
    results = (
        db.query(
            MarketPrice.product_name,
            MarketPrice.location,
            func.count(MarketPrice.id).label("records")
        )
        .group_by(MarketPrice.product_name, MarketPrice.location)
        .order_by(func.count(MarketPrice.id).desc())
        .limit(10)
        .all()
    )

    return [
        {
            "product_name": r.product_name,
            "location": r.location,
            "records": r.records
        }
        for r in results
    ]
from datetime import datetime

@router.get("/data-freshness")
def data_freshness(db: Session = Depends(get_db)):
    latest = (
        db.query(MarketPrice.created_at)
        .order_by(MarketPrice.created_at.desc())
        .first()
    )

    if not latest:
        return {"status": "no data in database"}

    latest_time = latest[0]
    age_hours = (datetime.utcnow() - latest_time).total_seconds() / 3600

    return {
        "latest_record_time": latest_time,
        "data_age_hours": round(age_hours, 2),
        "status": "fresh" if age_hours < 24 else "stale"
    }
@router.get("/export")
def export_prices(product_name: str, location: str, db: Session = Depends(get_db)):

    records = (
        db.query(MarketPrice)
        .filter(
            MarketPrice.product_name.ilike(f"%{product_name.lower()}%"),
            MarketPrice.location.ilike(f"%{location.lower()}%")
        )
        .order_by(MarketPrice.created_at.asc())
        .all()
    )

    if not records:
        return {"message": "No data found"}

    output = StringIO()
    writer = csv.writer(output)

    # CSV Header
    writer.writerow(["Product", "Location", "Price per Quintal", "Date Recorded"])

    # Rows
    for r in records:
        writer.writerow([r.product_name, r.location, r.price_per_unit, r.created_at])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={product_name}_prices.csv"}
    )
