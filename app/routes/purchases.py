from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import Purchase,MarketPrice
from app.schemas.purchase import PurchaseCreate, PurchaseResponse,PurchaseAnalysisResponse, PurchaseAnalysisItem,SupplierRankingResponse, SupplierRankItem
from sqlalchemy import func
from app.database.models import Inventory


router = APIRouter()

# ➕ Add a new purchase
@router.post("/", response_model=PurchaseResponse)
def add_purchase(data: PurchaseCreate, db: Session = Depends(get_db)):
    new_purchase = Purchase(**data.dict())
    db.add(new_purchase)
    db.commit()
    db.refresh(new_purchase)
    return new_purchase


# 📜 Get all purchases of a vendor
@router.get("/vendor/{vendor_id}", response_model=list[PurchaseResponse])
def get_vendor_purchases(vendor_id: int, db: Session = Depends(get_db)):
    purchases = (
        db.query(Purchase)
        .filter(Purchase.vendor_id == vendor_id)
        .order_by(Purchase.created_at.desc())
        .all()
    )
    return purchases


@router.get("/analysis/{vendor_id}", response_model=PurchaseAnalysisResponse)
def purchase_analysis(vendor_id: int, db: Session = Depends(get_db)):

    purchases = db.query(Purchase).filter(Purchase.vendor_id == vendor_id).all()

    results = []

    for p in purchases:
        prices = (
            db.query(MarketPrice.price_per_unit)
            .filter(
                MarketPrice.product_name == p.product_name.lower()
            )
            .order_by(MarketPrice.created_at.desc())
            .limit(20)
            .all()
        )

        if not prices:
            continue

        market_avg = sum(price[0] for price in prices) / len(prices)
        diff_percent = ((p.price_per_unit - market_avg) / market_avg) * 100

        if diff_percent > 10:
            insight = "Bought much higher than market 😟"
        elif diff_percent > 3:
            insight = "Slightly above market price"
        elif diff_percent < -5:
            insight = "Great deal! Bought below market 💰"
        else:
            insight = "Bought at fair market price"

        results.append({
            "product_name": p.product_name,
            "purchase_price": p.price_per_unit,
            "market_average_price": round(market_avg, 2),
            "difference_percent": round(diff_percent, 2),
            "insight": insight
        })

    return {
        "vendor_id": vendor_id,
        "analysis": results
    }

@router.get("/suppliers/{vendor_id}", response_model=SupplierRankingResponse)
def supplier_ranking(vendor_id: int, db: Session = Depends(get_db)):

    suppliers = (
        db.query(
            Purchase.seller_name,
            func.avg(Purchase.price_per_unit).label("avg_price"),
            func.count(Purchase.id).label("total_purchases")
        )
        .filter(Purchase.vendor_id == vendor_id, Purchase.seller_name != None)
        .group_by(Purchase.seller_name)
        .all()
    )

    results = []

    for s in suppliers:
        avg_price = float(s.avg_price)
        total_purchases = s.total_purchases

        if avg_price <= 0:
            performance = "No data"
        elif total_purchases >= 5 and avg_price < 25:
            performance = "Best Supplier 🏆"
        elif avg_price < 28:
            performance = "Good Pricing 👍"
        else:
            performance = "Expensive ⚠️"

        results.append({
            "seller_name": s.seller_name,
            "avg_price": round(avg_price, 2),
            "total_purchases": total_purchases,
            "performance": performance
        })

    return {
        "vendor_id": vendor_id,
        "suppliers": sorted(results, key=lambda x: x["avg_price"])
    }
@router.post("/", response_model=PurchaseResponse)
def add_purchase(data: PurchaseCreate, db: Session = Depends(get_db)):

    new_purchase = Purchase(**data.dict())
    db.add(new_purchase)

    # 📦 Update Inventory
    inventory = db.query(Inventory).filter(
        Inventory.vendor_id == data.vendor_id,
        Inventory.product_name == data.product_name.lower()
    ).first()

    if inventory:
        inventory.quantity_available += data.quantity
    else:
        inventory = Inventory(
            vendor_id=data.vendor_id,
            product_name=data.product_name.lower(),
            quantity_available=data.quantity
        )
        db.add(inventory)

    db.commit()
    db.refresh(new_purchase)

    return new_purchase
