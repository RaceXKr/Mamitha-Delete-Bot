import os, asyncio, logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

# Logging (set to WARNING to reduce logs on Koyeb)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Environment variables
API_ID = int(os.environ.get("API_ID", 29394851))
API_HASH = os.environ.get("API_HASH", "4a97459b3db52a61a35688e9b6b86221")
USER_STRING = os.environ.get("USER_STRING", "AQGql-8Aq7mcxYq3d9LvRJSiTVAWPY-ZsNkGJEySvxmFCF2sfZiYrzECoQnYfve7h2MhaNVr_10mrWjIcIw8QHLlNEpK01Se1sfcAn_xEQOvq6pBz5XCDtrFHmUUgyXTf4O4yi9qK5_bBNwe-XDL0FDVW6aomO0FHgxMFRD-s_zHXR6GwJCr49sbRDlT99vo094SnqgoeIVee08yeL9l-lumHkDc6q0ov8FjJJB2cz1ww5Ze6xCU4zujSDPeA-7wSV4E22JlbwffbWiqZWsmNCQh-3igaBiC9enul2wWbe0g96nVp3PraM18zEX3Mf5AbRPYTe__m2qJOv5zGe1B-whg1z8HrgAAAAFzPARfAA")
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

    async def start(self):
        await super().start()
        logger.warning("User client started.")

        # Register handlers using on_message for more control
        self.on_message(filters.command("start") & filters.private)(self.start_command)
        self.on_message(filters.group)(self.delete_handler)

        # Start keep-alive server
        app.router.add_get("/", self.health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
        await site.start()
        logger.warning("Keep-alive server running.")

    async def start_command(self, client, message):
        # Log the user sending the /start command
        logger.info(f"/start command received from user {message.from_user.id}")
        btn = [[InlineKeyboardButton("➕ Add me to your Group", url=f"http://t.me/{BOT_USERNAME}?startgroup=none&admin=delete_messages")]]
        await message.reply_text(
            "👋 Hello! I'm an auto-delete bot.\nMessages will auto-delete after 10 minutes.",
            reply_markup=InlineKeyboardMarkup(btn)
        )

    async def delete_handler(self, client, message):
        if message.chat.id in AUTH_GROUPS:
            # Log the message being scheduled for deletion
            logger.info(f"Scheduling message {message.id} for deletion in group {message.chat.id}")
            asyncio.create_task(self.schedule_delete(message))
        else:
            logger.info(f"Message {message.id} ignored from unauthorized group {message.chat.id}")

    async def schedule_delete(self, message):
        try:
            # Adding logs to track when the deletion is scheduled
            logger.info(f"Message {message.id} will be deleted after {DELETE_TIME} seconds.")
            await asyncio.sleep(DELETE_TIME)
            await message.delete()
            logger.info(f"Message {message.id} deleted successfully after {DELETE_TIME} seconds.")
        except asyncio.CancelledError:
            logger.warning(f"Scheduled deletion of message {message.id} was cancelled.")
        except Exception as e:
            logger.error(f"Error while trying to delete message {message.id}: {e}")

    async def health_check(self, request):
        return web.Response(text="I'm alive!", content_type='text/html')


if __name__ == "__main__":
    if not USER_STRING:
        logger.error("USER_STRING is missing.")
        exit(1)

    bot = AutoDeleteBot()
    try:
        # Launch using Pyrogram's internal event loop
        bot.run()
    except Exception as e:
        logger.error(f"Bot encountered an error: {e}")
