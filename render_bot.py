import os
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

TEHRAN = ZoneInfo("Asia/Tehran")
PRICE_API_BASE = "https://api.priceto.day/v1/latest/irr"
TROY_OUNCE_GRAMS = 31.1034768
HTTP = requests.Session()
HTTP.headers.update({
    "Accept": "application/json",
    "User-Agent": "GoldPriceBot/2.0",
})


def log(message):
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    tehran_now = datetime.now(TEHRAN).strftime("%Y-%m-%d %H:%M:%S Tehran")
    print(f"[{utc_now} | {tehran_now}] {message}", flush=True)


def request_json(url, *, method="GET", json_body=None, timeout=20):
    last_error = None
    for attempt in range(1, 4):
        try:
            response = HTTP.request(
                method, url, json=json_body, timeout=timeout
            )
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError as exc:
                raise RuntimeError(
                    f"Server returned non-JSON response (HTTP {response.status_code})"
                ) from exc
            return data
        except (requests.RequestException, RuntimeError) as exc:
            last_error = exc
            log(f"Request attempt {attempt}/3 failed: {exc}")
            if attempt < 3:
                time.sleep(attempt * 2)
    raise RuntimeError(f"Request failed after 3 attempts: {last_error}")


def get_price(symbol):
    data = request_json(f"{PRICE_API_BASE}/{symbol}")
    if not isinstance(data, dict) or not data.get("success") or data.get("price") is None:
        raise RuntimeError(f"Price unavailable for symbol: {symbol}")
    value = float(data["price"]) / 10  # API returns rial; message uses toman.
    if value <= 0:
        raise RuntimeError(f"Invalid price for symbol: {symbol}")
    return value


def format_toman(value):
    return "فعلاً ناموجود" if value is None else f"{value:,.0f}"


def format_usd(value):
    return "فعلاً ناموجود" if value is None else f"{value:,.2f}"


def build_message():
    symbols = (
        "gold-18k", "gold-24k", "gold-ounce",
        "silver-ounce", "usd", "tether",
    )
    prices = {}
    errors = []

    # Fetch each symbol once; a failed field is reported as unavailable,
    # while the other prices are still sent to both platforms.
    for symbol in symbols:
        try:
            prices[symbol] = get_price(symbol)
            log(f"Price retrieved: {symbol}")
        except Exception as exc:
            prices[symbol] = None
            errors.append(symbol)
            log(f"Price unavailable for {symbol}: {exc}")

    dollar = prices["usd"]
    gold_ounce_usd = (
        prices["gold-ounce"] / dollar
        if prices["gold-ounce"] is not None and dollar
        else None
    )
    silver_ounce_usd = (
        prices["silver-ounce"] / dollar
        if prices["silver-ounce"] is not None and dollar
        else None
    )
    silver_925 = (
        prices["silver-ounce"] / TROY_OUNCE_GRAMS * 0.925
        if prices["silver-ounce"] is not None
        else None
    )

    snapshot_time = datetime.now(TEHRAN).strftime("%Y/%m/%d - %H:%M:%S")
    message = f"""📊 قیمت‌های بازار
🕐 {snapshot_time} - به وقت تهران

🟡 طلای ۱۸ عیار: {format_toman(prices["gold-18k"])} تومان
🟡 طلای ۲۴ عیار: {format_toman(prices["gold-24k"])} تومان

🌍 انس جهانی طلا: {format_usd(gold_ounce_usd)} دلار
⚪ انس جهانی نقره: {format_usd(silver_ounce_usd)} دلار

🥈 نقره ۹۲۵ (هر گرم): {format_toman(silver_925)} تومان

💵 دلار: {format_toman(dollar)} تومان
💎 تتر: {format_toman(prices["tether"])} تومان"""

    if errors:
        log("Warning: one or more prices were unavailable: " + ", ".join(errors))
    return message


def send_telegram(message):
    token = os.environ.get("BOT_TOKEN", "").strip()
    chat_id = os.environ.get("USER_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("Missing required Telegram environment variables")

    data = request_json(
        f"https://api.telegram.org/bot{token}/sendMessage",
        method="POST",
        json_body={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True,
        },
        timeout=25,
    )
    if not data.get("ok"):
        raise RuntimeError("Telegram API rejected the message")
    log("Telegram message sent successfully.")


def send_bale(message):
    token = os.environ.get("BALE_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("BALE_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("Missing required Bale environment variables")

    data = request_json(
        f"https://tapi.bale.ai/bot{token}/sendMessage",
        method="POST",
        json_body={"chat_id": chat_id, "text": message},
        timeout=25,
    )
    if not data.get("ok"):
        raise RuntimeError("Bale API rejected the message")
    log("Bale message sent successfully.")


def main():
    log("Scheduled price run started.")
    message = build_message()
    failures = []

    # Send independently so a failure on one platform doesn't block the other.
    for platform, sender in (("Telegram", send_telegram), ("Bale", send_bale)):
        try:
            sender(message)
        except Exception as exc:
            failures.append(platform)
            log(f"{platform} delivery failed: {exc}")

    if failures:
        log("Run finished with delivery failures: " + ", ".join(failures))
        sys.exit(1)

    log("Run finished successfully; both platforms accepted the message.")


if __name__ == "__main__":
    main()
