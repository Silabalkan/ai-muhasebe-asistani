# schemas.py
from pydantic import BaseModel, field_validator
from datetime import date, datetime

class InvoiceRead(BaseModel):
    id: int
    filename: str
    total_amount: float | None
    payment_type: str | None
    kdv_rate: float | None
    kdv_amount: float | None
    category: str
    invoice_date: date | None
    vendor: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ManualIncomeCreate(BaseModel):
    amount: float
    date: date
    description: str

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d").date()
        return v
