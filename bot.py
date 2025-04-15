import os, re, asyncio, logging, threading
from typing import Dict, Optional
from pyrogram import Client, filters, enums, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait, MessageDeleteForbidden
from motor.motor_asyncio import AsyncIOMotorClient
from flask import Flask, redirect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
API_ID = int(os.environ.get("API_ID", 29394851))
API_HASH = os.environ.get("API_HASH", "4a97459b3db52a61a35688e9b6b86221")
USER_STRING = os.environ.get("USER_STRING", "AgHAh6MAtgaeUygtEKQ79xLpyRtnQtKiEOTvpRajN6EFDRG6m8cmj_qAdmyBFC7ikQkZaprRhNcUcY5WtJaAHFQQxA0rcSP5XBfAWVfpXQBWRAgRX8OtljxeW9NPaVLj5us2t2jPW1MGem7ozdedoTqSDuItwvtnGDt2EilVC1QFyuq-nCRHA_3Auu1FY0pspnD9jZBHXw-s8OaERD_m5qwDv1R6avKuiiE2uMktXFtoYKa9qTOfe82VnvMyF95HA9_m_TBfmNL-exkWjTQFVV1G9xD2TasjfKm8S0YsJphWPR8oO73ErjDleU5HrZMJ-NCwubGn8ZFWUnRPRk3JGTtShpeEDgAAAAGdPH8SAA")
DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb+srv://krkkanish2:kx@cluster0.uhrg1rj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

BOT_USERNAME = os.environ.get("BOT_USERNAME", "kdeletebot")
KEEP_ALIVE_URL = os.environ.get("KEEP_ALIVE_URL", "https://mamitha-delete-bot.onrender.com")

if not USER_STRING:
    logger.error("USER_STRING is missing. Please provide a valid Pyrogram session string.")
    exit(1)

class AutoDeleteBot:
    def __init__(self):
        # Database setup
        self.mongo_client = AsyncIOMotorClient(DATABASE_URL)
        self.db = self.mongo_client['databas']
        self.groups_collection = self.db['group_id']
        self.groups_data: Dict[int, Dict[str, int]] = {}

        # Initialize Pyrogram Client
        self.user_client = Client("user_client", api_id=API_ID, api_hash=API_HASH, session_string=USER_STRING)
        
        # Register message handlers
        self.register_handlers()
        
        # Flask app for keep-alive
        self.flask_app = Flask(__name__)
        self.setup_flask_routes()

    def register_handlers(self):
        @self.user_client.on_message(filters.command("start") & filters.private)
        async def start(_, message):
            logger.info(f"Received /start from {message.from_user.id}")
            button = [[InlineKeyboardButton("➕ Add me to your Group", url=f"http://t.me/{BOT_USERNAME}?startgroup=none&admin=delete_messages")]]
            await message.reply_text("Hello! I can auto-delete messages in groups. Use /set_time <time>", reply_markup=InlineKeyboardMarkup(button))
        
        @self.user_client.on_message(filters.command("set_time") & filters.group)
        async def set_delete_time(_, message):
            if len(message.text.split()) < 2:
                await message.reply("Usage: /set_time <time> (e.g., 1h, 30m, 1d)")
                return
            
            delete_time_str = message.text.split()[1]
            delete_time = self.parse_time_to_seconds(delete_time_str)
            
            if delete_time is None:
                await message.reply("Invalid time format. Use: 1h, 30m, 1d")
                return
            
            chat_id = message.chat.id
            self.groups_data[chat_id] = {"delete_time": delete_time}
            await self.groups_collection.update_one({"group_id": chat_id}, {"$set": {"delete_time": delete_time}}, upsert=True)
            await message.reply(f"Auto-delete time set to {delete_time_str}.")

        @self.user_client.on_message(filters.group)
        async def delete_message(_, message):
            chat_id = message.chat.id

            # Load from cache, or fetch from DB if missing
            if chat_id not in self.groups_data:
                group = await self.groups_collection.find_one({"group_id": chat_id})
                if group:
                    self.groups_data[chat_id] = {"delete_time": group["delete_time"]}
                else:
                    self.groups_data[chat_id] = {"delete_time": 600}  # default 10 mins

            delete_time = self.groups_data[chat_id]["delete_time"]

            logger.info(f"Scheduled to delete message {message.id} from {chat_id} after {delete_time} seconds.")
            await asyncio.sleep(delete_time)

            try:
                await message.delete()
                logger.info(f"Deleted message {message.id} from {chat_id}.")
            except Exception as e:
                logger.error(f"Failed to delete message {message.id} from {chat_id}: {e}")

    @staticmethod
    def parse_time_to_seconds(time_str: str) -> Optional[int]:
        match = re.match(r'^(\d+)([smhdw])$', time_str.lower())
        if not match:
            return None
        unit_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
        return int(match[1]) * unit_map[match[2]]
    
    def setup_flask_routes(self):
        @self.flask_app.route('/')
        def index():
            return redirect("https://telegram.me/AboutRazi", code=302)

    def run_flask(self):
        self.flask_app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

    def run(self):
        threading.Thread(target=self.run_flask, daemon=True).start()
        self.user_client.run()
        logger.info("User client started successfully and is listening for commands.")

if __name__ == "__main__":
    bot = AutoDeleteBot()
    bot.run()
