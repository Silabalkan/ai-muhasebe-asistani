# main.py
from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from PIL import Image
import pytesseract
import io
from typing import List

# Tesseract yolu (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Yerel modüller
import models
from db import Base, engine, get_db
from crud import create_invoice, list_invoices
from schemas import InvoiceRead
from nlp_utils import analyze_invoice_text

# FastAPI app
app = FastAPI(title="AI Muhasebe Asistanı - OCR API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Veritabanı tablolarını oluştur
Base.metadata.create_all(bind=engine)


# 1) Sağlık kontrolü
@app.get("/health")
def health_check():
    return {"status": "ok"}


# 2) Debug için sadece OCR çıktısı
@app.post("/debug-ocr")
async def debug_ocr(file: UploadFile = File(...)):
    data = await file.read()
    image = Image.open(io.BytesIO(data))

    try:
        text = pytesseract.image_to_string(image, lang="tur")
    except Exception:
        text = pytesseract.image_to_string(image)

    return {"raw_text": text}


@app.post("/invoices/upload-analyze", response_model=InvoiceRead)
async def upload_analyze_save(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Kullanıcıdan alınan fiş/fatura görselini OCR ile okuyup
    NLP analizinden geçirerek veritabanına kaydeder.
    """
    content = await file.read()
    image = Image.open(io.BytesIO(content))

    # --- OCR ---
    try:
        text = pytesseract.image_to_string(image, lang="tur")
    except Exception:
        text = pytesseract.image_to_string(image)

    # --- NLP Analizi ---
    result = analyze_invoice_text(text)

    inv = create_invoice(
        db,
        filename=file.filename,
        raw_text=text,
        total_amount=result.get("tutar"),
        payment_type=result.get("odeme_tipi"),
        kdv_rate=result.get("kdv_orani"),
        kdv_amount=result.get("kdv_tutari"),
        category=result.get("kategori"),
        invoice_date=result.get("tarih"),
        vendor=result.get("satıcı"),
    )

    return inv


# 4) Kayıtlı fişleri listele
@app.get("/invoices", response_model=List[InvoiceRead])
def get_invoices(db: Session = Depends(get_db), limit: int = 50):
    return list_invoices(db, limit=limit)


# 5) Özet rapor
@app.get("/reports/summary")
def summary_report(db: Session = Depends(get_db)):
    income = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(models.Invoice.category == "Gelir")
        .scalar()
        or 0.0
    )
    expense = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(models.Invoice.category == "Gider")
        .scalar()
        or 0.0
    )

    net = income - expense

    by_cat = (
        db.query(models.Invoice.category, func.sum(models.Invoice.total_amount))
        .group_by(models.Invoice.category)
        .all()
    )

    by_cat = [
        {"category": c or "Bilinmiyor", "total": float(t or 0)}
        for c, t in by_cat
    ]

    return {
        "income": float(income),
        "expense": float(expense),
        "net": float(net),
        "by_category": by_cat,
    }
