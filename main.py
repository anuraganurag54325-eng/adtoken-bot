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
def home(): return "LinkVilla Active!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host='0.0.0.0', port=port)

# --- CONFIG (Railway Variables se lega) ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URI = os.environ.get("MONGO_URI", "")

# Ye niche wali values ab aap Railway Variables mein daalna
OWNER_ID = int(os.environ.get("OWNER_ID", 7422529128))
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "@linkvillaadmin")
UPI_ID = os.environ.get("UPI_ID", "anuragjaat992@ibl")
BACKUP_LINK = os.environ.get("BACKUP_LINK", "https://t.me/+yvfe10wEbaJhZTM1")
PREMIUM_PIC = "https://i.ibb.co/3y2p7bFP/image.png"

app = Client("linkvilla", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["linkvilla_main"]
videos, premium_users, users_db = db["videos"], db["premium"], db["users"]

app.batch_data = {}

async def check_join(client, user_id):
    try:
        await client.get_chat_member(CHANNEL_USERNAME, user_id)
        return True
    except: return False

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    await users_db.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)
    
    # Force Join Check
    if not await check_join(client, user_id):
        await message.reply_text(
            f"🚀 **To use this bot, you must join our channel:**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")]])
        )
        return

    if len(message.command) < 2:
        await message.reply_text("👋 Welcome to **LinkVilla Premium Bot**!")
        return
    
    # Video Link Logic... (Baki code wahi rahega)
    await message.reply_text("🔎 Finding your link...")

# (Add baki admin commands here jo pehle diye the)

async def start_services():
    Thread(target=run_web, daemon=True).start()
    await app.start()
    print(f"🚀 BOT STARTED! Channel: {CHANNEL_USERNAME}")
    await idle()

if __name__ == "__main__":
    asyncio.run(start_services())
