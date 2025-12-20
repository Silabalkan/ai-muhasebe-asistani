# crud.py
from sqlalchemy.orm import Session
import models

def create_invoice(
    db: Session,
    filename: str,
    raw_text: str,
    total_amount,
    payment_type,
    kdv_rate,
    kdv_amount,
    category,
    invoice_date,
    vendor,
):
    invoice = models.Invoice(
        filename=filename,
        raw_text=raw_text or "OCR",
        total_amount=total_amount,
        payment_type=payment_type,
        kdv_rate=kdv_rate,
        kdv_amount=kdv_amount,
        category=category,
        invoice_date=invoice_date,
        vendor=vendor,
        # ❌ created_at ELLE VERİLMİYOR
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def create_manual_income(db: Session, data):
    # Eğer tarih verilmemişse, bugünü kullan
    invoice_date = data.date if data.date else None
    
    invoice = models.Invoice(
        filename="MANUAL",
        raw_text=data.description,
        total_amount=data.amount,
        payment_type="Nakit",
        category="Gelir",
        invoice_date=invoice_date,
        vendor=data.description,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def list_invoices(db: Session, limit: int = 50):
    return (
        db.query(models.Invoice)
        .order_by(models.Invoice.created_at.desc())
        .limit(limit)
        .all()
    )
