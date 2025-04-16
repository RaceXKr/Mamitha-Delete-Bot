import os, asyncio, logging
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

# Logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Environment variables
API_ID = int(os.environ.get("API_ID", 29394851))
API_HASH = os.environ.get("API_HASH", "4a97459b3db52a61a35688e9b6b86221")
USER_STRING = os.environ.get("USER_STRING", "AgHAh6MAZleu9iBhzALF2pkQwwB-KwIDazSWbB85zBY27lRWOgplcViMQ4LCxwgDYnASR88Upty86Ng5WJ-OaefaP4nC1HVsSnn1NXAkSf2nYLHbSP1kSTWfaqc9k7OFWStTDqoMUiK4kkyMeGCuElnc_asqjss9LTZFYq1PmZPXva86M30hAXY8fkwHIpn6TWClpMpo-0-Elpxa8e0gnQGzsl4BX-V2M604_QyZEzqhLrkDPite-lYS9waSGRhz2zEHE7DEYgip3OwB-9mzD3NmwIsZaaMWXM1Q-sJIi8_1BiW0H3vGEot8gZZH5xKDU2rB3ShHH2kCORgH2pne6LCf0jOqrQAAAAGdPH8SAA")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "kdeletebot")
DELETE_TIME = 10  # seconds
AUTH_GROUPS = [-1002234999320, -1002589924363]  # Replace with your auth Replace with your authorized group IDs

app = web.Application()

class AutoDeleteBot(Client):
    def __init__(self):
        super().__init__(
            "user_client",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=USER_STRING
        )

    async def start_bot(self):
        await self.start()
        logger.warning("User client started.")

        self.add_handler(MessageHandler(self.start_command, filters.command("start") & filters.private))
        self.add_handler(MessageHandler(self.delete_handler, filters.group))

        logger.warning("Handlers registered.")

    async def stop_bot(self):
        await self.stop()
        logger.warning("Bot stopped.")

    async def start_command(self, client, message):
        logger.info(f"/start from {message.from_user.id}")
        btn = [[InlineKeyboardButton("➕ Add me to your Group", url=f"http://t.me/{BOT_USERNAME}?startgroup=none&admin=delete_messages")]]
        await message.reply_text("👋 I'm an auto-delete bot. I delete group messages after 10 mins.", reply_markup=InlineKeyboardMarkup(btn))

    async def delete_handler(self, client, message):
        if message.chat.id in AUTH_GROUPS:
            logger.info(f"Scheduling deletion: msg {message.id} in group {message.chat.id}")
            asyncio.create_task(self.schedule_delete(message))

    async def schedule_delete(self, message):
        try:
            logger.info(f"Msg {message.id} will delete after {DELETE_TIME}s")
            await asyncio.sleep(DELETE_TIME)
            await message.delete()
            logger.info(f"Deleted msg {message.id}")
        except Exception as e:
            logger.error(f"Failed to delete msg {message.id}: {e}")

    async def health_check(self, request):
        return web.Response(text="I'm alive!", content_type="text/html")

# Entry point
async def main():
    if not USER_STRING:
        logger.error("USER_STRING is missing.")
        return

    bot = AutoDeleteBot()
    await bot.start_bot()

    app.router.add_get("/", bot.health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

    logger.warning("Keep-alive server running.")
    
    # Keep running forever
    try:
        while True:
            await asyncio.sleep(60)
    finally:
        await bot.stop_bot()

if __name__ == "__main__":
    asyncio.run(main())
