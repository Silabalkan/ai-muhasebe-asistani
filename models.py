from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime
from db import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)

    total_amount = Column(Float, nullable=True)
    payment_type = Column(String(20), nullable=True)   # "Nakit", "Kredi Kartı", ...
    kdv_rate = Column(Integer, nullable=True)          # 8, 18, ...
    category = Column(String(20), nullable=True)       # "Gelir", "Gider", ...

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
