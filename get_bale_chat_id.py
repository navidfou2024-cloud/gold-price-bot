import os
import requests

token = os.environ["BALE_BOT_TOKEN"]
url = f"https://tapi.bale.ai/bot{token}/getUpdates"

response = requests.get(url, timeout=25)
response.raise_for_status()

try:
    data = response.json()
except ValueError as error:
    raise RuntimeError(f"Bale returned a non-JSON response: {response.text[:200]}") from error

if not data.get("ok", False):
    raise RuntimeError(f"Bale API error: {data}")

found = set()
for update in data.get("result", []):
    message = update.get("message") or update.get("edited_message")
    if not message:
        continue

    text = message.get("text", "")
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    chat_type = chat.get("type")

    if chat_id is not None and chat_type == "private" and text.strip().startswith("/start"):
        found.add(str(chat_id))

if found:
    for chat_id in sorted(found):
        print(f"BALE_CHAT_ID={chat_id}")
else:
    print("No private /start message found yet.")
    print("Open your Bale bot and send /start, then run this workflow again.")
