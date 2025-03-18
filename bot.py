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
USER_SESSION = os.environ.get("USER_SESSION", "AgHAh6MAtgaeUygtEKQ79xLpyRtnQtKiEOTvpRajN6EFDRG6m8cmj_qAdmyBFC7ikQkZaprRhNcUcY5WtJaAHFQQxA0rcSP5XBfAWVfpXQBWRAgRX8OtljxeW9NPaVLj5us2t2jPW1MGem7ozdedoTqSDuItwvtnGDt2EilVC1QFyuq-nCRHA_3Auu1FY0pspnD9jZBHXw-s8OaERD_m5qwDv1R6avKuiiE2uMktXFtoYKa9qTOfe82VnvMyF95HA9_m_TBfmNL-exkWjTQFVV1G9xD2TasjfKm8S0YsJphWPR8oO73ErjDleU5HrZMJ-NCwubGn8ZFWUnRPRk3JGTtShpeEDgAAAAGdPH8SAA")  # Use a Pyrogram user session
DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb+srv://krkkanish2:kx@cluster0.uhrg1rj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")


BOT_USERNAME = os.environ.get("BOT_USERNAME", "kdeletebot")

# Database setup
client = AsyncIOMotorClient(DATABASE_URL)
db = client['databas']
groups = db['group_id']

user_bot = Client("user_deletebot", session_string=USER_SESSION, api_id=API_ID, api_hash=API_HASH)

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

    try:
        delete_time = int(group.get("delete_time", 0))  # Ensure delete_time is an integer
    except ValueError:
        delete_time = 0

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

# Flask configuration
app = Flask(__name__)

@app.route('/')
def index():
    return redirect("https://telegram.me/KristyX_TG", code=302)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

# Keep-alive function using aiohttp
async def keep_alive():
    url = "https://conservation-adria-selvarajsangeeth419-5dc1bf17.koyeb.app"  # Replace with your bot's URL
    while True:
        try:
            async with ClientSession() as session:
                async with session.get(url) as response:
                    print(f"Keep-alive ping sent! Status: {response.status}")
        except Exception as e:
            print(f"Keep-alive error: {e}")
        await asyncio.sleep(300)  # Ping every 5 minutes

# Start Flask in a separate thread
flask_thread = Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# Run keep-alive function
async def main():
    asyncio.create_task(keep_alive())  # Ensure keep-alive runs in the background
    await user_bot.start()
    await asyncio.Event().wait()  # Keeps the bot running

asyncio.run(main())  # Run the bot with keep-alive
user_bot.run()
