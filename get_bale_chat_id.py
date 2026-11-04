import os
import requests

token = os.environ["BALE_BOT_TOKEN"].strip()
url = f"https://tapi.bale.ai/bot{token}/getUpdates"

response = requests.get(url, timeout=25)
response.raise_for_status()

try:
    data = response.json()
except ValueError as error:
    raise RuntimeError(f"Bale returned a non-JSON response: {response.text[:200]}") from error

if not data.get("ok", False):
    raise RuntimeError(f"Bale API error: {data}")

found_private = set()
found_channels = set()

for update in data.get("result", []):
    # Private chats arrive as message updates; channel posts may arrive
    # under channel_post or edited_channel_post.
    message = (
        update.get("message")
        or update.get("edited_message")
        or update.get("channel_post")
        or update.get("edited_channel_post")
    )
    if not message:
        continue

    message_text = message.get("text", "")
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    chat_type = chat.get("type")

    if chat_id is None:
        continue

    if chat_type == "private" and message_text.strip().startswith("/start"):
        found_private.add(str(chat_id))
    elif chat_type in {"channel", "supergroup", "group"}:
        found_channels.add((str(chat_id), str(chat_type), chat.get("title", "")))

if found_private:
    for chat_id in sorted(found_private):
        print(f"BALE_CHAT_ID={chat_id}")
else:
    print("No new private /start update found.")

if found_channels:
    for chat_id, chat_type, title in sorted(found_channels):
        print(f"Possible Bale channel/group destination: id={chat_id}, type={chat_type}, title={title}")
else:
    print("No channel/group post update found.")
    print("If the API does not expose channel posts, use the channel's public @username when available, or provide its ID through a supported admin/bot update.")
