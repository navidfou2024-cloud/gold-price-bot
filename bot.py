
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


def get_price(symbol: str):
    url = f"{API_BASE}/{symbol}"

    try:
        response = requests.get(
            url,
            timeout=15,
            headers={"Accept": "application/json",
                     "User-Agent": "GoldPriceBot/1.0"}
        )

        if response.status_code != 200:
            print(f"API error for {symbol}: HTTP {response.status_code}")
            print(response.text[:300])
            return None

        try:
            data = response.json()
        except ValueError:
            print(f"Invalid JSON for {symbol}.")
            print("Content-Type:", response.headers.get("Content-Type"))
            print("Response:", repr(response.text[:300]))
            return None

        if not data.get("success") or data.get("price") is None:
            print(f"Price unavailable for {symbol}: {data}")
            return None

        price = float(data["price"])

        # API values are assumed to be in IRR.
        # Convert rial to toman.
        return f"{price / 10:,.0f}"

    except requests.RequestException as error:
        print(f"Network error for {symbol}: {error}")
        return None


def format_price(value):
    return value if value is not None else "فعلاً ناموجود"


def build_message():
    gold18 = get_price("gold-18k")
    gold24 = get_price("gold-24k")
    ounce_gold = get_price("gold-ounce")
    ounce_silver = get_price("silver-ounce")
    dollar = get_price("usd")
    tether = get_price("tether")

    now = datetime.now(TEHRAN).strftime("%Y/%m/%d - %H:%M")

    return f"""📊 قیمت‌های بازار
🕐 {now} - به وقت تهران

🟡 طلای ۱۸ عیار: {format_price(gold18)} تومان
🟡 طلای ۲۴ عیار: {format_price(gold24)} تومان
🌍 انس جهانی طلا: {format_price(ounce_gold)} دلار
⚪ انس جهانی نقره: {format_price(ounce_silver)} دلار

💵 دلار: {format_price(dollar)} تومان
💎 تتر: {format_price(tether)} تومان

منبع API: priceto.day"""


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
