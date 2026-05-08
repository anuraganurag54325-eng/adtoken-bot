import os, asyncio, time, random, string, qrcode
from io import BytesIO
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

# --- KEEP-ALIVE (Railway Health Check) ---
web = Flask('')
@web.route('/')
def home(): return "Link Haveli is Live!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host='0.0.0.0', port=port)

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URI = os.environ.get("MONGO_URI", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 7422529128))

# Channel Username Auto-Fix logic
raw_channel = os.environ.get("CHANNEL_USERNAME", "linkvillaadmin")
CHANNEL_USERNAME = f"@{raw_channel}" if not raw_channel.startswith("@") else raw_channel

UPI_ID = os.environ.get("UPI_ID", "anuragjaat992@ibl")
BACKUP_LINK = os.environ.get("BACKUP_LINK", "https://t.me/+yvfe10wEbaJhZTM1")
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

async def auto_delete(message):
    await asyncio.sleep(300) # 5 Minutes
    try: await message.delete()
    except: pass

# --- HANDLERS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    await users_db.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)
    
    # Force Join Check
    if not await check_join(client, user_id):
        join_url = f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"
        await message.reply_text(
            f"🚀 **To use this bot, you must join our channel:**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=join_url)]])
        )
        return

    if len(message.command) < 2:
        await message.reply_text(f"👋 Welcome to **Link Haveli**!\nStatus: Active ✅")
        return

    name = message.command[1].lower()
    data = await videos.find_one({"name": name})
    if not data:
        await message.reply_text("❌ Link Expired or Invalid!")
        return

    user_p = await premium_users.find_one({"user_id": user_id})
    if user_p and user_p["expiry"] > int(time.time()):
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("Join Backup Channel ↗️", url=BACKUP_LINK)]])
        m = await message.reply_video(data["file_id"], protect_content=True, reply_markup=markup)
        warn = await message.reply_text("⚠️ Video 5 minute mein delete ho jayegi!")
        asyncio.create_task(auto_delete(m))
        asyncio.create_task(auto_delete(warn))
    else:
        await message.reply_photo(photo=PREMIUM_PIC, caption="💎 Premium Required to access this link!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 SUBSCRIBE 💎", callback_data="premium")]]))

@app.on_callback_query()
async def cb(client, query):
    if query.data == "premium":
        btns = [[InlineKeyboardButton("30 Days - ₹172", callback_data="buy_30d")], [InlineKeyboardButton("1 Year - ₹493", callback_data="buy_365d")]]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(btns))
    elif query.data.startswith("buy_"):
        days = query.data.split("_")[1]
        price = "172" if "30" in days else "493"
        pid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        qr = qrcode.make(f"upi://pay?pa={UPI_ID}&pn=LinkHaveli&am={price}&cu=INR&tn={pid}")
        bio = BytesIO(); bio.name = "pay.png"; qr.save(bio, "PNG"); bio.seek(0)
        await query.message.reply_photo(photo=bio, caption=f"Plan: {days}\nAmount: ₹{price}\n\n`/verify {pid} UTR_NO`")
    await query.answer()

# --- ADMIN COMMANDS ---
@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def add_video(client, message):
    if not message.reply_to_message or not message.reply_to_message.video:
        await message.reply_text("❌ Video ko reply karke `/add name` likho")
        return
    name = message.command[1].lower()
    fid = message.reply_to_message.video.file_id
    await videos.update_one({"name": name}, {"$set": {"file_id": fid}}, upsert=True)
    bot = await client.get_me()
    await message.reply_text(f"✅ Link Created:\nhttps://t.me/{bot.username}?start={name}")

# --- STARTUP ---
async def start_services():
    Thread(target=run_web, daemon=True).start()
    await app.start()
    print(f"🚀 BOT IS LIVE: @{app.me.username}")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(start_services())
