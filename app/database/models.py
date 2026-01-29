from sqlalchemy import Column, Integer, String, DateTime,Float
from sqlalchemy.sql import func
from datetime import datetime
from .db import Base



class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    city = Column(String(100))
    language = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(100), index=True, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    location = Column(String(100), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)

    # Link purchase to a vendor
    vendor_id = Column(Integer, nullable=False)  # later we can add ForeignKey

    product_name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    seller_name = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, nullable=False)
    product_name = Column(String(100), nullable=False)
    quantity_available = Column(Float, default=0)

    minimum_threshold = Column(Float, default=10)  # 🔔 Alert level

    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
