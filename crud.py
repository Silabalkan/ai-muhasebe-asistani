from sqlalchemy.orm import Session
from models import Invoice

def create_invoice(db: Session, **kwargs) -> Invoice:
    inv = Invoice(**kwargs)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv

def list_invoices(db: Session, limit: int = 50):
    return db.query(Invoice).order_by(Invoice.created_at.desc()).limit(limit).all()
