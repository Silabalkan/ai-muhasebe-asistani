# AI-Based Accounting Assistant

An AI-integrated financial automation system designed for small and medium-sized enterprises (SMEs).

This project enables users to upload invoices and receipts, automatically extract text using OCR, classify financial transactions using NLP models, and generate structured income–expense reports.

---

## 🚀 Features

- Invoice & receipt upload
- OCR-based text extraction (Tesseract)
- NLP-based financial category classification (BERTurk)
- Automated income–expense reporting
- RESTful API architecture (FastAPI)
- PostgreSQL / SQLite database integration
- Modular backend architecture
- Frontend integration for visualization

---

## 🏗 Architecture Overview

The system follows a layered backend architecture:

- **API Layer** – FastAPI endpoints
- **Service Layer** – Business logic & processing
- **OCR Layer** – Image preprocessing & text extraction
- **NLP Layer** – Financial category classification
- **Database Layer** – Structured data persistence

---

## 🛠 Tech Stack

**Backend**
- Python
- FastAPI
- PostgreSQL / SQLite
- SQLAlchemy

**AI & Data Processing**
- Tesseract OCR
- Transformers (BERTurk)
- Image preprocessing techniques

**Frontend**
- React.js

**DevOps**
- Docker (Containerized backend environment)

---

## ⚙️ Running the Project

```bash
# Clone repository
git clone https://github.com/yourusername/ai-muhasebe-asistani.git

# Install backend dependencies
pip install -r requirements.txt

# Run backend
uvicorn main:app --reload

Frontend:
cd ai-muhasebe-frontend
npm install
npm start
