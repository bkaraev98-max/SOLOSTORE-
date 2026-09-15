import asyncio

from aiogram import Bot, Dispatcher

from config import MASTER_BOT_TOKEN
from core.database import Database
from bots.master import router as master_router


async def main() -> None:
    database = Database()
    database.initialize()

    bot = Bot(
        token=MASTER_BOT_TOKEN
    )

    dispatcher = Dispatcher()

    dispatcher.include_router(
        master_router
    )

    try:
        print("MasterX Manager is starting...")

        await dispatcher.start_polling(
            bot
        )

    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
