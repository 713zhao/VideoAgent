from __future__ import annotations
import os
import requests
from typing import Optional

def send_telegram_message(text: str, bot_token_env: str = "TELEGRAM_BOT_TOKEN", chat_id_env: str = "TELEGRAM_CHAT_ID") -> bool:
    """Send a plain text message via Telegram Bot API.

    Reads bot token and chat id from environment variables by default.
    Returns True on success, False otherwise.
    """
    bot_token = os.environ.get(bot_token_env, "")
    chat_id = os.environ.get(chat_id_env, "")

    if not bot_token or not chat_id:
        print(f"⚠️ Telegram not configured: set {bot_token_env} and {chat_id_env} environment variables")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": text})
        if resp.status_code == 200:
            print("✅ Telegram message sent")
            return True
        else:
            print(f"❌ Telegram send failed: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Telegram send exception: {e}")
        return False
