# models.py
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String(32), nullable=False, default="personel", server_default="personel")
    
    # Relasyon
    invoices = relationship("Invoice", back_populates="user")
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    
    # Kullanıcı ilişkisi
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="invoices")

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
