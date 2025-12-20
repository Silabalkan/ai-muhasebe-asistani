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
# FİŞ YÜKLE + OCR + NLP
# =========================
@app.post("/invoices/upload-analyze", response_model=InvoiceRead)
async def upload_analyze_save(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
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
        category=result.get("kategori", "Gider"),
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
# RAPOR ÖZETİ
# =========================
# =========================
# RAPOR ÖZETİ
# =========================
@app.get("/reports/summary")
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
