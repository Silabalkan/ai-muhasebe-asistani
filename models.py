# models.py
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime
from db import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    # Dosya bilgisi
    filename = Column(String, nullable=False)

    # OCR ham metin
    raw_text = Column(Text, nullable=False)

    # Analiz edilen alanlar
    total_amount = Column(Float, nullable=True)        # Toplam tutar
    payment_type = Column(String(20), nullable=True)   # "Nakit", "Kredi Kartı", ...
    kdv_rate = Column(Integer, nullable=True)          # 0, 1, 8, 18 ...
    kdv_amount = Column(Float, nullable=True)          # TOPKDV 0,38 gibi (opsiyonel)
    category = Column(String(20), nullable=True)       # "Gelir", "Gider", ...

    # Yeni alanlar:
    invoice_date = Column(String(20), nullable=True)   # Fiş tarihi (ör: 16/12/2017)
    vendor = Column(String(100), nullable=True)        # Satıcı adı (market ismi)

    # Kayıt zamanı (sistem zamanı)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

