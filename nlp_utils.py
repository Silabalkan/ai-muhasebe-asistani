import re

def analyze_invoice_text(text: str):
    text = text.upper()

    # Bazı OCR hatalarını düzelt
    text = text.replace("TRY", "TL").replace("₺", "TL").replace(",", ".")
    text = re.sub(r"\s+", " ", text)  # gereksiz boşlukları temizle

    # 1️⃣ Tutarı bul
    # Örneğin: 179.54 TL veya TL 179.54
    amount_match = re.search(r'([0-9]+\.[0-9]{1,2})\s*TL', text)
    if not amount_match:
        amount_match = re.search(r'TL\s*([0-9]+\.[0-9]{1,2})', text)
    amount = float(amount_match.group(1)) if amount_match else None

    # 2️⃣ Ödeme tipini bul
    if "NAKIT" in text or "Nakit" in text:
        payment_type = "Nakit"
    elif "KART" in text or "KREDI" in text:
        payment_type = "Kredi Kartı"
    else:
        payment_type = "Bilinmiyor"

    # 3️⃣ KDV oranını bul (örnek: KDV %8, %18)
    kdv_match = re.search(r'KDV\s*[%]?\s*([0-9]+)', text)
    kdv = int(kdv_match.group(1)) if kdv_match else None

    # 4️⃣ Kategori belirleme (basitleştirilmiş mantık)
    if any(word in text for word in ["SATIŞ", "TAHSİLAT", "GELİR"]):
        category = "Gelir"
    elif any(word in text for word in ["GİDER", "ÜRÜN", "MALZEME", "FATURA", "TOPLAM", "KDV"]):
        category = "Gider"
    else:
        category = "Bilinmiyor"

    return {
        "tutar": amount,
        "odeme_tipi": payment_type,
        "kdv_orani": kdv,
        "kategori": category
    }
