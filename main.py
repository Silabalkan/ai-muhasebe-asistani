# =========================
# IMPORTLAR
# =========================
from fastapi import FastAPI, File, UploadFile, Depends
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
from db import Base, engine, get_db
from crud import (
    create_invoice,
    list_invoices,
    create_manual_income
)
from schemas import (
    InvoiceRead,
    ManualIncomeCreate
)
from nlp_utils import analyze_invoice_text

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
# FİŞ YÜKLE + OCR + NLP (ANA SAYFADA - GIDER OLARAK)
# =========================
@app.post("/invoices/upload-analyze", response_model=InvoiceRead)
async def upload_analyze_save(
    file: UploadFile = File(...),
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
    )

    return invoice

# =========================
# FİŞ YÜKLE + OCR + NLP (GELİR OLARAK)
# =========================
@app.post("/invoices/upload-analyze-income", response_model=InvoiceRead)
async def upload_analyze_income(
    file: UploadFile = File(...),
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
    )

    return invoice

# =========================
# KAYITLI FİŞLER
# =========================
@app.get("/invoices", response_model=List[InvoiceRead])
def get_invoices(
    db: Session = Depends(get_db),
    limit: int = 50
):
    return list_invoices(db, limit=limit)

# =========================
# MANUEL GELİR EKLE
# =========================
@app.post("/invoices/manual-income")
def add_manual_income(
    data: ManualIncomeCreate,
    db: Session = Depends(get_db)
):
    return create_manual_income(db, data)

# =========================
# HIZLI ÖZET (ANA SAYFA İÇİN)
# =========================
@app.get("/reports/quick-summary")
def quick_summary(db: Session = Depends(get_db)):
    """Günün/Ayın özeti - ana sayfa için"""
    today = date.today()
    month_start = today.replace(day=1)

    # Bugünün veriler
    today_income = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(
            models.Invoice.category == "Gelir",
            models.Invoice.invoice_date == today
        )
        .scalar()
        or 0
    )

    today_expense = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(
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

    # İŞLEM SAYILARI
    income_count = (
        db.query(func.count(models.Invoice.id))
        .filter(
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
