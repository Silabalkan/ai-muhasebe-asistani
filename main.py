from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import io

app = FastAPI(title="AI Muhasebe Asistanı - OCR API")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/ocr/image")
async def ocr_image(file: UploadFile = File(...)):
    # Sadece jpg/png kabul
    if file.content_type not in ("image/jpeg", "image/png"):
        return JSONResponse({"error": "Lütfen JPG veya PNG dosyası yükleyin."}, status_code=400)
    
    # Dosyayı oku
    content = await file.read()
    image = Image.open(io.BytesIO(content))
    
    # Türkçe OCR (TR paketi varsa)
    try:
        text = pytesseract.image_to_string(image, lang="tur")
    except Exception:
        text = pytesseract.image_to_string(image)
    
    return {"filename": file.filename, "text": text.strip()}

from nlp_utils import analyze_invoice_text

@app.post("/ocr/analyze")
async def analyze_image(file: UploadFile = File(...)):
    # Görseli oku
    content = await file.read()
    image = Image.open(io.BytesIO(content))

    # OCR metni al
    text = pytesseract.image_to_string(image, lang="tur")

    # NLP analizi uygula
    result = analyze_invoice_text(text)

    return {
        "filename": file.filename,
        "text": text.strip(),
        "analysis": result
    }

