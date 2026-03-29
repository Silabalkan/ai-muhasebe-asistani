# AI Muhasebe Asistani

KOBI odakli bir gelir-gider takip ve raporlama uygulamasi.
Backend FastAPI ile, frontend React ile gelistirilmistir.

## Ozellikler

- Fis/fatura gorseli yukleme
- OCR ile metin cikarma (Tesseract + pytesseract)
- Regex tabanli fatura alani ayrisimi (tarih, tutar, KDV, odeme tipi, satici)
- Gelir ve gider kaydi (otomatik OCR + manuel gelir)
- KPI, trend, kategori dagilimi ve odeme tipi raporlari
- Zaman serisi tahmini (auto: Prophet/ARIMA/Linear fallback)

## Mimari Ozeti

- Backend API: FastAPI ([main.py](main.py))
- Veri erisimi: SQLAlchemy + SQLite ([db.py](db.py), [models.py](models.py))
- Kimlik dogrulama: JWT + sifre hash ([auth.py](auth.py))
- Is katmani/CRUD: [crud.py](crud.py)
- OCR/NLP yardimcilari: [nlp_utils.py](nlp_utils.py)
- Frontend: React ([ai-muhasebe-frontend/src](ai-muhasebe-frontend/src))

## Teknoloji Yigini

- Python, FastAPI, SQLAlchemy, Pydantic
- SQLite (varsayilan)
- Tesseract OCR + pytesseract
- Prophet, statsmodels, pandas (tahmin icin)
- React, axios, recharts

## Calistirma

### Backend

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd ai-muhasebe-frontend
npm install
npm start
```
