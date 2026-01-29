from pydantic import BaseModel

class VendorDashboardResponse(BaseModel):
    vendor_id: int
    total_purchases: int
    total_spent: float
    most_purchased_product: str | None
    recent_purchases_7_days: int
class VendorDashboardResponse(BaseModel):
    vendor_id: int
    total_purchases: int
    total_spent: float
    most_purchased_product: str | None
    recent_purchases_7_days: int

    avg_purchase_price: float | None
    avg_market_price: float | None
    overall_savings_percent: float | None
