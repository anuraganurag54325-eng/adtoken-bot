import os, time, asyncio, random, string, qrcode
from io import BytesIO
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, idle
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

# --- KEEP-ALIVE ---
web = Flask('')
@web.route('/')
def home(): return "LinkVilla Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# --- CONFIG ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
CHANNEL_USERNAME = "@linkvillaadmin" 
OWNER_ID = 1853401283
UPI_ID = "anuragjaat992@ibl"
BACKUP_LINK = "https://t.me/+yvfe10wEbaJhZTM1"
PREMIUM_PIC = "https://i.ibb.co/3y2p7bFP/image.png"

app = Client("linkvilla_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["linkvilla_vfinal_db"]
videos, premium_users, payments, users_db = db["videos"], db["premium"], db["payments"], db["users"]

app.batch_data = {}

# --- FUNCTIONS ---
async def check_join(client, user_id):
    try:
        await client.get_chat_member(CHANNEL_USERNAME, user_id)
        return True
    except: return False

async def auto_delete(message):
    await asyncio.sleep(300)
    try: await message.delete()
    except: pass

# --- COMMANDS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await users_db.update_one({"user_id": message.from_user.id}, {"$set": {"user_id": message.from_user.id}}, upsert=True)
    if not await check_join(client, message.from_user.id):
        await message.reply_text(f"🚫 पहले channel join करो:\n\nhttps://t.me/{CHANNEL_USERNAME.replace('@','')}")
        return
    if len(message.command) < 2:
        await message.reply_text("👋 Welcome to LinkVilla Bot!")
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
        warn = await message.reply_text("⚠️ Ye videos 5 minute mein automatic delete ho jayengi!")
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
        await payments.insert_one({"user_id": query.from_user.id, "payment_id": pid, "days": int(days.replace('d',''))})
        await query.message.reply_photo(photo=bio, caption=f"Plan: {days}\nAmount: ₹{price}\n\n`/verify {pid} YOUR_UTR`")
    await query.answer()

# --- ADMIN ---
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):
    if not message.reply_to_message: return
    async for user in users_db.find():
        try: await message.reply_to_message.copy(user["user_id"])
        except: pass
    await message.reply_text("✅ Done!")

@app.on_message(filters.command("verify"))
async def verify(client, message):
    if len(message.command) < 3: return
    pid, utr = message.command[1], message.command[2]
    pay = await payments.find_one({"payment_id": pid})
    if pay:
        await client.send_message(OWNER_ID, f"💰 Payment: `{message.from_user.id}`\nPlan: {pay['days']}\nID: {pid}\nUTR: {utr}\n\n`/approve {message.from_user.id} {pay['days']}`")
        await message.reply_text("✅ Sent to admin!")

@app.on_message(filters.command("approve") & filters.user(OWNER_ID))
async def approve(client, message):
    uid, d = int(message.command[1]), int(message.command[2])
    exp = int(time.time()) + (d * 86400)
    await premium_users.update_one({"user_id": uid}, {"$set": {"expiry": exp}}, upsert=True)
    await client.send_message(uid, "🎉 Premium Active!")

@app.on_message((filters.video | filters.document) & filters.private & filters.user(OWNER_ID))
async def handle_v(client, message):
    fid = message.video.file_id if message.video else message.document.file_id
    if OWNER_ID not in app.batch_data: app.batch_data[OWNER_ID] = []
    app.batch_data[OWNER_ID].append(fid)
    app.last_fid = fid
    await message.reply_text(f"✅ Added! Size: {len(app.batch_data[OWNER_ID])}")

@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def add_s(client, message):
    name = message.command[1].lower()
    await videos.update_one({"name": name}, {"$set": {"file_id": app.last_fid, "type": "single"}}, upsert=True)
    bot = await client.get_me()
    await message.reply_text(f"https://t.me/{bot.username}?start={name}")

@app.on_message(filters.command("addbatch") & filters.user(OWNER_ID))
async def add_b(client, message):
    name = message.command[1].lower()
    f_list = list(app.batch_data.get(OWNER_ID, []))
    await videos.update_one({"name": name}, {"$set": {"file_ids": f_list, "type": "batch"}}, upsert=True)
    app.batch_data[OWNER_ID] = []
    bot = await client.get_me()
    await message.reply_text(f"Batch: https://t.me/{bot.username}?start={name}")

# --- FIX STARTUP LOGIC ---
async def start_bot():
    keep_alive()
    await app.start()
    print("LinkVilla Bot is Running!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
