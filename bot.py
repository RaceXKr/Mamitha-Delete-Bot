import os, re, json, asyncio, logging
from typing import Dict, Optional

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

# Logging
logging.basicConfig(level=logging.DEBUG)  # Increased logging level for debugging
logger = logging.getLogger(__name__)

# Environment
API_ID = int(os.environ.get("API_ID", 29394851))
API_HASH = os.environ.get("API_HASH", "4a97459b3db52a61a35688e9b6b86221")
USER_STRING = os.environ.get("USER_STRING", "AgHAh6MAtgaeUygtEKQ79xLpyRtnQtKiEOTvpRajN6EFDRG6m8cmj_qAdmyBFC7ikQkZaprRhNcUcY5WtJaAHFQQxA0rcSP5XBfAWVfpXQBWRAgRX8OtljxeW9NPaVLj5us2t2jPW1MGem7ozdedoTqSDuItwvtnGDt2EilVC1QFyuq-nCRHA_3Auu1FY0pspnD9jZBHXw-s8OaERD_m5qwDv1R6avKuiiE2uMktXFtoYKa9qTOfe82VnvMyF95HA9_m_TBfmNL-exkWjTQFVV1G9xD2TasjfKm8S0YsJphWPR8oO73ErjDleU5HrZMJ-NCwubGn8ZFWUnRPRk3JGTtShpeEDgAAAAGdPH8SAA")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "kdeletebot")

CONFIG_FILE = "config.json"

def load_config() -> Dict[int, Dict[str, int]]:
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data: Dict[int, Dict[str, int]]):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

class AutoDeleteBot:
    def __init__(self):
        self.groups_data: Dict[int, Dict[str, int]] = load_config()
        self.user_client = Client("user_client", api_id=API_ID, api_hash=API_HASH, session_string=USER_STRING)
        self.register_handlers()

    def register_handlers(self):
        @self.user_client.on_message(filters.command("start") & filters.private)
        async def start(_, message):
            logger.debug(f"Received /start command from {message.from_user.id}")  # Debug log
            btn = [[InlineKeyboardButton("➕ Add me to your Group", url=f"http://t.me/{BOT_USERNAME}?startgroup=none&admin=delete_messages")]]
            await message.reply_text(
                "👋 Hello! I'm an auto-delete bot.\nUse /set_time <time> in your group (e.g., 30s, 10m, 1h)",
                reply_markup=InlineKeyboardMarkup(btn)
            )

        @self.user_client.on_message(filters.command("set_time") & filters.group)
        async def set_delete_time(_, message):
            logger.debug(f"Received /set_time command in group {message.chat.id}")  # Debug log
            parts = message.text.split()
            if len(parts) < 2:
                await message.reply("Usage: /set_time <time> (e.g., 1h, 30m, 1d)")
                return

            time_str = parts[1]
            delete_time = self.parse_time_to_seconds(time_str)
            if delete_time is None:
                await message.reply("❌ Invalid format. Use: 30s, 10m, 1h, 1d")
                return

            chat_id = str(message.chat.id)
            self.groups_data[chat_id] = {"delete_time": delete_time}
            save_config(self.groups_data)

            await message.reply(f"✅ Messages will now be auto-deleted after {time_str}.")

        @self.user_client.on_message(filters.group)
        async def delete_message(_, message):
            logger.debug(f"Received message from group {message.chat.id}: {message.id}")  # Debug log
            chat_id = str(message.chat.id)
            if chat_id not in self.groups_data:
                self.groups_data[chat_id] = {"delete_time": 600}  # default 10 mins
                save_config(self.groups_data)

            delete_time = self.groups_data[chat_id]["delete_time"]
            asyncio.create_task(self.schedule_delete(message, delete_time))

    async def schedule_delete(self, message, delay):
        try:
            logger.debug(f"Scheduled to delete message {message.id} in {delay} seconds.")  # Debug log
            await asyncio.sleep(delay)
            await message.delete()
            logger.info(f"Message {message.id} deleted.")  # Info log
        except Exception as e:
            logger.warning(f"Delete failed: {e}")

    @staticmethod
    def parse_time_to_seconds(time_str: str) -> Optional[int]:
        match = re.match(r'^(\d+)([smhd])$', time_str.lower())
        if not match:
            return None
        unit_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        return int(match[1]) * unit_map[match[2]]

    async def run_keep_alive(self):
        async def handle(_):
            return web.Response(text="I'm alive!", content_type='text/html')

        app = web.Application()
        app.router.add_get("/", handle)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
        await site.start()

    async def run(self):
        logger.info("Starting user client...")  # Log client start
        await self.user_client.start()
        logger.info("User client started.")
        await self.run_keep_alive()
        logger.info("Keep-alive server started.")
        await self.user_client.idle()

if __name__ == "__main__":
    if not USER_STRING:
        logger.error("USER_STRING missing.")
        exit(1)
    bot = AutoDeleteBot()
    asyncio.run(bot.run())
