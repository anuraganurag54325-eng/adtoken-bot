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
def home(): return "LinkVilla Railway is Live!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host='0.0.0.0', port=port)

# --- CONFIG ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = 7422529128  # Updated Owner ID
UPI_ID = "anuragjaat992@ibl"
CHANNEL_USERNAME = "@linkvillaadmin"
BACKUP_LINK = "https://t.me/+yvfe10wEbaJhZTM1"
PREMIUM_PIC = "https://i.ibb.co/3y2p7bFP/image.png"

app = Client("linkvilla_railway", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["linkvilla_railway_db"]
videos, premium_users, users_db = db["videos"], db["premium"], db["users"]

app.batch_data = {}

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
    await users_db.update_one({"user_id": message.from_user.id}, {"$set": {"user_id": message.from_user.id}}, upsert=True)
    if not await check_join(client, message.from_user.id):
        await message.reply_text(f"🚫 पहले channel join करो:\n\nhttps://t.me/{CHANNEL_USERNAME.replace('@','')}")
        return
    if len(message.command) < 2:
        await message.reply_text("👋 Welcome to **LinkVilla Premium Bot**!")
        return
    name = message.command[1].lower()
    data = await videos.find_one({"name": name})
    if not data:
        await message.reply_text("❌ Link Expired!")
        return
    user_p = await premium_users.find_one({"user_id": message.from_user.id})
    if user_p and user_p["expiry"] > int(time.time()):
        sent_msgs = []
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("Join Backup Channel ↗️", url=BACKUP_LINK)]])
        if data.get("type") == "batch":
            for f_id in data["file_ids"]:
                m = await message.reply_video(f_id, protect_content=True, reply_markup=markup)
                sent_msgs.append(m)
        else:
            m = await message.reply_video(data["file_id"], protect_content=True, reply_markup=markup)
            sent_msgs.append(m)
        warn = await message.reply_text("⚠️ Videos 5 minute mein delete ho jayengi!")
        for msg in sent_msgs: asyncio.create_task(auto_delete(msg))
        asyncio.create_task(auto_delete(warn))
    else:
        await message.reply_photo(photo=PREMIUM_PIC, caption="💎 Premium Required!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 SUBSCRIBE 💎", callback_data="premium")]]))

@app.on_callback_query()
async def cb(client, query):
    if query.data == "premium":
        btns = [[InlineKeyboardButton("30 Days - ₹172", callback_data="buy_30d")], [InlineKeyboardButton("1 Year - ₹493", callback_data="buy_365d")]]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(btns))
    elif query.data.startswith("buy_"):
        days = query.data.split("_")[1]
        price = "172" if "30" in days else "493"
        pid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        qr = qrcode.make(f"upi://pay?pa={UPI_ID}&pn=LinkVilla&am={price}&cu=INR&tn={pid}")
        bio = BytesIO(); bio.name = "pay.png"; qr.save(bio, "PNG"); bio.seek(0)
        await query.message.reply_photo(photo=bio, caption=f"Plan: {days}\nAmount: ₹{price}\n\n`/verify {pid} UTR_NO`")
    await query.answer()

# --- ADMIN COMMANDS ---
@app.on_message(filters.command("approve") & filters.user(OWNER_ID))
async def approve(client, message):
    if len(message.command) < 3: return
    uid, d = int(message.command[1]), int(message.command[2])
    exp = int(time.time()) + (d * 86400)
    await premium_users.update_one({"user_id": uid}, {"$set": {"expiry": exp}}, upsert=True)
    await client.send_message(uid, "🎉 Your Premium is now Active!")
    await message.reply_text("✅ Approved!")

@app.on_message((filters.video | filters.document) & filters.private & filters.user(OWNER_ID))
async def handle_v(client, message):
    fid = message.video.file_id if message.video else message.document.file_id
    if OWNER_ID not in app.batch_data: app.batch_data[OWNER_ID] = []
    app.batch_data[OWNER_ID].append(fid)
    app.last_fid = fid
    await message.reply_text(f"✅ Added! Total in Batch: {len(app.batch_data[OWNER_ID])}")

@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def add_s(client, message):
    if len(message.command) < 2: return
    name = message.command[1].lower()
    await videos.update_one({"name": name}, {"$set": {"file_id": app.last_fid, "type": "single"}}, upsert=True)
    bot = await client.get_me()
    await message.reply_text(f"✅ Link Created:\nhttps://t.me/{bot.username}?start={name}")

# --- STARTUP ---
async def start_services():
    Thread(target=run_web, daemon=True).start()
    await app.start()
    print("🚀 LINKVILLA IS LIVE ON RAILWAY!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(start_services())
