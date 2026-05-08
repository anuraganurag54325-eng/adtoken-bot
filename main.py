import os, asyncio, random, string, qrcode, time
from io import BytesIO
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

# --- KEEP-ALIVE ---
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
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = 1853401283
CHANNEL_USERNAME = "@linkvillaadmin"
UPI_ID = "anuragjaat992@ibl"
PREMIUM_PIC = "https://i.ibb.co/3y2p7bFP/image.png"

app = Client("linkvilla_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["linkvilla_vfinal"]
videos, premium_users, users_db = db["videos"], db["premium"], db["users"]

# --- BOT LOGIC ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await users_db.update_one({"user_id": message.from_user.id}, {"$set": {"user_id": message.from_user.id}}, upsert=True)
    await message.reply_text("👋 Welcome! Bot is working perfectly.")

# --- STARTUP ---
async def start_services():
    # Start Web Server in Thread
    Thread(target=run_web, daemon=True).start()
    
    # Start Telegram Bot
    await app.start()
    print("✅ BOT STARTED SUCCESSFULLY!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(start_services())
    except RuntimeError:
        # If loop is already running, use this
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_services())
