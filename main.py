import os, asyncio, time, random, string, qrcode
from io import BytesIO
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

# --- KEEP-ALIVE ---
web = Flask('')
@web.route('/')
def home(): return "LinkVilla Live!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host='0.0.0.0', port=port)

# --- CONFIG ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = 1853401283
UPI_ID = "anuragjaat992@ibl"
CHANNEL_USERNAME = "@linkvillaadmin"
PREMIUM_PIC = "https://i.ibb.co/3y2p7bFP/image.png"

# --- BOT CLIENT ---
app = Client("linkvilla_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["linkvilla_vfinal"]
videos, premium_users, users_db = db["videos"], db["premium"], db["users"]

# --- SIMPLE START COMMAND ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await users_db.update_one({"user_id": message.from_user.id}, {"$set": {"user_id": message.from_user.id}}, upsert=True)
    await message.reply_text("✅ Bot is Online and Working!")

# --- NEW STARTUP LOGIC FOR PYTHON 3.14+ ---
async def start_services():
    # 1. Start Web Server
    Thread(target=run_web, daemon=True).start()
    
    # 2. Start Bot
    await app.start()
    print("🚀 BOT STARTED SUCCESSFULLY!")
    
    # 3. Keep running
    await idle()
    await app.stop()

if __name__ == "__main__":
    try:
        # Render ke naye environment ke liye safest tarika
        asyncio.run(start_services())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Critical Error: {e}")
