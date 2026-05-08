import os, asyncio, time
from flask import Flask
from threading import Thread
from pyrogram import Client, idle

# --- KEEP ALIVE ---
web = Flask('')
@web.route('/')
def home(): return "Bot is Online!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host='0.0.0.0', port=port)

# --- CONFIG ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("linkvilla_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def start_bot():
    Thread(target=run_web, daemon=True).start()
    await app.start()
    print("✅ BOT IS LIVE!")
    await idle()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
