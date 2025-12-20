import re

# Tarih formatları
DATE_PATTERNS = [
    r"\d{2}\.\d{2}\.\d{4}",      # 16.09.2022
    r"\d{2}/\d{2}/\d{4}",        # 16/09/2022
    r"\d{4}-\d{2}-\d{2}",        # 2022-09-16
    r"\d{2}-\d{2}-\d{2,4}",      # 16-09-22 / 16-09-2022
]

# 179,54 veya 1.200,50 gibi miktarlar
CURRENCY_PATTERN = r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)"

# %00, %01, %08, %18
KDV_RATE_PATTERN = r"%\s*(\d{1,2})"

# TOPKDV 0,38 / KDV TUTARI 0,38 gibi
TOP_KDV_PATTERN = r"(?:TOPKDV|TOP KDV|KDV TUTARI)[^\d]*(\d{1,3}[.,]\d{2})"

INCOME_KEYWORDS = ["tahsilat", "ödeme alındı", "satış", "gelir", "fatura"]
EXPENSE_KEYWORDS = ["gider", "alış", "malzeme", "kira", "ekmek", "market", "ürün"]


def analyze_invoice_text(text: str) -> dict:
    """
    OCR çıktısını analiz ederek tarih, satıcı, tutar, kdv, ödeme tipi, kategori gibi alanları döndürür.
    Dönen dict backend tarafından veritabanına yazılıyor.
    """
    result = {
        "tarih": None,
        "satıcı": None,
        "tutar": None,
        "odeme_tipi": None,
        "kdv_orani": None,
        "kdv_tutari": None,
        "kategori": None,
    }

    # Normalizasyon
    clean_text = text.lower().replace("\n", " ").replace("\t", " ").strip()

    # 🔹 Tarih bulma
    for pattern in DATE_PATTERNS:
        m = re.search(pattern, clean_text)
        if m:
            result["tarih"] = m.group()
            break

    # 🔹 Tutar (en büyük miktarı al)
    amounts = re.findall(CURRENCY_PATTERN, clean_text)
    if amounts:
        numbers = []
        for a in amounts:
            try:
                clean_a = a.replace(".", "").replace(",", ".")
                numbers.append(float(clean_a))
            except:
                pass
        if numbers:
            result["tutar"] = max(numbers)

    # 🔹 KDV TUTARI (TOPKDV satırı)
    kdv_total_match = re.search(TOP_KDV_PATTERN, clean_text)
    if kdv_total_match:
        try:
            result["kdv_tutari"] = float(kdv_total_match.group(1).replace(",", "."))
        except:
            pass

    # 🔹 KDV oranı (%00 %01 %08 vb.)
    kdv_rates = re.findall(KDV_RATE_PATTERN, clean_text)
    if kdv_rates:
        # En yüksek görünen oranı seç (genelde 18 veya 8)
        try:
            result["kdv_orani"] = max(int(r) for r in kdv_rates)
        except:
            result["kdv_orani"] = None

    # 🔹 Ödeme tipi
    if "nakit" in clean_text:
        result["odeme_tipi"] = "Nakit"
    elif "kredi kart" in clean_text or "visa" in clean_text or "mastercard" in clean_text:
        result["odeme_tipi"] = "Kredi Kartı"

    # 🔹 Kategori (gelir / gider)
    if any(w in clean_text for w in INCOME_KEYWORDS):
        result["kategori"] = "Gelir"
    elif any(w in clean_text for w in EXPENSE_KEYWORDS):
        result["kategori"] = "Gider"
    else:
        result["kategori"] = "Bilinmiyor"

    # 🔹 Satıcı adı (üst kısımdaki büyük harf satırlarını dene)
    # Orijinal metin üzerinden çalışalım
    possible_vendor = None
    for line in text.splitlines():
        line_stripped = line.strip()
        # Tamamen büyük harf + Türkçe karakter + boşluk
        if re.fullmatch(r"[A-ZÇĞİÖŞÜ0-9\s\.\-]{3,}", line_stripped):
            # Bazı gereksiz kelimeleri ele
            if not any(k in line_stripped for k in ["FİŞ", "TARİH", "SAAT", "VD.", "V.D.", "VERGİ", "NO"]):
                possible_vendor = line_stripped
                break

    result["satıcı"] = possible_vendor

    return result
