from sqlalchemy import Column, Integer, String, DateTime
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
