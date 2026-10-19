import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Bot
import asyncio
import os

# ----------------- تنظیمات -----------------
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
TEHRAN = ZoneInfo("Asia/Tehran")
# ------------------------------------------

def get_price(symbol: str) -> str:
    try:
        url = f"https://api.priceto.day/v1/latest/irr/{symbol}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("success"):
            price = data["price"]
            toman = price // 10
            return f"{toman:,}"
        return "---"
    except Exception as e:
        print(f"خطا در گرفتن {symbol}: {e}")
        return "---"

def build_message() -> str:
    gold18 = get_price("gold-18k")
    gold24 = get_price("gold-24k")
    ounce_gold = get_price("gold-ounce")
    ounce_silver = get_price("silver-ounce")
    dollar = get_price("usd")
    tether = get_price("tether")

    now = datetime.now(TEHRAN).strftime("%Y/%m/%d - %H:%M")

    msg = f"""📊 قیمت‌های لحظه‌ای بازار
🕐 {now}

🟡 طلای ۱۸ عیار: {gold18} تومان
🟡 طلای ۲۴ عیار: {gold24} تومان
🌍 انس جهانی طلا: {ounce_gold} دلار
⚪️ انس جهانی نقره: {ounce_silver} دلار

💵 دلار: {dollar} تومان
💎 تتر: {tether} تومان

منبع: tgju.org"""
    return msg

async def main():
    bot = Bot(token=BOT_TOKEN)
    message = build_message()
    await bot.send_message(chat_id=CHANNEL_ID, text=message, disable_web_page_preview=True)
    print("پیام با موفقیت ارسال شد")

if __name__ == "__main__":
    asyncio.run(main())
