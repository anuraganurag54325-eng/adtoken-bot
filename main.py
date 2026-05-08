import os, asyncio, time
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- WEB SERVER ---
web = Flask('')
@web.route('/')
def home(): return "LinkVilla is Running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host='0.0.0.0', port=port)

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
# Yahan variable add kiya hai jo Railway se connect hoga
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "@linkvillaadmin")

app = Client("linkvilla_final", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    # Seedha check join logic
    user_id = message.from_user.id
    try:
        await client.get_chat_member(CHANNEL_USERNAME, user_id)
        await message.reply_text(f"👋 Welcome to LinkVilla!\nStatus: Active ✅")
    except:
        # Agar join nahi kiya hai toh ye button dikhayega
        btn = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")]]
        await message.reply_text(
            "🚀 **To use this bot, you must join our channel:**",
            reply_markup=InlineKeyboardMarkup(btn)
        )

async def main():
    Thread(target=run_web, daemon=True).start()
    await app.start()
    print(f"✅ BOT LIVE! Channel: {CHANNEL_USERNAME}")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
