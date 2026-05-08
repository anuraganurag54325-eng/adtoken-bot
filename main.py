import os
import asyncio
from threading import Thread

from flask import Flask
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

# =========================================================
# WEB SERVER (Railway Health Check)
# =========================================================

web = Flask(__name__)

@web.route("/")
def home():
    return "Link Haveli Bot Running ✅"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host="0.0.0.0", port=port)

# =========================================================
# CONFIG
# =========================================================

API_ID = int(os.environ.get("API_ID", "26279930"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")

MONGO_URI = os.environ.get("MONGO_URI", "")

raw_channel = os.environ.get("CHANNEL_USERNAME", "linkvillaadmin")
CHANNEL_USERNAME = raw_channel if raw_channel.startswith("@") else f"@{raw_channel}"

OWNER_ID = int(os.environ.get("OWNER_ID", "7422529128"))

# =========================================================
# BOT
# =========================================================

app = Client(
    "linkhaveli_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# =========================================================
# DATABASE
# =========================================================

mongo = None
users_db = None

if MONGO_URI.strip():
    try:
        mongo = AsyncIOMotorClient(MONGO_URI)
        db = mongo["linkhaveli_db"]
        users_db = db["users"]
        print("✅ MongoDB Connected")
    except Exception as e:
        print("❌ MongoDB Error:", e)
else:
    print("⚠️ Mongo URI Not Found")

# =========================================================
# FORCE JOIN CHECK
# =========================================================

async def check_join(client, user_id):
    try:
        member = await client.get_chat_member(CHANNEL_USERNAME, user_id)

        if member.status in [
            "member",
            "administrator",
            "creator",
            "restricted"
        ]:
            return True

        return False

    except Exception as e:
        print("Force Join Error:", e)
        return False

# =========================================================
# START COMMAND
# =========================================================

@app.on_message(filters.command("start"))
async def start_cmd(client, message):

    user_id = message.from_user.id

    # Save User
    try:
        if users_db:
            await users_db.update_one(
                {"user_id": user_id},
                {"$set": {"user_id": user_id}},
                upsert=True
            )
    except Exception as e:
        print("User Save Error:", e)

    # Force Join
    joined = await check_join(client, user_id)

    if not joined:

        join_link = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"

        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📢 Join Channel",
                        url=join_link
                    )
                ]
            ]
        )

        await message.reply_text(
            f"🚀 First Join Our Channel\n\n{CHANNEL_USERNAME}",
            reply_markup=buttons
        )

        return

    # Success Message
    await message.reply_text(
        "✅ Bot Working Successfully!"
    )

# =========================================================
# PING COMMAND
# =========================================================

@app.on_message(filters.command("ping"))
async def ping_cmd(client, message):
    await message.reply_text("🏓 Pong!")

# =========================================================
# ERROR HANDLER
# =========================================================

@app.on_message(filters.private)
async def all_private(client, message):
    try:
        print(
            f"Message From {message.from_user.id}: "
            f"{message.text}"
        )
    except:
        pass

# =========================================================
# MAIN
# =========================================================

async def main():

    Thread(target=run_web, daemon=True).start()

    await app.start()

    me = await app.get_me()

    print("===================================")
    print(f"🚀 Bot Started : @{me.username}")
    print("===================================")

    await idle()

    await app.stop()

# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
