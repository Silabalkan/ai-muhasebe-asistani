import re
from datetime import datetime

# Tarih formatları
DATE_PATTERNS = [
    r"\d{2}\.\d{2}\.\d{4}",
    r"\d{4}-\d{2}-\d{2}",
    r"\d{2}/\d{2}/\d{4}",
    r"\d{2}-\d{2}-\d{2,4}",
]

# Para kalıpları
STRICT_MONEY_PATTERN = r"\d+[.,]\d{2}"                 # Sadece para formatı (128,95 gibi)
STAR_MONEY_PATTERN = r"\*\s*(\d+[.,]\d{2})"            # *128,95 formatı
TOPLAM_LINE_PATTERN = r"(toplam|total|genel toplam|ara toplam|top)\D*(\d+[.,]\d{2})"
TOP_KDV_PATTERN = r"topkdv\D*(\d+[.,]\d{2})"

# KDV oranları
KDV_RATE_PATTERN = r"%\s*(\d{1,2})"

# Anahtar kelimeler
INCOME_KEYWORDS = ["tahsilat", "ödeme alındı", "satış", "gelir", "fatura"]
EXPENSE_KEYWORDS = ["gider", "alış", "malzeme", "kira", "ekmek", "market", "ürün"]


#  SORUN ÇÖZEN YENİ TUTAR BULMA ALGORİTMASI 
def extract_amount(clean_text):
    lines = clean_text.split()

    # 1️⃣ TOPLAM satırı
    toplam_match = re.search(TOPLAM_LINE_PATTERN, clean_text)
    if toplam_match:
        val = toplam_match.group(2)
        return float(val.replace(".", "").replace(",", "."))

    # 2️⃣ Yıldızlı toplam (*128,95)
    star_match = re.search(STAR_MONEY_PATTERN, clean_text)
    if star_match:
        val = star_match.group(1)
        return float(val.replace(".", "").replace(",", "."))

    # 3️⃣ Normal para formatı (128,95)
    money_values = re.findall(STRICT_MONEY_PATTERN, clean_text)
    if money_values:
        values = [float(x.replace(".", "").replace(",", ".")) for x in money_values]
        return max(values)

    # 4️⃣ Güvenli fallback (ama tek başına tam sayıları PARA SAYMA!)
    all_numbers = re.findall(r"\d+[.,]?\d*", clean_text)
    filtered = []
    for num in all_numbers:
        if "." in num or "," in num:  # sadece ondalıklı olanlar
            try:
                filtered.append(float(num.replace(".", "").replace(",", ".")))
            except:
                pass

    return max(filtered) if filtered else None


#  Ana analiz fonksiyonu (GÜNCEL)
def analyze_invoice_text(text: str) -> dict:
    result = {
        "tarih": None,
        "satıcı": None,
        "tutar": None,
        "odeme_tipi": None,
        "kdv_orani": None,
        "kdv_tutari": None,
        "kategori": None,
    }

    # Normalize
    clean_text = (
        text.lower()
        .replace("\n", " ")
        .replace("\t", " ")
        .replace("*", " *")  # yıldızlı tutarlar için önemli
        .strip()
    )

    # TARİH
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, clean_text)
        if match:
            result["tarih"] = match.group()
            break

    #  TUTAR (yeni güçlü algoritma)
    result["tutar"] = extract_amount(clean_text)

    #  KDV Tutarı
    top_kdv_match = re.search(TOP_KDV_PATTERN, clean_text)
    if top_kdv_match:
        result["kdv_tutari"] = float(top_kdv_match.group(1).replace(",", "."))

    #  KDV ORANI
    kdv_rates = re.findall(KDV_RATE_PATTERN, clean_text)
    if kdv_rates:
        result["kdv_orani"] = max(kdv_rates)

    #  ÖDEME TİPİ
    if "nakit" in clean_text:
        result["odeme_tipi"] = "Nakit"
    elif "kredi" in clean_text or "visa" in clean_text or "mastercard" in clean_text:
        result["odeme_tipi"] = "Kredi Kartı"

    #  KATEGORİ
    if any(k in clean_text for k in INCOME_KEYWORDS):
        result["kategori"] = "Gelir"
    elif any(k in clean_text for k in EXPENSE_KEYWORDS):
        result["kategori"] = "Gider"
    else:
        result["kategori"] = "Bilinmiyor"

    #  SATICI (ilk büyük harfli blok)
    satıcı = re.findall(r"[A-ZÇĞİÖŞÜ\s]{3,}", text)
    if satıcı:
        result["satıcı"] = satıcı[0].strip()

    return result
