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
    UserRead
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
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """KPI, trend ve detaylı analiz"""
    today = date.today()

    if period == "weekly":
        start_date = today - timedelta(days=7)
    elif period == "yearly":
        start_date = today.replace(month=1, day=1)
    else:  # monthly
        start_date = today.replace(day=1)

    end_date = today

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
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Son N ay gelir-gider trendi"""
    today = date.today()
    data = []

    for i in range(months - 1, -1, -1):
        # Ay başlangıcı ve sonu
        current_date = today - timedelta(days=today.day - 1)
        month_start = current_date - timedelta(days=i * 30)
        month_start = month_start.replace(day=1)
        
        # Sonraki ayın ilk günü (aralık hesabı için)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)

        income = (
            db.query(func.sum(models.Invoice.total_amount))
            .filter(
                models.Invoice.user_id == current_user.id,
                models.Invoice.category == "Gelir",
                models.Invoice.invoice_date >= month_start,
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
                models.Invoice.invoice_date >= month_start,
                models.Invoice.invoice_date <= month_end
            )
            .scalar()
            or 0
        )

        data.append({
            "month": month_start.strftime("%b %Y"),  # Örn: "Dec 2025"
            "income": float(income),
            "expense": float(expense),
            "net": float(income - expense),
        })

    return {"trend": data}

# =========================
# KATEGORİ DAĞILIM (GİDER)
# =========================
@app.get("/reports/category-distribution")
def category_distribution(
    period: str = "monthly",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Giderlerin kategori bazında dağılımı"""
    today = date.today()

    if period == "weekly":
        start_date = today - timedelta(days=7)
    elif period == "yearly":
        start_date = today.replace(month=1, day=1)
    else:  # monthly
        start_date = today.replace(day=1)

    end_date = today

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
