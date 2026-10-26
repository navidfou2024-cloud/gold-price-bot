
import os
import asyncio
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Bot

BOT_TOKEN = os.environ["BOT_TOKEN"]
USER_CHAT_ID = os.environ["USER_CHAT_ID"]

TEHRAN = ZoneInfo("Asia/Tehran")
API_BASE = "https://api.priceto.day/v1/latest/irr"

# وزن یک انس تروا بر حسب گرم
TROY_OUNCE_GRAMS = 31.1034768


def get_price(symbol):
    try:
        response = requests.get(
            f"{API_BASE}/{symbol}",
            timeout=15,
            headers={
                "Accept": "application/json",
                "User-Agent": "GoldPriceBot/1.0"
            }
        )

        if response.status_code != 200:
            print(f"API error for {symbol}: HTTP {response.status_code}")
            return None

        try:
            data = response.json()
        except ValueError:
            print(f"Invalid JSON for {symbol}: {response.text[:200]}")
            return None

        if not data.get("success") or data.get("price") is None:
            print(f"Price unavailable for {symbol}")
            return None

        # API قیمت را به ریال برمی‌گرداند؛ تبدیل به تومان
        return float(data["price"]) / 10

    except (requests.RequestException, ValueError, TypeError) as error:
        print(f"Error for {symbol}: {error}")
        return None


def format_toman(value):
    if value is None:
        return "فعلاً ناموجود"
    return f"{value:,.0f}"


def format_usd(value):
    if value is None:
        return "فعلاً ناموجود"
    return f"{value:,.2f}"


def build_message():
    gold18 = get_price("gold-18k")
    gold24 = get_price("gold-24k")
    ounce_gold_toman = get_price("gold-ounce")
    ounce_silver_toman = get_price("silver-ounce")
    dollar = get_price("usd")
    tether = get_price("tether")

    # تبدیل ارزش تومانی انس به دلار
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

    # برآورد قیمت هر گرم نقره ۹۲۵ بر اساس انس جهانی
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


async def main():
    message = build_message()

    async with Bot(token=BOT_TOKEN) as bot:
        await bot.send_message(
            chat_id=int(USER_CHAT_ID),
            text=message,
            disable_web_page_preview=True
        )

    print("Private message sent successfully.")


if __name__ == "__main__":
    asyncio.run(main())
