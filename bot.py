import os, asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DELETE_DURATION = int(os.getenv("DELETE_DURATION", 600))

# List of group IDs (comma-separated)
GROUP_IDS = list(map(int, os.getenv("GROUP_IDS", "").split(",")))

app = Flask(__name__)

bot = Client(
    "auto_deleter_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN)

@app.route("/")
def home():
    return "Hello, World!"
    
def run_flask():
    app.run(host="0.0.0.0", port=5000)

@bot.on_message(filters.chat(GROUP_IDS))
async def delete_message(client, message):
    try:
        await asyncio.sleep(DELETE_DURATION)
        await message.delete()
    except FloodWait as e:
        print(f"FloodWait error! Sleeping for {e.value} seconds...")
        await asyncio.sleep(e.value)
    except Exception as ex:
        print(f"Error occurred: {ex}")


if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    print("Bot is running...")
    bot.run()
