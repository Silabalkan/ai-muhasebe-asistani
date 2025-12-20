from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class InvoiceBase(BaseModel):
    filename: str
    raw_text: str

    total_amount: Optional[float] = None
    payment_type: Optional[str] = None
    kdv_rate: Optional[int] = None
    kdv_amount: Optional[float] = None
    category: Optional[str] = None

    invoice_date: Optional[str] = None
    vendor: Optional[str] = None

class InvoiceRead(InvoiceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True   # SQLAlchemy objesinden okumak için
