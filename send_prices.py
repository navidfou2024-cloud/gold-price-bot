import asyncio
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from telegram import Bot

TEHRAN = ZoneInfo("Asia/Tehran")
PRICE_API_BASE = "https://api.priceto.day/v1/latest/irr"
BALE_API_BASE = "https://tapi.bale.ai"


def get_price(symbol):
    """Fetch a price in rial and convert it to toman."""
    try:
        response = requests.get(
            f"{PRICE_API_BASE}/{symbol}",
            timeout=15,
            headers={"Accept": "application/json", "User-Agent": "GoldPriceBot/1.0"},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success") or data.get("price") is None:
            print(f"Price unavailable for {symbol}")
            return None
        return float(data["price"]) / 10
    except (requests.RequestException, ValueError, TypeError) as error:
        print(f"Price fetch failed for {symbol}: {type(error).__name__}: {error}")
        return None


def format_toman(value):
    return "فعلاً ناموجود" if value is None else f"{value:,.0f}"


def format_usd(value):
    return "فعلاً ناموجود" if value is None else f"{value:,.2f}"


def build_message():
    # Fetch each price once so both apps receive the same snapshot.
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
        ounce_silver_toman / 31.1034768 * 0.925
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


async def send_telegram(message):
    token = os.environ["BOT_TOKEN"].strip()
    private_chat_id = os.environ["USER_CHAT_ID"].strip()
    channel_chat_id = os.environ["TELEGRAM_CHANNEL_CHAT_ID"].strip()
    second_channel_chat_id = os.getenv("TELEGRAM_CHANNEL_2_CHAT_ID", "").strip()

    # Deliver independently to every configured Telegram destination.
    destinations = [
        ("private chat", private_chat_id),
        ("Telegram channel 1", channel_chat_id),
    ]
    if second_channel_chat_id:
        destinations.append(("Telegram channel 2", second_channel_chat_id))
    errors = []
    async with Bot(token=token) as bot:
        for destination_name, chat_id in destinations:
            try:
                await bot.send_message(
                    chat_id=int(chat_id),
                    text=message,
                    disable_web_page_preview=True,
                )
                print(f"Telegram {destination_name}: message sent successfully.")
            except Exception as error:
                print(
                    f"Telegram {destination_name} send failed: "
                    f"{type(error).__name__}: {error}"
                )
                errors.append(destination_name)

    if errors:
        raise RuntimeError(
            "Telegram delivery failed for: " + ", ".join(errors)
        )


def send_bale(message):
    token = os.environ["BALE_BOT_TOKEN"].strip()
    private_chat_id = os.environ["BALE_CHAT_ID"].strip()
    channel_1_chat_id = os.getenv("BALE_CHANNEL_CHAT_ID", "").strip()
    channel_2_chat_id = os.getenv("BALE_CHANNEL_2_CHAT_ID", "").strip()

    destinations = [("private chat", private_chat_id)]
    if channel_1_chat_id:
        destinations.append(("Bale channel 1", channel_1_chat_id))
    if channel_2_chat_id:
        destinations.append(("Bale channel 2", channel_2_chat_id))

    errors = []
    for destination_name, chat_id in destinations:
        try:
            response = requests.post(
                f"{BALE_API_BASE}/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message},
                timeout=20,
            )
            response.raise_for_status()
            try:
                result = response.json()
            except ValueError as error:
                raise RuntimeError("Bale returned a non-JSON response") from error
            if not result.get("ok", False):
                raise RuntimeError("Bale API did not confirm message delivery")
            print(f"Bale {destination_name}: message sent successfully.")
        except Exception as error:
            print(
                f"Bale {destination_name} send failed: "
                f"{type(error).__name__}: {error}"
            )
            errors.append(destination_name)

    if errors:
        raise RuntimeError("Bale delivery failed for: " + ", ".join(errors))


async def main():
    message = build_message()
    errors = []

    # Attempt both destinations even if one of them fails.
    try:
        await send_telegram(message)
    except Exception as error:
        print(f"Telegram send failed: {type(error).__name__}: {error}")
        errors.append("Telegram")

    try:
        send_bale(message)
    except Exception as error:
        print(f"Bale send failed: {type(error).__name__}: {error}")
        errors.append("Bale")

    if errors:
        raise RuntimeError("Message delivery failed for: " + ", ".join(errors))


if __name__ == "__main__":
    asyncio.run(main())
