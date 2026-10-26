import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

BALE_BOT_TOKEN = os.environ["BALE_BOT_TOKEN"]
BALE_CHAT_ID = os.environ["BALE_CHAT_ID"]

BALE_API_BASE = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}"
PRICE_API_BASE = "https://api.priceto.day/v1/latest/irr"
TEHRAN = ZoneInfo("Asia/Tehran")
TROY_OUNCE_GRAMS = 31.1034768


def get_price(symbol):
    try:
        response = requests.get(
            f"{PRICE_API_BASE}/{symbol}",
            timeout=15,
            headers={
                "Accept": "application/json",
                "User-Agent": "GoldPriceBot/1.0",
            },
        )

        if response.status_code != 200:
            print(f"Price API error for {symbol}: HTTP {response.status_code}")
            return None

        try:
            data = response.json()
        except ValueError:
            print(f"Invalid JSON for {symbol}: {response.text[:200]}")
            return None

        if not data.get("success") or data.get("price") is None:
            print(f"Price unavailable for {symbol}")
            return None

        # The price API returns rial; convert to toman, matching the Telegram bot.
        return float(data["price"]) / 10

    except (requests.RequestException, ValueError, TypeError) as error:
        print(f"Error for {symbol}: {error}")
        return None


def format_toman(value):
    return "فعلاً ناموجود" if value is None else f"{value:,.0f}"


def format_usd(value):
    return "فعلاً ناموجود" if value is None else f"{value:,.2f}"


def build_message():
    gold18 = get_price("gold-18k")
    gold24 = get_price("gold-24k")
    ounce_gold_toman = get_price("gold-ounce")
    ounce_silver_toman = get_price("silver-ounce")
    dollar = get_price("usd")
    tether = get_price("tether")

    ounce_gold_usd = (
        ounce_gold_toman / dollar
        if ounce_gold_toman is not None and dollar
        else None
    )
    ounce_silver_usd = (
        ounce_silver_toman / dollar
        if ounce_silver_toman is not None and dollar
        else None
    )
    silver925 = (
        ounce_silver_toman / TROY_OUNCE_GRAMS * 0.925
        if ounce_silver_toman is not None
        else None
    )

    now = datetime.now(TEHRAN).strftime("%Y/%m/%d - %H:%M")

    return f"""📊 قیمت‌های بازار
🕐 {now} - به وقت تهران

🟡 طلای ۱۸ عیار: {format_toman(gold18)} تومان
🟡 طلای ۲۴ عیار: {format_toman(gold24)} تومان

🌍 انس جهانی طلا: {format_usd(ounce_gold_usd)} دلار
⚪ انس جهانی نقره: {format_usd(ounce_silver_usd)} دلار

🥈 نقره ۹۲۵ (هر گرم): {format_toman(silver925)} تومان

💵 دلار: {format_toman(dollar)} تومان
💎 تتر: {format_toman(tether)} تومان"""


def main():
    message = build_message()
    response = requests.post(
        f"{BALE_API_BASE}/sendMessage",
        json={"chat_id": BALE_CHAT_ID, "text": message},
        timeout=20,
    )
    response.raise_for_status()

    try:
        result = response.json()
    except ValueError as error:
        raise RuntimeError(f"Bale returned a non-JSON response: {response.text[:200]}") from error

    if not result.get("ok", False):
        raise RuntimeError(f"Bale API rejected the message: {result}")

    print("Private Bale message sent successfully.")


if __name__ == "__main__":
    main()
