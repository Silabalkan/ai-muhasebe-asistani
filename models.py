# models.py
from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.sql import func
from db import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)
    raw_text = Column(String, nullable=False)

    total_amount = Column(Float, nullable=True)
    payment_type = Column(String, nullable=True)

    kdv_rate = Column(Float, nullable=True)
    kdv_amount = Column(Float, nullable=True)

    category = Column(String, nullable=False)  # Gelir / Gider
    invoice_date = Column(Date, nullable=True)
    vendor = Column(String, nullable=True)

    # 🔴 BURASI KRİTİK
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # ← OTOMATİK DOLDUR
        nullable=False
    )
