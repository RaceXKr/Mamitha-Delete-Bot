import os, asyncio, logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

# Logging (set to WARNING to reduce verbosity)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Environment
API_ID = int(os.environ.get("API_ID", 29394851))
API_HASH = os.environ.get("API_HASH", "4a97459b3db52a61a35688e9b6b86221")
USER_STRING = os.environ.get("USER_STRING", "AgHAh6MARs2Y3qzJzJQDh3kAfoKjCudJjwG6-GYE1JvET7bxFzyeKBNTpTxMCIn6_itw_G1xutV1VWIKLej_3Ab8zYdvA-4LIdZYWZ5AA2n9qBr2S55Oa9t7spw3_IOnBON7_p1aD5s2_ZMowSAMlcZnG-ZjZGyNj3Q787XtBuJErbBifYcqfX6GSXVKj0pJLoYQ6ThSV9JX_MIxMzx11_2AwrVCOZtT8dgaqMDrC-MnDL2zW1_KYSyhEtiC0LyOt42yDdpjaMh_LaogVr5kUVqf4Di529MUTYlIFYJWCPQuapXUgsr0IDQGw-hAVKHqFmijYbl3MPjyo-lgxPajWLLTafM1HgAAAAGdPH8SAA")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "kdeletebot")


# Default delete time in seconds
DELETE_TIME = 600  # 10 minutes

class AutoDeleteBot:
    def __init__(self):
        self.user_client = Client(
            "user_client", api_id=API_ID, api_hash=API_HASH, session_string=USER_STRING
        )
        self.register_handlers()

    def register_handlers(self):
        @self.user_client.on_message(filters.command("start") & filters.private)
        async def start(_, message):
            btn = [[InlineKeyboardButton("➕ Add me to your Group", url=f"http://t.me/{BOT_USERNAME}?startgroup=none&admin=delete_messages")]]
            await message.reply_text(
                "👋 Hello! I'm an auto-delete bot.\nMessages will auto-delete after 10 minutes.",
                reply_markup=InlineKeyboardMarkup(btn)
            )

        @self.user_client.on_message(filters.group)
        async def delete_message(_, message):
            asyncio.create_task(self.schedule_delete(message))

    async def schedule_delete(self, message):
        try:
            await asyncio.sleep(DELETE_TIME)
            await message.delete()
        except Exception as e:
            logger.warning(f"Delete failed: {e}")

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
        await self.user_client.start()
        await self.run_keep_alive()
        await self.user_client.run()

if __name__ == "__main__":
    if not USER_STRING:
        logger.error("USER_STRING is missing.")
        exit(1)
    bot = AutoDeleteBot()
    asyncio.run(bot.run())
