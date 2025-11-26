# schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class InvoiceBase(BaseModel):
    filename: str
    raw_text: str
    total_amount: Optional[float] = None
    payment_type: Optional[str] = None
    kdv_rate: Optional[int] = None
    category: Optional[str] = None


class InvoiceRead(InvoiceBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True          # Pydantic v1 için
        from_attributes = True   # Pydantic v2 için (zararı yok)
