# nlp_utils.py
import re

DATE_PATTERNS = [
    r"\d{2}\.\d{2}\.\d{4}",
    r"\d{4}-\d{2}-\d{2}",
    r"\d{2}/\d{2}/\d{4}",
    r"\d{2}-\d{2}-\d{2,4}",
]

CURRENCY_PATTERN = r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)"
KDV_RATE_PATTERN = r"%\s*(\d{1,2})"
TOP_KDV_PATTERN = r"TOPKDV.*?(\d{1,3}[.,]\d{2})"

INCOME_KEYWORDS = ["tahsilat", "ödeme alındı", "satış", "gelir", "fatura"]
EXPENSE_KEYWORDS = ["gider", "alış", "malzeme", "kira", "ekmek", "market", "ürün"]


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

    clean_text = text.lower().replace("\n", " ").replace("\t", " ").strip()

    # Tarih
    for pattern in DATE_PATTERNS:
        m = re.search(pattern, clean_text)
        if m:
            result["tarih"] = m.group()
            break

    # Tutar (en büyük sayı)
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

    # KDV tutarı (TOPKDV satırı)
    top_kdv_match = re.search(TOP_KDV_PATTERN, clean_text)
    if top_kdv_match:
        try:
            result["kdv_tutari"] = float(
                top_kdv_match.group(1).replace(",", ".")
            )
        except:
            pass

    # Ürün KDV oranları
    kdv_rate_match = re.findall(KDV_RATE_PATTERN, clean_text)
    if kdv_rate_match:
        result["kdv_orani"] = max(kdv_rate_match)

    # Ödeme tipi
    if "nakit" in clean_text:
        result["odeme_tipi"] = "Nakit"
    elif "kredi kart" in clean_text or "visa" in clean_text or "mastercard" in clean_text:
        result["odeme_tipi"] = "Kredi Kartı"

    # Kategori
    if any(w in clean_text for w in INCOME_KEYWORDS):
        result["kategori"] = "Gelir"
    elif any(w in clean_text for w in EXPENSE_KEYWORDS):
        result["kategori"] = "Gider"
    else:
        result["kategori"] = "Bilinmiyor"

    # Satıcı adı (büyük harfler)
    satıcı = re.findall(r"[A-ZÇĞİÖŞÜ\s]{3,}", text)
    if satıcı:
        result["satıcı"] = satıcı[0].strip()

    return result
