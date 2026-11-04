import asyncio

from send_prices import build_message, send_telegram


async def main():
    # Build one fresh snapshot and test only Telegram destinations.
    # Bale is intentionally excluded from this verification workflow.
    message = build_message()
    await send_telegram(message)


if __name__ == "__main__":
    asyncio.run(main())
