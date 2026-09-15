import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher

from config import MASTER_BOT_TOKEN
from core.database import Database
from bots.master import router as master_router


# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("masterx")


# --------------------------------------------------
# RENDER PORT
# --------------------------------------------------

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8080"))


# --------------------------------------------------
# HEALTH SERVER
# --------------------------------------------------

async def health_handler(request: web.Request) -> web.Response:
    return web.json_response(
        {
            "status": "ok",
            "service": "MasterX Manager",
        }
    )


async def start_health_server() -> web.AppRunner:
    app = web.Application()

    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        HOST,
        PORT,
    )

    await site.start()

    logger.info(
        "HTTP server started on %s:%s",
        HOST,
        PORT,
    )

    return runner


# --------------------------------------------------
# MAIN
# --------------------------------------------------

async def main() -> None:
    logger.info("Starting MasterX Manager...")

    # Database
    database = Database()
    database.initialize()

    logger.info("Database initialized.")

    # Bot
    bot = Bot(
        token=MASTER_BOT_TOKEN,
    )

    # Dispatcher
    dispatcher = Dispatcher()

    dispatcher.include_router(
        master_router
    )

    # Render health server
    health_runner = await start_health_server()

    try:
        # Remove an old Telegram webhook if one exists.
        # We are using polling for now.
        await bot.delete_webhook(
            drop_pending_updates=True
        )

        logger.info("Telegram webhook cleared.")

        logger.info("MasterX Manager is running.")

        # Telegram polling
        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )

    except Exception:
        logger.exception(
            "MasterX Manager stopped because of an error."
        )
        raise

    finally:
        logger.info("Shutting down...")

        await health_runner.cleanup()

        await bot.session.close()

        logger.info("MasterX Manager stopped.")


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info(
            "MasterX Manager stopped manually."
    )
