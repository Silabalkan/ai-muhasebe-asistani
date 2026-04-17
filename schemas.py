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


class MonthlyAggregatePoint(BaseModel):
    month: str
    income: float
    expense: float
    net: float


class MonthlyAggregateResponse(BaseModel):
    months: int
    start_month: str
    end_month: str
    points: list[MonthlyAggregatePoint]


class ForecastPoint(BaseModel):
    month: str
    income: float
    expense: float
    net: float
    income_lower: float | None = None
    income_upper: float | None = None
    expense_lower: float | None = None
    expense_upper: float | None = None


class ForecastQuality(BaseModel):
    holdout_months: int
    income_mape: float | None = None
    expense_mape: float | None = None
    income_wape: float | None = None
    expense_wape: float | None = None
    confidence_level: str


class ForecastResponse(BaseModel):
    model_used: str
    model_version: str
    trained_at: str
    history_months: int
    forecast_months: int
    history_start_month: str
    history_end_month: str
    quality: ForecastQuality
    history: list[MonthlyAggregatePoint]
    forecast: list[ForecastPoint]


class FinancialInsightResponse(BaseModel):
    period: str
    start_date: date
    end_date: date
    total_income: float
    total_expense: float
    net: float
    forecast_next_expense: float | None = None
    insight_text: str
    insight_source: str
    model_used: str | None = None


class AICommentRequest(BaseModel):
    summary: str

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v):
        value = (v or "").strip()
        if len(value) < 10:
            raise ValueError("summary en az 10 karakter olmali")
        return value


class AICommentResponse(BaseModel):
    comment: str
    provider: str


class AIStatusResponse(BaseModel):
    provider: str
    configured_model: str
    healthy: bool
    detail: str
