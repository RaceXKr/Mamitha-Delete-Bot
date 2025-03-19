import os
import asyncio
from pyrogram import Client, filters, enums
from threading import Thread
from aiohttp import ClientSession
from flask import Flask, redirect
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from motor.motor_asyncio import AsyncIOMotorClient

API_ID = int(os.environ.get("API_ID", 29394851))
API_HASH = os.environ.get("API_HASH", "4a97459b3db52a61a35688e9b6b86221")
USER_SESSION = os.environ.get("USER_SESSION", "AgHAh6MAG4P7me1d6hXKIGh0gA7Jb8ygRFXzo42Vq0P619HA083Sw7WqFbQXeYZ9MmlLSoX3tZImEbRhARj2JgJTQQ9RBQSeCeEOs1Kl61tjvGseihXBrMuw2fzSIH98kDvsPQHKvc4SBOXj_NByS-9CoPiV9jmUGLG7eQWpYyE58j9ae1pGppDL2_ajJrI_5FkfIKbpAG9MZzWKd_K9jEQmTFvJ7u9wkh0RhF0R1d-jK2r9HX2Gn85U3LgdZFSS-jf_FlgtTyx2--snx_0qtezHuNGi3UEmArhv8GaRhVKYLY24A01ET11TVEaIXD4V17H8p1GW6Qko-Ay09IQ8OAo5Y9wo1AAAAAGdPH8SAA")  # Replace with your session string
DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb+srv://krkkanish2:kx@cluster0.uhrg1rj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

BOT_USERNAME = os.environ.get("BOT_USERNAME", "kdeletebot")

# Database setup
client = AsyncIOMotorClient(DATABASE_URL)
db = client['databas']
groups = db['group_id']

user_bot = Client("user_deletebot", session_string=USER_SESSION, api_id=API_ID, api_hash=API_HASH)

# Command Handlers
@user_bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    button = [[
        InlineKeyboardButton("➕ Add me to your Group", url=f"http://t.me/{BOT_USERNAME}?startgroup=none&admin=delete_messages"),
    ], [
        InlineKeyboardButton("📌 Updates Channel", url="https://t.me/botsync"),
    ]]
    await message.reply_text(
        f"**Hello {message.from_user.first_name},\nI am an AutoDelete Bot. I can delete all messages in your group automatically after a certain period of time.\nUsage:** `/set_time <time_in_seconds>`",
        reply_markup=InlineKeyboardMarkup(button),
        parse_mode=enums.ParseMode.MARKDOWN
    )

@user_bot.on_message(filters.command("set_time"))
async def set_delete_time(_, message):
    if message.chat.type == enums.ChatType.PRIVATE:
        await message.reply("This command can only be used in groups.")
        return

    args = message.text.split()
    if len(args) == 1 or not args[1].isdigit():
        await message.reply_text("**Please provide the delete time in seconds. Usage:** `/set_time <time_in_seconds>`")
        return

    delete_time = int(args[1])
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None

    administrators = [m.user.id async for m in user_bot.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS)]
    if user_id and user_id not in administrators:
        await message.reply("Only group admins can enable or disable auto delete.")
        return

    await groups.update_one(
        {"group_id": chat_id},
        {"$set": {"delete_time": delete_time}},
        upsert=True
    )

    await message.reply_text(f"**Set delete time to {delete_time} seconds for this group.**")

@user_bot.on_message(filters.group & ~filters.command(["set_time", "start", "delete_all"]))
async def delete_message(client, message):
    chat_id = message.chat.id
    group = await groups.find_one({"group_id": chat_id})
    if not group:
        return

    delete_time = int(group.get("delete_time", 0))
    if delete_time > 0:
        await asyncio.sleep(delete_time)
        try:
            await client.delete_messages(chat_id, message.id)
        except Exception as e:
            print(f"Error deleting message in {chat_id}: {e}")

@user_bot.on_message(filters.command("delete_all"))
async def delete_all_messages(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None

    administrators = [m.user.id async for m in user_bot.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS)]
    if user_id and user_id not in administrators:
        await message.reply("Only group admins can use this command.")
        return

    deleted_count = 0
    async for msg in user_bot.get_chat_history(chat_id):
        try:
            await client.delete_messages(chat_id, msg.id)
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting message {msg.id}: {e}")

    await message.reply(f"✅ Successfully deleted {deleted_count} messages in this group/channel!")

# Flask Configuration for Keep-Alive
app = Flask(__name__)

@app.route('/')
def index():
    return redirect("https://telegram.me/KristyX_TG", code=302)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

# Keep-Alive Function using aiohttp
async def keep_alive():
    url = "https://low-lesly-selvarajsangeeth419-4a099a4d.koyeb.app"  # Replace with your bot's URL
    while True:
        try:
            async with ClientSession() as session:
                async with session.get(url) as response:
                    print(f"✅ Keep-alive ping sent! Status: {response.status}")
        except Exception as e:
            print(f"⚠ Keep-alive error: {e}")
        await asyncio.sleep(300)  # Ping every 5 minutes

# Start Keep-Alive and Flask Before Bot Runs
def start_services():
    # Start Flask server in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start Keep-Alive in an Asyncio Loop
    loop = asyncio.get_event_loop()
    loop.create_task(keep_alive())

# Run the bot and services
if __name__ == "__main__":
    start_services()  # Start Flask and Keep-Alive
    user_bot.run()  # Start Pyrogram bot properly
