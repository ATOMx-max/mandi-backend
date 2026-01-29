from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database.db import get_db
from app.database.models import Purchase
from app.schemas.vendor import VendorDashboardResponse
from app.database.models import MarketPrice


router = APIRouter()

@router.get("/dashboard/{vendor_id}", response_model=VendorDashboardResponse)
def vendor_dashboard(vendor_id: int, db: Session = Depends(get_db)):

    purchases = db.query(Purchase).filter(Purchase.vendor_id == vendor_id)

    total_purchases = purchases.count()

    total_spent = db.query(
        func.sum(Purchase.quantity * Purchase.price_per_unit)
    ).filter(Purchase.vendor_id == vendor_id).scalar() or 0

    most_purchased = db.query(
        Purchase.product_name,
        func.sum(Purchase.quantity).label("total_qty")
    ).filter(
        Purchase.vendor_id == vendor_id
    ).group_by(
        Purchase.product_name
    ).order_by(
        func.sum(Purchase.quantity).desc()
    ).first()

    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    recent_purchases = db.query(Purchase).filter(
        Purchase.vendor_id == vendor_id,
        Purchase.created_at >= seven_days_ago
    ).count()

    return {
        "vendor_id": vendor_id,
        "total_purchases": total_purchases,
        "total_spent": round(total_spent, 2),
        "most_purchased_product": most_purchased[0] if most_purchased else None,
        "recent_purchases_7_days": recent_purchases
    }
@router.get("/dashboard/{vendor_id}", response_model=VendorDashboardResponse)
def vendor_dashboard(vendor_id: int, db: Session = Depends(get_db)):

    purchases_query = db.query(Purchase).filter(Purchase.vendor_id == vendor_id)
    purchases = purchases_query.all()

    total_purchases = len(purchases)

    total_spent = db.query(
        func.sum(Purchase.quantity * Purchase.price_per_unit)
    ).filter(Purchase.vendor_id == vendor_id).scalar() or 0

    most_purchased = db.query(
        Purchase.product_name,
        func.sum(Purchase.quantity).label("total_qty")
    ).filter(
        Purchase.vendor_id == vendor_id
    ).group_by(
        Purchase.product_name
    ).order_by(
        func.sum(Purchase.quantity).desc()
    ).first()

    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    recent_purchases = db.query(Purchase).filter(
        Purchase.vendor_id == vendor_id,
        Purchase.created_at >= seven_days_ago
    ).count()

    # 📈 Profit analysis
    avg_purchase_price = None
    avg_market_price = None
    overall_savings_percent = None

    if purchases:
        avg_purchase_price = sum(p.price_per_unit for p in purchases) / len(purchases)

        market_prices = (
            db.query(MarketPrice.price_per_unit)
            .order_by(MarketPrice.created_at.desc())
            .limit(50)
            .all()
        )

        if market_prices:
            avg_market_price = sum(m[0] for m in market_prices) / len(market_prices)
            overall_savings_percent = ((avg_market_price - avg_purchase_price) / avg_market_price) * 100

    return {
        "vendor_id": vendor_id,
        "total_purchases": total_purchases,
        "total_spent": round(total_spent, 2),
        "most_purchased_product": most_purchased[0] if most_purchased else None,
        "recent_purchases_7_days": recent_purchases,
        "avg_purchase_price": round(avg_purchase_price, 2) if avg_purchase_price else None,
        "avg_market_price": round(avg_market_price, 2) if avg_market_price else None,
        "overall_savings_percent": round(overall_savings_percent, 2) if overall_savings_percent else None
    }
