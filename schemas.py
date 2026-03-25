# schemas.py
from pydantic import BaseModel, field_validator
from datetime import date, datetime

# ========================
# USER SCHEMAs
# ========================
class UserRegister(BaseModel):
    email: str
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        value = v.strip()
        if len(value) < 3:
            raise ValueError("Kullanici adi en az 3 karakter olmali")
        if len(value) > 32:
            raise ValueError("Kullanici adi en fazla 32 karakter olmali")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Sifre en az 6 karakter olmali")
        if len(v.encode("utf-8")) > 256:
            raise ValueError("Sifre cok uzun")
        return v

class UserLogin(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_login_username(cls, v):
        return v.strip()

class UserRead(BaseModel):
    id: int
    email: str
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserRead

# ========================
# INVOICE SCHEMAs
# ========================
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
