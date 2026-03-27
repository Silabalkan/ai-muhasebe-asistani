# =========================
# IMPORTLAR
# =========================
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from PIL import Image
import pytesseract
import io
from typing import List
from datetime import date, timedelta, datetime
import math
import importlib
import warnings

# Yerel modüller
import models
from db import Base, engine, get_db, ensure_schema_compatibility
from crud import (
    create_invoice,
    list_invoices,
    create_manual_income,
    create_user,
    get_user_by_email,
    get_user_by_username,
    authenticate_user
)
from schemas import (
    InvoiceRead,
    ManualIncomeCreate,
    UserRegister,
    UserLogin,
    TokenResponse,
    UserRead,
    MonthlyAggregateResponse,
    ForecastResponse,
)
from nlp_utils import analyze_invoice_text
from auth import get_current_user, create_access_token

# =========================
# TESSERACT (WINDOWS)
# =========================
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# =========================
# FASTAPI APP
# =========================
app = FastAPI(title="AI Muhasebe Asistanı - OCR API")

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DB OLUŞTUR
# =========================
Base.metadata.create_all(bind=engine)
ensure_schema_compatibility()

# =========================
# TARİH GÜVENLİ PARSE
# =========================
def safe_parse_date(value):
    if not value:
        return None

    if isinstance(value, date):
        return value

    try:
        # ISO format: YYYY-MM-DD
        return datetime.fromisoformat(value).date()
    except Exception:
        try:
            # DD/MM/YYYY format
            return datetime.strptime(value, "%d/%m/%Y").date()
        except Exception:
            return None


def month_start(d: date) -> date:
    return d.replace(day=1)


def add_months(d: date, delta: int) -> date:
    month_index = (d.month - 1) + delta
    year = d.year + (month_index // 12)
    month = (month_index % 12) + 1
    return d.replace(year=year, month=month, day=1)


def month_diff_inclusive(start_month: date, end_month: date) -> int:
    return ((end_month.year - start_month.year) * 12) + (end_month.month - start_month.month) + 1


def build_monthly_aggregate_points_for_window(
    db: Session,
    user_id: int,
    start_month: date,
    end_month: date,
):
    if start_month > end_month:
        return []

    query_end = add_months(end_month, 1) - timedelta(days=1)

    rows = (
        db.query(
            func.strftime("%Y-%m", models.Invoice.invoice_date).label("month_key"),
            models.Invoice.category,
            func.sum(models.Invoice.total_amount).label("amount")
        )
        .filter(
            models.Invoice.user_id == user_id,
            models.Invoice.invoice_date >= start_month,
            models.Invoice.invoice_date <= query_end,
            models.Invoice.total_amount.isnot(None)
        )
        .group_by("month_key", models.Invoice.category)
        .all()
    )

    month_map = {}
    cursor = start_month
    while cursor <= end_month:
        key = cursor.strftime("%Y-%m")
        month_map[key] = {"income": 0.0, "expense": 0.0}
        cursor = add_months(cursor, 1)

    for row in rows:
        month_key = row.month_key
        if month_key not in month_map:
            continue
        amount = float(row.amount or 0)
        if row.category == "Gelir":
            month_map[month_key]["income"] += amount
        elif row.category == "Gider":
            month_map[month_key]["expense"] += amount

    points = []
    for month_key in sorted(month_map.keys()):
        income = month_map[month_key]["income"]
        expense = month_map[month_key]["expense"]
        points.append(
            {
                "month": month_key,
                "income": float(income),
                "expense": float(expense),
                "net": float(income - expense),
            }
        )

    return points


def build_monthly_aggregate_points(db: Session, user_id: int, months: int):
    current_month = month_start(date.today())
    start_month = add_months(current_month, -(months - 1))
    points = build_monthly_aggregate_points_for_window(
        db=db,
        user_id=user_id,
        start_month=start_month,
        end_month=current_month,
    )

    return start_month, current_month, points


def resolve_period_dates(
    period: str,
    start_date: date | None,
    end_date: date | None,
):
    today = date.today()

    if start_date or end_date:
        if not start_date or not end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date ve end_date birlikte gönderilmeli"
            )
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date, end_date'den büyük olamaz"
            )
        if end_date > today:
            end_date = today
        return start_date, end_date

    if period == "weekly":
        return today - timedelta(days=7), today
    if period == "yearly":
        return today.replace(month=1, day=1), today
    return today.replace(day=1), today


def linear_forecast(values: list[float], forecast_months: int):
    n = len(values)
    if n == 0:
        return [(0.0, 0.0, 0.0) for _ in range(forecast_months)]

    if n == 1:
        base = max(0.0, float(values[0]))
        return [(base, base, base) for _ in range(forecast_months)]

    x_mean = (n - 1) / 2
    y_mean = sum(values) / n

    cov = 0.0
    var = 0.0
    for i, y in enumerate(values):
        cov += (i - x_mean) * (y - y_mean)
        var += (i - x_mean) ** 2

    slope = cov / var if var else 0.0
    intercept = y_mean - slope * x_mean

    residual_sum = 0.0
    for i, y in enumerate(values):
        y_hat = intercept + slope * i
        residual_sum += (y - y_hat) ** 2
    residual_std = math.sqrt(residual_sum / max(1, n - 2))

    results = []
    for h in range(forecast_months):
        x = n + h
        pred = max(0.0, intercept + slope * x)
        lower = max(0.0, pred - 1.96 * residual_std)
        upper = max(lower, pred + 1.96 * residual_std)
        results.append((float(pred), float(lower), float(upper)))

    return results


def prophet_forecast(month_keys: list[str], values: list[float], forecast_months: int):
    try:
        pd = importlib.import_module("pandas")
        prophet_module = importlib.import_module("prophet")
        Prophet = getattr(prophet_module, "Prophet")
    except Exception:
        return None

    try:
        ds = [datetime.strptime(k + "-01", "%Y-%m-%d") for k in month_keys]
        df = pd.DataFrame({"ds": ds, "y": values})

        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        model.fit(df)

        future = model.make_future_dataframe(periods=forecast_months, freq="MS")
        pred = model.predict(future).tail(forecast_months)

        result = []
        for _, row in pred.iterrows():
            month = row["ds"].strftime("%Y-%m")
            yhat = max(0.0, float(row["yhat"]))
            lower = max(0.0, float(row["yhat_lower"]))
            upper = max(lower, float(row["yhat_upper"]))
            result.append(
                {
                    "month": month,
                    "value": yhat,
                    "lower": lower,
                    "upper": upper,
                }
            )
        return result
    except Exception:
        return None


def arima_forecast(month_keys: list[str], values: list[float], forecast_months: int):
    if len(values) < 4:
        return None

    try:
        arima_module = importlib.import_module("statsmodels.tsa.arima.model")
        ARIMA = getattr(arima_module, "ARIMA")
        sm_exceptions = importlib.import_module("statsmodels.tools.sm_exceptions")
        ConvergenceWarning = getattr(sm_exceptions, "ConvergenceWarning")
    except Exception:
        return None

    try:
        base_series = [float(v) for v in values]
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            model = ARIMA(base_series, order=(1, 1, 1))
            fitted = model.fit()
        forecast_obj = fitted.get_forecast(steps=forecast_months)

        mean_values = [float(v) for v in forecast_obj.predicted_mean]
        conf_int = forecast_obj.conf_int(alpha=0.05)

        if hasattr(conf_int, "values"):
            conf_rows = conf_int.values.tolist()
        else:
            conf_rows = [list(r) for r in conf_int]

        end_month = datetime.strptime(month_keys[-1] + "-01", "%Y-%m-%d").date()

        result = []
        for i in range(forecast_months):
            month = add_months(end_month, i + 1).strftime("%Y-%m")
            pred = max(0.0, mean_values[i])
            lower_raw, upper_raw = conf_rows[i][0], conf_rows[i][1]
            lower = max(0.0, float(lower_raw))
            upper = max(lower, float(upper_raw))
            result.append(
                {
                    "month": month,
                    "value": pred,
                    "lower": lower,
                    "upper": upper,
                }
            )
        return result
    except Exception:
        return None


def forecast_series_with_model(
    month_keys: list[str],
    values: list[float],
    forecast_months: int,
    model_name: str,
):
    if model_name == "prophet":
        return prophet_forecast(month_keys, values, forecast_months)
    if model_name == "arima":
        return arima_forecast(month_keys, values, forecast_months)
    if model_name == "linear":
        end_month = datetime.strptime(month_keys[-1] + "-01", "%Y-%m-%d").date()
        linear_result = linear_forecast(values, forecast_months)
        result = []
        for i in range(forecast_months):
            pred, lower, upper = linear_result[i]
            result.append(
                {
                    "month": add_months(end_month, i + 1).strftime("%Y-%m"),
                    "value": float(pred),
                    "lower": float(lower),
                    "upper": float(upper),
                }
            )
        return result

    return None


def calculate_error_metrics(actuals: list[float], preds: list[float]):
    if not actuals or not preds or len(actuals) != len(preds):
        return None, None

    pairs = [(float(a), float(p)) for a, p in zip(actuals, preds)]

    non_zero_pairs = [(a, p) for a, p in pairs if abs(a) > 1e-9]
    if non_zero_pairs:
        mape = (
            sum(abs((a - p) / a) for a, p in non_zero_pairs)
            / len(non_zero_pairs)
        ) * 100
    else:
        mape = None

    denom = sum(abs(a) for a, _ in pairs)
    if denom > 0:
        wape = (sum(abs(a - p) for a, p in pairs) / denom) * 100
    else:
        wape = None

    return mape, wape


def confidence_from_wape(income_wape: float | None, expense_wape: float | None):
    available = [v for v in [income_wape, expense_wape] if v is not None]
    if not available:
        return "unknown"

    avg_wape = sum(available) / len(available)
    if avg_wape <= 15:
        return "high"
    if avg_wape <= 30:
        return "medium"
    return "low"


def run_backtest(month_keys: list[str], values: list[float], model_name: str):
    n = len(values)
    if n < 6:
        return {
            "holdout_months": 0,
            "mape": None,
            "wape": None,
        }

    holdout = min(3, max(1, n // 4))
    train_n = n - holdout
    if train_n < 3:
        return {
            "holdout_months": 0,
            "mape": None,
            "wape": None,
        }

    train_keys = month_keys[:train_n]
    train_values = values[:train_n]
    test_values = values[train_n:]

    forecast_result = forecast_series_with_model(
        month_keys=train_keys,
        values=train_values,
        forecast_months=holdout,
        model_name=model_name,
    )

    if forecast_result is None or len(forecast_result) != holdout:
        linear_result = linear_forecast(train_values, holdout)
        preds = [float(item[0]) for item in linear_result]
    else:
        preds = [float(item["value"]) for item in forecast_result]

    mape, wape = calculate_error_metrics(test_values, preds)
    return {
        "holdout_months": holdout,
        "mape": mape,
        "wape": wape,
    }

# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
def health_check():
    return {"status": "ok"}

# =========================
# REGISTER
# =========================
@app.post("/auth/register", response_model=TokenResponse)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Yeni kullanıcı kaydı"""
    # Email kontrol
    existing_email = get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email zaten kayıtlı"
        )
    
    # Username kontrol
    existing_username = get_user_by_username(db, user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username zaten alınmış"
        )
    
    # Kullanıcı oluştur
    user = create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password
    )
    
    # Token oluştur
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserRead.from_orm(user)
    }

# =========================
# LOGIN
# =========================
@app.post("/auth/login", response_model=TokenResponse)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Kullanıcı girişi"""
    user = authenticate_user(db, user_data.username, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatalı username veya şifre"
        )
    
    # Token oluştur
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserRead.from_orm(user)
    }

# =========================
# FİŞ YÜKLE + OCR + NLP (ANA SAYFADA - GIDER OLARAK)
# =========================
@app.post("/invoices/upload-analyze", response_model=InvoiceRead)
async def upload_analyze_save(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ana sayfadan fiş yükle - HER ZAMAN Gider olarak kaydet"""
    content = await file.read()
    image = Image.open(io.BytesIO(content))

    try:
        raw_text = pytesseract.image_to_string(image, lang="tur")
    except Exception:
        raw_text = pytesseract.image_to_string(image)

    result = analyze_invoice_text(raw_text)

    # Tarih bulunamadıysa, bugünü atayalım
    parsed_date = safe_parse_date(result.get("tarih"))
    if not parsed_date:
        parsed_date = date.today()

    invoice = create_invoice(
        db=db,
        filename=file.filename,
        raw_text=raw_text,
        total_amount=result.get("tutar"),
        payment_type=result.get("odeme_tipi"),
        kdv_rate=result.get("kdv_orani"),
        kdv_amount=result.get("kdv_tutari"),
        category="Gider",  # ✅ ANA SAYFA = HER ZAMAN GİDER
        invoice_date=parsed_date,
        vendor=result.get("satıcı"),
        user_id=current_user.id,
    )

    return invoice

# =========================
# FİŞ YÜKLE + OCR + NLP (GELİR OLARAK)
# =========================
@app.post("/invoices/upload-analyze-income", response_model=InvoiceRead)
async def upload_analyze_income(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fiş yükle ve HER ZAMAN Gelir olarak kaydet"""
    content = await file.read()
    image = Image.open(io.BytesIO(content))

    try:
        raw_text = pytesseract.image_to_string(image, lang="tur")
    except Exception:
        raw_text = pytesseract.image_to_string(image)

    result = analyze_invoice_text(raw_text)

    # Tarih bulunamadıysa, bugünü atayalım
    parsed_date = safe_parse_date(result.get("tarih"))
    if not parsed_date:
        parsed_date = date.today()

    invoice = create_invoice(
        db=db,
        filename=file.filename,
        raw_text=raw_text,
        total_amount=result.get("tutar"),
        payment_type=result.get("odeme_tipi"),
        kdv_rate=result.get("kdv_orani"),
        kdv_amount=result.get("kdv_tutari"),
        category="Gelir",  # ✅ HER ZAMAN GELİR OLARAK KAYDET
        invoice_date=parsed_date,
        vendor=result.get("satıcı"),
        user_id=current_user.id,
    )

    return invoice

# =========================
# KAYITLI FİŞLER
# =========================
@app.get("/invoices", response_model=List[InvoiceRead])
def get_invoices(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    return list_invoices(db, user_id=current_user.id, limit=limit)

# =========================
# MANUEL GELİR EKLE
# =========================
@app.post("/invoices/manual-income")
def add_manual_income(
    data: ManualIncomeCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return create_manual_income(db, data, user_id=current_user.id)

# =========================
# HIZLI ÖZET (ANA SAYFA İÇİN)
# =========================
@app.get("/reports/quick-summary")
def quick_summary(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Günün/Ayın özeti - ana sayfa için"""
    today = date.today()
    month_start = today.replace(day=1)

    # Bugünün veriler
    today_income = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(
            models.Invoice.user_id == current_user.id,
            models.Invoice.category == "Gelir",
            models.Invoice.invoice_date == today
        )
        .scalar()
        or 0
    )

    today_expense = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(
            models.Invoice.user_id == current_user.id,
            models.Invoice.category == "Gider",
            models.Invoice.invoice_date == today
        )
        .scalar()
        or 0
    )

    # Ayın veriler
    month_income = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(
            models.Invoice.user_id == current_user.id,
            models.Invoice.category == "Gelir",
            models.Invoice.invoice_date >= month_start,
            models.Invoice.invoice_date <= today
        )
        .scalar()
        or 0
    )

    month_expense = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(
            models.Invoice.user_id == current_user.id,
            models.Invoice.category == "Gider",
            models.Invoice.invoice_date >= month_start,
            models.Invoice.invoice_date <= today
        )
        .scalar()
        or 0
    )

    # Son işlemler
    recent = (
        db.query(models.Invoice)
        .filter(models.Invoice.user_id == current_user.id)
        .order_by(models.Invoice.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "today": {
            "income": float(today_income),
            "expense": float(today_expense),
            "net": float(today_income - today_expense),
        },
        "month": {
            "income": float(month_income),
            "expense": float(month_expense),
            "net": float(month_income - month_expense),
        },
        "recent": [
            {
                "id": r.id,
                "vendor": r.vendor,
                "amount": r.total_amount,
                "category": r.category,
                "date": r.invoice_date,
                "created_at": r.created_at,
            }
            for r in recent
        ],
    }

# =========================
# RAPOR ÖZETİ
# =========================
def summary_report(
    period: str = "monthly",
    db: Session = Depends(get_db)
):
    today = date.today()

    if period == "weekly":
        start_date = today - timedelta(days=7)
    elif period == "yearly":
        start_date = today.replace(month=1, day=1)
    else:  # monthly
        start_date = today.replace(day=1)

    end_date = today

    income = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(
            models.Invoice.category == "Gelir",
            models.Invoice.invoice_date >= start_date,
            models.Invoice.invoice_date <= end_date
        )
        .scalar()
        or 0
    )

    expense = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(
            models.Invoice.category == "Gider",
            models.Invoice.invoice_date >= start_date,
            models.Invoice.invoice_date <= end_date
        )
        .scalar()
        or 0
    )

    return {
        "total_income": float(income),
        "total_expense": float(expense),
        "net": float(income - expense),
    }

# =========================
# GELİŞMİŞ RAPOR (KPI & ANALİZ)
# =========================
@app.get("/reports/advanced")
def advanced_report(
    period: str = "monthly",
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """KPI, trend ve detaylı analiz"""
    start_date, end_date = resolve_period_dates(period, start_date, end_date)

    # TOPLAM VERİLER
    income = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(
            models.Invoice.user_id == current_user.id,
            models.Invoice.category == "Gelir",
            models.Invoice.invoice_date >= start_date,
            models.Invoice.invoice_date <= end_date
        )
        .scalar()
        or 0
    )

    expense = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(
            models.Invoice.user_id == current_user.id,
            models.Invoice.category == "Gider",
            models.Invoice.invoice_date >= start_date,
            models.Invoice.invoice_date <= end_date
        )
        .scalar()
        or 0
    )

    # İŞLEM SAYILARI
    income_count = (
        db.query(func.count(models.Invoice.id))
        .filter(
            models.Invoice.user_id == current_user.id,
            models.Invoice.category == "Gelir",
            models.Invoice.invoice_date >= start_date,
            models.Invoice.invoice_date <= end_date
        )
        .scalar()
        or 0
    )

    expense_count = (
        db.query(func.count(models.Invoice.id))
        .filter(
            models.Invoice.user_id == current_user.id,
            models.Invoice.category == "Gider",
            models.Invoice.invoice_date >= start_date,
            models.Invoice.invoice_date <= end_date
        )
        .scalar()
        or 0
    )

    # ORTALAMA TUTARlar
    avg_income = float(income / income_count) if income_count > 0 else 0
    avg_expense = float(expense / expense_count) if expense_count > 0 else 0

    # KARLıLIK ORANI
    profitability = (
        ((income - expense) / income * 100) if income > 0 else 0
    )

    # TOPLAM KDV
    total_kdv = (
        db.query(func.sum(models.Invoice.kdv_amount))
        .filter(
            models.Invoice.user_id == current_user.id,
            models.Invoice.kdv_amount.isnot(None),
            models.Invoice.invoice_date >= start_date,
            models.Invoice.invoice_date <= end_date
        )
        .scalar()
        or 0
    )

    # ÖDEME TİPİ DAĞILIMI
    payment_types = (
        db.query(
            models.Invoice.payment_type,
            func.count(models.Invoice.id).label("count"),
            func.sum(models.Invoice.total_amount).label("amount")
        )
        .filter(
            models.Invoice.user_id == current_user.id,
            models.Invoice.invoice_date >= start_date,
            models.Invoice.invoice_date <= end_date
        )
        .group_by(models.Invoice.payment_type)
        .all()
    )

    payment_distribution = [
        {
            "type": pt[0] or "Bilinmiyor",
            "count": pt[1],
            "amount": float(pt[2] or 0)
        }
        for pt in payment_types
    ]

    return {
        "total_income": float(income),
        "total_expense": float(expense),
        "net": float(income - expense),
        "income_count": int(income_count),
        "expense_count": int(expense_count),
        "avg_income": float(avg_income),
        "avg_expense": float(avg_expense),
        "profitability_rate": float(profitability),
        "total_kdv": float(total_kdv),
        "payment_distribution": payment_distribution,
    }

# =========================
# AYLIK TREND VERİSİ
# =========================
@app.get("/reports/trend")
def trend_report(
    months: int = 6,
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Son N ay gelir-gider trendi"""
    if (start_date is None) != (end_date is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date ve end_date birlikte gönderilmeli"
        )

    today = date.today()
    if start_date and end_date:
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date, end_date'den büyük olamaz"
            )
        if end_date > today:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_date bugunden ileri olamaz"
            )
        range_start = month_start(start_date)
        range_end = month_start(end_date)
    else:
        if months < 1 or months > 60:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="months parametresi 1 ile 60 arasında olmalı"
            )
        range_end = month_start(today)
        range_start = add_months(range_end, -(months - 1))

    data = []

    cursor = range_start
    while cursor <= range_end:
        current_month_start = cursor
        month_end = add_months(current_month_start, 1) - timedelta(days=1)

        income = (
            db.query(func.sum(models.Invoice.total_amount))
            .filter(
                models.Invoice.user_id == current_user.id,
                models.Invoice.category == "Gelir",
                models.Invoice.invoice_date >= current_month_start,
                models.Invoice.invoice_date <= month_end
            )
            .scalar()
            or 0
        )

        expense = (
            db.query(func.sum(models.Invoice.total_amount))
            .filter(
                models.Invoice.user_id == current_user.id,
                models.Invoice.category == "Gider",
                models.Invoice.invoice_date >= current_month_start,
                models.Invoice.invoice_date <= month_end
            )
            .scalar()
            or 0
        )

        data.append({
            "month": current_month_start.strftime("%b %Y"),  # Örn: "Dec 2025"
            "income": float(income),
            "expense": float(expense),
            "net": float(income - expense),
        })

        cursor = add_months(cursor, 1)

    return {"trend": data}

# =========================
# KATEGORİ DAĞILIM (GİDER)
# =========================
@app.get("/reports/category-distribution")
def category_distribution(
    period: str = "monthly",
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Giderlerin kategori bazında dağılımı"""
    start_date, end_date = resolve_period_dates(period, start_date, end_date)

    categories = (
        db.query(
            models.Invoice.vendor,
            func.count(models.Invoice.id).label("count"),
            func.sum(models.Invoice.total_amount).label("amount")
        )
        .filter(
            models.Invoice.user_id == current_user.id,
            models.Invoice.invoice_date >= start_date,
            models.Invoice.invoice_date <= end_date
        )
        .group_by(models.Invoice.vendor)
        .order_by(func.sum(models.Invoice.total_amount).desc())
        .limit(10)
        .all()
    )

    return {
        "categories": [
            {
                "name": cat[0] or "Bilinmiyor",
                "count": cat[1],
                "amount": float(cat[2] or 0)
            }
            for cat in categories
        ]
    }


@app.get("/reports/monthly-aggregates", response_model=MonthlyAggregateResponse)
def monthly_aggregates(
    months: int = 12,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Time-series hazırlığı için aylık gelir/gider toplamlarını döndürür."""
    if months < 1 or months > 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="months parametresi 1 ile 60 arasında olmalı"
        )

    start_month, current_month, points = build_monthly_aggregate_points(
        db=db,
        user_id=current_user.id,
        months=months,
    )

    return {
        "months": months,
        "start_month": start_month.strftime("%Y-%m"),
        "end_month": current_month.strftime("%Y-%m"),
        "points": points,
    }


@app.get("/reports/forecast", response_model=ForecastResponse)
def forecast_report(
    history_months: int = 12,
    forecast_months: int = 3,
    forecast_model: str = "auto",
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aylık gelir/gider serisinden gelecek ay tahminleri üretir."""
    if forecast_months < 1 or forecast_months > 24:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="forecast_months 1 ile 24 arasında olmalı"
        )

    forecast_model = (forecast_model or "auto").strip().lower()
    allowed_models = {"auto", "prophet", "arima", "linear"}
    if forecast_model not in allowed_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="forecast_model auto, prophet, arima veya linear olmalı"
        )

    custom_window = start_date is not None or end_date is not None
    if custom_window:
        if not start_date or not end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date ve end_date birlikte gönderilmeli"
            )
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date, end_date'den büyük olamaz"
            )
        if end_date > date.today():
            end_date = date.today()

        range_start = month_start(start_date)
        range_end = month_start(end_date)
        history_months = month_diff_inclusive(range_start, range_end)

        if history_months < 1 or history_months > 60:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ozel aralik en az 1, en fazla 60 ay olmali"
            )

        history_points = build_monthly_aggregate_points_for_window(
            db=db,
            user_id=current_user.id,
            start_month=range_start,
            end_month=range_end,
        )
        end_month = range_end
    else:
        if history_months < 1 or history_months > 60:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="history_months 1 ile 60 arasında olmalı"
            )

        _, end_month, history_points = build_monthly_aggregate_points(
            db=db,
            user_id=current_user.id,
            months=history_months,
        )

    month_keys = [p["month"] for p in history_points]
    income_values = [float(p["income"]) for p in history_points]
    expense_values = [float(p["expense"]) for p in history_points]

    if forecast_model == "auto":
        model_order = ["prophet", "arima", "linear"]
    elif forecast_model == "prophet":
        model_order = ["prophet", "arima", "linear"]
    elif forecast_model == "arima":
        model_order = ["arima", "prophet", "linear"]
    else:
        model_order = ["linear"]

    selected_model = None
    income_result = None
    expense_result = None
    for candidate in model_order:
        current_income = forecast_series_with_model(
            month_keys=month_keys,
            values=income_values,
            forecast_months=forecast_months,
            model_name=candidate,
        )
        current_expense = forecast_series_with_model(
            month_keys=month_keys,
            values=expense_values,
            forecast_months=forecast_months,
            model_name=candidate,
        )
        if (
            current_income is not None
            and current_expense is not None
            and len(current_income) == forecast_months
            and len(current_expense) == forecast_months
        ):
            selected_model = candidate
            income_result = current_income
            expense_result = current_expense
            break

    if selected_model is None:
        selected_model = "linear"
        income_result = forecast_series_with_model(
            month_keys=month_keys,
            values=income_values,
            forecast_months=forecast_months,
            model_name="linear",
        )
        expense_result = forecast_series_with_model(
            month_keys=month_keys,
            values=expense_values,
            forecast_months=forecast_months,
            model_name="linear",
        )

    model_meta = {
        "prophet": ("prophet", "prophet-v1.0"),
        "arima": ("arima", "arima-v1.0"),
        "linear": ("linear-trend-fallback", "linear-trend-v1.0"),
    }
    model_used, model_version = model_meta[selected_model]

    forecast = []
    for i in range(forecast_months):
        income_item = income_result[i]
        expense_item = expense_result[i]
        income_pred = float(income_item["value"])
        expense_pred = float(expense_item["value"])
        forecast.append(
            {
                "month": income_item["month"],
                "income": income_pred,
                "expense": expense_pred,
                "net": float(income_pred - expense_pred),
                "income_lower": float(income_item["lower"]),
                "income_upper": float(income_item["upper"]),
                "expense_lower": float(expense_item["lower"]),
                "expense_upper": float(expense_item["upper"]),
            }
        )

    income_backtest = run_backtest(month_keys, income_values, selected_model)
    expense_backtest = run_backtest(month_keys, expense_values, selected_model)
    confidence_level = confidence_from_wape(
        income_backtest["wape"], expense_backtest["wape"]
    )
    trained_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    history_start_month = (
        history_points[0]["month"] if history_points else end_month.strftime("%Y-%m")
    )
    history_end_month = (
        history_points[-1]["month"] if history_points else end_month.strftime("%Y-%m")
    )

    return {
        "model_used": model_used,
        "model_version": model_version,
        "trained_at": trained_at,
        "history_months": history_months,
        "forecast_months": forecast_months,
        "history_start_month": history_start_month,
        "history_end_month": history_end_month,
        "quality": {
            "holdout_months": max(
                int(income_backtest["holdout_months"]),
                int(expense_backtest["holdout_months"]),
            ),
            "income_mape": (
                float(income_backtest["mape"])
                if income_backtest["mape"] is not None
                else None
            ),
            "expense_mape": (
                float(expense_backtest["mape"])
                if expense_backtest["mape"] is not None
                else None
            ),
            "income_wape": (
                float(income_backtest["wape"])
                if income_backtest["wape"] is not None
                else None
            ),
            "expense_wape": (
                float(expense_backtest["wape"])
                if expense_backtest["wape"] is not None
                else None
            ),
            "confidence_level": confidence_level,
        },
        "history": history_points,
        "forecast": forecast,
    }
