import os
import asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, idle

# --- KEEP ALIVE ---
web = Flask('')
@web.route('/')
def home(): return "Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host='0.0.0.0', port=port)

# --- BOT CONFIG ---
# Variables ko try-except mein rakha hai taki crash na ho
try:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
except:
    print("❌ Error: API_ID or other variables missing!")

app = Client("linkvilla_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- SIMPLE STARTUP ---
async def start_bot():
    print("🚀 Starting Web Server...")
    Thread(target=run_web, daemon=True).start()
    
    print("🤖 Starting Telegram Bot...")
    await app.start()
    print("✅ BOT IS LIVE AND RUNNING!")
    await idle()

if __name__ == "__main__":
    # Naye Python versions ke liye sabse best startup logic
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())
