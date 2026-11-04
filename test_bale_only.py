from send_prices import build_message, send_bale


def main():
    # Build one price snapshot and test Bale only; Telegram is not called.
    message = build_message()
    send_bale(message)


if __name__ == "__main__":
    main()
