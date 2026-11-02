
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiohttp import web

from .settings import BOT_TOKEN
from .database import init_db
from .handlers import router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("MASTER_X")


async def health_check(request):
    return web.Response(text="MASTER X is running!")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)

    await site.start()
    logger.info("Web server started on port %s", port)

    return runner


async def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Set it in Render Environment Variables."
        )

    init_db()

    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    runner = None

    try:
        runner = await start_web_server()

        logger.info("MASTER X bot is starting...")

        await dispatcher.start_polling(bot)

    except Exception:
        logger.exception("MASTER X stopped because of an error.")
        raise

    finally:
        if runner is not None:
            await runner.cleanup()

        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
    
    
