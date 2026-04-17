import json
import os
from urllib import error, request
from dotenv import load_dotenv


load_dotenv()


def build_financial_prompt(
    *,
    period: str,
    start_date: str,
    end_date: str,
    total_income: float,
    total_expense: float,
    net: float,
    forecast_next_expense: float | None,
) -> str:
    trend_hint = (
        f"Tahmini bir sonraki ay gider: {forecast_next_expense:.2f} TL"
        if forecast_next_expense is not None
        else "Tahmini bir sonraki ay gider: Veri yetersiz"
    )

    return (
        "Sen bir finansal analiz asistanisin. Asagidaki verileri kisa, net ve eyleme donuk sekilde yorumla. "
        "Yaniti Turkce ver. Abartili ifade kullanma. 3-5 cumle ile sinirli kal.\n\n"
        f"Donem: {period}\n"
        f"Baslangic: {start_date}\n"
        f"Bitis: {end_date}\n"
        f"Toplam gelir: {total_income:.2f} TL\n"
        f"Toplam gider: {total_expense:.2f} TL\n"
        f"Net sonuc: {net:.2f} TL\n"
        f"{trend_hint}\n\n"
        "Istenen cikti bicimi:\n"
        "1) Kisa durum ozeti\n"
        "2) Olasi risk/uyari\n"
        "3) Tek bir somut onerilen aksiyon"
    )


def _local_fallback_commentary(
    *,
    total_income: float,
    total_expense: float,
    net: float,
    forecast_next_expense: float | None,
) -> str:
    if total_income <= 0 and total_expense <= 0:
        return (
            "Bu donemde yeterli finansal hareket gorunmuyor. "
            "Duzenli kayit girildikce sistem daha guvenilir yorum uretecektir. "
            "Oncelik olarak gelir ve gider kayitlarinizi duzenli ekleyin."
        )

    expense_ratio = (total_expense / total_income) if total_income > 0 else None

    status = "Gelir-gider dengesi su an genel olarak olumlu gorunuyor."
    risk = "Kisa vadede belirgin bir risk sinyali yok."
    action = "Aylik butce hedefi belirleyip sapmalari haftalik izleyin."

    if net < 0:
        status = "Bu donemde giderler gelirlerin uzerine cikmis gorunuyor."
        risk = "Mevcut trend devam ederse nakit akisinda baski olusabilir."
        action = "Degisken gider kalemlerinde en yuksek 3 kalemi azaltma plani yapin."
    elif expense_ratio is not None and expense_ratio > 0.85:
        status = "Gelir-gider dengesi sinirda ilerliyor."
        risk = "Giderlerin kucuk bir artisinda net kar hizla azalabilir."
        action = "Sabit giderleri gozden gecirip en az %5 tasarruf hedefleyin."

    if forecast_next_expense is not None and total_expense > 0:
        if forecast_next_expense > (total_expense * 1.15):
            risk = "Tahmine gore onumuzdeki donemde giderlerde artis riski bulunuyor."
            action = "Erken onlem icin yuksek tutarli giderleri onceleyen bir limit plani uygulayin."

    return f"{status} {risk} {action}"


def generate_financial_insight(
    *,
    period: str,
    start_date: str,
    end_date: str,
    total_income: float,
    total_expense: float,
    net: float,
    forecast_next_expense: float | None,
) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        return {
            "insight_text": _local_fallback_commentary(
                total_income=total_income,
                total_expense=total_expense,
                net=net,
                forecast_next_expense=forecast_next_expense,
            ),
            "insight_source": "rule-based-fallback",
            "model_used": None,
        }

    prompt = build_financial_prompt(
        period=period,
        start_date=start_date,
        end_date=end_date,
        total_income=total_income,
        total_expense=total_expense,
        net=net,
        forecast_next_expense=forecast_next_expense,
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "KOBI odakli finansal yorum yapan dikkatli bir asistansin.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 220,
    }

    try:
        req = request.Request(
            url=f"{base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            if not text:
                raise ValueError("Empty LLM response")

            return {
                "insight_text": text,
                "insight_source": "llm",
                "model_used": model,
            }
    except (error.URLError, error.HTTPError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
        return {
            "insight_text": _local_fallback_commentary(
                total_income=total_income,
                total_expense=total_expense,
                net=net,
                forecast_next_expense=forecast_next_expense,
            ),
            "insight_source": "rule-based-fallback",
            "model_used": None,
        }
