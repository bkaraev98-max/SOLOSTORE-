
import asyncio
import logging

from aiogram import Bot, Dispatcher

from .settings import BOT_TOKEN
from .database import init_db
from .handlers import router


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Set BOT_TOKEN in Render Environment Variables."
        )

    init_db()

    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    logging.info("MASTER X is starting...")

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
    
