# crud.py
from sqlalchemy.orm import Session
import models
from auth import hash_password, verify_password

# ========================
# USER CRUD
# ========================
def create_user(db: Session, email: str, username: str, password: str) -> models.User:
    """Yeni kullanıcı oluştur"""
    hashed_password = hash_password(password)
    user = models.User(
        email=email,
        username=username,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_username(db: Session, username: str) -> models.User | None:
    """Username ile kullanıcı getir"""
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> models.User | None:
    """Email ile kullanıcı getir"""
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, username: str, password: str) -> models.User | None:
    """Kullanıcı otoentikasyonu"""
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# ========================
# INVOICE CRUD
# ========================
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
    user_id: int,
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
        user_id=user_id,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def create_manual_income(db: Session, data, user_id: int):
    # Eğer tarih verilmemişse, bugünün tarihini kullan
    from datetime import date
    invoice_date = data.date if data.date else date.today()

    invoice = models.Invoice(
        filename="MANUAL",
        raw_text=data.description,
        total_amount=data.amount,
        payment_type="Nakit",
        category="Gelir",
        invoice_date=invoice_date,
        vendor=data.description,
        user_id=user_id,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def list_invoices(db: Session, user_id: int, limit: int = 50):
    return (
        db.query(models.Invoice)
        .filter(models.Invoice.user_id == user_id)
        .order_by(models.Invoice.created_at.desc())
        .limit(limit)
        .all()
    )
