import os, asyncio, time, random, string, qrcode
from io import BytesIO
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

# --- WEB SERVER (For Railway Health) ---
web = Flask('')
@web.route('/')
def home(): return "Link Haveli is Online!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host='0.0.0.0', port=port)

# --- CONFIG (Hardcoded for direct connection) ---
API_ID = int(os.environ.get("API_ID", 26279930)) # Apna API_ID variable se lega
API_HASH = os.environ.get("API_HASH", "774900a3f81e39a3f2b435b8004f213b") # API_HASH variable se
BOT_TOKEN = "8684358051:AAEKmb3K1amES4LRIGn7nPf7_COTNi9P-78" # Naya Token Direct
MONGO_URI = os.environ.get("MONGO_URI", "") # MongoDB URI variable se

# Channel Username (Auto @ adder)
raw_ch = os.environ.get("CHANNEL_USERNAME", "linkvillaadmin")
CHANNEL_USERNAME = f"@{raw_ch}" if not raw_ch.startswith("@") else raw_ch

OWNER_ID = 7422529128 
UPI_ID = "anuragjaat992@ibl"
PREMIUM_PIC = "https://i.ibb.co/3y2p7bFP/image.png"

app = Client("linkhaveli_final", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["linkhaveli_db"]
videos, premium_users, users_db = db["videos"], db["premium"], db["users"]

# --- FUNCTIONS ---
async def check_join(client, user_id):
    try:
        await client.get_chat_member(CHANNEL_USERNAME, user_id)
        return True
    except: return False

# --- START COMMAND ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    # Add user to DB
    await users_db.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)
    
    # Check Force Join
    if not await check_join(client, user_id):
        join_url = f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"
        btn = [[InlineKeyboardButton("📢 Join Channel", url=join_url)]]
        await message.reply_text(
            f"🚀 **To use this bot, you must join our channel first!**",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    await message.reply_text(f"👋 Welcome to **Link Haveli**!\n\nBot is active and connected to {CHANNEL_USERNAME}")

# --- STARTUP ---
async def main():
    Thread(target=run_web, daemon=True).start()
    await app.start()
    print(f"🚀 BOT LIVE ON @linkhaveli")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
