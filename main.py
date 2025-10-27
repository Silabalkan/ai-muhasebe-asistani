from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from PIL import Image
import pytesseract
import io
from typing import List
from sqlalchemy import func

# Yerel modüller
import models
from db import Base, engine, get_db
from crud import create_invoice, list_invoices
from schemas import InvoiceRead
from nlp_utils import analyze_invoice_text

# Uygulama başlat
app = FastAPI(title="AI Muhasebe Asistanı - OCR API")

# CORS (Frontend için gerekli olabilir)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Veritabanı tablolarını oluştur
Base.metadata.create_all(bind=engine)


# 🩺 Sağlık kontrolü
@app.get("/health")
def health_check():
    return {"status": "ok"}


# 🧾 Fatura Yükle + OCR + NLP Analiz + Veritabanına Kaydet
@app.post("/invoices/upload-analyze", response_model=InvoiceRead)
async def upload_analyze_save(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Kullanıcıdan alınan fiş/fatura görselini OCR ile okuyup
    NLP analizinden geçirerek veritabanına kaydeder.
    """
    content = await file.read()
    image = Image.open(io.BytesIO(content))

    # OCR (Türkçe desteği varsa 'tur' olarak kullan)
    try:
        text = pytesseract.image_to_string(image, lang="tur").strip()
    except Exception:
        text = pytesseract.image_to_string(image).strip()

    # NLP analizi (tutar, kategori, ödeme tipi vb.)
    result = analyze_invoice_text(text)

    # Veritabanına kaydet
    inv = create_invoice(
        db,
        filename=file.filename,
        raw_text=text,
        total_amount=result.get("tutar"),
        payment_type=result.get("odeme_tipi"),
        kdv_rate=result.get("kdv_orani"),
        category=result.get("kategori"),
    )

    return inv


# 📜 Kayıtlı faturaları listele
@app.get("/invoices", response_model=List[InvoiceRead])
def get_invoices(db: Session = Depends(get_db), limit: int = 50):
    """
    Veritabanındaki son 50 faturayı getirir.
    """
    return list_invoices(db, limit=limit)


# 📊 Özet rapor (gelir/gider toplamı)
@app.get("/reports/summary")
def summary_report(db: Session = Depends(get_db)):
    """
    Gelir - Gider - Net kazanç ve kategori bazlı toplamları döner.
    """
    income = db.query(func.sum(models.Invoice.total_amount))\
               .filter(models.Invoice.category == "Gelir").scalar() or 0.0
    expense = db.query(func.sum(models.Invoice.total_amount))\
                .filter(models.Invoice.category == "Gider").scalar() or 0.0
    net = (income or 0.0) - (expense or 0.0)

    by_cat = db.query(models.Invoice.category, func.sum(models.Invoice.total_amount))\
               .group_by(models.Invoice.category).all()
    by_cat = [{"category": c or "Bilinmiyor", "total": float(t or 0)} for c, t in by_cat]

    return {
        "income": float(income or 0),
        "expense": float(expense or 0),
        "net": float(net),
        "by_category": by_cat,
    }


#  Uygulama çalıştırma (isteğe bağlı)
# Terminalde: uvicorn main:app --reload
